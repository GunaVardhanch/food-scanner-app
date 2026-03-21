"use client";
import { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";

const API = typeof process.env.NEXT_PUBLIC_API_URL === "string"
  ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
  : "http://127.0.0.1:7860";

const TRANSLATE_ENDPOINT = `${API}/api/translate`;

// In-memory cache: "text::targetLang" → translated string
const cache = {};

export const LANGUAGES = [
  { code: "en", label: "English", native: "English" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "bn", label: "Bengali", native: "বাংলা" },
  { code: "gu", label: "Gujarati", native: "ગુજરાતી" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ" },
];

const TranslateContext = createContext(null);

export function TranslateProvider({ children }) {
  const [lang, setLang] = useState("en");
  const [translations, setTranslations] = useState({});
  const pendingRef = useRef(new Set());

  // Batching queue for the frontend
  const queueRef = useRef([]);
  const timeoutRef = useRef(null);

  const translateBatch = useCallback(async (texts, targetLang) => {
    // Kept to avoid breaking existing usages (though 't' now queues)
  }, []);

  const flushQueue = useCallback(async () => {
    const queue = queueRef.current;
    if (queue.length === 0) return;

    // Group requests by language
    const byLang = {};
    queue.forEach(({ text, targetLang }) => {
      if (!byLang[targetLang]) byLang[targetLang] = new Set();
      byLang[targetLang].add(text);
    });

    queueRef.current = []; // Clear queue immediately

    // Process each language batch
    for (const [targetLang, textSet] of Object.entries(byLang)) {
      const uncachedTexts = Array.from(textSet).filter(t => {
        const key = `${t}::${targetLang}`;
        return !cache[key] && !pendingRef.current.has(key);
      });

      if (uncachedTexts.length === 0) continue;

      // Mark as pending
      uncachedTexts.forEach(t => pendingRef.current.add(`${t}::${targetLang}`));

      try {
        const res = await fetch(TRANSLATE_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ texts: uncachedTexts, target: targetLang }),
        });

        if (!res.ok) throw new Error("Translation failed");

        const data = await res.json();
        const newEntries = {};

        if (data.translations && data.translations.length === uncachedTexts.length) {
          uncachedTexts.forEach((original, i) => {
            const translated = data.translations[i];
            const key = `${original}::${targetLang}`;
            cache[key] = translated;
            // Only update UI if this language is still the active one
            if (targetLang === lang) {
              newEntries[original] = translated;
            }
            pendingRef.current.delete(key);
          });
        }

        setTranslations(prev => ({ ...prev, ...newEntries }));
      } catch (err) {
        // Fallback to English on error
        console.error("Translation proxy error:", err);
        uncachedTexts.forEach(t => pendingRef.current.delete(`${t}::${targetLang}`));
      }
    }
  }, [lang]);

  const changeLang = useCallback((newLang) => {
    setLang(newLang);
    setTranslations({}); // clear display map; let 't' rebuild it
  }, []);

  const t = useCallback((text) => {
    if (!text || lang === "en") return text;
    const key = `${text}::${lang}`;
    if (cache[key]) return cache[key];

    // Queue translation (fire-and-forget, will trigger re-render via setTranslations later)
    if (!pendingRef.current.has(key)) {
      queueRef.current.push({ text, targetLang: lang });
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      // Wait 50ms to grab all UI strings rendering at once
      timeoutRef.current = setTimeout(flushQueue, 50);
    }

    // Return original English text while we wait for translation to load
    return translations[text] || text;
  }, [lang, translations, flushQueue]);

  return (
    <TranslateContext.Provider value={{ lang, changeLang, t, translateBatch, LANGUAGES }}>
      {children}
    </TranslateContext.Provider>
  );
}

export function useTranslate() {
  const ctx = useContext(TranslateContext);
  if (!ctx) throw new Error("useTranslate must be used inside <TranslateProvider>");
  return ctx;
}

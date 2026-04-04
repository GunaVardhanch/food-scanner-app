import { useCallback } from 'react';
import { translations } from './translations';

/**
 * Custom hook for multi-language translation support
 * Usage: const t = useTranslation('en');
 *        const greeting = t('goodMorning');
 */
export function useTranslation(language = 'en') {
  // Fallback to English if language not supported
  const lang = translations[language] ? language : 'en';
  
  const t = useCallback((key, defaultValue = key) => {
    return translations[lang]?.[key] ?? defaultValue;
  }, [lang]);
  
  return t;
}

/**
 * Custom hook for managing language preference with localStorage
 */
export function useLanguagePreference() {
  const getLanguage = useCallback(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('app_language') || 'en';
    }
    return 'en';
  }, []);
  
  const setLanguage = useCallback((language) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('app_language', language);
      window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language } }));
    }
  }, []);
  
  return { getLanguage, setLanguage };
}

/**
 * Detect user's default language based on browser settings
 */
export function detectUserLanguage() {
  if (typeof window === 'undefined') return 'en';
  
  const browserLang = navigator.language.split('-')[0];
  const supportedLangs = ['en', 'hi', 'te', 'ta'];
  
  return supportedLangs.includes(browserLang) ? browserLang : 'en';
}

/**
 * Format text for specific language (e.g., RTL support in future)
 */
export function getLanguageDirection(language) {
  const rtlLanguages = []; // Add RTL languages if needed
  return rtlLanguages.includes(language) ? 'rtl' : 'ltr';
}

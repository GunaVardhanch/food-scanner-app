"use client";

import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import "../i18n";
import SplashScreen from "./components/SplashScreen";
import WelcomeScreen from "./components/WelcomeScreen";
import HistoryFeed from "./components/HistoryFeed";
import TrendsView from "./components/TrendsView";

const API = typeof process.env.NEXT_PUBLIC_API_URL === "string"
  ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
  : "http://127.0.0.1:7860";

// ── Small helpers ──────────────────────────────────────────────────────────────
const scoreConfig = {
  RED: { bg: "bg-gradient-to-br from-red-500 to-rose-700", label: "HARMFUL", emoji: "🚨", badge: "bg-red-100 text-red-700", glow: "0 0 40px rgba(239,68,68,0.5)" },
  YELLOW: { bg: "bg-gradient-to-br from-yellow-400 to-amber-500", label: "MODERATE", emoji: "⚠️", badge: "bg-yellow-100 text-yellow-800", glow: "0 0 40px rgba(234,179,8,0.5)" },
  GREEN: { bg: "bg-gradient-to-br from-emerald-400 to-green-600", label: "HEALTHY", emoji: "✅", badge: "bg-green-100 text-green-800", glow: "0 0 40px rgba(16,185,129,0.5)" },
};

// ── NutritionCard ──────────────────────────────────────────────────────────────
const NutritionCard = ({ nutrition }) => {
  if (!nutrition) return null;
  const items = [
    { label: "Calories", val: nutrition.calories || "N/A", color: "text-slate-900" },
    { label: "Protein", val: nutrition.protein || "N/A", color: "text-emerald-600" },
    { label: "Fat", val: nutrition.total_fat || "N/A", color: "text-orange-500" },
    { label: "Sugar", val: nutrition.sugar || "N/A", color: "text-red-500" },
    { label: "Carbs", val: nutrition.carbs || "N/A", color: "text-blue-500" },
    { label: "Sodium", val: nutrition.sodium || "N/A", color: "text-purple-500" },
  ];
  return (
    <div className="grid grid-cols-3 gap-2 mb-6">
      {items.map((it, i) => (
        <div key={i} className="bg-white rounded-2xl p-3 border border-slate-100 shadow-sm text-center">
          <p className="text-[9px] font-black text-slate-400 mb-0.5 uppercase tracking-wide">{it.label}</p>
          <p className={`text-sm font-black ${it.color}`}>{it.val}</p>
        </div>
      ))}
    </div>
  );
};

// ── ScoreReveal overlay ────────────────────────────────────────────────────────
const ScoreReveal = ({ result, onDone }) => {
  const [phase, setPhase] = useState("initial"); // initial→nutrition→additives→score
  const [displayNum, setDisplayNum] = useState(0);
  const score = result.health_score || "YELLOW";
  const cfg = scoreConfig[score] || scoreConfig.YELLOW;
  const finalNum = result.score_value ?? (score === "RED" ? 2 : score === "GREEN" ? 9 : 5);
  const nutrition = result.nutrition || {};

  useEffect(() => {
    const ts = [
      setTimeout(() => setPhase("nutrition"), 1200),
      setTimeout(() => setPhase("additives"), 3800),
      setTimeout(() => setPhase("score"), 6000),
    ];
    return () => ts.forEach(clearTimeout);
  }, []);

  useEffect(() => {
    if (phase !== "score") return;
    let c = 0;
    const iv = setInterval(() => {
      c++;
      setDisplayNum(Math.floor(Math.random() * 10));
      if (c > 20) { clearInterval(iv); setDisplayNum(finalNum); setTimeout(onDone, 2200); }
    }, 60);
    return () => clearInterval(iv);
  }, [phase, finalNum]);

  return (
    <div className="fixed inset-0 bg-slate-950/97 backdrop-blur-2xl flex flex-col items-center justify-center z-50 p-6 overflow-hidden">
      {phase === "initial" && (
        <div className="text-center animate-reveal-pop">
          <div className="w-20 h-20 border-4 border-white/20 border-t-emerald-400 rounded-full animate-spin mx-auto mb-6" />
          <p className="text-white font-black tracking-widest uppercase text-xs animate-pulse">Processing with RAG Engine…</p>
        </div>
      )}
      {phase !== "initial" && (
        <div className="absolute top-10 left-0 right-0 text-center px-6">
          <h3 className="text-white font-black text-lg uppercase tracking-tight">
            {result.brand && <span className="opacity-50 text-sm mr-2">{result.brand} —</span>}
            {result.product_name || "Unknown Product"}
          </h3>
        </div>
      )}
      {phase === "nutrition" && (
        <div className="w-full max-w-sm animate-reveal-pop">
          <p className="text-emerald-400 font-black tracking-widest uppercase text-[10px] mb-2 text-center">Discovery 01: Nutritional Profile</p>
          <h2 className="text-white text-3xl font-black text-center mb-8">Nutrition Facts</h2>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "SUGAR", val: nutrition.sugar, col: "text-red-400" },
              { label: "FAT", val: nutrition.total_fat, col: "text-orange-400" },
              { label: "CARBS", val: nutrition.carbs, col: "text-blue-400" },
              { label: "CALORIES", val: nutrition.calories, col: "text-white" },
            ].map((n, i) => (
              <div key={i} className="bg-white/5 border border-white/10 rounded-3xl p-6">
                <p className="text-slate-500 text-[9px] font-black uppercase tracking-widest mb-1">{n.label}</p>
                <p className={`text-2xl font-black ${n.col}`}>{n.val ?? "N/A"}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {phase === "additives" && (
        <div className="w-full max-w-sm animate-reveal-pop">
          <p className="text-amber-400 font-black tracking-widest uppercase text-[10px] mb-2 text-center">Discovery 02: Ingredient Check</p>
          <h2 className="text-white text-3xl font-black text-center mb-6">Additives Found</h2>
          <div className="space-y-3 max-h-[40vh] overflow-y-auto pr-1">
            {result.additives && result.additives.length > 0 ? (
              result.additives.slice(0, 6).map((a, i) => (
                <div key={i} className="bg-white/5 border border-white/10 rounded-2xl p-4 flex justify-between items-center">
                  <p className="text-white/80 font-black text-xs">{a.name}</p>
                  <span className={`text-[8px] font-black px-2 py-0.5 rounded-full uppercase ${a.risk_level === "RED" ? "bg-red-500 text-white" : "bg-slate-700 text-white"}`}>{a.risk_level}</span>
                </div>
              ))
            ) : (
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-6 text-center">
                <p className="text-emerald-400 font-black text-sm uppercase">✅ Clean Label — No harmful additives detected</p>
              </div>
            )}
            {result.rag_analysis?.warnings?.length > 0 && (
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-3">
                {result.rag_analysis.warnings.slice(0, 3).map((w, i) => (
                  <p key={i} className="text-amber-300 text-[10px] font-bold">⚠ {w}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      {phase === "score" && (
        <div className="flex flex-col items-center animate-reveal-pop">
          <p className="text-[#6c63ff] font-black tracking-widest uppercase text-[10px] mb-8 animate-pulse">Final RAG Analysis Complete</p>
          <div
            className={`w-60 h-60 rounded-full bg-gradient-to-br ${cfg.bg.replace("bg-gradient-to-br ", "")} flex flex-col items-center justify-center border-8 border-white/20 shadow-2xl transition-all duration-700`}
            style={{ boxShadow: cfg.glow }}
          >
            <span className="text-8xl font-black text-white drop-shadow-2xl">{displayNum}</span>
            <span className="text-white/60 text-[10px] font-black tracking-widest uppercase mt-1">Health Score</span>
          </div>
          <div className="mt-8 text-center">
            <span className="text-5xl">{cfg.emoji}</span>
            <p className="text-3xl font-black mt-3 text-white uppercase tracking-tight">{cfg.label}</p>
          </div>
        </div>
      )}
    </div>
  );
};

// ── SettingsView ───────────────────────────────────────────────────────────────
const SettingsView = ({ preferences, onUpdate, currentUser, isGuest, onLogout }) => {
  const toggles = [
    { id: "vegan", label: "Vegan", emoji: "🌱", desc: "Flag animal-derived ingredients" },
    { id: "no_sugar", label: "No Sugar", emoji: "🚫", desc: "Strict alerts for sucrose/syrups" },
    { id: "low_sodium", label: "Low Sodium", emoji: "🧂", desc: "Flag high salt content" },
    { id: "gluten_free", label: "Gluten Free", emoji: "🌾", desc: "Alert for wheat, barley, rye" },
  ];
  return (
    <div className="flex-1 px-5 pt-4 pb-24 overflow-y-auto">
      {/* User card */}
      <div className={`rounded-3xl p-5 mb-6 ${isGuest ? "bg-slate-100" : "bg-gradient-to-br from-[#3a3f85] to-[#6c63ff]"}`}>
        <div className="flex items-center gap-4">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl font-black shadow-inner ${isGuest ? "bg-slate-200 text-slate-500" : "bg-white/20 text-white"}`}>
            {isGuest ? "👤" : (currentUser?.name?.[0]?.toUpperCase() || "U")}
          </div>
          <div>
            <p className={`font-black text-base ${isGuest ? "text-slate-600" : "text-white"}`}>
              {isGuest ? "Guest User" : currentUser?.name || "User"}
            </p>
            <p className={`text-xs mt-0.5 ${isGuest ? "text-slate-400" : "text-white/60"}`}>
              {isGuest ? "Limited access — sign in to unlock all features" : currentUser?.email}
            </p>
          </div>
        </div>
        {!isGuest && (
          <button onClick={onLogout}
            className="mt-4 w-full py-2.5 bg-white/10 hover:bg-white/20 border border-white/20 text-white text-xs font-black rounded-2xl uppercase tracking-widest transition-all">
            Sign Out
          </button>
        )}
      </div>

      <h2 className="text-xl font-black text-gray-900 mb-4">Preferences</h2>
      <div className="space-y-3">
        {toggles.map(t => (
          <div key={t.id} className={`bg-white rounded-3xl p-5 border border-slate-100 shadow-sm flex items-center justify-between transition-all ${isGuest ? "opacity-50 pointer-events-none" : ""}`}>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center text-2xl">{t.emoji}</div>
              <div>
                <p className="font-black text-gray-900 text-sm">{t.label}</p>
                <p className="text-gray-400 text-xs">{t.desc}</p>
              </div>
            </div>
            <button
              onClick={() => !isGuest && onUpdate({ ...preferences, [t.id]: !preferences[t.id] })}
              className={`w-14 h-8 rounded-full transition-all flex items-center px-1 ${preferences[t.id] ? "bg-emerald-500 justify-end" : "bg-slate-200 justify-start"}`}>
              <div className="w-6 h-6 bg-white rounded-full shadow-md" />
            </button>
          </div>
        ))}
      </div>
      {isGuest && <p className="text-center text-slate-400 text-xs mt-4 italic">Sign in to save preferences</p>}
    </div>
  );
};

// ── MAIN APP ───────────────────────────────────────────────────────────────────
export default function Home() {
  const { i18n } = useTranslation();
  const [appPhase, setAppPhase] = useState("splash"); // splash→welcome→app
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(undefined); // undefined = not yet resolved from localStorage
  const [isGuest, setIsGuest] = useState(false);

  const [activeTab, setActiveTab] = useState("dashboard");
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [showReveal, setShowReveal] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState("");
  const [refreshTick, setRefreshTick] = useState(0);
  const [preferences, setPreferences] = useState({ vegan: false, no_sugar: false, low_sodium: false, gluten_free: false });
  const [mounted, setMounted] = useState(false);
  const [scanMode, setScanMode] = useState("barcode"); // "barcode" | "label"

  useEffect(() => { setMounted(true); }, []);

  // Restore auth on page load — runs after mount
  useEffect(() => {
    if (!mounted) return;
    const savedToken = localStorage.getItem("ns_token");
    const savedUser = localStorage.getItem("ns_user");
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setCurrentUser(JSON.parse(savedUser));
        setIsGuest(false);
        setAppPhase("app"); // skip splash+welcome if already logged in
      } catch { /* ignore parse err */ }
    } else {
      setToken(null); // explicitly resolved: no saved token
    }
    // Trigger history refresh once auth is resolved
    setRefreshTick(t => t + 1);
  }, [mounted]);

  // Camera — MUST be declared before any early return to satisfy Rules of Hooks
  useEffect(() => {
    if (!mounted) return; // guard inside the hook, not an early return from component
    let stream;
    (async () => {
      if (activeTab !== "scanner" || capturedImage) return;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        if (videoRef.current) videoRef.current.srcObject = stream;
      } catch { /* camera denied */ }
    })();
    return () => { if (stream) stream.getTracks().forEach(t => t.stop()); };
  }, [activeTab, capturedImage, mounted]);

  // ── Early return AFTER all hooks ────────────────────────────────────────────
  if (!mounted) return (
    <div className="bg-slate-100 min-h-screen flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  // ── Event handlers (not hooks, safe after early return) ─────────────────────
  const handleAuth = (user, tok) => {
    setCurrentUser(user);
    setToken(tok);
    setIsGuest(false);
    setAppPhase("app");
  };
  const handleGuest = () => { setIsGuest(true); setAppPhase("app"); };
  const handleLogout = () => {
    localStorage.removeItem("ns_token");
    localStorage.removeItem("ns_user");
    setCurrentUser(null); setToken(null); setIsGuest(false);
    setAppPhase("welcome");
  };

  const takePhoto = () => {
    const video = videoRef.current, canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    setCapturedImage(canvas.toDataURL("image/jpeg", 0.9));
    video.srcObject?.getTracks().forEach(t => t.stop());
  };

  const handleFileUpload = e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = () => setCapturedImage(reader.result);
    reader.readAsDataURL(file);
  };

  // Core scan logic — barcode mode: /api/scan (XGBoost+DB, no RAG)
  //                   label mode:   /api/scan-label (OCR + RAG)
  const handleAnalyzeClick = async () => {
    if (!capturedImage) return;
    setIsAnalyzing(true);

    const isBarcodeMode = scanMode === "barcode";
    setAnalysisStatus(isBarcodeMode ? "Decoding barcode…" : "Initialising RAG label analysis…");

    const timers = isBarcodeMode ? [
      setTimeout(() => setAnalysisStatus("Querying nutrition database…"), 2000),
      setTimeout(() => setAnalysisStatus("Scoring with health model…"), 4000),
    ] : [
      setTimeout(() => setAnalysisStatus("Running OCR on label image…"), 2000),
      setTimeout(() => setAnalysisStatus("Identifying additives…"), 5000),
      setTimeout(() => setAnalysisStatus("RAG intelligence scoring…"), 9000),
    ];

    try {
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      let res, data;

      if (isBarcodeMode) {
        // ── Barcode path: fast, XGBoost scored, no RAG ──────────────────
        res = await fetch(`${API}/api/scan`, {
          method: "POST",
          headers,
          body: JSON.stringify({ image: capturedImage }),
        });
        data = await res.json();

        if (!res.ok || data.status === "error" || data.status === "partial") {
          const msg =
            data.message === "barcode_not_found"
              ? "No barcode detected. Make sure the barcode is clear and well-lit, or switch to 'Scan Label' mode."
              : data.message === "nutrition_unavailable"
                ? `Barcode read (${data.gtin}) but product not in database. Try 'Scan Label' mode for this product.`
                : data.error || "Barcode scan failed.";
          throw new Error(msg);
        }
      } else {
        // ── Label path: OCR + RAG pipeline ─────────────────────────────
        const productName = prompt("Enter the product name (helps the RAG engine):") || "Unknown Product";
        res = await fetch(`${API}/api/scan-label`, {
          method: "POST",
          headers,
          body: JSON.stringify({ image: capturedImage, product_name: productName }),
        });
        data = await res.json();
        if (!res.ok && !data.health_score) throw new Error(data.error || "Label analysis failed.");
      }

      setAnalysisResult(data);
      setShowReveal(true);
      // refreshTick will increment in handleRevealDone after animation
    } catch (err) {
      alert(err.message || "Failed to connect to the backend.");
    } finally {
      setIsAnalyzing(false);
      setAnalysisStatus("");
      timers.forEach(clearTimeout);
    }
  };

  const handleRevealDone = () => {
    setShowReveal(false);
    setActiveTab("results");
    // ✅ Refresh history + trends AFTER reveal animation completes
    // (scan is guaranteed saved to DB by now)
    setRefreshTick(t => t + 1);
  };

  const updatePreferences = newPrefs => {
    setPreferences(newPrefs);
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    fetch(`${API}/preferences`, {
      method: "POST",
      headers,
      body: JSON.stringify(newPrefs),
    }).catch(() => { });
  };

  return (
    <div className="bg-slate-100 min-h-screen overflow-x-hidden">
      {/* Splash */}
      {appPhase === "splash" && <SplashScreen onDone={() => setAppPhase("welcome")} />}
      {/* Auth / Welcome */}
      {appPhase === "welcome" && <WelcomeScreen onAuth={handleAuth} onGuest={handleGuest} />}

      <div className="max-wrapper relative min-h-screen flex flex-col">
        {showReveal && analysisResult && <ScoreReveal result={analysisResult} onDone={handleRevealDone} />}

        {/* TOP BAR */}
        <header className="sticky top-0 z-40 w-full flex justify-between items-center px-5 py-3.5 bg-white/90 backdrop-blur-md border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-[#3a3f85] to-[#6c63ff] flex items-center justify-center shadow-lg">
              <svg viewBox="0 0 32 32" className="w-5 h-5">
                <rect x="3" y="6" width="1.5" height="20" rx="0.75" fill="white" />
                <rect x="6.5" y="4" width="1" height="24" rx="0.5" fill="white" opacity="0.8" />
                <rect x="9.5" y="6" width="2" height="20" rx="1" fill="white" />
                <rect x="13.5" y="4" width="1" height="24" rx="0.5" fill="white" opacity="0.8" />
                <rect x="16" y="6" width="2.5" height="20" rx="1" fill="white" />
                <rect x="20.5" y="4" width="1" height="24" rx="0.5" fill="white" opacity="0.8" />
                <rect x="23" y="6" width="1.5" height="20" rx="0.75" fill="white" />
                <rect x="26.5" y="4" width="1" height="24" rx="0.5" fill="white" opacity="0.8" />
                <rect x="29" y="6" width="1.5" height="20" rx="0.75" fill="white" />
                <rect x="2" y="14.5" width="28" height="3" rx="1.5" fill="#00f5c4" opacity="0.9" />
              </svg>
            </div>
            <div>
              <p className="font-black text-gray-900 text-sm leading-none">NutriScanner</p>
              <select onChange={e => i18n.changeLanguage(e.target.value)} value={i18n.language}
                className="text-[10px] font-bold bg-transparent border-none outline-none text-[#3a3f85] cursor-pointer mt-0.5">
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
                <option value="mr">मराठी</option>
              </select>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isGuest && (
              <button onClick={() => setAppPhase("welcome")}
                className="text-[10px] font-black bg-[#3a3f85] text-white px-3 py-1.5 rounded-xl uppercase tracking-wide">
                Sign In
              </button>
            )}
            {currentUser && (
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#3a3f85] to-[#6c63ff] flex items-center justify-center text-white font-black text-sm shadow-md">
                {currentUser.name?.[0]?.toUpperCase() || "U"}
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 flex flex-col">
          {/* DASHBOARD — always mounted, hidden when inactive */}
          <div className={activeTab === "dashboard" ? "px-5 py-5 pb-28 overflow-y-auto" : "hidden"}>
            <div className="mb-6 flex items-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-slate-900 flex items-center justify-center shadow-xl text-3xl">👋</div>
              <div>
                <p className="text-xl font-black text-gray-900">
                  {isGuest ? "Hello, Guest!" : `Hello, ${currentUser?.name?.split(" ")[0] || "there"}!`}
                </p>
                <p className="text-slate-400 text-sm mt-0.5">
                  {isGuest ? "Scan mode active" : "Track your food health"}
                </p>
              </div>
            </div>

            <button onClick={() => setActiveTab("scanner")}
              className="w-full bg-gradient-to-r from-[#3a3f85] to-[#6610f2] rounded-3xl p-6 flex justify-between items-center cursor-pointer active:scale-[0.98] transition-all shadow-xl shadow-blue-500/15 mb-6 border border-white/10 group">
              <div>
                <p className="text-white font-black text-xl leading-tight group-hover:translate-x-1 transition-transform">Scan Now</p>
                <p className="text-white/60 text-sm mt-1">Point camera at barcode or label</p>
              </div>
              <div className="w-14 h-14 bg-white/15 backdrop-blur-md rounded-2xl flex items-center justify-center border border-white/20 group-hover:rotate-6 transition-transform text-3xl">📸</div>
            </button>

            <div className="flex justify-between items-center mb-3 px-1">
              <p className="font-black text-slate-900 text-xs tracking-widest uppercase">Recent Scans</p>
              {!isGuest && refreshTick > 0 && (
                <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">✓ Updated</span>
              )}
            </div>
            <HistoryFeed refreshTick={refreshTick} token={token} isGuest={isGuest} />
          </div>

          {/* TRENDS — always mounted, hidden when inactive */}
          <div className={activeTab === "trends" ? "" : "hidden"}>
            <TrendsView refreshTick={refreshTick} token={token} isGuest={isGuest} />
          </div>

          {/* SCANNER */}
          {activeTab === "scanner" && (
            <div className="flex-1 flex flex-col pb-28 px-5 pt-5">
              <p className="font-black text-slate-900 text-xl tracking-tight mb-1">Scan Product</p>

              {/* ── Mode selector pill ── */}
              <div className="flex gap-2 mb-5 bg-slate-100 rounded-2xl p-1">
                <button
                  id="mode-barcode"
                  onClick={() => { setScanMode("barcode"); setCapturedImage(null); }}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${scanMode === "barcode"
                    ? "bg-slate-900 text-white shadow-lg"
                    : "text-slate-400 hover:text-slate-600"
                    }`}>
                  <span>📦</span> Scan Barcode
                </button>
                <button
                  id="mode-label"
                  onClick={() => { setScanMode("label"); setCapturedImage(null); }}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${scanMode === "label"
                    ? "bg-gradient-to-r from-[#3a3f85] to-[#6c63ff] text-white shadow-lg"
                    : "text-slate-400 hover:text-slate-600"
                    }`}>
                  <span>🔬</span> Scan Label
                </button>
              </div>

              {/* Mode hint */}
              <p className="text-slate-400 text-[10px] font-bold mb-4 text-center uppercase tracking-widest">
                {scanMode === "barcode"
                  ? "📦 Point at the barcode — fast & accurate via health model"
                  : "🔬 Photo the nutrition / ingredient label — RAG AI deep analysis"}
              </p>

              <div className="flex-1 flex items-center justify-center">
                <div className="relative w-full aspect-[9/12] bg-slate-900 rounded-[36px] shadow-2xl p-1.5 ring-8 ring-slate-50">
                  <canvas ref={canvasRef} className="hidden" />
                  <div className="relative h-full w-full bg-slate-800 rounded-[30px] overflow-hidden flex items-center justify-center border border-white/10">
                    {!capturedImage
                      ? <video ref={videoRef} autoPlay playsInline muted className="object-cover w-full h-full" />
                      : <img src={capturedImage} alt="Captured" className="object-cover w-full h-full" />
                    }
                    {/* Scan overlay line */}
                    {!capturedImage && (
                      <div className="absolute inset-0 pointer-events-none">
                        <div className="scanner-line" />
                        <div className="absolute inset-8 border-2 border-dashed border-white/20 rounded-3xl" />
                      </div>
                    )}
                    {/* Bottom buttons */}
                    <div className="absolute bottom-6 left-0 right-0 flex justify-center gap-4 px-8 z-20">
                      {capturedImage ? (
                        <button onClick={() => setCapturedImage(null)}
                          className="flex-1 h-12 bg-white/20 backdrop-blur border border-white/40 text-white text-xs font-black rounded-2xl active:scale-95 transition-all">
                          ↺ Retake
                        </button>
                      ) : (
                        <button onClick={takePhoto}
                          className="w-20 h-20 bg-white rounded-full shadow-2xl active:scale-90 transition-all flex items-center justify-center border-8 border-white/20">
                          <div className="w-12 h-12 rounded-full border-4 border-slate-900" />
                        </button>
                      )}
                    </div>
                    {!capturedImage && (
                      <button onClick={() => fileInputRef.current?.click()}
                        className="absolute top-5 right-5 w-11 h-11 bg-white/10 backdrop-blur border border-white/20 rounded-2xl flex items-center justify-center text-white text-lg active:scale-90 transition-all">
                        📁
                      </button>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                {isAnalyzing ? (
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-full h-14 bg-slate-900 text-white rounded-2xl font-black flex items-center justify-center gap-3">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-emerald-400 rounded-full animate-spin" />
                      ANALYZING…
                    </div>
                    {analysisStatus && <p className="text-[10px] text-slate-500 font-bold animate-pulse uppercase tracking-widest">{analysisStatus}</p>}
                  </div>
                ) : capturedImage ? (
                  <button onClick={handleAnalyzeClick}
                    className={`w-full h-14 text-white rounded-2xl font-black shadow-lg active:scale-98 transition-all uppercase tracking-widest ${scanMode === "barcode"
                      ? "bg-slate-900 shadow-slate-500/20"
                      : "bg-gradient-to-r from-[#3a3f85] to-[#6c63ff] shadow-blue-500/20"
                      }`}>
                    {scanMode === "barcode" ? "Analyse Barcode 📦" : "Analyse with RAG AI 🔬"}
                  </button>
                ) : (
                  <div className="w-full h-14 bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl flex items-center justify-center text-slate-400 text-[10px] font-black uppercase tracking-widest">
                    Point camera at product
                  </div>
                )}
              </div>
            </div>
          )}

          {/* RESULTS */}
          {activeTab === "results" && analysisResult && (() => {
            const key = analysisResult.health_score || "YELLOW";
            const cfg = scoreConfig[key] || scoreConfig.YELLOW;
            return (
              <div className="px-5 py-5 pb-28 overflow-y-auto animate-fade-in">
                <div className={`rounded-[28px] p-7 text-white ${cfg.bg} mb-6 relative overflow-hidden shadow-2xl`}>
                  <div className="relative z-10">
                    <div className="flex justify-between items-start mb-5">
                      <span className="bg-white/20 backdrop-blur px-3 py-1.5 rounded-full text-[10px] font-black tracking-widest uppercase border border-white/20">Health Score</span>
                      <span className="text-4xl">{cfg.emoji}</span>
                    </div>
                    <h1 className="text-3xl font-black leading-tight uppercase tracking-tighter">
                      {analysisResult.brand && <span className="text-white/50 block text-[10px] tracking-widest mb-1 font-black">{analysisResult.brand.toUpperCase()}</span>}
                      {analysisResult.product_name || "Unknown Product"}
                    </h1>
                    <p className="text-white/70 font-black uppercase tracking-[0.2em] text-[10px] mt-1">{cfg.label}</p>
                    <div className="mt-6 flex items-baseline gap-1.5">
                      <span className="text-6xl font-black">{analysisResult.score_value ?? "–"}</span>
                      <span className="text-xl font-bold text-white/40">/10</span>
                    </div>
                  </div>
                  <div className="absolute -bottom-8 -right-8 w-40 h-40 bg-white/10 rounded-full blur-3xl" />
                </div>

                <NutritionCard nutrition={analysisResult.nutrition} />

                {/* RAG insights */}
                {analysisResult.rag_analysis && (
                  <div className="bg-gradient-to-br from-[#3a3f85]/5 to-[#6c63ff]/5 border border-[#6c63ff]/20 rounded-3xl p-5 mb-6">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-lg">🧠</span>
                      <p className="font-black text-[#3a3f85] text-xs uppercase tracking-widest">RAG Intelligence Analysis</p>
                    </div>
                    {analysisResult.rag_analysis.warnings?.length > 0 && (
                      <div className="space-y-2 mb-3">
                        {analysisResult.rag_analysis.warnings.map((w, i) => (
                          <div key={i} className="bg-amber-50 border border-amber-100 rounded-2xl px-3 py-2 text-xs font-semibold text-amber-700">
                            ⚠ {w}
                          </div>
                        ))}
                      </div>
                    )}
                    {analysisResult.rag_analysis.fssai_compliance === false && (
                      <div className="bg-red-50 border border-red-100 rounded-2xl px-3 py-2 text-xs font-bold text-red-700">
                        🚨 {analysisResult.rag_analysis.compliance_message}
                      </div>
                    )}
                    {analysisResult.rag_analysis.allergens_detected?.length > 0 && (
                      <p className="text-xs text-slate-600 mt-2 font-medium">
                        🥜 Allergens: {analysisResult.rag_analysis.allergens_detected.join(", ")}
                      </p>
                    )}
                  </div>
                )}

                {/* Additives */}
                {analysisResult.additives?.length > 0 && (
                  <div className="mb-6">
                    <p className="font-black text-slate-900 text-xs tracking-widest uppercase mb-3 px-1">Ingredient Flags</p>
                    <div className="space-y-3">
                      {analysisResult.additives.map((a, i) => (
                        <div key={i} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex justify-between items-start">
                          <div>
                            <p className="font-black text-slate-900 text-sm">{a.name}</p>
                            <p className="text-slate-400 text-xs mt-0.5">{a.reason}</p>
                          </div>
                          <span className={`text-[9px] font-black px-2 py-0.5 rounded-full ml-3 flex-shrink-0 ${a.risk_level === "RED" ? "bg-red-100 text-red-700" : a.risk_level === "ORANGE" ? "bg-orange-100 text-orange-700" : "bg-yellow-100 text-yellow-700"}`}>
                            {a.risk_level}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* XAI Insights */}
                {analysisResult.xai && analysisResult.xai.shap_impacts && Object.keys(analysisResult.xai.shap_impacts).length > 0 && (
                  <div className="mb-6">
                    <p className="font-black text-slate-900 text-xs tracking-widest uppercase mb-3 px-1">AI Impact Analysis</p>
                    <div className="space-y-3">
                      {Object.entries(analysisResult.xai.shap_impacts).map(([feature, impact], i) => (
                        <div key={i} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex justify-between items-center">
                          <p className="font-black text-slate-900 text-sm">{feature}</p>
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] font-black ${impact < 0 ? "text-red-500" : "text-emerald-500"}`}>
                              {impact > 0 ? "+" : ""}{impact.toFixed(1)}
                            </span>
                            <div className={`h-1.5 rounded-full ${impact < 0 ? "bg-red-400" : "bg-emerald-400"}`} style={{ width: `${Math.min(50, Math.abs(impact) * 15)}px` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Healthy alternative */}
                {analysisResult.healthy_alternative && (
                  <div className="bg-emerald-50 rounded-[28px] p-6 border border-emerald-100 mb-6 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">💡</span>
                      <p className="text-emerald-600 font-black text-[10px] uppercase tracking-widest">Better Alternative</p>
                    </div>
                    <p className="text-slate-900 font-black text-lg leading-snug">{analysisResult.healthy_alternative}</p>
                  </div>
                )}

                <button onClick={() => setActiveTab("scanner")}
                  className="w-full h-14 bg-slate-900 text-white rounded-2xl font-black uppercase tracking-widest">
                  Scan Another Product 📸
                </button>
              </div>
            );
          })()}

          {/* PREFS */}
          {activeTab === "profile" && (
            <SettingsView
              preferences={preferences}
              onUpdate={updatePreferences}
              currentUser={currentUser}
              isGuest={isGuest}
              onLogout={handleLogout}
            />
          )}
        </main>

        {/* BOTTOM NAV */}
        <nav className="fixed bottom-0 left-0 right-0 z-40 flex justify-center pointer-events-none">
          <div className="w-full max-w-md bg-white/90 backdrop-blur-2xl border-t border-slate-100 px-6 py-4 flex justify-between items-center pointer-events-auto rounded-t-[28px] shadow-[0_-10px_40px_rgba(0,0,0,0.06)]">
            {[
              { id: "dashboard", icon: "🏠", label: "Home" },
              { id: "trends", icon: "📊", label: "Trends" },
              { id: "results", icon: "🔍", label: "Result" },
              { id: "profile", icon: "⚙️", label: "Profile" },
            ].map(tab => (
              <button key={tab.id} onClick={() => {
                setActiveTab(tab.id);
                // Re-fetch history when going back to home or trends
                if (tab.id === "dashboard" || tab.id === "trends") {
                  setRefreshTick(t => t + 1);
                }
              }}
                className={`flex flex-col items-center gap-1 transition-all ${activeTab === tab.id ? "text-[#3a3f85] scale-110" : "text-slate-300"}`}>
                <div className="text-2xl">{tab.icon}</div>
                <span className="text-[9px] font-black uppercase tracking-widest">{tab.label}</span>
              </button>
            ))}
          </div>
          {/* Central scan fab */}
          <button
            onClick={() => setActiveTab("scanner")}
            className="absolute bottom-10 w-18 h-18 w-[72px] h-[72px] bg-gradient-to-br from-[#3a3f85] to-[#6c63ff] rounded-3xl flex items-center justify-center text-white shadow-[0_15px_30px_rgba(58,63,133,0.35)] border-4 border-white active:scale-90 transition-all pointer-events-auto z-50">
            <span className="text-3xl">📸</span>
          </button>
        </nav>
      </div>

      <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept="image/*" />
    </div>
  );
}

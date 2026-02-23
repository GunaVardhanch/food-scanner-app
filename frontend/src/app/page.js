"use client";

import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import '../i18n';

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

// --- ICONS ---
const UserIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-gray-700">
    <path fillRule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clipRule="evenodd" />
  </svg>
);

const UserIconSmall = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-gray-700">
    <path fillRule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clipRule="evenodd" />
  </svg>
);

// --- CONFETTI COMPONENT ---
const Confetti = ({ active }) => {
  const canvasRef = useRef(null);
  useEffect(() => {
    if (!active) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    const pieces = Array.from({ length: 120 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height - canvas.height,
      r: Math.random() * 8 + 4,
      color: ['#00c55e', '#ffd624', '#3a3f85', '#ff6b6b', '#00d4ff', '#ff9f43'][Math.floor(Math.random() * 6)],
      speed: Math.random() * 4 + 2,
      swing: Math.random() * 3 - 1.5,
      angle: Math.random() * 360,
      spin: Math.random() * 5 - 2.5,
    }));
    let frame;
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      pieces.forEach(p => {
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.angle * Math.PI / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.r / 2, -p.r / 2, p.r, p.r * 2);
        ctx.restore();
        p.y += p.speed;
        p.x += p.swing;
        p.angle += p.spin;
        if (p.y > canvas.height) { p.y = -20; p.x = Math.random() * canvas.width; }
      });
      frame = requestAnimationFrame(draw);
    };
    draw();
    const timeout = setTimeout(() => cancelAnimationFrame(frame), 4000);
    return () => { cancelAnimationFrame(frame); clearTimeout(timeout); };
  }, [active]);

  if (!active) return null;
  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none z-50" />;
};

// --- SCORE REVEAL COMPONENT ---
const ScoreReveal = ({ score, specificScore, onDone }) => {
  const { t } = useTranslation();
  const [phase, setPhase] = useState('counting'); // counting → flashing → done
  const [displayNum, setDisplayNum] = useState(0);

  const scoreConfig = {
    RED: { label: 'RED — HARMFUL', color: 'from-red-500 to-red-700', glow: 'score-glow-red', emoji: '🚨', textColor: 'text-red-100' },
    YELLOW: { label: 'YELLOW — MODERATE', color: 'from-yellow-400 to-orange-500', glow: 'score-glow-yellow', emoji: '⚠️', textColor: 'text-yellow-900' },
    GREEN: { label: 'GREEN — HEALTHY', color: 'from-green-400 to-emerald-600', glow: 'score-glow-green', emoji: '✅', textColor: 'text-green-50' },
  };
  const cfg = scoreConfig[score] || scoreConfig['YELLOW'];
  const finalNum = specificScore !== undefined ? specificScore : (score === 'RED' ? 2 : score === 'GREEN' ? 9 : 5);

  useEffect(() => {
    let count = 0;
    const interval = setInterval(() => {
      count++;
      // Randomly cycle numbers during the 'counting' phase
      setDisplayNum(Math.floor(Math.random() * 10));
      if (count > 25) {
        clearInterval(interval);
        setDisplayNum(finalNum);
        setPhase('flashing');
        setTimeout(() => { setPhase('done'); onDone(); }, 1500);
      }
    }, 60);
    return () => clearInterval(interval);
  }, [finalNum]);

  return (
    <div className="fixed inset-0 bg-slate-950/90 backdrop-blur-xl flex flex-col items-center justify-center z-50">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full blur-[120px] opacity-20 ${cfg.color}`}></div>
      </div>
      <p className="text-white/40 font-black tracking-widest uppercase text-[10px] mb-8 animate-pulse relative z-10">Neural engine analyzing...</p>
      <div className={`w-64 h-64 rounded-full bg-gradient-to-br ${cfg.color} ${cfg.glow} flex flex-col items-center justify-center
        reveal-animation transition-all duration-700 relative z-10 border-4 border-white/20 shadow-2xl`}>
        <span className="text-9xl font-black text-white drop-shadow-2xl">{displayNum}</span>
        <span className="text-white/70 text-[10px] font-black tracking-widest uppercase mt-1">{t('health_score')}</span>
      </div>
      {phase === 'flashing' && (
        <div className="mt-10 text-center relative z-10 animate-reveal-pop">
          <span className="text-5xl">{cfg.emoji}</span>
          <p className="text-3xl font-black mt-4 text-white uppercase tracking-tight">{cfg.label}</p>
        </div>
      )}
    </div>
  );
};

// --- ADDITIVE CARD COMPONENT ---
const AdditiveCard = ({ additive, index }) => {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), index * 150);
    return () => clearTimeout(t);
  }, [index]);

  const riskColors = {
    RED: 'bg-red-500 text-white shadow-red-200',
    ORANGE: 'bg-orange-400 text-white shadow-orange-200',
    YELLOW: 'bg-yellow-400 text-gray-900 shadow-yellow-100',
  };

  const riskBadge = {
    RED: 'bg-red-100 text-red-700',
    ORANGE: 'bg-orange-100 text-orange-700',
    YELLOW: 'bg-yellow-100 text-yellow-700',
  };

  const risk = additive.risk_level || 'YELLOW';

  return (
    <div className={`${visible ? 'premium-card-entry' : 'opacity-0'}`}>
      <div className="glass-morphism rounded-3xl p-5 shadow-sm flex gap-4 items-start group hover:shadow-md transition-all duration-300 border-white/50">
        <div className={`w-12 h-12 rounded-2xl ${riskColors[risk]} flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform`}>
          <span className="text-xl">{risk === 'RED' ? '🚫' : risk === 'ORANGE' ? '⚠️' : '🔍'}</span>
        </div>
        <div className="flex-1">
          <div className="flex justify-between items-start mb-1">
            <p className="font-black text-slate-900 text-sm tracking-wide">{additive.name}</p>
            <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase ${riskBadge[risk]}`}>{risk}</span>
          </div>
          <p className="text-slate-500 text-xs leading-relaxed font-medium">{additive.reason}</p>
        </div>
      </div>
    </div>
  );
};


// --- XAI EXPLANATION COMPONENT ---
const XAIExplanation = ({ xaiData, imageUrl }) => {
  const { t } = useTranslation();
  const [showHeatmap, setShowHeatmap] = useState(false);

  if (!xaiData) return null;

  const impacts = xaiData.shap_impacts || {};

  return (
    <div className="bg-slate-900 rounded-3xl p-6 text-white mb-6 border border-slate-700 shadow-2xl animate-fade-in relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full translate-x-10 -translate-y-10"></div>

      <div className="flex justify-between items-center mb-6 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">📊</div>
          <p className="font-black text-sm uppercase tracking-widest">Interpretability Layer</p>
        </div>
        <div className="flex gap-2">
          <span className="bg-white/5 border border-white/10 px-2 py-1 rounded-md text-[9px] font-black text-slate-400 uppercase">XGBoost</span>
          <span className="bg-white/5 border border-white/10 px-2 py-1 rounded-md text-[9px] font-black text-slate-400 uppercase">SHAP</span>
        </div>
      </div>

      {/* SHAP IMPACTS */}
      <div className="bg-white/5 rounded-2xl p-4 mb-6 relative z-10 border border-white/5">
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Feature Impact Analysis</p>
        <div className="space-y-5">
          {Object.entries(impacts).map(([feature, impact], i) => (
            <div key={i} className="relative">
              <div className="flex justify-between items-end mb-1.5">
                <span className="text-[11px] font-bold text-slate-300">{feature}</span>
                <span className={`text-[10px] font-black font-mono ${impact < 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {impact > 0 ? '+' : ''}{impact.toFixed(1)}
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800/50 rounded-full overflow-hidden flex">
                {/* Zero point centered logic */}
                <div className="flex-1 flex justify-end">
                  {impact < 0 && (
                    <div
                      className="h-full bg-gradient-to-l from-rose-500 to-rose-400 rounded-l-full animate-grow-left"
                      style={{ width: `${Math.min(Math.abs(impact) * 20, 100)}%` }}
                    ></div>
                  )}
                </div>
                <div className="w-[1px] h-full bg-white/20 z-10"></div>
                <div className="flex-1">
                  {impact > 0 && (
                    <div
                      className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-r-full animate-grow-right"
                      style={{ width: `${Math.min(impact * 20, 100)}%` }}
                    ></div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* GRAD-CAM TOGGLE (Visualizing where the model looked) */}
      <div className="relative z-10">
        <button
          onClick={() => setShowHeatmap(!showHeatmap)}
          className="w-full py-3 bg-white/5 border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
        >
          {showHeatmap ? '👁️ Hide Model Focus' : '🎯 View Model Focus (Grad-CAM)'}
        </button>

        {showHeatmap && (
          <div className="mt-4 rounded-2xl overflow-hidden relative aspect-video border border-white/10 animate-fade-in">
            <img src={imageUrl || "https://via.placeholder.com/400x200?text=Heatmap+Image"} className="w-full h-full object-cover grayscale opacity-40" alt="Heatmap base" />
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/40 via-yellow-500/40 to-red-500/40 mix-blend-overlay"></div>
            <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
              <div className="w-32 h-32 rounded-full border-2 border-dashed border-white/40 animate-ping absolute"></div>
              <p className="text-[10px] font-black uppercase tracking-tighter text-white drop-shadow-lg">Detection Region: Nutrition Table</p>
              <p className="text-[9px] text-white/60 mt-1 italic">Confident: 98.4%</p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-8 pt-6 border-t border-white/5 flex justify-between items-center relative z-10">
        <div className="flex flex-col">
          <p className="text-[9px] font-bold text-slate-500 uppercase tracking-tighter">Model Confidence</p>
          <div className="flex gap-1 mt-1">
            {[1, 2, 3, 4, 5].map(s => <div key={s} className={`w-3 h-1 rounded-full ${s <= 4 ? 'bg-emerald-500' : 'bg-slate-700'}`}></div>)}
          </div>
        </div>
        <p className="text-[10px] text-slate-400 font-medium">
          SHAP-Explainable v2.1
        </p>
      </div>
    </div>
  );
};

// --- NUTRITION SUMMARY COMPONENT ---
const NutritionSummary = ({ nutrition }) => {
  if (!nutrition) return null;
  const items = [
    { label: 'CALORIES', value: nutrition.calories || '--', color: 'text-slate-900' },
    { label: 'PROTEIN', value: nutrition.protein || '--', color: 'text-emerald-600' },
    { label: 'FAT', value: nutrition.total_fat || '--', color: 'text-orange-500' },
    { label: 'SUGAR', value: nutrition.sugar || '--', color: 'text-red-500' },
  ];

  return (
    <div className="grid grid-cols-4 gap-2 mb-6">
      {items.map((item, i) => (
        <div key={i} className="bg-white rounded-xl p-2 border border-slate-100 shadow-sm text-center">
          <p className="text-[9px] font-black text-slate-400 mb-0.5">{item.label}</p>
          <p className={`text-xs font-black ${item.color}`}>{item.value}</p>
        </div>
      ))}
    </div>
  );
};

// --- HISTORY FEED COMPONENT ---
const HistoryFeed = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/history`)
      .then(res => res.json())
      .then(data => { setHistory(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-10 text-center animate-pulse text-gray-400 font-bold uppercase tracking-widest text-xs">Loading History...</div>;
  if (history.length === 0) return (
    <div className="bg-white rounded-3xl p-8 text-center border-2 border-dashed border-slate-200">
      <p className="text-slate-400 text-sm font-semibold">No scans yet. Start capturing food labels!</p>
    </div>
  );

  return (
    <div className="space-y-3">
      {history.map((item, i) => {
        const scoreColors = {
          RED: 'bg-red-500',
          YELLOW: 'bg-yellow-400',
          GREEN: 'bg-emerald-500'
        };
        return (
          <div key={i} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex items-center justify-between animate-fade-in group hover:border-slate-300 transition-all">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl ${scoreColors[item.health_score] || 'bg-slate-200'} flex items-center justify-center text-white text-xl shadow-md`}>
                {item.health_score === 'GREEN' ? '✅' : item.health_score === 'RED' ? '🚨' : '⚠️'}
              </div>
              <div>
                <p className="font-bold text-gray-900 text-sm uppercase tracking-tight">{item.product_name || "Unknown Product"}</p>
                <p className="text-gray-400 text-[10px] font-bold mt-0.5">{item.timestamp}</p>
              </div>
            </div>
            <div className="flex flex-col items-end">
              <span className="text-[10px] font-black text-slate-300 uppercase italic">NutriScore</span>
              <span className="text-xs font-black text-slate-800">{item.score_value || 0}/10</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// --- SETTINGS VIEW COMPONENT ---
const SettingsView = ({ preferences, onUpdate }) => {
  const { t } = useTranslation();
  const toggles = [
    { id: 'vegan', label: t('vegan'), emoji: '🌱', desc: 'Flag any animal-derived ingredients' },
    { id: 'no_sugar', label: t('no_sugar'), emoji: '🚫', desc: 'Strict alerts for sucrose and syrups' },
    { id: 'low_sodium', label: t('low_sodium'), emoji: '🧂', desc: 'Flag products with high salt content' },
    { id: 'gluten_free', label: t('gluten_free'), emoji: '🌾', desc: 'Alert for wheat, barley, or rye' },
  ];

  return (
    <div className="flex-1 px-5 pt-4 pb-24 overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-black text-gray-900 leading-tight">{t('preferences')}</h2>
      </div>

      <div className="space-y-4">
        {toggles.map((t) => (
          <div key={t.id} className="bg-white rounded-3xl p-5 border border-slate-100 shadow-sm flex items-center justify-between group transition-all hover:shadow-md">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-slate-50 flex items-center justify-center text-2xl shadow-inner">{t.emoji}</div>
              <div>
                <p className="font-black text-gray-900 text-base">{t.label}</p>
                <p className="text-gray-400 text-xs">{t.desc}</p>
              </div>
            </div>
            <button
              onClick={() => onUpdate({ ...preferences, [t.id]: !preferences[t.id] })}
              className={`w-14 h-8 rounded-full transition-all flex items-center px-1 ${preferences[t.id] ? 'bg-emerald-500 justify-end' : 'bg-slate-200 justify-start'}`}>
              <div className="w-6 h-6 bg-white rounded-full shadow-md"></div>
            </button>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-[#3a3f85]/5 rounded-3xl p-6 border border-[#3a3f85]/10">
        <p className="text-[#3a3f85] font-black text-sm uppercase tracking-widest mb-2">Pro Tip</p>
        <p className="text-slate-600 text-xs leading-relaxed">Setting dietary preferences directly affects your NutriScore. The AI will prioritize your health choices during every scan.</p>
      </div>
    </div>
  );
};

// --- TRENDS VIEW COMPONENT ---
const TrendsView = ({ analytics }) => {
  const { t } = useTranslation();
  if (!analytics) return <div className="p-10 text-center animate-pulse text-gray-400 font-bold uppercase tracking-widest text-xs">CALCULATING INSIGHTS...</div>;

  const maxScore = 10;
  const trend = analytics.history_trend || [];

  return (
    <div className="flex-1 px-5 pt-4 pb-24 overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-black text-gray-900 leading-tight">{t('analytics')}</h2>
      </div>

      {/* Average Score Card */}
      <div className="bg-gradient-to-br from-[#3a3f85] to-[#6c63ff] rounded-3xl p-6 text-white shadow-xl mb-6 relative overflow-hidden">
        <div className="relative z-10">
          <p className="text-white/70 font-black text-xs uppercase tracking-widest mb-1">Average Health Score</p>
          <div className="flex items-baseline gap-2">
            <span className="text-5xl font-black">{analytics.avg_score}</span>
            <span className="text-xl font-bold text-white/50">/10</span>
          </div>
          <p className="text-white/80 text-xs mt-4 font-medium leading-relaxed italic">
            "Your choices are improving! You're picking 15% cleaner products than last week."
          </p>
        </div>
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full translate-x-10 -translate-y-10"></div>
      </div>

      {/* Mini Bar Chart */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-sm mb-6">
        <p className="font-black text-gray-900 text-sm uppercase tracking-widest mb-4">Score History</p>
        <div className="flex items-end justify-between h-32 gap-1 px-2">
          {trend.length > 0 ? trend.map((score, i) => (
            <div key={i} className="flex-1 flex flex-col items-center group relative">
              <div
                className={`w-full rounded-t-lg transition-all duration-500 hover:opacity-80
                  ${score >= 8 ? 'bg-emerald-500' : score >= 5 ? 'bg-yellow-400' : 'bg-red-500'}`}
                style={{ height: `${(score / maxScore) * 100}%` }}
              >
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-[10px] px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                  {score}
                </div>
              </div>
            </div>
          )) : (
            <div className="w-full h-full flex items-center justify-center text-slate-300 text-xs italic">
              Need more scans for trend data...
            </div>
          )}
        </div>
        <div className="flex justify-between mt-2 text-[8px] font-black text-slate-300 uppercase tracking-widest">
          <span>Oldest</span>
          <span>Latest Scans</span>
        </div>
      </div>

      {/* Top Flagged Additives */}
      <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-sm">
        <p className="font-black text-gray-900 text-sm uppercase tracking-widest mb-4">Top Concerns</p>
        <div className="space-y-3">
          {analytics.top_additives && analytics.top_additives.length > 0 ? analytics.top_additives.map((item, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-2xl border border-slate-100">
              <div className="flex items-center gap-3">
                <span className="text-xl">{i === 0 ? '🚫' : '⚠️'}</span>
                <p className="font-bold text-gray-800 text-xs">{item.name}</p>
              </div>
              <span className="bg-white px-3 py-1 rounded-full border border-slate-200 text-[10px] font-black text-slate-500">
                {item.count} SCANS
              </span>
            </div>
          )) : (
            <p className="text-center text-slate-400 text-xs italic py-4">No recurring additives found yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

// --- MAIN APP ---
export default function Home() {
  const { t, i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState('dashboard');
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null); // Step 1: Ingredients
  const [nutritionImage, setNutritionImage] = useState(null); // Step 2: Nutrition
  const [scanStep, setScanStep] = useState(1); // 1: Ingredients, 2: Nutrition
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [showReveal, setShowReveal] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const workerRef = useRef(null);
  const [edgeOcrText, setEdgeOcrText] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const fileInputRef = useRef(null);
  const [preferences, setPreferences] = useState({
    vegan: false,
    no_sugar: false,
    low_sodium: false,
    gluten_free: false
  });

  // Init Worker
  useEffect(() => {
    workerRef.current = new Worker(new URL('../utils/ocrWorker.js', import.meta.url), { type: 'module' });
    workerRef.current.onmessage = (e) => {
      if (e.data.type === 'INFERENCE_RESULT') {
        setEdgeOcrText(e.data.text);
      }
    };
    workerRef.current.postMessage({ type: 'LOAD' });
    return () => workerRef.current.terminate();
  }, []);

  // Frame Capture Loop
  useEffect(() => {
    if (activeTab !== 'scanner' || (scanStep === 1 && capturedImage) || (scanStep === 2 && nutritionImage)) return;

    const interval = setInterval(() => {
      if (videoRef.current && canvasRef.current && workerRef.current) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        // Use small size for faster edge processing
        canvas.width = 224;
        canvas.height = 224;
        ctx.drawImage(video, 0, 0, 224, 224);

        const imageData = ctx.getImageData(0, 0, 224, 224);
        workerRef.current.postMessage({
          type: 'INFER',
          imageData: imageData.data.buffer // Send as transferable if possible
        }, [imageData.data.buffer]);
      }
    }, 500); // Process every 500ms

    return () => clearInterval(interval);
  }, [activeTab, scanStep, capturedImage, nutritionImage]);

  useEffect(() => {
    if (!searchQuery || searchQuery.length < 3) {
      setSuggestions([]);
      return;
    }
    const delayDebounceFn = setTimeout(() => {
      setIsSearching(true);
      fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(searchQuery)}`)
        .then(res => res.json())
        .then(data => {
          setSuggestions(data.products || []);
          setIsSearching(false);
        })
        .catch(() => setIsSearching(false));
    }, 500);
    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  useEffect(() => {
    if (activeTab === 'trends') {
      fetch(`${API_BASE_URL}/analytics`)
        .then(res => res.json())
        .then(data => setAnalytics(data))
        .catch(err => console.error("Analytics fetch error:", err));
    }
  }, [activeTab]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/preferences`)
      .then(res => res.json())
      .then(data => setPreferences(data))
      .catch(err => console.error("Pref fetch error:", err));
  }, []);

  const updatePreferences = (newPrefs) => {
    setPreferences(newPrefs);
    fetch(`${API_BASE_URL}/preferences`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newPrefs)
    });
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const dataUrl = reader.result;
        if (scanStep === 1) setCapturedImage(dataUrl);
        else setNutritionImage(dataUrl);
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerFileUpload = () => {
    if (fileInputRef.current) fileInputRef.current.click();
  };

  useEffect(() => {
    let stream;
    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        if (videoRef.current) { videoRef.current.srcObject = stream; }
      } catch (err) { alert("Could not access camera. Please grant permission."); }
    };
    if (activeTab === 'scanner') {
      if ((scanStep === 1 && !capturedImage) || (scanStep === 2 && !nutritionImage)) {
        startCamera();
      }
    }
    return () => { if (stream) stream.getTracks().forEach(t => t.stop()); };
  }, [activeTab, capturedImage, nutritionImage, scanStep]);

  const takePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 300;
      canvas.height = video.videoHeight || 300;
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg');

      if (scanStep === 1) {
        setCapturedImage(dataUrl);
      } else {
        setNutritionImage(dataUrl);
      }

      const stream = video.srcObject;
      if (stream) stream.getTracks().forEach(t => t.stop());
    }
  };

  const retakePhoto = () => {
    if (scanStep === 1) setCapturedImage(null);
    else setNutritionImage(null);
    setAnalysisResult(null);
  };

  const nextStep = () => setScanStep(2);
  const prevStep = () => setScanStep(1);

  const handleAnalyzeClick = async () => {
    if (!capturedImage) return;
    setIsAnalyzing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ingredients_image: capturedImage,
          nutrition_image: nutritionImage
        })
      });
      const data = await response.json();
      setAnalysisResult(data);
      setIsAnalyzing(false);
      setShowReveal(true);
    } catch (error) {
      alert("Failed to connect to the backend server.");
      setIsAnalyzing(false);
    }
  };

  const handleRevealDone = () => {
    setShowReveal(false);
    setActiveTab('results');
    if (analysisResult?.health_score === 'GREEN') {
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 4500);
    }
  };

  const scoreConfig = {
    RED: { bg: 'bg-gradient-to-br from-red-500 to-rose-700', label: 'HARMFUL', emoji: '🚨', shadow: 'shadow-red-200', badge: 'bg-red-100 text-red-700' },
    YELLOW: { bg: 'bg-gradient-to-br from-yellow-400 to-amber-500', label: 'MODERATE', emoji: '⚠️', shadow: 'shadow-yellow-200', badge: 'bg-yellow-100 text-yellow-800' },
    GREEN: { bg: 'bg-gradient-to-br from-emerald-400 to-green-600', label: 'HEALTHY', emoji: '✅', shadow: 'shadow-green-200', badge: 'bg-green-100 text-green-800' },
  };

  return (
    <div className="bg-slate-100 min-h-screen">
      <div className="max-wrapper overflow-x-hidden">
        {/* Score Reveal Overlay */}
        {showReveal && analysisResult && (
          <ScoreReveal score={analysisResult.health_score} specificScore={analysisResult.score_value} onDone={handleRevealDone} />
        )}

        {/* Confetti Canvas */}
        <Confetti active={showConfetti} />

        {/* TOP BAR */}
        <header className="sticky top-0 z-40 w-full flex justify-between items-center px-6 py-4 bg-white/80 backdrop-blur-md border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#3a3f85] to-[#6c63ff] flex items-center justify-center text-white font-black text-sm shadow-lg">FS</div>
            <div>
              <p className="font-black text-gray-900 text-sm leading-none tracking-tight">NutriScanner</p>
              <select
                onChange={(e) => i18n.changeLanguage(e.target.value)}
                value={i18n.language}
                className="text-[10px] font-bold bg-transparent border-none outline-none text-[#3a3f85] cursor-pointer mt-1"
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
                <option value="mr">मराठी</option>
              </select>
            </div>
          </div>
          <div className="p-1 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer">
            <UserIconSmall />
          </div>
        </header>

        <main className="flex-1 flex flex-col relative">
          {/* Transition wrapper for tabs */}
          <div className="flex-1 animate-fade-in">
            {/* ===== SCREEN 1: DASHBOARD ===== */}
            {activeTab === 'dashboard' && (
              <div className="px-6 py-6 pb-24">
                <div className="mb-8 flex gap-4 items-center animate-slide-up">
                  <div className="w-16 h-16 rounded-2xl bg-slate-900 flex items-center justify-center shadow-xl relative overflow-hidden">
                    <div className="w-6 h-6 bg-white/20 rounded-full absolute -top-1 -right-1"></div>
                    <div className="text-3xl">👋</div>
                  </div>
                  <div>
                    <p className="text-2xl font-black text-gray-900 leading-tight">{t('dashboard')}</p>
                    <p className="text-slate-400 text-sm font-medium mt-0.5">Welcome back, Guna!</p>
                  </div>
                </div>

                {/* Quick Scan CTA */}
                <div onClick={() => setActiveTab('scanner')} className="bg-gradient-to-r from-[#3a3f85] to-[#6610f2] rounded-3xl p-6 flex justify-between items-center cursor-pointer active:scale-[0.98] transition-all shadow-xl shadow-blue-500/10 mb-8 border border-white/10 group">
                  <div>
                    <p className="text-white font-black text-xl leading-tight group-hover:translate-x-1 transition-transform">{t('scan_now')}</p>
                    <p className="text-white/70 text-sm mt-1">{t('scanning')}</p>
                  </div>
                  <div className="w-14 h-14 bg-white/15 backdrop-blur-md rounded-2xl flex items-center justify-center border border-white/20 shadow-inner group-hover:rotate-6 transition-transform">
                    <span className="text-3xl">📸</span>
                  </div>
                </div>

                {/* Recent Scans Section */}
                <div className="mb-4">
                  <div className="flex justify-between items-end mb-4 px-1">
                    <p className="font-black text-slate-900 text-xs tracking-widest uppercase">{t('history')}</p>
                    <button className="text-[10px] font-black text-[#3a3f85] uppercase tracking-wider">See All</button>
                  </div>
                  <HistoryFeed />
                </div>
              </div>
            )}

            {/* ===== SCREEN 1.5: PROFILE/SETTINGS ===== */}
            {activeTab === 'profile' && (
              <SettingsView preferences={preferences} onUpdate={updatePreferences} />
            )}

            {/* ===== SCREEN 1.6: TRENDS ===== */}
            {activeTab === 'trends' && (
              <TrendsView analytics={analytics} />
            )}

            {/* ===== SCREEN 2: SCANNER ===== */}
            {activeTab === 'scanner' && (
              <div className="flex-1 flex flex-col pb-24 px-6 pt-6">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <p className="font-black text-slate-900 text-xl tracking-tight">
                      {scanStep === 1 ? 'Ingredient List' : 'Nutrition Facts'}
                    </p>
                    <p className="text-slate-400 text-xs font-bold mt-1">STEP {scanStep} OF 2</p>
                  </div>
                  <div className="flex gap-1.5">
                    <div className={`w-8 h-1.5 rounded-full transition-all duration-500 ${scanStep >= 1 ? 'bg-[#3a3f85]' : 'bg-slate-200'}`}></div>
                    <div className={`w-8 h-1.5 rounded-full transition-all duration-500 ${scanStep >= 2 ? 'bg-[#3a3f85]' : 'bg-slate-200'}`}></div>
                  </div>
                </div>

                <div className="flex-1 flex items-center justify-center">
                  <div className="relative w-full aspect-[9/12] bg-slate-900 rounded-[40px] shadow-2xl p-1.5 ring-8 ring-slate-50 overflow-hidden group">
                    <canvas ref={canvasRef} className="hidden"></canvas>
                    <div className="relative h-full w-full bg-slate-800 rounded-[34px] overflow-hidden flex items-center justify-center border border-white/10">
                      {scanStep === 1 ? (
                        !capturedImage ? (
                          <video ref={videoRef} autoPlay playsInline muted className="object-cover w-full h-full" />
                        ) : (
                          <img src={capturedImage} alt="Captured Ingredients" className="object-cover w-full h-full" />
                        )
                      ) : (
                        !nutritionImage ? (
                          <video ref={videoRef} autoPlay playsInline muted className="object-cover w-full h-full" />
                        ) : (
                          <img src={nutritionImage} alt="Captured Nutrition" className="object-cover w-full h-full" />
                        )
                      )}

                      {((scanStep === 1 && !capturedImage) || (scanStep === 2 && !nutritionImage)) && (
                        <>
                          <div className="scanner-line"></div>
                          <div className="absolute inset-0 border-[40px] border-black/20 pointer-events-none"></div>
                          <div className="absolute top-6 left-6 right-6 bottom-6 border-2 border-dashed border-white/30 rounded-3xl pointer-events-none"></div>
                        </>
                      )}
                    </div>

                    <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleFileUpload} />

                    <div className="absolute bottom-8 left-0 right-0 flex justify-center gap-4 z-20 px-8">
                      {(scanStep === 1 ? capturedImage : nutritionImage) ? (
                        <button
                          onClick={retakePhoto}
                          className="flex-1 h-14 bg-white/20 backdrop-blur-md border border-white/40 text-white text-xs font-black rounded-2xl shadow-xl active:scale-95 transition-all flex items-center justify-center gap-2"
                        >
                          <span>↺</span> RETAKE
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={takePhoto}
                            className="w-20 h-20 bg-white rounded-full shadow-2xl active:scale-90 transition-all flex items-center justify-center border-8 border-white/20"
                          >
                            <div className="w-12 h-12 rounded-full border-4 border-slate-900"></div>
                          </button>
                        </>
                      )}
                    </div>
                    {!(scanStep === 1 ? capturedImage : nutritionImage) && (
                      <button
                        onClick={triggerFileUpload}
                        className="absolute top-6 right-6 w-12 h-12 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl flex items-center justify-center text-white text-xl shadow-xl active:scale-90 transition-all"
                      >
                        📁
                      </button>
                    )}
                  </div>
                </div>

                <div className="pb-8 mt-10">
                  <div className="flex gap-4">
                    {scanStep === 2 && (
                      <button
                        onClick={prevStep}
                        className="w-16 h-16 bg-slate-100 rounded-2xl font-black flex items-center justify-center text-xl hover:bg-slate-200 transition-colors"
                      >
                        ←
                      </button>
                    )}
                    {isAnalyzing ? (
                      <div className="flex-1 h-16 bg-slate-900 text-white rounded-2xl font-black flex items-center justify-center gap-3">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        ANALYZING...
                      </div>
                    ) : (scanStep === 1 && capturedImage) ? (
                      <button onClick={nextStep} className="flex-1 h-16 bg-[#3a3f85] text-white rounded-2xl font-black shadow-lg shadow-blue-500/20 active:scale-98 transition-all">CONTINUE TO NUTRITION</button>
                    ) : (scanStep === 2 && nutritionImage) ? (
                      <button onClick={handleAnalyzeClick} className="flex-1 h-16 bg-emerald-500 text-white rounded-2xl font-black shadow-lg shadow-emerald-500/20 active:scale-98 transition-all uppercase tracking-widest">Generate Scan</button>
                    ) : (
                      <div className="flex-1 h-16 bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl flex items-center justify-center text-slate-400 text-[10px] font-black uppercase tracking-widest">
                        Position product label in frame
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ===== SCREEN 3: RESULTS ===== */}
            {activeTab === 'results' && analysisResult && (
              <div className="px-6 py-6 pb-24 animate-fade-in">
                <div className={`rounded-[32px] p-8 text-white ${scoreConfig[analysisResult.health_score].bg} ${scoreConfig[analysisResult.health_score].shadow} mb-8 relative overflow-hidden shadow-2xl`}>
                  <div className="relative z-10">
                    <div className="flex justify-between items-start mb-6">
                      <span className="bg-white/20 backdrop-blur-md px-3 py-1.5 rounded-full text-[10px] font-black tracking-widest uppercase border border-white/20">{t('health_score')}</span>
                      <span className="text-4xl filter drop-shadow-md">{scoreConfig[analysisResult.health_score].emoji}</span>
                    </div>
                    <h1 className="text-4xl font-black mb-1 leading-tight tracking-tighter uppercase">{analysisResult.product_name || "Unknown Product"}</h1>
                    <p className="text-white/80 font-black uppercase tracking-[0.2em] text-[10px]">{scoreConfig[analysisResult.health_score].label}</p>
                    <div className="mt-8 flex items-baseline gap-2">
                      <span className="text-7xl font-black tracking-tighter">{analysisResult.score_value || 0}</span>
                      <span className="text-2xl font-bold text-white/40">/10</span>
                    </div>
                  </div>
                  <div className="absolute -bottom-10 -right-10 w-48 h-48 bg-white/10 rounded-full blur-3xl"></div>
                </div>

                <NutritionSummary nutrition={analysisResult.nutrition} />

                {/* XAI SECTION */}
                {analysisResult.xai && (
                  <XAIExplanation xaiData={analysisResult.xai} imageUrl={nutritionImage} />
                )}

                {analysisResult.additives && analysisResult.additives.length > 0 && (
                  <div className="mb-8">
                    <div className="flex items-center gap-2 mb-4 px-1">
                      <div className="w-1.5 h-4 bg-slate-900 rounded-full"></div>
                      <p className="font-black text-slate-900 text-xs tracking-widest uppercase">Ingredient Flags</p>
                    </div>
                    <div className="space-y-4">
                      {analysisResult.additives.map((add, i) => (
                        <AdditiveCard key={i} additive={add} index={i} />
                      ))}
                    </div>
                  </div>
                )}

                {analysisResult.healthy_alternative && (
                  <div className="bg-emerald-50 rounded-[32px] p-7 border border-emerald-100 mb-8 shadow-sm">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xl">💡</span>
                      <p className="text-emerald-600 font-black text-[10px] uppercase tracking-widest">Better Alternative</p>
                    </div>
                    <p className="text-slate-900 font-black text-xl leading-snug mb-2">{analysisResult.healthy_alternative}</p>
                    <p className="text-emerald-700/60 text-[11px] font-medium italic">Choosing this improves your health baseline.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>

        {/* BOTTOM NAV */}
        <nav className="fixed bottom-0 left-0 right-0 z-40 flex justify-center pointer-events-none">
          <div className="w-full max-w-md bg-white/90 backdrop-blur-2xl border-t border-slate-100 px-8 py-5 flex justify-between items-center pointer-events-auto rounded-t-[32px] shadow-[0_-10px_40px_rgba(0,0,0,0.05)]">
            <button onClick={() => setActiveTab('dashboard')} className={`flex flex-col items-center gap-1.5 transition-all ${activeTab === 'dashboard' ? 'text-[#3a3f85] scale-110' : 'text-slate-300'}`}>
              <div className="text-2xl">{activeTab === 'dashboard' ? '🏠' : '🏚️'}</div>
              <span className="text-[9px] font-black uppercase tracking-widest">Home</span>
            </button>
            <button onClick={() => setActiveTab('trends')} className={`flex flex-col items-center gap-1.5 transition-all ${activeTab === 'trends' ? 'text-[#3a3f85] scale-110' : 'text-slate-300'}`}>
              <div className="text-2xl">{activeTab === 'trends' ? '📊' : '📈'}</div>
              <span className="text-[9px] font-black uppercase tracking-widest">Trends</span>
            </button>
            <div className="w-16 h-1 w-1 px-1"></div> {/* Spacer for middle button */}
            <button onClick={() => setActiveTab('results')} className={`flex flex-col items-center gap-1.5 transition-all ${activeTab === 'results' ? 'text-[#3a3f85] scale-110' : 'text-slate-300'}`}>
              <div className="text-2xl">{activeTab === 'results' ? '💎' : '🔍'}</div>
              <span className="text-[9px] font-black uppercase tracking-widest">Result</span>
            </button>
            <button onClick={() => setActiveTab('profile')} className={`flex flex-col items-center gap-1.5 transition-all ${activeTab === 'profile' ? 'text-[#3a3f85] scale-110' : 'text-slate-300'}`}>
              <div className="text-2xl">{activeTab === 'profile' ? '👤' : '⚙️'}</div>
              <span className="text-[9px] font-black uppercase tracking-widest">Prefs</span>
            </button>
          </div>

          <button
            onClick={() => setActiveTab('scanner')}
            className="absolute bottom-10 w-20 h-20 bg-gradient-to-br from-[#3a3f85] to-[#6c63ff] rounded-3xl flex items-center justify-center text-white shadow-[0_15px_30px_rgba(58,63,133,0.3)] border-4 border-white active:scale-90 active:rotate-3 transition-all pointer-events-auto z-50"
          >
            <div className="text-3xl font-bold">📸</div>
          </button>
        </nav>
      </div>
    </div>
  );
}

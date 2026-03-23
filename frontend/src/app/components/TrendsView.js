"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslate } from "../../lib/translateContext";

const emojiMap = { GREEN: "🟢", YELLOW: "🟡", RED: "🔴" };

const API = typeof process.env.NEXT_PUBLIC_API_URL === "string"
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : "http://127.0.0.1:7860";

// ── SVG Score Graph ──────────────────────────────────────────────────────────
function ScoreGraph({ trend, onSelectPoint }) {
    const svgRef = useRef(null);
    const [hovered, setHovered] = useState(null);
    // touch: track tap count for double-tap detection
    const tapRef = useRef({ last: 0, timer: null });

    const handleTap = useCallback((i) => {
        const now = Date.now();
        if (now - tapRef.current.last < 350) {
            // double-tap
            clearTimeout(tapRef.current.timer);
            onSelectPoint && onSelectPoint(i);
        } else {
            tapRef.current.timer = setTimeout(() => setHovered(i), 200);
        }
        tapRef.current.last = now;
    }, [onSelectPoint]);

    if (!trend || trend.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-44 text-center">
                <div className="text-4xl mb-2">📊</div>
                <p className="text-slate-400 text-xs font-semibold">No scans yet today</p>
                <p className="text-slate-300 text-[10px] mt-1">Scan a product to see your score graph</p>
            </div>
        );
    }

    const W = 320, H = 160;
    const PAD = { top: 20, right: 20, bottom: 36, left: 36 };
    const chartW = W - PAD.left - PAD.right;
    const chartH = H - PAD.top - PAD.bottom;

    const scores = trend.map(t => typeof t === "object" ? (t.score ?? 0) : t);
    const n = scores.length;

    // X: scan index (1-based), Y: score 0-10
    const xScale = i => (n === 1) ? PAD.left + chartW / 2 : PAD.left + (i / (n - 1)) * chartW;
    const yScale = v => PAD.top + chartH - (Math.max(0, Math.min(10, v)) / 10) * chartH;

    // Build polyline points
    const points = scores.map((s, i) => `${xScale(i)},${yScale(s)}`).join(" ");

    // Y-axis grid lines at 0, 4, 7, 10
    const yLines = [
        { v: 10, label: "10", color: "#10b981" },
        { v: 7, label: "7", color: "#10b981" },
        { v: 4, label: "4", color: "#f59e0b" },
        { v: 0, label: "0", color: "#ef4444" },
    ];

    // Grade → dot color
    const dotColor = (item) => {
        const grade = typeof item === "object" ? (item.grade || "") : "";
        const score = typeof item === "object" ? (item.score ?? 0) : item;
        if (grade === "GREEN" || score >= 7) return "#10b981";
        if (grade === "YELLOW" || score >= 4) return "#f59e0b";
        return "#ef4444";
    };

    // X-axis labels: show day scan number
    const xLabels = scores.map((_, i) => i + 1);

    return (
        <div className="relative w-full select-none">
            <svg
                ref={svgRef}
                viewBox={`0 0 ${W} ${H}`}
                className="w-full"
                style={{ maxHeight: 180 }}
            >
                {/* Background */}
                <rect x="0" y="0" width={W} height={H} rx="12" fill="#f8fafc" />

                {/* Colored zone bands */}
                <rect x={PAD.left} y={PAD.top} width={chartW}
                    height={yScale(7) - PAD.top}
                    fill="#10b981" fillOpacity="0.06" />
                <rect x={PAD.left} y={yScale(7)} width={chartW}
                    height={yScale(4) - yScale(7)}
                    fill="#f59e0b" fillOpacity="0.07" />
                <rect x={PAD.left} y={yScale(4)} width={chartW}
                    height={yScale(0) - yScale(4)}
                    fill="#ef4444" fillOpacity="0.06" />

                {/* Y-axis grid lines */}
                {yLines.map(g => (
                    <g key={g.v}>
                        <line
                            x1={PAD.left} y1={yScale(g.v)}
                            x2={PAD.left + chartW} y2={yScale(g.v)}
                            stroke={g.color} strokeWidth="0.8" strokeDasharray="4 3" strokeOpacity="0.5"
                        />
                        <text
                            x={PAD.left - 5} y={yScale(g.v) + 3.5}
                            textAnchor="end" fontSize="8" fill={g.color} fontWeight="700"
                        >
                            {g.label}
                        </text>
                    </g>
                ))}

                {/* X-axis line */}
                <line
                    x1={PAD.left} y1={PAD.top + chartH}
                    x2={PAD.left + chartW} y2={PAD.top + chartH}
                    stroke="#cbd5e1" strokeWidth="1"
                />

                {/* Connecting gradient line */}
                {n > 1 && (
                    <polyline
                        points={points}
                        fill="none"
                        stroke="url(#lineGrad)"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                )}

                {/* Gradient def */}
                <defs>
                    <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#6c63ff" />
                        <stop offset="100%" stopColor="#3a3f85" />
                    </linearGradient>
                </defs>

                {/* Area fill under line */}
                {n > 1 && (
                    <polygon
                        points={`${xScale(0)},${yScale(0)} ${points} ${xScale(n - 1)},${yScale(0)}`}
                        fill="url(#lineGrad)"
                        fillOpacity="0.08"
                    />
                )}

                {/* Data points */}
                {scores.map((s, i) => {
                    const cx = xScale(i), cy = yScale(s);
                    const item = trend[i];
                    const fill = dotColor(item);
                    const isHov = hovered === i;
                    return (
                        <g key={i}
                            onMouseEnter={() => setHovered(i)}
                            onMouseLeave={() => setHovered(null)}
                            onDoubleClick={() => onSelectPoint && onSelectPoint(i)}
                            onTouchStart={(e) => { e.preventDefault(); handleTap(i); }}
                            style={{ cursor: "pointer" }}>
                            <circle cx={cx} cy={cy} r={isHov ? 7 : 5}
                                fill={fill} stroke="white" strokeWidth="2"
                                style={{ transition: "r 0.15s" }} />
                            {/* Score label above dot when hovered */}
                            {isHov && (
                                <g>
                                    <rect x={cx - 18} y={cy - 22} width={36} height={14}
                                        rx="4" fill="#1e293b" fillOpacity="0.9" />
                                    <text x={cx} y={cy - 12}
                                        textAnchor="middle" fontSize="8" fill="white" fontWeight="800">
                                        {s}/10
                                    </text>
                                </g>
                            )}
                        </g>
                    );
                })}

                {/* X-axis scan number labels */}
                {xLabels.map((label, i) => (
                    <text key={i}
                        x={xScale(i)} y={PAD.top + chartH + 14}
                        textAnchor="middle" fontSize="7.5" fill="#94a3b8" fontWeight="700">
                        {label}
                    </text>
                ))}

                {/* X-axis title */}
                <text
                    x={PAD.left + chartW / 2} y={H - 3}
                    textAnchor="middle" fontSize="7" fill="#94a3b8" fontWeight="700"
                    letterSpacing="1">
                    SCAN # (TODAY)
                </text>

                {/* Y-axis title */}
                <text
                    transform={`rotate(-90, 10, ${PAD.top + chartH / 2})`}
                    x={10} y={PAD.top + chartH / 2}
                    textAnchor="middle" fontSize="7" fill="#94a3b8" fontWeight="700"
                    letterSpacing="1">
                    SCORE
                </text>
            </svg>

            {/* Tooltip for hovered point */}
            {hovered !== null && trend[hovered] && (
                <div className="mt-1 mx-2 p-2 bg-slate-800 rounded-xl text-white text-[10px] flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor(trend[hovered]) === "#10b981" ? "bg-emerald-400" :
                        dotColor(trend[hovered]) === "#f59e0b" ? "bg-yellow-400" : "bg-red-400"
                        }`} />
                    <span className="font-black">{trend[hovered].score ?? scores[hovered]}/10</span>
                    <span className="text-slate-400 truncate">{trend[hovered].product || `Scan #${hovered + 1}`}</span>
                    <span className="ml-auto text-slate-500 text-[9px]">{trend[hovered].timestamp || ""}</span>
                </div>
            )}

            {/* Legend */}
            <div className="flex items-center gap-4 justify-center mt-2">
                {[["bg-emerald-500", "GREEN ≥7"], ["bg-yellow-400", "YELLOW 4–6"], ["bg-red-500", "RED <4"]].map(([cls, lbl]) => (
                    <div key={lbl} className="flex items-center gap-1.5">
                        <span className={`w-2.5 h-2.5 rounded-full ${cls}`} />
                        <span className="text-[9px] font-black text-slate-500">{lbl}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}


// ── MAIN TrendsView ──────────────────────────────────────────────────────────
export default function TrendsView({ refreshTick, token, isGuest }) {
    const { t } = useTranslate();
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedPoint, setSelectedPoint] = useState(null);
    const [selectedAdditive, setSelectedAdditive] = useState(null); // { name, products[] }

    useEffect(() => {
        if (isGuest) { setLoading(false); return; }
        if (token === undefined) return;
        setLoading(true);
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        fetch(`${API}/analytics`, { headers })
            .then(r => r.json())
            .then(data => { setAnalytics(data); setLoading(false); })
            .catch(() => setLoading(false));
    }, [refreshTick, isGuest, token]);

    if (isGuest) {
        return (
            <div className="flex-1 px-5 pt-4 pb-24 overflow-y-auto">
                <h2 className="text-2xl font-black text-gray-900 mb-6">{t("Analytics")}</h2>
                <div className="bg-gradient-to-br from-[#3a3f85]/10 to-[#6c63ff]/5 rounded-3xl p-10 text-center border-2 border-dashed border-[#6c63ff]/20">
                    <div className="text-5xl mb-4">📊</div>
                    <p className="font-black text-slate-700 text-base mb-2">{t("Sign in to see Analytics")}</p>
                    <p className="text-slate-400 text-sm leading-relaxed">{t("Your health trends, score history, and additive analysis are only available for registered users.")}</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex-1 px-5 pt-4 pb-24 overflow-y-auto">
                <div className="h-6 bg-slate-100 rounded w-32 mb-6 animate-pulse" />
                <div className="space-y-4">
                    {[1, 2, 3].map(i => <div key={i} className="h-32 bg-slate-100 rounded-3xl animate-pulse" />)}
                </div>
            </div>
        );
    }

    if (!analytics) return (
        <div className="flex-1 px-5 pt-4 pb-24 flex items-center justify-center">
            <p className="text-slate-400 text-sm font-medium">Could not load analytics.</p>
        </div>
    );

    const trend = analytics.history_trend || [];
    const dist = analytics.score_distribution || { GREEN: 0, YELLOW: 0, RED: 0 };
    const dailyAvg = analytics.daily_avg || [];

    // Filter today's scans for the graph — use local date to match backend IST timestamps
    const todayLocal = new Date();
    const today = `${todayLocal.getFullYear()}-${String(todayLocal.getMonth() + 1).padStart(2, "0")}-${String(todayLocal.getDate()).padStart(2, "0")}`;
    const todayTrend = trend.filter(t =>
        typeof t === "object" && (t.timestamp || "").startsWith(today)
    );
    // Fallback: use latest 20 if no today scans
    const graphTrend = todayTrend.length > 0 ? todayTrend : trend.slice(-20);

    return (
        <div className="flex-1 px-5 pt-4 pb-24 overflow-y-auto">
            <h2 className="text-2xl font-black text-gray-900 leading-tight mb-6">{t("Analytics")}</h2>

            {/* Average Score Card */}
            <div className="bg-gradient-to-br from-[#3a3f85] to-[#6c63ff] rounded-3xl p-6 text-white shadow-xl mb-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full translate-x-10 -translate-y-10" />
                <div className="relative z-10">
                    <p className="text-white/60 font-black text-xs uppercase tracking-widest mb-1">{t("Average Health Score")}</p>
                    <div className="flex items-baseline gap-2">
                        <span className="text-5xl font-black">{analytics.avg_score ?? "–"}</span>
                        <span className="text-xl font-bold text-white/40">/10</span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                        <span className="bg-white/10 px-3 py-1 rounded-full text-xs font-black">{analytics.total_scans ?? 0} scans</span>
                        <span className="bg-white/10 px-3 py-1 rounded-full text-xs font-black">
                            🟢 {dist.GREEN} &nbsp;🟡 {dist.YELLOW} &nbsp;🔴 {dist.RED}
                        </span>
                        {analytics.green_streak > 0 && (
                            <span className="bg-emerald-500/30 px-3 py-1 rounded-full text-xs font-black">
                                🔥 {analytics.green_streak} GREEN streak
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* ══ SCORE HISTORY GRAPH ══ */}
            <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-sm mb-5">
                <div className="flex items-center justify-between mb-1">
                    <p className="font-black text-gray-900 text-sm uppercase tracking-widest">{t("Score History")}</p>
                    <span className="text-[9px] font-black text-slate-400 bg-slate-100 px-2 py-1 rounded-full uppercase tracking-wide">
                        {todayTrend.length > 0 ? `${todayTrend.length} scans today` : `Last ${graphTrend.length} scans`}
                    </span>
                </div>
                <p className="text-slate-400 text-[10px] mb-3">
                    Y-axis = health score · X-axis = scan # · double-click dot for details
                </p>
                <ScoreGraph trend={graphTrend} onSelectPoint={(i) => setSelectedPoint(graphTrend[i])} />
            </div>

            {/* Daily Average bar chart */}
            {dailyAvg.length > 0 && (
                <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-sm mb-5">
                    <p className="font-black text-gray-900 text-sm uppercase tracking-widest mb-4">{t("Daily Average")}</p>
                    <div className="space-y-2.5">
                        {dailyAvg.slice(-7).map((d, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <span className="text-[10px] text-slate-400 font-bold w-20 shrink-0">{d.date}</span>
                                <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden relative">
                                    <div
                                        className={`h-full rounded-full transition-all duration-700 ${d.avg >= 7 ? "bg-emerald-400" : d.avg >= 4 ? "bg-yellow-400" : "bg-red-400"}`}
                                        style={{ width: `${(d.avg / 10) * 100}%` }}
                                    />
                                </div>
                                <span className={`text-[10px] font-black w-8 text-right ${d.avg >= 7 ? "text-emerald-600" : d.avg >= 4 ? "text-yellow-600" : "text-red-600"}`}>
                                    {d.avg}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Top Flagged Additives */}
            <div className="bg-white rounded-3xl p-5 border border-slate-100 shadow-sm">
                <p className="font-black text-gray-900 text-sm uppercase tracking-widest mb-1">{t("Top Flagged Additives")}</p>
                <p className="text-slate-400 text-[10px] mb-4">{t("Tap an additive to see which products contained it")}</p>
                <div className="space-y-3">
                    {analytics.top_additives && analytics.top_additives.length > 0 ? (
                        analytics.top_additives.map((item, i) => {
                            const allTrend = analytics.history_trend || [];
                            const products = allTrend.filter(scan =>
                                Array.isArray(scan.flagged_additives) &&
                                scan.flagged_additives.some(a =>
                                    (typeof a === "object" ? a.name : a) === item.name
                                )
                            );
                            return (
                                <button key={i}
                                    onClick={() => setSelectedAdditive({ name: item.name, products })}
                                    className="w-full flex items-center justify-between p-3 bg-slate-50 rounded-2xl border border-slate-100 active:scale-[0.98] hover:border-slate-300 hover:shadow-sm transition-all text-left">
                                    <div className="flex items-center gap-3">
                                        <span className="text-xl">{i === 0 ? "🚫" : i === 1 ? "⚠️" : "🔶"}</span>
                                        <div>
                                            <p className="font-bold text-gray-800 text-xs">{item.name}</p>
                                            <p className="text-slate-400 text-[9px] mt-0.5">{products.length} product{products.length !== 1 ? "s" : ""}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="bg-white px-3 py-1 rounded-full border border-slate-200 text-[10px] font-black text-slate-500">{item.count}×</span>
                                        <span className="text-slate-300 text-xs">›</span>
                                    </div>
                                </button>
                            );
                        })
                    ) : (
                        <p className="text-center text-slate-400 text-xs italic py-4">
                            {t("No recurring additives yet — scan more products!")}
                        </p>
                    )}
                </div>
            </div>

            {/* Additive detail popup */}
            {selectedAdditive && (
                <div className="fixed inset-0 z-[9999] flex items-end justify-center">
                    <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" onClick={() => setSelectedAdditive(null)} />
                    <div className="relative w-full max-w-md bg-white rounded-t-[32px] px-6 pt-6 pb-10 shadow-2xl">
                        <div className="w-10 h-1 bg-slate-200 rounded-full mx-auto mb-5" />
                        <div className="flex items-center gap-3 mb-5">
                            <div className="w-12 h-12 rounded-2xl bg-red-100 flex items-center justify-center text-2xl shrink-0">🚫</div>
                            <div>
                                <p className="font-black text-slate-900 text-base leading-tight">{selectedAdditive.name}</p>
                                <p className="text-slate-400 text-xs mt-0.5">
                                    Found in {selectedAdditive.products.length} scanned product{selectedAdditive.products.length !== 1 ? "s" : ""}
                                </p>
                            </div>
                        </div>
                        {selectedAdditive.products.length > 0 ? (
                            <div className="space-y-2 max-h-[45vh] overflow-y-auto pr-1">
                                {selectedAdditive.products.map((scan, idx) => {
                                    const score = scan.grade || "YELLOW";
                                    const gradMap = { GREEN: "from-emerald-400 to-green-500", RED: "from-red-500 to-rose-600", YELLOW: "from-amber-400 to-yellow-500" };
                                    return (
                                        <div key={idx} className="flex items-center gap-3 bg-slate-50 rounded-2xl p-3 border border-slate-100">
                                            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${gradMap[score] || gradMap.YELLOW} flex items-center justify-center shrink-0`}>
                                                <span className="text-white text-xs font-black">{scan.score ?? "–"}</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-black text-slate-900 text-xs truncate">{scan.product || "Unknown Product"}</p>
                                                {scan.brand && <p className="text-slate-400 text-[9px] truncate">{scan.brand}</p>}
                                            </div>
                                            <span className="text-[9px] font-black text-slate-400 shrink-0">{(scan.timestamp || "").slice(0, 10)}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="bg-slate-50 rounded-2xl p-6 text-center">
                                <p className="text-slate-400 text-xs font-bold">No detailed product data available for this additive.</p>
                            </div>
                        )}
                        <button onClick={() => setSelectedAdditive(null)}
                            className="mt-5 w-full h-12 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest active:scale-95 transition-all">
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

"use client";
import { useState, useEffect } from "react";
import { useTranslate } from "../../lib/translateContext";

const scoreStyle = {
    RED:    { grad: "from-red-500 to-rose-600",      glow: "shadow-red-300",     ring: "ring-red-200",     icon: "", label: "HARMFUL" },
    YELLOW: { grad: "from-amber-400 to-yellow-500",  glow: "shadow-amber-200",   ring: "ring-amber-200",   icon: "", label: "MODERATE" },
    GREEN:  { grad: "from-emerald-400 to-green-500", glow: "shadow-emerald-200", ring: "ring-emerald-200", icon: "", label: "HEALTHY" },
};

const emojiMap = { RED: "", YELLOW: "", GREEN: "" };

// Derive correct grade from score_value — guards against stale DB entries
function resolveGrade(item) {
    const val = item.score_value ?? item.score;
    if (val !== undefined && val !== null) {
        if (val >= 7.5) return "GREEN";
        if (val >= 5.0) return "YELLOW";
        return "RED";
    }
    return item.health_score || item.grade || "YELLOW";
}

export default function HistoryFeed({ refreshTick, token, isGuest }) {
    const { t } = useTranslate();
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selected, setSelected] = useState(null);

    const API = typeof process.env.NEXT_PUBLIC_API_URL === "string"
        ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
        : "http://127.0.0.1:7860";

    useEffect(() => {
        if (isGuest) { setLoading(false); return; }
        if (token === undefined) return;
        setLoading(true);
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        fetch(`${API}/history?limit=20`, { headers })
            .then(r => r.json())
            .then(data => { setHistory(Array.isArray(data) ? data : []); setLoading(false); })
            .catch(() => setLoading(false));
    }, [refreshTick, isGuest, token]);

    if (isGuest) return (
        <div className="bg-gradient-to-br from-[#3a3f85]/10 to-[#6c63ff]/5 rounded-3xl p-8 text-center border-2 border-dashed border-[#6c63ff]/20">
            <div className="text-4xl mb-3"></div>
            <p className="font-black text-slate-700 text-sm mb-1">{t("Sign in to view history")}</p>
            <p className="text-slate-400 text-xs">{t("Guest mode only shows scan results.")}</p>
        </div>
    );

    if (loading) return (
        <div className="space-y-3">
            {[1, 2, 3].map(i => (
                <div key={i} className="bg-white rounded-2xl p-4 border border-slate-100 flex items-center gap-3 animate-pulse">
                    <div className="w-12 h-12 rounded-xl bg-slate-100" />
                    <div className="flex-1 space-y-2">
                        <div className="h-3 bg-slate-100 rounded w-2/3" />
                        <div className="h-2 bg-slate-100 rounded w-1/3" />
                    </div>
                </div>
            ))}
        </div>
    );

    if (history.length === 0) return (
        <div className="bg-white rounded-3xl p-8 text-center border-2 border-dashed border-slate-200">
            <div className="text-4xl mb-3"></div>
            <p className="text-slate-400 text-sm font-semibold">{t("No scans yet. Start scanning food labels!")}</p>
        </div>
    );

    return (
        <>
            <div className="space-y-3">
                {history.map((item, i) => {
                    const score = resolveGrade(item);
                    const style = scoreStyle[score] || scoreStyle.YELLOW;
                    return (
                        <div key={i} onClick={() => setSelected(item)}
                            className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex items-center justify-between cursor-pointer active:scale-[0.98] hover:border-slate-300 hover:shadow-md transition-all">
                            <div className="flex items-center gap-3">
                                <div className={`relative w-14 h-14 rounded-2xl bg-gradient-to-br ${style.grad} flex flex-col items-center justify-center shadow-lg ring-2 ${style.ring} ${style.glow}`}>
                                    <span className="text-lg leading-none">{style.icon}</span>
                                    <span className="text-white text-[9px] font-black leading-none mt-0.5">{item.score_value ?? "–"}</span>
                                </div>
                                <div>
                                    <p className="font-bold text-gray-900 text-sm leading-tight">{item.product_name || "Unknown Product"}</p>
                                    <p className="text-gray-400 text-[10px] font-bold mt-0.5">
                                        {item.brand && <span className="mr-2 text-slate-500">{item.brand}</span>}
                                        {item.timestamp}
                                    </p>
                                </div>
                            </div>
                            <div className="flex flex-col items-end gap-1">
                                <span className={`text-[9px] font-black px-2.5 py-1 rounded-full uppercase tracking-wide ${score === "GREEN" ? "bg-emerald-100 text-emerald-700" : score === "RED" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                                    {style.label}
                                </span>
                                <span className="text-[10px] font-black text-slate-400">{item.timestamp?.slice(0, 10)}</span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {selected && (() => {
                const score = resolveGrade(selected);
                const style = scoreStyle[score] || scoreStyle.YELLOW;
                const emoji = emojiMap[score] || "";
                const nutrition = selected.nutrition || {};
                const additives = Array.isArray(selected.flagged_additives) ? selected.flagged_additives : [];
                const harmfulOnes = Array.isArray(selected.harmful_additives) && selected.harmful_additives.length > 0
                    ? selected.harmful_additives
                    : additives.filter(a => typeof a === "object" && a.risk_level === "RED");
                const nutItems = [
                    { label: "Calories", val: nutrition.calories,  color: "text-slate-800" },
                    { label: "Sugar",    val: nutrition.sugar,     color: "text-red-500" },
                    { label: "Fat",      val: nutrition.total_fat, color: "text-orange-500" },
                    { label: "Protein",  val: nutrition.protein,   color: "text-emerald-600" },
                    { label: "Carbs",    val: nutrition.carbs,     color: "text-blue-500" },
                    { label: "Sodium",   val: nutrition.sodium,    color: "text-purple-500" },
                ].filter(n => n.val && n.val !== "N/A");

                return (
                    <div className="fixed inset-0 z-[9999] flex items-center justify-center px-4">
                        <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" onClick={() => setSelected(null)} />
                        <div className="relative w-full max-w-sm bg-white rounded-3xl shadow-2xl overflow-hidden">
                            <div className={`px-6 pt-6 pb-5 bg-gradient-to-r ${style.grad}`}>
                                <div className="flex justify-between items-start">
                                    <div className="flex-1 pr-3">
                                        {selected.brand && <p className="text-white/70 text-[10px] font-black uppercase tracking-widest mb-1">{selected.brand}</p>}
                                        <p className="text-white font-black text-base leading-tight">{selected.product_name || "Unknown Product"}</p>
                                        <p className="text-white/60 text-[10px] mt-1">{selected.timestamp}</p>
                                    </div>
                                    <div className="flex flex-col items-center bg-white/20 rounded-2xl px-3 py-2 border border-white/30">
                                        <span className="text-white text-2xl font-black">{selected.score_value ?? "–"}</span>
                                        <span className="text-white/70 text-[8px] font-black uppercase">/10</span>
                                    </div>
                                </div>
                                <span className={`mt-3 inline-block text-[9px] font-black px-3 py-1 rounded-full uppercase ${score === "GREEN" ? "bg-emerald-100 text-emerald-700" : score === "RED" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"}`}>
                                    {emoji} {score}
                                </span>
                            </div>

                            <div className="px-6 py-5 space-y-4 max-h-[55vh] overflow-y-auto">
                                {nutItems.length > 0 && (
                                    <div>
                                        <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">Nutrition per 100g</p>
                                        <div className="grid grid-cols-3 gap-2">
                                            {nutItems.map((n, idx) => (
                                                <div key={idx} className="bg-slate-50 rounded-2xl p-3 text-center border border-slate-100">
                                                    <p className="text-[8px] font-black text-slate-400 uppercase mb-0.5">{n.label}</p>
                                                    <p className={`text-xs font-black ${n.color}`}>{n.val}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                <div>
                                    <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">Additives {additives.length > 0 ? `(${additives.length})` : ""}</p>
                                    {additives.length > 0 ? (
                                        <div className="flex flex-wrap gap-1.5">
                                            {additives.map((a, idx) => {
                                                const name = typeof a === "object" ? a.name : a;
                                                const risk = typeof a === "object" ? a.risk_level : "YELLOW";
                                                return (
                                                    <span key={idx} className={`text-[9px] font-black px-2.5 py-1 rounded-full ${risk === "RED" ? "bg-red-100 text-red-700" : risk === "GREEN" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                                                        {name}
                                                    </span>
                                                );
                                            })}
                                        </div>
                                    ) : (
                                        <p className="text-[10px] font-black text-emerald-600"> No additives detected — clean label</p>
                                    )}
                                </div>
                                {harmfulOnes.length > 0 && (
                                    <div className="bg-red-50 border border-red-100 rounded-2xl p-4">
                                        <p className="text-[9px] font-black text-red-500 uppercase tracking-widest mb-2"> Harmful Ingredients ({harmfulOnes.length})</p>
                                        <div className="flex flex-wrap gap-1.5">
                                            {harmfulOnes.map((a, idx) => (
                                                <span key={idx} className="text-[9px] font-black px-2.5 py-1 rounded-full bg-red-200 text-red-800">
                                                    {typeof a === "object" ? a.name : a}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {selected.healthy_alternative && (
                                    <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-4">
                                        <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest mb-1"> Try Instead</p>
                                        <p className="text-xs text-emerald-700 font-bold leading-snug">{selected.healthy_alternative}</p>
                                    </div>
                                )}
                            </div>

                            <div className="px-6 pb-6">
                                <button onClick={() => setSelected(null)}
                                    className="w-full h-12 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest active:scale-95 transition-all">
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                );
            })()}
        </>
    );
}
"use client";
import { useState, useEffect } from "react";

export default function HistoryFeed({ refreshTick, token, isGuest }) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    const API = typeof process.env.NEXT_PUBLIC_API_URL === "string"
        ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
        : "http://127.0.0.1:7860";

    useEffect(() => {
        if (isGuest) { setLoading(false); return; }
        // Wait until auth is resolved — undefined means localStorage hasn't loaded yet
        if (token === undefined) return;
        setLoading(true);
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        fetch(`${API}/history?limit=20`, { headers })
            .then(r => r.json())
            .then(data => { setHistory(Array.isArray(data) ? data : []); setLoading(false); })
            .catch(() => setLoading(false));
    }, [refreshTick, isGuest, token]);

    if (isGuest) {
        return (
            <div className="bg-gradient-to-br from-[#3a3f85]/10 to-[#6c63ff]/5 rounded-3xl p-8 text-center border-2 border-dashed border-[#6c63ff]/20">
                <div className="text-4xl mb-3">🔒</div>
                <p className="font-black text-slate-700 text-sm mb-1">Sign in to view history</p>
                <p className="text-slate-400 text-xs">Guest mode only shows scan results.<br />Create an account to track your health over time.</p>
            </div>
        );
    }

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
            <div className="text-4xl mb-3">📭</div>
            <p className="text-slate-400 text-sm font-semibold">No scans yet. Start scanning food labels!</p>
        </div>
    );

    return (
        <div className="space-y-3">
            {history.map((item, i) => {
                const sc = { RED: "bg-red-500", YELLOW: "bg-yellow-400", GREEN: "bg-emerald-500" };
                const emoji = { RED: "🚨", YELLOW: "⚠️", GREEN: "✅" };
                const score = item.health_score || "YELLOW";
                return (
                    <div key={i} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex items-center justify-between group hover:border-slate-300 transition-all animate-fade-in">
                        <div className="flex items-center gap-3">
                            <div className={`w-12 h-12 rounded-xl ${sc[score] || "bg-slate-200"} flex items-center justify-center text-xl shadow-sm group-hover:scale-105 transition-transform`}>
                                {emoji[score] || "🔍"}
                            </div>
                            <div>
                                <p className="font-bold text-gray-900 text-sm leading-tight">
                                    {item.product_name || "Unknown Product"}
                                </p>
                                <p className="text-gray-400 text-[10px] font-bold mt-0.5">
                                    {item.brand && <span className="mr-2 text-slate-500">{item.brand}</span>}
                                    {item.timestamp}
                                </p>
                            </div>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                            <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase ${score === "GREEN" ? "bg-emerald-100 text-emerald-700" : score === "RED" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"}`}>
                                {score}
                            </span>
                            <span className="text-xs font-black text-slate-700">{item.score_value ?? "–"}/10</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

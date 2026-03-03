"use client";
import { useEffect, useState } from "react";

export default function SplashScreen({ onDone }) {
    const [phase, setPhase] = useState("logo"); // logo → tagline → done

    useEffect(() => {
        const t1 = setTimeout(() => setPhase("tagline"), 1200);
        const t2 = setTimeout(() => { setPhase("done"); onDone(); }, 2600);
        return () => { clearTimeout(t1); clearTimeout(t2); };
    }, []);

    return (
        <div className="fixed inset-0 z-[200] flex flex-col items-center justify-center bg-gradient-to-br from-[#1a1d4e] via-[#2d3270] to-[#6c63ff] overflow-hidden">
            {/* Ambient blobs */}
            <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-[#6c63ff]/30 rounded-full blur-[100px] animate-pulse" />
            <div className="absolute bottom-1/4 right-1/4 w-48 h-48 bg-emerald-400/20 rounded-full blur-[80px] animate-pulse delay-500" />

            {/* Logo */}
            <div className={`flex flex-col items-center transition-all duration-700 ${phase !== "logo" ? "scale-95 opacity-80" : "scale-100 opacity-100"}`}>
                <div className="relative w-28 h-28 mb-6">
                    <div className="absolute inset-0 rounded-[32px] bg-white/10 backdrop-blur-md border border-white/20 shadow-2xl" />
                    <div className="absolute inset-0 flex items-center justify-center">
                        <svg viewBox="0 0 80 80" className="w-16 h-16">
                            <defs>
                                <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stopColor="#00f5c4" />
                                    <stop offset="100%" stopColor="#6c63ff" />
                                </linearGradient>
                            </defs>
                            {/* Barcode lines */}
                            <rect x="8" y="20" width="4" height="40" rx="2" fill="url(#logoGrad)" />
                            <rect x="16" y="15" width="2" height="50" rx="1" fill="white" opacity="0.9" />
                            <rect x="22" y="20" width="5" height="40" rx="2" fill="url(#logoGrad)" />
                            <rect x="31" y="15" width="2" height="50" rx="1" fill="white" opacity="0.9" />
                            <rect x="37" y="20" width="6" height="40" rx="2" fill="url(#logoGrad)" />
                            <rect x="47" y="15" width="3" height="50" rx="1" fill="white" opacity="0.9" />
                            <rect x="54" y="20" width="4" height="40" rx="2" fill="url(#logoGrad)" />
                            <rect x="62" y="15" width="2" height="50" rx="1" fill="white" opacity="0.9" />
                            <rect x="67" y="20" width="5" height="40" rx="2" fill="url(#logoGrad)" />
                            {/* Scan line */}
                            <rect x="6" y="38" width="68" height="3" rx="1.5" fill="#00f5c4" opacity="0.9" />
                            {/* Health cross */}
                            <circle cx="40" cy="39.5" r="10" fill="#1a1d4e" />
                            <rect x="36.5" y="34" width="7" height="11" rx="2" fill="white" />
                            <rect x="34" y="36.5" width="12" height="6" rx="2" fill="white" />
                        </svg>
                    </div>
                    {/* Pulse ring */}
                    <div className="absolute inset-0 rounded-[32px] border-2 border-emerald-400/40 animate-ping" style={{ animationDuration: "2s" }} />
                </div>

                <h1 className="text-4xl font-black text-white tracking-tight">
                    Nutri<span className="text-emerald-400">Scanner</span>
                </h1>
            </div>

            {phase !== "logo" && (
                <p className="mt-4 text-white/60 text-sm font-medium tracking-wider animate-fade-in">
                    AI-Powered Food Intelligence
                </p>
            )}

            {/* Loading dots */}
            <div className="absolute bottom-16 flex gap-2">
                {[0, 1, 2].map(i => (
                    <div
                        key={i}
                        className="w-2 h-2 rounded-full bg-white/40"
                        style={{ animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }}
                    />
                ))}
            </div>
        </div>
    );
}

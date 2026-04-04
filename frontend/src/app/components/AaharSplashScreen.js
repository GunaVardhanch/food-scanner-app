"use client";
import { useEffect, useState } from "react";

export default function AaharSplashScreen({ onDone }) {
    const [phase, setPhase] = useState("logo"); // logo → tagline → done

    useEffect(() => {
        const t1 = setTimeout(() => setPhase("tagline"), 1200);
        const t2 = setTimeout(() => { setPhase("done"); onDone(); }, 2600);
        return () => { clearTimeout(t1); clearTimeout(t2); };
    }, []);

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center max-w-md mx-auto w-full bg-gradient-to-br from-dark-navy via-slate-900 to-dark-navy overflow-hidden">
            {/* Ambient tricolor blobs */}
            <div className="absolute top-1/4 left-[10%] w-72 h-72 bg-saffron/20 rounded-full blur-[120px] animate-pulse" />
            <div className="absolute bottom-1/4 right-[10%] w-64 h-64 bg-india-green/20 rounded-full blur-[100px] animate-pulse delay-700" />
            <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-ashoka-blue/15 rounded-full blur-[120px] animate-pulse delay-1000" />

            {/* Branding */}
            <div className={`flex flex-col items-center transition-all duration-700 ${phase !== "logo" ? "scale-95 opacity-80" : "scale-100 opacity-100"}`}>
                <h1 className="text-5xl font-bold text-white tracking-tight text-center">
                    MA-Shabari
                </h1>
            </div>

            {/* Tagline */}
            {phase !== "logo" && (
                <p className="mt-4 text-white/70 text-sm font-medium tracking-wider animate-fade-in text-center px-4">
                    Your Personal Meal Planner
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

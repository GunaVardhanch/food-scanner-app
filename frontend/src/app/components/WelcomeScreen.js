"use client";
import { useState } from "react";
import { useTranslate } from "../../lib/translateContext";

const API_BASE_URL = typeof process.env.NEXT_PUBLIC_API_URL === "string"
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : "http://127.0.0.1:7860";

export default function WelcomeScreen({ onAuth, onGuest }) {
    const { t } = useTranslate();
    const [mode, setMode] = useState("welcome"); // welcome | login | register
    const [form, setForm] = useState({ name: "", email: "", password: "" });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

    const submit = async () => {
        setError("");
        if (!form.email || !form.password) { setError("Email and password are required."); return; }
        if (mode === "register" && !form.name) { setError("Your name is required."); return; }
        if (form.password.length < 6) { setError("Password must be at least 6 characters."); return; }
        setLoading(true);
        try {
            const endpoint = mode === "register" ? "/auth/register" : "/auth/login";
            const body = mode === "register"
                ? { name: form.name, email: form.email, password: form.password }
                : { email: form.email, password: form.password };
            const res = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (!res.ok) { setError(data.error || "Something went wrong."); return; }
            localStorage.setItem("ns_token", data.token);
            localStorage.setItem("ns_user", JSON.stringify(data.user));
            onAuth(data.user, data.token);
        } catch {
            setError("Network error — is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    if (mode === "welcome") {
        return (
            <div className="fixed inset-0 z-[150] flex flex-col bg-gradient-to-br from-[#1a1d4e] via-[#2d3270] to-[#0f0f2e] overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                    <div className="absolute top-1/4 left-[-10%] w-80 h-80 bg-[#6c63ff]/20 rounded-full blur-[120px]" />
                    <div className="absolute bottom-1/4 right-[-10%] w-64 h-64 bg-emerald-500/15 rounded-full blur-[100px]" />
                </div>

                <div className="flex-1 flex flex-col items-center justify-center px-8 relative z-10">
                    {/* Logo mark */}
                    <div className="w-20 h-20 rounded-3xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center mb-6 shadow-2xl">
                        <svg viewBox="0 0 60 60" className="w-12 h-12">
                            <defs>
                                <linearGradient id="wg" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stopColor="#00f5c4" />
                                    <stop offset="100%" stopColor="#6c63ff" />
                                </linearGradient>
                            </defs>
                            <rect x="5" y="12" width="3" height="36" rx="1.5" fill="url(#wg)" />
                            <rect x="11" y="8" width="2" height="44" rx="1" fill="white" opacity="0.9" />
                            <rect x="16" y="12" width="4" height="36" rx="1.5" fill="url(#wg)" />
                            <rect x="23" y="8" width="2" height="44" rx="1" fill="white" opacity="0.9" />
                            <rect x="28" y="12" width="5" height="36" rx="1.5" fill="url(#wg)" />
                            <rect x="36" y="8" width="2" height="44" rx="1" fill="white" opacity="0.9" />
                            <rect x="41" y="12" width="3" height="36" rx="1.5" fill="url(#wg)" />
                            <rect x="47" y="8" width="2" height="44" rx="1" fill="white" opacity="0.9" />
                            <rect x="52" y="12" width="3" height="36" rx="1.5" fill="url(#wg)" />
                            <rect x="4" y="28" width="52" height="4" rx="2" fill="#00f5c4" opacity="0.7" />
                        </svg>
                    </div>

                    <h1 className="text-5xl font-black text-white text-center leading-tight">
                        Nutri<span className="text-emerald-400">Scanner</span>
                    </h1>
                    <p className="text-white/50 text-base mt-3 text-center font-medium">
                        {t("Know what's really in your food")}
                    </p>

                    <div className="w-full mt-14 space-y-3">
                        <button
                            onClick={() => setMode("login")}
                            className="w-full h-14 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl shadow-emerald-500/30 active:scale-95 transition-all flex items-center justify-center gap-2"
                        >
                            🔑 {t("Sign In")}
                        </button>
                        <button
                            onClick={() => setMode("register")}
                            className="w-full h-14 bg-white/10 backdrop-blur border border-white/20 text-white rounded-2xl font-black text-sm uppercase tracking-widest active:scale-95 transition-all flex items-center justify-center gap-2"
                        >
                            ✨ {t("Create Account")}
                        </button>
                        <button
                            onClick={onGuest}
                            className="w-full h-12 text-white/40 text-xs font-bold uppercase tracking-widest hover:text-white/70 transition-colors"
                        >
                            {t("Continue as Guest")} →
                        </button>
                    </div>
                </div>

                <div className="pb-10 px-8 text-center relative z-10">
                    <p className="text-white/20 text-[10px] font-medium">
                        {t("Guest mode: scan only · No history saved")}
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-[150] flex flex-col bg-gradient-to-br from-[#1a1d4e] via-[#2d3270] to-[#0f0f2e] overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                <div className="absolute top-1/4 left-[-10%] w-80 h-80 bg-[#6c63ff]/20 rounded-full blur-[120px]" />
            </div>

            <div className="flex-1 flex flex-col justify-center px-6 py-8 relative z-10 overflow-y-auto">
                <button
                    onClick={() => { setMode("welcome"); setError(""); }}
                    className="w-10 h-10 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center text-white mb-8 self-start"
                >
                    ←
                </button>

                <h2 className="text-3xl font-black text-white mb-1">
                    {mode === "login" ? t("Welcome back") : t("Create account")}
                </h2>
                <p className="text-white/40 text-sm mb-8">
                    {mode === "login" ? t("Sign in to access your scan history & analytics") : t("Join to save your scans and track your health")}
                </p>

                {/* Tab row */}
                <div className="flex bg-white/5 border border-white/10 rounded-2xl p-1 mb-6">
                    {["login", "register"].map(m => (
                        <button key={m} onClick={() => { setMode(m); setError(""); }}
                            className={`flex-1 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all ${mode === m ? "bg-white/15 text-white" : "text-white/30"}`}>
                            {m === "login" ? t("Sign In") : t("Register")}
                        </button>
                    ))}
                </div>

                <div className="space-y-3">
                    {mode === "register" && (
                        <input type="text" placeholder={t("Your name")} value={form.name}
                            onChange={e => update("name", e.target.value)}
                            className="w-full px-4 py-4 rounded-2xl bg-white/10 border border-white/15 text-white placeholder:text-white/30 text-sm font-medium focus:outline-none focus:border-emerald-400/60 focus:bg-white/15 transition-all" />
                    )}
                    <input type="email" placeholder={t("Email address")} value={form.email}
                        onChange={e => update("email", e.target.value)}
                        className="w-full px-4 py-4 rounded-2xl bg-white/10 border border-white/15 text-white placeholder:text-white/30 text-sm font-medium focus:outline-none focus:border-emerald-400/60 focus:bg-white/15 transition-all" />
                    <input type="password" placeholder={t("Password (min 6 chars)")} value={form.password}
                        onChange={e => update("password", e.target.value)}
                        onKeyDown={e => e.key === "Enter" && submit()}
                        className="w-full px-4 py-4 rounded-2xl bg-white/10 border border-white/15 text-white placeholder:text-white/30 text-sm font-medium focus:outline-none focus:border-emerald-400/60 focus:bg-white/15 transition-all" />

                    {error && (
                        <div className="bg-red-500/20 border border-red-500/30 rounded-2xl px-4 py-3 text-xs text-red-300 font-bold">
                            ⚠️ {error}
                        </div>
                    )}

                    <button onClick={submit} disabled={loading}
                        className="w-full h-14 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl shadow-emerald-500/30 active:scale-95 transition-all disabled:opacity-60 flex items-center justify-center gap-2 mt-2">
                        {loading
                            ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            : mode === "login" ? t("Sign In") : t("Create Account")}
                    </button>

                    <button onClick={onGuest}
                        className="w-full py-3 text-white/30 text-xs font-bold uppercase tracking-widest hover:text-white/60 transition-colors">
                        {t("Continue as Guest (scan only)")}
                    </button>
                </div>
            </div>
        </div>
    );
}

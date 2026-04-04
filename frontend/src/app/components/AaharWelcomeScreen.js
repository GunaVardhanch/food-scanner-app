"use client";
import { useState } from "react";

const API_BASE_URL = typeof process.env.NEXT_PUBLIC_API_URL === "string"
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : "http://127.0.0.1:5001";

export default function AaharWelcomeScreen({ onAuth, onBack }) {
    const [mode, setMode] = useState("welcome"); // welcome | login | register
    const [form, setForm] = useState({ name: "", email: "", password: "" });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

    const submit = async () => {
        setError("");
        if (!form.email || !form.password) { setError("Email and password required."); return; }
        if (mode === "register" && !form.name) { setError("Name is required."); return; }
        if (form.password.length < 6) { setError("Password must be 6+ characters."); return; }
        
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
            
            localStorage.setItem("aa_token", data.token);
            localStorage.setItem("aa_user", JSON.stringify(data.user));
            onAuth(data.user, data.token);
        } catch {
            setError("Network error — is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    if (mode === "welcome") {
        return (
            <div className="fixed inset-0 z-[150] flex items-center justify-center bg-gradient-to-br from-dark-navy via-slate-900 to-dark-navy overflow-hidden">
                <div className="w-full max-w-md h-screen flex flex-col bg-gradient-to-br from-dark-navy via-slate-900 to-dark-navy">
                {/* Tricolor ambient blobs */}
                <div className="absolute top-1/4 left-[-5%] w-80 h-80 bg-saffron/15 rounded-full blur-[120px]" />
                <div className="absolute bottom-1/4 right-[-5%] w-64 h-64 bg-india-green/15 rounded-full blur-[100px]" />

                <div className="flex-1 flex flex-col items-center justify-center px-8 relative z-10">
                    {/* Logo mark */}
                    <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-saffron/20 via-ashoka-blue/20 to-india-green/20 backdrop-blur border border-white/20 flex items-center justify-center mb-8 shadow-2xl">
                        <div className="text-7xl">🍽️</div>
                    </div>

                    {/* Title with tricolor */}
                    <h1 className="text-5xl font-black text-white text-center leading-tight mb-2">
                        MA-Shabari
                    </h1>
                    <p className="text-2xl font-black text-center mb-2">
                        <span className="bg-gradient-to-r from-saffron via-white to-india-green bg-clip-text text-transparent">AI</span>
                    </p>

                    {/* Tagline */}
                    <p className="text-white/60 text-sm font-medium tracking-wider text-center mb-12">
                        Personalized Indian Meal Planning
                    </p>

                    {/* CTA Buttons */}
                    <div className="w-full space-y-3">
                        <button
                            onClick={() => setMode("login")}
                            className="w-full h-14 bg-gradient-to-r from-saffron to-india-green text-white rounded-2xl font-black text-sm uppercase tracking-widest active:scale-95 transition-all"
                        >
                            Sign In
                        </button>
                        <button
                            onClick={() => setMode("register")}
                            className="w-full h-14 bg-gradient-to-r from-ashoka-blue to-indigo-900 text-white rounded-2xl font-black text-sm uppercase tracking-widest active:scale-95 transition-all"
                        >
                            Create Account
                        </button>
                    </div>
                </div>
            </div>
            </div>
        );
    }

    // Login / Register mode
    return (
        <div className="fixed inset-0 z-[150] flex items-center justify-center bg-gradient-to-br from-dark-navy via-slate-900 to-dark-navy overflow-hidden">
            <div className="w-full max-w-md h-screen flex flex-col bg-gradient-to-br from-dark-navy via-slate-900 to-dark-navy">
                {/* Header with back button */}
                <div className="flex items-center justify-between p-6 relative z-10">
                <button
                    onClick={() => { setMode("welcome"); setError(""); }}
                    className="w-10 h-10 flex items-center justify-center rounded-lg bg-ashoka-blue/20 hover:bg-ashoka-blue/40 text-blue-300 hover:text-white transition-all text-2xl"
                >
                    ←
                </button>
                <h2 className="text-white font-black text-lg capitalize">{mode === "login" ? "Sign In" : "Create Account"}</h2>
                <div className="w-8" />
            </div>

            {/* Form */}
            <div className="flex-1 flex flex-col items-center justify-center px-8 pb-12 relative z-10">
                <div className="w-full space-y-4">
                    {mode === "register" && (
                        <input
                            type="text"
                            placeholder="Your Name"
                            value={form.name}
                            onChange={(e) => update("name", e.target.value)}
                            className="w-full h-12 px-4 rounded-xl bg-orange-500/10 backdrop-blur border-2 border-orange-400/40 text-white placeholder-white/50 focus:border-saffron focus:bg-orange-500/20 focus:outline-none transition-all"
                        />
                    )}
                    <input
                        type="email"
                        placeholder="Email"
                        value={form.email}
                        onChange={(e) => update("email", e.target.value)}
                        className="w-full h-12 px-4 rounded-xl bg-blue-500/10 backdrop-blur border-2 border-blue-400/40 text-white placeholder-white/50 focus:border-saffron focus:bg-blue-500/20 focus:outline-none transition-all"
                    />
                    <input
                        type="password"
                        placeholder="Password (min 6 chars)"
                        value={form.password}
                        onChange={(e) => update("password", e.target.value)}
                        className="w-full h-12 px-4 rounded-xl bg-purple-500/10 backdrop-blur border-2 border-purple-400/40 text-white placeholder-white/50 focus:border-india-green focus:bg-purple-500/20 focus:outline-none transition-all"
                    />

                    {/* Error message */}
                    {error && (
                        <div className="px-4 py-3 rounded-xl bg-red-500/20 border-2 border-red-400/60 text-red-100 text-xs font-bold text-center shadow-lg shadow-red-500/20">
                            {error}
                        </div>
                    )}

                    {/* Submit button */}
                    <button
                        onClick={submit}
                        disabled={loading}
                        className="w-full h-14 bg-gradient-to-r from-saffron to-india-green text-white rounded-2xl font-black text-sm uppercase tracking-widest active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-6"
                    >
                        {loading ? "Processing..." : mode === "login" ? "Sign In" : "Create Account"}
                    </button>
                </div>
            </div>
            </div>
        </div>
    );
}

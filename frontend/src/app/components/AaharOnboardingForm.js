"use client";
import { useState } from "react";

const API_BASE_URL = typeof process.env.NEXT_PUBLIC_API_URL === "string"
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")
    : "http://127.0.0.1:5001";

const INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
];

export default function AaharOnboardingForm({ onComplete }) {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [profile, setProfile] = useState({
        age: "",
        gender: "",
        weight: "",
        height: "",
        diet_type: "",
        state: "",
        cuisine: "",
        health_goal: "",
        weekly_budget: "2000",
        activity_level: "",
    });

    const updateProfile = (key, value) => {
        setProfile(p => ({ ...p, [key]: value }));
    };

    const handleNext = () => {
        if (step < 4) setStep(step + 1);
    };

    const handleBack = () => {
        if (step > 1) setStep(step - 1);
    };

    const handleComplete = async () => {
        setLoading(true);
        try {
            // Create profile object
            const profileData = {
                age: parseInt(profile.age),
                gender: profile.gender,
                weight: parseFloat(profile.weight),
                height: parseFloat(profile.height),
                diet_type: profile.diet_type,
                state: profile.state.toLowerCase(),
                cuisine: profile.cuisine.toLowerCase(),
                health_goal: profile.health_goal,
                weekly_budget: parseInt(profile.weekly_budget),
                activity_level: profile.activity_level,
            };

            // Try to submit to backend
            let success = false;
            try {
                const token = localStorage.getItem("aa_token");
                console.log("📤 Submitting profile with token:", token?.substring(0, 20) + "...");
                
                if (!token) {
                    throw new Error("No authentication token found. Please login first.");
                }
                
                const res = await fetch(`${API_BASE_URL}/api/profile`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`,
                    },
                    body: JSON.stringify(profileData),
                });

                console.log("📥 Profile response status:", res.status);
                
                const responseData = await res.json();
                console.log("📥 Profile response data:", responseData);

                if (res.ok) {
                    success = true;
                    console.log("✅ Profile saved successfully!");
                    
                    // Update profile_complete flag in localStorage (don't cache profile data)
                    const user = JSON.parse(localStorage.getItem("aa_user") || "{}");
                    user.profile_complete = true;
                    // ⚠️ Don't cache profile data - always fetch from backend via /api/profile
                    localStorage.setItem("aa_user", JSON.stringify(user));

                    onComplete();
                } else {
                    throw new Error(`Backend error: ${res.status} - ${JSON.stringify(responseData)}`);
                }
            } catch (backendError) {
                console.error("❌ Profile save failed:", backendError.message);
                alert("Error saving profile: " + backendError.message);
                setLoading(false);
                return;
            }
        } catch (error) {
            console.error("Profile error:", error);
            alert("Error saving profile: " + error.message);
        } finally {
            setLoading(false);
        }
    };

    const progressPercent = (step / 4) * 100;

    return (
        <div className="fixed inset-0 z-[140] flex flex-col bg-warm-cream max-w-md mx-auto w-full">
            {/* Progress bar */}
            <div className="sticky top-0 z-50 bg-white/80 backdrop-blur border-b border-slate-200 shrink-0">
                <div className="h-1 bg-gradient-to-r from-slate-100 via-orange-100 to-slate-100 rounded-full">
                    <div
                        className="h-full bg-gradient-to-r from-saffron via-yellow-400 to-india-green transition-all duration-300 rounded-full"
                        style={{ width: `${progressPercent}%` }}
                    />
                </div>
                <div className="px-6 py-4 flex items-center justify-between bg-gradient-to-r from-orange-50/50 to-transparent">
                    <h1 className="text-lg font-black bg-gradient-to-r from-dark-navy to-saffron bg-clip-text text-transparent">Your Profile</h1>
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">Step {step}/4</span>
                </div>
            </div>

            {/* Content - scrollable */}
            <div className="flex-1 overflow-y-auto px-6 py-8 pb-32">

                {/* STEP 1: Physical Stats */}
                {step === 1 && (
                    <div className="animate-slide-up space-y-6">
                        <h2 className="text-3xl font-black text-dark-navy mb-8">Physical Stats</h2>

                        <div>
                            <label className="block text-sm font-bold text-black mb-2">Age (10-100) <span className="text-red-500">*</span></label>
                            <input
                                type="number"
                                min="10"
                                max="100"
                                placeholder="e.g., 25"
                                required
                                value={profile.age}
                                onChange={(e) => updateProfile("age", e.target.value)}
                                className="w-full h-12 px-4 rounded-xl border-2 border-orange-300 bg-orange-50/50 focus:border-saffron focus:bg-orange-100/50 focus:outline-none transition-all text-slate-900 font-semibold"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-black mb-3">Gender <span className="text-red-500">*</span></label>
                            <div className="flex gap-3">
                                {["Male", "Female", "Other"].map(g => (
                                    <button
                                        key={g}
                                        onClick={() => updateProfile("gender", g)}
                                        className={`flex-1 h-12 rounded-xl font-bold text-sm transition-all border-2 ${
                                            profile.gender === g
                                                ? "bg-gradient-to-r from-saffron via-yellow-400 to-india-green text-white border-transparent"
                                                : "bg-orange-50/60 text-orange-700 hover:bg-orange-100 border-orange-300/50 hover:border-orange-400"
                                        }`}
                                    >
                                        {g}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-black mb-2">Weight (kg) <span className="text-red-500">*</span></label>
                            <input
                                type="number"
                                placeholder="e.g., 70"
                                required
                                value={profile.weight}
                                onChange={(e) => updateProfile("weight", e.target.value)}
                                className="w-full h-12 px-4 rounded-xl border-2 border-red-300 bg-red-50/50 focus:border-saffron focus:bg-red-100/50 focus:outline-none transition-all text-slate-900 font-semibold"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-black mb-2">Height (cm) <span className="text-red-500">*</span></label>
                            <input
                                type="number"
                                placeholder="e.g., 175"
                                required
                                value={profile.height}
                                onChange={(e) => updateProfile("height", e.target.value)}
                                className="w-full h-12 px-4 rounded-xl border-2 border-blue-300 bg-blue-50/50 focus:border-india-green focus:bg-blue-100/50 focus:outline-none transition-all text-slate-900 font-semibold"
                            />
                        </div>
                    </div>
                )}

                {/* STEP 2: Your Food World */}
                {step === 2 && (
                    <div className="animate-slide-up space-y-6">
                        <h2 className="text-3xl font-black text-dark-navy mb-8">Your Food World</h2>

                        <div>
                            <label className="block text-sm font-bold text-black mb-3">Diet Type <span className="text-red-500">*</span></label>
                            <div className="space-y-2">
                                {[
                                    { label: "🌱 Vegetarian", val: "veg" },
                                    { label: "🥚 Eggetarian", val: "eggetarian" },
                                    { label: "🍗 Non-Veg", val: "non-veg" },
                                    { label: "🌿 Vegan", val: "vegan" },
                                    { label: "🙏 Jain", val: "jain" },
                                    { label: "☮️ Satvik", val: "satvik" },
                                ].map(d => (
                                    <button
                                        key={d.val}
                                        onClick={() => updateProfile("diet_type", d.val)}
                                        className={`w-full h-12 rounded-xl font-semibold text-sm transition-all px-4 text-left border-2 ${
                                            profile.diet_type === d.val
                                                ? "bg-gradient-to-r from-saffron to-india-green text-white border-transparent"
                                                : "bg-green-50/60 text-green-700 hover:bg-green-100 border-green-300/50 hover:border-green-400"
                                        }`}
                                    >
                                        {d.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-black mb-2">State / Region <span className="text-red-500">*</span></label>
                            <select
                                value={profile.state}
                                onChange={(e) => updateProfile("state", e.target.value)}
                                required
                                className="w-full h-12 px-4 rounded-xl border-2 border-green-300 bg-green-50/50 focus:border-india-green focus:bg-green-100/50 focus:outline-none transition-all text-slate-900 font-semibold"
                            >
                                <option value="">Select a state...</option>
                                {INDIAN_STATES.map(s => (
                                    <option key={s} value={s}>{s}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-black mb-3">Cuisine Preference <span className="text-red-500">*</span></label>
                            <div className="flex gap-3 flex-wrap">
                                {["South Indian", "North Indian", "Coastal", "East Indian", "No preference"].map(c => (
                                    <button
                                        key={c}
                                        onClick={() => updateProfile("cuisine", c)}
                                        className={`px-4 h-10 rounded-full font-bold text-xs transition-all border-2 ${
                                            profile.cuisine === c
                                                ? "bg-gradient-to-r from-saffron to-india-green text-white border-transparent"
                                                : "bg-orange-50/60 text-orange-700 hover:bg-orange-100 border-orange-300/50 hover:border-orange-400"
                                        }`}
                                    >
                                        {c}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* STEP 3: Health Goal */}
                {step === 3 && (
                    <div className="animate-slide-up space-y-4">
                        <h2 className="text-3xl font-black text-dark-navy mb-8">Health Goal <span className="text-red-500">*</span></h2>

                        <div className="space-y-3">
                            {[
                                { label: "🏃 Lose Weight", val: "lose_weight" },
                                { label: "💪 Gain Muscle", val: "gain_muscle" },
                                { label: "🥗 Stay Healthy", val: "stay_healthy" },
                                { label: "🤰 Pregnancy Nutrition", val: "pregnancy" },
                                { label: "🩺 Manage Diabetes", val: "diabetes" },
                                { label: "💊 PCOD / Hormonal Health", val: "pcod" },
                                { label: "👴 Senior Nutrition", val: "senior" },
                            ].map(g => (
                                <button
                                    key={g.val}
                                    onClick={() => updateProfile("health_goal", g.val)}
                                    className={`w-full h-16 rounded-2xl font-bold text-base transition-all px-4 border-2 ${
                                        profile.health_goal === g.val
                                            ? g.val === "gain_muscle" 
                                                ? "bg-gradient-to-r from-saffron to-india-green text-black scale-105 border-transparent"
                                                : "bg-gradient-to-r from-saffron to-india-green text-white scale-105 border-transparent"
                                            : "bg-indigo-50/60 text-indigo-700 hover:bg-indigo-100 border-indigo-300/50 hover:border-indigo-400"
                                    }`}
                                >
                                    {g.label}
                                </button>
                            ))}
]
                        </div>
                    </div>
                )}

                {/* STEP 4: Budget & Family */}
                {step === 4 && (
                    <div className="animate-slide-up space-y-6">
                        <h2 className="text-3xl font-black text-dark-navy mb-8">Budget & Family</h2>

                        <div>
                            <label className="block text-sm font-bold text-black mb-3">Weekly Budget <span className="text-red-500">*</span></label>
                            <div className="block text-sm font-bold text-black mb-2">₹{profile.weekly_budget}</div>
                            <input
                                type="range"
                                min="500"
                                max="5000"
                                step="100"
                                value={profile.weekly_budget}
                                onChange={(e) => updateProfile("weekly_budget", e.target.value)}
                                className="w-full h-2 bg-gradient-to-r from-yellow-200 to-orange-200 rounded-lg appearance-none cursor-pointer accent-saffron"
                            />
                            <p className="text-xs text-slate-600 mt-2 font-semibold bg-gradient-to-r from-saffron/10 to-india-green/10 px-3 py-2 rounded-lg border border-saffron/20">
                                ₹{Math.round(profile.weekly_budget / 7)} per person per day
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-bold text-black mb-3">Activity Level <span className="text-red-500">*</span></label>
                            <div className="space-y-2">
                                {["Sedentary", "Light", "Moderate", "Active"].map(a => (
                                    <button
                                        key={a}
                                        onClick={() => updateProfile("activity_level", a.toLowerCase())}
                                        className={`w-full h-12 rounded-xl font-semibold text-sm transition-all px-4 text-left border-2 ${
                                            profile.activity_level === a.toLowerCase()
                                                ? "bg-gradient-to-r from-saffron to-india-green text-white border-transparent"
                                                : "bg-blue-50/60 text-blue-700 hover:bg-blue-100 border-blue-300/50 hover:border-blue-400"
                                        }`}
                                    >
                                        {a}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

            </div>

            {/* Navigation buttons - fixed at bottom */}
            <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto w-full bg-white/80 backdrop-blur border-t border-slate-200 px-6 py-4 flex gap-3 z-40">
                <button
                    onClick={handleBack}
                    disabled={step === 1}
                    className="flex-1 h-12 rounded-xl border-2 border-ashoka-blue/50 text-ashoka-blue font-bold text-sm uppercase tracking-wide hover:bg-ashoka-blue/10 hover:border-ashoka-blue disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                    Back
                </button>
                {step < 4 ? (
                    <button
                        onClick={handleNext}
                        className="flex-1 h-12 rounded-xl bg-gradient-to-r from-india-green to-green-600 text-white font-bold text-sm uppercase tracking-wide transition-all active:scale-95"
                    >
                        Next
                    </button>
                ) : (
                    <button
                        onClick={handleComplete}
                        disabled={loading}
                        className="flex-1 h-12 rounded-xl bg-gradient-to-r from-india-green to-saffron text-white font-bold text-sm uppercase tracking-wide transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? "Saving..." : "Complete"}
                    </button>
                )}
            </div>
        </div>
    );
}

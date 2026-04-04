"use client";

import { useState, useEffect } from "react";
import MealPlanViewer from "./MealPlanViewer";
import LanguageSelector from "./LanguageSelector";

export default function AaharProfileTab({ user, token, onSignOut, onEditProfile }) {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showMealPlan, setShowMealPlan] = useState(false);
    const firstName = user?.name?.split(" ")[0] || "User";

    // Fetch profile data from backend
    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const headers = {};
                if (token) {
                    headers["Authorization"] = `Bearer ${token}`;
                }
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001"}/api/profile`, {
                    method: "GET",
                    headers,
                });
                if (res.ok) {
                    const data = await res.json();
                    console.log("✅ Profile fetched:", data);
                    setProfile(data);
                } else {
                    console.error("❌ Profile fetch failed:", res.status, res.statusText);
                }
            } catch (err) {
                console.error("❌ Profile fetch error:", err);
            } finally {
                setLoading(false);
            }
        };

        if (token) {
            console.log("🔄 Fetching profile with token:", token?.substring(0, 20) + "...");
            fetchProfile();
        } else {
            console.warn("⚠️ No token found");
            setLoading(false);
        }
    }, [token, user?.profile_complete]);
    const healthGoals = {
        lose_weight: "🏃 Lose Weight",
        gain_muscle: "💪 Gain Muscle",
        stay_healthy: "🥗 Stay Healthy",
        pregnancy: "🤰 Pregnancy Nutrition",
        diabetes: "🩺 Manage Diabetes",
        pcod: "💊 PCOD / Hormonal Health",
        senior: "👴 Senior Nutrition",
    };

    const dietTypes = {
        veg: "🌱 Vegetarian",
        eggetarian: "🥚 Eggetarian",
        "non-veg": "🍗 Non-Veg",
        vegan: "🌿 Vegan",
        jain: "🙏 Jain",
        satvik: "☮️ Satvik",
    };

    return (
        <>
            {showMealPlan && (
                <MealPlanViewer 
                    token={token} 
                    onClose={() => setShowMealPlan(false)} 
                />
            )}
            <div className="px-5 py-5 pb-32">
            {/* Loading state */}
            {loading && (
                <div className="flex items-center justify-center py-12">
                    <div className="w-8 h-8 border-3 border-saffron border-t-transparent rounded-full animate-spin"></div>
                </div>
            )}

            {/* Profile content */}
            {!loading && (
                <>
                    {/* Profile header */}
                    <div className="mb-8 text-center">
                        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-saffron via-ashoka-blue to-india-green flex items-center justify-center text-white font-black text-5xl shadow-lg mx-auto mb-4">
                            {firstName.charAt(0).toUpperCase()}
                        </div>
                        <h1 className="text-3xl font-black text-dark-navy">{user?.name}</h1>
                        <p className="text-sm text-slate-500 font-medium mt-1">{user?.email}</p>
                    </div>

                    {/* Profile complete status */}
                    {profile?.profile_complete ? (
                        <div className="mb-6 text-center">
                            <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-full px-4 py-2">
                                <span className="text-lg">✅</span>
                                <span className="text-xs font-bold text-emerald-600">Profile Complete</span>
                            </div>
                        </div>
                    ) : (
                        <div className="mb-6 text-center">
                            <button
                                onClick={onEditProfile}
                                className="inline-flex items-center gap-2 bg-orange-50 border border-orange-200 rounded-full px-4 py-2 hover:bg-orange-100"
                            >
                                <span className="text-lg">⚙️</span>
                                <span className="text-xs font-bold text-orange-600">Complete Profile</span>
                            </button>
                        </div>
                    )}

                    {/* Health goal badge */}
                    {profile?.health_goal && (
                        <div className="mb-6">
                            <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-2">Health Goal</p>
                            <div className={`inline-block bg-gradient-to-r from-saffron to-india-green ${profile.health_goal === 'gain_muscle' ? 'text-black' : 'text-white'} px-6 py-2 rounded-full font-bold text-sm`}>
                                {healthGoals[profile.health_goal] || profile.health_goal}
                            </div>
                        </div>
                    )}

                    {/* Language Selector */}
                    <div className="mb-6">
                        <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-3">🌐 Language</p>
                        <LanguageSelector />
                    </div>

                    {/* Step 1: Biometrics */}
                    {(profile?.age || profile?.gender || profile?.weight || profile?.height) && (
                        <div className="mb-6">
                            <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-3">📊 Biometrics (Step 1)</p>
                            <div className="grid grid-cols-2 gap-3">
                                {profile?.age && (
                                    <div className="bg-orange-50 rounded-xl p-4 border border-orange-100 text-center">
                                        <p className="text-xs text-slate-500 font-bold mb-1">Age</p>
                                        <p className="text-2xl font-black text-saffron">{profile.age}</p>
                                        <p className="text-xs text-slate-400 mt-1">years</p>
                                    </div>
                                )}
                                {profile?.gender && (
                                    <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 text-center">
                                        <p className="text-xs text-slate-500 font-bold mb-1">Gender</p>
                                        <p className="text-lg font-black text-ashoka-blue capitalize">{profile.gender}</p>
                                    </div>
                                )}
                                {profile?.weight && (
                                    <div className="bg-red-50 rounded-xl p-4 border border-red-100 text-center">
                                        <p className="text-xs text-slate-500 font-bold mb-1">Weight</p>
                                        <p className="text-2xl font-black text-red-600">{profile.weight}</p>
                                        <p className="text-xs text-slate-400 mt-1">kg</p>
                                    </div>
                                )}
                                {profile?.height && (
                                    <div className="bg-blue-50 rounded-xl p-4 border border-blue-100 text-center">
                                        <p className="text-xs text-slate-500 font-bold mb-1">Height</p>
                                        <p className="text-2xl font-black text-ashoka-blue">{profile.height}</p>
                                        <p className="text-xs text-slate-400 mt-1">cm</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Step 2: Preferences */}
                    {(profile?.diet_type || profile?.state || profile?.cuisine) && (
                        <div className="mb-6">
                            <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-3">🌾 Preferences (Step 2)</p>
                            <div className="space-y-3">
                                {profile?.diet_type && (
                                    <div className="bg-white rounded-xl p-4 border border-slate-100">
                                        <p className="text-xs text-slate-500 font-bold mb-2">Diet Type</p>
                                        <span className="inline-block bg-gradient-to-r from-green-50 to-emerald-50 text-green-700 px-4 py-2 rounded-lg font-bold text-sm">
                                            {dietTypes[profile.diet_type] || profile.diet_type}
                                        </span>
                                    </div>
                                )}
                                {profile?.state && (
                                    <div className="bg-white rounded-xl p-4 border border-slate-100">
                                        <p className="text-xs text-slate-500 font-bold mb-2">Region</p>
                                        <span className="text-sm font-bold text-dark-navy">📍 {profile.state}</span>
                                    </div>
                                )}
                                {profile?.cuisine && (
                                    <div className="bg-white rounded-xl p-4 border border-slate-100">
                                        <p className="text-xs text-slate-500 font-bold mb-2">Cuisine Preference</p>
                                        <span className="text-sm font-bold text-dark-navy">🍛 {profile.cuisine}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Step 4: Lifestyle */}
                    {(profile?.activity_level || profile?.weekly_budget) && (
                        <div className="mb-6">
                            <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-3">💰 Lifestyle (Step 4)</p>
                            <div className="space-y-3">
                                {profile?.activity_level && (
                                    <div className="bg-white rounded-xl p-4 border border-slate-100">
                                        <p className="text-xs text-slate-500 font-bold mb-2">Activity Level</p>
                                        <span className="inline-block bg-blue-50 text-blue-700 px-4 py-2 rounded-lg font-bold text-sm capitalize">
                                            {profile.activity_level}
                                        </span>
                                    </div>
                                )}
                                {profile?.weekly_budget && (
                                    <div className="bg-white rounded-xl p-4 border border-slate-100">
                                        <p className="text-xs text-slate-500 font-bold mb-2">Weekly Budget</p>
                                        <p className="text-2xl font-black text-saffron mb-1">₹{profile.weekly_budget}</p>
                                        <p className="text-xs text-slate-500">₹{Math.round(profile.weekly_budget / 7)} per person per day</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Health Metrics - Calorie Requirements */}
                    {profile?.health_metrics && (
                        <div className="mb-6">
                            <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-3">🔥 Daily Calorie Requirements</p>
                            <div className="grid grid-cols-1 gap-3">
                                {/* Daily Calories - Primary */}
                                <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-5 border-2 border-orange-200">
                                    <p className="text-xs text-slate-600 font-bold mb-2">🎯 Target Daily Calories</p>
                                    <p className="text-4xl font-black text-orange-600 mb-1">
                                        {profile.health_metrics.daily_calories?.toFixed(0)}
                                    </p>
                                    <p className="text-xs text-slate-500">kcal per day</p>
                                </div>

                                {/* BMR and TDEE in 2-column grid */}
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                                        <p className="text-xs text-slate-500 font-bold mb-2">BMR</p>
                                        <p className="text-2xl font-black text-blue-600">
                                            {profile.health_metrics.bmr?.toFixed(0)}
                                        </p>
                                        <p className="text-xs text-slate-400 mt-1">Resting Calories</p>
                                    </div>
                                    <div className="bg-purple-50 rounded-xl p-4 border border-purple-100">
                                        <p className="text-xs text-slate-500 font-bold mb-2">TDEE</p>
                                        <p className="text-2xl font-black text-purple-600">
                                            {profile.health_metrics.tdee?.toFixed(0)}
                                        </p>
                                        <p className="text-xs text-slate-400 mt-1">Total Daily</p>
                                    </div>
                                </div>

                                {/* Info text */}
                                <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                                    <p className="text-xs text-slate-600">
                                        <span className="font-bold">💡 Tip:</span> Your daily calorie target is calculated based on your age, gender, weight, height, and activity level. Adjust your diet accordingly to meet your health goals.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}



                    {/* No profile message */}
                    {!profile?.profile_complete && !profile?.age && (
                        <div className="bg-orange-50 border border-orange-200 rounded-xl p-6 text-center mb-6">
                            <p className="text-sm text-orange-700 font-bold mb-4">Complete your profile to get personalized meal plans!</p>
                            <button
                                onClick={onEditProfile}
                                className="w-full h-12 bg-gradient-to-r from-saffron to-india-green text-white rounded-lg font-black text-sm"
                            >
                                Start Onboarding →
                            </button>
                        </div>
                    )}
                </>
            )}

            {/* Action buttons */}
            <div className="mt-12 space-y-3 pb-4">
                <button
                    onClick={onEditProfile}
                    className="w-full h-14 bg-gradient-to-r from-saffron to-india-green text-black rounded-xl font-black text-sm uppercase tracking-widest transition-all active:scale-95"
                >
                    ✏️ Edit Profile
                </button>
                <button
                    onClick={onSignOut}
                    className="w-full h-14 bg-red-50 border-2 border-red-400/50 text-red-600 rounded-xl font-black text-sm uppercase tracking-widest hover:bg-red-100 hover:border-red-500 active:scale-95 transition-all"
                >
                    🚪 Sign Out
                </button>
            </div>
            </div>
        </>
    );
}

"use client";

import { useState, useEffect } from "react";

export default function MealPlanViewer({ token, onClose }) {
    const [mealPlan, setMealPlan] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedDay, setSelectedDay] = useState(0);
    const [loadingPhase, setLoadingPhase] = useState(0);
    const [cachedResult, setCachedResult] = useState(false);

    useEffect(() => {
        fetchMealPlan();
    }, [token]);

    const fetchMealPlan = async () => {
        setLoading(true);
        setError(null);
        setCachedResult(false);
        setLoadingPhase(0);
        
        try {
            // Simulate phase progress
            const phaseInterval = setInterval(() => {
                setLoadingPhase(prev => (prev < 3 ? prev + 1 : 3));
            }, 2000);

            const startTime = Date.now();
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001"}/api/meal-plan`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            const elapsedTime = Date.now() - startTime;
            
            clearInterval(phaseInterval);

            if (!response.ok) {
                throw new Error(`Failed to fetch meal plan: ${response.status}`);
            }

            const data = await response.json();
            console.log("✅ Meal plan fetched:", data);
            
            // If response was faster than 2 seconds, it was likely cached
            if (elapsedTime < 2000) {
                setCachedResult(true);
            }
            
            setMealPlan(data);
            setSelectedDay(0);
        } catch (err) {
            console.error("❌ Error fetching meal plan:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const loadingMessages = [
        "🔐 Authenticating...",
        "🍽️ Generating meal plan with AI...",
        "📊 Calculating nutrition & budget...",
        "✅ Finalizing meal plan...",
    ];

    if (loading) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-white rounded-2xl p-8 max-w-sm w-full mx-4">
                    <div className="flex flex-col items-center gap-4">
                        {/* Spinner */}
                        <div className="relative w-14 h-14">
                            <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
                            <div className="absolute inset-0 border-4 border-transparent border-t-saffron border-r-india-green rounded-full animate-spin"></div>
                        </div>
                        
                        {/* Phase messages */}
                        <div className="text-center">
                            <p className="text-sm font-bold text-slate-700 min-h-5">
                                {loadingMessages[loadingPhase]}
                            </p>
                            <p className="text-xs text-slate-500 mt-2">
                                First-time generation takes 30-60 seconds
                            </p>
                        </div>

                        {/* Progress bar */}
                        <div className="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
                            <div 
                                className="h-full bg-gradient-to-r from-saffron to-india-green transition-all duration-500"
                                style={{ width: `${(loadingPhase / 3) * 100}%` }}
                            />
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-white rounded-2xl p-6 max-w-sm w-full mx-4">
                    <div className="text-center">
                        <p className="text-xl font-black text-red-600 mb-2">❌ Error</p>
                        <p className="text-xs text-slate-500 mb-4">Generation failed</p>
                        <p className="text-sm text-slate-700 mb-6 bg-red-50 p-3 rounded-lg">{error}</p>
                        <button
                            onClick={fetchMealPlan}
                            className="w-full bg-saffron text-white font-bold py-3 rounded-xl hover:bg-orange-600 transition-all active:scale-95"
                        >
                            🔄 Try Again
                        </button>
                        <button
                            onClick={onClose}
                            className="w-full mt-2 bg-slate-100 text-slate-700 font-bold py-3 rounded-xl hover:bg-slate-200 transition-all active:scale-95"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (!mealPlan) {
        return null;
    }

    const weeklyPlan = mealPlan.weekly_plan || [];
    const currentDay = weeklyPlan[selectedDay] || mealPlan.today_plan;
    const todayPlan = mealPlan.today_plan || {};
    const groceryList = mealPlan.grocery_list || [];

    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

    return (
        <div className="fixed inset-0 bg-black/50 flex items-end z-50 overflow-y-auto">
            <div className="w-full bg-white rounded-t-3xl max-h-screen overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-gradient-to-r from-saffron to-india-green text-white px-6 py-6 flex items-center justify-between gap-4">
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            <h2 className="text-2xl font-black">Your Meal Plan</h2>
                            {cachedResult && (
                                <span className="text-xs font-bold bg-white/30 px-2 py-1 rounded-full">
                                    ⚡ Instant
                                </span>
                            )}
                        </div>
                        <p className="text-sm opacity-90">
                            {weeklyPlan.length} days personalized just for you
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-2xl font-bold hover:opacity-80 transition"
                    >
                        ✕
                    </button>
                </div>

                <div className="px-5 py-6 pb-32">
                    {/* Day Selector */}
                    <div className="mb-6">
                        <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-3">
                            📅 Select Day
                        </p>
                        <div className="flex gap-2 overflow-x-auto pb-2">
                            {weeklyPlan.map((dayPlan, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => setSelectedDay(idx)}
                                    className={`px-4 py-3 rounded-xl font-bold text-sm min-w-fit transition-all ${
                                        selectedDay === idx
                                            ? "bg-gradient-to-r from-saffron to-india-green text-white shadow-lg"
                                            : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                                    }`}
                                >
                                    {dayPlan.day?.substring(0, 3) || days[idx]?.substring(0, 3)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Today's Highlight */}
                    {selectedDay === 0 && todayPlan.day && (
                        <div className="mb-6 p-4 bg-gradient-to-r from-orange-50 to-amber-50 border-l-4 border-saffron rounded-lg">
                            <p className="text-xs font-bold text-saffron uppercase tracking-wide">
                                🌅 Today's Meal Plan
                            </p>
                            <p className="text-sm text-slate-700 mt-1">
                                This is your personalized meal plan for today
                            </p>
                        </div>
                    )}

                    {/* Daily Calorie Info */}
                    <div className="mb-6">
                        <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-3">
                            🔥 Daily Food
                        </p>
                        <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-5 border-2 border-orange-200">
                            <p className="text-xs text-slate-600 font-bold mb-2">Total Calories</p>
                            <p className="text-4xl font-black text-orange-600">
                                {currentDay?.total_calories?.toFixed(0) || 0}
                            </p>
                            <p className="text-xs text-slate-500 mt-1">kcal for the day</p>
                        </div>
                    </div>

                    {/* Meals Section */}
                    <div className="mb-8">
                        <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-4">
                            🍽️ Meals for {currentDay?.day || "This Day"}
                        </p>

                        <div className="space-y-4">
                            {/* Breakfast */}
                            {currentDay?.meals?.breakfast && (
                                <MealCard
                                    emoji="🌅"
                                    mealType="Breakfast"
                                    meal={currentDay.meals.breakfast}
                                />
                            )}

                            {/* Lunch */}
                            {currentDay?.meals?.lunch && (
                                <MealCard
                                    emoji="🍲"
                                    mealType="Lunch"
                                    meal={currentDay.meals.lunch}
                                />
                            )}

                            {/* Dinner */}
                            {currentDay?.meals?.dinner && (
                                <MealCard
                                    emoji="🍽️"
                                    mealType="Dinner"
                                    meal={currentDay.meals.dinner}
                                />
                            )}

                            {/* Snacks */}
                            {currentDay?.meals?.snacks && currentDay.meals.snacks.length > 0 && (
                                <div>
                                    <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-2 mt-4">
                                        🥜 Snacks
                                    </p>
                                    <div className="space-y-2">
                                        {currentDay.meals.snacks.map((snack, idx) => (
                                            <MealCard
                                                key={idx}
                                                emoji="🥤"
                                                mealType={`Snack ${idx + 1}`}
                                                meal={snack}
                                            />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Grocery List */}
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <p className="text-xs font-bold text-slate-600 uppercase tracking-wide">
                                🛒 Weekly Grocery List
                            </p>
                            <p className="text-sm font-bold text-saffron">
                                ₹{mealPlan.total_estimated_cost?.toFixed(0) || 0}
                            </p>
                        </div>

                        <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                            <div className="grid grid-cols-2 gap-3 max-h-64 overflow-y-auto">
                                {groceryList.slice(0, 20).map((item, idx) => (
                                    <div
                                        key={idx}
                                        className="bg-white rounded-lg p-3 border border-slate-100"
                                    >
                                        <p className="text-xs font-bold text-slate-700">
                                            {item.item}
                                        </p>
                                        <p className="text-xs text-slate-500 mt-1">
                                            {item.quantity}
                                        </p>
                                        <p className="text-xs font-bold text-saffron mt-2">
                                            ₹{item.estimated_cost}
                                        </p>
                                    </div>
                                ))}
                            </div>
                            {groceryList.length > 20 && (
                                <p className="text-xs text-slate-500 mt-3 text-center">
                                    ... and {groceryList.length - 20} more items
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Budget Summary */}
                    <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-xs font-bold text-slate-600 mb-1">
                                    💰 Total Grocery Budget
                                </p>
                                <p className="text-2xl font-black text-green-600">
                                    ₹{mealPlan.total_estimated_cost?.toFixed(0) || 0}
                                </p>
                            </div>
                            <div className="text-right">
                                <p className="text-xs text-slate-600 font-bold mb-1">Budget per day</p>
                                <p className="text-xl font-black text-green-600">
                                    ₹
                                    {(
                                        (mealPlan.total_estimated_cost || 0) / 7
                                    ).toFixed(0)}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="space-y-3 mb-4">
                        <button
                            onClick={fetchMealPlan}
                            className="w-full bg-gradient-to-r from-saffron to-india-green text-white font-bold py-3 rounded-xl hover:shadow-lg transition"
                        >
                            🔄 Regenerate Meal Plan
                        </button>
                        <button
                            onClick={onClose}
                            className="w-full bg-slate-200 text-slate-700 font-bold py-3 rounded-xl hover:bg-slate-300 transition"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function MealCard({ emoji, mealType, meal }) {
    return (
        <div className="bg-white rounded-xl p-4 border-2 border-slate-150 hover:border-saffron hover:shadow-md transition">
            <div className="flex items-start gap-3 mb-3">
                <span className="text-4xl">{emoji}</span>
                <div className="flex-1">
                    <h3 className="font-black text-dark-navy text-sm">{mealType}</h3>
                    <p className="text-xs text-slate-600 font-medium mt-0.5">
                        {meal.meal}
                    </p>
                </div>
                <span className="text-xs font-bold text-white bg-saffron px-3 py-1 rounded-full whitespace-nowrap">
                    {meal.calories} cal
                </span>
            </div>
            <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                <p className="text-xs text-slate-600">
                    <span className="font-bold">📏 Portion:</span> {meal.portion}
                </p>
            </div>
        </div>
    );
}

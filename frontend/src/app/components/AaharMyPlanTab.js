"use client";
import { useState, useEffect } from "react";

export default function AaharMyPlanTab({ token }) {
    const [selectedDay, setSelectedDay] = useState(0);
    const [mealPlan, setMealPlan] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const fullDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

    useEffect(() => {
        fetchMealPlan();
    }, [token]);

    const fetchMealPlan = async () => {
        if (!token) {
            setError("Please login to view meal plans");
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            setError(null);
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001"}/api/meal-plan`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                if (response.status === 404) {
                    setError("Complete your profile first to get meal plans");
                } else {
                    setError("Failed to load meal plan");
                }
                setLoading(false);
                return;
            }

            const data = await response.json();
            console.log("✅ Meal plan loaded:", data);
            setMealPlan(data);
            setSelectedDay(0);
        } catch (err) {
            console.error("Error fetching meal plan:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="px-5 py-5 pb-32">
                <div className="mb-6">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Weekly Plan</p>
                    <h1 className="text-2xl font-bold text-slate-900">Your 7-Day Plan</h1>
                </div>
                <div className="flex items-center justify-center py-12">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="px-5 py-5 pb-32">
                <div className="mb-6">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Weekly Plan</p>
                    <h1 className="text-2xl font-bold text-slate-900">Your 7-Day Plan</h1>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                    <p className="text-base text-red-700 font-semibold mb-4">{error}</p>
                    <button
                        onClick={fetchMealPlan}
                        className="w-full bg-accent hover:bg-accent-dark text-slate-900 font-semibold py-2.5 rounded-lg"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    if (!mealPlan || !mealPlan.weekly_plan || mealPlan.weekly_plan.length === 0) {
        return (
            <div className="px-5 py-5 pb-32">
                <div className="mb-6">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Weekly Plan</p>
                    <h1 className="text-2xl font-bold text-slate-900">Your 7-Day Plan</h1>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 text-center">
                    <p className="text-sm text-slate-700 font-medium">No meal plan generated yet</p>
                </div>
            </div>
        );
    }

    const weeklyPlan = mealPlan.weekly_plan;
    const todayIndex = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1;
    const dayPlan = weeklyPlan[selectedDay];
    
    // Build allMeals array, handling both object and array meal formats
    const allMeals = (() => {
        const meals = [];
        if (dayPlan?.meals) {
            const mealEmojis = {
                breakfast: '🥞',
                lunch: '🍛',
                snacks: '🥜',
                dinner: '🍜'
            };
            
            Object.entries(dayPlan.meals).forEach(([mealType, mealData]) => {
                if (!mealData) return;
                
                if (Array.isArray(mealData)) {
                    // Handle array meals (snacks)
                    mealData.forEach((item, idx) => {
                        if (item) {
                            meals.push({
                                type: mealType.charAt(0).toUpperCase() + mealType.slice(1),
                                emoji: mealEmojis[mealType] || '🍽️',
                                name: item.meal || `${mealType} #${idx+1}`,
                                portion_size: item.portion,
                                calories: item.calories || 0
                            });
                        }
                    });
                } else {
                    // Handle object meals
                    meals.push({
                        type: mealType.charAt(0).toUpperCase() + mealType.slice(1),
                        emoji: mealEmojis[mealType] || '🍽️',
                        name: mealData.meal || mealType,
                        portion_size: mealData.portion,
                        calories: mealData.calories || 0
                    });
                }
            });
        }
        return meals;
    })();
    const totalCalories = dayPlan?.total_calories || 0;
    const targetCalories = dayPlan?.total_calories || 2000;

    return (
        <div className="px-5 py-5 pb-32">
            {/* Header */}
            <div className="mb-6">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Weekly Plan</p>
                <h1 className="text-2xl font-bold text-slate-900 mb-1">Your 7-Day Plan</h1>
                <p className="text-sm text-slate-500">Customized for your goals</p>
            </div>

            {/* Day selector */}
            <div className="mb-8 flex gap-2 overflow-x-auto pb-2 -mx-5 px-5">
                {days.map((day, idx) => (
                    <button
                        key={day}
                        onClick={() => setSelectedDay(idx)}
                        className={`px-4 py-2.5 rounded-lg font-medium text-sm min-w-fit transition-all ${
                            selectedDay === idx
                                ? "bg-accent text-slate-900"
                                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                        } ${todayIndex === idx ? "ring-2 ring-accent" : ""}`}
                    >
                        {day}
                        {todayIndex === idx && <span className="text-xs ml-1">•</span>}
                    </button>
                ))}
            </div>

            {/* Daily summary */}
            {dayPlan && (
                <div className="mb-8 bg-white rounded-lg p-6 border border-slate-200 shadow-sm">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-4">
                        {fullDays[selectedDay]} - Daily Summary
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <p className="text-xs text-slate-500 mb-1">Total Calories</p>
                            <p className="text-3xl font-bold text-slate-900">{dayPlan.total_calories}</p>
                            <p className="text-xs text-slate-400 mt-0.5">kcal</p>
                        </div>
                        <div>
                            <p className="text-xs text-slate-500 mb-1">Meals</p>
                            <p className="text-3xl font-bold text-slate-900">{allMeals.length}</p>
                            <p className="text-xs text-slate-400 mt-0.5">planned</p>
                        </div>
                    </div>
                    <div className="mt-4 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-accent rounded-full" style={{width: '75%'}}></div>
                    </div>
                </div>
            )}

            {/* Meals */}
            {dayPlan && allMeals.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-base font-semibold text-slate-900 mb-4">Meal Details</h2>
                    <div className="space-y-2.5">
                        {allMeals.map((meal, idx) => (
                            <div
                                key={idx}
                                className="w-full bg-white rounded-lg p-4 border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center text-xl">
                                        {meal.emoji}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-medium text-slate-900 text-sm">{meal.name}</h3>
                                        <div className="flex items-center gap-2 mt-0.5">
                                            <span className="text-xs text-slate-500">{meal.type}</span>
                                            {meal.portion_size && (
                                                <span className="text-xs text-slate-400">• {meal.portion_size}</span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="text-right flex-shrink-0">
                                        <span className="text-sm font-semibold text-slate-900">{meal.calories}</span>
                                        <p className="text-xs text-slate-400">kcal</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Action button */}
            {mealPlan && (
                <button
                    onClick={() => fetchMealPlan()}
                    className="w-full h-11 bg-accent hover:bg-accent-dark text-slate-900 rounded-lg font-semibold text-sm transition-colors active:scale-95"
                >
                    Regenerate Plan
                </button>
            )}
        </div>
    );
}

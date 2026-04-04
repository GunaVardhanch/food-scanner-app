"use client";
import { useState, useEffect } from "react";

export default function AaharHomeTab({ user, token }) {
    const [selectedMeal, setSelectedMeal] = useState(null);
    const [meals, setMeals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [totalCalories, setTotalCalories] = useState(0);
    
    const today = new Date();
    const dayName = today.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

    // Fetch today's meals from the API
    useEffect(() => {
        if (!token) {
            setError("Please login to view meals");
            setLoading(false);
            return;
        }
        fetchTodaysMeals();
    }, [token]);

    const fetchTodaysMeals = async () => {
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
                    setError("Complete your profile to get meal plans");
                } else {
                    setError("Failed to load today's meals");
                }
                setLoading(false);
                return;
            }

            const data = await response.json();
            
            // Get today's meals (Monday is index 0)
            const todayIndex = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1;
            const todayPlan = data.weekly_plan?.[todayIndex];
            
            if (todayPlan && todayPlan.meals) {
                const mealList = [];
                const mealTimes = {
                    breakfast: "8:00 AM",
                    lunch: "1:00 PM",
                    snacks: "4:00 PM",
                    dinner: "8:00 PM"
                };
                const mealEmojis = {
                    breakfast: "🥞",
                    lunch: "🍛",
                    snacks: "🥜",
                    dinner: "🍜"
                };
                const mealTypes = {
                    breakfast: "Breakfast",
                    lunch: "Lunch",
                    snacks: "Snacks",
                    dinner: "Dinner"
                };
                
                let totalCals = 0;
                Object.entries(todayPlan.meals).forEach(([key, meal]) => {
                    if (meal) {
                        // Handle both single meals (object) and snacks (array)
                        if (Array.isArray(meal)) {
                            meal.forEach((item, idx) => {
                                if (item) {
                                    const mealName = item.meal || `${key} #${idx+1}`;
                                    const cals = item.calories || 0;
                                    mealList.push({
                                        id: mealList.length + 1,
                                        type: mealTypes[key],
                                        emoji: mealEmojis[key],
                                        time: mealTimes[key],
                                        calories: cals,
                                        name: mealName,
                                        portion_size: item.portion
                                    });
                                    totalCals += cals;
                                }
                            });
                        } else {
                            const mealName = meal.meal || key;
                            const cals = meal.calories || 0;
                            mealList.push({
                                id: mealList.length + 1,
                                type: mealTypes[key],
                                emoji: mealEmojis[key],
                                time: mealTimes[key],
                                calories: cals,
                                name: mealName,
                                portion_size: meal.portion
                            });
                            totalCals += cals;
                        }
                    }
                });
                setMeals(mealList);
                setTotalCalories(totalCals);
            } else {
                setError("No meals found for today. Complete your profile first.");
            }
        } catch (err) {
            console.error("Error fetching today's meals:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const firstName = user?.name?.split(" ")[0] || "there";

    // Loading state
    if (loading) {
        return (
            <div className="px-5 py-5">
                <div className="mb-8">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Today's Plan</p>
                    <h1 className="text-2xl font-bold text-slate-900">{firstName}</h1>
                </div>
                <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                        <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                        <p className="text-sm text-slate-600 font-medium">Loading meals...</p>
                    </div>
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="px-5 py-5 pb-32">
                <div className="mb-8">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Today's Plan</p>
                    <h1 className="text-2xl font-bold text-slate-900">{firstName}</h1>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                    <p className="text-base text-red-700 font-semibold mb-4">{error}</p>
                    <button
                        onClick={fetchTodaysMeals}
                        className="w-full h-11 bg-accent hover:bg-accent-dark text-slate-900 rounded-lg font-semibold text-sm transition-colors active:scale-95"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="px-5 py-5 pb-32">
            {/* Header */}
            <div className="mb-8">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Today's Plan</p>
                <h1 className="text-2xl font-bold text-slate-900 mb-1">{firstName}</h1>
                <p className="text-sm text-slate-500 font-medium">{dayName}</p>
            </div>

            {/* Today's Calorie Summary */}
            <div className="mb-8 bg-white rounded-lg p-6 border border-slate-200 shadow-sm">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Daily Goal</h3>
                <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-slate-900">{totalCalories}</span>
                    <span className="text-sm text-slate-400 font-medium">kcal</span>
                </div>
                <div className="mt-4 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-accent rounded-full" style={{width: '65%'}}></div>
                </div>
            </div>

            {/* Today's Meals */}
            <div className="mb-6">
                <h2 className="text-base font-semibold text-slate-900 mb-4">Meals</h2>
                <div className="space-y-2.5">
                    {meals && meals.length > 0 ? meals.map(meal => (
                        <button
                            key={meal.id}
                            onClick={() => setSelectedMeal(meal)}
                            className="w-full bg-white rounded-lg p-4 border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all active:scale-95 text-left group"
                        >
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center text-xl group-hover:bg-slate-200 transition-colors">
                                    {meal.emoji}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h3 className="font-medium text-slate-900 text-sm">{meal.name}</h3>
                                    <div className="flex items-center gap-2 mt-0.5">
                                        <span className="text-xs text-slate-500">{meal.time}</span>
                                        {meal.portion_size && (
                                            <span className="text-xs text-slate-400">• {meal.portion_size}</span>
                                        )}
                                    </div>
                                </div>
                                <div className="text-right flex-shrink-0">
                                    <span className="text-sm font-semibold text-slate-900">{meal.calories}</span>\n                                    <p className="text-xs text-slate-400\">kcal</p>\n                                </div>
                            </div>
                        </button>
                    )) : (
                        <div className="py-8 text-center bg-white rounded-lg border border-slate-200">
                            <p className="text-sm text-slate-500\">No meals available</p>
                            <p className="text-xs text-slate-400 mt-1\">Generate a meal plan to start</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Action button to refresh meals */}
            <div>
                <button
                    onClick={fetchTodaysMeals}
                    className="w-full h-11 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm transition-colors active:scale-95"
                >
                    Refresh Meals
                </button>
            </div>

            {/* Meal Detail Sheet */}
            {selectedMeal && (
                <div className="fixed inset-0 z-40 flex items-end bg-black/30 backdrop-blur-sm" onClick={() => setSelectedMeal(null)}>
                    <div
                        className="w-full bg-white rounded-t-2xl p-6 shadow-2xl animate-slide-up max-h-[80vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Close button */}
                        <button
                            onClick={() => setSelectedMeal(null)}
                            className="float-right text-2xl text-slate-300 hover:text-slate-600 mb-4"
                        >
                            ✕
                        </button>

                        {/* Meal title */}
                        <div className="flex items-center gap-3 mb-6 clear-both">
                            <span className="text-5xl">{selectedMeal.emoji}</span>
                            <div>
                                <h2 className="text-xl font-bold text-slate-900">{selectedMeal.name}</h2>
                                <p className="text-sm text-slate-500">{selectedMeal.type}</p>
                            </div>
                        </div>

                        {/* Nutrition breakdown */}
                        <div className="bg-slate-50 rounded-lg p-4 mb-6 border border-slate-200">
                            <h3 className="text-sm font-semibold text-slate-900 mb-3\">Nutrition</h3>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-white rounded-lg p-3 border border-slate-200">
                                    <p className="text-xs text-slate-500 mb-1\">Calories</p>
                                    <p className="text-lg font-bold text-slate-900\">{selectedMeal.calories}</p>
                                </div>
                                <div className="bg-white rounded-lg p-3 border border-slate-200\">
                                    <p className="text-xs text-slate-500 mb-1\">Protein</p>
                                    <p className="text-lg font-bold text-slate-900\">18g</p>
                                </div>
                                <div className="bg-white rounded-lg p-3 border border-slate-200\">
                                    <p className="text-xs text-slate-500 mb-1\">Carbs</p>
                                    <p className="text-lg font-bold text-slate-900\">65g</p>
                                </div>
                                <div className="bg-white rounded-lg p-3 border border-slate-200\">
                                    <p className="text-xs text-slate-500 mb-1\">Fat</p>
                                    <p className="text-lg font-bold text-slate-900\">12g</p>
                                </div>
                            </div>
                        </div>

                        {/* Ingredients */}
                        <div className="mb-6">
                            <h3 className="text-sm font-semibold text-slate-900 mb-3\">Ingredients</h3>
                            <ul className="space-y-2 text-sm text-slate-700\">
                                <li className="flex items-start gap-2\"><span className="text-blue-600\">✓</span> Rice (2 cups)</li>
                                <li className="flex items-start gap-2\"><span className="text-blue-600\">✓</span> Red lentils (1 cup)</li>
                                <li className="flex items-start gap-2\"><span className="text-blue-600\">✓</span> Turmeric powder (1/2 tsp)</li>
                                <li className="flex items-start gap-2\"><span className="text-blue-600\">✓</span> Cumin seeds</li>
                                <li className="flex items-start gap-2\"><span className="text-blue-600\">✓</span> Salt to taste</li>
                            </ul>
                        </div>

                        {/* Action button */}
                        <button className="w-full h-11 bg-accent hover:bg-accent-dark text-slate-900 rounded-lg font-semibold text-sm transition-colors active:scale-95">
                            Swap Meal
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

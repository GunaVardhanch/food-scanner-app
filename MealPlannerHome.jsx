"use client";

import { useState } from "react";
import { ChevronRight, Flame, Clock, RefreshCw, Calendar, ShoppingCart } from "lucide-react";

export default function MealPlannerHome() {
  const [selectedMeal, setSelectedMeal] = useState(null);

  // Sample data
  const today = new Date();
  const dayName = today.toLocaleDateString("en-US", { weekday: "long" });
  const dateStr = today.toLocaleDateString("en-US", { month: "short", day: "numeric" });

  const calorieTarget = 2000;
  const calorieConsumed = 850;
  const calorieRemaining = calorieTarget - calorieConsumed;
  const calorieProgress = (calorieConsumed / calorieTarget) * 100;

  const meals = [
    {
      id: 1,
      type: "Breakfast",
      icon: "🥘",
      dish: "Paneer Bhurji + Roti",
      calories: 350,
      time: "7:30 AM",
      ingredients: "Paneer, Onions, Tomatoes, Bell Peppers, Whole wheat roti",
      protein: "15g",
      carbs: "45g",
      fat: "12g",
      isUpcoming: true,
    },
    {
      id: 2,
      type: "Mid-Morning Snack",
      icon: "🥤",
      dish: "Buttermilk + Almonds",
      calories: 120,
      time: "10:30 AM",
      ingredients: "Buttermilk, 5 Almonds, Cumin seeds",
      protein: "5g",
      carbs: "8g",
      fat: "6g",
      isUpcoming: false,
    },
    {
      id: 3,
      type: "Lunch",
      icon: "🍲",
      dish: "Chana Dal + Basmati Rice + Cucumber Raita",
      calories: 650,
      time: "1:00 PM",
      ingredients: "Chana dal, Rice, Yogurt, Cucumber, Ginger",
      protein: "18g",
      carbs: "72g",
      fat: "14g",
      isUpcoming: false,
    },
    {
      id: 4,
      type: "Evening Snack",
      icon: "🥜",
      dish: "Roasted Chickpeas + Green Tea",
      calories: 80,
      time: "4:00 PM",
      ingredients: "Chickpeas, Rock salt, Chaat masala",
      protein: "8g",
      carbs: "12g",
      fat: "1g",
      isUpcoming: false,
    },
    {
      id: 5,
      type: "Dinner",
      icon: "🍛",
      dish: "Dal Makhani + Brown Rice",
      calories: 550,
      time: "8:00 PM",
      ingredients: "Black dal, Kidney beans, Cream, Brown rice, Tomatoes",
      protein: "20g",
      carbs: "58g",
      fat: "16g",
      isUpcoming: false,
    },
  ];

  const smartInsight = {
    status: "Under Target",
    message: `You are ${calorieRemaining} kcal under your target. Consider a protein-rich snack or increase portion sizes slightly.`,
    suggestion: "Add: Greek yogurt or cottage cheese",
    color: "emerald",
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 mobile:px-4 px-6 py-6">
      {/* ──────────────────────────────────────────────────────────────────────*/}
      {/* 1. TOP SECTION - Daily Overview */}
      {/* ──────────────────────────────────────────────────────────────────────*/}
      <div className="max-w-md mx-auto space-y-6">
        {/* Header */}
        <div className="pt-2">
          <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-1">TODAY</p>
          <h1 className="text-2xl font-black text-slate-900 leading-tight">
            {dayName}
            <span className="block text-sm text-slate-500 font-bold mt-0.5">{dateStr}</span>
          </h1>
        </div>

        {/* Calorie Summary Card */}
        <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-3xl p-6 border border-orange-100 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center">
                <Flame className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs font-black text-slate-500 uppercase tracking-wider">Calorie Goal</span>
            </div>
            <span className="text-xs font-black bg-orange-100 text-orange-700 px-3 py-1.5 rounded-full uppercase">
              {calorieProgress.toFixed(0)}%
            </span>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="h-3 bg-white rounded-full overflow-hidden shadow-inner border border-orange-100">
              <div
                className="h-full bg-gradient-to-r from-orange-400 to-red-500 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${Math.min(calorieProgress, 100)}%` }}
              />
            </div>
          </div>

          {/* Calorie Numbers */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white rounded-2xl p-3 text-center border border-orange-200">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-0.5">Consumed</p>
              <p className="text-lg font-black text-orange-600">{calorieConsumed}</p>
              <p className="text-[9px] text-slate-400">kcal</p>
            </div>
            <div className="bg-white rounded-2xl p-3 text-center border border-orange-200">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-0.5">Target</p>
              <p className="text-lg font-black text-slate-900">{calorieTarget}</p>
              <p className="text-[9px] text-slate-400">kcal</p>
            </div>
            <div className="bg-white rounded-2xl p-3 text-center border border-emerald-200">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-0.5">Remaining</p>
              <p className="text-lg font-black text-emerald-600">{calorieRemaining}</p>
              <p className="text-[9px] text-slate-400">kcal</p>
            </div>
          </div>
        </div>

        {/* ──────────────────────────────────────────────────────────────────────*/}
        {/* 2. TODAY'S MEAL TIMELINE */}
        {/* ──────────────────────────────────────────────────────────────────────*/}
        <div>
          <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Today's Meals</p>

          <div className="space-y-3">
            {meals.map((meal) => (
              <div
                key={meal.id}
                onClick={() => setSelectedMeal(selectedMeal?.id === meal.id ? null : meal)}
                className={`rounded-2xl p-4 border-2 cursor-pointer transition-all duration-300 ${
                  meal.isUpcoming
                    ? "bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-300 shadow-lg shadow-blue-200 ring-2 ring-blue-300 ring-offset-2"
                    : "bg-white border-slate-200 hover:border-slate-300 hover:shadow-md"
                } ${selectedMeal?.id === meal.id ? "ring-2 ring-blue-400 ring-offset-2" : ""}`}
              >
                {/* Meal Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="text-2xl">{meal.icon}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        <p className="text-[11px] font-black text-slate-400 uppercase tracking-wide">{meal.type}</p>
                        {meal.isUpcoming && (
                          <span className="text-[9px] font-black bg-blue-200 text-blue-700 px-2 py-0.5 rounded-full uppercase">
                            Next
                          </span>
                        )}
                      </div>
                      <h3 className="font-black text-slate-900 text-sm leading-tight">{meal.dish}</h3>
                    </div>
                  </div>

                  {/* Calorie Badge */}
                  <div className="bg-gradient-to-br from-yellow-100 to-orange-100 rounded-xl px-3 py-2 text-center border border-yellow-200 flex-shrink-0">
                    <p className="text-xs font-black text-orange-700">{meal.calories}</p>
                    <p className="text-[8px] text-orange-600 font-bold">kcal</p>
                  </div>
                </div>

                {/* Time */}
                <div className="flex items-center gap-1.5 mt-3 mb-0">
                  <Clock className="w-3 h-3 text-slate-400" />
                  <p className="text-xs text-slate-500 font-bold">{meal.time}</p>
                </div>

                {/* Expanded Details */}
                {selectedMeal?.id === meal.id && (
                  <div className="mt-4 pt-4 border-t-2 border-slate-200 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                    {/* Ingredients */}
                    <div>
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1.5">Ingredients</p>
                      <p className="text-xs text-slate-600 leading-relaxed">{meal.ingredients}</p>
                    </div>

                    {/* Macros */}
                    <div>
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">Macronutrients</p>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="bg-emerald-50 rounded-lg p-2 text-center border border-emerald-200">
                          <p className="text-xs font-black text-emerald-700">{meal.protein}</p>
                          <p className="text-[8px] text-emerald-600 font-bold">Protein</p>
                        </div>
                        <div className="bg-blue-50 rounded-lg p-2 text-center border border-blue-200">
                          <p className="text-xs font-black text-blue-700">{meal.carbs}</p>
                          <p className="text-[8px] text-blue-600 font-bold">Carbs</p>
                        </div>
                        <div className="bg-orange-50 rounded-lg p-2 text-center border border-orange-200">
                          <p className="text-xs font-black text-orange-700">{meal.fat}</p>
                          <p className="text-[8px] text-orange-600 font-bold">Fat</p>
                        </div>
                      </div>
                    </div>

                    {/* Action Button */}
                    <button className="w-full h-10 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-xl font-bold text-xs uppercase tracking-wider active:scale-95 transition-all">
                      View Full Recipe
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* ──────────────────────────────────────────────────────────────────────*/}
        {/* 3. SMART INSIGHT SECTION */}
        {/* ──────────────────────────────────────────────────────────────────────*/}
        <div className={`bg-gradient-to-br from-${smartInsight.color}-50 to-${smartInsight.color}-100 rounded-2xl p-4 border-2 border-${smartInsight.color}-200 shadow-md`}>
          <div className="flex items-start gap-3">
            <div className={`text-xl mt-0.5`}>💡</div>
            <div className="flex-1">
              <p className={`text-xs font-black text-${smartInsight.color}-600 uppercase tracking-widest mb-1`}>
                {smartInsight.status}
              </p>
              <p className="text-sm font-bold text-slate-700 leading-snug mb-2">{smartInsight.message}</p>
              <p className={`text-xs font-bold text-${smartInsight.color}-700 bg-${smartInsight.color}-200 bg-opacity-50 px-2.5 py-1 rounded-lg inline-block`}>
                💪 {smartInsight.suggestion}
              </p>
            </div>
          </div>
        </div>

        {/* ──────────────────────────────────────────────────────────────────────*/}
        {/* 4. QUICK ACTIONS */}
        {/* ──────────────────────────────────────────────────────────────────────*/}
        <div className="space-y-2 pb-8">
          {/* View Weekly Plan */}
          <button className="w-full h-12 bg-gradient-to-r from-slate-900 to-slate-800 hover:from-slate-800 hover:to-slate-700 text-white rounded-2xl font-black text-xs uppercase tracking-widest active:scale-95 transition-all flex items-center justify-center gap-2 shadow-lg">
            <Calendar className="w-4 h-4" />
            View Full 7-Day Plan
            <ChevronRight className="w-4 h-4 ml-auto" />
          </button>

          {/* Generate Grocery List + Regenerate - Two Column */}
          <div className="grid grid-cols-2 gap-2">
            <button className="h-12 bg-white border-2 border-slate-300 hover:bg-slate-50 hover:border-slate-400 text-slate-900 rounded-2xl font-black text-xs uppercase tracking-widest active:scale-95 transition-all flex items-center justify-center gap-1.5 shadow-sm">
              <ShoppingCart className="w-4 h-4" />
              Grocery List
            </button>
            <button className="h-12 bg-white border-2 border-slate-300 hover:bg-slate-50 hover:border-slate-400 text-slate-900 rounded-2xl font-black text-xs uppercase tracking-widest active:scale-95 transition-all flex items-center justify-center gap-1.5 shadow-sm">
              <RefreshCw className="w-4 h-4" />
              Regenerate
            </button>
          </div>

          {/* Tip */}
          <div className="bg-blue-50 rounded-xl p-3 border border-blue-200 mt-4">
            <p className="text-[11px] text-blue-700 font-bold leading-tight">
              💡 <span className="font-black">Tip:</span> Indian meals are rich in vegetables and legumes. Adjust portions based on your activity level.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

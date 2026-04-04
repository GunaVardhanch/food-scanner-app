# Meal Planner Integration Guide

## Overview

The meal planner uses **Google Gemini API** to generate personalized meal plans based on user profile data. The system generates:

1. **Today's Plan** - One day selected from the weekly plan
2. **7-Day Weekly Plan** - Monday through Sunday with all meals
3. **Grocery List** - Budget-aware shopping list with estimated costs

## Setup Instructions

### Step 1: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy your API key (starts with `AIza...`)

### Step 2: Configure Environment Variable

Add your Gemini API key to the `.env` file in the backend directory:

```bash
# .env
GEMINI_API_KEY=your_api_key_here
```

Or set it as a system environment variable:

```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your_api_key_here"

# Windows Command Prompt
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY="your_api_key_here"
```

### Step 3: Install Dependencies

```bash
cd food-scanner-app/backend
pip install google-generativeai
```

Or reinstall from requirements.txt:

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python -c "import google.generativeai; print('✅ google-generativeai installed')"
```

## API Endpoint

### Generate Meal Plan

```http
GET /api/meal-plan
Authorization: Bearer {token}
```

**Requirements:**
- User must be authenticated (valid JWT token)
- User must have a completed profile with:
  - Age, Gender, Weight, Height
  - Diet type (veg, non-veg, etc.)
  - State (Maharashtra, Karnataka, etc.)
  - Cuisine preference (North Indian, South Indian, etc.)
  - Health goal (lose_weight, gain_weight, maintain)
  - Activity level (sedentary, light, moderate, active)
  - Daily calorie target (auto-calculated from Mifflin-St Jeor equation)
  - Weekly budget (₹)

**Response: HTTP 200**

```json
{
  "today_plan": {
    "day": "Monday",
    "meals": {
      "breakfast": {
        "meal": "Masala Dosa with Sambar",
        "portion": "2 dosas (400g)",
        "calories": 350
      },
      "lunch": {
        "meal": "Chicken Biryani with Raita",
        "portion": "1.5 cups (375g)",
        "calories": 600
      },
      "dinner": {
        "meal": "Vegetable Curry with Roti",
        "portion": "1 cup curry + 2 rotis (300g)",
        "calories": 400
      },
      "snacks": [
        {
          "meal": "Roasted Almonds and Banana",
          "portion": "30g almonds + 1 medium banana",
          "calories": 200
        }
      ]
    },
    "total_calories": 1550
  },
  "weekly_plan": [
    {
      "day": "Monday",
      "meals": { /* ...same as today_plan... */ },
      "total_calories": 1550
    },
    { /* Tuesday through Sunday */ }
  ],
  "grocery_list": [
    {
      "item": "Basmati Rice",
      "quantity": "2kg",
      "estimated_cost": 200
    },
    { /* ...more items... */ }
  ],
  "total_estimated_cost": 2450
}
```

**Error Responses:**

```json
// 401 Not Authenticated
{
  "error": "Not authenticated"
}

// 404 Profile Not Complete
{
  "error": "User profile not complete",
  "message": "Please complete your profile before generating meal plans"
}

// 500 Gemini API Error
{
  "error": "Failed to generate meal plan",
  "details": "API key invalid or quota exceeded",
  "type": "ValueError"
}
```

## Features

### Meal Plan Guarantees

✅ **Calorie Accuracy**
- Each day matches daily target ±50 calories
- All meals include calorie values
- Total = sum of meal calories

✅ **Diet Compliance**
- Strictly follows user's diet type (veg/non-veg/vegan/etc.)
- Uses locally available foods for the user's state
- All meals are realistic Indian cuisine

✅ **Portion Details**
- Every meal includes precise portion sizes (grams, cups, or count)
- No vague terms like "1 plate"

✅ **Budget Awareness**
- Total grocery cost ≤ weekly budget
- Uses affordable, common ingredients

✅ **Variety**
- No meal repeats more than twice per week
- Balanced nutrition across all days

### Frontend Integration

The frontend should:

1. **Call the endpoint** after user completes profile:
   ```javascript
   const response = await fetch('/api/meal-plan', {
     headers: { 'Authorization': `Bearer ${token}` }
   });
   const mealPlan = await response.json();
   ```

2. **Display today's plan** immediately
3. **Show weekly overview** with calorie totals
4. **List grocery items** with estimated costs

## Troubleshooting

### Error: "Gemini API key not found"

**Solution:** Set `GEMINI_API_KEY` environment variable
```bash
$env:GEMINI_API_KEY = "AIza..."
```

### Error: "google-generativeai not installed"

**Solution:** Install package
```bash
pip install google-generativeai
```

### Error: "API key invalid or quota exceeded"

**Solution:** Verify API key at [AI Studio](https://aistudio.google.com/app/apikey)

### Error: "Invalid JSON response from Gemini"

**Possible causes:**
- API quota exceeded
- Network timeout
- Malformed user data

**Solution:** Check backend logs and reduce request frequency

### Meal plan totals don't match calorie target

**Expected:** ±50 calories from daily_calories
- If 2000 cal target → meals should total 1950-2050
- Gemini may adjust slightly due to realistic portions

## Performance Considerations

- **First request:** ~3-5 seconds (Gemini API latency)
- **Cached requests:** <100ms (if caching implemented)
- **API quota:** Gemini free tier allows ~60 requests/minute
- **Timeout:** 30 seconds recommended for API calls

## Production Checklist

- [ ] Keep `GEMINI_API_KEY` secret (never commit to git)
- [ ] Use `.env` file for local development
- [ ] Set environment variable in production
- [ ] Monitor API quota usage
- [ ] Implement rate limiting for meal plan requests
- [ ] Cache meal plans (optional, reduces API calls)
- [ ] Add user feedback mechanism for plan quality

## Testing the Integration

### Test with cURL:

```bash
# Register user
curl -X POST http://localhost:5001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"test1234"}'

# Save token from response

# Create profile
curl -X POST http://localhost:5001/api/profile \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 25,
    "gender": "Male",
    "weight": 70,
    "height": 175,
    "diet_type": "non-veg",
    "state": "maharashtra",
    "cuisine": "north indian",
    "health_goal": "maintain",
    "weekly_budget": 3000,
    "activity_level": "moderate"
  }'

# Generate meal plan
curl -X GET http://localhost:5001/api/meal-plan \
  -H "Authorization: Bearer {token}"
```

## Code Architecture

### File Structure:
```
backend/
├── app/
│   ├── services/
│   │   ├── meal_planner_service.py    ← New
│   │   ├── calorie_calculator.py      ← Used for daily_calories
│   │   └── ...other services...
│   ├── routes.py                      ← New endpoint: /api/meal-plan
│   └── ...
├── requirements.txt                   ← Added: google-generativeai
└── ...
```

### Service Flow:

```
User Authentication
    ↓
Profile Retrieval (age, diet_type, budget, etc.)
    ↓
MealPlannerService.generate_meal_plan()
    ↓
Gemini API Call (via google-generativeai)
    ↓
JSON Parsing
    ↓
Return Meal Plan (today, weekly, grocery list)
```

## API Limits & Quotas

Google Gemini API free tier:
- **Requests:** 60 per minute
- **Tokens:** 1,000,000 per day
- **Response time:** ~2-5 seconds

For production, consider upgrading to paid tier for higher limits.

---

For issues or questions, check the backend logs:
```bash
# Terminal where backend is running
# Look for [MEAL_PLAN] prefixed logs
```

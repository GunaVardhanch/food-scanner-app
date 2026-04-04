import requests
import json
import time

API_URL = "http://localhost:5001"

print("🧪 Testing Complete Meal Planner Flow...\n")

# 1. Register
print("1️⃣  Registering user...")
user_data = {
    "name": "Meal Plan Tester",
    "email": f"test_{int(time.time())}@example.com",
    "password": "Test@123"
}
resp = requests.post(f"{API_URL}/auth/register", json=user_data)
if resp.status_code != 201:
    print(f"   ❌ Registration failed: {resp.text}")
    exit(1)

auth_resp = resp.json()
token = auth_resp.get('token')
print(f"   ✅ Registered (Token: {token[:40]}...)")

# 2. Create profile
print("\n2️⃣  Creating profile...")
profile_data = {
    "health_goal": "stay_healthy",
    "age": 28,
    "gender": "female",
    "weight": 65,
    "height": 162,
    "diet_type": "veg",
    "state": "Maharashtra",
    "cuisine": "North Indian",
    "activity_level": "moderate",
    "weekly_budget": 2500
}
resp = requests.post(
    f"{API_URL}/api/profile",
    json=profile_data,
    headers={"Authorization": f"Bearer {token}"}
)
if resp.status_code != 200:
    print(f"   ❌ Profile creation failed: {resp.status_code}")
    print(f"   Response: {resp.text}")
    exit(1)

print(f"   ✅ Profile created successfully")

# 3. Get meal plan
print("\n3️⃣  Fetching 7-day meal plan (Powered by Gemini AI)...")
resp = requests.get(
    f"{API_URL}/api/meal-plan",
    headers={"Authorization": f"Bearer {token}"}
)
if resp.status_code != 200:
    print(f"   ❌ Meal plan fetch failed: {resp.status_code}")
    print(f"   Response: {resp.text}")
    exit(1)

meal_plan = resp.json()
print(f"   ✅ Meal plan generated successfully!")

# Display summary
print("\n" + "="*60)
print("📊 MEAL PLAN SUMMARY")
print("="*60)
print(f"✅ Total Weekly Days: {len(meal_plan.get('weekly_plan', []))}")
print(f"🍽️  Today's Calories: {meal_plan.get('today_plan', {}).get('total_calories')} kcal")
print(f"🛒 Total Grocery Items: {len(meal_plan.get('grocery_list', []))}")
print(f"💰 Total Estimated Cost: ₹{meal_plan.get('total_estimated_cost')}")

# Show detailed breakdown
print("\n📋 TODAY'S MEALS:")
today = meal_plan.get('today_plan', {})
if today and today.get('meals'):
    for meal_type, details in today.get('meals', {}).items():
        if details:
            print(f"  • {meal_type.upper()}")
            print(f"    Name: {details.get('name')}")
            print(f"    Portion: {details.get('portion_size')}")
            print(f"    Calories: {details.get('calories')} kcal")

# Show first 5 grocery items
print("\n🛒 GROCERY LIST (First 5 items):")
grocery = meal_plan.get('grocery_list', [])[:5]
for item in grocery:
    print(f"  • {item.get('item')}: {item.get('quantity')} ({item.get('estimated_price')})")

print("\n" + "="*60)
print("✅ INTEGRATION TEST SUCCESSFUL!")
print("🎉 Meal Planner is fully operational with Gemini AI")
print("="*60)

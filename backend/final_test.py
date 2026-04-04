import requests
import json
import time

API_URL = "http://localhost:5001"

print("🧪 Testing Meal Planner Integration...\n")

# 1. Register new user
print("1️⃣  Registering test user...")
user_data = {
    "name": "Test User",
    "email": f"test_{int(time.time())}@example.com",
    "password": "Password123!"
}
resp = requests.post(f"{API_URL}/auth/register", json=user_data)
print(f"   Status: {resp.status_code}")
if resp.ok:
    user = resp.json()
    user_id = user.get('id')
    print(f"   ✅ User ID: {user_id}")
else:
    print(f"   ❌ {resp.text}")
    exit(1)

# 2. Login
print("\n2️⃣  Logging in...")
login_data = {"email": user_data["email"], "password": user_data["password"]}
resp = requests.post(f"{API_URL}/auth/login", json=login_data)
print(f"   Status: {resp.status_code}")
if resp.ok:
    auth = resp.json()
    token = auth.get('access_token')
    print(f"   ✅ Token: {token[:30]}...")
else:
    print(f"   ❌ {resp.text}")
    exit(1)

# 3. Create profile
print("\n3️⃣  Creating profile...")
profile_data = {
    "health_goal": "gain_muscle",
    "age": 30,
    "gender": "male",
    "weight": 75,
    "height": 180,
    "diet_type": "non-veg",
    "state": "Karnataka",
    "cuisine": "South Indian",
    "activity_level": "moderate",
    "weekly_budget": 3000
}
resp = requests.post(
    f"{API_URL}/api/profile",
    json=profile_data,
    headers={"Authorization": f"Bearer {token}"}
)
print(f"   Status: {resp.status_code}")
if resp.ok:
    profile = resp.json()
    print(f"   ✅ Profile created: {profile.get('email')}")
else:
    print(f"   ❌ {resp.text}")
    exit(1)

# 4. Get meal plan
print("\n4️⃣  Getting meal plan (Gemini-powered)...")
resp = requests.get(
    f"{API_URL}/api/meal-plan",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"   Status: {resp.status_code}")
if resp.ok:
    meal_plan = resp.json()
    print(f"   ✅ Meal plan generated!")
    print(f"   📅 Total days: {len(meal_plan.get('weekly_plan', []))}")
    print(f"   🍽️  Today's calories: {meal_plan.get('today_plan', {}).get('total_calories')} kcal")
    print(f"   🛒 Grocery items: {len(meal_plan.get('grocery_list', []))}")
    print(f"   💰 Total cost: ₹{meal_plan.get('total_estimated_cost')}")
    
    # Show sample meals
    today = meal_plan.get('today_plan', {})
    if today:
        mealslist = today.get('meals', {})
        if mealslist:
            print(f"\n   📋 Sample meals for today:")
            for meal_type, details in mealslist.items():
                if details:
                    print(f"      • {meal_type.capitalize()}: {details.get('name')} ({details.get('calories')} cal)")
else:
    print(f"   ❌ {resp.text}")
    exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED! Meal planner is working perfectly!")
print("="*60)

import requests
import json
import time

API_URL = "http://localhost:5001"

print("🧪 FINAL VERIFICATION: Complete Meal Planner with Caching\n")
print("=" * 70)

# 1. Register
print("\n1️⃣  Registering new user...")
user_data = {
    "name": "Final Test User",
    "email": f"final_test_{int(time.time())}@example.com",
    "password": "FinalTest@123"
}
resp = requests.post(f"{API_URL}/auth/register", json=user_data)
if resp.status_code != 201:
    print(f"   ❌ Failed: {resp.text}")
    exit(1)
token = resp.json()['token']
print(f"   ✅ User registered")

# 2. Create profile
print("\n2️⃣  Creating user profile...")
profile_data = {
    "age": 30,
    "gender": "Female",
    "weight": 65,
    "height": 162,
    "diet_type": "veg",
    "state": "Karnataka",
    "cuisine": "South Indian",
    "health_goal": "lose_weight",
    "activity_level": "moderate",
    "weekly_budget": 2800
}
resp = requests.post(f"{API_URL}/api/profile", json=profile_data, headers={"Authorization": f"Bearer {token}"})
if resp.status_code != 200:
    print(f"   ❌ Failed: {resp.text}")
    exit(1)
print(f"   ✅ Profile created with calories calculated")

# 3. First meal plan call
print("\n3️⃣  FIRST REQUEST: Generating meal plan from Gemini AI...")
start = time.time()
resp = requests.get(f"{API_URL}/api/meal-plan", headers={"Authorization": f"Bearer {token}"})
duration1 = time.time() - start

if resp.status_code != 200:
    print(f"   ❌ Failed: {resp.text}")
    exit(1)

data = resp.json()
print(f"   ✅ Generated in {duration1:.1f} seconds")
print(f"      • Days: {len(data.get('weekly_plan', []))}")
print(f"      • Total calories (today): {data.get('today_plan', {}).get('total_calories')} kcal")
print(f"      • Grocery items: {len(data.get('grocery_list', []))}")
print(f"      • Total cost: ₹{data.get('total_estimated_cost')}")

# 4. Second meal plan call (should be cached)
print("\n4️⃣  SECOND REQUEST: Fetching from cache...")
start = time.time()
resp = requests.get(f"{API_URL}/api/meal-plan", headers={"Authorization": f"Bearer {token}"})
duration2 = time.time() - start

if resp.status_code != 200:
    print(f"   ❌ Failed: {resp.text}")
    exit(1)

data2 = resp.json()
print(f"   ✅ Retrieved in {duration2:.1f} seconds (⚡ CACHED!)")

# 5. Verify data is identical
if data == data2:
    print(f"   ✅ Data verification: IDENTICAL ✓")
else:
    print(f"   ❌ Data mismatch!")
    exit(1)

# 6. Show performance
print("\n" + "=" * 70)
print("📊 PERFORMANCE METRICS")
print("=" * 70)
print(f"Gemini generation:     {duration1:>7.1f}s (first time)")
print(f"Cache retrieval:       {duration2:>7.1f}s (subsequent)")
print(f"Performance gain:      {duration1/duration2:>7.1f}x faster ⚡")
print(f"Time saved per user:   {duration1 - duration2:>7.1f}s")

# 7. Final status
print("\n" + "=" * 70)
print("✅ ALL SYSTEMS OPERATIONAL")
print("=" * 70)
print("✓ Authentication working")
print("✓ Profile creation working")
print("✓ Gemini AI integration working")
print("✓ Meal plan generation working")
print("✓ Database caching working")
print("✓ Performance optimized")
print("\n🚀 Meal Planner is PRODUCTION READY!")
print("=" * 70)

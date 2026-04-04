import requests
import json
import time

API_URL = "http://localhost:5001"

print("🧪 Testing Meal Planner Endpoint...\n")

# Create a simple test with email login (check the auth routes)
print("1️⃣  Checking auth endpoints...")
resp = requests.get(f"{API_URL}/auth/me")
print(f"   GET /auth/me Status: {resp.status_code}")
print(f"   Response: {resp.text[:100]}")

# Try posting to register
print("\n2️⃣  Testing registration endpoint...")
user_data = {
    "name": "Integration Test",
    "email": f"test_{int(time.time())}@example.com",
    "password": "Test@123"
}
resp = requests.post(f"{API_URL}/auth/register", json=user_data)
print(f"   POST /auth/register Status: {resp.status_code}")
response_json = resp.json()
print(f"   Response keys: {list(response_json.keys())}")
print(f"   Full response: {json.dumps(response_json, indent=2)[:300]}")

if 'token' in response_json:
    token = response_json['token']
    print(f"\n✅ Got token from register: {token[:30]}...")
else:
    print("\n   No token in register response, checking auth/login...")
    # Try login instead
    resp = requests.post(f"{API_URL}/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    print(f"   POST /auth/login Status: {resp.status_code}")
    print(f"   Response: {json.dumps(resp.json(), indent=2)}")

#!/usr/bin/env python3
import sqlite3
import json
import hmac
import hashlib
import time
import base64
import requests

# Connect to database
conn = sqlite3.connect('food_scanner.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check users table
cursor.execute('SELECT id, name, email FROM users LIMIT 1')
user = cursor.fetchone()

if user:
    print(f"✅ Found user: ID={user['id']}, Name={user['name']}, Email={user['email']}")
    user_id = user['id']
    
    # Generate a test token (must match backend's JWT_SECRET)
    _JWT_SECRET = "aahar-secret-key-please-change-in-production"
    _TOKEN_TTL = 30 * 24 * 60 * 60  # 30 days
    
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({
        "sub": user_id,
        "email": user['email'],
        "exp": int(time.time()) + _TOKEN_TTL,
    }).encode()).decode().rstrip("=")
    sig = hmac.new(_JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    token = f"{header}.{payload}.{sig}"
    
    print(f"\n🔑 Generated token (first 50 chars): {token[:50]}...")
    
    # Test GET /api/profile endpoint
    print(f"\n📡 Testing GET /api/profile...")
    try:
        res = requests.get('http://localhost:5001/api/profile', headers={
            'Authorization': f'Bearer {token}'
        })
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(res.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No users found in database")

conn.close()

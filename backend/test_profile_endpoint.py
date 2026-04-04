#!/usr/bin/env python3
import requests
import json
import sqlite3

# Test the /api/profile endpoint
API_URL = "http://localhost:5001"

print("="*80)
print("Testing Aahar AI Backend - Profile Endpoint")
print("="*80)
print()

# First, let's get the auth token from the database
conn = sqlite3.connect('food_scanner.db')
cursor = conn.cursor()
cursor.execute("SELECT id, email FROM users WHERE email='venkatarajesh016@gmail.com'")
user = cursor.fetchone()
conn.close()

if not user:
    print("ERROR: User not found in database!")
    exit(1)

user_id, email = user
print(f"Found user: ID={user_id}, Email={email}")
print()

# Since we can't generate a valid token without the secret, let's check what's actually in the DB
print("Current Database Status:")
print("-" * 80)

conn = sqlite3.connect('food_scanner.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"Available tables: {tables}")
print()

# Check if profiles table exists
if 'profiles' in tables:
    cursor.execute("SELECT COUNT(*) FROM profiles")
    count = cursor.fetchone()[0]
    print(f"✅ Profiles table EXISTS with {count} records")
    if count > 0:
        cursor.execute("SELECT * FROM profiles")
        profile = cursor.fetchone()
        # Get column names
        cursor.execute("PRAGMA table_info(profiles)")
        cols = [row[1] for row in cursor.fetchall()]
        print("\nProfile data:")
        for col_name, value in zip(cols, profile):
            print(f"  {col_name}: {value}")
else:
    print("❌ Profiles table does NOT exist yet")
    print("   This will be created when user completes onboarding form")

conn.close()
print()
print("="*80)
print("To populate profiles table:")
print("  1. Go to frontend app (http://localhost:3000)")
print("  2. Complete the 4-step onboarding form")
print("  3. Click 'Complete' on Step 4")
print("  4. Run this script again to verify data was saved")
print("="*80)

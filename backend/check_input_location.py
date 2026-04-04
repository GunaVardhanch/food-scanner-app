#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('food_scanner.db')
cursor = conn.cursor()

# Check all table schemas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = [row[0] for row in cursor.fetchall()]

print('\n=== TABLE SCHEMAS ===\n')
for table in tables:
    print(f'TABLE: {table}')
    cursor.execute(f'PRAGMA table_info({table})')
    columns = cursor.fetchall()
    for col in columns:
        print(f'  - {col[1]} ({col[2]})')
    print()

print('\n=== PROFILE DATA STORAGE LOCATION ===\n')
print('Your onboarding form data would be stored in TWO places:')
print()
print('1. Frontend (localStorage):')
print('   - Key: "aa_user"')
print('   - Contains: user token, name, email, profile_complete flag')
print('   - Location: Browser storage (persists until cleared)')
print()
print('2. Backend (SQLite Database):')
print('   - Table: "profiles" (will be auto-created on first form submission)')
print('   - Fields: age, gender, weight, height, diet_type, state, cuisine,')
print('            health_goal, weekly_budget, activity_level')
print('   - Location: food_scanner.db (in backend folder)')
print()
print('Current Status:')
print('  - Account created: YES (user "raj" registered)')
print('  - Onboarding form submitted: NO (profiles table not created)')
print('  - Profile data in localStorage: Check browser DevTools > Application > LocalStorage')

conn.close()

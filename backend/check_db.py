#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('food_scanner.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check if tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('Tables in database:', tables)
print('\n' + '='*80 + '\n')

# Users table
try:
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    if users:
        print('USERS TABLE:')
        for i, user in enumerate(users, 1):
            print(f'  Record {i}:')
            for key, value in dict(user).items():
                if key == 'password':
                    print(f'    {key}: [HASHED]')
                else:
                    print(f'    {key}: {value}')
    else:
        print('USERS TABLE: (empty)')
except Exception as e:
    print(f'USERS TABLE: Error - {e}')

print('\n' + '='*80 + '\n')

# Profiles table
try:
    cursor.execute('SELECT * FROM profiles')
    profiles = cursor.fetchall()
    if profiles:
        print('PROFILES TABLE:')
        for i, profile in enumerate(profiles, 1):
            print(f'  Record {i}:')
            for key, value in dict(profile).items():
                print(f'    {key}: {value}')
    else:
        print('PROFILES TABLE: (empty)')
except Exception as e:
    print(f'PROFILES TABLE: Error - {e}')

print('\n' + '='*80 + '\n')

# Preferences table
try:
    cursor.execute('SELECT * FROM preferences')
    prefs = cursor.fetchall()
    if prefs:
        print('PREFERENCES TABLE:')
        for i, pref in enumerate(prefs, 1):
            print(f'  Record {i}:')
            for key, value in dict(pref).items():
                print(f'    {key}: {value}')
    else:
        print('PREFERENCES TABLE: (empty)')
except Exception as e:
    print(f'PREFERENCES TABLE: Error - {e}')

print('\n' + '='*80 + '\n')

# Scans table
try:
    cursor.execute('SELECT * FROM scans LIMIT 5')
    scans = cursor.fetchall()
    if scans:
        print(f'SCANS TABLE: ({len(scans)} records shown, may be more...)')
        for i, scan in enumerate(scans, 1):
            rec = dict(scan)
            print(f'  Record {i}:')
            for key, value in rec.items():
                if key in ('nutrition', 'ingredients', 'flagged_additives'):
                    print(f'    {key}: [JSON DATA]')
                else:
                    print(f'    {key}: {value}')
    else:
        print('SCANS TABLE: (empty)')
except Exception as e:
    print(f'SCANS TABLE: Error - {e}')

print('\n' + '='*80 + '\n')

# Scan results table
try:
    cursor.execute('SELECT * FROM scan_results LIMIT 5')
    results = cursor.fetchall()
    if results:
        print(f'SCAN_RESULTS TABLE: ({len(results)} records shown, may be more...)')
        for i, result in enumerate(results, 1):
            rec = dict(result)
            print(f'  Record {i}:')
            for key, value in rec.items():
                if len(str(value)) > 100:
                    print(f'    {key}: [LARGE DATA]')
                else:
                    print(f'    {key}: {value}')
    else:
        print('SCAN_RESULTS TABLE: (empty)')
except Exception as e:
    print(f'SCAN_RESULTS TABLE: Error - {e}')

print('\n' + '='*80 + '\n')

# Nutrition cache table
try:
    cursor.execute('SELECT * FROM nutrition_cache LIMIT 5')
    cache = cursor.fetchall()
    if cache:
        print(f'NUTRITION_CACHE TABLE: ({len(cache)} records shown, may be more...)')
        for i, item in enumerate(cache, 1):
            rec = dict(item)
            print(f'  Record {i}:')
            for key, value in rec.items():
                if len(str(value)) > 100:
                    print(f'    {key}: [LARGE DATA]')
                else:
                    print(f'    {key}: {value}')
    else:
        print('NUTRITION_CACHE TABLE: (empty)')
except Exception as e:
    print(f'NUTRITION_CACHE TABLE: Error - {e}')

conn.close()

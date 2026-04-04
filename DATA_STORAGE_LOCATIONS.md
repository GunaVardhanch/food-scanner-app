# 📊 Aahar AI - Data Storage Locations

## 1. SQLite Database (Server-Side - Persistent)

### Location
```
c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend\food_scanner.db
```

### Current Status
```
✅ USERS TABLE (1 record)
   - id: 1
   - name: raj
   - email: venkatarajesh016@gmail.com
   - password: [HASHED with PBKDF2]
   - created_at: 2026-04-03 18:03:26

⏳ PROFILES TABLE (0 records - will be created on first profile submission)
   - Will store: age, gender, weight, height, diet_type, state, cuisine, health_goal, weekly_budget, activity_level

⏳ PREFERENCES TABLE (0 records - empty until user sets preferences)

⏳ SCANS TABLE (0 records - empty until user scans a food barcode)

⏳ SCAN_RESULTS TABLE (0 records - empty until food is analyzed)

⏳ NUTRITION_CACHE TABLE (0 records - empty until food data is cached)
```

### View Database Contents
```bash
cd backend
python check_db.py
```

### Database Structure (SQL)
```sql
-- USERS TABLE (Already created)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PROFILES TABLE (Auto-created on first profile POST)
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    age INTEGER,
    gender TEXT,
    weight REAL,
    height REAL,
    diet_type TEXT,
    state TEXT,
    cuisine TEXT,
    health_goal TEXT,
    weekly_budget INTEGER,
    activity_level TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- PREFERENCES TABLE
CREATE TABLE preferences (
    user_id INTEGER PRIMARY KEY,
    vegan INTEGER DEFAULT 0,
    no_sugar INTEGER DEFAULT 0,
    low_sodium INTEGER DEFAULT 0,
    gluten_free INTEGER DEFAULT 0
);

-- SCANS TABLE
CREATE TABLE scans (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    barcode TEXT,
    product_name TEXT,
    quantity INTEGER,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SCAN_RESULTS TABLE
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY,
    scan_id INTEGER,
    calories INTEGER,
    protein REAL,
    fat REAL,
    carbs REAL
);

-- NUTRITION_CACHE TABLE
CREATE TABLE nutrition_cache (
    product_id TEXT PRIMARY KEY,
    nutrition_data TEXT,
    last_updated TIMESTAMP
);
```

---

## 2. Frontend Local Storage (Client-Side - Temporary)

### Location
```
Browser: http://localhost:3000 → Developer Tools (F12) → Application → Local Storage
```

### Stored Values

```javascript
{
  // Authentication Token (JWT)
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  
  // User Info
  "user": {
    "id": 1,
    "email": "venkatarajesh016@gmail.com",
    "name": "raj"
  },
  
  // Profile Completion Status
  "profile_complete": true  // Only set after onboarding
  
  // Note: Profile data is NOT cached here!
  // Always fetched from SQLite DB via GET /api/profile
}
```

### Current State (After User Registration)
```
✅ token: Available (JWT bearer token for API calls)
✅ user: { id, email, name }
⏳ profile_complete: Will be set to true after onboarding
❌ profile: NOT stored in localStorage (fetched from backend on demand)
```

### View Local Storage
```javascript
// In Browser Console (F12):
console.log(localStorage)  // Shows all stored items
console.log(localStorage.getItem('token'))  // Shows JWT token
console.log(localStorage.getItem('profile_complete'))  // Shows profile completion status

// Note: localStorage.profile will be undefined/empty
// Profile data is fetched from backend via GET /api/profile
```

---

## 3. File-Based Data Storage

### Scan History (JSON File)
```
Location: c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend\app\data\scan_history.json

Example:
[
  {
    "scan_id": 1,
    "user_id": 1,
    "barcode": "8901234567890",
    "product_name": "Britannia Good Day",
    "scanned_at": "2026-04-04 10:30:00",
    "nutrition": {
      "calories": 130,
      "protein": 2.5,
      "fat": 6.0,
      "carbs": 16.0
    }
  }
]
```

### User Preferences (JSON File)
```
Location: c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend\app\data\user_preferences.json

Example:
{
  "user_1": {
    "diet_type": "vegetarian",
    "no_sugar": true,
    "low_sodium": false,
    "notifications": true
  }
}
```

---

## 4. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       USER INPUT                            │
│    (Registration, Onboarding Form, Food Scanning)           │
└────────────────────┬────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    ┌─────────────┐      ┌──────────────┐
    │  Frontend   │      │   Backend    │
    │ localStorage│      │   Flask      │
    │             │      │              │
    │ • token     │      │ • routes.py  │
    │ • user      │      │ • services   │
    │ • profile   │      │ • validation │
    │             │      │              │
    └─────────────┘      └──────┬───────┘
          ▲                     │
          │                     ▼
          └─────────────────────────────────┐
                                            │
                       ┌────────────────────┴──────────┐
                       ▼                               ▼
              ┌──────────────────┐      ┌─────────────────────┐
              │   SQLite DB      │      │ JSON Files (cache)  │
              │ (food_scanner.db)│      │                     │
              │                  │      │ • scan_history.json │
              │ Tables:          │      │ • preferences.json  │
              │ • users          │      │ • user_prefs.json   │
              │ • profiles       │      │                     │
              │ • preferences    │      │ [Backup/Cache only] │
              │ • scans          │      │                     │
              │ • scan_results   │      │                     │
              │ • nutrition_cache│      │                     │
              │                  │      │                     │
              │ [PRIMARY STORAGE]│      │ [SECONDARY STORAGE] │
              └──────────────────┘      └─────────────────────┘
```

---

## 5. Data Storage Status Summary

### What's Currently Stored
```
✅ USERS TABLE
   - 1 user registered: "raj" (email: venkatarajesh016@gmail.com)
   - Password hashed with PBKDF2-HMAC-SHA256
   - Registered: 2026-04-03 18:03:26

⏳ PROFILES TABLE
   - Empty (0 records)
   - Will be auto-created when user completes onboarding
   - Will store: age, gender, weight, height, diet, state, cuisine, goal, budget, activity

⏳ PREFERENCES TABLE
   - Empty (0 records)
   - Will store dietary restrictions (vegan, no_sugar, low_sodium, gluten_free)

⏳ SCANS TABLE
   - Empty (0 records)
   - Will store food barcode scans with timestamps

⏳ OTHER TABLES
   - scan_results, nutrition_cache: Empty
```

### Frontend Storage
```
✅ localStorage.token
   - JWT Bearer token for authentication
   - Valid for 30 days
   - Sent with every API request in Authorization header

✅ localStorage.user
   - User ID, email, name
   - Set on successful login

✅ localStorage.profile_complete
   - Set to true after onboarding
   - Used to determine if user should skip onboarding

❌ localStorage.profile
   - NOT cached in localStorage
   - Always fetched from SQLite backend via GET /api/profile
   - Fetched automatically when Profile tab is clicked
```

---

## 6. How to Populate the Data

### Step 1: Complete Onboarding (Create Profile)
```
1. Frontend → AaharOnboardingForm.js
2. User fills 4 steps:
   - Step 1: age, gender, weight, height
   - Step 2: diet_type, state, cuisine
   - Step 3: health_goal
   - Step 4: weekly_budget, activity_level
3. Form POSTs to /api/profile with Bearer token
4. Backend creates profiles table if not exists
5. Data inserted into profiles table
```

### Step 2: Verify Data in Database
```bash
cd backend
python check_db.py

# Should show:
# PROFILES TABLE:
#   Record 1:
#     id: 1
#     user_id: 1
#     age: 28
#     gender: Female
#     ... etc
```

### Step 3: Verify Data in Frontend
```
1. Click Profile tab
2. Profile fetches from GET /api/profile
3. Data displays organized by step
4. localStorage shows profile data
```

---

## 7. Data Access Commands

### View Database with SQLite CLI
```bash
cd backend

# View all tables
sqlite3 food_scanner.db ".tables"

# View users table
sqlite3 food_scanner.db "SELECT * FROM users;"

# View profiles table
sqlite3 food_scanner.db "SELECT * FROM profiles;"

# View with formatted output
sqlite3 food_scanner.db -header -column "SELECT * FROM profiles;"
```

### View Database with Python Script
```bash
cd backend
python check_db.py
```

### View Browser LocalStorage in Console
```javascript
// F12 → Console tab
console.log(localStorage)
console.table(localStorage)  // Better formatting

// Profile data is NOT in localStorage - fetched from backend instead
// To see profile data, open Network tab and check GET /api/profile response
```

---

## 8. Data Persistence Flow

```
Registration
  ↓
Email + Password → /auth/register → Hash password → Insert into users table
                                                     ↓
                                              Return user ID + token
                                                     ↓
                                              Store token in localStorage

Onboarding
  ↓
Form Input (10 fields) → POST /api/profile + Bearer token
                              ↓
                        Verify token → Extract user_id
                              ↓
                        Create profiles table if not exists
                              ↓
                        Insert/Update profiles table
                              ↓
                        Set localStorage.profile_complete = true
                              ↓
                        Redirect to Dashboard

Profile Display
  ↓
Click Profile tab → GET /api/profile + Bearer token
                         ↓
                   Backend queries SQLite profiles table
                         ↓
                   Return full profile JSON (10 fields)
                         ↓
                   Frontend renders profile card sections
                         ↓
                   Profile data is displayed but NOT cached
                         ↓
                   Refresh tab = Fresh data fetched from DB


---

## 9. Backup & Recovery

### Database Backup Location
```
Original: c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend\food_scanner.db

To backup:
cp food_scanner.db food_scanner.db.backup
```

### Restore from Backup
```
cp food_scanner.db.backup food_scanner.db
```

### Reset Database (Delete All Data)
```powershell
# WARNING: This deletes all data!
rm c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend\food_scanner.db

# Then restart the app - new database will be created
```

---

## 10. Storage Size Estimates

| Table | Records | Avg Size | Total |
|-------|---------|----------|-------|
| users | 1 | 200 bytes | 200 bytes |
| profiles | 0 | 500 bytes | 0 bytes |
| scans | 0 | 100 bytes | 0 bytes |
| scan_results | 0 | 80 bytes | 0 bytes |
| preferences | 0 | 50 bytes | 0 bytes |
| nutrition_cache | 0 | 1 KB | 0 KB |
| **Total** | **1** | - | **< 1 MB** |

### After Full Daily Usage
- 30 food scans per user = ~50 KB
- 1 month of data = ~1.5 MB
- 1 year of data = ~18 MB
- 10 users for 1 year = ~180 MB

---

## Summary

### Data is Stored In 3 Places:

1. **SQLite Database** (Primary, Server) ✅ MAIN STORAGE
   - Location: `backend/food_scanner.db`
   - Contains: users, profiles, scans, preferences, nutrition data
   - **Profile data ONLY stored here** - not cached in browser
   - Persistent until database is deleted

2. **Browser LocalStorage** (Secondary, Client) 
   - Location: Browser DevTools → Application → LocalStorage
   - Contains: JWT token, user info, **profile_complete flag only**
   - Persists across browser sessions (until cleared)
   - ⚠️ Profile data NOT cached here for security and freshness

3. **JSON Files** (Backup/Cache)
   - Location: `backend/app/data/`
   - Contains: scan_history.json, user_preferences.json
   - Optional - used for optional offline caching only

**Data Caching Strategy:** 
- ✅ Profile data fetched fresh from SQLite every time Profile tab is opened
- ✅ GET /api/profile called automatically on tab load
- ✅ Always latest data from database
- ✅ No stale data issues
- ✅ No sync conflicts

**Current Status:** ✅ Database ready, 1 user registered, waiting for onboarding completion to populate profiles table.


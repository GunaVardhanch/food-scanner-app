# Aahar AI - Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AAHAR AI SYSTEM ARCHITECTURE                 │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│   CLIENT (Browser)       │
│  - Next.js Frontend      │
│  - React Components      │
│  - Tailwind CSS          │
│  - Mobile Optimized      │
└────────────┬─────────────┘
             │
             │ HTTPS/JSON
             │
┌────────────┴──────────────┐
│  API Gateway             │
│  - CORS Enabled          │
│  - Bearer Token Auth     │
│  - Rate Limiting         │
└────────────┬──────────────┘
             │
             │ HTTP/REST
             │
┌────────────┴─────────────────────────────┐
│    BACKEND (Flask Server)                │
│  ┌───────────────────────────────────┐   │
│  │ Routes & Controllers              │   │
│  │ - /auth (register, login, me)     │   │
│  │ - /api/profile (GET, POST)        │   │
│  │ - /api/meal-plan (GET)            │   │
│  │ - /api/scan (POST)                │   │
│  │ - /api/preferences (GET, POST)    │   │
│  │ - /api/analytics (GET)            │   │
│  └───────────────────────────────────┘   │
│                 │                        │
│  ┌──────────────┴────────────────────┐   │
│  │   Business Logic Layer            │   │
│  │ - Profile Service                 │   │
│  │ - Meal Plan Generator             │   │
│  │ - Nutrition Calculator            │   │
│  │ - Health Score Analyzer           │   │
│  │ - Authentication Service          │   │
│  └──────────────┬────────────────────┘   │
│                 │                        │
│  ┌──────────────┴────────────────────┐   │
│  │   Data Layer                      │   │
│  │ - SQLite Database Connection      │   │
│  │ - Query Builder                   │   │
│  │ - Transaction Manager             │   │
│  └──────────────┬────────────────────┘   │
└─────────────────┼────────────────────────┘
                  │
                  │ SQL
                  │
         ┌────────┴────────┐
         │  SQLite DB      │
         │ (food_scanner)  │
         │ - users         │
         │ - profiles      │
         │ - preferences   │
         │ - scans         │
         │ - scan_results  │
         │ - nutrition_cache
         └────────────────┘
```

---

## 📊 Data Flow Diagram

### 1. Registration & Login Flow

```
User Input (Email/Password)
    ↓
Frontend: AaharOnboardingForm
    ↓
POST /auth/register or /auth/login
    ↓
Backend: Password Hashing (PBKDF2)
    ↓
Database: users table INSERT/SELECT
    ↓
Backend: JWT Token Generation
    ↓
Frontend: Store token in localStorage
    ↓
Frontend: Set Authorization header
```

### 2. Profile Data Collection & Storage

```
User Input (4-Step Form)
    ↓
Frontend: AaharOnboardingForm
    - Step 1: Biometrics (age, gender, weight, height)
    - Step 2: Preferences (diet_type, state, cuisine)
    - Step 3: Health Goal
    - Step 4: Lifestyle (weekly_budget, activity_level)
    ↓
Frontend: Validation (type, range, enum)
    ↓
POST /api/profile + Bearer Token
    ↓
Backend: Verify Bearer Token
    ↓
Backend: Validation (age 10-120, weight 20-300, etc.)
    ↓
Backend: Create profiles table if not exists
    ↓
Database: UPSERT profiles table
    ↓
Backend: Return 200 + full profile data
    ↓
Frontend: Update localStorage (profile_complete: true)
    ↓
Frontend: Redirect to Dashboard
```

### 3. Profile Display & Fetching

```
User Opens Profile Tab
    ↓
Frontend: AaharProfileTab useEffect Hook
    - Read token from props
    - Call GET /api/profile
    ↓
GET /api/profile + Bearer Token
    ↓
Backend: Verify Bearer Token + Get user_id
    ↓
Database: SELECT * FROM profiles WHERE user_id=?
    ↓
Backend: Check if profile exists
    │
    ├─→ No Profile → Return { profile_complete: false }
    │
    └─→ Profile Exists → Return { all fields, profile_complete: true }
    ↓
Frontend: Render Profile Sections
    - Step 1: Biometrics (2x2 grid of color cards)
    - Step 2: Preferences (badges and icons)
    - Step 3: Health Goal (gradient banner)
    - Step 4: Lifestyle (activity + budget with daily calc)
    ↓
Frontend: Display ✅ Profile Complete or ⚙️ Complete Profile CTA
```

---

## 🗄️ Database Schema

### Tables Structure

```
users
├── id (PK, integer)
├── email (unique, text)
├── password (hashed, text)
└── created_at (timestamp)

profiles
├── id (PK, integer)
├── user_id (FK→users.id, unique)
├── age (integer, 10-120)
├── gender (text)
├── weight (float, kg)
├── height (float, cm)
├── diet_type (text, enum)
├── state (text)
├── cuisine (text)
├── health_goal (text, enum)
├── weekly_budget (integer, ₹)
├── activity_level (text, enum)
├── created_at (timestamp)
└── updated_at (timestamp)

preferences
├── user_id (PK, FK→users.id)
├── vegan (boolean)
├── no_sugar (boolean)
├── low_sodium (boolean)
└── gluten_free (boolean)

scans
├── id (PK, integer)
├── user_id (FK→users.id)
├── barcode (text)
├── product_name (text)
├── quantity (integer)
└── scanned_at (timestamp)

scan_results
├── id (PK, integer)
├── scan_id (FK→scans.id)
├── calories (integer)
├── protein (float)
├── fat (float)
└── carbs (float)

nutrition_cache
├── product_id (PK, text)
├── nutrition_data (json)
└── last_updated (timestamp)
```

---

## 🔐 Authentication & Security

### Token-Based Authorization

```
1. Login
   User: email + password
   ↓
   Backend: Verify password (PBKDF2)
   ↓
   Backend: Generate JWT token (HS256, 30-day TTL)
   Response: { token: "eyJ..." }
   ↓
   Frontend: Store in localStorage

2. API Request
   Frontend: GET /api/profile
   Header: Authorization: Bearer eyJ...
   ↓
   Backend: Verify JWT signature
   ↓
   Backend: Check expiration
   ↓
   Backend: Extract user_id from token payload
   ↓
   Backend: Proceed with request

3. Token Expiration
   If token expired → 401 Unauthorized
   Frontend: Clear localStorage, redirect to login
```

### Password Hashing

```
User Password: "SecurePass@123"
    ↓
PBKDF2-HMAC-SHA256
  - Iterations: 100,000
  - Salt: Random
    ↓
Hashed: "$pbkdf2-sha256$100000$...$..."
    ↓
Database: Store hashed password
    ↓
On Login:
  - Hash submitted password
  - Compare hashes
  - If match → Generate token
```

---

## 🎯 Component Architecture

### Frontend Component Hierarchy

```
page.js (Homepage)
  ↓ (redirect to)
AaharDashboard.js (Main orchestrator)
├── AaharSplashScreen.js
├── AaharWelcomeScreen.js
├── AaharOnboardingForm.js (4-step form)
│   ├── Step 1: Biometrics
│   ├── Step 2: Preferences
│   ├── Step 3: Health Goal
│   └── Step 4: Lifestyle
├── AaharBottomNav.js (Tab navigation)
├── AaharHomeTab.js (Home content)
├── AaharMyPlanTab.js (Meal plans)
├── AaharGroceryTab.js (Shopping list)
├── AaharProfileTab.js (Profile + settings)
│   ├── Profile Display
│   ├── Edit Profile button
│   └── Sign Out button
└── FAB Chatbot

AaharProfileTab.js
├── useEffect Hook (Fetch profile on mount)
├── Loading Spinner
├── Step 1: Biometrics Section
│   ├── Age Card (orange)
│   ├── Gender Card (blue)
│   ├── Weight Card (red)
│   └── Height Card (blue)
├── Step 2: Preferences Section
│   ├── Diet Type Badge (green)
│   ├── State Display
│   └── Cuisine Display
├── Step 3: Health Goal
│   └── Gradient Badge
├── Step 4: Lifestyle Section
│   ├── Activity Level Badge (blue)
│   └── Weekly Budget Display (saffron)
└── Profile Status Indicator
```

### Backend Service Architecture

```
Flask App
├── routes.py
│   ├── /auth/register (POST)
│   ├── /auth/login (POST)
│   ├── /auth/me (GET)
│   ├── /api/profile (GET, POST)
│   ├── /api/preferences (GET, POST)
│   ├── /api/meal-plan (GET)
│   ├── /api/scan (POST)
│   └── /api/analytics (GET)
│
├── services/
│   ├── profile_service.py
│   │   ├── get_user_profile()
│   │   ├── save_profile()
│   │   └── validate_profile_data()
│   │
│   ├── meal_plan_generator.py
│   │   ├── generate_meal_plan()
│   │   ├── calculate_nutrition()
│   │   └── optimize_budget()
│   │
│   ├── nutrition_calculator.py
│   │   ├── calculate_daily_needs()
│   │   └── score_nutrition()
│   │
│   └── auth_service.py
│       ├── hash_password()
│       ├── verify_password()
│       ├── generate_token()
│       └── verify_token()
│
├── utils/
│   ├── validation.py
│   └── constants.py
│
└── database/
    └── connection.py

```

---

## 🔄 API Request/Response Cycle

### Example: Get User Profile

```
1. Frontend
   const token = localStorage.getItem('token')
   fetch('/api/profile', {
     headers: { 'Authorization': `Bearer ${token}` }
   })

2. Browser
   HTTP GET request sent to http://localhost:5001/api/profile
   Headers: 
     - Authorization: Bearer eyJ...
     - Content-Type: application/json

3. Backend - Flask Router
   @bp.route("/profile", methods=["GET", "POST"])
   def profile():
       # Route handler receives request

4. Backend - Authentication Layer
   token = extract_bearer_token(headers)
   user_id = verify_jwt_token(token)
   # If invalid → return 401 Unauthorized

5. Backend - Business Logic Layer
   profile = get_user_profile(user_id)
   # Query from database

6. Backend - Response Layer
   return jsonify({
     "user_id": 1,
     "age": 28,
     ...all fields...
     "profile_complete": true
   }), 200

7. Browser
   HTTP 200 OK response received
   Response body: JSON profile data

8. Frontend
   const profile = await response.json()
   setProfile(profile)
   # Component re-renders with profile data

9. User
   Sees Profile Tab with all 10 fields displayed
   Organized in 4 sections by step
   Colored cards and badges for visual appeal
```

---

## 📱 Mobile-First Responsive Design

```
Desktop (max-w-full)
┌──────────────────────────┐
│         Header           │
├──────────────────────────┤
│                          │
│    Profile Content       │
│  (organized in columns)  │
│                          │
├──────────────────────────┤
│       Footer/Nav         │
└──────────────────────────┘

Mobile (max-w-md)
┌──────────────────────────┐
│      Header              │
├──────────────────────────┤
│                          │
│  Profile Content         │
│  (stacked vertically)    │
│                          │
├──────────────────────────┤
│      Bottom Nav (FAB)    │
└──────────────────────────┘

Tailwind Breakpoints Used:
- Mobile: default (no prefix)
- Tablet & up: md: (768px)
- Desktop & up: lg: (1024px)

Container: max-w-md (fixed 448px)
Main constraint: Mobile-first approach
```

---

## 🔌 Integration Points

### Frontend ↔ Backend

| Component | Endpoint | Method | Auth | Data |
|-----------|----------|--------|------|------|
| AaharWelcomeScreen | /auth/register | POST | ❌ | email, password |
| AaharWelcomeScreen | /auth/login | POST | ❌ | email, password |
| AaharDashboard | /auth/me | GET | ✅ | - |
| AaharOnboardingForm | /api/profile | POST | ✅ | 10 profile fields |
| AaharProfileTab | /api/profile | GET | ✅ | - |
| AaharMyPlanTab | /api/meal-plan | GET | ✅ | - |
| AaharHomeTab | /api/analytics | GET | ✅ | period |
| Barcode Scanner | /api/scan | POST | ✅ | barcode, name |
| Preferences Modal | /api/preferences | GET/POST | ✅ | preferences |

---

## 🚀 Deployment Architecture

```
Production Environment:
┌─────────────────────────┐
│   Client Tier           │
│ - Vercel (Frontend)     │
│ - CDN (Static Assets)   │
│ - HTTPS Certificate     │
└────────┬────────────────┘
         │
         │ Internet
         │
┌────────┴────────────────┐
│   Application Tier      │
│ - Railway (Backend)     │
│ - Flask WSGI (Gunicorn) │
│ - Environment Variables │
│ - CORS Configuration    │
└────────┬────────────────┘
         │
         │ SQL
         │
┌────────┴────────────────┐
│   Data Tier             │
│ - PostgreSQL (prod)     │
│ - Connection Pooling    │
│ - Backups               │
│ - Replication          │
└─────────────────────────┘
```

---

## 📊 Data Flow Summary

```
1. User Registration
   Email + Password → /auth/register → Hash → DB users table → Token

2. User Login
   Email + Password → /auth/login → Verify hash → Generate token → localStorage

3. Profile Creation (Onboarding)
   Form Input (10 fields) → POST /api/profile → Validate → DB profiles table → Success

4. Profile Display
   Click Profile Tab → GET /api/profile + Token → Query DB → Render Component

5. Meal Plan Generation
   Profile Data → ML Model → Generate plan → POST /api/meal-plan → Display

6. Food Scanning
   Barcode → ML OCR → Recognize → Lookup OFF API → POST /api/scan → Update nutrition

7. Analytics
   Historical data → Aggregate → Calculate scores → GET /api/analytics → Dashboard
```

---

## ✅ Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Frontend Architecture | ✅ Complete | 9 components built |
| Authentication | ✅ Complete | JWT + Bearer tokens |
| Profile Schema | ✅ Complete | 14-column table |
| Profile Endpoints | ✅ Complete | GET & POST working |
| Profile Display | ✅ Complete | Organized by steps |
| Meal Plan Endpoint | 🔨 In Progress | Needs ML integration |
| Scan Integration | 🔨 In Progress | OCR model pending |
| Analytics Dashboard | ⏳ Not Started | Metrics calculation |

---

## 🎯 Next Steps

1. **Test End-to-End Flow**
   - Run both frontend and backend
   - Complete registration → onboarding → profile display
   - Verify database persistence

2. **Meal Plan Generation**
   - Create ML-based meal planner
   - Integrate with profile data
   - Connect to AaharMyPlanTab

3. **Barcode Scanning**
   - Integrate camera/barcode scanner
   - Setup OCR pipeline
   - Link to food database

4. **Production Deployment**
   - Deploy frontend to Vercel
   - Deploy backend to Railway
   - Setup PostgreSQL database
   - Configure CI/CD pipelines

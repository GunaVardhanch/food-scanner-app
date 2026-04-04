# Aahar AI - User Profile Data Schema & Storage

## 📊 Database Schema

### Table: `profiles` (SQLite)

```sql
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    -- Step 1: Biometrics
    age INTEGER,
    gender TEXT,
    weight REAL,
    height REAL,
    -- Step 2: Preferences
    diet_type TEXT,
    state TEXT,
    cuisine TEXT,
    -- Step 3: Health Goal
    health_goal TEXT,
    -- Step 4: Lifestyle
    weekly_budget INTEGER,
    activity_level TEXT,
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

## 🔄 Data Flow

### 1. **Collection Phase** (Frontend: AaharOnboardingForm.js)

**Step 1 - Biometrics:**
- age (10-120 years)
- gender (Male/Female/Other)
- weight (20-300 kg)
- height (100-250 cm)

**Step 2 - Preferences:**
- diet_type (veg, eggetarian, non-veg, vegan, jain, satvik)
- state (28 Indian states)
- cuisine (North Indian, South Indian, East Indian, West Indian, Continental)

**Step 3 - Health Goal:**
- health_goal (Lose Weight, Gain Muscle, Stay Healthy, Pregnancy, Diabetes, PCOD, Senior)

**Step 4 - Lifestyle:**
- weekly_budget (₹100 - ₹50,000)
- activity_level (sedentary, light, moderate, active)

### 2. **Storage Phase** (Backend: /api/profile POST)

**Endpoint:** `POST /api/profile`
- **Header:** `Authorization: Bearer <token>`
- **Body:** JSON with profile fields
- **Response:** Saves to SQLite `profiles` table

### 3. **Display Phase** (Frontend: AaharProfileTab.js)

**Endpoint:** `GET /api/profile`
- **Header:** `Authorization: Bearer <token>`
- **Response:** Returns full profile data

**UI Display:**
- Biometrics section with colorful cards (Step 1)
- Preferences section with badges (Step 2)
- Health goal banner (Step 3)
- Lifestyle section with budget details (Step 4)

## 📝 Data Validation

### Age
- Range: 10-120 years
- Type: Integer
- Required: Yes

### Weight
- Range: 20-300 kg
- Type: Float
- Required: Yes

### Height
- Range: 100-250 cm
- Type: Float
- Required: Yes

### Weekly Budget
- Range: ₹100-₹50,000
- Type: Integer
- Required: Yes

### Enums
- **Diet Type**: veg, eggetarian, non-veg, vegan, jain, satvik
- **Activity Level**: sedentary, light, moderate, active
- **Health Goals**: multiple options
- **States**: 28 Indian states

## 🔐 Security

- All endpoints require Bearer token authentication
- Passwords hashed with PBKDF2-HMAC-SHA256
- Profile data is user-specific (tied to user_id)
- Only authenticated users can POST/GET their profile

## 📱 Frontend Components

### AaharOnboardingForm.js
- Collects 4-step user input
- Validates data before submission
- POSTs to `/api/profile`
- Stores `profile_complete: true` in localStorage

### AaharProfileTab.js
- Fetches profile via GET `/api/profile`
- Displays all data in organized sections
- Shows loading state while fetching
- Provides Edit Profile button

### AaharDashboard.js
- Orchestrates component flow
- Manages token and user state
- Passes token prop to ProfileTab

## 💾 Sample Profile Data

```json
{
  "user_id": 1,
  "age": 28,
  "gender": "Female",
  "weight": 65.5,
  "height": 165,
  "diet_type": "vegetarian",
  "state": "Maharashtra",
  "cuisine": "North Indian",
  "health_goal": "lose_weight",
  "weekly_budget": 3000,
  "activity_level": "moderate",
  "created_at": "2026-04-04 10:30:00",
  "updated_at": "2026-04-04 10:30:00",
  "profile_complete": true
}
```

## 🚀 API Endpoints

### POST /api/profile
**Save user profile data**

Request:
```json
{
  "age": 28,
  "gender": "Female",
  "weight": 65.5,
  "height": 165,
  "diet_type": "vegetarian",
  "state": "Maharashtra",
  "cuisine": "North Indian",
  "health_goal": "lose_weight",
  "weekly_budget": 3000,
  "activity_level": "moderate"
}
```

Response:
```json
{
  "status": "ok",
  "user_id": 1,
  "profile": {...all fields...},
  "profile_complete": true
}
```

### GET /api/profile
**Retrieve user profile data**

Response:
```json
{
  "user_id": 1,
  "age": 28,
  "gender": "Female",
  "weight": 65.5,
  "height": 165,
  "diet_type": "vegetarian",
  "state": "Maharashtra",
  "cuisine": "North Indian",
  "health_goal": "lose_weight",
  "weekly_budget": 3000,
  "activity_level": "moderate",
  "created_at": "2026-04-04 10:30:00",
  "updated_at": "2026-04-04 10:30:00",
  "profile_complete": true
}
```

## ✅ What's Implemented

✅ Backend schema created in routes.py  
✅ POST /api/profile endpoint validates and stores data  
✅ GET /api/profile endpoint retrieves user data  
✅ Frontend form collects all 4 steps  
✅ Profile tab fetches and displays data  
✅ Data validation on both frontend and backend  
✅ SQLite database persistence  
✅ JWT token-based authentication  

## 📊 Database Management

To check stored data:
```bash
cd backend
python check_db.py
```

This displays all tables including the profiles table with user data.

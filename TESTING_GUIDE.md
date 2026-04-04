# Aahar AI - End-to-End Testing Guide

## 🚀 Step-by-Step Testing Procedure

### Prerequisites
- Node.js and Python installed
- Both frontend and backend running
- SQLite database at `backend/food_scanner.db`

---

## Phase 1: Start Services

### Terminal 1 - Backend Flask Server
```bash
cd backend
python run_local.py
```
✅ Expected output: Flask running on `http://localhost:5001`

### Terminal 2 - Frontend Next.js Dev Server
```bash
cd frontend
npm run dev
```
✅ Expected output: Next.js running on `http://localhost:3000`

---

## Phase 2: User Authentication Flow

### Step 1: Navigate to App
1. Open browser: `http://localhost:3000`
2. You should see: Splash screen with Aahar AI branding (3-5 seconds auto-redirect)
3. Should redirect to: `http://localhost:3000/aahar`

### Step 2: Create New User (if needed)
1. Click "Get Started" on Welcome screen
2. Enter email and password
3. Click "Register"
4. ✅ Expected: Toast notification "Signin successful!"
5. Receive Bearer token (stored in localStorage as `token`)

**Sample User Data:**
- Email: `test@example.com`
- Password: `Test@123`

### Step 3: Login (for existing users)
1. Click "Sign In" on Welcome screen
2. Enter email and password
3. Click "Sign In"
4. ✅ Expected: Dashboard loads, token stored in localStorage

**Existing Test User:**
- Email: `venkatarajesh016@gmail.com`
- Password: (check your backend logs or set new password)

---

## Phase 3: Complete Onboarding (Steps 1-4)

### Step 1: Biometrics
1. Navigate to Onboarding form after login
2. Enter:
   - **Age**: 28 (range 10-120)
   - **Gender**: Select Female/Male/Other
   - **Weight**: 65 (kg, range 20-300)
   - **Height**: 165 (cm, range 100-250)
3. Click "Next" → Proceed to Step 2

### Step 2: Preferences
1. **Diet Type**: Select from 6 options
   - 🌱 Vegetarian
   - 🥚 Eggetarian
   - 🍗 Non-Vegetarian
   - 🌾 Vegan
   - 🙏 Jain
   - 🕉️ Satvik
2. **State**: Select from 28 Indian states (default: Maharashtra)
3. **Cuisine**: Select cooking style
   - North Indian
   - South Indian
   - East Indian
   - West Indian
   - Continental
4. Click "Next" → Proceed to Step 3

### Step 3: Health Goal
1. Select primary health focus from:
   - 🏃 Lose Weight
   - 💪 Gain Muscle
   - 🥗 Stay Healthy
   - 🤰 Pregnancy Nutrition
   - 🩺 Manage Diabetes
   - 💊 PCOD / Hormonal Health
   - 👴 Senior Nutrition
2. Click "Next" → Proceed to Step 4

### Step 4: Lifestyle
1. **Weekly Budget**: Drag slider (₹100 - ₹50,000)
   - Show: Daily budget calculation (budget ÷ 7)
   - Example: ₹3000/week = ₹428/day
2. **Activity Level**: Select one
   - Sedentary (little to no exercise)
   - Light (light exercise 1-3 days/week)
   - Moderate (exercise 3-5 days/week)
   - Active (intense exercise 6-7 days/week)
3. Click "Complete Profile"

### ✅ Expected Result:
- Form data POSTs to `/api/profile` endpoint
- Backend validates all fields
- Creates entry in `profiles` table
- Returns success response:
  ```json
  {
    "status": "ok",
    "user_id": <user_id>,
    "profile": {...all fields...},
    "profile_complete": true
  }
  ```
- Redirects to Dashboard
- localStorage shows `profile_complete: true`

---

## Phase 4: Verify Data in Database

### Run Database Check Script
```bash
cd backend
python check_db.py
```

### Expected Output:
```
Tables in database: ['users', 'profiles', 'preferences', 'scans', 'scan_results', ...]

================================================================================

USERS TABLE:
  Record 1:
    id: 1
    email: test@example.com
    created_at: 2026-04-04 10:30:00

================================================================================

PROFILES TABLE:
  Record 1:
    id: 1
    user_id: 1
    age: 28
    gender: Female
    weight: 65.0
    height: 165.0
    diet_type: vegetarian
    state: Maharashtra
    cuisine: North Indian
    health_goal: lose_weight
    weekly_budget: 3000
    activity_level: moderate
    created_at: 2026-04-04 10:30:00
    updated_at: 2026-04-04 10:30:00

================================================================================
```

---

## Phase 5: Verify Profile Display

### Step 1: Navigate to Profile Tab
1. From Dashboard, click on Profile icon (bottom nav)
2. Wait for data to load (loading spinner should show briefly)

### Step 2: Verify Display Sections

#### Section 1: Biometrics (Step 1)
```
👤 Step 1: Biometrics
┌────────────────┬────────────────┐
│ 🎂 Age: 28     │ 👩 Gender:     │
│ years          │ Female         │
├────────────────┼────────────────┤
│ ⚖️  Weight:    │ 📏 Height:     │
│ 65 kg          │ 165 cm         │
└────────────────┴────────────────┘
```

#### Section 2: Preferences (Step 2)
```
🍽️ Step 2: Preferences
- Diet Type: 🌱 Vegetarian
- State: 📍 Maharashtra
- Cuisine: 🍛 North Indian
```

#### Section 3: Health Goal (Step 3)
```
🎯 Step 3: Health Goal
┌──────────────────────────────┐
│ 🏃 Lose Weight               │
│ Primary Focus                │
└──────────────────────────────┘
```

#### Section 4: Lifestyle (Step 4)
```
💪 Step 4: Lifestyle
- Activity Level: 🏋️ Moderate
- Weekly Budget: ₹3,000 / week
- Daily Budget: ₹428 / day
```

#### Profile Status
```
✅ Profile Complete | Last Updated: 2026-04-04 10:30:00
```

---

## Phase 6: Browser Developer Console Checks

### Check 1: Verify Bearer Token
```javascript
// In Console (F12):
console.log(localStorage.getItem('token'))
// Expected: Long JWT token string (starts with eyJ...)
```

### Check 2: Verify Profile Data Load
```javascript
// In Console:
console.log(JSON.parse(localStorage.getItem('profile')))
// Expected: All profile fields showing
```

### Check 3: Verify API Call Success
```javascript
// In Network tab (F12):
// Filter: fetch/XHR
// Look for GET request to: http://localhost:5001/api/profile
// Status: 200
// Response preview should show all profile fields
```

---

## Phase 7: Test Data Refresh

### Step 1: Edit Profile (Simulate)
1. Manually update a field in the database
2. Or complete onboarding with different values
3. Refresh the browser (F5)

### Step 2: Verify Update
1. Profile Tab should reload
2. New values should display

---

## 🐛 Troubleshooting

### Issue 1: Token Not Found
**Error:** Bearer token missing or null
**Solution:**
```javascript
// In Console:
localStorage.setItem('token', 'your-bearer-token-here')
```

### Issue 2: Profile Data Not Loading
**Error:** `profile_complete: false` or blank section
**Possible Causes:**
- User hasn't completed onboarding yet
- Backend `/api/profile` endpoint not responding
- Network request failed

**Debug:**
1. Check Network tab (F12) for failed requests
2. Verify backend running on port 5001
3. Check browser console for errors
4. Run: `python check_db.py` to verify DB has profiles table

### Issue 3: CORS Errors
**Error:** "Access to XMLHttpRequest has been blocked by CORS policy"
**Solution:** Backend should have CORS enabled in `run_local.py`
```python
from flask_cors import CORS
CORS(app)
```

### Issue 4: Database File Not Found
**Error:** `sqlite3.OperationalError: unable to open database file`
**Solution:**
```bash
cd backend
# Create empty database:
sqlite3 food_scanner.db "SELECT 1;"
# Then run the app
```

---

## ✅ Validation Checklist

- [ ] Splash screen redirects to `/aahar` after 3-5 seconds
- [ ] Welcome screen shows "Get Started" and "Sign In" buttons
- [ ] Registration creates user in database
- [ ] Login with existing credentials works
- [ ] Onboarding form accepts all 4 steps
- [ ] Form validation works (age 10-120, weight 20-300, etc.)
- [ ] Form submission POSTs to `/api/profile` successfully
- [ ] profiles table created in database after first submission
- [ ] Profile Tab loads and displays all 10 fields
- [ ] Data organized into 4 sections (Biometrics, Preferences, Health Goal, Lifestyle)
- [ ] Budget calculation correct (weekly ÷ 7 = daily)
- [ ] Bearer token sent in Authorization header
- [ ] Profile updates when form resubmitted
- [ ] check_db.py shows all profile data

---

## 📊 Sample Complete Flow

```
1. User starts app → Splash screen
2. 3-5 sec delay → Redirects to /aahar
3. Welcome page → "Get Started" button
4. Registration/Login → Bearer token in localStorage
5. Dashboard loads → 5 tabs visible
6. User clicks onboarding banner
7. Step 1: Biometrics (age 28, gender Female, weight 65, height 165)
8. Step 2: Preferences (veg, maharashtra, north indian)
9. Step 3: Health Goal (lose_weight)
10. Step 4: Lifestyle (budget ₹3000, activity moderate)
11. Click Complete → POSTs to /api/profile
12. Backend responds with 200 + profile data
13. Redirect to Dashboard
14. Click Profile tab
15. Fetch GET /api/profile with Bearer token
16. Display all 10 fields organized by step
17. Show ✅ Profile Complete status
18. User can click Edit Profile to modify
19. check_db.py confirms data in profiles table
```

---

## 🎯 Expected Outcomes

### Database State After Testing:
- ✅ users table: 1+ records with test user(s)
- ✅ profiles table: 1+ records with complete profile data
- ✅ All 10 fields populated (age, gender, weight, height, diet_type, state, cuisine, health_goal, weekly_budget, activity_level)
- ✅ Timestamps showing creation and last update

### Frontend State After Testing:
- ✅ Token successfully stored and used for authentication
- ✅ Profile data displayed on Profile Tab
- ✅ All sections color-coded and properly formatted
- ✅ Daily budget calculation working
- ✅ Edit and Sign Out buttons functional

### Backend State After Testing:
- ✅ Flask running without errors on port 5001
- ✅ /api/profile endpoint responding with 200 status
- ✅ Data validation working (age, weight, height ranges)
- ✅ Bearer token authentication working
- ✅ Database updates happening correctly

---

## Next Working Steps

After successful end-to-end testing:

1. **Real Meal Plan Generation**
   - Create `/api/meal-plan` endpoint
   - Use profile data to generate 7-day meal plans
   - Connect to AaharMyPlanTab.js

2. **Nutrition Tracking**
   - Integrate barcode scanning
   - Calculate daily nutrition from scans
   - Compare against profile budget/goals

3. **Chat Integration**
   - Connect chatbot to profile
   - Provide personalized recommendations
   - Answer nutrition questions

4. **Analytics Dashboard**
   - Show profile progress
   - Visualize spending vs budget
   - Track health metrics over time

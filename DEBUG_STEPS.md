# Debug Steps for Profile 404 Error

## Step 1: Restart Backend with New Logging

**In PowerShell (backend terminal):**
```powershell
# Stop the current backend (Ctrl+C)
# Then:
cd "c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend"
python run_local.py
```

**You should see:**
```
[TOKEN] Token valid
[PROFILE] Request: POST /api/profile
```

---

## Step 2: Submit Profile Form

**In Browser:**
1. Navigate to http://localhost:3000/aahar
2. Fill out all 4 onboarding steps:
   - Step 1: Age, Gender, Weight, Height
   - Step 2: Diet Type, State, Cuisine
   - Step 3: Health Goal
   - Step 4: Weekly Budget, Activity Level
3. Click "Complete Profile"

---

## Step 3: Check Backend Terminal Output

**CRITICAL:** Copy what you see in the **backend terminal** when you submit the profile.

Look for lines like:
```
[PROFILE] Request: POST /api/profile
[DEBUG] Authorization header: Bearer eyJ...
[TOKEN] Decoded data: {'sub': 1, 'exp': ...}
[PROFILE] Extracted user_id: 1
```

**OR if it fails, you'll see:**
```
[DEBUG] Authorization header: MISSING...
[TOKEN] ❌ Signature mismatch
[TOKEN] ❌ Token expired
[PROFILE] ❌ Not authenticated!
```

---

## Step 4: Check Browser Console

**In Browser (F12 → Console):**

Look for:
```
📤 Submitting profile with token: eyJ...
📥 Profile response: 200 {...}
✅ Profile saved successfully!
```

---

## What to Share

**Please copy-paste:**

1. **Backend Terminal Output** when submitting profile (look for [PROFILE], [TOKEN], [DEBUG] lines)
2. **Browser Console Output** when submitting profile (look for 📤, 📥, ✅ lines)
3. **Run this command:**
   ```bash
   cd backend && python check_db.py
   ```
   And show if profiles table exists

This will help identify exactly where the token authentication is failing.

# Backend Startup Guide

## New Gemini API Key
**Key**: `AIzaSyBvtY_L22WMYl9Y-blPV_VkGLVzpYTs4gw`

## Starting the Backend

### Option 1: Using PowerShell (Recommended)
```powershell
powershell -ExecutionPolicy Bypass -File "c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend\start_backend.ps1"
```

### Option 2: Using Batch File
```cmd
"c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend\restart_backend.bat"
```

### Option 3: Manual PowerShell
```powershell
$env:GEMINI_API_KEY = "AIzaSyBvtY_L22WMYl9Y-blPV_VkGLVzpYTs4gw"
Push-Location "c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend"
python run_local.py
```

## Backend Endpoints

- **Auth**: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- **Scan**: `POST /api/scan` (barcode scanning)
- **Chat**: `POST /api/chat` (Groq-powered chatbot)
- **Profile**: `POST /api/profile`, `GET /api/profile`
- **Analytics**: `GET /analytics`
- **History**: `GET /history`

## Health Check
```
curl http://localhost:5001/api/health
```

## Environment Variables
- `GEMINI_API_KEY`: Google Generative AI key (now: AIzaSyBvtY_L22WMYl9Y-blPV_VkGLVzpYTs4gw)
- `GROQ_API_KEY`: Groq API key for chatbot (set separately)
- `PORT`: Backend port (default: 5001)

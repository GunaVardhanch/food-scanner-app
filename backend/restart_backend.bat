@echo off
REM Kill any existing Python processes on port 5001
echo Stopping old backend processes...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":5001"') do (
    taskkill /PID %%a /F 2>nul
)

REM Wait a second for port to release
timeout /t 2 /nobreak

REM Start the backend with Gemini API key
echo.
echo 🚀 Starting Flask backend...
echo.
cd /d "c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend"
set GEMINI_API_KEY=AIzaSyBvtY_L22WMYl9Y-blPV_VkGLVzpYTs4gw
python run_local.py

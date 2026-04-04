# PowerShell script to start backend with Gemini API key
Write-Host "🧹 Cleaning up old processes..." -ForegroundColor Cyan
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "📂 Navigating to backend directory..." -ForegroundColor Cyan
Push-Location "c:\Users\hp\OneDrive\Desktop\nxt-wave\food-scanner-app\backend"

Write-Host "⚙️  Setting Gemini API key..." -ForegroundColor Cyan
$env:GEMINI_API_KEY = "AIzaSyBvtY_L22WMYl9Y-blPV_VkGLVzpYTs4gw"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "🚀 Starting Flask backend on http://localhost:5001..." -ForegroundColor Green
Write-Host "   Auth endpoints:  /auth/register, /auth/login, /auth/me" -ForegroundColor Gray
Write-Host "   Scan endpoint:   POST /api/scan" -ForegroundColor Gray
Write-Host "   Chat endpoint:   POST /api/chat" -ForegroundColor Gray
Write-Host "   Analytics:       GET  /analytics" -ForegroundColor Gray
Write-Host ""

& "C:\Users\hp\AppData\Local\Microsoft\WindowsApps\python3.13.exe" run_local.py

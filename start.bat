@echo off
title SentinelQ Launcher
echo ============================================
echo   Starting SentinelQ (Backend + Frontend)
echo ============================================
echo.

start "SentinelQ Backend" cmd /k "cd /d %~dp0backend && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
start "SentinelQ Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Two windows opened:
echo   Backend  -> http://localhost:8000
echo   Frontend -> http://localhost:5173   (open this in your browser)
echo.
echo Keep both windows open while using the app.
echo Close them to stop the servers.
echo.
timeout /t 8 >nul

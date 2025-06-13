@echo off
title AICounsel Servers Launcher

:: Start Backend Server
start "AICounsel Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload"

:: Wait for 3 seconds to let backend initialize first
timeout /t 3

:: Start Frontend Server
start "AICounsel Frontend" cmd /k "cd frontend && npm run dev"

echo Servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this window...
pause > nul 
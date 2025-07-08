@echo off
echo Starting AI Counsel Backend Server...

:: 가상환경 활성화
call venv\Scripts\activate.bat

:: 서버 시작
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause 
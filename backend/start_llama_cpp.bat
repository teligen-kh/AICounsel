@echo off
echo Starting AI Counsel Backend with llama-cpp-python...

:: 환경 변수 설정
set USE_LLAMA_CPP=true
set LLM_MODEL_TYPE=llama-2-7b-chat

:: 가상환경 활성화
call venv\Scripts\activate.bat

:: 서버 시작
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause 
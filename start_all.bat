@echo off
REM FOS Survey Agent - Start All Services
REM Run this script to start all AI services

echo ============================================================
echo FOS Voice Survey Agent - Starting Services
echo ============================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Starting services...
echo.

REM Start Whisper STT (port 8001)
echo [1/3] Starting Whisper STT on port 8001...
start "Whisper STT" cmd /k "cd /d %~dp0ai\stt && python -m uvicorn whisper_server:app --host 0.0.0.0 --port 8001"

REM Wait a bit for Whisper to start
timeout /t 3 /nobreak >nul

REM Start Piper TTS (port 8002)
echo [2/3] Starting Piper TTS on port 8002...
start "Piper TTS" cmd /k "cd /d %~dp0ai\tts && python -m uvicorn piper_server:app --host 0.0.0.0 --port 8002"

REM Wait a bit for Piper to start
timeout /t 2 /nobreak >nul

REM Start Backend (port 8000)
echo [3/3] Starting Backend on port 8000...
start "Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo ============================================================
echo All services started!
echo ============================================================
echo.
echo Services:
echo   - Backend:     http://localhost:8000
echo   - Voice UI:    http://localhost:8000/voice
echo   - Whisper STT: http://localhost:8001
echo   - Piper TTS:   http://localhost:8002
echo.
echo Press any key to exit (services will continue running)...
pause >nul

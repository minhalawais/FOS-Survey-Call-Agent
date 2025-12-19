@echo off
REM FOS Survey Agent - Start Local Services (No Docker)
REM Runs LiveKit, Ollama, Backend, and Agent as local processes

echo ============================================================
echo FOS Voice Survey Agent - Local LiveKit Stack
echo ============================================================

REM Set paths
set "OLLAMA_EXE=C:\Users\Mg\AppData\Local\Programs\Ollama\ollama.exe"

REM Check Ollama
if not exist "%OLLAMA_EXE%" (
    echo ERROR: Ollama not found at %OLLAMA_EXE%
    echo Please install Ollama from https://ollama.com
    pause
    exit /b 1
)

echo.
echo.
echo [1/4] Starting Ollama Server...
tasklist /fi "imagename eq ollama.exe" | find "ollama.exe" >nul
if %errorlevel%==0 (
    echo Ollama is already running. Skipping start.
) else (
    start "Ollama" cmd /k ""%OLLAMA_EXE%" serve"
)


echo.
echo [2/4] Starting LiveKit...
REM Check if using Cloud or Local
findstr /C:"LIVEKIT_URL=wss://" .env >nul
if %errorlevel%==0 (
    echo Using LiveKit Cloud - Configured in .env
) else (
    echo NOTE: For local LiveKit server, ensure 'livekit-server' is in PATH
    echo If this fails, please sign up for LiveKit Cloud and update .env
    start "LiveKit Server" cmd /k "livekit-server --dev --bind 0.0.0.0"
)

REM DETECT VIRTUAL ENVIRONMENT
set "VENV_ACTIVATE="
if exist ".venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=call .venv\Scripts\activate.bat"
    echo Found .venv, using it.
) else (
    if exist "venv\Scripts\activate.bat" (
        set "VENV_ACTIVATE=call venv\Scripts\activate.bat"
        echo Found venv, using it.
    ) else (
        if exist "backend\venv\Scripts\activate.bat" (
            set "VENV_ACTIVATE=call backend\venv\Scripts\activate.bat"
            echo Found backend\venv, using it.
        ) else (
            echo WARNING: No virtual environment found - .venv, venv, or backend\venv. Using system Python.
        )
    )
)

echo.
echo [3/4] Starting Backend API (Port 8000)...
if defined VENV_ACTIVATE (
    start "Backend API" cmd /k "%VENV_ACTIVATE% && cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
) else (
    start "Backend API" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
)

echo.
echo [4/4] Starting LiveKit Agent Worker...
echo Waiting for services to warm up...
timeout /t 5 /nobreak >nul
if defined VENV_ACTIVATE (
    start "Agent Worker" cmd /k "%VENV_ACTIVATE% && python -m agent.main dev"
) else (
    start "Agent Worker" cmd /k "python -m agent.main dev"
)

echo.
echo ============================================================
echo Services Starting...
echo ============================================================
echo.
echo 1. Access Voice UI: http://localhost:8000/voice
echo.
echo Press any key to exit launcher...
pause >nul

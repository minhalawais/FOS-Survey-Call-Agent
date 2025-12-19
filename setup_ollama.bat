@echo off
REM Setup Ollama Model (Fixes "ollama not found" error)

echo ============================================================
echo Installing Qwen 2.5 Model...
echo ============================================================

set "OLLAMA_Path=C:\Users\Mg\AppData\Local\Programs\Ollama\ollama.exe"

if not exist "%OLLAMA_Path%" (
    echo ERROR: Ollama not found at %OLLAMA_Path%
    echo Please install Ollama default location.
    pause
    exit /b 1
)

echo Found Ollama at: %OLLAMA_Path%
echo.
echo Pulling qwen2.5:7b model (this may take a while)...
"%OLLAMA_Path%" pull qwen2.5:7b

echo.
echo Model installed successfully!
echo You can now run start_local.bat
pause

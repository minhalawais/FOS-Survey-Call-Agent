@echo off
echo ============================================================
echo WARNING: Docker is not available.
echo Redirecting to LOCAL startup script...
echo ============================================================
timeout /t 2 /nobreak >nul
call start_local.bat

@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
if "%~1"=="" (
  python -B scripts\start_local_app.py tts --desktop
) else (
  python -B scripts\start_local_app.py tts --job "%~1"
)
if errorlevel 1 pause
endlocal

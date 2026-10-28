@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
set "PYTHONUNBUFFERED=1"
echo VoiceTTS is starting. Please wait while libraries load.
echo The browser will open automatically when ready: http://127.0.0.1:7865
echo Keep this window open while using VoiceTTS.
echo.
if "%~1"=="" (
  python -B scripts\start_local_app.py tts --desktop
) else (
  python -B scripts\start_local_app.py tts --job "%~1"
)
if errorlevel 1 pause
endlocal

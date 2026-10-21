@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
if "%~1"=="" (
  echo Usage: Start-24HReplier.cmd job-id
  exit /b 2
)
python -B scripts\start_local_app.py replier --job "%~1"
if errorlevel 1 pause
endlocal

@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
"extension\.runtime\qwen-tts\venv\Scripts\python.exe" -B "extension\src\qwen_tts_local.py" --open-browser
if errorlevel 1 pause

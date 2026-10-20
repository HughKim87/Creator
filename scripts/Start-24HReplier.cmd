@echo off
setlocal
cd /d "%~dp0.."
set "REPLIER_APP=%CD%\extension\.runtime\replier-desktop\24HReplier.exe"
if not exist "%REPLIER_APP%" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-24HReplier.ps1"
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
start "" "%REPLIER_APP%"
endlocal

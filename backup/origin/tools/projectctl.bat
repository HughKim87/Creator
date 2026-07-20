@echo off
setlocal

set "ROOT=%~dp0.."
set "SCRIPT=%ROOT%\tools\projectctl.py"
call "%ROOT%\tools\run_python.bat" "%SCRIPT%" %*
exit /b %ERRORLEVEL%

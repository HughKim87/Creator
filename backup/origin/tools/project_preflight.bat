@echo off
setlocal

set "ROOT=%~dp0.."
set "SCRIPT=%ROOT%\tools\project_preflight.py"
call "%ROOT%\tools\run_python.bat" "%SCRIPT%" %*
exit /b %ERRORLEVEL%

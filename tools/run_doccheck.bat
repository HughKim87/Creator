@echo off
setlocal

set "ROOT=%~dp0.."
set "SCRIPT=%ROOT%\tools\doccheck\check_docs.py"
call "%ROOT%\tools\run_python.bat" "%SCRIPT%" %*
exit /b %ERRORLEVEL%

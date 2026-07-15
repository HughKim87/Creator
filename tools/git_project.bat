@echo off
setlocal

for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "SAFE_ROOT=%ROOT:\=/%"

git -c "safe.directory=%SAFE_ROOT%" %*
exit /b %ERRORLEVEL%

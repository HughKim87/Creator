@echo off
setlocal

set "ROOT=%~dp0.."
set "SCRIPT=%ROOT%\tools\doccheck\check_docs.py"
set "PY="

if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  set "PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

if not defined PY (
  where py >nul 2>nul
  if %ERRORLEVEL%==0 (
    py -3 "%SCRIPT%" %*
    exit /b %ERRORLEVEL%
  )
)

if not defined PY (
  where python >nul 2>nul
  if %ERRORLEVEL%==0 (
    python "%SCRIPT%" %*
    exit /b %ERRORLEVEL%
  )
)

if defined PY (
  "%PY%" "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)

echo Python executable not found.
exit /b 1

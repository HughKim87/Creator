@echo off
setlocal
rem ============================================================
rem  MKV -> MP4 lossless remux (no re-encoding) - GENERIC TOOL
rem  Usage: drag & drop one or more .mkv files onto this file.
rem  Output: <same name>_remux.mp4 next to each source file.
rem  Requires: project ffmpeg at tools\ffmpeg\bin\ffmpeg.exe
rem ============================================================

set "FFMPEG=%~dp0ffmpeg\bin\ffmpeg.exe"
if not exist "%FFMPEG%" (
    echo [ERROR] ffmpeg not found: %FFMPEG%
    pause
    exit /b 1
)
if "%~1"=="" (
    echo Usage: drag and drop .mkv files onto this bat file.
    pause
    exit /b 1
)

:loop
if "%~1"=="" goto end
if exist "%~dpn1_remux.mp4" (
    echo [SKIP] already exists: %~n1_remux.mp4
    goto next
)
echo [START] %~nx1
"%FFMPEG%" -i "%~1" -c copy "%~dpn1_remux.mp4"
if errorlevel 1 (
    echo [ERROR] remux failed: %~nx1
) else (
    echo [OK] %~n1_remux.mp4
)
:next
shift
goto loop

:end
echo.
echo [ALL DONE]
pause

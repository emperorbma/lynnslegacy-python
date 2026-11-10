@echo off
setlocal
cd /d "%~dp0"

if not exist "gmap.exe" (
    echo gmap.exe not found in the project root.
    echo Build it with: build_gmap.bat
    pause
    exit /b 1
)

start "" /wait "%~dp0gmap.exe" %*
exit /b %ERRORLEVEL%

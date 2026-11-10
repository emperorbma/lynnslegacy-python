@echo off
setlocal
cd /d "%~dp0"

where fbc >nul 2>&1
if errorlevel 1 (
    echo FreeBASIC compiler ^(fbc^) not found on PATH.
    echo Install FreeBASIC, then re-run build_gmap.bat
    pause
    exit /b 1
)

where make >nul 2>&1
if errorlevel 1 (
    echo GNU make not found on PATH.
    pause
    exit /b 1
)

if not exist "fbsrc\src\gmap\obj" mkdir "fbsrc\src\gmap\obj"
make -C fbsrc/src/gmap %*
if errorlevel 1 (
    pause
    exit /b 1
)

if not exist "fbsrc\gmap.exe" (
    echo Build finished but fbsrc\gmap.exe is missing.
    pause
    exit /b 1
)

copy /Y "fbsrc\gmap.exe" "gmap.exe" >nul
echo Built gmap.exe ^(run with gmap.bat or ./gmap.sh^).
exit /b 0

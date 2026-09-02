@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo Create it with:
    echo   py -3 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -e ".[dev]"
    pause
    exit /b 1
)

if /I "%~1"=="/?" goto usage
if /I "%~1"=="-h" goto usage
if /I "%~1"=="help" goto usage
if /I "%~1"=="--help" goto usage

".venv\Scripts\python.exe" -m lynn %*
if errorlevel 1 pause
exit /b %ERRORLEVEL%

:usage
echo Usage: run.bat [objects^|map^|palette^|test^|help] [map] [--save spec]
echo   objects [map]  walk Lynn (default map: forest_fall)
echo   map [map]      tiles only
echo   palette        256-color ramp + lynn24.spr
echo   test           pytest (e.g. run.bat test --map valley)
echo   --save spec    load a save (path, or N for a local example / ll_saveN.sav)
exit /b 0

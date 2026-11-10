@echo off
cd /d "%~dp0"
call "%~dp0run.bat" gmap %*
exit /b %ERRORLEVEL%

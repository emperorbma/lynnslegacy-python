@echo off
cd /d "%~dp0"
call "%~dp0run.bat" config %*
exit /b %ERRORLEVEL%

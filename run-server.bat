@echo off
REM Keeps the workspace-assistant server running. If it stops for any reason,
REM it waits 5 seconds and starts it again. Output goes to logs\server.log.
cd /d "%~dp0"
if not exist logs mkdir logs

:loop
echo [%date% %time%] Starting server >> logs\server.log
python server.py >> logs\server.log 2>&1
echo [%date% %time%] Server stopped. Restarting in 5 seconds... >> logs\server.log
timeout /t 5 /nobreak >nul
goto loop

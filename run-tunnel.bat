@echo off
REM Keeps the ngrok tunnel running with your fixed domain. If it stops, it waits
REM 5 seconds and starts again. Output goes to logs\tunnel.log.
REM Requires ngrok to be installed and your authtoken already added
REM (ngrok config add-authtoken <token>). The token is NOT stored in this file.
cd /d "%~dp0"
if not exist logs mkdir logs

set NGROK_DOMAIN=panhandle-spotless-handpick.ngrok-free.dev

:loop
echo [%date% %time%] Starting tunnel on %NGROK_DOMAIN% >> logs\tunnel.log
ngrok http --domain=%NGROK_DOMAIN% 8000 >> logs\tunnel.log 2>&1
echo [%date% %time%] Tunnel stopped. Restarting in 5 seconds... >> logs\tunnel.log
timeout /t 5 /nobreak >nul
goto loop

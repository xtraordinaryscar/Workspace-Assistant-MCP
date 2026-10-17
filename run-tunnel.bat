@echo off
REM Keeps the ngrok tunnel running with your fixed domain. If it stops, it waits
REM 5 seconds and starts again. Output goes to logs\tunnel.log.
REM Requires ngrok to be installed and your authtoken already added
REM (ngrok config add-authtoken <token>). The token is NOT stored in this file.
cd /d "%~dp0"
if not exist logs mkdir logs

REM The domain is read from ngrok-domain.txt (not tracked by git). Create that file
REM with your domain on one line, for example: your-name.ngrok-free.dev
if not exist ngrok-domain.txt (
  echo ngrok-domain.txt is missing. Create it with your ngrok domain on one line.
  pause
  exit /b 1
)
set /p NGROK_DOMAIN=<ngrok-domain.txt

:loop
echo [%date% %time%] Starting tunnel on %NGROK_DOMAIN% >> logs\tunnel.log
ngrok http --domain=%NGROK_DOMAIN% 8000 >> logs\tunnel.log 2>&1
echo [%date% %time%] Tunnel stopped. Restarting in 5 seconds... >> logs\tunnel.log
timeout /t 5 /nobreak >nul
goto loop

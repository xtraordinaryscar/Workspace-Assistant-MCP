@echo off
REM Starts both watchdogs in their own minimized windows.
REM Double-click this file, or let Task Scheduler run it at login.
REM Do not run it twice: a second copy of the server would fail with "port in use".
cd /d "%~dp0"

start "workspace-assistant server" /min cmd /c run-server.bat
timeout /t 3 /nobreak >nul
start "ngrok tunnel" /min cmd /c run-tunnel.bat

echo Both services started in minimized windows.
echo Run check-status.bat in a few seconds to confirm they are up.
timeout /t 5 >nul

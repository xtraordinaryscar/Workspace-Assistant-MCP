@echo off
REM Checks whether the local server and the public ngrok address respond.
REM A status code (for example 406) means the server answered. "000" means no answer.
REM 406 is normal here: plain curl does not send the Accept header that MCP requires.
echo Checking local server...
curl -s -o nul -w "Local server:    HTTP %%{http_code}\n" http://127.0.0.1:8000/mcp
echo Checking public address...
curl -s -o nul -w "Public address:  HTTP %%{http_code}\n" https://panhandle-spotless-handpick.ngrok-free.dev/mcp
echo.
echo Expected: both show 406. 000 or 502/503 means that part is down.
pause

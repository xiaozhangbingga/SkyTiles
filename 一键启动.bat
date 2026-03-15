@echo off
setlocal

cd /d "%~dp0"

start "jinjiehaomap-dev" cmd /k "cd /d \"%~dp0\" && npm run dev"

timeout /t 3 /nobreak >nul
start "" "http://localhost:5173"

endlocal

@echo off
setlocal

cd /d "%~dp0"

python3 scripts/build_image_index.py
pause
endlocal

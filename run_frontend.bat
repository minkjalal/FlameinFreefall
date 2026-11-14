@echo off
echo Starting Flame in Freefall Modern Web Application on http://localhost:8000 ...
cd /d "%~dp0"
python -m uvicorn server:app --host 0.0.0.0 --port 8000
pause

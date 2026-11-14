@echo off
echo Starting Flame in Freefall Web Dashboard on localhost:8501...
cd /d "%~dp0"
python -m streamlit run web_app.py --server.port 8501
pause

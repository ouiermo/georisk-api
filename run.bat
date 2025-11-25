@echo off
echo Starting Georisk API...
python -m uvicorn app.main:app --reload --port 8000
pause

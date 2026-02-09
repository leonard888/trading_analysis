@echo off
set PORT=8000
set PYTHONPATH=%PYTHONPATH%;%CD%\backend
python backend\main.py
pause

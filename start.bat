@echo off
echo ========================================
echo  Trading Forecast Terminal - Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Installing Python dependencies...
cd backend
pip install -r requirements.txt -q

echo.
echo [2/4] Starting backend server...
start "Trading API Server" cmd /k "python main.py"

echo.
echo [3/4] Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Opening frontend...
cd ..\frontend
start index.html

echo.
echo ========================================
echo  Application Started!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Frontend: Open frontend\index.html in browser
echo.
echo Press any key to close this window...
pause >nul

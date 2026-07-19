@echo off
title MALAIKA v2 - EUG AI Health Assistant
cd /d "%~dp0"
echo.
echo ================================================
echo   MALAIKA v2 - Starting up...
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from python.org first.
    pause
    exit /b 1
)

REM Install dependencies if needed (one-time)
echo Checking dependencies...
python -c "import fastapi, uvicorn, serial, scipy, numpy, pandas, joblib, sklearn" 2>nul
if errorlevel 1 (
    echo Installing required packages (~30 sec)...
    pip install fastapi uvicorn pyserial scipy numpy pandas joblib scikit-learn --quiet
)

echo.
echo ================================================
echo   Open in browser: http://localhost:8000
echo   Press CTRL+C to stop the server
echo ================================================
echo.

python api.py
pause

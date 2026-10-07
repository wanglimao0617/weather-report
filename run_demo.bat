@echo off
setlocal
cd /d "%~dp0"

echo Installing required packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Failed to install dependencies. Please make sure Python is installed.
    pause
    exit /b 1
)

echo.
echo Starting weather dashboard at http://127.0.0.1:5020
start "" /b python weather.py
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5020

echo Close this window to stop the demo.
pause

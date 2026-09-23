@echo off
title BloodLink AI - Intelligent Blood Emergency Response System
cd /d "%~dp0"
if not exist "main.py" (
 echo ERROR: main.py not found.
 pause
 exit /b 1
)
where python >nul 2>&1
if errorlevel 1 (
 echo Python is not installed. Install Python 3.10+ first.
 pause
 exit /b 1
)
if not exist "venv\Scripts\python.exe" (
 echo Creating the application environment...
 python -m venv venv
 if errorlevel 1 (
  echo Could not create the Python environment.
  pause
  exit /b 1
 )
)
echo Installing required packages...
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
 echo Package installation failed.
 pause
 exit /b 1
)
echo Starting the application...
start "BloodLink AI Server" cmd /k ""%~dp0venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000"
timeout /t 6 /nobreak >nul
start "" "http://127.0.0.1:8000"

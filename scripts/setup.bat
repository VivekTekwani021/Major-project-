@echo off
REM ============================================================
REM BharatRoad Twin - Windows Setup Script
REM Run this once to set up the development environment.
REM ============================================================

echo.
echo ========================================
echo  BharatRoad Twin - Setup
echo ========================================
echo.

REM Find Python
set PYTHON_CMD=
where python >nul 2>&1 && set PYTHON_CMD=python
if "%PYTHON_CMD%"=="" (
    where py >nul 2>&1 && set PYTHON_CMD=py
)
if "%PYTHON_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
    )
)
if "%PYTHON_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    )
)
if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python not found. Please install Python 3.11+ from https://python.org
    exit /b 1
)

echo [INFO] Using Python: %PYTHON_CMD%
%PYTHON_CMD% --version

REM Create virtual environment
echo.
echo [1/4] Creating Python virtual environment...
if not exist "venv" (
    %PYTHON_CMD% -m venv venv
)
call venv\Scripts\activate.bat

REM Install backend dependencies
echo.
echo [2/4] Installing backend Python dependencies...
pip install -r backend\requirements.txt

REM Copy .env if not exists
echo.
echo [3/4] Setting up environment file...
if not exist ".env" (
    copy .env.example .env
    echo [INFO] Created .env from .env.example - please review and adjust settings.
) else (
    echo [INFO] .env already exists, skipping.
)

REM Check for Node.js
echo.
echo [4/4] Checking Node.js...
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Node.js not found. Install from https://nodejs.org for the frontend.
) else (
    echo [INFO] Node.js found:
    node --version
    echo [INFO] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To activate the virtual environment:
echo   venv\Scripts\activate
echo.
echo To run the backend:
echo   venv\Scripts\activate
echo   cd backend
echo   uvicorn app.main:app --reload
echo.
echo To run the frontend:
echo   cd frontend
echo   npm run dev
echo.
echo Optional: Install SUMO from https://sumo.dlr.de/docs/Downloads.php
echo   Set SUMO_HOME environment variable after install.
echo.

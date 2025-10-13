@echo off
echo ====================================
echo Payment Request Management System
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Install dependencies
echo Installing/updating dependencies...
pip install -r requirements.txt
echo.

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo WARNING: Please edit .env file and configure your database settings!
    echo.
    pause
)

REM Create uploads directory if it doesn't exist
if not exist "uploads\receipts" (
    echo Creating uploads directory...
    mkdir uploads\receipts
    echo.
)

REM Ask if user wants to initialize database
set /p INIT_DB="Do you want to initialize the database? (yes/no): "
if /i "%INIT_DB%"=="yes" (
    echo.
    echo Initializing database...
    python init_db.py
    echo.
)

REM Start the application
echo Starting Flask application...
echo.
echo Application will be available at: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause


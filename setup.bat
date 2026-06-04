@echo off
echo ========================================
echo AI Email Assistant - Setup
echo ========================================
echo.

echo Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found! Please install Python 3.8+
    pause
    exit /b
)

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Get OpenRouter API key from https://openrouter.ai/keys
echo 2. Create .env file with: OPENROUTER_API_KEY=your-key
echo 3. Get credentials.json from Google Cloud Console
echo 4. Run: python email_assistant_openrouter.py
echo.
pause
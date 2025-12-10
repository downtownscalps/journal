@echo off
SETLOCAL

REM Change to script directory
cd /d "%~dp0"

REM Create venv if it doesn't exist
IF NOT EXIST venv (
  echo Creating virtual environment...
  python -m venv venv
)

REM Activate venv
call venv\Scripts\activate

REM Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

REM Run app
python app.py

ENDLOCAL

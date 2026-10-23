@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo Digital Image Forensics - Project Setup
echo ==============================================

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        python -m venv .venv
    )
)

echo Installing required Python packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo Setup completed.
echo Run the project with run.bat
pause

@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Digital Image Forensics Analysis Tool...
".venv\Scripts\python.exe" -m streamlit run app.py

pause

@echo off
setlocal

cd /d "%~dp0"

echo.
echo ==============================================
echo       PDF KNOWLEDGE BASE SETUP
echo ==============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Python was not found.
    echo Install Python 3.10 or newer and try again.
    pause
    exit /b 1
)

echo Installing Python dependency...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Setup complete.
echo.
echo Next:
echo 1. Edit config.json
echo 2. Run generate_library.py
echo 3. Open index.html
echo 4. Commit and push to GitHub
echo.
pause
endlocal

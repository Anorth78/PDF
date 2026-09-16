@echo off
setlocal

cd /d "%~dp0"

echo.
echo ==============================================
echo       PDF KNOWLEDGE LIBRARY UPDATE
echo ==============================================
echo.

python generate_library.py

if errorlevel 1 (
    echo.
    echo ERROR: Library generation failed.
    pause
    exit /b 1
)

echo.
echo Checking Git status...
git status

echo.
set /p CONFIRM="Commit and push these changes to GitHub? (Y/N): "

if /I not "%CONFIRM%"=="Y" (
    echo.
    echo Update generated but not pushed.
    pause
    exit /b 0
)

git add .

git commit -m "Update PDF knowledge library"

if errorlevel 1 (
    echo.
    echo Git commit failed. There may be no changes to commit.
    pause
    exit /b 1
)

git push

if errorlevel 1 (
    echo.
    echo Git push failed.
    pause
    exit /b 1
)

echo.
echo ==============================================
echo             UPDATE COMPLETE
echo ==============================================
echo.
pause
endlocal

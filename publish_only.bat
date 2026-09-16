@echo off
setlocal

cd /d "%~dp0"

git add .
git commit -m "Update PDF knowledge library"
git push

pause
endlocal

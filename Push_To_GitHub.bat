@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo Usage:
    echo   Push_To_GitHub.bat https://github.com/LeniZevS/LeniZevS.git
    pause
    exit /b 1
)

set "REPO_URL=%~1"
set "COMMIT_MSG=Update LenivayaFigna bootstrap"

git --version >nul 2>&1
if errorlevel 1 (
    echo Git is not installed or not in PATH.
    pause
    exit /b 1
)

if not exist ".git" (
    git init
    if errorlevel 1 goto :err
)

git add .
if errorlevel 1 goto :err

git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo Nothing to commit or commit failed. Continuing...
)

git branch -M main
if errorlevel 1 goto :err

git remote get-url origin >nul 2>&1
if errorlevel 1 (
    git remote add origin "%REPO_URL%"
) else (
    git remote set-url origin "%REPO_URL%"
)
if errorlevel 1 goto :err

git push -u origin main
if errorlevel 1 goto :err

echo Done. Pushed to %REPO_URL%
pause
exit /b 0

:err
echo Failed to push to GitHub.
pause
exit /b 1

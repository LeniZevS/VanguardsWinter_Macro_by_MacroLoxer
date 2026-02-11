@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PY=%~dp0Python\python3.13.11\python.exe"
if not exist "%PY%" set "PY=python"

echo [1/6] Checking Python...
"%PY%" --version
if errorlevel 1 goto :python_error

echo [2/6] Installing build tools (PyInstaller)...
"%PY%" -m pip install --upgrade pip pyinstaller
if errorlevel 1 goto :pip_error

echo [3/6] Cleaning old build folders...
if exist "%~dp0build" rmdir /s /q "%~dp0build"
if exist "%~dp0dist" rmdir /s /q "%~dp0dist"
if exist "%~dp0LenivayaFigna.spec" del /q "%~dp0LenivayaFigna.spec"

echo [4/6] Building EXE...
"%PY%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name LenivayaFigna ^
  --add-data "Main.py;." ^
  --add-data "Position.py;." ^
  --add-data "Winter_Event.py;." ^
  --add-data "LenivayaFigna.py;." ^
  --add-data "webhook.py;." ^
  --add-data "Utility;Utility" ^
  --add-data "Tools;Tools" ^
  --add-data "Settings;Settings" ^
  --add-data "Resources;Resources" ^
  --add-data "tesseract;tesseract" ^
  Main.py
if errorlevel 1 goto :build_error

echo [5/6] Copying embedded Python runtime to dist...
if exist "%~dp0Python" (
  xcopy "%~dp0Python" "%~dp0dist\LenivayaFigna\Python\" /E /I /Y >nul
)

echo [6/6] Done.
echo Build output: dist\LenivayaFigna\LenivayaFigna.exe
echo.
echo To start app: run dist\LenivayaFigna\LenivayaFigna.exe
echo To enable splash: put start image into dist\LenivayaFigna\Resources\start.png
start "" explorer "%~dp0dist\LenivayaFigna"
exit /b 0

:python_error
echo ERROR: Python not found.
echo Put embedded Python in .\Python\python3.13.11\ or install Python.
pause
exit /b 1

:pip_error
echo ERROR: Failed to install build tools.
pause
exit /b 1

:build_error
echo ERROR: Build failed.
pause
exit /b 1

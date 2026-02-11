@echo off
setlocal
cd /d "%~dp0"

set "PYW=%~dp0Python\python3.13.11\pythonw.exe"
set "PYE=%~dp0Python\python3.13.11\python.exe"
set "APP=%~dp0Main.py"

if not exist "%APP%" (
    echo Main.py not found.
    pause
    exit /b 1
)

if exist "%PYW%" (
    start "" "%PYW%" "%APP%"
    exit /b 0
)

if exist "%PYE%" (
    start "" "%PYE%" "%APP%"
    exit /b 0
)

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw "%APP%"
    exit /b 0
)

where python >nul 2>&1
if %errorlevel%==0 (
    start "" python "%APP%"
    exit /b 0
)

echo Python was not found. Put embedded Python in:
echo Python\python3.13.11\
pause
exit /b 1

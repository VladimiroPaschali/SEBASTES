@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo SEBASTES Python environment not found.
    echo Complete the "Installation on Windows" section in the README,
    echo then double-click this file again.
    echo.
    echo Press any key to close this window.
    pause >nul
    exit /b 1
)

start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0application\MainWindow.py" %*
exit /b

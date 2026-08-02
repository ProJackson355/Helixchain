@echo off
REM Double-click to open the Helix Pool setup and monitoring GUI.
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Install Python 3.11+ from https://www.python.org/downloads/
    echo and tick "Add Python to PATH", then run this file again.
    pause
    exit /b 1
)
start "" pythonw "%~dp0install_pool.py" 2>nul
if errorlevel 1 python "%~dp0install_pool.py"

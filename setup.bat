@echo off
REM Double-click to open the Helix Node installer (GUI).
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Install Python 3.11+ from https://www.python.org/downloads/
    echo and tick "Add Python to PATH", then run this again.
    pause
    exit /b 1
)
start "" pythonw "%~dp0install_node.py" 2>nul
if errorlevel 1 python "%~dp0install_node.py"

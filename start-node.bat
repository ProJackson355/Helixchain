@echo off
REM ===========================================================================
REM  Helix Node - one-click setup and launcher (Windows)
REM  Double-click this file. It creates the Python environment, installs
REM  dependencies, starts the node, and optionally opens a Cloudflare tunnel.
REM ===========================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Helix Node setup

echo(
echo   ============================================
echo    Helix Node setup
echo   ============================================
echo(

REM --- 1. Check Python is available ---------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo  [X] Python was not found on your PATH.
    echo      Install Python 3.11 or newer from https://www.python.org/downloads/
    echo      and be sure to tick "Add Python to PATH", then run this again.
    echo(
    pause
    exit /b 1
)

REM --- 2. Create the virtual environment if it does not exist -------------
if not exist ".venv\Scripts\python.exe" (
    echo  [*] Creating virtual environment (.venv) ...
    python -m venv .venv
    if errorlevel 1 (
        echo  [X] Could not create the virtual environment. Is Python 3.11+ installed?
        pause
        exit /b 1
    )
) else (
    echo  [*] Virtual environment already exists.
)

REM --- 3. Install dependencies only if they are missing ------------------
".venv\Scripts\python.exe" -c "import cryptography, fastapi, uvicorn, requests, mnemonic" >nul 2>&1
if errorlevel 1 (
    echo  [*] Installing dependencies (this can take a minute the first time) ...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo  [X] Dependency installation failed. Check the messages above.
        pause
        exit /b 1
    )
) else (
    echo  [*] Required libraries are already installed - skipping.
)

REM --- 4. Start the node in its own window --------------------------------
echo  [*] Starting the Helix node on http://localhost:8000 ...
start "Helix Node" cmd /k "cd /d "%~dp0" && ".venv\Scripts\python.exe" run_node.py"

REM --- 5. Optionally expose the node with a Cloudflare tunnel -------------
echo(
set "EXPOSE="
set /p "EXPOSE=  Expose this node to the internet with a Cloudflare tunnel? (y/N): "
if /i "!EXPOSE!"=="y" (
    where cloudflared >nul 2>&1
    if errorlevel 1 (
        echo  [!] cloudflared is not installed. Download it from
        echo      https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
        echo      then re-run this script. The node is still running locally.
    ) else (
        echo  [*] Opening a Cloudflare quick tunnel. Copy the https://...trycloudflare.com
        echo      URL it prints into your Pages HELIX_NODE_URL, then redeploy.
        start "Helix Tunnel" cmd /k "cloudflared tunnel --url http://localhost:8000"
    )
)

REM --- 6. Open the local wallet UI ---------------------------------------
echo(
echo  [*] Waiting for the node to come up, then opening the wallet ...
timeout /t 4 /nobreak >nul
start "" "http://localhost:8000"

echo(
echo   ============================================
echo    Node is running. The wallet UI is at
echo    http://localhost:8000
echo    Close the "Helix Node" window to stop it.
echo   ============================================
echo(
echo  Tip: an admin API key is optional. To lock down admin routes on a public
echo  node, set HELIX_ADMIN_API_KEY and HELIX_REQUIRE_ADMIN_API_KEY=true before
echo  starting.
echo(
pause
endlocal

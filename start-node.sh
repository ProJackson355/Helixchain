#!/usr/bin/env bash
# Helix Node - one-click setup and launcher (Linux / macOS).
# Usage:  bash start-node.sh          (CLI setup + run)
#         bash start-node.sh --gui    (open the installer GUI)
set -e
cd "$(dirname "$0")"

if [ "$1" = "--gui" ]; then
    command -v python3 >/dev/null 2>&1 || { echo "Install Python 3.11+ first."; exit 1; }
    exec python3 install_node.py
fi

command -v python3 >/dev/null 2>&1 || { echo "Python 3.11+ not found. Install it and re-run."; exit 1; }

if [ ! -x ".venv/bin/python" ]; then
    echo "[*] Creating virtual environment (.venv) ..."
    python3 -m venv .venv
fi

if ./.venv/bin/python -c "import cryptography, fastapi, uvicorn, requests, mnemonic" >/dev/null 2>&1; then
    echo "[*] Required libraries are already installed - skipping."
else
    echo "[*] Installing dependencies ..."
    ./.venv/bin/python -m pip install --upgrade pip >/dev/null
    ./.venv/bin/python -m pip install -r requirements.txt
fi

echo "[*] Starting the Helix node on http://localhost:8000"
echo "    Wallet UI: http://localhost:8000   (Ctrl+C to stop)"
echo "    To expose it, run in another terminal: cloudflared tunnel --url http://localhost:8000"
exec ./.venv/bin/python run_node.py

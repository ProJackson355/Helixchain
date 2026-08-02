#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null 2>&1 || { echo "Install Python 3.11+ first."; exit 1; }
exec python3 install_pool.py

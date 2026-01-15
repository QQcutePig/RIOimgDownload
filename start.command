#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[RIOimgDownload] Creating venv..."
  python3 -m venv .venv
fi

source ".venv/bin/activate"

echo "[RIOimgDownload] Installing/updating dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

echo "[RIOimgDownload] Starting backend..."
python backend/main.py

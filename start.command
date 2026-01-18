#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "========================================"
echo "  RIOimgDownload 啟動中..."
echo "========================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[錯誤] 找不到 Python3！請先安裝 Python 3.8+"
    echo "建議使用 Homebrew: brew install python@3.11"
    exit 1
fi

# 建立虛擬環境
if [ ! -d ".venv" ]; then
    echo "[1/3] 建立虛擬環境..."
    python3 -m venv .venv
fi

source ".venv/bin/activate"

# 安裝依賴
echo "[2/3] 安裝/更新套件..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

# 跳過 Playwright 瀏覽器下載
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

echo "[3/3] 準備啟動..."
echo "  ⚠ macOS 不支援 gallery-dl/yt-dlp 整合"
echo ""

echo "========================================"
echo "  啟動 Backend Server..."
echo "  瀏覽器將自動開啟 http://127.0.0.1:8787"
echo "========================================"
echo ""

python backend/main.py

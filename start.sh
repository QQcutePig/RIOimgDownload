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

# 檢查工具
echo "[3/3] 檢查下載工具..."
if [ -f "gallery-dl" ]; then
    chmod +x gallery-dl
    echo "  ✓ gallery-dl 已就緒"
else
    echo "  ⚠ gallery-dl 未找到 (將自動下載)"
fi

if [ -f "yt-dlp" ]; then
    chmod +x yt-dlp
    echo "  ✓ yt-dlp 已就緒"
else
    echo "  ⚠ yt-dlp 未找到 (可選)"
fi

echo ""
echo "========================================"
echo "  啟動 Backend Server..."
echo "  瀏覽器將自動開啟 http://127.0.0.1:8787"
echo "========================================"
echo ""

python backend/main.py

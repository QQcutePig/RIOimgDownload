@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

echo ========================================
echo   RIOimgDownload 啟動中...
echo ========================================
echo.

REM 檢查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python！請先安裝 Python 3.8+
    pause
    exit /b 1
)

REM 建立虛擬環境
if not exist ".venv" (
    echo [1/3] 建立虛擬環境...
    python -m venv .venv
    if errorlevel 1 (
        echo [錯誤] 無法建立虛擬環境
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

REM 安裝依賴
echo [2/3] 安裝/更新套件...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

REM 跳過 Playwright 瀏覽器下載（使用系統 Chrome/Edge）
set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

REM 檢查工具
echo [3/3] 檢查下載工具...
if exist "gallery-dl.exe" (
    echo   ✓ gallery-dl.exe 已就緒
) else (
    echo   ⚠ gallery-dl.exe 未找到 ^(可選^)
    echo     下載: https://github.com/mikf/gallery-dl/releases
)

if exist "yt-dlp.exe" (
    echo   ✓ yt-dlp.exe 已就緒
) else (
    echo   ⚠ yt-dlp.exe 未找到 ^(可選^)
    echo     下載: https://github.com/yt-dlp/yt-dlp/releases
)

echo.
echo ========================================
echo   啟動 Backend Server...
echo   瀏覽器將自動開啟 http://127.0.0.1:8787
echo ========================================
echo.

python backend\main.py

REM 如果程式異常退出，暫停顯示錯誤
if errorlevel 1 pause

endlocal

@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

if not exist ".venv" (
  echo [RIOimgDownload] Creating venv...
  py -3 -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo [RIOimgDownload] Installing/updating dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Skip downloading Playwright browsers (use system Chrome/Edge)
set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

echo [RIOimgDownload] Starting backend...
python backend\main.py

endlocal

# 🎨 RIOimgDownload

<img width="3824" height="1790" alt="image" src="[https://github.com/user-attachments/assets/eab2e38f-2dfe-4bb4-97b7-501dc4e20995](https://raw.githubusercontent.com/QQcutePig/RIOimgDownload/refs/heads/main/1.jpg)" />


一個功能強大的網頁媒體掃描與下載工具，支援圖片/影片批次提取、智能篩選、多種下載引擎，並提供友善的視覺化操作界面。

🚀 快速開始

Windows 前置需求: 
安裝 Python 3.8+ 
執行 run.bat

macOS 前置需求:
安裝 xcode-select --install 
執行 start.command

Linux 啟動 前置需求:
sudo apt install python3
Ubuntu/Debian sudo dnf install python3
Fedora/RHEL sudo pacman -S python
Arch
執行 start.sh 啟動

## ✨ 主要功能

### 🔍 智能掃描
- **雙模式掃描**
  - **標準模式**: 快速掃描頁面可見的圖片與影片連結
  - **Ultra 模式**: 深度掃描，包含 DOM、網路請求、JavaScript 變數、懶載入圖片等隱藏資源
- **網站預設優化**: 自動辨識 Instagram、X (Twitter)、Facebook 等平台並套用最佳掃描參數
- **智能滾動**: 自動向下滾動頁面載入更多內容，並智能判斷何時停止
- **即時預覽**: 掃描過程中即時顯示找到的媒體縮圖 (800px 高品質)

### 🎯 進階篩選
- **格式篩選**: JPG、PNG、GIF、WebP 多格式快速切換
- **尺寸篩選**: 設定最小寬度/高度，過濾小圖示與廣告
- **類型篩選**: 分別顯示圖片 (IMAGE) 或影片 (VIDEO)
- **黑名單過濾**: 自動排除 avatar、logo、icon、emoji、banner 等無用資源

### ✅ 靈活選取
- **批次操作**: 全選、取消選取、反向選取
- **多選模式**:
  - 單擊: 切換選取狀態
  - Ctrl/Cmd + 點擊: 多選
  - Shift + 點擊: 範圍選取
- **雙擊預覽**: 雙擊圖片開啟 Lightbox 全螢幕檢視，支援鍵盤左右鍵切換

### 💾 多引擎下載
1. **內建下載器** (built-in)
   - 純 Python 實作，無需額外工具
   - 支援圖片與影片直接下載
   - 多線程並發下載 (20 workers)

2. **gallery-dl**
   - 專業圖庫下載工具
   - 支援 Instagram、Pixiv、Twitter 等 80+ 平台
   - 自動取得原始畫質與完整相簿

3. **yt-dlp**
   - 通用影片下載器
   - 支援 YouTube、Twitter、Facebook 等 1000+ 網站
   - 自動選擇最佳畫質

### 🎨 使用者體驗
- **深色主題**: 護眼的深色介面設計
- **響應式佈局**: 左側縮圖網格，右側控制面板
- **縮圖大小調整**: S/M/L/XL 四種尺寸切換 (120px-240px)
- **即時狀態顯示**: 進度條、掃描輪數、找到的媒體數量
- **工具版本檢測**: 自動檢查 gallery-dl 和 yt-dlp 是否安裝及版本更新

## 📦 安裝與執行

### 系統需求
- Python 3.8+
- Chromium 或 Microsoft Edge 瀏覽器
- Windows、Linux 或 macOS

### 安裝步驟

1. **克隆專案**
```bash
git clone https://github.com/your-username/RIOimgDownload.git
cd RIOimgDownload
```

2. **建立虛擬環境**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

3. **安裝依賴**
```bash
pip install -r requirements.txt
playwright install chromium  # 或 playwright install msedge (Windows)
```

4. **下載外部工具 (可選)**
   - [gallery-dl](https://github.com/mikf/gallery-dl/releases) → 下載後放到專案根目錄
   - [yt-dlp](https://github.com/yt-dlp/yt-dlp/releases) → 下載後放到專案根目錄
   - Windows: 下載 `.exe` 檔案
   - Linux: 下載二進位檔案並加上執行權限 `chmod +x gallery-dl yt-dlp`

### 啟動應用

**Windows:**
```bash
run.bat
```
或直接雙擊 `run.bat`

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```
或
```bash
bash start.sh
```

應用會自動在瀏覽器開啟 `http://localhost:7799`

## 📖 使用教學

### 基本流程

1. **輸入網址**
   - 在「掃描」區塊的輸入框貼上目標網頁網址
   - 例如: `https://www.instagram.com/username/`

2. **選擇掃描模式**
   - ☑️ **勾選 Ultra**: 深度掃描 (建議用於 Instagram、Twitter 等動態載入網站)
   - ☐ **不勾選**: 標準掃描 (適合一般網頁)

3. **開始掃描**
   - 點擊 **Scan** 按鈕
   - 等待自動滾動與掃描完成 (可在狀態欄看到進度)
   - 點擊 **Stop** 可隨時中止

4. **篩選媒體**
   - 點擊格式按鈕 (JPG/PNG/GIF/WebP) 篩選特定格式
   - 輸入最小寬度 (W) 和高度 (H)，點「套用篩選」
   - 點「重設篩選」清除所有篩選條件

5. **選取項目**
   - 點擊縮圖選取/取消
   - 使用「全選」、「取消選取」、「反向選取」快速操作
   - 已選數量會顯示在頂部

6. **下載**
   - 從下拉選單選擇下載引擎 (內建/gallery-dl/yt-dlp)
   - 點擊 **下載選取項目**
   - 檔案會儲存到顯示的下載路徑 (預設: ~/Downloads)
   - 可點「📁 變更路徑」修改下載位置

7. **清除**
   - 點擊 **Clear** 清空當前掃描結果與網址

### 進階技巧

#### Ultra 模式的使用時機
- ✅ 推薦使用:
  - Instagram、Twitter、Facebook 等單頁應用
  - 圖片透過 JavaScript 動態載入的網站
  - 需要捲動才能看到更多內容的頁面

- ⚠️ 不一定需要:
  - 傳統靜態網頁
  - 圖片已完整顯示在原始碼中的頁面

#### 縮圖檢視技巧
- **雙擊圖片**: 開啟 Lightbox 全螢幕預覽
- **Lightbox 操作**:
  - `←` / `→` 鍵: 切換上一張/下一張
  - `ESC` 鍵: 關閉 Lightbox
  - 點擊黑色背景: 關閉 Lightbox

#### 下載引擎選擇建議
- **內建下載器**: 適合一般圖片/影片直連
- **gallery-dl**: 專業圖庫網站 (Instagram/Pixiv/Twitter 媒體推文)
- **yt-dlp**: 影片串流網站 (YouTube/Twitter 影片/Facebook 影片)

#### 工具更新 (Linux)
- 應用會自動檢測 gallery-dl 和 yt-dlp 的版本
- 如果有新版本，點擊「🔄 更新」按鈕自動下載更新
- Windows 用戶需手動下載 `.exe` 檔案更新

## 🗂️ 專案結構

```
RIOimgDownload/
│
├── backend/
│   └── main.py          # FastAPI 後端主程式
│
├── web/
│   ├── index.html       # 前端 HTML
│   ├── app.js           # 前端 JavaScript
│   └── styles.css       # 樣式表
│
├── .venv/               # Python 虛擬環境 (自動建立)
│
├── gallery-dl.exe       # gallery-dl 工具 (需手動下載)
├── yt-dlp.exe           # yt-dlp 工具 (需手動下載)
│
├── requirements.txt     # Python 依賴清單
├── run.bat              # Windows 啟動腳本
├── start.sh             # Linux/macOS 啟動腳本
└── start.command        # macOS 雙擊啟動腳本
```

### 資料儲存位置

應用會在系統的用戶資料目錄建立資料夾:

- **Windows**: `C:\Users\YourName\AppData\Local\RIOimgDownload\`
- **Linux**: `~/.local/share/RIOimgDownload/`
- **macOS**: `~/Library/Application Support/RIOimgDownload/`

資料夾內容:
- `jobs/`: 掃描任務的縮圖快取
- `browser_profile/`: 瀏覽器設定檔 (用於記住登入狀態)
- `config.json`: 應用設定 (下載路徑等)

## ⚙️ 技術架構

### 後端 (backend/main.py)
- **FastAPI**: Web 框架
- **Playwright**: 無頭瀏覽器自動化 (頁面掃描與滾動)
- **Pillow (PIL)**: 圖片處理與縮圖生成
- **Requests**: HTTP 請求與檔案下載
- **ThreadPoolExecutor**: 多線程並發處理

### 前端 (web/)
- **Vanilla JavaScript**: 無框架，純原生 JS
- **Fetch API**: 與後端 API 通訊
- **CSS Grid**: 響應式佈局
- **LocalStorage**: 儲存使用者偏好設定

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/scan` | POST | 開始掃描網頁 |
| `/api/stop/{job_id}` | POST | 停止掃描任務 |
| `/api/status/{job_id}` | GET | 查詢任務狀態 |
| `/api/items/{job_id}` | GET | 取得掃描結果 |
| `/api/download` | POST | 下載選取的媒體 |
| `/api/gdl/direct` | POST | 使用 gallery-dl 下載 |
| `/api/ytdlp/direct` | POST | 使用 yt-dlp 下載 |
| `/api/tools/status` | GET | 查詢工具版本與狀態 |
| `/api/tools/update/{tool}` | POST | 更新工具 (Linux) |
| `/api/appinfo` | GET | 取得應用設定 |
| `/api/setdestdir` | POST | 設定下載路徑 |
| `/thumb/{job_id}/{item_id}.jpg` | GET | 取得縮圖 |

## 🔧 設定調整

你可以在 `backend/main.py` 頂部修改以下參數:

```python
THUMB_SIZE = 800                    # 縮圖解析度 (px)
VERIFY_WORKERS = 20                 # 驗證連結的並發數
THUMB_WORKERS = 12                  # 生成縮圖的並發數
SCROLL_WAIT_MS_DEFAULT = 1500       # 滾動後等待時間 (ms)
MAX_SCROLL_ROUNDS_DEFAULT = 50      # 最大滾動次數
STABLE_ROUNDS_TO_STOP_DEFAULT = 3   # 連續無變化幾輪後停止
```

## 🐛 常見問題

### Q1: 為什麼掃描不到圖片？
- **A**: 嘗試勾選「Ultra」模式，並確保網頁已完全載入
- 某些網站使用 Cloudflare 或反爬蟲機制，可能需要手動登入後再掃描

### Q2: gallery-dl 或 yt-dlp 顯示「未安裝」？
- **A**: 請從官方 GitHub Releases 下載對應系統的執行檔:
  - [gallery-dl releases](https://github.com/mikf/gallery-dl/releases)
  - [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases)
  - 將檔案放到專案根目錄 (與 `run.bat` 同層)
  - Linux 需要: `chmod +x gallery-dl yt-dlp`

### Q3: 掃描 Instagram 時卡住？
- **A**: Instagram 需要登入才能查看完整內容:
  1. 關閉應用
  2. 刪除 `RIOimgDownload/browser_profile/` 資料夾
  3. 重啟應用，會彈出瀏覽器視窗
  4. 手動登入 Instagram
  5. 關閉瀏覽器視窗，重新開始掃描

### Q4: 下載失敗怎麼辦？
- **A**: 
  - 檢查網址是否有效
  - 確認下載路徑有寫入權限
  - 嘗試切換不同的下載引擎
  - 查看終端機的錯誤訊息

### Q5: 如何清除快取？
- **A**: 刪除以下資料夾:
  - Windows: `C:\Users\YourName\AppData\Local\RIOimgDownload\jobs\`
  - Linux/macOS: `~/.local/share/RIOimgDownload/jobs/`

## 📝 TODO / 未來計劃

- [ ] 支援批次網址輸入
- [ ] 增加下載佇列管理
- [ ] 支援自訂黑名單關鍵字
- [ ] 匯出掃描結果為 JSON
- [ ] 支援拖曳上傳本機 HTML 檔案掃描
- [ ] Docker 容器化部署

## 📄 授權條款

MIT License - 請自由使用、修改與分享

## 🙏 致謝

- [Playwright](https://playwright.dev/) - 強大的瀏覽器自動化工具
- [gallery-dl](https://github.com/mikf/gallery-dl) - 專業圖庫下載器
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 通用影片下載器
- [FastAPI](https://fastapi.tiangolo.com/) - 現代化 Python Web 框架

## 🌟 Star History

如果這個專案對你有幫助，請給個 ⭐ Star 支持一下！

---

**Made with ❤️ for media archiving enthusiasts**


<img width="3824" height="1790" alt="image" src="https://raw.githubusercontent.com/QQcutePig/RIOimgDownload/refs/heads/main/%E8%9E%A2%E5%B9%95%E6%93%B7%E5%8F%96%E7%95%AB%E9%9D%A2%202026-01-15%20201816.jpg" />
# RIOimgDownload WebUI 版本

一個功能強大嘅本地圖片/影片掃描 & 下載工具，支持 Instagram、Facebook、X（Twitter）、TikTok 等主流社交平台及網站。

## 功能特點

- 🌐 **支持多平台**：Instagram、Facebook、X、TikTok、小紅書、Pinterest 等
- 🔐 **本地登入**：支持自動登入，突破平台限制
- 🎬 **多媒體支持**：同時掃描圖片及影片（MP4/WebM）
- ⚡ **高速掃描**：多線程並行下載，支持超大網站掃描
- 🎨 **WebUI 界面**：現代化網頁界面，方便操作
- 📊 **篩選功能**：按尺寸、格式、關鍵詞篩選媒體
- 🔗 **兩種下載模式**：Built-in download 或 gallery-dl
- 🛡️ **隱私保護**：全程本地運行，無需上傳數據

---

## 安裝指南

### 前置需求

- **Python 3.9+**
- **Windows / Mac / Linux**
- **Microsoft Edge**（用於登入/掃描，系統需要已安裝）

### 第一步：下載程式

🚀 快速開始
Windows
前置需求:
執行 run.bat

macOS
前置需求:
執行 start.command

Linux 啟動
前置需求:
執行 start.sh 啟動
```

程式會自動打開瀏覽器，進入 `http://localhost:5000`

---

## 使用說明

### 基本操作流程

#### 1️⃣ **登入（適用於有登入牆的平台）**

針對 Instagram、Facebook、X 等需要登入才能看到完整內容的平台：

1. 點擊「**開登入視窗**」按鈕
2. 瀏覽器會開啟 Instagram（預設）
3. 手動登入你的帳號（掃描會記住這個登入狀態）
4. 登入成功後關閉視窗

**更換登入平台**：登入視窗打開後，可以在網址列改成其他網址：
- Instagram: `https://www.instagram.com`
- Facebook: `https://www.facebook.com`
- X (Twitter): `https://x.com`
- TikTok: `https://www.tiktok.com`

登入狀態會保存在本地，所有 cookie 共用同一個 profile，下次掃描自動使用。

---

#### 2️⃣ **掃描網頁**

1. **貼入網址**：將要掃描的網址貼入頂部 URL 欄位
   - 例如：`https://www.instagram.com/username`
   - 或：`https://example.com/gallery`

2. **選擇掃描選項**：
   - ✅ **Ultra**：深度掃描，會使用更多資源但掃得更全（建議勾選）
   - ✅ **Login Mode**：使用已登入的 profile（登入後勾選）
   - ✅ **Debug Browser**：顯示瀏覽器窗口（用於排查問題）
   - ✅ **Images / Videos**：選擇要掃描嘅媒體類型

3. **點擊「Scan」按鈕**開始掃描

4. **等待完成**：
   - 進度條會顯示掃描進度
   - 底部會顯示找到嘅媒體數量

---

#### 3️⃣ **篩選結果**

掃描完成後，你會看到找到嘅所有圖片/影片。可以用下面嘅方式篩選：

**篩選條件**（左下方）：
- **Min W / Min H**：最小寬度/高度（像素），例如 `500 x 500` 只顯示 500px 以上嘅圖片
- **隱藏 ERR/BIG**：隱藏下載失敗 (ERR) 或超大文件 (BIG) 嘅項目
- **Blacklist**：排除包含特定關鍵詞嘅圖片（例如：`avatar,logo,icon` 會排除頭像、logo、圖標）

**預設 Blacklist**：
```
avatar, noavatar, logo, sprite, icon, favicon, emoji, emoticon, blank, spacer, loading, placeholder, banner, tracking, pixel
```

套用篩選後按「**套用篩選**」，點擊「**重設篩選**」恢復全部。

---

#### 4️⃣ **選擇媒體**

支持多種選擇方式：

**單個選擇：**
- 直接**點擊圖片或 checkbox** → 選中/取消

**快速選擇：**
- **「Select all」**：全選（篩選結果內全部）
- **「Deselect all」**：全取消
- **「Invert」**：反選

**多選：**
- **Ctrl + 點擊**：多選單個（按住 Ctrl 一個個點）
- **Shift + 點擊**：範圍選擇
  - 例如：點第 5 張 → Shift + 點第 10 張 → 第 5-10 張全選
  - 如果範圍內已全選 → Shift + 點擊會**全部反選**

---

#### 5️⃣ **下載媒體**

1. **選擇下載路徑**：
   - 在右邊「下載」panel 填入下載路徑
   - 例如：`~/Downloads` 或 `D:\Download`

2. **選擇下載引擎**：
   - **Built-in download**：程式內置下載（推薦，無需額外工具）
   - **gallery-dl**：需要提前安裝 gallery-dl 工具

3. **點擊「Download selected」**開始下載

4. **查看結果**：
   - 下載完成會彈出提示（成功數 / 失敗數）
   - 文件會自動按網站 + 日期分類存放

---

### 高級用法

#### 📌 **G-DL Direct（直接下載模式）**

如果你已經安裝了 gallery-dl，可以用「G-DL Direct」模式：
- 直接用 gallery-dl 掃網址並下載（**不經過圖片預覽**）
- 速度更快，適合已知網站結構嘅情況
- 點擊「**G-DL Direct**」按鈕即可

#### 📌 **清除登入資料**

點擊「**清除登入資料**」會清除已保存嘅 cookie 及登入狀態，下次需要重新登入。

#### 📌 **Debug 模式**

勾選「Debug Browser」會顯示瀏覽器窗口，用於：
- 觀察掃描過程
- 排查登入問題
- 驗證是否成功登入

---

## 文件結構

```
RIOimgDownload/
├── app.py                 # 後端 Flask 應用
├── requirements.txt       # Python 依賴
├── run.bat               # Windows 啟動腳本
├── web/
│   ├── index.html        # 前端頁面
│   ├── app.js            # 前端邏輯
│   ├── styles.css        # 樣式表
│   └── favicon.ico       # 圖標
├── README.md             # 本文件
└── config.json           # 配置文件（自動生成）
```

---

## 常見問題

### ❓ **掃描找不到圖片**

**原因 & 解決方案**：

1. **試試勾選「Ultra」**
   - 深度掃描可能會掃到更多圖片
   - 需要多些時間但更全面

2. **勾選「Login Mode」+「開登入視窗」**
   - 有些平台需要登入才能看完整內容
   - Instagram 特別推薦登入

3. **增加 Scroll 次數**
   - 某些無限滾動網站需要更多時間加載
   - 等待掃描完成（狀態會顯示穩定輪數）

4. **確認網站是否支持**
   - 某些網站有反爬蟲機制
   - 可試試用 Debug 模式觀察

### ❓ **登入視窗說「不安全」**

**已修復！** 最新版本已加入反偵測機制，應該不會再出現此提示。

如果仍然出現：
1. 手動允許瀏覽器進行
2. 聯絡開發者反映問題

### ❓ **下載失敗（ERR）**

**原因**：
- 圖片已被刪除
- 防盜鏈（403 禁止訪問）
- 伺服器返回錯誤

**解決方案**：
- 勾選「隱藏 ERR/BIG」過濾掉失敗項目
- 重新掃描試試

### ❓ **某個格式 (BIG) 的文件**

**原因**：檔案超過 25MB，為節省記憶體不生成縮圖

**解決方案**：
- 直接下載，下載時會取得完整文件
- 或勾選「隱藏 ERR/BIG」隱藏

### ❓ **Shift 多選不工作**

**已修復！** 最新版本支持 Shift 範圍選擇：
- 點第 5 張 → Shift + 點第 10 張 → 5-10 全選
- 如果已全選 → Shift + 點擊會反選

### ❓ **程式占用記憶體太高**

**優化建議**：
- 不要同時掃太多大型網站
- 定期按「Clear」清空結果
- 關閉「Debug Browser」以節省資源

---

## 配置文件

程式會自動生成 `config.json`，存放以下設置：

```json
{
  "isdark": true,                    # 暗色模式
  "destdir": "~/Downloads",          # 下載路徑
  "showjpg": true,                   # 掃描 JPG
  "showpng": true,                   # 掃描 PNG
  "showgif": true,                   # 掃描 GIF
  "showwebp": true,                  # 掃描 WEBP
  "blacklist": "avatar,logo,...",    # 黑名單
  "dlengine": "builtin",             # 下載引擎
  "ultramode": false,                # Ultra 模式
  "debugbrowser": false              # Debug 模式
}
```

你可以直接編輯此文件修改預設值。

---

## 技術細節

### 後端 (Python Flask)

- **Playwright**：自動化瀏覽器，支持登入及 JavaScript 渲染
- **requests**：HTTP 客戶端，用於直接下載
- **Pillow**：圖片處理，生成縮圖
- **gallery-dl**：可選，用於高級下載策略

### 前端 (JavaScript)

- 純 JavaScript（無框架依賴）
- CSS Grid 響應式設計
- 實時掃描進度更新

### 掃描邏輯

1. **頁面加載** → 等待 DOM 完成
2. **滾動頁面** → 觸發無限滾動加載
3. **提取 URL** → 從 HTML、CSS、Network 三個渠道提取媒體 URL
4. **驗證媒體** → 檢查是否真的是圖片/影片
5. **生成縮圖** → 用於預覽
6. **下載** → 支持多線程並行下載

---

## 安全性

- ✅ **全程本地**：所有操作在本地進行，無需上傳
- ✅ **自動登入**：登入信息存放本地，不上傳任何服務器
- ✅ **隱私友善**：支持自定義黑名單過濾敏感內容
- ✅ **開源代碼**：代碼完全透明，可審計

---

## 貢獻

歡迎 Issue 和 Pull Request！

### 常見貢獻方向

- 新網站支持
- Bug 修復
- 功能改進
- 文檔完善

---

## 更新日誌

### v2.0 (2026-01-15)

- ✨ WebUI 界面全新改寫
- ✨ 支持 Shift 多選
- 🐛 修復登入視窗被封鎖問題
- 🐛 修復篩選條件 UI 顯示
- ⚡ 優化掃描速度，增加 Network 捕捉

### v1.0

- 初始版本（Tkinter GUI）



## 開源許可

MIT License



## 致謝

感謝以下開源項目：
- [Playwright](https://playwright.dev/)
- [Flask](https://flask.palletsprojects.com/)
- [gallery-dl](https://github.com/mikf/gallery-dl)
- [Pillow](https://python-pillow.org/)

---

## 免責聲明

本工具僅供個人學習研究使用。使用者應遵守當地法律及相關平台服務條款，不得用於非法目的或侵犯他人隱私。開發者不承擔因使用本工具導致的任何法律責任。

---

**最後更新**：2026-01-15  
**版本**：v1.0  
**作者**：Your Name

let state = {
    jobId: null,
    items: [],
    selected: new Set(),
    theme: "dark",
    filterMinW: 0,
    filterMinH: 0,
    lastClickedIndex: null,
    gdlAvailable: false,
    gdlInfo: "",
    ytdlpAvailable: false,
    ytdlpInfo: "",
    filterFormats: new Set(),
    platformType: "unknown",
};

const $ = (id) => document.getElementById(id);

function setStatus(text) {
    $("statusText").textContent = text;
}

function setProgress(pct) {
    $("progressBar").style.width = `${pct}%`;
    $("progressPercent").textContent = `${Math.round(pct)}%`;
}

function toInt(v, def=0) {
    const n = parseInt(v, 10);
    return Number.isFinite(n) ? n : def;
}

async function api(path, method="GET", body=null) {
    const opts = { method, headers: {} };
    if (body) {
        opts.headers["Content-Type"] = "application/json";
        opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    if (!res.ok) {
        const t = await res.text();
        throw new Error(t || res.statusText);
    }
    return await res.json();
}

// 載入工具狀態
async function loadToolsStatus() {
    try {
        const data = await api("/api/tools/status");
        state.platformType = data.platform;
        state.gdlAvailable = data.gallery_dl.available;
        state.ytdlpAvailable = data.yt_dlp.available;
        
       let html = '<div style="font-size:11px; color:var(--muted); margin-bottom:8px;">🔧 工具狀態</div>';
        
        // gallery-dl
html += '<div class="tool-item">';
html += '<span class="tool-name">🟢 gallery-dl</span>';
if (data.gallery_dl.available) {
    html += `<span class="tool-version">${data.gallery_dl.version}</span>`;
            if (data.gallery_dl.has_update) {
                if (data.platform === "windows") {
                    html += `<span class="tool-update" onclick="alert('有新版本 ${data.gallery_dl.latest_version} 可用\\n請至 https://github.com/mikf/gallery-dl/releases 下載')">📥 更新可用</span>`;
                } else if (data.platform === "linux") {
                    html += `<span class="tool-update" onclick="updateTool('gallery-dl')">📥 點擊更新</span>`;
                }
            }
} else {
    html += `<span class="tool-name">🔴 gallery-dl</span>`;
    html += `<span class="tool-error">${data.gallery_dl.error}</span>`;
}
        html += '</div>';
        
        // yt-dlp
html += '<div class="tool-item">';
html += '<span class="tool-name">🟢 yt-dlp</span>';
if (data.yt_dlp.available) {
    html += `<span class="tool-version">${data.yt_dlp.version}</span>`;
            if (data.yt_dlp.has_update) {
                if (data.platform === "windows") {
                    html += `<span class="tool-update" onclick="alert('有新版本 ${data.yt_dlp.latest_version} 可用\\n請至 https://github.com/yt-dlp/yt-dlp/releases 下載')">📥 更新可用</span>`;
                } else if (data.platform === "linux") {
                    html += `<span class="tool-update" onclick="updateTool('yt-dlp')">📥 點擊更新</span>`;
                }
            }
} else {
    html += `<span class="tool-name">🔴 yt-dlp</span>`;
    html += `<span class="tool-error">${data.yt_dlp.error}</span>`;
}
        html += '</div>';
        
        if (data.platform === "macos") {
            html += '<div style="margin-top:8px; color:var(--warning); font-size:11px;">⚠️ macOS 不支援 gallery-dl/yt-dlp</div>';
        }
        
        $("toolsStatus").innerHTML = html;
        
        // 更新按鈕狀態
        $("gdlBtn").disabled = !data.gallery_dl.available;
        $("ytdlpBtn").disabled = !data.yt_dlp.available;
    } catch (e) {
        console.error("載入工具狀態失敗", e);
        $("toolsStatus").innerHTML = '<span class="tool-error">載入工具狀態失敗</span>';
    }
}

// 更新工具 (Linux only)
async function updateTool(tool) {
    if (!confirm(`確定要更新 ${tool} 嗎？`)) return;
    
    try {
        setStatus(`正在更新 ${tool}...`);
        const data = await api(`/api/tools/update/${tool}`, "POST");
        if (data.ok) {
            alert(`✅ ${data.message}`);
            loadToolsStatus();
        } else {
            alert(`❌ ${data.message}`);
        }
    } catch (e) {
        alert(`更新失敗: ${e.message}`);
    }
    setStatus("Ready.");
}

// 縮圖大小控制
function setThumbSize(size) {
    const grid = $("grid");
    grid.className = `grid size-${size}`;
    localStorage.setItem("rio_thumb_size", size);
    
    // 更新按鈕高光狀態
    ["S", "M", "L", "XL"].forEach(btn => {
        const el = document.querySelector(`[onclick="setThumbSize(${getSizeValue(btn)})"]`);
        if (el) el.classList.remove("active");
    });
    
    const activeBtn = document.querySelector(`[onclick="setThumbSize(${size})"]`);
    if (activeBtn) activeBtn.classList.add("active");
}

function getSizeValue(label) {
    const map = {"S": 120, "M": 160, "L": 200, "XL": 240};
    return map[label];
}

// 載入上次的篩選設定
function loadFilterSettings() {
    try {
        const saved = localStorage.getItem("rio_filter_settings");
        if (saved) {
            const settings = JSON.parse(saved);
            $("minW").value = settings.minW || 0;
            $("minH").value = settings.minH || 0;
            state.filterMinW = settings.minW || 0;
            state.filterMinH = settings.minH || 0;
        }
    } catch (e) {
        console.error("載入篩選設定失敗", e);
    }
}

// 儲存篩選設定
function saveFilterSettings() {
    try {
        const settings = { minW: state.filterMinW, minH: state.filterMinH };
        localStorage.setItem("rio_filter_settings", JSON.stringify(settings));
    } catch (e) {
        console.error("儲存篩選設定失敗", e);
    }
}

function toggleFilterFormat(fmt) {
    const btn = $(`filter${fmt.toUpperCase()}`);
    if (state.filterFormats.has(fmt)) {
        state.filterFormats.delete(fmt);
        btn.classList.remove("active");
    } else {
        state.filterFormats.add(fmt);
        btn.classList.add("active");
    }
    render();
}

function getFilteredItems() {
    return state.items.filter(it => {
        if (it.fmt === "ERR" || it.fmt === "BIG") return false;
        
        if (state.filterFormats.size > 0 && it.kind === "image") {
            const fmt = (it.fmt || "").toUpperCase();
            let match = false;
            if (state.filterFormats.has("jpg") && (fmt.includes("JPEG") || fmt === "JPG")) match = true;
            if (state.filterFormats.has("png") && fmt === "PNG") match = true;
            if (state.filterFormats.has("gif") && fmt === "GIF") match = true;
            if (state.filterFormats.has("webp") && fmt === "WEBP") match = true;
            if (!match) return false;
        }
        
        if (it.kind === "image" && it.w > 0 && it.h > 0) {
            if (it.w < state.filterMinW || it.h < state.filterMinH) return false;
        }
        
        return true;
    });
}

function render() {
    const grid = $("grid");
    grid.innerHTML = "";
    const filtered = getFilteredItems();
    
    if (filtered.length === 0 && state.items.length > 0) {
        const hint = document.createElement("div");
        hint.style.cssText = "padding:40px; text-align:center; color:var(--muted);";
        hint.textContent = "所有項目已被篩選隱藏，試試降低 Min W/H 或按「重設篩選」";
        grid.appendChild(hint);
        $("selCount").textContent = state.selected.size;
        return;
    }
    
    filtered.forEach((it, index) => {
        const card = document.createElement("div");
        card.className = "card";
        if (state.selected.has(it.id)) {
            card.classList.add("selected");
        }
        
        const img = document.createElement("img");
        img.className = "thumb";
        img.src = `/api/thumb/${state.jobId}/${it.id}.jpg`;
        img.loading = "lazy";
        card.appendChild(img);
        
        const meta = document.createElement("div");
        meta.className = "meta";
        
        const row1 = document.createElement("div");
        row1.className = "row";
        
        const left = document.createElement("div");
        left.style.display = "flex";
        left.style.gap = "6px";
        
        const b1 = document.createElement("span");
        b1.className = "badge";
        b1.textContent = it.kind.toUpperCase();
        
        const b2 = document.createElement("span");
        b2.className = "badge";
        b2.textContent = it.fmt || it.ct || "";
        
        left.appendChild(b1);
        left.appendChild(b2);
        
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = state.selected.has(it.id);
        cb.addEventListener("click", (e) => e.stopPropagation());
        cb.addEventListener("change", () => {
            if (cb.checked) state.selected.add(it.id);
            else state.selected.delete(it.id);
            $("selCount").textContent = state.selected.size;
            render();
        });
        
        row1.appendChild(left);
        row1.appendChild(cb);
        
        const row2 = document.createElement("div");
        row2.className = "row";
        
        const dim = document.createElement("div");
        dim.className = "badge";
        dim.textContent = (it.kind === "image" && it.w && it.h) ? `${it.w}x${it.h}` : "-";
        row2.appendChild(dim);
        
        const url = document.createElement("div");
        url.className = "url";
        url.title = it.url;
        url.textContent = it.url;
        
        meta.appendChild(row1);
        meta.appendChild(row2);
        meta.appendChild(url);
        card.appendChild(meta);
        
        // SHIFT 多選邏輯改進版
// 喺現有 card click listener 入面，最開頭加入：
card.addEventListener('click', (e) => {
  const currentFiltered = getFilteredItems();
  
  // 如果係雙擊圖片，打開 lightbox
  if (e.detail === 2 && it.kind === 'image') {
    e.preventDefault();
    e.stopPropagation();
    openLightbox(it.id);
    return;
  }            
            if (e.shiftKey && state.lastClickedIndex !== null) {
                const start = Math.min(state.lastClickedIndex, index);
                const end = Math.max(state.lastClickedIndex, index);
                const lastItem = currentFiltered[state.lastClickedIndex];
                const shouldSelect = !state.selected.has(lastItem.id);
                
                for (let i = start; i <= end; i++) {
                    if (shouldSelect) {
                        state.selected.add(currentFiltered[i].id);
                    } else {
                        state.selected.delete(currentFiltered[i].id);
                    }
                }
                state.lastClickedIndex = index;
                render();
            } else if (e.ctrlKey || e.metaKey) {
                if (state.selected.has(it.id)) {
                    state.selected.delete(it.id);
                } else {
                    state.selected.add(it.id);
                }
                state.lastClickedIndex = index;
                render();
            } else {
                if (state.selected.has(it.id)) {
                    state.selected.delete(it.id);
                } else {
                    state.selected.add(it.id);
                }
                state.lastClickedIndex = index;
                render();
            }
        });
        
        grid.appendChild(card);
    });
    
    $("selCount").textContent = state.selected.size;
}

function applyFilter() {
    state.filterMinW = toInt($("minW").value, 0);
    state.filterMinH = toInt($("minH").value, 0);
    saveFilterSettings();
    render();
}

function resetFilter() {
    state.filterMinW = 0;
    state.filterMinH = 0;
    $("minW").value = "";
    $("minH").value = "";
    state.filterFormats.clear();
    ["JPG", "PNG", "GIF", "WEBP"].forEach(fmt => {
        const btn = $(`filter${fmt}`);
        if (btn) btn.classList.remove("active");
    });
    saveFilterSettings();
    render();
}

function selectAll() {
    getFilteredItems().forEach(it => state.selected.add(it.id));
    render();
}

function unselectAll() {
    state.selected.clear();
    render();
}

function invertSelection() {
    const filtered = getFilteredItems();
    const newSel = new Set();
    filtered.forEach(it => {
        if (!state.selected.has(it.id)) newSel.add(it.id);
    });
    state.selected = newSel;
    render();
}

async function loadDest() {
    try {
        const data = await api("/api/appinfo");
        $("destPath").textContent = data.config.dest_dir || "-";
    } catch (e) {
        console.error("Failed to load dest:", e);
    }
}

async function changeDest() {
    const path = prompt("輸入下載路徑:", $("destPath").textContent);
    if (!path) return;
    try {
        await api("/api/set_dest_dir", "POST", { path });
        $("destPath").textContent = path;
        alert("路徑已儲存");
    } catch (e) {
        alert(`設定失敗: ${e.message}`);
    }
}

async function startScan() {
    const url = $("urlInput").value.trim();
    if (!url) {
        alert("請輸入網址");
        return;
    }
    
    const ultra = $("ultraCheck").checked;
    
    try {
        const data = await api("/api/scan", "POST", { url, ultra });
        state.jobId = data.job_id;
        state.items = [];
        state.selected.clear();
        render();
        
        $("scanBtn").disabled = true;
        $("stopBtn").disabled = false;
        $("scanBtn").classList.add("running");
        
        pollJob(data.job_id);
    } catch (e) {
        alert(`掃描失敗: ${e.message}`);
    }
}

function stopScan() {
    if (!state.jobId) return;
    api(`/api/stop/${state.jobId}`, "POST").catch(console.error);
}

function clearJob() {
  state.jobId = null;
  state.items = [];
  state.selected.clear();
  urlInput.value = '';  // 新增呢行:清除網址輸入欄
  render();
  setStatus('Ready.');
  setProgress(0);
}

async function pollJob(jid) {
    while (true) {
        try {
            const st = await api(`/api/status/${jid}`);
            setStatus(st.message || st.status);
            
            if (st.progress_total > 0) {
                const pct = (st.progress_i / st.progress_total) * 100;
                setProgress(pct);
            }
            
            if (st.status === "done" || st.status === "error" || st.status === "cancelled") {
                $("scanBtn").disabled = false;
                $("stopBtn").disabled = true;
                $("scanBtn").classList.remove("running");
                
                if (st.status === "done") {
                    const itemsData = await api(`/api/items/${jid}`);
                    state.items = itemsData.items || [];
                    render();
                }
                break;
            }
        } catch (e) {
            console.error(e);
            break;
        }
        await new Promise(r => setTimeout(r, 500));
    }
}

// gallery-dl 直接下載
async function startGDL() {
    const url = $("urlInput").value.trim();
    const dest = $("destPath").textContent;
    if (!url) {
        alert("請輸入網址");
        return;
    }
    if (!dest || dest === "-") {
        alert("請先設定下載路徑");
        return;
    }
    
    try {
        const data = await api("/api/gdl_direct", "POST", { url, dest_dir: dest });
        state.jobId = data.job_id;
        $("gdlBtn").disabled = true;
        $("gdlBtn").classList.add("running");
        pollJobForDirectDownload(data.job_id, "gdlBtn");
    } catch (e) {
        alert(`gallery-dl 啟動失敗: ${e.message}`);
    }
}

// yt-dlp 直接下載
async function startYTDLP() {
    const url = $("urlInput").value.trim();
    const dest = $("destPath").textContent;
    if (!url) {
        alert("請輸入網址");
        return;
    }
    if (!dest || dest === "-") {
        alert("請先設定下載路徑");
        return;
    }
    
    try {
        const data = await api("/api/ytdlp/direct", "POST", { url, dest_dir: dest });
        state.jobId = data.job_id;
        $("ytdlpBtn").disabled = true;
        $("ytdlpBtn").classList.add("running");
        pollJobForDirectDownload(data.job_id, "ytdlpBtn");
    } catch (e) {
        alert(`yt-dlp 啟動失敗: ${e.message}`);
    }
}

async function pollJobForDirectDownload(jid, btnId) {
    while (true) {
        try {
            const st = await api(`/api/status/${jid}`);
            setStatus(st.message || st.status);
            
            if (st.status === "done" || st.status === "error" || st.status === "cancelled") {
                $(btnId).disabled = false;
                $(btnId).classList.remove("running");
                break;
            }
        } catch (e) {
            console.error(e);
            break;
        }
        await new Promise(r => setTimeout(r, 500));
    }
}

async function downloadSelected() {
    const sel = Array.from(state.selected);
    if (sel.length === 0) {
        alert("請先選取項目");
        return;
    }
    
    const items = state.items.filter(it => sel.includes(it.id));
    const engine = $("engineSelect").value;
    const dest = $("destPath").textContent;
    
    if (!dest || dest === "-") {
        alert("請先設定下載路徑");
        return;
    }
    
    try {
        setStatus(`下載中... (${engine})`);
        const res = await api("/api/download", "POST", {
            items: items.map(it => ({ url: it.url })),
            engine,
            dest_dir: dest
        });
        
        if (res.result) {
            alert(`下載完成\n成功: ${res.result.ok}\n失敗: ${res.result.fail}`);
        } else {
            alert("下載完成");
        }
        setStatus("Ready.");
    } catch (e) {
        alert(`下載失敗: ${e.message}`);
        setStatus("Ready.");
    }
}

async function init() {
    loadDest();
    loadFilterSettings();
    
    // 恢復縮圖大小設定
    const savedSize = localStorage.getItem("rio_thumb_size") || "160";
    setThumbSize(parseInt(savedSize));
    
    // 載入工具狀態
    await loadToolsStatus();
}
// ============ 圖片放大瀏覽功能 ============
let lightbox = null;
let currentLightboxIndex = 0;
let lightboxItems = [];

function createLightbox() {
  if (lightbox) return;
  
  const overlay = document.createElement('div');
  overlay.id = 'lightbox-overlay';
  overlay.style.cssText = `
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.95);
    z-index: 10000;
    justify-content: center;
    align-items: center;
  `;
  
  const container = document.createElement('div');
  container.style.cssText = `
    position: relative;
    max-width: 90%;
    max-height: 90%;
    display: flex;
    align-items: center;
    justify-content: center;
  `;
  
  const img = document.createElement('img');
  img.id = 'lightbox-image';
  img.style.cssText = `
    max-width: 100%;
    max-height: 90vh;
    object-fit: contain;
  `;
  
  const closeBtn = document.createElement('button');
  closeBtn.innerHTML = '✕';
  closeBtn.style.cssText = `
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    font-size: 30px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    cursor: pointer;
    z-index: 10001;
  `;
  closeBtn.onclick = closeLightbox;
  
  const prevBtn = document.createElement('button');
  prevBtn.innerHTML = '‹';
  prevBtn.style.cssText = `
    position: absolute;
    left: 20px;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    font-size: 40px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    cursor: pointer;
    z-index: 10001;
  `;
  prevBtn.onclick = showPrevImage;
  
  const nextBtn = document.createElement('button');
  nextBtn.innerHTML = '›';
  nextBtn.style.cssText = `
    position: absolute;
    right: 20px;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    font-size: 40px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    cursor: pointer;
    z-index: 10001;
  `;
  nextBtn.onclick = showNextImage;
  
  const counter = document.createElement('div');
  counter.id = 'lightbox-counter';
  counter.style.cssText = `
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    color: white;
    background: rgba(0, 0, 0, 0.5);
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 14px;
  `;
  
  container.appendChild(img);
  overlay.appendChild(container);
  overlay.appendChild(closeBtn);
  overlay.appendChild(prevBtn);
  overlay.appendChild(nextBtn);
  overlay.appendChild(counter);
  
  document.body.appendChild(overlay);
  
  // 按 ESC 關閉
  document.addEventListener('keydown', (e) => {
    if (!lightbox || overlay.style.display === 'none') return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') showPrevImage();
    if (e.key === 'ArrowRight') showNextImage();
  });
  
  // 點擊背景關閉
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeLightbox();
  });
  
  lightbox = overlay;
}

function openLightbox(itemId) {
  if (!lightbox) createLightbox();
  
  const filtered = getFilteredItems();
  lightboxItems = filtered.filter(it => it.kind === 'image');
  
  currentLightboxIndex = lightboxItems.findIndex(it => it.id === itemId);
  if (currentLightboxIndex === -1) return;
  
  showLightboxImage();
  lightbox.style.display = 'flex';
}

function showLightboxImage() {
    if (!lightbox || lightboxItems.length === 0) return;
    
    const item = lightboxItems[currentLightboxIndex];
    const img = document.getElementById('lightbox-image');
    const counter = document.getElementById('lightbox-counter');
    
    // 先試原圖
    img.onerror = function() {
        console.warn('原圖載入失敗（CORS），改用大縮圖');
        // 改用 800px 大縮圖
        img.src = `/api/thumb_large/${state.jobId}/${item.id}.jpg`;
        img.onerror = function() {
            console.error('大縮圖也載入失敗，用小縮圖');
            // 最後備用方案：小縮圖
            img.src = `/api/thumb/${state.jobId}/${item.id}.jpg`;
        };
    };
    
    img.onload = function() {
        console.log('圖片載入成功');
    };
    
    img.src = item.url;
    counter.textContent = `${currentLightboxIndex + 1} / ${lightboxItems.length}`;
}

function showPrevImage() {
  if (lightboxItems.length === 0) return;
  currentLightboxIndex = (currentLightboxIndex - 1 + lightboxItems.length) % lightboxItems.length;
  showLightboxImage();
}

function showNextImage() {
  if (lightboxItems.length === 0) return;
  currentLightboxIndex = (currentLightboxIndex + 1) % lightboxItems.length;
  showLightboxImage();
}

function closeLightbox() {
  if (lightbox) {
    lightbox.style.display = 'none';
  }
}
// ↓↓↓ D2: 確保 DOM 載入完成 ↓↓↓
(function() {
    function safeInit() {
        try {
            // 檢查必要元素是否存在
            const ultraCheck = $('ultraCheck');
            const scanBtn = $('scanBtn');
            const stopBtn = $('stopBtn');
            
            if (!ultraCheck || !scanBtn || !stopBtn) {
                console.warn('某些 UI 元素尚未載入，延遲初始化');
                setTimeout(safeInit, 100);
                return;
            }
            
            // 載入設定
            loadDest();
            loadFilterSettings();
            
            // 載入縮圖大小
            const savedSize = localStorage.getItem('riothumbsize') || '160';
            setThumbSize(parseInt(savedSize));
            
            // 載入工具狀態
            loadToolsStatus();
            
        } catch (e) {
            console.error('初始化錯誤:', e);
        }
    }
    
    // 等待 DOM 載入
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', safeInit);
    } else {
        safeInit();
    }
})();
// ↑↑↑ D2 完 ↑↑↑

init();

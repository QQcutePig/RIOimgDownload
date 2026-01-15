let state = {
  jobId: null,
  items: [],
  selected: new Set(),
  theme: "dark",
  filterMinW: 0,
  filterMinH: 0,
  hideErr: false,  // NEW: hide ERR/BIG placeholder items
  lastClickedIndex: null,
  gdlAvailable: false,
  gdlInfo: "",
};

const $ = (id) => document.getElementById(id);

function setStatus(text) { $("statusText").textContent = text; }
function setProgress(pct) { $("progressBar").style.width = `${pct}%`; }
function toInt(v, def=0) { const n = parseInt(v, 10); return Number.isFinite(n) ? n : def; }

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

function getFilteredItems() {
  return state.items.filter(it => {
    // Filter by dimension
    if (it.kind === "image" && it.w > 0 && it.h > 0) {
      if (it.w < state.filterMinW || it.h < state.filterMinH) return false;
    }
    // NEW: Hide ERR/BIG items if checkbox checked
    if (state.hideErr && (it.fmt === "ERR" || it.fmt === "BIG")) {
      return false;
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
    return;
  }

  filtered.forEach((it, index) => {
    const card = document.createElement("div");
    card.className = "card";

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

    // FIXED: Shift/Ctrl multi-selection (consistent with Tkinter version)
    card.addEventListener("click", (e) => {
      if (e.shiftKey && state.lastClickedIndex !== null) {
        // Shift: range selection
        const start = Math.min(state.lastClickedIndex, index);
        const end = Math.max(state.lastClickedIndex, index);
        for (let i = start; i <= end; i++) {
          state.selected.add(filtered[i].id);
        }
        render();
      } else if (e.ctrlKey || e.metaKey) {
        // Ctrl/Cmd: toggle individual
        if (state.selected.has(it.id)) {
          state.selected.delete(it.id);
        } else {
          state.selected.add(it.id);
        }
        state.lastClickedIndex = index;
        render();
      } else {
        // Normal click: toggle single (match Tkinter behavior)
        if (state.selected.has(it.id)) {
          state.selected.delete(it.id);
        } else {
          state.selected.add(it.id);
        }
        state.lastClickedIndex = index;
        render();
      }
    });

    card.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      openPreview(index);
    });

    grid.appendChild(card);
  });
}

function openPreview(startIndex) {
  const filtered = getFilteredItems();
  if (!filtered.length) return;
  let currentIndex = startIndex;

  const modal = document.createElement("div");
  modal.style.cssText = `
    position:fixed; top:0; left:0; width:100vw; height:100vh;
    background:rgba(0,0,0,0.95); z-index:9999;
    display:flex; align-items:center; justify-content:center;
    flex-direction:column; gap:20px;
  `;

  const img = document.createElement("img");
  img.style.cssText = "max-width:90vw; max-height:70vh; border-radius:8px; box-shadow:0 0 40px rgba(0,0,0,0.8);";

  const info = document.createElement("div");
  info.style.cssText = "color:#fff; font-size:14px; text-align:center; max-width:800px;";

  const nav = document.createElement("div");
  nav.style.cssText = "display:flex; gap:12px; align-items:center;";

  const prevBtn = document.createElement("button");
  prevBtn.textContent = "← 上一張";
  prevBtn.className = "btn";

  const countLabel = document.createElement("span");
  countLabel.style.color = "#fff";
  countLabel.style.fontSize = "14px";

  const nextBtn = document.createElement("button");
  nextBtn.textContent = "下一張 →";
  nextBtn.className = "btn";

  const closeBtn = document.createElement("button");
  closeBtn.textContent = "關閉 (ESC)";
  closeBtn.className = "btn danger";

  nav.appendChild(prevBtn);
  nav.appendChild(countLabel);
  nav.appendChild(nextBtn);
  nav.appendChild(closeBtn);

  modal.appendChild(img);
  modal.appendChild(info);
  modal.appendChild(nav);
  document.body.appendChild(modal);

  function updatePreview() {
    const item = filtered[currentIndex];
    img.src = item.kind === "image" ? item.url : `/api/thumb/${state.jobId}/${item.id}.jpg`;
    info.innerHTML = `
      <div><strong>${item.kind.toUpperCase()}</strong> • ${item.fmt || item.ct}</div>
      ${item.w && item.h ? `<div>${item.w} x ${item.h}</div>` : ""}
      <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${item.url}</div>
    `;
    countLabel.textContent = `${currentIndex + 1} / ${filtered.length}`;
    prevBtn.disabled = currentIndex === 0;
    nextBtn.disabled = currentIndex === filtered.length - 1;
  }

  prevBtn.addEventListener("click", () => { if (currentIndex > 0) { currentIndex--; updatePreview(); } });
  nextBtn.addEventListener("click", () => { if (currentIndex < filtered.length - 1) { currentIndex++; updatePreview(); } });
  closeBtn.addEventListener("click", () => modal.remove());

  modal.addEventListener("click", (e) => { if (e.target === modal) modal.remove(); });

  function onKeydown(e) {
    if (e.key === "Escape") {
      modal.remove();
      document.removeEventListener("keydown", onKeydown);
    } else if (e.key === "ArrowLeft") {
      if (currentIndex > 0) { currentIndex--; updatePreview(); }
    } else if (e.key === "ArrowRight") {
      if (currentIndex < filtered.length - 1) { currentIndex++; updatePreview(); }
    }
  }
  document.addEventListener("keydown", onKeydown);

  updatePreview();
}

async function pollJob() {
  if (!state.jobId) return;
  const st = await api(`/api/jobs/${state.jobId}/status`);
  const pct = Math.floor((st.progress_i / Math.max(st.progress_total, 1)) * 100);
  setProgress(pct);
  setStatus(`${st.status}: ${st.message || ""}`);

  if (["running", "idle"].includes(st.status)) {
    setTimeout(pollJob, 500);
  } else {
    $("scanBtn").disabled = false;
    $("gdlDirectBtn").disabled = false;
    $("stopBtn").disabled = true;

    if (st.job_type === "scan" && st.status === "done") {
      const data = await api(`/api/jobs/${state.jobId}/items`);
      state.items = data.items || [];
      state.selected = new Set(state.items.map(x => x.id));
      render();
      alert(state.items.length > 0 ? `✅ 掃描完成！找到 ${state.items.length} 項媒體` : "⚠️ 掃描完成，但冇搵到媒體（試 Ultra / Login Mode）");
    } else if (st.job_type === "gdl_direct" && st.status === "done") {
      alert("✅ G-DL Direct 完成（已直接下載到目的資料夾）。");
    } else if (st.status === "error") {
      alert(`❌ 失敗：${st.message}`);
    } else if (st.status === "cancelled") {
      alert("🛑 已停止");
    }
  }
}

async function onScan() {
  const url = $("urlInput").value.trim();
  if (!url) return;

  $("scanBtn").disabled = true;
  $("gdlDirectBtn").disabled = true;
  $("stopBtn").disabled = false;
  setProgress(0);
  setStatus("Starting scan...");

  const payload = {
    url,
    ultra: $("ultraChk").checked,
    use_login_profile: $("loginModeChk").checked,
    debug_browser: $("debugChk").checked,
    want_image: $("wantImageChk").checked,
    want_video: $("wantVideoChk").checked,
    min_w: toInt($("minW").value, 0),
    min_h: toInt($("minH").value, 0),
    blacklist: $("blacklist").value.trim()
  };

  const res = await api("/api/scan", "POST", payload);
  state.jobId = res.job_id;
  state.items = [];
  state.selected = new Set();
  state.lastClickedIndex = null;
  render();
  pollJob();
}

async function onGdlDirect() {
  const url = $("urlInput").value.trim();
  if (!url) return;

  if (!state.gdlAvailable) {
    alert(state.gdlInfo);
    return;
  }

  const dest = $("destDir").value.trim();
  if (!dest) {
    alert("請先輸入下載路徑 dest_dir");
    return;
  }

  if (!confirm("G-DL Direct 會直接用 gallery-dl 掃網址並下載（冇預覽）。確定繼續？")) return;

  $("scanBtn").disabled = true;
  $("gdlDirectBtn").disabled = true;
  $("stopBtn").disabled = false;
  setProgress(0);
  setStatus("Starting G-DL Direct...");

  try {
    const res = await api("/api/gdl_direct", "POST", { url, dest_dir: dest });
    state.jobId = res.job_id;
    pollJob();
  } catch (e) {
    alert(`❌ ${e.message}`);
    $("scanBtn").disabled = false;
    $("gdlDirectBtn").disabled = false;
    $("stopBtn").disabled = true;
  }
}

async function onStop() {
  if (!state.jobId) return;
  await api(`/api/jobs/${state.jobId}/cancel`, "POST", {});
  setStatus("Cancelling...");
}

function onClear() {
  state.jobId = null;
  state.items = [];
  state.selected = new Set();
  state.filterMinW = 0;
  state.filterMinH = 0;
  state.hideErr = false;
  state.lastClickedIndex = null;
  $("minW").value = "0";
  $("minH").value = "0";
  $("hideErrChk").checked = false;
  $("grid").innerHTML = "";
  setProgress(0);
  setStatus("Ready.");
}

async function onDownload() {
  const dest = $("destDir").value.trim();
  if (!dest) { alert("請輸入下載路徑 dest_dir"); return; }

  const engine = $("engineSel").value;

  if (engine === "gallery-dl" && !state.gdlAvailable) {
    alert(state.gdlInfo);
    return;
  }

  const filtered = getFilteredItems();
  const selectedItems = filtered.filter(it => state.selected.has(it.id));
  const urls = selectedItems.map(x => x.url);
  if (!urls.length) { alert("未有選取項目"); return; }

  setStatus("Downloading...");
  const res = await api("/api/download", "POST", { urls, dest_dir: dest, engine });
  setStatus(`Download done. ok=${res.result.ok} fail=${res.result.fail}`);
  alert(`✅ 下載完成！成功：${res.result.ok}  失敗：${res.result.fail}`);
}

async function onOpenLogin() {
  await api("/api/login/open", "POST", { url: "https://www.instagram.com/" });
  alert("已開啟登入視窗：請登入後關閉視窗。之後掃描可勾選 Login Mode。");
}

async function onClearLogin() {
  await api("/api/login/clear", "POST", {});
  alert("已清除登入資料。");
}

function setTheme(next) {
  state.theme = next;
  if (next === "light") document.documentElement.classList.add("light");
  else document.documentElement.classList.remove("light");
}

function applyFilter() {
  state.filterMinW = toInt($("minW").value, 0);
  state.filterMinH = toInt($("minH").value, 0);
  state.hideErr = $("hideErrChk").checked;  // NEW
  render();
  const filtered = getFilteredItems();
  setStatus(`已套用篩選：顯示 ${filtered.length} / ${state.items.length} 項`);
}

function resetFilter() {
  state.filterMinW = 0;
  state.filterMinH = 0;
  state.hideErr = false;
  $("minW").value = "0";
  $("minH").value = "0";
  $("hideErrChk").checked = false;
  render();
  setStatus(`已重設篩選：顯示全部 ${state.items.length} 項`);
}

window.addEventListener("DOMContentLoaded", async () => {
  setTheme("dark");

  const info = await api("/api/appinfo");
  if (info.config && info.config.dest_dir) $("destDir").value = info.config.dest_dir;

  state.gdlAvailable = info.gallery_dl_available;
  state.gdlInfo = info.gallery_dl_info;

  if (!state.gdlAvailable) {
    $("gdlStatusText").textContent = `⚠️ gallery-dl: ${state.gdlInfo}`;
    $("gdlStatusText").style.color = "var(--warning)";
  } else {
    $("gdlStatusText").textContent = `✅ gallery-dl: ${state.gdlInfo}`;
    $("gdlStatusText").style.color = "var(--success)";
  }

  $("themeBtn").addEventListener("click", () => setTheme(state.theme === "dark" ? "light" : "dark"));

  $("scanBtn").addEventListener("click", onScan);
  $("gdlDirectBtn").addEventListener("click", onGdlDirect);
  $("stopBtn").addEventListener("click", onStop);
  $("clearBtn").addEventListener("click", onClear);
  $("downloadBtn").addEventListener("click", onDownload);

  $("loginBtn").addEventListener("click", onOpenLogin);
  $("clearLoginBtn").addEventListener("click", onClearLogin);

  $("selAllBtn").addEventListener("click", () => {
    const filtered = getFilteredItems();
    state.selected = new Set(filtered.map(x => x.id));
    render();
  });
  $("selNoneBtn").addEventListener("click", () => { state.selected = new Set(); render(); });
  $("invertBtn").addEventListener("click", () => {
    const filtered = getFilteredItems();
    const ns = new Set();
    for (const it of filtered) if (!state.selected.has(it.id)) ns.add(it.id);
    state.selected = ns;
    render();
  });

  $("applyFilterBtn").addEventListener("click", applyFilter);
  $("resetFilterBtn").addEventListener("click", resetFilter);

  // NEW: Hide ERR checkbox listener
  $("hideErrChk").addEventListener("change", applyFilter);

  $("minW").addEventListener("keypress", (e) => { if (e.key === "Enter") applyFilter(); });
  $("minH").addEventListener("keypress", (e) => { if (e.key === "Enter") applyFilter(); });

  $("blacklist").value = "avatar,noavatar,logo,sprite,icon,favicon,emoji,emoticon,blank,spacer,loading,placeholder,banner,tracking,pixel";
});

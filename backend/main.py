import os
import re
import json
import time
import shutil
import threading
import subprocess
import tempfile
import hashlib
import sys
import platform
from dataclasses import dataclass, asdict
from io import BytesIO
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image, ImageDraw
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from platformdirs import user_data_dir
from playwright.sync_api import sync_playwright

APP_NAME = "RIOimgDownload"

# ----------------- Tuning -----------------
THUMB_SIZE = 800  # 240 → 800 (提升 3 倍清晰度)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PAGE_GOTO_WAIT_UNTIL = "domcontentloaded"
GOTO_TIMEOUT_MS = 60000
HEAD_TIMEOUT = 10
GET_TIMEOUT = 25
DOWNLOAD_TIMEOUT = 90
MAX_THUMB_BYTES = 25 * 1024 * 1024
SNIFF_BYTES = 65536
SNIFF_GET_TIMEOUT = 18
SCROLL_WAIT_MS_DEFAULT = 1500
MAX_SCROLL_ROUNDS_DEFAULT = 50
STABLE_ROUNDS_TO_STOP_DEFAULT = 3
# ↓↓↓ B1: 增加並發數量 ↓↓↓
VERIFY_WORKERS = 20  # 12 → 20 (+67% 速度)
THUMB_WORKERS = 12   # 8 → 12 (+50% 速度)
# ↑↑↑ B1 完 ↑↑↑
DEFAULT_BLACKLIST = [
    "avatar", "noavatar", "logo", "sprite", "icon", "favicon", "emoji", "emoticon",
    "blank", "spacer", "loading", "placeholder", "banner", "tracking", "pixel"
]

# ----------------- Paths -----------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
APP_DATA = user_data_dir(APP_NAME, appauthor=False)
PROFILE_DIR = os.path.join(APP_DATA, "browser_profile")
JOBS_DIR = os.path.join(APP_DATA, "jobs")
CONFIG_PATH = os.path.join(APP_DATA, "config.json")
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# 工具執行檔路徑 (放在 run 資料夾層)
TOOLS_DIR = BASE_DIR
GDL_EXE = os.path.join(TOOLS_DIR, "gallery-dl.exe" if platform.system() == "Windows" else "gallery-dl")
YTDLP_EXE = os.path.join(TOOLS_DIR, "yt-dlp.exe" if platform.system() == "Windows" else "yt-dlp")

os.makedirs(APP_DATA, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)

# ----------------- Platform Detection -----------------
# ↓↓↓ C3: 簡化 platform detection ↓↓↓
def get_platform_type() -> str:
    """Returns: 'windows' | 'linux' | 'unknown'"""
    p = platform.system().lower()
    if "windows" in p:
        return "windows"
    elif "linux" in p:
        return "linux"
    return "unknown"  # 移除 macOS 特殊處理
# ↑↑↑ C3 完 ↑↑↑

# ----------------- Helpers -----------------
def safe_name(s: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]+', "_", s)
    return s.strip(" ._")[:160] or "file"

def hash8(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "ignore")).hexdigest()[:8]

def is_image_content_type(ct: str) -> bool:
    ct = (ct or "").split(";")[0].strip().lower()
    return ct.startswith("image/")

def is_video_content_type(ct: str) -> bool:
    ct = (ct or "").split(";")[0].strip().lower()
    return ct.startswith("video/")

def looks_like_image_url(u: str) -> bool:
    lu = u.lower().split("?")[0].split("#")[0]
    return lu.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".avif"))

def looks_like_video_url(u: str) -> bool:
    lu = u.lower().split("?")[0].split("#")[0]
    return lu.endswith((".mp4", ".webm", ".mov", ".m4v"))

def parse_srcset_pick_largest(srcset: str) -> Optional[str]:
    if not srcset:
        return None
    parts = [p.strip() for p in srcset.split(",") if p.strip()]
    best_url = None
    best_w = -1
    for p in parts:
        seg = p.split()
        if not seg:
            continue
        u = seg[0]
        w = None
        if len(seg) >= 2 and seg[1].endswith("w"):
            try:
                w = int(seg[1][:-1])
            except:
                w = None
        if w is not None and w > best_w:
            best_w = w
            best_url = u
        elif best_url is None:
            best_url = u
    return best_url

def extract_background_urls(style_text: str) -> List[str]:
    if not style_text:
        return []
    found = re.findall(r'url\(([\'"]?)(.*?)\1\)', style_text, flags=re.IGNORECASE)
    out = []
    for _, u in found:
        u = u.strip()
        if u and not u.lower().startswith("data:"):
            out.append(u)
    return out

def iter_strings(obj: Any):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from iter_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_strings(v)
    elif isinstance(obj, str):
        yield obj

_session_local = threading.local()

def new_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({"User-Agent": USER_AGENT})
    return s

def get_session() -> requests.Session:
    if not hasattr(_session_local, "s"):
        _session_local.s = new_session()
    return _session_local.s

def head_info(session: requests.Session, url: str) -> Tuple[str, Optional[int]]:
    try:
        r = session.head(url, timeout=HEAD_TIMEOUT, allow_redirects=True)
        ct = r.headers.get("Content-Type", "")
        cl = r.headers.get("Content-Length", "")
        size = int(cl) if cl and cl.isdigit() else None
        return ct, size
    except Exception as e:
        # D1: 記錄錯誤（但唔影響執行）
        # print(f"[head_info] {url}: {e}")
        return "", None

def get_bytes(session: requests.Session, url: str, timeout=GET_TIMEOUT) -> Tuple[bytes, dict]:
    r = session.get(url, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r.content, dict(r.headers)

def get_head_bytes(session: requests.Session, url: str, max_bytes=SNIFF_BYTES, timeout=SNIFF_GET_TIMEOUT) -> Tuple[bytes, dict]:
    with session.get(url, stream=True, timeout=timeout, allow_redirects=True) as r:
        r.raise_for_status()
        chunks = []
        got = 0
        for chunk in r.iter_content(chunk_size=8192):
            if not chunk:
                continue
            chunks.append(chunk)
            got += len(chunk)
            if got >= max_bytes:
                break
        return b"".join(chunks), dict(r.headers)

def make_placeholder_thumb(kind: str, size_px=THUMB_SIZE) -> Image.Image:
    img = Image.new("RGB", (size_px, size_px), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    text = "VIDEO" if kind == "video" else "ERR" if kind == "err" else "?"
    draw.rectangle([10, 10, size_px - 10, size_px - 10], outline=(90, 90, 90), width=2)
    tw = len(text) * 8
    draw.text((size_px // 2 - tw // 2, size_px // 2 - 8), text, fill=(220, 220, 220))
    return img

def make_image_thumb_from_bytes(b: bytes, size_px=THUMB_SIZE) -> Image.Image:
    img = Image.open(BytesIO(b))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    img.thumbnail((size_px, size_px))
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (30, 30, 30))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    return img

def save_thumb(img: Image.Image, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, format="JPEG", quality=85, optimize=True)

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {"dest_dir": DEFAULT_DOWNLOAD_DIR}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if "dest_dir" not in cfg:
            cfg["dest_dir"] = DEFAULT_DOWNLOAD_DIR
        return cfg
    except:
        return {"dest_dir": DEFAULT_DOWNLOAD_DIR}

def save_config(data: dict) -> None:
    os.makedirs(APP_DATA, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ----------------- Tool Detection (gallery-dl & yt-dlp) -----------------
def get_tool_command(tool: str) -> Optional[List[str]]:
    """
    Returns command to run tool (gallery-dl or yt-dlp), or None if not available.
    - Windows/Linux: use executable in run folder if present
    - macOS: return None (not supported)
    """
    pt = get_platform_type()
    if pt == "macos":
        return None
    
    exe_path = GDL_EXE if tool == "gallery-dl" else YTDLP_EXE
    if os.path.exists(exe_path):
        return [exe_path]
    return None

def get_tool_version(tool: str) -> Tuple[bool, str]:
    """Returns (ok, version_string_or_error)"""
    cmd = get_tool_command(tool)
    if not cmd:
        pt = get_platform_type()
        if pt == "macos":
            return False, f"{tool} not supported on macOS"
        return False, f"{tool} not found. Please download and place in run folder"
    
    try:
        p = subprocess.run(cmd + ["--version"], capture_output=True, text=True, timeout=10)
        if p.returncode == 0:
            return True, (p.stdout or "").strip()
        return False, (p.stderr or p.stdout or "version check failed").strip()
    except:
        return False, "version check error"

def check_tool_update(tool: str) -> Tuple[bool, str]:
    """
    Check if newer version available via GitHub API.
    Returns (has_update, latest_version_or_message)
    """
    try:
        repo = "mikf/gallery-dl" if tool == "gallery-dl" else "yt-dlp/yt-dlp"
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return False, "無法檢查更新"
        data = r.json()
        latest = data.get("tag_name", "").lstrip("v")
        
        ok, current = get_tool_version(tool)
        if not ok:
            return False, current
        
        # 簡單版本比較
        current_ver = current.split()[0].lstrip("v")
        if latest != current_ver:
            return True, latest
        return False, latest
    except Exception as e:
        return False, f"檢查更新失敗: {str(e)}"

def update_tool_linux(tool: str) -> Tuple[bool, str]:
    """Linux only: download latest binary from GitHub"""
    if get_platform_type() != "linux":
        return False, "自動更新僅支援 Linux"
    
    try:
        repo = "mikf/gallery-dl" if tool == "gallery-dl" else "yt-dlp/yt-dlp"
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        # 找到對應的下載連結
        asset_name = tool if tool == "gallery-dl" else "yt-dlp"
        download_url = None
        for asset in data.get("assets", []):
            if asset["name"] == asset_name or asset["name"] == f"{asset_name}_linux":
                download_url = asset["browser_download_url"]
                break
        
        if not download_url:
            return False, "找不到下載連結"
        
        exe_path = GDL_EXE if tool == "gallery-dl" else YTDLP_EXE
        temp_path = exe_path + ".tmp"
        
        # 下載檔案
        r = requests.get(download_url, timeout=120)
        r.raise_for_status()
        with open(temp_path, "wb") as f:
            f.write(r.content)
        
        # 設定執行權限並替換
        os.chmod(temp_path, 0o755)
        os.replace(temp_path, exe_path)
        
        ok, ver = get_tool_version(tool)
        return ok, f"已更新至 {ver}" if ok else ver
    except Exception as e:
        return False, f"更新失敗: {str(e)}"

# 向下相容的函數
def get_gdl_command() -> Optional[List[str]]:
    return get_tool_command("gallery-dl")

def get_ytdlp_command() -> Optional[List[str]]:
    return get_tool_command("yt-dlp")

def run_gallery_dl(args: List[str], timeout_sec: int = 60 * 30) -> Tuple[int, str]:
    cmd = get_gdl_command()
    if not cmd:
        return 127, "gallery-dl not available"
    
    try:
        p = subprocess.run(cmd + args, capture_output=True, text=True, timeout=timeout_sec)
        out = (p.stdout or "") + "\n" + (p.stderr or "")
        return p.returncode, out.strip()
    except FileNotFoundError:
        return 127, "gallery-dl not found"
    except subprocess.TimeoutExpired:
        return 124, "gallery-dl timeout"

def run_ytdlp(args: List[str], timeout_sec: int = 60 * 30) -> Tuple[int, str]:
    cmd = get_ytdlp_command()
    if not cmd:
        return 127, "yt-dlp not available"
    
    try:
        p = subprocess.run(cmd + args, capture_output=True, text=True, timeout=timeout_sec)
        out = (p.stdout or "") + "\n" + (p.stderr or "")
        return p.returncode, out.strip()
    except FileNotFoundError:
        return 127, "yt-dlp not found"
    except subprocess.TimeoutExpired:
        return 124, "yt-dlp timeout"

def get_gdl_version() -> Tuple[bool, str]:
    return get_tool_version("gallery-dl")

def get_ytdlp_version() -> Tuple[bool, str]:
    return get_tool_version("yt-dlp")

def update_gdl_linux() -> Tuple[bool, str]:
    return update_tool_linux("gallery-dl")

def update_ytdlp_linux() -> Tuple[bool, str]:
    return update_tool_linux("yt-dlp")

def auto_install_update_gdl_linux():
    """Background thread: Linux auto-install/update gallery-dl on startup."""
    if get_platform_type() != "linux":
        return
    
    def _worker():
        print("[RIOimgDownload] Linux: auto-installing/updating gallery-dl...")
        ok, msg = update_gdl_linux()
        print(f"[RIOimgDownload] {msg}")
    
    threading.Thread(target=_worker, daemon=True).start()
# ----------------- Presets -----------------
def detect_site_preset(start_url: str) -> dict:
    host = (urlparse(start_url).netloc or "").lower()
    preset = {
        "name": "generic",
        "scroll_wait_ms": SCROLL_WAIT_MS_DEFAULT,
        "max_scroll_rounds": MAX_SCROLL_ROUNDS_DEFAULT,
        "stable_rounds_to_stop": STABLE_ROUNDS_TO_STOP_DEFAULT,
        "parse_network_json": True,
        "network_url_keywords": [],
    }
    if "instagram.com" in host:
        preset.update({
            "name": "instagram",
            "scroll_wait_ms": 1800,
            "max_scroll_rounds": 80,
            "stable_rounds_to_stop": 4,
            "network_url_keywords": ["graphql", "api", "query", "feed", "reels", "media"],
        })
    elif "x.com" in host or "twitter.com" in host:
        preset.update({
            "name": "x",
            "scroll_wait_ms": 1700,
            "max_scroll_rounds": 90,
            "stable_rounds_to_stop": 4,
            "network_url_keywords": ["graphql", "api", "timeline", "Tweet", "Search", "User", "HomeTimeline"],
        })
    elif "facebook.com" in host or "fb.com" in host:
        preset.update({
            "name": "facebook",
            "scroll_wait_ms": 1900,
            "max_scroll_rounds": 80,
            "stable_rounds_to_stop": 4,
            "network_url_keywords": ["graphql", "api", "photo", "video", "stories"],
        })
    return preset

def should_parse_network_response(resp_url: str, content_type: str, preset: dict, ultra: bool) -> bool:
    u = (resp_url or "").lower()
    ct = (content_type or "").lower()
    if looks_like_image_url(u) or looks_like_video_url(u):
        return True
    if ultra and ("graphql" in u or "api" in u):
        return True
    if "application/json" in ct or "text/javascript" in ct or "application/x-javascript" in ct:
        kws = preset.get("network_url_keywords") or []
        if not kws:
            return True
        return any(k in u for k in kws)
    if "graphql" in u:
        return True
    return False

# ----------------- Models -----------------
@dataclass
class MediaItem:
    id: str
    url: str
    kind: str
    ct: str
    w: int = 0
    h: int = 0
    fmt: str = ""
    size: Optional[int] = None
    thumb_path: str = ""

@dataclass
class JobState:
    id: str
    status: str
    message: str = ""
    progress_i: int = 0
    progress_total: int = 0
    created_at: float = 0.0
    finished_at: float = 0.0
    job_type: str = "scan"

# ----------------- Job Manager -----------------
class JobManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.jobs: Dict[str, JobState] = {}
        self.items: Dict[str, List[MediaItem]] = {}
        self.cancel: Dict[str, threading.Event] = {}

    def new_job(self, job_type: str = "scan") -> str:
        jid = hash8(str(time.time()) + str(os.getpid()) + str(threading.get_ident()))
        with self._lock:
            self.jobs[jid] = JobState(id=jid, status="idle", created_at=time.time(), job_type=job_type)
            self.items[jid] = []
            self.cancel[jid] = threading.Event()
        return jid

    def set_status(self, jid: str, status: str, message: str = ""):
        with self._lock:
            js = self.jobs[jid]
            js.status = status
            js.message = message
            if status in ("done", "error", "cancelled"):
                js.finished_at = time.time()

    def set_progress(self, jid: str, i: int, total: int, message: str = ""):
        with self._lock:
            js = self.jobs[jid]
            js.progress_i = i
            js.progress_total = max(total, 1)
            if message:
                js.message = message

    def add_items(self, jid: str, new_items: List[MediaItem]):
        with self._lock:
            self.items[jid].extend(new_items)

JM = JobManager()

# ----------------- Scan Logic -----------------
def _is_blacklisted(url: str, blacklist: List[str]) -> bool:
    lu = url.lower()
    return any(k in lu for k in blacklist)

def scan_worker(job_id: str, url: str, ultra: bool, use_login_profile: bool, debug_browser: bool,
                min_w: int, min_h: int, want_image: bool, want_video: bool,
                blacklist_csv: str):
    cancel_ev = JM.cancel[job_id]
    preset = detect_site_preset(url)
    browser_channel = "msedge" if platform.system() == "Windows" else "chrome"
    blacklist = [x.strip().lower() for x in (blacklist_csv or "").split(",") if x.strip()] or DEFAULT_BLACKLIST

    job_dir = os.path.join(JOBS_DIR, job_id)
    thumbs_dir = os.path.join(job_dir, "thumbs")
    os.makedirs(thumbs_dir, exist_ok=True)

    JM.set_status(job_id, "running", f"Scanning... ({preset['name']})")

    dom_candidates: List[str] = []
    net_candidates: set[str] = set()

    def add_dom(u: str):
        if not u or u.lower().startswith("data:") or _is_blacklisted(u, blacklist):
            return
        dom_candidates.append(u)

    def add_net(u: str):
        if not u or u.lower().startswith("data:") or _is_blacklisted(u, blacklist):
            return
        net_candidates.add(u)

    try:
        with sync_playwright() as p:
            headless = (not debug_browser)
            
            if use_login_profile:
                os.makedirs(PROFILE_DIR, exist_ok=True)
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=PROFILE_DIR,
                        channel=browser_channel,
                        headless=headless,
                        user_agent=USER_AGENT,
                        viewport={"width": 1280, "height": 800},
                        ignore_default_args=["--enable-automation"],
                        args=["--no-first-run", "--no-default-browser-check"],
                    )
                except Exception as e:
                    JM.set_status(job_id, "error", f"Cannot open {browser_channel}: {e}")
                    return
            else:
                try:
                    browser = p.chromium.launch(channel=browser_channel, headless=headless)
                    context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1280, "height": 800})
                except Exception as e:
                    JM.set_status(job_id, "error", f"Cannot open {browser_channel}: {e}")
                    return

            page = context.pages[0] if context.pages else context.new_page()

            def on_response(resp):
                if cancel_ev.is_set():
                    return
                try:
                    ru = resp.url
                    headers = resp.headers or {}
                    ct = headers.get("content-type", "") or headers.get("Content-Type", "")
                    
                    if should_parse_network_response(ru, ct, preset, ultra):
                        if want_image and looks_like_image_url(ru):
                            add_net(ru)
                            return
                        if want_video and looks_like_video_url(ru):
                            add_net(ru)
                            return
                        
                        try:
                            data = resp.json()
                        except:
                            return
                        
                        for s in iter_strings(data):
                            if not isinstance(s, str) or not s.startswith("http"):
                                continue
                            s2 = s.replace("\\u0026", "&")
                            if want_image and looks_like_image_url(s2):
                                add_net(s2)
                            elif want_video and looks_like_video_url(s2):
                                add_net(s2)
                except:
                    pass

            page.on("response", on_response)

            try:
                page.goto(url, wait_until=PAGE_GOTO_WAIT_UNTIL, timeout=GOTO_TIMEOUT_MS)
            except:
                pass

            page.wait_for_timeout(1500)

            last_h = 0
            stable = 0

            # A3: Ultra Mode 增加掃描時間
            if ultra:
                scroll_wait_ms = int(preset.get("scroll_wait_ms", SCROLL_WAIT_MS_DEFAULT)) + 500
                max_scroll_rounds = int(preset.get("max_scroll_rounds", MAX_SCROLL_ROUNDS_DEFAULT)) * 2
                stable_rounds_to_stop = int(preset.get("stable_rounds_to_stop", STABLE_ROUNDS_TO_STOP_DEFAULT)) + 2
            else:
                scroll_wait_ms = int(preset.get("scroll_wait_ms", SCROLL_WAIT_MS_DEFAULT))
                max_scroll_rounds = int(preset.get("max_scroll_rounds", MAX_SCROLL_ROUNDS_DEFAULT))
                stable_rounds_to_stop = int(preset.get("stable_rounds_to_stop", STABLE_ROUNDS_TO_STOP_DEFAULT))

            # B2: 智能滾動停止
            last_net_count = 0
            no_new_images_count = 0

            for round_num in range(max_scroll_rounds):
                if cancel_ev.is_set():
                    JM.set_status(job_id, "cancelled", "Cancelled.")
                    try:
                        context.close()
                    except:
                        pass
                    return

                JM.set_progress(job_id, round_num, max_scroll_rounds, 
                              f"Scrolling... ({round_num}/{max_scroll_rounds}) net={len(net_candidates)}")

                page.mouse.wheel(0, 1800)
                page.wait_for_timeout(scroll_wait_ms)

                try:
                    h = page.evaluate("() => document.body.scrollHeight")
                except:
                    h = last_h

                if h == last_h:
                    stable += 1
                    if stable >= stable_rounds_to_stop:
                        break
                else:
                    stable = 0
                last_h = h

                # 智能停止
                current_net_count = len(net_candidates)
                if current_net_count == last_net_count:
                    no_new_images_count += 1
                    if no_new_images_count >= 2 and round_num > 10:
                        break
                else:
                    no_new_images_count = 0
                last_net_count = current_net_count

            base_url = page.url

            # A1: 加入更多 data-* 屬性
            raw_img = page.eval_on_selector_all(
                "img",
                """els => els.map(e => ({
                src: e.getAttribute('src') || '',
                currentSrc: e.currentSrc || '',
                srcset: e.getAttribute('srcset') || '',
                dataSrc: e.getAttribute('data-src') || '',
                dataOriginal: e.getAttribute('data-original') || '',
                dataLazy: e.getAttribute('data-lazy') || '',
                dataLazySrc: e.getAttribute('data-lazy-src') || '',
                dataSrcset: e.getAttribute('data-srcset') || '',
                dataLazySrcset: e.getAttribute('data-lazy-srcset') || '',
                dataZoom: e.getAttribute('data-zoom-image') || '',
                dataLarge: e.getAttribute('data-large') || '',
                dataFullSrc: e.getAttribute('data-full-src') || '',
                dataHires: e.getAttribute('data-hires') || '',
                dataOriginalSrc: e.getAttribute('data-original-src') || '',
                dataHighRes: e.getAttribute('data-high-res') || '',
                dataLightbox: e.getAttribute('data-lightbox') || ''
            }))"""
            )

            raw_bg_styles = page.eval_on_selector_all(
                "[style]", "els => els.map(e => e.getAttribute('style') || '').filter(Boolean)"
            )

            raw_a = page.eval_on_selector_all(
                "a[href]", "els => els.map(a => a.getAttribute('href') || '').filter(Boolean)"
            )

            raw_video = page.eval_on_selector_all(
                "video, video source, source[type^='video']",
                """els => els.map(e => ({
                src: e.getAttribute('src') || '',
                srcset: e.getAttribute('srcset') || '',
                type: e.getAttribute('type') || ''
            }))"""
            )

            raw_source = []
            raw_link_preload = []
            js_urls = []
            
            if ultra:
                raw_source = page.eval_on_selector_all(
                    "source[srcset], source[src]",
                    "els => els.map(e => ({src: e.getAttribute('src') || '', srcset: e.getAttribute('srcset') || ''}))"
                )
                
                raw_link_preload = page.eval_on_selector_all(
                    "link[rel='preload'][href]",
                    "els => els.map(l => l.getAttribute('href') || '').filter(Boolean)"
                )
                
                # A2: Ultra Mode 掃描 JS 變數
                try:
                    js_urls = page.evaluate("""() => {
                        const urls = [];
                        const patterns = [
                            window.__INITIAL_DATA__,
                            window.__NEXT_DATA__,
                            window.__PRELOADED_STATE__,
                            window.App,
                            window.pageData
                        ];
                        
                        function findUrls(obj, depth = 0) {
                            if (depth > 5 || !obj) return;
                            if (typeof obj === 'string' && obj.match(/^https?:\\/\\/.+\\.(jpg|jpeg|png|gif|webp|bmp|mp4|webm)/i)) {
                                urls.push(obj);
                            } else if (typeof obj === 'object') {
                                for (let key in obj) {
                                    if (obj.hasOwnProperty(key)) {
                                        findUrls(obj[key], depth + 1);
                                    }
                                }
                            }
                        }
                        
                        patterns.forEach(p => findUrls(p));
                        return urls;
                    }""")
                except:
                    js_urls = []

            try:
                context.close()
            except:
                pass

            # 處理提取的資料
            for obj in raw_img:
                cand_list = []
                ss_best = parse_srcset_pick_largest(obj.get("srcset") or "")
                if ss_best:
                    cand_list.append(ss_best)
                cand_list.extend([
                    obj.get("currentSrc"), obj.get("src"), obj.get("dataSrc"), obj.get("dataOriginal"),
                    obj.get("dataLazy"), obj.get("dataLazySrc"), obj.get("dataSrcset"),
                    obj.get("dataLazySrcset"), obj.get("dataZoom"), obj.get("dataLarge"),
                    obj.get("dataFullSrc"), obj.get("dataHires"), obj.get("dataOriginalSrc"),
                    obj.get("dataHighRes"), obj.get("dataLightbox")
                ])
                best = ""
                for c in cand_list:
                    if c and not c.lower().startswith("data:"):
                        best = c
                        break
                if best:
                    add_dom(urljoin(base_url, best))

            for st in raw_bg_styles:
                for u2 in extract_background_urls(st):
                    add_dom(urljoin(base_url, u2))

            for href in raw_a:
                absu = urljoin(base_url, href)
                if absu.lower().startswith(("javascript:", "data:")):
                    continue
                if ultra:
                    add_dom(absu)
                else:
                    lu = absu.lower()
                    if looks_like_image_url(lu) or looks_like_video_url(lu) or "/attachment" in lu or "/attachments" in lu:
                        add_dom(absu)

            if ultra:
                for obj in raw_source:
                    ss_best = parse_srcset_pick_largest(obj.get("srcset") or "")
                    if ss_best:
                        add_dom(urljoin(base_url, ss_best))
                    s = obj.get("src") or ""
                    if s and not s.lower().startswith("data:"):
                        add_dom(urljoin(base_url, s))

                for href in raw_link_preload:
                    add_dom(urljoin(base_url, href))
                
                # A2: 處理 JS 變數提取的 URLs
                for js_url in js_urls:
                    add_dom(js_url)

            for obj in raw_video:
                s = obj.get("src") or ""
                if s:
                    add_dom(urljoin(base_url, s))
                ss_best = parse_srcset_pick_largest(obj.get("srcset") or "")
                if ss_best:
                    add_dom(urljoin(base_url, ss_best))

            merged = list(net_candidates) + dom_candidates
            uniq = list(dict.fromkeys([u for u in merged if u]))

            if not uniq:
                JM.set_status(job_id, "done", "No candidates found (try Ultra).")
                return

            JM.set_progress(job_id, 0, len(uniq), f"Verifying links... (net={len(net_candidates)} dom={len(dom_candidates)})")

        verified: List[Tuple[str, str, Optional[int]]] = []

        def verify_one(u: str):
            s = get_session()
            ct, size = head_info(s, u)
            if want_image and (is_image_content_type(ct) or looks_like_image_url(u)):
                return (u, ct, size)
            if want_video and (is_video_content_type(ct) or looks_like_video_url(u)):
                return (u, ct, size)
            try:
                headb, headers = get_head_bytes(s, u)
                ct2 = headers.get("Content-Type", ct)
                if want_image and (is_image_content_type(ct2) or looks_like_image_url(u)):
                    Image.open(BytesIO(headb))
                    return (u, ct2, size)
                if want_video and (is_video_content_type(ct2) or looks_like_video_url(u)):
                    return (u, ct2, size)
                return None
            except:
                return None

        done = 0

        # B3: 優化進度更新
        with ThreadPoolExecutor(max_workers=VERIFY_WORKERS) as ex:
            futs = [ex.submit(verify_one, u) for u in uniq]
            for fut in as_completed(futs):
                if cancel_ev.is_set():
                    JM.set_status(job_id, "cancelled", "Cancelled.")
                    return

                r = fut.result()
                if r:
                    verified.append(r)
                done += 1

                if done % 5 == 0 or done == len(uniq):
                    JM.set_progress(job_id, done, len(uniq), f"Verifying... ({done}/{len(uniq)})")

        if not verified:
            JM.set_status(job_id, "done", "No media verified (try Ultra).")
            return

        JM.set_progress(job_id, 0, len(verified), "Building thumbnails...")

        out_items: List[MediaItem] = []
        done2 = 0

        def thumb_one(tup: Tuple[str, str, Optional[int]]) -> Optional[MediaItem]:
            u, ct, size = tup
            kind = "video" if (is_video_content_type(ct) or looks_like_video_url(u)) else "image"
            item_id = hash8(u)
            thumb_path = os.path.join(thumbs_dir, f"{item_id}.jpg")

            if kind == "video":
                img = make_placeholder_thumb("video")
                save_thumb(img, thumb_path)
                return MediaItem(id=item_id, url=u, kind="video", ct=ct, fmt="VIDEO", size=size, thumb_path=thumb_path)

            s = get_session()
            if size and size > MAX_THUMB_BYTES:
                img = make_placeholder_thumb("err")
                save_thumb(img, thumb_path)
                return MediaItem(id=item_id, url=u, kind="image", ct=ct, fmt="BIG", size=size, thumb_path=thumb_path)

            try:
                b, headers = get_bytes(s, u, timeout=GET_TIMEOUT)
                img = make_image_thumb_from_bytes(b)
                save_thumb(img, thumb_path)

                try:
                    im = Image.open(BytesIO(b))
                    w, h = im.size
                    fmt = (im.format or "").upper()
                except:
                    w, h, fmt = 0, 0, ""

                return MediaItem(id=item_id, url=u, kind="image", ct=ct, w=w, h=h, fmt=fmt, size=size, thumb_path=thumb_path)
            except:
                img = make_placeholder_thumb("err")
                save_thumb(img, thumb_path)
                return MediaItem(id=item_id, url=u, kind="image", ct=ct, fmt="ERR", size=size, thumb_path=thumb_path)

        # B3: 優化縮圖進度更新
        with ThreadPoolExecutor(max_workers=THUMB_WORKERS) as ex:
            futs = [ex.submit(thumb_one, v) for v in verified]
            for fut in as_completed(futs):
                if cancel_ev.is_set():
                    JM.set_status(job_id, "cancelled", "Cancelled.")
                    return

                it = fut.result()
                done2 += 1

                if done2 % 3 == 0 or done2 == len(verified):
                    JM.set_progress(job_id, done2, len(verified), f"Thumb... ({done2}/{len(verified)})")

                if not it:
                    continue
                if it.kind == "image" and it.w and it.h:
                    if it.w < min_w or it.h < min_h:
                        continue
                out_items.append(it)

        out_items.sort(key=lambda x: (0 if x.kind == "image" else 1, (x.w * x.h) if x.w and x.h else 0), reverse=True)

        JM.add_items(job_id, out_items)
        JM.set_status(job_id, "done", f"Done. {len(out_items)} items. (net={len(net_candidates)})")

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[scan_worker] Error: {error_detail}")
        JM.set_status(job_id, "error", f"Error: {str(e)[:200]}")
    # ↑↑↑ D3 完 ↑↑↑

# ----------------- Download Engines -----------------
def download_builtin(urls: List[str], dest_dir: str) -> Dict[str, Any]:
    s = get_session()
    ok = 0
    fail = 0
    os.makedirs(dest_dir, exist_ok=True)

    for u in urls:
        try:
            host = safe_name(urlparse(u).netloc)
            outdir = os.path.join(dest_dir, host)
            os.makedirs(outdir, exist_ok=True)

            base = safe_name(os.path.basename(urlparse(u).path) or "")
            if not base:
                base = f"{host}_{hash8(u)}"
            else:
                base = os.path.splitext(base)[0] or f"{host}_{hash8(u)}"

            part = os.path.join(outdir, base + ".part")
            final = os.path.join(outdir, base)

            with s.get(u, stream=True, timeout=DOWNLOAD_TIMEOUT, allow_redirects=True) as r:
                r.raise_for_status()
                ct = r.headers.get("Content-Type", "")

                ext = "bin"
                if is_image_content_type(ct):
                    ext = "jpg" if "jpeg" in ct.lower() else ct.split("/")[1].split(";")[0].strip().lower()
                elif is_video_content_type(ct):
                    ext = ct.split("/")[1].split(";")[0].strip().lower()
                elif looks_like_image_url(u) or looks_like_video_url(u):
                    ext = os.path.splitext(u.split("?")[0])[1].lstrip(".") or "bin"

                final_path = final + "." + ext
                k = 1
                while os.path.exists(final_path):
                    final_path = os.path.join(outdir, f"{base}_{k}.{ext}")
                    k += 1

                with open(part, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)

                os.replace(part, final_path)
            ok += 1
        except:
            fail += 1

    return {"ok": ok, "fail": fail}

def download_gallery_dl(urls: List[str], dest_dir: str) -> Dict[str, Any]:
    cmd = get_gdl_command()
    if not cmd:
        return {"ok": 0, "fail": len(urls), "error": "gallery-dl not available"}

    os.makedirs(dest_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as f:
        path = f.name
        for u in urls:
            f.write(u.strip() + "\n")

    try:
        code, out = run_gallery_dl(["--input-file", path, "--directory", dest_dir], timeout_sec=60 * 30)
        if code == 0:
            return {"ok": len(urls), "fail": 0}
        return {"ok": 0, "fail": len(urls), "error": out}
    finally:
        try:
            os.remove(path)
        except:
            pass

def download_ytdlp(urls: List[str], dest_dir: str) -> Dict[str, Any]:
    cmd = get_ytdlp_command()
    if not cmd:
        return {"ok": 0, "fail": len(urls), "error": "yt-dlp not available"}

    os.makedirs(dest_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as f:
        path = f.name
        for u in urls:
            f.write(u.strip() + "\n")

    try:
        code, out = run_ytdlp(["--batch-file", path, "--paths", dest_dir], timeout_sec=60 * 30)
        if code == 0:
            return {"ok": len(urls), "fail": 0}
        return {"ok": 0, "fail": len(urls), "error": out}
    finally:
        try:
            os.remove(path)
        except:
            pass

def gdl_direct_worker(job_id: str, url: str, dest_dir: str):
    cancel_ev = JM.cancel[job_id]
    cmd = get_gdl_command()
    if not cmd:
        JM.set_status(job_id, "error", "gallery-dl not available")
        return

    JM.set_status(job_id, "running", "gallery-dl downloading...")
    JM.set_progress(job_id, 0, 1, "gallery-dl running...")

    code, out = run_gallery_dl(["--directory", dest_dir, url], timeout_sec=60 * 60)

    if cancel_ev.is_set():
        JM.set_status(job_id, "cancelled", "Cancelled")
        return

    if code == 0:
        JM.set_status(job_id, "done", "gallery-dl done")
    else:
        JM.set_status(job_id, "error", f"gallery-dl failed: {out[:800]}")

def ytdlp_direct_worker(job_id: str, url: str, dest_dir: str):
    cancel_ev = JM.cancel[job_id]
    cmd = get_ytdlp_command()
    if not cmd:
        JM.set_status(job_id, "error", "yt-dlp not available")
        return

    JM.set_status(job_id, "running", "yt-dlp downloading...")
    JM.set_progress(job_id, 0, 1, "yt-dlp running...")

    # 最簡單版本（恢復原版）
    code, out = run_ytdlp(["--paths", dest_dir, url], timeout_sec=60 * 60)

    if cancel_ev.is_set():
        JM.set_status(job_id, "cancelled", "Cancelled")
        return

    if code == 0:
        JM.set_status(job_id, "done", "yt-dlp done")
    else:
        JM.set_status(job_id, "error", f"yt-dlp failed: {out[:800]}")
# ----------------- API -----------------
app = FastAPI(title=APP_NAME)

@app.get("/api/tools/status")
def api_tools_status():
    """檢查 gallery-dl 和 yt-dlp 的狀態"""
    gdl_ok, gdl_ver = get_gdl_version()
    ytdlp_ok, ytdlp_ver = get_ytdlp_version()
    
    # 檢查更新
    gdl_has_update, gdl_latest = check_tool_update("gallery-dl") if gdl_ok else (False, "")
    ytdlp_has_update, ytdlp_latest = check_tool_update("yt-dlp") if ytdlp_ok else (False, "")
    
    return {
        "platform": get_platform_type(),
        "gallery_dl": {
            "available": gdl_ok,
            "version": gdl_ver if gdl_ok else None,
            "error": gdl_ver if not gdl_ok else None,
            "has_update": gdl_has_update,
            "latest_version": gdl_latest if gdl_has_update else None
        },
        "yt_dlp": {
            "available": ytdlp_ok,
            "version": ytdlp_ver if ytdlp_ok else None,
            "error": ytdlp_ver if not ytdlp_ok else None,
            "has_update": ytdlp_has_update,
            "latest_version": ytdlp_latest if ytdlp_has_update else None
        }
    }

@app.post("/api/tools/update/{tool}")
def api_tools_update(tool: str):
    """更新工具 (僅 Linux 支援自動更新)"""
    if tool not in ["gallery-dl", "yt-dlp"]:
        raise HTTPException(400, "Invalid tool")
    
    if get_platform_type() == "windows":
        return {"ok": False, "message": "Windows 請手動下載更新"}
    elif get_platform_type() == "macos":
        return {"ok": False, "message": "macOS 不支援"}
    
    # Linux 自動更新
    ok, msg = update_tool_linux(tool)
    return {"ok": ok, "message": msg}

@app.get("/api/appinfo")
def appinfo():
    cfg = load_config()
    pt = get_platform_type()
    gdl_ok, gdl_msg = get_gdl_version()
    return {
        "app": APP_NAME,
        "data_dir": APP_DATA,
        "has_login_profile": os.path.exists(PROFILE_DIR),
        "config": cfg,
        "platform": pt,
        "gallery_dl_available": gdl_ok,
        "gallery_dl_info": gdl_msg
    }

@app.post("/api/config")
def set_config(payload: dict):
    cfg = load_config()
    cfg.update(payload or {})
    save_config(cfg)
    return {"ok": True, "config": cfg}

@app.post("/api/set_dest_dir")
def set_dest_dir(payload: dict):
    path = (payload or {}).get("path", "").strip()
    if not path:
        raise HTTPException(400, "path required")
    cfg = load_config()
    cfg["dest_dir"] = path
    save_config(cfg)
    return {"ok": True, "dest_dir": path}

# ↓↓↓ C2: 移除重複 API ↓↓↓
@app.get("/api/gdl_status")
def gdl_status():
    """檢查 gallery-dl 版本"""
    ok, msg = get_gdl_version()
    return {"ok": ok, "message": msg}
# ↑↑↑ C2 完（已刪除 gallery_dl_version）↑↑↑

@app.post("/api/gallery-dl/update")
def gallery_dl_update():
    """Linux only: auto-update gallery-dl"""
    ok, msg = update_gdl_linux()
    return {"ok": ok, "message": msg}
@app.post("/api/login/clear")
def clear_login():
    if os.path.exists(PROFILE_DIR):
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    return {"ok": True, "message": "Login profile cleared."}

@app.post("/api/scan")
def scan(payload: dict):
    url = (payload or {}).get("url", "").strip()
    if not url:
        raise HTTPException(400, "url required")

    ultra = bool((payload or {}).get("ultra", False))
    use_login_profile = bool((payload or {}).get("use_login_profile", False))
    debug_browser = bool((payload or {}).get("debug_browser", False))
    min_w = int((payload or {}).get("min_w", 0) or 0)
    min_h = int((payload or {}).get("min_h", 0) or 0)
    want_image = bool((payload or {}).get("want_image", True))
    want_video = bool((payload or {}).get("want_video", True))
    blacklist = (payload or {}).get("blacklist", ",".join(DEFAULT_BLACKLIST))

    job_id = JM.new_job(job_type="scan")
    t = threading.Thread(
        target=scan_worker,
        args=(job_id, url, ultra, use_login_profile, debug_browser, min_w, min_h, want_image, want_video, blacklist),
        daemon=True
    )
    t.start()
    return {"job_id": job_id}

@app.post("/api/gdl_direct")
def gdl_direct(payload: dict):
    url = (payload or {}).get("url", "").strip()
    if not url:
        raise HTTPException(400, "url required")

    dest_dir = (payload or {}).get("dest_dir", "").strip()
    if not dest_dir:
        dest_dir = load_config().get("dest_dir", DEFAULT_DOWNLOAD_DIR)

    cmd = get_gdl_command()
    if not cmd:
        raise HTTPException(400, "gallery-dl not available")

    job_id = JM.new_job(job_type="gdl_direct")
    t = threading.Thread(target=gdl_direct_worker, args=(job_id, url, dest_dir), daemon=True)
    t.start()
    return {"job_id": job_id}

@app.post("/api/ytdlp/direct")
def ytdlp_direct(payload: dict):
    """yt-dlp 直接下載（不掃描）"""
    url = (payload or {}).get("url", "").strip()
    if not url:
        raise HTTPException(400, "url required")

    dest_dir = (payload or {}).get("dest_dir", "").strip()
    if not dest_dir:
        dest_dir = load_config().get("dest_dir", DEFAULT_DOWNLOAD_DIR)

    cmd = get_ytdlp_command()
    if not cmd:
        raise HTTPException(400, "yt-dlp not available")

    job_id = JM.new_job(job_type="ytdlp_direct")
    t = threading.Thread(target=ytdlp_direct_worker, args=(job_id, url, dest_dir), daemon=True)
    t.start()
    return {"job_id": job_id}

@app.post("/api/stop/{job_id}")
def cancel(job_id: str):
    if job_id not in JM.jobs:
        raise HTTPException(404, "job not found")
    JM.cancel[job_id].set()
    return {"ok": True}

@app.get("/api/status/{job_id}")
def job_status(job_id: str):
    if job_id not in JM.jobs:
        raise HTTPException(404, "job not found")
    return asdict(JM.jobs[job_id])

@app.get("/api/items/{job_id}")
def job_items(job_id: str):
    if job_id not in JM.jobs:
        raise HTTPException(404, "job not found")
    items = JM.items.get(job_id, [])
    return {"items": [asdict(x) for x in items]}

@app.get("/api/thumb/{job_id}/{item_id}.jpg")
def thumb(job_id: str, item_id: str):
    p = os.path.join(JOBS_DIR, job_id, "thumbs", f"{item_id}.jpg")
    if not os.path.exists(p):
        raise HTTPException(404, "thumb not found")
    return FileResponse(p, media_type="image/jpeg")

@app.get("/api/thumb_large/{job_id}/{item_id}.jpg")
def thumb_large(job_id: str, item_id: str):
    """Lightbox large thumbnail (800x800)"""
    p = os.path.join(JOBSDIR, job_id, "thumbs", f"{item_id}_large.jpg")
    if not os.path.exists(p):
        # Fallback to normal thumbnail
        p = os.path.join(JOBSDIR, job_id, "thumbs", f"{item_id}.jpg")
        if not os.path.exists(p):
            raise HTTPException(404, "thumb not found")
    return FileResponse(p, media_type="image/jpeg")

@app.post("/api/download")
def download(payload: dict):
    """下載選取的項目"""
    items_data = (payload or {}).get("items", [])
    engine = (payload or {}).get("engine", "builtin")
    dest_dir = (payload or {}).get("dest_dir", "").strip()

    if not dest_dir:
        dest_dir = load_config().get("dest_dir", DEFAULT_DOWNLOAD_DIR)

    # 支援兩種格式：items (新) 或 urls (舊)
    if items_data:
        urls = [it["url"] for it in items_data if "url" in it]
    else:
        urls = (payload or {}).get("urls") or []

    if not isinstance(urls, list) or not urls:
        raise HTTPException(400, "urls required")

    if engine == "gallery-dl":
        res = download_gallery_dl(urls, dest_dir)
    elif engine == "yt-dlp":
        res = download_ytdlp(urls, dest_dir)
    else:
        res = download_builtin(urls, dest_dir)

    return {"ok": True, "result": res}

app.mount("/ui", StaticFiles(directory=WEB_DIR, html=True), name="web")

def _auto_open_ui():
    time.sleep(1)
    try:
        import webbrowser
        webbrowser.open("http://127.0.0.1:8787/ui/")
    except:
        pass

if __name__ == "__main__":
    auto_install_update_gdl_linux()
    threading.Thread(target=_auto_open_ui, daemon=True).start()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8787, log_level="info")

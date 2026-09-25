#!/usr/bin/env python3
# ==============================================================================
# DRX WINGO CLUSTER - EXECUTION WORKER NODE (ওয়ার্কার কোড)
# ==============================================================================
# Responsibilities:
# - Connects to Firebase RTDB and registers as an active worker terminal
# - Handles browser sessions (Headless Firefox, GeckoDriver, Container isolation)
# - Performs auto-login across 6 platforms, resolves Error 22 auto-takeover
# - Dismisses modals & USDT bonus announcements
# - Executes 24/7 invisible ghost martingale trading engine (WinGo 30S)
# - Photo / Screenshot function REMOVED (Zero screenshot disk I/O or overhead)
# ==============================================================================

import os
import sys
import subprocess
import time
import threading
import shutil
import json
import socket
import gc
import urllib.request
import urllib.error
import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [WORKER] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("WORKER_NODE")

def install_and_import(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
    except ImportError:
        logger.warning(f"Installing missing package: {package_name}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "--upgrade", "--no-cache-dir", package_name
            ])
            logger.info(f"Successfully installed: {package_name}")
        except Exception as e:
            logger.error(f"Pip installation failed for {package_name}: {e}")

install_and_import("selenium")
install_and_import("psutil")

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
import psutil

# ==============================================================================
# WORKER CONFIGURATION & CLUSTER REGISTRY
# ==============================================================================
FIREBASE_RTDB_URL = os.environ.get("FIREBASE_RTDB_URL", "https://x7e77eey-default-rtdb.firebaseio.com")
PREDICTION_API_URL = os.environ.get("PREDICTION_API_URL", "https://medieval-pink-yqnjxslo-dp376cefm0gv.edgeone.dev/apipid.json")
HEADLESS_MODE = os.environ.get("HEADLESS", "true").lower() == "true"
NODE_ID = f"worker_{socket.gethostname()}_{os.getpid()}_{uuid.uuid4().hex[:6]}"

PROFILES_BASE_DIR = os.path.expanduser("~/.ff_bot_profiles")
os.makedirs(PROFILES_BASE_DIR, exist_ok=True)

active_sessions = {}
WORKER_ACTIVE = True

PLATFORMS = {
    "site_amarclub": {
        "name": "Amar Club",
        "login": "https://amarclub1.com/#/login",
        "wingo": "https://amarclub1.com/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"
    },
    "site_dkwin": {
        "name": "DK Win",
        "login": "https://dkwin6.com/#/login",
        "wingo": "https://dkwin6.com/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"
    },
    "site_tigroclub": {
        "name": "Tigro Club",
        "login": "https://tigroclub.vip/#/login",
        "wingo": "https://tigroclub.vip/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"
    },
    "site_hgnice": {
        "name": "HG Nice",
        "login": "https://hgnice.org/#/login",
        "wingo": "https://hgnice.org/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"
    },
    "site_kanpur91": {
        "name": "Kanpur 91",
        "login": "https://kanpur91.com/#/login",
        "wingo": "https://kanpur91.com/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"
    },
    "site_bdgwinsvip": {
        "name": "BDG Wins VIP",
        "login": "https://bdgwinsvip.com/#/login",
        "wingo": "https://bdgwinsvip.com/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"
    }
}

# ==============================================================================
# FIREBASE HTTP HELPER
# ==============================================================================
def firebase_sync_http(path: str, method: str = "GET", payload=None, timeout: float = 4.0):
    url = f"{FIREBASE_RTDB_URL.rstrip('/')}/{path.strip('/')}.json"
    raw_data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        raw_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=raw_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_content = response.read()
            if res_content:
                return json.loads(res_content.decode("utf-8"))
            return None
    except Exception:
        return None

def measure_network_latency(url: str, timeout: float = 3.5) -> float:
    try:
        start_ts = time.time()
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response.read(256)
        return round((time.time() - start_ts) * 1000, 2)
    except Exception:
        return 9999.0

def emit_event_to_manager(event_type: str, data: dict):
    ev_id = f"ev_{int(time.time()*1000)}_{uuid.uuid4().hex[:4]}"
    data["type"] = event_type
    data["worker_id"] = NODE_ID
    data["timestamp"] = time.time()
    firebase_sync_http(f"manager_events/{ev_id}", "PUT", data)

# ==============================================================================
# AGGRESSIVE ZOMBIE CLEANUP & MEMORY HYGIENE
# ==============================================================================
def kill_process_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except Exception:
                pass
        gone, still_alive = psutil.wait_procs(children, timeout=2.0)
        for p in still_alive:
            try:
                p.kill()
            except Exception:
                pass
        parent.terminate()
        parent.wait(timeout=2.0)
    except Exception:
        pass

def cleanup_zombie_browsers():
    current_pid = os.getpid()
    try:
        for proc in psutil.process_iter(['pid', 'name', 'ppid']):
            try:
                pname = (proc.info['name'] or '').lower()
                if 'firefox' in pname or 'geckodriver' in pname:
                    if proc.info['ppid'] == 1 or proc.info['ppid'] == current_pid:
                        is_active = False
                        for s in list(active_sessions.values()):
                            d = s.get('driver')
                            if d and hasattr(d, 'service') and d.service and hasattr(d.service, 'process'):
                                if d.service.process and d.service.process.pid == proc.info['pid']:
                                    is_active = True
                                    break
                        if not is_active:
                            try:
                                proc.kill()
                            except Exception:
                                pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

# ==============================================================================
# HARDENED BROWSER ALLOCATION
# ==============================================================================
def allocate_session_tab(session_id, target_url):
    sess = active_sessions.get(session_id)
    if not sess:
        raise Exception("Session data not found.")

    cleanup_zombie_browsers()

    profile_dir = os.path.join(PROFILES_BASE_DIR, f"profile_{session_id}")
    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir, ignore_errors=True)
    os.makedirs(profile_dir, exist_ok=True)

    options = Options()
    if HEADLESS_MODE:
        options.add_argument("--headless")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--width=412")
    options.add_argument("--height=915")
    options.page_load_strategy = 'eager'
    options.add_argument("-profile")
    options.add_argument(profile_dir)

    # Railway 512MB Strict Low-RAM Tuning (Anti-Freeze & Anti-OOM)
    options.set_preference("dom.ipc.processCount", 1)  # Only 1 content process (cuts Firefox RAM by 60%)
    options.set_preference("browser.sessionhistory.max_entries", 2)
    options.set_preference("browser.sessionhistory.max_total_viewers", 0)
    options.set_preference("image.mem.surfacecache.max_size_kb", 1024)
    options.set_preference("javascript.options.mem.max", 32768)
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", True)
    options.set_preference("network.http.use-cache", False)
    options.set_preference("network.prefetch-next", False)
    options.set_preference("webgl.disabled", True)
    options.set_preference("accessibility.force_disabled", 1)
    options.set_preference("toolkit.telemetry.enabled", False)
    options.set_preference("dom.disable_open_during_load", True)
    options.set_preference("dom.popup_maximum", 0)
    options.set_preference("media.peerconnection.enabled", False)
    options.set_preference("media.navigator.enabled", False)

    service = FirefoxService(log_output=os.devnull)
    driver = webdriver.Firefox(service=service, options=options)

    driver.set_page_load_timeout(35)
    driver.set_script_timeout(20)
    driver.implicitly_wait(3)
    driver.set_window_size(412, 915)

    try:
        driver.get(target_url)
    except Exception as e:
        logger.warning(f"Initial get timeout/warning for {target_url}: {e}")

    sess["driver"] = driver
    sess["window_handle"] = driver.current_window_handle
    sess["last_activity"] = time.time()
    return driver, sess["window_handle"]

def safe_tab_execute(sid, task_fn, timeout=25.0):
    sess = active_sessions.get(sid)
    if not sess:
        return None

    lock = sess.get("lock")
    driver = sess.get("driver")

    if not driver or not lock:
        return None

    acquired = lock.acquire(timeout=6.0)
    if not acquired:
        return None

    result_container = {"res": None, "error": None, "completed": False}

    def execute_worker():
        try:
            result_container["res"] = task_fn(driver)
            result_container["completed"] = True
            sess["last_activity"] = time.time()
        except Exception as e:
            result_container["error"] = e

    worker_thread = threading.Thread(target=execute_worker, daemon=True)
    worker_thread.start()
    worker_thread.join(timeout=timeout)

    if not result_container["completed"]:
        try:
            lock.release()
        except RuntimeError:
            pass
        logger.error(f"Tab execution timed out on sid: {sid}. Triggering restart...")
        threading.Thread(target=close_session_tab, args=(sid,), daemon=True).start()
        return None

    try:
        lock.release()
    except RuntimeError:
        pass

    gc.collect()

    if result_container["error"]:
        err_msg = str(result_container["error"])
        if "unexpectedly closed" in err_msg or "Tried to run command without establishing a connection" in err_msg:
            logger.error(f"Driver severed connection (Status 0): {err_msg}")
        return None

    return result_container["res"]

def close_session_tab(session_id):
    sess = active_sessions.pop(session_id, None)
    if sess:
        sess["is_trading"] = False
        driver = sess.get("driver")
        if driver:
            try:
                driver.execute_script("if(window.__WINGO_ST && window.__WINGO_ST.autoInt) clearInterval(window.__WINGO_ST.autoInt);")
            except Exception:
                pass
            try:
                driver.quit()
            except Exception:
                pass
            try:
                if hasattr(driver, 'service') and driver.service and driver.service.process:
                    kill_process_tree(driver.service.process.pid)
            except Exception:
                pass

        profile_dir = os.path.join(PROFILES_BASE_DIR, f"profile_{session_id}")
        if os.path.exists(profile_dir):
            shutil.rmtree(profile_dir, ignore_errors=True)

    cleanup_zombie_browsers()
    gc.collect()

# ==============================================================================
# JAVASCRIPT INJECTION SCRIPTS (POPUP DISMISSER, LOGIN & WINGO)
# ==============================================================================
MODAL_AUTO_DISMISSER_JS = """
(function(){
    const sweepModals = () => {
        const targetBonusDialogs = document.querySelectorAll('.announcement-box, .dialog-box, .bonus-dialog, .van-popup, .van-dialog');
        targetBonusDialogs.forEach(dialog => {
            const txt = (dialog.innerText || '').toLowerCase();
            if (txt.includes('announcement') || txt.includes('bonus') || txt.includes('usdt') || txt.includes('notice') || txt.includes('welcome')) {
                const confBtn = dialog.querySelector('button, .van-button, .van-dialog__confirm, div[role="button"]');
                if (confBtn) {
                    try { confBtn.click(); } catch(e){}
                }
                try { dialog.remove(); } catch(e){}
            }
        });

        const directSelectors = [
            '.van-dialog__confirm', '.dialog-confirm', '.van-button--primary',
            '.van-popup__close-icon', '.van-overlay', '.dialog-close', '.close-btn',
            'button[class*="close" i]', 'button[class*="confirm" i]', 'div[class*="close" i]',
            '.announcement-box .close', '.modal-mask', '.reward-receive-btn',
            'button.van-dialog__cancel', '.van-button--danger'
        ];
        directSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                if (el && el.offsetParent !== null && !el.closest('#sys-core-fin')) {
                    try { 
                        ['pointerdown','mousedown','mouseup','click'].forEach(evt => {
                            el.dispatchEvent(new MouseEvent(evt, {bubbles:true, cancelable:true, view:window}));
                        });
                        el.click(); 
                    } catch(e){}
                }
            });
        });

        const clickableNodes = document.querySelectorAll('button, div[role="button"], span, p, a');
        clickableNodes.forEach(node => {
            if (node && node.offsetParent !== null && !node.closest('#sys-core-fin')) {
                const txt = (node.innerText || '').trim().toLowerCase();
                if (txt === 'confirm' || txt === 'receive' || txt === 'got it' || txt === '確定' || txt === 'close' || txt === 'ok') {
                    try { node.click(); } catch(e){}
                }
            }
        });

        document.querySelectorAll('.van-overlay, .van-dialog, .modal-backdrop').forEach(overlay => {
            if (overlay && overlay.offsetParent !== null && !overlay.closest('#sys-core-fin')) {
                try { overlay.remove(); } catch(e){}
            }
        });
    };

    sweepModals();
    if (!window.__SWEEPER_INTERVAL) {
        window.__SWEEPER_INTERVAL = setInterval(sweepModals, 600);
    }
})();
"""

AUTO_FILL_AND_CLICK_JS = """
const phone = arguments[0];
const pass = arguments[1];

if (!window.location.hash.includes('login')) {
    window.location.hash = '#/login';
}

const dismissInitial = () => {
    document.querySelectorAll('.van-dialog__confirm, .dialog-confirm, button[class*="confirm" i], .van-button--primary, .van-popup__close-icon').forEach(btn => {
        try { btn.click(); } catch(e){}
    });
};
dismissInitial();

let elN = document.querySelector('input[type="tel"], input[placeholder*="phone" i], input[placeholder*="Phone" i]') || 
          document.querySelector('body > div > div:nth-of-type(2) > div:nth-of-type(4) > div > div > div > div:nth-of-type(2) > input');

let elP = document.querySelector('input[type="password"]') || 
          document.querySelector('body > div > div:nth-of-type(2) > div:nth-of-type(4) > div > div > div:nth-of-type(2) > div:nth-of-type(2) > input');

let elL = document.querySelector('button[type="submit"]') || 
          document.querySelector('body > div > div:nth-of-type(2) > div:nth-of-type(4) > div > div > div:nth-of-type(4) > button');

if (!elN || !elP || !elL) {
    return "NOT_READY";
}

const clearAndSet = (el, val) => {
    el.focus();
    el.value = '';
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
    if (setter) {
        setter.call(el, val);
    } else {
        el.value = val;
    }
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
};

clearAndSet(elN, phone);

setTimeout(() => {
    clearAndSet(elP, pass);
    setTimeout(() => {
        ['pointerdown','mousedown','mouseup','click'].forEach(evt => {
            try { elL.dispatchEvent(new MouseEvent(evt, {bubbles:true, cancelable:true, view:window})); } catch(e){}
        });
        elL.click();
    }, 500);
}, 500);

return "SUCCESS";
"""

CHECK_LOGIN_STATUS_JS = """
const hash = window.location.hash || '';
const href = window.location.href || '';
const dialog = document.querySelector('.van-dialog');
if (dialog) {
    const dText = dialog.innerText || '';
    if (dText.includes('already logged in') || dText.includes('somewhere else') || 
        dText.includes('logged in') || dText.includes('22') || dText.includes('other device') ||
        dText.includes('Confirm') || dText.includes('Determine') || dText.includes('continue')) {
        const confirmBtn = dialog.querySelector('.van-dialog__confirm, button[class*="confirm" i], .van-button--danger, .van-button--primary, button');
        if (confirmBtn) {
            try { confirmBtn.click(); } catch(e){}
            return { status: "CONFIRM_CLICKED", message: "Auto-confirmed device prompt" };
        }
    }
}

document.querySelectorAll('.van-dialog__confirm, .dialog-confirm, button[class*="confirm" i], button[class*="close" i], .van-popup__close-icon').forEach(b => {
    try { b.click(); } catch(e){}
});

try {
    const t1 = localStorage.getItem('token') || localStorage.getItem('token_str') || localStorage.getItem('auth');
    const t2 = sessionStorage.getItem('token') || sessionStorage.getItem('auth');
    if (t1 || t2) return { status: "SUCCESS" };
} catch(e){}

if (!href.includes('/login') && (!hash.includes('login') || hash.length > 8)) {
    return { status: "SUCCESS" };
}

const toast = document.querySelector('.van-toast--text, .van-toast--fail, .van-toast');
if (toast && toast.innerText && toast.innerText.trim().length > 0) {
    const t = toast.innerText.trim();
    if (t.includes('already logged in') || t.includes('somewhere else') || t.includes('22')) {
        const loginBtn = document.querySelector('button[type="submit"], body > div > div:nth-of-type(2) > div:nth-of-type(4) > div > div > div:nth-of-type(4) > button');
        if (loginBtn) {
            try { loginBtn.click(); } catch(e){}
        }
        return { status: "PENDING", message: "Handling session takeover..." };
    }
    if (t.includes('password') || t.includes('incorrect') || t.includes('wrong') || t.includes('Account does not exist') || t.includes('frozen')) {
        return { status: "ERROR", message: t };
    }
}

return { status: "PENDING" };
"""

WINGO_PERSISTENT_NAV_JS = """
const targetUrl = arguments[0];

(function(){
    document.querySelectorAll('.announcement-box, .bonus-dialog, .van-overlay, .van-dialog').forEach(el => {
        try {
            const btn = el.querySelector('button, .van-button--primary');
            if (btn) btn.click();
            el.remove();
        } catch(e){}
    });

    const currentHash = window.location.hash || '';
    const currentHref = window.location.href || '';
    const bodyTxt = document.body ? document.body.innerText : '';

    if (currentHash.includes('WinGo') || currentHref.includes('WinGo') || bodyTxt.includes('Time remaining') || bodyTxt.includes('30S') || bodyTxt.includes('Win Go')) {
        return "ALREADY_VERIFIED";
    }

    try {
        if (!window.location.href.includes('WinGo')) {
            window.location.href = targetUrl;
        }
    } catch(e){}

    const s = [
        'img[src*="wingo" i]', 'img[alt*="wingo" i]',
        'body > div > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(7) > div:nth-of-type(3) > div > div:nth-of-type(2) > div > div > div > img',
        'body > div > div:nth-of-type(3) > div:nth-of-type(5) > div:nth-of-type(2) > div:nth-of-type(3) > div > div > div > img',
        'body > div > div:nth-of-type(2) > div:nth-of-type(5) > div:nth-of-type(2) > div > div',
        'div[class*="lottery" i]', 'div[class*="wingo" i]'
    ];
    for (let i = 0; i < s.length; i++) {
        let el = document.querySelector(s[i]);
        if (el && el.offsetParent !== null) {
            ['pointerdown','mousedown','mouseup','click'].forEach(evt => {
                try { el.dispatchEvent(new MouseEvent(evt, {bubbles:true, cancelable:true, view:window})); } catch(err){}
            });
            try { el.click(); } catch(err){}
            return "CLICKED_SELECTOR";
        }
    }

    return "NAV_INJECTED";
})();
"""

CHECK_WINGO_READY_JS = """
const hash = window.location.hash || '';
const href = window.location.href || '';
const bodyText = document.body ? document.body.innerText : '';

document.querySelectorAll('.van-dialog__confirm, .dialog-close, .van-popup__close-icon, button[class*="close" i], .van-dialog button').forEach(btn => {
    try { btn.click(); } catch(e){}
});

if (hash.includes('WinGo') || href.includes('WinGo') || bodyText.includes('Win Go') || bodyText.includes('30S') || bodyText.includes('Time remaining')) {
    return true;
}
return false;
"""

FETCH_BALANCE_JS = r"""
let els = document.querySelectorAll('*');
for (let i = 0; i < els.length; i++) {
    let txt = els[i].innerText || '';
    if (txt.includes('Wallet balance') || txt.includes('Balance')) {
        let parentTxt = (els[i].parentNode && els[i].parentNode.innerText) ? els[i].parentNode.innerText : '';
        let match = parentTxt.match(/[৳₹$€£]\s*([\d,]+\.?\d*)/);
        if (match) return parseFloat(match[1].replace(/,/g, ''));
    }
}
for (let i = 0; i < els.length; i++) {
    let txt = els[i].innerText || '';
    if (txt.trim().match(/^[৳₹$€£]\s*[\d,]+\.?\d*$/)) {
        return parseFloat(txt.replace(/[^\d.]/g, ''));
    }
}
return 0;
"""

WINGO_CORE_JS = r"""
const autoTargetProfit = arguments[0];
const autoTotalSteps = arguments[1];
const predictionApiUrl = arguments[2] || "https://medieval-pink-yqnjxslo-dp376cefm0gv.edgeone.dev/apipid.json";

(function(){
    let ghostContainer = document.getElementById('sys-core-fin');
    if (!ghostContainer) {
        ghostContainer = document.createElement('div');
        ghostContainer.id = 'sys-core-fin';
        ghostContainer.setAttribute('style', 'display: none !important; opacity: 0 !important; pointer-events: none !important; position: fixed !important; top: -9999px !important; left: -9999px !important; width: 0 !important; height: 0 !important; z-index: -9999 !important; overflow: hidden !important;');
        document.body.appendChild(ghostContainer);
    }

    if (window.__WINGO_ST && window.__WINGO_ST.isRun) {
        window.__WINGO_ST.steps = Math.max(1, parseInt(autoTotalSteps) || 5);
        if (autoTargetProfit && autoTargetProfit > 0) {
            let liveBal = (typeof chkBal === 'function') ? chkBal() : window.__WINGO_ST.curBal;
            window.__WINGO_ST.tgtAmt = (autoTargetProfit <= liveBal && liveBal > 0) ? (liveBal + autoTargetProfit) : autoTargetProfit;
        }
        return "ALREADY_RUNNING_UPDATED";
    }

    if (window.__WINGO_ST && window.__WINGO_ST.autoInt) {
        clearInterval(window.__WINGO_ST.autoInt);
    }

    const cfg = { fRt: 300, syncDly: 2500, minSf: 10 };
    const st = {
        isRun: true,
        tgtAmt: 0,
        startBal: 0,
        curBal: 0,
        autoInt: null,
        isTrd: false,
        stpIdx: 0,
        steps: Math.max(1, parseInt(autoTotalSteps) || 5),
        dynSeq: [],
        tradesDone: 0,
        lastPred: null,
        lastPeriod: null,
        w: 0,
        l: 0,
        cur_w_streak: 0,
        cur_l_streak: 0,
        max_w_streak: 0,
        max_l_streak: 0
    };
    window.__WINGO_ST = st;

    function chkBal() {
        try {
            let els = document.querySelectorAll('*');
            for (let i = 0; i < els.length; i++) {
                let txt = els[i].innerText || '';
                if (txt.includes('Wallet balance') || txt.includes('Balance')) {
                    let parentTxt = (els[i].parentNode && els[i].parentNode.innerText) ? els[i].parentNode.innerText : '';
                    let match = parentTxt.match(/[৳₹$€£]\s*([\d,]+\.?\d*)/);
                    if (match) {
                        st.curBal = Math.floor(parseFloat(match[1].replace(/,/g, '')));
                        return st.curBal;
                    }
                }
            }
            for (let i = 0; i < els.length; i++) {
                let txt = els[i].innerText || '';
                if (txt.trim().match(/^[৳₹$€£]\s*[\d,]+\.?\d*$/)) {
                    st.curBal = Math.floor(parseFloat(txt.replace(/[^\d.]/g, '')));
                    return st.curBal;
                }
            }
        } catch(e) {}
        return st.curBal || 0;
    }

    function getRemainingSeconds() {
        try {
            let timeEl = document.querySelector('.time-box, [class*="time" i], .Time');
            if (timeEl) {
                let txt = timeEl.innerText || '';
                let m = txt.match(/(\d+)\s*:\s*(\d+)/);
                if (m) {
                    return (parseInt(m[1]) * 60) + parseInt(m[2]);
                }
            }
        } catch(e){}
        return 30;
    }

    const calcSeq = (cBal, nSteps) => {
        let B = Math.floor(Number(cBal)) || 0;
        let n = parseInt(nSteps) || 5;
        if (n < 1) n = 1;
        let u = Math.pow(2, n) - 1;
        let s1 = Math.floor(B / u);
        if (s1 < 1) s1 = 1;
        let seq = [];
        let sum = 0;
        for (let k = 1; k < n; k++) {
            let sk = Math.floor(s1 * Math.pow(2, k - 1));
            seq.push(sk);
            sum += sk;
        }
        let sn = Math.floor(B - sum);
        seq.push(sn > 0 ? sn : Math.floor(s1 * Math.pow(2, n - 1)));
        return seq;
    };

    const getNextLivePeriod = (str) => {
        let chars = String(str).split('');
        for (let i = chars.length - 1; i >= 0; i--) {
            if (chars[i] !== '9') {
                chars[i] = String.fromCharCode(chars[i].charCodeAt(0) + 1);
                return chars.join('');
            }
            chars[i] = '0';
        }
        return '1' + chars.join('');
    };

    const drx_triggerEvent = (el, etype) => {
        let ev = new Event(etype, { bubbles: true, cancelable: true });
        el.dispatchEvent(ev);
    };

    const drx_simClick = (el) => {
        if (!el) return;
        ['pointerdown', 'mousedown', 'touchstart', 'pointerup', 'mouseup', 'touchend', 'click'].forEach(evt => {
            try {
                el.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
            } catch(e) {}
        });
        if (typeof el.click === 'function') {
            try { el.click(); } catch(e) {}
        }
    };

    const exeTrd = (pred, amt, cb) => {
        try {
            let remSec = getRemainingSeconds();
            if (remSec <= 5 && remSec > 0) {
                if (cb) cb(false);
                return;
            }

            let btn = null;
            let targetText = String(pred).toLowerCase().trim();
            let btns = document.querySelectorAll('button, div, span');
            for (let i = 0; i < btns.length; i++) {
                let t = (btns[i].innerText || '').trim().toLowerCase();
                if (t === targetText && btns[i].offsetParent && !btns[i].children.length) {
                    btn = btns[i];
                    break;
                }
            }
            if (!btn) {
                if (targetText === 'big') btn = document.querySelector('.Betting__C-foot-b, .bet-btn-big, button[class*="big" i]');
                else if (targetText === 'small') btn = document.querySelector('.Betting__C-foot-s, .bet-btn-small, button[class*="small" i]');
                else if (targetText === 'green') btn = document.querySelector('button[class*="green"], div[class*="green"]');
                else if (targetText === 'red') btn = document.querySelector('button[class*="red"], div[class*="red"]');
                else if (targetText === 'violet') btn = document.querySelector('button[class*="violet"], div[class*="violet"]');
            }
            if (!btn) {
                if (cb) cb(false);
                return;
            }
            drx_simClick(btn);

            let checkAttempts = 0;
            let valInterval = setInterval(() => {
                checkAttempts++;
                let inpEl = document.querySelector("input[type='number'], input.van-field__control, .van-stepper__input");
                if (inpEl || checkAttempts > 18) {
                    clearInterval(valInterval);
                    if (inpEl) {
                        inpEl.focus();
                        let setV = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
                        if (setV) setV.call(inpEl, String(amt));
                        else inpEl.value = amt;
                        drx_triggerEvent(inpEl, 'input');
                        drx_triggerEvent(inpEl, 'change');
                        drx_triggerEvent(inpEl, 'blur');
                    }
                    setTimeout(() => {
                        let dEl = document.querySelector('button.bet-amount, button[class*="bet-amount"], .Betting__C-foot-total, .van-button--danger, .van-button--warning, .van-button--primary');
                        if (!dEl) {
                            let docButtons = document.querySelectorAll('button, div[role="button"]');
                            for (let b of docButtons) {
                                let txt = (b.innerText || '').toLowerCase();
                                if ((txt.includes('total amount') || txt.includes('total') || txt.includes('confirm') || txt.includes('bet')) && b.offsetParent) {
                                    dEl = b;
                                    break;
                                }
                            }
                        }
                        if (dEl) {
                            drx_simClick(dEl);
                        }
                        setTimeout(() => {
                            if (cb) cb(true);
                        }, 1800);
                    }, 700);
                }
            }, 180);
        } catch(e) {
            if (cb) cb(false);
        }
    };

    let initialBal = chkBal();
    st.startBal = initialBal;
    st.curBal = initialBal;
    let targetProfitVal = parseFloat(autoTargetProfit) || 0;
    st.tgtAmt = (targetProfitVal <= initialBal && initialBal > 0) ? (initialBal + targetProfitVal) : targetProfitVal;
    st.dynSeq = calcSeq(initialBal > 0 ? initialBal : st.tgtAmt, st.steps);
    st.stpIdx = 0;
    sessionStorage.removeItem('drx_sig');

    let isFetchingApi = false;

    const apiLoopTask = async () => {
        if (!st.isRun || st.isTrd || isFetchingApi) return;
        isFetchingApi = true;

        try {
            chkBal();
            if (st.curBal >= st.tgtAmt && st.curBal > 0) {
                st.isRun = false;
                st.isTrd = false;
                if (st.autoInt) clearInterval(st.autoInt);
                isFetchingApi = false;
                return;
            }

            let ts = Math.floor(Date.now() / 1000);
            let sep = predictionApiUrl.includes('?') ? '&' : '?';
            let fetchUrl = predictionApiUrl + sep + "page=1&ts=" + ts;
            let res = await fetch(fetchUrl);
            let rawJson = await res.json();

            if (rawJson) {
                let nextObj = rawJson.next || (rawJson.data && rawJson.data.next) || null;
                let histArray = rawJson.history || (rawJson.data && rawJson.data.history) || [];

                // Support legacy format if next is not directly on root
                if (!nextObj && Array.isArray(rawJson) && rawJson[0]) {
                    let first = rawJson[0];
                    if (first.next) {
                        nextObj = first.next;
                        histArray = first.history || histArray;
                    } else {
                        histArray = first.history || [];
                        nextObj = {
                            period: histArray[0] ? getNextLivePeriod(String(histArray[0].pid || histArray[0].period)) : '',
                            size: first.size || first.pred || first.prediction || 'BIG'
                        };
                    }
                }

                if (nextObj || (histArray && histArray.length > 0)) {
                    // Extract live period identifier
                    let cSig = '';
                    if (nextObj && nextObj.period) {
                        cSig = String(nextObj.period).trim();
                    } else if (histArray[0]) {
                        let prevPid = String(histArray[0].period || histArray[0].pid || '');
                        cSig = prevPid ? getNextLivePeriod(prevPid) : '';
                    }

                    let sSig = sessionStorage.getItem('drx_sig');

                    if (cSig && cSig !== sSig) {
                        // Check result of previous bet if pending
                        if (st.lastPred && st.lastPred !== 'SKIP' && st.lastPeriod) {
                            let finishedItem = histArray.find(h => String(h.period || h.pid) === String(st.lastPeriod)) || histArray[0];
                            let won = false;

                            if (finishedItem) {
                                let actualSize = '';
                                if (finishedItem.actual_size) {
                                    actualSize = String(finishedItem.actual_size).toUpperCase().trim();
                                } else if (typeof finishedItem.actual === 'number') {
                                    actualSize = finishedItem.actual >= 5 ? 'BIG' : 'SMALL';
                                } else if (finishedItem.actual) {
                                    let actStr = String(finishedItem.actual).toUpperCase().trim();
                                    if (actStr === 'BIG' || actStr === 'SMALL') actualSize = actStr;
                                    else if (!isNaN(parseInt(actStr))) actualSize = parseInt(actStr) >= 5 ? 'BIG' : 'SMALL';
                                }

                                if (finishedItem.status) {
                                    let statStr = String(finishedItem.status).toUpperCase();
                                    if (statStr === 'WIN' && finishedItem.pred && String(finishedItem.pred).toUpperCase() === st.lastPred) {
                                        won = true;
                                    } else if (statStr === 'LOSS' && finishedItem.pred && String(finishedItem.pred).toUpperCase() === st.lastPred) {
                                        won = false;
                                    } else {
                                        won = (st.lastPred === actualSize);
                                    }
                                } else {
                                    won = (st.lastPred === actualSize);
                                }
                            }

                            if (won) {
                                st.w++;
                                st.cur_w_streak++;
                                st.cur_l_streak = 0;
                                if (st.cur_w_streak > st.max_w_streak) st.max_w_streak = st.cur_w_streak;
                                st.stpIdx = 0;
                            } else {
                                st.l++;
                                st.cur_l_streak++;
                                st.cur_w_streak = 0;
                                if (st.cur_l_streak > st.max_l_streak) st.max_l_streak = st.cur_l_streak;
                                st.stpIdx = Math.min(st.stpIdx + 1, st.dynSeq.length - 1);
                            }
                        }

                        st.lastPred = null;
                        st.lastPeriod = cSig;
                        st.isTrd = true;

                        let nBal = chkBal();
                        if (nBal >= st.tgtAmt && nBal > 0) {
                            st.isTrd = false;
                            isFetchingApi = false;
                            return;
                        }

                        st.dynSeq = calcSeq(nBal, st.steps);
                        if (st.stpIdx >= st.dynSeq.length) st.stpIdx = st.dynSeq.length - 1;
                        let tAmt = st.dynSeq[st.stpIdx] || 1;

                        if (nBal < tAmt) {
                            st.stpIdx = 0;
                            st.isTrd = false;
                            isFetchingApi = false;
                            return;
                        }

                        // Determine prediction specifically from "size" field
                        let rawPred = (nextObj && (nextObj.size || nextObj.pred)) ||
                                      rawJson.size ||
                                      rawJson.pred ||
                                      rawJson.prediction ||
                                      'BIG';
                        let prediction = String(rawPred).toUpperCase().trim();

                        setTimeout(() => {
                            if (prediction === 'SKIP') {
                                st.lastPred = null;
                                sessionStorage.setItem('drx_sig', cSig);
                                setTimeout(() => { st.isTrd = false; }, 1000);
                            } else {
                                st.lastPred = prediction;
                                exeTrd(prediction, tAmt, (suc) => {
                                    if (suc) {
                                        sessionStorage.setItem('drx_sig', cSig);
                                        sessionStorage.setItem('drx_p_bal', st.curBal);
                                        st.tradesDone++;
                                    } else {
                                        st.lastPred = null;
                                    }
                                    setTimeout(() => { st.isTrd = false; }, 1000);
                                });
                            }
                        }, 1800);
                    }
                }
            }
        } catch(e) {
            st.isTrd = false;
        }
        isFetchingApi = false;
    };

    let tradeLockTs = 0;
    setInterval(() => {
        if (st.isTrd) {
            if (!tradeLockTs) tradeLockTs = Date.now();
            else if (Date.now() - tradeLockTs > 15000) {
                st.isTrd = false;
                isFetchingApi = false;
                tradeLockTs = 0;
            }
        } else {
            tradeLockTs = 0;
        }
    }, 3000);

    st.autoInt = setInterval(apiLoopTask, 1000);
    return "GHOST_TRADING_INITIATED";
})();
"""

# ==============================================================================
# WORKER EXECUTION PIPELINE (PHOTO/SCREENSHOT REMOVED)
# ==============================================================================
def execute_worker_login(chat_id, sid, phone, password, login_url, site_name, anim_msg_id=None):
    logger.info(f"Worker executing login for session {sid} on {site_name}...")
    try:
        driver, handle = allocate_session_tab(sid, login_url)
        safe_tab_execute(sid, lambda drv: drv.execute_script(MODAL_AUTO_DISMISSER_JS))
    except Exception as e:
        emit_event_to_manager("LOGIN_FAILED", {
            "session_id": sid,
            "chat_id": chat_id,
            "site_name": site_name,
            "anim_msg_id": anim_msg_id,
            "reason": str(e)
        })
        close_session_tab(sid)
        return

    fill_ok = False
    for _ in range(70):
        res = safe_tab_execute(sid, lambda drv: drv.execute_script(AUTO_FILL_AND_CLICK_JS, phone, password))
        if res == "SUCCESS":
            fill_ok = True
            time.sleep(2.0)
            break
        time.sleep(0.4)

    if not fill_ok:
        emit_event_to_manager("LOGIN_FAILED", {
            "session_id": sid,
            "chat_id": chat_id,
            "site_name": site_name,
            "anim_msg_id": anim_msg_id,
            "reason": "Login form elements not accessible"
        })
        close_session_tab(sid)
        return

    login_status = "PENDING"
    err_detail = ""
    for _ in range(40):
        res = safe_tab_execute(sid, lambda drv: drv.execute_script(CHECK_LOGIN_STATUS_JS))
        if isinstance(res, dict):
            if res.get("status") == "SUCCESS":
                login_status = "SUCCESS"
                break
            elif res.get("status") == "CONFIRM_CLICKED":
                time.sleep(1.5)
                continue
            elif res.get("status") == "ERROR":
                login_status = "ERROR"
                err_detail = res.get("message", "Invalid credentials")
                break
        time.sleep(0.5)

    if safe_tab_execute(sid, lambda drv: drv.execute_script("return !!(localStorage.getItem('token') || sessionStorage.getItem('token'));")):
        login_status = "SUCCESS"

    if login_status == "ERROR":
        close_session_tab(sid)
        emit_event_to_manager("LOGIN_FAILED", {
            "session_id": sid,
            "chat_id": chat_id,
            "site_name": site_name,
            "anim_msg_id": anim_msg_id,
            "reason": err_detail
        })
        return

    # Sweep USDT bonus popups immediately
    safe_tab_execute(sid, lambda drv: drv.execute_script(MODAL_AUTO_DISMISSER_JS))
    time.sleep(1.5)

    # Note: Photo/Screenshot taking completely removed here!
    # Directly report successful login to manager node
    emit_event_to_manager("LOGIN_SUCCESS", {
        "session_id": sid,
        "chat_id": chat_id,
        "site_name": site_name,
        "phone": phone,
        "anim_msg_id": anim_msg_id
    })

def execute_worker_prepare_wingo(chat_id, sid, wingo_url, site_name):
    logger.info(f"Worker preparing WinGo market for session {sid}...")
    verified = False
    for _ in range(15):
        safe_tab_execute(sid, lambda drv: drv.execute_script(MODAL_AUTO_DISMISSER_JS))
        safe_tab_execute(sid, lambda drv: drv.execute_script(WINGO_PERSISTENT_NAV_JS, wingo_url))
        time.sleep(2.0)

        is_ready = safe_tab_execute(sid, lambda drv: drv.execute_script(CHECK_WINGO_READY_JS))
        if is_ready:
            verified = True
            break
        time.sleep(1.0)

    if not verified:
        safe_tab_execute(sid, lambda drv: drv.get(wingo_url))
        time.sleep(3.0)
        safe_tab_execute(sid, lambda drv: drv.execute_script(MODAL_AUTO_DISMISSER_JS))

    current_bal = 0.0
    for _ in range(15):
        bal = safe_tab_execute(sid, lambda drv: drv.execute_script(FETCH_BALANCE_JS))
        if bal and float(bal) > 0:
            current_bal = float(bal)
            break
        time.sleep(0.4)

    if sid in active_sessions:
        active_sessions[sid]["current_balance"] = current_bal

    safe_tab_execute(sid, lambda drv: drv.execute_script(MODAL_AUTO_DISMISSER_JS))

    # Note: Photo/Screenshot taking completely removed here!
    emit_event_to_manager("WINGO_READY", {
        "session_id": sid,
        "chat_id": chat_id,
        "site_name": site_name,
        "live_balance": current_bal
    })

def worker_monitor_trading_loop(chat_id, sid, site_name):
    while True:
        sess = active_sessions.get(sid)
        if not sess or not sess.get("is_trading"):
            break

        def _get_st(drv):
            return drv.execute_script("""
                if (window.__WINGO_ST) {
                    return {
                        isRun: window.__WINGO_ST.isRun,
                        curBal: window.__WINGO_ST.curBal || 0,
                        tgtAmt: window.__WINGO_ST.tgtAmt || 0,
                        startBal: window.__WINGO_ST.startBal || 0,
                        w: window.__WINGO_ST.w || 0,
                        l: window.__WINGO_ST.l || 0,
                        step: (window.__WINGO_ST.stpIdx || 0) + 1,
                        tradesDone: window.__WINGO_ST.tradesDone || 0
                    };
                }
                return null;
            """)

        js_data = safe_tab_execute(sid, _get_st)

        if js_data:
            sess["cur_bal"] = js_data.get("curBal", sess.get("cur_bal", 0))
            sess["wins"] = js_data.get("w", 0)
            sess["losses"] = js_data.get("l", 0)
            tgt_amt = js_data.get("tgtAmt", 0)
            start_b = sess.get("start_bal", 0)
            is_run = js_data.get("isRun", False)

            # Record status in Firebase
            task_payload = {
                "chat_id": chat_id,
                "session_id": sid,
                "site_name": site_name,
                "status": "RUNNING" if is_run else "PAUSED",
                "start_balance": start_b,
                "current_balance": sess["cur_bal"],
                "target_amount": tgt_amt,
                "wins": sess["wins"],
                "losses": sess["losses"],
                "updated_at": time.time()
            }
            firebase_sync_http(f"user_tasks/{chat_id}/{sid}", "PUT", task_payload)

            if not is_run or (sess["cur_bal"] >= tgt_amt and tgt_amt > 0 and sess["cur_bal"] > 0):
                if sess["cur_bal"] >= tgt_amt and tgt_amt > 0 and sess["cur_bal"] > 0:
                    sess["is_trading"] = False
                    task_payload["status"] = "COMPLETED"
                    firebase_sync_http(f"user_tasks/{chat_id}/{sid}", "PUT", task_payload)

                    emit_event_to_manager("TARGET_ACHIEVED", {
                        "session_id": sid,
                        "chat_id": chat_id,
                        "site_name": site_name,
                        "start_balance": start_b,
                        "final_balance": sess["cur_bal"],
                        "wins": sess["wins"],
                        "losses": sess["losses"]
                    })
                    break
                elif not is_run:
                    sess["is_trading"] = False
                    break

        time.sleep(4.0)

# ==============================================================================
# WORKER TASK AND ACTION LISTENER LOOP
# ==============================================================================
def worker_task_listener():
    logger.info(f"Worker task polling initiated on node: {NODE_ID}...")
    while WORKER_ACTIVE:
        try:
            task = firebase_sync_http(f"terminals/{NODE_ID}/task", "GET")
            if task and isinstance(task, dict):
                firebase_sync_http(f"terminals/{NODE_ID}/task", "DELETE")
                t_type = task.get("type")

                if t_type == "LOGIN_AND_PREPARE":
                    sid = task["session_id"]
                    chat_id = task["chat_id"]
                    site_name = task.get("site_name", "Amar Club")
                    login_url = task["login_url"]
                    wingo_url = task["wingo_url"]
                    phone = task["phone"]
                    password = task["password"]

                    active_sessions[sid] = {
                        "chat_id": chat_id,
                        "session_id": sid,
                        "site_name": site_name,
                        "login_url": login_url,
                        "wingo_url": wingo_url,
                        "phone": phone,
                        "password": password,
                        "is_trading": False,
                        "created_at": time.time(),
                        "last_activity": time.time(),
                        "lock": threading.RLock()
                    }

                    anim_msg_id = task.get("anim_msg_id")
                    threading.Thread(
                        target=execute_worker_login,
                        args=(chat_id, sid, phone, password, login_url, site_name, anim_msg_id),
                        daemon=True
                    ).start()

            action_pkt = firebase_sync_http(f"terminals/{NODE_ID}/action", "GET")
            if action_pkt and isinstance(action_pkt, dict):
                firebase_sync_http(f"terminals/{NODE_ID}/action", "DELETE")
                kind = action_pkt.get("kind")
                sid = action_pkt.get("session_id")
                chat_id = action_pkt.get("chat_id")

                if kind == "PREPARE_WINGO" and sid in active_sessions:
                    sess = active_sessions[sid]
                    threading.Thread(
                        target=execute_worker_prepare_wingo,
                        args=(chat_id, sid, sess["wingo_url"], sess["site_name"]),
                        daemon=True
                    ).start()

                elif kind == "START_TRADING" and sid in active_sessions:
                    sess = active_sessions[sid]
                    target_profit = action_pkt.get("target_profit", 0)
                    total_steps = action_pkt.get("total_steps", 5)
                    pred_url = action_pkt.get("prediction_api_url") or PREDICTION_API_URL
                    sess["is_trading"] = True
                    sess["target_profit"] = target_profit
                    sess["total_steps"] = total_steps
                    safe_tab_execute(sid, lambda drv: drv.execute_script(WINGO_CORE_JS, target_profit, total_steps, pred_url))

                    cur_b = sess.get("current_balance", 0.0)
                    sess["start_bal"] = cur_b
                    threading.Thread(
                        target=worker_monitor_trading_loop,
                        args=(chat_id, sid, sess["site_name"]),
                        daemon=True
                    ).start()

                elif kind == "REQUEST_TELEMETRY" and sid in active_sessions:
                    sess = active_sessions[sid]
                    def _tel(drv):
                        return drv.execute_script("""
                            if (window.__WINGO_ST) {
                                return {
                                    curBal: window.__WINGO_ST.curBal || 0,
                                    tgtAmt: window.__WINGO_ST.tgtAmt || 0,
                                    w: window.__WINGO_ST.w || 0,
                                    l: window.__WINGO_ST.l || 0,
                                    step: (window.__WINGO_ST.stpIdx || 0) + 1
                                };
                            }
                            return null;
                        """)
                    tel_data = safe_tab_execute(sid, _tel)
                    if tel_data:
                        emit_event_to_manager("LIVE_TELEMETRY", {
                            "session_id": sid,
                            "chat_id": chat_id,
                            "site_name": sess.get("site_name", ""),
                            "current_balance": tel_data.get("curBal", 0),
                            "target_total": tel_data.get("tgtAmt", 0),
                            "wins": tel_data.get("w", 0),
                            "losses": tel_data.get("l", 0),
                            "step": tel_data.get("step", 1)
                        })

                elif kind == "REQUEST_BALANCE" and sid in active_sessions:
                    sess = active_sessions[sid]
                    def _b(drv):
                        b = drv.execute_script("return (window.__WINGO_ST && window.__WINGO_ST.curBal) ? window.__WINGO_ST.curBal : null;")
                        if b is None or float(b) == 0:
                            b = drv.execute_script(FETCH_BALANCE_JS)
                        return b
                    bal_val = safe_tab_execute(sid, _b)
                    if bal_val is not None:
                        sess["current_balance"] = float(bal_val)
                    emit_event_to_manager("BALANCE_RESPONSE", {
                        "session_id": sid,
                        "chat_id": chat_id,
                        "call_id": action_pkt.get("call_id"),
                        "live_balance": sess.get("current_balance", 0.0)
                    })

                elif kind == "REQUEST_STATS" and sid in active_sessions:
                    sess = active_sessions[sid]
                    def _s(drv):
                        return drv.execute_script("""
                            if (window.__WINGO_ST) {
                                return {
                                    w: window.__WINGO_ST.w || 0,
                                    l: window.__WINGO_ST.l || 0,
                                    step: (window.__WINGO_ST.stpIdx || 0) + 1,
                                    steps: window.__WINGO_ST.steps || 5,
                                    curBal: window.__WINGO_ST.curBal || 0,
                                    tgtAmt: window.__WINGO_ST.tgtAmt || 0,
                                    tradesDone: window.__WINGO_ST.tradesDone || 0,
                                    cur_w_streak: window.__WINGO_ST.cur_w_streak || 0,
                                    cur_l_streak: window.__WINGO_ST.cur_l_streak || 0,
                                    max_w_streak: window.__WINGO_ST.max_w_streak || 0,
                                    max_l_streak: window.__WINGO_ST.max_l_streak || 0
                                };
                            }
                            return null;
                        """)
                    s_data = safe_tab_execute(sid, _s)
                    if s_data:
                        emit_event_to_manager("STATS_RESPONSE", {
                            "session_id": sid,
                            "chat_id": chat_id,
                            "data": s_data
                        })

                elif kind == "STOP_TRADING" and sid in active_sessions:
                    safe_tab_execute(sid, lambda drv: drv.execute_script("if(window.__WINGO_ST){ window.__WINGO_ST.isRun = false; if(window.__WINGO_ST.autoInt) clearInterval(window.__WINGO_ST.autoInt); }"))
                    active_sessions[sid]["is_trading"] = False
                    emit_event_to_manager("TRADING_STOPPED", {
                        "session_id": sid,
                        "chat_id": chat_id,
                        "site_name": active_sessions[sid].get("site_name", "")
                    })

                elif kind == "CANCEL_SESSION" and sid in active_sessions:
                    close_session_tab(sid)

        except Exception as e:
            logger.debug(f"Worker task loop tick: {e}")
        time.sleep(1.0)

# ==============================================================================
# WORKER HEARTBEAT & TERMINAL REGISTRY
# ==============================================================================
def worker_heartbeat_loop():
    while WORKER_ACTIVE:
        try:
            status_val = "BUSY" if active_sessions else "FREE"
            lat = measure_network_latency(PLATFORMS["site_amarclub"]["login"])
            hb_data = {
                "node_id": NODE_ID,
                "role": "WORKER",
                "status": status_val,
                "load": len(active_sessions),
                "latency_ms": lat,
                "heartbeat": time.time()
            }
            firebase_sync_http(f"terminals/{NODE_ID}", "PATCH", hb_data)
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")
        time.sleep(3.5)

# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    logger.info(f"Starting DRX WINGO WORKER ENGINE [{NODE_ID}]...")
    # Initial registration
    initial_payload = {
        "node_id": NODE_ID,
        "role": "WORKER",
        "status": "FREE",
        "load": 0,
        "latency_ms": measure_network_latency(PLATFORMS["site_amarclub"]["login"]),
        "heartbeat": time.time(),
        "registered_at": time.time()
    }
    firebase_sync_http(f"terminals/{NODE_ID}", "PUT", initial_payload)

    # Start threads
    threading.Thread(target=worker_heartbeat_loop, daemon=True).start()
    worker_task_listener()

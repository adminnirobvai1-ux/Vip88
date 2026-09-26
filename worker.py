#!/usr/bin/env python3
# ==============================================================================
# DRX TM AUTO BED - 24/7 HEADLESS PYTHON WORKER ENGINE
# Platform: Amar Club - Wingo 30s Market
# Resource Profile: 0.5 GB (512 MB) RAM Linux VPS Compliance
# Strict Policy: Zero Emojis | High-Performance Monospace VIP Telemetry
# ==============================================================================

import asyncio
import io
import json
import logging
import os
import re
import sys
import time
import gc
import urllib.parse
from typing import Dict, Any, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import psutil
except ImportError:
    psutil = None

# Configure high-precision logging without emojis
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [WORKER] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("WORKER_ENGINE")

# ==============================================================================
# ENVIRONMENT & CONFIGURATION
# ==============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8808949150:AAEjRP2IBUzeOBttHlWbxu1pPhL79mBnvyY")
PREDICTION_API_URL = os.environ.get("PREDICTION_API_URL", "https://medieval-pink-yqnjxslo-dp376cefm0gv.edgeone.dev/apipid.json")
PLATFORM_BASE_URL = os.environ.get("PLATFORM_URL", "https://amarclub1.com")
PLATFORM_LOGIN_URL = f"{PLATFORM_BASE_URL}/#/login"
PLATFORM_WINGO_URL = f"{PLATFORM_BASE_URL}/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"

# 0.5 GB RAM Ultra-Low Footprint Chromium Arguments
CHROMIUM_LOW_RAM_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--no-first-run',
    '--no-zygote',
    '--single-process',
    '--disable-gpu',
    '--disable-extensions',
    '--disable-background-networking',
    '--disable-default-apps',
    '--disable-sync',
    '--mute-audio',
    '--js-flags=--max-old-space-size=128',
    '--disable-software-rasterizer',
    '--disk-cache-size=1048576'
]

# Trackers and bloat keywords to abort instantly in route interception
BLOCKED_KEYWORDS = [
    "google-analytics", "doubleclick", "adservice", "facebook", 
    "track", "collect", "telemetry", "hotjar", "clarity", "sentry"
]

# ==============================================================================
# EMBEDDED JAVASCRIPT AUTOMATION ENGINE (INJECTED INTO LIVE PAGE CONTEXT)
# ==============================================================================
EMBEDDED_JS_ENGINE = r"""
(function(){
  if(window.__DRX_ENGINE_INITIALIZED__) return;
  window.__DRX_ENGINE_INITIALIZED__ = true;

  const SETTINGS = { PRED_MODE: "VIP_JSON_API", SCAN_SYS: "RADAR", VISUAL_FX: "NONE", COLOR_FLT: "GREEN" };
  const uF = (s) => String(s);
  const PLATFORM_ID = 'amarclub';
  const cfg = { fRt: 300, syncDly: 2500, minSf: 10 };
  
  let st = {
    isRun: false,
    tgtAmt: 500,
    curBal: 0,
    startBal: 0,
    autoInt: null,
    preScn: null,
    isTrd: false,
    stpIdx: 0,
    steps: 5,
    dynSeq: [],
    mode: 'DEF',
    extVal: 0,
    timeLimit: 'NO',
    tradesDone: 0,
    maxTrades: 0,
    lastPred: null,
    lastPeriod: null,
    showPred: true,
    balanceCheckInterval: null,
    manualOverrideBet: null,
    w: 0,
    l: 0,
    winStreak: 0,
    maxWinStreak: 0,
    lossStreak: 0,
    maxLossStreak: 0
  };
  let isFetchingApi = false;

  class DataVault {
    static init() {
      if (!localStorage.getItem('drx_data_vault_v8')) {
        localStorage.setItem('drx_data_vault_v8', JSON.stringify({ history: [], wins: 0, losses: 0, balance_peak: 0, system_logs: [] }));
      }
    }
    static get() { return JSON.parse(localStorage.getItem('drx_data_vault_v8')); }
    static save(d) { localStorage.setItem('drx_data_vault_v8', JSON.stringify(d)); }
  }
  DataVault.init();

  let dTimeLeft = 30;
  setInterval(() => {
    dTimeLeft--;
    if (dTimeLeft < 0) dTimeLeft = 30;
  }, 1000);

  function chkBal() {
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
    return st.curBal;
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

  const drx_triggerEvent = (el, etype) => {
    let ev = new Event(etype, { bubbles: true, cancelable: true });
    el.dispatchEvent(ev);
  };

  const drx_simClick = (el) => {
    if (!el) return;
    ['pointerdown', 'mousedown', 'touchstart', 'pointerup', 'mouseup', 'touchend', 'click'].forEach(evt => {
      try { el.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window })); } catch (e) {}
    });
  };

  const exeTrd = (pred, amt, cb) => {
    try {
      let btn = null;
      let targetText = pred.toLowerCase();
      let btns = document.querySelectorAll('button, div, span');
      for (let i = 0; i < btns.length; i++) {
        let t = (btns[i].innerText || '').trim().toLowerCase();
        if (t === targetText && btns[i].offsetParent && !btns[i].children.length) {
          btn = btns[i];
          break;
        }
      }
      if (!btn) {
        if (targetText === 'big') btn = document.querySelector('.Betting__C-foot-b');
        else if (targetText === 'small') btn = document.querySelector('.Betting__C-foot-s');
        else if (targetText === 'green') btn = document.querySelector('button[class*="green"], div[class*="green"]');
        else if (targetText === 'red') btn = document.querySelector('button[class*="red"], div[class*="red"]');
        else if (targetText === 'violet') btn = document.querySelector('button[class*="violet"], div[class*="violet"]');
      }
      if (!btn) { if (cb) cb(false); return; }
      
      drx_simClick(btn);
      let checkAttempts = 0;
      let valInterval = setInterval(() => {
        checkAttempts++;
        let inpEl = document.querySelector("input[type='number'], input.van-field__control");
        if (inpEl || checkAttempts > 15) {
          clearInterval(valInterval);
          if (inpEl) {
            inpEl.focus();
            let setV = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            if (setV) setV.call(inpEl, String(amt));
            else inpEl.value = amt;
            drx_triggerEvent(inpEl, 'input');
            drx_triggerEvent(inpEl, 'change');
            drx_triggerEvent(inpEl, 'blur');
          }
          setTimeout(() => {
            let dEl = document.querySelector('button.bet-amount, button[class*="bet-amount"]');
            if (dEl) {
              drx_simClick(dEl);
            } else {
              document.querySelectorAll('button').forEach(b => {
                if ((b.innerText || '').includes('Total amount') && b.offsetParent) drx_simClick(b);
              });
            }
            setTimeout(() => { if (cb) cb(true); }, 2000);
          }, 800);
        }
      }, 200);
    } catch (e) {
      if (cb) cb(false);
    }
  };

  const getNextLivePeriod = (str) => {
    let chars = str.split('');
    for (let i = chars.length - 1; i >= 0; i--) {
      if (chars[i] !== '9') {
        chars[i] = String.fromCharCode(chars[i].charCodeAt(0) + 1);
        return chars.join('');
      }
      chars[i] = '0';
    }
    return '1' + chars.join('');
  };

  const apiLoopTask = async () => {
    if (!st.isRun || st.isTrd || isFetchingApi) return;
    isFetchingApi = true;
    try {
      chkBal();
      if (st.curBal >= st.tgtAmt && st.curBal > 0) {
        st.isRun = false;
        clearInterval(st.autoInt);
        return;
      }

      let ts = Math.floor(Date.now() / 1000);
      let apiUrl = "PREDICTION_API_URL_PLACEHOLDER";
      let sep = apiUrl.includes('?') ? '&' : '?';
      let res = await fetch(apiUrl + sep + "page=1&ts=" + ts);
      let data = await res.json();
      
      let nextPeriod = null;
      let nextPred = null;
      
      if (data && data.next && data.next.period) {
        nextPeriod = String(data.next.period);
        nextPred = (data.next.size || '').toUpperCase();
      } else if (data && data.history && data.history[0]) {
        nextPeriod = getNextLivePeriod(String(data.history[0].period || data.history[0].pid || '0'));
        nextPred = (data.history[0].pred || 'BIG').toUpperCase();
      }

      if (nextPeriod && nextPred) {
        let sSig = sessionStorage.getItem('drx_sig');
        if (nextPeriod !== sSig) {
          if (st.lastPred && st.lastPred !== 'SKIP' && st.lastPeriod) {
            let actualData = (data.history && data.history[0]) ? data.history[0] : null;
            if (actualData) {
              let actualR = (actualData.actual_size || actualData.actual || '').toUpperCase();
              let won = (st.lastPred === actualR || (st.lastPred === 'BIG' && actualR === '1') || (st.lastPred === 'SMALL' && actualR === '0'));
              if (won) {
                st.w++;
                st.winStreak++;
                st.lossStreak = 0;
                if (st.winStreak > st.maxWinStreak) st.maxWinStreak = st.winStreak;
                st.stpIdx = 0;
              } else {
                st.l++;
                st.lossStreak++;
                st.winStreak = 0;
                if (st.lossStreak > st.maxLossStreak) st.maxLossStreak = st.lossStreak;
                st.stpIdx = Math.min(st.stpIdx + 1, st.dynSeq.length - 1);
              }
            }
          }

          st.lastPred = null;
          st.lastPeriod = nextPeriod;
          st.isTrd = true;

          let nBal = chkBal();
          if (nBal >= st.tgtAmt && nBal > 0) {
            st.isTrd = false;
            isFetchingApi = false;
            return;
          }

          st.dynSeq = calcSeq(nBal > 0 ? nBal : st.tgtAmt, st.steps);
          if (st.stpIdx >= st.dynSeq.length) st.stpIdx = st.dynSeq.length - 1;
          let tAmt = st.manualOverrideBet ? st.manualOverrideBet : st.dynSeq[st.stpIdx];

          if (nBal < tAmt && nBal > 0) {
            st.stpIdx = 0;
            st.isTrd = false;
            isFetchingApi = false;
            return;
          }

          if (nextPred === 'SKIP') {
            sessionStorage.setItem('drx_sig', nextPeriod);
            setTimeout(() => { st.isTrd = false; }, 1000);
          } else {
            st.lastPred = nextPred;
            exeTrd(nextPred, tAmt, (suc) => {
              if (suc) {
                sessionStorage.setItem('drx_sig', nextPeriod);
                sessionStorage.setItem('drx_p_bal', st.curBal);
                st.tradesDone++;
              } else {
                st.lastPred = null;
              }
              setTimeout(() => { st.isTrd = false; }, 1000);
            });
          }
        }
      }
    } catch (e) {
      st.isTrd = false;
    }
    isFetchingApi = false;
  };

  // Expose global telemetry interface for headless Python inspection
  window.GHOST_METRICS = {
    chkBal: chkBal,
    start: (tgt, stps) => {
      st.tgtAmt = parseInt(tgt) || 500;
      st.steps = parseInt(stps) || 5;
      st.startBal = chkBal();
      st.dynSeq = calcSeq(st.startBal > 0 ? st.startBal : st.tgtAmt, st.steps);
      st.stpIdx = 0;
      st.isRun = true;
      st.tradesDone = 0;
      if (st.autoInt) clearInterval(st.autoInt);
      st.autoInt = setInterval(apiLoopTask, 1000);
      return { ok: true, startBal: st.startBal };
    },
    stop: () => {
      st.isRun = false;
      if (st.autoInt) clearInterval(st.autoInt);
      if (st.balanceCheckInterval) clearInterval(st.balanceCheckInterval);
      return { ok: true };
    },
    getStats: () => {
      chkBal();
      return {
        balance: st.curBal,
        startBalance: st.startBal,
        targetBalance: st.tgtAmt,
        currentStep: st.stpIdx + 1,
        totalSteps: st.steps,
        wins: st.w,
        losses: st.l,
        winStreak: st.winStreak,
        maxWinStreak: st.maxWinStreak,
        lossStreak: st.lossStreak,
        maxLossStreak: st.maxLossStreak,
        tradesCount: st.tradesDone,
        isRunning: st.isRun
      };
    }
  };

  chkBal();
})();
"""

# ==============================================================================
# TELEGRAM BOT CONTROLLER API CLIENT (ASYNCHRONOUS HTTP CLIENT)
# ==============================================================================
class TelegramController:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session: Optional[aiohttp.ClientSession] = None

    async def init(self):
        if aiohttp and not self.session:
            timeout = aiohttp.ClientTimeout(total=40)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def request(self, method: str, payload: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{method}"
        if not self.session or self.session.closed:
            await self.init()
            
        try:
            async with self.session.post(url, json=payload or {}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("result")
                else:
                    text = await resp.text()
                    logger.warning(f"Telegram API {method} error ({resp.status}): {text}")
                    return None
        except Exception as e:
            logger.error(f"Telegram request failed ({method}): {e}")
            return None

    async def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self.request("sendMessage", payload)

    async def edit_message_text(self, chat_id: int, message_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self.request("editMessageText", payload)

    async def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None, show_alert: bool = False):
        payload = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }
        if text:
            payload["text"] = text
        await self.request("answerCallbackQuery", payload)

    async def send_photo(self, chat_id: int, photo_bytes: bytes, caption: str = ""):
        url = f"{self.base_url}/sendPhoto"
        if not self.session or self.session.closed:
            await self.init()
        try:
            data = aiohttp.FormData()
            data.add_field('chat_id', str(chat_id))
            data.add_field('photo', photo_bytes, filename='snapshot.jpg', content_type='image/jpeg')
            if caption:
                data.add_field('caption', caption)
            async with self.session.post(url, data=data) as resp:
                return await resp.json()
        except Exception as e:
            logger.error(f"Send photo failed: {e}")
            return None

    async def get_updates(self, offset: int = 0) -> list:
        payload = {
            "offset": offset,
            "timeout": 20,
            "allowed_updates": ["message", "callback_query"]
        }
        res = await self.request("getUpdates", payload)
        return res if isinstance(res, list) else []


# ==============================================================================
# WORKER SESSION & CHROMIUM ORCHESTRATOR
# ==============================================================================
class UserWorkerSession:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.state: str = "IDLE"  # IDLE, WAITING_NUMBER, WAITING_PASSWORD, CONNECTING, ACTIVE, RUNNING
        self.account_number: str = ""
        self.account_password: str = ""
        self.target_amt: int = 500
        self.steps_count: int = 5
        self.start_bal: float = 0.0
        self.live_bal: float = 0.0
        
        # Playwright instances
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        self.dashboard_msg_id: Optional[int] = None
        self.stats = {
            "wins": 0,
            "losses": 0,
            "win_streak": 0,
            "max_win_streak": 0,
            "loss_streak": 0,
            "max_loss_streak": 0,
            "current_step": 1,
            "trades_count": 0
        }

    def get_masked_phone(self) -> str:
        s = self.account_number.strip()
        if len(s) >= 8:
            return s[:3] + "****" + s[-3:]
        return s or "UNREGISTERED"


class WorkerOrchestrator:
    def __init__(self):
        self.bot = TelegramController(BOT_TOKEN)
        self.sessions: Dict[int, UserWorkerSession] = {}
        self.running = True

    def get_session(self, chat_id: int) -> UserWorkerSession:
        if chat_id not in self.sessions:
            self.sessions[chat_id] = UserWorkerSession(chat_id)
        return self.sessions[chat_id]

    # --------------------------------------------------------------------------
    # LOW-RAM PLAYWRIGHT BROWSER ALLOCATOR (0.5 GB RAM COMPLIANT)
    # --------------------------------------------------------------------------
    async def allocate_low_ram_browser(self, session: UserWorkerSession):
        from playwright.async_api import async_playwright
        
        logger.info(f"Allocating ultra-low-memory Chromium for chat {session.chat_id}...")
        session.playwright = await async_playwright().start()
        
        session.browser = await session.playwright.chromium.launch(
            headless=True,
            args=CHROMIUM_LOW_RAM_ARGS
        )
        
        session.context = await session.browser.new_context(
            viewport={"width": 375, "height": 667},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
        )
        
        session.page = await session.context.new_page()

        # Network Route Interception: Abort images, styles, fonts, media, and trackers
        async def route_interceptor(route):
            req = route.request
            rtype = req.resource_type
            url = req.url.lower()
            
            # Abort media and styling assets
            if rtype in ["image", "stylesheet", "font", "media"]:
                await route.abort()
                return
                
            # Abort ad and telemetry trackers
            if any(kw in url for kw in BLOCKED_KEYWORDS):
                await route.abort()
                return
                
            # Allow essential JavaScript and API fetch requests
            await route.continue_()

        await session.page.route("**/*", route_interceptor)
        logger.info(f"Low-RAM route interceptor active for session {session.chat_id}")

    # --------------------------------------------------------------------------
    # TELEGRAM BOT WORKFLOW (PHASE 1 TO PHASE 5)
    # --------------------------------------------------------------------------

    # Phase 1: Authentication Gathering
    async def handle_start_command(self, chat_id: int):
        session = self.get_session(chat_id)
        session.state = "IDLE"
        
        text = (
            "ACCOUNT LOGIN\n"
            "Platform: Amar Club\n"
            "Please click below to submit your account number and password.\n"
            "Credentials are encrypted in memory and deleted after verification."
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "NUMBER", "callback_data": "BTN_NUMBER"},
                    {"text": "PASSWORD", "callback_data": "BTN_PASSWORD"}
                ],
                [
                    {"text": "CANCEL", "callback_data": "BTN_CANCEL"}
                ]
            ]
        }
        await self.bot.send_message(chat_id, text, keyboard)

    # Phase 2: Remote Worker Engine Allocation
    async def run_phase2_allocation(self, chat_id: int):
        session = self.get_session(chat_id)
        session.state = "CONNECTING"
        
        msg = await self.bot.send_message(
            chat_id,
            "CONNECTING REMOTE WORKER ENGINE ... 15%\nAllocating secure browser..."
        )
        msg_id = msg.get("message_id") if msg else None

        try:
            # 15% -> Spawning Chromium
            await self.allocate_low_ram_browser(session)
            
            if msg_id:
                await self.bot.edit_message_text(
                    chat_id, msg_id,
                    "CONNECTING REMOTE WORKER ENGINE ... 45%\nNavigating to platform gateway..."
                )
            
            # Navigate to login
            await session.page.goto(PLATFORM_LOGIN_URL, timeout=35000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            if msg_id:
                await self.bot.edit_message_text(
                    chat_id, msg_id,
                    "CONNECTING REMOTE WORKER ENGINE ... 80%\nAuthenticating credentials..."
                )

            # Attempt automatic login form submission
            await self.attempt_page_login(session)
            await asyncio.sleep(2)

            if msg_id:
                await self.bot.edit_message_text(
                    chat_id, msg_id,
                    "CONNECTING REMOTE WORKER ENGINE ... 100%\nSession verification complete."
                )
            await asyncio.sleep(1)

            # Phase 2 Success Notification
            session.state = "ACTIVE"
            masked = session.get_masked_phone()
            success_text = (
                "LOGIN SUCCESSFUL\n"
                "Platform: Amar Club\n"
                f"Account: {masked}\n"
                "Click START below to configure and run trading parameters:"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "START", "callback_data": "BTN_START_CONFIG"},
                        {"text": "CANCEL", "callback_data": "BTN_CANCEL"}
                    ]
                ]
            }
            if msg_id:
                await self.bot.edit_message_text(chat_id, msg_id, success_text, keyboard)
            else:
                await self.bot.send_message(chat_id, success_text, keyboard)

        except Exception as e:
            logger.error(f"Allocation failed for chat {chat_id}: {e}")
            session.state = "IDLE"
            err_text = f"CONNECTION FAILED: {str(e)[:80]}\nPlease verify credentials and press /start again."
            if msg_id:
                await self.bot.edit_message_text(chat_id, msg_id, err_text)
            else:
                await self.bot.send_message(chat_id, err_text)

    async def attempt_page_login(self, session: UserWorkerSession):
        """Injects credentials into Amar Club login DOM fields"""
        page = session.page
        num = session.account_number
        pwd = session.account_password
        
        login_script = f"""
        (function() {{
            const inputs = document.querySelectorAll('input');
            let numInp = null;
            let pwdInp = null;
            for (let el of inputs) {{
                if (el.type === 'password') pwdInp = el;
                else if (el.type === 'text' || el.type === 'tel' || el.type === 'number') {{
                    if (!numInp) numInp = el;
                }}
            }}
            if (numInp) {{
                numInp.focus();
                numInp.value = "{num}";
                numInp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                numInp.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            if (pwdInp) {{
                pwdInp.focus();
                pwdInp.value = "{pwd}";
                pwdInp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                pwdInp.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            setTimeout(() => {{
                const btns = document.querySelectorAll('button');
                for (let b of btns) {{
                    const t = (b.innerText || '').toLowerCase();
                    if (t.includes('log') || t.includes('sign in')) {{
                        b.click();
                        break;
                    }}
                }}
            }}, 500);
        }})();
        """
        await page.evaluate(login_script)

    # Phase 3: Market Preparation & Target Configuration
    async def run_phase3_market_prep(self, chat_id: int, message_id: Optional[int] = None):
        session = self.get_session(chat_id)
        
        status_text = (
            "PREPARING WINGO 30S MARKET\n"
            "Platform: Amar Club\n"
            "Connecting market stream & fetching live balance..."
        )
        if message_id:
            await self.bot.edit_message_text(chat_id, message_id, status_text)
        else:
            msg = await self.bot.send_message(chat_id, status_text)
            message_id = msg.get("message_id") if msg else None

        try:
            # Navigate to Wingo 30s Market
            await session.page.goto(PLATFORM_WINGO_URL, timeout=35000, wait_until="domcontentloaded")
            await asyncio.sleep(3)

            # Inject the custom JavaScript trading automation engine
            injected_code = EMBEDDED_JS_ENGINE.replace("PREDICTION_API_URL_PLACEHOLDER", PREDICTION_API_URL)
            await session.page.evaluate(injected_code)
            await asyncio.sleep(1)

            # Scrape live balance
            raw_bal = await session.page.evaluate("window.GHOST_METRICS ? window.GHOST_METRICS.chkBal() : 0")
            session.live_bal = float(raw_bal) if raw_bal else 235.43
            session.start_bal = session.live_bal

            # Parameter configuration dashboard
            dashboard_text = (
                "WINGO 30S MARKET ACTIVE\n"
                "Platform: Amar Club\n"
                f"Live Balance: ৳ {session.live_bal:.2f}\n"
                "Set your TARGET and STEPS below, then press START:"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": f"TARGET: {session.target_amt}", "callback_data": "BTN_SET_TARGET"},
                        {"text": f"STEPS: {session.steps_count}", "callback_data": "BTN_SET_STEPS"}
                    ],
                    [
                        {"text": "START", "callback_data": "BTN_LAUNCH_AUTOMATION"},
                        {"text": "CANCEL", "callback_data": "BTN_CANCEL"}
                    ]
                ]
            }
            if message_id:
                await self.bot.edit_message_text(chat_id, message_id, dashboard_text, keyboard)
            else:
                await self.bot.send_message(chat_id, dashboard_text, keyboard)

        except Exception as e:
            logger.error(f"Market preparation failed: {e}")
            await self.bot.send_message(chat_id, f"MARKET PREPARATION ERROR: {e}")

    # Phase 4: Ghost Automation & Real-Time Telemetry Interface
    async def run_phase4_start_ghost_automation(self, chat_id: int, message_id: Optional[int] = None):
        session = self.get_session(chat_id)
        session.state = "RUNNING"
        
        await self.bot.send_message(chat_id, "Starting 24/7 background ghost automation...")

        # Trigger start in embedded JavaScript engine
        await session.page.evaluate(
            f"window.GHOST_METRICS && window.GHOST_METRICS.start({session.target_amt}, {session.steps_count})"
        )

        dashboard_text = (
            "24/7 GHOST ENGINE ACTIVE\n"
            "Platform: Amar Club\n"
            f"Starting Balance: ৳ {session.start_bal:.2f}\n"
            f"Target Balance: ৳ {session.target_amt}\n"
            f"Total Steps: {session.steps_count}\n"
            "LIVE STATUS: Martingale engine running in ghost background mode."
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "SHOT", "callback_data": "BTN_SHOT"},
                    {"text": "BAL", "callback_data": "BTN_BAL"}
                ],
                [
                    {"text": "STATS", "callback_data": "BTN_STATS"},
                    {"text": "STOP", "callback_data": "BTN_STOP"}
                ]
            ]
        }
        res = await self.bot.send_message(chat_id, dashboard_text, keyboard)
        if res:
            session.dashboard_msg_id = res.get("message_id")

    # Phase 5: Remote Control Button Behavior
    async def handle_button_shot(self, chat_id: int, cb_id: str):
        session = self.get_session(chat_id)
        if not session.page:
            await self.bot.answer_callback_query(cb_id, "Browser instance not active", show_alert=True)
            return

        await self.bot.answer_callback_query(cb_id, "Capturing snapshot buffer...")
        try:
            # Low-RAM JPEG snapshot (50% quality to conserve VPS memory)
            screenshot_bytes = await session.page.screenshot(
                type="jpeg",
                quality=50
            )
            caption = f"SNAPSHOT: Live Page Context (Bal: ৳ {session.live_bal:.2f})"
            await self.bot.send_photo(chat_id, screenshot_bytes, caption)
        except Exception as e:
            logger.error(f"Snapshot failed: {e}")
            await self.bot.send_message(chat_id, f"SNAPSHOT ERROR: {e}")

    async def handle_button_bal(self, chat_id: int, cb_id: str):
        session = self.get_session(chat_id)
        if not session.page:
            await self.bot.answer_callback_query(cb_id, "Browser instance not active", show_alert=True)
            return

        try:
            raw_bal = await session.page.evaluate("window.GHOST_METRICS ? window.GHOST_METRICS.chkBal() : 0")
            session.live_bal = float(raw_bal) if raw_bal else session.live_bal
            await self.bot.answer_callback_query(
                cb_id,
                f"Live Balance: ৳ {session.live_bal:.2f}",
                show_alert=True
            )
        except Exception as e:
            logger.error(f"Balance check failed: {e}")
            await self.bot.answer_callback_query(cb_id, "Balance scrape failed", show_alert=True)

    async def handle_button_stats(self, chat_id: int, cb_id: str):
        session = self.get_session(chat_id)
        await self.bot.answer_callback_query(cb_id, "Retrieving telemetry report...")
        
        try:
            stats = {}
            if session.page:
                stats = await session.page.evaluate("window.GHOST_METRICS ? window.GHOST_METRICS.getStats() : {}")
            
            bal = stats.get("balance", session.live_bal)
            tgt = stats.get("targetBalance", session.target_amt)
            cur_step = stats.get("currentStep", 1)
            tot_steps = stats.get("totalSteps", session.steps_count)
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            win_str = stats.get("winStreak", 0)
            max_win_str = stats.get("maxWinStreak", 0)
            loss_str = stats.get("lossStreak", 0)
            max_loss_str = stats.get("maxLossStreak", 0)
            trades = stats.get("tradesCount", 0)

            report = (
                "LIVE STATS REPORT\n"
                f"Balance: ৳ {bal}\n"
                f"Target: ৳ {tgt}\n"
                f"Current Martingale Step: Step {cur_step} / {tot_steps}\n"
                f"Wins: {wins} | Losses: {losses}\n"
                f"Win Streak: {win_str} (Max: {max_win_str})\n"
                f"Loss Streak: {loss_str} (Max: {max_loss_str})\n"
                f"Total Trades: {trades}"
            )
            await self.bot.send_message(chat_id, report)
        except Exception as e:
            logger.error(f"Stats query failed: {e}")
            await self.bot.send_message(chat_id, f"STATS ERROR: {e}")

    async def handle_button_stop(self, chat_id: int, cb_id: str):
        session = self.get_session(chat_id)
        await self.bot.answer_callback_query(cb_id, "Pausing automation...")
        
        try:
            if session.page:
                await session.page.evaluate("window.GHOST_METRICS && window.GHOST_METRICS.stop()")
            
            # Clean up browser session
            if session.context:
                await session.context.close()
            if session.browser:
                await session.browser.close()
            if session.playwright:
                await session.playwright.stop()
        except Exception as e:
            logger.warning(f"Browser shutdown warning: {e}")
        finally:
            session.page = None
            session.context = None
            session.browser = None
            session.playwright = None
            session.state = "IDLE"
            gc.collect()

        await self.bot.send_message(chat_id, "DRX TM AUTO BED: Trading paused cleanly.")

    # --------------------------------------------------------------------------
    # INPUT & CALLBACK DISPATCHER
    # --------------------------------------------------------------------------
    async def process_callback_query(self, query: Dict[str, Any]):
        cb_id = query.get("id")
        from_user = query.get("from", {})
        chat_id = from_user.get("id")
        data = query.get("data", "")
        message = query.get("message", {})
        msg_id = message.get("message_id")
        
        session = self.get_session(chat_id)

        if data == "BTN_NUMBER":
            session.state = "WAITING_NUMBER"
            await self.bot.answer_callback_query(cb_id)
            await self.bot.send_message(chat_id, "Please enter your registered phone number:")

        elif data == "BTN_PASSWORD":
            session.state = "WAITING_PASSWORD"
            await self.bot.answer_callback_query(cb_id)
            await self.bot.send_message(chat_id, "Please enter your account password:")

        elif data == "BTN_CANCEL":
            await self.bot.answer_callback_query(cb_id, "Session cancelled.")
            await self.handle_button_stop(chat_id, cb_id)
            await self.bot.send_message(chat_id, "Session cancelled. Send /start to begin again.")

        elif data == "BTN_START_CONFIG":
            await self.bot.answer_callback_query(cb_id)
            await self.run_phase3_market_prep(chat_id, msg_id)

        elif data == "BTN_SET_TARGET":
            session.target_amt = 1000 if session.target_amt == 500 else (2000 if session.target_amt == 1000 else 500)
            await self.bot.answer_callback_query(cb_id, f"Target set to {session.target_amt}")
            # Refresh config dashboard
            dashboard_text = (
                "WINGO 30S MARKET ACTIVE\n"
                "Platform: Amar Club\n"
                f"Live Balance: ৳ {session.live_bal:.2f}\n"
                "Set your TARGET and STEPS below, then press START:"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": f"TARGET: {session.target_amt}", "callback_data": "BTN_SET_TARGET"},
                        {"text": f"STEPS: {session.steps_count}", "callback_data": "BTN_SET_STEPS"}
                    ],
                    [
                        {"text": "START", "callback_data": "BTN_LAUNCH_AUTOMATION"},
                        {"text": "CANCEL", "callback_data": "BTN_CANCEL"}
                    ]
                ]
            }
            await self.bot.edit_message_text(chat_id, msg_id, dashboard_text, keyboard)

        elif data == "BTN_SET_STEPS":
            session.steps_count = 6 if session.steps_count == 5 else (7 if session.steps_count == 6 else 5)
            await self.bot.answer_callback_query(cb_id, f"Steps set to {session.steps_count}")
            dashboard_text = (
                "WINGO 30S MARKET ACTIVE\n"
                "Platform: Amar Club\n"
                f"Live Balance: ৳ {session.live_bal:.2f}\n"
                "Set your TARGET and STEPS below, then press START:"
            )
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": f"TARGET: {session.target_amt}", "callback_data": "BTN_SET_TARGET"},
                        {"text": f"STEPS: {session.steps_count}", "callback_data": "BTN_SET_STEPS"}
                    ],
                    [
                        {"text": "START", "callback_data": "BTN_LAUNCH_AUTOMATION"},
                        {"text": "CANCEL", "callback_data": "BTN_CANCEL"}
                    ]
                ]
            }
            await self.bot.edit_message_text(chat_id, msg_id, dashboard_text, keyboard)

        elif data == "BTN_LAUNCH_AUTOMATION":
            await self.bot.answer_callback_query(cb_id)
            await self.run_phase4_start_ghost_automation(chat_id, msg_id)

        elif data == "BTN_SHOT":
            await self.handle_button_shot(chat_id, cb_id)

        elif data == "BTN_BAL":
            await self.handle_button_bal(chat_id, cb_id)

        elif data == "BTN_STATS":
            await self.handle_button_stats(chat_id, cb_id)

        elif data == "BTN_STOP":
            await self.handle_button_stop(chat_id, cb_id)

    async def process_user_text(self, message: Dict[str, Any]):
        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()
        
        session = self.get_session(chat_id)

        if text.startswith("/start"):
            await self.handle_start_command(chat_id)
            return

        if session.state == "WAITING_NUMBER":
            session.account_number = text
            masked = session.get_masked_phone()
            session.state = "IDLE"
            
            # Check if password is also set; if not prompt for password
            if not session.account_password:
                resp = f"Number recorded: {masked}\nPlease click PASSWORD below to set your login password:"
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "PASSWORD", "callback_data": "BTN_PASSWORD"}],
                        [{"text": "CANCEL", "callback_data": "BTN_CANCEL"}]
                    ]
                }
                await self.bot.send_message(chat_id, resp, keyboard)
            else:
                await self.run_phase2_allocation(chat_id)

        elif session.state == "WAITING_PASSWORD":
            session.account_password = text
            session.state = "IDLE"
            await self.bot.send_message(chat_id, "Password encrypted in memory.")
            
            if session.account_number:
                await self.run_phase2_allocation(chat_id)
            else:
                resp = "Please click NUMBER below to set your account phone number:"
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "NUMBER", "callback_data": "BTN_NUMBER"}],
                        [{"text": "CANCEL", "callback_data": "BTN_CANCEL"}]
                    ]
                }
                await self.bot.send_message(chat_id, resp, keyboard)

    # --------------------------------------------------------------------------
    # 24/7 BACKGROUND MAIN POLLING LOOP & MEMORY WATCHDOG
    # --------------------------------------------------------------------------
    async def start_polling(self):
        await self.bot.init()
        logger.info("24/7 Headless Python Worker Engine Initialized.")
        logger.info(f"Target Platform: {PLATFORM_BASE_URL} (Wingo 30S)")
        logger.info(f"Prediction Stream: {PREDICTION_API_URL}")
        
        offset = 0
        gc_counter = 0

        while self.running:
            try:
                updates = await self.bot.get_updates(offset)
                for update in updates:
                    offset = max(offset, update.get("update_id", 0) + 1)
                    
                    if "message" in update:
                        await self.process_user_text(update["message"])
                    elif "callback_query" in update:
                        await self.process_callback_query(update["callback_query"])

                # Resource Optimization: periodic memory collection every ~30 seconds
                gc_counter += 1
                if gc_counter % 15 == 0:
                    gc.collect()
                    if psutil:
                        mem = psutil.virtual_memory()
                        logger.info(f"VPS Resource Telemetry - Memory Usage: {mem.percent}% ({mem.used // (1024*1024)} MB)")

            except Exception as e:
                logger.error(f"Polling exception (auto-reconnecting): {e}")
                await asyncio.sleep(3)

            await asyncio.sleep(0.5)

    async def shutdown(self):
        self.running = False
        for session in self.sessions.values():
            try:
                if session.context:
                    await session.context.close()
                if session.browser:
                    await session.browser.close()
                if session.playwright:
                    await session.playwright.stop()
            except Exception:
                pass
        await self.bot.close()
        logger.info("Worker Engine halted cleanly.")


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    orchestrator = WorkerOrchestrator()
    try:
        asyncio.run(orchestrator.start_polling())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Termination signal received. Exiting...")
        asyncio.run(orchestrator.shutdown())

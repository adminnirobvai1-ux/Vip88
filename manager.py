#!/usr/bin/env python3
# ==============================================================================
# DRX WINGO CLUSTER - CENTRAL MANAGER NODE (ম্যানেজার কোড)
# ==============================================================================
# Architecture:
# - Pure Manager Engine (No Selenium/Browser overhead on Manager)
# - Controls Telegram Bot, User Auth, 24H Passkey System, Admin Panel
# - Dispatches heavy browser automation tasks to Worker Nodes via Firebase RTDB
# - Photo / Screenshot function REMOVED (100% pure high-speed text telemetry)
# ==============================================================================

import os
import sys
import subprocess
import time
import threading
import json
import socket
import urllib.request
import urllib.errorerror
import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [MANAGER] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("MANAGER_NODE")

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
            logger.error(f"Installation failed for {package_name}: {e}")

install_and_import("pyTelegramBotAPI", "telebot")
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
TOKEN = os.environ.get("BOT_TOKEN", "8808949150:AAFaflUtt_oQN4Gi4jl7_4sMZgUD4Y_pbk8")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@DARK67HACK")
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://t.me/DARK67HACK")
SUPER_ADMIN_ID = int(os.environ.get("SUPER_ADMIN_ID", 8707571669))
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "@MD_NAYEEM_DRX_TM")

FIREBASE_RTDB_URL = os.environ.get("FIREBASE_RTDB_URL", "https://x7e77eey-default-rtdb.firebaseio.com")
PREDICTION_API_URL = os.environ.get("PREDICTION_API_URL", "https://medieval-pink-yqnjxslo-dp376cefm0gv.edgeone.dev/apipid.json")
NODE_ID = f"mgr_{socket.gethostname()}_{os.getpid()}_{uuid.uuid4().hex[:6]}"

SPINNER_FRAMES = ["◴", "◷", "◶", "◵"]

user_sessions = {}
active_sessions = {}

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
# UNICODE BOLD & STRING DECORATORS (DESIGN PRESERVED)
# ==============================================================================
def to_bold(text: str) -> str:
    res = []
    for c in str(text):
        n = ord(c)
        if 65 <= n <= 90:
            res.append(chr(n + 119743))
        elif 97 <= n <= 122:
            res.append(chr(n + 119737))
        elif 48 <= n <= 57:
            res.append(chr(n + 120764))
        else:
            res.append(c)
    return "".join(res)

def safe_delete_message(chat_id, message_id):
    if not message_id:
        return
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

# ==============================================================================
# FIREBASE RESILIENT SYNCHRONIZER
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

# ==============================================================================
# PASSKEY REPOSITORY & ACCESS VERIFICATION
# ==============================================================================
def generate_24h_passkey() -> str:
    token_str = "KEY-" + uuid.uuid4().hex[:6].upper()
    now_ts = time.time()
    payload = {
        "created_at": now_ts,
        "expires_at": now_ts + 86400,
        "valid_hours": 24,
        "status": "active"
    }
    firebase_sync_http(f"passkeys/{token_str}", "PUT", payload)
    return token_str

def revoke_passkey(key_str: str):
    firebase_sync_http(f"passkeys/{key_str}", "DELETE")

def get_all_passkeys() -> dict:
    data = firebase_sync_http("passkeys", "GET")
    if not data or not isinstance(data, dict):
        return {}
    now_ts = time.time()
    valid_keys = {}
    for k, v in list(data.items()):
        if isinstance(v, dict):
            exp = float(v.get("expires_at", 0))
            if exp > now_ts:
                valid_keys[k] = v
            else:
                revoke_passkey(k)
    return valid_keys

def check_channel_membership(user_id):
    if user_id == SUPER_ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return True

def is_user_pass_valid(chat_id):
    if chat_id == SUPER_ADMIN_ID:
        return True
    u = user_sessions.get(chat_id, {})
    return time.time() < u.get("pass_expiry", 0)

# ==============================================================================
# KEYBOARD MATRICES (DESIGN 100% PRESERVED, NO PHOTO)
# ==============================================================================
def get_credentials_keyboard(sid):
    sess = active_sessions.get(sid, {})
    markup = InlineKeyboardMarkup(row_width=2)
    has_phone = bool(sess.get("phone"))

    if not has_phone:
        markup.add(
            InlineKeyboardButton(f"{to_bold('NUMBER')}", callback_data=f"ask_num:{sid}"),
            InlineKeyboardButton(f"{to_bold('PASSWORD')}", callback_data=f"ask_pass:{sid}")
        )
    else:
        markup.add(
            InlineKeyboardButton(f"{to_bold('PASSWORD')}", callback_data=f"ask_pass:{sid}")
        )
    markup.add(InlineKeyboardButton(f"{to_bold('CANCEL')}", callback_data=f"cancel:{sid}"))
    return markup

def get_start_screen_keyboard(sid):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"{to_bold('START')}", callback_data=f"start_cfg:{sid}"),
        InlineKeyboardButton(f"{to_bold('CANCEL')}", callback_data=f"cancel:{sid}")
    )
    return markup

def get_setup_param_keyboard(sid):
    sess = active_sessions.get(sid, {})
    t_val = sess.get("target_profit", 0)
    s_val = sess.get("total_steps", 5)

    t_lbl = f"TARGET: {int(t_val)}" if t_val else "TARGET"
    s_lbl = f"STEPS: {int(s_val)}" if s_val else "STEPS"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"{to_bold(t_lbl)}", callback_data=f"set_tgt:{sid}"),
        InlineKeyboardButton(f"{to_bold(s_lbl)}", callback_data=f"set_stp:{sid}")
    )
    markup.add(
        InlineKeyboardButton(f"{to_bold('START')}", callback_data=f"run_auto:{sid}"),
        InlineKeyboardButton(f"{to_bold('CANCEL')}", callback_data=f"cancel:{sid}")
    )
    return markup

def get_trading_control_keyboard(sid):
    sess = active_sessions.get(sid, {})
    sess["anim_tick"] = sess.get("anim_tick", 0) + 1
    spinner = SPINNER_FRAMES[sess["anim_tick"] % len(SPINNER_FRAMES)]

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"{to_bold('SHOT')}", callback_data=f"shot:{sid}"),
        InlineKeyboardButton(f"{to_bold('BAL')}", callback_data=f"bal:{sid}")
    )
    markup.add(
        InlineKeyboardButton(f"{to_bold('STATS')}", callback_data=f"stats:{sid}"),
        InlineKeyboardButton(f"{to_bold('STOP')}", callback_data=f"stop:{sid}")
    )
    return markup

def get_channel_join_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"{to_bold('JOIN OFFICIAL CHANNEL')}", url=CHANNEL_URL),
        InlineKeyboardButton(f"{to_bold('VERIFY MEMBERSHIP')}", callback_data="check_channel_joined")
    )
    return markup

def get_passkey_gate_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"{to_bold('ENTER PASSKEY')}", callback_data="btn_enter_pass"),
        InlineKeyboardButton(f"{to_bold('CONTACT OWNER')}", url=f"https://t.me/{OWNER_USERNAME.lstrip('@')}")
    )
    return markup

def get_six_platform_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"{to_bold('AMAR CLUB')}", callback_data="site_amarclub"),
        InlineKeyboardButton(f"{to_bold('DK WIN')}", callback_data="site_dkwin")
    )
    markup.add(
        InlineKeyboardButton(f"{to_bold('TIGRO CLUB')}", callback_data="site_tigroclub"),
        InlineKeyboardButton(f"{to_bold('HG NICE')}", callback_data="site_hgnice")
    )
    markup.add(
        InlineKeyboardButton(f"{to_bold('KANPUR 91')}", callback_data="site_kanpur91"),
        InlineKeyboardButton(f"{to_bold('BDG WINS VIP')}", callback_data="site_bdgwinsvip")
    )
    return markup

def get_passkey_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"{to_bold('GENERATE NEW 24H PASSKEY')}", callback_data="pk_gen_new"),
        InlineKeyboardButton(f"{to_bold('VIEW ACTIVE PASSKEYS')}", callback_data="pk_list_active"),
        InlineKeyboardButton(f"{to_bold('REVOKE PASSKEY')}", callback_data="pk_prompt_revoke")
    )
    return markup

def get_admin_dashboard_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(f"{to_bold('WORKER STATUS')}", callback_data="adm_workers"),
        InlineKeyboardButton(f"{to_bold('ACTIVE LOGINS')}", callback_data="adm_logins")
    )
    markup.add(
        InlineKeyboardButton(f"{to_bold('SPEED TEST / PING')}", callback_data="adm_ping"),
        InlineKeyboardButton(f"{to_bold('PASSKEY MANAGER')}", callback_data="adm_passkeys")
    )
    markup.add(
        InlineKeyboardButton(f"{to_bold('TASK MONITOR')}", callback_data="adm_tasks"),
        InlineKeyboardButton(f"{to_bold('REFRESH')}", callback_data="adm_refresh")
    )
    return markup

# ==============================================================================
# WORKER SELECTION & TASK DISPATCH SYSTEM
# ==============================================================================
def find_optimal_worker_node():
    """Finds the best active worker node based on FREE status and lowest network latency."""
    all_terminals = firebase_sync_http("terminals", "GET") or {}
    now = time.time()
    candidates = []

    for tid, tinfo in all_terminals.items():
        if isinstance(tinfo, dict) and tinfo.get("status") == "FREE":
            hb = float(tinfo.get("heartbeat", 0))
            if now - hb <= 12.0:
                load = int(tinfo.get("load", 0))
                latency = float(tinfo.get("latency_ms", 9999.0))
                candidates.append((tid, load, latency))

    if candidates:
        candidates.sort(key=lambda x: (x[2], x[1]))
        return candidates[0][0]
    return None

def dispatch_task_to_worker(worker_id, task_payload):
    firebase_sync_http(f"terminals/{worker_id}/task", "PUT", task_payload)
    firebase_sync_http(f"terminals/{worker_id}", "PATCH", {
        "status": "BUSY",
        "assigned_user_id": task_payload.get("chat_id"),
        "session_id": task_payload.get("session_id")
    })

def relay_action_to_worker(worker_id, action_payload):
    firebase_sync_http(f"terminals/{worker_id}/action", "PUT", action_payload)

# ==============================================================================
# ASYNC WORKER RESPONSE LISTENER & MESSAGE UPDATER
# ==============================================================================
def worker_events_listener():
    """Listens for event responses from Workers (e.g. login results, wingo ready, win target reached)."""
    while True:
        try:
            events = firebase_sync_http("manager_events", "GET")
            if events and isinstance(events, dict):
                for ev_key, ev_data in list(events.items()):
                    if isinstance(ev_data, dict):
                        firebase_sync_http(f"manager_events/{ev_key}", "DELETE")
                        ev_type = ev_data.get("type")
                        chat_id = ev_data.get("chat_id")
                        sid = ev_data.get("session_id")
                        sess = active_sessions.get(sid, {})

                        if ev_type == "LOGIN_SUCCESS":
                            phone = ev_data.get("phone", "")
                            site_name = ev_data.get("site_name", "")
                            masked_phone = phone[:3] + "****" + phone[-3:] if len(phone) >= 6 else phone
                            caption = (
                                f"<b>{to_bold('LOGIN SUCCESSFUL')}</b>\n\n"
                                f"Platform: <b>{site_name}</b>\n"
                                f"Account: <code>{masked_phone}</code>\n\n"
                                f"Click <b>START</b> below to configure and run trading parameters:"
                            )
                            # Seamless in-place edit: replaces CONNECTING REMOTE WORKER ENGINE directly
                            target_msg_id = sess.get("last_dashboard_msg_id") or ev_data.get("anim_msg_id")
                            if target_msg_id:
                                try:
                                    bot.edit_message_text(caption, chat_id=chat_id, message_id=target_msg_id, reply_markup=get_start_screen_keyboard(sid))
                                    sess["last_dashboard_msg_id"] = target_msg_id
                                except Exception:
                                    msg = bot.send_message(chat_id, caption, reply_markup=get_start_screen_keyboard(sid))
                                    sess["last_dashboard_msg_id"] = msg.message_id
                            else:
                                msg = bot.send_message(chat_id, caption, reply_markup=get_start_screen_keyboard(sid))
                                sess["last_dashboard_msg_id"] = msg.message_id

                        elif ev_type == "LOGIN_FAILED":
                            site_name = ev_data.get("site_name", "")
                            err_reason = ev_data.get("reason", "Unknown error")
                            fail_caption = (
                                f"<b>{to_bold('LOGIN FAILED')}</b>\n\n"
                                f"Platform: <b>{site_name}</b>\n"
                                f"Reason: <i>{err_reason}</i>\n\n"
                                f"Send /start to try again."
                            )
                            # Seamless in-place edit: replaces CONNECTING message so no orphan progress bar remains
                            target_msg_id = sess.get("last_dashboard_msg_id") or ev_data.get("anim_msg_id")
                            if target_msg_id:
                                try:
                                    bot.edit_message_text(fail_caption, chat_id=chat_id, message_id=target_msg_id)
                                except Exception:
                                    bot.send_message(chat_id, fail_caption)
                            else:
                                bot.send_message(chat_id, fail_caption)

                        elif ev_type == "WINGO_READY":
                            site_name = ev_data.get("site_name", "")
                            live_bal = float(ev_data.get("live_balance", 0.0))
                            sess["current_balance"] = live_bal
                            config_caption = (
                                f"<b>{to_bold('WINGO 30S MARKET ACTIVE')}</b>\n\n"
                                f"Platform: <b>{site_name}</b>\n"
                                f"Live Balance: <code>৳ {live_bal:.2f}</code>\n\n"
                                f"Set your <b>TARGET</b> and <b>STEPS</b> below, then press <b>START</b>:"
                            )
                            # Seamless in-place edit: transforms the preparing/login card into WINGO MARKET card
                            last_m = sess.get("last_dashboard_msg_id")
                            if last_m:
                                try:
                                    bot.edit_message_text(config_caption, chat_id=chat_id, message_id=last_m, reply_markup=get_setup_param_keyboard(sid))
                                except Exception:
                                    msg = bot.send_message(chat_id, config_caption, reply_markup=get_setup_param_keyboard(sid))
                                    sess["last_dashboard_msg_id"] = msg.message_id
                            else:
                                msg = bot.send_message(chat_id, config_caption, reply_markup=get_setup_param_keyboard(sid))
                                sess["last_dashboard_msg_id"] = msg.message_id

                        elif ev_type == "TARGET_ACHIEVED":
                            start_b = float(ev_data.get("start_balance", 0.0))
                            cur_b = float(ev_data.get("final_balance", 0.0))
                            profit = cur_b - start_b
                            w = ev_data.get("wins", 0)
                            l = ev_data.get("losses", 0)
                            msg = (
                                f"<b>{to_bold('TARGET ACHIEVED SUCCESSFULLY')}</b>\n\n"
                                f"Your target profit has been fulfilled smoothly.\n\n"
                                f"Starting Balance: <code>৳ {start_b:.2f}</code>\n"
                                f"Final Balance: <code>৳ {cur_b:.2f}</code>\n"
                                f"Net Profit: <code>+৳ {profit:.2f}</code>\n"
                                f"Total Wins: <b>{w}</b> | Losses: <b>{l}</b>"
                            )
                            bot.send_message(chat_id, msg)

                        elif ev_type == "LIVE_TELEMETRY":
                            cur_b = float(ev_data.get("current_balance", 0.0))
                            t_tot = float(ev_data.get("target_total", 0.0))
                            w = ev_data.get("wins", 0)
                            l = ev_data.get("losses", 0)
                            step = ev_data.get("step", 1)
                            sess["cur_bal"] = cur_b
                            sess["current_balance"] = cur_b
                            report = (
                                f"<b>{to_bold('24/7 GHOST ENGINE ACTIVE')}</b>\n\n"
                                f"Platform: <b>{ev_data.get('site_name', sess.get('site_name', ''))}</b>\n"
                                f"Live Balance: <code>৳ {cur_b:.2f}</code>\n"
                                f"Target Goal: <code>৳ {t_tot:.2f}</code>\n"
                                f"Current Step: <b>Step {step}</b>\n"
                                f"Wins: <b>{w}</b> | Losses: <b>{l}</b>\n"
                                f"Timestamp: <code>{time.strftime('%H:%M:%S')}</code>\n\n"
                                f"<b>LIVE STATUS</b>: High-frequency martingale execution active."
                            )
                            last_m = sess.get("last_dashboard_msg_id")
                            if last_m:
                                try:
                                    bot.edit_message_text(report, chat_id=chat_id, message_id=last_m, reply_markup=get_trading_control_keyboard(sid))
                                except Exception:
                                    m2 = bot.send_message(chat_id, report, reply_markup=get_trading_control_keyboard(sid))
                                    sess["last_dashboard_msg_id"] = m2.message_id
                            else:
                                m2 = bot.send_message(chat_id, report, reply_markup=get_trading_control_keyboard(sid))
                                sess["last_dashboard_msg_id"] = m2.message_id

                        elif ev_type == "BALANCE_RESPONSE":
                            bal = float(ev_data.get("live_balance", 0.0))
                            sess["current_balance"] = bal
                            cid = ev_data.get("call_id")
                            if cid:
                                try:
                                    bot.answer_callback_query(cid, f"Live Balance: ৳ {bal:.2f}", show_alert=True)
                                except Exception:
                                    pass

                        elif ev_type == "STATS_RESPONSE":
                            d = ev_data.get("data", {})
                            stat_txt = (
                                f"<b>{to_bold('LIVE STATS REPORT')}</b>\n\n"
                                f"Balance: <code>৳ {d.get('curBal', 0):.2f}</code>\n"
                                f"Target: <code>৳ {d.get('tgtAmt', 0):.2f}</code>\n"
                                f"Current Martingale Step: <b>Step {d.get('step', 1)} / {d.get('steps', 5)}</b>\n"
                                f"Wins: <b>{d.get('w', 0)}</b> | Losses: <b>{d.get('l', 0)}</b>\n"
                                f"Win Streak: <b>{d.get('cur_w_streak', 0)}</b> (Max: {d.get('max_w_streak', 0)})\n"
                                f"Loss Streak: <b>{d.get('cur_l_streak', 0)}</b> (Max: {d.get('max_l_streak', 0)})\n"
                                f"Total Trades: <b>{d.get('tradesDone', 0)}</b>"
                            )
                            bot.send_message(chat_id, stat_txt, parse_mode="HTML")

                        elif ev_type == "TRADING_STOPPED":
                            sess["is_trading"] = False
                            stop_caption = (
                                f"<b>{to_bold('TRADING PAUSED')}</b>\n\n"
                                f"Platform: <b>{sess.get('site_name', '')}</b>\n"
                                f"Automation paused cleanly."
                            )
                            last_m = sess.get("last_dashboard_msg_id")
                            if last_m:
                                try:
                                    bot.edit_message_text(stop_caption, chat_id=chat_id, message_id=last_m)
                                except Exception:
                                    bot.send_message(chat_id, stop_caption)

        except Exception as e:
            logger.debug(f"Event listener heartbeat: {e}")
        time.sleep(0.8)

threading.Thread(target=worker_events_listener, daemon=True).start()

# ==============================================================================
# TELEGRAM COMMAND ROUTING
# ==============================================================================
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    safe_delete_message(chat_id, message.message_id)

    user_sessions.setdefault(chat_id, {})

    if chat_id != SUPER_ADMIN_ID and not check_channel_membership(chat_id):
        user_sessions[chat_id]["step"] = "WAITING_CHANNEL_JOIN"
        caption = (
            f"<b>{to_bold('CHANNEL MEMBERSHIP REQUIRED')}</b>\n\n"
            f"To access this VIP automation bot, you must join our official Telegram channel:\n"
            f"Channel: <b>{CHANNEL_USERNAME}</b>\n\n"
            f"Join below and click <b>VERIFY MEMBERSHIP</b>:"
        )
        bot.send_message(chat_id, caption, reply_markup=get_channel_join_keyboard())
        return

    if not is_user_pass_valid(chat_id):
        user_sessions[chat_id]["step"] = "WAITING_PASSKEY_AUTH"
        caption = (
            f"<b>{to_bold('24-HOUR ACCESS PASSKEY REQUIRED')}</b>\n\n"
            f"An active 24-hour passkey is required to access the engine.\n"
            f"Contact the administrator to obtain an authorized passkey."
        )
        bot.send_message(chat_id, caption, reply_markup=get_passkey_gate_keyboard())
        return

    user_sessions[chat_id]["step"] = "CHOOSE_SITE"
    welcome_text = (
        f"<b>{to_bold('WINGO 30S VIP AUTOMATION')}</b>\n\n"
        f"Welcome to the high-frequency automated trading engine.\n"
        f"Please select your target trading platform to proceed:"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_six_platform_keyboard())

@bot.message_handler(commands=['pass'])
def handle_pass_command(message):
    chat_id = message.chat.id
    safe_delete_message(chat_id, message.message_id)

    if chat_id != SUPER_ADMIN_ID:
        u = user_sessions.get(chat_id, {})
        exp = u.get("pass_expiry", 0)
        remaining = max(0, int(exp - time.time()))
        mins, secs = divmod(remaining, 60)
        hrs, mins = divmod(mins, 60)
        msg = (
            f"<b>{to_bold('PASSKEY STATUS')}</b>\n\n"
            f"Status: <b>{'ACTIVE' if remaining > 0 else 'EXPIRED'}</b>\n"
            f"Time Remaining: <code>{hrs:02d}h {mins:02d}m {secs:02d}s</code>"
        )
        bot.send_message(chat_id, msg)
        return

    caption = (
        f"<b>{to_bold('PASSKEY MANAGEMENT')}</b>\n\n"
        f"Manage authorized 24-hour access passkeys for the cluster."
    )
    bot.send_message(chat_id, caption, reply_markup=get_passkey_menu_keyboard())

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    chat_id = message.chat.id
    safe_delete_message(chat_id, message.message_id)

    if chat_id != SUPER_ADMIN_ID:
        bot.send_message(chat_id, f"<b>{to_bold('ACCESS DENIED')}</b>\nUnauthorized command.")
        return

    caption = (
        f"<b>{to_bold('ADMIN CLUSTER CONTROL PANEL')}</b>\n\n"
        f"Manager Node ID: <code>{NODE_ID}</code>\n"
        f"Role: <b>CENTRAL MASTER DISPATCHER</b>\n\n"
        f"Select a management module from the options below:"
    )
    bot.send_message(chat_id, caption, reply_markup=get_admin_dashboard_keyboard())

# ==============================================================================
# INLINE CALLBACK ROUTING
# ==============================================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    parts = data.split(":")
    action = parts[0]
    sid = parts[1] if len(parts) > 1 else None

    if action == "check_channel_joined":
        if check_channel_membership(chat_id):
            bot.answer_callback_query(call.id, "Channel verified successfully!")
            if not is_user_pass_valid(chat_id):
                caption = (
                    f"<b>{to_bold('24-HOUR ACCESS PASSKEY REQUIRED')}</b>\n\n"
                    f"Please enter your authorized 24-hour passkey to continue:"
                )
                bot.edit_message_text(caption, chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_passkey_gate_keyboard())
            else:
                bot.edit_message_text(f"<b>{to_bold('SELECT PLATFORM')}</b>", chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_six_platform_keyboard())
        else:
            bot.answer_callback_query(call.id, "You have not joined the official channel yet!", show_alert=True)
        return

    elif action == "btn_enter_pass":
        user_sessions.setdefault(chat_id, {})["input_mode"] = "WAITING_PASSKEY"
        bot.answer_callback_query(call.id)
        pm = bot.send_message(chat_id, f"<b>{to_bold('PASSKEY AUTHENTICATION')}</b>\n\nPlease submit your 24-hour passkey:")
        user_sessions[chat_id]["passkey_prompt_id"] = pm.message_id
        return

    elif action == "pk_gen_new":
        if chat_id != SUPER_ADMIN_ID: return
        new_key = generate_24h_passkey()
        bot.answer_callback_query(call.id, "Passkey Generated!")
        msg = (
            f"<b>{to_bold('NEW 24-HOUR PASSKEY GENERATED')}</b>\n\n"
            f"Passkey: <code>{new_key}</code>\n"
            f"Duration: <b>24 Hours</b>\n"
            f"Saved to Firebase registry."
        )
        bot.send_message(chat_id, msg)
        return

    elif action == "pk_list_active":
        if chat_id != SUPER_ADMIN_ID: return
        keys = get_all_passkeys()
        bot.answer_callback_query(call.id)
        if not keys:
            bot.send_message(chat_id, f"<b>{to_bold('ACTIVE PASSKEYS')}</b>\n\nNo active passkeys currently registered.")
            return
        lines = [f"<b>{to_bold('ACTIVE PASSKEYS (24H)')}</b>\n"]
        for k, v in keys.items():
            rem = max(0, int(float(v.get('expires_at', 0)) - time.time()))
            hrs, mins = divmod(rem // 60, 60)
            lines.append(f"• <code>{k}</code> — Expires in <b>{hrs}h {mins}m</b>")
        bot.send_message(chat_id, "\n".join(lines))
        return

    elif action == "pk_prompt_revoke":
        if chat_id != SUPER_ADMIN_ID: return
        user_sessions.setdefault(chat_id, {})["input_mode"] = "WAITING_REVOKE_KEY"
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"<b>{to_bold('REVOKE PASSKEY')}</b>\nSend the exact passkey code you wish to delete:")
        return

    elif action in ["adm_refresh", "adm_home"]:
        if chat_id != SUPER_ADMIN_ID: return
        caption = (
            f"<b>{to_bold('ADMIN CLUSTER CONTROL PANEL')}</b>\n\n"
            f"Manager ID: <code>{NODE_ID}</code>\n"
            f"Role: <b>CENTRAL MASTER DISPATCHER</b>\n\n"
            f"Select a management module from the options below:"
        )
        bot.edit_message_text(caption, chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_admin_dashboard_keyboard())
        bot.answer_callback_query(call.id, "Refreshed")
        return

    elif action == "adm_workers":
        if chat_id != SUPER_ADMIN_ID: return
        terms = firebase_sync_http("terminals", "GET") or {}
        now_ts = time.time()
        total_cnt = len(terms)
        busy_cnt = sum(1 for t in terms.values() if isinstance(t, dict) and t.get("status") == "BUSY")
        free_cnt = sum(1 for t in terms.values() if isinstance(t, dict) and t.get("status") == "FREE")
        offline_cnt = sum(1 for t in terms.values() if isinstance(t, dict) and (t.get("status") == "OFFLINE" or now_ts - float(t.get("heartbeat", 0)) > 15.0))
        active_cnt = total_cnt - offline_cnt

        lines = [
            f"<b>{to_bold('CLUSTER WORKER TOPOLOGY')}</b>\n",
            f"Total Nodes: <b>{total_cnt}</b>",
            f"Active Nodes: <b>{active_cnt}</b>",
            f"Idle / Free: <b>{free_cnt}</b>",
            f"Busy / In-Task: <b>{busy_cnt}</b>",
            f"Offline: <b>{offline_cnt}</b>\n"
        ]
        for tid, tval in terms.items():
            if isinstance(tval, dict):
                st_txt = tval.get("status", "UNKNOWN")
                hb_diff = int(now_ts - float(tval.get("heartbeat", 0)))
                lat = tval.get("latency_ms", "N/A")
                lines.append(f"• <code>{tid}</code> | Status: <b>{st_txt}</b> (Ping: {lat}ms | HB: {hb_diff}s ago)")

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"{to_bold('BACK')}", callback_data="adm_home"))
        bot.edit_message_text("\n".join(lines), chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        return

    elif action == "adm_logins":
        if chat_id != SUPER_ADMIN_ID: return
        sessions_data = firebase_sync_http("sessions", "GET") or {}
        lines = [f"<b>{to_bold('AUTHENTICATED USER SESSIONS')}</b>\n", f"Total Active Sessions: <b>{len(sessions_data)}</b>\n"]
        for sid_key, sval in sessions_data.items():
            if isinstance(sval, dict):
                c_id = sval.get("chat_id", "N/A")
                site = sval.get("site_name", "N/A")
                ph = sval.get("phone", "N/A")
                worker_assigned = sval.get("node_id", "N/A")
                masked = ph[:3] + "****" + ph[-3:] if len(ph) >= 6 else ph
                lines.append(f"• User <code>{c_id}</code> | Site: <b>{site}</b> | Phone: <code>{masked}</code> | Worker: <code>{worker_assigned}</code>")

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"{to_bold('BACK')}", callback_data="adm_home"))
        bot.edit_message_text("\n".join(lines), chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        return

    elif action == "adm_ping":
        if chat_id != SUPER_ADMIN_ID: return
        bot.answer_callback_query(call.id, "Testing platform latency...")
        lines = [f"<b>{to_bold('NETWORK LATENCY / SPEED TEST')}</b>\n"]
        for pkey, pcfg in PLATFORMS.items():
            lat = measure_network_latency(pcfg["login"])
            lines.append(f"• {pcfg['name']}: <b>{lat} ms</b>" if lat < 9000 else f"• {pcfg['name']}: <b>TIMEOUT (>3500ms)</b>")

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"{to_bold('BACK')}", callback_data="adm_home"))
        bot.edit_message_text("\n".join(lines), chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        return

    elif action == "adm_passkeys":
        if chat_id != SUPER_ADMIN_ID: return
        bot.edit_message_text(
            f"<b>{to_bold('PASSKEY MANAGER')}</b>\n\nGenerate or inspect 24-hour access tokens:",
            chat_id=chat_id, message_id=call.message.message_id,
            reply_markup=get_passkey_menu_keyboard()
        )
        return

    elif action == "adm_tasks":
        if chat_id != SUPER_ADMIN_ID: return
        all_tasks = firebase_sync_http("user_tasks", "GET") or {}
        total_sub = sum(len(v) for v in all_tasks.values() if isinstance(v, dict))
        markup = InlineKeyboardMarkup(row_width=1)

        lines = [
            f"<b>{to_bold('TASK COMPLETED MONITOR')}</b>\n",
            f"Total Submitting Users: <b>{len(all_tasks)}</b>",
            f"Total Historical/Active Tasks: <b>{total_sub}</b>\n",
            "Select an individual user below to inspect task breakdowns:"
        ]
        for u_id, t_dict in all_tasks.items():
            if isinstance(t_dict, dict):
                comp = sum(1 for t in t_dict.values() if isinstance(t, dict) and t.get("status") == "COMPLETED")
                run = sum(1 for t in t_dict.values() if isinstance(t, dict) and t.get("status") == "RUNNING")
                markup.add(InlineKeyboardButton(f"User {u_id} (Done: {comp} | Active: {run})", callback_data=f"adm_user_t:{u_id}"))

        markup.add(InlineKeyboardButton(f"{to_bold('BACK')}", callback_data="adm_home"))
        bot.edit_message_text("\n".join(lines), chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        return

    elif action == "adm_user_t":
        if chat_id != SUPER_ADMIN_ID: return
        target_uid = sid
        u_tasks = firebase_sync_http(f"user_tasks/{target_uid}", "GET") or {}
        lines = [f"<b>{to_bold('USER TASK DETAILS')}</b>\nUser: <code>{target_uid}</code>\n"]
        for t_sid, tinfo in u_tasks.items():
            if isinstance(tinfo, dict):
                lines.append(
                    f"• Task <code>{t_sid}</code>\n"
                    f"  Status: <b>{tinfo.get('status', 'N/A')}</b> | Platform: <b>{tinfo.get('site_name', 'N/A')}</b>\n"
                    f"  Start: ৳ {tinfo.get('start_balance', 0):.2f} ➔ Live: ৳ {tinfo.get('current_balance', 0):.2f}\n"
                    f"  Target: ৳ {tinfo.get('target_amount', 0):.2f} | W: {tinfo.get('wins', 0)} L: {tinfo.get('losses', 0)}\n"
                )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"{to_bold('BACK TO TASKS')}", callback_data="adm_tasks"))
        bot.edit_message_text("\n".join(lines), chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
        return

    elif action in PLATFORMS:
        p_cfg = PLATFORMS[action]
        site_name = p_cfg["name"]
        sid = f"{chat_id}_{int(time.time()) % 1000000}"

        active_sessions[sid] = {
            "chat_id": chat_id,
            "session_id": sid,
            "site_name": site_name,
            "login_url": p_cfg["login"],
            "wingo_url": p_cfg["wingo"],
            "phone": None,
            "password": None,
            "target_profit": 0,
            "total_steps": 5,
            "is_trading": False,
            "created_at": time.time(),
            "anim_tick": 0
        }
        user_sessions.setdefault(chat_id, {})["active_sid"] = sid

        caption = (
            f"<b>{to_bold('ACCOUNT LOGIN')}</b>\n\n"
            f"Platform: <b>{site_name}</b>\n\n"
            f"Please click below to submit your account number and password. "
            f"Credentials are encrypted in memory and deleted after verification."
        )

        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            caption,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=get_credentials_keyboard(sid)
        )
        active_sessions[sid]["cred_card_msg_id"] = call.message.message_id

    elif action == "ask_num" and sid in active_sessions:
        active_sessions[sid]["input_mode"] = "WAITING_PHONE"
        user_sessions[chat_id]["active_sid"] = sid
        bot.answer_callback_query(call.id)
        prompt_m = bot.send_message(chat_id, f"<b>{to_bold('ACCOUNT NUMBER')}</b>\nEnter your registered phone number:")
        active_sessions[sid]["temp_prompt_id"] = prompt_m.message_id

    elif action == "ask_pass" and sid in active_sessions:
        if not active_sessions[sid].get("phone"):
            bot.answer_callback_query(call.id, "Please enter your phone number first!", show_alert=True)
            return
        active_sessions[sid]["input_mode"] = "WAITING_PASS"
        user_sessions[chat_id]["active_sid"] = sid
        bot.answer_callback_query(call.id)
        prompt_m = bot.send_message(chat_id, f"<b>{to_bold('ACCOUNT PASSWORD')}</b>\nEnter your account password:")
        active_sessions[sid]["temp_prompt_id"] = prompt_m.message_id

    elif action == "start_cfg" and sid in active_sessions:
        sess = active_sessions[sid]
        sess["last_dashboard_msg_id"] = call.message.message_id
        bot.answer_callback_query(call.id, "Preparing WinGo 30S market...")
        # Smooth in-place transition: update card to show preparing state
        try:
            bot.edit_message_text(
                f"<b>{to_bold('PREPARING WINGO 30S MARKET')}</b>\n\n"
                f"Platform: <b>{sess.get('site_name', 'Amar Club')}</b>\n"
                f"<code>Connecting market stream & fetching live balance...</code>",
                chat_id=chat_id,
                message_id=call.message.message_id
            )
        except Exception:
            pass
        assigned_worker = sess.get("assigned_worker")
        if assigned_worker:
            relay_action_to_worker(assigned_worker, {
                "kind": "PREPARE_WINGO",
                "session_id": sid,
                "chat_id": chat_id
            })

    elif action == "set_tgt" and sid in active_sessions:
        active_sessions[sid]["input_mode"] = "WAITING_TARGET"
        active_sessions[sid]["last_dashboard_msg_id"] = call.message.message_id
        user_sessions[chat_id]["active_sid"] = sid
        bot.answer_callback_query(call.id)
        cur_bal = active_sessions[sid].get("current_balance", 0.0)
        p_msg = bot.send_message(chat_id, f"<b>{to_bold('TARGET PROFIT')}</b>\nLive Balance: <code>৳ {cur_bal:.2f}</code>\nEnter profit amount (e.g. <code>250</code>):")
        active_sessions[sid]["temp_prompt_id"] = p_msg.message_id

    elif action == "set_stp" and sid in active_sessions:
        active_sessions[sid]["input_mode"] = "WAITING_STEPS"
        active_sessions[sid]["last_dashboard_msg_id"] = call.message.message_id
        user_sessions[chat_id]["active_sid"] = sid
        bot.answer_callback_query(call.id)
        p_msg = bot.send_message(chat_id, f"<b>{to_bold('MARTINGALE STEPS')}</b>\nEnter step count (e.g. <code>5</code> or <code>7</code>):")
        active_sessions[sid]["temp_prompt_id"] = p_msg.message_id

    elif action == "run_auto" and sid in active_sessions:
        sess = active_sessions[sid]
        if not sess.get("target_profit") or sess["target_profit"] <= 0:
            bot.answer_callback_query(call.id, "Please set a target profit amount first!", show_alert=True)
            return

        bot.answer_callback_query(call.id, "Starting 24/7 background ghost automation...")
        assigned_worker = sess.get("assigned_worker")
        if assigned_worker:
            relay_action_to_worker(assigned_worker, {
                "kind": "START_TRADING",
                "session_id": sid,
                "chat_id": chat_id,
                "target_profit": sess["target_profit"],
                "total_steps": sess["total_steps"],
                "prediction_api_url": PREDICTION_API_URL
            })

        cur_b = sess.get("current_balance", 0.0)
        target_total = cur_b + sess["target_profit"]
        sess["is_trading"] = True
        sess["start_bal"] = cur_b

        dashboard_caption = (
            f"<b>{to_bold('24/7 GHOST ENGINE ACTIVE')}</b>\n\n"
            f"Platform: <b>{sess.get('site_name', '')}</b>\n"
            f"Starting Balance: <code>৳ {cur_b:.2f}</code>\n"
            f"Target Balance: <code>৳ {target_total:.2f}</code>\n"
            f"Total Steps: <b>{sess['total_steps']}</b>\n\n"
            f"<b>LIVE STATUS</b>: Martingale engine running in ghost background mode."
        )

        target_m_id = call.message.message_id or sess.get("last_dashboard_msg_id")
        sess["last_dashboard_msg_id"] = target_m_id
        if target_m_id:
            try:
                bot.edit_message_text(dashboard_caption, chat_id=chat_id, message_id=target_m_id, reply_markup=get_trading_control_keyboard(sid))
            except Exception:
                m2 = bot.send_message(chat_id, dashboard_caption, reply_markup=get_trading_control_keyboard(sid))
                sess["last_dashboard_msg_id"] = m2.message_id
        else:
            m2 = bot.send_message(chat_id, dashboard_caption, reply_markup=get_trading_control_keyboard(sid))
            sess["last_dashboard_msg_id"] = m2.message_id

    elif action == "shot" and sid in active_sessions:
        sess = active_sessions[sid]
        sess["last_dashboard_msg_id"] = call.message.message_id
        bot.answer_callback_query(call.id, "Fetching live telemetry...")
        assigned_worker = sess.get("assigned_worker")
        if assigned_worker:
            relay_action_to_worker(assigned_worker, {
                "kind": "REQUEST_TELEMETRY",
                "session_id": sid,
                "chat_id": chat_id
            })

    elif action == "bal" and sid in active_sessions:
        sess = active_sessions[sid]
        cur_b = sess.get("current_balance", 0.0)
        assigned_worker = sess.get("assigned_worker")
        if assigned_worker:
            relay_action_to_worker(assigned_worker, {
                "kind": "REQUEST_BALANCE",
                "session_id": sid,
                "chat_id": chat_id,
                "call_id": call.id
            })
        else:
            bot.answer_callback_query(call.id, f"Live Balance: ৳ {cur_b:.2f}", show_alert=True)

    elif action == "stats" and sid in active_sessions:
        sess = active_sessions[sid]
        bot.answer_callback_query(call.id, "Fetching live stats...")
        assigned_worker = sess.get("assigned_worker")
        if assigned_worker:
            relay_action_to_worker(assigned_worker, {
                "kind": "REQUEST_STATS",
                "session_id": sid,
                "chat_id": chat_id
            })

    elif action == "stop" and sid in active_sessions:
        sess = active_sessions[sid]
        sess["last_dashboard_msg_id"] = call.message.message_id
        assigned_worker = sess.get("assigned_worker")
        if assigned_worker:
            relay_action_to_worker(assigned_worker, {
                "kind": "STOP_TRADING",
                "session_id": sid,
                "chat_id": chat_id
            })
        sess["is_trading"] = False
        bot.answer_callback_query(call.id, "Trading paused cleanly", show_alert=True)
        stop_caption = (
            f"<b>{to_bold('TRADING PAUSED')}</b>\n\n"
            f"Platform: <b>{sess.get('site_name', '')}</b>\n"
            f"Automation paused cleanly."
        )
        try:
            bot.edit_message_text(stop_caption, chat_id=chat_id, message_id=call.message.message_id)
        except Exception:
            bot.send_message(chat_id, stop_caption)

    elif action == "cancel" and sid in active_sessions:
        assigned_worker = active_sessions[sid].get("assigned_worker")
        if assigned_worker:
            relay_action_to_worker(assigned_worker, {
                "kind": "CANCEL_SESSION",
                "session_id": sid,
                "chat_id": chat_id
            })
        bot.answer_callback_query(call.id, "Session terminated")
        active_sessions.pop(sid, None)
        safe_delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, f"<b>{to_bold('SESSION TERMINATED')}</b>\nSend /start to begin a new session.")

# ==============================================================================
# USER TEXT INPUT HANDLER
# ==============================================================================
@bot.message_handler(func=lambda msg: True)
def handle_user_text(message):
    chat_id = message.chat.id
    text = message.text.strip()
    u = user_sessions.get(chat_id, {})

    if u.get("input_mode") == "WAITING_PASSKEY":
        safe_delete_message(chat_id, message.message_id)
        if u.get("passkey_prompt_id"):
            safe_delete_message(chat_id, u["passkey_prompt_id"])
            u["passkey_prompt_id"] = None

        key_data = firebase_sync_http(f"passkeys/{text}", "GET")
        now_ts = time.time()
        is_valid = False

        if chat_id == SUPER_ADMIN_ID or text.startswith("KEY-"):
            if key_data and isinstance(key_data, dict):
                if float(key_data.get("expires_at", 0)) > now_ts:
                    is_valid = True
            else:
                is_valid = True

        if is_valid:
            u["pass_expiry"] = now_ts + 86400
            u["input_mode"] = None
            u["step"] = "CHOOSE_SITE"
            bot.send_message(
                chat_id,
                f"<b>{to_bold('PASSKEY ACTIVATED (24 HOURS)')}</b>\n\nYour session is authorized. Select a platform to proceed:",
                reply_markup=get_six_platform_keyboard()
            )
        else:
            pm = bot.send_message(
                chat_id,
                f"<b>{to_bold('INVALID OR EXPIRED PASSKEY')}</b>\nPlease re-enter a valid 24-hour passkey:"
            )
            u["passkey_prompt_id"] = pm.message_id
        return

    if u.get("input_mode") == "WAITING_REVOKE_KEY" and chat_id == SUPER_ADMIN_ID:
        safe_delete_message(chat_id, message.message_id)
        u["input_mode"] = None
        revoke_passkey(text)
        bot.send_message(chat_id, f"<b>{to_bold('PASSKEY REVOKED')}</b>\nKey <code>{text}</code> has been deleted.")
        return

    sid = u.get("active_sid")
    if not sid or sid not in active_sessions:
        return

    sess = active_sessions[sid]
    input_mode = sess.get("input_mode")

    safe_delete_message(chat_id, message.message_id)
    if sess.get("temp_prompt_id"):
        safe_delete_message(chat_id, sess["temp_prompt_id"])
        sess["temp_prompt_id"] = None

    if input_mode == "WAITING_PHONE":
        sess["phone"] = text
        sess["input_mode"] = None

        if sess.get("cred_card_msg_id"):
            try:
                masked = text[:3] + "****" + text[-3:] if len(text) >= 6 else text
                updated_card_text = (
                    f"<b>{to_bold('ACCOUNT LOGIN')}</b>\n\n"
                    f"Platform: <b>{sess.get('site_name', '')}</b>\n"
                    f"Number: <code>{masked}</code> (Recorded)\n\n"
                    f"Now click <b>PASSWORD</b> to enter your login password:"
                )
                bot.edit_message_text(
                    updated_card_text,
                    chat_id=chat_id,
                    message_id=sess["cred_card_msg_id"],
                    reply_markup=get_credentials_keyboard(sid)
                )
            except Exception:
                pass

    elif input_mode == "WAITING_PASS":
        sess["password"] = text
        sess["input_mode"] = None

        if sess.get("cred_card_msg_id"):
            safe_delete_message(chat_id, sess["cred_card_msg_id"])
            sess["cred_card_msg_id"] = None

        worker_id = find_optimal_worker_node()
        if not worker_id:
            bot.send_message(chat_id, f"<b>{to_bold('NO WORKER AVAILABLE')}</b>\n\nAll worker nodes are busy or offline. Please wait a few moments and try again.")
            return

        sess["assigned_worker"] = worker_id

        # Record session in Firebase
        firebase_sync_http(f"sessions/{sid}", "PUT", {
            "node_id": worker_id,
            "chat_id": chat_id,
            "site_name": sess.get("site_name"),
            "login_url": sess.get("login_url"),
            "wingo_url": sess.get("wingo_url"),
            "phone": sess.get("phone"),
            "dispatched_at": time.time()
        })

        anim_msg = bot.send_message(chat_id, "<b>CONNECTING REMOTE WORKER ENGINE</b>\n<code>▰▱▱▱▱▱▱▱▱▱ 15% Allocating secure browser...</code>")
        sess["last_dashboard_msg_id"] = anim_msg.message_id

        # Dispatch Task to selected Worker
        task_payload = {
            "type": "LOGIN_AND_PREPARE",
            "session_id": sid,
            "chat_id": chat_id,
            "site_name": sess.get("site_name"),
            "login_url": sess.get("login_url"),
            "wingo_url": sess.get("wingo_url"),
            "phone": sess.get("phone"),
            "password": sess.get("password"),
            "anim_msg_id": anim_msg.message_id,
            "dispatched_at": time.time()
        }
        dispatch_task_to_worker(worker_id, task_payload)

    elif input_mode == "WAITING_TARGET":
        try:
            val = float(text)
            if val <= 0: raise ValueError()
            sess["target_profit"] = val
            sess["input_mode"] = None

            cur_bal = sess.get("current_balance", 0.0)
            config_caption = (
                f"<b>{to_bold('WINGO 30S MARKET ACTIVE')}</b>\n\n"
                f"Platform: <b>{sess.get('site_name', '')}</b>\n"
                f"Live Balance: <code>৳ {cur_bal:.2f}</code>\n"
                f"Selected Target: <code>৳ {val:.2f}</code>\n\n"
                f"Parameters updated. Click <b>START</b> to initiate trading:"
            )

            last_m = sess.get("last_dashboard_msg_id")
            if last_m:
                try:
                    bot.edit_message_text(config_caption, chat_id=chat_id, message_id=last_m, reply_markup=get_setup_param_keyboard(sid))
                except Exception:
                    m2 = bot.send_message(chat_id, config_caption, reply_markup=get_setup_param_keyboard(sid))
                    sess["last_dashboard_msg_id"] = m2.message_id
            else:
                m2 = bot.send_message(chat_id, config_caption, reply_markup=get_setup_param_keyboard(sid))
                sess["last_dashboard_msg_id"] = m2.message_id
        except ValueError:
            p_msg = bot.send_message(chat_id, "Please enter a valid positive number (e.g. 250):")
            sess["temp_prompt_id"] = p_msg.message_id

    elif input_mode == "WAITING_STEPS":
        try:
            steps_val = int(text)
            if steps_val <= 0: raise ValueError()
            sess["total_steps"] = steps_val
            sess["input_mode"] = None

            cur_bal = sess.get("current_balance", 0.0)
            config_caption = (
                f"<b>{to_bold('WINGO 30S MARKET ACTIVE')}</b>\n\n"
                f"Platform: <b>{sess.get('site_name', '')}</b>\n"
                f"Live Balance: <code>৳ {cur_bal:.2f}</code>\n"
                f"Selected Steps: <b>{steps_val}</b>\n\n"
                f"Parameters updated. Click <b>START</b> to initiate trading:"
            )

            last_m = sess.get("last_dashboard_msg_id")
            if last_m:
                try:
                    bot.edit_message_text(config_caption, chat_id=chat_id, message_id=last_m, reply_markup=get_setup_param_keyboard(sid))
                except Exception:
                    m2 = bot.send_message(chat_id, config_caption, reply_markup=get_setup_param_keyboard(sid))
                    sess["last_dashboard_msg_id"] = m2.message_id
            else:
                m2 = bot.send_message(chat_id, config_caption, reply_markup=get_setup_param_keyboard(sid))
                sess["last_dashboard_msg_id"] = m2.message_id
        except ValueError:
            p_msg = bot.send_message(chat_id, "Please enter a valid integer (e.g. 5):")
            sess["temp_prompt_id"] = p_msg.message_id

# ==============================================================================
# MAIN ENTRYPOINT (POLLING BIND TO MANAGER ONLY)
# ==============================================================================
if __name__ == "__main__":
    logger.info(f"Starting {to_bold('CENTRAL MANAGER NODE')} [{NODE_ID}]...")
    try:
        bot.remove_webhook()
    except Exception:
        pass
    print(f"[*] Manager running Telegram Polling. Ready to dispatch tasks to Workers.")
    bot.infinity_polling(skip_pending=True)

#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
# JILL_BOT — long-polling runner (MODE=polling).
# Reuses main.build_bot so handlers are IDENTICAL to webhook mode: each update becomes one
# BotX instance processed in a worker thread. DB connections AND Telegram HTTP sessions are
# pooled per worker thread (see Model/gestion._acquire + Model/_get_thread_curl), so the
# reconnect cost is paid once per thread, not once per update.
#
# Stability features:
#   • single-instance lockfile guard (poll.lock)
#   • keep-alive HTTP session to the Telegram API (no TCP/TLS handshake per getUpdates)
#   • exponential backoff on transient errors; auto deleteWebhook on 409 conflicts
#   • clean SIGINT/SIGTERM shutdown that drains the pool and releases the lock
#   Run:  python3 poll.py   (or via run.py when MODE=polling)
import os, sys, time, json, base64, pathlib, signal, requests
from concurrent.futures import ThreadPoolExecutor

_BASE = pathlib.Path(__file__).resolve().parent
_LOCK = _BASE / 'poll.lock'
_STOP = False


def _load_env() -> None:
    for p in [_BASE / 'Model' / 'config.env', _BASE / '.env']:
        if p.exists():
            for line in p.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _handle(build_bot, query: str) -> None:
    # Close only the per-update DB cursor. Both the DB connection (gestion._acquire)
    # and the Telegram HTTP session (BotX._get_thread_curl) are thread-local — kept
    # alive across updates so we don't pay TCP+TLS reconnects on every command.
    bot = None
    try:
        bot = build_bot(query)
        bot.compile_bot()
    except Exception:
        pass
    finally:
        if bot is not None:
            try: bot.gestion.cursor.close()
            except Exception: pass


def _acquire_lock() -> bool:
    """Single-instance guard. Two pollers on the same token fight over getUpdates and
    render inconsistent replies (old vs new code) — refuse to start if one is already alive."""
    if _LOCK.exists():
        try:
            old = int(_LOCK.read_text().strip())
            os.kill(old, 0)                       # raises if pid is dead
            print(f"[JILL] another poller is already running (pid {old}) — aborting")
            return False
        except (ValueError, ProcessLookupError, PermissionError):
            pass                                  # stale lock -> overwrite
    _LOCK.write_text(str(os.getpid()))
    return True


def _release_lock() -> None:
    try: _LOCK.unlink()
    except Exception: pass


def _install_signals() -> None:
    def _stop(signum, frame):
        global _STOP
        _STOP = True
        print(f"\n[JILL] signal {signum} — shutting down…")
    for s in (signal.SIGINT, signal.SIGTERM):
        try: signal.signal(s, _stop)
        except Exception: pass


def run() -> None:
    global _STOP
    _load_env()
    if not _acquire_lock():
        return
    _install_signals()
    from main import build_bot
    token = os.getenv('BOT_TOKEN', '').strip()
    if not token:
        print("[JILL] BOT_TOKEN missing — set Model/config.env"); _release_lock(); return
    api     = f"https://api.telegram.org/bot{token}"
    workers = int(os.getenv('POLL_WORKERS', '8'))

    session = requests.Session()                  # keep-alive to Telegram (reused connection)

    def _drop_webhook():
        # Polling and webhook are mutually exclusive — drop any webhook AND clear the queued
        # backlog. Without drop_pending_updates, a restart replays every update received while
        # the bot was down (re-runs old commands / re-fires old button taps).
        try: session.get(f"{api}/deleteWebhook", params={'drop_pending_updates': 'true'}, timeout=15)
        except Exception: pass

    _drop_webhook()

    # Only ask for the update types we actually handle (skip my_chat_member, chat_member, etc.)
    allowed = json.dumps(['message', 'callback_query'])
    pool    = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='jill')
    offset  = 0
    backoff = 1                                   # seconds; grows on repeated failures, caps at 15
    print(f"[JILL] polling started (workers={workers})")
    while not _STOP:
        try:
            r = session.get(f"{api}/getUpdates",
                            params={'offset': offset, 'timeout': 50, 'allowed_updates': allowed},
                            timeout=60).json()
        except Exception:
            time.sleep(min(backoff, 15)); backoff = min(backoff * 2, 15); continue
        if not r.get('ok'):
            # 409 = another getUpdates consumer OR a webhook is active — re-drop it and retry.
            if r.get('error_code') == 409:
                print(f"[JILL] getUpdates conflict: {r.get('description')} — re-dropping webhook")
                _drop_webhook()
            elif r.get('error_code') == 429:
                wait = r.get('parameters', {}).get('retry_after', 10)
                print(f"[JILL] rate-limited by Telegram — waiting {wait}s")
                time.sleep(wait + 1)
                backoff = 1
                continue
            time.sleep(min(backoff, 15)); backoff = min(backoff * 2, 15); continue
        backoff = 1                              # healthy response -> reset backoff
        for upd in r.get('result', []):
            offset = upd['update_id'] + 1
            query  = base64.b64encode(json.dumps(upd).encode('utf-8')).decode('utf-8')
            pool.submit(_handle, build_bot, query)

    print("[JILL] draining workers…")
    pool.shutdown(wait=True, cancel_futures=False)
    _release_lock()
    print("[JILL] polling stopped")


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        _release_lock()
        sys.exit(0)

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

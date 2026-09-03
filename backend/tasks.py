#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
# JILL_BOT — scheduled automation. Run from cron (from the project dir), e.g.:
#   0  12 * * *  cd ~/www && python3 tasks.py expiry     # daily 12:00 — warn premiums expiring in <24h
#   30 *  * * *  cd ~/www && python3 tasks.py cleanup     # hourly    — drop card-use rows older than 24h
import sys, os, datetime, pathlib, requests
from Model.gestion import gestion

_BASE = pathlib.Path(__file__).resolve().parent


def _load_env() -> None:
    for p in [_BASE / 'Model' / 'config.env', _BASE / '.env']:
        if p.exists():
            for line in p.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()
_API = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN', '')}"


def _send(chat_id, text) -> None:
    try:
        requests.post(f"{_API}/sendMessage", data={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}, timeout=10)
    except Exception:
        pass


def _g() -> gestion:
    return gestion(os.getenv('DB_HOST', ''), os.getenv('DB_NAME', ''), os.getenv('DB_USER', ''), os.getenv('DB_PASS', ''))


def _bi(text: str) -> str:
    out = []
    for c in str(text):
        o = ord(c)
        if   65 <= o <= 90:  out.append(chr(0x1D63C + o - 65))
        elif 97 <= o <= 122: out.append(chr(0x1D656 + o - 97))
        else:                out.append(c)
    return ''.join(out)


def task_expiry() -> None:
    """DM premium users whose access expires within the next 24h."""
    g    = _g()
    now  = datetime.datetime.now()
    soon = now + datetime.timedelta(hours=24)
    data = g.no_commit("SELECT user_id, n_bil FROM users WHERE rango = 'premium'")
    rows = data['data'] if data['status'] and data['data'] else []
    n = 0
    for uid, n_bil in rows:
        exp = g._set(n_bil)
        if exp and now < exp <= soon:
            _send(uid, f"⏳ {_bi('Premium Expiring')}\n────────────────────\n🍸 {_bi('Your premium expires in less than 24h')}\n🍸 {_bi('Renew with')}: <code>/prices</code>")
            n += 1
    print(f"[expiry] notified {n} user(s)")


def task_cleanup() -> None:
    """Remove card-usage rows older than 24h (rate-limit/abuse window has passed)."""
    g      = _g()
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
    g.commit("DELETE FROM card_uses WHERE used_at < %s", (str(cutoff),))
    print("[cleanup] old card_uses removed")


if __name__ == '__main__':
    task = sys.argv[1] if len(sys.argv) > 1 else ''
    if   task == 'expiry':  task_expiry()
    elif task == 'cleanup': task_cleanup()
    else: print("usage: python3 tasks.py expiry|cleanup")

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

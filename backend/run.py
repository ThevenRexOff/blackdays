#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
# JILL_BOT — entrypoint. Picks the run mode from Model/config.env  (MODE=webhook | polling).
#
#   MODE=polling   ->  python3 run.py   starts the long-polling loop (no server needed).
#   MODE=webhook   ->  python3 run.py   registers the webhook at WEBHOOK_URL; Telegram then
#                      POSTs updates to index.php (the PHP receiver launches main.py per update).
import os, pathlib, requests

_BASE = pathlib.Path(__file__).resolve().parent


def _load_env() -> None:
    for p in [_BASE / 'Model' / 'config.env', _BASE / '.env']:
        if p.exists():
            for line in p.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> None:
    _load_env()
    token = os.getenv('BOT_TOKEN', '').strip()
    if not token:
        print("[JILL] BOT_TOKEN missing — set Model/config.env"); return
    api  = f"https://api.telegram.org/bot{token}"
    mode = os.getenv('MODE', 'webhook').strip().lower()

    if mode == 'polling':
        import poll
        poll.run()
    else:  # webhook
        url = os.getenv('WEBHOOK_URL', '').strip()
        if not url:
            print("[JILL] MODE=webhook but WEBHOOK_URL is empty — set it in Model/config.env (e.g. https://yourdomain/index.php)")
            return
        r = requests.get(f"{api}/setWebhook", params={'url': url, 'drop_pending_updates': 'True'}, timeout=15).json()
        print("[JILL] setWebhook ->", r)


if __name__ == '__main__':
    main()

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

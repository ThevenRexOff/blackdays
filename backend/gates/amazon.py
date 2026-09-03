# Pure gate motor for 'amazon' — no Telegram-bot dependency.
#
# Uses the faithful US-billing + CA-prime CookieContext port. Supports an
# optional proxy (passed via `ctx['proxy']` from apis/gates.py).

import time, threading, html as _html_mod

from Commands.Gates.mamazon import CookieContext

_GATEWAY = 'Amazon'

def _run_flow(cc_str, cookie, proxy=None):
    """Run the Amazon billing flow once and normalise the result to the shape the
    handlers below expect. Returns (status, response) where status is
    'Approved ✅' | 'Declined ❌' | 'Error ⚠️'."""
    try:
        r = CookieContext(card=cc_str, cookie=cookie, proxy=proxy).buildFlowBilling()
    except Exception as e:
        return ('Error ⚠️', str(e)[:200])
    if not r.get('status'):
        if 'apiResponse' in r:
            return (r.get('apiResponse', 'Error ⚠️'), r.get('response', 'Unknown Amazon response'))
        return ('Error ⚠️', r.get('message', 'Gate error'))
    resp = r.get('response', '')
    if r.get('card_info'):
        resp = (f"{resp} | {r['card_info']}").strip(' |')
    return (r.get('apiResponse', 'Error ⚠️'), resp)

def run_check(cc, bin_data, ctx=None):
    """Single-card checker for /mass. `ctx` carries {'cookie': <amazon cookie>, 'proxy': <optional>}.
    Returns {'status': 'Approved ✅'|'Declined ❌'|'Error ⚠️', 'response': ...}."""
    ctx = ctx or {}
    cookie = ctx.get('cookie')
    if not cookie:
        return {'status': 'Error ⚠️', 'response': 'No Amazon cookie (use /cookie)'}
    cc_str = f'{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}'
    status, response = _run_flow(cc_str, cookie, ctx.get('proxy'))
    return {'status': status, 'response': response}

# ══════════════════════════════════════════════════════════════════════════
#  PURE motor for gate: disney (Disney+ Plans MX). No Telegram-bot dependency.
# ══════════════════════════════════════════════════════════════════════════
import os


def _run_flow(card_input: str, proxy=None, capsolver_key: str = '') -> dict:
    from Commands.Gates.disney.disney_core import processDisneyFlow
    return processDisneyFlow(card_input, proxy=proxy, capsolver_key=capsolver_key, retries=0)


def _checker(cc, binData, proxy=None, capsolver_key=''):
    try:
        card = f'{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}'
        return _run_flow(card, proxy=proxy, capsolver_key=capsolver_key)
    except Exception as e:
        return {'status': False, 'raise': str(e)[:300]}


def run_check(cc, bin_data, ctx=None):
    from api.proxies import get_proxy as _pool_proxy
    ctx = ctx or {}
    capsolver = (ctx.get('capsolver_key') or '') or os.getenv('CAPSOLVER_KEY', '')
    card = f'{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}'
    last_exc = None
    for _attempt in range(4):
        proxy = (ctx.get('proxy') or '') or _pool_proxy('MX')  # rotate on each attempt
        try:
            r = _checker(cc, bin_data, proxy=proxy, capsolver_key=capsolver)
            if r.get('status'):
                return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌',
                        'response': r.get('response') or r.get('apiResponse') or ''}
            last_exc = r.get('raise') or r.get('message', 'Gate error')
        except Exception as e:
            last_exc = str(e)[:300]
    return {'status': 'Error ⚠️', 'response': last_exc}
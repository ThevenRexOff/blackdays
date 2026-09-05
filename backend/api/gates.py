# ══════════════════════════════════════════════════════════════════════════
#  JILL_BOT API — gate orchestration.
#  ─ /gate/mj /gate/mm /gate/wr /gate/br /gate/bl /gate/dns /gate/rc /gate/op
#  ─ /gate/pd /gate/wu /gate/zb /gate/ps          (1-card, run_check)
#  ─ /gate/amz /gate/amzg                         (Amazon — requires cookie)
#  ─ /gate/tcl  (Telcel MX), /gate/em (Netflix), /gate/ds (Disney+)
#  Every gate checks a SINGLE card. The actual engines live in gates/ and
#  Commands/Gates/ — this module only routes, validates and normalizes.
# ══════════════════════════════════════════════════════════════════════════
import time

from api.core import parse_card, bin_info, get_params

from config import load_env

_RUN_CHECK_GATES = {
    'mj':   'gates.mj',
    'mm':   'gates.mm',
    'wr':   'gates.wr',
    'br':   'gates.br',
    'bl':   'gates.bl',
    'dns':  'gates.dns',
    'rc':   'gates.rc',
    'op':   'gates.op',
    'pd':   'gates.pd',
    'wu':   'gates.wu',
    'zb':   'gates.zb',
    'ps':   'gates.ps',
    'shopify': 'gates.shopify',
    'amz':  'gates.amazon',
    'amazon': 'gates.amazon',
}

_ALIASES = {
    'amz': 'amazon', 'amzg': 'amazon',
    'tcl': 'telcel', 'telcel': 'telcel',
    'em': 'netflix', 'netflix': 'netflix',
    'ds': 'disney', 'disney': 'disney',
    'telmex': 'zb', 'bait': 'ps', 'sfy': 'shopify',
}

# Parameters each gate REQUIRES beyond `card`. Missing ones produce a 4xx.
# A list item may be a single param name or a tuple of alternatives (any-of).
_GATE_REQUIRED = {
    'amazon': ('cookie',),
    'telcel': ('phone',),
    'ps': ('phone',),
    'zb': ('phone',),
    'shopify': (('website', 'url', 'site'),),
    'netflix': (), 'disney': (),
}


def _load(module: str):
    import importlib
    return importlib.import_module(module)


def _run_one(cc_parts: list, bin_data: dict, gate: str, params: dict) -> dict:
    """Run a single card through a gate checkout, returning a normalized result."""
    mod = _load(_RUN_CHECK_GATES[gate])
    ctx = {}
    extra = {}
    proxy = (params or {}).get('proxy') or ''
    cookie = (params or {}).get('cookie') or ''
    # Amazon gate uses cookie directly - no proxy needed
    if gate == 'amz' and cookie:
        ctx['cookie'] = cookie
    if gate in ('bl', 'pd', 'zb', 'ps') and proxy:
        ctx['proxy'] = proxy
    if gate == 'shopify':
        ctx['website'] = (params or {}).get('website') or (params or {}).get('site') or (params or {}).get('url') or ''
        ctx['address'] = (params or {}).get('address')
        ctx['email'] = (params or {}).get('email')
        ctx['product'] = (params or {}).get('product')
        if proxy:
            ctx['proxy'] = proxy
    if gate in ('ps', 'zb'):
        phone = (params or {}).get('phone') or ''
        monto = (params or {}).get('monto') or ''
        if phone or monto:
            checker = getattr(mod, '_checker', None)
            if checker:
                kwargs = {}
                if phone:
                    kwargs['phone'] = phone
                if monto:
                    kwargs['monto'] = monto
                if proxy:
                    kwargs['proxy'] = proxy
                return normalized(checker(cc_parts, bin_data, **kwargs))
    fn = getattr(mod, 'run_check', None)
    if not callable(fn):
        return {'status': 'Error ⚠️', 'response': f'Gate [{gate}] has no run_check'}
    return normalized(fn(cc_parts, bin_data, ctx) if ctx else fn(cc_parts, bin_data))


def normalized(r: dict) -> dict:
    if not isinstance(r, dict):
        return {'status': 'Error ⚠️', 'response': str(r)[:200]}
    if r.get('status') is False:
        return {'status': 'Error ⚠️', 'response': r.get('raise') or r.get('response') or 'Gate error'}
    status = r.get('status', '')
    if status in ('Approved ✅', 'Declined ❌', 'Live Card 🟢', 'Error ⚠️', 'Unknown ⚠️'):
        return r
    success = bool(r.get('success'))
    resp = r.get('response') or ''
    return {'status': 'Approved ✅' if success else 'Declined ❌', 'response': resp}


def _mask_card(card: str) -> str:
    digits = ''.join(ch for ch in (card or '') if ch.isdigit())
    if len(digits) >= 10:
        return f"{digits[:6]}...{digits[-4:]}"
    return (card or '')[:16]


def _is_infra_error(status) -> bool:
    """True when the gate failed at infrastructure level (vs a normal decline).
    Normal outcomes (Approved/Declined/Live/Dead) never trigger admin alerts."""
    if status is False:
        return True
    s = str(status or '').strip().lower()
    return 'error' in s or 'unknown' in s or s in ('', 'false')


def gate_run(params: dict) -> dict:
    t0 = time.time()

    def _done(result: dict, raw_card: str) -> dict:
        result.pop('success', None)
        result['card'] = raw_card
        result['time_taken'] = round(time.time() - t0, 2)
        return result

    name, card, phone, monto, cookie, proxy = get_params(params, {},
                                                        'gate', 'card', 'phone', 'monto', 'cookie', 'proxy')
    name = (name or '').lower().strip()
    gate = _ALIASES.get(name, name)
    if gate not in _RUN_CHECK_GATES and gate not in ('amazon', 'telcel', 'netflix', 'disney'):
        return {'status': False, 'error': f'Unknown gate [{name}]. See /apis/routes'}

    # Required-parameter validation (beyond card, which parse_card enforces below).
    missing = []
    for alt in _GATE_REQUIRED.get(gate, ()):
        names = alt if isinstance(alt, tuple) else (alt,)
        present = any(str((params or {}).get(n) or '').strip() for n in names)
        if not present:
            missing.append(' or '.join(names))
    if missing:
        return {'status': False, 'code': 'MISSING_PARAM',
                'error': f"Gate [{gate}] is missing required parameter(s): {', '.join(missing)}"}

    extra = {'phone': phone, 'monto': monto, 'cookie': cookie, 'proxy': proxy}

    parsed = parse_card(card)
    if not parsed.get('status'):
        return {'status': False, 'error': parsed.get('raise')}

    try:
        if gate == 'telcel':
            result = _done(gate_telcel(parsed, extra), card)
        elif gate == 'netflix':
            result = _done(gate_netflix(parsed), card)
        elif gate == 'disney':
            result = _done(gate_disney(parsed), card)
        elif gate == 'amazon':
            if not cookie:
                result = {'status': False, 'error': 'Amazon gate requires a cookie parameter'}
            else:
                result = _done(_run_one(parsed['parts'], bin_info(parsed['parts'][0]), 'amz', extra), card)
        elif gate == 'shopify':
            if not (params.get('website') or params.get('site') or params.get('url')):
                result = {'status': 'error', 'code': 'NO_API_URL', 'card': card,
                          'time_taken': round(time.time() - t0, 2)}
            else:
                result = _done(_run_one(parsed['parts'], bin_info(parsed['parts'][0]), 'shopify', params), card)
        else:
            result = _done(_run_one(parsed['parts'], bin_info(parsed['parts'][0]), gate, extra), card)

        if _is_infra_error(result.get('status')):
            _notify_gate_error(gate, result, card=card, params=params)
        return result
    except Exception as exc:
        import traceback as _tb
        result = {'status': False, 'error': f'Gate [{gate}] internal error: {exc}', 'card': card,
                  'time_taken': round(time.time() - t0, 2)}
        _notify_gate_error(gate, result, card=card, params=params,
                           trace=_tb.format_exc())
        return result


def _notify_gate_error(gate: str, result: dict, *, card: str = '', params: dict = None, trace: str = ''):
    """Notify admins via Telegram when a gate returns an infrastructure error."""
    try:
        from api.telegram_alert import notify_gate_error
        body = dict(result)
        body.pop('card', None)  # keep the full card private in the alert body
        user = (params or {}).get('user') or (params or {}).get('username') or ''
        notify_gate_error(gate, body, user=user, card_mask=_mask_card(card), trace=trace)
    except Exception:
        # Never let a notification failure break the gate response.
        pass


def gate_telcel(parsed: dict, extra: dict) -> dict:
    from Commands.Gates.telcel_core import main
    monto = extra.get('monto') or '100'
    numero = extra.get('phone') or ''
    if not numero:
        return {'status': False, 'error': 'Telcel gate requires a phone parameter'}
    r = main(parsed['card'], monto, numero)
    return {'card': parsed['card'], 'phone': numero, 'monto': monto, **r}


def gate_netflix(parsed: dict) -> dict:
    load_env()
    from gates.netflix import run_check as netflix_rc
    result = netflix_rc(parsed['parts'], bin_info(parsed['parts'][0]))
    return {'card': parsed['card'], **result}


def gate_disney(parsed: dict) -> dict:
    load_env()
    from gates.disney import run_check as disney_rc
    result = disney_rc(parsed['parts'], bin_info(parsed['parts'][0]))
    return {'card': parsed['card'], **result}
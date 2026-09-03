# ══════════════════════════════════════════════════════════════════════════
#  Gate endpoints. Most gates share the `run_check(cc, bin_data, ctx)` contract.
#  ─ /gate/mj /gate/mm /gate/wr /gate/br /gate/bl /gate/dns /gate/rc /gate/op
#  ─ /gate/pd /gate/wu /gate/zb /gate/ps          (1-card, run_check)
#  ─ /gate/amz /gate/amzg                         (Amazon — requires cookie)
#  ─ /gate/tcl  (Telcel MX), /gate/em (Netflix), /gate/ds (Disney+)
#  Every gate checks a SINGLE card.
# ══════════════════════════════════════════════════════════════════════════
import os
import time

from apis.core import load_env, parse_card, bin_info, get_params
from apis.proxies import get_proxy

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

# Gate -> default proxy region. When no explicit `proxy` / `region` is given,
# apis.proxies.get_proxy(region) picks a proxy from php/proxies_<region>.txt.
_GATE_REGION = {
    'bl': 'mx', 'pd': 'mx', 'zb': 'mx', 'ps': 'mx',
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
    region = (params or {}).get('region') or _GATE_REGION.get(gate, '')
    # No explicit proxy -> pull one for the gate's region.
    if not proxy and region:
        proxy = get_proxy(region)
    cookie = (params or {}).get('cookie') or ''
    if gate == 'amz' and cookie:
        ctx['cookie'] = cookie
        if proxy:
            ctx['proxy'] = proxy
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

    if gate == 'telcel':
        return _done(gate_telcel(parsed, extra), card)
    if gate == 'netflix':
        return _done(gate_netflix(parsed), card)
    if gate == 'disney':
        return _done(gate_disney(parsed), card)
    if gate == 'amazon':
        if not cookie:
            return {'status': False, 'error': 'Amazon gate requires a cookie parameter'}
        return _done(_run_one(parsed['parts'], bin_info(parsed['parts'][0]), 'amz', extra), card)

    if gate == 'shopify':
        if not (params.get('website') or params.get('site') or params.get('url')):
            return {'status': 'error', 'code': 'NO_API_URL', 'card': card,
                    'time_taken': round(time.time() - t0, 2)}
        result = _run_one(parsed['parts'], bin_info(parsed['parts'][0]), 'shopify', params)
        return _done(result, card)

    result = _run_one(parsed['parts'], bin_info(parsed['parts'][0]), gate, extra)
    return _done(result, card)


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
# ══════════════════════════════════════════════════════════════════════════
#  Tool endpoints: /bin /fake /ip /phone /gen /sk /site /tmail
#  Each handler receives the merged params dict and returns a JSON-serializable dict.
# ══════════════════════════════════════════════════════════════════════════
import json
import random
import string
from types import SimpleNamespace

import requests

from apis.core import load_env, ns_to_dict, get_params

_TMAIL_API = 'https://api.mail.tm'

_MOCK_BOT = SimpleNamespace(raise_post=lambda *a, **k: None)


def cmd_bin(params: dict) -> dict:
    query, = get_params(params, {}, 'bin')
    from Commands.Tools.binc import lookup
    r = lookup(query)
    if not r.get('status'):
        return {'status': False, 'error': 'BIN not found (min 6 digits)'}
    return {'status': True, 'data': r['response']}


def cmd_fake(params: dict) -> dict:
    country, amount = get_params(params, {}, 'country', 'amount')
    try:
        amount = max(1, min(int(amount or 1), 10))
    except (ValueError, TypeError):
        amount = 1
    country = (country or 'US').upper()
    from Model.libs.__addr import AddrGenerator
    r = AddrGenerator.generate(country, amount)
    if not r.status:
        return {'status': False, 'error': getattr(r, 'message', 'Generation failed')}
    return {'status': True, 'country': r.country, 'flag': r.flag,
            'code': r.code, 'total': r.total,
            'data': [ns_to_dict(a) for a in r.results]}


def cmd_ip(params: dict) -> dict:
    ip, = get_params(params, {}, 'ip')
    if not ip:
        return {'status': False, 'error': 'Missing ip parameter'}
    from Model.libs.__ip import ipLookup
    r = ipLookup(ip).run()
    if not getattr(r, 'status', False):
        return {'status': False, 'error': getattr(r, 'message', 'IP lookup failed')}
    return {'status': True, 'data': ns_to_dict(r)}


def cmd_phone(params: dict) -> dict:
    number, = get_params(params, {}, 'number')
    if not number:
        return {'status': False, 'error': 'Missing number parameter'}
    from Model.libs.__phone import phoneLookup
    r = phoneLookup(number).run()
    if not getattr(r, 'status', False):
        return {'status': False, 'error': getattr(r, 'message', 'Phone lookup failed')}
    return {'status': True, 'data': ns_to_dict(r)}


def _gen_cards(gen_parts: list, amount: int) -> dict:
    """Bounded live-card generator from an extrapolate gen line CC|MM|YY|CVV."""
    import luhn as _luhn
    import random as _random

    cc_raw, mes, year_raw, cvv_raw = gen_parts[0], gen_parts[1], gen_parts[2], gen_parts[3]
    year = year_raw if year_raw.isdigit() else _random.choice(['2023', '2024', '2025', '2026', '2027', '2028', '2029'])
    mes = mes if mes.isdigit() else _random.choice(['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'])

    def _fill(raw: str) -> str:
        return ''.join(ch if ch.isdigit() else str(_random.randint(0, 9)) for ch in raw)

    found, seen, attempts = [], set(), 0
    while len(found) < amount and attempts < 5000:
        attempts += 1
        cc = _fill(cc_raw)
        if cc in seen or not _luhn.verify(cc):
            continue
        seen.add(cc)
        found.append(f'{cc}|{mes}|{year}|{_fill(cvv_raw)}')
    return {'status': True, 'total': len(found), 'data': found}


def cmd_gen(params: dict) -> dict:
    cc, amount = get_params(params, {}, 'cc', 'amount')
    try:
        amount = max(1, min(int(amount or 10), 20))
    except (ValueError, TypeError):
        amount = 10
    if not cc:
        return {'status': False, 'error': 'Missing cc parameter (extrapolate bin, e.g. 5200828282828210|12|26|xxx)'}
    from Commands.Tools.cc_gen import array
    parsed = array(text=cc, bot=_MOCK_BOT)
    if not parsed.get('status'):
        return {'status': False, 'error': parsed.get('raise', 'Invalid extrapolate card')}
    cards = _gen_cards(parsed['gen'].split('|'), amount)
    if not cards['data']:
        return {'status': False, 'error': 'Card generator failed (no luhn-valid cards found)'}
    return {'status': True, 'bin': parsed['gen'], 'total': cards['total'], 'data': cards['data']}


def cmd_sk(params: dict) -> dict:
    key, = get_params(params, {}, 'key')
    if not key:
        return {'status': False, 'error': 'Missing key parameter'}
    from Commands.Tools.sk import sk_check
    r = sk_check(key.strip(), _MOCK_BOT)
    if isinstance(r, str):
        return {'status': 'Error ❌', 'data': r}
    return {'status': r.get('status', 'Error ❌'), 'data': r.get('response', ''),
            'amount': r.get('amount', '?'), 'cards': r.get('cards', '?'),
            'currency': r.get('currency', '?')}


def cmd_site(params: dict) -> dict:
    url, = get_params(params, {}, 'url')
    if not url:
        return {'status': False, 'error': 'Missing url parameter'}
    from Commands.Tools.site import check
    r = check(url)
    if r.get('status') is False and 'processors' not in r:
        return {'status': False, 'error': r.get('raise', 'Could not analyze site')}
    return {'status': True, 'data': {
        'url': r.get('url', url),
        'ip': r.get('ip', 'N/A'),
        'server': r.get('server', 'N/A'),
        'gateways': r.get('processors', []),
        'ecommerce': r.get('ecommerce', []),
        'securities': r.get('securities', []),
    }}


def cmd_tmail(params: dict) -> dict:
    from Commands.Tools import tmail as _tmail
    load_env()
    return {'status': True, 'note': 'TempMail is session-bound to a Telegram user; read via bot /tmail.',
            'sessions': list(_tmail._loadSessions().keys())}


def cmd_amz_generator(params: dict) -> dict:
    """Amazon account/cookie generator. Requires `country` (US/MX/CA/…).
    Uses a US-region proxy by default; an explicit `proxy` overrides it."""
    country, proxy = get_params(params, {}, 'country', 'proxy')
    country = (country or '').strip().upper()
    if not country:
        return {'status': False, 'code': 'MISSING_PARAM',
                'error': 'Missing required parameter(s): country'}
    from Commands.Tools.cookiegen import _generate_cookie, COUNTRIES
    if country not in COUNTRIES:
        return {'status': False, 'error':
                f'Invalid country [{country}]. Supported: {", ".join(COUNTRIES.keys())}'}
    from apis.proxies import get_proxy
    proxy = (proxy or get_proxy(country)) or None
    result = _generate_cookie(country, proxy)
    if not result or not result.get('status'):
        return {'status': False, 'error':
                (result or {}).get('message', 'Cookie generation failed') or 'Cookie generation failed'}
    return {'status': True, 'country': COUNTRIES.get(country, country),
            'proxy': proxy,
            'cookies': result.get('cookies', ''),
            'profile': (result.get('profile') or {}),
            'billing': result.get('billingMessage', ''),
            'time_taken': result.get('time_taken', '')}


# ══════════════════════════════════════════════════════════════════════════
#  mail.tm proxy — Vercel's IPs are blocked by api.mail.tm (HTTP 500), but the
#  VPS is not. The Next.js frontend proxies mail.tm through this endpoint so the
#  request originates from the VPS datacenter instead of Vercel.
# ══════════════════════════════════════════════════════════════════════════
def _tmail_random(n: int = 10) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _tmail_headers(auth: str = '') -> dict:
    h = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }
    if auth:
        h['Authorization'] = f'Bearer {auth}'
    return h


def cmd_tmail_proxy(params: dict) -> dict:
    """Proxy mail.tm so the request comes from the VPS (not blocked by Cloudflare).

    Body: { action: 'domains'|'generate'|'inbox'|'read', params: {...} }
    """
    action = (params.get('action') or '').strip().lower()
    p = params.get('params') or {}
    if not isinstance(p, dict):
        p = {}
    p = dict(p)
    p['action'] = action

    try:
        if action == 'domains':
            r = requests.get(f'{_TMAIL_API}/domains', headers=_tmail_headers(), timeout=15)
            if r.status_code != 200:
                return {'status': False, 'error': f'HTTP {r.status_code}'}
            data = r.json()
            members = data.get('hydra:member', []) if isinstance(data, dict) else []
            return {'status': True, 'domains': [
                {'domain': d.get('domain', ''), 'isActive': bool(d.get('isActive'))}
                for d in members if isinstance(d, dict)
            ]}

        if action == 'generate':
            domain = (p.get('domain') or '').strip()
            members = []
            r = requests.get(f'{_TMAIL_API}/domains', headers=_tmail_headers(), timeout=15)
            if r.status_code == 200:
                data = r.json()
                members = data.get('hydra:member', []) if isinstance(data, dict) else []
            active = [d for d in members if isinstance(d, dict) and d.get('isActive')]
            if domain and not any(d.get('domain') == domain for d in members):
                domain = ''
            if not domain:
                domain = active[0].get('domain') if active else (members[0].get('domain') if members else '')
            if not domain:
                return {'status': False, 'error': 'No hay dominios disponibles'}

            login = _tmail_random(10)
            password = _tmail_random(16)
            email = f'{login}@{domain}'

            rc = requests.post(f'{_TMAIL_API}/accounts',
                               headers={**_tmail_headers(), 'Content-Type': 'application/json'},
                               json={'address': email, 'password': password}, timeout=15)
            if rc.status_code not in (200, 201):
                return {'status': False, 'error': f'Create failed: {rc.text[:120]}'}

            rt = requests.post(f'{_TMAIL_API}/token',
                               headers={**_tmail_headers(), 'Content-Type': 'application/json'},
                               json={'address': email, 'password': password}, timeout=15)
            token = rt.json().get('token') if rt.status_code == 200 else ''
            if not token:
                return {'status': False, 'error': 'Token failed'}

            return {'status': True, 'email': email, 'token': token,
                    'password': password, 'domain': domain, 'type': 'jwt'}

        if action == 'inbox':
            token = (p.get('token') or '').strip()
            r = requests.get(f'{_TMAIL_API}/messages', headers=_tmail_headers(token), timeout=15)
            if r.status_code != 200:
                return {'status': False, 'error': f'HTTP {r.status_code}'}
            data = r.json()
            members = data.get('hydra:member', []) if isinstance(data, dict) else []
            messages = []
            for m in members:
                if not isinstance(m, dict):
                    continue
                fr = m.get('from') or {}
                messages.append({
                    'id': m.get('id', ''),
                    'from': fr.get('address', 'Unknown') if isinstance(fr, dict) else str(fr),
                    'subject': m.get('subject', 'No Subject'),
                    'intro': (m.get('intro') or '')[:100],
                    'date': m.get('createdAt', ''),
                    'seen': bool(m.get('seen')),
                })
            return {'status': True, 'messages': messages, 'type': 'jwt'}

        if action == 'read':
            token = (p.get('token') or '').strip()
            mid = (p.get('id') or '').strip()
            r = requests.get(f'{_TMAIL_API}/messages/{mid}', headers=_tmail_headers(token), timeout=15)
            if r.status_code != 200:
                return {'status': False, 'error': f'HTTP {r.status_code}'}
            m = r.json()
            fr = m.get('from') or {}
            return {'status': True, 'type': 'jwt', 'message': {
                'id': m.get('id', ''),
                'from': fr.get('address', 'Unknown') if isinstance(fr, dict) else str(fr),
                'subject': m.get('subject', 'No Subject'),
                'textBody': (m.get('text') or m.get('intro') or 'No content')[:3500],
            }}

        return {'status': False, 'error': f'Acción mail.tm no soportada: {action}'}
    except Exception as e:
        return {'status': False, 'error': str(e)[:200]}

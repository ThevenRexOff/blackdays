# ══════════════════════════════════════════════════════════════════════════
#  Shared helpers for the JILL_BOT HTTP API.
# ══════════════════════════════════════════════════════════════════════════
import json
import os
import pathlib
import re
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_env() -> None:
    """Load Model/config.env + .env into os.environ (never overrides set vars)."""
    for env_path in [ROOT / 'Model' / 'config.env', ROOT / '.env']:
        try:
            if not env_path.exists():
                continue
            for line in env_path.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and os.getenv(key) is None:
                    os.environ[key] = value
        except Exception:
            pass


def api_key() -> str:
    """Optional shared secret. When set, every request must send X-API-Key (or ?key=)."""
    load_env()
    return os.getenv('JILLBOT_API_KEY', '').strip()


def ns_to_dict(obj) -> dict:
    """Convert a SimpleNamespace / object with attributes into a plain dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if isinstance(obj, (str, int, float, bool)):
        return {'value': obj}
    data = {}
    for key in dir(obj):
        if key.startswith('_'):
            continue
        try:
            value = getattr(obj, key)
        except Exception:
            continue
        if callable(value):
            continue
        data[key] = value
    return data


def parse_card(text: str) -> dict:
    """Parse 'CC|MM|YY|CVV' (also accepts / or spaces) into parts."""
    raw = str(text or '').strip()
    parts = [p for p in re.split(r'\s*[|/]\s*|\s+', raw) if p]
    if len(parts) < 4:
        return {'status': False, 'raise': 'Expected format: CC|MM|YY|CVV'}
    number, month, year, cvv = parts[0], parts[1], parts[2], parts[3]
    if not number.isdigit() or len(number) < 15:
        return {'status': False, 'raise': 'Invalid card number'}
    month = month.zfill(2)
    if len(year) == 4:
        year = year[-2:]
    return {'status': True, 'parts': [number, month, year, cvv],
            'card': f'{number}|{month}|{year}|{cvv}'}


def bin_info(card_number: str) -> dict:
    """Best-effort BIN data (same shape _template/checkers expect), or {} on failure."""
    try:
        from Commands.Tools.binc import lookup
        r = lookup(card_number[:6])
        if r.get('status'):
            resp = r['response']
            return {
                'brand':   str(resp.get('brand', 'N/A')),
                'type':    str(resp.get('type', 'N/A')),
                'level':   str(resp.get('level', 'N/A')),
                'bank':    str(resp.get('bank', 'N/A')),
                'country': str(resp.get('country', 'N/A')),
                'flag':    str(resp.get('flag', 'N/A')),
            }
    except Exception:
        pass
    return {}


def get_params(query: dict, body: dict = None, *names):
    """Resolve a parameter from query string or JSON body (body wins)."""
    merged = dict(query)
    if body:
        merged.update(body)
    out = []
    for name in names:
        value = merged.get(name)
        if value is None and name == 'card':
            value = merged.get('cc')
        out.append(str(value) if value is not None else '')
    return out
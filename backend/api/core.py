# ══════════════════════════════════════════════════════════════════════════
#  JILL_BOT API — shared request helpers.
#  Pure functions, no Flask dependency, so gate/tool handlers stay testable.
# ══════════════════════════════════════════════════════════════════════════
import re


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
    """Resolve a parameter from a params dict / body (body wins)."""
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
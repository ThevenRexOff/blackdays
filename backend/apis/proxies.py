# ══════════════════════════════════════════════════════════════════════════
#  Proxy source by region. Each region reads from php/proxies_<region>.txt
#  (fallback to php/proxies.txt when the region file is missing).
#  get_proxy(region) returns a single usable proxy URL, rotating per call
#  so concurrent checks spread across the pool.
# ══════════════════════════════════════════════════════════════════════════
import itertools
import pathlib
import threading

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_PHP_DIR = _ROOT / 'php'
_LOCK = threading.Lock()
_ROTATORS: dict = {}

# region name -> default file (used when an unknown region is requested)
_DEFAULT_REGION = 'us'


def _load_list(region: str) -> list:
    region = (region or '').strip().lower() or _DEFAULT_REGION
    if region.startswith('us'):
        region = 'us'
    elif region.startswith('mx') or region.startswith('me'):
        region = 'mx'
    candidates = [
        _PHP_DIR / f'proxies_{region}.txt',
        _PHP_DIR / f'proxies_{region[:2]}.txt',
        _PHP_DIR / 'proxies.txt',
    ]
    for path in candidates:
        try:
            if not path.exists():
                continue
            lines = [ln.strip() for ln in path.read_text(encoding='utf-8').splitlines() if ln.strip()]
            if lines:
                return lines
        except Exception:
            continue
    return []


def get_proxy(region: str = '') -> str:
    """Return the next proxy URL for the given region ('' -> default)."""
    with _LOCK:
        proxies = _load_list(region)
        if not proxies:
            return ''
        pool_key = region.strip().lower() or _DEFAULT_REGION
        it = _ROTATORS.setdefault(pool_key, itertools.cycle(proxies))
        return next(it)


def get_proxy_with_scheme(region: str = '') -> str:
    """Return a proxy formatted for curl/requests, adding http:// scheme."""
    p = get_proxy(region)
    if not p:
        return ''
    return p if p.startswith(('http://', 'https://', 'socks')) else f'http://{p}'


def pool_size(region: str = '') -> int:
    return len(_load_list(region))
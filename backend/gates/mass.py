# Pure gate motor for 'mass' — no Telegram-bot dependency.

import time, threading, datetime, importlib, inspect, html as _html_mod

from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_CARDS = 10

_GATE_COST = {'auths': 1, 'charged': 1, 'ccn': 2, 'avs': 2, 'specials': 3}

_ALIAS = {'amz': 'amazon', 'amzg': 'amazon'}

def _load_checker(cmd: str):
    """Import Commands.Gates.{cmd}, normalize its signature to (cc, bin_d, ctx),
    and return the wrapper — or None if the module/function doesn't exist."""
    try:
        mod = importlib.import_module(f'Commands.Gates.{_ALIAS.get(cmd, cmd)}')
        fn = getattr(mod, 'run_check', None)
        if not callable(fn):
            return None
        try:
            n = len(inspect.signature(fn).parameters)
        except (ValueError, TypeError):
            n = 3
        if n < 3:
            return lambda cc, bin_d, ctx=None: fn(cc, bin_d)
        return fn
    except (ImportError, Exception):
        pass
    return None
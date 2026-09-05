# ══════════════════════════════════════════════════════════════════════════
#  JILL_BOT API — configuration & environment helpers.
#
#  Loads Model/config.env + .env into os.environ (never overriding variables
#  already set), and exposes the settings the Flask app needs: the optional
#  shared API key and the CORS origin allowlist.
# ══════════════════════════════════════════════════════════════════════════
import os
import pathlib

# Absolute path of the backend root (the directory that contains this file).
# Everything under it — gates/, Commands/, Model/, php/ — is importable as a
# top-level package once this path is on sys.path.
ROOT = pathlib.Path(__file__).resolve().parent


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


def allowed_origins(override: str = '') -> list:
    """Comma-separated CORS origin allowlist. Empty -> localhost dev defaults."""
    raw = (override or os.getenv('JILLBOT_ALLOWED_ORIGIN', '')).strip()
    if not raw:
        return ['http://localhost', 'http://127.0.0.1']
    return [o.strip() for o in raw.split(',') if o.strip()]
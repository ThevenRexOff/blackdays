# ══════════════════════════════════════════════════════════════════════════
#  JILL_BOT HTTP API server — zero-dependency (standard library only).
#
#  Run:
#      python3 apis/server.py --host 0.0.0.0 --port 8080
#      python3 apis/server.py --port 8080 --key Sk-xXx   (require ?key= or X-API-Key)
#
#  Optional auth via env JILLBOT_API_KEY or --key.
# ══════════════════════════════════════════════════════════════════════════
import argparse
import json
import os
import pathlib
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apis.core import api_key
from apis.routes import match, public_routes

_START = time.time()
_REQUIRED_KEY = ''

# Frontend origin allowlist for CORS. Values may be comma-separated.
def _allowed_origins() -> list:
    raw = os.getenv('JILLBOT_ALLOWED_ORIGIN', '').strip()
    if not raw:
        # Default: full wildcard fallback stays disabled; allow localhost dev only.
        return ['http://localhost', 'http://127.0.0.1']
    return [o.strip() for o in raw.split(',') if o.strip()]

_ALLOWED_ORIGINS = _allowed_origins()


class ApiHandler(BaseHTTPRequestHandler):
    server_version = 'JillBotAPI/1.0'

    # ── helpers ──────────────────────────────────────────────────────────────
    def _origin_allowed(self) -> str:
        """Return the Origin header value if it's in the allowlist, else ''."""
        req_origin = self.headers.get('Origin') or ''
        if not req_origin:
            return ''
        for allowed in _ALLOWED_ORIGINS:
            if req_origin == allowed or req_origin.rstrip('/') == allowed.rstrip('/'):
                return req_origin
        return ''

    def _cors_headers(self) -> dict:
        origin = self._origin_allowed()
        if not origin:
            return {}
        return {
            'Access-Control-Allow-Origin': origin,
            'Vary': 'Origin',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Expose-Headers': 'X-Request-Id',
        }

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        for k, v in self._cors_headers().items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # Preflight: only answer if the request Origin is allowlisted.
        if not self._origin_allowed():
            return self._send(403, {'status': False, 'error': 'Origin not allowed'})
        self.send_response(204)
        for k, v in self._cors_headers().items():
            self.send_header(k, v)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _authorized(self, query: dict) -> bool:
        if not _REQUIRED_KEY:
            return True
        header = self.headers.get('X-API-Key') or ''
        qkey = query.get('key') or ''
        if isinstance(qkey, (list, tuple)):
            qkey = qkey[-1] if qkey else ''
        return header == _REQUIRED_KEY or qkey == _REQUIRED_KEY

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get('Content-Length') or 0)
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            data = json.loads(raw.decode('utf-8'))
            return data if isinstance(data, dict) else {'__values': data}
        except Exception:
            return {}

    def log_message(self, fmt, *args):
        sys.stderr.write('[%s] %s\n' % (self.log_date_time_string(), fmt % args))

    # ── dispatch ─────────────────────────────────────────────────────────────
    def _handle(self) -> None:
        parsed = urlparse(self.path)
        query = {k: v[-1] for k, v in parse_qs(parsed.query).items()}

        if not self._authorized(query):
            return self._send(401, {'status': False, 'error': 'Unauthorized — missing/invalid key'})

        handler, gate_name = match(parsed.path)
        params = dict(query)
        if self.command == 'POST' or self.command == 'PUT':
            params.update(self._read_body())

        if gate_name:
            params.setdefault('gate', gate_name)
            if 'card' not in params and 'cc' not in params:
                return self._send(400, {'status': False, 'error': 'Missing card (cc|mm|yy|cvv) parameter'})

        if handler is None:
            return self._send(404, {'status': False, 'error': f'No route for {self.command} {parsed.path}'})

        try:
            result = handler(params)
            if result is None:
                result = {'status': False, 'error': 'Handler returned nothing'}
            self._send(200, result)
        except Exception as exc:
            trace = traceback.format_exc()
            try:
                from apis.telegram_alert import send_alert
                send_alert(f"API {self.command} {parsed.path} → 500",
                           str(exc)[:1500], level='ERROR', trace=trace[-3000:])
            except Exception:
                pass
            self._send(500, {'status': False, 'error': str(exc)[:500], 'trace': trace.splitlines()[-3:]})

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()


def main() -> None:
    global _REQUIRED_KEY
    parser = argparse.ArgumentParser(description='JILL_BOT HTTP API')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--key', default='', help='Require this key via ?key= or X-API-Key header')
    parser.add_argument('--origin', default='', help='Comma-separated allowed CORS origins (overrides JILLBOT_ALLOWED_ORIGIN)')
    args = parser.parse_args()

    _REQUIRED_KEY = args.key or api_key()
    if args.origin:
        _ALLOWED_ORIGINS[:] = [o.strip() for o in args.origin.split(',') if o.strip()]

    httpd = ThreadingHTTPServer((args.host, args.port), ApiHandler)
    httpd.daemon_threads = True

    print('═' * 60)
    print('  JILL_BOT HTTP API  (apis/)')
    print('═' * 60)
    print(f'  Serving on      : http://{args.host}:{args.port}/apis')
    print(f'  Auth            : {"required (key set)" if _REQUIRED_KEY else "disabled"}')
    print(f'  CORS origins    : {", ".join(_ALLOWED_ORIGINS) or "none (blocked)"}')
    print(f'  Endpoints       : {sum(1 for r in public_routes())}')
    print('─' * 60)
    for r in public_routes():
        print(f"  {r['method']:<5} {r['path']:<28} {r['description']}")
    print('═' * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        httpd.shutdown()


if __name__ == '__main__':
    main()
# ══════════════════════════════════════════════════════════════════════════
#  JILL_BOT HTTP API — Flask application factory.
#
#  Behavior mirrors the legacy stdlib server 1:1:
#    • Path-based dispatch (method only decides if the JSON body is merged in)
#    • OPTIONS preflight gated by the CORS origin allowlist
#    • Optional shared key via X-API-Key header or ?key= query param
#    • JSON responses with ensure_ascii=False and default=str (non-ASCII safe)
# ══════════════════════════════════════════════════════════════════════════
import sys
import time
import traceback
from urllib.parse import parse_qs

from flask import Flask, Response, request

from config import ROOT, api_key, allowed_origins, load_env
from api.routes import ROUTES, handlers, public_routes
from api.gates import gate_run

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_START = time.time()


def create_app(require_key: str = '', origin_override: str = '') -> Flask:
    """Build and configure the JILL_BOT Flask application.

    require_key     : if set, every /apis request must send X-API-Key or ?key=.
    origin_override : comma-separated CORS allowlist (overrides env var).
    """
    load_env()
    key = (require_key or api_key()).strip()

    app = Flask(__name__)
    app.config['JILLBOT_API_KEY'] = key
    # Match the legacy encoder: no ASCII escaping, no key sorting, str fallback.
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    origins = allowed_origins(origin_override)

    # ── helpers ────────────────────────────────────────────────────────────
    def _origin_allowed() -> str:
        req_origin = request.headers.get('Origin') or ''
        if not req_origin:
            return ''
        for allowed in origins:
            if req_origin == allowed or req_origin.rstrip('/') == allowed.rstrip('/'):
                return req_origin
        return ''

    def _cors_headers() -> dict:
        origin = _origin_allowed()
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

    def _json(status, payload) -> Response:
        body = app.json.dumps(payload, default=str)
        resp = Response(body, status=status, mimetype='application/json; charset=utf-8')
        for k, v in _cors_headers().items():
            resp.headers[k] = v
        return resp

    def _merged_params() -> dict:
        """Query string (last value wins) merged with the JSON body (body wins)."""
        query = {k: v[-1] for k, v in parse_qs(request.query_string.decode('utf-8', 'replace')).items()}
        params = dict(query)
        if request.method in ('POST', 'PUT'):
            body = request.get_json(silent=True)
            if isinstance(body, dict):
                params.update(body)
            elif body is not None:
                params['__values'] = body
        return params

    def _handle_error(req, exc) -> Response:
        trace = traceback.format_exc()
        try:
            from api.telegram_alert import send_alert
            send_alert(f"API {req.method} {req.path} → 500",
                       str(exc)[:1500], level='ERROR', trace=trace[-3000:])
        except Exception:
            pass
        return _json(500, {'status': False, 'error': str(exc)[:500],
                           'trace': trace.splitlines()[-3:]})

    def _view(handler) -> Response:
        def wrapped():
            try:
                result = handler(_merged_params())
                if result is None:
                    result = {'status': False, 'error': 'Handler returned nothing'}
                return _json(200, result)
            except Exception as exc:
                return _handle_error(request, exc)
        return wrapped

    # ── preflight (OPTIONS) ────────────────────────────────────────────────
    @app.before_request
    def _preflight():
        if request.method == 'OPTIONS':
            origin = _origin_allowed()
            if not origin:
                return _json(403, {'status': False, 'error': 'Origin not allowed'})
            resp = Response(status=204)
            for k, v in _cors_headers().items():
                resp.headers[k] = v
            resp.headers['Content-Length'] = '0'
            return resp
        return None

    # ── shared-key auth ────────────────────────────────────────────────────
    @app.before_request
    def _authorize():
        if not key:
            return None
        if not request.path.startswith('/apis'):
            return None
        header = request.headers.get('X-API-Key') or ''
        qkey = request.args.get('key') or ''
        if header == key or qkey == key:
            return None
        return _json(401, {'status': False, 'error': 'Unauthorized — missing/invalid key'})

    # ── URL rules (path-based dispatch, GET/POST/PUT all accepted) ─────────
    # Gate paths (/apis/gate/*) are handled by the single dynamic rule below so
    # that the gate name survives any HTTP method (the frontend POSTs to them).
    for method, path_map in handlers().items():
        for path, handler in path_map.items():
            if path.startswith('/apis/gate/'):
                continue
            app.add_url_rule(path, view_func=_view(handler),
                             methods=['GET', 'POST', 'PUT'], strict_slashes=False,
                             endpoint=f'{method}:{path}')

    # Dynamic gate route: /apis/gate/<gate> (any name, incl. aliases)
    def _gate_view(gate_name: str) -> Response:
        params = _merged_params()
        params.setdefault('gate', gate_name)
        if 'card' not in params and 'cc' not in params:
            return _json(400, {'status': False, 'error': 'Missing card (cc|mm|yy|cvv) parameter'})
        try:
            return _json(200, gate_run(params))
        except Exception as exc:
            return _handle_error(request, exc)

    app.add_url_rule('/apis/gate/<gate_name>', view_func=_gate_view,
                     methods=['GET', 'POST', 'PUT'], strict_slashes=False,
                     endpoint='gate_dynamic')

    # ── error handling ─────────────────────────────────────────────────────
    @app.errorhandler(404)
    def _not_found(e):
        return _json(404, {'status': False,
                           'error': f'No route for {request.method} {request.path}'})

    @app.errorhandler(405)
    def _method_not_allowed(e):
        return _json(405, {'status': False,
                           'error': f'No route for {request.method} {request.path}'})

    @app.errorhandler(Exception)
    def _uncaught(e):
        return _handle_error(request, e)

    return app


def banner(app: Flask, host: str, port: int) -> None:
    """Print the familiar startup banner with the endpoint list."""
    print('═' * 60)
    print('  JILL_BOT HTTP API  (Flask)')
    print('═' * 60)
    print(f'  Serving on      : http://{host}:{port}/apis')
    print(f'  Auth            : {"required (key set)" if app.config.get("JILLBOT_API_KEY") else "disabled"}')
    print(f'  CORS origins    : {", ".join(allowed_origins()) or "none (blocked)"}')
    print(f'  Endpoints       : {sum(1 for r in public_routes())} + /apis/gate/<gate>')
    print('─' * 60)
    for r in public_routes():
        print(f"  {r['method']:<5} {r['path']:<28} {r['description']}")
    print('═' * 60)
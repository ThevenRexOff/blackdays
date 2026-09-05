# ══════════════════════════════════════════════════════════════════════════
#  JILL_BOT HTTP API — entry point.
#
#  Run:
#      python app.py --host 0.0.0.0 --port 8080
#      python app.py --port 8080 --key Sk-xXx      (require ?key= or X-API-Key)
#
#  Uses Waitress (production WSGI server) when available; otherwise falls back
#  to Flask's built-in threaded development server.
# ══════════════════════════════════════════════════════════════════════════
import argparse

# Load .env / Model/config.env FIRST — before any other import — so that
# CAPSOLVER_KEY / AMZN_PROXY / etc. are visible when gate modules read
# them at import time (e.g. gates/bl.py:17 caches _CAPSOLVER_KEY).
import config
config.load_env()

from api import create_app, banner


def main() -> None:
    parser = argparse.ArgumentParser(description='JILL_BOT HTTP API (Flask)')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--key', default='', help='Require this key via ?key= or X-API-Key header')
    parser.add_argument('--origin', default='', help='Comma-separated allowed CORS origins (overrides JILLBOT_ALLOWED_ORIGIN)')
    args = parser.parse_args()

    app = create_app(require_key=args.key, origin_override=args.origin)
    banner(app, args.host, args.port)

    try:
        from waitress import serve
        serve(app, host=args.host, port=args.port, threads=8, channel_timeout=600,
              ident='JillBotAPI-Flask')
    except ImportError:
        app.run(host=args.host, port=args.port, threaded=True, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
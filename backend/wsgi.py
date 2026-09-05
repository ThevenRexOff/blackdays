# ══════════════════════════════════════════════════════════════════════════
#  WSGI entry point — for gunicorn / waitress / mod_wsgi:
#      gunicorn 'wsgi:app' --bind 0.0.0.0:8080 --workers 2 --threads 8
# ══════════════════════════════════════════════════════════════════════════
# Load .env first — see app.py for the rationale (CAPSOLVER_KEY needs to be
# available when gate modules are imported).
import config
config.load_env()

from api import create_app

app = create_app()

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080, threads=8, channel_timeout=600)
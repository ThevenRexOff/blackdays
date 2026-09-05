# ══════════════════════════════════════════════════════════════════════════
#  WSGI entry point — for gunicorn / waitress / mod_wsgi:
#      gunicorn 'wsgi:app' --bind 0.0.0.0:8080 --workers 2 --threads 8
# ══════════════════════════════════════════════════════════════════════════
from api import create_app

app = create_app()

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080, threads=8, channel_timeout=600)
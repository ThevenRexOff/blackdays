# ══════════════════════════════════════════════════════════════════════════
#  Telegram alert notifier — envía errores del sistema/gates a los admins.
#  Usa un bot dedicado (ALERT_BOT_TOKEN) y un chat/grupo de administradores
#  (ALERT_CHAT_ID). Si el mensaje es grande (>4000 chars) lo manda como archivo.
# ══════════════════════════════════════════════════════════════════════════
import io
import json
import os
import time
import traceback

import requests

ALERT_TOKEN = os.getenv('ALERT_BOT_TOKEN', '8965203280:AAGgExEMPc7BkgZpNePiuOt5Agcr1eSgs84')
ALERT_CHAT = os.getenv('ALERT_CHAT_ID', '-5252581179')
MAX_INLINE = 3900  # Telegram sendMessage soft limit (~4096); keep margin for HTML tags.


def _api(method: str, **data) -> dict:
    """POST to the Telegram Bot API; returns parsed JSON or {} on failure."""
    url = f"https://api.telegram.org/bot{ALERT_TOKEN}/{method}"
    try:
        r = requests.post(url, data=data, timeout=15)
        return r.json() if r.ok else {}
    except Exception:
        return {}


def _safe(text: str) -> str:
    """Mask obvious secrets and cap length."""
    if not isinstance(text, str):
        text = str(text)
    text = text[:20000]
    return text


def send_alert(title: str, detail: str, *, level: str = 'ERROR', gate: str = '', trace: str = '') -> bool:
    """Send a formatted error alert to the admin group.

    title  — short summary, e.g. 'Gate BL: upstream error'
    detail — the error body / message
    level  — 'ERROR' | 'WARN' | 'INFO'
    gate   — gate name (optional)
    trace  — full traceback/extra (optional; sent as file if big)
    """
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    icon = {'ERROR': '🚨', 'WARN': '⚠️', 'INFO': 'ℹ️'}.get(level.upper(), '🔔')
    header = f"{icon} <b>[{level.upper()}]</b> JILL GATE ALERT\n📅 <code>{ts}</code>"
    if gate:
        header += f"\n🎯 Gate: <code>{gate}</code>"

    body = f"\n\n<b>Detalle:</b>\n<pre>{_safe(detail)[:1800]}</pre>"
    if trace:
        body += f"\n\n<b>Traza:</b>\n<pre>{_safe(trace)[:1800]}</pre>"

    text = header + body

    # Si el contenido total cabe, mandarlo como mensaje.
    if len(text) <= MAX_INLINE and not trace:
        return bool(_api('sendMessage', chat_id=ALERT_CHAT, text=text, parse_mode='HTML'))
    if len(text) <= MAX_INLINE:
        _api('sendMessage', chat_id=ALERT_CHAT, text=text, parse_mode='HTML')

    # Contenido grande: enviar un mensaje corto + el detalle en un archivo .txt
    _api('sendMessage', chat_id=ALERT_CHAT, text=header, parse_mode='HTML')
    return _send_file(f"JILL ALERT - {ts} - {level}.txt",
                      f"{title}\n{'=' * 40}\nTS: {ts}\nGate: {gate or '-'}\n\nDETALLE:\n{detail}\n\nTRAZA:\n{trace}\n")


def _send_file(filename: str, content: str) -> bool:
    """Upload `content` as a text file to the chat (via multipart)."""
    url = f"https://api.telegram.org/bot{ALERT_TOKEN}/sendDocument"
    try:
        r = requests.post(
            url,
            data={'chat_id': ALERT_CHAT},
            files={'document': (filename, io.BytesIO(content.encode('utf-8')), 'text/plain')},
            timeout=20,
        )
        return r.ok
    except Exception:
        return False


def notify_gate_error(gate: str, result: dict, *, user: str = '', card_mask: str = '', trace: str = '') -> bool:
    """High-level helper: notify admins when a gate returns an infrastructure error.

    Ignores normal outcomes (Declined/Approved); only notifies on "Error ⚠️" statuses.
    """
    detail = json.dumps(result, ensure_ascii=False, default=str)
    meta = []
    if user:
        meta.append(f"user: {user}")
    if card_mask:
        meta.append(f"card: {card_mask}")
    if meta:
        detail = f"({' | '.join(meta)})\n{detail}"
    trace = trace or ''.join(traceback.format_stack())[-3000:]
    return send_alert(f"Gate {gate} devolvió error", detail, level='ERROR', gate=gate, trace=trace)
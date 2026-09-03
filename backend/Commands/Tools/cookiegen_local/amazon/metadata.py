import random
from typing import Optional
from . import core
from curl_cffi import requests as curl


class AccountBuilder:

    def __init__(self, cookie: str, country: str) -> None:
        country = country.upper()
        if country not in core.DOMAIN_MAP:
            raise ValueError(f"Country '{country}' is not supported. Use: {', '.join(core.DOMAIN_MAP)}")
        self.countryCode = country
        self.domain      = core.DOMAIN_MAP[country]
        self.cookie      = cookie
        self.session     = self.__buildSessionForCountry(cookie, self.domain)

    def __buildSessionForCountry(self, cookie: str, target_domain: str) -> curl.Session:
        """Build a session that lives on the target marketplace domain.

        The previous version duplicated every cookie onto .amazon.com as well,
        which polluted auth state (e.g. sess-at-acbde on amazon.com confuses
        the US endpoint). Fresh cookies coming from registration already carry
        the right region suffix, so we only need to warm up the target domain.
        """
        session = curl.Session(impersonate=random.choice(core.IMPERSONATE_BROWSERS))
        for pair in cookie.split(";"):
            if "=" not in pair: continue
            name, value = map(str.strip, pair.split("=", 1))
            session.cookies.set(name, value, domain=target_domain, path="/")
        session.allow_redirects = True
        session.headers.update({"Connection": "keep-alive"})
        # Warm up the target domain so Amazon binds the session server-side.
        try:
            session.get(f"https://www.{target_domain}/?ref_=nav_ya_signin", timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            })
        except Exception:
            pass
        return session

    def extractBetween(self, haystack: Optional[str], start: str, end: str, index: int = 1) -> Optional[str]:
        if haystack is None: return None
        try: return haystack.split(start)[index].split(end)[0]
        except (IndexError, ValueError): return None

    # Plausible billing profiles for every supported marketplace. The
    # countryCode must match the account's registration country or Amazon
    # rejects the address. Phone numbers are randomised to avoid collisions.
    _BILLING_PROFILES = {
        'US': {'countryCode': 'US', 'fullName': 'Mark O. Montanez',    'phone': '6065406572',                                                   'line1': '8326 NW 68th St',          'city': 'Miami',     'state': 'Florida',            'postalCode': '33166'},
        'CA': {'countryCode': 'CA', 'fullName': 'James Smith',         'phone': lambda: '1' + str(random.randint(1000000000, 9999999999)),     'line1': '123 Yonge Street',         'city': 'Toronto',   'state': 'Ontario',            'postalCode': 'M5V 2Z2'},
        'MX': {'countryCode': 'MX', 'fullName': 'Julian Talaveras',    'phone': lambda: '55' + str(random.randint(10000000, 99999999)),         'line1': 'Andador Tulipanes 991',    'city': 'Tarimbaro', 'state': 'Michoacan de Ocampo','postalCode': '58893'},
        'BR': {'countryCode': 'BR', 'fullName': 'Lucas Oliveira',      'phone': lambda: '11' + str(random.randint(900000000, 999999999)),       'line1': 'Rua Augusta 1500',         'city': 'Sao Paulo', 'state': 'SP',                  'postalCode': '01310-100'},
        'UK': {'countryCode': 'GB', 'fullName': 'Oliver Harris',       'phone': lambda: '7' + str(random.randint(100000000, 999999999)),        'line1': '221B Baker Street',        'city': 'London',    'state': 'London',              'postalCode': 'NW1 6XE'},
        'DE': {'countryCode': 'DE', 'fullName': 'Max Müller',          'phone': lambda: '15' + str(random.randint(100000000, 999999999)),       'line1': 'Friedrichstraße 123',      'city': 'Berlin',    'state': 'Berlin',              'postalCode': '10117'},
        'FR': {'countryCode': 'FR', 'fullName': 'Jean Dupont',         'phone': lambda: '6' + str(random.randint(10000000, 99999999)),          'line1': '25 Rue de Rivoli',         'city': 'Paris',     'state': 'Île-de-France',       'postalCode': '75001'},
        'IT': {'countryCode': 'IT', 'fullName': 'Marco Rossi',         'phone': lambda: '3' + str(random.randint(100000000, 999999999)),        'line1': 'Via del Corso 100',        'city': 'Roma',      'state': 'RM',                  'postalCode': '00186'},
        'ES': {'countryCode': 'ES', 'fullName': 'Carlos García',       'phone': lambda: '6' + str(random.randint(10000000, 99999999)),          'line1': 'Calle Mayor 25',           'city': 'Madrid',    'state': 'Madrid',              'postalCode': '28013'},
        'NL': {'countryCode': 'NL', 'fullName': 'Jan de Vries',        'phone': lambda: '6' + str(random.randint(10000000, 99999999)),          'line1': 'Damrak 70',                'city': 'Amsterdam', 'state': 'Noord-Holland',       'postalCode': '1012 LM'},
        'SG': {'countryCode': 'SG', 'fullName': 'Wei Tan',             'phone': lambda: '8' + str(random.randint(1000000, 9999999)),            'line1': '1 Raffles Place',          'city': 'Singapore', 'state': 'Singapore',           'postalCode': '048616'},
        'AU': {'countryCode': 'AU', 'fullName': 'James Wilson',        'phone': lambda: '4' + str(random.randint(10000000, 99999999)),          'line1': '123 George Street',        'city': 'Sydney',    'state': 'NSW',                 'postalCode': '2000'},
        'JP': {'countryCode': 'JP', 'fullName': '田中 太郎',            'phone': lambda: '90' + str(random.randint(10000000, 99999999)),          'line1': '1-1-1 Marunouchi',          'city': 'Chiyoda-ku','state': 'Tokyo',              'postalCode': '100-0005'},
    }

    @classmethod
    def _resolveBilling(cls, country: str) -> dict:
        profile = dict(cls._BILLING_PROFILES.get(country.upper(), cls._BILLING_PROFILES['US']))
        phone = profile.get('phone')
        if callable(phone):
            profile['phone'] = phone()
        return profile

    def addBillingAddress(self) -> bool:
        data = self._resolveBilling(self.countryCode)
        headers1 = {"host": f"www.{self.domain}", "referer": f"https://www.{self.domain}/a/addresses?ref_=ya_d_c_addr", "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36", "viewport-width": "1536"}

        try:
            request1 = self.session.get(url=f"https://www.{self.domain}/a/addresses/add?ref=ya_address_book_add_button", headers=headers1).text
        except Exception:
            return False

        start_time = self.extractBetween(request1, 'name="address-ui-widgets-form-load-start-time" value="', '"')
        request_id = self.extractBetween(request1, '=AddView&hostPageRID=', '&', 1)
        csrf_token = self.extractBetween(request1, 'type="hidden" name="address-ui-widgets-csrfToken" value="', '"')
        address_jwt = self.extractBetween(request1, 'type="hidden" name="address-ui-widgets-previous-address-form-state-token" value="', '"')
        customer_id = self.extractBetween(request1, '"customerID":"', '"')
        interaction_id = self.extractBetween(request1, 'name="address-ui-widgets-address-wizard-interaction-id" value="', '"')
        csrf_token_address = self.extractBetween(request1, "type='hidden' name='csrfToken' value='", "'")

        if not csrf_token and not csrf_token_address:
            return False

        headers3 = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Origin": f"https://www.{self.domain}", "Referer": f"https://www.{self.domain}/a/addresses/add?ref=ya_address_book_add_button", "Upgrade-Insecure-Requests": "1", "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "same-origin"}
        payload3 = {"csrfToken": csrf_token_address or "", "addressID": "", "address-ui-widgets-countryCode": data["countryCode"], "address-ui-widgets-enterAddressFullName": data["fullName"], "address-ui-widgets-enterAddressLine1": data["line1"], "address-ui-widgets-enterAddressPostalCode": data["postalCode"], "address-ui-widgets-enterAddressStateOrRegion": data["state"], "address-ui-widgets-enterAddressCity": data["city"], "address-ui-widgets-enterAddressPhoneNumber": data["phone"], "address-ui-widgets-previous-address-form-state-token": address_jwt or "", "address-ui-widgets-addressFormButtonText": "save", "address-ui-widgets-addressFormHideHeading": "true", "address-ui-widgets-enableAddressDetails": "true", "address-ui-widgets-returnLegacyAddressID": "false", "address-ui-widgets-enableDeliveryInstructions": "true", "address-ui-widgets-clientName": "YourAccountAddressBook", "address-ui-widgets-obfuscated-customerId": customer_id or "", "address-ui-widgets-csrfToken": csrf_token or "", "address-ui-widgets-form-load-start-time": start_time or "", "address-ui-widgets-clickstream-related-request-id": request_id or "", "address-ui-widgets-address-wizard-interaction-id": interaction_id or ""}
        resp = self.session.post(f"https://www.{self.domain}/a/addresses/add?ref=ya_address_book_add_post", headers=headers3, data=payload3)
        self.countryData = data

        # Try to extract address ID from the POST response or redirect page
        addr_id = self.extractBetween(resp.text, 'addressId=', '&') or self.extractBetween(resp.text, 'addressId=', '"') or self.extractBetween(resp.text, '"addressId":"', '"')
        if addr_id:
            self._addressId = addr_id
            return True

        # Fallback: scrape the address book page for the most recent address
        self._addressId = self.__getAddressIdFromBook()
        return resp.status_code == 200

    def __getAddressIdFromBook(self) -> Optional[str]:
        """Get address ID from the address book page (works for all countries)."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"}
            resp = self.session.get(f"https://www.{self.domain}/a/addresses", headers=headers, timeout=30)
            # Address IDs appear as data-addressid or in edit/delete links
            addr_id = self.extractBetween(resp.text, 'data-addressid="', '"')
            if addr_id: return addr_id
            addr_id = self.extractBetween(resp.text, 'addressId=', '&')
            if addr_id: return addr_id
            addr_id = self.extractBetween(resp.text, 'addressID=', '&')
            if addr_id: return addr_id
            # Try JSON pattern
            addr_id = self.extractBetween(resp.text, '"addressId":"', '"')
            return addr_id
        except Exception:
            return None

    def getBillingAddressId(self) -> Optional[str]:
        # First check if we already got it from addBillingAddress
        if hasattr(self, '_addressId') and self._addressId:
            return self._addressId
        # Fallback: scrape address book
        return self.__getAddressIdFromBook()

    def handleBillingAddress(self) -> dict:
        added = self.addBillingAddress()
        if not added:
            return {'status': False, 'message': 'Failed Adding Billing Address'}
        addressId = self.getBillingAddressId()
        if addressId:
            return {'status': True, 'message': 'Billing Address Added', 'data': self.countryData, 'addressId': addressId}
        return {'status': False, 'message': 'Failed Adding Billing Address'}
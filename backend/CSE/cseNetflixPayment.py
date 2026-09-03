"""
╔══════════════════════════════════════════════════════════════════════╗
║       🔐 Netflix Payment — Client Side Encryption                    ║
║                     (CSE - Python Implementation)                    ║
╚══════════════════════════════════════════════════════════════════════╝
📌 DESCRIPTION
Implementa el cifrado de tarjeta de Netflix (CLCS addCardAndStartMembership).
Replica el módulo JS 53568 del chunk 8967 de nflxext.com.

Algoritmo: RSA-OAEP SHA-1 · exponent fijo 0x10001 · AID fijo 2

🛠 INSTALL
pip install cryptography curl_cffi

📥 BASIC USAGE

  from CSE.cseNetflixPayment import CseNetflixPayment

  result = CseNetflixPayment.encrypt(
      kid = 1776877276283,
      pk  = "9fe0e3effa1a4b4b...",   # hex modulus de ncds o del GraphQL response
      data = {
          "cc": {
              "num":    "4111111111111111",
              "expMon": "05",
              "expYr":  "2027",
              "cvv":    "123",
          }
      }
  )

📤 OUTPUT
{
  "response": {
    "VERSION": 1,
    "PAYLOAD": "eyJFREFUQSI6..."
  }
}

📑 REVERSE ENGINEERING NOTES
- JS source: assets.nflxext.com/web/ffe/wp/8967.{hash}.js
- Módulo 53568 → encrypt_oaep / setPublic
- Módulo 62072 (= 53568 alias) → exportado como c.default en encryptCardData
- Plaintext: JSON.stringify(data) donde data = {cc: {num, expMon, expYr, cvv}}
  (expYr se normaliza a 4 dígitos si viene con 2)
- Encrypt: RSA-OAEP SHA-1, modulus hex, exponent hex (siempre '10001')
- Inner JSON: {"EDATA":"<b64(rsa_bytes)>","AID":2,"KID":kid}
- PAYLOAD: base64(inner_json)
- Clave pública disponible en:
    · ncds.nflxext.com/v1/2/jsonp/current  (JSONP → {kid, aid, modulus, exponent})
    · GraphQL response de saveSelectedPaymentOption → publicKey.{modulus,exponent,kid,aid}

👨‍💻 AUTHOR — Vxsilisk @ Sagitario  |  https://t.me/Sxgitario
"""

import json, base64, re
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.backends import default_backend


NCDS_URL  = 'https://ncds.nflxext.com/v1/2/jsonp/current'
_EXPONENT = '10001'   # siempre 65537 — hardcoded en ncds y en el JS
_AID      = 2         # siempre 2 — hardcoded en el JS


class CseNetflixPayment:

    # ── API pública (estático — sin estado) ─────────────────────────────

    @staticmethod
    def encrypt(kid: int, pk: str, data: dict) -> dict:
        """
        Cifra los datos de tarjeta con RSA-OAEP SHA-1.

        Args:
            kid:  Key ID entero (de ncds o del GraphQL publicKey.kid)
            pk:   Modulus hex string (de ncds o del GraphQL publicKey.modulus)
            data: Plaintext ya estructurado:
                  {
                    "cc": {
                      "num":    "4111111111111111",
                      "expMon": "05",
                      "expYr":  "2027",   # 2 ó 4 dígitos
                      "cvv":    "123",
                      "zip":    "12345",  # opcional
                    }
                  }

        Returns:
            {
              "response": {
                "VERSION": 1,
                "PAYLOAD": "<base64_of_inner_json>"
              }
            }
        """
        try:
            plaintext = CseNetflixPayment._build_plaintext(data)
            encrypted = CseNetflixPayment._rsa_encrypt(pk, plaintext)
            payload   = CseNetflixPayment._build_payload(kid, encrypted)
            return {'response': {'VERSION': 1, 'PAYLOAD': payload}}
        except Exception as e:
            raise RuntimeError(f'CseNetflixPayment.encrypt failed: {e}') from e

    @staticmethod
    def fetch_public_key() -> dict:
        """
        GET ncds.nflxext.com/v1/2/jsonp/current
        Retorna {kid, aid, modulus (hex), exponent (hex)}.
        """
        from curl_cffi import requests as curl
        r = curl.get(
            NCDS_URL,
            params={'callback': 'callback'},
            impersonate='chrome131',
            timeout=10,
        )
        r.raise_for_status()
        m = re.search(r'callback\((\{.*?\})\)', r.text, re.DOTALL)
        if not m:
            raise ValueError(f'Respuesta inesperada de ncds: {r.text[:200]}')
        return json.loads(m.group(1))

    # ── Internals ────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_year(yr: str) -> str:
        v = int(yr)
        if 0 < v < 100:
            return str(v + 2000)
        return yr

    @staticmethod
    def _build_plaintext(data: dict) -> str:
        """
        Normaliza expYr y serializa el plaintext.
        Replica: JSON.stringify({cc: {...data.cc, expYr: normalize(expYr)}})
        """
        cc = dict(data.get('cc', data))   # acepta {cc:{...}} o directamente {num,...}
        cc['expYr'] = CseNetflixPayment._normalize_year(str(cc.get('expYr', '')))
        return json.dumps({'cc': cc}, separators=(',', ':'))

    @staticmethod
    def _rsa_encrypt(modulus_hex: str, plaintext: str) -> bytes:
        """RSA-OAEP SHA-1 — replica encrypt_oaep del módulo JS 53568."""
        n = int(modulus_hex, 16)
        e = int(_EXPONENT,   16)
        pub = RSAPublicNumbers(e, n).public_key(default_backend())
        return pub.encrypt(
            plaintext.encode('utf-8'),
            OAEP(mgf=MGF1(algorithm=SHA1()), algorithm=SHA1(), label=None),
        )

    @staticmethod
    def _build_payload(kid: int, encrypted: bytes) -> str:
        """
        inner_json = {"EDATA":"<b64>","AID":2,"KID":kid}
        PAYLOAD    = base64(inner_json)
        """
        edata      = base64.b64encode(encrypted).decode()
        inner_json = f'{{"EDATA":"{edata}","AID":{_AID},"KID":{kid}}}'
        return base64.b64encode(inner_json.encode()).decode()


# ═══════════════════════════════════════════════════════════════════════
# Test rápido
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys

    KID_HAR = 1776877276283
    PK_HAR  = (
        '9fe0e3effa1a4b4b081c5b7b9a715414b96f044de6f8a93eee724c1e79f07208'
        'a918ba670c927bd094efc02b379fa12d1e540aae62c3990ad47ed3c6347e64b'
        'a1d422a74a4ba5ae26c8be3fdd8c4009cd3de8736445c006cf6da7aebc71dbaa'
        '82f9ca87e698b372cd14b6fa9ba34af2db3d0b391a45b9bb36ee925d0884b4a'
        '03c4f914b31a6f411eaa593d91464bfa71ec78c204cf3466f44e1a5a20ad6588'
        '245cd1e3ec5d79aeade9c9bc6ad152784e9dc1e08ca12e6bcce68ddf0b1a380a'
        '63a10777dc507f335ec0f05b0973177d6cf2dbf2e5a57a89a36567fc0145222c'
        '98defde4ce1a5a2291cf9591b47948ab7778e7374a58f8b84214c60da1fa30eb7d'
    )

    # Formato igual al de la API spec
    request_body = {
        'kid': KID_HAR,
        'pk':  PK_HAR,
        'data': {
            'cc': {
                'num':    '4557880666503796',
                'expMon': '05',
                'expYr':  '2027',
                'cvv':    '123',
            }
        }
    }

    print('[ Test offline — clave del HAR ]')
    result = CseNetflixPayment.encrypt(**request_body)
    print(json.dumps(result, indent=2))

    # Verificar estructura
    resp    = result['response']
    assert resp['VERSION'] == 1,               'VERSION debe ser 1'
    inner   = json.loads(base64.b64decode(resp['PAYLOAD'] + '=='))
    assert inner['AID'] == 2,                  'AID debe ser 2'
    assert inner['KID'] == KID_HAR,            'KID no coincide'
    edata_b = base64.b64decode(inner['EDATA'] + '==')
    assert len(edata_b) == 256,                f'EDATA debe ser 256 bytes, es {len(edata_b)}'
    print()
    print(f'  AID   = {inner["AID"]}')
    print(f'  KID   = {inner["KID"]}')
    print(f'  EDATA = {len(edata_b)} bytes')
    print()
    print('✅  Cifrado OK — estructura válida')

    if '--live' in sys.argv:
        print()
        print('[ Test live — clave de ncds.nflxext.com ]')
        live_pk = CseNetflixPayment.fetch_public_key()
        print(f'  kid live = {live_pk["kid"]}')
        res_live = CseNetflixPayment.encrypt(
            kid  = live_pk['kid'],
            pk   = live_pk['modulus'],
            data = request_body['data'],
        )
        print(json.dumps(res_live, indent=2))

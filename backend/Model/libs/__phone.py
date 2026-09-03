# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import requests


_API_KEY = 'ca42c5a821315f4ef8809c9c1a30effb'
_API_URL = 'https://apilayer.net/api/validate'


class phoneLookup:

    class phoneResult:
        def __init__(self, array:dict) -> None:
            for key, value in array.items(): setattr(self, key, value)


    def __init__(self, query:str) -> None:
        self.query = query


    def __extractNumber(self) -> str:
        """Extract phone number from query, keep + prefix and digits."""
        raw = self.query.strip().split()[0] if self.query.strip() else ''
        number = ''
        for ch in raw:
            if ch == '+' and not number:
                number += ch
            elif ch.isdigit():
                number += ch
        return number


    def run(self) -> 'phoneLookup.phoneResult':
        number = self.__extractNumber()
        if not number or len(number) < 7:
            return phoneLookup.phoneResult({'status': False, 'message': 'Insert a valid phone number! (e.g. +526631234567)'})

        try:
            resp = requests.get(_API_URL, params={
                'access_key': _API_KEY,
                'number': number,
                'country_code': '',
                'format': 1
            }, timeout=10).json()

            if not resp.get('valid', False):
                return phoneLookup.phoneResult({'status': False, 'message': f'Number {number} is not valid!'})

            line_type = resp.get('line_type') or 'Unknown'
            carrier   = resp.get('carrier') or 'Unknown'
            location  = resp.get('location') or 'Unknown'

            return phoneLookup.phoneResult({
                'status': True,
                'valid': True,
                'number': resp.get('number', number),
                'local_format': resp.get('local_format', 'N/A'),
                'international_format': resp.get('international_format', number),
                'country_prefix': resp.get('country_prefix', 'N/A'),
                'country_code': resp.get('country_code', 'N/A'),
                'country_name': resp.get('country_name', 'N/A'),
                'location': location,
                'carrier': carrier,
                'line_type': line_type,
            })

        except Exception as e:
            return phoneLookup.phoneResult({'status': False, 'message': f'API error: {str(e)}'})

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

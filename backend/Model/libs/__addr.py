# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
"""
Address Generator — Real addresses + Fake identities.
Uses dad-tool (real addresses) + random-address (US) + Faker (fake identity).
"""

import json, random
from pathlib import Path
from faker import Faker


#//! Load dad-tool JSON data directly (no broken API)
_DAD_DIR = None
try:
    import dad_tool
    _DAD_DIR = Path(dad_tool.__file__).parent / "dad" / "src" / "addresses"
except ImportError:
    pass

#//! random-address for US
try:
    from random_address import real_random_address
    _HAS_RADDR = True
except ImportError:
    _HAS_RADDR = False


#//! Country → dad-tool JSON paths + Faker locale
_COUNTRY_MAP = {
    'US': {'dirs': ['united-states'], 'locale': 'en_US', 'flag': '🇺🇸', 'name': 'United States'},
    'MX': {'dirs': ['mexico'],        'locale': 'es_MX', 'flag': '🇲🇽', 'name': 'Mexico'},
    'CA': {'dirs': ['canada'],         'locale': 'en_CA', 'flag': '🇨🇦', 'name': 'Canada'},
    'BR': {'dirs': [],                 'locale': 'pt_BR', 'flag': '🇧🇷', 'name': 'Brazil'},
    'IT': {'dirs': [],                 'locale': 'it_IT', 'flag': '🇮🇹', 'name': 'Italy'},
    'AU': {'dirs': ['australia'],      'locale': 'en_AU', 'flag': '🇦🇺', 'name': 'Australia'},
    'JP': {'dirs': [],                 'locale': 'ja_JP', 'flag': '🇯🇵', 'name': 'Japan'},
    'UK': {'dirs': ['europe'],         'locale': 'en_GB', 'flag': '🇬🇧', 'name': 'United Kingdom'},
    'DE': {'dirs': ['europe'],         'locale': 'de_DE', 'flag': '🇩🇪', 'name': 'Germany'},
    'FR': {'dirs': ['europe'],         'locale': 'fr_FR', 'flag': '🇫🇷', 'name': 'France'},
    'ES': {'dirs': ['europe'],         'locale': 'es_ES', 'flag': '🇪🇸', 'name': 'Spain'},
}

#//! Filter patterns for europe files (they mix countries)
_EU_FILE_MAP = {
    'UK': 'uk-addresses.json',
    'DE': 'de-addresses.json',
    'FR': 'fr-addresses.json',
    'ES': 'es-addresses.json',
}


def _loadAddresses(country: str) -> list:
    """Load real addresses from dad-tool JSON files."""
    cfg = _COUNTRY_MAP.get(country, {})
    if not _DAD_DIR or not cfg.get('dirs'):
        return []

    addresses = []
    for d in cfg['dirs']:
        dirPath = _DAD_DIR / d
        if not dirPath.exists(): continue

        #//* For European countries, load specific file
        if country in _EU_FILE_MAP:
            fpath = dirPath / _EU_FILE_MAP[country]
            if fpath.exists():
                with open(fpath) as f: addresses.extend(json.load(f))
        else:
            #//* Load all non-minified JSON files in the directory
            for fpath in dirPath.glob('*-addresses.json'):
                if '.min.' not in fpath.name:
                    with open(fpath) as f: addresses.extend(json.load(f))

    return addresses


class AddrGenerator:
    """Generates real address + fake identity for a given country."""

    class addrResult:
        def __init__(self, array: dict):
            for key, value in array.items(): setattr(self, key, value)

    @classmethod
    def generate(cls, country: str = 'US', amount: int = 1) -> 'AddrGenerator.addrResult':
        country = country.upper().strip()
        if country not in _COUNTRY_MAP:
            codes = ', '.join(_COUNTRY_MAP.keys())
            return cls.addrResult({'status': False, 'message': f'Country not supported! Use: {codes}'})

        cfg   = _COUNTRY_MAP[country]
        fake  = Faker(cfg['locale'])
        addrs = _loadAddresses(country)

        #//* US: prefer random-address (more data, geocode verified)
        useRaddr = country == 'US' and _HAS_RADDR

        results = []
        for _ in range(amount):
            #//* Real address
            if useRaddr:
                try:
                    ra = real_random_address()
                    addr = {'street1': ra.get('address1', ''), 'street2': ra.get('address2', ''),
                            'city': ra.get('city', ''), 'state': ra.get('state', ''),
                            'zip': ra.get('postalCode', ''), 'country': 'US'}
                except: addr = random.choice(addrs) if addrs else None
            else:
                addr = random.choice(addrs) if addrs else None

            #//* Fallback: Faker address (not real but better than nothing)
            if not addr:
                addr = {'street1': fake.street_address(), 'street2': '',
                        'city': fake.city(), 'state': fake.state() if hasattr(fake, 'state') else '',
                        'zip': fake.postcode(), 'country': country}

            #//* Fake identity
            results.append({
                'name':    fake.name(),
                'email':   fake.free_email(),
                'phone':   fake.phone_number(),
                'street':  addr.get('street1', ''),
                'street2': addr.get('street2', ''),
                'city':    addr.get('city', ''),
                'state':   addr.get('state', ''),
                'zip':     addr.get('zip', ''),
                'country': cfg['name'],
                'flag':    cfg['flag'],
            })

        return cls.addrResult({
            'status':  True,
            'results': results,
            'total':   len(results),
            'country': cfg['name'],
            'flag':    cfg['flag'],
            'code':    country,
        })

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

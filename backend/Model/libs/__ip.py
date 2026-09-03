# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import requests


class ipLookup:
    """
    IP lookup using proxycheck.io (risk + geo + VPN/proxy detection)
    with ip-api.com as geo fallback.

    :author: `Stradale`
    """

    class ipResult:
        def __init__(self, array:dict) -> None:
            for key, value in array.items(): setattr(self, key, value)


    def __init__(self, query:str) -> None:
        self.query = query


    def __getIp(self) -> str:
        """Extract first valid IPv4 from query."""
        for p in self.query.split():
            p = p.strip('.,;()[]{}')
            segs = p.split('.')
            if len(segs) == 4 and all(s.isdigit() and 0 <= int(s) <= 255 for s in segs):
                return p
        return None


    def __proxycheck(self, ip:str) -> dict:
        """Fetch from proxycheck.io (risk + geo + proxy/VPN, free no key)."""
        try:
            resp = requests.get(
                f'https://proxycheck.io/v2/{ip}',
                params={'vpn': 1, 'asn': 1, 'risk': 1},
                timeout=10
            ).json()
            if resp.get('status') == 'ok' and ip in resp:
                return resp[ip]
        except: pass
        return {}


    def __ipapi_fallback(self, ip:str) -> dict:
        """Fallback geo from ip-api.com if proxycheck fails."""
        try:
            resp = requests.get(
                f'http://ip-api.com/json/{ip}',
                params={'fields': 'status,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,hosting,reverse'},
                timeout=8
            ).json()
            if resp.get('status') == 'success':
                return resp
        except: pass
        return {}


    def __getColor(self, score) -> str:
        try:
            s = int(score)
            if   s >= 80: return '🔴'
            elif s >= 50: return '🟠'
            elif s >= 20: return '🟡'
            else: return '🟢'
        except: return '⚪'


    def run(self) -> 'ipLookup.ipResult':
        ip = self.__getIp()
        if not ip:
            return ipLookup.ipResult({'status': False, 'message': 'Insert a valid IPv4 address'})

        pc = self.__proxycheck(ip)

        if pc:
            risk_score = pc.get('risk', 0)
            color      = self.__getColor(risk_score)
            proxy_flag = pc.get('proxy', 'no').lower() == 'yes'
            vpn_type   = pc.get('type', '').lower()
            is_vpn     = vpn_type == 'vpn'
            is_hosting = vpn_type in ('hosting', 'business')

            #//* Risk level from score
            s = int(risk_score) if str(risk_score).isdigit() else 0
            if   s >= 80: risk_level = 'Very High'
            elif s >= 66: risk_level = 'High'
            elif s >= 33: risk_level = 'Medium'
            elif s >= 1:  risk_level = 'Low'
            else:         risk_level = 'Very Low'

            country_code = pc.get('isocode', 'N/A')

            return ipLookup.ipResult({
                'status':      True,
                'ip':          ip,
                'is_server':   is_hosting,
                'is_vpn':      is_vpn or proxy_flag,
                'is_proxy':    proxy_flag,
                'score':       str(risk_score),
                'risk':        f"{risk_level} {color}",
                'blacklist':   'N/A',
                'host':        pc.get('hostname', 'N/A') or 'N/A',
                'carrier':     pc.get('provider', 'N/A') or 'N/A',
                'org':         pc.get('organisation', 'N/A') or 'N/A',
                'asn':         pc.get('asn', 'N/A') or 'N/A',
                'country':     f"{pc.get('country', 'N/A')} -{country_code}-",
                'state':       pc.get('region', 'N/A') or 'N/A',
                'city':        pc.get('city', 'N/A') or 'N/A',
                'region':      pc.get('regioncode', 'N/A') or 'N/A',
                'postal_code': pc.get('postcode', 'N/A') or 'N/A',
                'timezone':    pc.get('timezone', 'N/A') or 'N/A',
                'coordinates': f"{pc.get('latitude', 'N/A')} {pc.get('longitude', 'N/A')}",
                'is_mobile':   False,
                'net_type':    pc.get('type', 'N/A') or 'N/A',
            })

        #//* Fallback to ip-api.com (no risk score, but reliable geo)
        fb = self.__ipapi_fallback(ip)
        if fb:
            return ipLookup.ipResult({
                'status':      True,
                'ip':          ip,
                'is_server':   fb.get('hosting', False),
                'is_vpn':      fb.get('proxy', False),
                'is_proxy':    fb.get('proxy', False),
                'score':       'N/A',
                'risk':        'N/A ⚪',
                'blacklist':   'N/A',
                'host':        fb.get('reverse', 'N/A') or 'N/A',
                'carrier':     fb.get('isp', 'N/A') or 'N/A',
                'org':         fb.get('org', 'N/A') or 'N/A',
                'asn':         fb.get('as', 'N/A') or 'N/A',
                'country':     f"{fb.get('country', 'N/A')} -{fb.get('countryCode', 'N/A')}-",
                'state':       fb.get('regionName', 'N/A') or 'N/A',
                'city':        fb.get('city', 'N/A') or 'N/A',
                'region':      'N/A',
                'postal_code': fb.get('zip', 'N/A') or 'N/A',
                'timezone':    fb.get('timezone', 'N/A') or 'N/A',
                'coordinates': f"{fb.get('lat', 'N/A')} {fb.get('lon', 'N/A')}",
                'is_mobile':   False,
                'net_type':    'N/A',
            })

        return ipLookup.ipResult({'status': False, 'message': 'Error fetching IP data'})

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

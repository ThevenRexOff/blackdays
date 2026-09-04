# ══════════════════════════════════════════════════════════════════════════
#  Route registry — every consumable endpoint of the JILL_BOT API.
# ══════════════════════════════════════════════════════════════════════════
import inspect

from apis.tools import cmd_bin, cmd_fake, cmd_ip, cmd_phone, cmd_gen, cmd_sk, cmd_site, cmd_tmail, cmd_amz_generator
from apis.gates import gate_run

TOOLS = {
    'bin':   {'fn': cmd_bin,   'params': {'bin': 'BIN (6+ digits)'}},
    'fake':  {'fn': cmd_fake,  'params': {'country': 'US/MX/CA/...', 'amount': '1-10 (default 1)'}},
    'ip':    {'fn': cmd_ip,    'params': {'ip': 'IPv4 address'}},
    'phone': {'fn': cmd_phone, 'params': {'number': 'phone number (+52...)'}},
    'gen':   {'fn': cmd_gen,   'params': {'cc': 'extrapolate bin CC|MM|YY|CVV', 'amount': 'cards (default 10)'}},
    'sk':    {'fn': cmd_sk,    'params': {'key': 'Stripe key sk_live_...'}},
    'site':  {'fn': cmd_site,  'params': {'url': 'https://target.com'}},
    'tmail': {'fn': cmd_tmail, 'params': {'': ''}},
}


def _route(method, path, desc, params, handler):
    return {'method': method, 'path': path, 'description': desc, 'params': params, 'handler': handler}


ROUTES = [
    _route('GET', '/apis', 'List every endpoint', {}, lambda p: {'status': True, 'endpoints': '/apis/routes'}),
    _route('GET', '/apis/routes', 'Index of all API routes', {}, lambda p: {'status': True, 'version': '1.0.0', 'routes': public_routes()}),
    _route('GET', '/apis/health', 'Health check + uptime info', {}, lambda p: {'status': True, 'message': 'ok', 'api': 'jillbot'}),
    _route('GET', '/apis/bin', 'BIN / card lookup', TOOLS['bin']['params'], TOOLS['bin']['fn']),
    _route('GET', '/apis/fake', 'Generate fake identity + real address', TOOLS['fake']['params'], TOOLS['fake']['fn']),
    _route('GET', '/apis/ip', 'IP / risk / VPN-geo lookup', TOOLS['ip']['params'], TOOLS['ip']['fn']),
    _route('GET', '/apis/phone', 'Phone carrier / line lookup', TOOLS['phone']['params'], TOOLS['phone']['fn']),
    _route('GET', '/apis/gen', 'Live CC generator from an extrapolate bin', TOOLS['gen']['params'], TOOLS['gen']['fn']),
    _route('GET', '/apis/sk', 'Stripe key checker (live/dead + balance)', TOOLS['sk']['params'], TOOLS['sk']['fn']),
    _route('GET', '/apis/site', 'Website technology fingerprint', TOOLS['site']['params'], TOOLS['site']['fn']),
    _route('GET', '/apis/tmail', 'TempMail session info', TOOLS['tmail']['params'], TOOLS['tmail']['fn']),
    _route('GET', '/apis/amz_generator', 'Amazon account/cookie generator', {'country': 'US/MX/CA/...', 'proxy': 'optional'}, cmd_amz_generator),
    _route('GET', '/apis/gate/mj', 'Stripe Auth gate — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/mm', 'Gate mm — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/wr', 'Gate wr — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/br', 'Gate br — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/bl', 'Blizzard/Battle.net (Disney+ core) gate', {'card': 'cc|mm|yy|cvv', 'proxy': 'optional'}, gate_run),
    _route('GET', '/apis/gate/zb', 'Telcel ClaroPay — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv', 'phone': '10 digits', 'monto': '10-500'}, gate_run),
    _route('GET', '/apis/gate/ps', 'BAIT recargas — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv', 'phone': '10 digits', 'monto': '50/100/200/300/500'}, gate_run),
    _route('GET', '/apis/gate/dns', 'Gate dns — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/rc', 'Gate rc — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/op', 'Gate op — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/pd', 'PlayDoit MX CCN — Depósito $100', {'card': 'cc|mm|yy|cvv', 'proxy': 'optional'}, gate_run),
    _route('GET', '/apis/gate/wu', 'Gate wu — CC|MM|YY|CVV', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/amz', 'Amazon — needs cookie', {'card': 'cc|mm|yy|cvv', 'cookie': 'amazon cookie'}, gate_run),
    _route('GET', '/apis/gate/telcel', 'Telcel MX recharges', {'card': 'cc|mm|yy|cvv', 'phone': '10 digits', 'monto': 'MXN amount'}, gate_run),
    _route('GET', '/apis/gate/netflix', 'Netflix Plans MX (needs CAPSOLVER_KEY + MailX)', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/disney', 'Disney+ Plans MX (needs CAPSOLVER_KEY)', {'card': 'cc|mm|yy|cvv'}, gate_run),
    _route('GET', '/apis/gate/sfy', 'Shopify Checkout — needs website (alias: shopify)', {'card': 'cc|mm|yy|cvv', 'website': 'https://tienda.com', 'address': 'optional JSON', 'email': 'optional', 'product': 'optional JSON', 'proxy': 'optional'}, gate_run),
    _route('GET', '/apis/gate/shopify', 'Shopify Checkout — needs website', {'card': 'cc|mm|yy|cvv', 'website': 'https://tienda.com', 'address': 'optional JSON', 'email': 'optional', 'product': 'optional JSON', 'proxy': 'optional'}, gate_run),
    _route('POST', '/apis/gate', 'Run any gate (JSON body: gate, card, phone, monto, cookie)', {'body': '{"gate":"mj","card":"...|..|..|.."}'}, gate_run),

]


def match(path: str):
    """Resolve a request path to (handler, gate_name_or_None)."""
    path = path.split('?', 1)[0]
    if path in ('/apis', '/apis/'):
        return ROUTES[0]['handler'], None
    if path.rstrip('/') in ('/apis/routes', '/apis/health'):
        return (ROUTES[1]['handler'], None) if path.rstrip('/') == '/apis/routes' else (ROUTES[2]['handler'], None)
    # Original /apis/gate/ pattern
    prefix = '/apis/gate/'
    if path.startswith(prefix):
        name = path[len(prefix):].split('/')[0] or None
        return gate_run, name
    for r in ROUTES:
        if r['path'] == path:
            return r['handler'], None
    return None, None


def public_routes():
    """Return ROUTES stripped of handler callables (JSON-safe)."""
    out = []
    for r in ROUTES:
        out.append({'method': r['method'], 'path': r['path'],
                    'description': r['description'], 'params': r['params']})
    return out
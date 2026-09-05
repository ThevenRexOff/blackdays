# ══════════════════════════════════════════════════════════════════════════
#  Endpoint smoke test — verifica que todos los endpoints respondan y que las
#  validaciones clave devuelvan la estructura esperada.
#
#  Uso:
#      python tests/check_api.py                 # contra http://127.0.0.1:8080
#      python tests/check_api.py --base http://127.0.0.1:18080
#
#  Los endpoints que hacen llamadas externas de red (gates, ip, phone, site,
#  tmail_proxy, amz_generator) se marcan como "live" y solo se comprueba que
#  respondan JSON con un shape válido.
# ══════════════════════════════════════════════════════════════════════════
import argparse
import json
import sys
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:8080'
CARD = 'card=4599858290851419|12|2030|985'

# Campos cuyo valor puede cambiar entre ejecuciones (datos aleatorios/timing).
VOLATILE = {'data', 'time_taken', 'total', 'country', 'flag', 'code', 'name', 'email',
            'phone', 'street', 'street2', 'city', 'state', 'zip', 'bin', 'card',
            'sessions', 'trace'}


def hit(method, path, body=None, timeout=90):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if body is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {'exception': str(e)[:150]}


def shape(v):
    """Signature estructural de una respuesta (key set + tipos)."""
    if isinstance(v, type):
        return v.__name__
    if isinstance(v, dict):
        return {k: shape(x) if k not in VOLATILE else 'volatile' for k, x in v.items()}
    if isinstance(v, list):
        return ['list', len(v)] + ([shape(v[0])] if v else [])
    return type(v).__name__


def matches(actual, expected):
    """Comprueba que cada clave esperada exista en la respuesta con el shape correcto
    (se permiten claves extra en la respuesta real)."""
    if isinstance(expected, type):
        return isinstance(actual, expected)
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(matches(actual.get(k), exp) for k, exp in expected.items() if k not in VOLATILE)
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        if expected[0] != 'list':
            return True
        if expected[1] is not int and len(actual) != expected[1]:
            return False
        if len(expected) > 2:
            return all(matches(item, expected[2]) for item in actual)
        return True
    return actual == expected


# (método, path, body, shape esperado, descripción)
CASES = [
    ('GET',    '/apis',                  None,                   {'status': bool, 'endpoints': str}, 'lista endpoints'),
    ('GET',    '/apis/routes',           None,                   {'status': bool, 'version': str, 'routes': ['list', int, {'method': str, 'path': str, 'description': str, 'params': {}}]}, 'índice de rutas'),
    ('GET',    '/apis/health',           None,                   {'status': bool, 'message': str, 'api': str}, 'health'),
    ('GET',    '/apis/bin?bin=424242',   None,                   {'status': bool, 'data': {}}, 'bin lookup'),
    ('GET',    '/apis/bin',              None,                   {'status': bool, 'error': str}, 'bin sin param'),
    ('GET',    '/apis/fake?country=US&amount=1', None,           {'status': bool, 'data': ['list', int, {}]}, 'fake identity'),
    ('GET',    '/apis/ip',               None,                   {'status': bool, 'error': str}, 'ip sin param'),
    ('GET',    '/apis/phone',            None,                   {'status': bool, 'error': str}, 'phone sin param'),
    ('GET',    '/apis/gen',              None,                   {'status': bool, 'error': str}, 'gen sin param'),

    ('GET',    '/apis/gate/zzz?' + CARD, None,                   {'status': bool, 'error': str}, 'gate desconocido'),
    ('GET',    '/apis/gate/mj',          None,                   {'status': bool, 'error': str}, 'gate sin card -> 400'),
    ('GET',    '/apis/gate/mj?card=123|1|2|3', None,             {'status': bool, 'error': str}, 'card inválida'),
    ('GET',    '/apis/gate/zb?' + CARD,  None,                   {'status': bool, 'code': str, 'error': str}, 'zb sin phone'),
    ('GET',    '/apis/gate/shopify?' + CARD, None,               {'status': bool, 'code': str, 'error': str}, 'shopify sin website'),
    ('GET',    '/apis/gate/amz?' + CARD, None,                   {'status': bool, 'code': str, 'error': str}, 'amazon sin cookie'),
    ('GET',    '/apis/gate/telcel?' + CARD, None,                {'status': bool, 'code': str, 'error': str}, 'telcel sin phone'),

    ('POST',   '/apis/gate',             {'gate': 'zzz'},        {'status': bool, 'error': str}, 'POST gate desconocido'),
    ('POST',   '/apis/amz_generator',    {'country': 'ZZ'},      {'status': bool, 'error': str}, 'amz gen país inválido'),
    ('POST',   '/apis/tmail_proxy',      {'action': 'bogus'},    {'status': bool, 'error': str}, 'tmail proxy acción inválida'),

    ('OPTIONS', '/apis/health',          None,                   {'status': bool, 'error': str}, 'preflight sin origin -> 403'),

    # Llamadas externas: solo validamos que responda JSON con status.
    ('GET',    '/apis/gate/op?' + CARD,  None,                   {'status': 'live', 'card': 'volatile', 'time_taken': 'volatile'}, 'gate op (live)'),
    ('GET',    '/apis/gate/dns?' + CARD, None,                   {'status': 'live', 'card': 'volatile', 'time_taken': 'volatile'}, 'gate dns (live)'),
    ('POST',   '/apis/tmail_proxy',      {'action': 'domains', 'params': {}},  {'status': bool, 'domains': ['list', int, {}]}, 'tmail proxy domains (live)'),
]

EXPECT_400 = {'/apis/gate/mj'}
EXPECT_403 = {('OPTIONS', '/apis/health')}


def run():
    global BASE
    parser = argparse.ArgumentParser(description='JILL_BOT API smoke test')
    parser.add_argument('--base', default=BASE, help='Base URL de la API')
    args = parser.parse_args()
    BASE = args.base

    passed = failed = 0
    for method, path, body, expected, desc in CASES:
        code, resp = hit(method, path, body)
        expect_status = 403 if (method, path) in EXPECT_403 else (400 if path in EXPECT_400 else 200)
        ok = code == expect_status
        if ok and expected:
            if expected.get('status') == 'live':
                ok = resp.get('status') in ('Approved ✅', 'Declined ❌', 'Live Card 🟢', 'Error ⚠️', 'Unknown ⚠️')
            else:
                ok = matches(resp, expected)
        if ok:
            passed += 1
            print(f'  PASS  {method:<6} {path:<45} {desc}')
        else:
            failed += 1
            print(f'  FAIL  {method:<6} {path:<45} {desc}')
            print(f'        status={code} body={json.dumps(resp, ensure_ascii=False)[:200]}')

    print(f'\n{passed} passed, {failed} failed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(run())
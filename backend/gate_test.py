#!/usr/bin/env python3
import sys, time, traceback
sys.path.insert(0, '/opt/jillbot')

# Test card — always declines but exercises the full gate flow
CC   = ['4111111111111111', '01', '30', '123']
BIN  = {
    'brand': 'VISA', 'type': 'CREDIT', 'level': 'CLASSIC',
    'bank': 'TEST BANK', 'country': 'US', 'flag': '🇺🇸',
    'bin': '411111'
}
MX_PHONE = '5548448605'

PROXY_HINTS = ['403', '407', 'proxy', 'blocked', 'ip', 'region', 'country',
               'forbidden', 'access denied', 'vpn', 'unavailable', '451',
               'geo', 'restricted', 'not available', 'contabo']

results = {}

def classify(resp: str) -> str:
    r = resp.lower()
    if any(h in r for h in PROXY_HINTS):
        return '🌐 PROXY'
    return '✅ OK'

def test(name, cmd, fn, *args, **kwargs):
    t0 = time.time()
    try:
        r = fn(*args, **kwargs)
        elapsed = round(time.time() - t0, 1)
        resp = str(r.get('response', r.get('raise', r)))[:120]
        status = r.get('status', False)
        if not status:
            verdict = classify(resp)
        else:
            success = r.get('success', False)
            verdict = classify(resp) if not success else '✅ OK'
        results[name] = {'cmd': cmd, 'verdict': verdict, 'resp': resp, 'time': elapsed}
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        err = str(e)[:120]
        results[name] = {'cmd': cmd, 'verdict': classify(err) if any(h in err.lower() for h in PROXY_HINTS) else '❌ ERROR', 'resp': err, 'time': elapsed}

# ── GATES WITH run_check ──────────────────────────────────────────────────
from Commands.Gates import mj, mm, wr, br, cp, bl, dns, gt, wu, rc, op, pd, ts, ps, zb, amazon

test('Mojito (Stripe Auth)',       '/mj',  mj.run_check,  CC, BIN)
test('Moscow Mule (Auth $2)',       '/mm',  mm.run_check,  CC, BIN)
test('White Russian (Recurly)',     '/wr',  wr.run_check,  CC, BIN)
test('BridgePay',                  '/ts',  ts.run_check,  CC, BIN)
test('NMI',                        '/gt',  gt.run_check,  CC, BIN)
test('Braintree',                  '/br',  br.run_check,  CC, BIN)
test('ClaroPay (PayTelcel)',        '/zb',  zb.run_check,  CC, BIN, {'phone': MX_PHONE, 'monto': '10'})
test('BAIT Recargas',              '/ps',  ps.run_check,  CC, BIN, {'phone': MX_PHONE, 'monto': '50'})
test('CyberPanel',                 '/cp',  cp.run_check,  CC, BIN)
test('Blackline',                  '/bl',  bl.run_check,  CC, BIN)
test('DNS Filter',                 '/dns', dns.run_check,  CC, BIN)
test('Western Union',              '/wu',  wu.run_check,  CC, BIN)
test('RC',                         '/rc',  rc.run_check,  CC, BIN)
test('OP',                         '/op',  op.run_check,  CC, BIN)
test('PD',                         '/pd',  pd.run_check,  CC, BIN)
test('Amazon',                     '/amz', amazon.run_check, CC, BIN)

# ── TELCEL (no run_check — test core directly) ────────────────────────────
try:
    from Commands.Gates import telcel_core
    t0 = time.time()
    try:
        r = telcel_core.main('4111111111111111|01|30|123', 50, MX_PHONE)
        elapsed = round(time.time() - t0, 1)
        resp = str(r.get('message', r.get('status', r)))[:120]
        verdict = classify(resp)
        results['Telcel FONYOU'] = {'cmd': '/tcl', 'verdict': verdict, 'resp': resp, 'time': elapsed}
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        err = str(e)[:120]
        results['Telcel FONYOU'] = {'cmd': '/tcl', 'verdict': classify(err) if any(h in err.lower() for h in PROXY_HINTS) else '❌ ERROR', 'resp': err, 'time': elapsed}
except Exception as e:
    results['Telcel FONYOU'] = {'cmd': '/tcl', 'verdict': '❌ ERROR', 'resp': str(e)[:120], 'time': 0}

# ── NETFLIX (test core directly) ──────────────────────────────────────────
try:
    import os
    os.chdir('/opt/jillbot')
    from Commands.Gates.netflix import netflix_core
    t0 = time.time()
    try:
        r = netflix_core.processNetflixFlow('4111111111111111|01|30|123', proxy=None, capsolver_key='', retries=0)
        elapsed = round(time.time() - t0, 1)
        resp = str(r.get('response', r.get('apiResponse', r)))[:120]
        verdict = classify(resp)
        results['Netflix Plans'] = {'cmd': '/em', 'verdict': verdict, 'resp': resp, 'time': elapsed}
    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        err = str(e)[:120]
        results['Netflix Plans'] = {'cmd': '/em', 'verdict': classify(err) if any(h in err.lower() for h in PROXY_HINTS) else '❌ ERROR', 'resp': err, 'time': elapsed}
except Exception as e:
    results['Netflix Plans'] = {'cmd': '/em', 'verdict': '❌ ERROR', 'resp': str(e)[:120], 'time': 0}

# ── PRINT REPORT ──────────────────────────────────────────────────────────
print(f"\n{'─'*70}")
print(f"{'GATE':<26} {'CMD':<7} {'VERDICT':<14} {'TIME':>5}  RESPONSE")
print(f"{'─'*70}")
for name, d in results.items():
    print(f"{name:<26} {d['cmd']:<7} {d['verdict']:<14} {d['time']:>4}s  {d['resp']}")
print(f"{'─'*70}")

ok    = [n for n,d in results.items() if d['verdict'].startswith('✅')]
proxy = [n for n,d in results.items() if d['verdict'].startswith('🌐')]
err   = [n for n,d in results.items() if d['verdict'].startswith('❌')]
print(f"\n✅ Working:     {len(ok)}")
print(f"🌐 Need proxy:  {len(proxy)}  → {', '.join(proxy)}")
print(f"❌ Errors:      {len(err)}  → {', '.join(err)}")

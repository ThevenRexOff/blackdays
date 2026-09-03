import os, sys, json, time, pathlib
sys.path.insert(0, '/var/www/html/bot')
os.chdir('/var/www/html/bot')

env_path = pathlib.Path('Model/config.env')
for line in env_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from Commands.Gates import telcel_core

cc_str = '5247200074626167|07|27|079'
numero = '4871009914'
monto = 20

print(f"Testing telcel_core.main(cc={cc_str}, monto={monto}, numero={numero})")
start = time.time()
try:
    result = telcel_core.main(cc_str, monto, numero)
    elapsed = round(time.time() - start, 1)
    print(f"\n[{elapsed}s] Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    elapsed = round(time.time() - start, 1)
    print(f"\n[{elapsed}s] ERROR: {e}")
    import traceback
    traceback.print_exc()

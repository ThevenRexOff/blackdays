import os, sys, json, base64, pathlib, time, traceback
sys.path.insert(0, '/var/www/html/bot')
os.chdir('/var/www/html/bot')

env_path = pathlib.Path('Model/config.env')
for line in env_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from Commands.Gates.telcel import gateCmd

# Simulate .tcl 5247200074626167|07|27|079 4871009914
# Need bot object
from main import build_bot

upd = json.dumps({
    "update_id": 99999,
    "message": {
        "message_id": 99999,
        "from": {"id": 7132523590, "first_name": "Debug", "username": "dbg_test"},
        "chat": {"id": 7132523590, "type": "private"},
        "date": int(time.time()),
        "text": ".tcl 5247200074626167|07|27|079 4871009914"
    }
})
q = base64.b64encode(upd.encode()).decode()

from Model import BotX
original_post = BotX._post_with_retry
def debug_post(self, url, data=None, retries=3):
    if data and data.get('method') == 'sendMessage':
        text = data.get('text', '')
        print(f"[REPLY] text: {text[:500]}")
    result = original_post(self, url, data, retries)
    if result and not result.get('ok'):
        print(f"[API ERROR] {result.get('error_code')}: {result.get('description','')[:200]}")
    return result
BotX._post_with_retry = debug_post

try:
    bot = build_bot(q)
    bot.compile_bot()
    print("\n=== DONE ===")
except Exception as e:
    print(f"\nFATAL: {e}")
    traceback.print_exc()

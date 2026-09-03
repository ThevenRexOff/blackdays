"""Direct DB bootstrap — reads Model/config.env and runs setup without interactive prompts."""
import sys, os, pathlib, datetime

BASE = pathlib.Path(__file__).parent
sys.path.insert(0, str(BASE))

# Load config.env
env_file = BASE / 'Model' / 'config.env'
d = {}
for line in env_file.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('=')
        d[k.strip()] = v.strip()

print(f"[bootstrap] Loaded config: DB={d.get('DB_NAME')} HOST={d.get('DB_HOST')} SCHEMA={d.get('DB_SCHEMA','public')}")

import psycopg2
from rich.console import Console
c = Console()

schema = d.get('DB_SCHEMA', 'public') or 'public'

# Connect without schema to create it
try:
    base = psycopg2.connect(
        host=d['DB_HOST'], dbname=d['DB_NAME'], user=d['DB_USER'],
        password=d['DB_PASS'], connect_timeout=10)
    base.autocommit = True
    base.cursor().execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    base.close()
    c.print(f"[green]✓[/] Schema [bold]{schema}[/] ready")
except Exception as e:
    c.print(f"[red]✗ DB connection failed: {e}[/]")
    sys.exit(1)

conn = psycopg2.connect(
    host=d['DB_HOST'], dbname=d['DB_NAME'], user=d['DB_USER'],
    password=d['DB_PASS'], connect_timeout=10,
    options=f'-c search_path={schema}')
cur = conn.cursor()

# Tables
stmts = [
    "CREATE TABLE IF NOT EXISTS users (user_id VARCHAR(30) PRIMARY KEY, rango VARCHAR(20) DEFAULT 'free', c_name VARCHAR(100) DEFAULT 'free user', credits VARCHAR(20) DEFAULT '0', ban VARCHAR(10) DEFAULT 'false', warns VARCHAR(5) DEFAULT '0', d_reg VARCHAR(30), admin VARCHAR(10) DEFAULT 'false', su VARCHAR(10) DEFAULT 'false', l_reg VARCHAR(30), spam VARCHAR(20) DEFAULT '60', n_bil VARCHAR(100), nombre_usuario TEXT DEFAULT '', nombre TEXT DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS comandos (comando VARCHAR(50) PRIMARY KEY, tipo VARCHAR(30), status VARCHAR(10) DEFAULT 'on', d_reg VARCHAR(30), comentario VARCHAR(200) DEFAULT 'none', name VARCHAR(100), use VARCHAR(200) DEFAULT '', gate VARCHAR(60) DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS keys (key VARCHAR(60) PRIMARY KEY, days VARCHAR(10), credits VARCHAR(20), status VARCHAR(20) DEFAULT 'active')",
    "CREATE TABLE IF NOT EXISTS banned_bins (bin VARCHAR(8) PRIMARY KEY, reason VARCHAR(255) DEFAULT '', added_by VARCHAR(20) DEFAULT '', d_reg DATE DEFAULT CURRENT_DATE)",
    "CREATE TABLE IF NOT EXISTS card_uses (id SERIAL PRIMARY KEY, card_hash VARCHAR(64) NOT NULL, user_id VARCHAR(20) NOT NULL, used_at TIMESTAMP DEFAULT NOW())",
    "CREATE INDEX IF NOT EXISTS idx_card_hash_time ON card_uses (card_hash, used_at)",
    "CREATE INDEX IF NOT EXISTS idx_card_user_time ON card_uses (card_hash, user_id, used_at)",
    "CREATE TABLE IF NOT EXISTS usage_log (id SERIAL PRIMARY KEY, user_id VARCHAR(30), command VARCHAR(50), cmd_type VARCHAR(30), used_at TIMESTAMP DEFAULT NOW())",
    "CREATE TABLE IF NOT EXISTS cookies (user_id VARCHAR(30) PRIMARY KEY, cookie TEXT NOT NULL, updated_at TIMESTAMP DEFAULT NOW())",
    "CREATE TABLE IF NOT EXISTS plans (name VARCHAR(60) PRIMARY KEY, days INTEGER NOT NULL, credits VARCHAR(20) NOT NULL DEFAULT 'unlimited', price NUMERIC(10,2) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE, d_reg DATE DEFAULT CURRENT_DATE)",
    "CREATE TABLE IF NOT EXISTS sales (id SERIAL PRIMARY KEY, seller_id VARCHAR(30) NOT NULL, seller_name VARCHAR(100), plan VARCHAR(60) NOT NULL, price NUMERIC(10,2) NOT NULL, client VARCHAR(60), method VARCHAR(40), sold_at TIMESTAMP DEFAULT NOW())",
    "CREATE INDEX IF NOT EXISTS idx_sales_seller_time ON sales (seller_id, sold_at)",
    "CREATE INDEX IF NOT EXISTS idx_sales_time ON sales (sold_at)",
    "CREATE TABLE IF NOT EXISTS tickets (id SERIAL PRIMARY KEY, user_id VARCHAR(30) NOT NULL, username VARCHAR(100), problem VARCHAR(120), description TEXT, status VARCHAR(20) DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW(), closed_by VARCHAR(100))",
    "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status, created_at)",
    "CREATE TABLE IF NOT EXISTS events (id SERIAL PRIMARY KEY, actor_id VARCHAR(30), actor_name VARCHAR(100), action VARCHAR(60), target VARCHAR(60), detail TEXT, at TIMESTAMP DEFAULT NOW())",
    "CREATE INDEX IF NOT EXISTS idx_events_at ON events (at)",
]
for s in stmts:
    cur.execute(s)
c.print("[green]✓[/] Tables created/verified")

# Plans
for name, days, credits, price in [('Premium 31 dias', 31, 'unlimited', 50), ('Premium 92 dias', 92, 'unlimited', 120), ('Premium 184 dias', 184, 'unlimited', 200), ('Premium 1 ano', 365, 'unlimited', 350)]:
    cur.execute("INSERT INTO plans (name, days, credits, price) VALUES(%s,%s,%s,%s) ON CONFLICT (name) DO NOTHING", (name, days, credits, price))
c.print("[green]✓[/] Plans seeded")

# Commands (same as setup.py _seed_commands)
today = str(datetime.date.today())
tools = [
    ('bin','tool','on','BIN lookup','BIN','BIN',''),
    ('fake','tool','on','Fake address generator','Fake','MX|US|ES',''),
    ('nm','tool','on','Phone number info','Number','NUMERO',''),
    ('ip','tool','on','IP address lookup','IP','ADDRESS',''),
    ('gen','tool','on','CC generator by BIN','Gen','BIN x10',''),
    ('sk','tool','on','Stripe key checker','Stripe Key','sk_live_...',''),
    ('site','tool','on','Site status checker','Site','URL',''),
    ('tmail','tool','on','Temporary email','TempMail','',''),
]
auths = [
    ('mj','auths','on','Stripe auth gate','Mojito','cc|mm|yy|cvv','Stripe Auth'),
    ('mg','auths','on','Braintree auth gate','Margarita','cc|mm|yy|cvv','Braintree Auth'),
    ('pc','auths','on','Adyen auth gate','Pina Colada','cc|mm|yy|cvv','Adyen Auth'),
    ('dq','auths','on','Recurly auth gate','Daiquiri','cc|mm|yy|cvv','Recurly Auth'),
    ('mt','auths','on','Chase auth gate','Martini','cc|mm|yy|cvv','Chase Auth'),
    ('cs','auths','on','Bluepay auth gate','Cosmopolitan','cc|mm|yy|cvv','Bluepay Auth'),
    ('ng','auths','on','Moneris auth gate','Negroni','cc|mm|yy|cvv','Moneris Auth'),
    ('of','auths','on','Zuora auth gate','Old Fashioned','cc|mm|yy|cvv','Zuora Auth'),
]
charged = [
    ('mh','charged','on','Stripe charged $2 gate','Manhattan','cc|mm|yy|cvv','Stripe Charged'),
    ('ws','charged','on','Braintree charged $2 gate','Whiskey Sour','cc|mm|yy|cvv','Braintree Charged'),
    ('lit','charged','on','Adyen charged $5 gate','Long Island','cc|mm|yy|cvv','Adyen Charged'),
    ('bm','charged','on','Recurly charged $10 gate','Bloody Mary','cc|mm|yy|cvv','Recurly Charged'),
    ('sob','charged','on','Chase charged $10 gate','Sex on Beach','cc|mm|yy|cvv','Chase Charged'),
    ('ts','charged','on','Bluepay charged $10 gate','Tequila Sunrise','cc|mm|yy|cvv','Bluepay Charged'),
    ('mtai','charged','on','Cybersource charged $10','Mai Tai','cc|mm|yy|cvv','Cybersource Charged'),
    ('cp','charged','on','Chase charged $10 gate','Caipirinha','cc|mm|yy|cvv','Chase Charged'),
    ('mm','charged','on','Authorize.net charged $10','Moscow Mule','cc|mm|yy|cvv','Authorize.net Charged'),
    ('cl','charged','on','NMI charged $5 gate','Cuba Libre','cc|mm|yy|cvv','NMI Charged'),
    ('gt','charged','on','Square charged $5 gate','Gin Tonic','cc|mm|yy|cvv','Square Charged'),
    ('tc','charged','on','Checkout.com charged $5','Tom Collins','cc|mm|yy|cvv','Checkout.com Charged'),
]
specials = [
    ('mass','specials','on','Corre cualquier gate en masa. Primera linea = gate, resto = tarjetas. Cobra 2 cred por live.','Mass Checker','GATE\ncc1|mm|yy|cvv\ncc2|mm|yy|cvv',''),
    ('amz','specials','on','Amazon billing (Sxgitario mamazon flow)','Amazon','cc|mm|yy|cvv','Amazon'),
    ('amzg','specials','on','Amazon billing alias','Amazon','cc|mm|yy|cvv','Amazon'),
    ('tcl','specials','on','Telcel MX recharge gate','Telcel Gate','cc|mm|yy|cvv|monto|numero','Telcel MX'),
    ('bl','specials','on','Disney+ gate','Blue Lagoon','cc|mm|yy|cvv','Disney+'),
    ('zb','specials','on','Telcel recargas gate','Zombie','cc|mm|yy|cvv','Telcel Recargas'),
    ('hr','specials','on','Movistar recargas gate','Hurricane','cc|mm|yy|cvv','Movistar Recargas'),
    ('ps','specials','on','BAIT recargas gate','Pisco Sour','cc|mm|yy|cvv','BAIT Recargas'),
    ('pl','specials','on','Amazon Global gate','Paloma','cc|mm|yy|cvv','Amazon Global'),
    ('em','specials','on','Netflix gate','Espresso Martini','cc|mm|yy|cvv','Netflix'),
    ('dns','specials','on','Mercado Libre gate','Dark n Stormy','cc|mm|yy|cvv','Mercado Libre'),
]
ccn = [
    ('as','ccn','on','Stripe CCN charged $2','Aperol Spritz','cc|mm|yy|cvv','Stripe Charged'),
    ('bln','ccn','on','Braintree CCN charged $5','Bellini','cc|mm|yy|cvv','Braintree Charged'),
    ('mmo','ccn','on','Adyen CCN charged $4','Mimosa','cc|mm|yy|cvv','Adyen Charged'),
    ('f75','ccn','on','Payeezy CCN charged $4','French 75','cc|mm|yy|cvv','Payeezy Charged'),
    ('ss','ccn','on','Convergepay CCN charged $5','Singapore Sling','cc|mm|yy|cvv','Convergepay Charged'),
    ('sc','ccn','on','Zuora CCN charged $7','Sidecar','cc|mm|yy|cvv','Zuora Charged'),
    ('wr','ccn','on','Payeezy CCN charged $15','White Russian','cc|mm|yy|cvv','Payeezy Charged'),
    ('br','ccn','on','Paypal CCN charged $1','Black Russian','cc|mm|yy|cvv','Paypal Charged'),
    ('ic','ccn','on','Cybersource CCN charged $8','Irish Coffee','cc|mm|yy|cvv','Cybersource Charged'),
]
avs = [
    ('cc','avs','on','Cybersource AVS gate','Clover Club','cc|mm|yy|cvv','Cybersource AVS'),
    ('bd','avs','on','Braintree AVS gate','Boulevardier','cc|mm|yy|cvv','Braintree AVS'),
    ('av','avs','on','Payeezy AVS gate','Aviation','cc|mm|yy|cvv','Payeezy AVS'),
    ('sz','avs','on','Authorize.net AVS gate','Sazerac','cc|mm|yy|cvv','Authorize.net AVS'),
]
rows = tools + auths + charged + specials + ccn + avs
for cmd, tipo, status, comentario, name, use, gate in rows:
    cur.execute(
        "INSERT INTO comandos (comando, tipo, status, d_reg, comentario, name, use, gate) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) "
        "ON CONFLICT (comando) DO UPDATE SET "
        "tipo=EXCLUDED.tipo, comentario=EXCLUDED.comentario, name=EXCLUDED.name, "
        "use=EXCLUDED.use, gate=EXCLUDED.gate",
        (cmd, tipo, status, today, comentario, name, use, gate)
    )
c.print(f"[green]✓[/] {len(rows)} commands uploaded")

# Both owners
now = datetime.datetime.now()
for oid in ['7132523590', '8683891436']:
    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (oid,))
    if cur.fetchone():
        cur.execute("UPDATE users SET rango='owner', c_name='owner', credits='unlimited', ban='false', admin='true', su='true' WHERE user_id=%s", (oid,))
    else:
        cur.execute(
            "INSERT INTO users (user_id, rango, c_name, credits, ban, warns, d_reg, admin, su, l_reg, spam, n_bil, nombre_usuario, nombre) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (oid, 'owner', 'owner', 'unlimited', 'false', '0', str(now.date()), 'true', 'true', str(now), '60', str(now), '', ''))
    c.print(f"[green]✓[/] Owner {oid} seeded")

conn.commit()
conn.close()
c.print("[bold green]✓ Bootstrap complete! DB ready.[/]")

# Register webhook
import requests as req
token = d.get('BOT_TOKEN', '')
webhook_url = d.get('WEBHOOK_URL', '')
if token and webhook_url:
    r = req.post(f"https://api.telegram.org/bot{token}/setWebhook",
                 json={'url': webhook_url, 'allowed_updates': ['message', 'edited_message', 'callback_query']},
                 timeout=15)
    j = r.json()
    if j.get('ok'):
        c.print(f"[green]✓[/] Webhook set → {webhook_url}")
    else:
        c.print(f"[red]✗ Webhook failed: {j}[/]")
else:
    c.print("[yellow]⚠ Skipping webhook (TOKEN or WEBHOOK_URL not set)[/]")

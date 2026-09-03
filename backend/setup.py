#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
# JILL_BOT — interactive setup (rich terminal). Run once: python3 setup.py
import os, sys

# Ensure rich is available (rest of deps come from requirements.txt)
try:
    import rich  # noqa: F401
except ImportError:
    os.system(f"{sys.executable} -m pip install rich requests psycopg2-binary --quiet")

import datetime, pathlib, requests, psycopg2
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import box

c    = Console()
BASE = pathlib.Path(__file__).resolve().parent
ENV  = BASE / 'Model' / 'config.env'

BANNER = "[bold magenta]🍸  J I L L   B O T[/]\n[dim]interactive setup[/]"


def _mask(s, keep=4):
    s = str(s or '')
    return (s[:keep] + '•' * max(len(s) - keep, 0)) if s else '—'


class Setup:
    def __init__(self):
        self.d = {}

    # ── 1. collect ────────────────────────────────────────────────────────────
    def collect(self):
        c.print(Panel(BANNER, box=box.DOUBLE, border_style="magenta", expand=False))
        c.print("[bold cyan]› Bot & Owner[/]")
        self.d['BOT_TOKEN'] = Prompt.ask("  [green]Bot token[/]").strip()
        self.bot_name = self._check_token(self.d['BOT_TOKEN'])
        self.d['OWNER_ID'] = Prompt.ask("  [green]Owner Telegram ID[/]").strip()

        self._db_guide()
        c.print("\n[bold cyan]› Database (PostgreSQL)[/] [dim](Enter = default in [brackets])[/]")
        self.d['DB_HOST']   = Prompt.ask("  [green]DB host[/]", default="localhost").strip()
        self.d['DB_NAME']   = Prompt.ask("  [green]DB name[/]", default="jillbot").strip()
        self.d['DB_USER']   = Prompt.ask("  [green]DB user[/]", default="postgres").strip()
        self.d['DB_PASS']   = Prompt.ask("  [green]DB password[/] [dim](Enter for none)[/]", password=True, default="").strip()
        self.d['DB_SCHEMA'] = Prompt.ask("  [green]DB schema[/] [dim](public, or a name to isolate)[/]", default="public").strip() or "public"

        c.print("\n[bold cyan]› Run mode[/]")
        self.d['MODE'] = Prompt.ask("  [green]Mode[/]", choices=["webhook", "polling"], default="webhook")
        if self.d['MODE'] == 'webhook':
            self.d['WEBHOOK_URL']  = Prompt.ask("  [green]Webhook URL[/] [dim](https://.../index.php)[/]").strip()
            self.d['POLL_WORKERS'] = '8'
            self.d['ASYNC_MODE']   = 'true' if Confirm.ask("  [green]Async (background launch)?[/]", default=True) else 'false'
        else:
            self.d['WEBHOOK_URL']  = ''
            self.d['POLL_WORKERS'] = str(IntPrompt.ask("  [green]Polling workers[/]", default=8))
            self.d['ASYNC_MODE']   = 'true'

        c.print("\n[bold cyan]› Channels[/] [dim](Enter to skip)[/]")
        self.d['ERROR_CHANNEL']   = Prompt.ask("  [green]Error/logs channel id[/]", default="").strip()
        self.d['SUPPORT_CHANNEL'] = Prompt.ask("  [green]Tickets/support channel id[/]", default="").strip()
        self.d['REFS_CHANNEL']    = Prompt.ask("  [green]References channel id[/]", default="").strip()

        c.print("\n[bold cyan]› Public links[/] [dim](Enter to skip)[/]")
        self.d['CHAT_URL'] = Prompt.ask("  [green]General chat URL[/]", default="").strip()
        self.d['REFS_URL'] = Prompt.ask("  [green]References channel URL[/]", default="").strip()

    def _db_guide(self):
        c.print(Panel(
            "[bold]¿No tienes una base de datos PostgreSQL? Elige una opción:[/]\n\n"
            "[bold magenta]A) LOCAL (localhost)[/] — corre en la misma máquina\n"
            "  [cyan]macOS:[/]   brew install postgresql@16 && brew services start postgresql@16\n"
            "  [cyan]Ubuntu:[/]  sudo apt install postgresql && sudo service postgresql start\n"
            "  [cyan]Crear DB + usuario:[/]\n"
            "    sudo -u postgres psql\n"
            "    [dim]CREATE DATABASE jillbot;[/]\n"
            "    [dim]CREATE USER postgres WITH PASSWORD 'tu_clave';[/]\n"
            "    [dim]GRANT ALL PRIVILEGES ON DATABASE jillbot TO postgres;[/]\n"
            "  [cyan]Luego usa:[/] host=[green]localhost[/]  name=[green]jillbot[/]  user=[green]postgres[/]\n\n"
            "[bold magenta]B) HOSTEADO (gratis)[/] — en la nube, no requiere instalar nada\n"
            "  • [cyan]Neon[/]        neon.tech        (serverless, generoso)\n"
            "  • [cyan]Supabase[/]    supabase.com     (500MB gratis)\n"
            "  • [cyan]Railway[/]     railway.app\n"
            "  • [cyan]alwaysdata[/]  alwaysdata.com   (100MB gratis)\n"
            "  [dim]Crea el proyecto/DB y copia host, name, user y password que te den.[/]\n\n"
            "[bold]SCHEMA:[/] deja [green]public[/] para un deploy normal. Usa otro nombre\n"
            "(ej. [green]jill[/]) solo si compartes la misma DB con otro bot y quieres aislar las tablas.",
            title="🐘 Cómo montar la base de datos", border_style="cyan", box=box.ROUNDED, expand=False))

    def _check_token(self, token):
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10).json()
            if r.get('ok'):
                name = r['result'].get('first_name', '?')
                c.print(f"  [green]✓[/] Bot: [magenta]{name}[/] @{r['result'].get('username','')}")
                return name
            c.print(f"  [red]✗ Invalid token: {r.get('description','?')}[/]")
        except Exception as e:
            c.print(f"  [red]✗ Could not verify token: {e}[/]")
        if not Confirm.ask("  [yellow]Continue anyway?[/]", default=False):
            sys.exit(1)
        return '?'

    # ── 2. summary + confirm ────────────────────────────────────────────────────
    def summary(self):
        t = Table(box=box.ROUNDED, border_style="magenta", show_header=False)
        t.add_column(style="cyan"); t.add_column(style="white")
        t.add_row("Owner",   self.d['OWNER_ID'])
        t.add_row("Token",   _mask(self.d['BOT_TOKEN'], 8) + (f"  ({self.bot_name})" if self.bot_name else ''))
        t.add_row("DB host", _mask(self.d['DB_HOST']))
        t.add_row("DB name", self.d['DB_NAME'])
        t.add_row("DB user", _mask(self.d['DB_USER']))
        t.add_row("DB pass", '•' * len(self.d['DB_PASS']) if self.d['DB_PASS'] else '—')
        t.add_row("DB schema", self.d.get('DB_SCHEMA', 'public'))
        t.add_row("Mode",    self.d['MODE'])
        t.add_row("Webhook", self.d['WEBHOOK_URL'] or '—')
        t.add_row("Workers", self.d['POLL_WORKERS'])
        t.add_row("Async",   self.d['ASYNC_MODE'])
        t.add_row("Channels", f"err={self.d['ERROR_CHANNEL'] or '—'}  sup={self.d['SUPPORT_CHANNEL'] or '—'}  refs={self.d['REFS_CHANNEL'] or '—'}")
        t.add_row("Links",   f"chat={self.d['CHAT_URL'] or '—'}  refs={self.d['REFS_URL'] or '—'}")
        c.print("\n", t)
        if not Confirm.ask("[bold]Proceed with this configuration?[/]", default=True):
            c.print("[yellow]Aborted.[/]"); sys.exit(0)

    # ── 3. database ───────────────────────────────────────────────────────────
    def _conn(self):
        schema = self.d.get('DB_SCHEMA', 'public') or 'public'
        return psycopg2.connect(
            host=self.d['DB_HOST'], dbname=self.d['DB_NAME'], user=self.d['DB_USER'],
            password=self.d['DB_PASS'], connect_timeout=8,
            options=f'-c search_path={schema}',
        )

    def build_db(self):
        schema = self.d.get('DB_SCHEMA', 'public') or 'public'
        try:
            # First connect without a schema search_path so we can create it if missing.
            base = psycopg2.connect(host=self.d['DB_HOST'], dbname=self.d['DB_NAME'],
                                    user=self.d['DB_USER'], password=self.d['DB_PASS'], connect_timeout=8)
            base.autocommit = True
            base.cursor().execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
            base.close()
            conn = self._conn(); cur = conn.cursor()
            c.print(f"[green]✓[/] Database connected [dim](schema: {schema})[/]")
        except Exception as e:
            c.print(f"[red]✗ DB connection failed: {e}[/]")
            c.print("[yellow]Revisa la guía de arriba: host/name/user/password y que el servidor esté encendido.[/]")
            sys.exit(1)
        self._create_tables(cur)
        self._seed_plans(cur)
        self._seed_commands(cur)
        self._seed_owner(cur)
        conn.commit(); conn.close()
        c.print("[green]✓[/] Tables, plans, commands & owner ready")

    def _create_tables(self, cur):
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

    def _seed_plans(self, cur):
        for name, days, credits, price in [('Premium 31 dias', 31, 'unlimited', 50), ('Premium 92 dias', 92, 'unlimited', 120), ('Premium 184 dias', 184, 'unlimited', 200), ('Premium 1 ano', 365, 'unlimited', 350)]:
            cur.execute("INSERT INTO plans (name, days, credits, price) VALUES(%s,%s,%s,%s) ON CONFLICT (name) DO NOTHING", (name, days, credits, price))

    def _seed_commands(self, cur):
        # (comando, tipo, status, comentario, name, use, gate)
        tools = [
            ('bin',   'tool', 'on', 'BIN lookup',            'BIN',        'BIN',          ''),
            ('fake',  'tool', 'on', 'Fake address generator', 'Fake',       'MX|US|ES',     ''),
            ('nm',    'tool', 'on', 'Phone number info',       'Number',     'NUMERO',       ''),
            ('ip',    'tool', 'on', 'IP address lookup',       'IP',         'ADDRESS',      ''),
            ('gen',   'tool', 'on', 'CC generator by BIN',     'Gen',        'BIN x10',      ''),
            ('sk',    'tool', 'on', 'Stripe key checker',      'Stripe Key', 'sk_live_...',  ''),
            ('site',  'tool', 'on', 'Site status checker',     'Site',       'URL',          ''),
            ('tmail', 'tool', 'on', 'Temporary email',         'TempMail',   '',             ''),
        ]
        auths = [
            ('mj',  'auths', 'on', 'Stripe auth gate',    'Mojito',        'cc|mm|yy|cvv', 'Stripe Auth'),
            ('mg',  'auths', 'on', 'Braintree auth gate', 'Margarita',     'cc|mm|yy|cvv', 'Braintree Auth'),
            ('pc',  'auths', 'on', 'Adyen auth gate',     'Pina Colada',   'cc|mm|yy|cvv', 'Adyen Auth'),
            ('dq',  'auths', 'on', 'Recurly auth gate',   'Daiquiri',      'cc|mm|yy|cvv', 'Recurly Auth'),
            ('mt',  'auths', 'on', 'Chase auth gate',     'Martini',       'cc|mm|yy|cvv', 'Chase Auth'),
            ('cs',  'auths', 'on', 'Bluepay auth gate',   'Cosmopolitan',  'cc|mm|yy|cvv', 'Bluepay Auth'),
            ('ng',  'auths', 'on', 'Moneris auth gate',   'Negroni',       'cc|mm|yy|cvv', 'Moneris Auth'),
            ('of',  'auths', 'on', 'Zuora auth gate',     'Old Fashioned', 'cc|mm|yy|cvv', 'Zuora Auth'),
        ]
        charged = [
            ('mh',   'charged', 'on', 'Stripe charged $2 gate',     'Manhattan',      'cc|mm|yy|cvv', 'Stripe Charged'),
            ('ws',   'charged', 'on', 'Braintree charged $2 gate',  'Whiskey Sour',   'cc|mm|yy|cvv', 'Braintree Charged'),
            ('lit',  'charged', 'on', 'Adyen charged $5 gate',      'Long Island',    'cc|mm|yy|cvv', 'Adyen Charged'),
            ('bm',   'charged', 'on', 'Recurly charged $10 gate',   'Bloody Mary',    'cc|mm|yy|cvv', 'Recurly Charged'),
            ('sob',  'charged', 'on', 'Chase charged $10 gate',     'Sex on Beach',   'cc|mm|yy|cvv', 'Chase Charged'),
            ('ts',   'charged', 'on', 'Bluepay charged $10 gate',   'Tequila Sunrise','cc|mm|yy|cvv', 'Bluepay Charged'),
            ('mtai', 'charged', 'on', 'Cybersource charged $10',    'Mai Tai',        'cc|mm|yy|cvv', 'Cybersource Charged'),
            ('cp',   'charged', 'on', 'Chase charged $10 gate',     'Caipirinha',     'cc|mm|yy|cvv', 'Chase Charged'),
            ('mm',   'charged', 'on', 'Authorize.net charged $10',  'Moscow Mule',    'cc|mm|yy|cvv', 'Authorize.net Charged'),
            ('cl',   'charged', 'on', 'NMI charged $5 gate',        'Cuba Libre',     'cc|mm|yy|cvv', 'NMI Charged'),
            ('gt',   'charged', 'on', 'Square charged $5 gate',     'Gin Tonic',      'cc|mm|yy|cvv', 'Square Charged'),
            ('tc',   'charged', 'on', 'Checkout.com charged $5',    'Tom Collins',    'cc|mm|yy|cvv', 'Checkout.com Charged'),
        ]
        specials = [
            ('mass', 'specials', 'on', 'Corre cualquier gate en masa. Primera linea = gate, resto = tarjetas. Cobra 2 cred por live.', 'Mass Checker', 'GATE\\ncc1|mm|yy|cvv\\ncc2|mm|yy|cvv', ''),
            ('amz',  'specials', 'on', 'Amazon billing (Sxgitario mamazon flow)', 'Amazon', 'cc|mm|yy|cvv', 'Amazon'),
            ('amzg', 'specials', 'on', 'Amazon billing alias',                    'Amazon', 'cc|mm|yy|cvv', 'Amazon'),
            ('tcl',  'specials', 'on', 'Telcel MX recharge gate',        'Telcel Gate',    'cc|mm|yy|cvv|monto|numero','Telcel MX'),
            ('bl',   'specials', 'on', 'Disney+ gate',                   'Blue Lagoon',    'cc|mm|yy|cvv',  'Disney+'),
            ('zb',   'specials', 'on', 'Telcel recargas gate',           'Zombie',         'cc|mm|yy|cvv',  'Telcel Recargas'),
            ('hr',   'specials', 'on', 'Movistar recargas gate',         'Hurricane',      'cc|mm|yy|cvv',  'Movistar Recargas'),
            ('ps',   'specials', 'on', 'BAIT recargas gate',             'Pisco Sour',     'cc|mm|yy|cvv',  'BAIT Recargas'),
            ('pl',   'specials', 'on', 'Amazon Global gate',             'Paloma',         'cc|mm|yy|cvv',  'Amazon Global'),
            ('em',   'specials', 'on', 'Netflix gate',                   'Espresso Martini','cc|mm|yy|cvv', 'Netflix'),
            ('dns',  'specials', 'on', 'Mercado Libre gate',             'Dark n Stormy',  'cc|mm|yy|cvv',  'Mercado Libre'),
        ]
        ccn = [
            ('as',   'ccn', 'on', 'Stripe CCN charged $2',      'Aperol Spritz',  'cc|mm|yy|cvv', 'Stripe Charged'),
            ('bln',  'ccn', 'on', 'Braintree CCN charged $5',   'Bellini',        'cc|mm|yy|cvv', 'Braintree Charged'),
            ('mmo',  'ccn', 'on', 'Adyen CCN charged $4',       'Mimosa',         'cc|mm|yy|cvv', 'Adyen Charged'),
            ('f75',  'ccn', 'on', 'Payeezy CCN charged $4',     'French 75',      'cc|mm|yy|cvv', 'Payeezy Charged'),
            ('ss',   'ccn', 'on', 'Convergepay CCN charged $5', 'Singapore Sling','cc|mm|yy|cvv', 'Convergepay Charged'),
            ('sc',   'ccn', 'on', 'Zuora CCN charged $7',       'Sidecar',        'cc|mm|yy|cvv', 'Zuora Charged'),
            ('wr',   'ccn', 'on', 'Payeezy CCN charged $15',    'White Russian',  'cc|mm|yy|cvv', 'Payeezy Charged'),
            ('br',   'ccn', 'on', 'Paypal CCN charged $1',      'Black Russian',  'cc|mm|yy|cvv', 'Paypal Charged'),
            ('ic',   'ccn', 'on', 'Cybersource CCN charged $8', 'Irish Coffee',   'cc|mm|yy|cvv', 'Cybersource Charged'),
        ]
        avs = [
            ('cc',   'avs', 'on', 'Cybersource AVS gate',   'Clover Club',  'cc|mm|yy|cvv', 'Cybersource AVS'),
            ('bd',   'avs', 'on', 'Braintree AVS gate',     'Boulevardier', 'cc|mm|yy|cvv', 'Braintree AVS'),
            ('av',   'avs', 'on', 'Payeezy AVS gate',       'Aviation',     'cc|mm|yy|cvv', 'Payeezy AVS'),
            ('sz',   'avs', 'on', 'Authorize.net AVS gate', 'Sazerac',      'cc|mm|yy|cvv', 'Authorize.net AVS'),
        ]
        today = str(datetime.date.today())
        rows  = tools + auths + charged + specials + ccn + avs
        for cmd, tipo, status, comentario, name, use, gate in rows:
            # UPSERT: upload everything as it is now. On re-run it UPDATES tipo/name/use/gate/
            # comentario so the DB always matches this file (status/mode kept if already set).
            cur.execute(
                "INSERT INTO comandos (comando, tipo, status, d_reg, comentario, name, use, gate) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (comando) DO UPDATE SET "
                "tipo=EXCLUDED.tipo, comentario=EXCLUDED.comentario, name=EXCLUDED.name, "
                "use=EXCLUDED.use, gate=EXCLUDED.gate",
                (cmd, tipo, status, today, comentario, name, use, gate)
            )
        c.print(f"[green]✓[/] {len(rows)} commands uploaded/updated in DB")

    def _seed_owner(self, cur):
        oid = self.d['OWNER_ID']
        if not oid:
            return
        now = datetime.datetime.now()
        cur.execute("SELECT user_id FROM users WHERE user_id = %s", (oid,))
        if cur.fetchone():
            cur.execute("UPDATE users SET rango='owner', c_name='owner', credits='unlimited', ban='false', admin='true', su='true' WHERE user_id=%s", (oid,))
        else:
            cur.execute("INSERT INTO users (user_id, rango, c_name, credits, ban, warns, d_reg, admin, su, l_reg, spam, n_bil, nombre_usuario, nombre) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (oid, 'owner', 'owner', 'unlimited', 'false', '0', str(now).split(' ')[0], 'true', 'true', str(now), '60', str(now), '', ''))

    # ── 4. config + webhook ───────────────────────────────────────────────────
    def write_config(self):
        keys = ['BOT_TOKEN', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASS', 'DB_SCHEMA', 'OWNER_ID', 'ERROR_CHANNEL',
                'MODE', 'WEBHOOK_URL', 'POLL_WORKERS', 'ASYNC_MODE',
                'SUPPORT_CHANNEL', 'REFS_CHANNEL', 'CHAT_URL', 'REFS_URL']
        ENV.parent.mkdir(parents=True, exist_ok=True)
        with open(ENV, 'w', encoding='utf-8') as f:
            f.write("# JILL_BOT config — generated by setup.py\n")
            for k in keys:
                f.write(f"{k}={self.d.get(k, '')}\n")
        c.print(f"[green]✓[/] Config written -> [dim]{ENV}[/]")

    def apply_mode(self):
        token = self.d['BOT_TOKEN']
        try:
            if self.d['MODE'] == 'webhook' and self.d['WEBHOOK_URL']:
                r = requests.get(f"https://api.telegram.org/bot{token}/setWebhook", params={'url': self.d['WEBHOOK_URL'], 'drop_pending_updates': 'True'}, timeout=15).json()
                c.print(f"[green]✓[/] Webhook set" if r.get('ok') else f"[red]✗ Webhook: {r.get('description','?')}[/]")
            elif self.d['MODE'] == 'polling':
                requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook", params={'drop_pending_updates': 'false'}, timeout=15)
                c.print("[green]✓[/] Webhook cleared (polling mode)")
        except Exception as e:
            c.print(f"[yellow]! Could not apply mode: {e}[/]")

    def finish(self):
        run = "python3 run.py" if self.d['MODE'] == 'webhook' else "python3 run.py   [dim](or python3 poll.py)[/]"
        c.print(Panel(
            f"[green]JILL is ready![/]\n\n"
            f"[cyan]Mode:[/] {self.d['MODE']}\n"
            f"[cyan]Start:[/] {run}\n"
            f"[dim]Cron (optional): python3 tasks.py expiry | cleanup[/]",
            title="✅ Setup complete", border_style="green", box=box.ROUNDED, expand=False))

    def run(self):
        self.collect()
        self.summary()
        self.build_db()
        self.write_config()
        self.apply_mode()
        self.finish()


if __name__ == '__main__':
    try:
        Setup().run()
    except KeyboardInterrupt:
        c.print("\n[yellow]Cancelled.[/]")

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

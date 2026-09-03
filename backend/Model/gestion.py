# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import psycopg2, datetime, luhn, requests, random, hashlib, threading, time

# Per-thread persistent DB connection. Opening a connection to the remote (alwaysdata)
# Postgres costs ~1.7s; polling reuses a fixed pool of worker threads, so we keep one live
# connection per thread and reuse it across updates instead of reconnecting every time.
_tls         = threading.local()
_PING_AFTER  = 20   # seconds idle before we re-validate a pooled connection (pool_pre_ping)
_MAX_CONN_AGE = 150  # force-reconnect after this many seconds regardless — NAT on Contabo→alwaysdata
                     # silently kills idle TCP after ~10 min; reconnecting at 2.5 min avoids dead-socket
                     # hangs that previously caused 600 s "Tiempo De Compilacion" spikes.

def _open_conn(host, name, user, pw, schema):
    return psycopg2.connect(
        host=host, dbname=name, user=user, password=pw, connect_timeout=5,
        keepalives=1, keepalives_idle=10, keepalives_interval=3, keepalives_count=3,
        tcp_user_timeout=8000,
        options=f'-c statement_timeout=8000 -c search_path={schema}',
    )


class gestion:

    rangos      = ['admin', 'owner', 'mod']
    prem        = ['admin', 'owner', 'mod', 'premium']
    _rangos     = ['admin', 'owner']
    sellers     = ['owner', 'admin', 'seller']   # who can register plan sales
    _types      = ['auths', 'charged', 'specials', 'ccn', 'avs', 'tool']
    modes       = {'on': '✅', 'of': '❌', 'ma': '⚠️'}
    MAX_WARNS       = 3
    CARD_COOLDOWN   = 300     # same card can't be re-checked within this window (no warn, just wait)
    ABUSE_THRESHOLD = 3       # allowed checks of the same card by the same user before it counts as abuse
    ABUSE_WINDOW    = 3600    # time window for abuse counting
    _CODER          = "Coder: t.me/Vxsilisk - Shop: t.me/Sxgitario"   # do not remove — code attribution


    def __init__(self, host_db, name_db, user_db, pass_db, schema_db='public') -> None:
        self._cargs      = (host_db, name_db, user_db, pass_db, schema_db)
        self.connect     = self._acquire()
        self.cursor      = self.connect.cursor()
        self._view_cache = {}
        self._session    = requests.Session()


    def _acquire(self):
        """Return a live connection for this thread, reusing the thread-local one if still valid.

        Strategy:
          • < _PING_AFTER seconds idle  → reuse as-is (definitely alive)
          • >= _MAX_CONN_AGE seconds old → force-close and open a fresh connection; skip the ping
            entirely because NAT on the Contabo→alwaysdata path silently kills idle TCP sockets
            after ~10 min and SELECT 1 on a dead socket hangs for hundreds of seconds.
          • between the two thresholds   → ping with SELECT 1 (short round-trip, socket still young)
        """
        key  = (self._cargs[0], self._cargs[1], self._cargs[2], self._cargs[4])
        conn = getattr(_tls, 'conn', None)
        now  = time.time()
        if conn is not None and getattr(_tls, 'key', None) == key and conn.closed == 0:
            idle = now - getattr(_tls, 'last', 0)
            age  = now - getattr(_tls, 'created', 0)
            if age >= _MAX_CONN_AGE:
                # Too old — NAT may have already killed the socket. Skip the hanging ping.
                try: conn.close()
                except Exception: pass
            elif idle < _PING_AFTER:
                _tls.last = now
                return conn
            else:
                try:                               # moderate idle → quick ping while socket is young
                    cur = conn.cursor(); cur.execute('SELECT 1'); cur.fetchone(); cur.close()
                    _tls.last = now
                    return conn
                except Exception:
                    try: conn.close()
                    except Exception: pass
        elif conn is not None:
            try: conn.close()
            except Exception: pass
        conn = _open_conn(*self._cargs)
        _tls.conn, _tls.key, _tls.last, _tls.created = conn, key, now, now
        return conn


    def _reconnect(self):
        """Drop the (dead) thread-local connection and open a new one."""
        try:
            if self.connect and self.connect.closed == 0: self.connect.close()
        except Exception: pass
        _tls.conn = None
        self.connect = self._acquire()
        self.cursor  = self.connect.cursor()


    def _run(self, query:str, params:tuple = (), fetch:bool = False, commit:bool = False, _retry:bool = True) -> dict:
        try:
            # Pass params only when present — otherwise psycopg2 treats a literal % (e.g. LIKE '-%') as a placeholder
            if params: self.cursor.execute(query, params)
            else:      self.cursor.execute(query)
            data = self.cursor.fetchall() if fetch else None
            if commit: self.connect.commit()
            return {'status': True, 'data': data}
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as error:
            # Pooled connection went stale (idle timeout / server drop) -> reconnect once and retry.
            if _retry:
                try:
                    self._reconnect()
                    return self._run(query, params, fetch, commit, _retry=False)
                except Exception as e2:
                    return {'status': False, 'data': e2}
            return {'status': False, 'data': error}
        except Exception as error:
            try: self.connect.rollback()
            except Exception: pass
            return {'status': False, 'data': error}


    def commit(self, query:str, params:tuple = ()) -> dict:
        data = self._run(query=query, params=params, commit=True)
        return {'status': True} if data['status'] else {'status': False, 'reason': data['data']}


    def no_commit(self, query:str, params:tuple = ()) -> dict:
        data = self._run(query=query, params=params, fetch=True)
        return {'status': True, 'data': data['data']} if data['status'] else {'status': False, 'data': data['data']}


    def view(self, user_id:str) -> dict:
        uid = str(user_id).replace(' ', '')
        if uid in self._view_cache:
            return self._view_cache[uid]
        now = datetime.datetime.now()
        try:
            data_ = self.no_commit("SELECT * FROM users WHERE user_id = %s", (uid,))
            if not data_['status']: return {'status': False}
            B = data_['data']
            if len(B) > 0:
                data = {'status':True, 'user_id':B[0][0], 'rango':B[0][1], 'c_name':B[0][2], 'credits':B[0][3], 'ban':B[0][4], 'warns':B[0][5], 'd_reg':str(B[0][6]).split(' ')[0], 'admin':B[0][7], 'su':B[0][8], 'l_reg':B[0][9], 'spam':B[0][10], 'n_bil':B[0][11], 'nombre_usuario': B[0][12] if len(B[0]) > 12 else '', 'nombre': B[0][13] if len(B[0]) > 13 else ''}
                if data['rango'].lower() in self.rangos or data['rango'].lower() in ('free', 'seller'):
                    self._view_cache[uid] = data
                    return data
                else:
                    a = self._set(time=data['n_bil'])
                    if a and now <= a:
                        diff  = a - now
                        days  = diff.days
                        hours = diff.seconds // 3600
                        mins  = (diff.seconds % 3600) // 60
                        if days > 0:    display = f"{days}d {hours}h"
                        elif hours > 0: display = f"{hours}h {mins}m"
                        else:           display = f"{mins}m" if mins > 0 else 'Today'
                        result = {**data, 'days': display}
                        self._view_cache[uid] = result
                        return result
                    else:
                        self.commit("UPDATE users SET rango = %s, c_name = %s, credits = %s, spam = %s WHERE user_id = %s", ('free', 'free user', '0', '60', uid))
                        self._view_cache.pop(uid, None)
                        return self.view(uid)
            else:
                self.commit(
                    "INSERT INTO users (user_id, rango, c_name, credits, ban, warns, d_reg, admin, su, l_reg, spam, n_bil, nombre_usuario, nombre) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (uid, 'free', 'free user', '0', 'false', '0', str(now).split(' ')[0], 'false', 'false', str(now - datetime.timedelta(seconds=60)), '60', str(now - datetime.timedelta(days=1)), '', '')
                )
                return self.view(uid)
        except Exception: return {'status': False}


    def viewCmd(self, cmd:str) -> dict:
        try:
            data_ = self.no_commit("SELECT * FROM comandos WHERE comando = %s", (cmd,))
            if not data_['status']: return {'status': False}
            B = data_['data']
            if len(B) > 0:
                return {'status':True, 'command':B[0][0], 'mode':B[0][2], 'type':B[0][1], 'review':B[0][3], 'comment':B[0][4], 'emoji':self.modes.get(B[0][2], '?'), 'name':B[0][5], 'use':B[0][6]}
            else: return {'status': 'unval'}
        except Exception: return {'status': False}


    def viewCmds(self, typeC:str) -> dict:
        try:
            data_ = self.no_commit("SELECT * FROM comandos WHERE tipo = %s", (typeC,))
            if not data_['status']: return {'status': False}
            B = data_['data']
            if len(B) > 0: return {'status': True, 'response': B}
            else: return {'status': 'unval'}
        except Exception: return {'status': False}


    def addC(self, cmd:str, mode:str, typec:str, comment:str, name:str, use:str) -> None:
        try:
            self.commit(
                "INSERT INTO comandos (comando, tipo, status, d_reg, comentario, name, use) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (cmd, typec, mode, str(datetime.datetime.now()).split(' ')[0], comment, name, use)
            )
        except Exception: return {'status': False}


    def delC(self, cmd:str) -> None:
        try: self.commit("DELETE FROM comandos WHERE comando = %s", (cmd,))
        except Exception: return {'status': False}


    def upC(self, cmd:str, mode:str, comment:str) -> None:
        try:
            self.commit(
                "UPDATE comandos SET status = %s, d_reg = %s, comentario = %s WHERE comando = %s",
                (mode, str(datetime.datetime.now()).split(' ')[0], comment, cmd)
            )
        except Exception: return {'status': False}


    def update_cmd_field(self, command:str, field:str, value:str) -> dict:
        values = {'type': 'tipo', 'name': 'name', 'status': 'status', 'comment': 'comentario', 'use': 'use'}
        if field not in values:
            return {'status': False, 'reason': 'invalid_field'}
        return self.commit(f"UPDATE comandos SET {values[field]} = %s, d_reg = %s WHERE comando = %s", (value, str(datetime.datetime.now()).split(' ')[0], command))


    def vKey(self, key:str) -> dict:
        try:
            data_ = self.no_commit("SELECT * FROM keys WHERE key = %s", (key,))
            if not data_['status']: return {'status': False}
            B = data_['data']
            return {'status':True, 'days':B[0][1], 'credits':B[0][2], 'mode':B[0][3], 'key':B[0][0]} if len(B) > 0 else {'status': False}
        except Exception: return {'status': False}


    def addDays(self, days:int, base:object = None) -> object:
        try:
            if base is None: base = datetime.datetime.now()
            return base + datetime.timedelta(days=int(days))
        except Exception: return None


    def all_user_ids(self) -> list:
        try:
            data = self.no_commit("SELECT user_id FROM users WHERE user_id NOT LIKE '-%'")
            return [r[0] for r in data['data']] if data['status'] and data['data'] else []
        except Exception: return []


    def user_stats(self) -> dict:
        out = {'total': 0, 'free': 0, 'premium': 0, 'staff': 0, 'banned': 0}
        try:
            rows = self.no_commit(
                "SELECT COUNT(*), "
                "COUNT(*) FILTER (WHERE rango='free'), "
                "COUNT(*) FILTER (WHERE rango='premium'), "
                "COUNT(*) FILTER (WHERE rango IN ('admin','owner','mod')), "
                "COUNT(*) FILTER (WHERE ban='true') "
                "FROM users WHERE user_id NOT LIKE '-%'"
            )
            if rows['status'] and rows['data']:
                r = rows['data'][0]
                out = {'total': r[0], 'free': r[1], 'premium': r[2], 'staff': r[3], 'banned': r[4]}
        except Exception: pass
        return out


    def proxy(self) -> dict:
        try:
            if not self._view_cache.get('_proxies'):
                with open("Commands/Docs/proxy2.txt", 'r') as f:
                    self._view_cache['_proxies'] = [l.strip() for l in f if l.strip()]
            raw = random.choice(self._view_cache['_proxies'])
            if '@' in raw:
                proxy_url = f"http://{raw}"
            else:
                a = raw.split(':')
                proxy_url = f"http://{a[0]}:{a[1]}"
            return {'http': proxy_url, 'https': proxy_url}
        except Exception: return {}


    def _set(self, time:str) -> object:
        try:
            return datetime.datetime.fromisoformat(str(time).replace('Z', ''))
        except Exception:
            try:
                b = str(time).replace(' ', '|').replace('-', '|').replace(':', '|')
                e = b.split('|')
                return datetime.datetime(year=int(e[0]), month=int(e[1]), day=int(e[2]), hour=int(e[3]), minute=int(e[4]), second=int(round(float(e[5]), 0)))
            except Exception: return None


    def antispam(self, spam:str, l_reg:str) -> dict:
        try:
            _set = self._set(str(l_reg))
            if _set is None: return {'perm': True}
            spam_time = _set + datetime.timedelta(seconds=int(spam))
            now = datetime.datetime.now()
            if spam_time <= now: return {'perm': True}
            else: return {'perm': False, 'time': str(int(round((spam_time - now).total_seconds(), 0)))}
        except Exception: return {'perm': True}


    def regex(self, text:str) -> dict:
        try:
            year = datetime.datetime.now().year
            card = ['', '', '', '']
            lens = {'3': 15, '4': 16, '5': 16, '6': 16}
            cvvs = {'3': 4, '4': 3, '5': 3, '6': 3}
            data = [i for i in ''.join(c if c.isdigit() else ' ' for c in text).split() if i]
            for i in data:
                if i[0] in lens.keys() and card[0] == '':
                    if len(i) == lens[i[0]]: card[0] = i
                elif int(i) <= 12 and card[1] == '':
                    card[1] = f"0{i}" if len(i) == 1 else i
                elif int(i) >= 2020 and int(i) <= year + 10 and card[2] == '':
                    card[2] = i
                elif len(i) == 2 and card[2] == '':
                    if int(i) >= int(str(year)[2:]) and int(i) <= int(str((year + 10))[2:]):
                        card[2] = f"20{i}"
                elif len(i) in [3, 4] and card[3] == '':
                    card[3] = i
            cc = [i for i in card if i]
            if len(cc) == 4 and luhn.verify(cc[0]):
                exp = datetime.datetime(int(cc[2]), int(cc[1]), 20)
                if datetime.datetime.now() <= exp:
                    if len(card[3]) == cvvs[card[0][0]]: return {'status': True, 'response': cc}
                    else: return {'status': False, 'response': cc}
                else: return {'status': False, 'rise': cc}
            else: return {'status': False, 'rise': cc}
        except Exception: return {'status': False}


    def lookup(self, text:str) -> dict:
        _bin = ''.join([i for i in text if i.isdigit()])
        if len(_bin) >= 6:
            _bin6 = _bin[:6]
            if _bin6 in self._view_cache.get('_bins', {}):
                return self._view_cache['_bins'][_bin6]
            try:
                r = self._session.get(url=f"https://jaimito.alwaysdata.net/Apis/bin.php?bin={_bin6}", timeout=10).json()
                if r.get('status') and r.get('brand'):
                    result = {'status': True, 'response': {
                        'bin':      r['bin'],
                        'brand':    r['brand'].title(),
                        'type':     r['type'].title(),
                        'level':    r.get('level', 'N/A').title(),
                        'bank':     (r.get('bank_name') or 'N/A').title(),
                        'country':  r.get('country_name', 'N/A').title(),
                        'flag':     r.get('flag', ''),
                        'currency': r.get('iso2', 'N/A'),
                    }}
                else:
                    result = {'status': False}
                if '_bins' not in self._view_cache: self._view_cache['_bins'] = {}
                self._view_cache['_bins'][_bin6] = result
                return result
            except Exception: return {'status': False}
        else: return {'status': False}


    # ── BIN BAN SYSTEM ──────────────────────────────────────────────────────────

    def _hash_card(self, card:str) -> str:
        return hashlib.sha256(card.encode()).hexdigest()


    def is_bin_banned(self, _bin:str) -> bool:
        try:
            data = self.no_commit("SELECT 1 FROM banned_bins WHERE bin = %s", (str(_bin)[:6],))
            return bool(data['status'] and data['data'])
        except Exception: return False


    def add_banned_bin(self, _bin:str, added_by:str = '', reason:str = '') -> dict:
        b = str(_bin)[:6]
        if len(b) != 6 or not b.isdigit():
            return {'status': False, 'reason': 'invalid_bin'}
        if self.is_bin_banned(b):
            return {'status': False, 'reason': 'already_banned'}
        r = self.commit("INSERT INTO banned_bins (bin, reason, added_by) VALUES(%s,%s,%s)", (b, reason, str(added_by)))
        return {'status': True} if r['status'] else {'status': False, 'reason': str(r.get('reason', 'db error'))}


    def remove_banned_bin(self, _bin:str) -> dict:
        b = str(_bin)[:6]
        if len(b) != 6 or not b.isdigit():
            return {'status': False, 'reason': 'invalid_bin'}
        if not self.is_bin_banned(b):
            return {'status': False, 'reason': 'not_banned'}
        r = self.commit("DELETE FROM banned_bins WHERE bin = %s", (b,))
        return {'status': True} if r['status'] else {'status': False, 'reason': str(r.get('reason', 'db error'))}


    def list_banned_bins(self, limit:int = 20, offset:int = 0) -> dict:
        data = self.no_commit("SELECT bin, reason, added_by, d_reg FROM banned_bins ORDER BY d_reg DESC LIMIT %s OFFSET %s", (limit, offset))
        return {'status': True, 'data': data['data']} if data['status'] and data['data'] else {'status': False, 'data': []}


    def count_banned_bins(self) -> int:
        data = self.no_commit("SELECT COUNT(*) FROM banned_bins")
        return int(data['data'][0][0]) if data['status'] and data['data'] else 0


    # ── CARD RATE-LIMIT & ABUSE DETECTION ───────────────────────────────────────

    def _card_cooldown(self, card:str) -> dict:
        # Rate-limit: same card checked by anyone within CARD_COOLDOWN → wait, no warn
        try:
            h      = self._hash_card(card)
            cutoff = datetime.datetime.now() - datetime.timedelta(seconds=self.CARD_COOLDOWN)
            data   = self.no_commit("SELECT used_at FROM card_uses WHERE card_hash = %s AND used_at > %s ORDER BY used_at DESC LIMIT 1", (h, cutoff))
            if data['status'] and data['data']:
                last = self._set(data['data'][0][0])
                if last:
                    wait = int((last + datetime.timedelta(seconds=self.CARD_COOLDOWN) - datetime.datetime.now()).total_seconds())
                    return {'limited': True, 'wait': max(wait, 0)}
            return {'limited': False, 'wait': 0}
        except Exception: return {'limited': False, 'wait': 0}


    def _card_user_uses(self, card:str, user_id:str) -> int:
        # Abuse: how many times this user checked this same card within ABUSE_WINDOW
        try:
            h      = self._hash_card(card)
            cutoff = datetime.datetime.now() - datetime.timedelta(seconds=self.ABUSE_WINDOW)
            data   = self.no_commit("SELECT COUNT(*) FROM card_uses WHERE card_hash = %s AND user_id = %s AND used_at > %s", (h, str(user_id), cutoff))
            return int(data['data'][0][0]) if data['status'] and data['data'] else 0
        except Exception: return 0


    def register_card_use(self, card:str, user_id:str) -> None:
        try:
            h      = self._hash_card(card)
            now    = datetime.datetime.now()
            cutoff = now - datetime.timedelta(hours=24)
            # Store used_at with the app clock (matches antispam/l_reg) — NOT the DB now() default, which is UTC
            self.commit("INSERT INTO card_uses (card_hash, user_id, used_at) VALUES(%s,%s,%s)", (h, str(user_id), str(now)))
            self.commit("DELETE FROM card_uses WHERE used_at < %s", (str(cutoff),))
        except Exception: pass


    def check_card_abuse(self, card:str, user_id:str) -> dict:
        """Two-tier: cooldown (no warn) → abuse (warn + auto-ban BIN). Records the use only on 'allow'."""
        try:
            cd = self._card_cooldown(card)
            if cd['limited']:
                return {'action': 'rate_limited', 'wait': cd['wait']}
            if self._card_user_uses(card, user_id) >= self.ABUSE_THRESHOLD:
                _bin = ''.join([c for c in str(card) if c.isdigit()])[:6]
                self.add_banned_bin(_bin, reason='AutoProtect', added_by='AutoProtect')
                warns = self.add_warn(str(user_id))
                if warns >= self.MAX_WARNS:
                    return {'action': 'user_banned', 'warns': warns, 'bin': _bin}
                return {'action': 'abuse_detected', 'warns': warns, 'bin': _bin}
            self.register_card_use(card, user_id)
            return {'action': 'allow'}
        except Exception:
            return {'action': 'allow'}


    # ── WARN SYSTEM (auto-ban at MAX_WARNS) ─────────────────────────────────────

    def add_warn(self, user_id:str) -> int:
        try:
            data  = self.no_commit("SELECT warns FROM users WHERE user_id = %s", (str(user_id),))
            if data['status'] and data['data']:
                warns = int(data['data'][0][0]) + 1
                self.commit("UPDATE users SET warns = %s WHERE user_id = %s", (str(warns), str(user_id)))
                if warns >= self.MAX_WARNS:
                    self.commit(
                        "UPDATE users SET ban = %s, rango = %s, c_name = %s, credits = %s WHERE user_id = %s",
                        ('true', 'free', 'free user', '0', str(user_id))
                    )
                self._view_cache.pop(str(user_id), None)
                return warns
            return 0
        except Exception: return 0


    # ── USAGE LOGGING ───────────────────────────────────────────────────────────

    def log_usage(self, user_id:str, command:str, cmd_type:str = 'unknown') -> None:
        try: self.commit("INSERT INTO usage_log (user_id, command, cmd_type) VALUES(%s,%s,%s)", (str(user_id), command, cmd_type))
        except Exception: pass


    # ── EVENT HISTORY (full queryable audit trail) ───────────────────────────────

    def log_event(self, actor_id:str, actor_name:str, action:str, target:str = '', detail:str = '') -> None:
        try:
            self.commit(
                "INSERT INTO events (actor_id, actor_name, action, target, detail) VALUES(%s,%s,%s,%s,%s)",
                (str(actor_id), str(actor_name)[:100], str(action)[:60], str(target)[:60], str(detail)[:500])
            )
        except Exception: pass

    def list_events(self, target:str = None, limit:int = 15) -> list:
        # Recent events; if `target` given, match either the actor or the target of the event
        if target:
            d = self.no_commit(
                "SELECT TO_CHAR(at,'DD/MM HH24:MI'), actor_name, action, target, detail FROM events "
                "WHERE actor_id = %s OR target = %s ORDER BY at DESC LIMIT %s",
                (str(target), str(target), limit)
            )
        else:
            d = self.no_commit(
                "SELECT TO_CHAR(at,'DD/MM HH24:MI'), actor_name, action, target, detail FROM events ORDER BY at DESC LIMIT %s",
                (limit,)
            )
        return d['data'] if d['status'] and d['data'] else []


    def sync_user(self, user_id:str, username:str, nombre:str = '') -> None:
        try:
            uid   = str(user_id)
            uname = username.lstrip('@') if username else ''
            if not uname and not nombre:
                return
            # Skip the write when nothing changed (view() was already called this request)
            cached = self._view_cache.get(uid)
            if cached is not None:
                same_u = (not uname)  or cached.get('nombre_usuario', '') == uname
                same_n = (not nombre) or cached.get('nombre', '')         == nombre
                if same_u and same_n:
                    return
            parts, vals = [], []
            if uname:
                parts.append("nombre_usuario = %s"); vals.append(uname)
            if nombre:
                parts.append("nombre = %s"); vals.append(nombre)
            vals.append(uid)
            self.commit(f"UPDATE users SET {', '.join(parts)} WHERE user_id = %s", tuple(vals))
            self._view_cache.pop(uid, None)
        except Exception: pass


    # ── COOKIE STORE (Amazon) ───────────────────────────────────────────────────

    def cookie_verify(self, user_id:str) -> dict:
        try:
            data = self.no_commit("SELECT cookie FROM cookies WHERE user_id = %s", (str(user_id),))
            if data['status'] and data['data']:
                return {'status': True, 'response': data['data'][0][0]}
            return {'status': False, 'raise': 'No cookie found for this user!'}
        except Exception as e:
            return {'status': False, 'raise': str(e)}


    def cookie_add(self, user_id:str, cookie:str) -> dict:
        r = self.commit(
            "INSERT INTO cookies (user_id, cookie, updated_at) VALUES(%s, %s, NOW()) "
            "ON CONFLICT (user_id) DO UPDATE SET cookie = EXCLUDED.cookie, updated_at = NOW()",
            (str(user_id), cookie)
        )
        return {'status': True} if r['status'] else {'status': False, 'raise': str(r.get('reason', 'db error'))}


    def cookie_del(self, user_id:str) -> dict:
        r = self.commit("DELETE FROM cookies WHERE user_id = %s", (str(user_id),))
        return {'status': True} if r['status'] else {'status': False, 'raise': str(r.get('reason', 'db error'))}


    def cookie_list(self) -> dict:
        try:
            data = self.no_commit("SELECT user_id FROM cookies ORDER BY updated_at DESC")
            return {'status': True, 'response': [r[0] for r in data['data']] if data['status'] and data['data'] else []}
        except Exception as e:
            return {'status': False, 'raise': str(e)}


    # ── PLANS / SALES / SELLERS ─────────────────────────────────────────────────

    def add_plan(self, name:str, days:str, credits:str, price:str) -> dict:
        return self.commit(
            "INSERT INTO plans (name, days, credits, price) VALUES(%s,%s,%s,%s) "
            "ON CONFLICT (name) DO UPDATE SET days=EXCLUDED.days, credits=EXCLUDED.credits, price=EXCLUDED.price, active=TRUE",
            (name, int(days), str(credits), float(price))
        )

    def del_plan(self, name:str) -> dict:
        return self.commit("DELETE FROM plans WHERE lower(name) = lower(%s)", (name,))

    def view_plans(self) -> list:
        d = self.no_commit("SELECT name, days, credits, price FROM plans WHERE active = TRUE ORDER BY price")
        return d['data'] if d['status'] and d['data'] else []

    def view_plan(self, name:str) -> dict:
        d = self.no_commit("SELECT name, days, credits, price FROM plans WHERE lower(name) = lower(%s) AND active = TRUE", (name,))
        if d['status'] and d['data']:
            r = d['data'][0]
            return {'status': True, 'name': r[0], 'days': r[1], 'credits': r[2], 'price': float(r[3])}
        return {'status': False}

    def record_sale(self, seller_id:str, seller_name:str, plan:str, price, client:str, method:str) -> dict:
        return self.commit(
            "INSERT INTO sales (seller_id, seller_name, plan, price, client, method) VALUES(%s,%s,%s,%s,%s,%s)",
            (str(seller_id), seller_name, plan, float(price), str(client), method)
        )

    def sales_report(self, seller_id:str = None) -> dict:
        """Current-month sales aggregated by plan. Pass seller_id to scope to one seller.
        Returns {'plans': [(plan, count, total, unit)], 'total': float, 'count': int}."""
        where  = "WHERE date_trunc('month', sold_at) = date_trunc('month', NOW())"
        params = ()
        if seller_id:
            where += " AND seller_id = %s"; params = (str(seller_id),)
        d = self.no_commit(f"SELECT plan, COUNT(*), SUM(price) FROM sales {where} GROUP BY plan ORDER BY SUM(price) DESC", params)
        rows  = d['data'] if d['status'] and d['data'] else []
        plans = [(r[0], int(r[1]), float(r[2]), float(r[2]) / int(r[1]) if r[1] else 0.0) for r in rows]
        return {'plans': plans, 'total': sum(p[2] for p in plans), 'count': sum(p[1] for p in plans)}

    def sellers_report(self) -> list:
        """Current-month totals per seller. Returns [(seller_id, seller_name, count, total)]."""
        d = self.no_commit(
            "SELECT seller_id, MAX(seller_name), COUNT(*), SUM(price) FROM sales "
            "WHERE date_trunc('month', sold_at) = date_trunc('month', NOW()) "
            "GROUP BY seller_id ORDER BY SUM(price) DESC"
        )
        return [(r[0], r[1], int(r[2]), float(r[3])) for r in d['data']] if d['status'] and d['data'] else []


    # ── TICKETS / SUPPORT ────────────────────────────────────────────────────────

    def create_ticket(self, user_id:str, username:str, problem:str, description:str) -> dict:
        r = self._run(
            "INSERT INTO tickets (user_id, username, problem, description) VALUES(%s,%s,%s,%s) RETURNING id",
            (str(user_id), username, problem, description), fetch=True, commit=True
        )
        return {'status': True, 'id': r['data'][0][0]} if r['status'] and r['data'] else {'status': False}

    def view_ticket(self, ticket_id) -> dict:
        d = self.no_commit("SELECT id, user_id, username, problem, description, status, TO_CHAR(created_at,'DD/MM/YYYY'), closed_by FROM tickets WHERE id = %s", (int(ticket_id),))
        if d['status'] and d['data']:
            r = d['data'][0]
            return {'status': True, 'id': r[0], 'user_id': r[1], 'username': r[2], 'problem': r[3], 'description': r[4], 'ticket_status': r[5], 'date': r[6], 'closed_by': r[7]}
        return {'status': False}

    def list_tickets(self, status:str = 'pending', limit:int = 15) -> list:
        d = self.no_commit("SELECT id, username, problem, TO_CHAR(created_at,'DD/MM/YYYY') FROM tickets WHERE status = %s ORDER BY created_at DESC LIMIT %s", (status, limit))
        return d['data'] if d['status'] and d['data'] else []

    def set_ticket_status(self, ticket_id, status:str, closed_by:str = None) -> dict:
        return self.commit("UPDATE tickets SET status = %s, closed_by = %s WHERE id = %s", (status, closed_by, int(ticket_id)))

    def count_tickets(self, status:str = 'pending') -> int:
        d = self.no_commit("SELECT COUNT(*) FROM tickets WHERE status = %s", (status,))
        return int(d['data'][0][0]) if d['status'] and d['data'] else 0


    # ── GATE VALIDATION ─────────────────────────────────────────────────────────

    def gates(self, user:dict, chat:dict, text:str, cmd:dict, bot) -> dict:
        try:
            if user['ban'] == 'false':
                if chat['rango'] in self.prem:
                    if cmd['status'] != 'unval':
                        if cmd['mode'] == 'on' or chat['rango'].lower() == 'owner':
                            if len(text) > 0:
                                data = self.regex(text=text)
                                if data['status']:
                                    _bin = self.lookup(text=data['response'][0])
                                    if _bin['status']:
                                        # BIN blacklist check
                                        if self.is_bin_banned(data['response'][0][:6]):
                                            return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()} 🌩</i></b>\n<b><i><u>Raise:</u></i></b> <code>[{data['response'][0][:6]}] BIN Banned!</code>"}
                                        if _bin['response']['brand'].lower() in ['visa', 'mastercard', 'discover', 'american express']:
                                            if 'prepaid' not in _bin['response']['level'].lower():
                                                gate_type = cmd.get('type', 'charged')
                                                is_staff  = user['rango'] in self.rangos
                                                if not is_staff:
                                                    # Antispam (all gate types)
                                                    spam = self.antispam(spam=user['spam'], l_reg=user['l_reg'])
                                                    if not spam['perm']:
                                                        return {'status': False, 'text': f"<b><i>$ Anti Spam ⚠️</i></b>\n<b><i><u>Raise:</u></i></b> <code>Wait {spam['time']}'s for the next check!</code>"}
                                                    # Card abuse check (all gate types)
                                                    abuse = self.check_card_abuse(data['response'][0], str(user['user_id']))
                                                    if abuse['action'] == 'rate_limited':
                                                        return {'status': False, 'text': f"<b><i>$ Anti Abuse ⚠️</i></b>\n<b><i><u>Raise:</u></i></b> <code>Card checked too soon! Wait {abuse['wait']}'s.</code>"}
                                                    if abuse['action'] == 'user_banned':
                                                        return {'status': False, 'text': f"<b><i>$ Anti Abuse ⚠️</i></b>\n<b><i><u>Raise:</u></i></b> <code>Auto-banned for card abuse ({abuse['warns']} warns).</code>"}
                                                    if abuse['action'] == 'abuse_detected':
                                                        return {'status': False, 'text': f"<b><i>$ Anti Abuse ⚠️</i></b>\n<b><i><u>Raise:</u></i></b> <code>Abuse detected! BIN {abuse['bin']} banned. Warn {abuse['warns']}/{self.MAX_WARNS}</code>"}
                                                    # Record gate use time so antispam cooldown kicks in on next attempt
                                                    self.commit("UPDATE users SET l_reg = %s WHERE user_id = %s", (str(datetime.datetime.now()), str(user['user_id'])))
                                                    self._view_cache.pop(str(user['user_id']), None)
                                                    # Credit cost by gate type: auth/charged=1, ccn/avs=2, specials=3
                                                    _COST = {'auths': 1, 'charged': 1, 'ccn': 2, 'avs': 2, 'specials': 3}
                                                    cost = _COST.get(gate_type, 1)
                                                    try:    credits = int(user.get('credits', 0))
                                                    except (ValueError, TypeError): credits = 0
                                                    if credits < cost:
                                                        return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()} 🌩</i></b>\n<b><i><u>Raise:</u></i></b> <code>Need at least {cost} credit{'s' if cost > 1 else ''}! Use /claim to add more.</code>"}
                                                    return {'status': True, 'cc': data['response'], 'bin': _bin['response'], 'credits': credits, 'gate_type': gate_type, 'cost': cost}
                                                else:
                                                    # Staff: antispam only, no credit management
                                                    spam = self.antispam(spam=user['spam'], l_reg=user['l_reg'])
                                                    if not spam['perm']:
                                                        return {'status': False, 'text': f"<b><i>$ Anti Spam ⚠️</i></b>\n<b><i><u>Raise:</u></i></b> <code>Wait {spam['time']}'s for the next check!</code>"}
                                                    return {'status': True, 'cc': data['response'], 'bin': _bin['response'], 'credits': '∞', 'gate_type': gate_type}
                                            else: return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()} 🌩</i></b>\n<b><i><u>Raise:</u></i></b> <code>[{_bin['response']['bin']}] Bin Banned!</code>"}
                                        else: return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()} 🌩</i></b>\n<b><i><u>Raise:</u></i></b> <code>Only Support Visa, Master, Discover & Amex!</code>"}
                                    else: return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()}_ 🌩</i></b>\n<b><i><u>Raise:</u></i></b> <code>Only Support Visa, Master, Discover & Amex!</code>"}
                                else: return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()} 🌩</i></b>\n<b><i><u>Use:</u></i></b> <code>/{cmd['command']} {cmd['use']}</code>"}
                            else: return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()} 🌩</i></b>\n<b><i><u>Use:</u></i></b> <code>/{cmd['command']} {cmd['use']}</code>" + ('\n<b><i><u>Comment:</u></i></b> <code>' + cmd['comment'].title() + '</code>' if cmd['comment'].lower() != 'none' else '')}
                        elif cmd['mode'] == 'ma': return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()} {self.modes[cmd['mode']]}</i></b>\n<b><i><u>Raise:</u></i></b> <code>Command in maintenance! ({self.modes[cmd['mode']]})</code>" + ('\n<b><i><u>Comment:</u></i></b> <code>' + cmd['comment'].title() + '</code>' if cmd['comment'].lower() != 'none' else '')}
                        elif cmd['mode'] == 'of': return {'status': False, 'text': f"<b><i>$ {cmd['name'].title()} {self.modes[cmd['mode']]}</i></b>\n<b><i><u>Raise:</u></i></b> <code>Command Offline! ({self.modes[cmd['mode']]})</code>" + ('\n<b><i><u>Comment:</u></i></b> <code>' + cmd['comment'].title() + '</code>' if cmd['comment'].lower() != 'none' else '')}
                    else: return {'status': False, 'text': "<b><i>$ Wrong Data_ ⚠️</i></b>\n<b><i><u>Important:</u></i></b> <code>This command exists but is not yet registered, be patient for its inauguration!</code>"}
                else: return {'status': False, 'text': "<b><i>$ Wrong Data_ ⚠️</i></b>\n<b><i><u>Raise:</u></i></b> <code>This Chat Is Not Authorized!</code>"}
            else: return {'status': False, 'text': "<b><i>$ Wrong Data_ ⚠️</i></b>\n<b><i><u>Raise:</u></i></b> <code>You are banned from this bot!</code>"}
        except Exception as a:
            bot.raise_post(f"Error en el verificador de gates - {str(a)}")
            return {'status': False, 'text': "<b><i>$ Wrong Data_ ⚠️</i></b>\n<b><i><u>Raise:</u></i></b> <code>There is a problem, contact an administrator!</code>"}

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

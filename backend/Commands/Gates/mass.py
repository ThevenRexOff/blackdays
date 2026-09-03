# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time, threading, datetime, importlib, inspect, html as _html_mod
from concurrent.futures import ThreadPoolExecutor, as_completed
from Commands.Gates._template import DIV

MAX_CARDS  = 10
_GATE_COST = {'auths': 1, 'charged': 1, 'ccn': 2, 'avs': 2, 'specials': 3}

# Gate command -> module that actually implements run_check (for aliases).
_ALIAS = {'amz': 'amazon', 'amzg': 'amazon'}


# ── Checker loader ────────────────────────────────────────────────────────────

def _load_checker(cmd: str):
    """Import Commands.Gates.{cmd}, normalize its signature to (cc, bin_d, ctx),
    and return the wrapper — or None if the module/function doesn't exist."""
    try:
        mod = importlib.import_module(f'Commands.Gates.{_ALIAS.get(cmd, cmd)}')
        fn  = getattr(mod, 'run_check', None)
        if not callable(fn):
            return None
        try:
            n = len(inspect.signature(fn).parameters)
        except (ValueError, TypeError):
            n = 3
        if n < 3:
            return lambda cc, bin_d, ctx=None: fn(cc, bin_d)
        return fn
    except (ImportError, Exception):
        pass
    return None


# ── Per-card runner (called from thread pool) ─────────────────────────────────

def _run_one(checker, gestion, raw: str, ctx: dict = None) -> dict:
    try:
        parsed = gestion.regex(raw)
        if not parsed['status']:
            return {'cc': raw[:35], 'status': 'Invalid ⚠️', 'live': False}
        cc     = parsed['response']
        cc_str = f"{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}"
        if gestion.is_bin_banned(cc[0][:6]):
            return {'cc': cc_str, 'status': 'BIN Banned ⛔', 'live': False}
        bin_r  = gestion.lookup(cc[0])
        bin_d  = bin_r.get('response', {}) if bin_r.get('status') else {}
        result = checker(cc, bin_d, ctx)  # signature normalized by _load_checker
        live   = result.get('success', False) or result.get('status') == 'Approved ✅'
        status = result.get('response') or result.get('status') or ('Approved ✅' if live else 'Declined ❌')
        return {'cc': cc_str, 'status': status, 'live': live}
    except Exception:
        return {'cc': str(raw)[:35], 'status': 'Error ⚠️', 'live': False}


# ── Command handler ───────────────────────────────────────────────────────────

def gateCmd(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)

        raw   = (bot.cmd.args if len(bot.cmd.args) > 0
                 else (update.reply_to.text if update.reply_to else ''))
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]

        _usage = (
            f"{bot.bi('Mass Checker')} [ 🍸 ]\n{DIV}\n"
            f"🍹 {bot.bi('How it works')}:\n"
            f"<code>Corre cualquier gate registrado en masa.\n"
            f"La primera línea es el comando del gate,\n"
            f"las siguientes son las tarjetas a procesar.</code>\n{DIV}\n"
            f"🍸 {bot.bi('Use')}:\n"
            f"<code>/mass GATE\n"
            f"cc|mm|yy|cvv\n"
            f"cc|mm|yy|cvv</code>\n{DIV}\n"
            f"🍸 {bot.bi('Example')}:\n"
            f"<code>/mass mj\n"
            f"4111111111111111|12|2026|123\n"
            f"5200828282828210|08|2027|456</code>\n{DIV}\n"
            f"💳 {bot.bi('Cost')}: <code>1-3 créditos por live según gate — solo cobra si es Approved.</code>\n"
            f"⚡ {bot.bi('Info')}: <code>Máx {MAX_CARDS} tarjetas por corrida. Sub de chat requerida.</code>"
        )

        if len(lines) < 2:
            return bot.replyMessage(text=_usage)

        target_cmd = lines[0].lower().strip()
        card_lines  = lines[1:]

        # ── Guards ─────────────────────────────────────────────────────────────
        if user['ban'] == 'true':
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>You are banned from this bot!</code>"
            ))
        if chat['rango'] not in gestion.prem:
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>This chat is not authorized!</code>"
            ))

        # ── Target gate lookup ─────────────────────────────────────────────────
        target = gestion.viewCmd(target_cmd)
        if target.get('status') != True:
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>Gate [{target_cmd}] not found in DB.</code>"
            ))

        is_staff  = user['rango'] in gestion.rangos
        gate_mode = target.get('mode', 'on')
        if gate_mode != 'on' and not is_staff:
            label = 'maintenance' if gate_mode == 'ma' else 'offline'
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>Gate [{target_cmd}] is {label}.</code>"
            ))

        gate_name = target.get('name', target_cmd).title()

        # ── Anti-spam & credits ────────────────────────────────────────────────
        gate_type_mass = target.get('type', 'charged')
        live_cost      = _GATE_COST.get(gate_type_mass, 1)
        if not is_staff:
            spam = gestion.antispam(spam=user['spam'], l_reg=user['l_reg'])
            if not spam['perm']:
                return bot.replyMessage(text=(
                    f"{bot.bi('Anti Spam')} [ ⚠️ ]\n"
                    f"🍸 {bot.bi('Raise')}: <code>Wait {spam['time']}'s for the next check!</code>"
                ))
            credits_raw = str(user.get('credits', '0'))
            if credits_raw.lower() != 'unlimited':
                try:    credits = int(credits_raw)
                except (ValueError, TypeError): credits = 0
                if credits < live_cost:
                    return bot.replyMessage(text=(
                        f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                        f"🍸 {bot.bi('Raise')}: <code>Need at least {live_cost} credit{'s' if live_cost > 1 else ''}. Use /claim.</code>"
                    ))

        # ── Checker lookup ─────────────────────────────────────────────────────
        checker = _load_checker(target_cmd)
        if checker is None:
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>Gate [{target_cmd}] has no mass checker yet.</code>\n"
                f"⚡ {bot.bi('Fix')}: <code>Add run_check() to Commands/Gates/{target_cmd}.py</code>"
            ))

        # ── Context (cookie for Amazon-style gates) ────────────────────────────
        cookie = None
        try:
            ck = gestion.cookie_verify(str(update.user_id))
            cookie = ck.get('response') if ck.get('status') else None
        except Exception:
            cookie = None
        # Amazon Global (amz/amzg) needs a cookie — fail fast with a clear message.
        if target_cmd in _ALIAS and not cookie:
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>This gate needs your Amazon cookie.</code>\n"
                f"🍸 {bot.bi('Fix')}: <code>/cookie your_amazon_cookie</code>"
            ))
        ctx = {'gestion': gestion, 'user_id': str(update.user_id), 'cookie': cookie}

        # ── Process ────────────────────────────────────────────────────────────
        cards = card_lines[:MAX_CARDS]
        n     = len(cards)
        now   = time.time()
        edit  = bot.replyMessage(text=(
            f"{bot.bi('Mass')}({gate_name}) [ 🍸 ]\n{DIV}\n"
            f"⚡ {bot.bi('Running')}: <code>{n} cards → {gate_name}...</code>"
        ))
        mid = edit.message_id if edit else None

        stop = threading.Event()
        if mid:
            _dots = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
            def _spin():
                i = 0
                while not stop.is_set():
                    try: bot.editMessage(message_id=mid, text=(
                        f"{bot.bi('Mass')}({gate_name}) [ 🍸 ]\n{DIV}\n"
                        f"⚡ {bot.bi('Running')}: <code>{n} cards → {gate_name} {_dots[i % 10]}</code>"
                    ))
                    except Exception: pass
                    i += 1
                    stop.wait(1.4)
            th = threading.Thread(target=_spin, daemon=True)
            th.start()
        else:
            th = None

        try:
            results = []
            with ThreadPoolExecutor(max_workers=min(n, 5)) as pool:
                futs = {pool.submit(_run_one, checker, gestion, c, ctx): c for c in cards}
                for fut in as_completed(futs):
                    try:    results.append(fut.result())
                    except: results.append({'cc': futs[fut][:35], 'status': 'Error ⚠️', 'live': False})
        finally:
            stop.set()
            if th: th.join(timeout=2)

        lives    = sum(1 for r in results if r['live'])
        declines = sum(1 for r in results if not r['live'] and 'Declined' in r.get('status', ''))
        errors   = n - lives - declines

        # Atomic deduction — avoids race with concurrent webhook processes.
        # Only runs against numeric credits rows (unlimited users are untouched).
        if not is_staff and lives > 0:
            gestion.commit(
                "UPDATE users SET credits = GREATEST(0, (credits::integer - %s))::text "
                "WHERE user_id = %s AND credits ~ '^[0-9]+$'",
                (str(lives * live_cost), str(update.user_id))
            )

        # Update l_reg so antispam cooldown starts from this mass run
        if not is_staff:
            gestion.commit(
                "UPDATE users SET l_reg = %s WHERE user_id = %s",
                (str(datetime.datetime.now()), str(update.user_id))
            )
            gestion._view_cache.pop(str(update.user_id), None)

        # ── Build result card ──────────────────────────────────────────────────
        # Sort: live first, declined second, errors last
        sorted_r = sorted(results, key=lambda x: (
            0 if x['live'] else (1 if 'Declined' in x.get('status', '') else 2)
        ))

        text = f"{bot.bi('Mass')}({gate_name}) [ 🍸 ]\n{DIV}\n"
        for r in sorted_r:
            if r['live']:
                icon = '✅'
            elif 'Declined' in r.get('status', ''):
                icon = '❌'
            else:
                icon = '⚠️'
            resp = r.get('status', '')
            for pfx in ('Approved ✅ | ', 'Declined ❌ | ', 'Error ⚠️ | '):
                if resp.startswith(pfx):
                    resp = resp[len(pfx):]
                    break
            if resp in ('Approved ✅', 'Declined ❌', 'Error ⚠️', ''):
                resp = ''
            if len(resp) > 45:
                resp = resp[:45] + '…'
            suffix = f' · <code>{_html_mod.escape(resp)}</code>' if resp else ''
            text += f"{icon} <code>{r['cc']}</code>{suffix}\n"

        cost_note = ''
        if not is_staff and lives > 0:
            cost_note = f"💳 {bot.bi('Cost')}: <code>{lives * live_cost} credits</code>\n"

        text += (
            f"{DIV}\n"
            f"✅ {bot.bi('Live')}: <code>{lives}</code>  "
            f"❌ {bot.bi('Dead')}: <code>{declines}</code>  "
            f"⚠️ {bot.bi('Error')}: <code>{errors}</code>\n"
            f"💳 {bot.bi('Gate')}: <code>{gate_name}</code>\n"
            f"{cost_note}"
            f"⚡ {bot.bi('T. Taken')}: <code>{round(time.time() - now, 1)}'s</code>\n"
            f"👤 {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV}\n"
            f"🍸 {bot.bi('By')}: @Bl4ckD4ys ☁️"
        )
        bot.editMessage(message_id=mid, text=text) if mid else bot.replyMessage(text=text)

    except Exception as e:
        bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

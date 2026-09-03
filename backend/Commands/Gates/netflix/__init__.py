import os, time, threading
from Commands.Gates._template import waiting_bar, DIV
from . import netflix_core


def _load_proxies():
    """Convert Commands/Docs/proxy.txt (host:port:user:pass) to user:pass@host:port."""
    paths = [
        os.path.join('Commands', 'Docs', 'proxy.txt'),
        os.path.join('Commands', 'Docs', 'proxy2.txt'),
    ]
    for p in paths:
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read().splitlines()
        except Exception:
            continue
        out = []
        for line in raw:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) == 4:
                host, port, user, pwd = parts
                out.append(f'{user}:{pwd}@{host}:{port}')
            else:
                out.append(line)
        if out:
            return out
    return None


def gateCmd(bot, update, gestion):
    try:
        bot.sendAction(action='typing')
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        raw  = bot.cmd.args if len(bot.cmd.args) > 0 else (update.reply_to.text if update.reply_to is not None else '')

        if not raw:
            return bot.replyMessage(text=(
                f"{bot.bi('Netflix Gate')} [ 🍸 ]\n{DIV}\n"
                f"🍸 {bot.bi('Use')}: <code>/em cc|mm|yy|cvv</code>\n"
                f"💳 {bot.bi('Ejemplo')}: <code>/em 4111111111111111|12|2026|123</code>\n{DIV}\n"
                f"🍸 {bot.bi('Plan')}: Netflix Planes (MX) 🎬"
            ))

        # Standard gate guards: ban, chat mode, BIN-ban, credits, anti-abuse
        b = gestion.gates(user=user, chat=chat, text=raw, cmd=cmd, bot=bot)
        if not b['status']:
            return bot.replyMessage(text=b['text'])

        cc, binData = b['cc'], b['bin']
        cc_str = f"{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}"
        now  = time.time()
        edit = bot.replyMessage(text=waiting_bar(bot, 0, 'Netflix Plans', 'Netflix Gate'))

        stop, th = threading.Event(), None
        if edit is not None:
            def _spin():
                pcts, i = [15, 30, 45, 60, 75, 90], 0
                while not stop.is_set():
                    try: bot.editMessage(message_id=edit.message_id, text=waiting_bar(bot, pcts[i % len(pcts)], 'Netflix Plans', 'Netflix Gate'))
                    except Exception: pass
                    i += 1
                    stop.wait(1.4)
            th = threading.Thread(target=_spin, daemon=True)
            th.start()

        capsolver = os.getenv('CAPSOLVER_KEY', '')
        proxies   = _load_proxies()

        try:
            result = netflix_core.processNetflixFlow(cc_str, proxy=proxies, capsolver_key=capsolver, retries=0)
        except Exception as e:
            result = {'status': 'Error ⚠️', 'success': False, 'response': str(e)[:200], 'apiResponse': 'Error ⚠️'}
        finally:
            stop.set()
            if th is not None: th.join(timeout=2)

        mid = edit.message_id if edit is not None else None
        success = bool(result.get('success'))
        status  = result.get('apiResponse', 'Approved ✅' if success else 'Declined ❌')

        if not success:
            txt = f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>{result.get('response', 'Gate error')}</code>"
            return bot.editMessage(message_id=mid, text=txt) if mid else bot.replyMessage(text=txt)

        # Deduct 2 credits on live (specials gate type)
        if isinstance(b.get('credits'), int):
            gestion.commit("UPDATE users SET credits = %s WHERE user_id = %s",
                           (str(b['credits'] - 2), str(update.user_id)))

        card = (
            f"{bot.bi('Netflix Gate')} [ 🍸 ]\n{DIV}\n"
            f"🍸 {bot.bi('Card')}: <code>{cc_str}</code>\n"
            f"⚡ {bot.bi('Status')}: <code>{status}</code>\n"
            f"💳 {bot.bi('Gate')}: <code>Netflix Plans MX</code>\n{DIV}\n"
            f"📧 {bot.bi('Email')}: <code>{result.get('email', 'N/A')}</code>\n"
            f"🔑 {bot.bi('Password')}: <code>{result.get('password', 'N/A')}</code>\n{DIV}\n"
            f"🍸 {bot.bi('Info')}: <code>{binData['brand'].title()}</code> - <code>{binData['type'].title()}</code> - <code>{binData['level'].title()}</code>\n"
            f"🍸 {bot.bi('Bank')}: <code>{binData['bank'].title()}</code>\n"
            f"🍸 {bot.bi('Country')}: <code>{binData['country'].title()}</code> {binData.get('flag', '')}\n{DIV}\n"
            f"⚡ {bot.bi('T. Taken')}: <code>{round(time.time() - now, 1)}'s</code>\n"
            f"👤 {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV}\n"
            f"🍸 {bot.bi('By')}: @Bl4ckD4ys ☁️"
        )
        bot.editMessage(message_id=mid, text=card) if mid else bot.replyMessage(text=card)
    except Exception as e:
        bot.raise_post(str(e))

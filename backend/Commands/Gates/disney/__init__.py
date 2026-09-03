import os, time, threading, html as _html_mod
from Commands.Gates._template import waiting_bar, DIV
from . import disney_core


def gateCmd(bot, update, gestion):
    try:
        bot.sendAction(action='typing')
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        raw  = bot.cmd.args if len(bot.cmd.args) > 0 else (update.reply_to.text if update.reply_to is not None else '')

        if not raw:
            return bot.replyMessage(text=(
                f"{bot.bi('Disney+ Gate')} [ 🍸 ]\n{DIV}\n"
                f"🍸 {bot.bi('Use')}: <code>/ds cc|mm|yy|cvv</code>\n"
                f"💳 {bot.bi('Ejemplo')}: <code>/ds 4111111111111111|12|2026|123</code>\n{DIV}\n"
                f"🍸 {bot.bi('Plan')}: Disney+ Subscripción (MX) 🎬"
            ))

        b = gestion.gates(user=user, chat=chat, text=raw, cmd=cmd, bot=bot)
        if not b['status']:
            return bot.replyMessage(text=b['text'])

        cc, binData = b['cc'], b['bin']
        cc_str = f"{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}"
        now  = time.time()
        edit = bot.replyMessage(text=waiting_bar(bot, 0, 'Disney+ Plans', 'Disney+ Gate'))

        stop, th = threading.Event(), None
        if edit is not None:
            def _spin():
                pcts, i = [15, 30, 45, 60, 75, 90], 0
                while not stop.is_set():
                    try: bot.editMessage(message_id=edit.message_id, text=waiting_bar(bot, pcts[i % len(pcts)], 'Disney+ Plans', 'Disney+ Gate'))
                    except Exception: pass
                    i += 1
                    stop.wait(1.4)
            th = threading.Thread(target=_spin, daemon=True)
            th.start()

        capsolver = os.getenv('CAPSOLVER_KEY', '')
        result = None

        try:
            for _retry in range(3):
                proxy_dict = gestion.proxy()
                proxy = list(proxy_dict.values())[0].replace('http://', '') if proxy_dict else None
                try:
                    result = disney_core.processDisneyFlow(cc_str, proxy=proxy, capsolver_key=capsolver, retries=0)
                    if result.get('status') or result.get('success'):
                        break
                except Exception as e:
                    result = {'status': False, 'message': str(e)[:200]}
                if 'Forbidden' in str(result.get('message', '')):
                    continue
                break

            if result is None:
                result = {'status': False, 'message': 'No hay proxies disponibles'}
        finally:
            stop.set()
            if th is not None: th.join(timeout=2)

        mid = edit.message_id if edit is not None else None
        success = bool(result.get('success'))
        status  = result.get('apiResponse', 'Approved ✅' if success else 'Declined ❌')

        if not result.get('status', True) and not success:
            msg = _html_mod.escape(str(result.get('message', result.get('response', 'Gate error'))))
            txt = f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>{msg}</code>"
            return bot.editMessage(message_id=mid, text=txt) if mid else bot.replyMessage(text=txt)

        if not success:
            resp = _html_mod.escape(str(result.get('response', 'Declined'))[:120])
            txt = (
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n{DIV}\n"
                f"🍸 {bot.bi('Card')}: <code>{cc_str}</code>\n"
                f"⚡ {bot.bi('Status')}: <code>{status}</code>\n"
                f"💳 {bot.bi('Gate')}: <code>Disney+ Plans MX</code>\n{DIV}\n"
                f"🍸 {bot.bi('Raise')}: <code>{resp}</code>\n{DIV}\n"
                f"🍸 {bot.bi('Info')}: <code>{_html_mod.escape(binData['brand'].title())}</code> - <code>{_html_mod.escape(binData['type'].title())}</code> - <code>{_html_mod.escape(binData['level'].title())}</code>\n"
                f"🍸 {bot.bi('Bank')}: <code>{_html_mod.escape(binData['bank'].title())}</code>\n"
                f"🍸 {bot.bi('Country')}: <code>{_html_mod.escape(binData['country'].title())}</code> {binData.get('flag', '')}\n{DIV}\n"
                f"⚡ {bot.bi('T. Taken')}: <code>{round(time.time() - now, 1)}'s</code>\n"
                f"👤 {bot.bi('User')}: {update.username} [{_html_mod.escape(user['c_name'].title())}]\n{DIV}\n"
                f"🍸 {bot.bi('By')}: @Bl4ckD4ys ☁️"
            )
            return bot.editMessage(message_id=mid, text=txt) if mid else bot.replyMessage(text=txt)

        if isinstance(b.get('credits'), int):
            gestion.commit("UPDATE users SET credits = %s WHERE user_id = %s",
                           (str(b['credits'] - 2), str(update.user_id)))

        card = (
            f"{bot.bi('Disney+ Gate')} [ 🍸 ]\n{DIV}\n"
            f"🍸 {bot.bi('Card')}: <code>{cc_str}</code>\n"
            f"⚡ {bot.bi('Status')}: <code>{status}</code>\n"
            f"💳 {bot.bi('Gate')}: <code>Disney+ Plans MX</code>\n{DIV}\n"
            f"📧 {bot.bi('Email')}: <code>{result.get('email', 'N/A')}</code>\n"
            f"🔑 {bot.bi('Password')}: <code>{result.get('password', 'N/A')}</code>\n{DIV}\n"
            f"🍸 {bot.bi('Info')}: <code>{_html_mod.escape(binData['brand'].title())}</code> - <code>{_html_mod.escape(binData['type'].title())}</code> - <code>{_html_mod.escape(binData['level'].title())}</code>\n"
            f"🍸 {bot.bi('Bank')}: <code>{_html_mod.escape(binData['bank'].title())}</code>\n"
            f"🍸 {bot.bi('Country')}: <code>{_html_mod.escape(binData['country'].title())}</code> {binData.get('flag', '')}\n{DIV}\n"
            f"⚡ {bot.bi('T. Taken')}: <code>{round(time.time() - now, 1)}'s</code>\n"
            f"👤 {bot.bi('User')}: {update.username} [{_html_mod.escape(user['c_name'].title())}]\n{DIV}\n"
            f"🍸 {bot.bi('By')}: @Bl4ckD4ys ☁️"
        )
        bot.editMessage(message_id=mid, text=card) if mid else bot.replyMessage(text=card)
    except Exception as e:
        bot.raise_post(str(e))

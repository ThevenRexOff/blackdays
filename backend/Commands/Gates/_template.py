# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
"""
JILL_BOT — Gate template. Add a new gate in ~5 lines: write a `checker` and call run_gate.

    # Commands/Gates/mojito.py
    from Commands.Gates._template import run_gate

    def gateCmd(bot, update, gestion):
        def checker(cc, binData):
            ...
            return {'status': True, 'success': ok, 'response': msg}
        run_gate(bot, update, gestion, gateway='Stripe Auth', checker=checker)

Then register it in main.py:  bot.addCommand('mj', 'Commands.Gates.mojito:gateCmd')
and add a row in the `comandos` table (tipo='auth', gate='Stripe Auth').
"""
import time, threading, html as _html_mod

# Keep DIV exported — imported by mass.py and other modules
DIV      = "────────────────────"
_BAR_ON  = "▰"
_BAR_OFF = "▱"

_TYPE_ICONS = {
    'auths':    '🍸',
    'charged':  '🥃',
    'specials': '🍹',
    'ccn':      '🍷',
    'avs':      '🧉',
}

# ── JILL premium emoji design system ─────────────────────────────────────────
# NewsEmoji (animated=True) — animate for Premium viewers
_E_RAINBOW  = '<tg-emoji emoji-id="5103122966779004034">🌈</tg-emoji>'
_E_BOLT     = '<tg-emoji emoji-id="5456140674028019486">⚡️</tg-emoji>'
_E_ARROW    = '<tg-emoji emoji-id="5416117059207572332">➡️</tg-emoji>'
_E_CHART    = '<tg-emoji emoji-id="5246762912428603768">📉</tg-emoji>'
_E_MONITOR  = '<tg-emoji emoji-id="5282843764451195532">🖥</tg-emoji>'
_E_GLOBE    = '<tg-emoji emoji-id="5447410659077661506">🌐</tg-emoji>'
_E_CHECK    = '<tg-emoji emoji-id="5206607081334906820">✔️</tg-emoji>'
_E_DIV_UNIT = '<tg-emoji emoji-id="5084991328547242847">👤</tg-emoji>'
_E_DIV_DEAD = '<tg-emoji emoji-id="5120689786746570155">🚫</tg-emoji>'
# DecorationEmojiPack (video=True) — visible as premium for all users
_E_HDR_END  = '<tg-emoji emoji-id="5102628843676501227">👤</tg-emoji>'
_E_USER     = '<tg-emoji emoji-id="5103125230226768804">👤</tg-emoji>'

_E_RED      = '<tg-emoji emoji-id="5210952531676504517">🔴</tg-emoji>'
_JILL_DIV_OK   = _E_DIV_UNIT * 13   # approved
_JILL_DIV_DEAD = _E_DIV_DEAD  * 13  # declined / error


def waiting_bar(bot, percent: int, gateway: str, name: str, icon: str = '🍸') -> str:
    filled = min(max(percent, 0) // 10, 10)
    bar    = _BAR_ON * filled + _BAR_OFF * (10 - filled)
    return (
        f"{_E_RAINBOW}{bot.bi(name)} [ {icon} ]{_E_HDR_END}\n{_JILL_DIV_OK}\n"
        f"💳 {bot.bi('Gate')}: <code>{gateway}</code>\n"
        f"{_E_BOLT} {bot.bi('Status')}: <code>{bar} {percent}%</code>"
    )


def run_gate(bot, update, gestion, gateway: str, checker, animate: bool = True) -> None:
    try:
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        bot.sendAction(action='typing')
        args = bot.cmd.args if len(bot.cmd.args) > 0 else (update.reply_to.text if update.reply_to is not None else '')

        b = gestion.gates(user=user, chat=chat, text=args, cmd=cmd, bot=bot)
        if not b['status']:
            return bot.replyMessage(text=b['text'])

        cc, binData = b['cc'], b['bin']
        name = cmd['name'].title()
        icon = _TYPE_ICONS.get(cmd.get('type', 'charged'), '🍸')
        now  = time.time()
        edit = bot.replyMessage(text=waiting_bar(bot, 0, gateway, name, icon))

        stop, th = threading.Event(), None
        if animate and edit is not None:
            def _spin():
                pcts, i = [15, 30, 45, 60, 75, 90], 0
                while not stop.is_set():
                    try: bot.editMessage(message_id=edit.message_id, text=waiting_bar(bot, pcts[i % len(pcts)], gateway, name, icon))
                    except Exception: pass
                    i += 1
                    stop.wait(1.4)
            th = threading.Thread(target=_spin, daemon=True)
            th.start()

        try:
            result = checker(cc, binData)
        except Exception as e:
            result = {'status': False, 'raise': str(e)[:200]}
        finally:
            stop.set()
            if th is not None: th.join(timeout=2)

        mid = edit.message_id if edit is not None else None

        if not result.get('status'):
            raise_msg = _html_mod.escape(str(result.get('raise', 'Gate error')))
            txt = f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>{raise_msg}</code>"
            return bot.editMessage(message_id=mid, text=txt) if mid else bot.replyMessage(text=txt)

        is_success  = result.get('success', False)
        jdiv        = _JILL_DIV_OK if is_success else _JILL_DIV_DEAD
        status_line = f"Approved {_E_CHECK}" if is_success else f"Declined {_E_RED}"

        # Strip redundant status prefix from response text (e.g. "Approved ✅ | Free trial")
        resp = result.get('response', '')
        for pfx in ('Approved ✅ | ', 'Declined ❌ | '):
            if resp.startswith(pfx):
                resp = resp[len(pfx):]
                break
        if resp in ('Approved ✅', 'Declined ❌', ''):
            resp = ''
        resp_line = f"{_E_ARROW} {bot.bi('Response')}: <code>{_html_mod.escape(resp)}</code>\n" if resp else ''

        # Optional country tag for gates that return a 2-letter country_code
        country_code = result.get('country_code', '')
        ctag = f" [ {bot.bi(country_code)} ]" if country_code else ''

        gate_type = b.get('gate_type', 'charged')
        cost      = b.get('cost', 0)
        if is_success and cost > 0 and isinstance(b.get('credits'), int):
            gestion.commit("UPDATE users SET credits = %s WHERE user_id = %s",
                           (str(b['credits'] - cost), str(update.user_id)))

        card = (
            f"{_E_RAINBOW}{bot.bi(name)}{ctag} [ {icon} ]{_E_HDR_END}\n{jdiv}\n"
            f"{icon} {bot.bi('Card')}: <code>{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}</code>\n"
            f"{_E_BOLT} {bot.bi('Status')}: {status_line}\n"
            f"{resp_line}"
            f"💳 {bot.bi('Gate')}: <code>{gateway}</code>\n{jdiv}\n"
            f"{_E_CHART} {bot.bi('Info')}: <code>{_html_mod.escape(binData['brand'].title())}</code> - <code>{_html_mod.escape(binData['type'].title())}</code> - <code>{_html_mod.escape(binData['level'].title())}</code>\n"
            f"{_E_MONITOR} {bot.bi('Bank')}: <code>{_html_mod.escape(binData['bank'].title())}</code>\n"
            f"{_E_GLOBE} {bot.bi('Country')}: <code>{_html_mod.escape(binData['country'].title())}</code> {binData.get('flag', '')}\n{jdiv}\n"
            f"{_E_BOLT} {bot.bi('T. Taken')}: <code>{round(time.time() - now, 1)}'s</code>\n"
            f"{_E_USER} {bot.bi('User')}: {update.username} [{_html_mod.escape(user['c_name'].title())}]\n{jdiv}"
        )
        bot.editMessage(message_id=mid, text=card) if mid else bot.replyMessage(text=card)
    except Exception as e:
        bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

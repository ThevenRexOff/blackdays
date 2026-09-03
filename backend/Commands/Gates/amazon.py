# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time, threading, html as _html_mod
from Commands.Gates._template import waiting_bar, DIV
from Commands.Gates.mamazon import CookieContext

_GATEWAY = 'Amazon'


def _run_flow(cc_str, cookie):
    """Run the Amazon billing flow once and normalise the result to the shape the
    handlers below expect. Returns (status, response) where status is
    'Approved ✅' | 'Declined ❌' | 'Error ⚠️'."""
    try:
        r = CookieContext(card=cc_str, cookie=cookie).buildFlowBilling()
    except Exception as e:
        return 'Error ⚠️', str(e)[:200]
    if not r.get('status'):
        # flow ran to end but Amazon response not in known patterns
        if 'apiResponse' in r:
            return r.get('apiResponse', 'Error ⚠️'), r.get('response', 'Unknown Amazon response')
        return 'Error ⚠️', r.get('message', 'Gate error')
    return r.get('apiResponse', 'Error ⚠️'), r.get('response', '')


def gateCmd(bot, update, gestion):
    try:
        bot.sendAction(action='typing')
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        args = bot.cmd.args if len(bot.cmd.args) > 0 else (update.reply_to.text if update.reply_to is not None else '')

        if user['ban'] == 'true':
            return bot.replyMessage(text=f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>You are banned from this bot!</code>")

        ck = gestion.cookie_verify(str(update.user_id))
        if not ck['status']:
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>{_html_mod.escape(str(ck.get('raise', 'No cookie')))}</code>\n"
                f"🍸 {bot.bi('Fix')}: <code>/cookie your_amazon_cookie</code>"
            ))

        if not args:
            return bot.replyMessage(text=f"{bot.bi('Amazon')} [ 🍸 ]\n🍸 {bot.bi('Use')}: <code>/amz cc|mm|yy|cvv</code>")

        b = gestion.gates(user=user, chat=chat, text=args, cmd=cmd, bot=bot)
        if not b['status']:
            return bot.replyMessage(text=b['text'])

        cc, binData = b['cc'], b['bin']
        cc_str = f"{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}"
        cookie = ck['response']
        now    = time.time()
        edit   = bot.replyMessage(text=waiting_bar(bot, 0, _GATEWAY, 'Amazon'))

        stop, th = threading.Event(), None
        if edit is not None:
            def _spin():
                pcts, i = [15, 30, 45, 60, 75, 90], 0
                while not stop.is_set():
                    try: bot.editMessage(message_id=edit.message_id, text=waiting_bar(bot, pcts[i % len(pcts)], _GATEWAY, 'Amazon'))
                    except Exception: pass
                    i += 1
                    stop.wait(1.4)
            th = threading.Thread(target=_spin, daemon=True)
            th.start()

        try:
            status, response = _run_flow(cc_str, cookie)
        finally:
            stop.set()
            if th is not None: th.join(timeout=2)

        mid = edit.message_id if edit is not None else None

        # Approved / Declined are successful runs; anything else is a gate error
        if status not in ('Approved ✅', 'Declined ❌'):
            txt = f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>{_html_mod.escape(str(response or 'Gate error'))}</code>"
            return bot.editMessage(message_id=mid, text=txt) if mid else bot.replyMessage(text=txt)

        # Deduct 2 credits on live (specials gate type)
        if status == 'Approved ✅' and isinstance(b.get('credits'), int):
            gestion.commit("UPDATE users SET credits = %s WHERE user_id = %s",
                           (str(b['credits'] - 2), str(update.user_id)))

        card = (
            f"{bot.bi('Amazon')} [ 🍸 ]\n{DIV}\n"
            f"🍸 {bot.bi('Card')}: <code>{cc_str}</code>\n"
            f"⚡ {bot.bi('Status')}: <code>{status}</code>\n"
            f"🍸 {bot.bi('Response')}: <code>{_html_mod.escape(str(response))}</code>\n"
            f"💳 {bot.bi('Gate')}: <code>{_GATEWAY}</code>\n{DIV}\n"
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


def run_check(cc, bin_data, ctx=None):
    """Single-card checker for /mass. `ctx` carries {'cookie': <amazon cookie>}.
    Returns {'status': 'Approved ✅'|'Declined ❌'|'Error ⚠️', 'response': ...}."""
    cookie = (ctx or {}).get('cookie')
    if not cookie:
        return {'status': 'Error ⚠️', 'response': 'No Amazon cookie (use /cookie)'}
    cc_str = f"{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}"
    status, response = _run_flow(cc_str, cookie)
    return {'status': status, 'response': response}

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time
from Model.libs.__vr.Flexxe import analyze
from Commands.jill import *


def check(url: str) -> dict:
    """Full technology fingerprint."""
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        r = analyze(url)
        if 'processors' not in r:
            return {'status': False, 'raise': r.get('error', 'Could not analyze site')}
        return r
    except Exception as e:
        return {'status': False, 'raise': str(e)[:120]}


def cmdSite(bot, update, gestion) -> None:
    try:
        now  = time.time()
        args = bot.cmd.args.strip() if bot.cmd.args.strip() else (update.reply_to.text.strip() if update.reply_to else '')
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        bot.sendAction(action='typing')
        if user['ban'] != 'false':
            return bot.replyMessage(text=error('You are banned from this bot!'))
        if chat['rango'] not in gestion.prem:
            return bot.replyMessage(text=error('This Chat Is Not Authorized!'))
        if cmd['status'] == 'unval':
            return bot.replyMessage(text=error('This command is not yet registered!'))
        if cmd['mode'] == 'ma':
            return bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
        if cmd['mode'] == 'of':
            return bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
        if not args:
            return bot.replyMessage(text=error(f"Use: /{cmd['command']} {cmd['use']}"))

        edit = bot.replyMessage(text=f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_BOLT} ]{E_HDR_END}\n{E_BOLT} {bot.bi('Status')}: <code>Analyzing...</code>")
        a = check(args)

        if not a.get('status') and 'processors' not in a:
            return bot.editMessage(message_id=edit.message_id, text=error(a.get('raise', 'Could not analyze site')))

        _fmt = lambda lst: ', '.join(f"<code>{i}</code>" for i in (lst or ['Not Found!']))
        bot.editMessage(message_id=edit.message_id, text=(
            f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_GLOBE} {bot.bi('Site')}: <code>{a.get('url', args)}</code>\n"
            f"{E_MONITOR} {bot.bi('IP')}: <code>{a.get('ip', 'N/A')}</code>\n"
            f"{E_LETTER} {bot.bi('Server')}: <code>{a.get('server', 'N/A')}</code>\n"
            f"💳 {bot.bi('Gateways')}: {_fmt(a.get('processors'))}\n"
            f"🛒 {bot.bi('E-Commerce')}: {_fmt(a.get('ecommerce'))}\n"
            f"🛡 {bot.bi('Securities')}: {_fmt(a.get('securities'))}\n{DIV_STARS}\n"
            f"{E_BOLT} {bot.bi('T. Taken')}: <code>{round(time.time()-now, 1)}'s</code>\n"
            f"{E_USER} {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV_STARS}"
        ))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

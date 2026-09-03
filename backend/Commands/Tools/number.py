# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time
from Model.libs.__phone import phoneLookup
from Commands.jill import *


def cmdNm(bot, update, gestion) -> None:
    try:
        now  = time.time()
        args = bot.cmd.args.strip()
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        bot.sendAction(action='typing')
        if user['ban'] == 'false':
            if chat['rango'] in gestion.prem:
                if cmd['status'] != 'unval':
                    if cmd['mode'] == 'on':
                        if args:
                            edit = bot.replyMessage(text=f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_BOLT} ]{E_HDR_END}\n{E_BOLT} {bot.bi('Status')}: <code>Fetching Data_</code>")
                            r = phoneLookup(args).run()
                            if r.status:
                                bot.editMessage(message_id=edit.message_id, text=(
                                    f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                                    f"{E_LETTER} {bot.bi('Number')}: <code>{r.international_format}</code>\n"
                                    f"{E_LETTER} {bot.bi('Local')}: <code>{r.local_format}</code>\n"
                                    f"{E_GLOBE} {bot.bi('Country')}: <code>{r.country_name} ({r.country_code}) {r.country_prefix}</code>\n"
                                    f"{E_LETTER} {bot.bi('Location')}: <code>{r.location}</code>\n"
                                    f"{E_MONITOR} {bot.bi('Carrier')}: <code>{r.carrier}</code>\n"
                                    f"{E_LETTER} {bot.bi('Line Type')}: <code>{r.line_type}</code>\n{DIV_STARS}\n"
                                    f"{E_BOLT} {bot.bi('T. Taken')}: <code>{round(time.time()-now, 1)}'s</code>\n"
                                    f"{E_USER} {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV_STARS}"
                                ))
                            else:
                                bot.editMessage(message_id=edit.message_id, text=error(r.message))
                        else:
                            bot.replyMessage(text=error(f"Use: /{cmd['command']} {cmd['use']}"))
                    elif cmd['mode'] == 'ma': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                    elif cmd['mode'] == 'of': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                else: bot.replyMessage(text=error('This command is not yet registered!'))
            else: bot.replyMessage(text=error('This Chat Is Not Authorized!'))
        else: bot.replyMessage(text=error('You are banned from this bot!'))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

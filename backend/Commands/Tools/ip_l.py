# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time
from Model.libs.__ip import ipLookup
from Commands.jill import *


def cmdIp(bot, update, gestion) -> None:
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
                            r = ipLookup(args).run()
                            if r.status:
                                vpn  = f'Yes {E_CHECK}' if r.is_vpn   else f'No {E_RED}'
                                prxy = f'Yes {E_CHECK}' if r.is_proxy else f'No {E_RED}'
                                srv  = f'Yes {E_CHECK}' if r.is_server else f'No {E_RED}'
                                bot.editMessage(message_id=edit.message_id, text=(
                                    f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                                    f"{E_GLOBE} {bot.bi('IP')}: <code>{r.ip}</code>\n"
                                    f"{E_MONITOR} {bot.bi('ISP')}: <code>{r.carrier}</code>\n"
                                    f"{E_MONITOR} {bot.bi('Org')}: <code>{r.org}</code>\n"
                                    f"{E_LETTER} {bot.bi('ASN')}: <code>{r.asn}</code>\n{DIV_STARS}\n"
                                    f"{E_GLOBE} {bot.bi('Country')}: <code>{r.country}</code>\n"
                                    f"{E_LETTER} {bot.bi('State')}: <code>{r.state}</code> | {bot.bi('City')}: <code>{r.city}</code>\n"
                                    f"{E_LETTER} {bot.bi('Postal')}: <code>{r.postal_code}</code>\n"
                                    f"{E_LETTER} {bot.bi('Coords')}: <code>{r.coordinates}</code>\n"
                                    f"{E_LETTER} {bot.bi('Timezone')}: <code>{r.timezone}</code>\n{DIV_STARS}\n"
                                    f"{E_BOLT} {bot.bi('Risk')}: <code>{r.risk} [{r.score}]</code>\n"
                                    f"{E_LETTER} {bot.bi('VPN')}: <code>{vpn}</code> | {bot.bi('Proxy')}: <code>{prxy}</code> | {bot.bi('Server')}: <code>{srv}</code>\n{DIV_STARS}\n"
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

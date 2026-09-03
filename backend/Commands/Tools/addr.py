# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time
from Model.libs.__addr import AddrGenerator
from Commands.jill import *

_COUNTRIES = 'US, MX, CA, BR, IT, AU, JP, UK, DE, FR, ES'


def fake(query: str) -> dict:
    """Wrapper kept for backward compat with rg_fake callback."""
    parts   = query.strip().split()
    country = parts[0].upper() if parts else 'US'
    r = AddrGenerator.generate(country, 1)
    if not r.status:
        return {'status': False}
    a = r.results[0]
    return {'status': True, 'response': {
        'f_name':  a['name'].split()[0] if a['name'] else '?',
        'l_name':  ' '.join(a['name'].split()[1:]) if a['name'] else '?',
        'gender':  'N/A',
        'mail':    a['email'],
        'phone':   a['phone'],
        'country': a['country'],
        'state':   a['state'],
        'city':    a['city'],
        'zipcode': a['zip'],
        'street':  a['street'],
    }}


def cmdAddr(bot, update, gestion) -> None:
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
                            parts   = args.split()
                            country = parts[0].upper()
                            try:    amount = min(int(parts[1]), 5) if len(parts) > 1 else 1
                            except: amount = 1
                            edit = bot.replyMessage(text=f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_BOLT} ]{E_HDR_END}\n{E_BOLT} {bot.bi('Status')}: <code>Generating Addresses_</code>")
                            r = AddrGenerator.generate(country, amount)
                            if r.status:
                                btn1 = bot.addButton(text='𝗥𝗘 𝗚𝗘𝗡', callback='rg_fake')
                                btn2 = bot.addButton(text='𝗖𝗟𝗘𝗔𝗡 𝗤𝗨𝗘𝗥𝗬', callback='clean')
                                buttons = bot.replyMarkup(bot.addRow(btn1, btn2))
                                lines = []
                                for i, a in enumerate(r.results, 1):
                                    pfx = f"[{i}] " if amount > 1 else ''
                                    lines.append(
                                        f"\n{pfx}{E_LETTER} {bot.bi('Name')}: <code>{a['name']}</code>\n"
                                        f"{E_LETTER} {bot.bi('Email')}: <code>{a['email']}</code>\n"
                                        f"{E_LETTER} {bot.bi('Phone')}: <code>{a['phone']}</code>\n"
                                        f"{E_LETTER} {bot.bi('Address')}: <code>{a['street']}</code>\n"
                                        f"{E_LETTER} {bot.bi('City')}: <code>{a['city']}</code> | {bot.bi('State')}: <code>{a['state']}</code>\n"
                                        f"{E_LETTER} {bot.bi('Zip')}: <code>{a['zip']}</code> | {bot.bi('Country')}: <code>{r.flag} {r.country}</code>"
                                    )
                                body = '\n'.join(lines)
                                bot.editMessage(message_id=edit.message_id, reply_markup=buttons, text=(
                                    f"{E_RAINBOW}{bot.bi(cmd['name'].title())} ({r.flag} {r.country}) [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}"
                                    f"{body}\n\n{DIV_STARS}\n"
                                    f"{E_BOLT} {bot.bi('T. Taken')}: <code>{round(time.time()-now, 1)}'s</code>\n"
                                    f"{E_USER} {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV_STARS}"
                                ))
                            else:
                                bot.editMessage(message_id=edit.message_id, text=error(r.message))
                        else:
                            bot.replyMessage(text=error(f"Use: /{cmd['command']} country [amount]\nCountries: {_COUNTRIES}"))
                    elif cmd['mode'] == 'ma': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                    elif cmd['mode'] == 'of': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                else: bot.replyMessage(text=error('This command is not yet registered!'))
            else: bot.replyMessage(text=error('This Chat Is Not Authorized!'))
        else: bot.replyMessage(text=error('You are banned from this bot!'))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

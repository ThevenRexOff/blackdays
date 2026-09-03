# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time, psycopg2, requests
from Commands.Tools.binc import lookup
from Commands.jill import *

_EXTRAS_LINK = "https://infernoproject.xyz/ghidorah/ghidorah.php?q="
_ENCRYPT_URL = "https://infernoproject.xyz/PHP/encrypt.php?card="


def link_ac(message:str, bot) -> str:
    try: return _EXTRAS_LINK + requests.get(f'{_ENCRYPT_URL}{message}').text
    except Exception as a:
        bot.raise_post(str(a))
        return 'erroramigo'


def extra(_bin:str, bot) -> dict:
    try:
        db = '15 Millons!'
        with psycopg2.connect(host='ghidorah.cer3hzdxunqw.us-east-1.rds.amazonaws.com', dbname='ghidorah_bot', user='quetzal', password='Asteroide') as connect:
            cursor = connect.cursor()
            cursor.execute("SELECT cc FROM public.ccs WHERE bin=%s", (_bin,))
            cards = cursor.fetchall()
            if len(cards) > 0:
                u = []
                p = []
                for i in cards:
                    i = i[0].rstrip()
                    if i.split('|')[0] not in u:
                        u.append(i.split('|')[0])
                        p.append(i)
                if len(p) > 15:
                    return {'status':True, 'link':True, 'link_r':link_ac(message=_bin, bot=bot), 'count':str(len(p)), 'db':db}
                else:
                    extras_html = ''.join([f"{E_LETTER} <code>{i}</code>\n" for i in p])
                    return {'status':True, 'link':False, 'extras':extras_html, 'count':str(len(p)), 'db':db}
            else: return {'status':False}
    except Exception as a:
        bot.raise_post(str(a))
        return {'status':False}


def cmdExtra(bot, update, gestion) -> None:
    try:
        now  = time.time()
        args = bot.cmd.args if len(bot.cmd.args) > 0 else (update.reply_to.text if update.reply_to is not None else bot.cmd.args)
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        bot.sendAction(action='typing')
        if user['ban'] == 'false':
            if chat['rango'] in gestion.prem:
                if cmd['status'] != 'unval':
                    if cmd['mode'] == 'on' or chat['rango'].lower() == 'owner':
                        m1 = bot.replyMessage(text=f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_BOLT} ]{E_HDR_END}\n{E_BOLT} {bot.bi('Status')}: <code>Fetching Extras_</code>")
                        if len(args) >= 6:
                            try:
                                a = lookup(text=args)
                                if a['status'] and args != '000000':
                                    a   = a['response']
                                    ccs = extra(_bin=a['bin'], bot=bot)
                                    if ccs['status']:
                                        base_card = (
                                            f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                                            f"{E_LETTER} {bot.bi('Bin')}: <code>{a['bin']}</code> {a['flag']}\n"
                                            f"{E_BOLT} {bot.bi('Status')}: Found {E_CHECK}\n{DIV_STARS}\n"
                                            f"{E_CHART} {bot.bi('Info')}: <code>{a['brand'].title()}</code> - <code>{a['type'].title()}</code> - <code>{a['level'].title()}</code>\n"
                                            f"{E_MONITOR} {bot.bi('Bank')}: <code>{a['bank'].title()}</code>\n"
                                            f"{E_GLOBE} {bot.bi('Country')}: <code>{a['country'].title()}</code> - <code>{a['currency'].title()}</code>\n{DIV_STARS}\n"
                                            f"{E_LETTER} {bot.bi('Count')}: <code>{ccs['count']} Extras!</code>\n"
                                            f"{E_LETTER} {bot.bi('In Db')}: <code>{ccs['db']}</code>\n{DIV_STARS}\n"
                                            f"{E_BOLT} {bot.bi('T. Taken')}: <code>{str(round((time.time() - now), 1))}'s</code>\n"
                                            f"{E_USER} {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV_STARS}"
                                        )
                                        if ccs['link']:
                                            btn1 = bot.addButton(text='𝗘𝗫𝗧𝗥𝗔𝗦', url=ccs['link_r'])
                                            btn2 = bot.addButton(text='𝗖𝗟𝗘𝗔𝗡 𝗤𝗨𝗘𝗥𝗬', callback='clean')
                                            buttons = bot.replyMarkup(bot.addRow(btn1), bot.addRow(btn2))
                                            bot.editMessage(message_id=m1.message_id, text=base_card, reply_markup=buttons)
                                        else:
                                            btn2 = bot.addButton(text='𝗖𝗟𝗘𝗔𝗡 𝗤𝗨𝗘𝗥𝗬', callback='clean')
                                            buttons = bot.replyMarkup(bot.addRow(btn2))
                                            bot.editMessage(message_id=m1.message_id, text=base_card + f"\n{ccs['extras']}", reply_markup=buttons)
                                    else: bot.editMessage(message_id=m1.message_id, text=error('No Extras Fetch!'))
                                else: bot.editMessage(message_id=m1.message_id, text=error('Enter a message with a correct BIN!'))
                            except Exception as a: bot.raise_post(str(a))
                        else: bot.editMessage(message_id=m1.message_id, text=error(f"Use: /{cmd['command']} {cmd['use']}"))
                    elif cmd['mode'] == 'ma': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                    elif cmd['mode'] == 'of': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                else: bot.replyMessage(text=error('This command is not yet registered!'))
            else: bot.replyMessage(text=error('This Chat Is Not Authorized!'))
        else: bot.replyMessage(text=error('You are banned from this bot!'))
    except Exception as a: bot.raise_post(str(a))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

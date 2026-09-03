# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time, luhn, random, datetime
from Commands.Tools.binc import lookup
from Commands.jill import *


def gen(_bin:list) -> dict:
    YEARS = ["2023", "2024", "2025", "2026", "2027", "2028", "2029"]
    MES   = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    GEN   = []
    UNR   = []
    while len(GEN) <= 10:
        mes  = _bin[1] if _bin[1].isdigit() else random.choice(MES)
        year = _bin[2] if _bin[2].isdigit() else random.choice(YEARS)
        cc   = ''.join(i if i.isdigit() else str(random.randint(0, 9)) for i in _bin[0])
        cvv  = ''.join(i if i.isdigit() else str(random.randint(0, 9)) for i in _bin[3])
        if luhn.verify(cc) and cc not in UNR:
            UNR.append(cc)
            GEN.append(f"{cc}|{mes}|{year}|{cvv}")
    ccs = ''.join(f"{E_LETTER} <code>{i}</code>\n" for i in GEN)
    return {'status': True, 'response': ccs}


def array(text:str, bot) -> dict:
    try:
        year  = datetime.datetime.now().year
        longs = {'2':16, '3':15, '4':16, '5':16, '6':16}
        cvvs  = {'2':3, '3':4, '4':3, '5':3, '6':3}
        _gen  = ['', '', '', '']
        data  = ''
        for i in text:
            data += i if i.isdigit() or i == 'x' else ' '
        data = [i for i in data.split(' ') if i]
        for i in data:
            if len(i) >= 6 and _gen[0] == '':
                _gen[0] = i
            elif len(i) == 2 or i == 'xx':
                if i.isdigit():
                    if int(i) <= 12 and _gen[1] == '':
                        _gen[1] = i
                    elif int(i) >= int(str(year)[2:]) and int(i) <= int(str((year + 10))[2:]) and _gen[2] == '':
                        _gen[2] = f"20{i}"
                else:
                    _gen[1] = i
            elif len(i) == 1 or i == 'x':
                if i == 'x' and _gen[1] == '':
                    _gen[1] = 'xx'
                elif i.isdigit() and int(i) <= 12 and _gen[1] == '':
                    _gen[1] = f"0{i}"
            elif len(i) == 4 or i == 'xxxx':
                if i.isdigit():
                    if int(i) >= year and int(i) <= year + 10 and _gen[2] == '':
                        _gen[2] = i
                    elif int(i) >= int(str(year)[2:]) and int(i) <= int(str((year + 10))[2:]) and _gen[2] == '':
                        _gen[2] = i
                else:
                    if _gen[2] == '':
                        _gen[2] = i
            elif len(i) in [4,3] and _gen[3] == '':
                _gen[3] = i
        if len(data) > 0:
            cc  = _gen[0] if len(_gen[0]) == longs[_gen[0][0]] else f"{_gen[0]}{'x' * (longs[_gen[0][0]] - len(_gen[0]))}"
            mes = _gen[1] if len(_gen[1]) in [2] or _gen[1].isdigit() else 'xx'
            año = _gen[2] if len(_gen[2]) in [2, 4] or _gen[2].isdigit() else 'xxxx'
            cvv = _gen[3] if len(_gen[3]) == cvvs[_gen[0][0]] or _gen[3].isdigit() else 'x' * cvvs[_gen[0][0]]
            if cc.isdigit() and mes.isdigit() and año.isdigit() and cvv.isdigit():
                return {'status':False, 'raise':'use a extrapolate cc'}
            else:
                if len(cc) == longs[cc[0]]:
                    if año == 'xxxx':
                        return {'status':True, 'gen':f"{cc}|{mes}|{año}|{cvv}"}
                    else:
                        if mes == 'xx':
                            return {'status':True, 'gen':f"{cc}|{mes}|{año}|{cvv}"}
                        else:
                            date = datetime.datetime(int(año), int(mes), 28)
                            if date >= datetime.datetime.now():
                                return {'status':True, 'gen':f"{cc}|{mes}|{año}|{cvv}"}
                            else:
                                return {'status':False, 'raise':'use a correct date'}
                else:
                    return {'status':False, 'raise':'Insert a Correct Gen Bin'}
        else:
            return {'status':False, 'raise':'Insert a Correct Gen Bin'}
    except Exception as a:
        bot.raise_post(f"Error en parse_bin - {str(a)[0:300]}")
        return {'status':False, 'raise':'error in the code'}


def cmdGen(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        now  = time.time()
        args = bot.cmd.args if len(bot.cmd.args) > 0 else (update.reply_to.text if update.reply_to is not None else bot.cmd.args)
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        if user['ban'] == 'false':
            if chat['rango'] in gestion.prem:
                if cmd['status'] != 'unval':
                    if cmd['mode'] == 'on':
                        if len(args) > 0:
                            a = lookup(args)
                            if a['status']:
                                a = a['response']
                                if a['brand'].lower() in ['visa', 'mastercard', 'discover', 'american express']:
                                    diana = array(text=args, bot=bot)
                                    if diana['status']:
                                        darla   = gen(_bin=diana['gen'].split('|'))
                                        btn1    = bot.addButton(text='𝗥𝗘 𝗚𝗘𝗡', callback=f'rg_ccs {diana["gen"]}')
                                        btn2    = bot.addButton(text='𝗖𝗟𝗘𝗔𝗡 𝗤𝗨𝗘𝗥𝗬', callback='clean')
                                        buttons  = bot.replyMarkup(bot.addRow(btn1, btn2))
                                        buttons2 = bot.replyMarkup(bot.addRow(bot.addButton(text='𝗖𝗟𝗘𝗔𝗡 𝗤𝗨𝗘𝗥𝗬', callback='clean')))
                                        bot.replyMessage(reply_markup=buttons if len(bot.cmd.args) > 0 else buttons2, text=(
                                            f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                                            f"{E_LETTER} {bot.bi('Bin')}: <code>{diana['gen']}</code>\n"
                                            f"{E_LETTER} {bot.bi('Info')}: <code>{a['flag']}</code> - <code>{a['brand'].title()}</code> - <code>{a['type'].title()}</code> - <code>{a['level'].title()}</code> - <code>{a['bank'].title()}</code>\n\n"
                                            f"{darla['response']}\n"
                                            f"{E_BOLT} {bot.bi('T. Taken')}: <code>{str(round((time.time() - now), 1))}'s</code>\n"
                                            f"{E_USER} {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV_STARS}"
                                        ))
                                    else: bot.replyMessage(text=error(diana['raise'].title()))
                                else: bot.replyMessage(text=error('Only Support Visa, Master, Discover & Amex!'))
                            else: bot.replyMessage(text=error('Use a Correct Bin!'))
                        else: bot.replyMessage(text=error(f"Use: /gen {cmd['use']}"))
                    elif cmd['mode'] == 'ma': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                    elif cmd['mode'] == 'of': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                else: bot.replyMessage(text=error('This command is not yet registered!'))
            else: bot.replyMessage(text=error('This Chat Is Not Authorized!'))
        else: bot.replyMessage(text=error('You are banned from this bot!'))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

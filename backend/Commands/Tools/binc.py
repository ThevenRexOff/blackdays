import requests, time
from Commands.jill import *

_BIN_API   = 'https://jaimito.alwaysdata.net/Apis/bin.php'
_BIN_CACHE = {}


def lookup(text: str) -> dict:
    _bin = ''.join(i for i in text if i.isdigit())
    if len(_bin) < 6:
        return {'status': False}
    _bin6 = _bin[:6]
    if _bin6 in _BIN_CACHE:
        return _BIN_CACHE[_bin6]
    try:
        r = requests.get(url=f'{_BIN_API}?bin={_bin6}', timeout=10).json()
        if r.get('status') and r.get('brand'):
            result = {'status': True, 'response': {
                'bin':      r['bin'],
                'brand':    r['brand'].title(),
                'type':     r['type'].title(),
                'level':    r.get('level', 'N/A').title(),
                'bank':     (r.get('bank_name') or 'N/A').title(),
                'country':  r.get('country_name', 'N/A').title(),
                'flag':     r.get('flag', ''),
                'currency': r.get('iso2', 'N/A'),
            }}
        else:
            result = {'status': False}
        _BIN_CACHE[_bin6] = result
        return result
    except Exception:
        return {'status': False}


def cmdBin(bot, update, gestion) -> None:
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
                    if cmd['mode'] == 'on':
                        if len(args) >= 6:
                            a = lookup(text=args)
                            if a['status'] and args != '000000':
                                a = a['response']
                                bot.replyMessage(text=(
                                    f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                                    f"{E_LETTER} {bot.bi('Bin')}: <code>{a['bin']}</code> {a['flag']}\n"
                                    f"{E_BOLT} {bot.bi('Status')}: Found {E_CHECK}\n{DIV_STARS}\n"
                                    f"{E_CHART} {bot.bi('Info')}: <code>{a['brand']}</code> - <code>{a['type']}</code> - <code>{a['level']}</code>\n"
                                    f"{E_MONITOR} {bot.bi('Bank')}: <code>{a['bank']}</code>\n"
                                    f"{E_GLOBE} {bot.bi('Country')}: <code>{a['country']}</code> - <code>{a['currency']}</code>\n{DIV_STARS}\n"
                                    f"{E_BOLT} {bot.bi('T. Taken')}: <code>{str(round((time.time() - now), 1))}'s</code>\n"
                                    f"{E_USER} {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV_STARS}"
                                ))
                            else: bot.replyMessage(text=error("Enter a message with a correct BIN!"))
                        else: bot.replyMessage(text=error(f"Use: /bin {cmd['use']}"))
                    elif cmd['mode'] == 'ma': bot.replyMessage(text=error(f"Command in maintenance! ({gestion.modes[cmd['mode']]})"))
                    elif cmd['mode'] == 'of': bot.replyMessage(text=error(f"Command Offline! ({gestion.modes[cmd['mode']]})"))
                else: bot.replyMessage(text=error("This command is not yet registered."))
            else: bot.replyMessage(text=error("This Chat Is Not Authorized!"))
        else: bot.replyMessage(text=error("You are banned from this bot!"))
    except Exception as e: bot.raise_post(str(e))

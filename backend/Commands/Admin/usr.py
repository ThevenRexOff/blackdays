# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
from Commands.jill import *


def _user_info(db, gestion) -> str:
    if not db.get('status', True) is not False and not db.get('user_id'):
        return error('User not found!')
    is_plain  = db['rango'].lower() in gestion.rangos or db['rango'].lower() == 'free'
    days_line = '' if is_plain else f"{E_BOLT} {bi('Days')}: <code>{db['days']}</code>\n"
    return (
        f"{E_RAINBOW}{bi('User Information')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
        f"{E_USER} {bi('ID')}: <code>{db['user_id']}</code>\n"
        f"{E_LETTER} {bi('Status')}: <code>{db['c_name'].title()}</code>\n"
        f"💳 {bi('Credits')}: <code>{db['credits'].title()}</code>\n"
        f"{E_LETTER} {bi('Rank')}: <code>{db['rango'].title()}</code>\n"
        f"{E_BOLT} {bi('Spam')}: <code>{db['spam'].title()}</code>\n"
        f"{days_line}"
        f"{E_BOLT} {bi('Ban')}: <code>{db['ban'].title()}</code> | {E_LETTER} {bi('Warns')}: <code>{db['warns']}</code>\n"
        f"{E_BOLT} {bi('Last Chk')}: <code>{db['l_reg'].split(' ')[0]}</code>\n"
        f"{E_LETTER} {bi('Since')}: <code>{db['d_reg']}</code>\n{DIV_STARS}"
    )


def cmdUser(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'].lower() not in gestion.rangos:
            return
        bot.sendAction(action='typing')
        a = bot.replyMessage(text=loading())
        if update.reply_to is not None:
            target = gestion.view(user_id=update.reply_to.user_id)
            bot.editMessage(message_id=a.message_id, text=_user_info(target, gestion))
        elif len(bot.cmd.args) > 0:
            if bot.cmd.args.replace(' ', '').isdigit() or '-' in bot.cmd.args:
                target = gestion.view(user_id=bot.cmd.args.replace(' ', ''))
                bot.editMessage(message_id=a.message_id, text=_user_info(target, gestion))
            else:
                bot.editMessage(message_id=a.message_id, text=error('Insert Valid User ID.'))
        else:
            bot.editMessage(message_id=a.message_id, text=error('Reply to user or insert user id!'))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

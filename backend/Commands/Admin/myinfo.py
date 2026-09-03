from Commands.jill import *

def cmdMyInfo(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        a  = bot.replyMessage(text=loading())
        db = gestion.view(user_id=update.user_id)
        is_plain  = db['rango'].lower() in ('free', *gestion.rangos)
        days_line = '' if is_plain else f"{E_BOLT} {bi('Days Left')}: <code>{db['days']}</code>\n"
        bot.editMessage(message_id=a.message_id, text=(
            f"{E_RAINBOW}{bi('Your Information')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_LETTER} {bi('ID')}: <code>{db['user_id']}</code>\n"
            f"{E_LETTER} {bi('Status')}: <code>{db['c_name'].title()}</code>\n"
            f"{E_BOLT} {bi('Credits')}: <code>{db['credits'].title()}</code>\n"
            f"{days_line}"
            f"{E_BOLT} {bi('Ban')}: <code>{db['ban'].title()}</code> | {E_LETTER} {bi('Warns')}: <code>{db['warns']}</code>\n"
            f"{E_LETTER} {bi('Register')}: <code>{db['d_reg']}</code>\n{DIV_STARS}"
        ))
    except Exception as e: bot.raise_post(str(e))

from Commands.jill import *

def cmdCookie(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        db   = gestion.view(user_id=update.user_id)
        args = bot.cmd.args.strip()
        if db['ban'].lower() == 'true':
            return bot.replyMessage(text=error("You are banned from this bot!"))
        if not args:
            return bot.replyMessage(text=error(f"Use: /cookie your_cookie_here"))
        r = gestion.cookie_add(update.user_id, args)
        if r['status']:
            preview = args[:30] + '...' if len(args) > 30 else args
            bot.replyMessage(text=ok('Cookie Saved', ('Preview', preview)))
        else:
            bot.replyMessage(text=error(r['raise']))
    except Exception as e: bot.raise_post(str(e))


def cmdInfo(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        target = update.reply_to if update.reply_to else update
        db     = gestion.view(user_id=target.user_id)
        if db.get('status') is False:
            return bot.replyMessage(text=error('User not found!'))
        bot.replyMessage(text=(
            f"{E_RAINBOW}{bi('User Information')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_LETTER} {bi('ID')}: <code>{db['user_id']}</code>\n"
            f"{E_LETTER} {bi('Status')}: <code>{db['c_name'].title()}</code>\n"
            f"{E_BOLT} {bi('Credits')}: <code>{db['credits'].title()}</code>\n"
            f"{E_BOLT} {bi('Ban')}: <code>{db['ban'].title()}</code> | {E_LETTER} {bi('Warns')}: <code>{db['warns']}</code>\n"
            f"{E_LETTER} {bi('Register')}: <code>{db['d_reg']}</code>\n{DIV_STARS}"
        ))
    except Exception as e: bot.raise_post(str(e))

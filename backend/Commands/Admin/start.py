from Commands.jill import *

def cmdStart(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        bot.replyMessage(text=panel(
            'Hello Friend',
            ('See', 'Hello! I am JILL — a private checker by @Bl4ckD4ys.'),
            f"{E_LETTER} {bi('Commands')}: <code>/cmds to see everything.</code>",
        ))
    except Exception as e: bot.raise_post(str(e))

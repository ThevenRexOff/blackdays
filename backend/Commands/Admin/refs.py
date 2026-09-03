# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
from Commands.jill import *


def cmdRef(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['ban'].lower() == 'true':
            return bot.replyMessage(text=error('You are banned from this bot!'))
        bot.sendAction(action='typing')

        if not bot.refs_channel:
            return bot.replyMessage(text=error('References channel not configured (set REFS_CHANNEL).'))
        if update.reply_to is None:
            return bot.replyMessage(text=error('Reply to a message (screenshot/text) with /ref to publish it.'))

        uname  = (update.username or db.get('nombre') or str(update.user_id)).lstrip('@')
        header = (
            f"{E_RAINBOW}{bot.bi('Reference by')}: @{uname} [{db['c_name'].title()}]{E_HDR_END}\n{DIV_STARS}"
        )
        bot.sendMessage(text=header, chat_id=bot.refs_channel)
        bot.copyMessage(from_chat_id=update.chat_id, message_id=update.reply_to.message_id, to_chat_id=bot.refs_channel)

        markup = None
        if bot.refs_url:
            markup = bot.replyMarkup(bot.addRow(bot.addButton(text='📢 𝗥𝗲𝗳𝗲𝗿𝗲𝗻𝗰𝗲𝘀', url=bot.refs_url)))
        bot.replyMessage(text=ok('Reference Sent', ('Status', 'Published to the references channel')), reply_markup=markup)
    except Exception as e: bot.raise_post(str(e))


def cmdLinks(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        btns = []
        if bot.chat_url: btns.append(bot.addButton(text='💬 𝗖𝗵𝗮𝘁 𝗚𝗲𝗻𝗲𝗿𝗮𝗹', url=bot.chat_url))
        if bot.refs_url: btns.append(bot.addButton(text='📢 𝗥𝗲𝗳𝗲𝗿𝗲𝗻𝗰𝗶𝗮𝘀', url=bot.refs_url))
        markup = bot.replyMarkup(bot.addRow(*btns)) if btns else None
        extra  = '' if btns else f"\n{E_LETTER} {bot.bi('Raise')}: <code>No links configured yet (set CHAT_URL / REFS_URL).</code>"
        bot.replyMessage(text=(
            f"{E_RAINBOW}{bot.bi('Links')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_LETTER} {bot.bi('Join our official channels')}{extra}"
        ), reply_markup=markup)
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

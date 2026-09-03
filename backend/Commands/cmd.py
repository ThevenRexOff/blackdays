from Commands.jill import *

def cmdHelp(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        a = bot.replyMessage(text=loading('Fetching Keyboard'))
        btn1 = bot.addButton(text='𝗧𝗢𝗢𝗟𝗦',    callback='tools',  style='danger')
        btn2 = bot.addButton(text='𝗨𝗦𝗘𝗥',     callback='user',   style='primary')
        btn3 = bot.addButton(text='𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦', callback='gates',  style='success')
        buttons = bot.replyMarkup(bot.addRow(btn1, btn2), bot.addRow(btn3))
        bot.editMessage(
            message_id=a.message_id,
            text=(
                f"{E_RAINBOW}{bi('General Commands')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                f"{E_LETTER} {bi('Use')}: <code>Select a section from the keyboard below.</code>\n{DIV_STARS}"
            ),
            reply_markup=buttons
        )
    except Exception as e: bot.raise_post(str(e))

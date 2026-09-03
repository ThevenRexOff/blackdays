# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
from Commands.jill import *


def cmdBinBan(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion._rangos:
            return
        bot.sendAction(action='typing')
        args = bot.cmd.args.strip().split(' ', 1)

        if not args or not args[0]:
            total = gestion.count_banned_bins()
            return bot.replyMessage(text=(
                f"{E_RAINBOW}{bot.bi('BIN Ban System')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                f"{E_LETTER} <code>/binban add [BIN]</code> - Ban a BIN\n"
                f"{E_LETTER} <code>/binban del [BIN]</code> - Unban a BIN\n"
                f"{E_LETTER} <code>/binban list</code> - Show banned BINs\n"
                f"{E_LETTER} <code>/binban count</code> - Count banned BINs\n{DIV_STARS}\n"
                f"{E_BOLT} {bot.bi('Banned BINs')}: <code>{total}</code>"))

        action = args[0].lower()
        by     = update.username or str(update.user_id)

        if action == 'add':
            if len(args) < 2:
                return bot.replyMessage(text=error('Usage: /binban add [BIN]'))
            bin_num = args[1].strip()[:6]
            if len(bin_num) != 6 or not bin_num.isdigit():
                return bot.replyMessage(text=error('Invalid BIN! Must be 6 digits'))
            r = gestion.add_banned_bin(bin_num, added_by=str(update.user_id))
            if r['status']:
                bot.adminRegister('BIN Ban', bin_num)
                bot.replyMessage(text=ok('BIN Banned', ('BIN', bin_num), ('By', by)))
            elif r.get('reason') == 'already_banned':
                bot.replyMessage(text=error(f"BIN {bin_num} is already banned!"))
            else:
                bot.replyMessage(text=error(f"Failed to ban BIN: {r.get('reason', 'unknown')}"))

        elif action in ('del', 'remove', 'unban'):
            if len(args) < 2:
                return bot.replyMessage(text=error('Usage: /binban del [BIN]'))
            bin_num = args[1].strip()[:6]
            if len(bin_num) != 6 or not bin_num.isdigit():
                return bot.replyMessage(text=error('Invalid BIN! Must be 6 digits'))
            r = gestion.remove_banned_bin(bin_num)
            if r['status']:
                bot.adminRegister('BIN Unban', bin_num)
                bot.replyMessage(text=ok('BIN Unbanned', ('BIN', bin_num), ('By', by)))
            elif r.get('reason') == 'not_banned':
                bot.replyMessage(text=error(f"BIN {bin_num} is not banned!"))
            else:
                bot.replyMessage(text=error(f"Failed to unban BIN: {r.get('reason', 'unknown')}"))

        elif action in ('count', 'stats'):
            bot.replyMessage(text=ok('BIN Statistics', ('Total Banned', gestion.count_banned_bins())))

        elif action == 'list':
            total = gestion.count_banned_bins()
            d     = gestion.list_banned_bins(limit=20)
            if d['status'] and d['data']:
                lines = '\n'.join(f"{E_LETTER} <code>{b[0]}</code> — by <code>{b[2] or 'N/A'}</code> ({b[3]})" for b in d['data'])
                bot.replyMessage(text=(
                    f"{E_RAINBOW}{bot.bi('Banned BINs')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                    f"{E_BOLT} {bot.bi('Total')}: <code>{total}</code>\n{DIV_STARS}\n{lines}"))
            else:
                bot.replyMessage(text=ok('Banned BINs', ('Status', 'No BINs banned yet!')))

        else:
            bot.replyMessage(text=error('Use: add | del | list | count'))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

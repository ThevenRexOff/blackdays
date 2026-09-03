# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time
from Commands.jill import *


def cmdBroadcast(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] != 'owner':
            return
        bot.sendAction(action='typing')
        msg = bot.cmd.args.strip()
        if not msg:
            return bot.replyMessage(text=error(f"Use: /broadcast your message"))

        uids = gestion.all_user_ids()
        a = bot.replyMessage(text=(
            f"{E_RAINBOW}{bot.bi('Broadcast')} [ {E_BOLT} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_LETTER} {bot.bi('Targets')}: <code>{len(uids)}</code>\n"
            f"{E_BOLT} {bot.bi('Status')}: <code>Sending... 🟨</code>"))

        sent = failed = 0
        for uid in uids:
            try:
                r = bot.sendMessage(text=msg, chat_id=uid)
                if r and getattr(r, 'message_id', None): sent += 1
                else: failed += 1
            except Exception:
                failed += 1
            time.sleep(0.05)

        bot.editMessage(message_id=a.message_id, text=ok(
            'Broadcast Done',
            ('Sent', sent),
            ('Failed', failed),
            ('Total', len(uids)),
        ))
        bot.adminRegister('Broadcast', detail=f'{sent} sent / {failed} failed')
    except Exception as e: bot.raise_post(str(e))


def cmdGusers(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion.rangos:
            return
        bot.sendAction(action='typing')
        s = gestion.user_stats()
        bot.replyMessage(text=panel(
            'Users Stats',
            ('Total', s['total']),
            ('Free', s['free']),
            ('Premium', s['premium']),
            ('Staff', s['staff']),
            ('Banned', s['banned']),
        ))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

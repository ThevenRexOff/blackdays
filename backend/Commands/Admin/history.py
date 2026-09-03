# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
from Commands.jill import *
import html as _html_mod


def cmdHistory(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion.rangos:
            return
        bot.sendAction(action='typing')
        target = bot.cmd.args.strip().split('|')[0].strip() or None
        events = gestion.list_events(target=target, limit=15)
        if not events:
            return bot.replyMessage(text=ok('Event History', ('Status', 'No events recorded yet')))
        lines = ''
        for at, actor, action, tgt, detail in events:
            line  = f"{E_BOLT} <code>{at}</code> · {_html_mod.escape(str(actor))} · {bot.bi(action)}"
            if tgt:    line += f" → <code>{_html_mod.escape(str(tgt))}</code>"
            if detail: line += f"\n   {E_LETTER} <code>{_html_mod.escape(str(detail))}</code>"
            lines += line + "\n"
        head = bot.bi('Event History') + (f" · {target}" if target else "")
        bot.replyMessage(text=(
            f"{E_RAINBOW}{head} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{lines}{DIV_STARS}\n"
            f"{E_LETTER} {bot.bi('Filter')}: <code>/history uid</code>"
        ))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

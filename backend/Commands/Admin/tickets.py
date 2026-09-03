# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
from Commands.jill import *
import html as _html_mod

_STATUS = {'pending': 'Pendiente ⏳', 'open': 'Abierto 🔧', 'closed': 'Cerrado ✅'}


def _status(s: str) -> str:
    return _STATUS.get((s or 'pending').lower(), s or 'Pendiente')


def _card(bot, t: dict, created: bool = False) -> str:
    folio = f"#{int(t['id']):06d}"
    title = f"Ticket {folio} — Created {E_CHECK}" if created else f"Ticket {folio}"
    return (
        f"{E_RAINBOW}{bot.bi(title)} [ 🎫 ]{E_HDR_END}\n{DIV_STARS}\n"
        f"{E_USER} {bot.bi('User')}: @{_html_mod.escape(str(t['username'] or t['user_id']))}\n"
        f"{E_LETTER} {bot.bi('Problem')}: {_html_mod.escape(str(t['problem']))}\n"
        f"{E_LETTER} {bot.bi('Description')}: {_html_mod.escape(str(t['description']))}\n"
        f"{E_BOLT} {bot.bi('Date')}: {t['date']}\n"
        f"{E_BOLT} {bot.bi('Status')}: {_status(t['ticket_status'])}\n{DIV_STARS}"
    )


def cmdTicket(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['ban'].lower() == 'true':
            return bot.replyMessage(text=error('You are banned from this bot!'))
        bot.sendAction(action='typing')
        args = bot.cmd.args.strip()
        if not args:
            return bot.replyMessage(text=error('Use: /ticket problem | description'))
        parts       = args.split('|', 1)
        problem     = parts[0].strip()[:120]
        description = (parts[1].strip() if len(parts) > 1 else '—')[:1000]
        if not problem:
            return bot.replyMessage(text=error('Use: /ticket problem | description'))

        uname = (update.username or db.get('nombre') or str(update.user_id)).lstrip('@')
        r = gestion.create_ticket(update.user_id, uname, problem, description)
        if not r['status']:
            return bot.replyMessage(text=error('Could not create the ticket, try again!'))

        t = gestion.view_ticket(r['id'])
        bot.replyMessage(text=_card(bot, t, created=True))
        if bot.support_channel:
            bot.sendMessage(text=_card(bot, t), chat_id=bot.support_channel)
    except Exception as e: bot.raise_post(str(e))


def cmdTickets(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion.rangos:
            return
        bot.sendAction(action='typing')
        tks   = gestion.list_tickets('pending', 15)
        total = gestion.count_tickets('pending')
        if not tks:
            return bot.replyMessage(text=ok('Open Tickets', ('Status', 'No pending tickets')))
        lines = ''.join(f"{E_LETTER} <code>#{int(t[0]):06d}</code> · @{_html_mod.escape(str(t[1] or '?'))} · {_html_mod.escape(str(t[2]))} ({t[3]})\n" for t in tks)
        bot.replyMessage(text=(
            f"{E_RAINBOW}{bot.bi('Open Tickets')} [ 🎫 ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{lines}{DIV_STARS}\n"
            f"{E_LETTER} {bot.bi('Pending')}: <code>{total}</code>\n"
            f"{E_LETTER} {bot.bi('View')}: <code>/tk id</code>"
        ))
    except Exception as e: bot.raise_post(str(e))


def cmdTicketView(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion.rangos:
            return
        bot.sendAction(action='typing')
        tid = bot.cmd.args.strip().replace('#', '')
        if not tid.isdigit():
            return bot.replyMessage(text=error('Use: /tk id'))
        t = gestion.view_ticket(tid)
        if not t['status']:
            return bot.replyMessage(text=error('Ticket not found!'))
        bot.replyMessage(text=_card(bot, t))
    except Exception as e: bot.raise_post(str(e))


def cmdCloseTicket(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion.rangos:
            return
        bot.sendAction(action='typing')
        tid = bot.cmd.args.strip().replace('#', '')
        if not tid.isdigit():
            return bot.replyMessage(text=error('Use: /tclose id'))
        t = gestion.view_ticket(tid)
        if not t['status']:
            return bot.replyMessage(text=error('Ticket not found!'))
        by = (update.username or str(update.user_id)).lstrip('@')
        gestion.set_ticket_status(tid, 'closed', closed_by=by)
        bot.adminRegister('Close Ticket', f"#{int(tid):06d}")
        bot.replyMessage(text=ok(f"Ticket #{int(tid):06d} Closed", ('By', f"@{by}")))
        try:
            if t.get('user_id'):
                bot.sendMessage(
                    text=f"🎫 {bot.bi('Ticket')} <code>#{int(tid):06d}</code>\n{E_BOLT} {bot.bi('Status')}: {_status('closed')}",
                    chat_id=t['user_id']
                )
        except Exception:
            pass
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

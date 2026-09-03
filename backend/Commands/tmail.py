# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time, json, tempfile, os
from Model.libs.__tmail import TempMail
from Commands.jill import *

_SESSION_FILE = os.path.join(tempfile.gettempdir(), 'kg_tmail_sessions.json')


def _loadSessions() -> dict:
    try:
        with open(_SESSION_FILE, 'r') as f: return json.load(f)
    except: return {}

def _saveSessions(data: dict):
    with open(_SESSION_FILE, 'w') as f: json.dump(data, f)

def _getSession(uid) -> dict:
    return _loadSessions().get(str(uid))

def _setSession(uid, address, token):
    sessions = _loadSessions()
    sessions[str(uid)] = {'address': address, 'token': token}
    _saveSessions(sessions)


def cmdTmail(bot, update, gestion) -> None:
    try:
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        bot.sendAction(action='typing')
        if user['ban'] == 'false':
            if chat['rango'] in gestion.prem:
                if cmd['status'] != 'unval':
                    if cmd['mode'] == 'on':
                        customUser = bot.cmd.args.strip() or None
                        edit = bot.replyMessage(text=f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_BOLT} ]{E_HDR_END}\n{E_BOLT} {bot.bi('Status')}: <code>Creating Mailbox_</code>")
                        result = TempMail.create(customUser)
                        if not result.status:
                            bot.editMessage(message_id=edit.message_id, text=error(result.error)); return
                        _setSession(update.user_id, result.address, result.token)
                        rows = [
                            bot.addRow(
                                bot.addButton(text='- 𝖗𝖊𝖋𝖗𝖊𝖘𝖍 𝖎𝖓𝖇𝖔𝖝 -', callback='tmail_refresh'),
                                bot.addButton(text='- 𝖈𝖔𝖕𝖞 𝖊𝖒𝖆𝖎𝖑 -',    callback='tmail_copy'),
                            ),
                            bot.addRow(
                                bot.addButton(text='- 𝖓𝖊𝖜 𝖊𝖒𝖆𝖎𝖑 -', callback='tmail_new'),
                            ),
                        ]
                        bot.editMessage(message_id=edit.message_id, reply_markup=bot.replyMarkup(*rows), text=(
                            f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                            f"{E_LETTER} {bot.bi('Email')}: <code>{result.address}</code>\n"
                            f"{E_BOLT} {bot.bi('Status')}: Active {E_CHECK}\n"
                            f"{E_LETTER} {bot.bi('Inbox')}: <code>0 messages</code>\n{DIV_STARS}"
                        ))
                    elif cmd['mode'] == 'ma': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                    elif cmd['mode'] == 'of': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                else: bot.replyMessage(text=error('This command is not yet registered!'))
            else: bot.replyMessage(text=error('This Chat Is Not Authorized!'))
        else: bot.replyMessage(text=error('You are banned from this bot!'))
    except Exception as e: bot.raise_post(str(e))


def tmail_refresh(bot, update, gestion) -> None:
    try:
        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] Not Allowed', callback_id=update.query_id, alert=False); return
        session = _getSession(update.user_id)
        if not session:
            bot.showAlert(text='[!] No active mailbox — use /tmail', callback_id=update.query_id, alert=True); return
        inbox = TempMail.getInbox(session['token'])
        if not inbox.status:
            bot.showAlert(text='[!] Session expired — use /tmail', callback_id=update.query_id, alert=True); return
        rows = []
        if inbox.messages:
            for m in inbox.messages[:8]:
                rows.append(bot.addRow(
                    bot.addButton(text=f"- {m['subject'][:35]} -", callback=f"tmail_read {m['id']}")
                ))
        rows.append(bot.addRow(
            bot.addButton(text='- 𝖗𝖊𝖋𝖗𝖊𝖘𝖍 -', callback='tmail_refresh'),
            bot.addButton(text='- 𝖓𝖊𝖜 𝖊𝖒𝖆𝖎𝖑 -', callback='tmail_new'),
        ))
        bot.editMessage(message_id=update.message_id, reply_markup=bot.replyMarkup(*rows), text=(
            f"{E_RAINBOW}{bi('Temporal Mail')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_LETTER} {bi('Email')}: <code>{session['address']}</code>\n"
            f"{E_LETTER} {bi('Inbox')}: <code>{inbox.total} message(s)</code>\n"
            f"{DIV_STARS}"
            + ('' if not inbox.messages else
               '\n' + '\n'.join(
                   f"{E_LETTER} [{i+1}] <code>{m['from'][:30]}</code> — {m['subject'][:40]}"
                   for i, m in enumerate(inbox.messages[:8])
               ))
        ))
        bot.showAlert(text=f'{inbox.total} message{"s" if inbox.total != 1 else ""}', callback_id=update.query_id, alert=False)
    except Exception as e:
        bot.showAlert(text='[!] Error', callback_id=update.query_id)
        bot.raise_post(str(e))


def tmail_copy(bot, update, gestion) -> None:
    try:
        session = _getSession(update.user_id)
        if not session:
            bot.showAlert(text='[!] No active mailbox — use /tmail', callback_id=update.query_id, alert=True); return
        bot.showAlert(text=session['address'], callback_id=update.query_id, alert=True)
    except Exception as e:
        bot.showAlert(text='[!] Error', callback_id=update.query_id)
        bot.raise_post(str(e))


def tmail_read(bot, update, gestion) -> None:
    try:
        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] Not Allowed', callback_id=update.query_id, alert=False); return
        session = _getSession(update.user_id)
        if not session:
            bot.showAlert(text='[!] No active mailbox — use /tmail', callback_id=update.query_id, alert=True); return
        msgId = (bot.callback.args or '').strip()
        if not msgId:
            bot.showAlert(text='[!] Invalid message', callback_id=update.query_id, alert=False); return
        msg = TempMail.readMessage(session['token'], msgId)
        if not msg.status:
            bot.showAlert(text='[!] Error reading message', callback_id=update.query_id, alert=False); return
        rows = [bot.addRow(bot.addButton(text='- 𝖇𝖆𝖈𝖐 -', callback='tmail_refresh'))]
        bot.editMessage(message_id=update.message_id, reply_markup=bot.replyMarkup(*rows), text=(
            f"{E_RAINBOW}{bi('Temporal Mail — Message')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_LETTER} {bi('From')}: <code>{msg.sender}</code>\n"
            f"{E_LETTER} {bi('Subject')}: <code>{msg.subject}</code>\n"
            f"{E_BOLT} {bi('Date')}: <code>{msg.date}</code>\n{DIV_STARS}\n"
            f"<code>{msg.text[:3000]}</code>\n{DIV_STARS}"
        ))
        bot.showAlert(text='Message loaded', callback_id=update.query_id, alert=False)
    except Exception as e:
        bot.showAlert(text='[!] Error', callback_id=update.query_id)
        bot.raise_post(str(e))


def tmail_new(bot, update, gestion) -> None:
    try:
        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] Not Allowed', callback_id=update.query_id, alert=False); return
        result = TempMail.create()
        if not result.status:
            bot.showAlert(text=f'[!] {result.error}', callback_id=update.query_id, alert=False); return
        _setSession(update.user_id, result.address, result.token)
        rows = [
            bot.addRow(
                bot.addButton(text='- 𝖗𝖊𝖋𝖗𝖊𝖘𝖍 𝖎𝖓𝖇𝖔𝖝 -', callback='tmail_refresh'),
                bot.addButton(text='- 𝖈𝖔𝖕𝖞 𝖊𝖒𝖆𝖎𝖑 -',    callback='tmail_copy'),
            ),
            bot.addRow(
                bot.addButton(text='- 𝖓𝖊𝖜 𝖊𝖒𝖆𝖎𝖑 -', callback='tmail_new'),
            ),
        ]
        bot.editMessage(message_id=update.message_id, reply_markup=bot.replyMarkup(*rows), text=(
            f"{E_RAINBOW}{bi('Temporal Mail')} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_LETTER} {bi('Email')}: <code>{result.address}</code>\n"
            f"{E_BOLT} {bi('Status')}: Active {E_CHECK}\n"
            f"{E_LETTER} {bi('Inbox')}: <code>0 messages</code>\n{DIV_STARS}"
        ))
        bot.showAlert(text=result.address, callback_id=update.query_id, alert=False)
    except Exception as e:
        bot.showAlert(text='[!] Error', callback_id=update.query_id)
        bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

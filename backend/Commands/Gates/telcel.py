import time, threading, types, html as _html_mod
from Commands.Gates._template import waiting_bar, DIV
from Commands.Gates import telcel_core

_MONTOS     = [20, 30, 50, 80, 100, 150, 200, 300, 500]
_MONTOS_STR = ' / '.join(f'${m}' for m in _MONTOS)

_TCL_MONTOS = [(20,'🟢'),(30,'🟢'),(50,'🟢'),(80,'🟡'),(100,'🟡'),(150,'🟡'),(200,'🔴'),(300,'🔴'),(500,'🔴')]

def _tcl_kbd(bot, card_s=None, numero=None):
    if card_s and numero:
        flat = [bot.addButton(f"{e} ${a}", callback=f"tcl_monto {a}|{card_s}|{numero}") for a, e in _TCL_MONTOS]
    else:
        flat = [bot.addButton(f"{e} ${a}", callback=f"tcl_monto {a}") for a, e in _TCL_MONTOS]
    return bot.replyMarkup(bot.addRow(*flat[:3]), bot.addRow(*flat[3:6]), bot.addRow(*flat[6:]))

def _mask(num):
    return f"{num[:6]}·····{num[-4:]}" if len(num) > 10 else f"{num[:4]}···"

def _run_tcl(bot, update, gestion, cc_str, monto, numero, b):
    cc, binData = b['cc'], b['bin']
    user = gestion.view(user_id=update.user_id)
    now  = time.time()
    edit = bot.replyMessage(text=waiting_bar(bot, 0, 'Telcel MX', 'Telcel Gate'))

    stop, th = threading.Event(), None
    if edit is not None:
        def _spin():
            pcts, i = [15, 30, 45, 60, 75, 90], 0
            while not stop.is_set():
                try: bot.editMessage(message_id=edit.message_id, text=waiting_bar(bot, pcts[i % len(pcts)], 'Telcel MX', 'Telcel Gate'))
                except Exception: pass
                i += 1
                stop.wait(1.4)
        th = threading.Thread(target=_spin, daemon=True)
        th.start()

    try:
        result = telcel_core.main(cc_str, monto, numero)
    except Exception as e:
        result = {'status': 'Error ⚠️', 'message': str(e)[:200]}
    finally:
        stop.set()
        if th is not None: th.join(timeout=2)

    mid    = edit.message_id if edit is not None else None
    status = result.get('status', 'Error ⚠️')

    if status == 'Error ⚠️':
        msg = _html_mod.escape(str(result.get('message', 'Gate error')))
        txt = f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>{msg}</code>"
        return bot.editMessage(message_id=mid, text=txt) if mid else bot.replyMessage(text=txt)

    extra = ''
    if status == 'Approved ✅':
        if isinstance(b.get('credits'), int):
            gestion.commit("UPDATE users SET credits = %s WHERE user_id = %s",
                           (str(b['credits'] - 2), str(update.user_id)))
        extra = (
            f"📱 {bot.bi('Folio Telcel')}: <code>{_html_mod.escape(str(result.get('folio_telcel', 'N/A')))}</code>\n"
            f"⚡ {bot.bi('Folio Motor')}: <code>{_html_mod.escape(str(result.get('folio_motor', 'N/A')))}</code>\n"
            f"🍸 {bot.bi('Proveedor')}: <code>{_html_mod.escape(str(result.get('proveedor', 'FONYOU')))}</code>\n"
        )

    card = (
        f"{bot.bi('Telcel Gate')} [ 🍸 ]\n{DIV}\n"
        f"🍸 {bot.bi('Card')}: <code>{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}</code>\n"
        f"⚡ {bot.bi('Status')}: <code>{status}</code>\n"
        f"💳 {bot.bi('Gate')}: <code>Telcel MX</code>\n{DIV}\n"
        f"{extra}"
        f"📱 {bot.bi('Telefono')}: <code>{numero}</code>\n"
        f"💰 {bot.bi('Monto')}: <code>${monto} MXN</code>\n{DIV}\n"
        f"🍸 {bot.bi('Info')}: <code>{_html_mod.escape(binData['brand'].title())}</code> - <code>{_html_mod.escape(binData['type'].title())}</code> - <code>{_html_mod.escape(binData['level'].title())}</code>\n"
        f"🍸 {bot.bi('Bank')}: <code>{_html_mod.escape(binData['bank'].title())}</code>\n"
        f"🍸 {bot.bi('Country')}: <code>{_html_mod.escape(binData['country'].title())}</code> {binData.get('flag', '')}\n{DIV}\n"
        f"⚡ {bot.bi('T. Taken')}: <code>{round(time.time() - now, 1)}'s</code>\n"
        f"👤 {bot.bi('User')}: {update.username} [{_html_mod.escape(user['c_name'].title())}]\n{DIV}\n"
        f"🍸 {bot.bi('By')}: @Bl4ckD4ys ☁️"
    )
    bot.editMessage(message_id=mid, text=card) if mid else bot.replyMessage(text=card)


def gateCmd(bot, update, gestion):
    try:
        bot.sendAction(action='typing')
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        raw  = bot.cmd.args if len(bot.cmd.args) > 0 else (update.reply_to.text if update.reply_to is not None else '')

        if not raw:
            return bot.replyMessage(
                text=(
                    f"{bot.bi('Telcel Gate')} [ 🍸 ]\n{DIV}\n"
                    f"🍸 {bot.bi('Use')}: <code>/tcl cc|mm|yy|cvv numero</code>\n"
                    f"💳 {bot.bi('Montos')}: <code>{_MONTOS_STR}</code>\n{DIV}\n"
                    f"🍸 {bot.bi('Ejemplo')}: <code>/tcl 4111111111111111|12|26|123 5548448605</code>"
                ),
                reply_markup=_tcl_kbd(bot)
            )

        parts  = raw.strip().split()
        card_s = parts[0] if parts else ''
        numero = parts[1] if len(parts) > 1 else None
        monto_arg = parts[2] if len(parts) > 2 else None

        

        if not card_s or not numero:
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>Use: /tcl cc|mm|yy|cvv numero</code>"
            ))
        if len(numero) < 8 or not numero.isdigit():
            return bot.replyMessage(text=f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>Número inválido</code>")

        if not monto_arg:
            return bot.replyMessage(
                text=(
                    f"{bot.bi('Telcel Gate')} [ 🍸 ]\n{DIV}\n"
                    f"💳 {bot.bi('Card')}: <code>{_mask(card_s.split('|')[0])}</code>\n"
                    f"📱 {bot.bi('Número')}: <code>{numero}</code>\n{DIV}\n"
                    f"💰 {bot.bi('Selecciona el monto')}:"
                ),
                reply_markup=_tcl_kbd(bot, card_s=card_s, numero=numero)
            )

        try:
            monto = int(monto_arg)
        except ValueError:
            return bot.replyMessage(text=f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>Monto debe ser número</code>")
        if monto not in _MONTOS:
            return bot.replyMessage(text=(
                f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"
                f"🍸 {bot.bi('Raise')}: <code>Monto inválido. Opciones: {_MONTOS_STR}</code>"
            ))

        b = gestion.gates(user=user, chat=chat, text=card_s, cmd=cmd, bot=bot)
        if not b['status']:
            return bot.replyMessage(text=b['text'])

        _run_tcl(bot, update, gestion, card_s, monto, numero, b)
    except Exception as e:
        
        bot.raise_post(str(e))


def tcl_monto_cb(bot, update, gestion):
    monto_str = bot.callback.args.strip()
    if not monto_str:
        return

    card_s = ''
    numero = ''

    tokens = monto_str.split('|')
   
    if len(tokens) == 6:
        monto_str = tokens[0]
        card_s = f"{tokens[1]}|{tokens[2]}|{tokens[3]}|{tokens[4]}"
        numero = tokens[5]
    else:
        original = (update.message or '').strip()
        orig_tokens = original.split()
        if orig_tokens and orig_tokens[0].startswith('/'):
            orig_tokens = orig_tokens[1:]
        card_s = orig_tokens[0] if orig_tokens else ''
        numero = orig_tokens[1] if len(orig_tokens) > 1 else ''

    try:
        monto = int(monto_str)
    except ValueError:
        monto = 0
    if monto not in _MONTOS or not card_s or len(numero) < 8 or not numero.isdigit():
        return bot.showAlert('Sesión expirada, usa /tcl de nuevo', update.query_id, True)

    bot.showAlert(f'${monto} MXN seleccionado', update.query_id, False)

    bot.cmd = types.SimpleNamespace(command='tcl', args=card_s)
    user = gestion.view(user_id=update.user_id)
    chat = gestion.view(user_id=update.chat_id)
    cmd  = gestion.viewCmd('tcl')
    b    = gestion.gates(user=user, chat=chat, text=card_s, cmd=cmd, bot=bot)
    if not b['status']:
        return bot.replyMessage(text=b['text'])

    _run_tcl(bot, update, gestion, card_s, monto, numero, b)


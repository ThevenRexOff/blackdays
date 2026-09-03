# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time
from Model import BotX
from Commands.Tools.addr import fake
from Commands.Tools.binc import lookup
from Commands.Tools.cc_gen import array, gen


ITEMS_PER_PAGE = 5
_L = "https://t.me/Ghidorah_chkbot"
_S = f"<a href='{_L}'>ᚸ</a>"

# ── JILL design system ──
_bi  = BotX.bi
_DIV = "────────────────────"

# Premium emoji
_E_RAINBOW = '<tg-emoji emoji-id="5103122966779004034">🌈</tg-emoji>'
_E_HDR_END = '<tg-emoji emoji-id="5102628843676501227">👤</tg-emoji>'
_E_LETTER  = '<tg-emoji emoji-id="5253742260054409879">✉️</tg-emoji>'
_E_BOLT    = '<tg-emoji emoji-id="5456140674028019486">⚡️</tg-emoji>'
_E_CHECK   = '<tg-emoji emoji-id="5206607081334906820">✔️</tg-emoji>'
_E_STAR_GATES = '<tg-emoji emoji-id="4974627973463278527">🤩</tg-emoji>'
_E_STAR_TOOLS = '<tg-emoji emoji-id="4974574243422406122">🤩</tg-emoji>'
_E_STAR_USER  = '<tg-emoji emoji-id="4972101390231930110">🤩</tg-emoji>'
_CMD_DIV_GATES = _E_STAR_GATES * 13
_CMD_DIV_TOOLS = _E_STAR_TOOLS * 13
_CMD_DIV_USER  = _E_STAR_USER  * 13
_CMD_DIV       = _CMD_DIV_TOOLS   # default — used for general/return

_GATE_TITLES = {
    'auths':    'Gates Auths',
    'charged':  'Gates Charged',
    'specials': 'Gates Specials',
    'ccn':      'Gates Charged CCN',
    'avs':      'Gates AVS',
}
_GATE_ICONS = {
    'auths':    '🍸',
    'charged':  '🥃',
    'specials': '🍹',
    'ccn':      '🍷',
    'avs':      '🧉',
    'tool':     '⚙️',
}


def _rev(d) -> str:
    p = str(d or '').split('-')
    return f"{p[2]}-{p[1]}-{p[0]}" if len(p) == 3 and len(p[0]) == 4 else (str(d) if d else '—')

_USER_CMDS = [
    ('claim',  'key',       'Redeem Key'),
    ('p',      '',          'Profile / My ID'),
    ('myinfo', '',          'My Account Info'),
    ('info',   'uid|reply', 'User Info'),
    ('cookie', 'cookie',    'Save AMZ Cookie'),
    ('prices', '',          'Price List'),
    ('ticket', 'problem|desc', 'Open Ticket'),
    ('ref',    'reply',     'Send Reference'),
    ('links',  '',          'Official Links'),
]

_ADMIN_CMDS = [
    ('prmn',    'uid|days[|creds]',  'Promote Premium'),
    ('cred',    'uid|amount',        'Set Credits'),
    ('delay',   'uid|seconds',       'Set Delay'),
    ('rname',   'uid|name',          'Rename User'),
    ('rban',    'uid',               'Ban User'),
    ('ruban',   'uid',               'Unban User'),
    ('key',     'days|credits',      'Generate Key'),
    ('sell',    'uid|plan|method',   'Register Sale'),
    ('sales',   '[uid]',             'Sales Report'),
    ('seller',  'uid',               'Make Seller'),
    ('unseller','uid',               'Remove Seller'),
    ('addplan', 'name|days|cr|price', 'Add Plan'),
    ('delplan', 'name',              'Delete Plan'),
    ('tickets', '',                  'Open Tickets'),
    ('tclose',  'id',                'Close Ticket'),
    ('history', '[uid]',             'Event History'),
    ('binban',  'add|del|list|count','BIN Ban System'),
    ('broadcast','message',          'Broadcast to All'),
    ('gusers',  '',                  'User Stats'),
    ('stat_c',  'cmd',               'Command Stats'),
    ('addcmd',  'cmd|mode|type|...', 'Add Command'),
    ('mod',     '-c cmd -o field -v value', 'Modify Command Field'),
    ('delcmd',  'cmd',               'Delete Command'),
]


# ─── Format helpers ─────────────────────────────────────────────────────────

def _fmt_db_cmd(a, modes):
    # a = (comando, tipo, status, d_reg, comentario, name, use[, gate])
    status    = a[2] or ''
    name      = a[5] or a[0]
    use       = a[6] or ''
    gateway   = (a[7] if len(a) > 7 and a[7] else (a[1] or '').title())
    state_txt = f"ON{_E_CHECK}" if status == 'on' else f"{status.upper()}{modes.get(status, '')}"
    return (
        f"{_E_LETTER} {_bi(name)}: /{a[0]} {use}\n"
        f"{_E_BOLT} {_bi('State')}: {state_txt} | Reviewed: {_rev(a[3])}\n"
        f"💳 {_bi('Gate')}: {gateway}\n\n"
    )


def _fmt_admin_cmd(item):
    cmd, use, desc = item
    return f"{_E_LETTER} {_bi(desc)}: /{cmd} {use}\n\n"


def _page_nav(bot, category, page, pages, style='danger'):
    if pages <= 1:
        return []
    nav = []
    if page > 0:
        nav.append(bot.addButton(text='◀', callback=f'pg {category} {page - 1}', style=style))
    nav.append(bot.addButton(text=f'· {page + 1} / {pages} ·', callback='pgn', style=style))
    if page < pages - 1:
        nav.append(bot.addButton(text='▶', callback=f'pg {category} {page + 1}', style=style))
    return nav


def _paginate_db(bot, update, gestion, typeC, page, title, return_cb, icon='⚙️'):
    div   = _CMD_DIV_TOOLS if typeC == 'tool' else _CMD_DIV_GATES
    style = 'danger' if typeC == 'tool' else 'success'
    i = gestion.viewCmds(typeC=typeC)
    btn_ret = bot.addButton(text='𝗥𝗘𝗧𝗨𝗥𝗡', callback=return_cb, style=style)
    if i.get('status') is not True:
        bot.editMessage(
            message_id=update.message_id,
            text=(
                f"{_E_RAINBOW}{_bi(title)} [ {icon} ]{_E_HDR_END}\n{div}\n"
                f"{_E_LETTER} {_bi('Empty')}: <code>No commands in this section yet.</code>\n{div}"
            ),
            reply_markup=bot.replyMarkup(bot.addRow(btn_ret))
        )
        return
    items = i['response']
    total = len(items)
    pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page  = max(0, min(page, pages - 1))
    start = page * ITEMS_PER_PAGE
    chunk = items[start : start + ITEMS_PER_PAGE]
    text  = f"{_E_RAINBOW}{_bi(title)} [ {icon} ]{_E_HDR_END}\n{div}\n"
    for a in chunk:
        text += _fmt_db_cmd(a, gestion.modes).rstrip('\n') + '\n' + div + '\n'
    text = text.rstrip('\n')
    rows = []
    nav  = _page_nav(bot, typeC, page, pages, style=style)
    if nav: rows.append(bot.addRow(*nav))
    rows.append(bot.addRow(btn_ret))
    bot.editMessage(message_id=update.message_id, text=text, reply_markup=bot.replyMarkup(*rows))


def _paginate_admin(bot, update, page):
    items = _ADMIN_CMDS
    total = len(items)
    pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page  = max(0, min(page, pages - 1))
    start = page * ITEMS_PER_PAGE
    chunk = items[start : start + ITEMS_PER_PAGE]
    text  = f"{_E_RAINBOW}{_bi('Admin Panel')} [ {_E_LETTER} ]{_E_HDR_END}\n{_CMD_DIV_USER}\n"
    for item in chunk:
        text += _fmt_admin_cmd(item).rstrip('\n') + '\n' + _CMD_DIV_USER + '\n'
    text = text.rstrip('\n')
    rows = []
    nav  = _page_nav(bot, 'adm', page, pages, style='primary')
    if nav: rows.append(bot.addRow(*nav))
    rows.append(bot.addRow(bot.addButton(text='𝗥𝗘𝗧𝗨𝗥𝗡', callback='return_tools', style='primary')))
    bot.editMessage(message_id=update.message_id, text=text, reply_markup=bot.replyMarkup(*rows))


def _paginate_user(bot, update, gestion, page):
    user   = gestion.view(user_id=update.user_id)
    header = (
        f"{_E_RAINBOW}{_bi('User Panel')} [ {_E_LETTER} ]{_E_HDR_END}\n{_CMD_DIV_USER}\n"
        f"{_E_LETTER} {_bi('Rank')}: {user['c_name'].title()} | {_bi('Credits')}: {user['credits']}\n"
    )
    if user['rango'] == 'premium':
        header += f"{_E_BOLT} {_bi('Days Left')}: {user.get('days', '—')}\n"
    header += f"{_CMD_DIV_USER}\n"
    items    = _USER_CMDS
    per_page = 4   # header is richer (rank/credits), 4 entries keeps entity count under 100
    total    = len(items)
    pages    = max(1, (total + per_page - 1) // per_page)
    page     = max(0, min(page, pages - 1))
    start    = page * per_page
    chunk    = items[start : start + per_page]
    cmds_text = ''
    for item in chunk:
        cmds_text += _fmt_admin_cmd(item).rstrip('\n') + '\n' + _CMD_DIV_USER + '\n'
    cmds_text = cmds_text.rstrip('\n')
    rows  = []
    nav   = _page_nav(bot, 'usr', page, pages, style='primary')
    if nav: rows.append(bot.addRow(*nav))
    rows.append(bot.addRow(bot.addButton(text='𝗥𝗘𝗧𝗨𝗥𝗡', callback='return_tools', style='primary')))
    bot.editMessage(message_id=update.message_id, text=header + cmds_text, reply_markup=bot.replyMarkup(*rows))


# ─── Callbacks ──────────────────────────────────────────────────────────────

def callback_gates(bot, update, gestion) -> None:
    try:
        if update.user_id == update.origin_uid:
            btn1 = bot.addButton(text='𝗔𝗨𝗧𝗛𝗦',    callback='auths',        style='success')
            btn2 = bot.addButton(text='𝗖𝗛𝗔𝗥𝗚𝗘𝗗',  callback='charged',      style='success')
            btn3 = bot.addButton(text='𝗦𝗣𝗘𝗖𝗜𝗔𝗟𝗦', callback='specials',     style='success')
            btn4 = bot.addButton(text='𝗖𝗖𝗡',      callback='ccn',          style='success')
            btn5 = bot.addButton(text='𝗔𝗩𝗦',      callback='avs',          style='success')
            btn6 = bot.addButton(text='⚡️ 𝗠𝗔𝗦𝗦',   callback='mass_info',    style='success')
            btn7 = bot.addButton(text='𝗥𝗘𝗧𝗨𝗥𝗡',   callback='return_tools', style='success')
            btns = bot.replyMarkup(
                bot.addRow(btn1, btn2),
                bot.addRow(btn3, btn4),
                bot.addRow(btn5, btn6),
                bot.addRow(btn7)
            )
            bot.editMessage(
                message_id=update.message_id,
                text=(
                    f"{_E_RAINBOW}{_bi('Gateways')} [ 💳 ]{_E_HDR_END}\n{_CMD_DIV_GATES}\n"
                    f"{_E_LETTER} {_bi('Select')}: <code>Choose a gate type from the keyboard.</code>\n{_CMD_DIV_GATES}"
                ),
                reply_markup=btns
            )
        else: bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
    except Exception as e: bot.raise_post(str(e))


def callback_mass_info(bot, update, gestion) -> None:
    try:
        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
            return
        btn_back = bot.addButton(text='𝗥𝗘𝗧𝗨𝗥𝗡', callback='gates', style='success')
        btns = bot.replyMarkup(bot.addRow(btn_back))
        text = (
            f"{_E_RAINBOW}{_bi('Mass Checker')} [ {_E_BOLT} ]{_E_HDR_END}\n{_CMD_DIV_GATES}\n"
            f"{_E_LETTER} {_bi('Que es')}: <code>Corre cualquier gate en masa.\n"
            f"1ra linea = comando, siguientes = tarjetas.</code>\n{_CMD_DIV_GATES}\n"
            f"{_E_BOLT} {_bi('Uso')}:\n"
            f"<code>/mass GATE\ncc|mm|yy|cvv\ncc|mm|yy|cvv</code>\n{_CMD_DIV_GATES}\n"
            f"{_E_BOLT} {_bi('Ejemplo')}:\n"
            f"<code>/mass mj\n4111111111111111|12|26|123\n5200828282828210|08|27|456</code>\n{_CMD_DIV_GATES}\n"
            f"💳 {_bi('Costo')}: <code>2 creditos por live. Declined no cobra.</code>\n"
            f"{_E_BOLT} {_bi('Limite')}: <code>Max 10 tarjetas por corrida.</code>\n"
            f"🔒 {_bi('Req')}: <code>Sub de chat + creditos.</code>\n{_CMD_DIV_GATES}"
        )
        bot.editMessage(message_id=update.message_id, text=text, reply_markup=btns)
    except Exception as e: bot.raise_post(str(e))


def callback_tools(bot, update, gestion) -> None:
    try:
        if update.user_id == update.origin_uid:
            _paginate_db(bot, update, gestion, 'tool', 0, 'Commands Tools', 'return_tools', '⚙️')
        else: bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
    except Exception as e: bot.raise_post(str(e))


def callback_user(bot, update, gestion) -> None:
    try:
        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
            return
        user = gestion.view(user_id=update.user_id)
        if user['rango'] in gestion.rangos:
            _paginate_admin(bot, update, 0)
        else:
            _paginate_user(bot, update, gestion, 0)
    except Exception as e: bot.raise_post(str(e))


def c_cmds_gates_type(bot, update, gestion) -> None:
    try:
        if update.user_id == update.origin_uid:
            type_g = bot.callback.command
            title  = _GATE_TITLES.get(type_g, type_g.title())
            icon   = _GATE_ICONS.get(type_g, '🍸')
            _paginate_db(bot, update, gestion, type_g, 0, title, 'gates', icon)
        else: bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
    except Exception as e: bot.raise_post(str(e))


def callback_return(bot, update, gestion) -> None:
    try:
        if update.user_id == update.origin_uid:
            btn1 = bot.addButton(text='𝗧𝗢𝗢𝗟𝗦',    callback='tools',  style='danger')
            btn2 = bot.addButton(text='𝗨𝗦𝗘𝗥',     callback='user',   style='primary')
            btn3 = bot.addButton(text='𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦', callback='gates',  style='success')
            btns = bot.replyMarkup(bot.addRow(btn1, btn2), bot.addRow(btn3))
            bot.editMessage(
                message_id=update.message_id,
                text=(
                    f"{_E_RAINBOW}{_bi('General Commands')} [ {_E_LETTER} ]{_E_HDR_END}\n{_CMD_DIV}\n"
                    f"{_E_LETTER} {_bi('Use')}: <code>Select a section from the keyboard below.</code>\n{_CMD_DIV}"
                ),
                reply_markup=btns
            )
        else: bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
    except Exception as e: bot.raise_post(str(e))


def cmds_nav(bot, update, gestion) -> None:
    try:
        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
            return
        parts    = bot.callback.args.split(' ', 1)
        category = parts[0].lower() if parts else ''
        page     = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        if category == 'tool':
            _paginate_db(bot, update, gestion, 'tool', page, 'Commands Tools', 'return_tools', '⚙️')
        elif category in _GATE_TITLES:
            _paginate_db(bot, update, gestion, category, page,
                         _GATE_TITLES[category], 'gates',
                         _GATE_ICONS.get(category, '🍸'))
        elif category == 'adm':
            user = gestion.view(user_id=update.user_id)
            if user['rango'] in gestion.rangos:
                _paginate_admin(bot, update, page)
            else:
                bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
        elif category == 'usr':
            _paginate_user(bot, update, gestion, page)
        else:
            bot.showAlert(text='[!] Invalid section', callback_id=update.query_id)
    except Exception as e: bot.raise_post(str(e))


def pgn(bot, update, gestion) -> None:
    try: bot.showAlert(text=f'Page {bot.callback.args}', callback_id=update.query_id, alert=False)
    except Exception: pass


def rg_fake(bot, update, gestion) -> None:
    try:
        now       = time.time()
        user      = gestion.view(update.user_id)
        msg_parts = update.message.split()
        command   = msg_parts[0].lstrip('/').split('@')[0] if msg_parts else ''
        args      = ' '.join(msg_parts[1:]) if len(msg_parts) > 1 else ''
        if update.user_id == update.origin_uid:
            cmd = gestion.viewCmd(command)
            if cmd.get('status') is not True:
                bot.showAlert(text='[!] Command not available', callback_id=update.query_id)
                return
            if cmd['mode'] == 'on':
                btn1 = bot.addButton(text='𝗥𝗘 𝗚𝗘𝗡', callback='rg_fake')
                btn2 = bot.addButton(text='𝗖𝗟𝗘𝗔𝗡 𝗤𝗨𝗘𝗥𝗬', callback='clean')
                buttons = bot.replyMarkup(bot.addRow(btn1, btn2))
                _fake = fake(args)
                if not _fake['status']:
                    bot.editMessage(message_id=update.message_id,
                        text=f"{_E_RAINBOW}{_bi(cmd['name'].title())} [ ⚙️ ]{_E_HDR_END}\n{_CMD_DIV}\n{_E_LETTER} {_bi('Raise')}: <code>Error generating data, try again!</code>\n{_CMD_DIV}")
                    return
                a = _fake['response']
                bot.editMessage(
                    message_id=update.message_id,
                    text=(
                        f"{_E_RAINBOW}{_bi(cmd['name'].title())} ({a['country'].title()}) [ ⚙️ ]{_E_HDR_END}\n{_CMD_DIV}\n"
                        f"{_E_LETTER} {_bi('Name')}: <code>{a['f_name'].title()} {a['l_name'].title()}</code>\n"
                        f"{_E_LETTER} {_bi('Gender')}: <code>{a['gender'].title()}</code>\n"
                        f"{_E_LETTER} {_bi('Mail')}: <code>{a['mail']}</code>\n"
                        f"{_E_LETTER} {_bi('Phone')}: <code>{a['phone']}</code>\n{_CMD_DIV}\n"
                        f"{_E_LETTER} {_bi('Country')}: <code>{a['country'].title()}</code>\n"
                        f"{_E_LETTER} {_bi('State')}: <code>{a['state'].title()}</code> | {_bi('City')}: <code>{a['city'].title()}</code>\n"
                        f"{_E_LETTER} {_bi('ZipCode')}: <code>{a['zipcode']}</code>\n"
                        f"{_E_LETTER} {_bi('Street')}: <code>{a['street']}</code>\n{_CMD_DIV}\n"
                        f"{_E_BOLT} {_bi('T. Taken')}: <code>{str(round((time.time() - now), 1))}'s</code>\n"
                        f"{_E_LETTER} {_bi('User')}: {update.username} [{user['c_name'].title()}]\n{_CMD_DIV}"
                    ),
                    reply_markup=buttons
                )
            elif cmd['mode'] == 'ma':
                bot.editMessage(message_id=update.message_id,
                    text=f"{_E_RAINBOW}{_bi(cmd['name'].title())} [ ⚙️ ]{_E_HDR_END}\n{_CMD_DIV}\n{_E_LETTER} {_bi('Raise')}: <code>Command in maintenance! ({gestion.modes[cmd['mode']]})</code>\n{_CMD_DIV}")
            elif cmd['mode'] == 'of':
                bot.editMessage(message_id=update.message_id,
                    text=f"{_E_RAINBOW}{_bi(cmd['name'].title())} [ ⚙️ ]{_E_HDR_END}\n{_CMD_DIV}\n{_E_LETTER} {_bi('Raise')}: <code>Command Offline! ({gestion.modes[cmd['mode']]})</code>\n{_CMD_DIV}")
        else:
            bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
    except Exception as e: bot.raise_post(str(e))


def clean_query(bot, update, gestion) -> None:
    try:
        if update.user_id == update.origin_uid:
            bot.editMessage(message_id=update.message_id, text=f"{_bi('Message Cleaned')} [ 🗑 ]")
        else:
            bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
    except Exception as e: bot.raise_post(str(e))


def promote(bot, update, gestion) -> None:
    try:
        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
            return
        uid = bot.callback.args.strip()
        gestion.commit("UPDATE users SET c_name = %s, rango = %s, ban = %s, credits = %s, spam = %s, warns = %s, admin = %s, su = %s WHERE user_id = %s", ('admin', 'admin', 'false', 'unlimited', '0', '0', 'true', 'true', uid))
        gestion._view_cache.pop(uid, None)
        bot.adminRegister('Promote Admin', uid)
        bot.editMessage(
            message_id=update.message_id,
            text=(
                f"{_E_RAINBOW}{_bi('User Updated')} [ 📈 ]{_E_HDR_END}\n{_CMD_DIV}\n"
                f"{_E_LETTER} {_bi('UID')}: <code>{uid}</code>\n"
                f"{_E_LETTER} {_bi('Status')}: <code>Admin</code> | {_bi('Rank')}: <code>Admin</code>\n{_CMD_DIV}"
            )
        )
    except Exception as e: bot.raise_post(str(e))


def unpromote(bot, update, gestion) -> None:
    try:
        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
            return
        uid = bot.callback.args.strip()
        gestion.commit("UPDATE users SET c_name = %s, rango = %s, credits = %s, spam = %s, admin = %s, su = %s WHERE user_id = %s", ('free user', 'free', '0', '60', 'false', 'false', uid))
        gestion._view_cache.pop(uid, None)
        bot.adminRegister('Demote Admin', uid)
        bot.editMessage(
            message_id=update.message_id,
            text=(
                f"{_E_RAINBOW}{_bi('User Updated')} [ 📉 ]{_E_HDR_END}\n{_CMD_DIV}\n"
                f"{_E_LETTER} {_bi('UID')}: <code>{uid}</code>\n"
                f"{_E_LETTER} {_bi('Rank')}: <code>Free</code>\n{_CMD_DIV}"
            )
        )
    except Exception as e: bot.raise_post(str(e))


def rg_ccs(bot, update, gestion) -> None:
    try:
        now  = time.time()
        user = gestion.view(update.user_id)
        chat = gestion.view(update.chat_id)
        args = bot.callback.args.strip()

        if update.user_id != update.origin_uid:
            bot.showAlert(text='[!] No Allowed', callback_id=update.query_id)
            return
        if not args:
            bot.showAlert(text='[!] No BIN data in callback', callback_id=update.query_id)
            return
        if chat['rango'] not in gestion.prem:
            bot.showAlert(text='[!] Chat No Authorized', callback_id=update.query_id)
            return

        _lookup = lookup(args)
        if not _lookup['status']:
            bot.editMessage(message_id=update.message_id,
                text=f"{_E_RAINBOW}{_bi('Gen')} [ ⚙️ ]{_E_HDR_END}\n{_CMD_DIV}\n{_E_LETTER} {_bi('Raise')}: <code>Use a Correct Bin!</code>\n{_CMD_DIV}")
            return
        a     = _lookup['response']
        diana = array(text=args, bot=bot)
        if not diana['status']:
            bot.editMessage(message_id=update.message_id,
                text=f"{_E_RAINBOW}{_bi('Gen')} [ ⚙️ ]{_E_HDR_END}\n{_CMD_DIV}\n{_E_LETTER} {_bi('Raise')}: <code>{diana['raise'].title()}</code>\n{_CMD_DIV}")
            return
        darla   = gen(diana['gen'].split('|'))
        btn1    = bot.addButton(text='𝗥𝗘 𝗚𝗘𝗡', callback=f'rg_ccs {diana["gen"]}')
        btn2    = bot.addButton(text='𝗖𝗟𝗘𝗔𝗡 𝗤𝗨𝗘𝗥𝗬', callback='clean')
        buttons = bot.replyMarkup(bot.addRow(btn1, btn2))
        bot.editMessage(
            message_id=update.message_id,
            reply_markup=buttons,
            text=(
                f"{_E_RAINBOW}{_bi('Gen')} [ ⚙️ ]{_E_HDR_END}\n{_CMD_DIV}\n"
                f"{_E_LETTER} {_bi('Bin')}: <code>{diana['gen']}</code>\n"
                f"{_E_LETTER} {_bi('Info')}: <code>{a['flag']}</code> - <code>{a['brand'].title()}</code> - "
                f"<code>{a['type'].title()}</code> - <code>{a['level'].title()}</code> - <code>{a['bank'].title()}</code>\n{_CMD_DIV}\n"
                f"{darla['response']}\n{_CMD_DIV}\n"
                f"{_E_BOLT} {_bi('T. Taken')}: <code>{str(round((time.time() - now), 1))}'s</code>\n"
                f"{_E_LETTER} {_bi('User')}: {update.username} [{user['c_name'].title()}]\n{_CMD_DIV}"
            )
        )
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

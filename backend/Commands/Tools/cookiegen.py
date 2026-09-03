# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import time, os, sys, pathlib
from Commands.jill import *

# Add cookiegen_local to path so AmazonAccountCreator is importable
_CG_DIR = str(pathlib.Path(__file__).resolve().parent / 'cookiegen_local')
if _CG_DIR not in sys.path:
    sys.path.insert(0, _CG_DIR)

COST = 30

COUNTRIES = {
    'US': '🇺🇸 US', 'CA': '🇨🇦 CA', 'MX': '🇲🇽 MX', 'BR': '🇧🇷 BR',
    'UK': '🇬🇧 UK', 'DE': '🇩🇪 DE', 'FR': '🇫🇷 FR', 'IT': '🇮🇹 IT',
    'ES': '🇪🇸 ES', 'NL': '🇳🇱 NL', 'SG': '🇸🇬 SG', 'AU': '🇦🇺 AU',
    'JP': '🇯🇵 JP',
}


def _generate_cookie(country: str, proxy: str = None) -> dict:
    try:
        from account_creator import AmazonAccountCreator
        raw_domains  = os.getenv('MAIL_DOMAINS', 'shopsxgitario.com,sxgitarioshop.com')
        mail_domains = [d.strip() for d in raw_domains.split(',') if d.strip()]
        creator = AmazonAccountCreator(
            country     = country,
            proxy       = proxy,
            verbose     = False,
            clearScreen = False,
            mailDomains = mail_domains,
        )
        return creator.processRegistration()
    except Exception as e:
        return {'status': False, 'message': f'{type(e).__name__}: {e}'}


def _save_cookie_to_file(bot, uid, cookie_data):
    cookie_path = bot.getCookiePath()
    uid = str(uid)
    lines, found = [], False
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|>')
                if len(parts) >= 1 and parts[0] == uid:
                    lines.append(f"{uid}|>{cookie_data}\n"); found = True
                else:
                    lines.append(line)
    except FileNotFoundError:
        pass
    if not found:
        lines.append(f"{uid}|>{cookie_data}\n")
    with open(cookie_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


#//! Command {cgen} ────────────────────────────────────────────────────────
def cmdCookieGen(bot: object, update: object, gestion: object) -> None:
    try:
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        bot.sendAction(action='typing')

        if user['ban'] != 'false':
            bot.replyMessage(text=error('You are banned from this bot!')); return
        if chat['rango'] not in gestion.prem:
            bot.replyMessage(text=error('This Chat Is Not Authorized!')); return
        if cmd['status'] == 'unval':
            bot.replyMessage(text=error('This command is not yet registered!')); return
        if cmd['mode'] == 'ma':
            bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!")); return
        if cmd['mode'] == 'of':
            bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!")); return

        arg = bot.cmd.args.strip().upper()
        if arg in COUNTRIES:
            _execute(bot, update, gestion, user, cmd, arg); return

        is_admin = user['rango'].lower() in gestion.rangos
        credits  = '∞' if is_admin or str(user['credits']).lower() == 'unlimited' else user['credits']

        rows = []
        keys = list(COUNTRIES.keys())
        for i in range(0, len(keys), 4):
            row = [bot.addButton(text=COUNTRIES[k], callback=f"cgen {k}") for k in keys[i:i+4]]
            rows.append(bot.addRow(*row))

        bot.replyMessage(
            f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_GLOBE} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_LETTER} {bot.bi('Charge')}: <code>{COST} credits</code>\n"
            f"{E_LETTER} {bot.bi('Balance')}: <code>{credits} credits</code>\n"
            f"{E_BOLT} {bot.bi('Select Country')}:",
            bot.replyMarkup(*rows)
        )
    except Exception as e:
        bot.raise_post(str(e))


#//! Callback {cgen} ───────────────────────────────────────────────────────
def clbCookieGen(bot: object, update: object, gestion: object) -> None:
    if update.user_id != update.origin_uid:
        bot.showAlert(text='[ ⚠️ ] ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ', callback_id=update.query_id, alert=False); return

    country = str(update.data_query).replace('cgen', '').strip().upper()
    if country not in COUNTRIES:
        bot.showAlert(text='[ ⚠️ ] Invalid country', callback_id=update.query_id, alert=False); return

    user = gestion.view(user_id=update.user_id)
    cmd  = gestion.viewCmd('cgen')

    is_admin = user['rango'].lower() in gestion.rangos
    if not is_admin and str(user['credits']).lower() != 'unlimited':
        if int(user['credits']) < COST:
            bot.showAlert(text=f'[ ⚠️ ] Need {COST} credits, you have {user["credits"]}', callback_id=update.query_id, alert=True); return

    bot.showAlert(text=f'Generating {COUNTRIES[country]} account...', callback_id=update.query_id, alert=False)
    _execute(bot, update, gestion, user, cmd, country, message_id=update.message_id)


#//! Callback {savecookie} ────────────────────────────────────────────────
def clbSaveCookie(bot: object, update: object, gestion: object) -> None:
    if update.user_id != update.origin_uid:
        bot.showAlert(text='[ ⚠️ ] ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ', callback_id=update.query_id, alert=False); return
    bot.showAlert(text='[ ✅ ] Cookie already saved!', callback_id=update.query_id, alert=False)


#//! Internal execution ────────────────────────────────────────────────────
def _execute(bot, update, gestion, user, cmd, country, message_id=None):
    is_admin = user['rango'].lower() in gestion.rangos
    now      = time.time()
    charge   = '0 (admin)' if is_admin else str(COST)
    cmd_name = cmd['name'].title() if cmd and cmd.get('name') else 'Cookie Gen'

    if message_id:
        bot.editMessage(message_id,
            f"{E_RAINBOW}{bot.bi(cmd_name)} [ {E_BOLT} ]{E_HDR_END}\n"
            f"{E_BOLT} {bot.bi('Status')}: <code>Starting...</code>"
        )
        mid = message_id
    else:
        msg = bot.replyMessage(
            f"{E_RAINBOW}{bot.bi(cmd_name)} [ {E_BOLT} ]{E_HDR_END}\n"
            f"{E_BOLT} {bot.bi('Status')}: <code>Starting...</code>"
        )
        mid = msg.message_id

    bot.editMessage(mid,
        f"{E_RAINBOW}{bot.bi(cmd_name)} [ {E_BOLT} ]{E_HDR_END}\n{DIV_STARS}\n"
        f"{E_BOLT} {bot.bi('Status')}: <code>Generating...</code>\n"
        f"{E_GLOBE} {bot.bi('Country')}: <code>{COUNTRIES[country]}</code>\n"
        f"{E_USER} {bot.bi('User')}: {update.username}\n"
        f"{E_LETTER} {bot.bi('Charge')}: <code>{charge} credits</code>\n{DIV_STARS}"
    )

    result  = _generate_cookie(country)
    elapsed = f"{time.time() - now:.1f}s"

    if result and result.get('status'):
        if not is_admin and str(user['credits']).lower() != 'unlimited':
            gestion.update_user(str(user['user_id']), {'credits': str(int(user['credits']) - COST)})

        try:
            gestion.cookie_add(str(update.user_id), result['cookies'])
        except Exception:
            pass

        p      = result['profile']
        btn1   = bot.addButton(text="- 𝖘𝖆𝖛𝖊 𝖈𝖔𝖔𝖐𝖎𝖊 -", callback="savecookie")
        btn2   = bot.addButton(text="{ 𝕻𝖔𝖜𝖊𝖗𝖊𝖉𝕭𝖘 }", url="https://t.me/Sxgitario")
        markup = bot.replyMarkup(bot.addRow(btn1), bot.addRow(btn2))

        bot.editMessage(mid,
            f"{E_RAINBOW}{bot.bi(cmd_name)} [ {E_CHECK} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_CHECK} {bot.bi('Status')}: <code>Account Created ✅</code>\n"
            f"{E_GLOBE} {bot.bi('Country')}: <code>{COUNTRIES[country]}</code>\n"
            f"{E_LETTER} {bot.bi('Name')}: <code>{p['name']}</code>\n"
            f"{E_LETTER} {bot.bi('Email')}: <code>{p.get('email', 'N/A')}</code>\n"
            f"{E_LETTER} {bot.bi('Password')}: <code>{p['password']}</code>\n"
            f"{E_LETTER} {bot.bi('Billing')}: <code>{result.get('billingMessage', 'N/A')}</code>\n"
            f"{E_LETTER} {bot.bi('Charge')}: <code>{charge} credits</code>\n"
            f"{E_BOLT} {bot.bi('T. Taken')}: <code>{elapsed}</code>\n"
            f"{E_USER} {bot.bi('User')}: {update.username}\n{DIV_STARS}\n"
            f"{E_MONITOR} {bot.bi('Cookies')}:\n"
            f"<pre language=\"\">{result['cookies']}</pre>",
            reply_markup=markup
        )
    else:
        msg_err = result.get('message', 'Unknown error') if result else 'No response'
        bot.editMessage(mid,
            f"{E_RAINBOW}{bot.bi(cmd_name)} [ {E_RED} ]{E_HDR_END}\n{DIV_STARS}\n"
            f"{E_RED} {bot.bi('Status')}: <code>Failed</code>\n"
            f"{E_GLOBE} {bot.bi('Country')}: <code>{COUNTRIES[country]}</code>\n"
            f"{E_LETTER} {bot.bi('Reason')}: <code>{str(msg_err)[:120]}</code>\n"
            f"{E_LETTER} {bot.bi('Charge')}: <code>0 credits (not charged)</code>\n"
            f"{E_BOLT} {bot.bi('T. Taken')}: <code>{elapsed}</code>\n{DIV_STARS}"
        )

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

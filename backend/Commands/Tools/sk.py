# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import requests, time
from Commands.jill import *


def sk_check(stripe_key:str, bot) -> dict:
    try:
        responses = ['api_key_expired', 'invalid api key provided', 'testmode_charges_only']
        response  = requests.post(url='https://api.stripe.com/v1/tokens', headers={'Content-Type':'application/x-www-form-urlencoded'}, data="card[number]=5154620061414478&card[exp_month]=01&card[exp_year]=2023&card[cvc]=235", auth=(stripe_key, '')).text
        request   = [i for i in responses if i in response.lower()]
        if len(request) == 0:
            try:
                headers_bal = {'Authorization': f'bearer {stripe_key}'}
                bal_r = requests.get(url='https://api.stripe.com/v1/balance', headers=headers_bal).json()
                a = bal_r.get('available', [{}])[0]
                return {'status':'approved key ✅', 'response':'Live Key! ✅', 'amount':str(a.get('amount','?')), 'cards':str(a.get('source_types',{}).get('card','?')), 'currency':str(a.get('currency','?'))}
            except Exception:
                return {'status':'approved key ✅', 'response':'Live Key! ✅', 'amount':'?', 'cards':'?', 'currency':'?'}
        else:
            if request[0] != 'invalid api key provided': return {'status':'Dead Key ❌', 'response':request[0]}
            else: return {'status':'Dead Key ❌', 'response':'Invalid API Key!'}
    except Exception as a:
        bot.raise_post(str(a))
        return {'status':'Error ❌', 'response':'Error checking key, try again!'}


def skCMD(bot, update, gestion) -> None:
    try:
        now  = time.time()
        args = bot.cmd.args.replace(' ', '')
        user = gestion.view(user_id=update.user_id)
        chat = gestion.view(user_id=update.chat_id)
        cmd  = gestion.viewCmd(bot.cmd.command)
        bot.sendAction(action='typing')
        if user['ban'] == 'false':
            if chat['rango'] in gestion.prem:
                if cmd['status'] != 'unval':
                    if cmd['mode'] == 'on':
                        if len(args) > 0:
                            edit = bot.replyMessage(text=f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_BOLT} ]{E_HDR_END}\n{E_BOLT} {bot.bi('Status')}: <code>Waiting...</code>")
                            a = sk_check(args, bot)
                            if type(a) == dict:
                                masked = f"{args[0:10]}----------{args[-7:]}"
                                if a['status'] == 'approved key ✅':
                                    bot.editMessage(message_id=edit.message_id, text=(
                                        f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                                        f"{E_LETTER} {bot.bi('Key')}: <code>{masked}</code>\n"
                                        f"{E_BOLT} {bot.bi('Status')}: Live Key! {E_CHECK}\n"
                                        f"💳 {bot.bi('Balance')}: <code>{a['amount']}</code> (<code>{a['currency'].upper()}</code>)\n"
                                        f"💳 {bot.bi('Cards')}: <code>{a['cards']}</code>\n{DIV_STARS}\n"
                                        f"{E_BOLT} {bot.bi('T. Taken')}: <code>{str(round((time.time() - now), 1))}'s</code>\n"
                                        f"{E_USER} {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV_STARS}"
                                    ))
                                    bot.deleteMessage(update.chat_id, update.message_id)
                                else:
                                    bot.editMessage(message_id=edit.message_id, text=(
                                        f"{E_RAINBOW}{bot.bi(cmd['name'].title())} [ {E_LETTER} ]{E_HDR_END}\n{DIV_STARS}\n"
                                        f"{E_LETTER} {bot.bi('Key')}: <code>{masked}</code>\n"
                                        f"{E_BOLT} {bot.bi('Status')}: {a['status']}\n"
                                        f"{E_LETTER} {bot.bi('Response')}: <code>{a['response']}</code>\n{DIV_STARS}\n"
                                        f"{E_BOLT} {bot.bi('T. Taken')}: <code>{str(round((time.time() - now), 1))}'s</code>\n"
                                        f"{E_USER} {bot.bi('User')}: {update.username} [{user['c_name'].title()}]\n{DIV_STARS}"
                                    ))
                            else: bot.editMessage(message_id=edit.message_id, text=error('Use a Stripe Key!'))
                        else: bot.replyMessage(text=error(f"Use: /sk {cmd['use']}"))
                    elif cmd['mode'] == 'ma': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                    elif cmd['mode'] == 'of': bot.replyMessage(text=error(f"Command {gestion.modes[cmd['mode']]}!"))
                else: bot.replyMessage(text=error('This command is not yet registered!'))
            else: bot.replyMessage(text=error('This Chat Is Not Authorized!'))
        else: bot.replyMessage(text=error('You are banned from this bot!'))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

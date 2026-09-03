import secrets, datetime
from Commands.jill import *


def _get_cfg(gestion, key: str) -> str:
    r = gestion.no_commit("SELECT value FROM config WHERE key=%s", (key,))
    if r['status'] and r['data']:
        return r['data'][0][0]
    return ''


def _rotate_invite_link(bot, gestion, chat_id_key: str, link_key: str) -> None:
    chat_id  = _get_cfg(gestion, chat_id_key)
    old_link = _get_cfg(gestion, link_key)
    if not chat_id or not old_link:
        return
    try:
        resp = bot.curl.post(f"{bot.token}/createChatInviteLink",
                             json={"chat_id": chat_id}).json()
        if resp.get('ok'):
            new_link = resp['result']['invite_link']
            gestion.commit("UPDATE config SET value=%s WHERE key=%s", (new_link, link_key))
            bot.curl.post(f"{bot.token}/revokeChatInviteLink",
                          json={"chat_id": chat_id, "invite_link": old_link})
    except Exception:
        pass


def _send_vip_links(bot, update, gestion) -> None:
    vip_link      = _get_cfg(gestion, 'vip_link')
    scrapper_link = _get_cfg(gestion, 'scrapper_link')
    lines = [
        f"{E_RAINBOW}{bi('Welcome to JillChk')} [ 👑 ]{E_HDR_END}",
        DIV_STARS,
        f"💬 {bi('Chat Global')}: t.me/JillChkBotCha",
        f"📋 {bi('Referencias')}: t.me/JillChkBotRefs",
    ]
    if vip_link:
        lines.append(f"👑 {bi('VIP Group')}: {vip_link}")
    if scrapper_link:
        lines.append(f"🔍 {bi('Scrapper')}: {scrapper_link}")
    lines += [DIV_STARS, f"{E_BOLT} {bi('Info')}: <code>Links expire after use — keep them safe!</code>"]
    bot.sendMessage(text='\n'.join(lines), chat_id=str(update.user_id), preview=False)
    if vip_link:
        _rotate_invite_link(bot, gestion, 'vip_chat_id', 'vip_link')
    if scrapper_link:
        _rotate_invite_link(bot, gestion, 'scrapper_chat_id', 'scrapper_link')


def verify(_id: str) -> bool:
    return _id.isdigit() or _id.replace('-', '').isdigit()


def cmdRank(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion._rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading())
            if len(args) > 0:
                parts = args.split('|')
                if len(parts) >= 2 and parts[1].isdigit():
                    uid      = parts[0]
                    days_val = parts[1]
                    credits  = parts[2] if len(parts) >= 3 and parts[2].isdigit() else '100'
                    if verify(uid):
                        db = gestion.view(user_id=uid)
                        if db['ban'].lower() == 'false' and db['rango'].lower() != 'owner':
                            n_bill = gestion.addDays(days=days_val)
                            keep_name = db.get('c_name', 'premium') if db.get('c_name', 'free user') not in ('free user', 'premium', '') else 'premium'
                            gestion.commit("UPDATE users SET rango = %s, c_name = %s, n_bil = %s, spam = %s, credits = %s WHERE user_id = %s", ('premium', keep_name, str(n_bill), '40', credits, uid))
                            bot.adminRegister('Promote Premium', uid, f"{days_val}d +{credits}cr")
                            bot.editMessage(message_id=a.message_id, text=ok('Account Updated', ('Status', 'Premium'), ('Credits', credits), ('Days', days_val)))
                        else: bot.editMessage(message_id=a.message_id, text=error("User to promote is banned or an owner!"))
                    else: bot.editMessage(message_id=a.message_id, text=error("Insert Valid User or Chat ID!"))
                else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID & Credits!"))
            else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID & Credits!"))
    except Exception as e: bot.raise_post(str(e))


def cmdBan(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion.rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading())
            if len(args) > 0:
                uid = args.split('|')[0]
                if verify(uid):
                    if gestion.view(user_id=uid)['rango'].lower() == 'owner':
                        bot.editMessage(message_id=a.message_id, text=error("You cannot ban an owner!"))
                    else:
                        gestion.commit("UPDATE users SET c_name = %s, rango = %s, ban = %s, credits = %s, spam = %s WHERE user_id = %s", ('free user', 'free', 'true', '0', '60', uid))
                        bot.adminRegister('Ban User', uid)
                        bot.editMessage(message_id=a.message_id, text=ok('Account Banned', ('Status', 'Free User'), ('Ban', 'True')))
                else: bot.editMessage(message_id=a.message_id, text=error("Insert a Valid User ID!"))
            else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID!"))
    except Exception as e: bot.raise_post(str(e))


def cmdUban(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion.rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading())
            if len(args) > 0:
                uid = args.split('|')[0]
                if verify(uid):
                    db = gestion.view(user_id=uid)
                    if db['ban'].lower() == 'true':
                        gestion.commit("UPDATE users SET c_name = %s, rango = %s, ban = %s, credits = %s WHERE user_id = %s", ('free user', 'free', 'false', '0', uid))
                        bot.adminRegister('Unban User', uid)
                        bot.editMessage(message_id=a.message_id, text=ok('Account Unbanned', ('Status', 'Free User'), ('Ban', 'False')))
                    else: bot.editMessage(message_id=a.message_id, text=error("Insert a User ID from a banned user!"))
                else: bot.editMessage(message_id=a.message_id, text=error("Insert a Valid User ID!"))
            else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID!"))
    except Exception as e: bot.raise_post(str(e))


def cmdP(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        if update.reply_to is not None:
            bot.replyMessage(text=panel('Numbers ID', ('Chat ID', update.chat_id), ('User ID', update.reply_to.user_id)))
        else:
            bot.replyMessage(text=panel('Numbers ID', ('Chat ID', update.chat_id)))
    except Exception as e: bot.raise_post(str(e))


def cmdRname(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion.rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading())
            if len(args) > 0:
                parts = args.split('|')
                if len(parts) == 2:
                    if verify(parts[0]):
                        db = gestion.view(user_id=parts[0])
                        if db['ban'].lower() == 'false' and db['rango'].lower() != 'owner':
                            gestion.commit("UPDATE users SET c_name = %s WHERE user_id = %s", (parts[1], parts[0]))
                            bot.adminRegister('Rename User', parts[0], parts[1])
                            bot.editMessage(message_id=a.message_id, text=ok('Name Updated', ('User ID', parts[0]), ('Name', parts[1].lower())))
                        else: bot.editMessage(message_id=a.message_id, text=error("User to rename is banned or an owner!"))
                    else: bot.editMessage(message_id=a.message_id, text=error("Insert a Valid User ID."))
                else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID & New Name!"))
            else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID & New Name!"))
    except Exception as e: bot.raise_post(str(e))


def cmdCred(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion._rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading())
            if len(args) > 0:
                parts = args.split('|')
                if len(parts) == 2:
                    if parts[1].isdigit() and verify(parts[0]):
                        db = gestion.view(user_id=parts[0])
                        if db['ban'].lower() == 'false' and db['rango'].lower() != 'owner':
                            gestion.commit("UPDATE users SET credits = %s WHERE user_id = %s", (parts[1], parts[0]))
                            bot.adminRegister('Set Credits', parts[0], parts[1])
                            bot.editMessage(message_id=a.message_id, text=ok('Credits Updated', ('User ID', parts[0]), ('Credits', parts[1])))
                        else: bot.editMessage(message_id=a.message_id, text=error("User is banned or an owner!"))
                    else: bot.editMessage(message_id=a.message_id, text=error("Insert a Valid User ID."))
                else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID & New Balance!"))
            else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID & New Balance!"))
    except Exception as e: bot.raise_post(str(e))


def cmdDelay(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion._rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading())
            if len(args) > 0:
                parts = args.split('|')
                if len(parts) == 2:
                    if parts[1].isdigit() and verify(parts[0]):
                        db = gestion.view(user_id=parts[0])
                        if db['ban'].lower() == 'false' and db['rango'].lower() != 'owner':
                            gestion.commit("UPDATE users SET spam = %s WHERE user_id = %s", (parts[1], parts[0]))
                            bot.adminRegister('Set Delay', parts[0], parts[1])
                            bot.editMessage(message_id=a.message_id, text=ok('Delay Updated', ('User ID', parts[0]), ('Delay', f"{parts[1]}s")))
                        else: bot.editMessage(message_id=a.message_id, text=error("User is banned or an owner!"))
                    else: bot.editMessage(message_id=a.message_id, text=error("Insert a Valid User ID."))
                else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID & New Delay!"))
            else: bot.editMessage(message_id=a.message_id, text=error("Insert User ID & New Delay!"))
    except Exception as e: bot.raise_post(str(e))


def cmdKey(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion._rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading())
            if len(args) > 0:
                if len(args.split('|')) == 2:
                    if args.split('|')[0].isdigit() and args.split('|')[1].isdigit():
                        _alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
                        key = f"JillChk-{''.join(secrets.choice(_alpha) for _ in range(5))}-{''.join(secrets.choice(_alpha) for _ in range(5))}"
                        gestion.commit("INSERT INTO keys (key, days, credits, status) VALUES(%s, %s, %s, %s)", (key, args.split('|')[0], args.split('|')[1], 'active'))
                        bot.adminRegister('Generate Key', detail=f"{args.split('|')[0]}d {args.split('|')[1]}cr key={key}")
                        bot.editMessage(message_id=a.message_id, text=ok('Key Created', ('Key', key), ('Days', args.split('|')[0]), ('Credits', args.split('|')[1]), ('Use', '/claim Gift Code')))
                    else: bot.editMessage(message_id=a.message_id, text=error("Insert correct numbers!"))
                else: bot.editMessage(message_id=a.message_id, text=error("Insert Days & Credits"))
            else: bot.editMessage(message_id=a.message_id, text=error("Insert Days & Credits!"))
    except Exception as e: bot.raise_post(str(e))


def cmdClaim(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '')
        db   = gestion.view(user_id=update.user_id)
        a    = bot.replyMessage(text=loading())
        if db['ban'].lower() != 'true':
            if len(args) > 0:
                i = gestion.vKey(key=args)
                if i['status'] == True:
                    if i['mode'] == 'active':
                        if db['rango'] in gestion.rangos:
                            bot.editMessage(message_id=a.message_id, text=error("You Are Staff Member!"))
                        else:
                            try:
                                new_credits = str(int(db['credits']) + int(i['credits'])) if db['credits'].lower() != 'unlimited' else 'unlimited'
                            except (ValueError, TypeError):
                                new_credits = i['credits']
                            base = None
                            if db['rango'].lower() == 'premium':
                                exp = gestion._set(db.get('n_bil', ''))
                                if exp and exp > datetime.datetime.now():
                                    base = exp
                            b = gestion.addDays(days=i['days'], base=base)
                            gestion.commit("UPDATE users SET credits = %s, n_bil = %s, c_name = %s, rango = %s, spam = %s WHERE user_id = %s", (new_credits, str(b), 'premium', 'premium', '40', update.user_id))
                            gestion.commit("UPDATE keys SET status = %s WHERE key = %s", ('claim', i['key']))
                            bot.adminRegister('Key Claimed', str(update.user_id), f"+{i['days']}d +{i['credits']}cr")
                            bot.editMessage(message_id=a.message_id, text=ok('Account Updated', ('Status', 'Premium'), ('Credits', new_credits), ('Days', i['days'])))
                            _send_vip_links(bot, update, gestion)
                    else: bot.editMessage(message_id=a.message_id, text=error("The code has already been redeemed!"))
                else: bot.editMessage(message_id=a.message_id, text=error("The code does NOT exist!"))
            else: bot.editMessage(message_id=a.message_id, text=error("Insert Key to Redeem!"))
        else: bot.editMessage(message_id=a.message_id, text=error("You Are Banned From This Bot!"))
    except Exception as e: bot.raise_post(str(e))


def cmdAdmin(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'].lower() != 'owner':
            return
        bot.sendAction(action='typing')
        a   = bot.replyMessage(text=loading())
        uid = update.reply_to.user_id if update.reply_to is not None else bot.cmd.args.replace(' ', '')
        if not uid or not verify(uid):
            return bot.editMessage(message_id=a.message_id, text=error("Insert a Valid User ID!"))
        target = gestion.view(user_id=uid)
        if target['rango'].lower() in gestion.rangos:
            return bot.editMessage(message_id=a.message_id, text=error("This user is already a staff member!"))
        btn1 = bot.addButton(text='- 𝗬𝗘𝗦 -', callback=f'promote {uid}')
        btn2 = bot.addButton(text='- 𝗡𝗢 -',  callback='clean')
        bot.editMessage(message_id=a.message_id, reply_markup=bot.replyMarkup(bot.addRow(btn1, btn2)),
            text=confirm('Owner Confirmation', uid, 'This user will become ADMIN with access to staff commands.'))
    except Exception as e: bot.raise_post(str(e))


def cmdUnadmin(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'].lower() != 'owner':
            return
        bot.sendAction(action='typing')
        a   = bot.replyMessage(text=loading())
        uid = update.reply_to.user_id if update.reply_to is not None else bot.cmd.args.replace(' ', '')
        if not uid or not verify(uid):
            return bot.editMessage(message_id=a.message_id, text=error("Insert a Valid User ID!"))
        target = gestion.view(user_id=uid)
        if target['rango'].lower() not in gestion.rangos:
            return bot.editMessage(message_id=a.message_id, text=error("This user is not a staff member!"))
        if target['rango'].lower() == 'owner':
            return bot.editMessage(message_id=a.message_id, text=error("You cannot demote an owner!"))
        btn1 = bot.addButton(text='- 𝗬𝗘𝗦 -', callback=f'unpromote {uid}')
        btn2 = bot.addButton(text='- 𝗡𝗢 -',  callback='clean')
        bot.editMessage(message_id=a.message_id, reply_markup=bot.replyMarkup(bot.addRow(btn1, btn2)),
            text=confirm('Owner Confirmation', uid, 'This user will be demoted to free and lose all staff access.'))
    except Exception as e: bot.raise_post(str(e))


def cmdSetLink(bot, update, gestion) -> None:
    """Set VIP/Scrapper chat IDs or links. Usage: /setlink vip|CHAT_ID  or  /setlink scrapper|CHAT_ID"""
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'].lower() != 'owner':
            return
        bot.sendAction(action='typing')
        a    = bot.replyMessage(text=loading())
        args = bot.cmd.args.strip()
        if not args or '|' not in args:
            return bot.editMessage(message_id=a.message_id, text=error(
                "Use: /setlink vip|CHAT_ID  or  /setlink scrapper|CHAT_ID"))
        parts   = args.split('|', 1)
        target  = parts[0].strip().lower()
        value   = parts[1].strip()
        key_map = {
            'vip':      'vip_chat_id',
            'scrapper': 'scrapper_chat_id',
        }
        if target not in key_map:
            return bot.editMessage(message_id=a.message_id, text=error("Target must be 'vip' or 'scrapper'"))
        cfg_key = key_map[target]
        gestion.commit(
            "INSERT INTO config (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value=%s",
            (cfg_key, value, value)
        )
        bot.editMessage(message_id=a.message_id,
            text=ok('Config Updated', ('Key', cfg_key), ('Value', value[:40])))
    except Exception as e: bot.raise_post(str(e))

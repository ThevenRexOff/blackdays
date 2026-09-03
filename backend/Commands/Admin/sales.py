# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import datetime
from Commands.Admin.rangos import verify

DIV = "────────────────────"


def _money(v) -> str:
    try:
        v = float(v)
        return f"{int(v):,}" if v == int(v) else f"{v:,.2f}"
    except (ValueError, TypeError):
        return str(v)


def _err(bot, msg: str) -> str:
    return f"{bot.bi('Wrong Data')} [ ⚠️ ]\n🍸 {bot.bi('Raise')}: <code>{msg}</code>"


# ─── /prices — public price list ─────────────────────────────────────────────
def cmdPrices(bot, update, gestion) -> None:
    try:
        bot.sendAction(action='typing')
        plans = gestion.view_plans()
        if not plans:
            return bot.replyMessage(text=f"{bot.bi('Price List')} [ 💰 ]\n{DIV}\n🍸 {bot.bi('No plans configured yet')}")
        lines = ''.join(f"🍸 {bot.bi(p[0])}: <code>${_money(p[3])}</code> · {p[1]}d\n" for p in plans)
        bot.replyMessage(text=f"{bot.bi('Price List')} [ 💰 ]\n{DIV}\n{lines}{DIV}\n🍸 {bot.bi('Buy')}: <code>contact an admin or seller</code>")
    except Exception as e: bot.raise_post(str(e))


# ─── /sell uid|plan|method — register a sale (owner/admin/seller) ─────────────
def cmdSell(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion.sellers:
            return
        bot.sendAction(action='typing')
        a     = bot.replyMessage(text=f"{bot.bi('Fetching Data')} [ 🍸 ]\n🍸 {bot.bi('Status')}: <code>Waiting...</code>")
        use   = f"{bot.bi('Sell')} [ 💰 ]\n🍸 {bot.bi('Use')}: <code>/sell uid|plan|method</code>\n🍸 {bot.bi('Plans')}: <code>/prices</code>"
        parts = [p.strip() for p in bot.cmd.args.split('|')]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            return bot.editMessage(message_id=a.message_id, text=use)
        uid, plan_name = parts[0], parts[1]
        method = parts[2] if len(parts) > 2 and parts[2] else 'N/A'
        if not verify(uid):
            return bot.editMessage(message_id=a.message_id, text=_err(bot, 'Insert a valid User ID!'))
        plan = gestion.view_plan(plan_name)
        if not plan['status']:
            return bot.editMessage(message_id=a.message_id, text=_err(bot, f"Plan not found — see /prices"))
        target = gestion.view(user_id=uid)
        if target['rango'].lower() == 'owner':
            return bot.editMessage(message_id=a.message_id, text=_err(bot, 'You cannot sell a plan to an owner!'))

        # Extend from current expiry if the client is already an active premium, else from now
        base = None
        if target['rango'].lower() == 'premium':
            exp = gestion._set(target.get('n_bil', ''))
            if exp and exp > datetime.datetime.now():
                base = exp
        n_bil = gestion.addDays(days=plan['days'], base=base)
        gestion.commit("UPDATE users SET rango = %s, c_name = %s, n_bil = %s, spam = %s, credits = %s WHERE user_id = %s",
                       ('premium', 'premium', str(n_bil), '40', str(plan['credits']), uid))
        gestion._view_cache.pop(str(uid), None)

        seller_name = (update.username or '').lstrip('@') or db.get('nombre') or db.get('c_name') or str(update.user_id)
        gestion.record_sale(update.user_id, seller_name, plan['name'], plan['price'], uid, method)
        bot.adminRegister('Sale', uid, f"{plan['name']} ${_money(plan['price'])} via {method}")

        bot.editMessage(message_id=a.message_id, text=(
            f"{bot.bi('Sale Registered')} [ 💰 ]\n{DIV}\n"
            f"🍸 {bot.bi('Plan')}: <code>{plan['name']}</code>\n"
            f"💳 {bot.bi('Price')}: <code>${_money(plan['price'])}</code>\n"
            f"👤 {bot.bi('Client')}: <code>{uid}</code>\n"
            f"🍸 {bot.bi('Method')}: <code>{method}</code>\n"
            f"⚡ {bot.bi('Days')}: <code>{plan['days']}d</code>\n{DIV}\n"
            f"👤 {bot.bi('Seller')}: @{seller_name}"
        ))
    except Exception as e: bot.raise_post(str(e))


# ─── /sales — monthly sales report ───────────────────────────────────────────
def cmdSales(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion.sellers:
            return
        bot.sendAction(action='typing')
        staff = db['rango'] in gestion._rangos                 # owner/admin -> can see global + others
        arg   = bot.cmd.args.strip().split('|')[0].strip()

        if staff and arg:                                       # /sales <seller_uid>
            rep  = gestion.sales_report(seller_id=arg)
            _t   = gestion.view(user_id=arg)
            name = (_t.get('nombre') or _t.get('c_name') or arg)
            return bot.replyMessage(text=_fmt_seller(bot, rep, name))
        if not staff:                                           # a seller sees only their own
            name = (update.username or '').lstrip('@') or db.get('nombre') or db.get('c_name') or str(update.user_id)
            return bot.replyMessage(text=_fmt_seller(bot, gestion.sales_report(seller_id=update.user_id), name))

        # owner/admin -> global monthly report + per-seller breakdown
        rep   = gestion.sales_report()
        block = _fmt_global(bot, rep)
        sellers = gestion.sellers_report()
        if sellers:
            block += f"\n{DIV}\n👤 {bot.bi('By Seller')}\n"
            block += ''.join(f"🍸 @{(s[1] or s[0])}: <code>{s[2]}</code> → <code>${_money(s[3])}</code>\n" for s in sellers)
        bot.replyMessage(text=block)
    except Exception as e: bot.raise_post(str(e))


def _fmt_global(bot, rep) -> str:
    out = f"📊 {bot.bi('Reporte de Ventas del Mes')}\n{DIV}\n"
    if not rep['plans']:
        return out + f"🍸 {bot.bi('No sales this month yet')}"
    for plan, count, total, unit in rep['plans']:
        out += (f"🟣 {bot.bi(plan)}\n"
                f"🍸 {bot.bi('Ventas')}: <code>{count}</code>\n"
                f"💳 {bot.bi('Precio')}: <code>${_money(unit)}</code>\n"
                f"💰 {bot.bi('Total')}: <code>${_money(total)}</code>\n{DIV}\n")
    out += f"💰 {bot.bi('Total general')}: <code>${_money(rep['total'])}</code>\n🧾 {bot.bi('Ventas totales')}: <code>{rep['count']}</code>"
    return out


def _fmt_seller(bot, rep, name) -> str:
    out = f"📊 {bot.bi('Reporte de Ventas del Mes')}\n👤 {bot.bi('Seller')}: @{name}\n{DIV}\n"
    if not rep['plans']:
        return out + f"🍸 {bot.bi('No sales this month yet')}"
    for plan, count, total, unit in rep['plans']:
        out += f"🟣 {bot.bi(plan)}: <code>{count}</code> ventas = <code>${_money(total)}</code>\n"
    out += f"{DIV}\n🧾 {bot.bi('Total ventas')}: <code>{rep['count']}</code>\n💰 {bot.bi('Total generado')}: <code>${_money(rep['total'])}</code>"
    return out


# ─── /seller, /unseller — manage the seller role (owner/admin) ────────────────
def cmdSeller(bot, update, gestion) -> None:
    _set_seller(bot, update, gestion, promote=True)


def cmdUnseller(bot, update, gestion) -> None:
    _set_seller(bot, update, gestion, promote=False)


def _set_seller(bot, update, gestion, promote: bool) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] not in gestion._rangos:
            return
        bot.sendAction(action='typing')
        a   = bot.replyMessage(text=f"{bot.bi('Fetching Data')} [ 🍸 ]\n🍸 {bot.bi('Status')}: <code>Waiting...</code>")
        uid = update.reply_to.user_id if update.reply_to is not None else bot.cmd.args.replace(' ', '')
        if not uid or not verify(uid):
            return bot.editMessage(message_id=a.message_id, text=_err(bot, 'Insert a valid User ID!'))
        target = gestion.view(user_id=uid)
        if target['rango'].lower() in gestion.rangos:
            return bot.editMessage(message_id=a.message_id, text=_err(bot, 'This user is a staff member!'))
        if promote:
            gestion.commit("UPDATE users SET rango = %s, c_name = %s WHERE user_id = %s", ('seller', 'seller', uid))
            gestion._view_cache.pop(str(uid), None)
            bot.adminRegister('Promote Seller', uid)
            bot.editMessage(message_id=a.message_id, text=f"{bot.bi('User Updated')} [ 📈 ]\n{DIV}\n👤 {bot.bi('UID')}: <code>{uid}</code>\n🍸 {bot.bi('Rank')}: <code>Seller</code>")
        else:
            if target['rango'].lower() != 'seller':
                return bot.editMessage(message_id=a.message_id, text=_err(bot, 'This user is not a seller!'))
            gestion.commit("UPDATE users SET rango = %s, c_name = %s WHERE user_id = %s", ('free', 'free user', uid))
            gestion._view_cache.pop(str(uid), None)
            bot.adminRegister('Demote Seller', uid)
            bot.editMessage(message_id=a.message_id, text=f"{bot.bi('User Updated')} [ 📉 ]\n{DIV}\n👤 {bot.bi('UID')}: <code>{uid}</code>\n🍸 {bot.bi('Rank')}: <code>Free</code>")
    except Exception as e: bot.raise_post(str(e))


# ─── /addplan, /delplan — manage plans (owner) ───────────────────────────────
def cmdAddPlan(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] != 'owner':
            return
        bot.sendAction(action='typing')
        a     = bot.replyMessage(text=f"{bot.bi('Fetching Data')} [ 🍸 ]\n🍸 {bot.bi('Status')}: <code>Waiting...</code>")
        use   = f"{bot.bi('Add Plan')} [ 💰 ]\n🍸 {bot.bi('Use')}: <code>/addplan name|days|credits|price</code>\n🍸 {bot.bi('Example')}: <code>/addplan Premium 31 días|31|unlimited|50</code>"
        parts = [p.strip() for p in bot.cmd.args.split('|')]
        if len(parts) != 4 or not parts[0] or not parts[1].isdigit():
            return bot.editMessage(message_id=a.message_id, text=use)
        name, days, credits, price = parts
        try: float(price)
        except ValueError: return bot.editMessage(message_id=a.message_id, text=_err(bot, 'Price must be a number!'))
        r = gestion.add_plan(name, days, credits, price)
        if not r['status']:
            return bot.editMessage(message_id=a.message_id, text=_err(bot, 'Could not save plan!'))
        bot.adminRegister('Add Plan', name, f"{days}d {credits}cr ${_money(price)}")
        bot.editMessage(message_id=a.message_id, text=f"{bot.bi('Plan Saved')} [ ✅ ]\n{DIV}\n🍸 {bot.bi('Plan')}: <code>{name}</code>\n⚡ {bot.bi('Days')}: <code>{days}d</code>\n💳 {bot.bi('Price')}: <code>${_money(price)}</code> | {bot.bi('Credits')}: <code>{credits}</code>")
    except Exception as e: bot.raise_post(str(e))


def cmdDelPlan(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] != 'owner':
            return
        bot.sendAction(action='typing')
        a    = bot.replyMessage(text=f"{bot.bi('Fetching Data')} [ 🍸 ]\n🍸 {bot.bi('Status')}: <code>Waiting...</code>")
        name = bot.cmd.args.strip()
        if not name:
            return bot.editMessage(message_id=a.message_id, text=f"{bot.bi('Del Plan')} [ 💰 ]\n🍸 {bot.bi('Use')}: <code>/delplan plan name</code>")
        gestion.del_plan(name)
        bot.adminRegister('Delete Plan', name)
        bot.editMessage(message_id=a.message_id, text=f"{bot.bi('Plan Deleted')} [ 🗑 ]\n{DIV}\n🍸 {bot.bi('Plan')}: <code>{name}</code>")
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

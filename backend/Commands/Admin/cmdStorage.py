# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
from Commands.jill import *


def add(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] == 'owner':
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading('Build Data'))
            if len(args) > 0:
                args = args.split('|')
                if len(args) == 6:
                    if args[1] in gestion.modes.keys():
                        if args[2] in gestion._types:
                            comment = args[4] if args[4] != 'none' else 'no comment'
                            gestion.addC(cmd=args[0], mode=args[1], typec=args[2], comment=args[4], name=args[3], use=args[5])
                            bot.adminRegister('Add Command', args[0], f"{args[2]} · {args[1]}")
                            bot.editMessage(message_id=a.message_id, text=ok('Command Added', ('Name', args[3].title()), ('Command', f"/{args[0]} {args[5]}"), ('Type', args[2].title()), ('Comment', comment.title())))
                        else: bot.editMessage(message_id=a.message_id, text=error('Insert a correct type; Charge, Auth, Ccn, Tool'))
                    else: bot.editMessage(message_id=a.message_id, text=error('Insert a correct mode, OF, ON or MA'))
                else: bot.editMessage(message_id=a.message_id, text=error('Insert a cmd|mode|type|name|comment(or None)|use'))
            else: bot.editMessage(message_id=a.message_id, text=error('Insert a cmd|mode|type|name|comment(or None)|use'))
    except Exception as e: bot.raise_post(str(e))


def delc(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion._rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading('Build Data'))
            if len(args) > 0:
                db1 = gestion.viewCmd(args)
                if db1['status'] != 'unval':
                    gestion.delC(args)
                    bot.adminRegister('Delete Command', args)
                    bot.editMessage(message_id=a.message_id, text=ok('Command Deleted', ('Command', f"/{args.lower()}")))
                else: bot.editMessage(message_id=a.message_id, text=error("This Command Don't Exist!"))
            else: bot.editMessage(message_id=a.message_id, text=error('Insert a key command!'))
    except Exception as e: bot.raise_post(str(e))


def viewc(bot, update, gestion) -> None:
    try:
        args = bot.cmd.args.replace(' ', '').lower()
        db   = gestion.view(user_id=update.user_id)
        if db['rango'] in gestion._rangos:
            bot.sendAction(action='typing')
            a = bot.replyMessage(text=loading('Build Data'))
            if len(args) > 0:
                db1 = gestion.viewCmd(args)
                if db1['status'] != 'unval':
                    fields = [
                        ('Name',    db1['name'].title()),
                        ('Command', f"/{db1['command']} {db1['use']}"),
                        ('Mode',    f"{db1['mode'].upper()} [{db1['emoji']}]"),
                        ('Type',    db1['type']),
                        ('Review',  db1['review']),
                    ]
                    if db1['comment'] != 'none':
                        fields.append(('Comment', db1['comment'].title()))
                    bot.editMessage(message_id=a.message_id, text=ok('Command Stats', *fields))
                else: bot.editMessage(message_id=a.message_id, text=error("This Command Don't Exist!"))
            else: bot.editMessage(message_id=a.message_id, text=error('Insert a key command!'))
    except Exception as e: bot.raise_post(str(e))


def cmdMod(bot, update, gestion) -> None:
    try:
        db = gestion.view(user_id=update.user_id)
        if db['rango'] != 'owner':
            return
        bot.sendAction(action='typing')
        a    = bot.replyMessage(text=loading('Build Data'))
        args = bot.cmd.args
        use  = error('Use: /mod -c command -o field -v value')

        if not args:
            return bot.editMessage(message_id=a.message_id, text=use)

        data = [False, False, False]
        for i in args.split(' -'):
            parts = i.split(' ', 1)
            head  = parts[0].lower().lstrip('-')
            val   = parts[1].strip() if len(parts) > 1 else ''
            if   head == 'c': data[0] = val
            elif head == 'o': data[1] = val
            elif head == 'v': data[2] = val
        if False in data or '' in data:
            return bot.editMessage(message_id=a.message_id, text=use)

        command = gestion.viewCmd(data[0])
        if command.get('status') == 'unval' or not command.get('status'):
            return bot.editMessage(message_id=a.message_id, text=error("Command doesn't exist!"))

        result = gestion.update_cmd_field(data[0], data[1].lower(), data[2])
        if not result['status']:
            return bot.editMessage(message_id=a.message_id, text=error('Invalid field! Use: type, name, status, comment, use'))

        command = gestion.viewCmd(data[0])
        bot.adminRegister('Command Modifier', data[0], f"{data[1].lower()}={data[2]}")
        bot.editMessage(message_id=a.message_id, text=ok(
            'Command Updated',
            ('Command', f"/{command['command']}"),
            ('Field', data[1].lower()),
            ('Name', command['name'].title()),
            ('Mode', f"{command['mode'].upper()} [{command['emoji']}]"),
            ('Type', command['type'].title()),
        ))
    except Exception as e: bot.raise_post(str(e))

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

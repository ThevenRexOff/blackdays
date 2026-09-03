# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
import sys
from Model import BotX


def build_bot(query: str):
    """Register every command/callback and return a ready BotX.
    Shared by BOTH run modes so the handlers are identical:
      • webhook  — index.php runs `python3 main.py <update>` per update (this file's __main__).
      • polling  — poll.py calls build_bot(update).compile_bot() in a loop."""
    bot = BotX(query=query)

    #? COMMANDS (STAFF)
    bot.addCommand('id',      'Commands.Admin.rangos:cmdP')
    bot.addCommand('p',       'Commands.Admin.rangos:cmdP')
    bot.addCommand('start',   'Commands.Admin.start:cmdStart')
    bot.addCommand('claim',   'Commands.Admin.rangos:cmdClaim')
    bot.addCommand('myinfo',  'Commands.Admin.myinfo:cmdMyInfo')
    bot.addCommand('myacc',   'Commands.Admin.myinfo:cmdMyInfo')
    bot.addCommand('info',    'Commands.Admin.users:cmdInfo')
    bot.addCommand('cookie',  'Commands.Admin.users:cmdCookie')
    bot.addCommand('cmds',    'Commands.Admin.cmd:cmdHelp')
    bot.addCommand('rban',    'Commands.Admin.rangos:cmdBan')
    bot.addCommand('key',     'Commands.Admin.rangos:cmdKey')
    bot.addCommand('ruban',   'Commands.Admin.rangos:cmdUban')
    bot.addCommand('user',    'Commands.Admin.usr:cmdUser')
    bot.addCommand('prmn',    'Commands.Admin.rangos:cmdRank')
    bot.addCommand('admin',   'Commands.Admin.rangos:cmdAdmin')
    bot.addCommand('unadmin',  'Commands.Admin.rangos:cmdUnadmin')
    bot.addCommand('setlink', 'Commands.Admin.rangos:cmdSetLink')
    bot.addCommand('addcmd',  'Commands.Admin.cmdStorage:add')
    bot.addCommand('cred',    'Commands.Admin.rangos:cmdCred')
    bot.addCommand('rname',   'Commands.Admin.rangos:cmdRname')
    bot.addCommand('delcmd',  'Commands.Admin.cmdStorage:delc')
    bot.addCommand('mod',     'Commands.Admin.cmdStorage:cmdMod')
    bot.addCommand('stat_c',  'Commands.Admin.cmdStorage:viewc')
    bot.addCommand('delay',   'Commands.Admin.rangos:cmdDelay')
    bot.addCommand('binban',  'Commands.Admin.bban:cmdBinBan')
    bot.addCommand('bban',    'Commands.Admin.bban:cmdBinBan')
    bot.addCommand('rbin',    'Commands.Admin.bban:cmdBinBan')
    bot.addCommand('broadcast', 'Commands.Admin.broadcast:cmdBroadcast')
    bot.addCommand('gusers',    'Commands.Admin.broadcast:cmdGusers')

    #? HISTORY / TICKETS / SUPPORT
    bot.addCommand('history', 'Commands.Admin.history:cmdHistory')
    bot.addCommand('tickets', 'Commands.Admin.tickets:cmdTickets')
    bot.addCommand('tk',      'Commands.Admin.tickets:cmdTicketView')
    bot.addCommand('tclose',  'Commands.Admin.tickets:cmdCloseTicket')

    #? SALES / SELLERS / PLANS
    bot.addCommand('sell',    'Commands.Admin.sales:cmdSell')
    bot.addCommand('vender',  'Commands.Admin.sales:cmdSell')
    bot.addCommand('sales',   'Commands.Admin.sales:cmdSales')
    bot.addCommand('ventas',  'Commands.Admin.sales:cmdSales')
    bot.addCommand('seller',  'Commands.Admin.sales:cmdSeller')
    bot.addCommand('unseller','Commands.Admin.sales:cmdUnseller')
    bot.addCommand('addplan', 'Commands.Admin.sales:cmdAddPlan')
    bot.addCommand('delplan', 'Commands.Admin.sales:cmdDelPlan')

    #? COMMANDS (USERS)
    bot.addCommand('prices',  'Commands.Admin.sales:cmdPrices')
    bot.addCommand('precios', 'Commands.Admin.sales:cmdPrices')
    bot.addCommand('ticket',  'Commands.Admin.tickets:cmdTicket')
    bot.addCommand('ref',     'Commands.Admin.refs:cmdRef')
    bot.addCommand('links',   'Commands.Admin.refs:cmdLinks')
    bot.addCommand('bin',   'Commands.Tools.binc:cmdBin')
    bot.addCommand('fake',  'Commands.Tools.addr:cmdAddr')
    bot.addCommand('nm',    'Commands.Tools.number:cmdNm')
    bot.addCommand('ip',    'Commands.Tools.ip_l:cmdIp')
    bot.addCommand('gen',   'Commands.Tools.cc_gen:cmdGen')
    bot.addCommand('sk',    'Commands.Tools.sk:skCMD')
    bot.addCommand('site',  'Commands.Tools.site:cmdSite')
    bot.addCommand('tmail', 'Commands.Tools.tmail:cmdTmail')
    bot.addCommand('cgen',  'Commands.Tools.cookiegen:cmdCookieGen')

    #? GATEWAYS
    bot.addCommand('mass',  'Commands.Gates.mass:gateCmd')
    bot.addCommand('amz',   'Commands.Gates.amazon:gateCmd')
    bot.addCommand('amzg',  'Commands.Gates.amazon:gateCmd')
    bot.addCommand('tcl',   'Commands.Gates.telcel:gateCmd')
    bot.addCommand('mj',    'Commands.Gates.mj:gateCmd') # listo
    bot.addCommand('mm',    'Commands.Gates.mm:gateCmd')
    bot.addCommand('wr',    'Commands.Gates.wr:gateCmd')
    # bot.addCommand('ts',    'Commands.Gates.ts:gateCmd')
    # bot.addCommand('gt',    'Commands.Gates.gtgateCmd:')
    bot.addCommand('br',    'Commands.Gates.br:gateCmd')# listo
    # bot.addCommand('cp',    'Commands.Gates.cp:gateCmd') 
    bot.addCommand('bl',    'Commands.Gates.bl:gateCmd')
    bot.addCommand('zb',    'Commands.Gates.zb:gateCmd')
    bot.addCommand('ps',    'Commands.Gates.ps:gateCmd')
    bot.addCommand('dns',   'Commands.Gates.dns:gateCmd')
    bot.addCommand('wu',    'Commands.Gates.wu:gateCmd')
    bot.addCommand('rc',    'Commands.Gates.rc:gateCmd')
    bot.addCommand('op',    'Commands.Gates.op:gateCmd')
    bot.addCommand('pd',    'Commands.Gates.pd:gateCmd')
    bot.addCommand('em',    'Commands.Gates.netflix:gateCmd')

    #? CALLBACKS
    bot.addCallback('tools',        'Commands.Admin.callbacks:callback_tools')
    bot.addCallback('user',         'Commands.Admin.callbacks:callback_user')
    bot.addCallback('gates',        'Commands.Admin.callbacks:callback_gates')
    bot.addCallback('mass_info',    'Commands.Admin.callbacks:callback_mass_info')
    bot.addCallback('auths',        'Commands.Admin.callbacks:c_cmds_gates_type')
    bot.addCallback('charged',      'Commands.Admin.callbacks:c_cmds_gates_type')
    bot.addCallback('specials',     'Commands.Admin.callbacks:c_cmds_gates_type')
    bot.addCallback('ccn',          'Commands.Admin.callbacks:c_cmds_gates_type')
    bot.addCallback('avs',          'Commands.Admin.callbacks:c_cmds_gates_type')
    bot.addCallback('clean',        'Commands.Admin.callbacks:clean_query')
    bot.addCallback('promote',      'Commands.Admin.callbacks:promote')
    bot.addCallback('unpromote',    'Commands.Admin.callbacks:unpromote')
    bot.addCallback('rg_fake',      'Commands.Admin.callbacks:rg_fake')
    bot.addCallback('rg_ccs',       'Commands.Admin.callbacks:rg_ccs')
    bot.addCallback('return_tools', 'Commands.Admin.callbacks:callback_return')
    bot.addCallback('pg',           'Commands.Admin.callbacks:cmds_nav')
    bot.addCallback('pgn',          'Commands.Admin.callbacks:pgn')
    bot.addCallback('tmail_refresh', 'Commands.Tools.tmail:tmail_refresh')
    bot.addCallback('tmail_copy',   'Commands.Tools.tmail:tmail_copy')
    bot.addCallback('tmail_read',   'Commands.Tools.tmail:tmail_read')
    bot.addCallback('tmail_new',    'Commands.Tools.tmail:tmail_new')
    bot.addCallback('cgen',         'Commands.Tools.cookiegen:clbCookieGen')
    bot.addCallback('savecookie',   'Commands.Tools.cookiegen:clbSaveCookie')
    bot.addCallback('ps_monto',     'Commands.Gates.ps:ps_monto_cb')
    bot.addCallback('tcl_monto',    'Commands.Gates.telcel:tcl_monto_cb')

    return bot


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) >= 2 else ''
    if len(sys.argv) < 2:
        raise SystemExit(0)
    build_bot(query).compile_bot()

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

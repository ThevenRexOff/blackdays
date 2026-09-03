
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ██╗  ██╗██╗   ██╗███████╗██╗   ██╗ █████╗  ██████╗                   ║
║   ███╗ ██║██║   ██║██╔════╝██║   ██║██╔══██╗██╔════╝                   ║
║   ████╗██║██║   ██║█████╗  ██║   ██║███████║╚█████╗                    ║
║   ██╔████║██║   ██║██╔══╝  ╚██╗ ██╔╝██╔══██║ ╚═══██╗                   ║
║   ██║╚███║╚██████╔╝███████╗ ╚████╔╝ ██║  ██║██████╔╝                   ║
║   ╚═╝ ╚══╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚═════╝                    ║
║                                                                          ║
║            C Ó M O   A G R E G A R   T O O L S   Y   G A T E S          ║
╚══════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════
  VISIÓN GENERAL
═══════════════════════════════════════════════════════════════════════════

  Agregar un nuevo comando al bot requiere 3 pasos en todos los casos:

  ┌──────────────────────────────────────────────────────────────────────┐
  │                                                                      │
  │   PASO 1 ─── Crear el archivo .py con la función del comando         │
  │   PASO 2 ─── Registrar el comando en main.py                         │
  │   PASO 3 ─── Insertar la fila en la tabla comandos de la DB          │
  │                                                                      │
  └──────────────────────────────────────────────────────────────────────┘

  Diferencia entre Tool y Gate:

  ┌────────────────────────────┬───────────────────────────────────────┐
  │  TOOL                      │  GATE                                 │
  ├────────────────────────────┼───────────────────────────────────────┤
  │  Herramienta informativa   │  Hace cargo o verificación de tarjeta │
  │  No consume crédito        │  Consume crédito por uso              │
  │  No hace BIN lookup        │  Hace BIN lookup y anti-abuse         │
  │  Archivo en Commands/Tools │  Archivo en Commands/Gates            │
  │  tipo = 'tool'             │  tipo = 'charge' | 'mass' | 'auth'   │
  └────────────────────────────┴───────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  AGREGAR UN NUEVO TOOL
═══════════════════════════════════════════════════════════════════════════

  ──────────────────────────────────────────────────────────────────────
  PASO 1 — Crear Commands/Tools/mitool.py
  ──────────────────────────────────────────────────────────────────────

  Patrón estándar de un tool. Todos los tools siguen esta misma estructura:

  ┌──────────────────────────────────────────────────────────────────────┐
  │  import time                                                         │
  │                                                                      │
  │  DIV = "────────────────────"                                        │
  │                                                                      │
  │                                                                      │
  │  def cmdMiTool(bot, update, gestion) -> None:                        │
  │      try:                                                            │
  │          now  = time.time()                                          │
  │          args = bot.cmd.args if len(bot.cmd.args) > 0 else (         │
  │                 update.reply_to.text if update.reply_to else '')     │
  │          user = gestion.view(user_id=update.user_id)                 │
  │          chat = gestion.view(user_id=update.chat_id)                 │
  │          cmd  = gestion.viewCmd(bot.cmd.command)                     │
  │          bot.sendAction(action='typing')                             │
  │                                                                      │
  │          # Guardia 1 — usuario baneado                               │
  │          if user['ban'] == 'true':                                   │
  │              return bot.replyMessage(text=(                          │
  │                  f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"                 │
  │                  f"🍸 {bot.bi('Raise')}: "                           │
  │                  f"<code>You are banned!</code>"))                   │
  │                                                                      │
  │          # Guardia 2 — chat no autorizado                            │
  │          if chat['rango'] not in gestion.prem:                       │
  │              return bot.replyMessage(text=(                          │
  │                  f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"                 │
  │                  f"🍸 {bot.bi('Raise')}: "                           │
  │                  f"<code>This Chat Is Not Authorized!</code>"))      │
  │                                                                      │
  │          # Guardia 3 — comando no registrado en DB                   │
  │          if cmd['status'] == 'unval':                                │
  │              return bot.replyMessage(text=(                          │
  │                  f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"                 │
  │                  f"🍸 {bot.bi('Important')}: "                       │
  │                  f"<code>Command not registered!</code>"))           │
  │                                                                      │
  │          # Guardia 4 — modo del comando                              │
  │          if cmd['mode'] == 'ma':                                     │
  │              return bot.replyMessage(text=(                          │
  │                  f"{bot.bi(cmd['name'].title())} [ 🛠️ ]\n"           │
  │                  f"🍸 {bot.bi('Raise')}: "                           │
  │                  f"<code>Command in maintenance!</code>"))           │
  │          if cmd['mode'] == 'of':                                     │
  │              return bot.replyMessage(text=(                          │
  │                  f"{bot.bi(cmd['name'].title())} [ ❌ ]\n"           │
  │                  f"🍸 {bot.bi('Raise')}: "                           │
  │                  f"<code>Command Offline!</code>"))                  │
  │                                                                      │
  │          # Guardia 5 — argumentos requeridos                         │
  │          if not args:                                                │
  │              return bot.replyMessage(text=(                          │
  │                  f"{bot.bi(cmd['name'].title())} [ 🍸 ]\n{DIV}\n"    │
  │                  f"🍸 {bot.bi('Use')}: "                             │
  │                  f"<code>/{bot.cmd.command} "                        │
  │                  f"{cmd['use']}</code>"))                            │
  │                                                                      │
  │          # ─── LÓGICA PROPIA AQUÍ ─────────────────────────────     │
  │          result = mi_api_o_funcion(args)                             │
  │          # ─────────────────────────────────────────────────────    │
  │                                                                      │
  │          bot.replyMessage(text=(                                     │
  │              f"{bot.bi(cmd['name'].title())} [ 🍸 ]\n{DIV}\n"        │
  │              f"🍸 {bot.bi('Result')}: <code>{result}</code>\n"       │
  │              f"{DIV}\n"                                              │
  │              f"⚡ {bot.bi('T. Taken')}: "                            │
  │              f"<code>{round(time.time() - now, 1)}'s</code>\n"       │
  │              f"👤 {bot.bi('User')}: "                                │
  │              f"@{update.username} [{user['c_name'].title()}]\n"      │
  │              f"{DIV}\n"                                              │
  │              f"🍸 {bot.bi('By')}: @Low_47 ☁️"))                      │
  │                                                                      │
  │      except Exception as e:                                          │
  │          bot.raise_post(str(e))                                      │
  └──────────────────────────────────────────────────────────────────────┘

  Notas importantes sobre las guardias:

  ban == 'false' significa NO baneado. ban == 'true' significa baneado.
  ↑ String, no booleano. Comparar siempre con strings.

  gestion.prem = ['owner', 'admin', 'premium']
  Solo estos rangos pueden usar tools. Free no puede.

  cmd['status']:
    'on'    → activo
    'off'   → desactivado
    'unval' → no existe en la tabla comandos (no registrado)

  cmd['mode']:
    'on' → funcionando normal
    'ma' → en mantenimiento
    'of' → offline


  ──────────────────────────────────────────────────────────────────────
  PASO 2 — Registrar en main.py
  ──────────────────────────────────────────────────────────────────────

  Abrir main.py y agregar en la sección de TOOLS (línea ~64):

      bot.addCommand('mitl', 'Commands.Tools.mitool:cmdMiTool')

  El primer argumento es el comando de Telegram (/mitl).
  El segundo es  ruta.del.modulo:nombre_funcion


  ──────────────────────────────────────────────────────────────────────
  PASO 3 — Insertar en la tabla comandos
  ──────────────────────────────────────────────────────────────────────

  Opción A — Vía bot (recomendado mientras el bot está corriendo):

      /addcmd mitl|tool|Mi Tool|ARGUMENTO|Descripción del tool

      Formato:  /addcmd COMANDO|TIPO|NOMBRE|USO|COMENTARIO

  Opción B — Agregar al setup.py para que lo inserte en futuros setups:

  En la función _seed_commands() dentro del array tools, agregar:

      ('mitl', 'tool', 'on', 'Descripción del tool', 'Mi Tool', 'ARGUMENTO', ''),

      El orden de los campos es:
      (comando, tipo, status, comentario, name, use, gate)

  Verificar que quedó registrado:

      /stat_c mitl


═══════════════════════════════════════════════════════════════════════════
  AGREGAR UN NUEVO GATE (SIMPLE — usando el template)
═══════════════════════════════════════════════════════════════════════════

  Este es el método recomendado para la mayoría de los gates.
  Solo hay que escribir la función checker. El template maneja el resto.

  ──────────────────────────────────────────────────────────────────────
  PASO 1 — Crear Commands/Gates/migate.py
  ──────────────────────────────────────────────────────────────────────

  ┌──────────────────────────────────────────────────────────────────────┐
  │  from Commands.Gates._template import run_gate                       │
  │                                                                      │
  │  # Importar el módulo core del gateway                               │
  │  # (el archivo con la lógica real de la API)                         │
  │  from Commands.Gates import migate_core                              │
  │                                                                      │
  │                                                                      │
  │  def gateCmd(bot, update, gestion) -> None:                          │
  │                                                                      │
  │      def checker(cc, binData):                                       │
  │          """                                                         │
  │          cc      = [numero, mes, año, cvv]  (lista de strings)       │
  │          binData = {brand, type, level, bank, country, flag, ...}    │
  │                                                                      │
  │          Retornar siempre uno de estos dos formatos:                 │
  │                                                                      │
  │          Éxito (gate corrió):                                        │
  │            {'status': True, 'success': True/False,                  │
  │             'response': 'Approved ✅' o 'Declined ❌'}               │
  │                                                                      │
  │          Error (gate no pudo correr → crédito se devuelve):          │
  │            {'status': False, 'raise': 'mensaje de error'}            │
  │          """                                                         │
  │          cc_str = f"{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}"                │
  │                                                                      │
  │          try:                                                        │
  │              resultado = migate_core.main(cc_str)                    │
  │                                                                      │
  │              if resultado['status'] == 'Approved ✅':                │
  │                  return {'status': True, 'success': True,            │
  │                          'response': 'Approved ✅'}                  │
  │              elif resultado['status'] == 'Declined ❌':              │
  │                  return {'status': True, 'success': False,           │
  │                          'response': 'Declined ❌'}                  │
  │              else:                                                   │
  │                  return {'status': False,                            │
  │                          'raise': resultado.get('message','Error')}  │
  │          except Exception as e:                                      │
  │              return {'status': False, 'raise': str(e)[:200]}         │
  │                                                                      │
  │      run_gate(bot, update, gestion,                                  │
  │               gateway='Mi Gateway',                                  │
  │               checker=checker)                                       │
  └──────────────────────────────────────────────────────────────────────┘

  Qué hace run_gate automáticamente:
  ────────────────────────────────────────────────────────────────────
  ✓  Verifica ban, chat autorizado, cmd status/mode
  ✓  Parsea la tarjeta de args o de reply_to
  ✓  Hace BIN lookup
  ✓  Verifica BIN-ban
  ✓  Verifica créditos del usuario (y los descuenta)
  ✓  Verifica cooldown anti-spam
  ✓  Muestra barra de progreso animada mientras corre el checker
  ✓  Devuelve el crédito si status=False (error de gate)
  ✓  Muestra el resultado con diseño JILL completo
  ✓  Incluye info del BIN, tiempo, usuario, firma


  ──────────────────────────────────────────────────────────────────────
  PASO 2 — Registrar en main.py
  ──────────────────────────────────────────────────────────────────────

  En la sección GATEWAYS (línea ~74):

      bot.addCommand('mg', 'Commands.Gates.migate:gateCmd')


  ──────────────────────────────────────────────────────────────────────
  PASO 3 — Insertar en la tabla comandos
  ──────────────────────────────────────────────────────────────────────

  Vía bot:

      /addcmd mg|charge|Mi Gate|cc|mm|yy|cvv|Descripción del gate

  O en setup.py dentro del array gates en _seed_commands():

      ('mg', 'charge', 'on', 'Descripción del gate',
       'Mi Gate', 'cc|mm|yy|cvv', 'Mi Gateway'),

  Si el gate es de masa (procesa múltiples tarjetas), usar tipo 'mass'.
  Si solo verifica sin cobrar, usar tipo 'auth'.


═══════════════════════════════════════════════════════════════════════════
  AGREGAR UN GATE CON FLUJO ESPECIAL (sin template)
═══════════════════════════════════════════════════════════════════════════

  Usar este patrón cuando el gate necesita:
    ─  Argumentos extra (como /tcl que necesita monto y número)
    ─  Selector de región via botones (como /amz)
    ─  Múltiples tarjetas en paralelo (como /mamz)
    ─  Cookie o autenticación propia (como /amzg, /amz)

  En estos casos se llama a gestion.gates() manualmente para las
  validaciones, y se usa waiting_bar() para la animación:

  ┌──────────────────────────────────────────────────────────────────────┐
  │  import time, threading                                              │
  │  from Commands.Gates._template import waiting_bar, DIV              │
  │  from Commands.Gates import migate_core                              │
  │                                                                      │
  │                                                                      │
  │  def gateCmd(bot, update, gestion) -> None:                          │
  │      try:                                                            │
  │          bot.sendAction(action='typing')                             │
  │          user = gestion.view(user_id=update.user_id)                 │
  │          chat = gestion.view(user_id=update.chat_id)                 │
  │          cmd  = gestion.viewCmd(bot.cmd.command)                     │
  │          raw  = bot.cmd.args if len(bot.cmd.args) > 0 else (         │
  │                 update.reply_to.text if update.reply_to else '')     │
  │                                                                      │
  │          # Parsear argumentos extra aquí                             │
  │          # Ejemplo: card|argumento_extra                             │
  │          partes = raw.split('|')                                     │
  │          if len(partes) < 5:                                         │
  │              return bot.replyMessage(text=(                          │
  │                  f"{bot.bi('Mi Gate')} [ 🍸 ]\n{DIV}\n"              │
  │                  f"🍸 {bot.bi('Use')}: "                             │
  │                  f"<code>/mg cc|mm|yy|cvv|extra</code>"))            │
  │                                                                      │
  │          cc_str = f"{partes[0]}|{partes[1]}|{partes[2]}|{partes[3]}"│
  │          extra  = partes[4]                                          │
  │                                                                      │
  │          # Validaciones estándar vía gestion.gates()                 │
  │          b = gestion.gates(user=user, chat=chat,                     │
  │                            text=cc_str, cmd=cmd, bot=bot)            │
  │          if not b['status']:                                         │
  │              return bot.replyMessage(text=b['text'])                 │
  │                                                                      │
  │          cc, binData = b['cc'], b['bin']                             │
  │          now  = time.time()                                          │
  │          edit = bot.replyMessage(                                    │
  │              text=waiting_bar(bot, 0, 'Mi Gateway', 'Mi Gate'))      │
  │                                                                      │
  │          # Hilo de animación                                         │
  │          stop = threading.Event()                                    │
  │          def _spin():                                                │
  │              pcts, i = [15, 30, 45, 60, 75, 90], 0                  │
  │              while not stop.is_set():                                │
  │                  try: bot.editMessage(                               │
  │                      message_id=edit.message_id,                    │
  │                      text=waiting_bar(bot, pcts[i % 6],             │
  │                                       'Mi Gateway', 'Mi Gate'))      │
  │                  except: pass                                        │
  │                  i += 1                                              │
  │                  stop.wait(1.4)                                      │
  │          th = threading.Thread(target=_spin, daemon=True)            │
  │          th.start()                                                  │
  │                                                                      │
  │          try:                                                        │
  │              result = migate_core.main(                              │
  │                  f"{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}", extra)         │
  │          except Exception as e:                                      │
  │              result = {'status': 'Error ⚠️',                        │
  │                        'message': str(e)[:200]}                     │
  │          finally:                                                    │
  │              stop.set()                                              │
  │              th.join(timeout=2)                                      │
  │                                                                      │
  │          mid    = edit.message_id if edit else None                  │
  │          status = result.get('status', 'Error ⚠️')                  │
  │                                                                      │
  │          # Error → devolver crédito                                  │
  │          if status not in ('Approved ✅', 'Declined ❌'):            │
  │              if isinstance(b.get('credits'), int):                   │
  │                  gestion.commit(                                     │
  │                      "UPDATE users SET credits = %s WHERE user_id = %s",
  │                      (str(b['credits'] + 1), str(update.user_id)))   │
  │              txt = (f"{bot.bi('Wrong Data')} [ ⚠️ ]\n"              │
  │                     f"🍸 {bot.bi('Raise')}: "                        │
  │                     f"<code>{result.get('message','Error')}</code>") │
  │              return (bot.editMessage(message_id=mid, text=txt)       │
  │                      if mid else bot.replyMessage(text=txt))         │
  │                                                                      │
  │          # Mostrar resultado                                         │
  │          card = (                                                    │
  │              f"{bot.bi('Mi Gate')} [ 🍸 ]\n{DIV}\n"                  │
  │              f"🍸 {bot.bi('Card')}: "                                │
  │              f"<code>{cc[0]}|{cc[1]}|{cc[2]}|{cc[3]}</code>\n"       │
  │              f"⚡ {bot.bi('Status')}: <code>{status}</code>\n"        │
  │              f"💳 {bot.bi('Gate')}: <code>Mi Gateway</code>\n"        │
  │              f"{DIV}\n"                                              │
  │              f"🍸 {bot.bi('Extra')}: <code>{extra}</code>\n"          │
  │              f"{DIV}\n"                                              │
  │              f"🍸 {bot.bi('Info')}: "                                │
  │              f"<code>{binData['brand'].title()}</code> - "            │
  │              f"<code>{binData['type'].title()}</code>\n"              │
  │              f"🍸 {bot.bi('Bank')}: "                                │
  │              f"<code>{binData['bank'].title()}</code>\n"              │
  │              f"🍸 {bot.bi('Country')}: "                             │
  │              f"<code>{binData['country'].title()}</code> "            │
  │              f"{binData.get('flag','')}\n{DIV}\n"                    │
  │              f"⚡ {bot.bi('T. Taken')}: "                            │
  │              f"<code>{round(time.time() - now, 1)}'s</code>\n"       │
  │              f"👤 {bot.bi('User')}: "                                │
  │              f"@{update.username} [{user['c_name'].title()}]\n"      │
  │              f"{DIV}\n"                                              │
  │              f"🍸 {bot.bi('By')}: @Low_47 ☁️"                        │
  │          )                                                           │
  │          (bot.editMessage(message_id=mid, text=card)                 │
  │           if mid else bot.replyMessage(text=card))                   │
  │                                                                      │
  │      except Exception as e:                                          │
  │          bot.raise_post(str(e))                                      │
  └──────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  QUÉ HACE gestion.gates()
═══════════════════════════════════════════════════════════════════════════

  gestion.gates(user, chat, text, cmd, bot)  retorna un dict:

  ┌──────────────────────────────────────────────────────────────────────┐
  │  Si retorna status=False:                                            │
  │    {'status': False, 'text': 'mensaje de error para el usuario'}     │
  │    Razones: ban, chat no autorizado, cmd off, cmd ma, cmd unval,     │
  │    BIN baneado, cooldown activo, sin créditos, tarjeta inválida.     │
  │                                                                      │
  │  Si retorna status=True:                                             │
  │    {                                                                 │
  │      'status':  True,                                                │
  │      'cc':      ['numero', 'mes', 'año', 'cvv'],                     │
  │      'bin':     {'brand': ..., 'type': ..., 'level': ...,            │
  │                  'bank': ..., 'country': ..., 'flag': ...,           │
  │                  'currency': ...},                                   │
  │      'credits': int o None  (créditos antes de descontar,           │
  │                              None si es staff con unlimited)         │
  │    }                                                                 │
  │                                                                      │
  │  El campo 'credits' sirve para devolver el crédito si el gate        │
  │  falla: gestion.commit("UPDATE users SET credits = %s ...",         │
  │                         (str(b['credits'] + 1), user_id))            │
  └──────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  RETORNOS DEL CHECKER (run_gate)
═══════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────┐
  │  Gate corrió correctamente (Approved o Declined):                    │
  │                                                                      │
  │    return {                                                          │
  │        'status':   True,                                             │
  │        'success':  True,            ← True=Approved, False=Declined  │
  │        'response': 'Approved ✅'    ← texto que aparece en Status    │
  │    }                                                                 │
  │                                                                      │
  │  Gate no pudo correr (error de red, excepción, cookie inválida):     │
  │                                                                      │
  │    return {                                                          │
  │        'status': False,                                              │
  │        'raise':  'Mensaje de error corto'                            │
  │    }                                                                 │
  │    ↑ El crédito se devuelve automáticamente                          │
  └──────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  REGISTRAR EN main.py — REFERENCIA DE POSICIÓN
═══════════════════════════════════════════════════════════════════════════

  main.py tiene 4 secciones. Agregar en la correcta:

  ┌──────────────────────────────────────────────────────────────────────┐
  │  #? COMMANDS (STAFF)      ← comandos de gestión interna              │
  │  bot.addCommand(...)                                                 │
  │                                                                      │
  │  #? COMMANDS (USERS)      ← tools y comandos de usuario              │
  │  bot.addCommand('mitl', 'Commands.Tools.mitool:cmdMiTool')           │
  │                                                                      │
  │  #? GATEWAYS              ← gates de tarjetas                        │
  │  bot.addCommand('mg', 'Commands.Gates.migate:gateCmd')               │
  │                                                                      │
  │  #? CALLBACKS             ← botones inline                           │
  │  bot.addCallback('mg_accion', 'Commands.Gates.migate:migate_cb')     │
  └──────────────────────────────────────────────────────────────────────┘

  Si el gate tiene un callback (como el selector de región de /amz),
  la función del callback recibe también (bot, update, gestion):

      def mi_callback(bot, update, gestion) -> None:
          ...

      bot.addCallback('mg_select', 'Commands.Gates.migate:mi_callback')

  El callback_id en los botones debe empezar con el prefijo registrado:

      bot.addButton(text='Opción A', callback='mg_select opciona')
                                                ↑
                                         prefijo + espacio + args


═══════════════════════════════════════════════════════════════════════════
  REGISTRAR EN LA DB — TABLA COMANDOS
═══════════════════════════════════════════════════════════════════════════

  Campos de la tabla comandos:

  ┌──────────────────┬────────────────────────────────────────────────┐
  │  Campo           │  Descripción                                   │
  ├──────────────────┼────────────────────────────────────────────────┤
  │  comando         │  Nombre del comando (ej: 'mitl', 'mg')         │
  │  tipo            │  'tool' | 'charge' | 'mass' | 'auth'           │
  │  status          │  'on' al crear  (se cambia con /mod)           │
  │  comentario      │  Descripción breve                             │
  │  name            │  Nombre bonito (ej: 'Mi Tool', 'Mi Gate')      │
  │  use             │  Ejemplo de argumentos (ej: 'cc|mm|yy|cvv')    │
  │  gate            │  Nombre del gateway. Vacío para tools ('').    │
  └──────────────────┴────────────────────────────────────────────────┘

  Vía bot (mientras el bot está corriendo):

      /addcmd mitl|tool|Mi Tool|ARG|Descripción del tool
      /addcmd mg|charge|Mi Gate|cc|mm|yy|cvv|Descripción del gate

  Vía setup.py (para que se inserte en futuros setups):
  Editar la función _seed_commands() en setup.py:

      En el array tools agregar:
      ('mitl', 'tool', 'on', 'Descripción', 'Mi Tool', 'ARG', ''),

      En el array gates agregar:
      ('mg', 'charge', 'on', 'Descripción', 'Mi Gate', 'cc|mm|yy|cvv', 'Mi Gateway'),


═══════════════════════════════════════════════════════════════════════════
  LISTA DE VERIFICACIÓN COMPLETA
═══════════════════════════════════════════════════════════════════════════

  TOOL NUEVO
  ┌─────────────────────────────────────────────────────────────────────┐
  │  [ ]  Crear Commands/Tools/mitool.py con función cmdMiTool()        │
  │  [ ]  Importar dependencias necesarias en el archivo                │
  │  [ ]  Seguir el patrón de guardias (ban → prem → unval → mode)      │
  │  [ ]  Agregar en main.py:  bot.addCommand('mitl', '...:cmdMiTool')  │
  │  [ ]  Registrar en DB:  /addcmd mitl|tool|...                       │
  │  [ ]  Verificar con /stat_c mitl                                    │
  │  [ ]  Probar con /mitl argumento_de_prueba                          │
  └─────────────────────────────────────────────────────────────────────┘

  GATE NUEVO (con template)
  ┌─────────────────────────────────────────────────────────────────────┐
  │  [ ]  Crear Commands/Gates/migate_core.py  (lógica de la API)       │
  │  [ ]  Crear Commands/Gates/migate.py  con checker + run_gate()      │
  │  [ ]  Agregar en main.py:  bot.addCommand('mg', '...:gateCmd')      │
  │  [ ]  Registrar en DB:  /addcmd mg|charge|...                       │
  │  [ ]  Agregar a _seed_commands() en setup.py                        │
  │  [ ]  Verificar con /stat_c mg                                      │
  │  [ ]  Probar con /mg cc|mm|yy|cvv válida                            │
  │  [ ]  Verificar que crédito se devuelve si el core lanza excepción  │
  └─────────────────────────────────────────────────────────────────────┘

  GATE NUEVO (flujo especial)
  ┌─────────────────────────────────────────────────────────────────────┐
  │  [ ]  Crear Commands/Gates/migate_core.py                           │
  │  [ ]  Crear Commands/Gates/migate.py  con gestion.gates() manual    │
  │       y waiting_bar() + thread de animación                         │
  │  [ ]  Si tiene callback: agregar en main.py bot.addCallback(...)    │
  │  [ ]  Agregar en main.py:  bot.addCommand('mg', '...:gateCmd')      │
  │  [ ]  Registrar en DB:  /addcmd mg|charge|...                       │
  │  [ ]  Agregar a _seed_commands() en setup.py                        │
  │  [ ]  Verificar comportamiento ante error (crédito devuelto)        │
  │  [ ]  Verificar comportamiento ante declinada (crédito NO devuelto) │
  └─────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  REFERENCIA DE MÉTODOS ÚTILES EN EL HANDLER
═══════════════════════════════════════════════════════════════════════════

  bot.bi(texto)                      →  texto en bold-italic unicode
  bot.replyMessage(text)             →  envía mensaje al chat
  bot.editMessage(message_id, text)  →  edita mensaje existente
  bot.sendAction('typing')           →  muestra "escribiendo..."
  bot.raise_post(error)              →  postea error al canal de errores
  bot.addButton(text, callback)      →  botón inline
  bot.addRow(*buttons)               →  fila de botones
  bot.replyMarkup(*rows)             →  teclado inline completo

  gestion.view(user_id)              →  dict usuario
  gestion.viewCmd(comando)           →  dict comando de la DB
  gestion.gates(user, chat, text, cmd, bot)  →  validaciones gate
  gestion.commit(query, params)      →  escribe en DB
  gestion.prem                       →  ['owner','admin','premium']
  gestion.rangos                     →  ['owner','admin']
  gestion.sellers                    →  ['owner','admin','seller']

  update.user_id                     →  ID del usuario
  update.chat_id                     →  ID del chat
  update.username                    →  @username sin @
  update.message                     →  texto del mensaje
  update.reply_to                    →  mensaje respondido (o None)


╔══════════════════════════════════════════════════════════════════════╗
║  Tool  →  Commands/Tools/  ·  tipo='tool'  ·  sin crédito           ║
║  Gate  →  Commands/Gates/  ·  tipo='charge'  ·  con crédito         ║
║  En ambos casos: main.py + tabla comandos                            ║
╚══════════════════════════════════════════════════════════════════════╝

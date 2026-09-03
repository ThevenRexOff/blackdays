
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║  ███████╗████████╗██████╗ ██╗   ██╗ ██████╗████████╗██╗   ██╗██████╗   ║
║  ██╔════╝╚══██╔══╝██╔══██╗██║   ██║██╔════╝╚══██╔══╝██║   ██║██╔══██╗  ║
║  ███████╗   ██║   ██████╔╝██║   ██║██║        ██║   ██║   ██║██████╔╝  ║
║  ╚════██║   ██║   ██╔══██╗██║   ██║██║        ██║   ██║   ██║██╔══██╗  ║
║  ███████║   ██║   ██║  ██║╚██████╔╝╚██████╗   ██║   ╚██████╔╝██║  ██║  ║
║  ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝  ║
║                                                                          ║
║               E S T R U C T U R A   D E L   P R O Y E C T O             ║
╚══════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════
  ÁRBOL DE ARCHIVOS
═══════════════════════════════════════════════════════════════════════════

  JILL_BOT/
  │
  ├── main.py                ← Registra TODOS los comandos y callbacks.
  │                            Función build_bot(query) → retorna BotX.
  │                            Compartido entre webhook y polling.
  │
  ├── poll.py                ← Runner de long-polling.
  │                            ThreadPoolExecutor → llama build_bot
  │                            por cada update en paralelo.
  │
  ├── run.py                 ← Entrypoint principal. Lee MODE de config.env.
  │                            polling  → arranca poll.run()
  │                            webhook  → registra setWebhook en Telegram
  │
  ├── setup.py               ← Setup interactivo (rich terminal).
  │                            Crea tablas, siembra datos, escribe config.
  │                            Correr una sola vez al instalar.
  │
  ├── tasks.py               ← Tareas de mantenimiento (para cron).
  │                            expiry   → DM a premiums que expiran
  │                            cleanup  → borra card_uses > 24h
  │
  ├── index.php              ← Receptor webhook de Telegram (PHP).
  │                            POST con payload → base64 → python3 main.py
  │                            Solo en modo webhook. GET retorna 200 OK.
  │
  ├── requirements.txt       ← Todas las dependencias Python del proyecto.
  │
  ├── Model/
  │   ├── __init__.py        ← Framework BotX 3.0  (ver sección abajo)
  │   ├── gestion.py         ← Clase Gestion: DB y lógica de negocio
  │   ├── config.env         ← Variables de entorno (generado por setup)
  │   └── libs/
  │       ├── __addr.py      ← Generador de identidades / direcciones falsas
  │       ├── __ip.py        ← Lookup de IPs y dominios
  │       ├── __phone.py     ← Lookup de números telefónicos
  │       ├── __scrapper.py  ← Scraper de tarjetas de crédito
  │       └── __tmail.py     ← Email temporal
  │
  ├── Commands/
  │   ├── Admin/
  │   │   ├── callbacks.py   ← Todos los handlers de botones inline
  │   │   ├── rangos.py      ← prmn, ban, uban, cred, rname, delay, admin, key
  │   │   ├── users.py       ← info, cookie
  │   │   ├── usr.py         ← Panel /user
  │   │   ├── cmdStorage.py  ← addcmd, delcmd, mod, stat_c
  │   │   ├── bban.py        ← binban, bban, rbin
  │   │   ├── broadcast.py   ← broadcast, gusers
  │   │   ├── cmd.py         ← /cmds (panel paginado de comandos)
  │   │   ├── start.py       ← /start
  │   │   ├── myinfo.py      ← /myinfo, /myacc
  │   │   ├── history.py     ← /history (audit trail de eventos)
  │   │   ├── tickets.py     ← /ticket, /tickets, /tk, /tclose
  │   │   ├── sales.py       ← /sell, /sales, /prices, /seller, /unseller,
  │   │   │                     /addplan, /delplan
  │   │   └── refs.py        ← /ref, /links
  │   │
  │   ├── Tools/
  │   │   ├── binc.py        ← /bin
  │   │   ├── addr.py        ← /fake
  │   │   ├── number.py      ← /nm
  │   │   ├── ip_l.py        ← /ip
  │   │   ├── cc_gen.py      ← /gen
  │   │   ├── sk.py          ← /sk
  │   │   ├── site.py        ← /site
  │   │   ├── tmail.py       ← /tmail + callbacks tmail_*
  │   │   └── scr.py         ← /scr
  │   │
  │   └── Gates/
  │       ├── _template.py   ← run_gate(), waiting_bar() — base de gates
  │       ├── amz.py         ← /amz + callback amz_run (selector región)
  │       ├── mamz.py        ← /mamz (masa, ThreadPoolExecutor)
  │       ├── mamazon/       ← Módulo CookieContext para Amazon MX
  │       │   └── main.py
  │       ├── amzglobal.py   ← /amzg (Amazon Global Paloma)
  │       ├── amzglobal_core.py  ← Clase Amazon.buildFlowTest()
  │       ├── telcel.py      ← /tcl (Telcel MX recharge)
  │       └── telcel_core.py ← Función main(ccs, monto, num)


═══════════════════════════════════════════════════════════════════════════
  FRAMEWORK BotX 3.0  (Model/__init__.py)
═══════════════════════════════════════════════════════════════════════════

  BotX es el micro-framework propio del bot.
  NO usa python-telegram-bot, aiogram ni Telethon.

  ──────────────────────────────────────────────────────────────────────
  MODELO DE EJECUCIÓN
  ──────────────────────────────────────────────────────────────────────

  [Telegram]
      │
      │  POST JSON update
      ▼
  index.php  ──base64──►  python3 main.py <query>
                                   │
                                   ▼
                          build_bot(query)
                                   │
                   ┌───────────────┤
                   │  addCommand() │  registra handlers
                   │  addCallback()│
                   └───────────────┤
                                   │
                          compile_bot()
                                   │
                          decode(query)  →  update object
                          match command  →  handler(bot, update, gestion)
                                   │
                                   ▼
                          respuesta al usuario

  En modo POLLING:
  poll.py → getUpdates (long-poll 50s) → base64 → ThreadPoolExecutor
  → build_bot(query).compile_bot()  (mismo código que webhook)

  ──────────────────────────────────────────────────────────────────────
  MÉTODOS PRINCIPALES DE BotX
  ──────────────────────────────────────────────────────────────────────

  bot.replyMessage(text, reply_markup)  →  sendMessage al chat
  bot.editMessage(message_id, text)     →  editMessageText
  bot.sendAction(action)                →  sendChatAction ('typing')
  bot.showAlert(text, callback_id)      →  answerCallbackQuery
  bot.raise_post(error)                 →  error al ERROR_CHANNEL
  bot.bi(text)                          →  texto a bold-italic unicode
  bot.addButton(text, callback)         →  botón inline
  bot.addRow(*buttons)                  →  fila de botones
  bot.replyMarkup(*rows)                →  teclado inline
  bot.adminRegister(action, target, d)  →  log en audit trail + DB events
  bot.copyMessage(from_id, msg_id, to)  →  copyMessage API (para /ref)

  ──────────────────────────────────────────────────────────────────────
  OBJETO update  (disponible en todos los handlers)
  ──────────────────────────────────────────────────────────────────────

  update.user_id     →  Telegram ID del usuario que escribió
  update.chat_id     →  ID del chat (grupo o DM)
  update.username    →  @username sin el @
  update.message     →  texto completo del mensaje
  update.message_id  →  ID del mensaje
  update.reply_to    →  objeto del mensaje respondido (o None)
  update.query_id    →  ID del callback query (para botones)
  update.origin_uid  →  ID del usuario que inició el mensaje original

  ──────────────────────────────────────────────────────────────────────
  OBJETO bot.cmd  (en handlers de comandos)
  ──────────────────────────────────────────────────────────────────────

  bot.cmd.command  →  nombre del comando ('amz', 'bin', 'tcl', etc.)
  bot.cmd.args     →  argumentos después del comando (string)

  ──────────────────────────────────────────────────────────────────────
  OBJETO bot.callback  (en handlers de botones)
  ──────────────────────────────────────────────────────────────────────

  bot.callback.args  →  datos del callback después del prefijo


═══════════════════════════════════════════════════════════════════════════
  CLASE GESTION  (Model/gestion.py)
═══════════════════════════════════════════════════════════════════════════

  Maneja toda la lógica de negocio y acceso a la base de datos.

  ──────────────────────────────────────────────────────────────────────
  CONSTANTES DE RANGO
  ──────────────────────────────────────────────────────────────────────

  rangos   = ['owner', 'admin']              ← staff con permisos altos
  prem     = ['owner', 'admin', 'premium']   ← pueden usar tools y gates
  sellers  = ['owner', 'admin', 'seller']    ← pueden registrar ventas
  _rangos  = ['owner', 'admin']              ← alias para staff

  ──────────────────────────────────────────────────────────────────────
  MÉTODOS PRINCIPALES
  ──────────────────────────────────────────────────────────────────────

  Usuarios:
    view(user_id)                  →  dict completo del usuario en DB
    addUser(user_id, ...)          →  crea usuario si no existe
    addDays(days)                  →  calcula fecha futura (now + N días)

  Comandos:
    viewCmd(comando)               →  dict del comando en tabla comandos
    viewCmds(typeC)                →  lista de comandos por tipo

  DB:
    commit(query, params)          →  INSERT / UPDATE / DELETE
    _run(query, params)            →  SELECT → lista de filas

  Gates:
    gates(user, chat, text, cmd, bot)  →  valida todo, extrae CC+BIN
    regex(text)                        →  parsea tarjeta de texto
    is_bin_banned(bin6)                →  True si BIN está baneado
    check_card_abuse(card, uid)        →  'allow' | 'cooldown' | 'abuse'
    cookie_verify(user_id)             →  verifica cookie Amazon del usuario
    cookie_add(user_id, cookie)        →  guarda cookie en DB
    cookie_del(user_id)                →  elimina cookie

  Eventos y audit:
    log_event(actor_id, actor_name, action, target, detail)

  Ventas y planes:
    add_plan / del_plan / view_plans / view_plan
    record_sale / sales_report / sellers_report

  Tickets:
    create_ticket / list_tickets / view_ticket / set_ticket_status


═══════════════════════════════════════════════════════════════════════════
  ARQUITECTURA DE GATES
═══════════════════════════════════════════════════════════════════════════

  Todos los gates nuevos heredan del template en _template.py.

  ┌────────────────────────────────────────────────────────────────────┐
  │  run_gate(bot, update, gestion, gateway, checker)                  │
  │                                                                    │
  │  1.  Verifica usuario: ban, chat mode, cmd status/mode             │
  │  2.  Parsea la tarjeta de args o reply_to                          │
  │  3.  Lookup BIN → verifica BIN-ban                                 │
  │  4.  Verifica créditos + cooldown  (gestion.gates)                 │
  │  5.  Muestra barra de progreso animada  (waiting_bar)              │
  │  6.  Llama  checker(cc, binData)   ← ÚNICA parte custom            │
  │  7.  Detiene la animación                                          │
  │  8.  Si error:  devuelve crédito + muestra mensaje de error        │
  │  9.  Si OK:     muestra resultado con diseño JILL                  │
  └────────────────────────────────────────────────────────────────────┘

  Para crear un nuevo gate solo se necesita escribir el checker:

      from Commands.Gates._template import run_gate

      def gateCmd(bot, update, gestion):
          def checker(cc, binData):
              # cc = [numero, mm, yyyy, cvv]
              # binData = {brand, type, level, bank, country, flag, ...}
              result = mi_api(cc)
              return {'status': True, 'success': True, 'response': 'Approved ✅'}
          run_gate(bot, update, gestion, gateway='Mi Gateway', checker=checker)

  Gates con flujo especial (no usan run_gate directo):
  ─────────────────────────────────────────────────────
  /amz   →  selector de región via botones inline (callback amz_run)
  /mamz  →  procesa N tarjetas en paralelo (ThreadPoolExecutor)
  /tcl   →  args extendidos: cc|mm|yy|cvv|monto|numero

  Barra de progreso animada:
  ──────────────────────────
  Thread daemon edita el mensaje cada 1.4s mientras el checker corre:
  ▰▱▱▱▱▱▱▱▱▱ 15%  →  ▰▰▰▱▱▱▱▱▱▱ 30%  →  ▰▰▰▰▰▱▱▱▱▱ 50%  → ...


═══════════════════════════════════════════════════════════════════════════
  SISTEMA VISUAL JILL (Design System)
═══════════════════════════════════════════════════════════════════════════

  BotX.bi(texto)
  ──────────────
  Convierte texto a bold-italic unicode para estética en Telegram.
  A-Z  →  0x1D63C + offset  (𝘼𝘽𝘾𝘿...)
  a-z  →  0x1D656 + offset  (𝙖𝙗𝙘𝙙...)
  Otros chars pasan sin cambio.

  Separador estándar:  ────────────────────

  Iconos por sección:
    🍸  Labels e información general
    ⚡  Status, estado en curso, tiempo
    💳  Gate, tarjeta, créditos
    👤  Usuario, identidad

  Estructura estándar de un resultado:

  ┌─────────────────────────────────────┐
  │  𝘼𝙢𝙖𝙯𝙤𝙣 𝙂𝙖𝙩𝙚 [ 🍸 ]                │
  │  ────────────────────               │
  │  🍸 𝘾𝙖𝙧𝙙:    4111...|12|2026|123    │
  │  ⚡ 𝙎𝙩𝙖𝙩𝙪𝙨:  Approved ✅            │
  │  💳 𝙂𝙖𝙩𝙚:    Amazon MX              │
  │  ────────────────────               │
  │  🍸 𝙄𝙣𝙛𝙤:   Visa - Debit - Gold    │
  │  🍸 𝘽𝙖𝙣𝙠:   Banco Nacional         │
  │  🍸 𝘾𝙤𝙪𝙣𝙩𝙧𝙮: Mexico 🇲🇽             │
  │  ────────────────────               │
  │  ⚡ 𝙏. 𝙏𝙖𝙠𝙚𝙣: 3.2's                 │
  │  👤 𝙐𝙨𝙚𝙧:   @usuario [Premium]      │
  │  ────────────────────               │
  │  🍸 𝘽𝙮: @Low_47 ☁️                  │
  └─────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  BASE DE DATOS — ESQUEMA COMPLETO
═══════════════════════════════════════════════════════════════════════════

  ┌─ users ──────────────────────────────────────────────────────────┐
  │  user_id       VARCHAR(30) PK    Telegram User/Chat ID           │
  │  rango         VARCHAR(20)       free|premium|seller|admin|owner │
  │  c_name        VARCHAR(100)      Nombre display en resultados     │
  │  credits       VARCHAR(20)       'unlimited' o número entero     │
  │  ban           VARCHAR(10)       'true' | 'false'                │
  │  warns         VARCHAR(5)        Número de advertencias          │
  │  d_reg         VARCHAR(30)       Fecha de registro               │
  │  admin         VARCHAR(10)       'true' | 'false'                │
  │  su            VARCHAR(10)       Super-user (owner flag)         │
  │  l_reg         VARCHAR(30)       Último uso de gate              │
  │  spam          VARCHAR(20)       Cooldown en segundos            │
  │  n_bil         VARCHAR(100)      Fecha expiración premium        │
  │  nombre_usuario TEXT             @username guardado              │
  │  nombre        TEXT             Nombre guardado                  │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ comandos ───────────────────────────────────────────────────────┐
  │  comando       VARCHAR(50) PK    Nombre del comando              │
  │  tipo          VARCHAR(30)       tool | charge | mass | auth     │
  │  status        VARCHAR(10)       on | off                        │
  │  d_reg         VARCHAR(30)       Fecha de registro               │
  │  comentario    VARCHAR(200)      Descripción                     │
  │  name          VARCHAR(100)      Nombre display                  │
  │  use           VARCHAR(200)      Ejemplo de uso                  │
  │  gate          VARCHAR(60)       Nombre del gateway              │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ keys ───────────────────────────────────────────────────────────┐
  │  key           VARCHAR(60) PK    Llave alfanumérica              │
  │  days          VARCHAR(10)       Días de premium                 │
  │  credits       VARCHAR(20)       Créditos incluidos              │
  │  status        VARCHAR(20)       active | used                   │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ banned_bins ────────────────────────────────────────────────────┐
  │  bin           VARCHAR(8) PK     Primeros 6 dígitos de tarjeta   │
  │  reason        VARCHAR(255)      Motivo del ban                  │
  │  added_by      VARCHAR(20)       ID del admin que lo baneó       │
  │  d_reg         DATE              Fecha del ban                   │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ card_uses ──────────────────────────────────────────────────────┐
  │  id            SERIAL PK                                         │
  │  card_hash     VARCHAR(64)       SHA-256 del número de tarjeta   │
  │  user_id       VARCHAR(20)       Quién la usó                    │
  │  used_at       TIMESTAMP         Cuándo                          │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ usage_log ──────────────────────────────────────────────────────┐
  │  id            SERIAL PK                                         │
  │  user_id       VARCHAR(30)       Quién usó el comando            │
  │  command       VARCHAR(50)       Qué comando                     │
  │  cmd_type      VARCHAR(30)       Tipo del comando                │
  │  used_at       TIMESTAMP         Cuándo                          │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ cookies ────────────────────────────────────────────────────────┐
  │  user_id       VARCHAR(30) PK    Dueño de la cookie              │
  │  cookie        TEXT              Cookie Amazon completa           │
  │  updated_at    TIMESTAMP         Última actualización            │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ plans ──────────────────────────────────────────────────────────┐
  │  name          VARCHAR(60) PK    Nombre del plan                 │
  │  days          INTEGER           Días de acceso                  │
  │  credits       VARCHAR(20)       'unlimited' o número            │
  │  price         NUMERIC(10,2)     Precio de venta                 │
  │  active        BOOLEAN           Si el plan está activo          │
  │  d_reg         DATE              Fecha de creación               │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ sales ──────────────────────────────────────────────────────────┐
  │  id            SERIAL PK                                         │
  │  seller_id     VARCHAR(30)       ID del vendedor                 │
  │  seller_name   VARCHAR(100)      Nombre del vendedor             │
  │  plan          VARCHAR(60)       Plan vendido                    │
  │  price         NUMERIC(10,2)     Precio cobrado                  │
  │  client        VARCHAR(60)       ID del cliente                  │
  │  method        VARCHAR(40)       Método de pago (USDT, etc.)     │
  │  sold_at       TIMESTAMP         Cuándo                          │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ tickets ────────────────────────────────────────────────────────┐
  │  id            SERIAL PK                                         │
  │  user_id       VARCHAR(30)       Quién abrió el ticket           │
  │  username      VARCHAR(100)      @username del usuario           │
  │  problem       VARCHAR(120)      Título del problema             │
  │  description   TEXT              Descripción completa            │
  │  status        VARCHAR(20)       pending | closed                │
  │  created_at    TIMESTAMP         Cuándo se abrió                 │
  │  closed_by     VARCHAR(100)      Quién lo cerró                  │
  └──────────────────────────────────────────────────────────────────┘

  ┌─ events ─────────────────────────────────────────────────────────┐
  │  id            SERIAL PK                                         │
  │  actor_id      VARCHAR(30)       Quién realizó la acción         │
  │  actor_name    VARCHAR(100)      Nombre del actor                │
  │  action        VARCHAR(60)       Qué acción (Promote, Ban, etc.) │
  │  target        VARCHAR(60)       Sobre quién                     │
  │  detail        TEXT              Detalle adicional               │
  │  at            TIMESTAMP         Cuándo                          │
  └──────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  FLUJO COMPLETO DE UNA PETICIÓN
═══════════════════════════════════════════════════════════════════════════

  Usuario escribe  →  /amz 4111111111111111|12|2026|123
                                │
                                ▼
              [Telegram API]  POST JSON  →  index.php
                                                │
                             base64(payload)    │
                                                ▼
                         python3 main.py <query>
                                                │
                                       build_bot(query)
                                                │
                                BotX.decode()   →  update obj
                                BotX.match()    →  handler 'amz'
                                                │
                                                ▼
                      Commands.Gates.amz.gateCmd(bot, update, gestion)
                                                │
                         gestion.view()         →  datos del usuario
                         gestion.viewCmd('amz') →  status / mode del gate
                         gestion.cookie_verify  →  cookie Amazon del user
                         gestion.gates()        →  BIN lookup + crédito + abuse
                                                │
                         waiting_bar()  thread  →  animación progreso
                         CookieContext.buildFlowBilling()  →  Amazon API
                                                │
                         stop thread            →  animación detenida
                         bot.editMessage()      →  resultado final JILL
                                                │
                                                ▼
                                    [Usuario ve el resultado]


╔══════════════════════════════════════════════════════════════════════╗
║  Model/__init__.py  (BotX)  +  Model/gestion.py  (Gestion)          ║
║  son el núcleo del bot. Todos los handlers los usan.                 ║
╚══════════════════════════════════════════════════════════════════════╝

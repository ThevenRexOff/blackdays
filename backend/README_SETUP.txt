
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║       ██╗██╗██╗     ██╗         ██████╗  ██████╗ ████████╗              ║
║       ██║██║██║     ██║         ██╔══██╗██╔═══██╗╚══██╔══╝              ║
║       ██║██║██║     ██║         ██████╔╝██║   ██║   ██║                 ║
║  ██   ██║██║██║     ██║         ██╔══██╗██║   ██║   ██║                 ║
║  ╚█████╔╝██║███████╗███████╗    ██████╔╝╚██████╔╝   ██║                 ║
║   ╚════╝ ╚═╝╚══════╝╚══════╝    ╚═════╝  ╚═════╝    ╚═╝                 ║
║                                                                          ║
║                    S E T U P   &   C O N F I G                          ║
╚══════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════
  REQUISITOS PREVIOS
═══════════════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Python        3.9+     verificar: python3 --version                │
  │  pip           any      verificar: python3 -m pip --version         │
  │  PostgreSQL    12+      base de datos REMOTA hosteada               │
  │                         (alwaysdata, Supabase, Railway, Render...)   │
  │  PHP           7.4+     SOLO si usas modo WEBHOOK en servidor        │
  │  HTTPS         ──────── SOLO si usas modo WEBHOOK                   │
  └─────────────────────────────────────────────────────────────────────┘

  Instalar dependencias:

      python3 -m pip install -r requirements.txt


═══════════════════════════════════════════════════════════════════════════
  CORRIENDO EL SETUP
═══════════════════════════════════════════════════════════════════════════

      python3 setup.py

  El setup es completamente interactivo via terminal enriquecida (rich).
  Corre UNA SOLA VEZ. Si necesitas reconfigurar, puedes volver a correrlo.
  Las tablas se crean con IF NOT EXISTS — no se borran datos existentes.


═══════════════════════════════════════════════════════════════════════════
  FLUJO PASO A PASO
═══════════════════════════════════════════════════════════════════════════

  ┌─ PASO 1 ─ Bot & Owner ──────────────────────────────────────────────┐
  │                                                                     │
  │  Bot token   ─  Token de @BotFather. El setup lo valida             │
  │                 automáticamente con getMe.                          │
  │                 Ejemplo: 8863111403:AAFIw8efKQez4KL3...             │
  │                                                                     │
  │  Owner ID    ─  Tu Telegram User ID numérico.                       │
  │                 Obtenerlo con @userinfobot o enviando /id al bot.   │
  │                 Ejemplo: 7132523590                                 │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ PASO 2 ─ Base de Datos PostgreSQL ────────────────────────────────┐
  │                                                                     │
  │  DB host     ─  Host remoto de tu PostgreSQL                        │
  │                 Ejemplo: postgresql-mibot.alwaysdata.net            │
  │                                                                     │
  │  DB name     ─  Nombre de la base de datos                          │
  │                 Ejemplo: mibot_db                                   │
  │                                                                     │
  │  DB user     ─  Usuario de la base de datos                         │
  │                 Ejemplo: mibot                                      │
  │                                                                     │
  │  DB password ─  Contraseña (oculta al escribir)                     │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ PASO 3 ─ Modo de Ejecución ───────────────────────────────────────┐
  │                                                                     │
  │  webhook ─  Telegram envía updates a tu URL HTTPS.                 │
  │             Requiere servidor con PHP + URL pública HTTPS.          │
  │             > Te pedirá WEBHOOK_URL (ej: https://tudominio/index.php)│
  │             > Te pregunta ASYNC_MODE (recomendado: sí)              │
  │                                                                     │
  │  polling ─  El bot hace long-polling a Telegram.                   │
  │             No necesita PHP ni URL pública.                         │
  │             Ideal para VPS, RDP o máquina local.                    │
  │             > Te pedirá número de workers (default: 8)              │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ PASO 4 ─ Channels (opcionales, Enter para omitir) ────────────────┐
  │                                                                     │
  │  Error/logs channel  ─  Canal donde el bot postea errores internos  │
  │  Tickets/support     ─  Canal donde llegan los tickets de usuarios  │
  │  References channel  ─  Canal donde se publican las referencias     │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ PASO 5 ─ Links públicos (opcionales) ─────────────────────────────┐
  │                                                                     │
  │  Chat URL    ─  Link al grupo/canal principal (botón /links)        │
  │  Refs URL    ─  Link al canal de referencias (botón /links)         │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ PASO 6 ─ Confirmación y Build ────────────────────────────────────┐
  │                                                                     │
  │  Se muestra tabla resumen → confirmas → el setup ejecuta:           │
  │                                                                     │
  │  ✓  Conecta a la DB y verifica credenciales                         │
  │  ✓  Crea las 11 tablas (IF NOT EXISTS)                              │
  │  ✓  Inserta 4 planes Premium (31 / 92 / 184 / 365 días)             │
  │  ✓  Inserta 13 comandos en tabla comandos (9 tools + 4 gates)       │
  │  ✓  Crea o actualiza el owner en tabla users                        │
  │  ✓  Escribe Model/config.env con toda la configuración              │
  │  ✓  Registra o elimina webhook según modo elegido                   │
  └─────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  ARCHIVO DE CONFIGURACIÓN  →  Model/config.env
═══════════════════════════════════════════════════════════════════════════

  Generado automáticamente por setup.py. Editable manualmente.

  ┌──────────────────────┬─────────────────────────────────────────────┐
  │  Variable            │  Descripción                                │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │  BOT_TOKEN           │  Token del bot (de @BotFather)              │
  │  OWNER_ID            │  Telegram ID del dueño del bot              │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │  DB_HOST             │  Host PostgreSQL remoto                     │
  │  DB_NAME             │  Nombre de la base de datos                 │
  │  DB_USER             │  Usuario PostgreSQL                         │
  │  DB_PASS             │  Contraseña PostgreSQL                      │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │  MODE                │  webhook  ── requiere PHP + HTTPS           │
  │                      │  polling  ── solo Python                    │
  │                      │                                             │
  │  WEBHOOK_URL         │  (solo MODE=webhook)                        │
  │                      │  URL donde Telegram hace POST               │
  │                      │  Ej: https://midominio.com/index.php        │
  │                      │                                             │
  │  POLL_WORKERS        │  (solo MODE=polling)                        │
  │                      │  Threads paralelos. Recomendado: 4-8        │
  │                      │                                             │
  │  ASYNC_MODE          │  (solo MODE=webhook)                        │
  │                      │  true  = PHP retorna 200 de inmediato       │
  │                      │  false = PHP espera a que main.py termine   │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │  ERROR_CHANNEL       │  ID del canal de logs. Ej: -100123456789    │
  │  SUPPORT_CHANNEL     │  ID del canal de tickets                    │
  │  REFS_CHANNEL        │  ID del canal de referencias                │
  ├──────────────────────┼─────────────────────────────────────────────┤
  │  CHAT_URL            │  Link al grupo (usado en /links)            │
  │  REFS_URL            │  Link al canal de refs (usado en /links)    │
  └──────────────────────┴─────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  TABLAS CREADAS EN LA DB  (11 tablas)
═══════════════════════════════════════════════════════════════════════════

  ┌─────────────────┬──────────────────────────────────────────────────┐
  │  Tabla          │  Propósito                                        │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │  users          │  Usuarios (rango, créditos, ban, premium, etc.)  │
  │  comandos       │  Tools y gates (modo, status, nombre, uso)       │
  │  keys           │  Llaves de activación premium                    │
  │  banned_bins    │  BINs bloqueados por el admin                    │
  │  card_uses      │  Historial de tarjetas (anti-abuse)              │
  │  usage_log      │  Log de uso por comando y usuario                │
  │  cookies        │  Cookies Amazon por usuario (para gates amz)     │
  │  plans          │  Planes de venta (Premium 31d, 92d, etc.)        │
  │  sales          │  Registro de ventas por vendedor                 │
  │  tickets        │  Tickets de soporte de usuarios                  │
  │  events         │  Audit trail de acciones admin                   │
  └─────────────────┴──────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  DATOS SEMBRADOS AUTOMÁTICAMENTE
═══════════════════════════════════════════════════════════════════════════

  Planes Premium (tabla plans):

  ┌──────────────────────┬──────┬──────────┬────────┐
  │  Plan                │ Días │ Créditos │ Precio │
  ├──────────────────────┼──────┼──────────┼────────┤
  │  Premium 31 dias     │  31  │unlimited │  $50   │
  │  Premium 92 dias     │  92  │unlimited │  $120  │
  │  Premium 184 dias    │ 184  │unlimited │  $200  │
  │  Premium 1 ano       │ 365  │unlimited │  $350  │
  └──────────────────────┴──────┴──────────┴────────┘

  Comandos (tabla comandos):

      Tools:   bin   fake   nm   ip   gen   sk   site   tmail   scr
      Gates:   amz   mamz   amzg   tcl


═══════════════════════════════════════════════════════════════════════════
  INICIAR EL BOT
═══════════════════════════════════════════════════════════════════════════

  Inicio normal (lee MODE de config.env):

      python3 run.py

  Polling directo:

      python3 poll.py

  Tareas de mantenimiento (para configurar en cron):

      python3 tasks.py expiry      ← DM a premiums que expiran en <24h
      python3 tasks.py cleanup     ← Limpia card_uses más antiguos de 24h

  Cron sugerido:

      0   9   * * *   cd /ruta/bot && python3 tasks.py expiry
      0   *   * * *   cd /ruta/bot && python3 tasks.py cleanup


╔══════════════════════════════════════════════════════╗
║   setup.py → poll.py / run.py → bot online  🍸      ║
╚══════════════════════════════════════════════════════╝


╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ██████╗ ███╗   ███╗██████╗ ███████╗                                   ║
║  ██╔════╝ ████╗ ████║██╔══██╗██╔════╝                                   ║
║  ██║      ██╔████╔██║██║  ██║███████╗                                   ║
║  ██║      ██║╚██╔╝██║██║  ██║╚════██║                                   ║
║  ╚██████╗ ██║ ╚═╝ ██║██████╔╝███████║                                   ║
║   ╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚══════╝                                   ║
║                                                                          ║
║                  R E F E R E N C I A   C O M P L E T A                  ║
╚══════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════
  JERARQUÍA DE RANGOS
═══════════════════════════════════════════════════════════════════════════

      owner  ─────────  Dueño absoluto. Acceso total.
        │
        ├── admin  ────  Staff. Gestión de usuarios y comandos.
        │     │
        │     └── seller ─  Vendedor. Puede registrar ventas.
        │
        └── premium ───  Usuario de pago. Acceso a gates y tools.
              │
              └── free ─  Usuario gratuito. Comandos básicos.

  ┌─────────┬──────────────────────────────────────┐
  │  Icono  │  Nivel mínimo requerido              │
  ├─────────┼──────────────────────────────────────┤
  │   👑    │  owner únicamente                     │
  │   🔑    │  admin o superior                     │
  │   💰    │  seller o superior                    │
  │   ⭐    │  premium o superior (tools y gates)   │
  │   👤    │  free (todos los usuarios)            │
  └─────────┴──────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  CUENTA Y ACCESO
═══════════════════════════════════════════════════════════════════════════

  👤  /start
      Bienvenida. Registra al usuario automáticamente en la DB.

  👤  /myinfo   ·   /myacc
      Muestra tu perfil: rango, créditos, fecha expiración premium,
      cooldown spam, fecha de registro.

  👤  /id   ·   /p
      Muestra tu User ID y el Chat ID del grupo actual.

  👤  /claim  LLAVE
      Activa una llave premium.
      Ejemplo:  /claim JILL-XXXX-XXXX-XXXX

  👤  /prices   ·   /precios
      Lista pública de planes disponibles con precios.

  👤  /ticket  PROBLEMA|DESCRIPCION
      Abre un ticket de soporte. Se publica en el canal de tickets.
      Ejemplo:  /ticket Gate caído|/amz no responde desde ayer

  👤  /links
      Botones con links al chat y canal de referencias.

  ⭐  /cookie  TU_COOKIE_AMAZON
      Guarda tu cookie de Amazon en la DB.
      Necesaria para /amz, /mamz y /amzg.
      Ejemplo:  /cookie session-id=abc123; ubid-main=xyz...

  🔑  /ref   (responder a un mensaje)
      Copia el mensaje respondido al canal de referencias.


═══════════════════════════════════════════════════════════════════════════
  TOOLS  (herramientas)
═══════════════════════════════════════════════════════════════════════════

  Requieren que el tool esté ON en la DB. Staff los usa siempre.
  Usuarios free/premium están sujetos a cooldown y créditos.

  ──────────────────────────────────────────────────────────────────────

  ⭐  /bin  BIN
      Lookup de BIN: banco, marca, tipo, país, nivel, moneda.
      Ejemplo:  /bin 411111

  ⭐  /fake  PAIS
      Genera identidad falsa: nombre, dirección, teléfono, email.
      Países disponibles: MX  US  ES  FR  DE  UK  BR  CA  IT  JP  AU  AR
      Ejemplo:  /fake MX

  ⭐  /nm  NUMERO
      Información de número telefónico: país, operadora, tipo.
      Ejemplo:  /nm 5215512345678

  ⭐  /ip  DIRECCION
      Lookup de IP o dominio: país, ISP, ASN, coordenadas.
      Ejemplo:  /ip 8.8.8.8

  ⭐  /gen  BIN  [cantidad]
      Genera tarjetas a partir de un BIN. Default: 10.
      Ejemplo:  /gen 411111 20

  ⭐  /sk  sk_live_...
      Verifica una Stripe Secret Key (live o test).
      Ejemplo:  /sk sk_live_AbCdEfGhIj...

  ⭐  /site  URL
      Analiza un sitio web: status HTTP, plataforma de pagos detectada.
      Ejemplo:  /site https://tienda.com

  ⭐  /tmail
      Genera un email temporal con inbox. Botones: ver correos,
      copiar dirección, renovar, marcar como leído.

  ⭐  /scr  URL
      Scraper de tarjetas en una página web.
      Ejemplo:  /scr https://foro.com/hilo/12345


═══════════════════════════════════════════════════════════════════════════
  GATES  (pasarelas de pago)
═══════════════════════════════════════════════════════════════════════════

  Requisitos para usar gates:
    ─  Usuario no baneado
    ─  Gate en estado ON
    ─  Créditos disponibles (o rango staff)
    ─  Cooldown spam cumplido
    ─  BIN de la tarjeta no baneado
    ─  Chat autorizado (premium)

  El crédito se DEVUELVE si el gate falla por error interno.
  El crédito NO se devuelve si la tarjeta es declinada.

  Formato de tarjeta:  numero|mes|año|cvv
  Mes: 2 dígitos (01-12)   Año: 4 dígitos (2025-2030)

  ──────────────────────────────────────────────────────────────────────

  ⭐  /amz  CC|MM|YY|CVV
      Gate Amazon MX — billing test.
      Requiere /cookie guardada previamente.
      Después de ingresar la tarjeta aparece un menú para seleccionar
      la región de tu cookie (MX, US, ES, IT, DE, FR, UK, CA, BR,
      AU, JP, IN, SG, PL, NL, AE, SA, TR).
      Ejemplo:  /amz 4111111111111111|12|2026|123

  ⭐  /mamz  (lista de tarjetas, una por línea)
      Gate Amazon MX en masa. Máximo 10 tarjetas por llamada.
      Requiere /cookie. Tarjetas con BIN baneado o en cooldown se omiten.
      Se procesan en paralelo con ThreadPoolExecutor.
      Ejemplo:
          /mamz
          4111111111111111|12|2026|123
          5200828282828210|08|2027|456

  ⭐  /amzg  CC|MM|YY|CVV
      Gate Amazon Global (Paloma) — billing test.
      Requiere /cookie. La región se detecta sola desde la cookie.
      Soporta múltiples regiones (ES, MX, US, IT, DE, FR, UK, etc.)
      Ejemplo:  /amzg 4111111111111111|12|2026|123

  ⭐  /tcl  CC|MM|YY|CVV|MONTO|NUMERO
      Gate Telcel MX — recarga real a número de teléfono.
      Montos válidos (MXN): $20 / $30 / $50 / $80 / $100 / $150 / $200 / $300 / $500
      Ejemplo:  /tcl 4111111111111111|12|2026|123|50|5548448605


═══════════════════════════════════════════════════════════════════════════
  STAFF — GESTIÓN DE USUARIOS
═══════════════════════════════════════════════════════════════════════════

  🔑  /user  UID
      Panel completo del usuario: información, historial, acciones rápidas.

  🔑  /prmn  UID|DIAS   ·   /prmn  UID|DIAS|CREDITOS
      Promueve a premium. Si no se especifican créditos, default: 100.
      Ejemplo:  /prmn 123456789|30
      Ejemplo:  /prmn 123456789|30|200

  🔑  /rban  UID
      Banea a un usuario.

  🔑  /ruban  UID
      Desbanea a un usuario.

  🔑  /cred  UID|CREDITOS
      Asigna créditos a un usuario.
      Ejemplo:  /cred 123456789|500

  🔑  /rname  UID|NOMBRE
      Renombra el nombre display (c_name) de un usuario.
      Ejemplo:  /rname 123456789|VIP Client

  🔑  /delay  UID|SEGUNDOS
      Ajusta el cooldown spam de un usuario.
      Ejemplo:  /delay 123456789|20

  🔑  /admin  UID   (o responder a un mensaje)
      Promueve a Admin.

  🔑  /unadmin  UID   (o responder a un mensaje)
      Quita el rango Admin.

  🔑  /key  DIAS|CREDITOS
      Genera una llave de activación premium.
      Ejemplo:  /key 30|100

  🔑  /info  UID
      Muestra todos los datos de un usuario en la DB.


═══════════════════════════════════════════════════════════════════════════
  STAFF — GESTIÓN DE COMANDOS
═══════════════════════════════════════════════════════════════════════════

  🔑  /cmds
      Panel paginado de todos los comandos registrados en la DB.
      Secciones: Tools, Gates (charge), Mass.

  🔑  /addcmd  COMANDO|TIPO|NOMBRE|USO|COMENTARIO
      Registra un nuevo comando en la DB.
      Tipo: tool · charge · mass · auth
      Ejemplo:  /addcmd mj|charge|Mojito Gate|cc|mm|yy|cvv|Gate Mojito

  🔑  /delcmd  COMANDO
      Elimina un comando de la DB.
      Ejemplo:  /delcmd mj

  🔑  /mod  COMANDO|CAMPO|VALOR
      Modifica un campo de un comando en la DB.
      Campos disponibles:  status · mode · name · use · comentario · gate
      status valores:  on · off
      mode   valores:  on · of · ma
      Ejemplo:  /mod amz mode of          ← pone amz offline
      Ejemplo:  /mod bin name BIN Lookup  ← cambia nombre display

  🔑  /stat_c  COMANDO
      Muestra el estado actual de un comando en la DB.
      Ejemplo:  /stat_c amz

  🔑  /binban  BIN        ← banea el BIN
      /bban                ← alias
      /rbin   BIN          ← elimina el BIN de la lista
      /binban list         ← lista BINs baneados
      Ejemplo:  /binban 411111


═══════════════════════════════════════════════════════════════════════════
  STAFF — VENTAS Y PLANES
═══════════════════════════════════════════════════════════════════════════

  💰  /sell  UID|PLAN|METODO   ·   /vender
      Registra una venta y promueve al cliente a premium automáticamente.
      El plan debe existir en la tabla plans (ver /prices).
      Método: USDT, PayPal, Binance, etc.
      Ejemplo:  /sell 123456789|Premium 31 dias|USDT

  🔑  /sales   ·   /ventas
      Reporte de ventas del mes actual.
      /sales         → reporte global (todas las ventas)
      /sales me      → solo tus propias ventas
      /sales UID     → ventas de un vendedor específico

  🔑  /seller  UID   (o responder a un mensaje)
      Asigna rango Seller a un usuario.

  🔑  /unseller  UID   (o responder a un mensaje)
      Quita el rango Seller.

  🔑  /addplan  NOMBRE|DIAS|CREDITOS|PRECIO
      Crea un nuevo plan de venta en la DB.
      Ejemplo:  /addplan VIP 7 dias|7|50|15

  🔑  /delplan  NOMBRE
      Elimina un plan de la DB.
      Ejemplo:  /delplan VIP 7 dias


═══════════════════════════════════════════════════════════════════════════
  STAFF — SOPORTE Y TICKETS
═══════════════════════════════════════════════════════════════════════════

  🔑  /tickets
      Lista los tickets pendientes en el canal de soporte.

  🔑  /tk  ID
      Ver detalle completo de un ticket.
      Ejemplo:  /tk 42

  🔑  /tclose  ID
      Cierra el ticket y envía DM de notificación al usuario.
      Ejemplo:  /tclose 42


═══════════════════════════════════════════════════════════════════════════
  OWNER — EXCLUSIVOS
═══════════════════════════════════════════════════════════════════════════

  👑  /history  [UID]
      Audit trail: últimos 15 eventos del bot.
      /history         → todos los eventos
      /history UID     → solo eventos de ese usuario

  👑  /broadcast  MENSAJE
      Envía un mensaje masivo a todos los usuarios registrados.

  👑  /gusers
      Lista todos los User IDs registrados en la DB.


═══════════════════════════════════════════════════════════════════════════
  COOLDOWNS Y LÍMITES ANTI-ABUSE
═══════════════════════════════════════════════════════════════════════════

  ┌────────────────────────────────────────────────────────────────────┐
  │  Campo spam en users (segundos entre usos consecutivos de gates)   │
  │                                                                    │
  │  free      60 segundos  (default al registrarse)                   │
  │  premium   40 segundos  (al hacer upgrade)                         │
  │  admin     sin límite                                              │
  │  owner     sin límite                                              │
  │                                                                    │
  │  Anti-abuse (tabla card_uses):                                     │
  │  Misma tarjeta  +3 usos en 1 hora  →  warn + BIN auto-baneado      │
  │  Cooldown activo                   →  esperar, sin penalización     │
  └────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  CALLBACKS (BOTONES INLINE)
═══════════════════════════════════════════════════════════════════════════

  tools          →  Panel de herramientas paginado
  gates          →  Panel de gates paginado
  charge / mass  →  Sub-panel por tipo de gate
  user           →  Panel de usuario
  promote        →  Promover usuario a premium (desde panel /user)
  unpromote      →  Quitar premium (desde panel /user)
  amz_run        →  Selector de región Amazon (flow /amz)
  rg_fake        →  Regenerar datos fake
  rg_ccs         →  Regenerar tarjetas generadas
  clean          →  Cerrar / limpiar menú inline
  pg / pgn       →  Paginación de paneles
  tmail_*        →  Acciones de correo temporal (refresh, copy, read, new)


╔═══════════════════════════════════════════════════════════════╗
║  🍸 = info   ⚡ = status   💳 = gate/tarjeta   👤 = usuario     ║
╚═══════════════════════════════════════════════════════════════╝

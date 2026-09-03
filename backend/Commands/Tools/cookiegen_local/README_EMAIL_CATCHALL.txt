
  ╔═══════════════════════════════════════════════════════════════════╗
  ║        EMAIL CATCH-ALL — GUIA DE CONFIGURACION                   ║
  ║        Amazon CookieGen by Sxgitario                             ║
  ║        Soporte: https://t.me/Sxgitario                          ║
  ╚═══════════════════════════════════════════════════════════════════╝

  El generador usa Gmail como bandeja central. Cada dominio que
  configures redirige TODOS los correos entrantes a ese Gmail,
  sin importar la direccion usada.

  Cuando tengas el dominio listo, agregalo en main.py:

      _MAIL_DOMAINS = [
          "shopsxgitario.com",
          "sxgitarioshop.com",
          "tudominio.com",    <-- aqui
      ]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  CUANTOS DOMINIOS NECESITAS
  Cada dominio .com aguanta ~10-20 cuentas/dia antes de que Amazon
  empiece a pedir captcha en el primer intento.

      50-100  cuentas/dia  -->  1-2 dominios
      100-300 cuentas/dia  -->  3-4 dominios
      300-600 cuentas/dia  -->  5-6 dominios
      60+     cuentas/dia  -->  7+ dominios

  Señal de dominio quemado: captcha aparece en intento #1
  de forma consistente. Sacalo de _MAIL_DOMAINS y compra uno nuevo.

  Consejo: .com quema 2-3x mas lento que .xyz / .top / .click
           No uses el mismo dominio en dos instancias a la vez.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [1] NAMECHEAP (RECOMENDADO)
  ─────────────────────────────────────────────────────────────────

  PASO 1 — Comprar el dominio
    - Preferiblemente .com
    - Namecheap enviara un email de verificacion de ICANN al terminar
      la compra — confirmalo o el dominio queda suspendido

  PASO 2 — Configurar el catch-all
    1. namecheap.com --> Domain List --> Manage (tu dominio)
    2. Busca la seccion "Redirect Email" --> Email Routing
    3. Click "Add Catch-All"
    4. Destino: nexxusbot4@gmail.com
    5. Guardar -- debe aparecer: * --> nexxusbot4@gmail.com

  PASO 3 — Verificar
    Envia un email a test@tudominio.com desde cualquier cuenta.
    Debe llegar al Gmail en menos de 2 minutos.
    Si no llega en 5 min, el DNS esta propagando — espera 15-30 min.

  NOTA: Si cambias los nameservers a Cloudflare este panel desaparece.
        En ese caso usa el metodo de Cloudflare (ver abajo).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [2] CLOUDFLARE
  ─────────────────────────────────────────────────────────────────
  Requiere que el dominio use nameservers de Cloudflare.

    1. dash.cloudflare.com --> selecciona tu dominio
    2. Menu izquierdo --> Email --> Email Routing
    3. Si no esta activo: "Enable Email Routing" --> Confirm
       (Cloudflare agrega los MX records automaticamente)
    4. Routing rules --> Catch-all --> Edit
    5. Action: Send to --> nexxusbot4@gmail.com --> Save
    6. Cloudflare enviara un email de verificacion al Gmail --
       confirmalo o el reenvio no funciona.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [3] GODADDY
  ─────────────────────────────────────────────────────────────────
    1. godaddy.com --> My Products --> Domains --> Manage
    2. Pestaña Email (arriba) --> Manage junto a Email Forwarding
    3. Add Forwarder
    4. From: @ (o @tudominio.com) para catch-all
    5. To: nexxusbot4@gmail.com
    6. Save

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [4] PORKBUN
  ─────────────────────────────────────────────────────────────────
  Email Forwarding incluido gratis en todos sus dominios.

    1. porkbun.com --> tu dominio --> Details
    2. Email Forwarding --> Add Email Forward
    3. Alias: *  (asterisco = catch-all)
    4. Destination: nexxusbot4@gmail.com
    5. Save

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [5] SQUARESPACE DOMAINS (antes Google Domains)
  ─────────────────────────────────────────────────────────────────
    1. domains.squarespace.com --> tu dominio --> Settings
    2. Menu izquierdo --> Email
    3. Email forwarding --> Add email alias
    4. Alias: @ o busca "Catch-all / Forward all"
    5. Destino: nexxusbot4@gmail.com
    6. Save

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [6] NAME.COM
  ─────────────────────────────────────────────────────────────────
    1. name.com --> My Domains --> tu dominio --> Manage
    2. Menu izquierdo --> Email Forwarding
    3. Add Email Forward
    4. Forwarding Address: *  (catch-all)
    5. Destination: nexxusbot4@gmail.com
    6. Save

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

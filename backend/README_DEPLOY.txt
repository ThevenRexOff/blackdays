
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ██████╗ ███████╗██████╗ ██╗      ██████╗ ██╗   ██╗                    ║
║   ██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗╚██╗ ██╔╝                    ║
║   ██║  ██║█████╗  ██████╔╝██║     ██║   ██║ ╚████╔╝                     ║
║   ██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║  ╚██╔╝                      ║
║   ██████╔╝███████╗██║     ███████╗╚██████╔╝   ██║                       ║
║   ╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝                       ║
║                                                                          ║
║             V P S  ·  R D P  ·  W E B H O O K  ·  H O S T              ║
╚══════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════
  DOS MODOS DE EJECUCIÓN
═══════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────┬──────────────────────────────────────┐
  │   MODO POLLING               │   MODO WEBHOOK                       │
  ├──────────────────────────────┼──────────────────────────────────────┤
  │  Solo Python 3+              │  Servidor con PHP 7.4+               │
  │  Sin URL pública necesaria   │  URL HTTPS pública obligatoria       │
  │  Ideal: VPS, RDP, local      │  Ideal: hosting, VPS con dominio     │
  │  Inicia: python3 poll.py     │  Inicia: python3 run.py              │
  │  El bot llama a Telegram     │  Telegram llama al servidor          │
  │                              │                                      │
  │  ✓ Más simple de configurar  │  ✓ Más eficiente en producción       │
  │  ✓ Cero deps de servidor     │  ✓ Solo activo cuando hay updates    │
  └──────────────────────────────┴──────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
  MODO POLLING — VPS (Linux)
═══════════════════════════════════════════════════════════════════════════

  Requisitos mínimos:

      CPU      1 core
      RAM      512 MB
      OS       Ubuntu 20.04+ / Debian 11+ / CentOS 8+
      Python   3.9+

  ──────────────────────────────────────────────────────────────────────
  Setup rápido en VPS nuevo:
  ──────────────────────────────────────────────────────────────────────

  1. Subir el proyecto al servidor:

         scp -r ./JILL_BOT usuario@IP_SERVIDOR:/home/usuario/

  2. Instalar Python:

         sudo apt update && sudo apt install -y python3 python3-pip

  3. Instalar dependencias del bot:

         cd ~/JILL_BOT
         pip3 install -r requirements.txt

  4. Correr el setup (elegir MODE=polling):

         python3 setup.py

  5a. Correr en background con screen (recomendado para pruebas):

         screen -S jill
         python3 poll.py

         Ctrl+A, D  →  desconectar (bot sigue corriendo)
         screen -r jill  →  reconectar

  5b. Correr con nohup (simple):

         mkdir -p logs
         nohup python3 poll.py > logs/poll.log 2>&1 &
         echo $! > poll.pid

         tail -f logs/poll.log    ← ver logs en vivo
         kill $(cat poll.pid)     ← detener el bot

  ──────────────────────────────────────────────────────────────────────
  Setup con systemd (recomendado para producción):
  ──────────────────────────────────────────────────────────────────────

  Crear el archivo de servicio:

      /etc/systemd/system/jillbot.service
      ┌──────────────────────────────────────────────────────────────┐
      │  [Unit]                                                      │
      │  Description=JILL Bot Polling                                │
      │  After=network.target                                        │
      │                                                              │
      │  [Service]                                                   │
      │  Type=simple                                                 │
      │  User=ubuntu                                                 │
      │  WorkingDirectory=/home/ubuntu/JILL_BOT                     │
      │  ExecStart=/usr/bin/python3 poll.py                          │
      │  Restart=always                                              │
      │  RestartSec=5                                                │
      │                                                              │
      │  [Install]                                                   │
      │  WantedBy=multi-user.target                                  │
      └──────────────────────────────────────────────────────────────┘

  Activar y arrancar:

      sudo systemctl daemon-reload
      sudo systemctl enable jillbot
      sudo systemctl start  jillbot
      sudo systemctl status jillbot
      journalctl -u jillbot -f    ← logs en tiempo real


═══════════════════════════════════════════════════════════════════════════
  MODO POLLING — RDP (Windows Server)
═══════════════════════════════════════════════════════════════════════════

  1. Instalar Python 3.9+ desde python.org

  2. En PowerShell o CMD:

         cd C:\Users\Usuario\JILL_BOT
         pip install -r requirements.txt
         python setup.py

  3. Correr en segundo plano:

         start /B python poll.py > poll.log 2>&1

  4. Para servicio persistente usar NSSM (Non-Sucking Service Manager):

         nssm install JillBot "C:\Python39\python.exe" "C:\...\poll.py"
         nssm start JillBot
         nssm status JillBot


═══════════════════════════════════════════════════════════════════════════
  MODO WEBHOOK — ESTRUCTURA EN SERVIDOR
═══════════════════════════════════════════════════════════════════════════

  Archivos necesarios en public_html (o www/, htdocs/):

      public_html/
      └── JILL_BOT/
          ├── index.php          ← receptor Telegram (ya incluido)
          ├── main.py
          ├── poll.py
          ├── run.py
          ├── Model/
          │   └── config.env
          ├── Commands/
          └── ...

  Registrar el webhook (automático con run.py o manual):

      python3 run.py     ← registra automáticamente al arrancar

      Verificar que quedó registrado:
      https://api.telegram.org/botTU_TOKEN/getWebhookInfo


═══════════════════════════════════════════════════════════════════════════
  NGINX + PHP-FPM  (VPS con dominio)
═══════════════════════════════════════════════════════════════════════════

  Configuración /etc/nginx/sites-available/jillbot.conf:

  ┌──────────────────────────────────────────────────────────────────────┐
  │  server {                                                            │
  │      listen 443 ssl;                                                 │
  │      server_name tudominio.com;                                      │
  │                                                                      │
  │      ssl_certificate      /etc/letsencrypt/live/tudominio.com/fullchain.pem;
  │      ssl_certificate_key  /etc/letsencrypt/live/tudominio.com/privkey.pem;
  │                                                                      │
  │      root /var/www/JILL_BOT;                                         │
  │      index index.php;                                                │
  │                                                                      │
  │      location ~ \.php$ {                                             │
  │          include snippets/fastcgi-php.conf;                          │
  │          fastcgi_pass unix:/run/php/php8.1-fpm.sock;                 │
  │      }                                                               │
  │                                                                      │
  │      # Proteger config.env                                           │
  │      location ~ /Model/config\.env { deny all; }                    │
  │      location ~ /\.                 { deny all; }                    │
  │  }                                                                   │
  │                                                                      │
  │  server {                                                            │
  │      listen 80;                                                      │
  │      server_name tudominio.com;                                      │
  │      return 301 https://$host$request_uri;                           │
  │  }                                                                   │
  └──────────────────────────────────────────────────────────────────────┘

  SSL gratuito con Let's Encrypt:

      sudo apt install certbot python3-certbot-nginx
      sudo certbot --nginx -d tudominio.com

  Activar y recargar:

      sudo nginx -t && sudo systemctl reload nginx


═══════════════════════════════════════════════════════════════════════════
  APACHE + PHP  (hosting compartido o VPS con Apache)
═══════════════════════════════════════════════════════════════════════════

  Configuración /etc/apache2/sites-available/jillbot.conf:

  ┌──────────────────────────────────────────────────────────────────────┐
  │  <VirtualHost *:443>                                                 │
  │      ServerName tudominio.com                                        │
  │      DocumentRoot /var/www/JILL_BOT                                  │
  │                                                                      │
  │      SSLEngine on                                                    │
  │      SSLCertificateFile    /etc/letsencrypt/live/tudominio.com/fullchain.pem
  │      SSLCertificateKeyFile /etc/letsencrypt/live/tudominio.com/privkey.pem
  │                                                                      │
  │      <Directory /var/www/JILL_BOT>                                   │
  │          AllowOverride All                                           │
  │          Require all granted                                         │
  │      </Directory>                                                    │
  │                                                                      │
  │      <Files "config.env">                                            │
  │          Require all denied                                          │
  │      </Files>                                                        │
  │  </VirtualHost>                                                      │
  └──────────────────────────────────────────────────────────────────────┘

      sudo a2ensite jillbot.conf
      sudo a2enmod ssl rewrite
      sudo systemctl reload apache2


═══════════════════════════════════════════════════════════════════════════
  ALWAYSDATA  (hosting compartido recomendado)
═══════════════════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────┐
  │  Alwaysdata incluye PHP, Python 3 y PostgreSQL en el mismo panel.   │
  │  Es el hosting recomendado para este bot.                            │
  └──────────────────────────────────────────────────────────────────────┘

  1. Panel alwaysdata → Web → Sitios → Agregar sitio
     Tipo: PHP, directorio: www/JILL_BOT

  2. Subir archivos vía SSH / SFTP:

         sftp usuario@ssh-usuario.alwaysdata.net
         put -r JILL_BOT/ www/JILL_BOT/

  3. Conectar por SSH y configurar:

         ssh usuario@ssh-usuario.alwaysdata.net
         cd ~/www/JILL_BOT
         pip3 install -r requirements.txt --user
         python3 setup.py
         # → MODE=webhook
         # → WEBHOOK_URL=https://usuario.alwaysdata.net/index.php

  Nota: Python en alwaysdata puede ser python3.9 o python3.11.
  Verificar versión disponible:  python3 --version


═══════════════════════════════════════════════════════════════════════════
  NOTAS SOBRE ASYNC_MODE
═══════════════════════════════════════════════════════════════════════════

  ASYNC_MODE=true   →  index.php lanza main.py en segundo plano y
                        retorna HTTP 200 a Telegram de inmediato.
                        Telegram no espera. Recomendado en producción.

  ASYNC_MODE=false  →  index.php espera a que main.py termine antes de
                        retornar. Útil para debugging pero más lento.
                        Telegram puede timeout si el comando tarda.


═══════════════════════════════════════════════════════════════════════════
  CHECKLIST ANTES DE LANZAR
═══════════════════════════════════════════════════════════════════════════

  [ ]  Python 3.9+ instalado en el servidor
  [ ]  pip install -r requirements.txt  completado sin errores
  [ ]  python3 setup.py  ejecutado y completado
  [ ]  config.env escrito con BOT_TOKEN, DB_* y OWNER_ID correctos
  [ ]  DB conectada y 11 tablas creadas  (setup lo confirma)
  [ ]  Modo elegido: webhook o polling
  [ ]  Bot iniciado: python3 run.py  o  python3 poll.py
  [ ]  /start responde en Telegram
  [ ]  ERROR_CHANNEL recibe errores del bot  (opcional pero recomendado)
  [ ]  Cron para tasks.py configurado  (opcional)


╔══════════════════════════════════════════════════════════════╗
║   VPS + polling  →  screen / systemd                        ║
║   Hosting + webhook  →  index.php + SSL + run.py            ║
╚══════════════════════════════════════════════════════════════╝

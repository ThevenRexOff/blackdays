

     ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗███████╗ ██████╗ ███████╗███╗   ██╗
    ██╔════╝██╔═══██╗██╔═══██╗██║ ██╔╝██║██╔════╝██╔════╝ ██╔════╝████╗  ██║
    ██║     ██║   ██║██║   ██║█████╔╝ ██║█████╗  ██║  ███╗█████╗  ██╔██╗ ██║
    ██║     ██║   ██║██║   ██║██╔═██╗ ██║██╔══╝  ██║   ██║██╔══╝  ██║╚██╗██║
    ╚██████╗╚██████╔╝╚██████╔╝██║  ██╗██║███████╗╚██████╔╝███████╗██║ ╚████║
     ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝

                   Amazon Account Cookie Generator
                   Powered by Sxgitario @ Api Gateway Services


    ═══════════════════════════════════════════════════════════════════════
      WHAT IT DOES
    ═══════════════════════════════════════════════════════════════════════

    Generates fully registered Amazon accounts and returns authenticated
    session cookies ready to use. Each run produces:

        >  A fake but realistic profile (name, email, password)
        >  A verified identity — a private email address on a domain
           you own, with Gmail catch-all forwarding (see README_EMAIL_CATCHALL.txt)
        >  Billing address attached to the account
        >  Complete session cookie string for import into any browser

    Generation time:  10 - 40 seconds per account
    Cost per account: free (email channel only)


    ═══════════════════════════════════════════════════════════════════════
      REQUIREMENTS
    ═══════════════════════════════════════════════════════════════════════

    >  Python 3.9 or newer
    >  Pillow (PIL) — REQUIRED, not optional. See "WHY PILLOW MATTERS" below.
       `pip install -r requirements.txt` already installs it; do not skip
       this step or remove it if you hand-roll a virtualenv.
    >  At least one domain with email catch-all pointing to your Gmail.
       See README_EMAIL_CATCHALL.txt for setup instructions.
    >  (Recommended) Residential proxy for stable results


    ═══════════════════════════════════════════════════════════════════════
      WHY PILLOW MATTERS (read this before reporting a "captcha every time"
      bug)
    ═══════════════════════════════════════════════════════════════════════

    The fingerprint generator (`amazon/metadataGenSxgitario.py`) builds a
    "canvas fingerprint" using Pillow to render a small fake image and
    hash its pixels. If Pillow is missing, the code does NOT crash — it
    silently falls back to a much smaller, generic filler value instead.

    That fallback payload is dramatically smaller (~7KB vs ~92KB) and is
    empirically the kind of fingerprint Amazon's anti-bot system flags far
    more often, escalating to a captcha on almost every single attempt.

    Bottom line: always run `pip install -r requirements.txt` inside
    whatever environment (venv or global) you actually use to run
    `main.py`, and never remove Pillow from it.


    ═══════════════════════════════════════════════════════════════════════
      QUICK START
    ═══════════════════════════════════════════════════════════════════════

    Step 1 — Buy a .com domain and configure email catch-all to your Gmail.
             See README_EMAIL_CATCHALL.txt for step-by-step instructions.

    Step 2 — Open main.py and add your domain(s) to _MAIL_DOMAINS:

                 _MAIL_DOMAINS = [
                     "yourdomain.com",
                 ]

    Step 3 — Install Python dependencies:

                 pip install -r requirements.txt

    Step 4 — Run:

                 python main.py


    ═══════════════════════════════════════════════════════════════════════
      main.py vs. account_creator.py
    ═══════════════════════════════════════════════════════════════════════

    main.py is the CLI you actually run — animated dashboard, --debug mode,
    country selectable via argv:

        python main.py               (US, animated dashboard)
        python main.py CA            (Canada, animated dashboard)

    Run in DEBUG mode — plain terminal output instead of the Textual
    dashboard, so every attempt (including retries) stays in your
    terminal's normal scrollback and can be copy/pasted or grepped:

        python main.py US --debug
        python main.py US -d

    account_creator.py has just the engine — the `AmazonAccountCreator`
    class and every flow step, no CLI/dashboard/argv at all. Import it
    directly if you want to drive registrations from your own script:

        from account_creator import AmazonAccountCreator
        result = AmazonAccountCreator(
            country     = 'US',
            proxy       = 'user:pass@host:port',
            mailDomains = ['yourdomain.com'],
        ).processRegistration()


    ═══════════════════════════════════════════════════════════════════════
      HOW THE EMAIL CHANNEL WORKS
    ═══════════════════════════════════════════════════════════════════════

    The tool uses a Gmail inbox as a catch-all backend. Every domain in
    _MAIL_DOMAINS forwards all incoming email to that inbox; the tool reads
    the OTP code via IMAP.

    Per-account flow:
        1. A random domain is picked from _MAIL_DOMAINS
        2. A human-looking local part is generated from the fake profile
           name (e.g. ashley.black94@yourdomain.com instead of a random
           string)
        3. That address is submitted on Amazon's registration form
        4. Amazon sends the OTP to that address — it arrives at Gmail
           via catch-all forwarding
        5. The tool reads it via IMAP (header scan, no SEARCH lag)
        6. OTP is submitted and the account is finalized

    Using multiple domains spreads registration volume and slows down
    domain reputation burn. See README_EMAIL_CATCHALL.txt for how many
    domains you need based on daily volume.


    ═══════════════════════════════════════════════════════════════════════
      CAPTCHA HANDLING
    ═══════════════════════════════════════════════════════════════════════

    When Amazon serves a captcha during registration, the tool raises
    captcha_appeared immediately and retries with a fresh session
    (new WAF token + new fingerprint). A second attempt usually clears it.

    No captcha-solving service is needed or used. The retry approach
    works because the captcha is almost always triggered by a stale WAF
    token or fingerprint mismatch — a fresh session avoids it entirely
    on the next try.

    If captcha appears on attempt #1 consistently for EVERY account, the
    domain is burned. Add new domains to _MAIL_DOMAINS and remove the
    burned one.


    ═══════════════════════════════════════════════════════════════════════
      SUPPORTED COUNTRIES
    ═══════════════════════════════════════════════════════════════════════

        Code  Country           Domain
        ----  ----------------  ---------------
        US    United States     amazon.com
        CA    Canada            amazon.ca
        MX    Mexico            amazon.com.mx
        BR    Brazil            amazon.com.br
        UK    United Kingdom    amazon.co.uk
        DE    Germany           amazon.de
        FR    France            amazon.fr
        IT    Italy             amazon.it
        ES    Spain             amazon.es
        NL    Netherlands       amazon.nl
        SG    Singapore         amazon.sg
        AU    Australia         amazon.com.au
        JP    Japan             amazon.co.jp

    Not supported (confirmed incompatible with email channel):
        AE, SA, IN  — Amazon requires a real phone number for these markets
        PL, TR      — register POST returns "passwords don't match" (CSE key
                      mismatch, root cause unconfirmed)


    ═══════════════════════════════════════════════════════════════════════
      CONFIGURATION OPTIONS
    ═══════════════════════════════════════════════════════════════════════

    AmazonAccountCreator(
        country         = 'US',           (any of the 13 codes above)
        proxy           = None,           (optional residential proxy,
                                            'user:pass@host:port')
        verbose         = True,           (animated terminal output)
        clearScreen     = True,           (clear terminal between attempts —
                                            set False or use --debug to keep
                                            every attempt in scrollback)
        mailDomains     = ['...'],        (list of domains with catch-all
                                            configured — see main.py)
    ).processRegistration()


    ═══════════════════════════════════════════════════════════════════════
      OUTPUT FORMAT
    ═══════════════════════════════════════════════════════════════════════

    Success response:

        {
            "status":               True,
            "profile":              {
                "name":     "Ashley Black",
                "email":    "ashley.black94@yourdomain.com",
                "password": "TeamArgo4821"
            },
            "message":              "Account created successfully.",
            "billingAddressStatus": True,
            "billingMessage":       "Billing Address Added",
            "cookies":              "session-id=...; at-main=...; ...",
            "time_taken":           18.4,
            "retries":              0,
        }

    Failure response:

        {
            "status":  False,
            "message": "error description here",
        }


    ═══════════════════════════════════════════════════════════════════════
      TROUBLESHOOTING
    ═══════════════════════════════════════════════════════════════════════

        unusual_activity      Amazon flagged the session
                              -->  use a residential proxy matching country

        email_associated      Email address already tied to an existing account
                              -->  automatic retry with a fresh address

        email_timeout         OTP not received within 3 minutes
                              -->  check your domain catch-all is configured
                                   correctly (send a test email to anything@
                                   yourdomain.com and verify it lands at Gmail)

        captcha_appeared      Captcha shown during registration
                              -->  automatic retry with fresh session — usually
                                   clears on attempt #2. If it appears on every
                                   single attempt, the domain is burned: add a
                                   new domain and remove the burned one.

        no_arb                Amazon silently rejected the session on the
                              claim step
                              -->  use a residential proxy in the target country

        Captcha every single  You are very likely missing Pillow. Run
        attempt               `pip install -r requirements.txt` in the SAME
                              Python environment you run main.py from.


    ═══════════════════════════════════════════════════════════════════════
      TIPS FOR BEST RESULTS
    ═══════════════════════════════════════════════════════════════════════

    >  Never skip `pip install -r requirements.txt`, and never remove
       Pillow from a virtualenv — see "WHY PILLOW MATTERS".
    >  Use a residential proxy in the target country. Datacenter IPs get
       flagged by Amazon.
    >  Use `--debug` mode whenever you need to read or share what actually
       happened on a run — the normal dashboard mode can't be copy/pasted
       out of most terminals.
    >  Run multiple domains to slow reputation burn. See README_EMAIL_CATCHALL.txt
       for the recommended domain count by daily volume.
    >  .com domains burn 2-3x slower than .xyz / .top / .click
    >  If errors persist, wait 10-15 minutes. Amazon rate-limits by IP.


    ═══════════════════════════════════════════════════════════════════════
      LICENSE & SUPPORT
    ═══════════════════════════════════════════════════════════════════════

    This software is licensed for personal use only. Redistribution,
    reverse engineering, or reselling of this tool is strictly prohibited
    under the Sxgitario Gateway End User License Agreement.

    For support or to inquire about additional features:

        Shop (Telegram)    https://t.me/Sxgitario
        Dev  (Telegram)    https://t.me/Vxsilisk


    ═══════════════════════════════════════════════════════════════════════

                            Sxgitario (c) Api Gateway Services
                         May your cookies never die.

    ═══════════════════════════════════════════════════════════════════════

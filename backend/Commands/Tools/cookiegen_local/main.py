#!/usr/bin/env python3

'''
 #! =====================================================================================
 #! [⚠️] README — AMAZON PWA | COOKIEGEN FLOW (MULTI-MARKETPLACE)
 #! =====================================================================================
 #*
 #* Autor: Vxsilisk © Sxgitario Gateway API Service
 #* Proyecto: Amazon PWA Account Creator (CookieGen)
 #* Región: 18 mercados configurables (ver README.txt)
 #*
 #* Este archivo es el CLI (dashboard animado, modo --debug, pool de
 #* proxies sticky). El motor (clase `AmazonAccountCreator`) vive en
 #* `account_creator.py` — impórtala de ahí si quieres usarla en tu propio
 #* script sin el dashboard.
 #*
 #? -------------------------------------------------------------------------------------
 #?  REQUISITOS
 #? -------------------------------------------------------------------------------------
 #* Python 3.9+
 #*
 #* Librerías necesarias:
 #*   pip install -r requirements.txt
 #*
 #? -------------------------------------------------------------------------------------
 #?  FUNCIONALIDADES CLAVE
 #? -------------------------------------------------------------------------------------
 #* - Fingerprint real (perfiles de hardware coherentes)
 #* - Sesiones persistentes con cookies reales (curl_cffi)
 #* - Generación de perfil falso (Faker, locale por país)
 #* - Verificación por número real (5sim/HeroSMS/SMSCode.gg) o mail.tm gratis
 #* - Manejo de estados:
 #*     • Account created ✅
 #*     • Unusual activity ❌ (retry con nuevo número)
 #*     • Number already associated ❌ (retry con nuevo número)
 #*     • SMS timeout ❌ (retry limitado)
 #*     • Captcha sin CapSolver configurado ❌ (retry con nuevo número)
 #*     🇺🇸US, 🇨🇦CA, 🇲🇽MX, 🇧🇷BR, 🇬🇧UK, 🇩🇪DE, 🇫🇷FR, 🇮🇹IT, 🇪🇸ES, 🇳🇱NL, 🇸🇬SG, 🇯🇵JP
 #*
 #? -------------------------------------------------------------------------------------
 #?  USO
 #? -------------------------------------------------------------------------------------
 #*   python main.py                  (US, dashboard animado)
 #*   python main.py CA               (Canadá, dashboard animado)
 #*   python main.py US --debug       (sin dashboard, output plano — copiable)
 #*
 #? -------------------------------------------------------------------------------------
 #?  SOPORTE / CONTACTO
 #? -------------------------------------------------------------------------------------
 #* Telegram (SHOP): https://t.me/Sxgitario
 #* Telegram (DEV):  https://t.me/Vxsilisk
 #*
 #? Gracias por usar Sxgitario Gateway API Service ✨
 #! =====================================================================================
'''

import importlib.util
import os, sys
from pathlib import Path

_utf8_module_path = Path(__file__).resolve().parent / 'services' / 'terminal_utf8.py'
_utf8_spec = importlib.util.spec_from_file_location('_sxg_terminal_utf8', _utf8_module_path)
if _utf8_spec and _utf8_spec.loader:
    _utf8_mod = importlib.util.module_from_spec(_utf8_spec)
    _utf8_spec.loader.exec_module(_utf8_mod)
    _utf8_mod.enforce_process_utf8(__file__, sys.argv[1:])

from services import Log
from account_creator import AmazonAccountCreator


#//! ------------------------------------- Entrypoint ------------------------------------- !\\#
# ─────────────────────────────────────────────────────────────────────────────
# DOMINIOS DE EMAIL — agrega los dominios con catch-all activado.
# Ver README_EMAIL_CATCHALL.txt para instrucciones de configuracion.
#
#   1–10 cuentas/día   →  1–2 dominios
#   10–30 cuentas/día  →  3–4 dominios
#   30–60 cuentas/día  →  5–6 dominios
#   60+ cuentas/día    →  7+ dominios
# ─────────────────────────────────────────────────────────────────────────────
_MAIL_DOMAINS = [
    "vxsilisk.com",       # Cloudflare routing — llega a INBOX
    "shopsxgitario.com",  # Namecheap eforward — puede ir a Spam (ver mailx.py)
    "sxgitarioshop.com",  # Namecheap eforward — puede ir a Spam (ver mailx.py)
]


def _printResult(cookies: dict, targetCountry: str) -> None:
    if cookies['status']:
        Log.detail(f"Cookies ({targetCountry})", cookies['cookies'])
        Log.result(True, {
            "Name":            cookies['profile']['name'],
            "Email":           cookies['profile']['email'],
            "Password":        cookies['profile']['password'],
            "Country":         targetCountry,
            "Billing":         cookies['billingMessage'],
            "Canvas Strategy": cookies.get('canvas_strategy', ''),
            "Time":            f"{cookies['time_taken']:.2f}s",
            "Retries":         cookies['retries'],
            "Powered By":      cookies['PoweredBy'],
        })
    else:
        Log.result(False, {"Reason": cookies['message'], "Powered By": cookies['PoweredBy']})


def _printCanvasReport() -> None:
    try:
        from services.canvas_tracker import format_report_lines, build_report
        r = build_report()
        if r.get("total_accounts", 0) > 0:
            for line in format_report_lines():
                Log.info(line)
    except Exception:
        pass


if __name__ == '__main__':
    _argv = sys.argv[1:]
    debugMode = '--debug' in _argv or '-d' in _argv
    _argv = [a for a in _argv if a not in ('--debug', '-d')]
    targetCountry = _argv[0].upper() if _argv else 'US'


    if debugMode:
        Log.detach()

        creator = AmazonAccountCreator(
            country      = targetCountry,
            verbose      = True,
            clearScreen  = False,
            mailDomains  = _MAIL_DOMAINS,
        )

        cookies = creator.processRegistration()
        _printResult(cookies, targetCountry)
        _printCanvasReport()


    else:
        from services.dashboard import RegistrationDashboard


        def _runRegistration(dashboard):
            Log.attach(dashboard)

            creator = AmazonAccountCreator(
                country      = targetCountry,
                verbose      = True,
                mailDomains  = _MAIL_DOMAINS,
            )
            cookies = creator.processRegistration()
            _printResult(cookies, targetCountry)
            _printCanvasReport()


        _dashboard = RegistrationDashboard(on_start=_runRegistration)
        _dashboard.run()

        if _dashboard.final_result and _dashboard.final_result.get('cookie'):
            print("\nFull cookie:")
            print(_dashboard.final_result['cookie'])

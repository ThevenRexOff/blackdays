"""AmazonAccountCreator — the CookieGen registration engine.

Construct con tu config (país, proxy, dominios de email)
y llama `.processRegistration()`. No CLI, no dashboard, no argv parsing —
eso vive en `main.py`.

Autor: Vxsilisk © Sxgitario Gateway API Service
Proyecto: Amazon PWA Account Creator (CookieGen)

Manejo de estados:
    Account created ✅
    Unusual activity ❌ (retry con nueva identidad)
    Email timeout ❌ (retry con nueva dirección)
    Captcha ❌ (retry con nueva sesión)

Ejemplo:
    AmazonAccountCreator(
        country     = 'US',
        proxy       = 'user:pass@host:port',
        mailDomains = ['tudominio.com'],
    ).processRegistration()

Telegram (SHOP): https://t.me/Sxgitario
Telegram (DEV):  https://t.me/Vxsilisk
"""

import json
import os
import time
from pathlib import Path

from services import MailTM, Log, EscListener
from amazon import core, helpers, flow, AmazonRegisterError, AccountBuilder
from amazon.metadataGenSxgitario import FwcimAmazonSxgitario


#//! ------------------------------------- Main Flow Orchestrator ------------------------------------- !\\#
class AmazonAccountCreator:

    def __init__(self, country: str = 'US', proxy: str = None,
                 verbose: bool = True, clearScreen: bool = True,
                 mailDomains: list = None,
                 gmailUser: str = None, gmailPass: str = None) -> None:
        if country not in core.countrys_supported:
            raise ValueError(f"Country '{country}' is not supported. Use: {', '.join(core.countrys_supported)}")
        self.verbose         = verbose
        #//! Clearing the screen between attempts looks clean interactively,
        #//! but destroys every earlier attempt's output — including the
        #//! one showing WHY a captcha appeared — before it can be read or
        #//! copied out of the terminal's scrollback. Set False (debug mode
        #//! does this automatically) to keep every attempt's output intact.
        self.clearScreen     = clearScreen
        Log.verbose          = verbose
        self.targetCountry   = country

        self.domain          = core.DOMAIN_MAP[country]
        self.baseUrl         = f"https://www.{self.domain}"
        self.assocHandle     = core.ASSOC_HANDLE_MAP[country]
        self.registerUrl     = core.MANAGE_URLS[country]
        self.targetDomain    = self.domain
        self.proxy           = proxy
        self.user            = helpers.generateFakeProfile(country)
        self.phoneData       = None
        self.mailService     = MailTM(firstName=self.user.f_name, lastName=self.user.l_name,
                                      proxy=proxy, domains=mailDomains,
                                      imapUser=gmailUser, imapPass=gmailPass)


    #//! -------------------- Public entry point -------------------- !\\#
    def processRegistration(self, retry: int = 0) -> dict:
        # Reset canvas state so each account gets its own strategy+hash
        FwcimAmazonSxgitario.reset_session()

        try:
            from services import canvas_tracker as _ct
            banned0 = _ct.banned_strategies()
            newly   = _ct.apply_auto_ban()
            if newly:
                Log.warn(f"Canvas auto-ban: {', '.join(newly)}")
            elif banned0:
                Log.warn(f"Canvas banned: {', '.join(sorted(banned0))}")
        except Exception:
            pass

        try:
            if self.verbose and self.clearScreen and not Log._dashboard: os.system('cls' if os.name == 'nt' else 'clear')
            Log.banner(["Amazon PWA", f"Attempt #{retry + 1}"])

            if not hasattr(self, '_esc') or not self._esc._running:
                self._esc = EscListener().start()

            self.initTime = time.time()

            if not self.phoneData:
                spinner = Log.spinner("Acquiring identifier...").start()
                self.phoneData = self.mailService.getNumber()
                spinner.stop(f"Identifier acquired: {self.phoneData['number']}")
            else:
                Log.success(f"Identifier: {self.phoneData['number']}")
            Log.detail("Activation ID", self.phoneData['activationId'])

            self._esc.check()
            cookies = self.__executeFlow()

            if self.verbose and self.clearScreen and not Log._dashboard: os.system('cls' if os.name == 'nt' else 'clear')
            spinner = Log.spinner("Adding billing address...").start()
            billing = AccountBuilder(cookies, country=self.targetCountry).handleBillingAddress()
            if billing['status']: spinner.stop(billing['message'])
            else: spinner.fail(billing['message'])

            if hasattr(self, '_esc'): self._esc.stop()

            profileDict = {
                "name":     f"{self.user.f_name} {self.user.l_name}",
                "email":    self.phoneData['number'],
                "password": self.user.password,
            }
            result = {
                "status":               True,
                "profile":              profileDict,
                "message":              "Account created successfully.",
                "billingAddressStatus": billing['status'],
                "billingMessage":       billing['message'],
                "cookies":              cookies,
                "time_taken":           time.time() - self.initTime,
                "retries":              retry,
                "canvas_strategy":      FwcimAmazonSxgitario.current_canvas_strategy(),
            }
            self._saveOutput(result)
            try:
                from services import canvas_tracker as _ct
                _ct.record_account_result(FwcimAmazonSxgitario.current_canvas_strategy(), success=True)
            except Exception:
                pass
            return result

        except KeyboardInterrupt:
            return self.__handleCancellation()
        except Exception as error:
            try:
                from services import canvas_tracker as _ct
                _ct.record_account_result(FwcimAmazonSxgitario.current_canvas_strategy(), success=False)
            except Exception:
                pass
            return self.__handleRetry(error, retry)


    #//! -------------------- Linear registration flow -------------------- !\\#
    def __executeFlow(self) -> str:
        phone              = self.phoneData['number']
        phoneShort         = self.phoneData['normalizedNumber']
        user               = self.user
        baseUrl            = self.baseUrl
        defaultCountryCode = core.AMAZON_COUNTRY_CODE_MAP.get(self.targetCountry, self.targetCountry)

        session, userAgent = helpers.buildSession(baseUrl, self.domain, self.proxy, self.targetCountry)
        esc = lambda: self._esc.check() if hasattr(self, '_esc') else None

        #//! Step 0: Warmup — warm the session before signin
        esc()
        flow.warmupSession(session, baseUrl)

        #//! Step 1: Solve AWS WAF challenge and plant the token cookie
        esc()
        flow.solveWafToken(session, baseUrl, self.domain, self.proxy, userAgent)

        #//! Phone and email are genuinely different entry flows on Amazon's
        #//! side (confirmed live 2026-07-23) — NOT just the same flow with
        #//! a different identifier string.
        signinResponse, arbToken, csrfToken = flow.visitSignInPage(session, baseUrl, self.assocHandle)

        esc()
        dynamicUrls, dynamicHashes = helpers.extractScripts(signinResponse.text)
        registerPage, claimUrl, regParams = flow.submitEmailClaim(
            session, signinResponse, arbToken, csrfToken, phone, userAgent,
            baseUrl, self.assocHandle, dynamicUrls, dynamicHashes,
        )

        #//! Step 4: Re-solve WAF token right before register POST — the email
        #//! channel burns the original token across signin/claim/form-load requests.
        flow.solveWafToken(session, baseUrl, self.domain, self.proxy, userAgent)

        #//! Record canvas strategy attempt for tracker stats
        canvasStrategy = FwcimAmazonSxgitario.current_canvas_strategy()
        try:
            from services import canvas_tracker as _ct
            _ct.record_account_attempt(canvasStrategy)
        except Exception:
            pass

        esc()
        try:
            otpResponse = flow.submitRegistrationWithCaptcha(
                session, registerPage, claimUrl, phoneShort, user, userAgent, baseUrl,
                dynamicUrls, dynamicHashes, defaultCountryCode, self.assocHandle,
                leanPayload=True, regParams=regParams,
            )
        except AmazonRegisterError as e:
            if "captcha_appeared" in str(e):
                try:
                    from services import canvas_tracker as _ct
                    _ct.record_captcha(canvasStrategy)
                except Exception:
                    pass
            raise

        if helpers.isAuthenticated(session):
            Log.success("Account authenticated directly — no OTP required!")
            return flow.finalizeAccountCookies(session, registrationDomain=self.domain, targetDomain=self.targetDomain)

        esc()
        otpResponse = flow.switchWhatsappToSms(session, otpResponse, baseUrl)

        #//! OTP wave1 + Amazon resend + wave2 — recovers timeouts without burning the address
        spinner = Log.spinner("Waiting for verification code...").start()
        try:
            WAVE1 = 20
            WAVE2 = 40
            otpCode = self.mailService.getSMS(self.phoneData['activationId'], timeout=WAVE1)

            if not otpCode:
                # Trigger Amazon's resend and wait a second wave
                rs_action, rs_data = flow.findOtpResendForm(otpResponse.text, str(otpResponse.url))
                if rs_action and rs_data:
                    try:
                        rs_resp = helpers.postForm(session, rs_action, rs_data, str(otpResponse.url), baseUrl)
                        if rs_resp and rs_resp.text:
                            otpResponse = rs_resp
                        spinner.stop("OTP resend sent — waiting wave 2...")
                    except Exception:
                        pass
                else:
                    spinner.stop("Resend form not found — waiting wave 2...")
                otpCode = self.mailService.getSMS(self.phoneData['activationId'], timeout=WAVE2)

            if not otpCode:
                raise RuntimeError("Failed to retrieve verification code.")
            spinner.stop(f"Code received: {otpCode}")
        except RuntimeError:
            spinner.fail("Verification code not received")
            raise AmazonRegisterError("email_timeout")

        esc()
        return flow.submitOtpCode(session, otpResponse, otpCode, phoneShort, user, userAgent, baseUrl,
                                  dynamicUrls, dynamicHashes,
                                  registrationDomain=self.domain, targetDomain=self.targetDomain)


    #//! -------------------- Output JSON -------------------- !\\#
    def _saveOutput(self, result: dict) -> None:
        try:
            out_dir = Path("output")
            out_dir.mkdir(exist_ok=True)
            email_slug = result["profile"]["email"].replace("@", "_at_").replace(".", "_")[:50]
            out_path = out_dir / f"account_{email_slug}.json"
            payload = {
                "email":    result["profile"]["email"],
                "password": result["profile"]["password"],
                "name":     result["profile"]["name"],
                "country":  self.targetCountry,
                "billing":  result["billingMessage"],
                "cookies":  result["cookies"],
                "canvas_strategy": result.get("canvas_strategy", ""),
                "time_taken": round(result["time_taken"], 2),
            }
            out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


    #//! -------------------- Error / cancellation handlers -------------------- !\\#
    def __handleCancellation(self) -> dict:
        Log.warn("Interrupted — discarding current identifier...")
        if hasattr(self, '_esc'): self._esc.stop()
        self.phoneData = None
        return {"status": False, "message": "Cancelled by user"}

    #//! Error tags that mean the identifier itself is burned — get a fresh one.
    #//! Everything else is a session/WAF issue that retries on the same address.
    _ID_BURNED_ERRORS = ("email_associated", "email_timeout")

    def __handleRetry(self, error: Exception, retry: int) -> dict:
        errorMessage = str(error)
        generalCap   = 3

        if self.phoneData and any(tag in errorMessage for tag in self._ID_BURNED_ERRORS):
            self.phoneData = None

        if retry >= generalCap:
            if self.verbose and self.clearScreen and not Log._dashboard: os.system('cls' if os.name == 'nt' else 'clear')
            return {
                "status": False, "message": errorMessage,
            }

        if "unusual activity" in errorMessage or "actividad inusual" in errorMessage:
            self.user = helpers.generateFakeProfile(self.targetCountry)
            Log.warn(f"Unusual activity. New identity, same email... ({retry + 1}/{generalCap})")

        elif "email_associated" in errorMessage:
            Log.warn(f"Email already associated. Retrying with new address... ({retry + 1}/{generalCap})")

        elif "email_timeout" in errorMessage:
            Log.warn(f"Email timeout. Retrying with new address... ({retry + 1}/{generalCap})")

        elif "captcha_appeared" in errorMessage:
            Log.warn(f"Captcha appeared — retrying with fresh session... ({retry + 1}/{generalCap})")

        else:
            Log.warn(f"Retrying... ({retry + 1}/{generalCap}) — {errorMessage}")

        time.sleep(1.0)
        return self.processRegistration(retry + 1)

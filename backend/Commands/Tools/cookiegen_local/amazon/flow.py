"""Amazon registration pipeline steps, one function per pipeline stage.

Each public function in this module maps to exactly one step of the
registration flow that :meth:`main.AmazonAccountCreator._AmazonAccountCreator__executeFlow`
drives linearly:

1. :func:`solveWafToken` — AWS WAF ``challenge.js`` → token cookie.
2. :func:`loadRegistrationPage` — GET ``/ap/register`` landing page (phone
   channel), OR :func:`visitSignInPage` — GET ``/ap/signin`` (email/mail.tm
   channel — a genuinely different entry point, not interchangeable).
3. :func:`submitPhoneClaim` (phone) / :func:`submitEmailClaim` (email) —
   POST ``/ax/claim`` + load register form.
4. :func:`submitRegistrationWithCaptcha` — POST ``/ap/register``; raises
   ``captcha_appeared`` immediately if Amazon serves a captcha challenge.
5. :func:`switchWhatsappToSms` — flip the OTP channel when Amazon defaults
   to WhatsApp.
6. :func:`submitOtpCode` — POST OTP + serialize final cookie string.

Every function raises :class:`AmazonRegisterError` on recoverable failures
so the orchestrator's retry loop can pick a fresh phone and start over.

Author: Vxsilisk @ Sxgitario API Gateways Service
        DEV  https://t.me/Vxsilisk
        SHOP https://t.me/Sxgitario
"""

import re
import time
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from services import Log
from . import helpers
from .awsBypassSxgitario import AwsWaf
from .core import AmazonRegisterError


#//! ------------------------------------- Step 0 — Warmup ------------------------------------- !\\#
def warmupSession(session, baseUrl: str) -> bool:
    """GET the marketplace home page to warm up the session before signin.

    Soft step — never raises. Returns True if the server responded with 2xx/3xx.
    """
    try:
        r = session.get(f'{baseUrl}/', headers={
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }, timeout=10)
        ok = bool(r and r.status_code and r.status_code < 400)
        Log.success("Warmup OK" if ok else f"Warmup soft ({r.status_code if r else '?'})")
        return ok
    except Exception:
        return False


def findOtpResendForm(html: str, pageUrl: str) -> tuple:
    """Parse the Amazon 'Resend code' form from the OTP page.

    Returns (action_url, form_data_dict) or (None, {}) if not found.
    """
    soup = BeautifulSoup(html, 'html.parser')
    form = None
    for f in soup.find_all('form'):
        cls = ' '.join(f.get('class') or [])
        act_inp = f.find('input', {'name': 'action', 'value': 'resend'})
        if act_inp or 'cvf-widget-form-resend' in cls:
            fid = (f.get('id') or '')
            if fid == 'wait-resend-auto-read':
                continue
            form = f
            if 'cvf-widget-form-resend' in cls:
                break
    if not form:
        return None, {}
    action = form.get('action', '') or ''
    if action and not action.startswith('http'):
        action = urljoin(pageUrl, action)
    if not action:
        action = urljoin(pageUrl, 'verify')
    inputs: dict = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        if name:
            inputs[name] = inp.get('value', '') or ''
    inputs['action'] = 'resend'
    inputs.setdefault('resendContactType', 'email')
    return action, inputs


#//! ------------------------------------- Step 1 ------------------------------------- !\\#
def solveWafToken(session, baseUrl: str, domain: str, proxy: str, userAgent: str) -> bool:
    """Solve the AWS WAF ``challenge.js`` and plant the resulting token cookie.

    The WAF cookie is scoped to the registrable domain we're actually
    hitting — Amazon validates the domain when consuming the token, so
    the cookie must be set on ``.amazon.com`` for US, ``.amazon.it`` for
    IT, etc.

    Args:
        session: curl_cffi session the token cookie should be planted on.
        baseUrl: Full marketplace base URL (``https://www.amazon.com``).
        domain: Registrable domain for cookie scope (``amazon.com``).
        proxy: Optional proxy string; forwarded to the solver so the WAF
            token is generated from the same IP that will use it.
        userAgent: UA that the solver will announce.

    Returns:
        ``True`` on success. ``False`` when the challenge solver errored
        out (the flow continues; Amazon may challenge again later).
    """
    spinner = Log.spinner("Solving WAF challenge...").start()
    try:
        wafResult = AwsWaf(
            websiteURL=f'{baseUrl}/',
            proxy=helpers.normalizeProxy(proxy),
            userAgent=userAgent,
        ).solve()
        if wafResult['status']:
            session.cookies.set('aws-waf-token', wafResult['token'], domain=f'.{domain}', path='/')
            spinner.stop(f"WAF token obtained ({len(wafResult['token'])} chars)")
            return True
        spinner.fail(f"WAF: {wafResult['description']}")
        return False
    except Exception as error:
        spinner.fail(f"WAF: {error}")
        return False


#//! ------------------------------------- Step 2 ------------------------------------- !\\#
def loadRegistrationPage(session, registerUrl: str):
    """Fetch the register landing page and extract dynamic scripts.

    Args:
        session: Session with the WAF token already planted.
        registerUrl: Country-specific ``/ap/register`` URL from
            :data:`core.MANAGE_URLS`.

    Returns:
        Tuple ``(landingResponse, landingHtml, dynamicUrls, dynamicHashes)``:

        * ``landingResponse`` — the HTTP response object,
        * ``landingHtml`` — BeautifulSoup parse of the body,
        * ``dynamicUrls`` — list of JS ``src`` URLs for FWCIM,
        * ``dynamicHashes`` — list of inline-script 32-bit hashes.
    """
    spinner = Log.spinner("Loading registration page...").start()
    landingResponse = session.get(registerUrl, timeout=60)
    spinner.stop(f"Page loaded → {str(landingResponse.url)[:70]}")
    landingHtml = BeautifulSoup(landingResponse.text, 'html.parser')
    dynamicUrls, dynamicHashes = helpers.extractScripts(landingResponse.text)
    return landingResponse, landingHtml, dynamicUrls, dynamicHashes


#//! ------------------------------------- Step 3 ------------------------------------- !\\#
def submitPhoneClaim(session, landingResponse, landingHtml, phone: str, phoneShort: str,
                     defaultCountryCode: str, userAgent: str, baseUrl: str,
                     dynamicUrls: list, dynamicHashes: list):
    """Claim the phone number and load the registration form.

    Posts to ``/ax/claim`` with a fresh ``metadata1``, then uses the
    returned intent-confirmation token (``arb``) to load the
    ``/ap/register`` form. If the landing page is already the register
    form (Amazon sometimes skips the claim step), returns it directly.

    Args:
        session: Session with the WAF cookie.
        landingResponse: Response from :func:`loadRegistrationPage`.
        landingHtml: Parsed HTML of the landing page.
        phone: Full E.164 number without ``+``.
        phoneShort: National number (no calling code).
        defaultCountryCode: 2-letter Amazon country code to send if the
            form is missing one.
        userAgent: UA for the FWCIM metadata1.
        baseUrl: Marketplace base URL.
        dynamicUrls, dynamicHashes: Script lists from the landing page.

    Returns:
        Tuple ``(registerPage, claimUrl)`` — the response landing on the
        register form, and the URL of the claim step (for ``Referer``
        chaining).

    Raises:
        AmazonRegisterError: ``number_associated`` if the phone already
            exists, ``no_arb`` if the claim returned no intent token.

    Note:
        Phone-only. The mail.tm/email channel uses :func:`visitSignInPage`
        + :func:`submitEmailClaim` instead — NOT this function generalized
        to accept an email. That generalization was tried and confirmed
        live (2026-07-23) to produce a "phantom" account: the session gets
        authenticated (`at-main` cookie set, cookies extractable) but the
        account is never actually indexed by Amazon's normal `/ap/signin`
        lookup — real accounts require the `/ap/signin`-first entry with a
        leaner register-submit payload (see :func:`submitEmailClaim` and
        ``helpers.submitRegister``'s ``leanPayload`` flag).
    """
    if '/ax/claim' not in str(landingResponse.url) and helpers.getHiddenField(landingHtml, 'appActionToken'):
        return landingResponse, landingResponse.url

    identifierValue = f"+{phone}" if not phone.startswith('+') else phone

    #//! Claim phone number
    spinner = Log.spinner("Submitting phone number...").start()
    landingForm = landingHtml.find('form')
    claimAction = landingForm.get('action', '') if landingForm else ''
    if claimAction and not claimAction.startswith('http'):
        claimAction = f'{baseUrl}{claimAction}'

    # Claim POST payload — verified against Firefox HAR (MX, 11 fields).
    # Must include `countryCode` and empty `password` — Amazon's server-side
    # validation treats their absence as a malformed claim on some marketplaces
    # (flags the session as suspicious, then silently blocks OTP SMS later).
    #
    # metadata1: real browser sends a real XXTEA-encrypted fingerprint built
    # from the claim-form DOM. Our old code hard-coded the literal string
    # "true" which MX accepts but stricter markets correlate with anti-fraud
    # scoring, so we generate a real one here instead.
    claimMetadata = helpers.generateMetadata(
        str(landingResponse.url), "",
        dynamicUrls, dynamicHashes, userAgent,
        email=identifierValue,
        name="", password="",
        postCaptcha=False,
    )
    claimPayload = {
        'appAction': 'SIGNIN_CLAIM_COLLECT',
        'subPageType': 'FullPageUnifiedClaimCollect',
        'claimCollectionWorkflow': 'unified',
        'metadata1': claimMetadata,
        'claimType': 'phoneNumber',
        'countryCode': defaultCountryCode,
        'isServerSideRouting': 'true',
        'signalUnknownCredentialUnifiedAuthWeblabActive': 'false',
        'anti-csrftoken-a2z': helpers.getHiddenField(landingHtml, 'anti-csrftoken-a2z'),
        'email': identifierValue,
        'password': '',
    }

    claimResponse = helpers.postForm(session, claimAction or f'{baseUrl}/ax/claim',
                                     claimPayload, landingResponse.url, baseUrl)
    claimHtml = BeautifulSoup(claimResponse.text, 'html.parser')
    claimArb = helpers.getHiddenField(claimHtml, 'arb')

    registerFormTag = None
    for formTag in claimHtml.find_all('form'):
        if '/ap/register' in formTag.get('action', ''):
            registerFormTag = formTag
            break

    if claimArb:
        spinner.stop("Claimed successfully (new identifier)")
        claimedEmail   = helpers.getHiddenField(claimHtml, 'email') or phoneShort
        claimedCountry = helpers.getHiddenField(claimHtml, 'countryCode') or defaultCountryCode
    elif registerFormTag:
        spinner.stop("Identifier may exist, using register link", symbol="▲", color=Log._c.YELLOW)
        emailInput   = registerFormTag.find('input', {'name': 'email'})
        countryInput = registerFormTag.find('input', {'name': 'countryCode'})
        claimedEmail   = emailInput.get('value', phoneShort) if emailInput else phoneShort
        claimedCountry = countryInput.get('value', defaultCountryCode) if countryInput else defaultCountryCode
    elif 'SIGNIN_PWD_COLLECT' in claimResponse.text or 'SIGNIN_OTP_COLLECT' in claimResponse.text:
        spinner.fail("Identifier already associated with an account")
        raise AmazonRegisterError("number_associated")
    else:
        # Claim came back without arb / register form / OTP prompt. Common
        # causes: WAF token burned early, "Something went wrong" interstitial,
        # unexpected locale redirect, or a captcha served directly on /ax/claim.
        claimUrlShort = str(claimResponse.url)[:100]
        if helpers.isCaptcha(claimResponse.text):
            spinner.fail(f"Captcha served on claim step ({claimUrlShort})")
        elif helpers.isUnusual(claimResponse.text):
            spinner.fail(f"Unusual activity on claim step ({claimUrlShort})")
        else:
            spinner.fail(f"No intent confirmation received ({claimUrlShort})")
        raise AmazonRegisterError("no_arb")

    #//! Load registration form
    spinner = Log.spinner("Loading registration form...").start()
    targetForm    = registerFormTag or claimHtml.find('form')
    registerAction = targetForm.get('action', '') if targetForm else ''
    if registerAction and not registerAction.startswith('http'):
        registerAction = f'{baseUrl}{registerAction}'

    # `unifiedAuthTreatment` confirmed empty (not 'T2') on the real
    # register-load POST via HAR capture (2026-07-21); the CSRF field on
    # this particular page is only ever `anti-csrftoken-a2z` when that
    # hidden input actually exists — some claim responses (e.g. the
    # /ax/claim/intent confirmation page) name it `csrf-token` instead,
    # which the generic hidden-field forwarding loop below picks up on
    # its own since it isn't already a key in this dict.
    registerData = {
        'claimCollectionLayoutType': 'unifiedAuthClaimCollection',
        'unifiedAuthTreatment':      helpers.getHiddenField(claimHtml, 'unifiedAuthTreatment') or '',
        'countryCode':               claimedCountry, 'email': claimedEmail,
    }
    csrfTokenValue = helpers.getHiddenField(claimHtml, 'anti-csrftoken-a2z')
    if csrfTokenValue:
        registerData['anti-csrftoken-a2z'] = csrfTokenValue
    if claimArb:
        registerData['arb'] = claimArb
    for hiddenInput in targetForm.find_all('input', {'type': 'hidden'}):
        fieldName = hiddenInput.get('name')
        if fieldName and fieldName not in registerData:
            registerData[fieldName] = hiddenInput.get('value', '')

    registerPage = helpers.postForm(session, registerAction or f'{baseUrl}/ap/register',
                                    registerData, claimResponse.url, baseUrl)
    spinner.stop("Registration form loaded")
    return registerPage, claimResponse.url


#//! -------------------------------- Step 3b (email/mail.tm channel) -------------------------------- !\\#
def visitSignInPage(session, baseUrl: str, assocHandle: str):
    """Load ``/ap/signin`` — the real entry point for the email/mail.tm
    channel.

    The phone channel lands directly on ``/ap/register`` (see
    :func:`loadRegistrationPage`); the email channel needs THIS entry
    instead. Confirmed live (2026-07-23): generalizing the phone-flow's
    direct-``/ap/register``-landing to accept an email produced a session
    that LOOKS authenticated (``at-main`` cookie set, cookies extractable)
    but was never actually indexed by Amazon — a manual `/ap/signin`
    afterward said "looks like you're new to Amazon" for that same email.
    Routing email identities through THIS entry point instead produced a
    real, normally-loggable-into account in the same test.

    Args:
        session: Session with the WAF token already planted.
        baseUrl: Marketplace base URL (``https://www.amazon.com``).
        assocHandle: OpenID handle (``'usflex'``, ``'caflex'``, etc.).

    Returns:
        Tuple ``(signinResponse, arbToken, csrfToken)``.
    """
    spinner = Log.spinner("Loading sign-in page...").start()
    signinParams = {
        'openid.return_to': f'{baseUrl}/?ref_=nav_ya_signin',
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.assoc_handle': assocHandle,
        'openid.mode': 'checkid_setup',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.ns': 'http://specs.openid.net/auth/2.0',
    }
    signinResponse = session.get(f'{baseUrl}/ap/signin', params=signinParams, headers={
        'Referer': f'{baseUrl}/',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }, timeout=60)
    signinHtml = BeautifulSoup(signinResponse.text, 'html.parser')
    arbToken  = helpers.getHiddenField(signinHtml, 'arb')
    if not arbToken:
        arbMatch = re.search(r'arb=([a-zA-Z0-9_-]+)', signinResponse.text)
        arbToken = arbMatch.group(1) if arbMatch else None
    csrfToken = helpers.getHiddenField(signinHtml, 'anti-csrftoken-a2z')
    spinner.stop(f"Sign-in page loaded → {str(signinResponse.url)[:70]}")
    return signinResponse, arbToken, csrfToken


def submitEmailClaim(session, signinResponse, arbToken: str, csrfToken: str, emailAddress: str,
                     userAgent: str, baseUrl: str, assocHandle: str,
                     dynamicUrls: list, dynamicHashes: list):
    """Claim the email address and load the registration form.

    Mirrors the real-browser (and reference-tool "genv2") flow for the
    email channel: claim against the ``/ap/signin``-sourced ``arb``, then
    load ``/ap/register`` with a LEANER payload than the phone channel's
    :func:`submitPhoneClaim` uses — no ``countryCode`` at this stage,
    since the real flow never sends one here either.

    Args:
        session: Session with the WAF cookie.
        signinResponse: Response from :func:`visitSignInPage`.
        arbToken, csrfToken: Extracted from the sign-in page.
        emailAddress: The mail.tm address being claimed.
        userAgent: UA for the FWCIM metadata1.
        baseUrl: Marketplace base URL.
        assocHandle: OpenID handle (``'usflex'``, ``'caflex'``, etc.).
        dynamicUrls, dynamicHashes: Script lists from the sign-in page.

    Returns:
        Tuple ``(registerPage, claimUrl, regParams)`` — the response
        landing on the register form, the claim URL (for ``Referer``
        chaining), and the OpenID query params to reuse on the actual
        register submit (Amazon expects the SAME ``reg_params`` on both
        the form-load POST and the final REGISTER POST).

    Raises:
        AmazonRegisterError: ``number_associated`` if the email already
            exists, ``no_arb`` if the claim returned no intent token.
    """
    spinner = Log.spinner("Submitting email address...").start()

    claimMetadata = helpers.generateMetadata(
        str(signinResponse.url), "", dynamicUrls, dynamicHashes, userAgent,
        email=emailAddress, name="", password="", postCaptcha=False,
    )
    claimParams = {
        'openid.assoc_handle': assocHandle, 'openid.mode': 'checkid_setup',
        'policy_handle': 'Retail-Checkout', 'openid.return_to': f'{baseUrl}/?ref_=nav_ya_signin',
        'openid.ns': 'http://specs.openid.net/auth/2.0', 'arb': arbToken,
    }
    claimPayload = {
        'appAction': 'SIGNIN_CLAIM_COLLECT', 'subPageType': 'FullPageUnifiedClaimCollect',
        'claimCollectionWorkflow': 'unified', 'metadata1': claimMetadata,
        'claimType': '', 'countryCode': '', 'isServerSideRouting': 'true',
        'openid.ns': 'http://specs.openid.net/auth/2.0', 'openid.mode': 'checkid_setup',
        'openid.return_to': f'{baseUrl}/?ref_=nav_ya_signin', 'openid.assoc_handle': assocHandle,
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
        'signalUnknownCredentialUnifiedAuthWeblabActive': 'false',
        'anti-csrftoken-a2z': csrfToken, 'ue_back': '1', 'email': emailAddress, 'password': '',
    }
    claimResponse = helpers.postForm(session, f'{baseUrl}/ax/claim', claimPayload,
                                     str(signinResponse.url), baseUrl, params=claimParams)
    claimHtml = BeautifulSoup(claimResponse.text, 'html.parser')
    claimArb = helpers.getHiddenField(claimHtml, 'arb')
    if not claimArb:
        arbMatch = re.search(r'arb=([a-zA-Z0-9_-]+)', claimResponse.text)
        claimArb = arbMatch.group(1) if arbMatch else None
    csrfToken2 = helpers.getHiddenField(claimHtml, 'anti-csrftoken-a2z')

    if not claimArb:
        if 'SIGNIN_PWD_COLLECT' in claimResponse.text or 'SIGNIN_OTP_COLLECT' in claimResponse.text:
            spinner.fail("Email already associated with an account")
            raise AmazonRegisterError("number_associated")
        claimUrlShort = str(claimResponse.url)[:100]
        if helpers.isCaptcha(claimResponse.text):
            spinner.fail(f"Captcha served on claim step ({claimUrlShort})")
        elif helpers.isUnusual(claimResponse.text):
            spinner.fail(f"Unusual activity on claim step ({claimUrlShort})")
        else:
            spinner.fail(f"No intent confirmation received ({claimUrlShort})")
        raise AmazonRegisterError("no_arb")
    spinner.stop("Claimed successfully (new identifier)")

    #//! Load registration form — reg_params reused on the final REGISTER
    #//! submit too (see submitRegistrationWithCaptcha's leanPayload path).
    spinner = Log.spinner("Loading registration form...").start()
    formTag = claimHtml.find('form')
    createActionRaw = (formTag.get('action', '') if formTag else '').replace('&amp;', '&')
    returnToMatch = re.search(r'openid\.return_to=([^&"\']+)', unquote(createActionRaw))
    newReturnTo   = unquote(returnToMatch.group(1)) if returnToMatch else f'{baseUrl}/'

    regParams = {
        'openid.mode': 'checkid_setup', 'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.ns.pape': 'http://specs.openid.net/extensions/pape/1.0', 'showRememberMe': 'true',
        'openid.pape.max_auth_age': '900', 'pageId': assocHandle, 'prepopulatedLoginId': '',
        'openid.assoc_handle': assocHandle, 'openid.return_to': newReturnTo,
        'policy_handle': 'Retail-Checkout',
    }
    registerPage = helpers.postForm(session, f'{baseUrl}/ap/register', {
        'claimCollectionLayoutType': 'unifiedAuthClaimCollection', 'unifiedAuthTreatment': '',
        'email': emailAddress, 'arb': claimArb, 'csrf-token': csrfToken2,
    }, str(claimResponse.url), baseUrl, params=regParams)
    spinner.stop("Registration form loaded")
    return registerPage, claimResponse.url, regParams


#//! ------------------------------------- Step 4 ------------------------------------- !\\#
def submitRegistrationWithCaptcha(session, registerPage, claimUrl: str, phoneShort: str, user,
                                  userAgent: str, baseUrl: str, dynamicUrls: list,
                                  dynamicHashes: list, defaultCountryCode: str,
                                  assocHandle: str,
                                  leanPayload: bool = False, regParams: dict = None):
    """Submit the register form. Raises ``captcha_appeared`` immediately if Amazon
    serves a captcha challenge — the orchestrator retries with a fresh session.
    """
    registerHtml = BeautifulSoup(registerPage.text, 'html.parser')
    if not helpers.getHiddenField(registerHtml, 'appActionToken'):
        raise AmazonRegisterError("no_register_form")

    spinner = Log.spinner("Submitting registration form...").start()
    registerResponse = helpers.submitRegister(
        session, registerPage, claimUrl, phoneShort, user, userAgent,
        baseUrl, dynamicUrls, dynamicHashes, defaultCountryCode, "first",
        leanPayload=leanPayload, regParams=regParams,
    )

    # mobileclaimconflict = this number already has an account. Try the
    # "confirm and continue" action Amazon offers on that page before
    # giving up the number — see the matching handling in the captcha
    # loop below for the full rationale (HAR-confirmed 2026-07-21).
    if 'mobileclaimconflict' in str(registerResponse.url):
        spinner.stop("Number already has an account — confirming continue anyway...", symbol="▲", color=Log._c.YELLOW)
        continued = _continueMobileClaimConflict(session, registerResponse, baseUrl)
        if continued is None:
            spinner.fail("Phone number has a marketplace conflict")
            raise AmazonRegisterError("number_associated")
        registerResponse = continued
        spinner = Log.spinner("Submitting registration form...").start()

    # Some sessions get authenticated straight off the FIRST register
    # submit — no captcha, no OTP at all (confirmed live, 2026-07-21,
    # mail.tm channel: the response landed on the plain homepage with
    # `at-main` already set). Check before the text/URL classifiers,
    # which would otherwise misclassify the redirect as unrecognized.
    if helpers.isAuthenticated(session):
        spinner.stop("Registration accepted — account authenticated directly, no OTP needed!")
        return registerResponse
    if helpers.isUnusual(registerResponse.text):
        spinner.fail("Unusual activity detected")
        raise AmazonRegisterError("unusual activity")
    if helpers.isOtp(registerResponse.text):
        spinner.stop("Registration accepted — OTP page reached!")
        return registerResponse
    # Amazon can immediately reject the register POST with the form
    # re-rendered and an inline "There's already an account with this
    # email"-style alert — no captcha, no OTP, just a hard bounce. This
    # is a genuine identifier conflict, not an unclassified page; without
    # this check it fell through to `unexpected_response` and masked the
    # real cause (confirmed via HAR: 2026-07-21 mail.tm live test).
    if helpers.isRegForm(registerResponse.text) and _hasAlreadyAssociatedAlert(registerResponse.text):
        spinner.fail("Identifier already associated with an account")
        raise AmazonRegisterError("email_associated")
    if helpers.isCaptcha(registerResponse.text):
        captchaType = helpers.detectCaptchaType(registerResponse.text)
        spinner.stop(f"Captcha detected: {captchaType}", symbol="▲", color=Log._c.YELLOW)
        _dumpDebugHtml(registerResponse.text, f"captcha_{captchaType}")
        raise AmazonRegisterError("captcha_appeared")
    # Amazon redirects the register POST to /ap/cvf/request when it wants a
    # challenge (OTP or CAPTCHA). If that CVF page returns 404, the session is
    # bot-blocked at the WAF level — the comment in the body says "automated
    # access" explicitly. Treat as captcha_appeared so the orchestrator retries
    # with a completely fresh session+WAF token instead of burning more retries
    # on the same blocked IP/fingerprint.
    if registerResponse.status_code == 404 and '/ap/cvf/request' in str(registerResponse.url):
        spinner.fail(f"Bot-blocked on CVF request (404) — forcing fresh session")
        _dumpDebugHtml(registerResponse.text, "cvf_bot_blocked")
        raise AmazonRegisterError("captcha_appeared")
    if not helpers.isOtp(registerResponse.text):
        spinner.fail(f"Unexpected response ({str(registerResponse.url)[:100]})")
        _dumpDebugHtml(registerResponse.text, "unexpected_response")
        raise AmazonRegisterError("unexpected_response")


def _resubmitAndClassify(session, page, referer, phoneShort, user, userAgent,
                         baseUrl, dynamicUrls, dynamicHashes, defaultCountryCode, debugLabel,
                         postCaptcha=False, leanPayload=False, regParams=None):
    """Helper: re-submit register form and return the response."""
    return helpers.submitRegister(
        session, page, referer, phoneShort, user, userAgent,
        baseUrl, dynamicUrls, dynamicHashes, defaultCountryCode, debugLabel,
        postCaptcha=postCaptcha, leanPayload=leanPayload, regParams=regParams,
    )


# Multi-locale "this identifier already has an account" register-form
# alert. Amazon shows this as an inline error on the re-rendered register
# form rather than redirecting anywhere distinctive, so it has to be
# matched on text.
_ALREADY_ASSOCIATED_KEYWORDS = (
    "there's already an account with this email", "already an account with this",
    'ya existe una cuenta con este correo', 'ya existe una cuenta con esta dirección',
    'il existe déjà un compte avec cet e-mail', 'es gibt bereits ein konto mit dieser e-mail',
    'esiste già un account con questa email',
)


def _hasAlreadyAssociatedAlert(pageText: str) -> bool:
    lowered = pageText.lower()
    return any(keyword in lowered for keyword in _ALREADY_ASSOCIATED_KEYWORDS)


def _dumpDebugHtml(htmlText: str, label: str):
    """Save an HTML snippet to samples/ for offline diagnosis."""
    import time as _time
    from pathlib import Path
    outDir = Path('samples')
    outDir.mkdir(exist_ok=True)
    path = outDir / f"debug_{label}_{int(_time.time())}.html"
    path.write_text(htmlText[:300000])
    Log.debug(f"saved debug HTML: {path}")


def _continueMobileClaimConflict(session, mobileClaimResponse, baseUrl: str):
    """Confirm-and-continue past a "number already has an account" page.

    The mobileclaimconflict page has a form (`appAction=
    MOBILE_PHONE_REGISTRATION_CONFLICT_WARNED_VERIFY`,
    `confirmDeactivateCheckBox=true`, plus a `mobileNumberReclaimJWTToken`
    and the usual workflowState/appActionToken/prevRID trio) whose action
    deactivates the OLD account tied to the number and proceeds with a
    genuinely new registration on the SAME number — field shape and
    outcome confirmed via a real-browser HAR capture (2026-07-21): it
    leads back into the CVF/OTP flow and completes with `new_account=1`
    in the final redirect, rather than requiring a whole new number.

    Returns the response from submitting that form, or ``None`` if the
    page doesn't have the expected form (caller should fall back to
    treating this as a hard `number_associated`).
    """
    mcHtml = BeautifulSoup(mobileClaimResponse.text, 'html.parser')
    formTag = mcHtml.find('form')
    if not formTag:
        return None
    action = formTag.get('action', '')
    if not action:
        return None
    if not action.startswith('http'):
        action = urljoin(str(mobileClaimResponse.url), action)
    payload = {inp.get('name'): inp.get('value', '') for inp in formTag.find_all('input') if inp.get('name')}
    if payload.get('appAction') != 'MOBILE_PHONE_REGISTRATION_CONFLICT_WARNED_VERIFY':
        return None
    return helpers.postForm(session, action, payload, str(mobileClaimResponse.url), baseUrl)




#//! ------------------------------------- Step 5 ------------------------------------- !\\#

# Multi-locale markers for the WhatsApp OTP channel. When any of these appear
# in the page body we assume Amazon defaulted the verification to WhatsApp
# and we MUST switch to SMS before polling HeroSMS — otherwise the code
# is delivered to a WhatsApp number that we don't own and `getSMS` times
# out after 75s.
_WHATSAPP_MARKERS = (
    'whatsapp', 'wa.me', 'sent a code via whatsapp',
    'código por whatsapp', 'enviamos un código a whatsapp',
    'code via whatsapp', 'code par whatsapp', 'whatsapp-nachricht',
    'codice via whatsapp', 'код whatsapp',
)
# Markers that tell us we're already on the SMS OTP screen.
_SMS_MARKERS = (
    'text message', 'sms', 'mensaje de texto', 'sms-code',
    'code par sms', 'sms-nachricht', 'messaggio di testo',
    'mensagem de texto',
)
# Form input/value patterns Amazon has used historically to carry the
# channel switch. Each entry pairs (inputName → desiredValue).
_SMS_SWITCH_PATTERNS = [
    # Modern CVF switch (2024-2026)
    ('newContactType',        'SMS_OTP'),
    ('newContactType',        'sms'),
    # Legacy CVF switch
    ('requestedContactType',  'sms'),
    # Alternate naming observed in community writeups
    ('otpChannel',            'SMS'),
    ('otpChannel',            'sms'),
    ('deliveryMechanism',     'sms'),
    ('codeDeliveryType',      'SMS'),
    ('verificationMechanism', 'sms'),
    ('channel',               'sms'),
    ('contactType',           'sms'),
]


def _detectChannel(pageText: str) -> str:
    """Classify the OTP page as 'whatsapp', 'sms', or 'unknown'.

    Two hidden-input fields encode the active channel in different page types:
    - `verificationPageContactType`: present on real OTP pages (code input visible).
    - `requestedContactType`: present on /ap/cvf/request channel-selector pages
      where Amazon proposes a specific channel (whatsapp when SMS blocked).

    `requestedContactType` is checked FIRST because on cvf/request pages both
    fields can coexist with conflicting values (verificationPageContactType=sms
    but requestedContactType=whatsapp means "session was SMS but we now want WA").
    """
    # Priority 1 — CVF block page (hideSendOtpOverSms=true):
    # requestedContactType tells us what Amazon is proposing when SMS is
    # explicitly disabled for this number. Only consult requestedContactType
    # in this specific case; on normal OTP pages it just reflects a secondary
    # "also try via WhatsApp / SMS" button and is NOT the active channel.
    hasSmsHidden = bool(re.search(
        r'''name=["']hideSendOtpOverSms["']\s+value=["']true["']''', pageText
    ))
    if hasSmsHidden:
        reqMatch = re.search(
            r'''name=["']requestedContactType["']\s+value=["']([^"']+)["']''',
            pageText,
        )
        if reqMatch:
            val = reqMatch.group(1).strip().lower()
            if val == 'whatsapp':          return 'whatsapp'
            if val in ('sms', 'sms_otp'): return 'sms'

    # Priority 2 — standard OTP page: verificationPageContactType is the
    # ACTIVE delivery channel. This is the source of truth on multi-form pages
    # where both SMS and WhatsApp forms coexist (e.g. IT OTP page with 5 forms).
    match = re.search(
        r'''name=["\']verificationPageContactType["\']\s+value=["\']([^"\']+)["\']''',
        pageText,
    )
    if match:
        value = match.group(1).strip().lower()
        if value in ('sms', 'sms_otp'): return 'sms'
        if value == 'whatsapp':          return 'whatsapp'

    lowered = pageText.lower()
    hasWa  = any(marker in lowered for marker in _WHATSAPP_MARKERS)
    hasSms = any(marker in lowered for marker in _SMS_MARKERS)
    if hasWa and not hasSms: return 'whatsapp'
    if hasSms and not hasWa: return 'sms'
    if hasWa and hasSms:     return 'whatsapp'
    return 'unknown'


def _findSmsSwitchForm(html):
    """Return the form that flips the channel to SMS, or None.

    Tries every known (name, value) pattern in priority order. Each form
    on the page is scanned for a hidden input matching the pattern.
    """
    for fieldName, desiredValue in _SMS_SWITCH_PATTERNS:
        for formTag in html.find_all('form'):
            inp = formTag.find('input', {'name': fieldName})
            if not inp: continue
            val = (inp.get('value') or '').strip()
            if val.lower() == desiredValue.lower():
                return formTag, fieldName, val
    return None, None, None


def _findSmsSwitchLink(html):
    """Fallback: a bare <a href="..."> with SMS switching params in the URL."""
    for anchor in html.find_all('a', href=True):
        href = anchor['href']
        hrefLower = href.lower()
        if ('switchdefaultcvfotpchannel' in hrefLower
            or 'switch_contact_type' in hrefLower
            or ('deliverytype=sms' in hrefLower)
            or ('newcontacttype=sms' in hrefLower)):
            return anchor, href
    return None, None


def switchWhatsappToSms(session, otpResponse, baseUrl: str):
    """Flip the OTP channel to SMS when Amazon defaulted to WhatsApp.

    Three mechanisms are tried in order: form POST with a
    channel-switch hidden field (10 known ``name``/``value`` patterns),
    a bare ``<a href>`` with switching query params, and direct GETs to
    Amazon's documented ``switchDefaultCvfOtpChannel`` action URLs. On
    explicit CVF block pages (``hideSendOtpOverSms=true``) the force-SMS
    override is attempted once; if Amazon still delivers via WhatsApp,
    :class:`AmazonRegisterError` with ``sms_blocked`` is raised
    immediately so the retry loop can pick a fresh number.

    Args:
        session: curl_cffi session.
        otpResponse: Response returned by :func:`submitRegistrationWithCaptcha`.
        baseUrl: Marketplace base URL.

    Returns:
        Response to treat as the SMS OTP page — either a successfully
        switched page or the original response if it was already SMS.

    Raises:
        AmazonRegisterError: ``sms_blocked`` when Amazon refuses to
            switch away from WhatsApp.
    """
    otpHtml = BeautifulSoup(otpResponse.text, 'html.parser')
    channel = _detectChannel(otpResponse.text)

    #//! Fast path: already on SMS screen → nothing to do.
    if channel == 'sms':
        Log.detail("OTP channel", "SMS (no switch needed)")
        return otpResponse

    #//! CVF request page: requestedContactType=whatsapp → force SMS.
    # /ap/cvf/request pages have a single form that re-sends an OTP.
    # Amazon pre-fills requestedContactType=whatsapp when SMS is blocked
    # for the number. We try to override it; if it fails we raise
    # sms_blocked immediately so the caller retries with a fresh number
    # instead of wasting 75s waiting for an SMS that will never arrive.
    if channel == 'whatsapp':
        for formTag in otpHtml.find_all('form'):
            reqInput = formTag.find('input', {'name': 'requestedContactType'})
            if reqInput and reqInput.get('value', '').lower() == 'whatsapp':
                spinner = Log.spinner("Forcing SMS on CVF channel-request page...").start()
                forcedPayload = {
                    inp.get('name'): inp.get('value', '')
                    for inp in formTag.find_all('input') if inp.get('name')
                }
                forcedPayload['requestedContactType'] = 'sms'
                # Only strip `hideSendOtpOverSms` — it is the actual server-side
                # signal that tells Amazon "SMS delivery is blocked for this
                # number", so keeping it=true makes Amazon ignore our override.
                # Other fields (`shouldShowOtpOverWhatsapp`, `whatsAppOptionClickOnBlockCX`,
                # `hideSuccessAlertForBlockedCx`) are page-render flags the real
                # browser keeps in the POST (confirmed via HAR capture, MX flow).
                # Removing them was too aggressive and could make Amazon reject
                # the request as malformed.
                forcedPayload.pop('hideSendOtpOverSms', None)
                forcedAction = formTag.get('action', '')
                if forcedAction and not forcedAction.startswith('http'):
                    forcedAction = urljoin(str(otpResponse.url), forcedAction)
                if not forcedAction:
                    forcedAction = f'{baseUrl}/ap/cvf/verify'
                try:
                    forcedResp  = helpers.postForm(session, forcedAction, forcedPayload,
                                                   str(otpResponse.url), baseUrl)
                    forcedHtml  = BeautifulSoup(forcedResp.text, 'html.parser')
                    hasCode     = bool(forcedHtml.find('input', {'name': 'code'}))
                    newChannel  = _detectChannel(forcedResp.text)
                    # Only return as SMS page when the response is NOT WhatsApp.
                    # If Amazon sent via WhatsApp despite the override (hasCode=True
                    # but newChannel='whatsapp'), fall through to sms_blocked so the
                    # retry gets a fresh number instead of wasting 75s on a dead poll.
                    if (hasCode or newChannel == 'sms') and newChannel != 'whatsapp':
                        spinner.stop("Forced SMS channel via CVF request page")
                        return forcedResp
                    if newChannel == 'whatsapp':
                        spinner.fail("Force SMS rejected — Amazon sent via WhatsApp (number blocked for SMS)")
                    else:
                        spinner.fail(f"Force SMS failed on CVF request (channel={newChannel}, hasCode={hasCode})")
                except Exception as error:
                    spinner.fail(f"CVF force SMS error: {error}")
                # Amazon explicitly blocked SMS for this number — bail out
                # immediately instead of burning 75s on a dead activation.
                raise AmazonRegisterError("sms_blocked")
                break

    #//! Try form-based switch (most common).
    switchForm, fieldName, fieldValue = _findSmsSwitchForm(otpHtml)
    if switchForm is not None:
        spinner = Log.spinner(f"Switching to SMS via {fieldName}={fieldValue}...").start()
        payload = {}
        for inp in switchForm.find_all('input'):
            n = inp.get('name')
            if n:
                payload[n] = inp.get('value', '')

        action = switchForm.get('action', '')
        if action and not action.startswith('http'):
            action = urljoin(str(otpResponse.url), action)
        if not action:
            action = f'{baseUrl}/ap/cvf/verify'

        switchResponse = helpers.postForm(session, action, payload,
                                          str(otpResponse.url), baseUrl)
        newChannel = _detectChannel(switchResponse.text)
        switchHtml = BeautifulSoup(switchResponse.text, 'html.parser')
        hasCodeInput = bool(switchHtml.find('input', {'name': 'code'}))

        if hasCodeInput and newChannel != 'whatsapp':
            spinner.stop(f"Switched to SMS — code input present")
            return switchResponse
        if newChannel == 'sms':
            spinner.stop("Switched to SMS")
            return switchResponse
        spinner.fail(f"Form switch did not flip channel (still {newChannel})")

    #//! Fallback: GET the switch link if Amazon offered one.
    anchor, href = _findSmsSwitchLink(otpHtml)
    if anchor is not None:
        spinner = Log.spinner(f"Switching to SMS via link...").start()
        fullHref = href if href.startswith('http') else urljoin(str(otpResponse.url), href)
        try:
            linkResponse = session.get(fullHref, headers={
                'Referer': str(otpResponse.url),
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
            }, timeout=60)
            linkChannel = _detectChannel(linkResponse.text)
            if linkChannel == 'sms' or BeautifulSoup(linkResponse.text, 'html.parser').find('input', {'name': 'code'}):
                spinner.stop("Switched to SMS via link")
                return linkResponse
            spinner.fail(f"Link switch failed (channel={linkChannel})")
        except Exception as error:
            spinner.fail(f"Link switch error: {error}")

    #//! Last resort: direct GET with action params Amazon documents.
    if channel == 'whatsapp':
        spinner = Log.spinner("Switching to SMS via direct action...").start()
        for actionUrl in [
            f"{baseUrl}/ap/cvf/verify?action=SWITCH_CONTACT_TYPE_IN_CVF&newContactType=SMS_OTP",
            f"{baseUrl}/ap/cvf/verify?action=switchDefaultCvfOtpChannel&deliveryType=sms",
        ]:
            try:
                resp = session.get(actionUrl, headers={'Referer': str(otpResponse.url)}, timeout=60)
                if _detectChannel(resp.text) == 'sms' or BeautifulSoup(resp.text, 'html.parser').find('input', {'name': 'code'}):
                    spinner.stop(f"Switched to SMS via direct action")
                    return resp
            except Exception:
                continue
        spinner.fail("All switch mechanisms failed — SMS will likely time out")
        # Do NOT raise: let the flow still attempt getSMS; if it really
        # defaulted to WhatsApp the 75s timeout + retry will eventually
        # pick it up on a new number where SMS might be the default.

    #//! Channel was 'unknown' — just log and proceed.
    if channel == 'unknown':
        Log.detail("OTP channel", "unknown (no WA/SMS markers, proceeding)")

    return otpResponse


#//! ------------------------------------- Step 7 ------------------------------------- !\\#
def submitOtpCode(session, otpResponse, otpCode: str, phoneShort: str, user,
                  userAgent: str, baseUrl: str, dynamicUrls: list, dynamicHashes: list,
                  registrationDomain: str = 'amazon.com', targetDomain: str = None) -> str:
    """Submit the OTP code, warm up the wallet endpoint, and serialize cookies.

    Posts the OTP form with a fresh ``metadata1``, verifies the landing
    URL matches a known post-registration success marker, then follows
    up with a GET to ``/cpe/yourpayments/wallet`` on the target domain so
    the session picks up marketplace-specific auth cookies
    (``-acbes``/``-acbde``/…). Finally collects every non-empty cookie
    from the session jar into a single header-ready string.

    Args:
        session: curl_cffi session.
        otpResponse: Response from :func:`switchWhatsappToSms` (the SMS
            OTP page).
        otpCode: 6-digit code retrieved from HeroSMS.
        phoneShort: National phone number (for FWCIM).
        user: Fake-profile namespace (for FWCIM).
        userAgent: UA header.
        baseUrl: Base URL of the domain the OTP form was served on.
        dynamicUrls, dynamicHashes: FWCIM fallback script lists.
        registrationDomain: Registrable domain where the account was
            registered (always ``amazon.com`` in current configs).
        targetDomain: Domain whose wallet endpoint we should GET to pick
            up marketplace-specific cookies. Defaults to
            ``registrationDomain`` when not supplied.

    Returns:
        The final cookie string, ``"; "``-joined, ready to drop into a
        ``Cookie:`` header.

    Raises:
        AmazonRegisterError: ``otp_failed`` when the post-OTP landing URL
            doesn't match any success marker.
    """
    targetDomain = targetDomain or registrationDomain
    domain = registrationDomain
    spinner = Log.spinner("Submitting OTP verification code...").start()

    otpHtml = BeautifulSoup(otpResponse.text, 'html.parser')
    otpForm = None
    for formTag in otpHtml.find_all('form'):
        if formTag.find('input', {'name': 'code'}):
            otpForm = formTag
            break
    if not otpForm:
        otpForm = otpHtml.find('form')

    otpAction = otpForm.get('action', '') if otpForm else ''
    if otpAction and not otpAction.startswith('http'):
        otpAction = urljoin(str(otpResponse.url), otpAction)
    if not otpAction:
        otpAction = f'{baseUrl}/ap/cvf/verify'

    otpUrls, otpHashes = helpers.extractScripts(otpResponse.text)
    otpPayload = {}
    if otpForm:
        for hiddenInput in otpForm.find_all('input', {'type': 'hidden'}):
            fieldName = hiddenInput.get('name')
            if fieldName:
                otpPayload[fieldName] = hiddenInput.get('value', '')
    otpPayload['action']    = 'code'
    otpPayload['code']      = otpCode
    # Keep original metadata1 from the form rather than regenerating —
    # Amazon's OTP page already bakes in a valid ECdITeCs: token server-side;
    # overwriting with our own FWCIM metadata causes the submission to fail.
    # otpPayload['metadata1'] = helpers.generateMetadata(...)  # DISABLED

    otpSubmitResponse = helpers.postForm(session, otpAction, otpPayload, str(otpResponse.url), baseUrl)

    #//! `at-main` presence is the real "you are logged in" signal — the
    #//! landing URL after a successful code submit varies (homepage, a
    #//! /gp/ page, or a WebAuthn passkey-enrollment nudge) and shouldn't
    #//! be used to decide success/failure.
    if not helpers.isAuthenticated(session):
        raise AmazonRegisterError("otp_failed")

    spinner.stop("Account created successfully!")
    return finalizeAccountCookies(session, registrationDomain=domain, targetDomain=targetDomain)


def finalizeAccountCookies(session, registrationDomain: str = 'amazon.com', targetDomain: str = None) -> str:
    """Warm up the wallet endpoint and serialize the final cookie string.

    Shared tail for both post-OTP success (:func:`submitOtpCode`) and the
    no-OTP-needed case, where Amazon authenticates the account straight
    off a cleared captcha (confirmed via HAR capture, 2026-07-21) without
    ever showing an OTP page at all.

    Args:
        session: curl_cffi session, already authenticated (`at-main` set).
        registrationDomain: Registrable domain where the account was
            registered (always ``amazon.com`` in current configs).
        targetDomain: Domain whose wallet endpoint we should GET to pick
            up marketplace-specific cookies. Defaults to
            ``registrationDomain`` when not supplied.

    Returns:
        The final cookie string, ``"; "``-joined, ready to drop into a
        ``Cookie:`` header.
    """
    domain = registrationDomain
    targetDomain = targetDomain or registrationDomain

    #//! Navigate to the wallet page on the country-specific marketplace so the
    #//! session picks up the authenticated wallet/billing cookies before we
    #//! serialize. Amazon sets additional -main/-acb** cookies on this
    #//! endpoint that aren't present on the post-OTP landing page.
    #//! Fetch wallet on the TARGET marketplace domain (not the US
    #//! registration domain) so the session picks up country-specific
    #//! auth cookies (e.g. -acbes for ES, -acbde for DE, etc.).
    spinner = Log.spinner(f"Retrieving wallet cookies from {targetDomain}...").start()
    walletUrl = f"https://www.{targetDomain}/cpe/yourpayments/wallet?ref_=ya_mb_mpo"
    try:
        session.get(
            walletUrl,
            headers={
                'Referer': f'https://www.{domain}/',
                'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            },
            timeout=60,
            allow_redirects=True,
        )
        spinner.stop(f"Wallet cookies retrieved from {domain}")
    except Exception as error:
        spinner.fail(f"Wallet fetch failed: {error}")

    Log.info("Registration complete, retrieving cookies...")

    #//! Collect cookies via the underlying jar — avoids CookieConflictError
    #//! when the same name exists on multiple domains (e.g. session-id on
    #//! .amazon.com and .amazon.de after the wallet hit crossed domains).
    cookieMap = {}
    for cookieEntry in session.cookies.jar:
        if cookieEntry.value:
            cookieMap[cookieEntry.name] = cookieEntry.value

    signedCookies = {'tlgShopData': 'Sxgitario2026_ApiCodeServices', 'telegramCoderUser': 'Vxsilisk'}
    return "; ".join(
        [f"{name}={value}" for name, value in cookieMap.items()]
        + [f"{name}={value}" for name, value in signedCookies.items()]
    )

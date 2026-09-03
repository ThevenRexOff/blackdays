"""HTTP-session factory, fake-profile generator, form helpers and page classifiers.

All cross-step primitives live here so :mod:`amazon.flow` can stay
declarative — each step just composes these building blocks:

* :func:`buildSession` — curl_cffi session with coherent TLS/UA/client-hints
  headers for the target country.
* :func:`generateFakeProfile` — Faker-backed fake identity (name, email,
  password) with locale-appropriate character set.
* :func:`generateMetadata` — one-shot ``metadata1`` (FWCIM) builder that
  wraps :class:`FwcimAmazonSxgitario`.
* :func:`submitRegister` — register-form POST with fresh metadata1 +
  CSE-encrypted password.
* :func:`postForm` — form POST with Amazon-flavored headers.
* :func:`extractScripts` / :func:`getHiddenField` — page parsing.
* :func:`normalizeProxy` — coerce user-provided proxy string to the
  ``http://host:port`` shape curl_cffi expects.
* :func:`isCaptcha`, :func:`detectCaptchaType`, :func:`isOtp`,
  :func:`isUnusual`, :func:`isRegForm` — multi-locale page classifiers
  the flow uses to branch after every POST.

Amazon's client-side-encryption public key material is regional, not
global — see :data:`core.CSE_PROFILES` / :func:`core.cseProfileFor`.
"""

import os, random, re, time, types
from urllib.parse import urljoin

from faker import Faker
from curl_cffi import requests
from bs4 import BeautifulSoup

from . import core
from .metadataGenSxgitario import FwcimAmazonSxgitario
from .siegeCse import encryptPassword
from services import Log


def generateFakeProfile(country: str = 'US') -> types.SimpleNamespace:
    """Generate a Faker-backed fake identity for the target country.

    Uses the country's ``faker_locale`` so first/last names match the
    marketplace (e.g. Japanese names for ``JP``). Email local-parts are
    ASCII-normalized — Amazon rejects non-ASCII in email addresses even
    on the .jp domain.

    Args:
        country: ISO country code from :data:`core.COUNTRY_CONFIG`.
            Unknown codes fall back to ``'US'``.

    Returns:
        A ``types.SimpleNamespace`` with ``f_name``, ``l_name``, ``name``,
        ``password``, ``mail`` attributes.
    """
    countryConfig = core.COUNTRY_CONFIG.get(country.upper(), core.COUNTRY_CONFIG['US'])
    try:
        faker = Faker(countryConfig['faker_locale'])
    except Exception:
        faker = Faker('en_US')
    firstName = faker.first_name()
    lastName  = faker.last_name()
    # Strip non-ASCII for email local-part to keep Amazon happy
    asciiFirst = ''.join(char for char in firstName if char.isascii() and char.isalnum()) or "user"
    asciiLast  = ''.join(char for char in lastName  if char.isascii() and char.isalnum()) or "mail"
    return types.SimpleNamespace(
        f_name=firstName, l_name=lastName, name=f"{firstName} {lastName}",
        password=f"{random.choice(('Sxgitario', 'Quetzxl', 'TeamArgo', 'Vxsilisk'))}{random.randint(1000, 9999)}",
        mail=f"{asciiFirst}{random.choice('._-')}{asciiLast}{random.randint(0, 999)}@{random.choice(countryConfig['email_domains'])}",
    )


def buildSession(baseUrl, domain, proxy, country: str = 'US'):
    """Create a curl_cffi session with coherent TLS + header fingerprint.

    Picks a single entry from :data:`core.BROWSER_PROFILES` so the TLS
    handshake (JA3/JA4), ``User-Agent``, ``sec-ch-ua`` and
    ``sec-ch-ua-full-version-list`` all declare the same Chrome major.
    Also resets :class:`FwcimAmazonSxgitario`'s session-level cache so
    every new account gets a fresh hardware profile and ``lsUbid``.

    Args:
        baseUrl: Marketplace base URL (``https://www.amazon.com``).
        domain: Registrable domain for cookie scoping (``amazon.com``).
        proxy: Optional proxy (``user:pass@host:port`` or full URL).
        country: ISO code — drives ``Accept-Language`` and hardware hints.

    Returns:
        Tuple ``(session, userAgent)`` — ``curl_cffi.requests.Session``
        and the UA header value the session was configured with.
    """
    FwcimAmazonSxgitario.reset_session()

    countryConfig  = core.COUNTRY_CONFIG.get(country.upper(), core.COUNTRY_CONFIG['US'])
    acceptLanguage = countryConfig['accept_language']

    # Pick ONE browser profile so the TLS fingerprint (curl_cffi impersonate),
    # the User-Agent header and the sec-ch-ua client hints all declare the
    # same Chrome major version. Mixed versions used to leak a mismatch that
    # Amazon can cross-check between JA3/JA4 and UA.
    browserProfile  = random.choice(core.BROWSER_PROFILES)
    session         = requests.Session(impersonate=browserProfile['impersonate'])
    userAgent       = browserProfile['userAgent']
    majorVersion    = browserProfile['majorVersion']
    fullVersion     = browserProfile['fullVersion']
    secChUa         = browserProfile['secChUa']
    secChUaFull     = secChUa.replace(f'";v="{majorVersion}"', f'";v="{fullVersion}"') \
                             .replace(f'";v="24"', f'";v="24.0.0.0"') \
                             .replace(f'";v="99"', f'";v="99.0.0.0"')

    fingerprintProfile = FwcimAmazonSxgitario._session_profile
    if not fingerprintProfile:
        FwcimAmazonSxgitario(location=baseUrl, userAgent=userAgent)
        fingerprintProfile = FwcimAmazonSxgitario._session_profile

    screen             = fingerprintProfile["screen"]
    viewportWidth      = screen["width"]
    devicePixelRatio   = fingerprintProfile["dpr"]
    deviceMemory       = str(min(8, fingerprintProfile["deviceMemory"]))

    if proxy:
        formattedProxy = proxy if '://' in proxy else f'http://{proxy}'
        session.proxies = {'http': formattedProxy, 'https': formattedProxy}
    session.headers.update({
        'User-Agent': userAgent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': acceptLanguage, 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1',
        'sec-ch-ua': secChUa, 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-full-version-list': secChUaFull, 'sec-ch-ua-platform-version': '"10.0"',
        'device-memory': deviceMemory, 'sec-ch-device-memory': deviceMemory,
        'dpr': str(devicePixelRatio), 'sec-ch-dpr': str(devicePixelRatio),
        'viewport-width': str(viewportWidth), 'sec-ch-viewport-width': str(viewportWidth),
        'ect': '4g', 'rtt': '50', 'downlink': '10',
    })
    return session, userAgent


def getHiddenField(html, name):
    """Return the value of a hidden ``<input>`` (or selected ``<option>``).

    Args:
        html: ``BeautifulSoup`` object of the page.
        name: The ``name`` attribute to find.

    Returns:
        The ``value`` string, or ``None`` if the field isn't present.
    """
    inputElement = html.find('input', {'name': name})
    if inputElement:
        return inputElement.get('value', '')
    selectElement = html.find('select', {'name': name})
    if selectElement:
        selectedOption = selectElement.find('option', selected=True)
        return selectedOption.get('value', '') if selectedOption else None
    return None


def postForm(session, url, data, referer, origin, params=None):
    """POST a form with Amazon-flavored navigation headers.

    Sends ``Content-Type: application/x-www-form-urlencoded`` plus the
    ``Sec-Fetch-*`` set and ``Origin``/``Referer`` that Amazon expects on
    top-level form submissions.

    Args:
        session: A ``curl_cffi`` session.
        url: Destination URL.
        data: Form payload dict.
        referer: URL to put in the ``Referer`` header.
        origin: URL to put in the ``Origin`` header.
        params: Optional query-string params — the email/mail.tm channel's
            claim and register-form endpoints require the OpenID params
            on the URL itself, not just in the POST body.

    Returns:
        ``curl_cffi.requests.Response``.
    """
    return session.post(url, data=data, params=params, headers={
        'Content-Type': 'application/x-www-form-urlencoded', 'Origin': origin, 'Referer': str(referer),
        'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1',
    }, timeout=60)


def generateMetadata(location, referrer, urls, hashes, userAgent, email="", name="", password="", postCaptcha=False, canvasStrategy="", marketplace=""):
    """Build one ``metadata1`` value (FWCIM fingerprint) for the current request.

    Wraps :class:`FwcimAmazonSxgitario`. Metadata must be regenerated per
    POST — do NOT cache the returned string.

    Args:
        location: URL of the page the form is being submitted from.
        referrer: The ``document.referrer`` the bundle reads. Our
            non-browser flow passes an empty string unless the caller
            has a real DOM value.
        urls: List of dynamic script URLs from :func:`extractScripts`.
        hashes: List of 32-bit inline-script hashes from
            :func:`extractScripts`.
        userAgent: UA header the current session is using.
        email, name, password: Form values that should be fingerprinted.
        postCaptcha: True on a resubmit right after a captcha was cleared —
            sets ``token.pageHasCaptcha`` so the payload matches the
            server's own log of that page.
        marketplace: Two-letter market code (US, MX, DE, …). Used to
            select the correct HW profile pool, form email key, and
            keystroke timing. If omitted the marketplace is inferred from
            ``location``.

    Returns:
        The encrypted ``metadata1`` string (``ECdITeCs:…``).

    Raises:
        RuntimeError: if the generator itself fails (should be rare —
            it swallows nothing silently).
    """
    result = FwcimAmazonSxgitario(
        location=location, userAgent=userAgent, referrer=referrer,
        dynamicUrls=urls, inlineHashes=hashes,
        emailValue=email, customerName=name, passwordValue=password,
        postCaptcha=postCaptcha, canvasStrategy=canvasStrategy,
        marketplace=marketplace,
    ).generateMetadata()
    if not result.get('status'):
        raise RuntimeError(f"metadata1 generation failed: {result.get('description')}")
    return result['metadata1']


def extractScripts(htmlContent):
    """Extract dynamic script URLs and inline-script hashes from HTML.

    FWCIM's fingerprint depends on the list of scripts a real browser
    would load (by URL) and the 32-bit hashes of every inline script
    block. Those values go into ``metadata1`` and must match what
    Amazon's page actually contains at the time of the POST.

    Args:
        htmlContent: Raw HTML string.

    Returns:
        ``(scriptUrls, scriptHashes)`` — ``list[str]`` of src URLs
        (reversed to match browser-eval order) and ``list[int]`` of
        inline-script hashes (signed 32-bit).
    """
    scriptUrls = []
    for scriptTag in re.findall(r'<script[\s\S]*?>[\s\S]*?<\/script>', htmlContent, re.IGNORECASE):
        for pattern in [
            re.compile(r'load\.js\([\'"](https?://[^\'"]+)[\'"]\)'),
            re.compile(r'ue\.uels\([\'"](https?://[^\'"]+\.js)[\'"]\)'),
            re.compile(r'src=["\'](https://static\.siege-amazon\.com/[^\'"]+\.js\?v=\d+)["\']'),
            re.compile(r'src=["\'](https://[^"\']+AUIClients/[^"\']+)["\']'),
            re.compile(r'src=["\'](https://m\.media-amazon\.com/[^"\']+\.js[^"\']*)["\']'),
            re.compile(r'src=["\'](https://images-na\.ssl-images-amazon\.com/[^"\']+\.js[^"\']*)["\']'),
        ]:
            scriptUrls.extend(match.group(1) for match in pattern.finditer(scriptTag))
    seen_urls, deduped = set(), []
    for u in scriptUrls:
        if u not in seen_urls:
            seen_urls.add(u)
            deduped.append(u)
    deduped.reverse()
    scriptUrls = deduped

    scriptHashes = []
    for scriptTag in BeautifulSoup(htmlContent, 'html.parser').find_all('script'):
        if not scriptTag.get('src') and scriptTag.string:
            content = scriptTag.string.strip()
            if content:
                hashValue = 0
                for char in content:
                    hashValue = (31 * hashValue + ord(char)) & 0xFFFFFFFF
                if hashValue >= 0x80000000:
                    hashValue -= 0x100000000
                scriptHashes.append(hashValue)
    return scriptUrls, scriptHashes


def submitRegister(session, page, referer, phoneShort, user, userAgent, baseUrl,
                   dynamicUrls, dynamicHashes, defaultCountryCode, debugLabel,
                   postCaptcha=False, leanPayload=False, regParams=None):
    """Re-submit the register form with a fresh ``metadata1`` + encrypted password.

    Extracts the current page's hidden fields (appActionToken,
    workflowState, anti-csrftoken-a2z, etc.), overlays our fresh values
    for email/name/password/metadata1, and POSTs to the form's action
    URL. Confirmed field-for-field against a real-browser HAR capture
    (2026-07-21, US): the actual submission never includes plaintext
    ``password``/``passwordCheck`` at all — even though the rendered form
    has those input names, the client-side JS replaces them with
    ``encryptedPwd``/``encryptedPwdCheck`` before sending and drops the
    plaintext fields entirely.

    Args:
        session: curl_cffi session.
        page: Response containing the register form we should re-submit.
        referer: URL to put in ``Referer``.
        phoneShort: National phone number (no calling code) — goes in
            the ``email`` field.
        user: Fake-profile namespace from :func:`generateFakeProfile`.
        userAgent: UA for the FWCIM fingerprint.
        baseUrl: Marketplace base URL.
        dynamicUrls, dynamicHashes: Fallback script lists for FWCIM if
            the current page has none.
        defaultCountryCode: ``countryCode`` used when the hidden field
            is missing. Unused when ``leanPayload`` is True.
        debugLabel: Free-form string used in log lines for this submit.
        postCaptcha: Passed through to FWCIM (changes metric defaults).
        leanPayload: True for the email/mail.tm channel — omits
            ``countryCode``/``changeClaimUrl``/``encryptedPasswordExpected``.
            Confirmed live (2026-07-23): the phone channel's full payload
            (this flag False) produces a real, normally-loggable-into
            account there, but for email identities it produced a
            "phantom" account instead — session authenticated, cookies
            extractable, but never indexed by Amazon's own `/ap/signin`
            lookup. The reference tool's ("genv2") leaner payload, which
            this flag replicates, produced a real account in the same
            test. Do not set this for the phone channel — unverified
            there and the fuller payload is what's actually proven for it.
        regParams: OpenID query params to send alongside the POST body —
            required (non-None) when ``leanPayload`` is True, since the
            email channel's real register submit carries them on the URL
            too (`visitSignInPage`/`submitEmailClaim`'s ``regParams``).

    Returns:
        The POST response (``curl_cffi.requests.Response``).
    """
    pageHtml   = BeautifulSoup(page.text, 'html.parser')
    pageUrls, pageHashes = extractScripts(page.text)
    metadata   = generateMetadata(str(page.url), "", pageUrls or dynamicUrls,
                                  pageHashes or dynamicHashes, userAgent,
                                  email=phoneShort, name=user.name, password=user.password,
                                  postCaptcha=postCaptcha)
    # Extract NEW hidden fields from the page (critical for EU post-captcha
    # flow where appActionToken, workflowState, prevRID are refreshed and
    # may be ape:-encoded). Use these as-is — Amazon's server decodes them.
    # But ALWAYS override metadata1, email, customerName, password with our
    # fresh values — the form's hidden fields for these are either stale
    # (ape:-encoded metadata1 from the original POST) or empty (password
    # fields don't exist as hidden inputs in the post-CVF form).
    appActionTokenValue = getHiddenField(pageHtml, 'appActionToken')
    # Amazon's CSE public key is regional, not global (confirmed live
    # 2026-07-23 — see core.CSE_PROFILES): using the NA key for EU/FE
    # marketplaces encrypts the password against the wrong public key
    # entirely. defaultCountryCode is the Amazon 2-letter code (e.g. 'GB'
    # for UK), which is exactly what core.cseProfileFor expects.
    #
    # Uses amazon.siegeCse (our own reimplementation) instead of the
    # protected cseAmazonSxgitario module: Amazon's real envelope binds
    # the request's appActionToken into the encryption's AAD (confirmed
    # live via crypto.subtle instrumentation, 2026-07-23) and the
    # protected module has no way to accept that extra value. Omitting it
    # doesn't break registration — the OTP step is what authenticates the
    # session — but it left the account's real password out of sync with
    # what the user was told, so a normal password sign-in afterwards
    # failed with "incorrect password". See amazon/siegeCse.py docstring.
    cseProfile = core.cseProfileFor(defaultCountryCode)
    encryptedPwd      = encryptPassword(user.password, cseProfile['jwkN'], cseProfile['keyId'], appActionTokenValue)
    encryptedPwdCheck = encryptPassword(user.password, cseProfile['jwkN'], cseProfile['keyId'], appActionTokenValue)
    payload = {
        'appActionToken':            appActionTokenValue,
        'appAction':                 'REGISTER',
        'openid.return_to':          getHiddenField(pageHtml, 'openid.return_to'),
        'prevRID':                   getHiddenField(pageHtml, 'prevRID'),
        'workflowState':             getHiddenField(pageHtml, 'workflowState'),
        'anti-csrftoken-a2z':        getHiddenField(pageHtml, 'anti-csrftoken-a2z'),
        'claimCollectionLayoutType': getHiddenField(pageHtml, 'claimCollectionLayoutType') or 'unifiedAuthClaimCollection',
        # HAR capture (MX): the real browser ALWAYS sends
        # `unifiedAuthTreatment` (empty) on the register POST — missing it
        # makes Amazon treat the payload as malformed in some marketplaces.
        'unifiedAuthTreatment':      getHiddenField(pageHtml, 'unifiedAuthTreatment') or '',
        # These fields are ALWAYS our fresh data, never from hidden fields.
        'email':                     phoneShort,
        'customerName':              user.name,
        'encryptedPwd':              encryptedPwd,
        'encryptedPwdCheck':         encryptedPwdCheck,
        'metadata1':                 metadata,
    }
    if not leanPayload:
        # `countryCode`/`changeClaimUrl`/`encryptedPasswordExpected` — proven
        # required for the phone channel (see docstring), but confirmed to
        # produce a phantom/non-indexed account when sent for the email
        # channel instead. Only ever add them here, never for leanPayload.
        payload['countryCode']               = getHiddenField(pageHtml, 'countryCode') or defaultCountryCode
        payload['changeClaimUrl']            = getHiddenField(pageHtml, 'changeClaimUrl') or ''
        payload['encryptedPasswordExpected'] = ''

    # Use the form's action URL instead of hardcoding — post-CVF forms on
    # EU may have the full URL with the correct domain.
    formTag = pageHtml.find('form', action=True)
    formAction = formTag.get('action', '') if formTag else ''
    if formAction and formAction.startswith('http'):
        submitUrl = formAction
    else:
        submitUrl = f'{baseUrl}/ap/register'

    return postForm(session, submitUrl, payload, page.url, baseUrl, params=regParams)


def normalizeProxy(proxy):
    """Coerce a proxy string to the ``scheme://host:port`` form.

    Args:
        proxy: Proxy as ``user:pass@host:port`` or a full URL, or ``None``.

    Returns:
        The string with ``http://`` prefixed when no scheme was present,
        or ``None`` if input was falsy.
    """
    if not proxy: return None
    return proxy if '://' in proxy else f'http://{proxy}'


# ── Response detectors ──────────────────────────────────────────
# Multi-locale: Amazon localizes these pages, so we match on the
# translations for every supported marketplace, not just EN/ES.

_OTP_KEYWORDS = (
    # EN
    'verify your identity', 'verification code', 'we sent a code', 'verify mobile',
    'two-step verification', 'enter the code',
    # ES
    'confirma tu identidad', 'confirme su identidad', 'código de verificación',
    'enviamos un código', 'te enviamos un código', 'verifica tu número',
    # DE
    'identität bestätigen', 'bestätigungscode', 'bestätigen sie ihre identität',
    'wir haben einen code', 'code eingeben',
    # FR
    "vérifier votre identité", "code de vérification", "nous avons envoyé un code",
    "vérifiez votre identité", "saisissez le code",
    # IT
    'verifica la tua identità', 'codice di verifica', 'abbiamo inviato un codice',
    'inserisci il codice',
    # PT (BR)
    'verificar sua identidade', 'código de verificação', 'enviamos um código',
    'verifique sua identidade',
    # NL
    'verifieer je identiteit', 'verificatiecode', 'we hebben een code',
    # PL
    'zweryfikuj tożsamość', 'kod weryfikacyjny', 'wysłaliśmy kod',
    # TR
    'kimliğinizi doğrulayın', 'doğrulama kodu', 'bir kod gönderdik',
    # JP
    '本人確認', '確認コード', 'コードを送信しました',
    # AR
    'تحقق من هويتك', 'رمز التحقق', 'أرسلنا رمزًا',
)

_UNUSUAL_KEYWORDS = (
    # EN
    'unusual activity', "aren't able to create", 'we cannot create',
    # ES
    'actividad inusual', 'no podemos crear',
    # DE
    'ungewöhnliche aktivität', 'konto nicht erstellen',
    # FR
    'activité inhabituelle', 'impossible de créer',
    # IT
    'attività insolita', 'non è possibile creare',
    # PT
    'atividade incomum', 'não conseguimos criar',
    # NL
    'ongebruikelijke activiteit',
    # PL
    'nietypowa aktywność',
    # TR
    'olağandışı etkinlik', 'hesap oluşturamıyoruz',
    # JP
    '通常と異なるアクティビティ', 'アカウントを作成できません',
    # AR
    'نشاط غير معتاد',
)

_CAPTCHA_KEYWORDS = (
    'aamation', 'authentication required',
    'autenticación requerida', 'authentifizierung erforderlich',
    "authentification requise", 'autenticazione richiesta',
    'autenticação necessária', '認証が必要',
)

def isCaptcha(pageText):
    """Return ``True`` if the page is an aamation captcha challenge.

    Detects by the combination of ``data-external-id`` attribute and a
    known localized "authentication required" headline.
    """
    lowered = pageText.lower()
    return 'data-external-id' in lowered and any(keyword in lowered for keyword in _CAPTCHA_KEYWORDS)

def detectCaptchaType(pageText):
    """Detect which captcha system Amazon is serving.

    The aamation widget declares its variant through
    ``data-challenge-type``:

    * ``WAF_ADVERSARIAL_SYNTHETIC_GRID_V2_LEVEL_1`` — AWS WAF grid (US/CA).
    * ``ARKOSE_LEVEL_4`` — Arkose Labs FunCaptcha (every other marketplace).

    The Arkose enforcement bundle is lazy-loaded, so the raw HTML almost
    never contains the strings ``arkoselabs`` / ``funcaptcha`` — the
    ``data-challenge-type`` attribute is the reliable signal.

    Returns:
        ``'aws_waf'`` / ``'funcaptcha'`` / ``'both'`` / ``'none'``.
    """
    lowered       = pageText.lower()
    hasAamation   = 'data-external-id' in lowered and 'aamation' in lowered

    challengeMatch = re.search(r'"data-challenge-type"\s*:\s*"([^"]+)"', pageText)
    declaredType   = (challengeMatch.group(1) if challengeMatch else '').upper()

    hasArkose = declaredType.startswith('ARKOSE') \
                 or 'arkoselabs' in lowered \
                 or 'funcaptcha'  in lowered \
                 or '56938EF5-6EFA-483E-B6F6-C8A72B6A95EE' in pageText
    hasWaf    = declaredType.startswith('WAF') or (hasAamation and not hasArkose)

    if hasWaf and hasArkose: return 'both'
    if hasArkose:            return 'funcaptcha'
    if hasWaf:               return 'aws_waf'
    return 'none'

def isOtp(pageText):
    """Return ``True`` if the page is the real OTP-entry screen.

    A real OTP page has BOTH a localized "verification code" keyword in
    the body AND a ``<input name="code">`` field. The conjunction avoids
    false positives on register pages that mention "two-step verification"
    in a banner but don't actually ask for the code.
    """
    # A REAL OTP page has BOTH:
    #   1) a text keyword like "verification code" / "enter the code"
    #   2) an <input name="code"> for typing the OTP
    #
    # Previously we used (keyword OR codeInput) which caused false
    # positives on register pages that mention "two-step verification"
    # in their banner text. After captcha, the flow returned to
    # /ap/register with such text, our detector said "OTP reached!",
    # and we jumped to getSMS() without ever re-submitting the register
    # form — so the SMS was never triggered and the 75s timeout fired.
    #
    # Changing to AND is safe because real OTP pages always have both:
    # the keyword in the body AND the code input in the form.
    if isCaptcha(pageText):
        return False
    lowered = pageText.lower()
    if 'se ha producido un error' in lowered:
        return False
    hasKeyword   = any(keyword in lowered for keyword in _OTP_KEYWORDS)
    hasCodeInput = bool(re.search(r'name\s*=\s*["\']code["\']', pageText, re.I))
    return hasKeyword and hasCodeInput

def isUnusual(pageText):
    """Return ``True`` if the page carries an "unusual activity" marker.

    Matches the localized Amazon block-page copy across all 18 locales.
    """
    lowered = pageText.lower()
    return any(keyword in lowered for keyword in _UNUSUAL_KEYWORDS)

def isRegForm(pageText):
    """Return ``True`` if the page is a server-rendered register form.

    Requires an actual ``<form>`` with an ``appActionToken`` hidden
    input; parses the HTML rather than raw-grepping the text so we don't
    false-positive on SPA pages whose JS bundles embed those strings.
    """
    # Previous implementation matched on raw text ("appActionToken" +
    # "REGISTER" anywhere in the page). This false-positived on SPA pages
    # where JavaScript bundles contain those strings but no actual
    # <form> or <input> elements exist in the HTML. We now verify a
    # REAL <form> with an appActionToken hidden input, which is the only
    # reliable indicator that we have a server-rendered register form
    # we can POST from.
    if 'appActionToken' not in pageText:
        return False
    soup = BeautifulSoup(pageText, 'html.parser')
    for formTag in soup.find_all('form'):
        if formTag.find('input', {'name': 'appActionToken'}):
            return True
    return False


def isAuthenticated(session) -> bool:
    """True once Amazon has actually set the authenticated login cookie.

    More robust than matching the post-registration landing URL against a
    fixed marker list: a successful registration can land on very
    different final pages (homepage, a `/gp/...` page, or a WebAuthn
    passkey-enrollment nudge at `/ax/claim/webauthn/nudge` — confirmed via
    a real-browser HAR capture, 2026-07-21) depending on Amazon's own
    post-signup flow, but the auth cookie is only ever set once the
    account is genuinely logged in, regardless of where the redirect
    chain ends up.

    The cookie's NAME depends on the marketplace: `at-main` on
    amazon.com, but every other marketplace uses a country-suffixed
    variant instead — confirmed live 2026-07-22 that amazon.ca sets
    `at-acbca`, not `at-main` (a real successful CA registration was
    misclassified as `unexpected_response` before this fix, because the
    literal `at-main` check never matched). The `at-acb*` pattern is the
    same one already referenced elsewhere in this codebase for wallet
    cookies (`-acbes` for ES, `-acbde` for DE, etc.), so this checks for
    either shape instead of hardcoding just `at-main`.
    """
    for cookie in session.cookies.jar:
        if not cookie.value:
            continue
        if cookie.name == 'at-main' or cookie.name.startswith('at-acb'):
            return True
    return False

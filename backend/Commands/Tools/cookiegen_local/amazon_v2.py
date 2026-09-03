import os, re, sys, json, base64, random, uuid, time, secrets
import urllib.parse
import urllib3
import asyncio
import aiofiles

from curl_cffi import AsyncSession
import log
from faker import Faker
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from fingerprint import generate_metadata1
from generate_password import encrypt_password, REGION_KEYS
from tempmail import make_provider


# ── Country Configurations ───────────────────────────────────────────────────

COUNTRY_CONFIG = {
    "US": {"domain":"amazon.com","tld":"com","assoc_handle":"usflex","page_id":"usflex","lang":"en-US","faker_locale":"en_US","phone_prefix":"+1","phone_digits":(10,10),"accept_language":"en-US,en;q=0.9","address":{"city":"New York","state":"NY","postal":"10080","country_code":"US","street":"5th Avenue"}},
    "DE": {"domain":"amazon.de","tld":"de","assoc_handle":"deflex","page_id":"deflex","lang":"de-DE","faker_locale":"de_DE","phone_prefix":"+49","phone_digits":(10,11),"accept_language":"de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Berlin","state":"Berlin","postal":"10115","country_code":"DE","street":"Friedrichstraße"}},
    "ES": {"domain":"amazon.es","tld":"es","assoc_handle":"esflex","page_id":"esflex","lang":"es-ES","faker_locale":"es_ES","phone_prefix":"+34","phone_digits":(9,9),"accept_language":"es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Madrid","state":"Madrid","postal":"28001","country_code":"ES","street":"Calle de Alcalá"}},
    "IT": {"domain":"amazon.it","tld":"it","assoc_handle":"itflex","page_id":"itflex","lang":"it-IT","faker_locale":"it_IT","phone_prefix":"+39","phone_digits":(10,10),"accept_language":"it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Roma","state":"Lazio","postal":"00100","country_code":"IT","street":"Via del Corso"}},
    "JP": {"domain":"amazon.co.jp","tld":"co.jp","assoc_handle":"jpflex","page_id":"jpflex","lang":"ja-JP","faker_locale":"ja_JP","phone_prefix":"+81","phone_digits":(10,10),"accept_language":"ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"千代田区","state":"東京都","postal":"100-0001","country_code":"JP","street":"丸の内"}},
    "CA": {"domain":"amazon.ca","tld":"ca","assoc_handle":"caflex","page_id":"caflex","lang":"en-CA","faker_locale":"en_CA","phone_prefix":"+1","phone_digits":(10,10),"accept_language":"en-CA,en;q=0.9,fr-CA;q=0.8,fr;q=0.7","address":{"city":"Toronto","state":"ON","postal":"M5H 2N2","country_code":"CA","street":"Bay Street"}},
    "AU": {"domain":"amazon.com.au","tld":"com.au","assoc_handle":"auflex","page_id":"auflex","lang":"en-AU","faker_locale":"en_AU","phone_prefix":"+61","phone_digits":(9,9),"accept_language":"en-AU,en;q=0.9","address":{"city":"Sydney","state":"NSW","postal":"2000","country_code":"AU","street":"George Street"}},
    "BR": {"domain":"amazon.com.br","tld":"com.br","assoc_handle":"brflex","page_id":"brflex","lang":"pt-BR","faker_locale":"pt_BR","phone_prefix":"+55","phone_digits":(10,11),"accept_language":"pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"São Paulo","state":"SP","postal":"01001-000","country_code":"BR","street":"Avenida Paulista"}},
    "MX": {"domain":"amazon.com.mx","tld":"com.mx","assoc_handle":"mxflex","page_id":"mxflex","lang":"es-MX","faker_locale":"es_MX","phone_prefix":"+52","phone_digits":(10,10),"accept_language":"es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Ciudad de Mexico","state":"CDMX","postal":"06600","country_code":"MX","street":"Avenida Reforma"}},
    "IN": {"domain":"amazon.in","tld":"in","assoc_handle":"inflex","page_id":"inflex","lang":"en-IN","faker_locale":"en_IN","phone_prefix":"+91","phone_digits":(10,10),"accept_language":"en-IN,en;q=0.9,hi;q=0.8","address":{"city":"Mumbai","state":"Maharashtra","postal":"400001","country_code":"IN","street":"Marine Drive"}},
    "NL": {"domain":"amazon.nl","tld":"nl","assoc_handle":"nlflex","page_id":"nlflex","lang":"nl-NL","faker_locale":"nl_NL","phone_prefix":"+31","phone_digits":(9,9),"accept_language":"nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Amsterdam","state":"Noord-Holland","postal":"1012","country_code":"NL","street":"Damrak"}},
    "SG": {"domain":"amazon.sg","tld":"sg","assoc_handle":"sgflex","page_id":"sgflex","lang":"en-SG","faker_locale":"en_GB","phone_prefix":"+65","phone_digits":(8,8),"accept_language":"en-SG,en;q=0.9","address":{"city":"Singapore","state":"Singapore","postal":"018956","country_code":"SG","street":"Orchard Road"}},
    "AE": {"domain":"amazon.ae","tld":"ae","assoc_handle":"aeflex","page_id":"aeflex","lang":"en-AE","faker_locale":"ar_AE","phone_prefix":"+971","phone_digits":(9,9),"accept_language":"en-AE,en;q=0.9,ar;q=0.8","address":{"city":"Dubai","state":"Dubai","postal":"00000","country_code":"AE","street":"Sheikh Zayed Road"}},
    "SA": {"domain":"amazon.sa","tld":"sa","assoc_handle":"saflex","page_id":"saflex","lang":"ar-SA","faker_locale":"ar_SA","phone_prefix":"+966","phone_digits":(9,9),"accept_language":"ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Riyadh","state":"Riyadh","postal":"11564","country_code":"SA","street":"Olaya Street"}},
    "TR": {"domain":"amazon.com.tr","tld":"com.tr","assoc_handle":"trflex","page_id":"trflex","lang":"tr-TR","faker_locale":"tr_TR","phone_prefix":"+90","phone_digits":(10,10),"accept_language":"tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Istanbul","state":"Istanbul","postal":"34000","country_code":"TR","street":"İstiklal Caddesi"}},
    "SE": {"domain":"amazon.se","tld":"se","assoc_handle":"seflex","page_id":"seflex","lang":"sv-SE","faker_locale":"sv_SE","phone_prefix":"+46","phone_digits":(9,9),"accept_language":"sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Stockholm","state":"Stockholm","postal":"11120","country_code":"SE","street":"Drottninggatan"}},
    "PL": {"domain":"amazon.pl","tld":"pl","assoc_handle":"plflex","page_id":"plflex","lang":"pl-PL","faker_locale":"pl_PL","phone_prefix":"+48","phone_digits":(9,9),"accept_language":"pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Warsaw","state":"Mazowieckie","postal":"00-001","country_code":"PL","street":"Nowy Świat"}},
    "EG": {"domain":"amazon.eg","tld":"eg","assoc_handle":"egflex","page_id":"egflex","lang":"ar-EG","faker_locale":"ar_EG","phone_prefix":"+20","phone_digits":(10,10),"accept_language":"ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7","address":{"city":"Cairo","state":"Cairo","postal":"11511","country_code":"EG","street":"Tahrir Street"}},
}



class Account:
    def __init__(self, name, email, password, cookie):
        self.name = name
        self.email = email
        self.password = password
        self.cookie = cookie

    def __repr__(self):
        return f"Account(name={self.name!r}, email={self.email!r})"


def _build_account(result_data):
    return Account(
        name=result_data.get("name"),
        email=result_data.get("email"),
        password=result_data.get("password"),
        cookie=result_data.get("cookie_str"),
    )


load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_FAKERS = {}
# fmail.men is a separate service — Amazon never sees its IP, so it always goes
# direct (fast); only account traffic uses the REQ_PROXY below.
_PROXY_URL = os.getenv("AMZN_PROXY") or os.getenv("REQ_PROXY")

# User-Agent strings matched to each curl_cffi impersonate profile. Keeping the
# UA header consistent with the TLS (JA3) fingerprint matters: Amazon flags a
# chrome146 TLS handshake paired with a chrome131 UA as a bot giveaway.
_UA_MAP = {
    "chrome124": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "chrome131": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "chrome136": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "chrome142": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "chrome145": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "chrome146": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "chrome151": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "safari180": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "firefox133": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
}
# Allow overriding the TLS+UA profile at runtime via env var.
# chrome131 (the previous default) now gets flagged by amazon.com US as
# "automated traffic" — Amazon started rejecting its JA3 hash in late 2025.
# chrome142 is the most stable choice across amazon.com US + all the other
# regions (SA, MX, DE, BR…). It still passes amazon.com US on first try,
# and the matching sec-ch-ua is kept in lockstep in _SEC_CH_UA below.
_IMPERSONATE = os.getenv("AMZN_IMP", "chrome142")
if _IMPERSONATE not in _UA_MAP:
    log.warn(f"AMZN_IMP={_IMPERSONATE!r} no está en _UA_MAP — usando chrome142")
    _IMPERSONATE = "chrome142"
_UA = _UA_MAP[_IMPERSONATE]


def _profile_ua():
    return _UA_MAP.get(_IMPERSONATE, _UA)


# sec-ch-ua has to match the major version in the UA — otherwise the
# client-hints and the TLS fingerprint disagree, and Amazon's bot detector
# raises the "unusual activity" page instead of letting the register POST
# through. Keep these in lockstep with _IMPERSONATE.
_SEC_CH_UA = {
    "chrome124": '"Chromium";v="124", "Not-A.Brand";v="99", "Google Chrome";v="124"',
    "chrome131": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
    "chrome136": '"Chromium";v="136", "Not-A.Brand";v="99", "Google Chrome";v="136"',
    "chrome142": '"Chromium";v="142", "Not-A.Brand";v="99", "Google Chrome";v="142"',
    "chrome145": '"Chromium";v="145", "Not-A.Brand";v="99", "Google Chrome";v="145"',
    "chrome146": '"Chromium";v="146", "Not-A.Brand";v="99", "Google Chrome";v="146"',
    "chrome151": '"Chromium";v="151", "Not-A.Brand";v="99", "Google Chrome";v="151"',
}


def _profile_sec_ch_ua():
    return _SEC_CH_UA.get(_IMPERSONATE, _SEC_CH_UA["chrome131"])


def _tick(t0, label):
    log.info(label, f"+{time.time() - t0:.1f}s")


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_between(data, first, last):
    s = data.find(first)
    if s == -1: return None
    s += len(first)
    e = data.find(last, s)
    if e == -1: return None
    return data[s:e]

def bs_val(html, name, load_html=False, default=None):
    if load_html:
        html = BeautifulSoup(html, "lxml")
    el = html.find("input", {"name": name})
    if el:
        return el.get("value", default or "")
    return default or ""

async def save(filename, content):
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    async with aiofiles.open(filename, "w", encoding="utf-8") as f:
        log.highlight(f"[+] Guardando", filename)
        await f.write(content)

def extract_form_data(html_obj, url, form_id=None):
    form = html_obj.find("form", {"id": form_id}) if form_id else html_obj.find("form")
    if not form:
        return None, {}
    action = form.get("action", "")
    if action and not action.startswith("http"):
        action = urllib.parse.urljoin(url, action)
    inputs = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if name:
            inputs[name] = inp.get("value", "")
    return action, inputs

def extract_cookies_from_response(session, response, domain="amazon.com"):
    jar = {}
    # Get all cookies from session for the specific domain
    try:
        if hasattr(session.cookies, 'jar'):
            for cookie in session.cookies.jar:
                if cookie.name and cookie.value:
                    jar[cookie.name] = cookie.value
        else:
            jar.update(session.cookies.get_dict() or {})
    except Exception:
        pass
    
    # Add response cookies
    try:
        if hasattr(response.cookies, 'jar'):
            for cookie in response.cookies.jar:
                if cookie.name and cookie.value:
                    jar[cookie.name] = cookie.value
        else:
            jar.update(response.cookies.get_dict() or {})
    except Exception:
        pass
    
    # Process cookies
    processed = {}

    # log.info("Jar", jar)

    for k, v in jar.items():
        if not k or not v:
            continue
        if v == "-":
            continue  # Skip empty/dash cookies
        # Strip any surrounding quotes from cookie values (e.g. session-token, x-main)
        # to avoid double-quoting issues downstream
        processed[k] = v.strip('"')
    
    cookie_str = "; ".join(f"{k}={v}" for k, v in processed.items())
    return cookie_str, processed

def _has_auth_cookie(session):
    try:
        # Extraer nombres manejando tanto si son objetos con .name como si son strings directas
        names = {c.name if hasattr(c, "name") else str(c) for c in session.cookies}
    except Exception:
        try:
            names = set(session.cookies.keys())
        except Exception:
            return False

    # Real auth cookies only — session-id / x-main are set on EVERY Amazon
    # page (even logged out), so they can't prove a registration succeeded.
    auth_cookie_names = {"at-main", "sess-at-main", "sso-state-main", "session-token"}
    return bool(names & auth_cookie_names)


def _get_session_id(session, domain):
    """Return the value of the `session-id` cookie that Amazon set on the
    session (e.g. `702-6029894-4830416`). Amazon's FWCIM uses this exact value
    as the IV for the proof-of-work hash sent in metadata1 — if we send a
    different value the POW check fails and step 4 returns the aamation
    captcha page."""
    target = f"session-id"
    try:
        # 1) Direct attribute on the cookies jar
        for c in session.cookies.jar if hasattr(session.cookies, "jar") else session.cookies:
            name = getattr(c, "name", None) or (c[0] if isinstance(c, tuple) else None)
            cdomain = getattr(c, "domain", "") or ""
            if name == target and (not cdomain or cdomain.endswith(domain) or domain.endswith(cdomain.lstrip("."))):
                v = getattr(c, "value", None) or (c[1] if isinstance(c, tuple) else "")
                if v and v != "-":
                    return v
        # 2) get_dict
        d = session.cookies.get_dict() if hasattr(session.cookies, "get_dict") else {}
        for k, v in d.items():
            if k == target and v and v != "-":
                return v
    except Exception:
        pass
    return None
def _arb_from_text(text):
    for pattern in [
        r'arb=([a-zA-Z0-9_-]+)(?:">|&amp;|&|"|\s)',
        r'"arb"\s*:\s*"([a-zA-Z0-9_-]+)"',
        r"'arb'\s*:\s*'([a-zA-Z0-9_-]+)'",
        r'name=["\']arb["\'][^>]*value=["\']([^"\']+)["\']',
        r'value=["\']([^"\']+)["\'][^>]*name=["\']arb["\']',
    ]:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return None


# ── Session builder ──────────────────────────────────────────────────────────

def build_session(proxy=None, country_code="US") -> AsyncSession:
    # Per-request HTTP session: 20s timeout (vaultproxies can be slow on
    # transatlantic hops), 2 retries per request.
    session = AsyncSession(retry=2, impersonate=_IMPERSONATE, timeout=20.0)
    session.trust_env = False
    config = COUNTRY_CONFIG.get(country_code, COUNTRY_CONFIG["US"])
    accept_lang = config.get("accept_language", "en-US,en;q=0.9")
    session.headers.update({
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": _profile_ua(),
        "sec-ch-ua": _profile_sec_ch_ua(),
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "device-memory": "8",
        "downlink": "1.5",
        "dpr": "1",
        "ect": "4g",
        "rtt": "100",
        "sec-ch-device-memory": "8",
        "sec-ch-dpr": "1",
        "sec-ch-viewport-height": "803",
        "sec-ch-viewport-width": "1240",
        "viewport-width": "1240",
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;"
            "q=0.8,application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": accept_lang,
        "Priority": "u=0, i",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    })
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    return session

def _nav(referer, site="same-origin", user_action=False):
    return {
        "Referer": referer,
        "Sec-Fetch-Site": site,
        "Sec-Fetch-User": "?1" if user_action else "?0",
    }

def _post_nav(referer, domain, site="same-origin"):
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"https://www.{domain}",
        "Referer": referer,
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Site": site,
        "Sec-Fetch-User": "?1",
        "Service-Worker-Navigation-Preload": None,
    }

def _api_nav(referer, site="same-site"):
    return {
        "Referer": referer,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": site,
        "Sec-Fetch-User": None,
        "Upgrade-Insecure-Requests": None,
    }


# ── Temp-mail OTP service ─────────────────────────────────────────────────────

class TempMail:
    def __init__(self, proxy=None):
        self._client = make_provider(proxy)

    async def get_address(self):
        login, domain, email = await self._client.get_address()
        log.ok(f"Mail generado: {email} ({type(self._client).__name__})")
        return login, domain, email

    async def wait_for_code(self, login, domain, timeout=0, poll_interval=0,
                             sender_hint="amazon"):
        # OTP email delivery: poll the inbox every 0.5s, give up after 120s.
        timeout = timeout or 120.0
        poll_interval = poll_interval or 0.5
        async with log.Loader("Esperando OTP por email...") as loader:
            code = await self._client.wait_for_code(
                login, domain, timeout=timeout, poll_interval=poll_interval,
                sender_hint=sender_hint,
            )
            if code:
                log.ok(f"OTP email: {code}")
                return code
        log.error("Timeout esperando OTP email")
        return None


# ── OTP page detection ───────────────────────────────────────────────────────

async def detect_otp_page(html_obj, url):
    url_lower = url.lower()
    is_pv = "/ap/pv" in url_lower
    otp_url = any(x in url_lower for x in ("otp", "cvf", "verify", "code", "auth"))
    otp_fields = []
    for inp in html_obj.find_all("input"):
        name = (inp.get("name") or "").lower()
        typ  = (inp.get("type") or "text").lower()
        if typ == "hidden":
            continue
        if any(x in name for x in ("otp", "code", "pin", "cvf_captcha_input", "verificationcode")):
            otp_fields.append(inp.get("name"))
    page_text = html_obj.get_text().lower()
    keywords = [
        "verification code", "codigo de verificacion", "enter the otp",
        "enter the code", "we texted you", "we sent a code", "check your phone",
        "enter otp", "one-time password", "confirm your phone",
        "phone number verification", "text message",
        "we emailed you", "check your email", "sent to your email",
    ]
    otp_text = any(x in page_text for x in keywords)
    # A real OTP page always has an actual code/otp input field. Plain text
    # keywords alone are too noisy (e.g. the register form mentions "text message").
    detected = is_pv and (bool(otp_fields) or otp_text) or bool(otp_fields)
    return detected, otp_fields

# ── Add address ──────────────────────────────────────────────────────────────

async def add_address(session, first_name, last_name, phone_e164, prev_csrf, country_code, config):
    domain = config["domain"]
    addr = config["address"]

    log.step(9, "Adding Address")
    resp = await session.get(
        f"https://www.{domain}/a/addresses/add",
        params={"ref": "ya_address_book_add_post"},
        allow_redirects=True,
        headers={
            "Referer": f"https://www.{domain}/",
            "Sec-Fetch-Site": "same-origin",
            "Service-Worker-Navigation-Preload": "true",
        },
    )
    html = BeautifulSoup(resp.text, "lxml")
    csrf = bs_val(html, "csrfToken") or prev_csrf
    tok_state   = bs_val(html, "address-ui-widgets-previous-address-form-state-token")
    tok_cust    = bs_val(html, "address-ui-widgets-obfuscated-customerId")
    tok_csrf2   = bs_val(html, "address-ui-widgets-csrfToken")
    tok_load    = bs_val(html, "address-ui-widgets-form-load-start-time")
    tok_click   = bs_val(html, "address-ui-widgets-clickstream-related-request-id")
    tok_wizard  = bs_val(html, "address-ui-widgets-address-wizard-interaction-id")

    data = {
        "csrfToken": csrf,
        "addressID": "",
        "address-ui-widgets-countryCode": addr["country_code"],
        "address-ui-widgets-enterAddressFullName": f"{first_name} {last_name}",
        "address-ui-widgets-enterAddressPhoneNumber": phone_e164,
        # Use localized street name from country config instead of generic English.
        "address-ui-widgets-enterAddressLine1": (
            f"{addr['street']} {random.randint(1,999)}"
            if addr.get('street')
            else f"Street {random.randint(1,1000)} st"
        ),
        "address-ui-widgets-enterAddressLine2": "",
        "address-ui-widgets-enterAddressCity": addr["city"],
        "address-ui-widgets-enterAddressStateOrRegion": addr["state"],
        "address-ui-widgets-enterAddressPostalCode": addr["postal"],
        "address-ui-widgets-urbanization": "",
        "address-ui-widgets-previous-address-form-state-token": tok_state,
        "address-ui-widgets-use-as-my-default": "true",
        "address-ui-widgets-delivery-instructions-desktop-expander-context": (
            '{"deliveryInstructionsDisplayMode":"CDP_ONLY",'
            '"deliveryInstructionsClientName":"YourAccountAddressBook",'
            '"deliveryInstructionsDeviceType":"desktop",'
            '"deliveryInstructionsIsEditAddressFlow":"false"}'
        ),
        "address-ui-widgets-addressFormButtonText": "save",
        "address-ui-widgets-addressFormHideHeading": "true",
        "address-ui-widgets-heading-string-id": "",
        "address-ui-widgets-addressFormHideSubmitButton": "false",
        "address-ui-widgets-enableAddressDetails": "true",
        "address-ui-widgets-returnLegacyAddressID": "false",
        "address-ui-widgets-enableDeliveryInstructions": "true",
        "address-ui-widgets-enableAddressWizardInlineSuggestions": "true",
        "address-ui-widgets-enableEmailAddress": "false",
        "address-ui-widgets-enableAddressTips": "true",
        "address-ui-widgets-amazonBusinessGroupId": "",
        "address-ui-widgets-clientName": "YourAccountAddressBook",
        "address-ui-widgets-enableAddressWizardForm": "true",
        "address-ui-widgets-delivery-instructions-data": f'{{"initialCountryCode":"{addr["country_code"]}"}}',
        "address-ui-widgets-ab-delivery-instructions-data": "",
        "address-ui-widgets-address-wizard-interaction-id": tok_wizard,
        "address-ui-widgets-obfuscated-customerId": tok_cust,
        "address-ui-widgets-locationData": "",
        "address-ui-widgets-enableLatestAddressWizardForm": "false",
        "address-ui-widgets-avsSuppressSoftblock": "false",
        "address-ui-widgets-avsSuppressSuggestion": "false",
        "address-ui-widgets-csrfToken": tok_csrf2,
        "address-ui-widgets-form-load-start-time": tok_load,
        "address-ui-widgets-clickstream-related-request-id": tok_click,
        "address-ui-widgets-deliveryDestinationCity": addr["city"],
        "address-ui-widgets-deliveryDestinationNonUciPostalCode": addr["postal"],
        "address-ui-widgets-autofill-location-spinner-loading-text": "Loading",
        "address-ui-widgets-locale": "",
    }

    req_10 = await session.post(
        f"https://www.{domain}/a/addresses/add",
        data=data, params={"ref": "ya_address_book_add_post"},
        headers=_post_nav(resp.url, domain, "same-origin"),
    )

    # Amazon asks to review/confirm the address in some countries. The wording
    # varies per locale ("Review your address", "Adresse überprüfen", "Verifica",
    # "Revisar endereço"...), so detect it structurally: a re-rendered address
    # form with a submit button, instead of locale-specific text.
    html_review = BeautifulSoup(req_10.text, "lxml")
    confirm_form = html_review.find("form", {"id": re.compile(r"address-ui.*form", re.I)})
    if confirm_form is None:
        confirm_form = html_review.find("form", {"action": re.compile(r"address|save|confirm", re.I)})

    if confirm_form is not None:
        confirm_action = urllib.parse.urljoin(req_10.url, confirm_form.get("action", ""))

        confirm_data = {}
        for inp in confirm_form.find_all("input"):
            name = inp.get("name")
            if name:
                confirm_data[name] = inp.get("value", "")

        # if confirm_data:
        #     log.info("Confirmando dirección...")
        #     req_confirm = await session.post(
        #         confirm_action,
        #         data=confirm_data,
        #         headers=_post_nav(req_10.url, domain, "same-origin"),
        #     )
        #     if "address" in req_confirm.url or "Addresses" in req_confirm.text:
        #         log.ok('Dirección confirmada exitosamente!')
        #     else:
        #         log.ok('Dirección enviada (confirmación pendiente)')
        #     return req_confirm
        log.ok('Dirección procesada (sin formulario de confirmación)')
        return req_10

    if 'address' in req_10.url and 'add' not in req_10.url:
        log.ok('Direccion agregada exitosamente!')
    else:
        log.ok('Direccion procesada')

    return req_10


# ── MAIN ─────────────────────────────────────────────────────────────────────

async def create_email(country_code="US", max_attempts=None):
    """Create an account, retrying the whole flow (fresh temp-mail + fresh
    session → fresh proxy exit IP) when Amazon transiently rejects the register
    POST (e.g. the 404 rate-limit page)."""
    if max_attempts is None:
        max_attempts = 3  # registration retries per account (1 = no retry)
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            # Amazon's "We've detected unusual activity" is a transient
            # velocity flag: back off longer between attempts so the proxy pool
            # rotates to a clean exit IP before retrying.
            delay = random.uniform(2, 4) if attempt == 2 else random.uniform(20, 40)
            log.info(f"Reintento {attempt}/{max_attempts} en {delay:.0f}s (nueva IP/email)")
            await asyncio.sleep(delay)
        result = await _create_email_once(country_code)
        if result and result != "captcha":
            return result
        if result == "captcha":
            # Saltar a un backoff más largo (la IP/FP ya están quemadas).
            delay = random.uniform(20, 40)
            log.info(f"Reintento {attempt}/{max_attempts} en {delay:.0f}s (nueva IP/email)")
            await asyncio.sleep(delay)
        else:
            log.warn(f"Intento {attempt}/{max_attempts} fallido")
    return None


async def _create_email_once(country_code="US"):
    config = COUNTRY_CONFIG.get(country_code, COUNTRY_CONFIG["US"])
    domain = config["domain"]
    assoc_handle = config["assoc_handle"]
    page_id = config["page_id"]

    locale = config["faker_locale"]
    faker_instance = _FAKERS.get(locale)
    if faker_instance is None:
        faker_instance = Faker(locale)
        _FAKERS[locale] = faker_instance

    first_name = faker_instance.first_name()
    last_name  = faker_instance.last_name()
    # Usando secrets.randbelow en lugar de random.randint
    rand_num = secrets.randbelow(9000) + 1000  # Equivalente seguro a 1000-9999
    uuid_part = uuid.uuid4().hex[:8]

    password = f"@Osiris{rand_num}{uuid_part}"

    log.info("Country", f"{country_code} - {domain}")
    t0 = time.time()

    # Get a temp-mail address in parallel with loading the sign-in page
    # (independent network calls — overlapping saves one round trip per account).
    temp_mail = TempMail(proxy=None)
    mail_task = asyncio.create_task(temp_mail.get_address())

    session = build_session(proxy=_PROXY_URL, country_code=country_code)

    try:
        r_fresh = await session.get(
            f"https://www.{domain}/ap/signin",
            params={
                "openid.return_to": f"https://www.{domain}/?ref_=nav_ya_signin",
                "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
                "openid.assoc_handle": assoc_handle,
                "openid.mode": "checkid_setup",
                "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
                "openid.ns": "http://specs.openid.net/auth/2.0",
            },
            headers={
                "Referer": f"https://www.{domain}/",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Service-Worker-Navigation-Preload": "true",
            },
        )
    except BaseException:
        # Don't leave the temp-mail fetch running if the sign-in page fails.
        mail_task.cancel()
        raise
    signin_html = r_fresh.text
    signin_url  = r_fresh.url
    t_signin    = time.time()
    arb_token   = _arb_from_text(signin_html)
    signin_soup = BeautifulSoup(signin_html, "lxml")
    # Collect the temp-mail that was being fetched while the sign-in page loaded.
    mail_login, mail_domain, email_address = await mail_task
    _tick(t0, "email")

    anti_csrf_token = bs_val(signin_soup, "anti-csrftoken-a2z")
    signin_webauthn_arb = bs_val(signin_soup, "webAuthnGetArbForAutofill", default="")
    signin_webauthn_params = bs_val(signin_soup, "webAuthnGetParametersForAutofill", default="")
    signin_webauthn_challenge = bs_val(signin_soup, "webAuthnChallengeIdForAutofill", default="")
    log.info("arb_token", arb_token)
    log.step(1, "Sign-In Page Loaded")
    _tick(t0, "signin")

    # Step 2 — Claim email identity
    log.step(2, "Claiming email identity")
    claim_dwell_ms = int((time.time() - t_signin) * 1000)
    claim_fp = generate_metadata1(
        email=email_address,
        user_agent=_UA,
        location=signin_url,
        html_b64=base64.b64encode(signin_html.encode()).decode(),
        dwell_ms=claim_dwell_ms,
    )
    claim_metadata1 = claim_fp["metadata1"]

    claim_params = {
        "openid.assoc_handle": assoc_handle,
        "openid.mode": "checkid_setup",
        "policy_handle": "Retail-Checkout",
        "openid.return_to": f"https://www.{domain}/?ref_=nav_ya_signin",
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "arb": arb_token,
    }
    claim_data = {
        "appAction": "SIGNIN_CLAIM_COLLECT",
        "subPageType": "FullPageUnifiedClaimCollect",
        "claimCollectionWorkflow": "unified",
        "metadata1": claim_metadata1,
        "claimType": "",
        "countryCode": "",
        "isServerSideRouting": "true",
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": f"https://www.{domain}/?ref_=nav_ya_signin",
        "openid.assoc_handle": assoc_handle,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        "signalUnknownCredentialUnifiedAuthWeblabActive": bs_val(
            signin_soup, "signalUnknownCredentialUnifiedAuthWeblabActive",
            default="true",
        ),
        "anti-csrftoken-a2z": anti_csrf_token,
        "ue_back": "1",
        "email": email_address,
    }
    if signin_webauthn_arb:
        claim_data["webAuthnGetArbForAutofill"] = signin_webauthn_arb
    if signin_webauthn_params:
        claim_data["webAuthnGetParametersForAutofill"] = signin_webauthn_params
    if signin_webauthn_challenge:
        claim_data["webAuthnChallengeIdForAutofill"] = signin_webauthn_challenge

    req_2 = await session.post(
        f"https://www.{domain}/ax/claim",
        params=claim_params, data=claim_data,
        headers=_post_nav(signin_url, domain, "same-origin"),
    )

    html_2    = BeautifulSoup(req_2.text, "lxml")
    arb_token = bs_val(html_2, "arb") or _arb_from_text(req_2.text)
    _tick(t0, "claim")

    # Some regions (DE, etc.) redirect directly to register page from step 2
    if not arb_token and "ap/register" in req_2.url:
        arb_from_url = re.search(r'arb=([^&]+)', req_2.url)
        if arb_from_url:
            arb_token = arb_from_url.group(1)
            log.info("arb (from redirect)", arb_token)
            # Already on register page, skip step 3
            html_3 = html_2
            t_reg  = time.time()
            app_action_token = bs_val(html_3, "appActionToken")
            return_to_token  = bs_val(html_3, "openid.return_to")
            prev_rdi_token   = bs_val(html_3, "prevRID")
            workflowState    = bs_val(html_3, "workflowState")
            csrf_token       = bs_val(html_3, "anti-csrftoken-a2z")
            change_claim_url = bs_val(html_3, "changeClaimUrl")
            log.info("appActionToken", app_action_token)
            _tick(t0, "reg_page")
            
            # Extract reg_params from URL
            parsed = urllib.parse.urlparse(req_2.url)
            reg_params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
            
            # Skip to step 4 (fingerprint + register submission)
            req_3 = req_2
            skip_to_register = True
        else:
            log.error("arb_token no en step_2 — ver step_2.html")
            log.info("Status", str(req_2.status_code))
            return
    elif not arb_token:
        log.error("arb_token no en step_2 — ver step_2.html")
        log.info("Status", str(req_2.status_code))
        return
    else:
        skip_to_register = False

    if not skip_to_register:
        # Some regions (DE, etc.) show an "intent confirmation" page before register
        intent_form = html_2.find("form", {"id": "intent-confirmation-form"})
        if intent_form:
            log.info("Intent confirmation form detected, submitting...")
            intent_action = intent_form.get("action", "").replace("&amp;", "&")
            intent_data = {}
            for inp in intent_form.find_all("input"):
                name = inp.get("name")
                if name:
                    intent_data[name] = inp.get("value", "")
            if intent_action and intent_data:
                req_intent = await session.post(
                    intent_action,
                    data=intent_data,
                    headers=_post_nav(req_2.url, domain, "same-origin"),
                )
                html_2 = BeautifulSoup(req_intent.text, "lxml")
                arb_token = bs_val(html_2, "arb") or _arb_from_text(req_intent.text)

        anti_csrf_token = bs_val(html_2, "anti-csrftoken-a2z")
        create_url_raw  = find_between(req_2.text, ' action="', '"') or ""
        if not create_url_raw:
            form_el = html_2.find("form")
            if form_el:
                create_url_raw = form_el.get("action", "")
        create_url_raw = create_url_raw.replace("&amp;", "&")
        create_url = urllib.parse.unquote(create_url_raw)
        new_url = (
            find_between(create_url, "openid.return_to=", "&policy_handle")
            or find_between(create_url, "openid.return_to=", "&openid.ns")
            or f"https://www.{domain}/"
        )
        log.info("arb (step2)", arb_token)
        log.info("new_url", new_url)

        # Step 3 — Load register page
        log.step(3, "Loading Register Page")
        reg_params = {
            "openid.mode": "checkid_setup",
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.ns.pape": "http://specs.openid.net/extensions/pape/1.0",
            "showRememberMe": "true",
            "openid.pape.max_auth_age": "900",
            "pageId": page_id,
            "prepopulatedLoginId": "",
            "openid.assoc_handle": assoc_handle,
            "openid.return_to": new_url,
            "policy_handle": "Retail-Checkout",
        }
        req_3 = await session.post(
            f"https://www.{domain}/ap/register",
            params=reg_params,
            data={
                "claimCollectionLayoutType": "unifiedAuthClaimCollection",
                "unifiedAuthTreatment": "",
                "email": email_address,
                "arb": arb_token,
                "csrf-token": anti_csrf_token,
            },
            headers=_post_nav(req_2.url, domain, "same-origin"),
        )

        html_3           = BeautifulSoup(req_3.text, "lxml")
        t_reg            = time.time()
        app_action_token = bs_val(html_3, "appActionToken")
        return_to_token  = bs_val(html_3, "openid.return_to")
        prev_rdi_token   = bs_val(html_3, "prevRID")
        workflowState    = bs_val(html_3, "workflowState")
        csrf_token       = bs_val(html_3, "anti-csrftoken-a2z")
        change_claim_url = bs_val(html_3, "changeClaimUrl")
        log.info("appActionToken", app_action_token)
        _tick(t0, "reg_page")

    # Fingerprint
    reg_dwell_ms = int((time.time() - t_reg) * 1000)
    # FWCIM uses the real `session-id` cookie as the POW IV — if we send a
    # random IV the server-side check fails and step 4 returns the captcha
    # page. Pull the cookie that Amazon set on /ap/register.
    pow_session_id = _get_session_id(session, domain)
    log.info("pow iv (session-id)", pow_session_id or "<missing>")
    fp_result = generate_metadata1(
        email=email_address,
        password=password,
        name=f"{first_name} {last_name}",
        password_check=password,
        user_agent=_profile_ua(),
        location=req_3.url,
        html_b64=base64.b64encode(req_3.text.encode()).decode(),
        dwell_ms=reg_dwell_ms,
        session_id=pow_session_id,
    )
    fp_amz       = fp_result["metadata1"]
    reg_key_id   = REGION_KEYS.get(country_code, REGION_KEYS["US"])["keyId"]
    pwd_context  = {"appActionToken": app_action_token, "si:md5": reg_key_id}
    encrypted_pwd = encrypt_password(password, region=country_code, encryption_context=pwd_context)
    re_pwd        = encrypt_password(password, region=country_code, encryption_context=pwd_context)

    # Step 4 — Submit registration
    log.step(4, "Sending Register Data")
    reg_post_data = {
        "appActionToken": app_action_token,
        "appAction": "REGISTER",
        "openid.return_to": return_to_token,
        "prevRID": prev_rdi_token,
        "workflowState": workflowState,
        "anti-csrftoken-a2z": csrf_token,
        "claimCollectionLayoutType": "unifiedAuthClaimCollection",
        "unifiedAuthTreatment": "",
        "email": email_address,
    }
    if change_claim_url:
        reg_post_data["changeClaimUrl"] = change_claim_url
    reg_post_data["customerName"] = f"{first_name} {last_name}"
    if country_code == "JP":
        reg_post_data["customerNamePronunciation"] = f"{first_name} {last_name}"
    reg_post_data["encryptedPwd"] = encrypted_pwd
    reg_post_data["encryptedPwdCheck"] = re_pwd
    reg_post_data["metadata1"] = fp_amz
    req_4 = await session.post(
        f"https://www.{domain}/ap/register",
        data=reg_post_data,
        headers=_post_nav(req_3.url, domain, "same-origin"),
    )

    has_captcha = (
        "cvf-aamation-challenge-form" in req_4.text
        or ("clientContext" in req_4.text and "verifyToken" in req_4.text)
    )

    req_after = req_4
    _tick(t0, "register_post")
    if not has_captcha:
        log.ok("Sin captcha — registro directo")
    else:
        try:
            with open("output/debug_step4_captcha.html", "w", encoding="utf-8") as df:
                df.write(req_4.text)
        except Exception:
            pass
        # Si llegamos aquí con un fingerprint correcto, el server aún así
        # devolvió un challenge. Marcamos para retry con nueva IP/email.
        log.warn("Captcha detectado — se reintentará con nueva IP")
        return "captcha"

    # If Amazon re-rendered the register form, the REGISTER POST was rejected.
    if 'id="ap_register_form"' in req_after.text or "auth-error-message-box" in req_after.text:
        m = re.search(r'auth-error-message-box[^>]*>(.*?)</div>', req_after.text, re.S)
        err = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip() if m else "Unknown error"
        log.error(f"Registro rechazado por Amazon: {err[:200]}")
        return

    # A silent rejection comes back as the plain sign-in page (no OTP, no form
    # re-render). Catch it here so we don't burn a retry on a dead attempt and
    # so we can inspect what Amazon actually returned.
    if not _has_auth_cookie(session):
        lower_url = req_after.url.lower()
        if 'id="ap_signin_form"' in req_after.text or "/ap/signin" in lower_url:
            log.error("Registro rechazado: Amazon devolvió al login (IP/proxy marcado) — ver output/debug_silent_reject.html")
            # await save("output/debug_silent_reject.html", req_after.text)
            return

    # Step 8 — OTP (email)
    log.step(8, "OTP Check")
    h8 = BeautifulSoup(req_after.text, "lxml")
    is_otp, otp_fields = await detect_otp_page(h8, req_after.url)

    if is_otp:
        # await save("output/debug_otp.html", req_after.text)
        t_otp = time.time()
        is_phone_page = "/ap/pv" in req_after.url.lower()
        if is_phone_page:
            log.error("Verificación por teléfono (SMS) requerida — no hay integración SMS, descartando")
            return
        log.info("OTP page detectado (email)")
        form_action, form_inputs = extract_form_data(h8, req_after.url, "auth-pv-form")
        if not form_action:
            form_action, form_inputs = extract_form_data(h8, req_after.url)
        if not otp_fields:
            for inp in h8.find_all("input"):
                nm  = inp.get("name") or ""
                typ = (inp.get("type") or "text").lower()
                if typ != "hidden" and nm:
                    otp_fields.append(nm)

        otp_code = await temp_mail.wait_for_code(mail_login, mail_domain)
        if otp_code is None:
            log.error("No OTP recibido por email")
            return

        # Human reads the email and types the code — dwell includes the wait.
        otp_dwell_ms = int((time.time() - t_otp) * 1000)
        res_otp = generate_metadata1(
            otp=otp_code, user_agent=_UA,
            location=req_after.url,
            html_b64=base64.b64encode(req_after.text.encode()).decode(),
            dwell_ms=otp_dwell_ms,
        )

        otp_data = form_inputs.copy()
        for field in otp_fields:
            otp_data[field] = otp_code
        new_csrf = bs_val(h8, "anti-csrftoken-a2z")
        if new_csrf:
            otp_data["anti-csrftoken-a2z"] = new_csrf
        otp_data["metadata1"] = res_otp["metadata1"]

        async with log.Loader("Enviando OTP..."):
            req_8 = await session.post(
                form_action, data=otp_data,
                headers=_post_nav(req_after.url, domain, "same-origin"),allow_redirects=True
            )
            # with open("output/debug_otp_submit.html", "w", encoding="utf-8") as f:
            #     f.write(req_8.text)
            cookie_dict = {}
            for c in session.cookies:
                if hasattr(c, "name") and hasattr(c, "value"):
                    cookie_dict[c.name] = c.value
                else:
                    # Si session.cookies almacena los pares directamente o como tuplas/strings
                    name = getattr(c, "name", str(c))
                    value = session.cookies.get(name, "") if hasattr(session.cookies, "get") else ""
                    cookie_dict[name] = value
        log.step(8, "OTP Sent")
        req_after = req_8
        # with open("output/debug_otp_url.html", "w", encoding="utf-8") as f:
        #     f.write(req_8.text)

        _tick(t0, "otp_submit")
    else:
        log.ok("Sin OTP requerido")

    # Registration only counts once Amazon has actually logged us in (auth
    # cookies). Without this, a failed/rejected register POST that happens to
    # contain none of the error markers would be saved as a bogus "account".
    if not _has_auth_cookie(session):
        log.error("Registro no autenticado (sin cookies de sesión) — descartando")
        return

    # Add address
    phone_digits = random.randint(
        10 ** (config["phone_digits"][0] - 1),
        10 ** config["phone_digits"][0] - 1
    )
    fake_phone = f"{config['phone_prefix']}{phone_digits}"
    req_10 = await add_address(session, first_name, last_name, fake_phone, "", country_code, config)
    _tick(t0, "address")

    cookie_str, cookies = extract_cookies_from_response(session, req_10, domain)

    log.result_card(email_address, password, country_code, domain, len(cookie_str))

    result_data = {
        "email": email_address,
        "password": password,
        "name": f"{first_name} {last_name}",
        "cookies": cookies,
        "cookie_str": cookie_str,
        "country": country_code,
        "domain": domain,
    }

    os.makedirs("output", exist_ok=True)
    async with aiofiles.open(f"output/account_{mail_login}.json", "w") as f:
        await f.write(json.dumps(result_data, indent=2, ensure_ascii=False))

    log.ok(f"Saved: output/account_{mail_login}.json")
    return _build_account(result_data)


async def create_account(country_code="US"):
    result = await create_email(country_code)
    if isinstance(result, Account):
        return result
    return None


async def initialize():
    import time as _time
    

    log.banner()
    country_code = log.select_country()
    count = log.ask_count()

    config = COUNTRY_CONFIG[country_code]
    log.highlight("Target", f"amazon{config['tld']}")

    created = 0
    failed = 0

    start = _time.time()
    for i in range(count):
        log.step(f"{i+1}/{count}", config['domain'])
        try:
            result = await create_email(country_code)
            if isinstance(result, Account):
                created += 1
            else:
                failed += 1
        except KeyboardInterrupt:
            raise
        except Exception as e:
            failed += 1
            log.fail(str(e)[:80])

        if i < count - 1:
            try:
                # Wait 1.0–2.5s between accounts to avoid velocity limits.
                delay = random.uniform(1.0, 2.5)
                log.info("Next in", f"{delay:.0f}s")
                await asyncio.sleep(delay)
            except KeyboardInterrupt:
                raise

    elapsed = _time.time() - start
    log.summary(created, failed, elapsed)


# ── Cookie generation for CLI/PHP integration ────────────────────────────────

async def generate_account_cookie(country_code="SA"):
    """Create one account and return the cookie_str. Used by us.php via CLI."""
    result = await create_email(country_code)
    if isinstance(result, Account):
        return result.cookie
    return None


def _cli_generate_cookie():
    """CLI entry point: python amazon_v2.py --cookie <COUNTRY_CODE>
    Prints the cookie string to stdout for PHP shell_exec() to capture."""
    import sys
    country = sys.argv[2] if len(sys.argv) > 2 else "SA"
    cookie = asyncio.run(generate_account_cookie(country))
    if cookie:
        print(cookie)
    else:
        print("", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "--cookie":
        _cli_generate_cookie()
    else:
        try:
            asyncio.run(initialize())
        except KeyboardInterrupt:
            print()
        except SystemExit:
            pass

"""Per-country configuration and shared constants for the Amazon pipeline.

This module is the single source of truth for every country-specific
value the flow depends on:

* :data:`BROWSER_PROFILES` — coherent (TLS / User-Agent / sec-ch-ua)
  triples so every request matches the same declared Chrome version.
* :data:`COUNTRY_CONFIG` — 18 marketplaces with domain, assoc handle,
  locale, accept-language, timezone and faker locale.
* :data:`MANAGE_URLS` — fully-formed ``/ap/register`` URL per country,
  with the right ``openid.*`` query params for Amazon's OpenID auth.
* :data:`DOMAIN_MAP`, :data:`ASSOC_HANDLE_MAP`,
  :data:`AMAZON_COUNTRY_CODE_MAP` — flat convenience maps derived from
  :data:`COUNTRY_CONFIG`.
* :class:`AmazonRegisterError` — raised by any flow step when Amazon
  rejects the session or asks to retry.
"""

# ── Browser profiles (TLS fingerprint + UA + sec-ch-ua must all agree) ──
# Picking these three independently (old behaviour) produced mismatches
# like "TLS says Chrome 136 but UA says Chrome 124", which Amazon can
# detect by cross-checking the JA3/JA4 hash against the declared UA. Each
# entry below pins the triple together so every request is coherent.
# Per curl_cffi issue #500: chrome131/136 have known TLS extension
# mismatches (application_settings 17513 vs real Chrome's 17613).
# chrome124 has the most accurate TLS fingerprint match, so we pin
# to it exclusively until curl_cffi fixes newer versions.
BROWSER_PROFILES = [
    {
        'impersonate': 'chrome124',
        'userAgent':   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'majorVersion': '124',
        'fullVersion':  '124.0.0.0',
        'secChUa':      '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    },
]

# Legacy flat lists — kept for any caller that still imports them, but
# `buildSession` now always uses a single BROWSER_PROFILES entry so the
# UA/TLS/sec-ch-ua values stay in sync.
IMPERSONATE_BROWSERS = [profile['impersonate'] for profile in BROWSER_PROFILES]
USER_AGENTS          = [profile['userAgent']   for profile in BROWSER_PROFILES]

# ── Country config (18 marketplaces) ─────────────────────────────────
# Each entry: domain, assoc_handle (amazon's openid handle),
# amazon_country_code (form field), locale, accept_language,
# timezone_offset (CET+/-), faker_locale, email_domains (decorative —
# the account's real identity is the phone number, not this email).
#
# Restored 2026-07-22 from an earlier snapshot of this project
# (CookieGen-Sxigario-Global.zip) that supported 18 markets before the
# scope was trimmed to US/CA. Live-tested with the CURRENT pipeline
# (multi-provider SMS, mail.tm fallback, the unified
# metadataGenSxgitario.py fingerprint generator) via an 18-country batch
# run, 2026-07-22 — 5 markets were then dropped based on that run:
#   PL, TR — register POST came back "passwords don't match" on the
#     mail.tm/email channel; root cause unconfirmed (possibly a
#     per-marketplace CSE encryption key we don't have), not fixed.
#   AE, SA, IN — Amazon's own form explicitly demands "a valid mobile
#     phone number" for these marketplaces; they don't accept an
#     email-only claim at all. Not a bug — a real policy difference —
#     but incompatible with the mail.tm fallback either way, so out of
#     scope until phone-based registration is specifically validated
#     for them.
COUNTRY_CONFIG = {
    'US': {'domain': 'amazon.com',    'assoc_handle': 'usflex', 'amazon_country_code': 'US', 'locale': 'en_US', 'accept_language': 'en-US,en;q=0.9',                   'timezone_offset': -6, 'faker_locale': 'en_US', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'CA': {'domain': 'amazon.ca',     'assoc_handle': 'caflex', 'amazon_country_code': 'CA', 'locale': 'en_CA', 'accept_language': 'en-CA,en;q=0.9,fr-CA;q=0.8',        'timezone_offset': -5, 'faker_locale': 'en_CA', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'MX': {'domain': 'amazon.com.mx', 'assoc_handle': 'mxflex', 'amazon_country_code': 'MX', 'locale': 'es_MX', 'accept_language': 'es-MX,es;q=0.9,en;q=0.8',          'timezone_offset': -6, 'faker_locale': 'es_MX', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'BR': {'domain': 'amazon.com.br', 'assoc_handle': 'brflex', 'amazon_country_code': 'BR', 'locale': 'pt_BR', 'accept_language': 'pt-BR,pt;q=0.9,en;q=0.8',          'timezone_offset': -3, 'faker_locale': 'pt_BR', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'UK': {'domain': 'amazon.co.uk',  'assoc_handle': 'gbflex', 'amazon_country_code': 'GB', 'locale': 'en_GB', 'accept_language': 'en-GB,en;q=0.9',                   'timezone_offset': 0,  'faker_locale': 'en_GB', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'DE': {'domain': 'amazon.de',     'assoc_handle': 'deflex', 'amazon_country_code': 'DE', 'locale': 'de_DE', 'accept_language': 'de-DE,de;q=0.9,en;q=0.8',          'timezone_offset': 1,  'faker_locale': 'de_DE', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'FR': {'domain': 'amazon.fr',     'assoc_handle': 'frflex', 'amazon_country_code': 'FR', 'locale': 'fr_FR', 'accept_language': 'fr-FR,fr;q=0.9,en;q=0.8',          'timezone_offset': 1,  'faker_locale': 'fr_FR', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'IT': {'domain': 'amazon.it',     'assoc_handle': 'itflex', 'amazon_country_code': 'IT', 'locale': 'it_IT', 'accept_language': 'it-IT,it;q=0.9,en;q=0.8',          'timezone_offset': 1,  'faker_locale': 'it_IT', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'ES': {'domain': 'amazon.es',     'assoc_handle': 'esflex', 'amazon_country_code': 'ES', 'locale': 'es_ES', 'accept_language': 'es-ES,es;q=0.9,en;q=0.8',          'timezone_offset': 1,  'faker_locale': 'es_ES', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'NL': {'domain': 'amazon.nl',     'assoc_handle': 'nlflex', 'amazon_country_code': 'NL', 'locale': 'nl_NL', 'accept_language': 'nl-NL,nl;q=0.9,en;q=0.8',          'timezone_offset': 1,  'faker_locale': 'nl_NL', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'SG': {'domain': 'amazon.sg',     'assoc_handle': 'sgflex', 'amazon_country_code': 'SG', 'locale': 'en_SG', 'accept_language': 'en-SG,en;q=0.9',                   'timezone_offset': 8,  'faker_locale': 'en_US', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'AU': {'domain': 'amazon.com.au', 'assoc_handle': 'auflex', 'amazon_country_code': 'AU', 'locale': 'en_AU', 'accept_language': 'en-AU,en;q=0.9',                   'timezone_offset': 10, 'faker_locale': 'en_AU', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
    'JP': {'domain': 'amazon.co.jp',  'assoc_handle': 'jpflex', 'amazon_country_code': 'JP', 'locale': 'ja_JP', 'accept_language': 'ja-JP,ja;q=0.9,en;q=0.8',          'timezone_offset': 9,  'faker_locale': 'ja_JP', 'email_domains': ('gmail.com', 'outlook.com', 'hotmail.com')},
}

# ── Derived legacy maps (kept for compatibility) ────────────────────
countrys_supported      = list(COUNTRY_CONFIG.keys())
COUNTRY_MAP             = {k: k for k in COUNTRY_CONFIG}
DOMAIN_MAP              = {k: v['domain']              for k, v in COUNTRY_CONFIG.items()}
ASSOC_HANDLE_MAP        = {k: v['assoc_handle']        for k, v in COUNTRY_CONFIG.items()}
AMAZON_COUNTRY_CODE_MAP = {k: v['amazon_country_code'] for k, v in COUNTRY_CONFIG.items()}


def _build_manage_url(country_code: str) -> str:
    """Build the fully-formed Amazon ``/ap/register`` URL for a country.

    Assembles the OpenID checkid_setup parameters (``assoc_handle``,
    ``return_to``, etc.) using the country's domain and handle so the
    registration flow lands on the right marketplace with the right
    post-auth redirect.

    Args:
        country_code: ISO code from :data:`COUNTRY_CONFIG`.

    Returns:
        Full HTTPS URL to ``/ap/register`` with all OpenID params.
    """
    cfg = COUNTRY_CONFIG[country_code]
    domain = cfg['domain']
    handle = cfg['assoc_handle']
    return (
        f"https://www.{domain}/ap/register"
        f"?openid.pape.max_auth_age=0"
        f"&openid.return_to=https%3A%2F%2Fwww.{domain.replace('.', '%2E')}%2F%3F_encoding%3DUTF8%26ref_%3Dnav_newcust"
        f"&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
        f"&openid.assoc_handle={handle}"
        f"&openid.mode=checkid_setup"
        f"&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
        f"&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
    )

MANAGE_URLS = {k: _build_manage_url(k) for k in COUNTRY_CONFIG}


# ── CSE (client-side encryption) regional key material ──────────────
# Amazon's password-encryption public key is NOT global — it's one of
# three regional "SiegeCrypto" profiles served from
# static.siege-amazon.com/prod/profiles/AuthenticationPortalSignin{NA,EU,FE}.js.
# Confirmed live 2026-07-23 via Playwright capture against all 13
# marketplaces' real /ap/register submissions: US/CA/MX/BR carry the NA
# keyId, UK/DE/FR/IT/ES/NL carry a DIFFERENT EU keyId, SG/AU/JP carry a
# third FE (Far East) keyId. Every marketplace we support was previously
# encrypted with the NA key regardless of region — correct only for the
# 4 NA countries; wrong key material entirely for the other 9.
CSE_PROFILES = {
    'NA': {
        'keyId': '973900addb061fbe5bb4ea871e9d8161',
        'jwkN':  'rwLCVK_8hcUgil9KQiN7RbtmcJV5Pt12CwbhZ1h9fvdbVRILCanjv2RNSW9l-Mq0fnRq6DLTLzX3J3TuVCZQ1wjfa-Ef1BDeXnVNaY4q0Vvl2e1e9UF-uwyK5mDyiftlPt5JcsRuFXU1dMSb5TwDiFV1UlGOc-db33zi1MlmrL5L7iyfqBQmlEoa5el5pFbmeK2wSOKBZtJja-dbVzde0jrpGlVhHDZOAlH7g8aTftqwHLVP27T9Pr0UJtaj9LIX-sg_K9-Pl7H2W9BJDTJLJi_EAAqBHTrRueejO3XbEuSGrsrphCk0ZlYqoLkobey-kubWTba5kzsWL-huF--tzQ',
    },
    'EU': {
        'keyId': '8c3749c7577cfbe8de80ec2d8e03f35c',
        'jwkN':  '7MBo_ZCPa0E3BnEXiLK0zhb9fZwQVrkkCPEBuf9HVq_-uEnER6cZBu7BABkLvvvFQnPYaxvjyQ3vAhJsdQUkHVb6spDOJsDLq3xQnzPr5T41PxXgMVPlrEWtjT2eB3ENU5gf-gtwCAm6JZMzzMr4k41aehnfikRtEdAKewUZm0KbrS0gcWCKnBxrkAWiOHUEZaL0IWH45sU_ul6y9Ej2w8xl1Nm8KOvt3FV_uF8OXj2icLLHMlUTlYDbC3xSLNahTXoh0Dao5ihk6kf_Wxv_d2h_ftx0MWuPVmVMASYCY9YGErKQ182exEaWta0I_Eva-omXyYxoKxneN9LdZYw-NQ',
    },
    'FE': {
        'keyId': 'e7696039e9f2aed1c5c0d34eb95a3cd4',
        'jwkN':  'oez6pTbcxFW1_fdZyYWlQonAop33Yv9BK4b_f21ttSmSe7TmjPN2mqXsUpFoTpwcVJ3akIu3cExnkjV_juIoj0u7V8CvrkCZjRVWYSwuBdGmNKx3p8fsmHBkqvMXjcSrhFZAWI7_GFLo66DATzpJu5TVWbzkGS95nNL-YCsr8OUxy08o7Wp7oiujLGGdI7RtcYXXe1SchC5cMj3g8nfhDGuFui6hgEoDzg_fgypshbKsybaesCLyxNFqQbiH24_T8nSuOYVGui23Td8sKFJoTqEq14JYp-GDAn88IMUErUS4NdxL4FJPPEXV6SMsH5P0MDOrGu8TYpsgV0YRTT0ZBw',
    },
}

CSE_COUNTRY_REGION = {
    'US': 'NA', 'CA': 'NA', 'MX': 'NA', 'BR': 'NA',
    'GB': 'EU', 'DE': 'EU', 'FR': 'EU', 'IT': 'EU', 'ES': 'EU', 'NL': 'EU',
    'SG': 'FE', 'AU': 'FE', 'JP': 'FE',
}


def cseProfileFor(amazonCountryCode: str) -> dict:
    """Look up the CSE (jwkN, keyId) pair for an Amazon 2-letter country code.

    Args:
        amazonCountryCode: Value from :data:`AMAZON_COUNTRY_CODE_MAP`
            (e.g. ``'GB'`` for UK, ``'US'`` for US).

    Returns:
        The matching entry from :data:`CSE_PROFILES`. Falls back to
        ``'NA'`` for any code not in :data:`CSE_COUNTRY_REGION`.
    """
    region = CSE_COUNTRY_REGION.get((amazonCountryCode or '').upper(), 'NA')
    return CSE_PROFILES[region]


class AmazonRegisterError(Exception):
    """Signal that a registration step failed and a retry may help.

    Raised by every step in :mod:`amazon.flow` when Amazon's response
    indicates a recoverable problem. The exception *message* is also the
    retry discriminator used by :meth:`main.AmazonAccountCreator.processRegistration`:

    * ``"unusual activity"`` — the session was flagged. The retry handler
      regenerates the fake profile and waits before retrying.
    * ``"number_associated"`` — the phone is tied to another account /
      marketplace. Retry with a fresh number.
    * ``"sms_timeout"`` — the SMS provider didn't deliver the OTP in time.
      Retry with a fresh number (cap of 1).
    * ``"sms_blocked"`` — Amazon explicitly refused SMS delivery for this
      number (hideSendOtpOverSms=true override failed). Retry with a
      fresh number.
    * ``"solver_not_provided"`` — a captcha appeared but no CapSolver key is
      configured. Retry with a fresh number.
    * ``"no_arb"`` — the claim step returned no intent-confirmation
      token. Usually a WAF cookie or captcha on the claim step.
    * ``"no_register_form"`` / ``"unexpected_response"`` — registration
      POST landed on a page we can't parse.
    * ``"captcha_failed"`` — captcha loop exhausted after 8 attempts.
    """
    pass

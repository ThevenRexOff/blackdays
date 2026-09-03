"""Cookie region converter.

Takes a cookie string minted on one Amazon marketplace and rewrites the
region-specific markers (auth-cookie suffix, currency, locale) so the same
session can be presented against another marketplace — without having to
re-register. Ported from the "Jill" fork.
"""

import re


class CookieConverter:

    # suffix   -> the "-acbXX" tail Amazon appends to auth cookies (at-acbmx, sess-at-acbmx, ...)
    # currency -> value of the i18n-prefs cookie
    # locale   -> value of the lc-acbXX cookie
    REGIONS = {
        'US': {'suffix': 'main',  'currency': 'USD', 'locale': 'en_US', 'domain': 'amazon.com'},
        'CA': {'suffix': 'acbca', 'currency': 'CAD', 'locale': 'en_CA', 'domain': 'amazon.ca'},
        'MX': {'suffix': 'acbmx', 'currency': 'MXN', 'locale': 'es_MX', 'domain': 'amazon.com.mx'},
        'UK': {'suffix': 'acbuk', 'currency': 'GBP', 'locale': 'en_GB', 'domain': 'amazon.co.uk'},
        'FR': {'suffix': 'acbfr', 'currency': 'EUR', 'locale': 'fr_FR', 'domain': 'amazon.fr'},
        'IT': {'suffix': 'acbit', 'currency': 'EUR', 'locale': 'it_IT', 'domain': 'amazon.it'},
        'ES': {'suffix': 'acbes', 'currency': 'EUR', 'locale': 'es_ES', 'domain': 'amazon.es'},
        'AU': {'suffix': 'acbau', 'currency': 'AUD', 'locale': 'en_AU', 'domain': 'amazon.com.au'},
    }

    _ALL_SUFFIXES = {v['suffix'] for v in REGIONS.values()}

    @classmethod
    def detect_region(cls, cookie_text: str) -> str | None:
        """Return the region code the cookie string was minted on, or None."""
        for code, cfg in cls.REGIONS.items():
            if f"-{cfg['suffix']}" in cookie_text:
                return code
        return None

    @classmethod
    def convert(cls, cookie_text: str, target_region: str) -> str:
        """Rewrite ``cookie_text`` to look like a ``target_region`` session.

        No-op if the target is unknown, the source can't be detected, or the
        cookie is already in the target region.
        """
        target_region = target_region.upper()
        if target_region not in cls.REGIONS:
            return cookie_text

        source = cls.detect_region(cookie_text)
        if not source or source == target_region:
            return cookie_text

        src = cls.REGIONS[source]
        dst = cls.REGIONS[target_region]

        out = cookie_text

        # -acbca  -> -acbmx  (auth cookie suffix, hyphen-prefixed form)
        out = re.sub(rf'-{re.escape(src["suffix"])}\b', f'-{dst["suffix"]}', out)
        # bare suffix token (e.g. cookie *value* references)
        out = re.sub(rf'\b{re.escape(src["suffix"])}\b', dst['suffix'], out)
        # i18n-prefs=CAD -> i18n-prefs=MXN
        out = re.sub(rf'(i18n-prefs=){re.escape(src["currency"])}', rf'\1{dst["currency"]}', out)
        # lc-acbXX locale value  en_CA -> es_MX
        out = re.sub(re.escape(src['locale']), dst['locale'], out)

        return out

    @classmethod
    def convert_all(cls, cookie_text: str) -> dict[str, str]:
        """Return the cookie converted to every supported region."""
        return {code: cls.convert(cookie_text, code) for code in cls.REGIONS}

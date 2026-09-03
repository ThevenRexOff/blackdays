"""AmazonAccountCreator — synchronous wrapper over the async amazon_v2 engine.

The upstream generator (amazon_v2.py) is async, uses chrome142 TLS, and
returns an `Account` object. The rest of the backend expects a synchronous
`AmazonAccountCreator(...).processRegistration() -> dict` shape, so this module
adapts the two: it configures the proxy, runs one registration inside a fresh
event loop, and flattens the result into the dict contract used by
`cookiegen.py` / `apis/tools.py`.

Supported countries mirror amazon_v2.COUNTRY_CONFIG.
"""

import asyncio
import os
import time

import amazon_v2


class AmazonAccountCreator:
    """Synchronous facade over amazon_v2.create_email().

    Keeps the constructor signature (`country`, `proxy`, `verbose`,
    `clearScreen`, `mailDomains`) so `Commands/Tools/cookiegen.py` can keep
    calling it unchanged.
    """

    def __init__(self, country: str = "US", proxy: str = None,
                 verbose: bool = True, clearScreen: bool = True,
                 mailDomains: list = None,
                 gmailUser: str = None, gmailPass: str = None) -> None:
        if country not in amazon_v2.COUNTRY_CONFIG:
            raise ValueError(
                f"Country '{country}' is not supported. Use: "
                f"{', '.join(amazon_v2.COUNTRY_CONFIG.keys())}"
            )
        self.targetCountry = country
        self.proxy = proxy
        self.mailDomains = list(mailDomains) if mailDomains else None
        self.verbose = verbose

    #//! -------------------- Public entry point -------------------- !\\#
    def processRegistration(self, retry: int = 0) -> dict:
        initTime = time.time()

        # The async engine reads its proxy from this module-level var.
        amazon_v2._PROXY_URL = self.proxy

        try:
            account = asyncio.run(amazon_v2.create_email(self.targetCountry))
        except Exception as e:
            return {"status": False, "message": f"{type(e).__name__}: {e}"}

        if not isinstance(account, amazon_v2.Account):
            return {"status": False, "message": "Amazon rechazó el registro (posible captcha, cookie no generada) — intenta con otro país o proxy"}

        cookie_str = account.cookie or ""
        cookie_dict = self._parse_cookie(cookie_str)

        result = {
            "status":               True,
            "profile":              {
                "name":     account.name or "",
                "email":    account.email or "",
                "password": account.password or "",
            },
            "message":              "Account created successfully.",
            "billingAddressStatus": None,
            "billingMessage":       "",
            "cookies":              cookie_str,
            "cookie_dict":          cookie_dict,
            "time_taken":           time.time() - initTime,
            "retries":              retry,
        }
        return result

    @staticmethod
    def _parse_cookie(cookie_str: str) -> dict:
        """Break a 'name=value; name2=value2' cookie header into a dict."""
        parsed = {}
        if not cookie_str:
            return parsed
        for part in cookie_str.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            name, _, value = part.partition("=")
            name = name.strip()
            if name:
                parsed[name] = value
        return parsed

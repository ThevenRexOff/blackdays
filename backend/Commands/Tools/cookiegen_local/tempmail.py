import asyncio
import random
import re

from curl_cffi import AsyncSession


class FmailProvider:
    """
    Disposable inbox via fmail.men
    """

    BASE = "https://fmail.men/v1"
    # Verified against the API: iopia.org and kojoball.email silently fall back
    # to fmail.men, so only the two domains below actually work. Rotating keeps
    # accounts off a single (likely Amazon-flagged) domain.
    WHITELIST_DOMAINS = [
        "fmail.men", "guns.lat", "exolinker.com", "uncmail.org",
        "brodilla.email", "corpmail.club", "emailab.xyz", "emailawb.pro",
        "emailfoxi.pro", "emailvb.pro", "emailxo.pro", "heroclash.info",
        "safehouse.quest", "tempmailonline.co", "aquaflask.click",
        "canicasbrawl.com", "deislerlive.com", "kuruptd.ink",
        "ougoods.com", "sevril.win", "gootsijs.com", "fs6.baby",
    ]
    _last_domain = None

    def __init__(self, proxy=None):
        self._session = AsyncSession(impersonate="chrome131", timeout=10)
        if proxy:
            self._session.proxies = {"http": proxy, "https": proxy}

    async def _get_json(self, path, **params):
        last_exc = None
        for attempt in range(3):
            try:
                r = await self._session.get(f"{self.BASE}{path}", params=params)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_exc = e
                await asyncio.sleep(0.15 * (attempt + 1))
        raise last_exc

    async def get_address(self, domain=None):
        if domain is None:
            candidates = self.WHITELIST_DOMAINS[:]
            if self._last_domain in candidates:
                candidates.remove(self._last_domain)
            domain = random.choice(candidates)
        self._last_domain = domain
        data = await self._get_json("/random", domain=domain)
        return data["username"], data["domain"], data["address"]

    async def wait_for_code(self, login, domain, timeout=180, poll_interval=3,
                            sender_hint="amazon"):
        deadline = asyncio.get_event_loop().time() + timeout
        seen = set()
        while asyncio.get_event_loop().time() < deadline:
            try:
                inbox = await self._get_json(f"/inbox/{login}", domain=domain)
                for em in inbox.get("emails", []):
                    token = em.get("token")
                    if not token or token in seen:
                        continue
                    seen.add(token)
                    sender = (em.get("sender") or "").lower()
                    subject = (em.get("subject") or "").lower()
                    if sender_hint in sender or sender_hint in subject:
                        full = await self._get_json(f"/email/{token}")
                        blob = " ".join(filter(None, [
                            full.get("subject"),
                            full.get("body_text"),
                            full.get("body_html"),
                        ]))
                        m = re.search(r"\b(\d{6})\b", blob) or re.search(r"\b(\d{4,8})\b", blob)
                        if m:
                            return m.group(1)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
            await asyncio.sleep(poll_interval)
        return None


# Disposable-mail provider used to receive the registration OTP.
#   "fmail" → fmail.men / guns.lat (only provider that delivers the Amazon OTP
#             and passes registration; the mail.gw / guerrillamailblock.com /
#             mail.tm domains are rejected by Amazon with "unusual activity").
DEFAULT_PROVIDER = "fmail"


def make_provider(proxy=None):
    return FmailProvider(proxy)

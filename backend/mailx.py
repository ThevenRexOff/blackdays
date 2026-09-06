'''
MailX — proveedor de correo desechable para gates.
Uso:
    from mailx import FmailMailX
    mx = FmailMailX(proxy=None)
    email = mx.create()               # "abc123@fmail.men"
    links = mx.poll(email, timeout=180, filter_domain='netflix')   # lista de links Netflix
    mx.delete(email)                  # no-op
'''

import time, re, random, string
from urllib.parse import urlencode, quote
from curl_cffi import requests as curl


class FmailMailX:
    """Interceptor de la API fmail.men (la misma del generador de Amazon).

    Reemplaza al viejo MailX (CF Worker) y a GmailMailX (IMAP catch-all).
    La API fmail.men es la única que pasa los filtros anti-disposable de
    Amazon y no requiere credenciales.
    """

    BASE = 'https://fmail.men/v1'
    WHITELIST_DOMAINS = [
        'fmail.men', 'guns.lat', 'exolinker.com', 'uncmail.org',
        'brodilla.email', 'corpmail.club', 'emailab.xyz', 'emailawb.pro',
        'emailfoxi.pro', 'emailvb.pro', 'emailxo.pro', 'heroclash.info',
        'safehouse.quest', 'tempmailonline.co', 'aquaflask.click',
        'canicasbrawl.com', 'deislerlive.com', 'kuruptd.ink',
        'ougoods.com', 'sevril.win', 'gootsijs.com', 'fs6.baby',
    ]
    _last_domain = None

    def __init__(self, proxy=None):
        self._session = curl.Session(impersonate='chrome131', timeout=10)
        if proxy:
            self._session.proxies = {'http': proxy, 'https': proxy}
        self._seen = set()

    def _get_json(self, path, **params):
        last_exc = None
        for attempt in range(3):
            try:
                r = self._session.get(f'{self.BASE}{path}', params=params)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_exc = e
                time.sleep(0.15 * (attempt + 1))
        raise last_exc

    def create(self) -> str:
        domain = None
        if self._last_domain:
            candidates = self.WHITELIST_DOMAINS[:]
            if self._last_domain in candidates:
                candidates.remove(self._last_domain)
            domain = random.choice(candidates)
        data = self._get_json('/random', domain=domain)
        self._last_domain = data.get('domain')
        return data['address']

    def delete(self, addr: str) -> None:
        pass  # fmail es desechable — no necesita cleanup

    @staticmethod
    def _extract_links(text: str) -> list[str]:
        return list(dict.fromkeys(re.findall(r'https?://[^\s\'"<>\[\]]+', text or '')))

    def poll(self, addr: str, timeout: int = 180, interval: int = 3,
             filter_domain: str | None = None,
             magic_patterns: list[str] | None = None) -> tuple[list[str], str]:
        deadline = time.time() + timeout
        login = addr.split('@')[0]
        while time.time() < deadline:
            try:
                inbox = self._get_json(f'/inbox/{login}', domain=addr.split('@')[-1])
                for em in inbox.get('emails', []):
                    token = em.get('token')
                    if not token or token in self._seen:
                        continue
                    self._seen.add(token)
                    sender = (em.get('sender') or '').lower()
                    subject = (em.get('subject') or '').lower()
                    if filter_domain and filter_domain.lower() not in sender:
                        continue
                    full = self._get_json(f'/email/{token}', domain=addr.split('@')[-1])
                    body = ' '.join(filter(None, [
                        full.get('subject'), full.get('body_text'), full.get('body_html'),
                    ]))
                    links = self._extract_links(body)
                    if not links:
                        continue
                    if magic_patterns and not any(any(p in l for p in magic_patterns) for l in links):
                        continue
                    return links, body[:400]
            except Exception:
                pass
            time.sleep(interval)
        return [], ''

    def poll_and_follow(self, addr: str, session, timeout: int = 180,
                        filter_domain: str | None = None) -> bool:
        links = self.poll(addr, timeout=timeout, filter_domain=filter_domain)
        for link in links:
            try:
                session.get(url=link,
                            headers={'accept': 'text/html,*/*', 'accept-language': 'es-ES,es;q=0.9'},
                            timeout=20, allow_redirects=True)
                return True
            except Exception:
                continue
        return False


# Alias mantenido por compatibilidad con código anterior (el header del archivo
# y cualquier import legacy). El gate de Netflix usa FmailMailX.
MailX = FmailMailX
GmailMailX = FmailMailX
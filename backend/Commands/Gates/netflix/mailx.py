'''
MailX — cliente Python para el CF Email Worker privado.
Uso:
    from mailx import MailX
    mx = MailX()
    email = mx.create()               # "abc123@tudominio.xyz"
    links = mx.poll(email, timeout=180)   # lista de links Netflix/Stripe/etc
    mx.delete(email)                  # limpia KV
'''

import time, re, imaplib, email as _email_lib, string, random
from curl_cffi import requests as curl

class MailX:

    # ── Configura estos tres valores ──────────────────────────────────────────
    WORKER_URL = 'https://mailx-inbox.jonathandesktop1.workers.dev'
    SECRET     = '2b5cc434c1f9da164d1a223d95c16c59'
    # ─────────────────────────────────────────────────────────────────────────

    def __init__(self, worker_url: str | None = None, secret: str | None = None):
        self.url    = (worker_url or self.WORKER_URL).rstrip('/')
        self.secret = secret or self.SECRET
        self._params = {'secret': self.secret}

    def create(self) -> str:
        r = curl.post(f'{self.url}/create', params=self._params, timeout=10)
        r.raise_for_status()
        return r.json()['address']

    def inbox(self, addr: str) -> list[dict]:
        r = curl.get(f'{self.url}/inbox', params={**self._params, 'addr': addr}, timeout=10)
        r.raise_for_status()
        return r.json().get('messages', [])

    def delete(self, addr: str) -> None:
        try: curl.delete(f'{self.url}/inbox', params={**self._params, 'addr': addr}, timeout=10)
        except: pass

    def poll(self, addr: str, timeout: int = 180, interval: int = 5,
             filter_domain: str | None = None,
             magic_patterns: list[str] | None = None) -> tuple[list[str], str]:
        '''
        Espera hasta `timeout` segundos a que llegue un email a `addr`.
        Devuelve (links, body_snippet).
        magic_patterns: si se especifica, busca un email que tenga al menos un link que matchee.
        Si no matchea ninguno, sigue esperando (otro email puede llegar y sobrescribir).
        '''
        for _ in range(timeout // interval):
            time.sleep(interval)
            try:
                msgs = self.inbox(addr)
                for msg in msgs:
                    if filter_domain and filter_domain.lower() not in msg.get('from', '').lower():
                        continue
                    links = msg.get('links', [])
                    if not links:
                        continue
                    body = msg.get('body', '')
                    if magic_patterns:
                        if any(any(p in l for p in magic_patterns) for l in links):
                            return links, body
                        # No match yet — keep polling (maybe magic link email arrives later)
                    else:
                        return links, body
            except Exception:
                pass
        return [], ''

    def poll_and_follow(self, addr: str, session, timeout: int = 180,
                        filter_domain: str | None = None) -> bool:
        '''
        Poll + sigue el primer link con `session` (curl_cffi Session).
        Devuelve True si encontró y siguió un link, False si timeout.
        '''
        links = self.poll(addr, timeout=timeout, filter_domain=filter_domain)
        for link in links:
            try:
                session.get(url=link,
                            headers={'accept': 'text/html,*/*', 'accept-language': 'es-ES,es;q=0.9'},
                            timeout=20, allow_redirects=True)
                self.delete(addr)
                return True
            except Exception:
                continue
        return False

    def health(self) -> dict:
        r = curl.get(f'{self.url}/health', params=self._params, timeout=10)
        return r.json()


class GmailMailX:
    """Gmail IMAP catch-all — misma interfaz que MailX, sin CF Worker.

    Requiere catch-all configurado en Cloudflare Email Routing hacia Gmail.
    Genera direcciones aleatorias @dominio y las lee vía IMAP.
    """

    IMAP_HOST = 'imap.gmail.com'
    IMAP_PORT = 993
    IMAP_USER = 'nexxusbot4@gmail.com'
    IMAP_PASS = 'aodgrparjqxvrhxq'
    DOMAINS   = ['shopsxgitario.com', 'sxgitarioshop.com']

    def create(self) -> str:
        local  = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        domain = random.choice(self.DOMAINS)
        return f'{local}@{domain}'

    def delete(self, addr: str) -> None:
        pass  # catch-all IMAP — no cleanup needed

    def poll(self, addr: str, timeout: int = 180, interval: int = 5,
             filter_domain: str | None = None,
             magic_patterns: list[str] | None = None) -> tuple[list[str], str]:
        deadline = time.time() + timeout
        seen_ids: set = set()
        while time.time() < deadline:
            try:
                links, body = self._poll_once(addr, seen_ids, filter_domain, magic_patterns)
                if links:
                    return links, body
            except Exception:
                pass
            time.sleep(interval)
        return [], ''

    def _poll_once(self, addr: str, seen_ids: set,
                   filter_domain: str | None, magic_patterns: list | None):
        conn = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
        try:
            conn.login(self.IMAP_USER, self.IMAP_PASS.replace(' ', ''))
            _, mbox = conn.select('INBOX')
            total = int(mbox[0]) if mbox and mbox[0] else 0
            if total == 0:
                return [], ''

            start = max(1, total - 79)
            _, hdr_data = conn.fetch(f'{start}:{total}', '(BODY[HEADER.FIELDS (TO FROM)])')
            if not hdr_data:
                return [], ''

            candidates = []
            for item in hdr_data:
                if not isinstance(item, tuple):
                    continue
                seq_num = item[0].decode('latin-1').split()[0].encode()
                hdr     = item[1].decode('utf-8', errors='replace')
                if addr.lower() not in hdr.lower():
                    continue
                if filter_domain and filter_domain.lower() not in hdr.lower():
                    continue
                candidates.append(seq_num)

            for mid in reversed(candidates):
                if mid in seen_ids:
                    continue
                _, msg_data = conn.fetch(mid, '(RFC822)')
                if not msg_data or not msg_data[0]:
                    seen_ids.add(mid)
                    continue
                raw = msg_data[0][1]
                msg = _email_lib.message_from_bytes(raw)
                body = self._extract_body(msg)
                links = list(dict.fromkeys(re.findall(r'https?://[^\s\'"<>\[\]]+', body)))
                if not links:
                    continue
                if magic_patterns and not any(any(p in l for p in magic_patterns) for l in links):
                    continue
                seen_ids.add(mid)
                return links, body[:400]
        finally:
            try:
                conn.logout()
            except Exception:
                pass
        return [], ''

    @staticmethod
    def _extract_body(msg) -> str:
        parts = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ('text/plain', 'text/html'):
                    try:
                        parts.append(part.get_payload(decode=True).decode('utf-8', errors='replace'))
                    except Exception:
                        pass
        else:
            try:
                parts.append(msg.get_payload(decode=True).decode('utf-8', errors='replace'))
            except Exception:
                pass
        return '\n'.join(parts)

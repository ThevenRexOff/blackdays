"""NullMail — Gmail IMAP catch-all email provider.

Registers accounts using random addresses on a catch-all domain pool.
All emails land in one Gmail inbox; IMAP reads them by matching To: header.
Domains are picked randomly per account to spread reputation burn.

Implements the same provider interface as MailX/HeroSMS so the flow
needs no channel-specific branching.

Setup:
    1. Each domain: Cloudflare Email Routing catch-all → forward to Gmail
    2. Gmail: Settings → enable IMAP
    3. Google Account → Security → 2-Step Verification → App Passwords → create one

Config (.env or constructor args):
    IMAP_USER    = nexxusbot4@gmail.com
    IMAP_PASS    = xxxx xxxx xxxx xxxx   (App Password — spaces OK)
    MAIL_DOMAINS = shopsxgitario.com,sxgitarioshop.com,ionicmx.xyz
"""

import email
import imaplib
import os
import random
import re
import string
import time


IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
IMAP_USER = "nexxusbot4@gmail.com"
IMAP_PASS = "aodgrparjqxvrhxq"

# Default pool — overridden per-instance via domains= when called from main.py
MAIL_DOMAINS = []


def _random_local(length: int = 14) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def _name_local(first: str, last: str) -> str:
    """Generate a human-looking local part from a real name.

    Produces patterns like: ashley.black94, a_black2047, ashleyb19, ashley.bla302
    Much less bot-signal than a random 14-char string.
    """
    f = re.sub(r'[^a-z]', '', first.lower())[:9]
    l = re.sub(r'[^a-z]', '', last.lower())[:9]
    num = str(random.randint(1, 9999))
    sep = random.choice(['.', '_', ''])
    if not f:
        return _random_local()
    patterns = [
        f"{f}{sep}{l}{num}",
        f"{f}{num}",
        f"{f[0]}{sep}{l}{num}",
        f"{f}{sep}{l[:3]}{num}",
    ]
    return random.choice(patterns)


class NullMailError(Exception):
    pass


class NullMail:
    """Gmail IMAP catch-all inbox — drop-in replacement for MailX."""

    def __init__(self, firstName: str = "", lastName: str = "",
                 proxy: str = None, timeout: int = 30,
                 imapUser: str = None, imapPass: str = None,
                 domain: str = None, domains: list = None) -> None:
        self.imapUser   = imapUser or IMAP_USER
        self.imapPass   = (imapPass or IMAP_PASS).replace(" ", "")
        self._pinned_domain = domain
        # domains= overrides the module-level MAIL_DOMAINS pool (set from main.py)
        self._domains   = [d.strip() for d in domains if d and d.strip()] if domains else MAIL_DOMAINS
        self._firstName = firstName
        self._lastName  = lastName
        self.address    = None
        self.timeout    = timeout

        if not self.imapUser or not self.imapPass:
            raise NullMailError(
                "IMAP_USER and IMAP_PASS must be set (Gmail + App Password). "
                "Set them as env vars or pass imapUser/imapPass to the constructor."
            )


    #//! ── Shared provider interface ──────────────────────────────────── !\\#

    def getNumber(self) -> dict:
        """Generate a fresh address on a random domain from the pool."""
        suffix  = _name_local(self._firstName, self._lastName) if self._firstName else _random_local()
        domain  = self._pinned_domain or random.choice(self._domains)
        address = f"{suffix}@{domain}"
        self.address = address
        return {
            "activationId":     address,
            "number":           address,
            "normalizedNumber": address,
            "cost":             0.0,
        }

    def getSMS(self, activationId: str, timeout: int = 180) -> str:
        """Wait for a verification code sent to *activationId*.

        Polls the Gmail inbox via IMAP, filtering by To: header.
        Returns the extracted numeric code or None on timeout.
        """
        return self.waitForCode(activationId, timeout=timeout)

    def cancelActivation(self, activationId: str) -> None:
        pass  # nothing to delete — Gmail keeps the email

    def finishActivation(self, activationId: str) -> None:
        pass

    def getBalance(self):
        return None


    #//! ── IMAP reader ─────────────────────────────────────────────────── !\\#

    def waitForCode(
        self,
        addr:         str,
        timeout:      int   = 180,
        pollInterval: int   = 6,
    ) -> str:
        """Poll Gmail IMAP until a code arrives for *addr*.

        Searches UNSEEN messages addressed To: addr. Skips messages
        received before this call so stale OTPs from prior attempts
        are never reused.

        Returns:
            The first 4-8 digit code found, or None on timeout.
        """
        deadline = time.time() + timeout
        start_ts = time.time() - 5   # small back-buffer for clock skew
        seen_ids = set()

        while time.time() < deadline:
            try:
                code = self._poll_once(addr, start_ts, seen_ids)
                if code:
                    return code
            except Exception:
                pass
            time.sleep(pollInterval)

        return None

    def _poll_once(self, addr: str, start_ts: float, seen_ids: set) -> str:
        """One IMAP poll — connect, scan recent headers, disconnect.

        Scans the last 60 messages by header fetch instead of IMAP SEARCH.
        Gmail's IMAP search index can lag 2-5 min for forwarded emails, but
        fetching by message number is immediate.
        """
        conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        try:
            conn.login(self.imapUser, self.imapPass)
            _, mbox = conn.select("INBOX")
            total = int(mbox[0]) if mbox and mbox[0] else 0
            if total == 0:
                return None

            # Scan the last 60 messages newest-first
            start = max(1, total - 59)
            msg_range = f"{start}:{total}"
            _, hdr_data = conn.fetch(msg_range, "(BODY[HEADER.FIELDS (TO)])")
            if not hdr_data:
                return None

            # hdr_data alternates: (seq b'TO: ...\r\n') , b')' , ...
            candidates = []
            for item in hdr_data:
                if not isinstance(item, tuple):
                    continue
                seq_info = item[0].decode("latin-1")
                seq_num  = seq_info.split()[0].encode()
                hdr      = item[1].decode("utf-8", errors="replace")
                if addr.lower() in hdr.lower():
                    candidates.append(seq_num)

            for mid in reversed(candidates):
                if mid in seen_ids:
                    continue

                _, msg_data = conn.fetch(mid, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    seen_ids.add(mid)
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                body = self._extract_body(msg)
                code = self._extract_code(body)
                if code:
                    seen_ids.add(mid)
                    return code
                # No code yet — don't add to seen_ids, retry next poll
        finally:
            try:
                conn.logout()
            except Exception:
                pass
        return None

    @staticmethod
    def _extract_body(msg) -> str:
        """Extract plain-text body from a MIME message."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode("utf-8", errors="replace")
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
            except Exception:
                body = str(msg.get_payload())
        return body

    @staticmethod
    def _extract_code(body: str) -> str:
        """Extract a 4-8 digit verification code from email body."""
        match = re.search(r'\b(\d{6})\b', body)
        if match:
            return match.group(1)
        match = re.search(r'\b(\d{4,8})\b', body)
        if match:
            return match.group(1)
        return None

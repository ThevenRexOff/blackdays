# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════
"""
Temp Mail — Temporary email using mail.tm API.
Create inbox, poll messages, read content.
"""

import requests, random, string


_API = 'https://api.mail.tm'


class TempMail:
    """mail.tm temporary email client."""

    class tmResult:
        def __init__(self, array: dict):
            for key, value in array.items(): setattr(self, key, value)

    @staticmethod
    def _randomUser(length: int = 10) -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    @staticmethod
    def getDomains() -> list:
        try:
            resp = requests.get(f'{_API}/domains', timeout=10).json()
            return [d['domain'] for d in resp.get('hydra:member', []) if d.get('isActive')]
        except: return []

    @classmethod
    def create(cls, customUser: str = None) -> 'TempMail.tmResult':
        """Create a new temp email. Returns address + token."""
        domains = cls.getDomains()
        if not domains:
            return cls.tmResult({'status': False, 'error': 'No domains available'})

        domain   = random.choice(domains)
        user     = customUser or cls._randomUser()
        address  = f"{user}@{domain}"
        password = cls._randomUser(16)

        try:
            #//* Create account
            resp = requests.post(f'{_API}/accounts', json={
                'address': address, 'password': password
            }, timeout=10)
            if resp.status_code not in (200, 201):
                return cls.tmResult({'status': False, 'error': f'Create failed: {resp.text[:100]}'})

            #//* Get JWT token
            tokenResp = requests.post(f'{_API}/token', json={
                'address': address, 'password': password
            }, timeout=10).json()

            token = tokenResp.get('token')
            if not token:
                return cls.tmResult({'status': False, 'error': 'Token failed'})

            return cls.tmResult({
                'status': True,
                'address': address,
                'token': token,
                'password': password,
            })
        except Exception as e:
            return cls.tmResult({'status': False, 'error': str(e)})

    @classmethod
    def getInbox(cls, token: str) -> 'TempMail.tmResult':
        """Get inbox messages list."""
        try:
            resp = requests.get(f'{_API}/messages', headers={
                'Authorization': f'Bearer {token}'
            }, timeout=10).json()

            messages = []
            for msg in resp.get('hydra:member', []):
                messages.append({
                    'id': msg.get('id', ''),
                    'from': msg.get('from', {}).get('address', 'Unknown'),
                    'subject': msg.get('subject', 'No Subject'),
                    'intro': msg.get('intro', '')[:100],
                    'date': msg.get('createdAt', '')[:19].replace('T', ' '),
                    'seen': msg.get('seen', False),
                })

            return cls.tmResult({'status': True, 'messages': messages, 'total': len(messages)})
        except Exception as e:
            return cls.tmResult({'status': False, 'error': str(e)})

    @classmethod
    def readMessage(cls, token: str, msgId: str) -> 'TempMail.tmResult':
        """Read full message content."""
        try:
            resp = requests.get(f'{_API}/messages/{msgId}', headers={
                'Authorization': f'Bearer {token}'
            }, timeout=10).json()

            return cls.tmResult({
                'status': True,
                'id': resp.get('id', ''),
                'sender': resp.get('from', {}).get('address', 'Unknown'),
                'subject': resp.get('subject', 'No Subject'),
                'text': (resp.get('text') or resp.get('intro') or 'No content')[:3500],
                'date': resp.get('createdAt', '')[:19].replace('T', ' '),
            })
        except Exception as e:
            return cls.tmResult({'status': False, 'error': str(e)})

# ══════════════════════════════════════════════════════════════════════════
#  Coder: t.me/Vxsilisk  -  Shop: t.me/Sxgitario
# ══════════════════════════════════════════════════════════════════════════

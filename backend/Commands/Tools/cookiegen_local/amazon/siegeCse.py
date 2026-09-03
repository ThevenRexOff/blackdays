"""Amazon "SiegeCrypto" client-side password encryption, reimplemented.

Amazon's registration/signin forms encrypt the password client-side
before it ever reaches the wire, using a proprietary envelope that is
structurally identical to the AWS Encryption SDK message format (same
key-provider TLV layout, same ``AWSKMSEncryptionClient Final Frame`` AAD
string) but with a 128-bit AES data key instead of the SDK's usual 256-bit
default. Reverse-engineered 2026-07-23 by hooking ``window.crypto.subtle``
in a real Chromium session (Playwright) and diffing the exact
``generateKey``/``wrapKey``/``encrypt`` calls against the resulting
``/ap/register`` POST body — the envelope produced here has been verified
byte-for-byte identical to a real browser's output given the same message
ID, data key and ``appActionToken``.

Why this exists instead of using the protected ``cseAmazonSxgitario.py``:
that module only exposes ``encrypt(password)`` with no way to bind the
request's ``appActionToken`` into the encryption context. Amazon's real
client always includes it — omitting it (confirmed live, all 13
marketplaces, 2026-07-23) does not break registration outright, because
the OTP step is what actually authenticates the session, but it leaves the
account's real password mismatched with whatever the user was told, so a
normal password sign-in afterwards fails with "incorrect password".

Envelope layout (all integers big-endian)::

    version(1)=0x01  flag(1)=0x80  const(2)=0x0014  messageId(16, random)
    contextLen(2)  contextCount(2)=1
        keyLen(2) b"appActionToken"  valLen(2) appActionToken bytes
    keyProviderCount(2)=1
        providerIdLen(2) b"si:md5"
        keyIdLen(2) keyId bytes (32-char hex)
        wrappedKeyLen(2) wrappedKey (256 bytes, RSA-OAEP-SHA256)
    contentType(1)=0x02  reserved(4)=0x00000000  ivLength(1)=0x0c
    frameLength(4)=0x00000010
    -- header ends here; the header itself is used as GCM AAD below --
    headerAuthIv(12, all zero)  headerAuthTag(16)
        = AES-128-GCM(dataKey, iv=headerAuthIv, aad=header, pt=b"").tag
    finalFrameMarker(4)=0xFFFFFFFF  sequenceNumber(4)=0x00000001
    frameIv(12) = sequenceNumber.to_bytes(12, "big")
    contentLength(4) = len(password utf-8 bytes)
    ciphertext+tag
        = AES-128-GCM(dataKey, iv=frameIv, aad=frameAad, pt=password).
          frameAad = messageId + b"AWSKMSEncryptionClient Final Frame"
                     + sequenceNumber(4) + contentLength(8, uint64)

Author: Vxsilisk @ Sxgitario API Gateways Service
"""

import base64
import os
import struct

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_FINAL_FRAME_AAD_STRING = b"AWSKMSEncryptionClient Final Frame"


def _b64url_to_int(value: str) -> int:
    padded = value + "=" * (-len(value) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(padded), "big")


def _load_rsa_public_key(jwkN: str, jwkE: str = "AQAB"):
    numbers = RSAPublicNumbers(_b64url_to_int(jwkE), _b64url_to_int(jwkN))
    return numbers.public_key(default_backend())


def _tlv(data: bytes) -> bytes:
    """2-byte-big-endian-length-prefixed field, as used throughout the envelope."""
    return struct.pack(">H", len(data)) + data


def encryptPassword(password: str, jwkN: str, keyId: str, appActionToken: str,
                     providerId: str = "si:md5") -> str:
    """Build one Amazon SiegeCrypto envelope for a password field.

    Args:
        password: Plaintext password to encrypt.
        jwkN: RSA public modulus (base64url, no padding) for the target
            region — see :data:`core.CSE_PROFILES`.
        keyId: 32-char hex key identifier matching ``jwkN``.
        appActionToken: The current page's ``appActionToken`` hidden
            field value. This is the piece the protected
            ``cseAmazonSxgitario`` module can't bind — see module
            docstring.
        providerId: Amazon's fixed provider tag; always ``"si:md5"`` on
            every marketplace observed so far.

    Returns:
        Base64-encoded envelope, ready to drop straight into the
        ``encryptedPwd`` / ``encryptedPwdCheck`` form field.
    """
    publicKey = _load_rsa_public_key(jwkN)
    messageId = os.urandom(16)
    dataKey = AESGCM.generate_key(bit_length=128)

    contextSection = struct.pack(">H", 1) + _tlv(b"appActionToken") + _tlv(appActionToken.encode("utf-8"))

    wrappedKey = publicKey.encrypt(
        dataKey,
        rsa_padding.OAEP(mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    keyProviderSection = (
        struct.pack(">H", 1)
        + _tlv(providerId.encode("utf-8"))
        + _tlv(keyId.encode("utf-8"))
        + _tlv(wrappedKey)
    )

    header = (
        bytes([0x01, 0x80])
        + struct.pack(">H", 20)
        + messageId
        + struct.pack(">H", len(contextSection))
        + contextSection
        + keyProviderSection
        + bytes([0x02])         # content type: framed
        + b"\x00\x00\x00\x00"   # reserved
        + bytes([0x0C])         # IV length = 12
        + struct.pack(">I", 16)  # frame length (matches Amazon's own constant)
    )

    aesgcm = AESGCM(dataKey)

    headerAuthIv = b"\x00" * 12
    headerAuthTag = aesgcm.encrypt(headerAuthIv, b"", header)

    sequenceNumber = 1
    frameIv = sequenceNumber.to_bytes(12, "big")
    plaintext = password.encode("utf-8")
    frameAad = messageId + _FINAL_FRAME_AAD_STRING + struct.pack(">I", sequenceNumber) + struct.pack(">Q", len(plaintext))
    frameCiphertext = aesgcm.encrypt(frameIv, plaintext, frameAad)

    finalFrame = (
        b"\xff\xff\xff\xff"
        + struct.pack(">I", sequenceNumber)
        + frameIv
        + struct.pack(">I", len(plaintext))
        + frameCiphertext
    )

    envelope = header + headerAuthIv + headerAuthTag + finalFrame
    return base64.b64encode(envelope).decode("ascii")

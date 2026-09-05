#!/usr/bin/env python3
import os
import re
import json
import base64
import struct
from io import BytesIO
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# --- AWS KMS Key Config per region ---
# US key (from logg.js)
KEYS_US = {
    "n": "rwLCVK_8hcUgil9KQiN7RbtmcJV5Pt12CwbhZ1h9fvdbVRILCanjv2RNSW9l-Mq0fnRq6DLTLzX3J3TuVCZQ1wjfa-Ef1BDeXnVNaY4q0Vvl2e1e9UF-uwyK5mDyiftlPt5JcsRuFXU1dMSb5TwDiFV1UlGOc-db33zi1MlmrL5L7iyfqBQmlEoa5el5pFbmeK2wSOKBZtJja-dbVzde0jrpGlVhHDZOAlH7g8aTftqwHLVP27T9Pr0UJtaj9LIX-sg_K9-Pl7H2W9BJDTJLJi_EAAqBHTrRueejO3XbEuSGrsrphCk0ZlYqoLkobey-kubWTba5kzsWL-huF--tzQ",
    "e": "AQAB",
    "keyId": "973900addb061fbe5bb4ea871e9d8161",
}

KEYS_JP = {
    "n": "oez6pTbcxFW1_fdZyYWlQonAop33Yv9BK4b_f21ttSmSe7TmjPN2mqXsUpFoTpwcVJ3akIu3cExnkjV_juIoj0u7V8CvrkCZjRVWYSwuBdGmNKx3p8fsmHBkqvMXjcSrhFZAWI7_GFLo66DATzpJu5TVWbzkGS95nNL-YCsr8OUxy08o7Wp7oiujLGGdI7RtcYXXe1SchC5cMj3g8nfhDGuFui6hgEoDzg_fgypshbKsybaesCLyxNFqQbiH24_T8nSuOYVGui23Td8sKFJoTqEq14JYp-GDAn88IMUErUS4NdxL4FJPPEXV6SMsH5P0MDOrGu8TYpsgV0YRTT0ZBw",
    "e": "AQAB",
    "keyId": "e7696039e9f2aed1c5c0d34eb95a3cd4",
}

# EU key (from AuthenticationPortalSigninEU.js)
KEYS_EU = {
    "n": "7MBo_ZCPa0E3BnEXiLK0zhb9fZwQVrkkCPEBuf9HVq_-uEnER6cZBu7BABkLvvvFQnPYaxvjyQ3vAhJsdQUkHVb6spDOJsDLq3xQnzPr5T41PxXgMVPlrEWtjT2eB3ENU5gf-gtwCAm6JZMzzMr4k41aehnfikRtEdAKewUZm0KbrS0gcWCKnBxrkAWiOHUEZaL0IWH45sU_ul6y9Ej2w8xl1Nm8KOvt3FV_uF8OXj2icLLHMlUTlYDbC3xSLNahTXoh0Dao5ihk6kf_Wxv_d2h_ftx0MWuPVmVMASYCY9YGErKQ182exEaWta0I_Eva-omXyYxoKxneN9LdZYw-NQ",
    "e": "AQAB",
    "keyId": "8c3749c7577cfbe8de80ec2d8e03f35c",
}

# Region → key mapping
REGION_KEYS = {
    "US": KEYS_US, "CA": KEYS_US, "JP": KEYS_JP,
    "DE": KEYS_EU, "ES": KEYS_EU, "IT": KEYS_EU, "AU": KEYS_EU, "BR": KEYS_EU,
    "MX": KEYS_US, "IN": KEYS_EU, "NL": KEYS_EU, "SG": KEYS_EU,
    "AE": KEYS_EU, "SA": KEYS_EU, "TR": KEYS_EU, "SE": KEYS_EU,
    "PL": KEYS_EU, "EG": KEYS_EU,
}

ALGORITHM_ID = 20  # aes_128_gcm_iv12_tag16
PROVIDER_ID = "si:md5"
SERIALIZATION_VERSION = 1
OBJECT_TYPE = 128  # CUSTOMER_AE_DATA
CONTENT_TYPE = 2   # FRAMED_DATA
SEQUENCE_NUMBER_END = 0xFFFFFFFF
FINAL_FRAME_STRING_ID = b"AWSKMSEncryptionClient Final Frame"


def uint8(n):
    return struct.pack(">B", n)

def uint16be(n):
    return struct.pack(">H", n)

def uint32be(n):
    return struct.pack(">I", n)

def uint64be(n):
    return struct.pack(">Q", n)

def b64url_decode(s):
    s += "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s)

def serialize_encryption_context(context):
    if not context:
        return uint16be(0)
    items = sorted(context.items())
    encoded_pairs = []
    for k, v in items:
        kb = k.encode('utf-8')
        vb = v.encode('utf-8')
        encoded_pairs.append(uint16be(len(kb)) + kb + uint16be(len(vb)) + vb)
    inner = uint16be(len(items)) + b"".join(encoded_pairs)
    return uint16be(len(inner)) + inner

def serialize_encrypted_data_keys(edks):
    encoded = []
    for edk in edks:
        pb = edk['providerId'].encode('utf-8')
        kb = edk['keyInfo'].encode('utf-8')
        db = edk['encryptedDataKey']
        encoded.append(uint16be(len(pb)) + pb + uint16be(len(kb)) + kb + uint16be(len(db)) + db)
    return uint16be(len(edks)) + b"".join(encoded)

def serialize_message_header(header):
    return (
        uint8(header['version']) +
        uint8(header['type']) +
        uint16be(header['algorithmId']) +
        header['messageId'] +
        serialize_encryption_context(header['encryptionContext']) +
        serialize_encrypted_data_keys(header['encryptedDataKeys']) +
        uint8(header['contentType']) +
        b"\x00\x00\x00\x00" +
        uint8(header['headerIvLength']) +
        uint32be(header['frameLength'])
    )

def message_aad(message_id, content_string, sequence_number, content_length):
    return (
        message_id +
        content_string +
        uint32be(sequence_number) +
        uint64be(content_length)
    )

def frame_iv(iv_length, sequence_number):
    iv = bytearray(iv_length)
    struct.pack_into(">I", iv, iv_length - 4, sequence_number)
    return bytes(iv)


def encrypt_password(plaintext, region="US", encryption_context=None, requires_tail=False):
    if encryption_context is None:
        encryption_context = {}

    # Get region-specific key
    key_config = REGION_KEYS.get(region, KEYS_US)
    JWK_N = key_config["n"]
    JWK_E = key_config["e"]
    KEY_ID = key_config["keyId"]

    # 1. RSA Public Key
    n = int.from_bytes(b64url_decode(JWK_N), 'big')
    e = int.from_bytes(b64url_decode(JWK_E), 'big')
    public_key = rsa.RSAPublicNumbers(e, n).public_key()

    # 2. AES Data Key (16 bytes)
    data_key = os.urandom(16)

    # 3. Wrap with RSA-OAEP (SHA-256)
    wrapped_data_key = public_key.encrypt(
        data_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # 4. Header
    message_id = os.urandom(16)
    plaintext_bytes = plaintext.encode('utf-8')
    frame_length = len(plaintext_bytes) + 1

    header = {
        'version': SERIALIZATION_VERSION,
        'type': OBJECT_TYPE,
        'algorithmId': ALGORITHM_ID,
        'messageId': message_id,
        'encryptionContext': encryption_context,
        'encryptedDataKeys': [{
            'providerId': PROVIDER_ID,
            'keyInfo': KEY_ID,
            'encryptedDataKey': wrapped_data_key
        }],
        'contentType': CONTENT_TYPE,
        'headerIvLength': 12,
        'frameLength': frame_length
    }

    serialized_header = serialize_message_header(header)

    # 5. Header Auth Tag
    header_iv = b"\x00" * 12
    aesgcm = AESGCM(data_key)
    header_auth_tag = aesgcm.encrypt(header_iv, b"", serialized_header)

    # 6. Encrypt Final Frame
    seq_num = 1
    f_iv = frame_iv(12, seq_num)
    aad = message_aad(message_id, FINAL_FRAME_STRING_ID, seq_num, len(plaintext_bytes))
    frame_cipher_full = aesgcm.encrypt(f_iv, plaintext_bytes, aad)

    # 7. Final Frame Header
    final_frame_header = (
        uint32be(SEQUENCE_NUMBER_END) +
        uint32be(seq_num) +
        f_iv +
        uint32be(len(plaintext_bytes))
    )

    # 8. Assemble Full Message
    cipher_message = (
        serialized_header +
        header_iv +
        header_auth_tag +
        final_frame_header +
        frame_cipher_full
    )

    res = base64.b64encode(cipher_message).decode('utf-8')

    if requires_tail:
        tail = re.sub(r'[\s-]', '', plaintext)[-4:]
        if len(tail) > 3:
            res += "!" + tail

    return res

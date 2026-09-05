#!/usr/bin/env python3
"""
Metadata1 Decoder — Reverse of the FWCIM encoding pipeline.

Decodes a metadata1 value back to the original JSON fingerprint data.
Pipeline reversed: "identifier:base64" → Base64 → TEA decrypt → CRC32|UTF8 → JSON
"""

import json
import base64
import struct
import sys

# ============================================================
# Key material from Module 69 (keyProvider)
# ============================================================
KEY_IDENTIFIER = "ECdITeCs"
KEY_MATERIAL_UINT32 = [1888420705, 2576816180, 2347232058, 874813317]

def key_material_to_bytes(material):
    """Convert 4 uint32 values to 16 bytes (little-endian, matching JS charCodeAt packing)."""
    result = []
    for val in material:
        result.append(val & 0xFF)
        result.append((val >> 8) & 0xFF)
        result.append((val >> 16) & 0xFF)
        result.append((val >> 24) & 0xFF)
    return bytes(result)


# ============================================================
# TEA Decryption
# ============================================================

def te_decrypt(ciphertext, key_material_uint32):
    """TEA decryption — reverse of doEncrypt from module 70."""
    if len(ciphertext) == 0:
        return ''

    n = (len(ciphertext) + 3) // 4
    v = []
    for i in range(n):
        idx = 4 * i
        val = ord(ciphertext[idx]) & 0xFF
        if idx + 1 < len(ciphertext):
            val |= (ord(ciphertext[idx + 1]) & 0xFF) << 8
        if idx + 2 < len(ciphertext):
            val |= (ord(ciphertext[idx + 2]) & 0xFF) << 16
        if idx + 3 < len(ciphertext):
            val |= (ord(ciphertext[idx + 3]) & 0xFF) << 24
        v.append(val)

    delta = 0x9E3779B9
    rounds = (6 + 52 // n) if n > 0 else 0
    d = (rounds * delta) & 0xFFFFFFFF

    for _ in range(rounds):
        e = (d >> 2) & 3
        for u in range(n - 1, -1, -1):
            prev = v[(u - 1 + n) % n]
            a = ((prev >> 5) ^ (v[u] << 2)) + ((v[u] >> 3) ^ (prev << 4))
            b = (d ^ prev) + (key_material_uint32[(u & 3) ^ e] ^ v[u])
            v[u] = (v[u] - (a ^ b)) & 0xFFFFFFFF
        d = (d - delta) & 0xFFFFFFFF

    result = []
    for val in v:
        result.append(chr(val & 0xFF))
        result.append(chr((val >> 8) & 0xFF))
        result.append(chr((val >> 16) & 0xFF))
        result.append(chr((val >> 24) & 0xFF))
    return ''.join(result)


# ============================================================
# UTF-8 Decode (reverse of module 27)
# ============================================================

def utf8_decode(s):
    """Decode UTF-8 encoded string back to unicode."""
    result = []
    i = 0
    while i < len(s):
        c = ord(s[i])
        if c < 128:
            result.append(chr(c))
            i += 1
        elif c >= 192 and c < 224:
            result.append(chr(((c & 31) << 6) | (ord(s[i + 1]) & 63)))
            i += 2
        elif c >= 224:
            result.append(chr(((c & 15) << 12) | ((ord(s[i + 1]) & 63) << 6) | (ord(s[i + 2]) & 63)))
            i += 3
        else:
            i += 1
    return ''.join(result)


# ============================================================
# CRC32
# ============================================================

def crc32_hash(data_str):
    """CRC32 checksum (matching module 4)."""
    import zlib
    return zlib.crc32(data_str.encode('latin-1')) & 0xFFFFFFFF


# ============================================================
# Decode pipeline
# ============================================================

def decode_metadata1(metadata1):
    """Decode metadata1 value to JSON fingerprint data."""
    # Step 1: Split identifier:base64
    colon_idx = metadata1.index(':')
    identifier = metadata1[:colon_idx]
    b64_data = metadata1[colon_idx + 1:]

    print(f"Identifier: {identifier}")
    print(f"Base64 length: {len(b64_data)} chars")

    # Step 2: Base64 decode
    encrypted = base64.b64decode(b64_data).decode('latin-1')
    print(f"Encrypted length: {len(encrypted)} bytes")

    # Step 3: TEA decrypt
    decrypted = te_decrypt(encrypted, KEY_MATERIAL_UINT32)
    print(f"Decrypted length: {len(decrypted)} chars")

    # Step 4: Split CRC32|payload
    pipe_idx = decrypted.index('|')
    crc_hex = decrypted[:pipe_idx]
    body = decrypted[pipe_idx + 1:]

    print(f"CRC32 prefix: {crc_hex}")

    # Step 5: Verify CRC32
    body_utf8 = utf8_decode(body)
    computed_crc = crc32_hash(body)
    computed_hex = format(computed_crc, '08X')
    crc_match = (crc_hex == computed_hex)
    print(f"CRC32 expected: {crc_hex}")
    print(f"CRC32 computed: {computed_hex}")
    print(f"CRC32 match: {'YES' if crc_match else 'NO'}")

    # Step 6: Parse JSON
    data = json.loads(body_utf8)
    return data


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 decode_metadata1.py '<metadata1_value>'")
        print("   or: python3 decode_metadata1.py --file <file>")
        sys.exit(1)

    if sys.argv[1] == '--file':
        with open(sys.argv[2], 'r') as f:
            metadata1 = f.read().strip()
    else:
        metadata1 = sys.argv[1]

    print("=" * 60)
    print("Metadata1 Decoder")
    print("=" * 60)
    print(f"Key: {KEY_IDENTIFIER}")
    print(f"Material: {KEY_MATERIAL_UINT32}")
    print(f"Input: {len(metadata1)} chars")
    print("")

    data = decode_metadata1(metadata1)

    print("")
    print("=" * 60)
    print("DECODED FINGERPRINT JSON")
    print("=" * 60)
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Save to file
    with open('decoded-fingerprint.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to decoded-fingerprint.json")

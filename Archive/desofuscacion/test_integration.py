"""
Test script: integra el nuevo fingerprint generator con el password encryption de gen.py.

Uso:
    python3 test_integration.py
    python3 test_integration.py --email user@gmail.com --password MyPass123
"""

import json
import sys
import base64
import os

from fingerprint import generate_metadata1, generate_fingerprint
from gen import encrypt_password, AuthPayloads


def test_full_integration(
    email=None,
    password=None,
    name=None,
    password_check=None,
    user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0",
    html_b64=None,
    location=None,
    referrer=None,
):
    """Generate all auth payloads: metadata1 + encrypted password."""
    print("=" * 60)
    print("TEST: Generación completa de auth payloads")
    print("=" * 60)

    # 1. Generate fingerprint + metadata1
    print("\n[1] Generando fingerprint...")
    result = generate_metadata1(
        email=email,
        password=password,
        name=name,
        password_check=password_check,
        user_agent=user_agent,
        html_b64=html_b64,
        location=location,
        referrer=referrer,
    )

    fp = result["fingerprint"]
    metadata1 = result["metadata1"]
    profile = result["profile"]

    print(f"  Profile: {profile}")
    print(f"  Fields: {len(fp)} keys")
    print(f"  Form: {list(fp['form'].keys())}")
    print(f"  metadata1: {len(metadata1)} chars")

    # 2. Encrypt password (if provided)
    encrypted_pwd = ""
    repassword = ""
    if password:
        print("\n[2] Cifrando password...")
        encrypted_pwd = encrypt_password(password)
        repassword = encrypt_password(password)
        print(f"  encrypted_pwd: {encrypted_pwd[:50]}...")
        print(f"  repassword:    {repassword[:50]}...")
        print(f"  Match: {encrypted_pwd == repassword}")

    # 3. Build AuthPayloads
    print("\n[3] Construyendo AuthPayloads...")
    payloads = AuthPayloads(
        fingerprint=json.dumps(fp, separators=(',', ':')),
        metadata1=metadata1,
        encrypted_pwd=encrypted_pwd,
        repassword=repassword,
    )

    print(f"  fingerprint: {len(payloads.fingerprint)} chars")
    print(f"  metadata1:   {len(payloads.metadata1)} chars")
    print(f"  encrypted:   {len(payloads.encrypted_pwd)} chars")

    # 4. Show the form data that would be sent
    print("\n[4] Data que se enviaría al POST:")
    form_data = {
        "metadata1": payloads.metadata1,
    }
    if password:
        form_data["encryptedPwd"] = payloads.encrypted_pwd
        form_data["encryptedPwdCheck"] = payloads.repassword
    if name:
        form_data["customerName"] = name
    if email:
        form_data["email"] = email

    for k, v in form_data.items():
        val = v[:60] + "..." if len(str(v)) > 60 else v
        print(f"  {k}: {val}")

    # 5. Save files
    os.makedirs("output", exist_ok=True)
    with open("output/fingerprint.json", "w") as f:
        json.dump(fp, f, indent=2, ensure_ascii=False)
    with open("output/metadata1.txt", "w") as f:
        f.write(metadata1)
    if encrypted_pwd:
        with open("output/encrypted_pwd.txt", "w") as f:
            f.write(encrypted_pwd)

    print(f"\n[5] Archivos guardados en output/")
    print(f"  output/fingerprint.json")
    print(f"  output/metadata1.txt")
    if encrypted_pwd:
        print(f"  output/encrypted_pwd.txt")

    # 6. Verify metadata1 format
    print("\n[6] Verificando metadata1...")
    if metadata1.startswith("ECdITeCs:"):
        print("  Formato correcto: ECdITeCs:BASE64...")
        print(f"  Longitud: {len(metadata1)} chars")
        # Extract CRC32 prefix from decrypted payload (approximate)
        print(f"  Identificador: ECdITeCs")
        print("  OK - metadata1 válido")
    else:
        print(f"  ERROR: formato inesperado {metadata1[:20]}...")

    return payloads


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description='Test fingerprint + password encryption')
    p.add_argument('--email', default=None)
    p.add_argument('--password', default=None)
    p.add_argument('--name', default=None)
    p.add_argument('--password-check', default=None)
    p.add_argument('--user-agent', default="Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0")
    args = p.parse_args()

    test_full_integration(
        email=args.email,
        password=args.password,
        name=args.name,
        password_check=args.password_check,
        user_agent=args.user_agent,
    )

from fingerprint import generate_metadata1, generate_fingerprint
import base64
import json

# ============================================================
# Ejemplo 1: Generar metadata1 con datos basicos
# ============================================================

# password="P@ssw0rd!",
    # name="Carlos Garcia",
    # otp="456789",

html_b64 = base64.b64encode(open("signin.html","rb").read()).decode()
result = generate_metadata1(
    email="carlos@outlook.com",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    html_b64=html_b64
)

del result['metadata1']
with open('output.json', 'w') as f:
    f.write(json.dumps(result['fingerprint'], indent=4))
# Sxgitario Protected Module — Copyright (c) Sxgitario Gateway Services.
# Unauthorized reverse engineering, decompilation, or redistribution is
# prohibited under the Sxgitario Gateway End User License Agreement.

import base64 as _b64
import hashlib as _hh
import os as _os
import sys as _ss
import zlib as _zz
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AG

_d0=bytes.fromhex("5f2cf1d0111e06bceead06204077f063cb05ad67c0322cf9b2fd3c14357a1f84")
_d1=bytes.fromhex("47dc6f2491c90faae0bfffa84973b16617bdbe6877e1eb2ea9de49d76c9ec358")
_d2=bytes.fromhex("9c0e986424467d6603878ebb22ff54fd58e1589e2bb1c7f16ee7eb05852aa35a")
_d3=bytes.fromhex("e946eb2581f9e4df6d0f07434dfa205bfbb3d20a99b1b9a188f394f2eda4a490")

if _ss.gettrace() is not None or (_ss.getprofile() if hasattr(_ss, "getprofile") else None) is not None:
    raise SystemExit
if _os.environ.get("PYTHONINSPECT") or _os.environ.get("PYTHONBREAKPOINT") not in (None, "0"):
    raise SystemExit

_p1=bytes.fromhex("393ff73e38164958")
_p2=bytes.fromhex("34a886a4135b4de5")
_p3=bytes.fromhex("42864825f6519e0c")
_p4=bytes.fromhex("420e7bf1f6648be2")
_tag='awsBypassSxgitario'
_k=_hh.sha256(_p1+_p3+_p2+_p4+b"|Sxg|"+_tag.encode("utf-8")).digest()
_nonce=_b64.b64decode("vWAsTrzJLPUF2uqr")
_aad=_b64.b64decode("U1hHMnxhd3NCeXBhc3NTeGdpdGFyaW98MjM3OTU=")
_ct="".join([
    "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",
    "suMaGgA=",
])
_ctb=_b64.b64decode(_ct)
if _hh.sha256(_ctb+_nonce+_aad).hexdigest()!='1f0ba9d5463b6d7220e4e5b7b7b77253a69df2c068fdc2f4239c0a021777de37':
    raise SystemExit
_src=_zz.decompress(_AG(_k).decrypt(_nonce,_ctb,_aad)).decode("utf-8")
exec(_src, globals(), globals())
del _b64,_hh,_os,_ss,_zz,_AG,_d0,_d1,_d2,_d3,_p1,_p2,_p3,_p4,_tag,_k,_nonce,_aad,_ct,_ctb,_src

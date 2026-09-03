# Sxgitario Protected Module — Copyright (c) Sxgitario Gateway Services.
# Unauthorized reverse engineering, decompilation, or redistribution is
# prohibited under the Sxgitario Gateway End User License Agreement.

import base64 as _b64
import hashlib as _hh
import os as _os
import sys as _ss
import zlib as _zz
from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AG

_d0=bytes.fromhex("88cd0fe87604953ff5f49c744fa9ab6cf4fac2f93ced339590ee6e664a1a9a84")
_d1=bytes.fromhex("a2769f71d36dfe5f111e9be57b30218b96d5598562ab4e8b5ce2e6e1128b8af2")
_d2=bytes.fromhex("e0a0e26c2a0eb2af06ad6661fbe07869aba4287bd741050c83f3b34c9e24535d")
_d3=bytes.fromhex("fcde7267a6565e1b3c4f1ba076fc29488c1075ba388dd197ecf460859e17730e")

if _ss.gettrace() is not None or (_ss.getprofile() if hasattr(_ss, "getprofile") else None) is not None:
    raise SystemExit
if _os.environ.get("PYTHONINSPECT") or _os.environ.get("PYTHONBREAKPOINT") not in (None, "0"):
    raise SystemExit

_p1=bytes.fromhex("d6bf92834ea60ead")
_p2=bytes.fromhex("094f9c4a76281102")
_p3=bytes.fromhex("6abced0b95db221e")
_p4=bytes.fromhex("921844cf7237f508")
_tag='cseAmazonSxgitario'
_k=_hh.sha256(_p1+_p3+_p2+_p4+b"|Sxg|"+_tag.encode("utf-8")).digest()
_nonce=_b64.b64decode("43/WfLCPPTq2bezF")
_aad=_b64.b64decode("U1hHMnxjc2VBbWF6b25TeGdpdGFyaW98OTcyNA==")
_ct="".join([
    "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",
    "fCXaWg==",
])
_ctb=_b64.b64decode(_ct)
if _hh.sha256(_ctb+_nonce+_aad).hexdigest()!='edab3724d5aeb10eb00ebd11071973af8492244a1ad6a8b024d5a559646f6890':
    raise SystemExit
_src=_zz.decompress(_AG(_k).decrypt(_nonce,_ctb,_aad)).decode("utf-8")
exec(_src, globals(), globals())
del _b64,_hh,_os,_ss,_zz,_AG,_d0,_d1,_d2,_d3,_p1,_p2,_p3,_p4,_tag,_k,_nonce,_aad,_ct,_ctb,_src

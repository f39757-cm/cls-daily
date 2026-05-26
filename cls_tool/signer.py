"""
CLS API Signature: sign = MD5(SHA1(sorted query string))
"""

import hashlib
import urllib.parse


def build_sign(params: dict) -> str:
    """Generate CLS API sign = MD5(SHA1(alphabetically sorted query string))."""
    sorted_keys = sorted(params.keys())
    # Build query string with urllib.parse.urlencode for proper encoding
    query_string = urllib.parse.urlencode(
        [(k, params[k]) for k in sorted_keys]
    )
    sha1_hex = hashlib.sha1(query_string.encode()).hexdigest()
    sign = hashlib.md5(sha1_hex.encode()).hexdigest()
    return sign


def sign_params(params: dict) -> dict:
    """Return params dict with the 'sign' key added."""
    signed = dict(params)
    signed["sign"] = build_sign(params)
    return signed

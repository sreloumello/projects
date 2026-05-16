# app/middleware/auth.py — jwt validation via cognito jwks

import json
import time
import base64
import urllib.request
from functools import lru_cache
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

security = HTTPBearer(auto_error=False)


# ── jwks cache ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _fetch_jwks() -> dict:
    """fetch cognito public keys — cached in lambda memory between invocations"""
    url = get_settings().cognito_jwks_url
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read())


def _get_public_key(kid: str):
    """return the rsa public key matching the token kid"""
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
    from cryptography.hazmat.backends import default_backend

    jwks = _fetch_jwks()
    for key in jwks["keys"]:
        if key["kid"] == kid:
            def _b64_to_int(b64: str) -> int:
                padded = b64 + "=" * (4 - len(b64) % 4)
                return int.from_bytes(base64.urlsafe_b64decode(padded), "big")

            pub = RSAPublicNumbers(_b64_to_int(key["e"]), _b64_to_int(key["n"]))
            return pub.public_key(default_backend())

    raise HTTPException(status_code=401, detail="public key not found")


def _get_expected_issuer() -> str:
    """build expected issuer — supports both local floci and real aws"""
    s = get_settings()
    if s.ENV == "dev":
        # floci issues tokens with localhost as issuer
        return f"http://localhost:4566/{s.COGNITO_USER_POOL_ID}"
    return (
        f"https://cognito-idp.{s.COGNITO_REGION}.amazonaws.com"
        f"/{s.COGNITO_USER_POOL_ID}"
    )


def _decode_jwt(token: str) -> dict:
    """decode and validate cognito jwt signature and expiration"""
    header = jwt.get_unverified_header(token)
    pub_key = _get_public_key(header["kid"])

    payload = jwt.decode(
        token,
        pub_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )

    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=401, detail="token expired")

    expected_iss = _get_expected_issuer()
    if payload.get("iss") != expected_iss:
        raise HTTPException(status_code=401, detail="invalid token issuer")

    return payload


# ── dependencies ──────────────────────────────────────────────────────────────

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """returns token payload if present and valid, none if absent"""
    if not credentials:
        return None
    try:
        return _decode_jwt(credentials.credentials)
    except Exception:
        return None


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """dependency — requires valid token, raises 401 otherwise"""
    if not credentials:
        raise HTTPException(status_code=401, detail="authentication required")
    return _decode_jwt(credentials.credentials)

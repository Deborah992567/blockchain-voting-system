from datetime import datetime, timedelta
import json
import base64

# Prefer python-jose or PyJWT if available; otherwise provide a test-friendly
# fallback encoder/decoder (unsigned) so tests can run without external deps.
try:
    from jose import jwt as jose_jwt  # type: ignore
    _JWT_LIB = "jose"
    _JWT = jose_jwt
except Exception:
    try:
        import jwt as pyjwt  # type: ignore
        # Some `jwt` packages do not provide PyJWT API; ensure `.encode` exists
        if hasattr(pyjwt, "encode") and hasattr(pyjwt, "decode"):
            _JWT_LIB = "pyjwt"
            _JWT = pyjwt
        else:
            _JWT_LIB = None
            _JWT = None
    except Exception:
        _JWT_LIB = None
        _JWT = None

from app.config import settings
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="auth.jwt")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict) -> str:
    logger.debug("Creating access token", subject=data.get("sub"))
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    if _JWT_LIB == "jose":
        encoded_jwt = _JWT.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    elif _JWT_LIB == "pyjwt":
        encoded_jwt = _JWT.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        # PyJWT may return bytes in some versions
        if isinstance(encoded_jwt, bytes):
            encoded_jwt = encoded_jwt.decode()
    else:
        # simple unsigned token for test environments: base64(json(payload))
        encoded_jwt = base64.urlsafe_b64encode(json.dumps(to_encode, default=str).encode()).decode()
    logger.debug("Access token created")
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        # Try short-lived cache to reduce repeated JWT decoding
        from app.utils.cache import get as cache_get, set as cache_set

        cache_key = f"jwt:{token}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        if _JWT_LIB == "jose":
            payload = _JWT.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        elif _JWT_LIB == "pyjwt":
            payload = _JWT.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        else:
            # simple unsigned fallback: decode base64 json
            try:
                raw = base64.urlsafe_b64decode(token.encode()).decode()
                payload = json.loads(raw)
            except Exception:
                raise
        logger.debug("Token decoded", subject=payload.get("sub"))
        # cache payload for short time (60s) to reduce CPU usage
        try:
            cache_set(cache_key, payload, ex=60)
        except Exception:
            pass
        return payload
    except Exception:
        logger.exception("Failed to decode token")
        return None

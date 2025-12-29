from datetime import datetime, timedelta
import jwt

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
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug("Access token created")
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug("Token decoded", subject=payload.get("sub"))
        return payload
    except Exception:
        logger.exception("Failed to decode token")
        return None

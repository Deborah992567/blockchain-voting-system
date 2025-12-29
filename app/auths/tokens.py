# app/auth/tokens.py
from itsdangerous import URLSafeTimedSerializer
from app.config import settings
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="auth.tokens")

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def generate_token(email: str) -> str:
    logger.debug("Generating token", email=email)
    token = serializer.dumps(email, salt="email-token")
    logger.debug("Token generated", token=token)
    return token


def verify_token(token: str, max_age=3600):
    logger.debug("Verifying token", token=token)
    try:
        # Try cache first
        from app.utils.cache import get as cache_get, set as cache_set

        cache_key = f"email_token:{token}"
        cached = cache_get(cache_key)
        if cached:
            logger.debug("Token found in cache", email=cached)
            return cached

        email = serializer.loads(token, salt="email-token", max_age=max_age)
        logger.debug("Token valid", email=email)
        try:
            cache_set(cache_key, email, ex=max_age)
        except Exception:
            logger.exception("Failed to cache token")
        return email
    except Exception:
        logger.exception("Token verification failed", token=token)
        raise

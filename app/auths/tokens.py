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
        email = serializer.loads(token, salt="email-token", max_age=max_age)
        logger.debug("Token valid", email=email)
        return email
    except Exception:
        logger.exception("Token verification failed", token=token)
        raise

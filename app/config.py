"""Application configuration with Pydantic compatibility across v1/v2.

This module attempts to import BaseSettings from whichever package
is available so importing `app` during tests doesn't fail when the
environment has Pydantic v2 (where BaseSettings moved to
`pydantic-settings`).
"""
import os
from typing import Any, Optional

try:
    # Pydantic v1 (and modern v2 backwards compat in some envs)
    from pydantic import BaseSettings  # type: ignore
except Exception:
    # Pydantic v2 moved settings to pydantic-settings package
    try:
        from pydantic_settings import BaseSettings  # type: ignore
    except Exception:  # pragma: no cover - fallback if neither is available
        # If neither pydantic.BaseSettings nor pydantic_settings.BaseSettings
        # is available (e.g., in minimal test envs), provide a tiny fallback
        # so importing `app` doesn't fail. This fallback will not provide
        # validation; it's meant purely for test/development runtime.
        class BaseSettings:  # type: ignore
            def __init__(self, **_: Any) -> None:  # pragma: no cover - runtime fallback
                # nothing to do; Settings class will have class-level defaults
                return


class Settings(BaseSettings):
    # Core secrets
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    SECURITY_PASSWORD_SALT: str = os.getenv("SECURITY_PASSWORD_SALT", "")

    # Database
    # Prefer DATABASE_URL in the environment or .env
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Admin / blockchain
    ADMIN_ADDRESS: str = ""
    ADMIN_PRIVATE_KEY: str = ""
    RPC_URL: str = os.getenv("RPC_URL", "http://127.0.0.1:7545")  # Ganache / local node

    # Email / SendGrid settings
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    EMAIL_RETRY_MAX_ATTEMPTS: int = int(os.getenv("EMAIL_RETRY_MAX_ATTEMPTS", "5"))
    EMAIL_RETRY_BASE_DELAY_SECONDS: int = int(os.getenv("EMAIL_RETRY_BASE_DELAY_SECONDS", "60"))

    # OAuth settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Metrics & alerting
    METRICS_ENABLED: bool = bool(int(os.getenv("METRICS_ENABLED", "1")))
    SLACK_WEBHOOK_URL: str = ""

    # Database logging: default computed after instantiation
    DATABASE_LOGGING: Optional[bool] = None

    # Pydantic v1 env file support
    class Config:  # type: ignore
        env_file = ".env"
        env_file_encoding = "utf-8"

    # Pydantic v2 compatibility: allow model_config if present
    try:  # pragma: no cover - backwards compat
        model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    except Exception:
        pass


settings = Settings()

# If DATABASE_LOGGING wasn't explicitly set in env, compute a sensible default
if settings.DATABASE_LOGGING is None:
    env_db_logging = os.getenv("DATABASE_LOGGING")
    if env_db_logging is not None and env_db_logging != "":
        try:
            settings.DATABASE_LOGGING = bool(int(env_db_logging))
        except Exception:
            settings.DATABASE_LOGGING = env_db_logging.lower() in ("1", "true", "yes")
    else:
        settings.DATABASE_LOGGING = True if "postgresql" in settings.DATABASE_URL else False


# Backwards compatibility: some modules expect BLOCKCHAIN_RPC_URL
if not hasattr(settings, "BLOCKCHAIN_RPC_URL"):
    try:
        settings.BLOCKCHAIN_RPC_URL = getattr(settings, "RPC_URL")
    except Exception:
        settings.BLOCKCHAIN_RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:7545")


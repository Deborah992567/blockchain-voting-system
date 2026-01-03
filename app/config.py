"""Application configuration with Pydantic compatibility across v1/v2.

This module attempts to import BaseSettings from whichever package
is available so importing `app` during tests doesn't fail when the
environment has Pydantic v2 (where BaseSettings moved to
`pydantic-settings`).
"""
import os
from typing import Any

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
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    SECURITY_PASSWORD_SALT: str = os.getenv("SECURITY_PASSWORD_SALT", "mysalt")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/voting_db"
    )
    ADMIN_ADDRESS: str = os.getenv("ADMIN_ADDRESS", "")
    ADMIN_PRIVATE_KEY: str = os.getenv("ADMIN_PRIVATE_KEY", "")
    RPC_URL: str = os.getenv("RPC_URL", "http://127.0.0.1:7545")  # Ganache

    # Email / SendGrid settings
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "no-reply@example.com")
    EMAIL_RETRY_MAX_ATTEMPTS: int = int(os.getenv("EMAIL_RETRY_MAX_ATTEMPTS", "5"))
    EMAIL_RETRY_BASE_DELAY_SECONDS: int = int(
        os.getenv("EMAIL_RETRY_BASE_DELAY_SECONDS", "60")
    )

    # OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Metrics & alerting
    METRICS_ENABLED: bool = bool(int(os.getenv("METRICS_ENABLED", "1")))
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")


settings = Settings()

# Backwards compatibility: some modules expect BLOCKCHAIN_RPC_URL
if not hasattr(settings, "BLOCKCHAIN_RPC_URL"):
    try:
        settings.BLOCKCHAIN_RPC_URL = getattr(settings, "RPC_URL")
    except Exception:
        settings.BLOCKCHAIN_RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:7545")


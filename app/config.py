from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "12345trdfghjkiuytresxcvbnm67890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5

settings = Settings()

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    SECURITY_PASSWORD_SALT: str = os.getenv("SECURITY_PASSWORD_SALT", "mysalt")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:Echolacc11@localhost:5432/voting_db")
    ADMIN_ADDRESS: str = os.getenv("ADMIN_ADDRESS", "")
    ADMIN_PRIVATE_KEY: str = os.getenv("ADMIN_PRIVATE_KEY", "")
    RPC_URL: str = os.getenv("RPC_URL", "http://127.0.0.1:7545")  # Ganache
    # Email / SendGrid settings
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "no-reply@example.com")
    EMAIL_RETRY_MAX_ATTEMPTS: int = int(os.getenv("EMAIL_RETRY_MAX_ATTEMPTS", "5"))
    EMAIL_RETRY_BASE_DELAY_SECONDS: int = int(os.getenv("EMAIL_RETRY_BASE_DELAY_SECONDS", "60"))
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


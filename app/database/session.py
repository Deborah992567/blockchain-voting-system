from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.utils.logger import logger as base_logger
import os

logger = base_logger.bind(context="db.session")

# Use DATABASE_URL from env/config, or fallback to SQLite for local dev
DATABASE_URL = settings.DATABASE_URL or os.getenv("DATABASE_URL") or "sqlite:///./dev.db"

if not DATABASE_URL or DATABASE_URL == "":
    DATABASE_URL = "sqlite:///./dev.db"
    logger.warning("DATABASE_URL not set; using local SQLite for development")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    logger.debug("DB session opened")
    try:
        yield db
    finally:
        db.close()
        logger.debug("DB session closed")

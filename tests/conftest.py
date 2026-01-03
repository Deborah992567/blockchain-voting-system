import os
import sys
from pathlib import Path


# Ensure the backend package root is on sys.path so tests can import `app` both
# when run from the repo root or from the backend directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Set safe defaults at import time so modules that read env vars during import
# (like `app.config` / `app.database.session`) pick them up correctly.
# Use a file-backed SQLite DB by default for tests to avoid multiple-connection
# issues with ':memory:' databases (which create isolated DBs per connection).
os.environ.setdefault("DATABASE_URL", "sqlite:///./.pytest_test.db")
os.environ.setdefault("METRICS_ENABLED", "0")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("TESTING", "1")


def pytest_configure(config):
    # Use an in-memory SQLite DB for tests by default to avoid external deps
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    # Disable external metrics by default to avoid optional import problems
    os.environ.setdefault("METRICS_ENABLED", "0")
    # Use a short token secret for tests
    os.environ.setdefault("SECRET_KEY", "test-secret")
    # Signal test environment so modules that perform external checks can skip
    os.environ.setdefault("TESTING", "1")

    # Create DB tables for the in-memory SQLite DB so tests can run
    try:
        # Ensure all models are imported so SQLAlchemy metadata is populated
        try:
            import importlib

            importlib.import_module("app.models.user")
            importlib.import_module("app.models.election")
            importlib.import_module("app.models.candidate")
            importlib.import_module("app.models.vote")
        except Exception:
            # If models fail to import, let create_all attempt anyway and tests will fail clearly
            pass

        from app.database.base import Base
        from app.database.session import engine

        # Ensure a clean DB at the start of test sessions
        try:
            Base.metadata.drop_all(bind=engine)
        except Exception:
            pass

        Base.metadata.create_all(bind=engine)
    except Exception:
        # If creation fails, let tests handle it (useful when running with a real DB)
        pass


def pytest_unconfigure(config):
    # Drop tables to clean up after tests (best-effort)
    try:
        from app.database.base import Base
        from app.database.session import engine
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass


import pytest


@pytest.fixture(autouse=True)
def ensure_tables():
    """Create (and later drop) all tables for each test to ensure a clean DB.

    Using an autouse fixture ensures tables exist before any test uses the
    database, avoiding "no such table" operational errors in isolated
    in-memory SQLite environments.
    """
    # Import models first so metadata is complete
    try:
        import importlib

        importlib.import_module("app.models.user")
        importlib.import_module("app.models.election")
        importlib.import_module("app.models.candidate")
        importlib.import_module("app.models.vote")
    except Exception:
        pass

    from app.database.base import Base
    from app.database.session import engine

    Base.metadata.create_all(bind=engine)
    yield
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        pass

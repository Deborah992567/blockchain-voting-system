import os
import sys
from pathlib import Path


# Ensure backend package is importable when running pytest from repo root
ROOT = Path(__file__).resolve()
BACKEND = ROOT.joinpath("backend")
if BACKEND.exists() and str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def pytest_configure(config):
    # Default to an in-memory DB to keep tests hermetic
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("METRICS_ENABLED", "0")
    os.environ.setdefault("SECRET_KEY", "test-secret")

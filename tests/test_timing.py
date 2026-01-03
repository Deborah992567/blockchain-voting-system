import sys
from pathlib import Path
import pytest

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Backend is alive!"}

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.app import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("ASAAS_API_URL", "https://sandbox.asaas.com/api/v3")
    monkeypatch.setenv("ASAAS_API_KEY", "test_api_key")
    monkeypatch.setenv("FLASK_TESTING", "true")


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client

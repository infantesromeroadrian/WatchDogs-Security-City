"""Test-wide environment: no cache masking, fast retries. Set before app modules import."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import secrets
import tempfile

_tmp = tempfile.mkdtemp(prefix="watchdogs-tests-")
os.environ.setdefault("ADMIN_USERNAME", "tester")
# Credentials are generated per run: no secret-looking literals live in the repository.
TEST_USER = "tester"
# (stored in the environment so every import of this module in the process agrees on the value)
TEST_PASSWORD = os.environ.setdefault("WD_TEST_PASSWORD", "Aa1-" + secrets.token_urlsafe(18))
os.environ["ADMIN_PASSWORD"] = TEST_PASSWORD
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(32))
os.environ.setdefault("AUTH_STORAGE_FILE", os.path.join(_tmp, "auth.json"))
os.environ.setdefault("LLM_BUDGET_DB", os.path.join(_tmp, "budget.sqlite3"))
os.environ.setdefault("CACHE_ENABLED", "false")
os.environ.setdefault("AGENT_RETRY_MIN_WAIT", "0.05")
os.environ.setdefault("AGENT_RETRY_MAX_WAIT", "0.1")
os.environ.setdefault("FLASK_ENV", "production")


import pytest  # noqa: E402


def login(client, username=TEST_USER, password=TEST_PASSWORD):
    """Log a Flask test client in (session cookie is kept by the client)."""
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["session_token"]


@pytest.fixture
def auth_client():
    """A Flask test client that is already authenticated."""
    from src.backend.app import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        login(client)
        yield client


@pytest.fixture(autouse=True, scope="session")
def _no_rate_limit():
    """Rate limits are exercised explicitly in test_security.py; elsewhere they only add noise."""
    from src.backend import app as app_module

    app_module.limiter.enabled = False
    yield
    app_module.limiter.enabled = True


def _tiny_jpeg_b64() -> str:
    """A valid 64x64 JPEG as a data URI."""
    import base64
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (120, 160, 200)).save(buf, "JPEG")
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture(autouse=True)
def _reset_lockout():
    """Failed-login tests must not leave the shared test account locked for the next test."""
    yield
    from src.backend.services.auth import auth_service

    user = auth_service.users.get("tester")
    if user:
        user["failed_login_attempts"] = 0
        user["locked_until"] = None

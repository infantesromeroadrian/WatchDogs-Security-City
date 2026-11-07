"""Security controls: authentication, budget, limits, janitor, logging, CORS (offline)."""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import TEST_PASSWORD, TEST_USER, login
from stub_llm import StubLLM

from src.backend import config
from src.backend.app import app
from src.backend.services import llm_budget
from src.backend.services.auth.session_manager import SessionManager
from src.backend.utils.log_redaction import RedactingFilter, redact

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = {"/api/health", "/api/auth/login", "/login", "/favicon.ico"}


@pytest.fixture
def anon():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --------------------------------------------------------------- authentication
class TestAuthentication:
    def test_analysis_endpoints_return_401_without_credentials(self, anon):
        """Definition of done: no credentials -> 401 on every analysis endpoint."""
        for path in ("/api/analyze-frame", "/api/analyze-frame-stream", "/api/analyze-batch", "/api/chat-query"):
            response = anon.post(path, json={"frame": "x"})
            assert response.status_code == 401, path

    def test_every_route_is_protected_deny_by_default(self, anon):
        """Enumerate the URL map: anything not explicitly public must refuse anonymous access."""
        checked = 0
        for rule in app.url_map.iter_rules():
            if rule.endpoint == "static" or rule.rule in PUBLIC:
                continue
            url = rule.rule
            for arg in rule.arguments:
                url = url.replace(f"<{arg}>", "x").replace(f"<string:{arg}>", "x")
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                response = anon.open(url, method=method, json={} if method == "POST" else None)
                assert response.status_code in (401, 302), f"{method} {rule.rule} -> {response.status_code}"
                checked += 1
        assert checked >= 12

    def test_spa_redirects_to_login(self, anon):
        response = anon.get("/")
        assert response.status_code == 302 and response.headers["Location"].endswith("/login")
        assert anon.get("/login").status_code == 200

    def test_health_is_public_and_minimal(self, anon):
        data = anon.get("/api/health").get_json()
        assert "llm_model" not in data["checks"]

    def test_bad_credentials(self, anon):
        assert anon.post("/api/auth/login", json={"username": "tester", "password": "nope"}).status_code == 401
        assert anon.post("/api/auth/login", json={"username": "ghost", "password": "x"}).status_code == 401
        assert anon.post("/api/auth/login", json={"username": 1, "password": 2}).status_code == 400
        assert anon.post("/api/auth/login", json={"username": "a" * 999, "password": "b"}).status_code == 401

    def test_cookie_session_is_httponly_samesite_strict(self, anon):
        response = anon.post("/api/auth/login", json={"username": TEST_USER, "password": TEST_PASSWORD})
        cookie = response.headers["Set-Cookie"]
        assert "HttpOnly" in cookie and "SameSite=Strict" in cookie and "Secure" in cookie

    def test_bearer_token_and_logout_revocation(self, anon):
        token = login(anon)
        anon.delete_cookie(config.AUTH_COOKIE_NAME)
        headers = {"Authorization": f"Bearer {token}"}
        assert anon.get("/api/auth/me", headers=headers).status_code == 200
        assert anon.post("/api/auth/logout", headers=headers).status_code == 200
        assert anon.get("/api/auth/me", headers=headers).status_code == 401

    def test_tampered_and_expired_tokens(self, anon):
        token = login(anon)
        anon.delete_cookie(config.AUTH_COOKIE_NAME)
        assert anon.get("/api/auth/me", headers={"Authorization": f"Bearer {token[:-3]}xyz"}).status_code == 401
        short = SessionManager(secret_key=os.environ["FLASK_SECRET_KEY"], max_age_seconds=1)
        expiring = short.create_session("tester", "admin")
        time.sleep(2.1)
        assert short.validate_session(expiring) is None

    def test_cross_origin_post_with_cookie_is_refused(self, anon):
        login(anon)
        evil = anon.post("/api/analyze-frame", json={}, headers={"Origin": "https://evil.example"})
        assert evil.status_code == 403
        site = anon.post("/api/analyze-frame", json={}, headers={"Sec-Fetch-Site": "cross-site"})
        assert site.status_code == 403
        same = anon.post("/api/analyze-frame", json={}, headers={"Sec-Fetch-Site": "same-origin"})
        assert same.status_code == 400  # authenticated; fails later on the empty body

    def test_login_is_rate_limited(self, anon):
        from src.backend import app as app_module

        app_module.limiter.enabled = True
        try:
            codes = [
                anon.post("/api/auth/login", json={"username": "tester", "password": "bad"}).status_code
                for _ in range(8)
            ]
        finally:
            app_module.limiter.enabled = False
        assert 429 in codes

    def test_no_default_or_generated_credentials(self):
        """Refuses to start without ADMIN_PASSWORD, with a weak one, or unauthenticated in production."""
        env = {k: v for k, v in os.environ.items() if k not in ("ADMIN_PASSWORD", "AUTH_STORAGE_FILE")}
        env.update(PYTHONPATH=str(ROOT), AUTH_STORAGE_FILE="/nonexistent/none.json")
        code = "from src.backend.services.auth.auth_service import AuthService; AuthService()"

        def run(e):
            return subprocess.run([sys.executable, "-c", code], env=e, capture_output=True, text=True, cwd=ROOT)

        no_pw = run(env)
        assert no_pw.returncode != 0 and "ADMIN_PASSWORD is not set" in no_pw.stderr
        weak = run({**env, "ADMIN_PASSWORD": "short"})
        assert weak.returncode != 0 and "rejected" in weak.stderr
        prod = run({**env, "AUTH_ENABLED": "false", "FLASK_ENV": "production"})
        assert prod.returncode != 0 and "not allowed in production" in prod.stderr


# ------------------------------------------------------------------ LLM budget
class TestBudget:
    def test_reserve_enforces_global_and_user_caps(self, tmp_path):
        budget = llm_budget.DailyBudget(str(tmp_path / "b.sqlite3"), global_limit=5, per_user_limit=3)
        budget.reserve(3, "alice")
        with pytest.raises(llm_budget.BudgetExceeded) as exc:
            budget.reserve(1, "alice")
        assert exc.value.scope == "user:alice"
        budget.reserve(2, "bob")
        with pytest.raises(llm_budget.BudgetExceeded) as exc:
            budget.reserve(1, "bob")
        assert exc.value.scope == "global"
        assert budget.used("global") == 5  # failed reserves consumed nothing

    def test_counter_survives_new_instance(self, tmp_path):
        path = str(tmp_path / "b.sqlite3")
        llm_budget.DailyBudget(path, 10, 10).reserve(4, "u")
        assert llm_budget.DailyBudget(path, 10, 10).used("global") == 4

    def test_check_does_not_consume(self, tmp_path):
        budget = llm_budget.DailyBudget(str(tmp_path / "b.sqlite3"), 10, 10)
        budget.check(10, "u")
        assert budget.used("global") == 0
        with pytest.raises(llm_budget.BudgetExceeded):
            budget.check(11, "u")

    def test_api_returns_429_with_retry_after(self, auth_client, monkeypatch, tmp_path):
        monkeypatch.setattr(llm_budget, "_budget", llm_budget.DailyBudget(str(tmp_path / "b.sqlite3"), 5, 5))
        from conftest import _tiny_jpeg_b64

        response = auth_client.post("/api/analyze-frame", json={"frame": _tiny_jpeg_b64()})
        assert response.status_code == 429
        assert int(response.headers["Retry-After"]) > 0

    def test_llm_layer_hard_stop_with_principal_from_request_context(self, monkeypatch, tmp_path):
        """Even without the API pre-check, the provider is never called past the cap."""
        monkeypatch.setattr(llm_budget, "_budget", llm_budget.DailyBudget(str(tmp_path / "b.sqlite3"), 2, 2))
        monkeypatch.setattr(config, "LLM_PROVIDER", "custom")
        monkeypatch.setattr(config, "OPENAI_API_KEY", "k")
        monkeypatch.setattr(config, "OPENAI_MODEL", "m")
        from src.backend.llm import build_chat_model

        with StubLLM() as stub:
            monkeypatch.setattr(config, "OPENAI_BASE_URL", stub.url)
            llm = build_chat_model()
            llm.invoke("a")
            llm.invoke("b")
            with pytest.raises(llm_budget.BudgetExceeded):
                llm.invoke("c")
            assert stub.requests == 2

    def test_principal_propagates_into_langgraph_workers(self, monkeypatch, tmp_path):
        from conftest import _tiny_jpeg_b64
        from src.backend.agents.coordinator import CoordinatorAgent

        budget = llm_budget.DailyBudget(str(tmp_path / "b.sqlite3"), 1000, 1000)
        monkeypatch.setattr(llm_budget, "_budget", budget)
        monkeypatch.setattr(config, "LLM_PROVIDER", "custom")
        monkeypatch.setattr(config, "OPENAI_API_KEY", "k")
        monkeypatch.setattr(config, "OPENAI_MODEL", "m")
        with StubLLM() as stub:
            monkeypatch.setattr(config, "OPENAI_BASE_URL", stub.url)
            coordinator = CoordinatorAgent()
            token = llm_budget.current_principal.set("alice")
            try:
                coordinator.analyze_frame(_tiny_jpeg_b64(), "")
            finally:
                llm_budget.current_principal.reset(token)
        assert budget.used("user:alice") >= 16
        assert budget.used("user:alice") == budget.used("global")


# ------------------------------------------------------------- upload limits
class TestLimits:
    def test_json_body_too_large(self, auth_client, monkeypatch):
        monkeypatch.setattr(config, "MAX_JSON_BODY_MB", 1)
        big = '{"frame": "' + "A" * (2 * 1024 * 1024) + '"}'
        response = auth_client.post("/api/analyze-frame", data=big, content_type="application/json")
        assert response.status_code == 413

    def test_frame_over_per_image_cap(self, auth_client, monkeypatch):
        from src.backend.api import analysis_routes

        monkeypatch.setattr(analysis_routes, "MAX_BASE64_SIZE_BYTES", 1000)
        response = auth_client.post("/api/analyze-frame", json={"frame": "data:image/jpeg;base64," + "A" * 5000})
        assert response.status_code == 413

    def test_video_over_cap(self, auth_client, monkeypatch):
        monkeypatch.setattr(config, "MAX_VIDEO_SIZE_BYTES", 100)
        from io import BytesIO

        response = auth_client.post(
            "/api/upload-video",
            data={"video": (BytesIO(b"\x00" * 1000), "x.mp4")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 413

    def test_errors_do_not_leak_internals(self, auth_client):
        response = auth_client.post("/api/generate-pdf-report", json={"analysis_results": "not-a-dict"})
        assert response.status_code in (400, 500)
        assert "Traceback" not in response.get_data(as_text=True)


# -------------------------------------------------- retention / no persistence
class TestRetention:
    def test_janitor_removes_expired_videos_and_sessions(self, monkeypatch, tmp_path):
        from src.backend.services import janitor
        from src.backend.services import video_service as vs
        from src.backend.services.session_store import SessionImageStore

        monkeypatch.setattr(vs, "TEMP_VIDEO_PATH", tmp_path)
        old, fresh = tmp_path / "old.mp4", tmp_path / "fresh.mp4"
        old.write_bytes(b"x")
        fresh.write_bytes(b"x")
        past = time.time() - 3 * 3600
        os.utime(old, (past, past))
        monkeypatch.setattr(config, "VIDEO_RETENTION_HOURS", 1)
        store = SessionImageStore(ttl_seconds=0)
        monkeypatch.setattr(janitor, "session_store", store)
        store.create_session()
        time.sleep(0.01)
        counts = janitor.run_once()
        assert counts["videos"] == 1 and not old.exists() and fresh.exists()
        assert counts["sessions"] == 1 and store.active_session_count == 0

    def test_evicting_a_session_purges_its_chat_thread(self):
        from src.backend.services.session_store import SessionImageStore

        store = SessionImageStore()
        purged = []
        store.add_eviction_listener(purged.append)
        sid = store.create_session()
        thread_id = store.get_thread_id(sid)
        store.delete_session(sid)
        assert purged == [thread_id]

    def test_analysis_graph_is_not_checkpointed(self):
        from src.backend.agents.coordinator import CoordinatorAgent

        assert CoordinatorAgent().graph.checkpointer is None


# --------------------------------------------------------------------- logging
class TestLogRedaction:
    def test_redact_patterns(self):
        blob = "A" * 300
        text = redact(f"frame data:image/jpeg;base64,{blob} auth Bearer abc.def.ghi mail a.b@x.org {blob}")
        assert blob not in text
        assert "abc.def.ghi" not in text and "a.b@x.org" not in text
        assert "[image data redacted]" in text

    def test_filter_applies_to_formatted_records(self):
        record = logging.LogRecord("t", logging.INFO, "f", 1, "image: %s", ("data:image/png;base64," + "B" * 500,), None)
        RedactingFilter().filter(record)
        assert "BBBB" not in record.getMessage()

    def test_app_installs_filter_on_root_handlers(self):
        root = logging.getLogger()
        assert any(any(isinstance(f, RedactingFilter) for f in h.filters) for h in root.handlers)


# ------------------------------------------------------------------------ CORS
class TestCors:
    def test_no_cross_origin_access_by_default(self, auth_client):
        response = auth_client.get("/api/auth/me", headers={"Origin": "https://evil.example"})
        assert "Access-Control-Allow-Origin" not in response.headers
        assert response.headers["Cache-Control"] == "no-store"

    def test_wildcard_origin_is_rejected(self):
        env = {**os.environ, "ALLOWED_ORIGINS": "*", "PYTHONPATH": str(ROOT)}
        run = subprocess.run([sys.executable, "-c", "import src.backend.config"], env=env, capture_output=True, text=True, cwd=ROOT)
        assert run.returncode != 0 and "not allowed" in run.stderr


class TestEvalIsolation:
    def test_eval_uses_its_own_unlimited_budget(self):
        """The evaluation must neither consume nor be stopped by the application's daily budget."""
        code = "import eval.run_eval, os; print(os.environ['LLM_BUDGET_DB'], os.environ['LLM_DAILY_CALL_LIMIT'])"
        run = subprocess.run([sys.executable, "-c", code], env={**os.environ, "PYTHONPATH": str(ROOT)},
                             capture_output=True, text=True, cwd=ROOT)
        db, limit = run.stdout.split()[-2:]
        assert db != os.environ["LLM_BUDGET_DB"] and int(limit) > 10**6

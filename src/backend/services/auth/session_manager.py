"""
Session management with signed, stateless tokens.

A token is an itsdangerous URL-safe timed signature over ``{u, r, j}`` (username, role, token id)
made with FLASK_SECRET_KEY. Because nothing is stored server-side, sessions survive worker
recycling and Render restarts. Logout adds the token id to an in-memory revocation set (best effort:
the set is lost on restart, but tokens expire after SESSION_HOURS anyway).
"""

import os
import secrets
import threading

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from ... import config


class SessionManager:
    """Issues and validates signed session tokens."""

    def __init__(self, secret_key: str | None = None, max_age_seconds: int | None = None):
        key = secret_key or os.environ.get("FLASK_SECRET_KEY")
        if not key:
            if config.IS_PRODUCTION:
                raise RuntimeError("FLASK_SECRET_KEY is required in production")
            key = secrets.token_hex(32)  # development: sessions die with the process
        self._serializer = URLSafeTimedSerializer(key, salt="watchdogs-session")
        self.max_age = max_age_seconds or int(config.SESSION_HOURS * 3600)
        self._revoked: set[str] = set()
        self._lock = threading.Lock()

    def create_session(self, username: str, role: str, ip_address: str | None = None) -> str:
        """Return a signed token (``ip_address`` is accepted for API compatibility, not bound)."""
        return self._serializer.dumps({"u": username, "r": role, "j": secrets.token_hex(8)})

    def validate_session(self, session_token: str, ip_address: str | None = None) -> dict | None:
        """Return ``{"username", "role"}`` for a valid, unexpired, unrevoked token; else None."""
        if not session_token:
            return None
        try:
            data = self._serializer.loads(session_token, max_age=self.max_age)
        except (BadSignature, SignatureExpired):
            return None
        with self._lock:
            if data.get("j") in self._revoked:
                return None
        return {"username": data["u"], "role": data["r"]}

    def logout(self, session_token: str) -> bool:
        """Revoke a token. True if it was valid."""
        try:
            data = self._serializer.loads(session_token, max_age=self.max_age)
        except (BadSignature, SignatureExpired):
            return False
        with self._lock:
            self._revoked.add(data["j"])
        return True

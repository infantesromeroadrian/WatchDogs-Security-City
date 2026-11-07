"""
Authentication guard (deny by default).

``init_auth(app)`` installs a ``before_request`` hook that requires a valid session for EVERY
route except an explicit allow-list (health check, login, login page, static assets). New routes
are therefore protected automatically; ``auth_required`` is kept as a decorator so existing
routes still read naturally, but it only asserts that the guard has authenticated the request.

A session is accepted from ``Authorization: Bearer <token>`` or from the HttpOnly,
SameSite=Strict ``wd_session`` cookie (needed for ``<video>`` elements, which cannot send headers).
Cookie-authenticated state-changing requests must also be same-origin.
"""

import hashlib
import logging
from functools import wraps
from typing import Any
from urllib.parse import urlparse

from flask import Flask, Response, g, jsonify, redirect, request

from .. import config
from ..services.llm_budget import current_principal

logger = logging.getLogger(__name__)

PUBLIC_EXACT = {"/api/health", "/api/auth/login", "/login", "/favicon.ico"}
PUBLIC_PREFIXES = ("/static/",)
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _ip_tag() -> str:
    """Short salted hash of the client IP: lets logs correlate attempts without storing the IP."""
    raw = (request.remote_addr or "unknown").encode()
    return hashlib.sha256(b"wd-ip:" + raw).hexdigest()[:8]


def _extract_token() -> tuple[str | None, str]:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header.removeprefix("Bearer ").strip(), "bearer"
    cookie = request.cookies.get(config.AUTH_COOKIE_NAME)
    return (cookie, "cookie") if cookie else (None, "none")


def _same_origin() -> bool:
    """CSRF defence for cookie-authenticated unsafe requests."""
    site = request.headers.get("Sec-Fetch-Site")
    if site is not None:
        return site in ("same-origin", "none")
    origin = request.headers.get("Origin")
    if origin is None:
        return True  # non-browser client
    allowed = {request.host_url.rstrip("/"), *config.ALLOWED_ORIGINS}
    parsed = urlparse(origin)
    return f"{parsed.scheme}://{parsed.netloc}" in allowed


def _is_public(path: str) -> bool:
    return path in PUBLIC_EXACT or path.startswith(PUBLIC_PREFIXES)


def _deny(path: str) -> Response | tuple[Response, int]:
    if path.startswith("/api/"):
        return jsonify({"success": False, "error": "Authentication required"}), 401
    return redirect("/login", code=302)


def guard() -> Response | tuple[Response, int] | None:
    """before_request hook: authenticate, size-limit, set the LLM-budget principal."""
    path = request.path

    # Body size: only the video upload may be large; everything else is capped (DoS guard)
    limit = config.MAX_VIDEO_SIZE_BYTES if path == "/api/upload-video" else config.MAX_JSON_BODY_MB * 1024 * 1024
    if request.content_length is not None and request.content_length > limit:
        return jsonify({"success": False, "error": "Request body too large"}), 413

    if _is_public(path):
        return None
    if not config.AUTH_ENABLED:  # local development only (refused in production at startup)
        g.auth_session = {"username": "dev", "role": "admin"}
        current_principal.set("dev")
        return None

    from ..services.auth import auth_service  # lazy: avoids import cycle at load time

    token, source = _extract_token()
    session = auth_service.validate_session(token) if token else None
    if session is None:
        logger.warning("Unauthenticated request to %s (client %s)", path, _ip_tag())
        return _deny(path)
    if source == "cookie" and request.method not in SAFE_METHODS and not _same_origin():
        logger.warning("Cross-origin request blocked on %s (client %s)", path, _ip_tag())
        return jsonify({"success": False, "error": "Cross-origin request refused"}), 403

    g.auth_session = session
    current_principal.set(session["username"])
    return None


def init_auth(app: Flask) -> None:
    """Install the deny-by-default guard (and clear the per-request LLM principal afterwards)."""
    app.before_request(guard)

    @app.teardown_request
    def _clear_principal(_exc: BaseException | None) -> None:
        current_principal.set(None)


def auth_required(f: Any) -> Any:
    """Marker decorator: the route needs a session (enforced globally by ``guard``)."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        if config.AUTH_ENABLED and not getattr(g, "auth_session", None):
            return jsonify({"success": False, "error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated

"""
Authentication middleware for API endpoints.

Provides an ``auth_required`` decorator that validates Bearer tokens
via the existing ``AuthService.validate_session()`` infrastructure.

Behaviour is controlled by the ``AUTH_ENABLED`` config flag:
  - ``AUTH_ENABLED=True``  → enforces authentication on decorated routes
  - ``AUTH_ENABLED=False`` → decorator is a transparent no-op (local dev)
"""

import logging
from functools import wraps
from typing import Any

from flask import jsonify, request

from ..config import AUTH_ENABLED

logger = logging.getLogger(__name__)


def auth_required(f: Any) -> Any:
    """Decorator that enforces Bearer-token authentication.

    When ``AUTH_ENABLED`` is ``True``, the request must carry a valid
    ``Authorization: Bearer <token>`` header.  The token is validated
    against ``auth_service.validate_session()``.

    On success the decoded session dict is stored in
    ``request.auth_session`` for downstream use.

    When ``AUTH_ENABLED`` is ``False`` the decorator is a no-op so that
    local development is frictionless.

    Usage::

        @analysis_bp.route("/analyze-frame", methods=["POST"])
        @auth_required
        def analyze_frame():
            ...
    """

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        if not AUTH_ENABLED:
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(
                "Unauthenticated request to %s from %s",
                request.path,
                request.remote_addr,
            )
            return (
                jsonify({"success": False, "error": "Authentication required"}),
                401,
            )

        token = auth_header.removeprefix("Bearer ")

        # Lazy import to avoid circular dependency at module load time
        from ..services.auth import auth_service

        session = auth_service.validate_session(token, request.remote_addr)

        if not session:
            logger.warning(
                "Invalid/expired token on %s from %s",
                request.path,
                request.remote_addr,
            )
            return (
                jsonify({"success": False, "error": "Invalid or expired session"}),
                401,
            )

        # Attach session info for downstream handlers
        request.auth_session = session  # type: ignore[attr-defined]
        return f(*args, **kwargs)

    return decorated

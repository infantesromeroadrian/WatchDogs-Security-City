"""
Authentication routes: login, logout, whoami.

Login sets an HttpOnly + SameSite=Strict session cookie (and also returns the token for API
clients that prefer ``Authorization: Bearer``).
"""

import logging

from flask import Blueprint, g, jsonify, make_response, request

from .. import config
from ..services.auth import auth_service
from .middleware import _extract_token

logger = logging.getLogger(__name__)

# Blueprint
auth_bp = Blueprint("auth", __name__)

_MAX_FIELD = 256


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Expected JSON: {"username": "...", "password": "..."}
    Returns: session token (also set as cookie).
    """
    data = request.get_json(silent=True)
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("username"), str)
        or not isinstance(data.get("password"), str)
    ):
        return jsonify({"success": False, "error": "Missing username or password"}), 400
    username, password = data["username"], data["password"]
    if len(username) > _MAX_FIELD or len(password) > _MAX_FIELD:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    session_token = auth_service.authenticate(username, password)
    if not session_token:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    response = make_response(
        jsonify(
            {
                "success": True,
                "session_token": session_token,
                "user": auth_service.get_user_stats(username),
            }
        )
    )
    response.set_cookie(
        config.AUTH_COOKIE_NAME,
        session_token,
        max_age=int(config.SESSION_HOURS * 3600),
        httponly=True,
        secure=request.is_secure or config.IS_PRODUCTION,
        samesite="Strict",
        path="/",
    )
    return response, 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Revoke the current session and clear the cookie."""
    token, _source = _extract_token()
    if token:
        auth_service.logout(token)
    response = make_response(jsonify({"success": True, "message": "Logged out successfully"}))
    response.delete_cookie(config.AUTH_COOKIE_NAME, path="/", samesite="Strict")
    return response, 200


@auth_bp.route("/me", methods=["GET"])
def me():
    """Return the authenticated user (the global guard has already validated the session)."""
    session = getattr(g, "auth_session", None) or {}
    return jsonify({"success": True, "user": {"username": session.get("username"), "role": session.get("role")}})

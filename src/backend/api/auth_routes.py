"""
Authentication routes: login, logout
"""

import logging
from flask import Blueprint, request, jsonify

from ..services.auth import auth_service

logger = logging.getLogger(__name__)

# Blueprint
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User login endpoint.

    Expected JSON:
    {
        "username": "...",
        "password": "..."
    }

    Returns: Session token
    """
    try:
        data = request.get_json()

        if not data or "username" not in data or "password" not in data:
            return jsonify(
                {"success": False, "error": "Missing username or password"}
            ), 400

        username = data["username"]
        password = data["password"]

        # Authenticate
        session_token = auth_service.authenticate(username, password)

        if not session_token:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

        # Get user stats
        user_stats = auth_service.get_user_stats(username)

        return jsonify(
            {"success": True, "session_token": session_token, "user": user_stats}
        ), 200

    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    User logout endpoint.

    Headers:
    Authorization: Bearer <session_token>

    Returns: Success status
    """
    try:
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Missing authorization"}), 401

        session_token = auth_header.replace("Bearer ", "")

        # Logout
        auth_service.logout(session_token)

        return jsonify({"success": True, "message": "Logged out successfully"}), 200

    except Exception as e:
        logger.error(f"❌ Logout error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

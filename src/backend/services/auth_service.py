"""
Authentication Service
Basic multi-user authentication without external APIs
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class AuthService:
    """Simple authentication service with in-memory storage"""

    def __init__(self):
        # In-memory user storage (for production, use database)
        self.users = {}
        self.sessions = {}

        # Create default admin user
        self._create_default_admin()

    def _create_default_admin(self):
        """Create default admin user"""
        admin_username = "admin"
        admin_password = "watchdogs2026"  # CHANGE THIS IN PRODUCTION!

        self.register_user(admin_username, admin_password, role="admin")
        logger.info("🔐 Default admin user created (username: admin)")

    def hash_password(
        self, password: str, salt: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Hash password with salt.

        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (hashed_password, salt)
        """
        if not salt:
            salt = secrets.token_hex(32)

        # Use PBKDF2 for password hashing
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,  # iterations
        )

        return hashed.hex(), salt

    def register_user(
        self, username: str, password: str, role: str = "analyst"
    ) -> bool:
        """
        Register a new user.

        Args:
            username: Username
            password: Plain text password
            role: User role (admin, analyst, viewer)

        Returns:
            True if successful, False if user exists
        """
        if username in self.users:
            logger.warning(f"⚠️ User {username} already exists")
            return False

        hashed_pw, salt = self.hash_password(password)

        self.users[username] = {
            "password_hash": hashed_pw,
            "salt": salt,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "analysis_count": 0,
        }

        logger.info(f"✅ User registered: {username} ({role})")
        return True

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate user and create session.

        Args:
            username: Username
            password: Plain text password

        Returns:
            Session token if successful, None otherwise
        """
        if username not in self.users:
            logger.warning(f"⚠️ Authentication failed: user {username} not found")
            return None

        user = self.users[username]

        # Hash provided password with stored salt
        hashed_pw, _ = self.hash_password(password, user["salt"])

        # Compare hashes
        if hashed_pw != user["password_hash"]:
            logger.warning(f"⚠️ Authentication failed: invalid password for {username}")
            return None

        # Create session token
        session_token = secrets.token_urlsafe(32)

        self.sessions[session_token] = {
            "username": username,
            "role": user["role"],
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=24),
            "ip_address": None,  # Set from request
        }

        # Update last login
        user["last_login"] = datetime.now().isoformat()

        logger.info(f"✅ User authenticated: {username}")
        return session_token

    def validate_session(self, session_token: str) -> Optional[Dict]:
        """
        Validate session token.

        Args:
            session_token: Session token

        Returns:
            User info if valid, None otherwise
        """
        if session_token not in self.sessions:
            return None

        session = self.sessions[session_token]

        # Check expiration
        if datetime.now() > session["expires_at"]:
            del self.sessions[session_token]
            logger.info(f"🕐 Session expired for {session['username']}")
            return None

        return {"username": session["username"], "role": session["role"]}

    def logout(self, session_token: str) -> bool:
        """
        Logout user and invalidate session.

        Args:
            session_token: Session token

        Returns:
            True if successful
        """
        if session_token in self.sessions:
            username = self.sessions[session_token]["username"]
            del self.sessions[session_token]
            logger.info(f"👋 User logged out: {username}")
            return True

        return False

    def get_user_stats(self, username: str) -> Optional[Dict]:
        """Get user statistics"""
        if username not in self.users:
            return None

        user = self.users[username]
        return {
            "username": username,
            "role": user["role"],
            "created_at": user["created_at"],
            "last_login": user["last_login"],
            "analysis_count": user["analysis_count"],
        }

    def increment_analysis_count(self, username: str):
        """Increment user's analysis counter"""
        if username in self.users:
            self.users[username]["analysis_count"] += 1

    def check_permission(self, role: str, required_role: str) -> bool:
        """
        Check if role has required permission.

        Role hierarchy: admin > analyst > viewer
        """
        roles_hierarchy = {"admin": 3, "analyst": 2, "viewer": 1}

        user_level = roles_hierarchy.get(role, 0)
        required_level = roles_hierarchy.get(required_role, 0)

        return user_level >= required_level


# Global instance
auth_service = AuthService()

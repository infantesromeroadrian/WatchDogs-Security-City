"""
Main authentication service orchestrator
"""

import json
import logging
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path

from .lockout_manager import LockoutManager
from ... import config
from .password_handler import (
    LEGACY_ITERATIONS,
    PBKDF2_ITERATIONS,
    hash_password,
    validate_password_strength,
)
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class AuthService:
    """Security-hardened authentication service"""

    def __init__(self, storage_file: str | None = None):
        # Persistent storage
        self.storage_file = storage_file or os.getenv(
            "AUTH_STORAGE_FILE", "data/.auth_storage.json"
        )
        self.storage_path = Path(self.storage_file)

        # In-memory user storage
        self.users: dict = {}

        # Managers
        self.session_manager = SessionManager()
        self.lockout_manager = LockoutManager()

        # Load from disk
        self._load_from_disk()

        # The environment is the source of truth for the admin account
        if config.AUTH_ENABLED:
            self._sync_admin_from_env()

    def _load_from_disk(self):
        """Load users from persistent storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path) as f:
                    data = json.load(f)
                    self.users = data.get("users", {})
                    logger.info("✅ Loaded %s users from disk", len(self.users))
            else:
                logger.info("📝 No existing auth storage found, starting fresh")
        except (ValueError, TypeError, KeyError) as e:
            logger.error("❌ Error loading auth storage: %s", e)
            self.users = {}

    def _save_to_disk(self):
        """Save users to persistent storage with restrictive permissions."""
        try:
            # Create directory if it doesn't exist
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # H-5: Write with restrictive permissions (owner read/write only).
            # Use os.open + os.fdopen to set 0o600 atomically on creation.
            fd = os.open(
                str(self.storage_path),
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                0o600,
            )
            with os.fdopen(fd, "w") as f:
                json.dump({"users": self.users}, f, indent=2)

            logger.debug("💾 Auth data saved to disk")
        except (ValueError, TypeError, KeyError, OSError) as e:
            logger.error("❌ Error saving auth storage: %s", e)

    def _sync_admin_from_env(self) -> None:
        """Create/refresh the admin account from ADMIN_USERNAME / ADMIN_PASSWORD.

        No password is ever generated or printed: with auth enabled and no ADMIN_PASSWORD the
        application refuses to start (even if a stale storage file holds users), so a deployment
        can never come up open or with an unknown password. Re-running with a new ADMIN_PASSWORD rotates it.
        """
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD")
        if not password:
            raise RuntimeError(
                "ADMIN_PASSWORD is not set. Authentication is mandatory: set ADMIN_USERNAME and "
                "ADMIN_PASSWORD (12+ chars with upper/lower/digit, or 32+ random chars) in the environment."
            )
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            raise RuntimeError(f"ADMIN_PASSWORD rejected: {error_msg}")
        hashed_pw, salt = hash_password(password)
        existing = self.users.get(username, {})
        self.users[username] = {
            **existing,
            "password_hash": hashed_pw,
            "salt": salt,
            "iterations": PBKDF2_ITERATIONS,
            "role": "admin",
            "created_at": existing.get("created_at", datetime.now(UTC).isoformat()),
            "last_login": existing.get("last_login"),
            "analysis_count": existing.get("analysis_count", 0),
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        }
        self._save_to_disk()
        logger.info("🔐 Admin account provisioned from environment")

    def register_user(
        self, username: str, password: str, role: str = "analyst"
    ) -> tuple[bool, str]:
        """
        Register a new user with security validation.

        Args:
            username: Username
            password: Plain text password
            role: User role (admin, analyst, viewer)

        Returns:
            Tuple of (success, message)
        """
        # Validate username
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"

        if username in self.users:
            logger.warning("⚠️ Registration attempt for existing user: %s", username)
            return False, "User already exists"

        # Validate password strength
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            return False, error_msg

        # Validate role
        if role not in ["admin", "analyst", "viewer"]:
            return False, "Invalid role"

        # Hash password
        hashed_pw, salt = hash_password(password)

        # Create user
        self.users[username] = {
            "password_hash": hashed_pw,
            "salt": salt,
            "iterations": PBKDF2_ITERATIONS,
            "role": role,
            "created_at": datetime.now(UTC).isoformat(),
            "last_login": None,
            "analysis_count": 0,
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        }

        # Save to disk
        self._save_to_disk()

        logger.info("✅ User registered: %s (%s)", username, role)
        return True, "User registered successfully"

    def authenticate(
        self, username: str, password: str, ip_address: str | None = None
    ) -> str | None:
        """
        Authenticate user and create session.

        Args:
            username: Username
            password: Plain text password
            ip_address: Optional IP address for session binding

        Returns:
            Session token or None if authentication failed
        """
        # Check if user exists
        if username not in self.users:
            # Spend the same CPU as a real check so response time does not reveal valid usernames.
            hash_password(password, "0" * 64)
            logger.warning("⚠️ Authentication attempt for unknown user")
            return None

        user = self.users[username]

        # Check if account is active
        if not user.get("is_active", True):
            logger.warning("⚠️ Authentication attempt for disabled user")
            return None

        # Check account lockout
        is_locked, _lock_message = self.lockout_manager.check_lockout(user)
        if is_locked:
            return None

        # Hash provided password with stored salt
        hashed_pw, _ = hash_password(
            password, user["salt"], user.get("iterations", LEGACY_ITERATIONS)
        )

        # Compare hashes (constant-time comparison)
        if not secrets.compare_digest(hashed_pw, user["password_hash"]):
            logger.warning("⚠️ Failed login attempt")
            self.lockout_manager.record_failure(user, username)
            self._save_to_disk()
            return None

        # Reset failed attempts on successful login
        self.lockout_manager.reset_attempts(user)

        # Create session
        session_token = self.session_manager.create_session(username, user["role"], ip_address)

        # Update last login
        user["last_login"] = datetime.now(UTC).isoformat()
        self._save_to_disk()

        logger.info("✅ User authenticated")
        return session_token

    def validate_session(self, session_token: str, ip_address: str | None = None) -> dict | None:
        """Validate session token and make sure the account is still active."""
        session = self.session_manager.validate_session(session_token, ip_address)
        if session is None:
            return None
        user = self.users.get(session["username"])
        if user is None or not user.get("is_active", True):
            return None
        return session

    def logout(self, session_token: str) -> bool:
        """Logout user and invalidate session"""
        success = self.session_manager.logout(session_token)
        if success:
            logger.info("👋 User logged out")
        return success

    def get_user_stats(self, username: str) -> dict | None:
        """
        Get user statistics - SECURITY FIXED.

        Returns only safe, non-sensitive information.
        """
        if username not in self.users:
            return None

        user = self.users[username]

        # Return ONLY safe public data
        return {
            "username": username,
            "role": user["role"],
            "analysis_count": user.get("analysis_count", 0),
            "last_login": user.get("last_login"),
        }

    def increment_analysis_count(self, username: str):
        """Increment user's analysis counter"""
        if username in self.users:
            self.users[username]["analysis_count"] = (
                self.users[username].get("analysis_count", 0) + 1
            )
            self._save_to_disk()

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

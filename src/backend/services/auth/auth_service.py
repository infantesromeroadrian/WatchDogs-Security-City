"""
Main authentication service orchestrator
"""

import logging
import json
import os
import secrets
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path

from .password_handler import hash_password, validate_password_strength
from .session_manager import SessionManager
from .lockout_manager import LockoutManager

logger = logging.getLogger(__name__)


class AuthService:
    """Security-hardened authentication service"""

    def __init__(self, storage_file: Optional[str] = None):
        # Persistent storage
        self.storage_file = storage_file or os.getenv(
            "AUTH_STORAGE_FILE", "data/.auth_storage.json"
        )
        self.storage_path = Path(self.storage_file)

        # In-memory user storage
        self.users: Dict = {}

        # Managers
        self.session_manager = SessionManager()
        self.lockout_manager = LockoutManager()

        # Load from disk
        self._load_from_disk()

        # Create default admin if none exists
        if not self.users:
            self._create_default_admin()

    def _load_from_disk(self):
        """Load users from persistent storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.users = data.get("users", {})
                    logger.info(f"✅ Loaded {len(self.users)} users from disk")
            else:
                logger.info("📝 No existing auth storage found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Error loading auth storage: {e}")
            self.users = {}

    def _save_to_disk(self):
        """Save users to persistent storage"""
        try:
            # Create directory if it doesn't exist
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to disk
            with open(self.storage_path, "w") as f:
                json.dump({"users": self.users}, f, indent=2)

            logger.debug("💾 Auth data saved to disk")
        except Exception as e:
            logger.error(f"❌ Error saving auth storage: {e}")

    def _create_default_admin(self):
        """Create default admin user from environment variables"""
        # Get credentials from environment or use secure defaults
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if not admin_password:
            # Generate random password if none provided
            admin_password = secrets.token_urlsafe(16)
            logger.warning("⚠️ No ADMIN_PASSWORD set in environment!")
            logger.warning(f"🔐 Generated random password: {admin_password}")
            logger.warning("⚠️ SAVE THIS PASSWORD - it won't be shown again!")

        self.register_user(admin_username, admin_password, role="admin")
        logger.info(f"🔐 Default admin user created: {admin_username}")

    def register_user(
        self, username: str, password: str, role: str = "analyst"
    ) -> Tuple[bool, str]:
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
            logger.warning(f"⚠️ Registration attempt for existing user: {username}")
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
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "analysis_count": 0,
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        }

        # Save to disk
        self._save_to_disk()

        logger.info(f"✅ User registered: {username} ({role})")
        return True, "User registered successfully"

    def authenticate(
        self, username: str, password: str, ip_address: Optional[str] = None
    ) -> Optional[str]:
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
            logger.warning(
                f"⚠️ Authentication attempt for non-existent user: {username}"
            )
            # Don't reveal if user exists (security)
            return None

        user = self.users[username]

        # Check if account is active
        if not user.get("is_active", True):
            logger.warning(f"⚠️ Authentication attempt for disabled user: {username}")
            return None

        # Check account lockout
        is_locked, lock_message = self.lockout_manager.check_lockout(user)
        if is_locked:
            return None

        # Hash provided password with stored salt
        hashed_pw, _ = hash_password(password, user["salt"])

        # Compare hashes (constant-time comparison)
        if not secrets.compare_digest(hashed_pw, user["password_hash"]):
            logger.warning(f"⚠️ Failed login attempt for {username}")
            self.lockout_manager.record_failure(user, username)
            self._save_to_disk()
            return None

        # Reset failed attempts on successful login
        self.lockout_manager.reset_attempts(user)

        # Create session
        session_token = self.session_manager.create_session(
            username, user["role"], ip_address
        )

        # Update last login
        user["last_login"] = datetime.now().isoformat()
        self._save_to_disk()

        logger.info(
            f"✅ User authenticated: {username} from IP {ip_address or 'unknown'}"
        )
        return session_token

    def validate_session(
        self, session_token: str, ip_address: Optional[str] = None
    ) -> Optional[Dict]:
        """Validate session token"""
        return self.session_manager.validate_session(session_token, ip_address)

    def logout(self, session_token: str) -> bool:
        """Logout user and invalidate session"""
        success = self.session_manager.logout(session_token)
        if success:
            logger.info("👋 User logged out")
        return success

    def get_user_stats(self, username: str) -> Optional[Dict]:
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

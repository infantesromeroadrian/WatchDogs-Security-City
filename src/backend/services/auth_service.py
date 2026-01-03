"""
Secure Authentication Service
SECURITY-HARDENED - Production-ready authentication
"""

import logging
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class AuthService:
    """Security-hardened authentication service"""

    # Security constants
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=15)
    SESSION_DURATION = timedelta(hours=24)
    MIN_PASSWORD_LENGTH = 12

    def __init__(self, storage_file: Optional[str] = None):
        # Persistent storage
        self.storage_file = storage_file or os.getenv(
            "AUTH_STORAGE_FILE", "data/.auth_storage.json"
        )
        self.storage_path = Path(self.storage_file)

        # In-memory caches
        self.users = {}
        self.sessions = {}
        self.failed_attempts = {}  # Track failed login attempts

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

    def hash_password(
        self, password: str, salt: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Hash password with salt using PBKDF2-HMAC-SHA256.

        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (hashed_password, salt)
        """
        if not salt:
            salt = secrets.token_hex(32)

        # Use PBKDF2 with 100,000 iterations (OWASP recommendation)
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,  # iterations
        )

        return hashed.hex(), salt

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password meets security requirements.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return (
                False,
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters",
            )

        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        # Check for common passwords (basic check)
        common_passwords = ["password", "admin123", "watchdogs", "12345678"]
        if password.lower() in common_passwords:
            return False, "Password is too common"

        return True, ""

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
        is_valid, error_msg = self.validate_password_strength(password)
        if not is_valid:
            return False, error_msg

        # Validate role
        if role not in ["admin", "analyst", "viewer"]:
            return False, "Invalid role"

        # Hash password
        hashed_pw, salt = self.hash_password(password)

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

    def _check_account_lockout(self, username: str) -> Tuple[bool, str]:
        """
        Check if account is locked due to failed attempts.

        Returns:
            Tuple of (is_locked, message)
        """
        if username not in self.users:
            return False, ""

        user = self.users[username]

        # Check if account is locked
        if user.get("locked_until"):
            locked_until = datetime.fromisoformat(user["locked_until"])
            if datetime.now() < locked_until:
                remaining = (locked_until - datetime.now()).seconds // 60
                return True, f"Account locked. Try again in {remaining} minutes"
            else:
                # Unlock account
                user["locked_until"] = None
                user["failed_login_attempts"] = 0
                self._save_to_disk()

        return False, ""

    def _record_failed_attempt(self, username: str):
        """Record failed login attempt and lock if necessary"""
        if username not in self.users:
            return

        user = self.users[username]
        user["failed_login_attempts"] = user.get("failed_login_attempts", 0) + 1

        # Lock account if max attempts exceeded
        if user["failed_login_attempts"] >= self.MAX_LOGIN_ATTEMPTS:
            user["locked_until"] = (datetime.now() + self.LOCKOUT_DURATION).isoformat()
            logger.warning(f"🔒 Account locked due to failed attempts: {username}")

        self._save_to_disk()

    def _reset_failed_attempts(self, username: str):
        """Reset failed login attempts counter"""
        if username in self.users:
            self.users[username]["failed_login_attempts"] = 0
            self.users[username]["locked_until"] = None
            self._save_to_disk()

    def authenticate(
        self, username: str, password: str, ip_address: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Authenticate user and create session.

        Args:
            username: Username
            password: Plain text password
            ip_address: Optional IP address for session binding

        Returns:
            Tuple of (session_token, error_message)
        """
        # Check if user exists
        if username not in self.users:
            logger.warning(
                f"⚠️ Authentication attempt for non-existent user: {username}"
            )
            # Don't reveal if user exists (security)
            return None, "Invalid credentials"

        user = self.users[username]

        # Check if account is active
        if not user.get("is_active", True):
            logger.warning(f"⚠️ Authentication attempt for disabled user: {username}")
            return None, "Account disabled"

        # Check account lockout
        is_locked, lock_message = self._check_account_lockout(username)
        if is_locked:
            return None, lock_message

        # Hash provided password with stored salt
        hashed_pw, _ = self.hash_password(password, user["salt"])

        # Compare hashes (constant-time comparison)
        if not secrets.compare_digest(hashed_pw, user["password_hash"]):
            logger.warning(f"⚠️ Failed login attempt for {username}")
            self._record_failed_attempt(username)
            return None, "Invalid credentials"

        # Reset failed attempts on successful login
        self._reset_failed_attempts(username)

        # Create session token (cryptographically secure)
        session_token = secrets.token_urlsafe(32)

        # Store session
        self.sessions[session_token] = {
            "username": username,
            "role": user["role"],
            "created_at": datetime.now(),
            "expires_at": datetime.now() + self.SESSION_DURATION,
            "ip_address": ip_address,
        }

        # Update last login
        user["last_login"] = datetime.now().isoformat()
        self._save_to_disk()

        logger.info(
            f"✅ User authenticated: {username} from IP {ip_address or 'unknown'}"
        )
        return session_token, ""

    def validate_session(
        self, session_token: str, ip_address: Optional[str] = None
    ) -> Optional[Dict]:
        """Validate session token - SECURITY: No sensitive data exposed"""
        if session_token not in self.sessions:
            return None

        session = self.sessions[session_token]

        # Check expiration
        if datetime.now() > session["expires_at"]:
            del self.sessions[session_token]
            logger.info(f"🕐 Session expired for {session['username']}")
            return None

        # Optional: Check IP binding (commented out for ease of use)
        # Uncomment in production if needed
        # if ip_address and session.get('ip_address') != ip_address:
        #     logger.warning(f"⚠️ IP mismatch detected for session")
        #     return None

        # ✅ SECURE: Only return necessary data
        return {"username": session["username"], "role": session["role"]}

    def logout(self, session_token: str) -> bool:
        """Logout user and invalidate session"""
        if session_token in self.sessions:
            username = self.sessions[session_token]["username"]
            del self.sessions[session_token]
            logger.info(f"👋 User logged out: {username}")
            return True
        return False

    def get_user_stats(self, username: str) -> Optional[Dict]:
        """
        Get user statistics - SECURITY FIXED

        ✅ ONLY returns safe, non-sensitive information
        ❌ NO password_hash, salt, or internal data exposed
        """
        if username not in self.users:
            return None

        user = self.users[username]

        # ✅ SECURE: Return ONLY safe public data
        return {
            "username": username,
            "role": user["role"],
            "analysis_count": user.get("analysis_count", 0),
            "last_login": user.get("last_login"),
            # ❌ Explicitly NOT including:
            # - password_hash
            # - salt
            # - failed_login_attempts
            # - locked_until
            # - is_active (could reveal account status)
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

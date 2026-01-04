"""
Account lockout management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Lockout constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


class LockoutManager:
    """Manages account lockout after failed login attempts"""

    def check_lockout(self, user_data: Dict) -> Tuple[bool, str]:
        """
        Check if account is locked due to failed attempts.

        Args:
            user_data: User data dictionary

        Returns:
            Tuple of (is_locked, message)
        """
        # Check if account is locked
        if user_data.get("locked_until"):
            locked_until = datetime.fromisoformat(user_data["locked_until"])
            if datetime.now() < locked_until:
                remaining = (locked_until - datetime.now()).seconds // 60
                return True, f"Account locked. Try again in {remaining} minutes"
            else:
                # Unlock account
                user_data["locked_until"] = None
                user_data["failed_login_attempts"] = 0

        return False, ""

    def record_failure(self, user_data: Dict, username: str) -> bool:
        """
        Record failed login attempt and lock if necessary.

        Args:
            user_data: User data dictionary
            username: Username for logging

        Returns:
            True if account was locked
        """
        user_data["failed_login_attempts"] = (
            user_data.get("failed_login_attempts", 0) + 1
        )

        # Lock account if max attempts exceeded
        if user_data["failed_login_attempts"] >= MAX_LOGIN_ATTEMPTS:
            user_data["locked_until"] = (datetime.now() + LOCKOUT_DURATION).isoformat()
            logger.warning(f"🔒 Account locked due to failed attempts: {username}")
            return True

        return False

    def reset_attempts(self, user_data: Dict):
        """Reset failed login attempts counter"""
        user_data["failed_login_attempts"] = 0
        user_data["locked_until"] = None

"""
Session management
"""

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

# Session duration
SESSION_DURATION = timedelta(hours=24)


class SessionManager:
    """Manages user sessions"""

    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def create_session(
        self, username: str, role: str, ip_address: Optional[str] = None
    ) -> str:
        """
        Create new session.

        Args:
            username: Username
            role: User role
            ip_address: Optional IP address for session binding

        Returns:
            Session token
        """
        # Create session token (cryptographically secure)
        session_token = secrets.token_urlsafe(32)

        # Store session
        self.sessions[session_token] = {
            "username": username,
            "role": role,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + SESSION_DURATION,
            "ip_address": ip_address,
        }

        return session_token

    def validate_session(
        self, session_token: str, ip_address: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Validate session token.

        Returns:
            Session data or None if invalid
        """
        if session_token not in self.sessions:
            return None

        session = self.sessions[session_token]

        # Check expiration
        if datetime.now() > session["expires_at"]:
            del self.sessions[session_token]
            return None

        # Optional: Check IP binding (commented out for ease of use)
        # Uncomment in production if needed
        # if ip_address and session.get('ip_address') != ip_address:
        #     return None

        # Return only necessary data
        return {"username": session["username"], "role": session["role"]}

    def logout(self, session_token: str) -> bool:
        """
        Logout user and invalidate session.

        Returns:
            True if session was found and deleted
        """
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False

    def cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            token
            for token, session in self.sessions.items()
            if now > session["expires_at"]
        ]

        for token in expired:
            del self.sessions[token]

        return len(expired)

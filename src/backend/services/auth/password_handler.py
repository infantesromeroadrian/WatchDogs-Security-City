"""
Password hashing and validation
"""

import hashlib
import secrets

# Security constants
MIN_PASSWORD_LENGTH = 12


# OWASP (2023) minimum for PBKDF2-HMAC-SHA256. Stored per user so old hashes (100k) still verify.
PBKDF2_ITERATIONS = 600_000
LEGACY_ITERATIONS = 100_000


def hash_password(
    password: str, salt: str | None = None, iterations: int = PBKDF2_ITERATIONS
) -> tuple[str, str]:
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

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )

    return hashed.hex(), salt


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return (
            False,
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
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

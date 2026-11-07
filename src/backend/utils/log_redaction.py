"""
Log redaction: no image content, tokens or obvious personal data in logs.

Installed on the root handlers. Redacts data-URI / long base64 blobs (a frame in a debug log of an
HTTP client would otherwise end up in Render's log stream), Bearer tokens, session cookies and
e-mail addresses.
"""

import logging
import re

_PATTERNS = [
    (re.compile(r"data:[a-z]+/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=_-]+", re.I), "[image data redacted]"),
    (re.compile(r"[A-Za-z0-9+/=_-]{200,}"), "[blob redacted]"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]+", re.I), r"\1[redacted]"),
    (re.compile(r"(wd_session=)[^;\s]+", re.I), r"\1[redacted]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email redacted]"),
]


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFilter(logging.Filter):
    """Rewrites the record's message with sensitive content removed."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - malformed format args must not break logging
            return True
        record.msg = redact(message)
        record.args = ()
        return True


def install() -> None:
    """Attach the filter to every root handler and quiet chatty HTTP libraries."""
    root = logging.getLogger()
    for handler in root.handlers:
        if not any(isinstance(f, RedactingFilter) for f in handler.filters):
            handler.addFilter(RedactingFilter())
    for noisy in ("openai", "httpx", "httpcore", "httpcore2", "urllib3", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

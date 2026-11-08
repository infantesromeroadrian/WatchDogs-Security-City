"""
Retry utilities with exponential backoff for agent operations.
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from openai import APIConnectionError, InternalServerError, RateLimitError
from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
)

from ..config import AGENT_TIMEOUT_SECONDS
from ..exceptions import StructuredOutputError

logger = logging.getLogger(__name__)

# Retryable: rate limits, timeouts/connection drops (APITimeoutError is an
# APIConnectionError), 5xx, and an unparsable model reply. NOT retried: 400/401/403/404 -
# a bad key or request does not heal and retrying only burns quota and trips breakers.
RETRYABLE_EXCEPTIONS = (
    RateLimitError,
    APIConnectionError,
    InternalServerError,
    TimeoutError,
    ConnectionError,
    StructuredOutputError,
)


def agent_retry(max_attempts: int = 3, min_wait: float = 2.0, max_wait: float = 10.0):
    """
    Decorator for agent operations with retry logic.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
    """

    def decorator(func: Callable) -> Callable:
        @retry(
            # Never start a new attempt once the agent-level timeout has elapsed: the caller
            # already gave up, and a zombie retry would keep spending LLM quota.
            stop=stop_after_attempt(max_attempts) | stop_after_delay(AGENT_TIMEOUT_SECONDS),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator

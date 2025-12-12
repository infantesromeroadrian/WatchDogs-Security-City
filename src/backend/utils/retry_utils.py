"""
Retry utilities with exponential backoff for agent operations.
"""
import logging
from functools import wraps
from typing import Callable, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from openai import RateLimitError, APITimeoutError, APIError

logger = logging.getLogger(__name__)

# Retryable exceptions
RETRYABLE_EXCEPTIONS = (
    RateLimitError,
    APITimeoutError,
    APIError,
    TimeoutError,
    ConnectionError
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
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


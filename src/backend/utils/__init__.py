"""
Utility functions for the WatchDogs OSINT system.
"""

from .cache_utils import (
    clear_cache,
    get_cache_key,
    get_cache_stats,
    get_cached_result,
    get_image_hash,
    set_cached_result,
)
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, circuit_breaker
from .image_utils import verify_image_size
from .metrics_utils import _noop_decorator, get_agent_metrics, reset_metrics, track_agent_metrics
from .retry_utils import agent_retry
from .timeout_utils import AgentTimeoutError, TimeoutError, with_timeout

__all__ = [
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "AgentTimeoutError",
    "TimeoutError",
    "_noop_decorator",
    # Retry utils
    "agent_retry",
    "circuit_breaker",
    "clear_cache",
    "get_agent_metrics",
    "get_cache_key",
    "get_cache_stats",
    "get_cached_result",
    # Cache utils
    "get_image_hash",
    "reset_metrics",
    "set_cached_result",
    # Metrics utils
    "track_agent_metrics",
    # Image utils
    "verify_image_size",
    # Timeout utils
    "with_timeout",
]

"""
Metrics and observability utilities for agent operations.
"""

import logging
import threading
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# H-1: Thread lock — protects _metrics and _agent_stats from data races
# when 7 agents update concurrently.
_lock = threading.Lock()

# M-10: In-memory metrics storage — deque(maxlen=1000) for O(1) bounded storage
_MAX_METRICS_PER_AGENT = 1000
_metrics: dict[str, deque[dict[str, Any]]] = defaultdict(
    lambda: deque(maxlen=_MAX_METRICS_PER_AGENT)
)
_agent_stats: dict[str, dict[str, Any]] = defaultdict(
    lambda: {
        "total_calls": 0,
        "success_count": 0,
        "error_count": 0,
        "timeout_count": 0,
        "total_latency_ms": 0.0,
        "min_latency_ms": float("inf"),
        "max_latency_ms": 0.0,
    }
)


def _noop_decorator(func):
    """No-op decorator that does nothing (for when metrics are disabled)."""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def track_agent_metrics(agent_name: str):
    """
    Decorator to track metrics for agent operations.

    Args:
        agent_name: Name of the agent
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            status = "success"
            error_type = None

            try:
                result = func(*args, **kwargs)

                # Check if result indicates error
                if isinstance(result, dict):
                    if result.get("status") == "error":
                        status = "error"
                        error_type = result.get("error", "unknown")
                    elif result.get("status") == "timeout":
                        status = "timeout"

                return result

            except TimeoutError:
                status = "timeout"
                error_type = "timeout"
                raise
            except (ValueError, TypeError, RuntimeError) as e:
                status = "error"
                error_type = type(e).__name__
                raise
            finally:
                # Calculate latency
                latency_ms = (time.perf_counter() - start_time) * 1000

                with _lock:
                    # Update stats
                    stats = _agent_stats[agent_name]
                    stats["total_calls"] += 1

                    if status == "success":
                        stats["success_count"] += 1
                    elif status == "error":
                        stats["error_count"] += 1
                    elif status == "timeout":
                        stats["timeout_count"] += 1

                    stats["total_latency_ms"] += latency_ms
                    stats["min_latency_ms"] = min(stats["min_latency_ms"], latency_ms)
                    stats["max_latency_ms"] = max(stats["max_latency_ms"], latency_ms)

                    # Store metric entry (deque auto-evicts oldest beyond maxlen)
                    _metrics[agent_name].append(
                        {
                            "timestamp": time.time(),
                            "status": status,
                            "latency_ms": latency_ms,
                            "error_type": error_type,
                        }
                    )

                    avg_ms = stats["total_latency_ms"] / stats["total_calls"]

                logger.debug(
                    "📊 %s: %s in %.2fms (avg: %.2fms)",
                    agent_name,
                    status,
                    latency_ms,
                    avg_ms,
                )

        return wrapper

    return decorator


def get_agent_metrics(agent_name: str | None = None) -> dict[str, Any]:
    """
    Get metrics for agent(s).

    Args:
        agent_name: Specific agent name, or None for all

    Returns:
        Dict with metrics
    """
    with _lock:
        if agent_name:
            stats = _agent_stats.get(agent_name, {})
            if stats and stats["total_calls"] > 0:
                stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["total_calls"]
                stats["success_rate"] = stats["success_count"] / stats["total_calls"]
            elif stats:
                stats["avg_latency_ms"] = 0.0
                stats["success_rate"] = 0.0
            return {agent_name: stats}

        # Return all metrics
        result = {}
        for name, stats in _agent_stats.items():
            if stats["total_calls"] > 0:
                stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["total_calls"]
                stats["success_rate"] = stats["success_count"] / stats["total_calls"]
            else:
                stats["avg_latency_ms"] = 0.0
                stats["success_rate"] = 0.0
            result[name] = stats.copy()

        return result


def reset_metrics() -> None:
    """Reset all metrics."""
    with _lock:
        _metrics.clear()
        _agent_stats.clear()
    logger.info("📊 Metrics reset")

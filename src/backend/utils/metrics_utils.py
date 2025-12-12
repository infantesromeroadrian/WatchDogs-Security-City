"""
Metrics and observability utilities for agent operations.
"""
import logging
import time
from typing import Dict, Any, Optional
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)

# In-memory metrics storage
_metrics: Dict[str, list[Dict[str, Any]]] = defaultdict(list)
_agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
    "total_calls": 0,
    "success_count": 0,
    "error_count": 0,
    "timeout_count": 0,
    "total_latency_ms": 0.0,
    "min_latency_ms": float('inf'),
    "max_latency_ms": 0.0
})


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
                
            except TimeoutError as e:
                status = "timeout"
                error_type = "timeout"
                raise
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                raise
            finally:
                # Calculate latency
                latency_ms = (time.perf_counter() - start_time) * 1000
                
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
                
                # Store metric entry
                _metrics[agent_name].append({
                    "timestamp": time.time(),
                    "status": status,
                    "latency_ms": latency_ms,
                    "error_type": error_type
                })
                
                # Keep only last 1000 entries per agent
                if len(_metrics[agent_name]) > 1000:
                    _metrics[agent_name] = _metrics[agent_name][-1000:]
                
                logger.debug(
                    f"📊 {agent_name}: {status} in {latency_ms:.2f}ms "
                    f"(avg: {stats['total_latency_ms']/stats['total_calls']:.2f}ms)"
                )
        
        return wrapper
    return decorator


def get_agent_metrics(agent_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get metrics for agent(s).
    
    Args:
        agent_name: Specific agent name, or None for all
        
    Returns:
        Dict with metrics
    """
    if agent_name:
        stats = _agent_stats.get(agent_name, {})
        if stats["total_calls"] > 0:
            stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["total_calls"]
            stats["success_rate"] = stats["success_count"] / stats["total_calls"]
        else:
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
    _metrics.clear()
    _agent_stats.clear()
    logger.info("📊 Metrics reset")


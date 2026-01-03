"""
Caching utilities for agent results with LRU eviction.
"""

import hashlib
import logging
import time
from typing import Any, Optional
from collections import OrderedDict
from datetime import datetime

logger = logging.getLogger(__name__)

# Maximum cache size (LRU eviction when exceeded)
MAX_CACHE_SIZE = 500  # Configurable global limit

# In-memory cache with LRU (OrderedDict maintains insertion order)
_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
_cache_ttl: dict[str, float] = {}


def get_image_hash(image_base64: str) -> str:
    """
    Generate hash for image caching.

    Args:
        image_base64: Base64 encoded image

    Returns:
        SHA256 hash (first 16 chars)
    """
    # Remove data URI prefix if present
    if "," in image_base64:
        image_data = image_base64.split(",")[1]
    else:
        image_data = image_base64

    hash_obj = hashlib.sha256(image_data.encode())
    return hash_obj.hexdigest()[:16]


def get_cache_key(image_base64: str, agent_name: str, context: str = "") -> str:
    """
    Generate cache key for agent result.

    Args:
        image_base64: Base64 encoded image
        agent_name: Name of the agent
        context: Optional context string

    Returns:
        Cache key string
    """
    image_hash = get_image_hash(image_base64)
    context_hash = hashlib.md5(context.encode()).hexdigest()[:8] if context else "none"
    return f"{agent_name}:{image_hash}:{context_hash}"


def get_cached_result(
    cache_key: str, ttl_seconds: int = 3600
) -> Optional[dict[str, Any]]:
    """
    Get cached result if available and not expired.

    Args:
        cache_key: Cache key
        ttl_seconds: Time to live in seconds

    Returns:
        Cached result or None
    """
    if cache_key not in _cache:
        return None

    # Check TTL
    if cache_key in _cache_ttl:
        if time.time() > _cache_ttl[cache_key]:
            # Expired, remove
            del _cache[cache_key]
            del _cache_ttl[cache_key]
            logger.debug(f"🗑️ Cache expired for key: {cache_key[:20]}...")
            return None

    # Move to end (mark as recently used in LRU)
    _cache.move_to_end(cache_key)

    logger.info(f"💾 Cache hit for key: {cache_key[:20]}...")
    return _cache[cache_key].copy()


def set_cached_result(
    cache_key: str, result: dict[str, Any], ttl_seconds: int = 3600
) -> None:
    """
    Store result in cache with LRU eviction.

    Args:
        cache_key: Cache key
        result: Result to cache
        ttl_seconds: Time to live in seconds
    """
    # Evict oldest entry if at limit (LRU policy)
    if len(_cache) >= MAX_CACHE_SIZE:
        # Remove oldest (first item in OrderedDict)
        oldest_key = next(iter(_cache))
        del _cache[oldest_key]
        if oldest_key in _cache_ttl:
            del _cache_ttl[oldest_key]
        logger.debug(
            f"🗑️ LRU eviction: removed {oldest_key[:20]}... (cache at max size)"
        )

    _cache[cache_key] = result.copy()
    _cache_ttl[cache_key] = time.time() + ttl_seconds

    # Move to end (most recently used)
    _cache.move_to_end(cache_key)

    logger.debug(f"💾 Cached result for key: {cache_key[:20]}... (TTL: {ttl_seconds}s)")


def clear_cache() -> None:
    """Clear all cached results."""
    _cache.clear()
    _cache_ttl.clear()
    logger.info("🗑️ Cache cleared")


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dict with cache stats
    """
    now = time.time()
    expired = sum(1 for ttl in _cache_ttl.values() if now > ttl)
    active = len(_cache) - expired

    # Calculate memory usage (approximate)
    memory_bytes = sum(len(str(v).encode()) for v in _cache.values())
    memory_mb = memory_bytes / 1024 / 1024

    return {
        "total_entries": len(_cache),
        "active_entries": active,
        "expired_entries": expired,
        "max_size": MAX_CACHE_SIZE,
        "utilization_pct": (len(_cache) / MAX_CACHE_SIZE) * 100
        if MAX_CACHE_SIZE > 0
        else 0,
        "memory_usage_mb": round(memory_mb, 2),
    }

"""Caching implementation for SentinelOps API."""

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

from fastapi import Request

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache implementation.

    In production, this would be replaced with Redis or similar.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_default = 300  # 5 minutes default TTL

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now(timezone.utc) < entry["expires_at"]:
                logger.debug("Cache hit for key: %s", key)
                return entry["value"]
            else:
                # Expired entry, remove it
                del self._cache[key]
                logger.debug("Cache expired for key: %s", key)

        logger.debug("Cache miss for key: %s", key)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self._ttl_default
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
        }
        logger.debug("Cache set for key: %s, TTL: %ss", key, ttl)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug("Cache deleted for key: %s", key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, entry in self._cache.items() if now >= entry["expires_at"]
        ]

        for key in expired_keys:
            del self._cache[key]

        logger.debug("Cleaned up %d expired cache entries", len(expired_keys))
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.now(timezone.utc)
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values() if now >= entry["expires_at"]
        )

        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_size_bytes": len(json.dumps(self._cache, default=str)),
        }

    def get_keys(self) -> list[str]:
        """Get all cache keys."""
        return list(self._cache.keys())

    def get_default_ttl(self) -> int:
        """Get default TTL value."""
        return self._ttl_default


# Global cache instance
cache = InMemoryCache()


def generate_cache_key(prefix: str, **kwargs: Any) -> str:
    """Generate a consistent cache key from parameters."""
    # Sort kwargs to ensure consistent key generation
    sorted_params = sorted(kwargs.items())
    param_str = json.dumps(sorted_params, sort_keys=True, default=str)

    # Create hash for long keys
    if len(param_str) > 100:
        param_hash = hashlib.md5(param_str.encode(), usedforsecurity=False).hexdigest()
        return f"{prefix}:{param_hash}"

    return f"{prefix}:{param_str}"


F = TypeVar('F', bound=Callable[..., Any])


def cache_response(prefix: str, ttl: int = 300) -> Callable[[F], F]:
    """Decorator to cache API responses.

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract request if present
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            # Generate cache key
            cache_params = {}
            if request:
                # Include query parameters
                cache_params.update(dict(request.query_params))
                # Include path parameters
                cache_params.update(request.path_params)

            # Add function kwargs
            cache_params.update(kwargs)

            # Generate key
            cache_key = generate_cache_key(prefix, **cache_params)

            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        return cast(F, wrapper)

    return decorator


def invalidate_cache(patterns: Union[str, list[str]]) -> Callable[[F], F]:
    """Decorator to invalidate cache entries matching patterns.

    Args:
        patterns: String or list of cache key patterns to invalidate
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Call function first
            result = await func(*args, **kwargs)

            # Invalidate cache entries
            if isinstance(patterns, str):
                pattern_list = [patterns]
            else:
                pattern_list = patterns

            invalidated = 0
            for pattern in pattern_list:
                # Simple pattern matching (in production, use more sophisticated matching)
                keys_to_delete = [key for key in cache.get_keys() if pattern in key]

                for key in keys_to_delete:
                    if cache.delete(key):
                        invalidated += 1

            if invalidated > 0:
                logger.info("Invalidated %d cache entries", invalidated)

            return result

        return cast(F, wrapper)

    return decorator


# Specific cache functions for common operations
async def get_cached_incident_stats() -> Optional[Dict[str, Any]]:
    """Get cached incident statistics."""
    return cache.get("incident_stats")


async def set_cached_incident_stats(stats: Dict[str, Any], ttl: int = 300) -> None:
    """Set cached incident statistics."""
    cache.set("incident_stats", stats, ttl)


async def invalidate_incident_cache() -> None:
    """Invalidate all incident-related cache entries."""
    keys_to_delete = [key for key in cache.get_keys() if "incident" in key]

    for key in keys_to_delete:
        cache.delete(key)

    logger.info("Invalidated %d incident cache entries", len(keys_to_delete))


async def get_cache_status() -> Dict[str, Any]:
    """Get current cache status and statistics."""
    stats = cache.get_stats()
    stats["backend"] = "in-memory"
    stats["ttl_default"] = cache.get_default_ttl()
    return stats

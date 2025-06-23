"""
Query cache implementation for the Detection Agent.

This module provides caching for frequently used queries to improve performance.
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib
import logging
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Represents a cached query result."""
    query_hash: str
    query_text: str
    result: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    rule_type: Optional[str] = None


class QueryCache:
    """Manages caching of query results."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the query cache.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Cache settings
        cache_config = config.get("agents", {}).get("detection", {}).get("query_cache", {})
        self.enabled = cache_config.get("enabled", True)
        self.max_entries = cache_config.get("max_entries", 1000)
        self.default_ttl_minutes = cache_config.get("default_ttl_minutes", 60)
        self.min_hit_count_for_extension = cache_config.get("min_hit_count_for_extension", 3)

        # Cache storage
        self._cache: Dict[str, CacheEntry] = {}

        # Cache statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0
        }

    def _generate_cache_key(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        rule_type: Optional[str] = None
    ) -> str:
        """
        Generate a unique cache key for a query.

        Args:
            query: SQL query
            start_time: Query start time
            end_time: Query end time
            rule_type: Optional rule type

        Returns:
            Cache key hash
        """
        # Create a unique key from query parameters
        key_parts = [
            query.strip().lower(),  # Normalize query
            start_time.isoformat(),
            end_time.isoformat(),
            rule_type or ""
        ]
        key_string = "|".join(key_parts)

        # Generate hash
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        rule_type: Optional[str] = None
    ) -> Optional[Any]:
        """
        Retrieve a cached query result.

        Args:
            query: SQL query
            start_time: Query start time
            end_time: Query end time
            rule_type: Optional rule type

        Returns:
            Cached result if found and valid, None otherwise
        """
        if not self.enabled:
            return None

        self._stats["total_queries"] += 1

        # Generate cache key
        cache_key = self._generate_cache_key(query, start_time, end_time, rule_type)

        # Check if entry exists
        if cache_key not in self._cache:
            self._stats["misses"] += 1
            self.logger.debug("Cache miss for query: %s...", cache_key[:8])
            return None

        entry = self._cache[cache_key]

        # Check if entry is expired
        if datetime.now() > entry.expires_at:
            self._stats["misses"] += 1
            self.logger.debug("Cache entry expired for query: %s...", cache_key[:8])
            del self._cache[cache_key]
            return None

        # Update hit count and stats
        entry.hit_count += 1
        self._stats["hits"] += 1

        # Extend TTL for frequently accessed entries
        if entry.hit_count >= self.min_hit_count_for_extension:
            entry.expires_at = datetime.now() + timedelta(minutes=self.default_ttl_minutes)
            self.logger.debug("Extended TTL for frequently accessed query: %s...", cache_key[:8])

        self.logger.debug("Cache hit for query: %s... (hits: %s)", cache_key[:8], entry.hit_count)
        return entry.result

    def put(
        self,
        query: str,
        result: Any,
        start_time: datetime,
        end_time: datetime,
        rule_type: Optional[str] = None,
        ttl_minutes: Optional[int] = None
    ) -> None:
        """
        Store a query result in the cache.

        Args:
            query: SQL query
            result: Query result
            start_time: Query start time
            end_time: Query end time
            rule_type: Optional rule type
            ttl_minutes: Optional custom TTL in minutes
        """
        if not self.enabled:
            return

        # Check cache size and evict if necessary
        if len(self._cache) >= self.max_entries:
            self._evict_oldest()

        # Generate cache key
        cache_key = self._generate_cache_key(query, start_time, end_time, rule_type)

        # Create cache entry
        ttl = ttl_minutes or self.default_ttl_minutes
        entry = CacheEntry(
            query_hash=cache_key,
            query_text=query[:500],  # Store truncated query for debugging
            result=result,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=ttl),
            hit_count=0,
            rule_type=rule_type
        )

        self._cache[cache_key] = entry
        self.logger.debug("Cached query result: %s... (TTL: %s minutes)", cache_key[:8], ttl)

    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry."""
        if not self._cache:
            return

        # Find oldest entry
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )

        self.logger.debug("Evicting oldest cache entry: %s...", oldest_key[:8])
        del self._cache[oldest_key]
        self._stats["evictions"] += 1

    def invalidate(
        self,
        rule_type: Optional[str] = None,
        older_than: Optional[datetime] = None
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            rule_type: Invalidate entries for specific rule type
            older_than: Invalidate entries older than this time

        Returns:
            Number of entries invalidated
        """
        if not self.enabled:
            return 0

        keys_to_remove = []

        for key, entry in self._cache.items():
            should_remove = False

            # Check rule type filter
            if rule_type and entry.rule_type == rule_type:
                should_remove = True

            # Check age filter
            if older_than and entry.created_at < older_than:
                should_remove = True

            if should_remove:
                keys_to_remove.append(key)

        # Remove entries
        for key in keys_to_remove:
            del self._cache[key]

        if keys_to_remove:
            self.logger.info("Invalidated %s cache entries", len(keys_to_remove))

        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self.logger.info("Cleared query cache")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        total_queries = self._stats["total_queries"]
        hit_rate = 0.0
        if total_queries > 0:
            hit_rate = (self._stats["hits"] / total_queries) * 100

        return {
            "enabled": self.enabled,
            "size": len(self._cache),
            "max_size": self.max_entries,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "total_queries": total_queries,
            "hit_rate": f"{hit_rate:.2f}%",
            "default_ttl_minutes": self.default_ttl_minutes
        }

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get detailed information about cached entries.

        Returns:
            Dictionary with cache entry details
        """
        entries_info = []

        for key, entry in self._cache.items():
            time_to_expire = (entry.expires_at - datetime.now()).total_seconds() / 60
            entries_info.append({
                "hash": key[:8] + "...",
                "rule_type": entry.rule_type,
                "created_at": entry.created_at.isoformat(),
                "expires_in_minutes": round(time_to_expire, 1),
                "hit_count": entry.hit_count,
                "query_preview": entry.query_text[:100] + "..."
            })

        # Sort by hit count (most used first)
        entries_info.sort(
            key=lambda x: float(x["hit_count"]) if x["hit_count"] is not None else 0,
            reverse=True
        )

        return {
            "total_entries": len(entries_info),
            "entries": entries_info[:10]  # Return top 10 most used
        }

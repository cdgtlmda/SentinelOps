"""Tests for caching implementation using real production code."""

import asyncio
import time
from datetime import datetime
from typing import Any

import pytest

from src.api.cache import (
    InMemoryCache,
    cache,
    cache_response,
    generate_cache_key,
    get_cache_status,
    get_cached_incident_stats,
    invalidate_cache,
    invalidate_incident_cache,
    set_cached_incident_stats,
)


class TestInMemoryCache:
    """Test cases for InMemoryCache with real production code."""

    @pytest.fixture
    def cache_instance(self) -> InMemoryCache:
        """Create a fresh cache instance for testing."""
        return InMemoryCache()

    def test_initialization(self, cache_instance: InMemoryCache) -> None:
        """Test cache initialization."""
        assert cache_instance._cache == {}
        assert cache_instance._ttl_default == 300

    def test_set_and_get(self, cache_instance: InMemoryCache) -> None:
        """Test basic set and get operations."""
        cache_instance.set("test_key", "test_value")

        value = cache_instance.get("test_key")
        assert value == "test_value"

    def test_get_nonexistent_key(self, cache_instance: InMemoryCache) -> None:
        """Test getting a key that doesn't exist."""
        value = cache_instance.get("nonexistent")
        assert value is None

    def test_set_with_custom_ttl(self, cache_instance: InMemoryCache) -> None:
        """Test setting value with custom TTL."""
        cache_instance.set("ttl_key", "ttl_value", ttl=10)

        # Check the cache entry structure
        assert "ttl_key" in cache_instance._cache
        entry = cache_instance._cache["ttl_key"]
        assert entry["value"] == "ttl_value"
        assert "expires_at" in entry
        assert "created_at" in entry

    def test_expired_entry_removal(self, cache_instance: InMemoryCache) -> None:
        """Test that expired entries are automatically removed."""
        # Set with very short TTL
        cache_instance.set("expire_key", "expire_value", ttl=0)

        # Wait a tiny bit
        time.sleep(0.001)

        # Should return None and remove the entry
        value = cache_instance.get("expire_key")
        assert value is None
        assert "expire_key" not in cache_instance._cache

    def test_delete_existing_key(self, cache_instance: InMemoryCache) -> None:
        """Test deleting an existing key."""
        cache_instance.set("delete_me", "value")

        result = cache_instance.delete("delete_me")
        assert result is True
        assert cache_instance.get("delete_me") is None

    def test_delete_nonexistent_key(self, cache_instance: InMemoryCache) -> None:
        """Test deleting a key that doesn't exist."""
        result = cache_instance.delete("nonexistent")
        assert result is False

    def test_clear(self, cache_instance: InMemoryCache) -> None:
        """Test clearing all cache entries."""
        # Add multiple entries
        cache_instance.set("key1", "value1")
        cache_instance.set("key2", "value2")
        cache_instance.set("key3", "value3")

        # Clear cache
        cache_instance.clear()

        # Verify all entries are gone
        assert len(cache_instance._cache) == 0
        assert cache_instance.get("key1") is None
        assert cache_instance.get("key2") is None
        assert cache_instance.get("key3") is None

    def test_cleanup_expired(self, cache_instance: InMemoryCache) -> None:
        """Test cleanup of expired entries."""
        # Add entries with different TTLs
        cache_instance.set("valid1", "value1", ttl=300)
        cache_instance.set("expired1", "value2", ttl=0)
        time.sleep(0.001)
        cache_instance.set("valid2", "value3", ttl=300)
        cache_instance.set("expired2", "value4", ttl=0)

        # Run cleanup
        expired_count = cache_instance.cleanup_expired()

        assert expired_count == 2
        assert "valid1" in cache_instance._cache
        assert "valid2" in cache_instance._cache
        assert "expired1" not in cache_instance._cache
        assert "expired2" not in cache_instance._cache

    def test_get_stats(self, cache_instance: InMemoryCache) -> None:
        """Test getting cache statistics."""
        # Add some entries
        cache_instance.set("active1", "value1", ttl=300)
        cache_instance.set("active2", "value2", ttl=300)
        cache_instance.set("expired", "value3", ttl=0)
        time.sleep(0.001)

        stats = cache_instance.get_stats()

        assert stats["total_entries"] == 3
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 1
        assert "cache_size_bytes" in stats
        assert stats["cache_size_bytes"] > 0

    def test_get_keys(self, cache_instance: InMemoryCache) -> None:
        """Test getting all cache keys."""
        cache_instance.set("key1", "value1")
        cache_instance.set("key2", "value2")
        cache_instance.set("key3", "value3")

        keys = cache_instance.get_keys()

        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys

    def test_get_default_ttl(self, cache_instance: InMemoryCache) -> None:
        """Test getting default TTL value."""
        ttl = cache_instance.get_default_ttl()
        assert ttl == 300


class TestCacheKeyGeneration:
    """Test cases for cache key generation."""

    def test_generate_simple_key(self) -> None:
        """Test generating a simple cache key."""
        key = generate_cache_key("prefix", param1="value1", param2="value2")

        assert key.startswith("prefix:")
        assert "value1" in key
        assert "value2" in key

    def test_generate_key_consistent_order(self) -> None:
        """Test that key generation is consistent regardless of parameter order."""
        key1 = generate_cache_key("prefix", a=1, b=2, c=3)
        key2 = generate_cache_key("prefix", c=3, a=1, b=2)

        assert key1 == key2

    def test_generate_key_with_long_params(self) -> None:
        """Test key generation with long parameters uses hash."""
        long_value = "x" * 200
        key = generate_cache_key("prefix", long_param=long_value)

        assert key.startswith("prefix:")
        assert len(key) < 100  # Should be hashed
        assert long_value not in key  # Original value shouldn't be in key

    def test_generate_key_with_complex_types(self) -> None:
        """Test key generation with complex parameter types."""
        key = generate_cache_key(
            "prefix",
            list_param=[1, 2, 3],
            dict_param={"nested": "value"},
            date_param=datetime(2025, 6, 12),
        )

        assert key.startswith("prefix:")
        # Should contain string representations
        assert "nested" in key or len(key) < 100  # Either in key or hashed


class TestCacheDecorators:
    """Test cases for cache decorators."""

    @pytest.mark.asyncio
    async def test_cache_response_decorator_basic(self) -> None:
        """Test basic cache response decorator functionality."""
        call_count = 0

        @cache_response("test", ttl=60)
        async def test_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result-{value}"

        # First call should execute function
        result1 = await test_function(value="test1")
        assert result1 == "result-test1"
        assert call_count == 1

        # Second call with same params should use cache
        result2 = await test_function(value="test1")
        assert result2 == "result-test1"
        assert call_count == 1  # Function not called again

        # Call with different params should execute function
        result3 = await test_function(value="test2")
        assert result3 == "result-test2"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cache_response_with_simple_params(self) -> None:
        """Test cache response decorator with simple parameters."""
        call_count = 0

        @cache_response("api", ttl=60)
        async def api_function(
            item_id: int, filter_type: str = "active"
        ) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"item_id": item_id, "filter": filter_type, "count": call_count}

        # First call
        result1 = await api_function(item_id=123, filter_type="active")
        assert result1["item_id"] == 123
        assert result1["filter"] == "active"
        assert result1["count"] == 1
        assert call_count == 1

        # Second call with same params should use cache
        result2 = await api_function(item_id=123, filter_type="active")
        assert result2 == result1
        assert call_count == 1  # Function not called again

        # Call with different params should execute function
        result3 = await api_function(item_id=456, filter_type="active")
        assert result3["item_id"] == 456
        assert result3["count"] == 2
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_cache_decorator(self) -> None:
        """Test cache invalidation decorator."""
        # First, add some items to cache
        cache.set("test:item1", "value1")
        cache.set("test:item2", "value2")
        cache.set("other:item", "value3")

        @invalidate_cache("test:")
        async def update_function() -> str:
            return "updated"

        # Call function
        result = await update_function()
        assert result == "updated"

        # Check that test: keys were invalidated
        assert cache.get("test:item1") is None
        assert cache.get("test:item2") is None
        # Other keys should remain
        assert cache.get("other:item") == "value3"

    @pytest.mark.asyncio
    async def test_invalidate_cache_multiple_patterns(self) -> None:
        """Test cache invalidation with multiple patterns."""
        # Add items to cache
        cache.set("incidents:list", "list_data")
        cache.set("incidents:stats", "stats_data")
        cache.set("rules:list", "rules_data")
        cache.set("other:data", "other_data")

        @invalidate_cache(["incidents:", "rules:"])
        async def update_function() -> str:
            return "updated"

        result = await update_function()
        assert result == "updated"

        # Check invalidation
        assert cache.get("incidents:list") is None
        assert cache.get("incidents:stats") is None
        assert cache.get("rules:list") is None
        assert cache.get("other:data") == "other_data"


class TestCacheHelperFunctions:
    """Test cases for cache helper functions."""

    @pytest.mark.asyncio
    async def test_incident_stats_cache(self) -> None:
        """Test incident statistics caching functions."""
        stats = {"total": 100, "critical": 5, "resolved": 80}

        # Set stats
        await set_cached_incident_stats(stats, ttl=60)

        # Get stats
        cached_stats = await get_cached_incident_stats()
        assert cached_stats == stats

    @pytest.mark.asyncio
    async def test_invalidate_incident_cache(self) -> None:
        """Test incident cache invalidation."""
        # Add incident-related entries
        cache.set("incident:123", {"id": 123})
        cache.set("incidents:list", [1, 2, 3])
        cache.set("incident_stats", {"total": 10})
        cache.set("rules:list", ["rule1"])

        # Invalidate incident cache
        await invalidate_incident_cache()

        # Check that incident entries are gone
        assert cache.get("incident:123") is None
        assert cache.get("incidents:list") is None
        assert cache.get("incident_stats") is None
        # Non-incident entries should remain
        assert cache.get("rules:list") == ["rule1"]

    @pytest.mark.asyncio
    async def test_get_cache_status(self) -> None:
        """Test getting cache status."""
        # Add some data
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        status = await get_cache_status()

        assert status["backend"] == "in-memory"
        assert status["ttl_default"] == 300
        assert "total_entries" in status
        assert "active_entries" in status
        assert "expired_entries" in status
        assert "cache_size_bytes" in status


class TestGlobalCacheInstance:
    """Test cases for global cache instance."""

    def test_global_cache_is_inmemory(self) -> None:
        """Test that global cache is InMemoryCache instance."""
        assert isinstance(cache, InMemoryCache)
        assert cache._ttl_default == 300

    def test_global_cache_operations(self) -> None:
        """Test operations on global cache instance."""
        # Clear first to ensure clean state
        cache.clear()

        # Test basic operations
        cache.set("global_key", "global_value")
        assert cache.get("global_key") == "global_value"

        cache.delete("global_key")
        assert cache.get("global_key") is None

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self) -> None:
        """Test concurrent access to cache."""
        cache.clear()

        async def write_to_cache(key: str, value: str) -> Any:
            cache.set(key, value)
            await asyncio.sleep(0.001)
            return cache.get(key)

        # Run concurrent operations
        tasks = [write_to_cache(f"concurrent_{i}", f"value_{i}") for i in range(10)]

        results = await asyncio.gather(*tasks)

        # Verify all operations succeeded
        for i, result in enumerate(results):
            assert result == f"value_{i}"

    def test_cache_with_various_data_types(self) -> None:
        """Test caching various data types."""
        cache.clear()

        # Test different data types
        test_data = {
            "string": "test_string",
            "number": 42,
            "float": 3.14,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "bool": True,
            "none": None,
        }

        for key, value in test_data.items():
            cache.set(key, value)
            assert cache.get(key) == value

"""
Comprehensive test suite for detection_agent/query_cache.py

REQUIREMENTS:
- 100% production code (NO MOCKS)
- Achieve ≥90% statement coverage
- Test all major code paths and business logic
- Include comprehensive error handling scenarios
- Cover edge cases and boundary conditions
"""

from datetime import datetime, timedelta
import time
from dataclasses import asdict
from typing import Dict, Any

from detection_agent.query_cache import CacheEntry, QueryCache


class TestCacheEntry:
    """Test CacheEntry dataclass functionality."""

    def test_cache_entry_creation(self) -> None:
        """Test CacheEntry creation with all fields."""
        now = datetime.now()
        expires = now + timedelta(minutes=60)

        entry = CacheEntry(
            query_hash="test_hash",
            query_text="SELECT * FROM test",
            result={"data": "test"},
            created_at=now,
            expires_at=expires,
            hit_count=5,
            rule_type="TEST_RULE",
        )

        assert entry.query_hash == "test_hash"
        assert entry.query_text == "SELECT * FROM test"
        assert entry.result == {"data": "test"}
        assert entry.created_at == now
        assert entry.expires_at == expires
        assert entry.hit_count == 5
        assert entry.rule_type == "TEST_RULE"

    def test_cache_entry_default_values(self) -> None:
        """Test CacheEntry creation with default values."""
        now = datetime.now()
        expires = now + timedelta(minutes=60)

        entry = CacheEntry(
            query_hash="test_hash",
            query_text="SELECT * FROM test",
            result={"data": "test"},
            created_at=now,
            expires_at=expires,
        )

        assert entry.hit_count == 0
        assert entry.rule_type is None

    def test_cache_entry_serialization(self) -> None:
        """Test CacheEntry can be converted to dict."""
        now = datetime.now()
        expires = now + timedelta(minutes=60)

        entry = CacheEntry(
            query_hash="test_hash",
            query_text="SELECT * FROM test",
            result={"data": "test"},
            created_at=now,
            expires_at=expires,
            hit_count=3,
            rule_type="QUERY",
        )

        entry_dict = asdict(entry)
        assert isinstance(entry_dict, dict)
        assert entry_dict["query_hash"] == "test_hash"
        assert entry_dict["hit_count"] == 3


class TestQueryCache:
    """Test QueryCache class functionality."""

    def test_init_default_config(self) -> None:
        """Test QueryCache initialization with default configuration."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        assert cache.config == config
        assert cache.enabled is True
        assert cache.max_entries == 1000
        assert cache.default_ttl_minutes == 60
        assert cache.min_hit_count_for_extension == 3
        assert not cache._cache
        assert cache._stats == {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0,
        }

    def test_init_custom_config(self) -> None:
        """Test QueryCache initialization with custom configuration."""
        config = {
            "agents": {
                "detection": {
                    "query_cache": {
                        "enabled": False,
                        "max_entries": 500,
                        "default_ttl_minutes": 30,
                        "min_hit_count_for_extension": 5,
                    }
                }
            }
        }
        cache = QueryCache(config)

        assert cache.enabled is False
        assert cache.max_entries == 500
        assert cache.default_ttl_minutes == 30
        assert cache.min_hit_count_for_extension == 5

    def test_init_partial_config(self) -> None:
        """Test QueryCache initialization with partial configuration."""
        config = {"agents": {"detection": {"query_cache": {"max_entries": 2000}}}}
        cache = QueryCache(config)

        assert cache.enabled is True  # Default
        assert cache.max_entries == 2000  # Custom
        assert cache.default_ttl_minutes == 60  # Default

    def test_generate_cache_key_basic(self) -> None:
        """Test basic cache key generation."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs WHERE timestamp > ?"
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)

        key = cache._generate_cache_key(query, start_time, end_time)

        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hash length

        # Same parameters should generate same key
        key2 = cache._generate_cache_key(query, start_time, end_time)
        assert key == key2

    def test_generate_cache_key_with_rule_type(self) -> None:
        """Test cache key generation with rule type."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)

        key1 = cache._generate_cache_key(query, start_time, end_time, "QUERY")
        key2 = cache._generate_cache_key(query, start_time, end_time, "THRESHOLD")
        key3 = cache._generate_cache_key(query, start_time, end_time, None)

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_generate_cache_key_normalization(self) -> None:
        """Test cache key generation normalizes query."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 13, 0, 0)

        # Different whitespace and case should generate same key
        query1 = "SELECT * FROM logs"
        query2 = "  select * from logs  "
        query3 = "SELECT * FROM LOGS"

        key1 = cache._generate_cache_key(query1, start_time, end_time)
        key2 = cache._generate_cache_key(query2, start_time, end_time)
        key3 = cache._generate_cache_key(query3, start_time, end_time)

        assert key1 == key2 == key3

    def test_generate_cache_key_different_times(self) -> None:
        """Test cache key generation with different times."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        start_time1 = datetime(2023, 1, 1, 12, 0, 0)
        end_time1 = datetime(2023, 1, 1, 13, 0, 0)
        start_time2 = datetime(2023, 1, 1, 14, 0, 0)
        end_time2 = datetime(2023, 1, 1, 15, 0, 0)

        key1 = cache._generate_cache_key(query, start_time1, end_time1)
        key2 = cache._generate_cache_key(query, start_time2, end_time2)

        assert key1 != key2

    def test_put_and_get_basic(self) -> None:
        """Test basic put and get operations."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        result = {"count": 100, "data": ["log1", "log2"]}
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Put result in cache
        cache.put(query, result, start_time, end_time)

        # Get result from cache
        cached_result = cache.get(query, start_time, end_time)

        assert cached_result == result
        assert cache._stats["hits"] == 1
        assert cache._stats["misses"] == 0
        assert cache._stats["total_queries"] == 1

    def test_get_cache_miss(self) -> None:
        """Test cache miss scenario."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Get from empty cache
        result = cache.get(query, start_time, end_time)

        assert result is None
        assert cache._stats["hits"] == 0
        assert cache._stats["misses"] == 1
        assert cache._stats["total_queries"] == 1

    def test_get_disabled_cache(self) -> None:
        """Test get operation when cache is disabled."""
        config = {"agents": {"detection": {"query_cache": {"enabled": False}}}}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Put and get should return None when disabled
        cache.put(query, {"data": "test"}, start_time, end_time)
        result = cache.get(query, start_time, end_time)

        assert result is None
        assert cache._stats["total_queries"] == 0

    def test_put_disabled_cache(self) -> None:
        """Test put operation when cache is disabled."""
        config: Dict[str, Any] = {
            "agents": {"detection": {"query_cache": {"enabled": False}}}
        }
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Put should not store when disabled
        cache.put(query, {"data": "test"}, start_time, end_time)

        assert len(cache._cache) == 0

    def test_cache_expiration(self) -> None:
        """Test cache entry expiration."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        result = {"data": "test"}
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Put with very short TTL
        cache.put(query, result, start_time, end_time, ttl_minutes=0.01)  # 0.6 seconds

        # Should get immediately
        cached_result = cache.get(query, start_time, end_time)
        assert cached_result == result

        # Wait for expiration
        time.sleep(1)

        # Should miss after expiration
        expired_result = cache.get(query, start_time, end_time)
        assert expired_result is None
        assert cache._stats["misses"] == 1

    def test_hit_count_increment(self) -> None:
        """Test hit count increments on cache access."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        result = {"data": "test"}
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Put result
        cache.put(query, result, start_time, end_time)

        # Get multiple times
        cache.get(query, start_time, end_time)
        cache.get(query, start_time, end_time)
        cache.get(query, start_time, end_time)

        # Check hit count in cache entry
        cache_key = cache._generate_cache_key(query, start_time, end_time)
        entry = cache._cache[cache_key]
        assert entry.hit_count == 3

    def test_ttl_extension_on_frequent_access(self) -> None:
        """Test TTL extension for frequently accessed entries."""
        config: Dict[str, Any] = {
            "agents": {
                "detection": {
                    "query_cache": {
                        "min_hit_count_for_extension": 2,
                        "default_ttl_minutes": 60,
                    }
                }
            }
        }
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        result = {"data": "test"}
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Put result
        cache.put(query, result, start_time, end_time)

        # Get initial expiration time
        cache_key = cache._generate_cache_key(query, start_time, end_time)
        initial_expires = cache._cache[cache_key].expires_at

        # Access once (hit count = 1)
        cache.get(query, start_time, end_time)
        first_expires = cache._cache[cache_key].expires_at
        assert first_expires == initial_expires  # No extension yet

        # Access again (hit count = 2, should trigger extension)
        cache.get(query, start_time, end_time)
        extended_expires = cache._cache[cache_key].expires_at
        assert extended_expires > initial_expires  # TTL extended

    def test_cache_eviction(self) -> None:
        """Test cache eviction when max entries reached."""
        config: Dict[str, Any] = {
            "agents": {"detection": {"query_cache": {"max_entries": 3}}}
        }
        cache = QueryCache(config)

        base_time = datetime.now()

        # Fill cache to max capacity
        for i in range(3):
            query = f"SELECT * FROM table{i}"
            cache.put(query, {"data": i}, base_time, base_time + timedelta(hours=1))

        assert len(cache._cache) == 3
        assert cache._stats["evictions"] == 0

        # Add one more (should trigger eviction)
        cache.put(
            "SELECT * FROM table3",
            {"data": 3},
            base_time,
            base_time + timedelta(hours=1),
        )

        assert len(cache._cache) == 3  # Still at max
        assert cache._stats["evictions"] == 1

    def test_evict_oldest_empty_cache(self) -> None:
        """Test eviction on empty cache doesn't crash."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        # Should not crash on empty cache
        cache._evict_oldest()
        assert len(cache._cache) == 0
        assert cache._stats["evictions"] == 0

    def test_invalidate_by_rule_type(self) -> None:
        """Test cache invalidation by rule type."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        base_time = datetime.now()

        # Add entries with different rule types
        cache.put(
            "SELECT * FROM logs1",
            {"data": 1},
            base_time,
            base_time + timedelta(hours=1),
            rule_type="QUERY",
        )
        cache.put(
            "SELECT * FROM logs2",
            {"data": 2},
            base_time,
            base_time + timedelta(hours=1),
            rule_type="THRESHOLD",
        )
        cache.put(
            "SELECT * FROM logs3",
            {"data": 3},
            base_time,
            base_time + timedelta(hours=1),
            rule_type="QUERY",
        )
        cache.put(
            "SELECT * FROM logs4",
            {"data": 4},
            base_time,
            base_time + timedelta(hours=1),
            rule_type=None,
        )

        assert len(cache._cache) == 4

        # Invalidate QUERY rule type
        invalidated = cache.invalidate(rule_type="QUERY")

        assert invalidated == 2
        assert len(cache._cache) == 2

    def test_invalidate_by_age(self) -> None:
        """Test cache invalidation by age."""
        config: Dict[str, Any] = {}
        cache = QueryCache(config)

        base_time = datetime.now()
        old_time = base_time - timedelta(hours=2)

        # Add entries with different ages
        cache.put(
            "SELECT * FROM logs1",
            {"data": 1},
            base_time,
            base_time + timedelta(hours=1),
        )
        cache.put(
            "SELECT * FROM logs2",
            {"data": 2},
            base_time,
            base_time + timedelta(hours=1),
        )

        # Manually set one entry to be older
        cache_key = list(cache._cache.keys())[0]
        cache._cache[cache_key].created_at = old_time

        # Invalidate entries older than 1 hour ago
        cutoff_time = base_time - timedelta(hours=1)
        invalidated = cache.invalidate(older_than=cutoff_time)

        assert invalidated == 1
        assert len(cache._cache) == 1

    def test_invalidate_disabled_cache(self) -> None:
        """Test invalidation on disabled cache."""
        config: dict[str, dict[str, dict[str, dict[str, bool]]]] = {
            "agents": {"detection": {"query_cache": {"enabled": False}}}
        }
        cache = QueryCache(config)

        # Should return 0 when disabled
        invalidated = cache.invalidate(rule_type="QUERY")
        assert invalidated == 0

    def test_invalidate_no_matches(self) -> None:
        """Test invalidation when no entries match criteria."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        base_time = datetime.now()
        cache.put(
            "SELECT * FROM logs",
            {"data": 1},
            base_time,
            base_time + timedelta(hours=1),
            rule_type="QUERY",
        )

        # Invalidate non-existent rule type
        invalidated = cache.invalidate(rule_type="NONEXISTENT")
        assert invalidated == 0
        assert len(cache._cache) == 1

    def test_clear_cache(self) -> None:
        """Test clearing all cache entries."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        base_time = datetime.now()

        # Add multiple entries
        for i in range(5):
            query = f"SELECT * FROM table{i}"
            cache.put(query, {"data": i}, base_time, base_time + timedelta(hours=1))

        assert len(cache._cache) == 5

        # Clear cache
        cache.clear()

        assert len(cache._cache) == 0

    def test_get_stats_empty_cache(self) -> None:
        """Test statistics on empty cache."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        stats = cache.get_stats()

        expected_stats = {
            "enabled": True,
            "size": 0,
            "max_size": 1000,
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0,
            "hit_rate": "0.00%",
            "default_ttl_minutes": 60,
        }

        assert stats == expected_stats

    def test_get_stats_with_activity(self) -> None:
        """Test statistics after cache activity."""
        config: dict[str, dict[str, dict[str, dict[str, int]]]] = {
            "agents": {
                "detection": {
                    "query_cache": {"max_entries": 500, "default_ttl_minutes": 30}
                }
            }
        }
        cache = QueryCache(config)

        base_time = datetime.now()

        # Add entry and access it
        cache.put(
            "SELECT * FROM logs",
            {"data": "test"},
            base_time,
            base_time + timedelta(hours=1),
        )
        cache.get(
            "SELECT * FROM logs", base_time, base_time + timedelta(hours=1)
        )  # Hit
        cache.get(
            "SELECT * FROM other", base_time, base_time + timedelta(hours=1)
        )  # Miss

        stats = cache.get_stats()

        assert stats["enabled"] is True
        assert stats["size"] == 1
        assert stats["max_size"] == 500
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total_queries"] == 2
        assert stats["hit_rate"] == "50.00%"
        assert stats["default_ttl_minutes"] == 30

    def test_get_cache_info_empty(self) -> None:
        """Test cache info on empty cache."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        info = cache.get_cache_info()

        assert info["total_entries"] == 0
        assert not info["entries"]

    def test_get_cache_info_with_entries(self) -> None:
        """Test cache info with entries."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        base_time = datetime.now()

        # Add entries with different hit counts
        cache.put(
            "SELECT * FROM logs1",
            {"data": 1},
            base_time,
            base_time + timedelta(hours=1),
            rule_type="QUERY",
        )
        cache.put(
            "SELECT * FROM logs2",
            {"data": 2},
            base_time,
            base_time + timedelta(hours=1),
            rule_type="THRESHOLD",
        )

        # Access first entry multiple times
        cache.get("SELECT * FROM logs1", base_time, base_time + timedelta(hours=1))
        cache.get("SELECT * FROM logs1", base_time, base_time + timedelta(hours=1))

        info = cache.get_cache_info()

        assert info["total_entries"] == 2
        assert len(info["entries"]) == 2

        # Should be sorted by hit count (first entry should have more hits)
        first_entry = info["entries"][0]
        assert first_entry["hit_count"] == 2
        assert first_entry["rule_type"] == "QUERY"
        assert "expires_in_minutes" in first_entry
        assert "created_at" in first_entry
        assert "hash" in first_entry
        assert "query_preview" in first_entry

    def test_get_cache_info_truncation(self) -> None:
        """Test cache info only returns top 10 entries."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        base_time = datetime.now()

        # Add 15 entries
        for i in range(15):
            query = f"SELECT * FROM table{i}"
            cache.put(query, {"data": i}, base_time, base_time + timedelta(hours=1))

        info = cache.get_cache_info()

        assert info["total_entries"] == 15
        assert len(info["entries"]) == 10  # Should be truncated to top 10

    def test_cache_with_rule_type_operations(self) -> None:
        """Test cache operations with rule types."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        result = {"data": "test"}
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Put with rule type
        cache.put(query, result, start_time, end_time, rule_type="PATTERN")

        # Get with same rule type
        cached_result = cache.get(query, start_time, end_time, rule_type="PATTERN")
        assert cached_result == result

        # Get with different rule type should miss
        missed_result = cache.get(query, start_time, end_time, rule_type="THRESHOLD")
        assert missed_result is None

    def test_cache_custom_ttl(self) -> None:
        """Test cache with custom TTL."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        result = {"data": "test"}
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Put with custom TTL
        cache.put(query, result, start_time, end_time, ttl_minutes=120)

        # Check entry has correct TTL
        cache_key = cache._generate_cache_key(query, start_time, end_time)
        entry = cache._cache[cache_key]

        # TTL should be approximately 120 minutes from now
        time_diff = (entry.expires_at - datetime.now()).total_seconds() / 60
        assert 119 < time_diff < 121  # Allow for small timing differences

    def test_edge_case_empty_query(self) -> None:
        """Test edge case with empty query."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        query = ""
        result = {"data": "empty_query_result"}
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        cache.put(query, result, start_time, end_time)
        cached_result = cache.get(query, start_time, end_time)

        assert cached_result == result

    def test_edge_case_none_result(self) -> None:
        """Test edge case with None result."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        result = None
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        cache.put(query, result, start_time, end_time)
        cached_result = cache.get(query, start_time, end_time)

        assert cached_result is None

    def test_edge_case_large_query(self) -> None:
        """Test edge case with very large query."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        # Create a large query (over 500 characters)
        large_query = (
            "SELECT " + ", ".join([f"column_{i}" for i in range(100)]) + " FROM logs"
        )
        result = {"data": "large_query_result"}
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        cache.put(large_query, result, start_time, end_time)
        cached_result = cache.get(large_query, start_time, end_time)

        assert cached_result == result

        # Check that query text is truncated in cache entry
        cache_key = cache._generate_cache_key(large_query, start_time, end_time)
        entry = cache._cache[cache_key]
        assert len(entry.query_text) <= 500

    def test_complex_result_types(self) -> None:
        """Test caching complex result types."""
        config: dict[str, str] = {}
        cache = QueryCache(config)

        query = "SELECT * FROM logs"
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        # Test with list result
        list_result = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        cache.put(query + "_list", list_result, start_time, end_time)
        cached_list = cache.get(query + "_list", start_time, end_time)
        assert cached_list == list_result

        # Test with nested dict result
        nested_result = {
            "metadata": {"count": 100, "page": 1},
            "data": [{"nested": {"deep": {"value": 42}}}],
        }
        cache.put(query + "_nested", nested_result, start_time, end_time)
        cached_nested = cache.get(query + "_nested", start_time, end_time)
        assert cached_nested == nested_result

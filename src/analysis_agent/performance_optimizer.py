"""
Performance optimization for the Analysis Agent.

This module implements caching, batching, and rate limiting to optimize
the performance of the Analysis Agent.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from collections.abc import Awaitable
from datetime import datetime, timezone
from typing import Any, Callable, Optional, cast

from src.common.token_optimizer import TokenOptimizer


class AnalysisCache:
    """In-memory cache for analysis results and intermediate data."""

    def __init__(self, ttl: int = 3600, max_size: int = 1000) -> None:
        """
        Initialize the analysis cache.

        Args:
            ttl: Time to live in seconds (default: 1 hour)
            max_size: Maximum number of entries in cache
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._access_times: deque[tuple[str, float]] = deque(maxlen=max_size)
        self._ttl = ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if it exists and is not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                self._hits += 1
                # Update access time
                self._access_times.append((key, time.time()))
                return value
            else:
                # Expired entry
                del self._cache[key]

        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in cache with current timestamp."""
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            self._evict_oldest()

        self._cache[key] = (value, time.time())
        self._access_times.append((key, time.time()))

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Args:
            pattern: Optional pattern to match keys (prefix match)

        Returns:
            Number of entries invalidated
        """
        if pattern is None:
            # Clear entire cache
            count = len(self._cache)
            self._cache.clear()
            self._access_times.clear()
            return count

        # Invalidate entries matching pattern
        keys_to_remove = [key for key in self._cache if key.startswith(pattern)]

        for key in keys_to_remove:
            del self._cache[key]

        return len(keys_to_remove)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl": self._ttl,
        }

    def _evict_oldest(self) -> None:
        """Evict oldest entries to make room."""
        # Remove 10% of entries
        entries_to_remove = max(1, self._max_size // 10)

        # Sort by timestamp and remove oldest
        sorted_entries = sorted(
            self._cache.items(), key=lambda x: x[1][1]  # Sort by timestamp
        )

        for key, _ in sorted_entries[:entries_to_remove]:
            del self._cache[key]


class RequestBatcher:
    """Batches similar requests to optimize API usage."""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 1.0) -> None:
        """
        Initialize the request batcher.

        Args:
            batch_size: Maximum number of requests in a batch
            batch_timeout: Maximum time to wait before processing batch
        """
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout
        self._batches: dict[str, list[tuple[Any, asyncio.Future[Any]]]] = defaultdict(
            list
        )
        self._batch_timers: dict[str, asyncio.Task[None]] = {}

    async def add_request(
        self,
        batch_key: str,
        request_data: Any,
        processor_func: Callable[[list[Any]], Awaitable[list[Any]]],
    ) -> Any:
        """
        Add a request to be batched.

        Args:
            batch_key: Key to group similar requests
            request_data: The request data
            processor_func: Function to process the batch

        Returns:
            The result of the request
        """
        # Create a future for this request
        future: asyncio.Future[Any] = asyncio.Future()

        # Add to batch
        self._batches[batch_key].append((request_data, future))

        # Check if batch is full
        if len(self._batches[batch_key]) >= self._batch_size:
            await self._process_batch(batch_key, processor_func)
        elif batch_key not in self._batch_timers:
            # Start timer for this batch
            self._batch_timers[batch_key] = asyncio.create_task(
                self._batch_timer(batch_key, processor_func)
            )

        # Wait for result
        return await future

    async def _batch_timer(
        self,
        batch_key: str,
        processor_func: Callable[[list[Any]], Awaitable[list[Any]]],
    ) -> None:
        """Timer to process batch after timeout."""
        await asyncio.sleep(self._batch_timeout)
        await self._process_batch(batch_key, processor_func)

    async def _process_batch(
        self,
        batch_key: str,
        processor_func: Callable[[list[Any]], Awaitable[list[Any]]],
    ) -> None:
        """Process a batch of requests."""
        if batch_key not in self._batches:
            return

        batch = self._batches[batch_key]
        if not batch:
            return

        # Cancel timer if exists
        if batch_key in self._batch_timers:
            self._batch_timers[batch_key].cancel()
            del self._batch_timers[batch_key]

        # Extract request data
        requests = [req for req, _ in batch]
        futures = [future for _, future in batch]

        try:
            # Process batch
            results = await processor_func(requests)

            # Distribute results
            for i, future in enumerate(futures):
                if i < len(results):
                    future.set_result(results[i])
                else:
                    future.set_exception(Exception("No result for request in batch"))
        except (ValueError, KeyError, AttributeError, TypeError) as e:
            # Set exception for all futures
            for future in futures:
                future.set_exception(e)
        finally:
            # Clear batch
            del self._batches[batch_key]


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, max_per_minute: int = 30, max_per_hour: int = 500) -> None:
        """
        Initialize the rate limiter.

        Args:
            max_per_minute: Maximum requests per minute
            max_per_hour: Maximum requests per hour
        """
        self._max_per_minute = max_per_minute
        self._max_per_hour = max_per_hour
        self._minute_window: deque[float] = deque()
        self._hour_window: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            now = time.time()

            # Clean old entries
            self._clean_windows(now)

            # Check limits
            while (
                len(self._minute_window) >= self._max_per_minute
                or len(self._hour_window) >= self._max_per_hour
            ):
                # Calculate wait time
                wait_time = self._calculate_wait_time(now)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                # Clean again after waiting
                now = time.time()
                self._clean_windows(now)

            # Add current request
            self._minute_window.append(now)
            self._hour_window.append(now)

    def _clean_windows(self, now: float) -> None:
        """Remove old entries from windows."""
        minute_ago = now - 60
        hour_ago = now - 3600

        # Clean minute window
        while self._minute_window and self._minute_window[0] < minute_ago:
            self._minute_window.popleft()

        # Clean hour window
        while self._hour_window and self._hour_window[0] < hour_ago:
            self._hour_window.popleft()

    def _calculate_wait_time(self, now: float) -> float:
        """Calculate how long to wait before next request."""
        wait_times = []

        # Check minute limit
        if len(self._minute_window) >= self._max_per_minute:
            oldest_minute = self._minute_window[0]
            wait_times.append(60 - (now - oldest_minute))

        # Check hour limit
        if len(self._hour_window) >= self._max_per_hour:
            oldest_hour = self._hour_window[0]
            wait_times.append(3600 - (now - oldest_hour))

        return max(wait_times) if wait_times else 0

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "minute_window_size": len(self._minute_window),
            "hour_window_size": len(self._hour_window),
            "max_per_minute": self._max_per_minute,
            "max_per_hour": self._max_per_hour,
        }


class PerformanceOptimizer:
    """Main performance optimization coordinator."""

    rate_limiter: Optional[RateLimiter]

    def __init__(self, config: dict[str, Any], logger: logging.Logger) -> None:
        """
        Initialize the performance optimizer.

        Args:
            config: Performance configuration
            logger: Logger instance
        """
        self.logger = logger
        self.config = config

        # Initialize components
        self.cache = AnalysisCache(
            ttl=config.get("cache_ttl", 3600),
            max_size=config.get("cache_max_size", 1000),
        )

        self.batcher = RequestBatcher(
            batch_size=config.get("batch_size", 10),
            batch_timeout=config.get("batch_timeout", 1.0),
        )

        rate_limit_config = config.get("rate_limit", {})
        if rate_limit_config.get("enabled", True):
            self.rate_limiter = RateLimiter(
                max_per_minute=rate_limit_config.get("max_per_minute", 30),
                max_per_hour=rate_limit_config.get("max_per_hour", 500),
            )
        else:
            self.rate_limiter = None

        # Initialize token optimizer
        self.token_optimizer = TokenOptimizer()

        # Batch queue for similar incidents
        self._batch_queue: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(
            list
        )
        self._batch_processors: dict[str, asyncio.Task[None]] = {}

    def generate_cache_key(self, incident_id: str, data_hash: str) -> str:
        """Generate a cache key for an analysis."""
        return f"analysis:{incident_id}:{data_hash}"

    def compute_data_hash(self, data: dict[str, Any]) -> str:
        """Compute a hash of incident data for caching."""
        # Create a stable string representation
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    async def get_cached_analysis(
        self, incident_id: str, incident_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Get cached analysis if available."""
        if not self.config.get("cache_enabled", True):
            return None

        data_hash = self.compute_data_hash(incident_data)
        cache_key = self.generate_cache_key(incident_id, data_hash)

        cached_result = self.cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Cache hit for incident {incident_id}")
            return cast(dict[str, Any], cached_result)

        return None

    def cache_analysis(
        self, incident_id: str, incident_data: dict[str, Any], result: dict[str, Any]
    ) -> None:
        """Cache an analysis result."""
        if not self.config.get("cache_enabled", True):
            return

        data_hash = self.compute_data_hash(incident_data)
        cache_key = self.generate_cache_key(incident_id, data_hash)

        self.cache.set(cache_key, result)
        self.logger.debug(f"Cached analysis for incident {incident_id}")

    async def check_rate_limit(self) -> None:
        """Check and enforce rate limits."""
        if self.rate_limiter:
            await self.rate_limiter.acquire()

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics."""
        metrics = {
            "cache_stats": self.cache.get_stats(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if self.rate_limiter:
            metrics["rate_limiter_stats"] = self.rate_limiter.get_stats()

        return metrics

    def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries."""
        count = self.cache.invalidate(pattern)
        self.logger.info(f"Invalidated {count} cache entries")
        return count

    async def batch_similar_requests(
        self,
        incident_id: str,
        incident_data: dict[str, Any],
        processor_func: Callable[[list[Any]], Awaitable[list[Any]]],
    ) -> Optional[Any]:
        """
        Batch similar analysis requests to optimize API usage.

        Args:
            incident_id: The incident ID
            incident_data: The incident data
            processor_func: Function to process the batch

        Returns:
            The analysis result if batching is used, None otherwise
        """
        if not self.config.get("batch_enabled", False):
            return None

        # Determine batch key based on incident characteristics
        batch_key = self._get_batch_key(incident_data)

        # Add to batch queue
        self._batch_queue[batch_key].append((incident_id, incident_data))

        # Check if we should process the batch
        if len(self._batch_queue[batch_key]) >= self.config.get("batch_size", 5):
            # Process batch immediately
            return await self._process_incident_batch(batch_key, processor_func)
        elif batch_key not in self._batch_processors:
            # Schedule batch processing
            self._batch_processors[batch_key] = asyncio.create_task(
                self._delayed_batch_processing(batch_key, processor_func)
            )

        return None

    def _get_batch_key(self, incident_data: dict[str, Any]) -> str:
        """Generate a batch key based on incident characteristics."""
        # Group by severity and general event types
        severity = incident_data.get("severity", "unknown")
        event_types = set()

        for event in incident_data.get("events", [])[:5]:  # Check first 5 events
            event_type = event.get("event_type", "").split("_")[0]  # Get prefix
            event_types.add(event_type)

        event_signature = "_".join(sorted(event_types))
        return f"{severity}:{event_signature}"

    async def _delayed_batch_processing(
        self,
        batch_key: str,
        processor_func: Callable[[list[Any]], Awaitable[list[Any]]],
    ) -> None:
        """Process a batch after a delay."""
        await asyncio.sleep(self.config.get("batch_timeout", 2.0))
        await self._process_incident_batch(batch_key, processor_func)

    async def _process_incident_batch(
        self,
        batch_key: str,
        processor_func: Callable[[list[Any]], Awaitable[list[Any]]],
    ) -> Any:
        """Process a batch of similar incidents."""
        if batch_key not in self._batch_queue:
            return None

        batch = self._batch_queue[batch_key]
        if not batch:
            return None

        try:
            # Clear the batch
            del self._batch_queue[batch_key]
            if batch_key in self._batch_processors:
                del self._batch_processors[batch_key]

            self.logger.info(f"Processing batch of {len(batch)} incidents")

            # Process the batch using the provided function
            results = await processor_func(batch)
            return results

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            self.logger.error("Error processing batch: %s", e)
            return None

    def optimize_prompt_tokens(
        self,
        incident: Any,
        metadata: dict[str, Any],
        correlation_results: dict[str, Any],
        additional_context: Optional[dict[str, Any]] = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Optimize a prompt to minimize token usage.

        Args:
            incident: The incident object
            metadata: Incident metadata
            correlation_results: Correlation results
            additional_context: Optional additional context

        Returns:
            Tuple of (optimized_prompt, optimization_stats)
        """
        # Generate optimized prompt
        # Create a combined prompt from all the data
        prompt_parts = [
            f"Incident: {incident}",
            f"Metadata: {metadata}",
            f"Correlation Results: {correlation_results}"
        ]
        if additional_context:
            prompt_parts.append(f"Additional Context: {additional_context}")

        full_prompt = "\n\n".join(prompt_parts)
        optimized_prompt = self.token_optimizer.optimize_prompt(full_prompt)

        # Get stats (if we had the original prompt)
        stats = {
            "optimized_length": len(optimized_prompt),
            "estimated_tokens": self.token_optimizer.estimate_tokens(optimized_prompt),
        }

        return optimized_prompt, stats

    def prepare_batch_prompts(
        self, incidents: list[tuple[Any, dict[str, Any]]]
    ) -> list[str]:
        """
        Prepare optimized prompts for batch processing.

        Args:
            incidents: List of (incident, metadata) tuples

        Returns:
            List of optimized prompts
        """
        prompts = []
        for incident, metadata in incidents:
            prompt = f"Incident: {incident}\n\nMetadata: {metadata}"
            optimized = self.token_optimizer.optimize_prompt(prompt)
            prompts.append(optimized)
        return prompts

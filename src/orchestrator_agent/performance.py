"""
Performance optimization for the orchestrator agent.
"""

import asyncio
import functools
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set


class PerformanceOptimizer:
    """Handles performance optimization for the orchestrator agent."""

    def __init__(self, orchestrator_agent: Any):
        """Initialize the performance optimizer."""
        self.agent = orchestrator_agent

        # Caching
        self.incident_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=5)
        self.cache_timestamps: Dict[str, datetime] = {}

        # Batching
        self.firestore_batch_queue: deque[Dict[str, Any]] = deque()
        self.batch_size = 50
        self.batch_timeout = 1.0  # seconds
        self._batch_task: Optional[asyncio.Task[None]] = None

        # Connection pooling
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

        # Query optimization
        self.query_cache: Dict[str, Any] = {}
        self.indexed_fields = ["status", "severity", "created_at", "assigned_to"]

        # Resource limits
        self.max_concurrent_operations: Dict[str, int] = {
            "analysis_requests": 5,
            "remediation_requests": 3,
            "notifications": 10,
            "firestore_writes": 20,
        }
        self.current_operations: Dict[str, Set[str]] = {
            key: set() for key in self.max_concurrent_operations
        }

    async def initialize(self) -> None:
        """Initialize the performance optimizer."""
        # Start batch processing task
        self._batch_task = asyncio.create_task(self._batch_processor())

        # Warm up caches
        await self._warm_up_caches()

    async def shutdown(self) -> None:
        """Shutdown the performance optimizer."""
        # Cancel batch task
        if self._batch_task:
            self._batch_task.cancel()

        # Flush remaining batches
        await self._flush_batch()

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)

    async def get_incident_optimized(
        self, incident_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get incident data with caching."""
        # Check cache first
        if incident_id in self.incident_cache:
            cache_time = self.cache_timestamps.get(incident_id)
            if (
                cache_time
                and (datetime.now(timezone.utc) - cache_time) < self.cache_ttl
            ):
                return self.incident_cache[incident_id]

        # Fetch from Firestore
        doc = await self.agent.incidents_collection.document(incident_id).get()
        if doc.exists:
            incident_data: Optional[Dict[str, Any]] = doc.to_dict()
            if incident_data is None:
                return None

            # Update cache
            self.incident_cache[incident_id] = incident_data
            self.cache_timestamps[incident_id] = datetime.now(timezone.utc)

            # Limit cache size
            if len(self.incident_cache) > 1000:
                self._evict_cache_entries()

            return incident_data

        return None

    def invalidate_incident_cache(self, incident_id: str) -> None:
        """Invalidate cache entry for an incident."""
        self.incident_cache.pop(incident_id, None)
        self.cache_timestamps.pop(incident_id, None)

    async def batch_firestore_write(
        self, operation_type: str, document_ref: Any, data: Dict[str, Any]
    ) -> None:
        """Add a Firestore write operation to the batch queue."""
        operation = {
            "type": operation_type,
            "ref": document_ref,
            "data": data,
            "timestamp": datetime.now(timezone.utc),
        }

        self.firestore_batch_queue.append(operation)

        # Trigger immediate flush if batch is full
        if len(self.firestore_batch_queue) >= self.batch_size:
            await self._flush_batch()

    async def _batch_processor(self) -> None:
        """Process batched operations periodically."""
        while True:
            try:
                await asyncio.sleep(self.batch_timeout)

                if self.firestore_batch_queue:
                    await self._flush_batch()

            except asyncio.CancelledError:
                break
            except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                self.agent.logger.error("Batch processor error: %s", e)

    async def _flush_batch(self) -> None:
        """Flush the current batch to Firestore."""
        if not self.firestore_batch_queue:
            return

        # Create a batch
        batch = self.agent.db.batch()
        operations_count = 0

        while self.firestore_batch_queue and operations_count < self.batch_size:
            operation = self.firestore_batch_queue.popleft()

            if operation["type"] == "set":
                batch.set(operation["ref"], operation["data"])
            elif operation["type"] == "update":
                batch.update(operation["ref"], operation["data"])
            elif operation["type"] == "delete":
                batch.delete(operation["ref"])

            operations_count += 1

        try:
            # Commit the batch
            await batch.commit()
            self.agent.logger.debug(
                f"Flushed {operations_count} operations to Firestore"
            )
        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            self.agent.logger.error("Batch commit failed: %s", e)
            # Re-queue failed operations
            for _ in range(operations_count):
                self.firestore_batch_queue.appendleft(operation)

    async def optimize_query(
        self,
        collection: Any,
        filters: List[tuple[str, str, Any]],
        order_by: Optional[tuple[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Optimize Firestore queries with caching."""
        # Create cache key
        cache_key = f"{collection.id}:{filters}:{order_by}:{limit}"

        # Check cache
        if cache_key in self.query_cache:
            cached_result = self.query_cache[cache_key]
            if (datetime.now(timezone.utc) - cached_result["timestamp"]) < timedelta(
                seconds=30
            ):
                cached_data = cached_result["data"]
                if isinstance(cached_data, list):
                    return cached_data
                return []

        # Build optimized query
        query = collection

        # Apply filters in optimal order (indexed fields first)
        sorted_filters = sorted(
            filters, key=lambda f: 0 if f[0] in self.indexed_fields else 1
        )

        for field, op, value in sorted_filters:
            query = query.where(field, op, value)

        if order_by:
            query = query.order_by(*order_by)

        if limit:
            query = query.limit(limit)

        # Execute query
        results = []
        for doc in query.stream():
            results.append(doc.to_dict())

        # Cache results
        self.query_cache[cache_key] = {
            "data": results,
            "timestamp": datetime.now(timezone.utc),
        }

        # Limit cache size
        if len(self.query_cache) > 100:
            self._evict_query_cache()

        return results

    async def rate_limit_operation(
        self, operation_type: str, operation_id: str
    ) -> bool:
        """
        Check if an operation can proceed based on rate limits.

        Returns:
            True if operation can proceed, False if rate limited
        """
        if operation_type not in self.max_concurrent_operations:
            return True

        current_count = len(self.current_operations[operation_type])
        max_allowed = self.max_concurrent_operations[operation_type]

        if current_count >= max_allowed:
            self.agent.logger.warning(
                f"Rate limit reached for {operation_type}: {current_count}/{max_allowed}"
            )
            return False

        # Add to current operations
        self.current_operations[operation_type].add(operation_id)

        # Schedule removal
        asyncio.create_task(
            self._remove_operation_after_delay(operation_type, operation_id)
        )

        return True

    async def _remove_operation_after_delay(
        self, operation_type: str, operation_id: str, delay: float = 60.0
    ) -> None:
        """Remove an operation from tracking after a delay."""
        await asyncio.sleep(delay)
        self.current_operations[operation_type].discard(operation_id)

    def _evict_cache_entries(self, target_size: int = 800) -> None:
        """Evict oldest cache entries."""
        # Sort by timestamp
        sorted_entries = sorted(self.cache_timestamps.items(), key=lambda x: x[1])

        # Remove oldest entries
        entries_to_remove = len(self.incident_cache) - target_size
        for incident_id, _ in sorted_entries[:entries_to_remove]:
            self.incident_cache.pop(incident_id, None)
            self.cache_timestamps.pop(incident_id, None)

    def _evict_query_cache(self, target_size: int = 50) -> None:
        """Evict oldest query cache entries."""
        # Sort by timestamp
        sorted_entries = sorted(
            self.query_cache.items(), key=lambda x: x[1]["timestamp"]
        )

        # Remove oldest entries
        entries_to_remove = len(self.query_cache) - target_size
        for cache_key, _ in sorted_entries[:entries_to_remove]:
            self.query_cache.pop(cache_key, None)

    async def _warm_up_caches(self) -> None:
        """Pre-populate caches with frequently accessed data."""
        try:
            # Cache active incidents
            active_statuses = ["detected", "analyzing", "remediation_pending"]
            query = self.agent.incidents_collection.where(
                "status", "in", active_statuses
            ).limit(100)

            for doc in query.stream():
                incident_id = doc.id
                incident_data = doc.to_dict()

                self.incident_cache[incident_id] = incident_data
                self.cache_timestamps[incident_id] = datetime.now(timezone.utc)

            self.agent.logger.info(
                f"Warmed up cache with {len(self.incident_cache)} incidents"
            )

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            self.agent.logger.error("Cache warm-up failed: %s", e)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            return {
                "cache_size": len(self.incident_cache),
                "cache_hit_rate": self._calculate_cache_hit_rate(),
                "batch_queue_size": len(self.firestore_batch_queue),
                "current_operations": {
                    op_type: len(ops)
                    for op_type, ops in self.current_operations.items()
                },
                "thread_pool_active": self.thread_pool._threads,
                "query_cache_size": len(self.query_cache),
            }
        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            print(f"Failed to get performance data: {e}")
            return {}

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (placeholder)."""
        # In a real implementation, track hits and misses
        return 0.0

    def create_optimized_handler(self, handler: Any) -> Any:
        """Create an optimized version of a handler with caching and rate limiting."""

        @functools.wraps(handler)
        async def optimized_handler(*args: Any, **kwargs: Any) -> Any:
            # Add performance optimizations
            start_time = datetime.now(timezone.utc)

            try:
                result = await handler(*args, **kwargs)

                # Record performance metrics
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                await self.agent.metrics_collector.record_duration(
                    "handler_execution_time", duration, {"handler": handler.__name__}
                )

                return result

            except Exception as e:
                # Record error metrics
                await self.agent.metrics_collector.increment_counter(
                    "handler_errors",
                    {"handler": handler.__name__, "error_type": type(e).__name__},
                )
                raise

        return optimized_handler

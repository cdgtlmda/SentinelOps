"""
Performance optimization module for the Remediation Agent.

This module implements caching, batch operations, and performance monitoring
to ensure efficient execution of remediation actions.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import google.cloud.monitoring_v3 as monitoring
import redis.asyncio as aioredis

from src.common.models import RemediationAction


class PerformanceMetrics:
    """Tracks performance metrics for remediation operations."""

    def __init__(self, window_size: int = 300):  # 5-minute window
        """
        Initialize performance metrics tracker.

        Args:
            window_size: Time window in seconds for metrics
        """
        self.window_size = window_size
        self._metrics: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def record_execution_time(
        self, action_type: str, execution_time: float
    ) -> None:
        """Record execution time for an action."""
        async with self._lock:
            timestamp = time.time()
            self._metrics[f"execution_time_{action_type}"].append(
                (timestamp, execution_time)
            )
            self._cleanup_old_metrics()

    async def record_api_call(
        self, api_name: str, latency: float, success: bool
    ) -> None:
        """Record API call metrics."""
        async with self._lock:
            timestamp = time.time()
            metric_name = f"api_latency_{api_name}"
            self._metrics[metric_name].append((timestamp, latency))

            if success:
                self._counters[f"api_success_{api_name}"] += 1
            else:
                self._counters[f"api_failure_{api_name}"] += 1

            self._cleanup_old_metrics()

    async def get_average_execution_time(self, action_type: str) -> Optional[float]:
        """Get average execution time for an action type."""
        async with self._lock:
            metrics = self._metrics.get(f"execution_time_{action_type}", [])
            if not metrics:
                return None

            values = [value for _, value in metrics]
            return sum(values) / len(values)

    async def get_api_success_rate(self, api_name: str) -> float:
        """Get API success rate."""
        async with self._lock:
            success_count = self._counters.get(f"api_success_{api_name}", 0)
            failure_count = self._counters.get(f"api_failure_{api_name}", 0)

            total = success_count + failure_count
            if total == 0:
                return 1.0

            return success_count / total

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        async with self._lock:
            summary: Dict[str, Any] = {
                "execution_times": {},
                "api_latencies": {},
                "api_success_rates": {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Calculate average execution times
            for metric_name, values in self._metrics.items():
                if metric_name.startswith("execution_time_"):
                    action_type = metric_name.replace("execution_time_", "")
                    if values:
                        avg_time = sum(v for _, v in values) / len(values)
                        summary["execution_times"][action_type] = {
                            "average": avg_time,
                            "count": len(values),
                        }

                elif metric_name.startswith("api_latency_"):
                    api_name = metric_name.replace("api_latency_", "")
                    if values:
                        latencies = [v for _, v in values]
                        summary["api_latencies"][api_name] = {
                            "average": sum(latencies) / len(latencies),
                            "p95": self._calculate_percentile(latencies, 0.95),
                            "p99": self._calculate_percentile(latencies, 0.99),
                        }

            # Calculate API success rates
            api_names = set()
            for counter_name in self._counters:
                if counter_name.startswith("api_success_") or counter_name.startswith(
                    "api_failure_"
                ):
                    api_name = counter_name.split("_", 2)[2]
                    api_names.add(api_name)

            for api_name in api_names:
                # Calculate success rate inline to avoid deadlock
                success_count = self._counters.get(f"api_success_{api_name}", 0)
                failure_count = self._counters.get(f"api_failure_{api_name}", 0)
                total = success_count + failure_count
                success_rate = success_count / total if total > 0 else 1.0
                summary["api_success_rates"][api_name] = success_rate

            return summary

    def _cleanup_old_metrics(self) -> None:
        """Remove metrics outside the time window."""
        cutoff_time = time.time() - self.window_size

        for metric_name in list(self._metrics.keys()):
            self._metrics[metric_name] = [
                (timestamp, value)
                for timestamp, value in self._metrics[metric_name]
                if timestamp > cutoff_time
            ]

            if not self._metrics[metric_name]:
                del self._metrics[metric_name]

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


class CacheManager:
    """Manages caching for remediation operations."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 300,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize cache manager.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
            logger: Logger instance
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.logger = logger or logging.getLogger(__name__)
        self._redis_client: Optional[aioredis.Redis] = None
        self._local_cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_stats: Dict[str, int] = defaultdict(int)

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self.redis_url:
            try:
                self._redis_client = aioredis.from_url(
                    self.redis_url
                )  # type: ignore[no-untyped-call]
                if self._redis_client:
                    await self._redis_client.ping()
                self.logger.info("Redis cache initialized")
            except (ConnectionError, TypeError, ValueError) as e:
                self.logger.warning("Failed to connect to Redis: %s", e)
                self._redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._cache_stats["requests"] += 1

        # Try Redis first
        if self._redis_client:
            try:
                value = await self._redis_client.get(key)
                if value:
                    self._cache_stats["redis_hits"] += 1
                    return json.loads(value)
            except (ConnectionError, TypeError, ValueError) as e:
                self.logger.error(f"Redis get error: {e}")

        # Fall back to local cache
        if key in self._local_cache:
            value, expiry = self._local_cache[key]
            if time.time() < expiry:
                self._cache_stats["local_hits"] += 1
                return value
            else:
                del self._local_cache[key]

        self._cache_stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl

        # Store in Redis
        if self._redis_client:
            try:
                await self._redis_client.setex(key, ttl, json.dumps(value))
            except (ConnectionError, TypeError, ValueError) as e:
                self.logger.error(f"Redis set error: {e}")

        # Also store in local cache
        expiry = time.time() + ttl
        self._local_cache[key] = (value, expiry)

        # Cleanup old entries
        self._cleanup_local_cache()

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        if self._redis_client:
            try:
                await self._redis_client.delete(key)
            except (ConnectionError, TypeError, ValueError) as e:
                self.logger.error(f"Redis delete error: {e}")

        if key in self._local_cache:
            del self._local_cache[key]

    async def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return dict(self._cache_stats)

    def _cleanup_local_cache(self) -> None:
        """Remove expired entries from local cache."""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, expiry) in self._local_cache.items()
            if current_time >= expiry
        ]

        for key in expired_keys:
            del self._local_cache[key]

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()


class BatchOperationManager:
    """Manages batch operations for efficiency."""

    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout: float = 5.0,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize batch operation manager.

        Args:
            batch_size: Maximum batch size
            batch_timeout: Timeout for batch collection in seconds
            logger: Logger instance
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.logger = logger or logging.getLogger(__name__)

        self._batches: Dict[str, List[Any]] = defaultdict(list)
        self._batch_futures: Dict[str, asyncio.Future[Any]] = {}
        self._batch_tasks: Dict[str, asyncio.Task[Any]] = {}

    async def add_to_batch(self, operation_type: str, operation_data: Any) -> Any:
        """
        Add an operation to a batch.

        Args:
            operation_type: Type of operation
            operation_data: Operation data

        Returns:
            Result of the operation
        """
        # Add to batch
        self._batches[operation_type].append(operation_data)

        # Create future for this operation
        future: asyncio.Future[Any] = asyncio.Future()

        # Start batch processing if not already started
        if operation_type not in self._batch_tasks:
            self._batch_tasks[operation_type] = asyncio.create_task(
                self._process_batch(operation_type)
            )

        # Check if batch is full
        if len(self._batches[operation_type]) >= self.batch_size:
            # Trigger immediate processing
            if operation_type in self._batch_futures:
                self._batch_futures[operation_type].set_result(None)

        return await future

    async def _process_batch(self, operation_type: str) -> None:
        """Process a batch of operations."""
        while True:
            try:
                # Wait for batch to fill or timeout
                future: asyncio.Future[Any] = asyncio.Future()
                self._batch_futures[operation_type] = future

                try:
                    await asyncio.wait_for(future, timeout=self.batch_timeout)
                except asyncio.TimeoutError:
                    pass

                # Get current batch
                batch = self._batches[operation_type]
                if not batch:
                    continue

                # Clear batch
                self._batches[operation_type] = []

                # Process batch based on operation type
                await self._execute_batch(operation_type, batch)

                # Resolve futures with results
                # (Implementation would map results to original operations)

                self.logger.info(
                    "Processed batch of %d %s operations", len(batch), operation_type
                )

            except (RuntimeError, ValueError, TypeError) as e:
                self.logger.error("Batch processing error: %s", e)

    async def _execute_batch(self, operation_type: str, batch: List[Any]) -> List[Any]:
        """Execute a batch of operations."""
        if operation_type == "firewall_updates":
            return await self._batch_firewall_updates(batch)
        elif operation_type == "iam_changes":
            return await self._batch_iam_changes(batch)
        elif operation_type == "bucket_updates":
            return await self._batch_bucket_updates(batch)
        else:
            # Execute individually if no batch handler
            results: List[Any] = []
            for operation in batch:
                # Execute operation
                result = await self._execute_single_operation(operation_type, operation)
                results.append(result)
            return results

    async def _batch_firewall_updates(self, operations: List[Any]) -> List[Any]:
        """Batch firewall rule updates."""
        # Group by project and combine rules
        grouped = defaultdict(list)
        for op in operations:
            project_id = op.get("project_id")
            grouped[project_id].append(op)

        results: List[Any] = []
        for project_id in grouped.keys():
            # Combine into single API call where possible
            # (Implementation would use actual GCP batch API)
            pass

        return results

    async def _batch_iam_changes(self, operations: List[Any]) -> List[Any]:
        """Batch IAM policy changes."""
        # Group by resource and combine changes
        grouped = defaultdict(list)
        for op in operations:
            resource = op.get("resource")
            grouped[resource].append(op)

        results: List[Any] = []
        for resource in grouped.keys():
            # Apply all changes in single policy update
            # (Implementation would combine IAM changes)
            pass

        return results

    async def _batch_bucket_updates(self, operations: List[Any]) -> List[Any]:
        """Batch storage bucket updates."""
        # Similar batching logic for bucket operations
        _ = operations  # Mark as intentionally unused
        return []

    async def _execute_single_operation(
        self, operation_type: str, operation: Any
    ) -> Any:
        """Execute a single operation."""
        # Placeholder for single operation execution
        _ = operation_type  # Mark as intentionally unused
        _ = operation  # Mark as intentionally unused
        return {"status": "completed"}


def _extract_action_type(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    """Extract action type from function arguments."""
    if args and hasattr(args[0], "action_type"):
        return str(args[0].action_type)
    elif "action" in kwargs and hasattr(kwargs["action"], "action_type"):
        return str(kwargs["action"].action_type)
    return "unknown"


def performance_monitor(
    metrics: PerformanceMetrics,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to monitor function performance.

    Args:
        metrics: Performance metrics instance
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                action_type = _extract_action_type(args, kwargs)
                await metrics.record_execution_time(action_type, execution_time)
                return result

            except Exception:
                execution_time = time.time() - start_time
                await metrics.record_execution_time("error", execution_time)
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Record metric asynchronously
                asyncio.create_task(
                    metrics.record_execution_time("sync_operation", execution_time)
                )

                return result

            except Exception:
                execution_time = time.time() - start_time
                asyncio.create_task(
                    metrics.record_execution_time("error", execution_time)
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class ResourceOptimizer:
    """Optimizes resource usage for remediation operations."""

    def __init__(
        self,
        cache_manager: CacheManager,
        batch_manager: BatchOperationManager,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize resource optimizer.

        Args:
            cache_manager: Cache manager instance
            batch_manager: Batch operation manager
            logger: Logger instance
        """
        self.cache_manager = cache_manager
        self.batch_manager = batch_manager
        self.logger = logger or logging.getLogger(__name__)

        # API client pooling
        self._client_pool: Dict[str, List[Any]] = defaultdict(list)
        self._pool_size = 5

    async def get_optimized_client(self, client_type: str) -> Any:
        """Get a client from the pool."""
        if self._client_pool[client_type]:
            return self._client_pool[client_type].pop()

        # Create new client
        # (Implementation would create actual GCP clients)
        return None

    def return_client(self, client_type: str, client: Any) -> None:
        """Return a client to the pool."""
        if len(self._client_pool[client_type]) < self._pool_size:
            self._client_pool[client_type].append(client)

    @lru_cache(maxsize=128)
    def get_cached_permission(self, resource: str, permission: str) -> bool:
        """Get cached permission check result."""
        # This would check actual permissions in production
        _ = resource  # Mark as intentionally unused
        _ = permission  # Mark as intentionally unused
        return True

    async def optimize_action_execution(
        self, action: RemediationAction
    ) -> Dict[str, Any]:
        """
        Optimize action execution using caching and batching.

        Args:
            action: The remediation action

        Returns:
            Optimization suggestions
        """
        suggestions = {
            "use_cache": False,
            "batch_with": [],
            "estimated_speedup": 1.0,
        }

        # Check if result can be cached
        cache_key = f"action_result:{action.action_type}:{action.target_resource}"
        cached_result = await self.cache_manager.get(cache_key)

        if cached_result and self._is_cache_valid(cached_result, action):
            suggestions["use_cache"] = True
            suggestions["estimated_speedup"] = 10.0  # Cached results are much faster

        # Check if action can be batched
        if action.action_type in ["update_firewall_rule", "update_iam_policy"]:
            batch_list = suggestions["batch_with"]
            if isinstance(batch_list, list):
                batch_list.append(action.action_type)
            speedup = suggestions["estimated_speedup"]
            if isinstance(speedup, (int, float)):
                suggestions["estimated_speedup"] = speedup * 2.0

        return suggestions

    def _is_cache_valid(
        self, cached_result: Dict[str, Any], action: RemediationAction
    ) -> bool:
        """Check if cached result is still valid."""
        # Check cache age
        cache_time = cached_result.get("timestamp")
        if not cache_time:
            return False

        cache_age = (
            datetime.now(timezone.utc) - datetime.fromisoformat(cache_time)
        ).total_seconds()

        # Different actions have different cache validity periods
        validity_periods = {
            "list_firewall_rules": 300,  # 5 minutes
            "get_instance_status": 60,  # 1 minute
            "check_permissions": 600,  # 10 minutes
        }

        max_age = validity_periods.get(action.action_type, 120)

        return cache_age < max_age


class CloudMonitoringIntegration:
    """Integrates with Google Cloud Monitoring for performance tracking."""

    def __init__(self, project_id: str, logger: Optional[logging.Logger] = None):
        """
        Initialize Cloud Monitoring integration.

        Args:
            project_id: GCP project ID
            logger: Logger instance
        """
        self.project_id = project_id
        self.logger = logger or logging.getLogger(__name__)

        self.client: Optional[monitoring.MetricServiceClient] = None
        try:
            self.client = monitoring.MetricServiceClient()
            self.project_name = f"projects/{project_id}"
        except (ImportError, ValueError, TypeError) as e:
            self.logger.warning(f"Failed to initialize Cloud Monitoring: {e}")
            self.client = None

    async def report_metrics(self, performance_summary: Dict[str, Any]) -> None:
        """Report performance metrics to Cloud Monitoring."""
        if not self.client:
            return

        try:
            series_list = []

            # Create time series for execution times
            for action_type, metrics in performance_summary.get(
                "execution_times", {}
            ).items():
                series = self._create_time_series(
                    metric_type="remediation_agent/execution_time",
                    value=metrics["average"],
                    labels={
                        "action_type": action_type,
                    },
                )
                series_list.append(series)

            # Create time series for API latencies
            for api_name, metrics in performance_summary.get(
                "api_latencies", {}
            ).items():
                series = self._create_time_series(
                    metric_type="remediation_agent/api_latency",
                    value=metrics["average"],
                    labels={
                        "api_name": api_name,
                    },
                )
                series_list.append(series)

            # Write time series
            if series_list:
                self.client.create_time_series(
                    name=self.project_name, time_series=series_list
                )

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Failed to report metrics: {e}")

    def _create_time_series(
        self, metric_type: str, value: float, labels: Dict[str, str]
    ) -> Any:
        """Create a time series for a metric."""
        try:
            series = monitoring.TimeSeries()
        except (ImportError, AttributeError):
            return None

        series.metric.type = f"custom.googleapis.com/{metric_type}"
        # Labels are dictionary-like protobuf fields
        if hasattr(series.metric, 'labels'):
            metric_labels = series.metric.labels
            for key, val in labels.items():
                metric_labels[key] = val

        series.resource.type = "global"
        if hasattr(series.resource, 'labels'):
            resource_labels = series.resource.labels
            resource_labels["project_id"] = self.project_id

        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10**9)

        interval = monitoring.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )
        point = monitoring.Point(
            {"interval": interval, "value": {"double_value": value}}
        )
        series.points = [point]

        return series

"""
Monitoring and metrics collection for the Detection Agent.

This module provides comprehensive monitoring capabilities including:
- Rule processing metrics
- Query performance tracking
- Event and incident counting
- Resource usage monitoring
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


@dataclass
class RuleMetrics:
    """Metrics for a detection rule."""

    rule_id: str
    rule_type: str
    executions: int = 0
    successes: int = 0
    failures: int = 0
    events_detected: int = 0
    incidents_created: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    last_execution: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None


@dataclass
class QueryMetrics:
    """Metrics for query performance."""

    query_type: str
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    total_bytes_processed: int = 0
    total_rows_returned: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class ResourceMetrics:
    """System resource usage metrics."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""

    operation_type: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""

    error_type: str
    error_message: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Optional[Dict[str, Any]] = None


class DetectionAgentMonitor:
    """Comprehensive monitoring for the Detection Agent."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the monitoring system.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Monitoring configuration
        monitor_config = (
            config.get("agents", {}).get("detection", {}).get("monitoring", {})
        )
        self.enabled = monitor_config.get("enabled", True)
        self.metrics_retention_hours = monitor_config.get("retention_hours", 24)
        self.resource_sample_interval = monitor_config.get(
            "resource_sample_interval", 60
        )

        # Metrics storage
        self.rule_metrics: Dict[str, RuleMetrics] = {}
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.resource_history: deque[ResourceMetrics] = deque(
            maxlen=1440
        )  # 24 hours at 1-minute intervals

        # Counters
        self.total_events_processed = 0
        self.total_incidents_created = 0
        self.total_scan_cycles = 0
        self.agent_start_time = datetime.now()

        # Performance tracking
        self.recent_performance: deque[PerformanceMetrics] = deque(
            maxlen=100
        )  # Last 100 operations

        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recent_errors: deque[ErrorRecord] = deque(maxlen=50)  # Last 50 errors

        # Initialize resource monitoring
        self._last_resource_sample = datetime.now()
        if PSUTIL_AVAILABLE:
            self._initial_disk_io = psutil.disk_io_counters()
            self._initial_network_io = psutil.net_io_counters()
        else:
            self._initial_disk_io = None
            self._initial_network_io = None

    def record_rule_execution(
        self,
        rule_id: str,
        rule_type: str,
        execution_time: float,
        success: bool,
        events_found: int = 0,
        incidents_created: int = 0,
    ) -> None:
        """
        Record metrics for a rule execution.

        Args:
            rule_id: Rule identifier
            rule_type: Type of rule
            execution_time: Time taken to execute rule
            success: Whether execution was successful
            events_found: Number of events detected
            incidents_created: Number of incidents created
        """
        if not self.enabled:
            return

        # Get or create rule metrics
        if rule_id not in self.rule_metrics:
            self.rule_metrics[rule_id] = RuleMetrics(
                rule_id=rule_id, rule_type=rule_type
            )

        metrics = self.rule_metrics[rule_id]

        # Update counters
        metrics.executions += 1
        if success:
            metrics.successes += 1
            metrics.last_success = datetime.now()
        else:
            metrics.failures += 1
            metrics.last_failure = datetime.now()

        metrics.events_detected += events_found
        metrics.incidents_created += incidents_created

        # Update timing
        metrics.total_execution_time += execution_time
        metrics.avg_execution_time = metrics.total_execution_time / metrics.executions
        metrics.last_execution = datetime.now()

        # Update global counters
        self.total_events_processed += events_found
        self.total_incidents_created += incidents_created

        self.logger.debug(
            "Recorded rule execution: %s - %.2fs", rule_id, execution_time
        )

    def record_query_performance(
        self,
        query_type: str,
        execution_time: float,
        success: bool,
        bytes_processed: Optional[int] = None,
        rows_returned: Optional[int] = None,
        cache_hit: bool = False,
    ) -> None:
        """
        Record query performance metrics.

        Args:
            query_type: Type of query (e.g., 'vpc_flow', 'audit', 'firewall')
            execution_time: Query execution time in seconds
            success: Whether query was successful
            bytes_processed: Number of bytes processed by BigQuery
            rows_returned: Number of rows returned
            cache_hit: Whether this was a cache hit
        """
        if not self.enabled:
            return

        # Get or create query metrics
        if query_type not in self.query_metrics:
            self.query_metrics[query_type] = QueryMetrics(query_type=query_type)

        metrics = self.query_metrics[query_type]

        # Update counters
        metrics.total_queries += 1
        if success:
            metrics.successful_queries += 1
        else:
            metrics.failed_queries += 1

        # Update timing
        metrics.total_execution_time += execution_time
        metrics.avg_execution_time = (
            metrics.total_execution_time / metrics.total_queries
        )

        # Update data metrics
        if bytes_processed:
            metrics.total_bytes_processed += bytes_processed
        if rows_returned:
            metrics.total_rows_returned += rows_returned

        # Update cache metrics
        if cache_hit:
            metrics.cache_hits += 1
        else:
            metrics.cache_misses += 1

        # Track recent performance
        performance_metrics = PerformanceMetrics(
            operation_type=query_type,
            execution_time=execution_time,
            details={"success": success},
        )
        self.recent_performance.append(performance_metrics)

        self.logger.debug(
            "Recorded query performance: %s - %.2fs", query_type, execution_time
        )

    def record_scan_cycle(self) -> None:
        """Record completion of a scan cycle."""
        if not self.enabled:
            return

        self.total_scan_cycles += 1
        self.logger.debug("Recorded scan cycle: %s", self.total_scan_cycles)

    def record_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record an error occurrence.

        Args:
            error_type: Type/category of error
            error_message: Error message
            context: Optional additional context
        """
        if not self.enabled:
            return

        self.error_counts[error_type] += 1

        error_record = ErrorRecord(
            error_type=error_type, error_message=error_message, context=context
        )

        self.recent_errors.append(error_record)
        self.logger.debug("Recorded error: %s", error_type)

    def sample_resource_usage(self) -> Optional[ResourceMetrics]:
        """
        Sample current resource usage.

        Returns:
            ResourceMetrics with current usage or None if monitoring is disabled or fails
        """
        if not self.enabled:
            return None

        if not PSUTIL_AVAILABLE:
            # Return minimal metrics when psutil is not available
            return ResourceMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_io_sent_mb=0.0,
                network_io_recv_mb=0.0,
                timestamp=datetime.now(),
            )

        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = (disk_io.read_bytes - self._initial_disk_io.read_bytes) / (
                1024 * 1024
            )
            disk_write_mb = (
                disk_io.write_bytes - self._initial_disk_io.write_bytes
            ) / (1024 * 1024)

            # Network I/O
            net_io = psutil.net_io_counters()
            net_sent_mb = (net_io.bytes_sent - self._initial_network_io.bytes_sent) / (
                1024 * 1024
            )
            net_recv_mb = (net_io.bytes_recv - self._initial_network_io.bytes_recv) / (
                1024 * 1024
            )

            metrics = ResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_io_sent_mb=net_sent_mb,
                network_io_recv_mb=net_recv_mb,
            )

            # Store in history
            self.resource_history.append(metrics)
            self._last_resource_sample = datetime.now()

            return metrics

        except (OSError, RuntimeError, ValueError) as e:
            self.logger.error("Error sampling resource usage: %s", e)
            return None

    def get_rule_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive rule processing statistics.

        Returns:
            Dictionary with rule statistics
        """
        if not self.enabled:
            return {}

        rule_stats = {}
        total_executions = sum(m.executions for m in self.rule_metrics.values())
        total_success_rate: float = 0.0

        if total_executions > 0:
            total_successes = sum(m.successes for m in self.rule_metrics.values())
            total_success_rate = (total_successes / total_executions) * 100

        for rule_id, metrics in self.rule_metrics.items():
            success_rate: float = 0.0
            if metrics.executions > 0:
                success_rate = (metrics.successes / metrics.executions) * 100

            rule_stats[rule_id] = {
                "type": metrics.rule_type,
                "executions": metrics.executions,
                "success_rate": f"{success_rate:.1f}%",
                "events_detected": metrics.events_detected,
                "incidents_created": metrics.incidents_created,
                "avg_execution_time": f"{metrics.avg_execution_time:.2f}s",
                "last_execution": (
                    metrics.last_execution.isoformat()
                    if metrics.last_execution
                    else None
                ),
            }

        return {
            "total_rules": len(self.rule_metrics),
            "total_executions": total_executions,
            "overall_success_rate": f"{total_success_rate:.1f}%",
            "rules": rule_stats,
        }

    def get_query_statistics(self) -> Dict[str, Any]:
        """
        Get query performance statistics.

        Returns:
            Dictionary with query statistics
        """
        if not self.enabled:
            return {}

        query_stats = {}
        total_queries = sum(m.total_queries for m in self.query_metrics.values())
        total_bytes = sum(m.total_bytes_processed for m in self.query_metrics.values())

        for query_type, metrics in self.query_metrics.items():
            success_rate: float = 0.0
            cache_hit_rate: float = 0.0

            if metrics.total_queries > 0:
                success_rate = (
                    metrics.successful_queries / metrics.total_queries
                ) * 100
                total_cache_requests = metrics.cache_hits + metrics.cache_misses
                if total_cache_requests > 0:
                    cache_hit_rate = (metrics.cache_hits / total_cache_requests) * 100

            query_stats[query_type] = {
                "total_queries": metrics.total_queries,
                "success_rate": f"{success_rate:.1f}%",
                "avg_execution_time": f"{metrics.avg_execution_time:.2f}s",
                "total_bytes_processed": f"{metrics.total_bytes_processed / (1024**3):.2f} GB",
                "total_rows_returned": metrics.total_rows_returned,
                "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            }

        return {
            "total_query_types": len(self.query_metrics),
            "total_queries": total_queries,
            "total_bytes_processed": f"{total_bytes / (1024**3):.2f} GB",
            "by_type": query_stats,
        }

    def get_resource_statistics(self) -> Dict[str, Any]:
        """
        Get resource usage statistics.

        Returns:
            Dictionary with resource statistics
        """
        if not self.enabled or not self.resource_history:
            return {}

        # Calculate averages and peaks
        cpu_values = [r.cpu_percent for r in self.resource_history]
        memory_values = [r.memory_percent for r in self.resource_history]
        memory_used_values = [r.memory_used_mb for r in self.resource_history]

        return {
            "sample_count": len(self.resource_history),
            "sample_period_hours": (
                (datetime.now() - self.resource_history[0].timestamp).total_seconds()
                / 3600
            ),
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values),
                "peak": max(cpu_values),
            },
            "memory": {
                "current_percent": memory_values[-1] if memory_values else 0,
                "average_percent": sum(memory_values) / len(memory_values),
                "peak_percent": max(memory_values),
                "current_used_mb": memory_used_values[-1] if memory_used_values else 0,
                "average_used_mb": sum(memory_used_values) / len(memory_used_values),
                "peak_used_mb": max(memory_used_values),
            },
        }

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive monitoring report.

        Returns:
            Complete monitoring report
        """
        if not self.enabled:
            return {"monitoring_enabled": False}

        uptime = datetime.now() - self.agent_start_time

        return {
            "monitoring_enabled": True,
            "agent_uptime": str(uptime),
            "total_events_processed": self.total_events_processed,
            "total_incidents_created": self.total_incidents_created,
            "total_scan_cycles": self.total_scan_cycles,
            "error_summary": dict(self.error_counts),
            "recent_errors_count": len(self.recent_errors),
            "rule_statistics": self.get_rule_statistics(),
            "query_statistics": self.get_query_statistics(),
            "resource_statistics": self.get_resource_statistics(),
            "last_resource_sample": self._last_resource_sample.isoformat(),
        }

    def cleanup_old_metrics(self) -> None:
        """Clean up old metrics data beyond retention period."""
        if not self.enabled:
            return

        cutoff_time = datetime.now() - timedelta(hours=self.metrics_retention_hours)

        # Clean resource history
        while (
            self.resource_history and self.resource_history[0].timestamp < cutoff_time
        ):
            self.resource_history.popleft()

        # Clean recent performance data
        while (
            self.recent_performance
            and self.recent_performance[0].timestamp < cutoff_time
        ):
            self.recent_performance.popleft()

        # Clean recent errors
        while self.recent_errors and self.recent_errors[0].timestamp < cutoff_time:
            self.recent_errors.popleft()

        self.logger.debug("Cleaned up old metrics data")

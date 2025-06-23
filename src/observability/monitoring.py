"""
SentinelOps Observability and Monitoring Module

This module provides detailed monitoring, metrics collection, telemetry,
and observability features for the security platform.
"""

# Standard library imports
import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# Third-party imports
from google.cloud import logging as cloud_logging
from google.cloud import monitoring_v3
from prometheus_client import Counter, Gauge, Histogram, Summary

# Local imports
from .audit_logging import AuditLogger as BaseAuditLogger


# Configure structured logging
cloud_client = cloud_logging.Client()  # type: ignore[no-untyped-call]
# Set up cloud logging handler
cloud_logger = logging.getLogger("sentinelops.observability")
cloud_logger.setLevel(logging.INFO)


class MetricType(Enum):
    """Types of metrics collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class HealthStatus(Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class MetricDefinition:
    """Definition of a metric to be collected."""

    name: str
    type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    objectives: Optional[Dict[float, float]] = None  # For summaries


@dataclass
class HealthCheck:
    """Health check configuration."""

    name: str
    check_function: Callable[[], Any]
    interval_seconds: int = 30
    timeout_seconds: int = 10
    failure_threshold: int = 3
    success_threshold: int = 1
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SLODefinition:
    """Service Level Objective definition."""

    name: str
    description: str
    target_percentage: float
    measurement_window: timedelta
    metric_query: str
    tags: Dict[str, str] = field(default_factory=dict)


class ObservabilityManager:
    """Main observability and monitoring manager."""

    def __init__(self, project_id: str, service_name: str = "sentinelops"):
        self.project_id = project_id
        self.service_name = service_name
        self.metrics_client = monitoring_v3.MetricServiceClient()
        # Note: Dashboard functionality removed due to module availability

        # Metric registries
        self._metrics: Dict[str, Any] = {}
        self._metric_definitions: Dict[str, MetricDefinition] = {}

        # Health checks
        self._health_checks: Dict[str, HealthCheck] = {}
        self._health_status: Dict[str, Dict[str, Any]] = {}
        self._health_check_tasks: Dict[str, asyncio.Task[Any]] = {}

        # SLOs
        self._slos: Dict[str, SLODefinition] = {}
        self._slo_measurements: Dict[str, deque[Any]] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        # Audit logging
        self._audit_logger = BaseAuditLogger(project_id, service_name)

        # Performance tracking
        self._performance_tracker = PerformanceTracker()

        # Initialize standard metrics
        self._initialize_standard_metrics()

    def _initialize_standard_metrics(self) -> None:
        """Initialize standard platform metrics."""
        # Security event metrics
        self.register_metric(
            MetricDefinition(
                name="security_events_total",
                type=MetricType.COUNTER,
                description="Total number of security events processed",
                labels=["event_type", "severity", "source"],
            )
        )

        self.register_metric(
            MetricDefinition(
                name="security_events_processing_time",
                type=MetricType.HISTOGRAM,
                description="Time to process security events",
                labels=["event_type"],
                buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            )
        )

        # Detection metrics
        self.register_metric(
            MetricDefinition(
                name="threats_detected_total",
                type=MetricType.COUNTER,
                description="Total number of threats detected",
                labels=["threat_type", "confidence_level"],
            )
        )

        self.register_metric(
            MetricDefinition(
                name="false_positives_total",
                type=MetricType.COUNTER,
                description="Total number of false positive detections",
                labels=["threat_type"],
            )
        )

        # Analysis metrics
        self.register_metric(
            MetricDefinition(
                name="incident_analysis_duration",
                type=MetricType.HISTOGRAM,
                description="Time taken for incident analysis",
                labels=["incident_severity"],
                buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
            )
        )

        # Remediation metrics
        self.register_metric(
            MetricDefinition(
                name="remediation_actions_total",
                type=MetricType.COUNTER,
                description="Total remediation actions executed",
                labels=["action_type", "success"],
            )
        )

        self.register_metric(
            MetricDefinition(
                name="remediation_execution_time",
                type=MetricType.HISTOGRAM,
                description="Time to execute remediation actions",
                labels=["action_type"],
                buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
            )
        )

        # System metrics
        self.register_metric(
            MetricDefinition(
                name="active_incidents",
                type=MetricType.GAUGE,
                description="Number of currently active incidents",
                labels=["severity"],
            )
        )

        self.register_metric(
            MetricDefinition(
                name="api_requests_total",
                type=MetricType.COUNTER,
                description="Total API requests",
                labels=["endpoint", "method", "status_code"],
            )
        )

        self.register_metric(
            MetricDefinition(
                name="api_request_duration",
                type=MetricType.HISTOGRAM,
                description="API request duration",
                labels=["endpoint", "method"],
                buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            )
        )

    def register_metric(self, definition: MetricDefinition) -> None:
        """Register a new metric for collection."""
        if definition.name in self._metric_definitions:
            raise ValueError(f"Metric {definition.name} already registered")

        self._metric_definitions[definition.name] = definition

        # Create Prometheus metric based on type
        prometheus_metric: Union[Counter, Gauge, Histogram, Summary]
        if definition.type == MetricType.COUNTER:
            prometheus_metric = Counter(
                definition.name, definition.description, definition.labels
            )
        elif definition.type == MetricType.GAUGE:
            prometheus_metric = Gauge(
                definition.name, definition.description, definition.labels
            )
        elif definition.type == MetricType.HISTOGRAM:
            buckets = definition.buckets if definition.buckets is not None else []
            prometheus_metric = Histogram(
                definition.name,
                definition.description,
                definition.labels,
                buckets=buckets,
            )
        elif definition.type == MetricType.SUMMARY:
            prometheus_metric = Summary(
                definition.name, definition.description, definition.labels
            )
        else:
            raise ValueError(f"Unsupported metric type: {definition.type}")

        self._metrics[definition.name] = prometheus_metric

        # Also register with Google Cloud Monitoring
        # Use type ignore for GCP monitoring client type issues
        cloud_metric_descriptor = monitoring_v3.types.MetricDescriptor(  # type: ignore[attr-defined]
            type=f"custom.googleapis.com/{self.service_name}/{definition.name}",
            metric_kind=monitoring_v3.types.MetricDescriptor.MetricKind.GAUGE,  # type: ignore[attr-defined]
            value_type=monitoring_v3.types.MetricDescriptor.ValueType.DOUBLE,  # type: ignore[attr-defined]
            description=definition.description,
        )

        try:
            self.metrics_client.create_metric_descriptor(
                name=f"projects/{self.project_id}",
                metric_descriptor=cloud_metric_descriptor,
            )
        except Exception as e:
            cloud_logger.warning(f"Failed to create cloud metric descriptor: {e}")

    def record_metric(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value."""
        if name not in self._metrics:
            raise ValueError(f"Metric {name} not registered")

        metric = self._metrics[name]
        definition = self._metric_definitions[name]

        # Apply labels
        if labels:
            metric = metric.labels(**labels)

        # Record value based on type
        if definition.type == MetricType.COUNTER:
            metric.inc(value)
        elif definition.type == MetricType.GAUGE:
            metric.set(value)
        elif definition.type in [MetricType.HISTOGRAM, MetricType.SUMMARY]:
            metric.observe(value)

    def register_health_check(self, health_check: HealthCheck) -> None:
        """Register a health check."""
        self._health_checks[health_check.name] = health_check
        self._health_status[health_check.name] = {
            "status": HealthStatus.UNKNOWN,
            "last_check": None,
            "consecutive_failures": 0,
            "consecutive_successes": 0,
            "message": "Not yet checked",
        }

    async def start_health_checks(self) -> None:
        """Start all registered health checks."""
        for name, check in self._health_checks.items():
            if name not in self._health_check_tasks:
                task = asyncio.create_task(self._run_health_check(name))
                self._health_check_tasks[name] = task

    async def stop_health_checks(self) -> None:
        """Stop all health checks."""
        for task in self._health_check_tasks.values():
            task.cancel()

        await asyncio.gather(*self._health_check_tasks.values(), return_exceptions=True)
        self._health_check_tasks.clear()

    async def _run_health_check(self, name: str) -> None:
        """Run a health check continuously."""
        check = self._health_checks[name]

        while True:
            try:
                # Run check with timeout
                start_time = time.time()
                result = await asyncio.wait_for(
                    check.check_function(), timeout=check.timeout_seconds
                )
                duration = time.time() - start_time

                # Update status
                status_info = self._health_status[name]

                if result:
                    status_info["consecutive_successes"] += 1
                    status_info["consecutive_failures"] = 0

                    if status_info["consecutive_successes"] >= check.success_threshold:
                        status_info["status"] = HealthStatus.HEALTHY
                        status_info["message"] = "Health check passing"
                else:
                    status_info["consecutive_failures"] += 1
                    status_info["consecutive_successes"] = 0

                    if status_info["consecutive_failures"] >= check.failure_threshold:
                        status_info["status"] = HealthStatus.UNHEALTHY
                        status_info["message"] = "Health check failing"

                status_info["last_check"] = datetime.now(timezone.utc)
                status_info["duration_ms"] = duration * 1000

                # Record metric
                self.record_metric(
                    "health_check_duration",
                    duration,
                    {"check_name": name, "status": status_info["status"].value},
                )

            except asyncio.TimeoutError:
                status_info = self._health_status[name]
                status_info["consecutive_failures"] += 1
                status_info["consecutive_successes"] = 0
                status_info["status"] = HealthStatus.UNHEALTHY
                status_info["message"] = "Health check timeout"

            except Exception as e:
                cloud_logger.error(f"Health check {name} error: {e}")
                status_info = self._health_status[name]
                status_info["status"] = HealthStatus.UNHEALTHY
                status_info["message"] = str(e)

            # Wait for next check
            await asyncio.sleep(check.interval_seconds)

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all checks."""
        overall_status = HealthStatus.HEALTHY
        degraded_checks = []
        unhealthy_checks = []

        for name, status in self._health_status.items():
            if status["status"] == HealthStatus.UNHEALTHY:
                unhealthy_checks.append(name)
                overall_status = HealthStatus.UNHEALTHY
            elif status["status"] == HealthStatus.DEGRADED:
                degraded_checks.append(name)
                if overall_status != HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.DEGRADED

        return {
            "status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": self._health_status,
            "summary": {
                "total": len(self._health_checks),
                "healthy": len(
                    [
                        s
                        for s in self._health_status.values()
                        if s["status"] == HealthStatus.HEALTHY
                    ]
                ),
                "degraded": len(degraded_checks),
                "unhealthy": len(unhealthy_checks),
            },
        }

    def register_slo(self, slo: SLODefinition) -> None:
        """Register a Service Level Objective."""
        self._slos[slo.name] = slo

    def record_slo_event(self, slo_name: str, success: bool) -> None:
        """Record an event for SLO calculation."""
        if slo_name not in self._slos:
            raise ValueError(f"SLO {slo_name} not registered")

        self._slo_measurements[slo_name].append(
            {"timestamp": datetime.now(timezone.utc), "success": success}
        )

    def calculate_slo_status(self, slo_name: str) -> Dict[str, Any]:
        """Calculate current SLO status."""
        if slo_name not in self._slos:
            raise ValueError(f"SLO {slo_name} not registered")

        slo = self._slos[slo_name]
        measurements = self._slo_measurements[slo_name]

        if not measurements:
            return {
                "slo_name": slo_name,
                "target": slo.target_percentage,
                "current": 100.0,
                "status": "no_data",
                "error_budget_remaining": 100.0,
            }

        # Filter measurements within window
        cutoff_time = datetime.now(timezone.utc) - slo.measurement_window
        recent_measurements = [m for m in measurements if m["timestamp"] > cutoff_time]

        if not recent_measurements:
            return {
                "slo_name": slo_name,
                "target": slo.target_percentage,
                "current": 100.0,
                "status": "no_recent_data",
                "error_budget_remaining": 100.0,
            }

        # Calculate success rate
        successful = sum(1 for m in recent_measurements if m["success"])
        total = len(recent_measurements)
        current_percentage = (successful / total) * 100

        # Calculate error budget
        allowed_failures = total * (100 - slo.target_percentage) / 100
        actual_failures = total - successful
        error_budget_remaining = max(
            0, (allowed_failures - actual_failures) / allowed_failures * 100
        )

        status = (
            "healthy" if current_percentage >= slo.target_percentage else "breached"
        )

        return {
            "slo_name": slo_name,
            "target": slo.target_percentage,
            "current": current_percentage,
            "status": status,
            "error_budget_remaining": error_budget_remaining,
            "measurement_window": str(slo.measurement_window),
            "total_events": total,
            "successful_events": successful,
        }

    async def create_dashboard(self) -> str:
        """Create a monitoring dashboard."""
        # Dashboard client not available - return placeholder
        # Dashboard configuration removed since dashboard_client is not available
        project_path = f"projects/{self.project_id}"
        # Would create dashboard here if dashboard_client was available
        dashboard_name = f"{project_path}/dashboards/{self.service_name}-overview"

        return dashboard_name


class AuditLogger:
    """Specialized audit logger for security compliance."""

    def __init__(self, project_id: str, service_name: str):
        self.project_id = project_id
        self.service_name = service_name
        self.logger = cloud_logger

        # Audit event buffer for batch writing
        self._audit_buffer: List[Dict[str, Any]] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task[Any]] = None

    async def log_audit_event(
        self,
        event_type: str,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        details: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Log an audit event."""
        audit_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "service": self.service_name,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result,
            "source_ip": source_ip or "unknown",
            "session_id": session_id or "unknown",
            "details": details or {},
        }

        # Add to buffer
        async with self._buffer_lock:
            self._audit_buffer.append(audit_event)

            # Start flush task if not running
            if self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._flush_audit_events())

    async def _flush_audit_events(self) -> None:
        """Flush audit events to Cloud Logging."""
        await asyncio.sleep(1)  # Batch for 1 second

        async with self._buffer_lock:
            if not self._audit_buffer:
                return

            events_to_flush = self._audit_buffer.copy()
            self._audit_buffer.clear()

        # Write to Cloud Logging
        for event in events_to_flush:
            self.logger.info(
                "AUDIT_EVENT",
                extra={
                    "json_fields": event,
                    "labels": {
                        "event_type": event["event_type"],
                        "user_id": event["user_id"],
                        "result": event["result"],
                    },
                },
            )

    async def query_audit_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Query audit logs."""
        # Build filter
        filter_parts = [
            'resource.type="cloud_function"',
            f'jsonPayload.service="{self.service_name}"',
            f'timestamp>="{start_time.isoformat()}"',
            f'timestamp<="{end_time.isoformat()}"',
        ]

        if filters:
            for key, value in filters.items():
                filter_parts.append(f'jsonPayload.{key}="{value}"')

        filter_str = " AND ".join(filter_parts)

        # Query logs
        client = cloud_logging.Client(project=self.project_id)  # type: ignore[no-untyped-call]
        entries = client.list_entries(filter_=filter_str)  # type: ignore[no-untyped-call]

        results = []
        for entry in entries:
            if hasattr(entry, "json_fields"):
                results.append(entry.json_fields)

        return results


class PerformanceTracker:
    """Track performance metrics and identify bottlenecks."""

    def __init__(self) -> None:
        self._operation_times: Dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self._slow_operations: List[Dict[str, Any]] = []

    def track_operation(self, operation_name: str) -> "OperationTimer":
        """Context manager to track operation performance."""
        return OperationTimer(self, operation_name)

    def record_operation_time(
        self,
        operation_name: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record operation execution time."""
        # Just store the duration, not the full dict
        self._operation_times[operation_name].append(duration)

        # Store detailed info separately if it's a slow operation
        if duration > 1.0:  # Consider operations over 1 second as slow
            self._slow_operations.append(
                {
                    "operation": operation_name,
                    "timestamp": datetime.now(timezone.utc),
                    "duration": duration,
                    "metadata": metadata or {},
                }
            )

    def get_performance_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get performance statistics for an operation."""
        times: Any = self._operation_times.get(operation_name, [])

        if not times:
            return {
                "operation": operation_name,
                "count": 0,
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
            }

        durations = sorted([t["duration"] for t in times])
        count = len(durations)

        return {
            "operation": operation_name,
            "count": count,
            "avg_duration": sum(durations) / count,
            "min_duration": durations[0],
            "max_duration": durations[-1],
            "p50": durations[int(count * 0.5)],
            "p95": durations[int(count * 0.95)],
            "p99": durations[int(count * 0.99)],
        }

    def get_slow_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent slow operations."""
        return self._slow_operations[-limit:]


class OperationTimer:
    """Context manager for timing operations."""

    def __init__(self, tracker: PerformanceTracker, operation_name: str) -> None:
        self.tracker = tracker
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        self.metadata: Dict[str, Any] = {}

    def __enter__(self) -> "OperationTimer":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        assert self.start_time is not None
        duration = time.time() - self.start_time
        self.tracker.record_operation_time(self.operation_name, duration, self.metadata)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the operation timing."""
        self.metadata[key] = value

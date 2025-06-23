"""
Telemetry collection and metrics aggregation for SentinelOps.

This module provides comprehensive telemetry collection, including
distributed tracing, metrics aggregation, and performance monitoring.
"""

# Standard library imports
import asyncio
import json
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

# Third-party imports
from google.cloud import monitoring_v3
from google.cloud import trace_v2
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


class TelemetryType(Enum):
    """Types of telemetry data collected."""

    METRIC = "metric"
    TRACE = "trace"
    LOG = "log"
    EVENT = "event"
    PROFILE = "profile"


@dataclass
class TelemetryEvent:
    """Represents a telemetry event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    type: TelemetryType = TelemetryType.EVENT
    name: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


@dataclass
class MetricPoint:
    """Represents a single metric data point."""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    exemplar_trace_id: Optional[str] = None


@dataclass
class TraceSpan:
    """Represents a trace span."""

    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[TelemetryEvent] = field(default_factory=list)
    status: str = "ok"
    error: Optional[str] = None


class TelemetryCollector:
    """Main telemetry collection and aggregation system."""

    def __init__(self, project_id: str, service_name: str = "sentinelops"):
        self.project_id = project_id
        self.service_name = service_name

        # Initialize OpenTelemetry
        self._init_opentelemetry()

        # Metrics client
        self.metrics_client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"

        # Trace client
        self.trace_client = trace_v2.TraceServiceClient()

        # Telemetry buffers
        self._metric_buffer: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._trace_buffer: List[TraceSpan] = []
        self._event_buffer: List[TelemetryEvent] = []

        # Aggregation windows
        self._aggregation_windows = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "1d": timedelta(days=1),
        }

        # Performance baselines
        self._performance_baselines: Dict[str, Dict[str, float]] = {}

        # Anomaly detection
        self._anomaly_detectors: Dict[str, AnomalyDetector] = {}

        # Background tasks
        self._flush_task: Optional[asyncio.Task[None]] = None
        self._aggregation_task: Optional[asyncio.Task[None]] = None

        # Start background processing
        asyncio.create_task(self._start_background_tasks())

    def _init_opentelemetry(self) -> None:
        """Initialize OpenTelemetry instrumentation."""
        # Create resource
        resource = Resource.create(
            {
                "service.name": self.service_name,
                "service.version": "1.0.0",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_app_engine",
            }
        )

        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Add Cloud Trace exporter
        cloud_trace_exporter = CloudTraceSpanExporter(  # type: ignore[no-untyped-call]
            project_id=self.project_id
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        # Instrument libraries
        RequestsInstrumentor().instrument()
        grpc_instrumentor: Any = GrpcInstrumentorClient()  # type: ignore[no-untyped-call]
        grpc_instrumentor.instrument()

        # Set up propagator
        self.propagator = TraceContextTextMapPropagator()

    async def _start_background_tasks(self) -> None:
        """Start background telemetry processing tasks."""
        self._flush_task = asyncio.create_task(self._flush_telemetry_loop())
        self._aggregation_task = asyncio.create_task(self._aggregation_loop())

    async def _flush_telemetry_loop(self) -> None:
        """Periodically flush telemetry data."""
        while True:
            try:
                await asyncio.sleep(10)  # Flush every 10 seconds
                await self.flush_telemetry()
            except Exception as e:
                print(f"Error flushing telemetry: {e}")

    async def _aggregation_loop(self) -> None:
        """Periodically aggregate metrics."""
        while True:
            try:
                await asyncio.sleep(60)  # Aggregate every minute
                await self._aggregate_metrics()
            except Exception as e:
                print(f"Error aggregating metrics: {e}")

    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a metric value."""
        point = MetricPoint(
            timestamp=timestamp or datetime.now(timezone.utc),
            value=value,
            labels=labels or {},
        )

        # Add current trace context if available
        span = trace.get_current_span()
        if span and span.is_recording():
            span_context = span.get_span_context()
            point.exemplar_trace_id = format(span_context.trace_id, "032x")

        self._metric_buffer[name].append(point)

        # Check for anomalies
        if name in self._anomaly_detectors:
            if self._anomaly_detectors[name].is_anomaly(value):
                self.record_event(
                    "metric_anomaly",
                    {
                        "metric_name": name,
                        "value": value,
                        "expected_range": self._anomaly_detectors[
                            name
                        ].get_expected_range(),
                    },
                    severity="warning",
                )

    def record_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ) -> None:
        """Record a telemetry event."""
        event = TelemetryEvent(
            type=TelemetryType.EVENT,
            name=name,
            attributes=attributes or {},
            severity=severity,
        )

        # Add trace context
        span = trace.get_current_span()
        if span and span.is_recording():
            span_context = span.get_span_context()
            event.trace_id = format(span_context.trace_id, "032x")
            event.span_id = format(span_context.span_id, "016x")

            # Also add as span event
            span.add_event(name, attributes=attributes or {})

        self._event_buffer.append(event)

    @asynccontextmanager
    async def trace_operation(
        self, operation_name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[trace.Span, None]:
        """Context manager for tracing an operation."""
        with self.tracer.start_as_current_span(
            operation_name, attributes=attributes or {}
        ) as span:
            start_time = time.time()
            try:
                yield span
                span.set_status(trace.Status(trace.StatusCode.OK))
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
            finally:
                # Record operation duration
                duration = time.time() - start_time
                self.record_metric(
                    "operation_duration", duration, {"operation": operation_name}
                )

    async def flush_telemetry(self) -> None:
        """Flush all telemetry data to backends."""
        await asyncio.gather(
            self._flush_metrics(), self._flush_events(), return_exceptions=True
        )

    async def _flush_metrics(self) -> None:
        """Flush metrics to Cloud Monitoring."""
        if not self._metric_buffer:
            return

        # Create time series
        time_series_list = []

        for metric_name, points in self._metric_buffer.items():
            if not points:
                continue

            # Group by labels
            points_by_labels = defaultdict(list)
            for point in points:
                label_key = json.dumps(point.labels, sort_keys=True)
                points_by_labels[label_key].append(point)

            # Create time series for each label combination
            for label_key, label_points in points_by_labels.items():
                labels = json.loads(label_key)

                # Create time series
                series = monitoring_v3.TimeSeries()
                series.metric.type = (
                    f"custom.googleapis.com/{self.service_name}/{metric_name}"
                )

                # Add metric labels
                for key, value in labels.items():
                    series.metric.labels[key] = str(value)

                series.resource.type = "global"
                series.resource.labels["project_id"] = self.project_id

                # Create points
                points_list = []
                for point in label_points:
                    interval = monitoring_v3.TimeInterval(
                        end_time={"seconds": int(point.timestamp.timestamp())}
                    )
                    points_list.append(
                        monitoring_v3.Point(
                            interval=interval, value={"double_value": point.value}
                        )
                    )

                # Add points to series
                series.points = points_list

                time_series_list.append(series)

        # Write time series
        if time_series_list:
            self.metrics_client.create_time_series(
                name=self.project_name, time_series=time_series_list
            )

        # Clear buffer
        self._metric_buffer.clear()

    async def _flush_events(self) -> None:
        """Flush events to logging."""
        # Events are typically sent to structured logging
        # For now, we'll just clear the buffer
        # In production, these would go to Cloud Logging
        self._event_buffer.clear()

    async def _aggregate_metrics(self) -> None:
        """Aggregate metrics for different time windows."""
        current_time = datetime.now(timezone.utc)

        for window_name, window_duration in self._aggregation_windows.items():
            window_start = current_time - window_duration

            # Query metrics for the window
            interval = monitoring_v3.TimeInterval(
                {
                    "end_time": {"seconds": int(current_time.timestamp())},
                    "start_time": {"seconds": int(window_start.timestamp())},
                }
            )

            # Aggregate different metric types
            await self._aggregate_security_metrics(interval, window_name)
            await self._aggregate_performance_metrics(interval, window_name)
            await self._aggregate_error_metrics(interval, window_name)

    async def _aggregate_security_metrics(
        self, interval: monitoring_v3.TimeInterval, window_name: str
    ) -> None:
        """Aggregate security-specific metrics."""
        # Threat detection rate
        threat_filter = f'metric.type="custom.googleapis.com/{self.service_name}/threats_detected_total"'

        try:
            results = self.metrics_client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": threat_filter,
                    "interval": interval,
                    "aggregation": monitoring_v3.Aggregation(
                        alignment_period={"seconds": 60},
                        per_series_aligner="ALIGN_RATE",
                    ),
                }
            )

            total_rate = 0.0
            for result in results:
                for point in result.points:
                    total_rate += point.value.double_value

            # Record aggregated metric
            self.record_metric(
                f"threat_detection_rate_{window_name}",
                total_rate,
                {"window": window_name},
            )

        except Exception as e:
            print(f"Error aggregating security metrics: {e}")

    async def _aggregate_performance_metrics(
        self, interval: monitoring_v3.TimeInterval, window_name: str
    ) -> None:
        """Aggregate performance metrics."""
        # API latency percentiles
        latency_filter = f'metric.type="custom.googleapis.com/{self.service_name}/api_request_duration"'

        try:
            # P50
            results_p50 = self.metrics_client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": latency_filter,
                    "interval": interval,
                    "aggregation": monitoring_v3.Aggregation(
                        alignment_period={"seconds": 300},
                        per_series_aligner="ALIGN_PERCENTILE_50",
                    ),
                }
            )

            # P95
            results_p95 = self.metrics_client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": latency_filter,
                    "interval": interval,
                    "aggregation": monitoring_v3.Aggregation(
                        alignment_period={"seconds": 300},
                        per_series_aligner="ALIGN_PERCENTILE_95",
                    ),
                }
            )

            # P99
            results_p99 = self.metrics_client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": latency_filter,
                    "interval": interval,
                    "aggregation": monitoring_v3.Aggregation(
                        alignment_period={"seconds": 300},
                        per_series_aligner="ALIGN_PERCENTILE_99",
                    ),
                }
            )

            # Process results
            for percentile, results in [
                ("p50", results_p50),
                ("p95", results_p95),
                ("p99", results_p99),
            ]:
                for result in results:
                    if result.points:
                        latest_value = result.points[0].value.double_value
                        self.record_metric(
                            f"api_latency_{percentile}_{window_name}",
                            latest_value,
                            {"window": window_name, "percentile": percentile},
                        )

        except Exception as e:
            print(f"Error aggregating performance metrics: {e}")

    async def _aggregate_error_metrics(
        self, interval: monitoring_v3.TimeInterval, window_name: str
    ) -> None:
        """Aggregate error metrics."""
        # Error rate calculation
        error_filter = f'metric.type="custom.googleapis.com/{self.service_name}/api_requests_total" AND metric.label.status_code=~"5.."'
        total_filter = f'metric.type="custom.googleapis.com/{self.service_name}/api_requests_total"'

        try:
            # Get error count
            error_results = self.metrics_client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": error_filter,
                    "interval": interval,
                    "aggregation": monitoring_v3.Aggregation(
                        alignment_period={"seconds": 300},
                        per_series_aligner="ALIGN_SUM",
                    ),
                }
            )

            # Get total count
            total_results = self.metrics_client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": total_filter,
                    "interval": interval,
                    "aggregation": monitoring_v3.Aggregation(
                        alignment_period={"seconds": 300},
                        per_series_aligner="ALIGN_SUM",
                    ),
                }
            )

            error_count = 0
            total_count = 0

            for result in error_results:
                for point in result.points:
                    error_count += point.value.int64_value

            for result in total_results:
                for point in result.points:
                    total_count += point.value.int64_value

            # Calculate error rate
            error_rate = (error_count / total_count * 100) if total_count > 0 else 0

            self.record_metric(
                f"error_rate_{window_name}", error_rate, {"window": window_name}
            )

        except Exception as e:
            print(f"Error aggregating error metrics: {e}")

    def set_performance_baseline(
        self, metric_name: str, baseline_values: Dict[str, float]
    ) -> None:
        """Set performance baseline for regression detection."""
        self._performance_baselines[metric_name] = baseline_values

    def check_performance_regression(
        self, metric_name: str, current_value: float, threshold_percent: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """Check if current performance regresses from baseline."""
        if metric_name not in self._performance_baselines:
            return None

        baseline = self._performance_baselines[metric_name]

        # Check against different percentiles
        for percentile, baseline_value in baseline.items():
            if current_value > baseline_value * (1 + threshold_percent / 100):
                return {
                    "metric": metric_name,
                    "percentile": percentile,
                    "baseline": baseline_value,
                    "current": current_value,
                    "regression_percent": (
                        (current_value - baseline_value) / baseline_value
                    )
                    * 100,
                }

        return None

    def register_anomaly_detector(
        self, metric_name: str, detector: "AnomalyDetector"
    ) -> None:
        """Register an anomaly detector for a metric."""
        self._anomaly_detectors[metric_name] = detector

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get summary of telemetry collection."""
        return {
            "metrics_buffered": sum(
                len(points) for points in self._metric_buffer.values()
            ),
            "events_buffered": len(self._event_buffer),
            "active_anomaly_detectors": len(self._anomaly_detectors),
            "performance_baselines": list(self._performance_baselines.keys()),
            "aggregation_windows": list(self._aggregation_windows.keys()),
        }


class AnomalyDetector:
    """Simple anomaly detection for metrics."""

    def __init__(self, window_size: int = 100, std_threshold: float = 3.0):
        self.window_size = window_size
        self.std_threshold = std_threshold
        self.values: deque[float] = deque(maxlen=window_size)
        self._mean = 0.0
        self._std = 0.0

    def add_value(self, value: float) -> None:
        """Add a value to the detector."""
        self.values.append(value)

        if len(self.values) >= 10:  # Need minimum samples
            self._update_statistics()

    def _update_statistics(self) -> None:
        """Update mean and standard deviation."""
        if not self.values:
            return

        self._mean = sum(self.values) / len(self.values)

        if len(self.values) > 1:
            variance = sum((x - self._mean) ** 2 for x in self.values) / (
                len(self.values) - 1
            )
            self._std = variance**0.5
        else:
            self._std = 0.0

    def is_anomaly(self, value: float) -> bool:
        """Check if a value is anomalous."""
        if len(self.values) < 10:
            # Not enough data
            self.add_value(value)
            return False

        # Check if outside threshold
        if self._std > 0:
            z_score = abs((value - self._mean) / self._std)
            is_anomaly = z_score > self.std_threshold
        else:
            is_anomaly = False

        # Add value after checking
        self.add_value(value)

        return is_anomaly

    def get_expected_range(self) -> Tuple[float, float]:
        """Get expected value range."""
        if self._std == 0:
            return (self._mean, self._mean)

        lower = self._mean - (self.std_threshold * self._std)
        upper = self._mean + (self.std_threshold * self._std)

        return (lower, upper)


class SecurityTelemetry:
    """Security-specific telemetry collection."""

    def __init__(self, telemetry_collector: TelemetryCollector):
        self.telemetry = telemetry_collector

        # Security event types
        self.security_events = {
            "authentication_attempt",
            "authorization_check",
            "threat_detected",
            "incident_created",
            "remediation_executed",
            "policy_violation",
            "data_access",
            "configuration_change",
        }

        # Initialize security metrics
        self._init_security_metrics()

    def _init_security_metrics(self) -> None:
        """Initialize security-specific metrics."""
        # Authentication metrics
        self.telemetry.record_metric("auth_attempts_total", 0)
        self.telemetry.record_metric("auth_failures_total", 0)
        self.telemetry.record_metric("auth_success_rate", 100.0)

        # Threat metrics
        self.telemetry.record_metric(
            "threats_detected_by_severity", 0, {"severity": "low"}
        )
        self.telemetry.record_metric(
            "threats_detected_by_severity", 0, {"severity": "medium"}
        )
        self.telemetry.record_metric(
            "threats_detected_by_severity", 0, {"severity": "high"}
        )
        self.telemetry.record_metric(
            "threats_detected_by_severity", 0, {"severity": "critical"}
        )

        # Incident metrics
        self.telemetry.record_metric("incident_response_time", 0)
        self.telemetry.record_metric("incident_resolution_time", 0)

        # Setup anomaly detection for critical metrics
        self.telemetry.register_anomaly_detector(
            "auth_failures_total", AnomalyDetector(window_size=100, std_threshold=2.0)
        )

        self.telemetry.register_anomaly_detector(
            "threats_detected_total",
            AnomalyDetector(window_size=100, std_threshold=3.0),
        )

    async def record_authentication_attempt(
        self, user_id: str, success: bool, method: str, source_ip: str
    ) -> None:
        """Record authentication attempt."""
        async with self.telemetry.trace_operation(
            "authentication_attempt",
            {
                "user_id": user_id,
                "method": method,
                "success": str(success),
                "source_ip": source_ip,
            },
        ):
            # Record metrics
            self.telemetry.record_metric("auth_attempts_total", 1)

            if not success:
                self.telemetry.record_metric("auth_failures_total", 1)

                # Record failure event
                self.telemetry.record_event(
                    "auth_failure",
                    {"user_id": user_id, "method": method, "source_ip": source_ip},
                    severity="warning",
                )

    async def record_threat_detection(
        self,
        threat_type: str,
        severity: str,
        confidence: float,
        source: str,
        details: Dict[str, Any],
    ) -> None:
        """Record threat detection."""
        async with self.telemetry.trace_operation(
            "threat_detection",
            {
                "threat_type": threat_type,
                "severity": severity,
                "confidence": str(confidence),
                "source": source,
            },
        ):
            # Record metrics
            self.telemetry.record_metric(
                "threats_detected_total",
                1,
                {"threat_type": threat_type, "severity": severity},
            )

            self.telemetry.record_metric(
                "threats_detected_by_severity", 1, {"severity": severity}
            )

            self.telemetry.record_metric(
                "threat_detection_confidence", confidence, {"threat_type": threat_type}
            )

            # Record event
            self.telemetry.record_event(
                "threat_detected",
                {
                    "threat_type": threat_type,
                    "severity": severity,
                    "confidence": confidence,
                    "source": source,
                    **details,
                },
                severity=severity,
            )

    async def record_incident_lifecycle(
        self,
        incident_id: str,
        phase: str,
        duration_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record incident lifecycle events."""
        async with self.telemetry.trace_operation(
            f"incident_{phase}",
            {"incident_id": incident_id, "phase": phase, **(metadata or {})},
        ):
            # Record phase transition
            self.telemetry.record_event(
                f"incident_{phase}", {"incident_id": incident_id, **(metadata or {})}
            )

            # Record duration metrics
            if duration_seconds:
                if phase == "detected":
                    self.telemetry.record_metric(
                        "incident_detection_time", duration_seconds
                    )
                elif phase == "responded":
                    self.telemetry.record_metric(
                        "incident_response_time", duration_seconds
                    )
                elif phase == "resolved":
                    self.telemetry.record_metric(
                        "incident_resolution_time", duration_seconds
                    )

    async def record_remediation_action(
        self,
        action_type: str,
        target: str,
        success: bool,
        duration_seconds: float,
        dry_run: bool = False,
    ) -> None:
        """Record remediation action execution."""
        async with self.telemetry.trace_operation(
            "remediation_action",
            {
                "action_type": action_type,
                "target": target,
                "success": str(success),
                "dry_run": str(dry_run),
            },
        ):
            # Record metrics
            self.telemetry.record_metric(
                "remediation_actions_total",
                1,
                {
                    "action_type": action_type,
                    "success": str(success),
                    "dry_run": str(dry_run),
                },
            )

            self.telemetry.record_metric(
                "remediation_execution_time",
                duration_seconds,
                {"action_type": action_type},
            )

            # Record event
            severity = "info" if success else "error"
            self.telemetry.record_event(
                "remediation_executed",
                {
                    "action_type": action_type,
                    "target": target,
                    "success": success,
                    "duration_seconds": duration_seconds,
                    "dry_run": dry_run,
                },
                severity=severity,
            )

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of telemetry collection."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self.telemetry.get_telemetry_summary(),
            "traces": self.telemetry._trace_buffer,
            "logs": self.telemetry._event_buffer,
            "status": "healthy",
        }

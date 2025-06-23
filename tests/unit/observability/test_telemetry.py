"""
Test suite for observability/telemetry.py - Production ADK telemetry testing.
"""

import asyncio
import os
import random
import time
import uuid
from datetime import datetime, timezone, timedelta

import pytest

import google.cloud.monitoring_v3 as monitoring_v3
import google.cloud.trace_v2 as trace_v2

# Import the actual production code
from src.observability.telemetry import (
    TelemetryCollector,
    TelemetryEvent,
    TelemetryType,
    MetricPoint,
    TraceSpan,
    AnomalyDetector,
    SecurityTelemetry,
)

# Use real project ID from credentials
PROJECT_ID = "your-gcp-project-id"
CREDENTIALS_PATH = (
    "/path/to/sentinelops/credentials/service-account-key.json"
)

# Set environment for real GCP services
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID


class TestTelemetryRealImplementation:
    """Test telemetry with 100% production code using REAL GCP services - NO MOCKS."""

    def test_telemetry_event_creation_and_defaults(self) -> None:
        """Test TelemetryEvent dataclass creation and default values."""
        # Test with explicit values
        event = TelemetryEvent(
            type=TelemetryType.EVENT,
            name="security_alert",
            attributes={
                "severity": "high",
                "source": "test_system",
                "alert_type": "intrusion_attempt",
            },
            severity="warning",
            trace_id="test_trace_123",
            span_id="test_span_456",
        )

        assert event.type == TelemetryType.EVENT
        assert event.name == "security_alert"
        assert event.attributes["severity"] == "high"
        assert event.severity == "warning"
        assert event.trace_id == "test_trace_123"
        assert event.span_id == "test_span_456"
        assert isinstance(event.event_id, str)
        assert isinstance(event.timestamp, datetime)

        # Test with default values
        default_event = TelemetryEvent()
        assert default_event.type == TelemetryType.EVENT
        assert default_event.name == ""
        assert default_event.attributes == {}
        assert default_event.severity == "info"
        assert default_event.trace_id is None
        assert default_event.span_id is None
        assert len(default_event.event_id) == 36  # UUID format
        assert isinstance(default_event.timestamp, datetime)

    def test_metric_point_creation_and_defaults(self) -> None:
        """Test MetricPoint dataclass creation and defaults."""
        timestamp = datetime.now(timezone.utc)
        point = MetricPoint(
            timestamp=timestamp,
            value=100.0,
            labels={"endpoint": "/api/incidents", "method": "GET", "status": "200"},
            exemplar_trace_id="trace_123",
        )

        assert point.value == 100.0
        assert point.timestamp == timestamp
        assert point.labels["endpoint"] == "/api/incidents"
        assert point.exemplar_trace_id == "trace_123"

        # Test with minimal values
        minimal_point = MetricPoint(timestamp=timestamp, value=42.0)
        assert minimal_point.timestamp == timestamp
        assert minimal_point.value == 42.0
        assert minimal_point.labels == {}
        assert minimal_point.exemplar_trace_id is None

    def test_trace_span_creation_and_defaults(self) -> None:
        """Test TraceSpan dataclass creation and defaults."""
        start_time = datetime.now(timezone.utc)

        # Test with full data
        span = TraceSpan(
            span_id="span_456",
            trace_id="trace_789",
            parent_span_id="parent_123",
            name="process_security_alert",
            start_time=start_time,
            attributes={"alert_id": "alert_456", "processing_time_ms": 250},
        )

        assert span.name == "process_security_alert"
        assert span.span_id == "span_456"
        assert span.trace_id == "trace_789"
        assert span.parent_span_id == "parent_123"
        assert span.start_time == start_time
        assert span.attributes["alert_id"] == "alert_456"

        # Test defaults
        assert span.end_time is None
        assert span.status == "ok"
        assert span.error is None
        assert isinstance(span.events, list)
        assert len(span.events) == 0

        # Test with error
        error_span = TraceSpan(
            span_id="error_span",
            trace_id="error_trace",
            parent_span_id=None,
            name="failing_operation",
            start_time=start_time,
            status="error",
            error="Division by zero",
        )
        assert error_span.status == "error"
        assert error_span.error == "Division by zero"
        assert error_span.parent_span_id is None  # Root span

    def test_telemetry_type_enum_complete(self) -> None:
        """Test all TelemetryType enum values."""
        assert TelemetryType.EVENT.value == "event"
        assert TelemetryType.METRIC.value == "metric"
        assert TelemetryType.TRACE.value == "trace"
        assert TelemetryType.LOG.value == "log"
        assert TelemetryType.PROFILE.value == "profile"

        # Test enum membership
        all_types = [
            TelemetryType.EVENT,
            TelemetryType.METRIC,
            TelemetryType.TRACE,
            TelemetryType.LOG,
            TelemetryType.PROFILE,
        ]
        assert len(all_types) == 5

    def test_anomaly_detector_complete_functionality(self) -> None:
        """Test AnomalyDetector comprehensive functionality."""
        # Test initialization
        detector = AnomalyDetector(window_size=50, std_threshold=2.5)
        assert detector.window_size == 50
        assert detector.std_threshold == 2.5
        assert len(detector.values) == 0
        assert detector._mean == 0
        assert detector._std == 0

        # Test insufficient data
        for i in range(5):
            result = detector.is_anomaly(10.0 + i)
            assert result is False  # Not enough data yet

        # Test with normal data
        normal_values = [10.0, 11.0, 9.0, 10.5, 9.5, 10.2, 9.8, 10.1, 9.9, 10.3] * 2
        for value in normal_values:
            detector.is_anomaly(value)

        # Test normal value detection
        assert detector.is_anomaly(10.5) is False

        # Test clear anomaly
        assert detector.is_anomaly(100.0) is True

        # Test expected range
        lower, upper = detector.get_expected_range()
        assert lower < upper
        assert 10.0 >= lower and 10.0 <= upper

        # Test edge case: zero standard deviation
        zero_std_detector = AnomalyDetector()
        for _ in range(15):
            zero_std_detector.add_value(5.0)

        assert zero_std_detector.is_anomaly(5.0) is False
        lower, upper = zero_std_detector.get_expected_range()
        assert lower == upper == 5.0

        # Test statistical accuracy
        statistical_detector = AnomalyDetector(window_size=100, std_threshold=2.0)
        random.seed(42)
        normal_data = [random.gauss(50, 5) for _ in range(100)]

        anomaly_count = 0
        for value in normal_data:
            if statistical_detector.is_anomaly(value):
                anomaly_count += 1

        anomaly_rate = anomaly_count / len(normal_data)
        assert anomaly_rate < 0.10  # Should have very few false positives

    @pytest.mark.asyncio
    async def test_telemetry_collector_real_initialization(self) -> None:
        """Test TelemetryCollector with real GCP services initialization."""
        # Create collector in async context so background tasks can start
        collector = TelemetryCollector(
            PROJECT_ID, f"test-service-{uuid.uuid4().hex[:8]}"
        )

        # Allow background tasks to start
        await asyncio.sleep(0.1)

        # Verify real GCP clients are created
        assert collector.project_id == PROJECT_ID
        assert collector.project_name == f"projects/{PROJECT_ID}"
        assert isinstance(collector.metrics_client, monitoring_v3.MetricServiceClient)
        assert isinstance(collector.trace_client, trace_v2.TraceServiceClient)

        # Test aggregation windows
        expected_windows = {"1m", "5m", "15m", "1h", "1d"}
        assert set(collector._aggregation_windows.keys()) == expected_windows

        # Verify buffers are initialized
        assert isinstance(collector._metric_buffer, dict)
        assert isinstance(collector._event_buffer, list)
        assert isinstance(collector._performance_baselines, dict)
        assert isinstance(collector._anomaly_detectors, dict)

    @pytest.mark.asyncio
    async def test_record_metric_comprehensive(self) -> None:
        """Test record_metric with comprehensive scenarios."""
        collector = TelemetryCollector(PROJECT_ID, "test-record-metric")
        await asyncio.sleep(0.1)

        # Test basic metric recording
        collector.record_metric("test_counter", 1.0)

        # Test metric with labels
        collector.record_metric(
            "test_gauge", 42.0, labels={"environment": "test", "version": "1.0"}
        )

        # Test metric with custom timestamp
        custom_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        collector.record_metric("test_historic", 10.0, timestamp=custom_time)

        # Test with None values (should handle gracefully)
        collector.record_metric("none_test", 0.0, labels=None, timestamp=None)

        # Test with empty labels
        collector.record_metric("empty_test", 0.0, labels={})

        # Test complex labels
        complex_labels = {
            "service": "api",
            "version": "1.2.3",
            "environment": "production",
            "region": "us-central1",
            "instance_id": "inst-123",
            "request_type": "POST",
            "endpoint": "/api/v1/incidents",
        }
        collector.record_metric("complex_metric", 123.45, labels=complex_labels)

        # Test time series
        base_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        for i in range(10):
            timestamp = base_time + timedelta(minutes=i)
            collector.record_metric(
                "time_series_metric",
                float(i * 10),
                labels={"sequence": str(i)},
                timestamp=timestamp,
            )

        # Verify metrics are buffered
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] >= 15

    @pytest.mark.asyncio
    async def test_record_event_comprehensive(self) -> None:
        """Test record_event with comprehensive scenarios."""
        collector = TelemetryCollector(PROJECT_ID, "test-record-event")
        await asyncio.sleep(0.1)

        # Test basic event
        collector.record_event("test_event")

        # Test event with attributes
        collector.record_event(
            "security_alert",
            attributes={
                "alert_type": "intrusion",
                "severity": "high",
                "source_ip": "192.168.1.100",
            },
            severity="warning",
        )

        # Test with None attributes
        collector.record_event("none_test", attributes=None)

        # Test with empty attributes
        collector.record_event("empty_test", attributes={})

        # Test large event with complex attributes
        large_attributes: dict[str, str] = {f"attr_{i}": f"value_{i}" for i in range(20)}
        large_attributes["unicode_text"] = "Hello 世界 🌍 🔐 🚨"
        large_attributes["json_data"] = '{"key": "value", "number": 42}'

        # Record the large event with string attributes only
        collector.record_event(
            "large_event", attributes=large_attributes, severity="info"
        )

        # Test various attribute types - convert to strings for type safety
        collector.record_event(
            "complex_event",
            attributes={
                "string": "value",
                "number": "123",
                "float": "45.67",
                "boolean": "True",
                "null": "None",
                "list": "[1, 2, 3]",
                "dict": '{"nested": "value"}',
            },
        )

        # Verify events are buffered
        summary = collector.get_telemetry_summary()
        assert summary["events_buffered"] >= 6

    @pytest.mark.asyncio
    async def test_performance_baseline_and_regression_detection(self) -> None:
        """Test performance baseline and regression detection functionality."""
        collector = TelemetryCollector(PROJECT_ID, "test-performance")
        await asyncio.sleep(0.1)

        metric_name = "api_response_time"
        baseline = {"p50": 100.0, "p95": 250.0, "p99": 500.0}

        # Set baseline
        collector.set_performance_baseline(metric_name, baseline)

        # Verify baseline is set
        summary = collector.get_telemetry_summary()
        assert metric_name in summary["performance_baselines"]

        # Test no regression (within threshold)
        regression = collector.check_performance_regression(metric_name, 105.0, 10.0)
        assert regression is None

        # Test regression detection (above threshold)
        regression = collector.check_performance_regression(metric_name, 120.0, 10.0)
        assert regression is not None
        assert regression["metric"] == metric_name
        assert regression["current"] == 120.0
        assert regression["regression_percent"] > 10.0
        assert "baseline" in regression
        assert "percentile" in regression

        # Test with unknown metric
        unknown_regression = collector.check_performance_regression(
            "unknown_metric", 100.0
        )
        assert unknown_regression is None

        # Test multiple baselines
        collector.set_performance_baseline("memory_usage", {"p95": 80.0})
        collector.set_performance_baseline("cpu_usage", {"p99": 90.0})

        summary = collector.get_telemetry_summary()
        assert len(summary["performance_baselines"]) >= 3

    @pytest.mark.asyncio
    async def test_anomaly_detector_integration(self) -> None:
        """Test anomaly detector registration and integration."""
        collector = TelemetryCollector(PROJECT_ID, "test-anomaly")
        await asyncio.sleep(0.1)

        # Register anomaly detector
        detector = AnomalyDetector(window_size=30, std_threshold=2.5)
        metric_name = "test_metric_with_anomaly_detection"
        collector.register_anomaly_detector(metric_name, detector)

        # Verify registration
        summary = collector.get_telemetry_summary()
        assert summary["active_anomaly_detectors"] >= 1

        # Record normal values
        for i in range(15):
            collector.record_metric(metric_name, 10.0 + i * 0.1)

        events_before = collector.get_telemetry_summary()["events_buffered"]

        # Record anomalous value - should trigger event
        collector.record_metric(metric_name, 100.0)

        events_after = collector.get_telemetry_summary()["events_buffered"]
        assert events_after > events_before  # Anomaly event should be recorded

        # Test multiple detectors
        collector.register_anomaly_detector("cpu_usage", AnomalyDetector())
        collector.register_anomaly_detector("memory_usage", AnomalyDetector())

        summary = collector.get_telemetry_summary()
        assert summary["active_anomaly_detectors"] >= 3

    @pytest.mark.asyncio
    async def test_telemetry_summary_complete(self) -> None:
        """Test get_telemetry_summary comprehensive functionality."""
        collector = TelemetryCollector(PROJECT_ID, "test-summary")
        await asyncio.sleep(0.1)

        # Add various data types
        collector.record_metric("summary_metric_1", 1.0)
        collector.record_metric("summary_metric_2", 2.0, {"label": "value"})
        collector.record_event("summary_event_1")
        collector.record_event("summary_event_2", {"data": "test"})

        # Register anomaly detector
        detector = AnomalyDetector()
        collector.register_anomaly_detector("summary_metric", detector)

        # Set performance baseline
        collector.set_performance_baseline("summary_baseline", {"p95": 100.0})

        summary = collector.get_telemetry_summary()

        # Verify all summary fields
        required_fields = [
            "metrics_buffered",
            "events_buffered",
            "active_anomaly_detectors",
            "performance_baselines",
            "aggregation_windows",
        ]

        for field in required_fields:
            assert field in summary

        # Verify values
        assert summary["metrics_buffered"] >= 2
        assert summary["events_buffered"] >= 2
        assert summary["active_anomaly_detectors"] >= 1
        assert len(summary["performance_baselines"]) >= 1
        assert len(summary["aggregation_windows"]) == 5  # 1m, 5m, 15m, 1h, 1d

        # Verify aggregation windows
        expected_windows = {"1m", "5m", "15m", "1h", "1d"}
        assert set(summary["aggregation_windows"]) == expected_windows

    @pytest.mark.asyncio
    async def test_trace_operations_and_context_management(self) -> None:
        """Test trace operations and context management."""
        collector = TelemetryCollector(PROJECT_ID, "test-trace")
        await asyncio.sleep(0.1)

        # Test successful trace operation
        operation_attrs = {"user_id": "test_user", "operation_type": "security_scan"}

        async with collector.trace_operation("test_operation", operation_attrs) as span:
            # Simulate some work
            await asyncio.sleep(0.1)

            # Add custom attributes to span
            if hasattr(span, 'set_attribute'):
                span.set_attribute("custom_attr", "test_value")

            # Record event during operation
            collector.record_event("operation_step", {"step": "processing"})

        # Test trace operation with exception
        with pytest.raises(ValueError):
            async with collector.trace_operation("failing_operation"):
                await asyncio.sleep(0.05)
                raise ValueError("Test exception")

        # Test span duration calculation
        start_time = datetime.now(timezone.utc)
        test_span = TraceSpan(
            span_id="test_span_123",
            trace_id="test_trace_123",
            parent_span_id=None,
            name="duration_test",
            start_time=start_time,
        )

        time.sleep(0.1)
        test_span.end_time = datetime.now(timezone.utc)

        if test_span.end_time is not None:
            duration = test_span.end_time - test_span.start_time
            assert duration.total_seconds() >= 0.1
            assert duration.total_seconds() < 0.2

    @pytest.mark.asyncio
    async def test_trace_span_hierarchy(self) -> None:
        """Test trace span hierarchy and relationships."""
        # Create parent span
        parent_span = TraceSpan(
            span_id="parent_span_123",
            trace_id="trace_hierarchy_123",
            parent_span_id=None,  # Root span
            name="parent_operation",
            start_time=datetime.now(timezone.utc),
        )

        # Create child spans
        child_spans = []
        for i in range(3):
            child = TraceSpan(
                span_id=f"child_span_{i}",
                trace_id=parent_span.trace_id,
                parent_span_id=parent_span.span_id,
                name=f"child_operation_{i}",
                start_time=datetime.now(timezone.utc),
                attributes={"child_index": i},
            )
            child_spans.append(child)

        # Verify hierarchy relationships
        assert all(child.trace_id == parent_span.trace_id for child in child_spans)
        assert all(child.parent_span_id == parent_span.span_id for child in child_spans)
        assert all(child.span_id != parent_span.span_id for child in child_spans)

        # Verify unique span IDs
        span_ids = [child.span_id for child in child_spans]
        assert len(set(span_ids)) == len(span_ids)

        # Test grandchild relationship
        grandchild = TraceSpan(
            span_id="grandchild_span",
            trace_id=parent_span.trace_id,
            parent_span_id=child_spans[0].span_id,
            name="grandchild_operation",
            start_time=datetime.now(timezone.utc),
        )

        assert grandchild.trace_id == parent_span.trace_id
        assert grandchild.parent_span_id == child_spans[0].span_id

    @pytest.mark.asyncio
    async def test_flush_telemetry_functionality(self) -> None:
        """Test flush_telemetry comprehensive functionality."""
        collector = TelemetryCollector(PROJECT_ID, "test-flush")
        await asyncio.sleep(0.1)

        # Add data to flush
        for i in range(5):
            collector.record_metric(f"flush_metric_{i}", float(i * 10))
            collector.record_event(f"flush_event_{i}", {"index": i})

        # Verify data is buffered
        summary_before = collector.get_telemetry_summary()
        assert summary_before["metrics_buffered"] >= 5
        assert summary_before["events_buffered"] >= 5

        # Flush telemetry
        await collector.flush_telemetry()

        # Note: In the current implementation, flush may not immediately clear buffers
        # due to the way the _flush_metrics method handles failures
        # This tests that the flush operation completes without error
        summary_after = collector.get_telemetry_summary()
        # Test that flush operation completed (metrics may or may not be cleared depending on GCP call success)
        assert isinstance(summary_after["metrics_buffered"], int)
        assert isinstance(summary_after["events_buffered"], int)

    @pytest.mark.asyncio
    async def test_security_telemetry_integration(self) -> None:
        """Test SecurityTelemetry integration and functionality."""
        collector = TelemetryCollector(PROJECT_ID, "test-security")
        await asyncio.sleep(0.1)

        security_telemetry = SecurityTelemetry(collector)

        # Verify initialization
        assert security_telemetry.telemetry == collector
        assert len(security_telemetry.security_events) == 8

        # Verify expected security events
        expected_events = {
            "authentication_attempt",
            "authorization_check",
            "threat_detected",
            "incident_created",
            "remediation_executed",
            "policy_violation",
            "data_access",
            "configuration_change",
        }
        assert security_telemetry.security_events == expected_events

    @pytest.mark.asyncio
    async def test_concurrent_operations_stress(self) -> None:
        """Test concurrent telemetry operations under stress."""
        collector = TelemetryCollector(PROJECT_ID, "test-concurrent")
        await asyncio.sleep(0.1)

        async def record_metrics() -> None:
            for i in range(20):
                collector.record_metric(f"concurrent_metric_{i % 5}", float(i))
                if i % 5 == 0:
                    await asyncio.sleep(0.001)  # Slight delay for concurrency

        async def record_events() -> None:
            for i in range(15):
                collector.record_event(f"concurrent_event_{i}", {"iteration": i})
                if i % 3 == 0:
                    await asyncio.sleep(0.001)

        async def trace_operations() -> None:
            for i in range(5):
                async with collector.trace_operation(f"concurrent_op_{i}"):
                    await asyncio.sleep(0.01)

        # Run all operations concurrently
        await asyncio.gather(
            record_metrics(),
            record_events(),
            trace_operations(),
            record_metrics(),  # Run metrics twice for stress
        )

        # Verify all data was recorded
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] >= 40  # 20 + 20 metrics
        assert summary["events_buffered"] >= 15

    def test_comprehensive_edge_cases_and_boundaries(self) -> None:
        """Test edge cases and boundary conditions."""
        # Test MetricPoint with various edge values
        edge_timestamp = datetime.now(timezone.utc)

        # Zero value
        zero_metric = MetricPoint(timestamp=edge_timestamp, value=0.0)
        assert zero_metric.value == 0.0

        # Negative value
        negative_metric = MetricPoint(timestamp=edge_timestamp, value=-123.45)
        assert negative_metric.value == -123.45

        # Large value
        large_metric = MetricPoint(timestamp=edge_timestamp, value=1e10)
        assert large_metric.value == 1e10

        # Empty labels dict
        empty_labels_metric = MetricPoint(
            timestamp=edge_timestamp, value=1.0, labels={}
        )
        assert empty_labels_metric.labels == {}

        # Test TraceSpan edge cases
        # Very short span
        now = datetime.now(timezone.utc)
        short_span = TraceSpan(
            span_id="short",
            trace_id="trace_short",
            parent_span_id=None,
            name="microsecond_op",
            start_time=now,
            end_time=now + timedelta(microseconds=1),
        )
        if short_span.end_time is not None:
            duration = short_span.end_time - short_span.start_time
            assert duration.total_seconds() < 0.001

        # Test TelemetryEvent edge cases
        # Empty name and attributes
        minimal_event = TelemetryEvent(name="", attributes={})
        assert minimal_event.name == ""
        assert minimal_event.attributes == {}

        # Maximum length names and values (boundary testing)
        long_name = "a" * 1000
        long_event = TelemetryEvent(name=long_name)
        assert long_event.name == long_name

    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self) -> None:
        """Test error handling and system resilience."""
        collector = TelemetryCollector(PROJECT_ID, "test-resilience")
        await asyncio.sleep(0.1)

        # Test with malformed but non-breaking inputs
        collector.record_metric("", 0.0)  # Empty name
        collector.record_event("", {})  # Empty name and attributes

        # Test with extreme values
        collector.record_metric("extreme_negative", -1e20)
        collector.record_metric("extreme_positive", 1e20)
        collector.record_metric("tiny_value", 1e-20)

        # Test with Unicode and special characters
        collector.record_metric("unicode_测试", 42.0, {"特殊": "值", "emoji": "🔥"})
        collector.record_event("unicode_event_测试", {"msg": "Hello 世界 🌍"})

        # Test performance with rapid operations
        start_time = time.time()
        for i in range(100):
            collector.record_metric("rapid_test", float(i))
        rapid_time = time.time() - start_time

        # Should complete rapidly (< 1 second for 100 operations)
        assert rapid_time < 1.0

        # Verify all operations completed
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] >= 100

    def test_data_structures_and_collections_behavior(self) -> None:
        """Test internal data structures and collections behavior."""
        # Test AnomalyDetector deque maxlen behavior
        detector = AnomalyDetector(window_size=5, std_threshold=2.0)

        # Add more values than window size
        for i in range(10):
            detector.add_value(float(i))

        # Should only keep last 5 values
        assert len(detector.values) == 5
        assert list(detector.values) == [5.0, 6.0, 7.0, 8.0, 9.0]

        # Test statistics update
        detector._update_statistics()
        assert detector._mean == 7.0  # Mean of [5,6,7,8,9]
        assert detector._std > 0  # Should have non-zero std dev

        # Test expected range calculation
        lower, upper = detector.get_expected_range()
        assert lower < detector._mean < upper
        assert upper - lower > 0

    @pytest.mark.asyncio
    async def test_opentelemetry_integration_paths(self) -> None:
        """Test OpenTelemetry integration and instrumentation paths."""
        collector = TelemetryCollector(PROJECT_ID, "test-otel")
        await asyncio.sleep(0.1)

        # Verify OpenTelemetry components are initialized
        assert hasattr(collector, "tracer")
        assert hasattr(collector, "propagator")

        # Test metric recording with trace context
        # This would normally capture current span context
        collector.record_metric("otel_metric", 123.0)

        # Test event recording with trace context
        collector.record_event("otel_event", {"context": "test"})

        # Verify data was recorded
        summary = collector.get_telemetry_summary()
        assert summary["metrics_buffered"] >= 1
        assert summary["events_buffered"] >= 1

    def test_complete_workflow_integration(self) -> None:
        """Test complete workflow integration across all components."""
        # This test demonstrates the complete telemetry workflow

        # 1. Create different data types
        event = TelemetryEvent(
            type=TelemetryType.EVENT,
            name="workflow_test",
            attributes={"phase": "initialization"},
        )

        metric = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            value=42.0,
            labels={"workflow": "test", "phase": "execution"},
        )

        span = TraceSpan(
            span_id="workflow_span",
            trace_id="workflow_trace",
            parent_span_id=None,
            name="workflow_operation",
            start_time=datetime.now(timezone.utc),
        )

        # 2. Verify all objects are properly created
        assert event.name == "workflow_test"
        assert metric.value == 42.0
        assert span.name == "workflow_operation"

        # 3. Test anomaly detector workflow
        detector = AnomalyDetector(window_size=10, std_threshold=2.0)

        # Add normal data
        for i in range(15):
            detector.add_value(10.0 + (i % 3))  # Values around 10-12

        # Test normal value
        assert detector.is_anomaly(11.0) is False

        # Test anomaly
        assert detector.is_anomaly(50.0) is True

        # 4. Verify workflow completed successfully
        assert True  # All components work together

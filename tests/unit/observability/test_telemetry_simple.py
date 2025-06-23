"""SIMPLIFIED tests for observability/telemetry.py - Tests core telemetry logic."""

from datetime import datetime, timezone, timedelta
from typing import Any

import pytest

# Import the actual production code data structures
from src.observability.telemetry import (
    TelemetryEvent,
    TelemetryType,
    MetricPoint,
    TraceSpan,
    TelemetryCollector,
)


class TestTelemetryDataStructures:
    """Test telemetry data structures with real logic."""

    def test_telemetry_event_creation_and_validation(self) -> None:
        """Test TelemetryEvent creation with various configurations."""
        # Test with minimal data
        event1 = TelemetryEvent(name="user_login")

        assert event1.name == "user_login"
        assert event1.type == TelemetryType.EVENT
        assert event1.attributes == {}
        assert event1.severity == "info"
        assert isinstance(event1.event_id, str)
        assert len(event1.event_id) == 36  # UUID format
        assert isinstance(event1.timestamp, datetime)

        # Test with full data
        event2 = TelemetryEvent(
            name="security_alert",
            type=TelemetryType.EVENT,
            attributes={
                "alert_type": "malware_detected",
                "source_ip": "192.168.1.100",
                "target_system": "web-server-01",
                "confidence": 0.95,
            },
            severity="critical",
        )

        assert event2.name == "security_alert"
        assert event2.type == TelemetryType.EVENT
        assert len(event2.attributes) == 4
        assert event2.attributes["alert_type"] == "malware_detected"
        assert event2.severity == "critical"

    def test_telemetry_event_timestamp_behavior(self) -> None:
        """Test timestamp behavior in TelemetryEvent."""
        # Test automatic timestamp generation
        event1 = TelemetryEvent(name="auto_timestamp")
        assert isinstance(event1.timestamp, datetime)
        assert event1.timestamp.tzinfo is not None

        # Test custom timestamp
        custom_time = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        event2 = TelemetryEvent(name="custom_timestamp", timestamp=custom_time)
        assert event2.timestamp == custom_time
        assert event2.timestamp.tzinfo is not None

    def test_metric_point_creation_and_validation(self) -> None:
        """Test MetricPoint creation with various configurations."""
        now = datetime.now(timezone.utc)

        # Test with minimal data
        metric1 = MetricPoint(timestamp=now, value=75.5)

        assert metric1.value == 75.5
        assert metric1.labels == {}
        assert isinstance(metric1.timestamp, datetime)

        # Test with full data
        metric2 = MetricPoint(
            timestamp=now,
            value=1234,
            labels={
                "method": "POST",
                "endpoint": "/api/incidents",
                "status_code": "201",
                "service": "sentinelops-api",
            },
        )

        assert metric2.value == 1234
        assert len(metric2.labels) == 4
        assert metric2.labels["method"] == "POST"

    def test_metric_point_numeric_values(self) -> None:
        """Test MetricPoint with various numeric types."""
        now = datetime.now(timezone.utc)

        # Integer value
        m1 = MetricPoint(timestamp=now, value=100)
        assert m1.value == 100
        assert isinstance(m1.value, (int, float))

        # Float value
        m2 = MetricPoint(timestamp=now, value=99.99)
        assert m2.value == 99.99
        assert isinstance(m2.value, float)

        # Zero value
        m3 = MetricPoint(timestamp=now, value=0)
        assert m3.value == 0

        # Negative value
        m4 = MetricPoint(timestamp=now, value=-25.5)
        assert m4.value == -25.5

    def test_trace_span_creation_and_validation(self) -> None:
        """Test TraceSpan creation with various configurations."""
        now = datetime.now(timezone.utc)

        # Test with minimal data
        span1 = TraceSpan(
            span_id="span-12345",
            trace_id="trace_12345",
            parent_span_id=None,
            name="database_query",
            start_time=now,
        )

        assert span1.name == "database_query"
        assert span1.trace_id == "trace_12345"
        assert span1.parent_span_id is None
        assert span1.attributes == {}
        assert isinstance(span1.span_id, str)
        assert len(span1.span_id) == 10  # Custom span ID length
        assert isinstance(span1.start_time, datetime)
        assert span1.end_time is None

        # Test with full data
        span2 = TraceSpan(
            span_id="span-67890",
            trace_id="trace_67890",
            parent_span_id="parent_span_123",
            name="api.request.process",
            start_time=now,
            attributes={
                "http.method": "GET",
                "http.url": "/api/rules",
                "http.status_code": 200,
                "user.id": "user_456",
            },
        )

        assert span2.name == "api.request.process"
        assert span2.trace_id == "trace_67890"
        assert span2.parent_span_id == "parent_span_123"
        assert len(span2.attributes) == 4
        assert span2.attributes["http.status_code"] == 200

    def test_trace_span_unique_ids(self) -> None:
        """Test that spans generate unique IDs."""
        now = datetime.now(timezone.utc)
        spans = []
        for i in range(10):
            span = TraceSpan(
                span_id=f"span-{i}",
                trace_id="common_trace",
                parent_span_id=None,
                name=f"span_{i}",
                start_time=now,
            )
            spans.append(span)

        # All span IDs should be unique
        span_ids = [s.span_id for s in spans]
        assert len(set(span_ids)) == len(span_ids)

        # All should share the same trace ID
        assert all(s.trace_id == "common_trace" for s in spans)

    def test_telemetry_type_enum_usage(self) -> None:
        """Test TelemetryType enum usage in events."""
        for tel_type in TelemetryType:
            event = TelemetryEvent(type=tel_type, name=f"test_{tel_type.value}")
            assert event.type == tel_type
            assert event.name == f"test_{tel_type.value}"

    def test_event_severity_levels(self) -> None:
        """Test different severity levels for events."""
        severity_levels = ["debug", "info", "warning", "error", "critical"]

        for severity in severity_levels:
            event = TelemetryEvent(name=f"event_{severity}", severity=severity)
            assert event.severity == severity

    def test_span_end_time_behavior(self) -> None:
        """Test span end time functionality."""
        now = datetime.now(timezone.utc)
        span = TraceSpan(
            span_id="span-test",
            trace_id="trace_test",
            parent_span_id=None,
            name="test_operation",
            start_time=now,
        )

        # Initially, end_time should be None
        assert span.end_time is None

        # Can set end_time
        span.end_time = datetime.now(timezone.utc)
        assert span.end_time is not None
        assert span.end_time >= span.start_time

    def test_attribute_types_preservation(self) -> None:
        """Test that various attribute types are preserved correctly."""
        # Test with TelemetryEvent
        event = TelemetryEvent(
            name="test_event",
            attributes={
                "string": "value",
                "integer": 42,
                "float": 3.14,
                "boolean": True,
                "none": None,
                "list": [1, "two", 3.0],
                "dict": {"nested": {"key": "value"}},
            },
        )

        assert isinstance(event.attributes["string"], str)
        assert isinstance(event.attributes["integer"], int)
        assert isinstance(event.attributes["float"], float)
        assert isinstance(event.attributes["boolean"], bool)
        assert event.attributes["none"] is None
        assert isinstance(event.attributes["list"], list)
        assert isinstance(event.attributes["dict"], dict)
        assert event.attributes["dict"]["nested"]["key"] == "value"

    def test_metric_labels_as_strings(self) -> None:
        """Test that metric labels are string key-value pairs."""
        now = datetime.now(timezone.utc)
        metric = MetricPoint(
            timestamp=now,
            value=100,
            labels={"env": "production", "version": "1.2.3", "region": "us-central1"},
        )

        # All keys and values should be strings
        for key, value in metric.labels.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    def test_span_duration_calculation_helper(self) -> None:
        """Test calculating span duration."""
        # Create span with known start and end times
        start = datetime.now(timezone.utc)
        span = TraceSpan(
            span_id="span-timing",
            trace_id="trace_timing",
            parent_span_id=None,
            name="timed_operation",
            start_time=start,
        )

        # Set end time 1 second later
        end = start + timedelta(seconds=1)
        span.end_time = end

        # Calculate duration
        duration = (span.end_time - span.start_time).total_seconds()
        assert duration == 1.0

    def test_event_id_uniqueness(self) -> None:
        """Test that event IDs are unique."""
        events = []
        for i in range(100):
            event = TelemetryEvent(name=f"event_{i}")
            events.append(event)

        # All event IDs should be unique
        event_ids = [e.event_id for e in events]
        assert len(set(event_ids)) == len(event_ids)

        # All should be valid UUIDs
        for event_id in event_ids:
            assert len(event_id) == 36
            assert event_id.count("-") == 4

    def test_telemetry_collector_initialization(self) -> None:
        """Test TelemetryCollector initialization with real project."""
        project_id = "your-gcp-project-id"
        collector = TelemetryCollector(
            project_id=project_id, service_name="test-service"
        )

        assert collector.project_id == project_id
        assert collector.service_name == "test-service"
        assert hasattr(collector, "_metrics_buffer")
        assert hasattr(collector, "_events_buffer")

    @pytest.mark.asyncio
    async def test_record_metric_basic(self, telemetry_collector: Any) -> None:
        """Test basic metric recording functionality."""
        # Record a simple metric
        telemetry_collector.record_metric("test_metric", 42.5, {"env": "test"})

        # Verify metric was recorded
        assert len(telemetry_collector._metric_buffer) > 0
        metric_name = list(telemetry_collector._metric_buffer.keys())[0]
        assert "test_metric" in metric_name

    @pytest.mark.asyncio
    async def test_record_event_basic(self, telemetry_collector: Any) -> None:
        """Test basic event recording functionality."""
        # Record a simple event
        telemetry_collector.record_event(
            "test_event", {"action": "test", "result": "success"}
        )

        # Verify event was recorded
        assert len(telemetry_collector._event_buffer) > 0
        event = telemetry_collector._event_buffer[0]
        assert event.name == "test_event"
        assert event.attributes["action"] == "test"

    @pytest.mark.asyncio
    async def test_trace_span_creation(self) -> None:
        """Test TraceSpan creation with required fields."""
        now = datetime.now(timezone.utc)

        span = TraceSpan(
            span_id="span-123",
            trace_id="trace-456",
            parent_span_id="parent-789",
            name="database_query",
            start_time=now,
        )

        # Verify span creation
        assert span.span_id == "span-123"
        assert span.trace_id == "trace-456"
        assert span.name == "database_query"

    def test_telemetry_event_creation(self) -> None:
        """Test TelemetryEvent creation with real data."""
        now = datetime.now(timezone.utc)

        event = TelemetryEvent(
            name="user_login",
            attributes={"user_id": "123", "method": "oauth"},
            timestamp=now,
            severity="info",
        )

        assert event.name == "user_login"
        assert event.attributes["user_id"] == "123"
        assert event.severity == "info"

    def test_metric_point_creation(self) -> None:
        """Test MetricPoint creation with real timestamp."""
        now = datetime.now(timezone.utc)

        # Create metric point without metric_name (not a valid parameter)
        point = MetricPoint(timestamp=now, value=42.5, labels={"env": "test"})

        assert point.timestamp == now
        assert point.value == 42.5
        assert point.labels["env"] == "test"

    def test_trace_span_creation_complete(self) -> None:
        """Test TraceSpan creation with all required fields."""
        now = datetime.now(timezone.utc)

        span = TraceSpan(
            span_id="span-456",
            trace_id="trace-789",
            parent_span_id="parent-123",
            name="api_call",
            start_time=now,
        )

        assert span.span_id == "span-456"
        assert span.trace_id == "trace-789"
        assert span.name == "api_call"

    def test_metric_point_default_labels(self) -> None:
        """Test MetricPoint creation with default labels."""
        now = datetime.now(timezone.utc)

        point = MetricPoint(timestamp=now, value=100.0)

        assert point.timestamp == now
        assert point.value == 100.0
        assert point.labels == {}

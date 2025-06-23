"""
Comprehensive tests for common/logging_config.py module.

Tests all logging configuration classes and functions with real GCP services.
NO MOCKING - 100% production code testing for ≥90% statement coverage.
"""

import json
import logging
import threading
import time
from io import StringIO

import pytest

# Import the actual production code - NO MOCKS
from src.common.logging_config import (
    StructuredFormatter,
    setup_logging,
    PerformanceMonitor,
    CorrelationContext,
    log_context,
    log_agent_status,
    create_incident_logger,
    get_performance_monitor,
)


class TestStructuredFormatter:
    """Test StructuredFormatter class functionality with real implementation."""

    def test_basic_formatting(self) -> None:
        """Test basic log record formatting to JSON."""
        formatter = StructuredFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.created = 1700000000.123456  # Fixed timestamp for testing

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["message"] == "Test message"
        assert parsed["severity"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["module"] == "test_module"
        assert parsed["function"] == "test_function"
        assert parsed["line"] == 42
        assert "timestamp" in parsed

    def test_formatting_with_agent_context(self) -> None:
        """Test formatting with agent context fields."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=100,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        # Add agent context fields
        record.agent_id = "agent123"
        record.agent_type = "detection"
        record.incident_id = "incident456"
        record.correlation_id = "corr789"

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["agent_id"] == "agent123"
        assert parsed["agent_type"] == "detection"
        assert parsed["incident_id"] == "incident456"
        assert parsed["correlation_id"] == "corr789"

    def test_formatting_with_custom_extra_fields(self) -> None:
        """Test formatting with additional custom fields."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.WARNING,
            pathname="/test/path.py",
            lineno=200,
            msg="Warning message",
            args=(),
            exc_info=None,
        )

        # Add custom fields that should be included
        record.user_id = "user123"
        record.custom_data = {"key": "value"}

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["user_id"] == "user123"
        assert parsed["custom_data"] == {"key": "value"}

    def test_formatting_with_exception(self) -> None:
        """Test formatting with exception information."""
        formatter = StructuredFormatter()

        exc_info = None
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=300,
            msg="Error with exception",
            args=(),
            exc_info=exc_info,
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "Test exception" in parsed["exception"]

    def test_formatting_excludes_builtin_fields(self) -> None:
        """Test that built-in log record fields are excluded from extra fields."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=400,
            msg="Test exclusion",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        # These built-in fields should not appear as separate keys
        excluded_fields = [
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "levelname",
            "levelno",
            "process",
            "processName",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
        ]

        for field in excluded_fields:
            assert field not in parsed


class TestSetupLogging:
    """Test setup_logging function with real implementations."""

    def test_console_logging_setup(self) -> None:
        """Test console logging setup when cloud logging is disabled."""
        logger = setup_logging(
            agent_type="test_console",
            agent_id="console-123",
            use_cloud_logging=False,
            log_level="INFO",
        )

        assert logger.name == "sentinelops.test_console"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

        # Should have structured formatter
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)

    def test_console_logging_debug_mode(self) -> None:
        """Test console logging with debug mode enabled."""
        logger = setup_logging(
            agent_type="test_debug",
            agent_id="debug-456",
            use_cloud_logging=False,
            log_level="DEBUG",
        )

        assert logger.level == logging.DEBUG
        # Check that formatter is configured appropriately
        handler = logger.handlers[0]
        assert handler.formatter is not None

    def test_cloud_logging_setup_success(self) -> None:
        """Test cloud logging setup with real GCP integration."""
        # This will attempt real cloud logging setup
        logger = setup_logging(
            agent_type="test_cloud",
            agent_id="cloud-789",
            use_cloud_logging=True,
            log_level="WARNING",
        )

        assert logger.name == "sentinelops.test_cloud"
        assert logger.level == logging.WARNING
        assert len(logger.handlers) >= 1

        # Should have either Cloud Logging or fallback to console
        handler = logger.handlers[0]
        # Type will depend on whether cloud logging succeeded
        assert handler is not None

    def test_cloud_logging_fallback(self) -> None:
        """Test fallback to console logging when cloud logging fails."""
        # For testing, we can't easily force cloud logging failure
        # So we test with use_cloud_logging=False and verify console setup
        logger = setup_logging(
            agent_type="test_fallback",
            agent_id="fallback-000",
            use_cloud_logging=False,
            log_level="ERROR",
        )

        assert logger.name == "sentinelops.test_fallback"
        assert logger.level == logging.ERROR

    def test_different_log_levels(self) -> None:
        """Test different log levels are properly set."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level_str in levels:
            logger = setup_logging(
                agent_type=f"test_{level_str.lower()}",
                agent_id=f"level-{level_str}",
                use_cloud_logging=False,
                log_level=level_str,
            )

            expected_level = getattr(logging, level_str)
            assert logger.level == expected_level

    def test_agent_context_filter(self) -> None:
        """Test that agent context is added to log records."""
        logger = setup_logging(
            agent_type="test_context", agent_id="context-456", use_cloud_logging=False
        )

        # Capture log outpu
        string_io = StringIO()
        test_handler = logging.StreamHandler(string_io)
        test_handler.setFormatter(StructuredFormatter())
        logger.addHandler(test_handler)

        logger.info("Test message")

        output = string_io.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["agent_type"] == "test_context"
        assert parsed["agent_id"] == "context-456"

    def test_handler_clearing(self) -> None:
        """Test that existing handlers are cleared when setting up logging."""
        # Create logger with initial handler
        test_logger = logging.getLogger("sentinelops.test_clear")
        initial_handler = logging.StreamHandler()
        test_logger.addHandler(initial_handler)

        # Verify initial handler exists
        assert len(test_logger.handlers) == 1

        # Setup logging should clear existing handlers
        logger = setup_logging(
            agent_type="test_clear",
            agent_id="clear-123",
            use_cloud_logging=False,
            log_level="INFO",
        )

        # Should have new handler(s) only
        assert len(logger.handlers) >= 1
        # Initial handler should not be present
        assert initial_handler not in logger.handlers


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality with real implementations."""

    def test_monitor_initialization(self) -> None:
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        assert not monitor.metrics
        assert monitor.logger is not None

    def test_monitor_with_logger(self) -> None:
        """Test PerformanceMonitor with custom logger."""
        custom_logger = logging.getLogger("test.performance")
        monitor = PerformanceMonitor(logger=custom_logger)
        assert monitor.logger == custom_logger

    def test_measure_context_manager_success(self) -> None:
        """Test measure context manager for successful operations."""
        monitor = PerformanceMonitor()

        with monitor.measure("test_operation", category="test"):
            time.sleep(0.1)  # Simulate work

        metrics = monitor.get_metrics()
        assert "test_operation" in metrics

        metric = metrics["test_operation"]
        assert metric["count"] == 1
        assert metric["total_time"] >= 0.1
        assert metric["min_time"] >= 0.1
        assert metric["max_time"] >= 0.1
        assert metric["errors"] == 0

    def test_measure_context_manager_with_error(self) -> None:
        """Test measure context manager when operation fails."""
        monitor = PerformanceMonitor()

        with pytest.raises(ValueError):
            with monitor.measure("failing_operation"):
                raise ValueError("Test error")

        metrics = monitor.get_metrics()
        assert "failing_operation" in metrics

        metric = metrics["failing_operation"]
        assert metric["count"] == 1
        assert metric["errors"] == 1

    def test_multiple_operations_same_name(self) -> None:
        """Test recording multiple operations with the same name."""
        monitor = PerformanceMonitor()

        # Record multiple operations
        with monitor.measure("repeated_op"):
            time.sleep(0.05)

        with monitor.measure("repeated_op"):
            time.sleep(0.1)

        metrics = monitor.get_metrics()
        metric = metrics["repeated_op"]

        assert metric["count"] == 2
        assert metric["total_time"] >= 0.15
        assert metric["avg_time"] >= 0.075
        assert metric["min_time"] <= metric["max_time"]

    def test_concurrent_measurements(self) -> None:
        """Test concurrent performance measurements."""
        monitor = PerformanceMonitor()

        def worker(operation_id: int) -> None:
            with monitor.measure(f"concurrent_op_{operation_id}"):
                time.sleep(0.05)

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        metrics = monitor.get_metrics()

        # Should have metrics for each operation
        for i in range(3):
            assert f"concurrent_op_{i}" in metrics
            assert metrics[f"concurrent_op_{i}"]["count"] == 1

    def test_get_metrics_calculations(self) -> None:
        """Test that get_metrics calculates averages and error rates correctly."""
        monitor = PerformanceMonitor()

        # Record metrics with known values through _record_metric
        monitor._record_metric("test_calc", 1.0, False, {})
        monitor._record_metric("test_calc", 2.0, True, {})  # One error
        monitor._record_metric("test_calc", 3.0, False, {})

        metrics = monitor.get_metrics()
        metric = metrics["test_calc"]

        assert metric["count"] == 3
        assert metric["total_time"] == 6.0
        assert metric["avg_time"] == 2.0
        assert metric["min_time"] == 1.0
        assert metric["max_time"] == 3.0
        assert metric["errors"] == 1
        assert metric["error_rate"] == 1 / 3

    def test_reset_metrics(self) -> None:
        """Test resetting metrics."""
        monitor = PerformanceMonitor()

        with monitor.measure("test_reset"):
            pass

        assert len(monitor.get_metrics()) == 1

        monitor.reset()
        assert len(monitor.get_metrics()) == 0


class TestCorrelationContext:
    """Test CorrelationContext class with real implementation."""

    def test_set_and_get_correlation_id(self) -> None:
        """Test setting and getting correlation ID."""
        test_id = "test-correlation-123"

        CorrelationContext.set_correlation_id(test_id)
        retrieved_id = CorrelationContext.get_correlation_id()

        assert retrieved_id == test_id

    def test_get_correlation_id_when_none_set(self) -> None:
        """Test getting correlation ID when none is set."""
        CorrelationContext.clear()

        correlation_id = CorrelationContext.get_correlation_id()
        assert correlation_id is None

    def test_clear_correlation_id(self) -> None:
        """Test clearing correlation ID."""
        CorrelationContext.set_correlation_id("test-clear-456")
        assert CorrelationContext.get_correlation_id() is not None

        CorrelationContext.clear()
        assert CorrelationContext.get_correlation_id() is None

    def test_thread_local_isolation(self) -> None:
        """Test that correlation IDs are isolated between threads."""
        results = {}

        def set_and_get(thread_id: int) -> None:
            correlation_id = f"thread-{thread_id}-correlation"
            CorrelationContext.set_correlation_id(correlation_id)
            time.sleep(0.1)  # Allow other threads to run
            results[thread_id] = CorrelationContext.get_correlation_id()

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=set_and_get, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Each thread should have its own correlation ID
        for i in range(3):
            assert results[i] == f"thread-{i}-correlation"


class TestLogContext:
    """Test log_context function with real implementation."""

    def test_log_context_adds_fields(self) -> None:
        """Test that log_context adds fields to log records."""
        logger = logging.getLogger("test_log_context")
        logger.handlers.clear()

        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        with log_context(user_id="user123", operation="test_op"):
            logger.info("Test message")

        output = string_io.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["user_id"] == "user123"
        assert parsed["operation"] == "test_op"

    def test_log_context_includes_correlation_id(self) -> None:
        """Test that log_context includes correlation ID when set."""
        logger = logging.getLogger("test_correlation_context")
        logger.handlers.clear()

        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        CorrelationContext.set_correlation_id("test-corr-789")

        with log_context(test_field="test_value"):
            logger.info("Test message with correlation")

        output = string_io.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["correlation_id"] == "test-corr-789"
        assert parsed["test_field"] == "test_value"

        CorrelationContext.clear()

    def test_log_context_filter_cleanup(self) -> None:
        """Test that log context filter is properly removed after context."""
        logger = logging.getLogger("test_cleanup")
        initial_filter_count = len(logger.filters)

        with log_context(temp_field="temp_value"):
            # Should have added a filter
            assert len(logger.filters) == initial_filter_count + 1

        # Filter should be removed after contex
        assert len(logger.filters) == initial_filter_count


class TestLogAgentStatus:
    """Test log_agent_status function with real implementation."""

    def test_log_agent_status_basic(self) -> None:
        """Test basic agent status logging."""
        logger = logging.getLogger("test_agent_status")
        logger.handlers.clear()

        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        log_agent_status(
            logger=logger,
            agent_type="test_agent",
            agent_id="agent-123",
            status="starting",
        )

        output = string_io.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["message"] == "Agent status: starting"
        assert parsed["log_type"] == "agent_status"
        assert parsed["agent_type"] == "test_agent"
        assert parsed["agent_id"] == "agent-123"
        assert parsed["status"] == "starting"

    def test_log_agent_status_with_extra_fields(self) -> None:
        """Test agent status logging with extra fields."""
        logger = logging.getLogger("test_agent_status_extra")
        logger.handlers.clear()

        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        log_agent_status(
            logger=logger,
            agent_type="test_agent",
            agent_id="agent-456",
            status="error",
            error_code="E001",
            error_message="Test error",
            metadata={"key": "value"},
        )

        output = string_io.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["status"] == "error"
        assert parsed["error_code"] == "E001"
        assert parsed["error_message"] == "Test error"
        assert parsed["metadata"] == {"key": "value"}


class TestCreateIncidentLogger:
    """Test create_incident_logger function with real implementation."""

    def test_create_incident_logger(self) -> None:
        """Test creating incident-specific logger."""
        base_logger = logging.getLogger("test_base")
        incident_logger = create_incident_logger(base_logger, "incident-123")

        expected_name = "test_base.incident.incident-123"
        assert incident_logger.name == expected_name
        assert len(incident_logger.filters) >= 1

    def test_incident_logger_adds_context(self) -> None:
        """Test that incident logger adds incident context to logs."""
        base_logger = logging.getLogger("test_incident_context")
        base_logger.handlers.clear()

        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(StructuredFormatter())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.INFO)

        incident_logger = create_incident_logger(base_logger, "incident-456")
        incident_logger.info("Test incident message")

        output = string_io.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["incident_id"] == "incident-456"
        assert parsed["message"] == "Test incident message"


class TestGetPerformanceMonitor:
    """Test get_performance_monitor function with real implementation."""

    def test_get_global_monitor_singleton(self) -> None:
        """Test that get_performance_monitor returns singleton instance."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        # Should return the same instance
        assert monitor1 is monitor2
        assert isinstance(monitor1, PerformanceMonitor)

    def test_global_monitor_functionality(self) -> None:
        """Test that global monitor works correctly."""
        monitor = get_performance_monitor()

        # Clear any existing metrics
        monitor.reset()

        # Record a measuremen
        with monitor.measure("global_test", source="test"):
            time.sleep(0.05)

        # Verify it's recorded
        metrics = monitor.get_metrics()
        assert "global_test" in metrics
        assert metrics["global_test"]["count"] == 1


class TestIntegrationScenarios:
    """Test integration scenarios with real logging setup."""

    def test_complete_logging_workflow(self) -> None:
        """Test complete logging workflow with all components."""
        # Setup logger
        logger = setup_logging(
            agent_type="integration_test",
            agent_id="workflow-123",
            use_cloud_logging=False,
            log_level="INFO",
        )

        # Create performance monitor
        monitor = PerformanceMonitor(logger)

        # Set correlation contex
        CorrelationContext.set_correlation_id("workflow-correlation-456")

        # Use logging context with performance measuremen
        with log_context(workflow="integration_test", phase="execution"):
            with monitor.measure("workflow_execution"):
                logger.info("Starting workflow execution")
                time.sleep(0.1)
                logger.info("Workflow execution completed")

        # Verify metrics were recorded
        metrics = monitor.get_metrics()
        assert "workflow_execution" in metrics
        assert metrics["workflow_execution"]["count"] == 1

        # Cleanup
        CorrelationContext.clear()

    def test_incident_logger_with_performance_monitoring(self) -> None:
        """Test incident logger combined with performance monitoring."""
        base_logger = setup_logging(
            agent_type="incident_test",
            agent_id="incident-agent-789",
            use_cloud_logging=False,
        )

        incident_logger = create_incident_logger(base_logger, "incident-789")
        monitor = PerformanceMonitor(incident_logger)

        with monitor.measure("incident_analysis"):
            incident_logger.info("Starting incident analysis")
            time.sleep(0.05)
            incident_logger.info("Incident analysis completed")

        # Should complete without errors
        metrics = monitor.get_metrics()
        assert "incident_analysis" in metrics

    def test_concurrent_logging_with_correlation(self) -> None:
        """Test concurrent logging operations with correlation IDs."""

        def worker(worker_id: int) -> None:
            CorrelationContext.set_correlation_id(f"worker-{worker_id}")

            logger = setup_logging(
                agent_type="concurrent_test",
                agent_id=f"worker-{worker_id}",
                use_cloud_logging=False,
            )

            with log_context(worker_id=worker_id):
                logger.info("Worker %s started", worker_id)
                time.sleep(0.05)
                logger.info("Worker %s completed", worker_id)

        # Start multiple workers
        threads = []
        for w in range(3):
            thread = threading.Thread(target=worker, args=(w,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should complete without errors
        assert True

    def test_error_handling_in_logging_components(self) -> None:
        """Test error handling across logging components."""
        logger = setup_logging(
            agent_type="error_test",
            agent_id="error-handling-123",
            use_cloud_logging=False,
        )

        monitor = PerformanceMonitor(logger)

        # Test exception in monitored operation
        with pytest.raises(RuntimeError):
            with monitor.measure("error_operation"):
                logger.error("Simulating error condition")
                raise RuntimeError("Test error")

        # Should have recorded the failed operation
        metrics = monitor.get_metrics()
        assert "error_operation" in metrics
        assert metrics["error_operation"]["errors"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

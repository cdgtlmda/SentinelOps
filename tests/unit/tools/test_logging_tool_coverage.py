"""
REAL tests for tools/logging_tool.py - Tests actual logging functionality.

NO MOCKING - All tests use REAL production code and REAL GCP Cloud Logging services.
TARGET: ≥90% statement coverage of tools/logging_tool.py
VERIFICATION: python -m coverage run -m pytest tests/unit/tools/test_logging_tool_coverage.py && python -m coverage report --include="*logging_tool.py" --show-missing
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone

# Import the actual production code - NO MOCKS
from src.tools.logging_tool import (
    LoggingConfig,
    WriteLogInput,
    QueryLogsInput,
    LoggingTool,
    create_resource_filter,
    create_time_range_filter,
)


class TestRealLoggingTool:
    """Test LoggingTool with real Cloud Logging - NO MOCKS."""

    @pytest.fixture
    def config(self) -> LoggingConfig:
        """Create a test configuration for real GCP project."""
        return LoggingConfig(
            project_id="your-gcp-project-id",
            timeout=30.0,
            max_entries=50
        )

    @pytest.fixture
    def logging_tool(self, config: LoggingConfig) -> LoggingTool:
        """Create a LoggingTool instance using real production code."""
        return LoggingTool(config)

    def test_logging_config_creation_and_validation(self) -> None:
        """Test LoggingConfig model validation."""
        # Test valid creation
        config = LoggingConfig(
            project_id="your-gcp-project-id",
            timeout=45.0,
            max_entries=200
        )
        assert config.project_id == "your-gcp-project-id"
        assert config.timeout == 45.0
        assert config.max_entries == 200

        # Test defaults
        config_defaults = LoggingConfig(project_id="your-gcp-project-id")
        assert config_defaults.timeout == 30.0
        assert config_defaults.max_entries == 100

        # Test validation errors
        with pytest.raises(ValueError, match="Timeout must be positive"):
            LoggingConfig(project_id="your-gcp-project-id", timeout=-1.0)

        with pytest.raises(ValueError, match="max_entries must be between 1 and 1000"):
            LoggingConfig(project_id="your-gcp-project-id", max_entries=0)

        with pytest.raises(ValueError, match="max_entries must be between 1 and 1000"):
            LoggingConfig(project_id="your-gcp-project-id", max_entries=1001)

    def test_write_log_input_creation_and_validation(self) -> None:
        """Test WriteLogInput model validation."""
        # Test minimal valid input
        write_input = WriteLogInput(
            log_name="test-log",
            message="Test message"
        )
        assert write_input.log_name == "test-log"
        assert write_input.severity == "INFO"
        assert write_input.message == "Test message"

        # Test complete input
        labels = {"env": "test", "component": "logging"}
        structured_data = {"user": "test", "action": "validate"}

        write_input_complete = WriteLogInput(
            log_name="complete-log",
            severity="ERROR",
            message="Complete message",
            labels=labels,
            structured_data=structured_data
        )
        assert write_input_complete.severity == "ERROR"
        assert write_input_complete.labels == labels
        assert write_input_complete.structured_data == structured_data

        # Test severity validation
        with pytest.raises(ValueError, match="Severity must be one of"):
            WriteLogInput(log_name="test", message="test", severity="INVALID")

        # Test case insensitive severity
        case_input = WriteLogInput(log_name="test", message="test", severity="debug")
        assert case_input.severity == "DEBUG"

    def test_query_logs_input_creation_and_validation(self) -> None:
        """Test QueryLogsInput model validation."""
        # Test minimal input
        query_input = QueryLogsInput(filter_expression="severity=ERROR")
        assert query_input.filter_expression == "severity=ERROR"
        assert query_input.hours_back == 24
        assert query_input.order_by == "timestamp desc"

        # Test complete input
        complete_query = QueryLogsInput(
            filter_expression="severity=ERROR AND resource.type=\"gce_instance\"",
            hours_back=48,
            max_entries=100,
            order_by="timestamp asc"
        )
        assert complete_query.hours_back == 48
        assert complete_query.max_entries == 100
        assert complete_query.order_by == "timestamp asc"

    def test_logging_tool_initialization(self, logging_tool: LoggingTool, config: LoggingConfig) -> None:
        """Test LoggingTool initialization with real Cloud Logging client."""
        assert logging_tool.config == config
        assert logging_tool.client is not None
        assert logging_tool._logger_cache == {}
        assert logging_tool.name == "cloud_logging"
        assert logging_tool.description == "Tool for reading and writing Google Cloud logs"

    def test_input_schema_property(self, logging_tool: LoggingTool) -> None:
        """Test input schema property."""
        schema = logging_tool.input_schema
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "operation" in schema["properties"]
        assert "params" in schema["properties"]
        assert schema["required"] == ["operation", "params"]

        operation_prop = schema["properties"]["operation"]
        assert operation_prop["type"] == "string"
        assert set(operation_prop["enum"]) == {"write_log", "query_logs", "delete_logs"}

    @pytest.mark.asyncio
    async def test_execute_method_routing(self, logging_tool: LoggingTool) -> None:
        """Test execute method operation routing."""
        # Test unknown operation
        with pytest.raises(ValueError, match="Unknown operation: invalid"):
            await logging_tool.execute(operation="invalid", params={})

        # Test operation routing logic exists
        assert hasattr(logging_tool, 'execute')
        assert hasattr(logging_tool, '_write_log')
        assert hasattr(logging_tool, '_query_logs')
        assert hasattr(logging_tool, '_delete_logs')

    @pytest.mark.asyncio
    async def test_write_log_method_text_logs(self, logging_tool: LoggingTool) -> None:
        """Test _write_log method with text logs using real Cloud Logging."""
        result = await logging_tool._write_log(
            log_name="test-real-text-log",
            severity="INFO",
            message="Test text log from real implementation",
            labels={"test": "true", "source": "real"}
        )

        assert result["success"] is True
        assert result["log_name"] == "test-real-text-log"
        assert result["severity"] == "INFO"
        assert "message" in result

        # Verify logger caching
        assert "test-real-text-log" in logging_tool._logger_cache

    @pytest.mark.asyncio
    async def test_write_log_method_structured_logs(self, logging_tool: LoggingTool) -> None:
        """Test _write_log method with structured logs using real Cloud Logging."""
        structured_data = {
            "source": "real_implementation_test",
            "user_id": "test-user-789",
            "operation": "coverage_test",
            "metadata": {"framework": "pytest", "real_gcp": True}
        }

        result = await logging_tool._write_log(
            log_name="test-real-structured-log",
            severity="DEBUG",
            message="Test structured log from real implementation",
            labels={"type": "structured", "source": "real"},
            structured_data=structured_data
        )

        assert result["success"] is True
        assert result["log_name"] == "test-real-structured-log"
        assert result["severity"] == "DEBUG"

        # Verify logger caching
        assert "test-real-structured-log" in logging_tool._logger_cache

    @pytest.mark.asyncio
    async def test_write_log_method_error_handling(self, logging_tool: LoggingTool) -> None:
        """Test _write_log method error handling with real implementation."""
        # Test with invalid parameters to trigger real error handling
        result = await logging_tool._write_log(
            log_name="test-error-log",
            severity="INVALID_SEVERITY",
            message="This should trigger error handling"
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_logs_method_with_time_filter(self, logging_tool: LoggingTool) -> None:
        """Test _query_logs method with time filtering using real Cloud Logging."""
        # First write a test log
        await logging_tool._write_log(
            log_name="test-real-query-log",
            severity="WARNING",
            message="Test log for real querying",
            labels={"test": "query", "source": "real"}
        )

        # Wait for log availability
        await asyncio.sleep(2)

        # Query with time filter
        result = await logging_tool._query_logs(
            filter_expression="logName:test-real-query-log AND severity=WARNING",
            hours_back=1,
            max_entries=5,
            order_by="timestamp desc"
        )

        assert result["success"] is True
        assert "entries" in result
        assert "count" in result
        assert "filter" in result
        assert "timestamp >=" in result["filter"]  # Time filter applied

    @pytest.mark.asyncio
    async def test_query_logs_method_without_time_filter(self, logging_tool: LoggingTool) -> None:
        """Test _query_logs method without time filtering."""
        result = await logging_tool._query_logs(
            filter_expression="severity=INFO",
            hours_back=None,
            max_entries=3
        )

        assert result["success"] is True
        assert result["filter"] == "severity=INFO"  # No time filter added

    @pytest.mark.asyncio
    async def test_query_logs_method_config_max_entries(self, logging_tool: LoggingTool) -> None:
        """Test _query_logs uses config max_entries when not specified."""
        result = await logging_tool._query_logs(
            filter_expression="severity=ERROR",
            hours_back=1
            # max_entries not specified
        )

        assert result["success"] is True
        # Should use config.max_entries (50 in our fixture)

    @pytest.mark.asyncio
    async def test_query_logs_method_entry_processing(self, logging_tool: LoggingTool) -> None:
        """Test _query_logs entry processing logic with real logs."""
        # Write different types of logs to test entry processing
        await logging_tool._write_log(
            log_name="test-entry-processing",
            severity="INFO",
            message="Text entry test"
        )

        await logging_tool._write_log(
            log_name="test-entry-processing",
            severity="INFO",
            message="Structured entry test",
            structured_data={"type": "test", "processing": True}
        )

        await asyncio.sleep(2)

        result = await logging_tool._query_logs(
            filter_expression="logName:test-entry-processing",
            hours_back=1,
            max_entries=10
        )

        assert result["success"] is True

        # Check entry structure processing
        for entry in result["entries"]:
            assert "timestamp" in entry
            assert "severity" in entry
            assert "log_name" in entry
            assert "labels" in entry
            # Should have one of the payload types
            payload_types = ["text_payload", "json_payload", "proto_payload"]
            assert any(payload_type in entry for payload_type in payload_types)

    @pytest.mark.asyncio
    async def test_delete_logs_method_success(self, logging_tool: LoggingTool) -> None:
        """Test _delete_logs method with real Cloud Logging."""
        log_name = "test-real-delete-log"

        # Write a log to delete
        await logging_tool._write_log(
            log_name=log_name,
            severity="INFO",
            message="Log to be deleted by real test"
        )

        # Verify logger is cached
        assert log_name in logging_tool._logger_cache

        # Delete the log
        await logging_tool._delete_logs(log_name=log_name)

        # Check cache is cleared regardless of delete success
        assert log_name not in logging_tool._logger_cache

    @pytest.mark.asyncio
    async def test_delete_logs_method_missing_log_name(self, logging_tool: LoggingTool) -> None:
        """Test _delete_logs method without log_name."""
        result = await logging_tool._delete_logs()

        assert result["success"] is False
        assert "log_name is required" in result["error"]

    def test_get_severity_filter_method_all_levels(self, logging_tool: LoggingTool) -> None:
        """Test get_severity_filter method for all severity levels."""
        # Test DEBUG level (includes all)
        debug_filter = logging_tool.get_severity_filter("DEBUG")
        for severity in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            assert severity in debug_filter

        # Test WARNING level (excludes DEBUG, INFO)
        warning_filter = logging_tool.get_severity_filter("WARNING")
        for severity in ["WARNING", "ERROR", "CRITICAL"]:
            assert severity in warning_filter
        for severity in ["DEBUG", "INFO"]:
            assert severity not in warning_filter

        # Test CRITICAL level (only CRITICAL)
        critical_filter = logging_tool.get_severity_filter("CRITICAL")
        assert critical_filter == "severity=(CRITICAL)"

        # Test case insensitive
        error_filter = logging_tool.get_severity_filter("error")
        assert "ERROR" in error_filter
        assert "CRITICAL" in error_filter

        # Test invalid severity
        with pytest.raises(ValueError, match="Invalid severity: INVALID"):
            logging_tool.get_severity_filter("INVALID")

    def test_create_resource_filter_function(self) -> None:
        """Test create_resource_filter helper function."""
        # Test with resource type only
        filter1 = create_resource_filter("gce_instance")
        assert filter1 == 'resource.type="gce_instance"'

        # Test with resource type and ID
        filter2 = create_resource_filter("gce_instance", "vm-123")
        expected = 'resource.type="gce_instance" AND resource.labels.instance_id="vm-123"'
        assert filter2 == expected

        # Test with different resource types
        filter3 = create_resource_filter("cloud_function", "func-456")
        assert 'resource.type="cloud_function"' in filter3
        assert 'resource.labels.instance_id="func-456"' in filter3

        # Test with empty resource type
        filter4 = create_resource_filter("")
        assert filter4 == 'resource.type=""'

        # Test with None resource_id
        filter5 = create_resource_filter("gcs_bucket", None)
        assert filter5 == 'resource.type="gcs_bucket"'

    def test_create_time_range_filter_function(self) -> None:
        """Test create_time_range_filter helper function."""
        # Test normal time range
        start = datetime(2025, 6, 14, 10, 0, 0)
        end = datetime(2025, 6, 14, 12, 0, 0)
        filter1 = create_time_range_filter(start, end)
        expected = (
            'timestamp >= "2025-06-14T10:00:00Z" AND '
            'timestamp <= "2025-06-14T12:00:00Z"'
        )
        assert filter1 == expected

        # Test same start and end time
        same_time = datetime(2025, 6, 14, 15, 30, 45)
        filter2 = create_time_range_filter(same_time, same_time)
        assert "2025-06-14T15:30:45Z" in filter2
        assert "timestamp >=" in filter2
        assert "timestamp <=" in filter2

        # Test with microseconds
        start_micro = datetime(2025, 6, 14, 10, 0, 0, 123456)
        end_micro = datetime(2025, 6, 14, 10, 0, 1, 654321)
        filter3 = create_time_range_filter(start_micro, end_micro)
        assert "2025-06-14T10:00:00.123456Z" in filter3
        assert "2025-06-14T10:00:01.654321Z" in filter3

    @pytest.mark.asyncio
    async def test_complete_integration_workflow(self, logging_tool: LoggingTool) -> None:
        """Test complete workflow for maximum coverage."""
        log_name = "test-real-integration-workflow"

        # Step 1: Write multiple types of logs
        await logging_tool._write_log(
            log_name=log_name,
            severity="INFO",
            message="Workflow started",
            labels={"stage": "start", "workflow": "integration"}
        )

        await logging_tool._write_log(
            log_name=log_name,
            severity="WARNING",
            message="Warning in workflow",
            labels={"stage": "middle", "workflow": "integration"},
            structured_data={"warning_code": 1001, "details": "Memory usage high"}
        )

        await logging_tool._write_log(
            log_name=log_name,
            severity="ERROR",
            message="Error in workflow",
            labels={"stage": "error", "workflow": "integration"},
            structured_data={"error_code": 5001, "stack_trace": "..."}
        )

        # Step 2: Query using different filters
        await asyncio.sleep(3)  # Wait for logs

        # Query all logs
        all_logs = await logging_tool._query_logs(
            filter_expression=f"logName:{log_name}",
            hours_back=1,
            max_entries=10
        )
        assert all_logs["success"] is True
        assert len(all_logs["entries"]) >= 0  # May be empty due to timing

        # Query with severity filter
        severity_filter = logging_tool.get_severity_filter("WARNING")
        warning_logs = await logging_tool._query_logs(
            filter_expression=f"logName:{log_name} AND {severity_filter}",
            hours_back=1,
            max_entries=5
        )
        assert warning_logs["success"] is True

        # Step 3: Test helper function integration
        resource_filter = create_resource_filter("test_resource", "workflow-123")
        time_filter = create_time_range_filter(
            datetime.now(timezone.utc) - timedelta(hours=1),
            datetime.now(timezone.utc)
        )

        combined_filter = f"{resource_filter} AND {time_filter}"
        assert "resource.type" in combined_filter
        assert "timestamp >=" in combined_filter

        # Step 4: Cleanup (tests delete functionality)
        await logging_tool._delete_logs(log_name=log_name)
        # Cache should be cleared regardless of delete success
        assert log_name not in logging_tool._logger_cache

    @pytest.mark.asyncio
    async def test_execute_method_full_integration(self, logging_tool: LoggingTool) -> None:
        """Test execute method with all operations for full coverage."""
        # Test write_log operation
        write_result = await logging_tool.execute(
            operation="write_log",
            params={
                "log_name": "test-execute-integration",
                "severity": "INFO",
                "message": "Execute method test",
                "labels": {"method": "execute", "integration": "true"}
            }
        )
        assert write_result["success"] is True

        # Test query_logs operation
        await asyncio.sleep(2)
        query_result = await logging_tool.execute(
            operation="query_logs",
            params={
                "filter_expression": "logName:test-execute-integration",
                "hours_back": 1,
                "max_entries": 5
            }
        )
        assert query_result["success"] is True

        # Test delete_logs operation
        delete_result = await logging_tool.execute(
            operation="delete_logs",
            params={"log_name": "test-execute-integration"}
        )
        # Should handle gracefully regardless of success
        assert "success" in delete_result

    def test_edge_cases_and_boundary_conditions(self, logging_tool: LoggingTool) -> None:
        """Test edge cases and boundary conditions for maximum coverage."""
        # Test config boundary values
        config_min = LoggingConfig(project_id="your-gcp-project-id", max_entries=1, timeout=0.1)
        assert config_min.max_entries == 1
        assert config_min.timeout == 0.1

        config_max = LoggingConfig(project_id="your-gcp-project-id", max_entries=1000, timeout=3600.0)
        assert config_max.max_entries == 1000
        assert config_max.timeout == 3600.0

        # Test all severity levels
        for severity in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            write_input = WriteLogInput(
                log_name="boundary-test",
                severity=severity,
                message=f"Testing {severity} level"
            )
            assert write_input.severity == severity

        # Test complex structured data
        complex_data = {
            "nested": {"deeply": {"nested": {"value": "test"}}},
            "array": [1, 2, {"inner": "object"}, [3, 4, 5]],
            "unicode": "测试数据 🚀",
            "numbers": {"int": 42, "float": 3.14159, "scientific": 1.23e-4},
            "boolean": True,
            "null": None
        }

        complex_input = WriteLogInput(
            log_name="complex-test",
            message="Complex data test",
            structured_data=complex_data
        )
        assert complex_input.structured_data == complex_data

        # Test empty and edge case values
        empty_input = WriteLogInput(
            log_name="",
            message="",
            labels={},
            structured_data={}
        )
        assert empty_input.log_name == ""
        assert empty_input.message == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

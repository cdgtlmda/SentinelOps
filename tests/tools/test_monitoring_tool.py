"""Tests for Cloud Monitoring tool.

This test module verifies the Cloud Monitoring tool functionality using real GCP services.
All tests use actual Google Cloud Monitoring API calls - NO MOCKING.
"""

import asyncio
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.tools.monitoring_tool import (
    MonitoringTool,
    MonitoringConfig,
    WriteMetricInput,
    QueryMetricsInput,
    CreateAlertInput,
    UptimeCheckInput,
    create_metric_filter,
    create_resource_filter,
)


class TestMonitoringConfig:
    """Test MonitoringConfig model."""

    def test_valid_config(self) -> None:
        """Test creating valid monitoring configuration."""
        config = MonitoringConfig(
            project_id="your-gcp-project-id", timeout=30.0, max_results=100
        )
        assert config.project_id == "your-gcp-project-id"
        assert config.timeout == 30.0
        assert config.max_results == 100

    def test_config_defaults(self) -> None:
        """Test default configuration values."""
        config = MonitoringConfig(project_id="your-gcp-project-id")
        assert config.project_id == "your-gcp-project-id"
        assert config.timeout == 30.0
        assert config.max_results == 100

    def test_invalid_timeout(self) -> None:
        """Test validation of invalid timeout."""
        with pytest.raises(ValidationError) as exc_info:
            MonitoringConfig(project_id="your-gcp-project-id", timeout=-1.0)
        assert "Timeout must be positive" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MonitoringConfig(project_id="your-gcp-project-id", timeout=0.0)
        assert "Timeout must be positive" in str(exc_info.value)

    def test_invalid_max_results(self) -> None:
        """Test validation of invalid max_results."""
        with pytest.raises(ValidationError) as exc_info:
            MonitoringConfig(project_id="your-gcp-project-id", max_results=0)
        assert "max_results must be between 1 and 1000" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MonitoringConfig(
                project_id="your-gcp-project-id", max_results=1001
            )
        assert "max_results must be between 1 and 1000" in str(exc_info.value)


class TestInputModels:
    """Test input model validation."""

    def test_write_metric_input_valid(self) -> None:
        """Test valid WriteMetricInput."""
        input_data = WriteMetricInput(
            metric_type="custom.googleapis.com/test_metric",
            value=42.5,
            labels={"environment": "test"},
            resource_type="global",
            resource_labels={"project_id": "your-gcp-project-id"},
        )
        assert input_data.metric_type == "custom.googleapis.com/test_metric"
        assert input_data.value == 42.5
        assert input_data.labels == {"environment": "test"}
        assert input_data.resource_type == "global"

    def test_write_metric_input_defaults(self) -> None:
        """Test WriteMetricInput with defaults."""
        input_data = WriteMetricInput(
            metric_type="custom.googleapis.com/test_metric", value=100
        )
        assert input_data.metric_type == "custom.googleapis.com/test_metric"
        assert input_data.value == 100
        assert input_data.labels is None
        assert input_data.resource_type == "global"
        assert input_data.resource_labels is None

    def test_query_metrics_input_valid(self) -> None:
        """Test valid QueryMetricsInput."""
        input_data = QueryMetricsInput(
            metric_type="compute.googleapis.com/instance/cpu/utilization",
            hours_back=2,
            aggregation_alignment_period=300,
            aggregation_per_series_aligner="ALIGN_MAX",
            filter='resource.label.zone="us-central1-a"',
        )
        assert (
            input_data.metric_type == "compute.googleapis.com/instance/cpu/utilization"
        )
        assert input_data.hours_back == 2
        assert input_data.aggregation_alignment_period == 300
        assert input_data.aggregation_per_series_aligner == "ALIGN_MAX"
        assert input_data.filter == 'resource.label.zone="us-central1-a"'

    def test_query_metrics_input_defaults(self) -> None:
        """Test QueryMetricsInput with defaults."""
        input_data = QueryMetricsInput(
            metric_type="compute.googleapis.com/instance/cpu/utilization"
        )
        assert input_data.hours_back == 1
        assert input_data.aggregation_alignment_period == 60
        assert input_data.aggregation_per_series_aligner == "ALIGN_MEAN"
        assert input_data.filter is None

    def test_create_alert_input_valid(self) -> None:
        """Test valid CreateAlertInput."""
        input_data = CreateAlertInput(
            display_name="Test Alert",
            metric_type="compute.googleapis.com/instance/cpu/utilization",
            threshold_value=0.8,
            comparison_type="COMPARISON_GT",
            duration=300,
            notification_channels=["projects/test/notificationChannels/123"],
        )
        assert input_data.display_name == "Test Alert"
        assert input_data.threshold_value == 0.8
        assert input_data.comparison_type == "COMPARISON_GT"
        assert input_data.duration == 300

    def test_create_alert_input_validation(self) -> None:
        """Test CreateAlertInput validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateAlertInput(
                display_name="Test Alert",
                metric_type="compute.googleapis.com/instance/cpu/utilization",
                threshold_value=0.8,
                comparison_type="INVALID_COMPARISON",
            )
        assert "Comparison type must be one of" in str(exc_info.value)

    def test_uptime_check_input_valid(self) -> None:
        """Test valid UptimeCheckInput."""
        input_data = UptimeCheckInput(
            display_name="Test Uptime Check",
            host="example.com",
            path="/health",
            port=80,
            use_ssl=False,
            check_interval=300,
        )
        assert input_data.display_name == "Test Uptime Check"
        assert input_data.host == "example.com"
        assert input_data.path == "/health"
        assert input_data.port == 80
        assert input_data.use_ssl is False
        assert input_data.check_interval == 300

    def test_uptime_check_input_defaults(self) -> None:
        """Test UptimeCheckInput with defaults."""
        input_data = UptimeCheckInput(
            display_name="Test Uptime Check", host="example.com"
        )
        assert input_data.monitored_resource_type == "uptime_url"
        assert input_data.path == "/"
        assert input_data.port == 443
        assert input_data.use_ssl is True
        assert input_data.check_interval == 60


class TestMonitoringTool:
    """Test MonitoringTool functionality with real GCP services."""

    @pytest.fixture
    def config(self) -> MonitoringConfig:
        """Create monitoring configuration."""
        return MonitoringConfig(
            project_id="your-gcp-project-id", timeout=30.0, max_results=50
        )

    @pytest.fixture
    def monitoring_tool(self, config: MonitoringConfig) -> MonitoringTool:
        """Create MonitoringTool instance."""
        return MonitoringTool(config)

    def test_tool_initialization(self, monitoring_tool: MonitoringTool) -> None:
        """Test MonitoringTool initialization."""
        assert monitoring_tool.name == "cloud_monitoring"
        assert "Tool for metrics, alerts, and monitoring" in monitoring_tool.description
        assert monitoring_tool.config.project_id == "your-gcp-project-id"
        assert monitoring_tool.project_path == "projects/your-gcp-project-id"

        # Verify clients are initialized
        assert monitoring_tool.client is not None
        assert monitoring_tool.alert_client is not None
        assert monitoring_tool.uptime_client is not None

    def test_input_schema(self, monitoring_tool: MonitoringTool) -> None:
        """Test tool input schema definition."""
        schema = monitoring_tool.input_schema
        assert schema["type"] == "object"
        assert "operation" in schema["properties"]
        assert "params" in schema["properties"]

        # Check valid operations
        valid_operations = schema["properties"]["operation"]["enum"]
        expected_operations = [
            "write_metric",
            "query_metrics",
            "create_alert",
            "list_alerts",
            "create_uptime_check",
            "list_uptime_checks",
        ]
        assert set(valid_operations) == set(expected_operations)

    @pytest.mark.asyncio
    async def test_execute_invalid_operation(self, monitoring_tool: MonitoringTool) -> None:
        """Test execute with invalid operation."""
        result = await monitoring_tool.execute(operation="invalid_operation", params={})
        assert "Unknown operation: invalid_operation" in str(result)

    @pytest.mark.asyncio
    async def test_write_metric_success(self, monitoring_tool: MonitoringTool) -> None:
        """Test writing a custom metric successfully."""
        params = {
            "metric_type": "custom.googleapis.com/sentinelops_test_metric",
            "value": 123.45,
            "labels": {"environment": "test", "component": "monitoring_tool"},
            "resource_type": "global",
            "resource_labels": {"project_id": "your-gcp-project-id"},
        }

        result = await monitoring_tool.execute(operation="write_metric", params=params)

        assert result["success"] is True
        assert result["metric_type"] == "custom.googleapis.com/sentinelops_test_metric"
        assert result["value"] == 123.45
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_write_metric_minimal(self, monitoring_tool: MonitoringTool) -> None:
        """Test writing metric with minimal parameters."""
        params = {
            "metric_type": "custom.googleapis.com/sentinelops_minimal_test",
            "value": 1,
        }

        result = await monitoring_tool.execute(operation="write_metric", params=params)

        assert result["success"] is True
        assert result["metric_type"] == "custom.googleapis.com/sentinelops_minimal_test"
        assert result["value"] == 1

    @pytest.mark.asyncio
    async def test_write_metric_invalid_params(self, monitoring_tool: MonitoringTool) -> None:
        """Test writing metric with invalid parameters."""
        # Missing required parameters
        result = await monitoring_tool.execute(operation="write_metric", params={})

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_metrics_success(self, monitoring_tool: MonitoringTool) -> None:
        """Test querying metrics successfully."""
        # First write a metric to ensure we have data
        write_params = {
            "metric_type": "custom.googleapis.com/sentinelops_query_test",
            "value": 50,
        }
        await monitoring_tool.execute(operation="write_metric", params=write_params)

        # Wait a moment for metric to be available
        await asyncio.sleep(2)

        # Query the metric
        query_params = {
            "metric_type": "custom.googleapis.com/sentinelops_query_test",
            "hours_back": 1,
            "aggregation_alignment_period": 60,
            "aggregation_per_series_aligner": "ALIGN_MEAN",
        }

        result = await monitoring_tool.execute(
            operation="query_metrics", params=query_params
        )

        assert result["success"] is True
        assert "series_count" in result
        assert "time_series" in result
        assert isinstance(result["time_series"], list)

    @pytest.mark.asyncio
    async def test_query_metrics_with_filter(self, monitoring_tool: MonitoringTool) -> None:
        """Test querying metrics with additional filter."""
        query_params = {
            "metric_type": "custom.googleapis.com/sentinelops_query_test",
            "hours_back": 1,
            "filter": 'resource.type="global"',
        }

        result = await monitoring_tool.execute(
            operation="query_metrics", params=query_params
        )

        assert result["success"] is True
        assert "time_series" in result

    @pytest.mark.asyncio
    async def test_list_alerts(self, monitoring_tool: MonitoringTool) -> None:
        """Test listing alert policies."""
        result = await monitoring_tool.execute(operation="list_alerts", params={})

        assert result["success"] is True
        assert "count" in result
        assert "alert_policies" in result
        assert isinstance(result["alert_policies"], list)

    @pytest.mark.asyncio
    async def test_list_uptime_checks(self, monitoring_tool: MonitoringTool) -> None:
        """Test listing uptime checks."""
        result = await monitoring_tool.execute(
            operation="list_uptime_checks", params={}
        )

        assert result["success"] is True
        assert "count" in result
        assert "uptime_checks" in result
        assert isinstance(result["uptime_checks"], list)

    @pytest.mark.asyncio
    async def test_create_alert_success(self, monitoring_tool: MonitoringTool) -> None:
        """Test creating an alert policy successfully."""
        # Use a timestamp to ensure unique alert name
        timestamp = int(datetime.now().timestamp())
        params = {
            "display_name": f"SentinelOps Test Alert {timestamp}",
            "metric_type": "custom.googleapis.com/sentinelops_test_metric",
            "threshold_value": 100.0,
            "comparison_type": "COMPARISON_GT",
            "duration": 60,
        }

        result = await monitoring_tool.execute(operation="create_alert", params=params)

        assert result["success"] is True
        assert "alert_policy_id" in result
        assert result["display_name"] == f"SentinelOps Test Alert {timestamp}"
        assert "enabled" in result

    @pytest.mark.asyncio
    async def test_create_uptime_check_success(self, monitoring_tool: MonitoringTool) -> None:
        """Test creating an uptime check successfully."""
        # Use a timestamp to ensure unique check name
        timestamp = int(datetime.now().timestamp())
        params = {
            "display_name": f"SentinelOps Test Uptime {timestamp}",
            "host": "httpbin.org",
            "path": "/status/200",
            "port": 443,
            "use_ssl": True,
            "check_interval": 300,
        }

        result = await monitoring_tool.execute(
            operation="create_uptime_check", params=params
        )

        assert result["success"] is True
        assert "uptime_check_id" in result
        assert result["display_name"] == f"SentinelOps Test Uptime {timestamp}"
        assert result["host"] == "httpbin.org"
        assert result["path"] == "/status/200"


class TestHelperFunctions:
    """Test helper functions."""

    def test_create_metric_filter_basic(self) -> None:
        """Test basic metric filter creation."""
        filter_expr = create_metric_filter("custom.googleapis.com/test_metric")
        assert filter_expr == 'metric.type="custom.googleapis.com/test_metric"'

    def test_create_metric_filter_with_resource(self) -> None:
        """Test metric filter with resource type."""
        filter_expr = create_metric_filter(
            "custom.googleapis.com/test_metric", resource_type="global"
        )
        expected = (
            'metric.type="custom.googleapis.com/test_metric" AND resource.type="global"'
        )
        assert filter_expr == expected

    def test_create_metric_filter_with_labels(self) -> None:
        """Test metric filter with labels."""
        filter_expr = create_metric_filter(
            "custom.googleapis.com/test_metric",
            labels={"environment": "test", "version": "1.0"},
        )
        assert 'metric.type="custom.googleapis.com/test_metric"' in filter_expr
        assert 'metric.label.environment="test"' in filter_expr
        assert 'metric.label.version="1.0"' in filter_expr
        assert filter_expr.count(" AND ") == 2

    def test_create_metric_filter_complete(self) -> None:
        """Test metric filter with all parameters."""
        filter_expr = create_metric_filter(
            "custom.googleapis.com/test_metric",
            resource_type="gce_instance",
            labels={"environment": "prod"},
        )
        expected_parts = [
            'metric.type="custom.googleapis.com/test_metric"',
            'resource.type="gce_instance"',
            'metric.label.environment="prod"',
        ]
        for part in expected_parts:
            assert part in filter_expr

    def test_create_resource_filter_basic(self) -> None:
        """Test basic resource filter creation."""
        filter_expr = create_resource_filter("gce_instance")
        assert filter_expr == 'resource.type="gce_instance"'

    def test_create_resource_filter_with_labels(self) -> None:
        """Test resource filter with labels."""
        filter_expr = create_resource_filter(
            "gce_instance", labels={"zone": "us-central1-a", "instance_id": "123"}
        )
        assert 'resource.type="gce_instance"' in filter_expr
        assert 'resource.label.zone="us-central1-a"' in filter_expr
        assert 'resource.label.instance_id="123"' in filter_expr
        assert filter_expr.count(" AND ") == 2

    def test_create_resource_filter_empty_labels(self) -> None:
        """Test resource filter with empty labels."""
        filter_expr = create_resource_filter("global", labels={})
        assert filter_expr == 'resource.type="global"'

    def test_create_resource_filter_none_labels(self) -> None:
        """Test resource filter with None labels."""
        filter_expr = create_resource_filter("global", labels=None)
        assert filter_expr == 'resource.type="global"'


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def monitoring_tool(self) -> MonitoringTool:
        """Create MonitoringTool instance."""
        config = MonitoringConfig(project_id="your-gcp-project-id")
        return MonitoringTool(config)

    @pytest.mark.asyncio
    async def test_write_metric_very_large_value(self, monitoring_tool: MonitoringTool) -> None:
        """Test writing metric with very large value."""
        params = {
            "metric_type": "custom.googleapis.com/large_value_test",
            "value": 1e10,  # Very large number
        }

        result = await monitoring_tool.execute(operation="write_metric", params=params)

        assert result["success"] is True
        assert result["value"] == 1e10

    @pytest.mark.asyncio
    async def test_write_metric_negative_value(self, monitoring_tool: MonitoringTool) -> None:
        """Test writing metric with negative value."""
        params = {
            "metric_type": "custom.googleapis.com/negative_value_test",
            "value": -42.5,
        }

        result = await monitoring_tool.execute(operation="write_metric", params=params)

        assert result["success"] is True
        assert result["value"] == -42.5

    @pytest.mark.asyncio
    async def test_write_metric_zero_value(self, monitoring_tool: MonitoringTool) -> None:
        """Test writing metric with zero value."""
        params = {"metric_type": "custom.googleapis.com/zero_value_test", "value": 0}

        result = await monitoring_tool.execute(operation="write_metric", params=params)

        assert result["success"] is True
        assert result["value"] == 0

    @pytest.mark.asyncio
    async def test_query_metrics_long_timeframe(self, monitoring_tool: MonitoringTool) -> None:
        """Test querying metrics with long timeframe."""
        query_params = {
            "metric_type": "custom.googleapis.com/sentinelops_test_metric",
            "hours_back": 24,  # 24 hours back
            "aggregation_alignment_period": 3600,  # 1 hour alignment
        }

        result = await monitoring_tool.execute(
            operation="query_metrics", params=query_params
        )

        assert result["success"] is True
        assert "time_series" in result

    @pytest.mark.asyncio
    async def test_write_metric_unicode_labels(self, monitoring_tool: MonitoringTool) -> None:
        """Test writing metric with Unicode labels."""
        params = {
            "metric_type": "custom.googleapis.com/unicode_test",
            "value": 1,
            "labels": {
                "description": "测试metric with 🚀 emoji",
                "location": "São Paulo",
            },
        }

        result = await monitoring_tool.execute(operation="write_metric", params=params)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_alert_all_comparison_types(self, monitoring_tool: MonitoringTool) -> None:
        """Test creating alerts with all comparison types."""
        comparison_types = [
            "COMPARISON_GT",
            "COMPARISON_LT",
            "COMPARISON_GE",
            "COMPARISON_LE",
            "COMPARISON_EQ",
            "COMPARISON_NE",
        ]

        for comparison in comparison_types:
            timestamp = int(datetime.now().timestamp())
            params = {
                "display_name": f"Test Alert {comparison} {timestamp}",
                "metric_type": "custom.googleapis.com/sentinelops_test_metric",
                "threshold_value": 50.0,
                "comparison_type": comparison,
                "duration": 60,
            }

            result = await monitoring_tool.execute(
                operation="create_alert", params=params
            )

            assert (
                result["success"] is True
            ), f"Failed for comparison type: {comparison}"

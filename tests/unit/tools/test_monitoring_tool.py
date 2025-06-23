"""Tests for tools/monitoring_tool.py using real Google Cloud Monitoring services.

This module tests the Cloud Monitoring tool implementation with real GCP services.
NO MOCKING - all tests use actual Google Cloud Monitoring APIs.
"""

import pytest
import asyncio
from datetime import datetime

from src.tools.monitoring_tool import (
    MonitoringConfig,
    WriteMetricInput,
    QueryMetricsInput,
    CreateAlertInput,
    UptimeCheckInput,
    MonitoringTool,
    create_metric_filter,
    create_resource_filter,
)
from pydantic import ValidationError


class TestMonitoringConfig:
    """Test MonitoringConfig class validation and functionality."""

    def test_valid_config_creation(self) -> None:
        """Test creating a valid MonitoringConfig."""
        config = MonitoringConfig(
            project_id="your-gcp-project-id",
            timeout=30.0,
            max_results=100
        )
        assert config.project_id == "your-gcp-project-id"
        assert config.timeout == 30.0
        assert config.max_results == 100

    def test_config_with_defaults(self) -> None:
        """Test MonitoringConfig with default values."""
        config = MonitoringConfig(project_id="your-gcp-project-id")
        assert config.project_id == "your-gcp-project-id"
        assert config.timeout == 30.0
        assert config.max_results == 100

    def test_invalid_timeout_validation(self) -> None:
        """Test validation of invalid timeout values."""
        with pytest.raises(ValidationError) as exc_info:
            MonitoringConfig(
                project_id="your-gcp-project-id",
                timeout=0
            )
        assert "Timeout must be positive" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MonitoringConfig(
                project_id="your-gcp-project-id",
                timeout=-5.0
            )
        assert "Timeout must be positive" in str(exc_info.value)

    def test_invalid_max_results_validation(self) -> None:
        """Test validation of invalid max_results values."""
        with pytest.raises(ValidationError) as exc_info:
            MonitoringConfig(
                project_id="your-gcp-project-id",
                max_results=0
            )
        assert "max_results must be between 1 and 1000" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MonitoringConfig(
                project_id="your-gcp-project-id",
                max_results=1001
            )
        assert "max_results must be between 1 and 1000" in str(exc_info.value)


class TestWriteMetricInput:
    """Test WriteMetricInput validation and functionality."""

    def test_valid_metric_input_creation(self) -> None:
        """Test creating a valid WriteMetricInput."""
        metric_input = WriteMetricInput(
            metric_type="custom.googleapis.com/test_metric",
            value=42.5,
            labels={"environment": "test", "component": "api"},
            resource_type="gce_instance",
            resource_labels={"instance_id": "test-instance"}
        )
        assert metric_input.metric_type == "custom.googleapis.com/test_metric"
        assert metric_input.value == 42.5
        assert metric_input.labels == {"environment": "test", "component": "api"}
        assert metric_input.resource_type == "gce_instance"
        assert metric_input.resource_labels == {"instance_id": "test-instance"}

    def test_metric_input_with_defaults(self) -> None:
        """Test WriteMetricInput with default values."""
        metric_input = WriteMetricInput(
            metric_type="custom.googleapis.com/test_metric",
            value=100
        )
        assert metric_input.metric_type == "custom.googleapis.com/test_metric"
        assert metric_input.value == 100
        assert metric_input.labels is None
        assert metric_input.resource_type == "global"
        assert metric_input.resource_labels is None

    def test_metric_input_integer_value(self) -> None:
        """Test WriteMetricInput with integer value."""
        metric_input = WriteMetricInput(
            metric_type="custom.googleapis.com/counter",
            value=10
        )
        assert metric_input.value == 10
        assert isinstance(metric_input.value, int)

    def test_metric_input_float_value(self) -> None:
        """Test WriteMetricInput with float value."""
        metric_input = WriteMetricInput(
            metric_type="custom.googleapis.com/gauge",
            value=15.75
        )
        assert metric_input.value == 15.75
        assert isinstance(metric_input.value, float)


class TestQueryMetricsInput:
    """Test QueryMetricsInput validation and functionality."""

    def test_valid_query_input_creation(self) -> None:
        """Test creating a valid QueryMetricsInput."""
        query_input = QueryMetricsInput(
            metric_type="custom.googleapis.com/test_metric",
            hours_back=2,
            aggregation_alignment_period=120,
            aggregation_per_series_aligner="ALIGN_MAX",
            filter='resource.label.zone="us-central1-a"'
        )
        assert query_input.metric_type == "custom.googleapis.com/test_metric"
        assert query_input.hours_back == 2
        assert query_input.aggregation_alignment_period == 120
        assert query_input.aggregation_per_series_aligner == "ALIGN_MAX"
        assert query_input.filter == 'resource.label.zone="us-central1-a"'

    def test_query_input_with_defaults(self) -> None:
        """Test QueryMetricsInput with default values."""
        query_input = QueryMetricsInput(
            metric_type="custom.googleapis.com/test_metric"
        )
        assert query_input.metric_type == "custom.googleapis.com/test_metric"
        assert query_input.hours_back == 1
        assert query_input.aggregation_alignment_period == 60
        assert query_input.aggregation_per_series_aligner == "ALIGN_MEAN"
        assert query_input.filter is None


class TestCreateAlertInput:
    """Test CreateAlertInput validation and functionality."""

    def test_valid_alert_input_creation(self) -> None:
        """Test creating a valid CreateAlertInput."""
        alert_input = CreateAlertInput(
            display_name="Test Alert",
            metric_type="custom.googleapis.com/error_rate",
            threshold_value=0.05,
            comparison_type="COMPARISON_GT",
            duration=300,
            notification_channels=["projects/test/notificationChannels/123"]
        )
        assert alert_input.display_name == "Test Alert"
        assert alert_input.metric_type == "custom.googleapis.com/error_rate"
        assert alert_input.threshold_value == 0.05
        assert alert_input.comparison_type == "COMPARISON_GT"
        assert alert_input.duration == 300
        assert alert_input.notification_channels == ["projects/test/notificationChannels/123"]

    def test_alert_input_with_defaults(self) -> None:
        """Test CreateAlertInput with default values."""
        alert_input = CreateAlertInput(
            display_name="Default Alert",
            metric_type="custom.googleapis.com/test_metric",
            threshold_value=10.0
        )
        assert alert_input.display_name == "Default Alert"
        assert alert_input.metric_type == "custom.googleapis.com/test_metric"
        assert alert_input.threshold_value == 10.0
        assert alert_input.comparison_type == "COMPARISON_GT"
        assert alert_input.duration == 60
        assert alert_input.notification_channels is None

    def test_invalid_comparison_type_validation(self) -> None:
        """Test validation of invalid comparison types."""
        with pytest.raises(ValidationError) as exc_info:
            CreateAlertInput(
                display_name="Invalid Alert",
                metric_type="custom.googleapis.com/test_metric",
                threshold_value=1.0,
                comparison_type="INVALID_COMPARISON"
            )
        assert "Comparison type must be one of" in str(exc_info.value)

    def test_valid_comparison_types(self) -> None:
        """Test all valid comparison types."""
        valid_types = [
            "COMPARISON_GT",
            "COMPARISON_LT",
            "COMPARISON_GE",
            "COMPARISON_LE",
            "COMPARISON_EQ",
            "COMPARISON_NE"
        ]

        for comparison_type in valid_types:
            alert_input = CreateAlertInput(
                display_name=f"Alert {comparison_type}",
                metric_type="custom.googleapis.com/test_metric",
                threshold_value=1.0,
                comparison_type=comparison_type
            )
            assert alert_input.comparison_type == comparison_type


class TestUptimeCheckInput:
    """Test UptimeCheckInput validation and functionality."""

    def test_valid_uptime_check_input_creation(self) -> None:
        """Test creating a valid UptimeCheckInput."""
        uptime_input = UptimeCheckInput(
            display_name="Test Uptime Check",
            monitored_resource_type="uptime_url",
            host="example.com",
            path="/api/health",
            port=8080,
            use_ssl=False,
            check_interval=120
        )
        assert uptime_input.display_name == "Test Uptime Check"
        assert uptime_input.monitored_resource_type == "uptime_url"
        assert uptime_input.host == "example.com"
        assert uptime_input.path == "/api/health"
        assert uptime_input.port == 8080
        assert uptime_input.use_ssl is False
        assert uptime_input.check_interval == 120

    def test_uptime_check_input_with_defaults(self) -> None:
        """Test UptimeCheckInput with default values."""
        uptime_input = UptimeCheckInput(
            display_name="Default Uptime Check",
            host="api.example.com"
        )
        assert uptime_input.display_name == "Default Uptime Check"
        assert uptime_input.monitored_resource_type == "uptime_url"
        assert uptime_input.host == "api.example.com"
        assert uptime_input.path == "/"
        assert uptime_input.port == 443
        assert uptime_input.use_ssl is True
        assert uptime_input.check_interval == 60


class TestMonitoringTool:
    """Test MonitoringTool class using real Google Cloud Monitoring services."""

    @pytest.fixture
    def monitoring_config(self) -> MonitoringConfig:
        """Create a test MonitoringConfig."""
        return MonitoringConfig(
            project_id="your-gcp-project-id",
            timeout=30.0,
            max_results=50
        )

    @pytest.fixture
    def monitoring_tool(self, monitoring_config: MonitoringConfig) -> MonitoringTool:
        """Create a MonitoringTool instance."""
        return MonitoringTool(monitoring_config)

    def test_monitoring_tool_initialization(self, monitoring_tool: MonitoringTool, monitoring_config: MonitoringConfig) -> None:
        """Test MonitoringTool initialization."""
        assert monitoring_tool.name == "cloud_monitoring"
        assert "Tool for metrics, alerts, and monitoring" in monitoring_tool.description
        assert monitoring_tool.config == monitoring_config
        assert monitoring_tool.project_path == "projects/your-gcp-project-id"
        assert monitoring_tool.client is not None
        assert monitoring_tool.alert_client is not None
        assert monitoring_tool.uptime_client is not None

    def test_input_schema(self, monitoring_tool: MonitoringTool) -> None:
        """Test the input schema definition."""
        schema = monitoring_tool.input_schema
        assert schema["type"] == "object"
        assert "operation" in schema["properties"]
        assert "params" in schema["properties"]
        assert schema["required"] == ["operation", "params"]

        operation_schema = schema["properties"]["operation"]
        assert operation_schema["type"] == "string"
        expected_operations = [
            "write_metric",
            "query_metrics",
            "create_alert",
            "list_alerts",
            "create_uptime_check",
            "list_uptime_checks"
        ]
        assert set(operation_schema["enum"]) == set(expected_operations)

    @pytest.mark.asyncio
    async def test_write_metric_success(self, monitoring_tool: MonitoringTool) -> None:
        """Test successful metric writing to real Cloud Monitoring."""
        test_metric_type = f"custom.googleapis.com/test_metric_{int(datetime.now().timestamp())}"

        result = await monitoring_tool.execute(
            operation="write_metric",
            params={
                "metric_type": test_metric_type,
                "value": 42.5,
                "labels": {"test": "true", "component": "monitoring_tool"},
                "resource_type": "global"
            }
        )

        assert result["success"] is True
        assert result["metric_type"] == test_metric_type
        assert result["value"] == 42.5
        assert "timestamp" in result

        # Verify timestamp format
        timestamp_str = result["timestamp"]
        parsed_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        assert isinstance(parsed_timestamp, datetime)

    @pytest.mark.asyncio
    async def test_write_metric_with_resource_labels(self, monitoring_tool: MonitoringTool) -> None:
        """Test metric writing with resource labels."""
        test_metric_type = f"custom.googleapis.com/resource_test_{int(datetime.now().timestamp())}"

        result = await monitoring_tool.execute(
            operation="write_metric",
            params={
                "metric_type": test_metric_type,
                "value": 100,
                "resource_type": "gce_instance",
                "resource_labels": {
                    "instance_id": "test-instance-123",
                    "zone": "us-central1-a"
                }
            }
        )

        assert result["success"] is True
        assert result["metric_type"] == test_metric_type
        assert result["value"] == 100

    @pytest.mark.asyncio
    async def test_write_metric_validation_error(self, monitoring_tool: MonitoringTool) -> None:
        """Test metric writing with validation errors."""
        result = await monitoring_tool.execute(
            operation="write_metric",
            params={
                # Missing required metric_type
                "value": 42.5
            }
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_query_metrics_basic(self, monitoring_tool: MonitoringTool) -> None:
        """Test basic metrics querying."""
        # First write a metric to query
        test_metric_type = f"custom.googleapis.com/query_test_{int(datetime.now().timestamp())}"

        await monitoring_tool.execute(
            operation="write_metric",
            params={
                "metric_type": test_metric_type,
                "value": 75.0,
                "resource_type": "global"
            }
        )

        # Wait a moment for metric to be available
        await asyncio.sleep(2)

        # Query the metric
        result = await monitoring_tool.execute(
            operation="query_metrics",
            params={
                "metric_type": test_metric_type,
                "hours_back": 1
            }
        )

        assert result["success"] is True
        assert "series_count" in result
        assert "time_series" in result
        assert isinstance(result["time_series"], list)

    @pytest.mark.asyncio
    async def test_query_metrics_with_aggregation(self, monitoring_tool: MonitoringTool) -> None:
        """Test metrics querying with custom aggregation."""
        test_metric_type = f"custom.googleapis.com/agg_test_{int(datetime.now().timestamp())}"

        # Write multiple metric points
        for i in range(3):
            await monitoring_tool.execute(
                operation="write_metric",
                params={
                    "metric_type": test_metric_type,
                    "value": float(i * 10),
                    "resource_type": "global"
                }
            )
            await asyncio.sleep(1)

        # Query with custom aggregation
        result = await monitoring_tool.execute(
            operation="query_metrics",
            params={
                "metric_type": test_metric_type,
                "hours_back": 1,
                "aggregation_alignment_period": 120,
                "aggregation_per_series_aligner": "ALIGN_MAX"
            }
        )

        assert result["success"] is True
        assert isinstance(result["time_series"], list)

    @pytest.mark.asyncio
    async def test_list_alerts(self, monitoring_tool: MonitoringTool) -> None:
        """Test listing alert policies."""
        result = await monitoring_tool.execute(
            operation="list_alerts",
            params={}
        )

        assert result["success"] is True
        assert "count" in result
        assert "alert_policies" in result
        assert isinstance(result["alert_policies"], list)
        assert result["count"] == len(result["alert_policies"])

    @pytest.mark.asyncio
    async def test_list_uptime_checks(self, monitoring_tool: MonitoringTool) -> None:
        """Test listing uptime checks."""
        result = await monitoring_tool.execute(
            operation="list_uptime_checks",
            params={}
        )

        assert result["success"] is True
        assert "count" in result
        assert "uptime_checks" in result
        assert isinstance(result["uptime_checks"], list)
        assert result["count"] == len(result["uptime_checks"])

    @pytest.mark.asyncio
    async def test_unknown_operation(self, monitoring_tool: MonitoringTool) -> None:
        """Test handling of unknown operations."""
        result = await monitoring_tool.execute(
            operation="unknown_operation",
            params={}
        )

        assert result["success"] is False
        assert "Unknown operation" in result["error"]

    @pytest.mark.asyncio
    async def test_create_alert_basic(self, monitoring_tool: MonitoringTool) -> None:
        """Test creating a basic alert policy."""
        test_metric_type = f"custom.googleapis.com/alert_test_{int(datetime.now().timestamp())}"
        alert_name = f"Test Alert {int(datetime.now().timestamp())}"

        result = await monitoring_tool.execute(
            operation="create_alert",
            params={
                "display_name": alert_name,
                "metric_type": test_metric_type,
                "threshold_value": 50.0,
                "comparison_type": "COMPARISON_GT",
                "duration": 120
            }
        )

        # Note: This may fail in demo environment due to permissions
        # but we're testing the code path and validation
        if result["success"]:
            assert "alert_policy_id" in result
            assert result["display_name"] == alert_name
            assert "enabled" in result
        else:
            # Verify it's a permission/quota error, not a code error
            assert "error" in result
            # Common permission errors we expect in demo environment
            expected_errors = ["permission", "quota", "forbidden", "access", "billing"]
            assert any(error_type in result["error"].lower() for error_type in expected_errors)

    @pytest.mark.asyncio
    async def test_create_uptime_check_basic(self, monitoring_tool: MonitoringTool) -> None:
        """Test creating a basic uptime check."""
        check_name = f"Test Uptime Check {int(datetime.now().timestamp())}"

        result = await monitoring_tool.execute(
            operation="create_uptime_check",
            params={
                "display_name": check_name,
                "host": "httpbin.org",
                "path": "/status/200",
                "port": 443,
                "use_ssl": True,
                "check_interval": 60
            }
        )

        # Note: This may fail in demo environment due to permissions
        # but we're testing the code path and validation
        if result["success"]:
            assert "uptime_check_id" in result
            assert result["display_name"] == check_name
            assert result["host"] == "httpbin.org"
            assert result["path"] == "/status/200"
        else:
            # Verify it's a permission/quota error, not a code error
            assert "error" in result
            expected_errors = ["permission", "quota", "forbidden", "access", "billing"]
            assert any(error_type in result["error"].lower() for error_type in expected_errors)


class TestHelperFunctions:
    """Test helper functions for creating filters."""

    def test_create_metric_filter_basic(self) -> None:
        """Test creating a basic metric filter."""
        filter_expr = create_metric_filter("custom.googleapis.com/test_metric")
        expected = 'metric.type="custom.googleapis.com/test_metric"'
        assert filter_expr == expected

    def test_create_metric_filter_with_resource_type(self) -> None:
        """Test creating metric filter with resource type."""
        filter_expr = create_metric_filter(
            "custom.googleapis.com/test_metric",
            resource_type="gce_instance"
        )
        expected = 'metric.type="custom.googleapis.com/test_metric" AND resource.type="gce_instance"'
        assert filter_expr == expected

    def test_create_metric_filter_with_labels(self) -> None:
        """Test creating metric filter with labels."""
        filter_expr = create_metric_filter(
            "custom.googleapis.com/test_metric",
            labels={"environment": "prod", "service": "api"}
        )
        expected = 'metric.type="custom.googleapis.com/test_metric" AND metric.label.environment="prod" AND metric.label.service="api"'
        assert filter_expr == expected

    def test_create_metric_filter_complete(self) -> None:
        """Test creating metric filter with all parameters."""
        filter_expr = create_metric_filter(
            "custom.googleapis.com/test_metric",
            resource_type="gce_instance",
            labels={"zone": "us-central1-a"}
        )
        expected = 'metric.type="custom.googleapis.com/test_metric" AND resource.type="gce_instance" AND metric.label.zone="us-central1-a"'
        assert filter_expr == expected

    def test_create_resource_filter_basic(self) -> None:
        """Test creating a basic resource filter."""
        filter_expr = create_resource_filter("gce_instance")
        expected = 'resource.type="gce_instance"'
        assert filter_expr == expected

    def test_create_resource_filter_with_labels(self) -> None:
        """Test creating resource filter with labels."""
        filter_expr = create_resource_filter(
            "gce_instance",
            labels={"instance_id": "test-instance", "zone": "us-central1-a"}
        )
        expected = 'resource.type="gce_instance" AND resource.label.instance_id="test-instance" AND resource.label.zone="us-central1-a"'
        assert filter_expr == expected

    def test_create_resource_filter_empty_labels(self) -> None:
        """Test creating resource filter with empty labels."""
        filter_expr = create_resource_filter("global", labels={})
        expected = 'resource.type="global"'
        assert filter_expr == expected

    def test_filter_functions_with_special_characters(self) -> None:
        """Test filter functions handle special characters properly."""
        # Test metric filter with special characters in labels
        filter_expr = create_metric_filter(
            "custom.googleapis.com/test-metric",
            labels={"app_name": "my-app", "version": "1.0.0"}
        )
        expected = 'metric.type="custom.googleapis.com/test-metric" AND metric.label.app_name="my-app" AND metric.label.version="1.0.0"'
        assert filter_expr == expected

        # Test resource filter with special characters
        filter_expr = create_resource_filter(
            "k8s_container",
            labels={"cluster_name": "prod-cluster", "namespace_name": "default"}
        )
        expected = 'resource.type="k8s_container" AND resource.label.cluster_name="prod-cluster" AND resource.label.namespace_name="default"'
        assert filter_expr == expected

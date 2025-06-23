"""Google Cloud Monitoring tool for ADK agents.

This module provides a Cloud Monitoring tool implementation using ADK's BaseTool
for creating and querying metrics, alerts, and uptime checks in Google Cloud Monitoring.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from google.adk.tools import BaseTool
from google.cloud import monitoring_v3
from google.protobuf import timestamp_pb2
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class MonitoringConfig(BaseModel):
    """Configuration for Cloud Monitoring operations."""

    project_id: str = Field(description="Google Cloud Project ID")
    timeout: float = Field(default=30.0, description="Operation timeout in seconds")
    max_results: int = Field(default=100, description="Maximum results to return")

    @field_validator("timeout")
    def validate_timeout(cls, v: float) -> float:  # pylint: disable=no-self-argument
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @field_validator("max_results")
    def validate_max_results(cls, v: int) -> int:  # pylint: disable=no-self-argument
        if v <= 0 or v > 1000:
            raise ValueError("max_results must be between 1 and 1000")
        return v


class WriteMetricInput(BaseModel):
    """Input schema for writing a custom metric."""

    metric_type: str = Field(
        description="Metric type (e.g., 'custom.googleapis.com/my_metric')"
    )
    value: Union[int, float] = Field(description="Metric value")
    labels: Optional[Dict[str, str]] = Field(default=None, description="Metric labels")
    resource_type: str = Field(
        default="global", description="Resource type for the metric"
    )
    resource_labels: Optional[Dict[str, str]] = Field(
        default=None, description="Resource labels"
    )


class QueryMetricsInput(BaseModel):
    """Input schema for querying metrics."""

    metric_type: str = Field(description="Metric type to query")
    hours_back: int = Field(default=1, description="Number of hours to look back")
    aggregation_alignment_period: int = Field(
        default=60, description="Alignment period in seconds"
    )
    aggregation_per_series_aligner: str = Field(
        default="ALIGN_MEAN", description="How to align time series data"
    )
    filter: Optional[str] = Field(
        default=None, description="Additional filter for metrics"
    )


class CreateAlertInput(BaseModel):
    """Input schema for creating an alert policy."""

    display_name: str = Field(description="Alert policy display name")
    metric_type: str = Field(description="Metric type to monitor")
    threshold_value: float = Field(description="Threshold value for the alert")
    comparison_type: str = Field(
        default="COMPARISON_GT",
        description="Comparison type: COMPARISON_GT, COMPARISON_LT, etc.",
    )
    duration: int = Field(
        default=60, description="Duration in seconds before alert triggers"
    )
    notification_channels: Optional[List[str]] = Field(
        default=None, description="List of notification channel IDs"
    )

    @field_validator("comparison_type")
    def validate_comparison(cls, v: str) -> str:  # pylint: disable=no-self-argument
        valid_types = [
            "COMPARISON_GT",
            "COMPARISON_LT",
            "COMPARISON_GE",
            "COMPARISON_LE",
            "COMPARISON_EQ",
            "COMPARISON_NE",
        ]
        if v not in valid_types:
            raise ValueError(f"Comparison type must be one of: {valid_types}")
        return v


class UptimeCheckInput(BaseModel):
    """Input schema for creating an uptime check."""

    display_name: str = Field(description="Uptime check display name")
    monitored_resource_type: str = Field(
        default="uptime_url", description="Type of resource to monitor"
    )
    host: str = Field(description="Host to monitor")
    path: str = Field(default="/", description="Path to check")
    port: int = Field(default=443, description="Port number")
    use_ssl: bool = Field(default=True, description="Use HTTPS")
    check_interval: int = Field(default=60, description="Check interval in seconds")


class MonitoringTool(BaseTool):
    """ADK tool for interacting with Google Cloud Monitoring.

    This tool provides methods for:
    - Writing custom metrics
    - Querying time series data
    - Creating and managing alert policies
    - Setting up uptime checks
    - Managing dashboards
    """

    def __init__(self, config: MonitoringConfig):
        """Initialize the Cloud Monitoring tool.

        Args:
            config: Configuration for Cloud Monitoring operations
        """
        super().__init__(
            name="cloud_monitoring",
            description="Tool for metrics, alerts, and monitoring in Google Cloud",
        )
        self.config = config
        self.client = monitoring_v3.MetricServiceClient()
        self.alert_client = monitoring_v3.AlertPolicyServiceClient()
        self.uptime_client = monitoring_v3.UptimeCheckServiceClient()
        self.project_path = f"projects/{config.project_id}"

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define the input schema for the tool.

        Returns:
            JSON schema for tool inputs
        """
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "write_metric",
                        "query_metrics",
                        "create_alert",
                        "list_alerts",
                        "create_uptime_check",
                        "list_uptime_checks",
                    ],
                    "description": "Operation to perform",
                },
                "params": {
                    "type": "object",
                    "description": "Operation-specific parameters",
                },
            },
            "required": ["operation", "params"],
        }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute a Cloud Monitoring operation.

        Args:
            **kwargs: Operation and parameters

        Returns:
            Operation result
        """
        operation = kwargs.get("operation")
        params = kwargs.get("params", {})

        if operation == "write_metric":
            return await self._write_metric(**params)
        elif operation == "query_metrics":
            return await self._query_metrics(**params)
        elif operation == "create_alert":
            return await self._create_alert(**params)
        elif operation == "list_alerts":
            return await self._list_alerts(**params)
        elif operation == "create_uptime_check":
            return await self._create_uptime_check(**params)
        elif operation == "list_uptime_checks":
            return await self._list_uptime_checks(**params)
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}

    async def _write_metric(self, **kwargs: Any) -> Dict[str, Any]:
        """Write a custom metric to Cloud Monitoring.

        Args:
            **kwargs: Parameters from WriteMetricInput

        Returns:
            Result of metric write operation
        """
        try:
            # Validate input
            metric_input = WriteMetricInput(**kwargs)

            # Create time series
            series = monitoring_v3.TimeSeries()
            series.metric.type = metric_input.metric_type

            # Add metric labels
            if metric_input.labels:
                for (
                    key,
                    value,
                ) in metric_input.labels.items():  # pylint: disable=no-member
                    series.metric.labels[key] = value  # pylint: disable=no-member

            # Set resource
            series.resource.type = metric_input.resource_type
            if metric_input.resource_labels:
                for (
                    key,
                    value,
                ) in metric_input.resource_labels.items():  # pylint: disable=no-member
                    series.resource.labels[key] = value  # pylint: disable=no-member

            # Create point
            now = datetime.now(timezone.utc)
            point = monitoring_v3.Point()

            # Create and set the time interval
            point.interval = monitoring_v3.TimeInterval()
            point.interval.end_time = timestamp_pb2.Timestamp(
                seconds=int(now.timestamp())
            )  # pylint: disable=no-member

            point.value.double_value = float(metric_input.value)
            series.points = [point]

            # Write time series
            self.client.create_time_series(name=self.project_path, time_series=[series])

            return {
                "success": True,
                "metric_type": metric_input.metric_type,
                "value": metric_input.value,
                "timestamp": now.isoformat(),
            }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to write metric: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _query_metrics(self, **kwargs: Any) -> Dict[str, Any]:
        """Query time series data from Cloud Monitoring.

        Args:
            **kwargs: Parameters from QueryMetricsInput

        Returns:
            Time series data
        """
        try:
            # Validate input
            query_input = QueryMetricsInput(**kwargs)

            # Build time interval
            interval = monitoring_v3.TimeInterval()
            now = datetime.now(timezone.utc)
            interval.end_time = timestamp_pb2.Timestamp(
                seconds=int(now.timestamp())
            )  # pylint: disable=no-member
            start_time = now - timedelta(hours=query_input.hours_back)
            interval.start_time = timestamp_pb2.Timestamp(
                seconds=int(start_time.timestamp())
            )  # pylint: disable=no-member

            # Build aggregation
            aggregation = monitoring_v3.Aggregation()
            aggregation.alignment_period.seconds = (
                query_input.aggregation_alignment_period
            )
            aggregation.per_series_aligner = getattr(
                monitoring_v3.Aggregation.Aligner,
                query_input.aggregation_per_series_aligner,
            )

            # Build request
            request = monitoring_v3.ListTimeSeriesRequest(
                name=self.project_path,
                filter=f'metric.type="{query_input.metric_type}"',
                interval=interval,
                view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                aggregation=aggregation,
            )

            # Add additional filter if provided
            if query_input.filter:
                request.filter += f" AND {query_input.filter}"

            # Query time series
            results: List[Dict[str, Any]] = []
            for time_series in self.client.list_time_series(request=request):
                series_data: Dict[str, Any] = {
                    "metric": {
                        "type": time_series.metric.type,
                        "labels": dict(time_series.metric.labels),
                    },
                    "resource": {
                        "type": time_series.resource.type,
                        "labels": dict(time_series.resource.labels),
                    },
                    "points": [],
                }

                for point in time_series.points:
                    point_data = {
                        "timestamp": datetime.fromtimestamp(
                            point.interval.end_time.seconds
                        ).isoformat(),
                        "value": point.value.double_value or point.value.int64_value,
                    }
                    series_data["points"].append(point_data)

                results.append(series_data)

            return {
                "success": True,
                "series_count": len(results),
                "time_series": results,
            }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to query metrics: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _create_alert(self, **kwargs: Any) -> Dict[str, Any]:
        """Create an alert policy in Cloud Monitoring.

        Args:
            **kwargs: Parameters from CreateAlertInput

        Returns:
            Created alert policy details
        """
        try:
            # Validate input
            alert_input = CreateAlertInput(**kwargs)

            # Create condition
            condition = monitoring_v3.AlertPolicy.Condition()
            condition.display_name = f"{alert_input.display_name} - Condition"
            condition.condition_threshold = monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                filter=f'metric.type="{alert_input.metric_type}" AND resource.type="global"',
                comparison=getattr(
                    monitoring_v3.ComparisonType, alert_input.comparison_type
                ),
                threshold_value=alert_input.threshold_value,
                duration={"seconds": alert_input.duration},
                aggregations=[
                    monitoring_v3.Aggregation(
                        alignment_period={"seconds": 60},
                        per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                    )
                ],
            )

            # Create alert policy
            alert_policy = monitoring_v3.AlertPolicy()
            alert_policy.display_name = alert_input.display_name
            alert_policy.conditions.append(condition)  # pylint: disable=no-member
            alert_policy.combiner = monitoring_v3.AlertPolicy.ConditionCombinerType(
                monitoring_v3.AlertPolicy.ConditionCombinerType.AND
            )

            # Add notification channels if provided
            if alert_input.notification_channels:
                alert_policy.notification_channels.extend(  # pylint: disable=no-member
                    alert_input.notification_channels
                )

            # Create the alert policy
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_path, alert_policy=alert_policy
            )

            return {
                "success": True,
                "alert_policy_id": created_policy.name.split("/")[-1],
                "display_name": created_policy.display_name,
                "enabled": created_policy.enabled,
            }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to create alert: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _list_alerts(self, **kwargs: Any) -> Dict[str, Any]:
        """List alert policies in the project.

        Returns:
            List of alert policies
        """
        # kwargs parameter maintained for interface consistency
        _ = kwargs

        try:
            policies = []
            for policy in self.alert_client.list_alert_policies(name=self.project_path):
                policies.append(
                    {
                        "id": policy.name.split("/")[-1],
                        "display_name": policy.display_name,
                        "enabled": policy.enabled,
                        "conditions": len(policy.conditions),
                        "notification_channels": len(policy.notification_channels),
                    }
                )

            return {"success": True, "count": len(policies), "alert_policies": policies}

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to list alerts: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _create_uptime_check(self, **kwargs: Any) -> Dict[str, Any]:
        """Create an uptime check in Cloud Monitoring.

        Args:
            **kwargs: Parameters from UptimeCheckInput

        Returns:
            Created uptime check details
        """
        try:
            # Validate input
            uptime_input = UptimeCheckInput(**kwargs)

            # Create uptime check config
            config = monitoring_v3.UptimeCheckConfig()
            config.display_name = uptime_input.display_name
            config.period = {"seconds": uptime_input.check_interval}
            config.timeout = {"seconds": 10}

            # Configure monitored resource
            config.monitored_resource.type = uptime_input.monitored_resource_type
            config.monitored_resource.labels["host"] = (
                uptime_input.host
            )  # pylint: disable=no-member
            config.monitored_resource.labels["project_id"] = (
                self.config.project_id
            )  # pylint: disable=no-member

            # Configure HTTP check
            if uptime_input.monitored_resource_type == "uptime_url":
                config.http_check = monitoring_v3.UptimeCheckConfig.HttpCheck(
                    path=uptime_input.path,
                    port=uptime_input.port,
                    use_ssl=uptime_input.use_ssl,
                    validate_ssl=uptime_input.use_ssl,
                )

            # Create the uptime check
            created_check = self.uptime_client.create_uptime_check_config(
                parent=self.project_path, uptime_check_config=config
            )

            return {
                "success": True,
                "uptime_check_id": created_check.name.split("/")[-1],
                "display_name": created_check.display_name,
                "host": uptime_input.host,
                "path": uptime_input.path,
            }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to create uptime check: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _list_uptime_checks(self, **kwargs: Any) -> Dict[str, Any]:
        """List uptime checks in the project.

        Returns:
            List of uptime checks
        """
        # kwargs parameter maintained for interface consistency
        _ = kwargs

        try:
            checks = []
            for check in self.uptime_client.list_uptime_check_configs(
                parent=self.project_path
            ):
                check_data = {
                    "id": check.name.split("/")[-1],
                    "display_name": check.display_name,
                    "monitored_resource_type": check.monitored_resource.type,
                    "period": check.period.seconds if check.period else None,
                }

                # Add HTTP check details if available
                if check.http_check:
                    check_data["http_check"] = {
                        "path": check.http_check.path,
                        "port": check.http_check.port,
                        "use_ssl": check.http_check.use_ssl,
                    }

                # Add monitored resource labels
                if check.monitored_resource.labels:
                    check_data["host"] = check.monitored_resource.labels.get("host", "")

                checks.append(check_data)

            return {"success": True, "count": len(checks), "uptime_checks": checks}

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to list uptime checks: %s", str(e))
            return {"success": False, "error": str(e)}


# Helper functions for creating common metric filters
def create_metric_filter(
    metric_type: str,
    resource_type: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
) -> str:
    """Create a filter expression for metrics.

    Args:
        metric_type: Type of metric
        resource_type: Optional resource type filter
        labels: Optional metric labels to filter by

    Returns:
        Filter expression string
    """
    filters = [f'metric.type="{metric_type}"']

    if resource_type:
        filters.append(f'resource.type="{resource_type}"')

    if labels:
        for key, value in labels.items():
            filters.append(f'metric.label.{key}="{value}"')

    return " AND ".join(filters)


def create_resource_filter(
    resource_type: str, labels: Optional[Dict[str, str]] = None
) -> str:
    """Create a filter expression for resources.

    Args:
        resource_type: Type of resource
        labels: Optional resource labels to filter by

    Returns:
        Filter expression string
    """
    filters = [f'resource.type="{resource_type}"']

    if labels:
        for key, value in labels.items():
            filters.append(f'resource.label.{key}="{value}"')

    return " AND ".join(filters)

"""
Cost Analyzer Utility Module

This module provides utilities for analyzing Google Cloud Platform costs,
tracking usage metrics, and identifying cost optimization opportunities.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import google.cloud.monitoring_v3 as monitoring_v3
import numpy as np
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from src.common.secure_query_builder import SecureQueryBuilder

# Initialize logger
logger = logging.getLogger(__name__)


class CostAnalyzer:
    """Analyzes GCP costs and provides insights for optimization."""

    def __init__(self, project_id: str, billing_dataset: str = "sentinelops_billing"):
        """
        Initialize Cost Analyzer.

        Args:
            project_id: GCP project ID
            billing_dataset: BigQuery dataset containing billing export
        """
        # Validate project_id and dataset name to prevent SQL injection
        if not self._is_valid_identifier(project_id):
            raise ValueError(f"Invalid project_id: {project_id}")
        if not self._is_valid_identifier(billing_dataset):
            raise ValueError(f"Invalid billing_dataset: {billing_dataset}")

        self.project_id = project_id
        self.billing_dataset = billing_dataset

        # Initialize clients
        self.bq_client = bigquery.Client(project=project_id)
        self.monitoring_client = monitoring_v3.MetricServiceClient()

        # Cache for query results
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 3600  # 1 hour cache TTL

    def _is_valid_identifier(self, identifier: str) -> bool:
        """Validate that an identifier only contains allowed characters."""
        # BigQuery identifiers can contain letters, numbers, underscores, and hyphens
        # Project IDs can also contain hyphens
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", identifier))

    def _get_billing_table(self) -> str:
        """Get the latest billing export table name."""
        dataset_id = f"{self.project_id}.{self.billing_dataset}"

        try:
            tables = list(self.bq_client.list_tables(dataset_id))
            # Billing export tables follow pattern: gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX
            billing_tables = [
                t.table_id
                for t in tables
                if t.table_id.startswith("gcp_billing_export")
            ]

            if not billing_tables:
                raise ValueError("No billing export tables found")

            # Return the latest table
            latest_table = sorted(billing_tables)[-1]
            # Validate table name before returning
            if not self._is_valid_identifier(latest_table):
                raise ValueError(f"Invalid table name: {latest_table}")
            return str(latest_table)

        except NotFound:
            logger.error("Billing dataset %s not found", self.billing_dataset)
            raise

    def get_current_month_spend(self) -> Dict[str, float]:
        """
        Get current month's spending by service.

        Returns:
            Dictionary mapping service name to cost in USD
        """
        cache_key = f"month_spend_{datetime.now(timezone.utc).strftime('%Y%m')}"
        if cache_key in self._cache:
            cache_time, data = self._cache[cache_key]
            if (datetime.now(timezone.utc) - cache_time).seconds < self._cache_ttl:
                return dict(data)

        # Build query using secure query builder
        billing_table = self._get_billing_table()
        table_identifier = f"{self.project_id}.{self.billing_dataset}.{billing_table}"

        try:
            # Build base query with fields and conditions
            query = SecureQueryBuilder.build_select_query(
                table_identifier,
                [
                    "service.description as service_name",
                    "SUM(cost) as total_cost",
                    "currency"
                ],
                [
                    "DATE(usage_start_time) >= DATE_TRUNC(CURRENT_DATE(), MONTH)",
                    "project.id = @project_id"
                ]
            )
            # Add GROUP BY and ORDER BY
            query += "\nGROUP BY service_name, currency"
            query += "\nORDER BY total_cost DESC"
        except ValueError as e:
            logger.error("Invalid table identifier for cost query: %s", e)
            return {}

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_id", "STRING", self.project_id)
            ]
        )

        try:
            results = self.bq_client.query(query, job_config=job_config).result()

            spend_by_service = {}
            for row in results:
                spend_by_service[row.service_name] = float(row.total_cost)

            # Cache results
            self._cache[cache_key] = (datetime.now(timezone.utc), spend_by_service)

            return spend_by_service

        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to query billing data: %s", e)
            return {}

    def get_daily_spend_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily spending trend for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            List of daily spending records
        """
        # Build query using secure query builder
        billing_table = self._get_billing_table()
        table_identifier = f"{self.project_id}.{self.billing_dataset}.{billing_table}"

        try:
            # Build base query with fields and conditions
            query = SecureQueryBuilder.build_select_query(
                table_identifier,
                [
                    "DATE(usage_start_time) as usage_date",
                    "service.description as service_name",
                    "SUM(cost) as daily_cost"
                ],
                [
                    "DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY)",
                    "project.id = @project_id"
                ]
            )
            # Add GROUP BY and ORDER BY
            query += "\nGROUP BY usage_date, service_name"
            query += "\nORDER BY usage_date DESC, daily_cost DESC"
        except ValueError as e:
            logger.error("Invalid table identifier for daily spend query: %s", e)
            return []

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("days", "INT64", days),
                bigquery.ScalarQueryParameter("project_id", "STRING", self.project_id),
            ]
        )

        try:
            results = self.bq_client.query(query, job_config=job_config).result()

            daily_trend = []
            for row in results:
                daily_trend.append(
                    {
                        "date": row.usage_date.isoformat(),
                        "service": row.service_name,
                        "cost": float(row.daily_cost),
                    }
                )

            return daily_trend

        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to query daily spend trend: %s", e)
            return []

    def identify_cost_anomalies(self, sensitivity: float = 1.5) -> List[Dict[str, Any]]:
        """
        Identify cost anomalies using statistical analysis.

        Args:
            sensitivity: Multiplier for standard deviation (lower = more sensitive)

        Returns:
            List of detected anomalies
        """
        # Get daily spending data
        daily_data = self.get_daily_spend_trend(days=60)

        if not daily_data:
            return []

        # Group data by service
        service_data: Dict[str, List[Dict[str, Any]]] = {}
        for item in daily_data:
            service = item["service"]
            if service not in service_data:
                service_data[service] = []
            service_data[service].append(item)

        anomalies = []

        # Analyze each service separately
        for service, data_points in service_data.items():
            # Sort by date
            data_points.sort(key=lambda x: x["date"])

            if len(data_points) < 7:  # Need at least 7 days for rolling window
                continue

            costs = [d["cost"] for d in data_points]

            # Calculate rolling statistics manually
            for i in range(7, len(data_points)):
                # Get window of last 7 days
                window = costs[i - 7 : i]
                window_mean = np.mean(window)
                window_std = np.std(window)

                # Current value
                current_cost = costs[i]
                current_date = data_points[i]["date"]

                # Calculate bounds
                upper_bound = window_mean + (sensitivity * window_std)
                lower_bound = window_mean - (sensitivity * window_std)

                # Check for anomaly
                if current_cost > upper_bound or current_cost < lower_bound:
                    deviation_percent = (
                        abs(current_cost - window_mean) / window_mean * 100
                    )

                    anomalies.append(
                        {
                            "date": current_date,
                            "service": service,
                            "actual_cost": float(current_cost),
                            "expected_range": (
                                float(lower_bound),
                                float(upper_bound),
                            ),
                            "deviation_percent": float(deviation_percent),
                        }
                    )

        return sorted(anomalies, key=lambda x: x["deviation_percent"], reverse=True)

    def get_resource_utilization_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get resource utilization metrics for cost optimization.

        Returns:
            Dictionary of services and their utilization metrics
        """
        metrics = {}

        # Define metric queries for different services
        metric_queries = {
            "cloud_run": [
                ("cpu_utilization", "run.googleapis.com/container/cpu/utilizations"),
                (
                    "memory_utilization",
                    "run.googleapis.com/container/memory/utilizations",
                ),
                ("request_count", "run.googleapis.com/request_count"),
            ],
            "cloud_functions": [
                (
                    "execution_count",
                    "cloudfunctions.googleapis.com/function/execution_count",
                ),
                (
                    "execution_time",
                    "cloudfunctions.googleapis.com/function/execution_times",
                ),
                (
                    "memory_usage",
                    "cloudfunctions.googleapis.com/function/user_memory_bytes",
                ),
            ],
            "compute_engine": [
                ("cpu_utilization", "compute.googleapis.com/instance/cpu/utilization"),
                (
                    "disk_read_bytes",
                    "compute.googleapis.com/instance/disk/read_bytes_count",
                ),
                (
                    "disk_write_bytes",
                    "compute.googleapis.com/instance/disk/write_bytes_count",
                ),
            ],
        }

        project_name = f"projects/{self.project_id}"

        for service, service_metrics in metric_queries.items():
            service_data = {}

            for metric_name, metric_type in service_metrics:
                try:
                    # Query for the last 24 hours
                    interval = monitoring_v3.TimeInterval(
                        {
                            "end_time": {
                                "seconds": int(datetime.now(timezone.utc).timestamp())
                            },
                            "start_time": {
                                "seconds": int(
                                    (
                                        datetime.now(timezone.utc) - timedelta(hours=24)
                                    ).timestamp()
                                )
                            },
                        }
                    )

                    results = self.monitoring_client.list_time_series(
                        request={
                            "name": project_name,
                            "filter": f'metric.type="{metric_type}"',
                            "interval": interval,
                            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        }
                    )

                    # Calculate average utilization
                    total_value = 0.0
                    point_count = 0

                    for result in results:
                        for point in result.points:
                            total_value += point.value.double_value
                            point_count += 1

                    if point_count > 0:
                        service_data[metric_name] = total_value / point_count
                    else:
                        service_data[metric_name] = 0.0

                except (ValueError, KeyError, AttributeError) as e:
                    logger.error("Failed to get %s for %s: %s", metric_name, service, e)
                    service_data[metric_name] = 0.0

            if service_data:
                metrics[service] = service_data

        return metrics

    def calculate_cost_projections(self) -> Dict[str, Any]:
        """
        Calculate cost projections for the current month.

        Returns:
            Dictionary with projected costs
        """
        # Get current spending
        current_spend = sum(self.get_current_month_spend().values())

        # Get current day of month
        today = datetime.now(timezone.utc)
        days_in_month = 30  # Simplified - you might want to calculate actual days
        days_elapsed = today.day
        days_remaining = days_in_month - days_elapsed

        # Calculate daily average
        daily_average = current_spend / days_elapsed if days_elapsed > 0 else 0

        # Project end of month
        projected_total = current_spend + (daily_average * days_remaining)

        # Get recent trend
        recent_trend = self.get_daily_spend_trend(days=7)
        if recent_trend:
            # Calculate 7-day average
            recent_costs = [d["cost"] for d in recent_trend]
            recent_average = sum(recent_costs) / len(recent_costs)

            # Adjusted projection based on recent trend
            trend_projection = current_spend + (recent_average * days_remaining)
        else:
            trend_projection = projected_total

        return {
            "current_spend": current_spend,
            "daily_average": daily_average,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "simple_projection": projected_total,
            "trend_projection": float(trend_projection),
            "projection_date": today.isoformat(),
        }

    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate cost optimization recommendations based on usage patterns.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Get utilization metrics
        utilization = self.get_resource_utilization_metrics()

        # Check Cloud Run utilization
        if "cloud_run" in utilization:
            cpu_util = utilization["cloud_run"].get("cpu_utilization", 0)
            memory_util = utilization["cloud_run"].get("memory_utilization", 0)

            if cpu_util < 0.2 and memory_util < 0.3:
                recommendations.append(
                    {
                        "service": "Cloud Run",
                        "type": "rightsizing",
                        "priority": "high",
                        "recommendation": "Consider reducing CPU and memory allocation",
                        "potential_savings": "Up to 40% of Cloud Run costs",
                        "details": (
                            f"CPU utilization: {cpu_util:.1%}, "
                            f"Memory utilization: {memory_util:.1%}"
                        ),
                    }
                )

        # Check for anomalies
        anomalies = self.identify_cost_anomalies()
        if anomalies:
            for anomaly in anomalies[:3]:  # Top 3 anomalies
                recommendations.append(
                    {
                        "service": anomaly["service"],
                        "type": "anomaly",
                        "priority": "medium",
                        "recommendation": f"Investigate cost spike on {anomaly['date']}",
                        "potential_savings": "Variable",
                        "details": f"Cost was {anomaly['deviation_percent']:.1f}% above normal",
                    }
                )

        # Check for unused resources (simplified example)
        current_spend = self.get_current_month_spend()

        # Look for services with very low spend that might be unused
        for service, cost in current_spend.items():
            if 0 < cost < 1:  # Less than $1 spend
                recommendations.append(
                    {
                        "service": service,
                        "type": "unused_resource",
                        "priority": "low",
                        "recommendation": f"Review {service} - very low usage detected",
                        "potential_savings": f"${cost:.2f}/month",
                        "details": "Service shows minimal activity",
                    }
                )

        return recommendations

    def generate_cost_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive cost report.

        Returns:
            Dictionary containing the full cost report
        """
        logger.info("Generating comprehensive cost report...")

        current_month_spend = self.get_current_month_spend()
        daily_trend = self.get_daily_spend_trend(days=7)

        report: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": self.project_id,
            "current_month_spend": current_month_spend,
            "projections": self.calculate_cost_projections(),
            "anomalies": self.identify_cost_anomalies(),
            "utilization_metrics": self.get_resource_utilization_metrics(),
            "recommendations": self.get_cost_optimization_recommendations(),
            "daily_trend": daily_trend,
        }

        # Calculate total current spend
        report["total_current_spend"] = sum(current_month_spend.values())

        # Add summary statistics
        if daily_trend:
            daily_costs = [d["cost"] for d in daily_trend]
            report["summary_stats"] = {
                "avg_daily_cost": np.mean(daily_costs),
                "max_daily_cost": np.max(daily_costs),
                "min_daily_cost": np.min(daily_costs),
                "std_daily_cost": np.std(daily_costs),
            }

        logger.info("Cost report generation completed")
        return report


def format_cost_report(report: Dict[str, Any]) -> str:
    """
    Format cost report for display.

    Args:
        report: Cost report dictionary

    Returns:
        Formatted report string
    """
    lines = [
        "=" * 60,
        "SENTINELOPS COST REPORT",
        "=" * 60,
        f"Generated: {report['timestamp']}",
        f"Project: {report['project_id']}",
        "",
        "CURRENT MONTH SPENDING:",
        "-" * 40,
    ]

    # Current spending by service
    total_spend = report.get("total_current_spend", 0)
    lines.append(f"Total: ${total_spend:,.2f}")
    lines.append("")

    for service, cost in sorted(
        report["current_month_spend"].items(), key=lambda x: x[1], reverse=True
    ):
        if cost > 0:
            lines.append(f"  {service:<30} ${cost:>10,.2f}")

    # Projections
    projections = report.get("projections", {})
    if projections:
        lines.extend(
            [
                "",
                "COST PROJECTIONS:",
                "-" * 40,
                f"Days elapsed: {projections.get('days_elapsed', 0)}",
                f"Daily average: ${projections.get('daily_average', 0):,.2f}",
                f"Simple projection: ${projections.get('simple_projection', 0):,.2f}",
                f"Trend-based projection: ${projections.get('trend_projection', 0):,.2f}",
            ]
        )

    # Anomalies
    anomalies = report.get("anomalies", [])
    if anomalies:
        lines.extend(["", "COST ANOMALIES DETECTED:", "-" * 40])
        for anomaly in anomalies[:5]:
            lines.append(
                f"  {anomaly['service']} on {anomaly['date']}: "
                f"{anomaly['deviation_percent']:.1f}% deviation"
            )

    # Recommendations
    recommendations = report.get("recommendations", [])
    if recommendations:
        lines.extend(["", "OPTIMIZATION RECOMMENDATIONS:", "-" * 40])
        for i, rec in enumerate(recommendations[:5], 1):
            lines.extend(
                [
                    f"{i}. {rec['service']} ({rec['priority']} priority)",
                    f"   {rec['recommendation']}",
                    f"   Potential savings: {rec['potential_savings']}",
                ]
            )

    lines.append("=" * 60)

    return "\n".join(lines)

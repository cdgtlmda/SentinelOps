#!/usr/bin/env python3
"""
Create Monitoring Dashboards for SentinelOps

This script creates comprehensive monitoring dashboards for all SentinelOps
services using the Google Cloud Monitoring Dashboard API.
"""

import json
import os
import sys
from typing import Any, Dict, List

from google.api_core import exceptions
from google.cloud import monitoring_dashboard_v1

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.logger import Logger  # noqa: E402

# Initialize logger
logger = Logger(__name__).logger


class DashboardCreator:
    """Creates monitoring dashboards for SentinelOps."""

    def __init__(self, project_id: str):
        """
        Initialize Dashboard Creator.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.client = monitoring_dashboard_v1.DashboardsServiceClient()
        self.project_name = f"projects/{project_id}"

    def create_overview_dashboard(self) -> str:
        """Create main overview dashboard."""
        logger.info("Creating overview dashboard...")

        dashboard = monitoring_dashboard_v1.Dashboard()
        dashboard.display_name = "SentinelOps - Overview"
        dashboard.mosaicLayout = monitoring_dashboard_v1.MosaicLayout()

        tiles = []

        # System Health Scorecard
        health_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        health_tile.width = 12
        health_tile.height = 4
        health_tile.widget = monitoring_dashboard_v1.Widget()
        health_tile.widget.title = "System Health"
        health_tile.widget.scorecard = monitoring_dashboard_v1.Scorecard()
        health_tile.widget.scorecard.timeSeriesQuery = (
            monitoring_dashboard_v1.TimeSeriesQuery()
        )
        health_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        health_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter.filter = """
            resource.type="cloud_run_revision" AND
            metric.type="run.googleapis.com/request_count"
        """
        health_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        health_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        health_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_RATE
        )
        health_tile.widget.scorecard.sparkChartView = (
            monitoring_dashboard_v1.SparkChartView()
        )
        tiles.append(health_tile)

        # Request Rate Chart
        request_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        request_tile.yPos = 4
        request_tile.width = 6
        request_tile.height = 4
        request_tile.widget = monitoring_dashboard_v1.Widget()
        request_tile.widget.title = "Request Rate by Service"
        request_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()

        request_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        request_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        request_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        request_dataset.timeSeriesQuery.timeSeriesFilter.filter = """
            resource.type="cloud_run_revision" AND
            metric.type="run.googleapis.com/request_count"
        """
        request_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        request_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        request_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_RATE
        )
        request_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.groupByFields = [
            "resource.label.service_name"
        ]

        request_tile.widget.xyChart.dataSets.append(request_dataset)
        tiles.append(request_tile)

        # Error Rate Chart
        error_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        error_tile.xPos = 6
        error_tile.yPos = 4
        error_tile.width = 6
        error_tile.height = 4
        error_tile.widget = monitoring_dashboard_v1.Widget()
        error_tile.widget.title = "Error Rate"
        error_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()

        error_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        error_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        error_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        error_dataset.timeSeriesQuery.timeSeriesFilter.filter = """
            resource.type="cloud_run_revision" AND
            metric.type="run.googleapis.com/request_count" AND
            metric.label.response_code_class="5xx"
        """
        error_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        error_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        error_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_RATE
        )
        error_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.groupByFields = [
            "resource.label.service_name"
        ]

        error_tile.widget.xyChart.dataSets.append(error_dataset)
        tiles.append(error_tile)

        # Latency Chart
        latency_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        latency_tile.yPos = 8
        latency_tile.width = 12
        latency_tile.height = 4
        latency_tile.widget = monitoring_dashboard_v1.Widget()
        latency_tile.widget.title = "Request Latency (P95)"
        latency_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()

        latency_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        latency_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        latency_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        latency_dataset.timeSeriesQuery.timeSeriesFilter.filter = """
            resource.type="cloud_run_revision" AND
            metric.type="run.googleapis.com/request_latencies"
        """
        latency_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        latency_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        latency_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_PERCENTILE_95
        )
        latency_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.groupByFields = [
            "resource.label.service_name"
        ]

        latency_tile.widget.xyChart.dataSets.append(latency_dataset)
        tiles.append(latency_tile)

        dashboard.mosaicLayout.tiles.extend(tiles)

        try:
            response = self.client.create_dashboard(
                parent=self.project_name, dashboard=dashboard
            )
            logger.info(f"Created overview dashboard: {response.name}")
            return response.name
        except exceptions.AlreadyExists:
            logger.info("Overview dashboard already exists")
            return f"{self.project_name}/dashboards/sentinelops-overview"

    def create_service_dashboard(self, service_name: str) -> str:
        """Create detailed dashboard for a specific service."""
        logger.info(f"Creating dashboard for {service_name}...")

        dashboard = monitoring_dashboard_v1.Dashboard()
        dashboard.display_name = f"SentinelOps - {service_name}"
        dashboard.gridLayout = monitoring_dashboard_v1.GridLayout()

        widgets = []

        # CPU Utilization
        cpu_widget = monitoring_dashboard_v1.Widget()
        cpu_widget.title = "CPU Utilization"
        cpu_widget.xyChart = monitoring_dashboard_v1.XyChart()

        cpu_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        cpu_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        cpu_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        cpu_dataset.timeSeriesQuery.timeSeriesFilter.filter = f"""
            resource.type="cloud_run_revision" AND
            resource.label.service_name="{service_name}" AND
            metric.type="run.googleapis.com/container/cpu/utilizations"
        """
        cpu_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        cpu_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        cpu_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_MEAN
        )

        cpu_widget.xyChart.dataSets.append(cpu_dataset)
        widgets.append(cpu_widget)

        # Memory Utilization
        memory_widget = monitoring_dashboard_v1.Widget()
        memory_widget.title = "Memory Utilization"
        memory_widget.xyChart = monitoring_dashboard_v1.XyChart()

        memory_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        memory_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        memory_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        memory_dataset.timeSeriesQuery.timeSeriesFilter.filter = f"""
            resource.type="cloud_run_revision" AND
            resource.label.service_name="{service_name}" AND
            metric.type="run.googleapis.com/container/memory/utilizations"
        """
        memory_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        memory_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        memory_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_MEAN
        )

        memory_widget.xyChart.dataSets.append(memory_dataset)
        widgets.append(memory_widget)

        # Instance Count
        instance_widget = monitoring_dashboard_v1.Widget()
        instance_widget.title = "Active Instances"
        instance_widget.xyChart = monitoring_dashboard_v1.XyChart()

        instance_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        instance_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        instance_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        instance_dataset.timeSeriesQuery.timeSeriesFilter.filter = f"""
            resource.type="cloud_run_revision" AND
            resource.label.service_name="{service_name}" AND
            metric.type="run.googleapis.com/container/instance_count"
        """
        instance_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        instance_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        instance_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_MAX
        )

        instance_widget.xyChart.dataSets.append(instance_dataset)
        widgets.append(instance_widget)

        # Request Count by Status
        status_widget = monitoring_dashboard_v1.Widget()
        status_widget.title = "Requests by Status Code"
        status_widget.xyChart = monitoring_dashboard_v1.XyChart()

        status_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        status_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        status_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        status_dataset.timeSeriesQuery.timeSeriesFilter.filter = f"""
            resource.type="cloud_run_revision" AND
            resource.label.service_name="{service_name}" AND
            metric.type="run.googleapis.com/request_count"
        """
        status_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        status_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        status_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_RATE
        )
        status_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.groupByFields = [
            "metric.label.response_code_class"
        ]

        status_widget.xyChart.dataSets.append(status_dataset)
        widgets.append(status_widget)

        dashboard.gridLayout.widgets.extend(widgets)

        try:
            response = self.client.create_dashboard(
                parent=self.project_name, dashboard=dashboard
            )
            logger.info(f"Created {service_name} dashboard: {response.name}")
            return response.name
        except exceptions.AlreadyExists:
            logger.info(f"{service_name} dashboard already exists")
            return f"{self.project_name}/dashboards/sentinelops-{service_name}"

    def create_security_dashboard(self) -> str:
        """Create security monitoring dashboard."""
        logger.info("Creating security dashboard...")

        dashboard = monitoring_dashboard_v1.Dashboard()
        dashboard.display_name = "SentinelOps - Security"
        dashboard.mosaicLayout = monitoring_dashboard_v1.MosaicLayout()

        tiles = []

        # Failed Authentication Attempts
        auth_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        auth_tile.width = 6
        auth_tile.height = 4
        auth_tile.widget = monitoring_dashboard_v1.Widget()
        auth_tile.widget.title = "Failed Authentication Attempts"
        auth_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()

        auth_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        auth_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        auth_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        auth_dataset.timeSeriesQuery.timeSeriesFilter.filter = """
            resource.type="api" AND
            protoPayload.status.code!=0 AND
            protoPayload.authenticationInfo.principalEmail!=""
        """
        auth_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        auth_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 300
        }
        auth_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_COUNT
        )

        auth_tile.widget.xyChart.dataSets.append(auth_dataset)
        tiles.append(auth_tile)

        # Firewall Blocked Requests
        firewall_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        firewall_tile.xPos = 6
        firewall_tile.width = 6
        firewall_tile.height = 4
        firewall_tile.widget = monitoring_dashboard_v1.Widget()
        firewall_tile.widget.title = "Firewall Blocked Requests"
        firewall_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()

        firewall_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        firewall_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        firewall_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        firewall_dataset.timeSeriesQuery.timeSeriesFilter.filter = """
            resource.type="gce_subnetwork" AND
            metric.type="compute.googleapis.com/firewall/dropped_packets_count"
        """
        firewall_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        firewall_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 60
        }
        firewall_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_RATE
        )

        firewall_tile.widget.xyChart.dataSets.append(firewall_dataset)
        tiles.append(firewall_tile)

        # Active Incidents
        incident_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        incident_tile.yPos = 4
        incident_tile.width = 12
        incident_tile.height = 4
        incident_tile.widget = monitoring_dashboard_v1.Widget()
        incident_tile.widget.title = "Active Security Incidents"
        incident_tile.widget.scorecard = monitoring_dashboard_v1.Scorecard()
        incident_tile.widget.scorecard.timeSeriesQuery = (
            monitoring_dashboard_v1.TimeSeriesQuery()
        )
        incident_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        incident_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter.filter = """
            metric.type="custom.googleapis.com/security/active_incidents"
        """
        incident_tile.widget.scorecard.sparkChartView = (
            monitoring_dashboard_v1.SparkChartView()
        )
        tiles.append(incident_tile)

        dashboard.mosaicLayout.tiles.extend(tiles)

        try:
            response = self.client.create_dashboard(
                parent=self.project_name, dashboard=dashboard
            )
            logger.info(f"Created security dashboard: {response.name}")
            return response.name
        except exceptions.AlreadyExists:
            logger.info("Security dashboard already exists")
            return f"{self.project_name}/dashboards/sentinelops-security"

    def create_cost_dashboard(self) -> str:
        """Create cost monitoring dashboard."""
        logger.info("Creating cost dashboard...")

        dashboard = monitoring_dashboard_v1.Dashboard()
        dashboard.display_name = "SentinelOps - Cost Analysis"
        dashboard.mosaicLayout = monitoring_dashboard_v1.MosaicLayout()

        tiles = []

        # Daily Cost Trend
        cost_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        cost_tile.width = 12
        cost_tile.height = 4
        cost_tile.widget = monitoring_dashboard_v1.Widget()
        cost_tile.widget.title = "Daily Cost Trend"
        cost_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()

        cost_dataset = monitoring_dashboard_v1.XyChart.DataSet()
        cost_dataset.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery()
        cost_dataset.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        cost_dataset.timeSeriesQuery.timeSeriesFilter.filter = """
            metric.type="custom.googleapis.com/cost/daily_spend"
        """
        cost_dataset.timeSeriesQuery.timeSeriesFilter.aggregation = (
            monitoring_dashboard_v1.Aggregation()
        )
        cost_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.alignmentPeriod = {
            "seconds": 86400
        }
        cost_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.perSeriesAligner = (
            monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_SUM
        )
        cost_dataset.timeSeriesQuery.timeSeriesFilter.aggregation.groupByFields = [
            "metric.label.service"
        ]

        cost_tile.widget.xyChart.dataSets.append(cost_dataset)
        tiles.append(cost_tile)

        # Budget Utilization
        budget_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        budget_tile.yPos = 4
        budget_tile.width = 6
        budget_tile.height = 4
        budget_tile.widget = monitoring_dashboard_v1.Widget()
        budget_tile.widget.title = "Budget Utilization"
        budget_tile.widget.scorecard = monitoring_dashboard_v1.Scorecard()
        budget_tile.widget.scorecard.timeSeriesQuery = (
            monitoring_dashboard_v1.TimeSeriesQuery()
        )
        budget_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter = (
            monitoring_dashboard_v1.TimeSeriesFilter()
        )
        budget_tile.widget.scorecard.timeSeriesQuery.timeSeriesFilter.filter = """
            metric.type="custom.googleapis.com/budget/utilization_percent"
        """
        budget_tile.widget.scorecard.gaugeView = (
            monitoring_dashboard_v1.Scorecard.GaugeView()
        )
        budget_tile.widget.scorecard.gaugeView.lowerBound = 0.0
        budget_tile.widget.scorecard.gaugeView.upperBound = 100.0
        tiles.append(budget_tile)

        # Resource Utilization
        utilization_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
        utilization_tile.xPos = 6
        utilization_tile.yPos = 4
        utilization_tile.width = 6
        utilization_tile.height = 4
        utilization_tile.widget = monitoring_dashboard_v1.Widget()
        utilization_tile.widget.title = "Resource Utilization Efficiency"
        utilization_tile.widget.pieChart = monitoring_dashboard_v1.PieChart()
        utilization_tile.widget.pieChart.dataSets.append(
            monitoring_dashboard_v1.PieChart.PieChartDataSet(
                timeSeriesQuery=monitoring_dashboard_v1.TimeSeriesQuery(
                    timeSeriesFilter=monitoring_dashboard_v1.TimeSeriesFilter(
                        filter='metric.type="custom.googleapis.com/resource/efficiency_score"',
                        aggregation=monitoring_dashboard_v1.Aggregation(
                            alignmentPeriod={"seconds": 3600},
                            perSeriesAligner=monitoring_dashboard_v1.Aggregation.Aligner.ALIGN_MEAN,
                            groupByFields=["metric.label.resource_type"],
                        ),
                    )
                )
            )
        )
        tiles.append(utilization_tile)

        dashboard.mosaicLayout.tiles.extend(tiles)

        try:
            response = self.client.create_dashboard(
                parent=self.project_name, dashboard=dashboard
            )
            logger.info(f"Created cost dashboard: {response.name}")
            return response.name
        except exceptions.AlreadyExists:
            logger.info("Cost dashboard already exists")
            return f"{self.project_name}/dashboards/sentinelops-cost"

    def create_all_dashboards(self) -> Dict[str, str]:
        """Create all monitoring dashboards."""
        logger.info("Creating all monitoring dashboards...")

        dashboards = {}

        # Create overview dashboard
        dashboards["overview"] = self.create_overview_dashboard()

        # Create service-specific dashboards
        services = [
            "detection-agent",
            "analysis-agent",
            "communication-agent",
            "orchestration-agent",
        ]

        for service in services:
            dashboards[service] = self.create_service_dashboard(service)

        # Create specialized dashboards
        dashboards["security"] = self.create_security_dashboard()
        dashboards["cost"] = self.create_cost_dashboard()

        # Create summary
        summary = {
            "timestamp": os.environ.get("BUILD_TIMESTAMP", "manual"),
            "project_id": self.project_id,
            "dashboards_created": len(dashboards),
            "dashboard_urls": {},
        }

        # Generate console URLs
        for name, dashboard_id in dashboards.items():
            dashboard_name = dashboard_id.split("/")[-1]
            console_url = f"https://console.cloud.google.com/monitoring/dashboards/custom/{dashboard_name}?project={self.project_id}"
            summary["dashboard_urls"][name] = console_url

        # Save summary
        summary_path = os.path.join(os.path.dirname(__file__), "dashboard_summary.json")

        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Dashboard summary saved to: {summary_path}")

        return dashboards


def main():
    """Main function to create monitoring dashboards."""
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(
        description="Create monitoring dashboards for SentinelOps"
    )
    parser.add_argument(
        "--project-id",
        default=os.environ.get("GCP_PROJECT_ID", "sentinelops-project"),
        help="GCP Project ID",
    )
    parser.add_argument(
        "--dashboard",
        choices=["overview", "security", "cost", "all"],
        default="all",
        help="Which dashboard to create",
    )

    args = parser.parse_args()

    try:
        # Initialize dashboard creator
        creator = DashboardCreator(args.project_id)

        if args.dashboard == "all":
            dashboards = creator.create_all_dashboards()
            print("\nCreated dashboards:")
            for name, dashboard_id in dashboards.items():
                print("  {name}: {dashboard_id}")
        elif args.dashboard == "overview":
            dashboard_id = creator.create_overview_dashboard()
            print("Created overview dashboard: {dashboard_id}")
        elif args.dashboard == "security":
            dashboard_id = creator.create_security_dashboard()
            print("Created security dashboard: {dashboard_id}")
        elif args.dashboard == "cost":
            dashboard_id = creator.create_cost_dashboard()
            print("Created cost dashboard: {dashboard_id}")

        print(
            f"\nView dashboards at: https://console.cloud.google.com/monitoring/dashboards?project={args.project_id}"
        )

    except Exception as e:
        logger.error(f"Dashboard creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

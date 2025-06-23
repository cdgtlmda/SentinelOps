#!/usr/bin/env python3
"""Create Test Reporting Dashboard - Sets up monitoring dashboards for test metrics."""

import argparse
import json
import logging
import os
from typing import Any, Dict, List

try:
    from google.cloud import monitoring_dashboard_v1
except ImportError:
    print("Warning: Google Cloud monitoring dashboard library not installed.")
    monitoring_dashboard_v1 = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestReportingDashboard:
    """Creates and manages test reporting dashboards in Cloud Monitoring."""

    def __init__(self, project_id: str):
        """Initialize the dashboard creator."""
        self.project_id = project_id
        self.client = None

        if monitoring_dashboard_v1:
            try:
                self.client = monitoring_dashboard_v1.DashboardsServiceClient()
            except Exception as e:
                logger.warning(f"Failed to initialize dashboard client: {e}")

    def create_test_metrics_dashboard(self) -> str:
        """Create a comprehensive test metrics dashboard."""
        dashboard_config = {
            "displayName": "SentinelOps Test Metrics",
            "mosaicLayout": {
                "columns": 12,
                "tiles": [
                    self._create_test_pass_rate_tile(0, 0, 6, 4),
                    self._create_test_duration_tile(6, 0, 6, 4),
                    self._create_code_coverage_tile(0, 4, 6, 4),
                    self._create_test_failures_tile(6, 4, 6, 4),
                    self._create_flaky_tests_tile(0, 8, 12, 4),
                    self._create_test_trends_tile(0, 12, 12, 6),
                ],
            },
        }

        return self._create_dashboard(dashboard_config, "test-metrics")

    def create_performance_dashboard(self) -> str:
        """Create a performance testing dashboard."""
        dashboard_config = {
            "displayName": "SentinelOps Performance Testing",
            "mosaicLayout": {
                "columns": 12,
                "tiles": [
                    self._create_latency_percentiles_tile(0, 0, 6, 4),
                    self._create_throughput_tile(6, 0, 6, 4),
                    self._create_error_rate_tile(0, 4, 6, 4),
                    self._create_resource_usage_tile(6, 4, 6, 4),
                    self._create_performance_trends_tile(0, 8, 12, 6),
                ],
            },
        }

        return self._create_dashboard(dashboard_config, "performance-testing")

    def create_ci_pipeline_dashboard(self) -> str:
        """Create a CI/CD pipeline monitoring dashboard."""
        dashboard_config = {
            "displayName": "SentinelOps CI/CD Pipeline",
            "mosaicLayout": {
                "columns": 12,
                "tiles": [
                    self._create_build_success_rate_tile(0, 0, 4, 4),
                    self._create_build_duration_tile(4, 0, 4, 4),
                    self._create_deployment_frequency_tile(8, 0, 4, 4),
                    self._create_pipeline_stages_tile(0, 4, 12, 6),
                    self._create_failure_analysis_tile(0, 10, 12, 4),
                ],
            },
        }

        return self._create_dashboard(dashboard_config, "ci-pipeline")

    def _create_test_pass_rate_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing test pass rate."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Test Pass Rate",
                "scorecard": {
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": f'resource.project_id="{self.project_id}" '
                            'metric.type="custom.googleapis.com/sentinelops/test_pass_rate"',
                            "aggregation": {
                                "alignmentPeriod": "60s",
                                "perSeriesAligner": "ALIGN_MEAN",
                                "crossSeriesReducer": "REDUCE_MEAN",
                                "groupByFields": ["metric.label.branch"],
                            },
                        }
                    },
                    "gaugeView": {"lowerBound": 0.0, "upperBound": 100.0},
                },
            },
        }

    def _create_test_duration_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing test execution duration."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Test Execution Duration",
                "xyChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/test_duration"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                        "crossSeriesReducer": "REDUCE_MEAN",
                                        "groupByFields": ["metric.label.test_suite"],
                                    },
                                }
                            },
                            "plotType": "LINE",
                            "targetAxis": "Y1",
                        }
                    ],
                    "yAxis": {"label": "Duration (seconds)", "scale": "LINEAR"},
                },
            },
        }

    def _create_code_coverage_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing code coverage metrics."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Code Coverage",
                "xyChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/coverage_line"',
                                    "aggregation": {
                                        "alignmentPeriod": "300s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                        "crossSeriesReducer": "REDUCE_MEAN",
                                        "groupByFields": ["metric.label.branch"],
                                    },
                                }
                            },
                            "plotType": "LINE",
                            "targetAxis": "Y1",
                            "legendTemplate": "Line Coverage",
                        },
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/coverage_branch"',
                                    "aggregation": {
                                        "alignmentPeriod": "300s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                        "crossSeriesReducer": "REDUCE_MEAN",
                                        "groupByFields": ["metric.label.branch"],
                                    },
                                }
                            },
                            "plotType": "LINE",
                            "targetAxis": "Y1",
                            "legendTemplate": "Branch Coverage",
                        },
                    ],
                    "yAxis": {"label": "Coverage %", "scale": "LINEAR"},
                },
            },
        }

    def _create_test_failures_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing test failures."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Test Failures by Type",
                "pieChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/test_failed"',
                                    "aggregation": {
                                        "alignmentPeriod": "3600s",
                                        "perSeriesAligner": "ALIGN_SUM",
                                        "crossSeriesReducer": "REDUCE_SUM",
                                        "groupByFields": ["metric.label.test_type"],
                                    },
                                }
                            }
                        }
                    ]
                },
            },
        }

    def _create_flaky_tests_tile(self, x: int, y: int, width: int, height: int) -> Dict:
        """Create a tile showing flaky tests."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Flaky Test Detection",
                "scorecard": {
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": f'resource.project_id="{self.project_id}" '
                            'metric.type="custom.googleapis.com/sentinelops/flaky_test_count"',
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_MAX",
                            },
                        }
                    },
                    "sparkChartView": {"sparkChartType": "SPARK_BAR"},
                },
            },
        }

    def _create_test_trends_tile(self, x: int, y: int, width: int, height: int) -> Dict:
        """Create a tile showing test trends over time."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Test Execution Trends",
                "xyChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/test_total"',
                                    "aggregation": {
                                        "alignmentPeriod": "3600s",
                                        "perSeriesAligner": "ALIGN_SUM",
                                        "crossSeriesReducer": "REDUCE_SUM",
                                        "groupByFields": ["metric.label.branch"],
                                    },
                                }
                            },
                            "plotType": "STACKED_BAR",
                            "targetAxis": "Y1",
                        }
                    ],
                    "yAxis": {"label": "Test Count", "scale": "LINEAR"},
                },
            },
        }

    def _create_latency_percentiles_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing latency percentiles."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "API Latency Percentiles",
                "xyChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/api_latency"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_DELTA",
                                        "crossSeriesReducer": "REDUCE_PERCENTILE_95",
                                        "groupByFields": ["metric.label.endpoint"],
                                    },
                                }
                            },
                            "plotType": "LINE",
                            "targetAxis": "Y1",
                        }
                    ],
                    "yAxis": {"label": "Latency (ms)", "scale": "LINEAR"},
                },
            },
        }

    def _create_throughput_tile(self, x: int, y: int, width: int, height: int) -> Dict:
        """Create a tile showing throughput metrics."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "System Throughput",
                "xyChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/requests_per_second"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_RATE",
                                        "crossSeriesReducer": "REDUCE_SUM",
                                        "groupByFields": ["metric.label.service"],
                                    },
                                }
                            },
                            "plotType": "LINE",
                            "targetAxis": "Y1",
                        }
                    ],
                    "yAxis": {"label": "Requests/sec", "scale": "LINEAR"},
                },
            },
        }

    def _create_error_rate_tile(self, x: int, y: int, width: int, height: int) -> Dict:
        """Create a tile showing error rates."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Error Rate",
                "scorecard": {
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": f'resource.project_id="{self.project_id}" '
                            'metric.type="custom.googleapis.com/sentinelops/error_rate"',
                            "aggregation": {
                                "alignmentPeriod": "300s",
                                "perSeriesAligner": "ALIGN_MEAN",
                                "crossSeriesReducer": "REDUCE_MEAN",
                            },
                        }
                    },
                    "thresholds": [
                        {"value": 1.0, "color": "YELLOW"},
                        {"value": 5.0, "color": "RED"},
                    ],
                },
            },
        }

    def _create_resource_usage_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing resource usage."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Resource Usage",
                "xyChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/cpu_usage"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                        "crossSeriesReducer": "REDUCE_MEAN",
                                        "groupByFields": ["metric.label.service"],
                                    },
                                }
                            },
                            "plotType": "LINE",
                            "targetAxis": "Y1",
                            "legendTemplate": "CPU",
                        },
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/memory_usage"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                        "crossSeriesReducer": "REDUCE_MEAN",
                                        "groupByFields": ["metric.label.service"],
                                    },
                                }
                            },
                            "plotType": "LINE",
                            "targetAxis": "Y2",
                            "legendTemplate": "Memory",
                        },
                    ],
                    "yAxis": {"label": "CPU %", "scale": "LINEAR"},
                    "y2Axis": {"label": "Memory MB", "scale": "LINEAR"},
                },
            },
        }

    def _create_performance_trends_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing performance trends."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Performance Trends",
                "xyChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/performance_score"',
                                    "aggregation": {
                                        "alignmentPeriod": "3600s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                        "crossSeriesReducer": "REDUCE_MEAN",
                                        "groupByFields": ["metric.label.test_name"],
                                    },
                                }
                            },
                            "plotType": "LINE",
                            "targetAxis": "Y1",
                        }
                    ],
                    "yAxis": {"label": "Performance Score", "scale": "LINEAR"},
                },
            },
        }

    def _create_build_success_rate_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing build success rate."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Build Success Rate",
                "scorecard": {
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": f'resource.project_id="{self.project_id}" '
                            'metric.type="custom.googleapis.com/sentinelops/build_success_rate"',
                            "aggregation": {
                                "alignmentPeriod": "3600s",
                                "perSeriesAligner": "ALIGN_MEAN",
                            },
                        }
                    },
                    "gaugeView": {"lowerBound": 0.0, "upperBound": 100.0},
                },
            },
        }

    def _create_build_duration_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing build duration."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Average Build Duration",
                "scorecard": {
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": f'resource.project_id="{self.project_id}" '
                            'metric.type="custom.googleapis.com/sentinelops/build_duration"',
                            "aggregation": {
                                "alignmentPeriod": "300s",
                                "perSeriesAligner": "ALIGN_MEAN",
                            },
                        }
                    },
                    "sparkChartView": {"sparkChartType": "SPARK_LINE"},
                },
            },
        }

    def _create_deployment_frequency_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing deployment frequency."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Deployment Frequency",
                "scorecard": {
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": f'resource.project_id="{self.project_id}" '
                            'metric.type="custom.googleapis.com/sentinelops/deployments_per_day"',
                            "aggregation": {
                                "alignmentPeriod": "86400s",
                                "perSeriesAligner": "ALIGN_SUM",
                            },
                        }
                    }
                },
            },
        }

    def _create_pipeline_stages_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing pipeline stage durations."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Pipeline Stage Durations",
                "xyChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/stage_duration"',
                                    "aggregation": {
                                        "alignmentPeriod": "300s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                        "crossSeriesReducer": "REDUCE_MEAN",
                                        "groupByFields": ["metric.label.stage_name"],
                                    },
                                }
                            },
                            "plotType": "STACKED_BAR",
                            "targetAxis": "Y1",
                        }
                    ],
                    "yAxis": {"label": "Duration (seconds)", "scale": "LINEAR"},
                },
            },
        }

    def _create_failure_analysis_tile(
        self, x: int, y: int, width: int, height: int
    ) -> Dict:
        """Create a tile showing failure analysis."""
        return {
            "xPos": x,
            "yPos": y,
            "width": width,
            "height": height,
            "widget": {
                "title": "Failure Analysis",
                "pieChart": {
                    "dataSets": [
                        {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": f'resource.project_id="{self.project_id}" '
                                    'metric.type="custom.googleapis.com/sentinelops/failure_reason"',
                                    "aggregation": {
                                        "alignmentPeriod": "86400s",
                                        "perSeriesAligner": "ALIGN_SUM",
                                        "crossSeriesReducer": "REDUCE_SUM",
                                        "groupByFields": ["metric.label.reason"],
                                    },
                                }
                            }
                        }
                    ]
                },
            },
        }

    def _create_dashboard(self, config: Dict[str, Any], dashboard_id: str) -> str:
        """Create a dashboard with the given configuration."""
        if not self.client:
            logger.warning(
                "Dashboard client not available, skipping dashboard creation"
            )
            return f"mock-dashboard-{dashboard_id}"

        try:
            parent = f"projects/{self.project_id}"
            dashboard = monitoring_dashboard_v1.Dashboard(config)

            # Check if dashboard already exists
            dashboards = self.client.list_dashboards(parent=parent)
            for existing in dashboards:
                if existing.display_name == config["displayName"]:
                    logger.info(f"Dashboard '{config['displayName']}' already exists")
                    return existing.name

            # Create new dashboard
            response = self.client.create_dashboard(parent=parent, dashboard=dashboard)

            logger.info(f"Created dashboard: {response.name}")
            return response.name

        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            return ""

    def create_all_dashboards(self) -> List[str]:
        """Create all test reporting dashboards."""
        dashboards = []

        # Create test metrics dashboard
        dashboard_id = self.create_test_metrics_dashboard()
        if dashboard_id:
            dashboards.append(dashboard_id)
            logger.info("Created test metrics dashboard")

        # Create performance dashboard
        dashboard_id = self.create_performance_dashboard()
        if dashboard_id:
            dashboards.append(dashboard_id)
            logger.info("Created performance testing dashboard")

        # Create CI pipeline dashboard
        dashboard_id = self.create_ci_pipeline_dashboard()
        if dashboard_id:
            dashboards.append(dashboard_id)
            logger.info("Created CI/CD pipeline dashboard")

        return dashboards


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create test reporting dashboards")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument(
        "--dashboard",
        choices=["test-metrics", "performance", "ci-pipeline", "all"],
        default="all",
        help="Dashboard to create",
    )

    args = parser.parse_args()

    # Initialize dashboard creator
    creator = TestReportingDashboard(args.project_id)

    # Create requested dashboards
    if args.dashboard == "all":
        dashboards = creator.create_all_dashboards()
        print(f"Created {len(dashboards)} dashboards")
    elif args.dashboard == "test-metrics":
        dashboard_id = creator.create_test_metrics_dashboard()
        print(f"Created test metrics dashboard: {dashboard_id}")
    elif args.dashboard == "performance":
        dashboard_id = creator.create_performance_dashboard()
        print(f"Created performance dashboard: {dashboard_id}")
    elif args.dashboard == "ci-pipeline":
        dashboard_id = creator.create_ci_pipeline_dashboard()
        print(f"Created CI/CD pipeline dashboard: {dashboard_id}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test Metrics Collector - Collects and publishes test execution metrics."""

import argparse
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from google.cloud import (
        bigquery,
        error_reporting,
        firestore,
        monitoring_v3,
        storage,
    )
except ImportError:
    print("Warning: Google Cloud libraries not installed. Running in mock mode.")
    monitoring_v3 = None
    storage = None
    bigquery = None
    firestore = None
    error_reporting = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestMetricsCollector:
    """Collects and publishes test execution metrics to various GCP services."""

    def __init__(self, project_id: str):
        """Initialize the metrics collector."""
        self.project_id = project_id
        self.metrics_client = None
        self.storage_client = None
        self.bigquery_client = None
        self.firestore_client = None
        self.error_client = None

        if monitoring_v3:
            try:
                self.metrics_client = monitoring_v3.MetricServiceClient()
                self.storage_client = storage.Client(project=project_id)
                self.bigquery_client = bigquery.Client(project=project_id)
                self.firestore_client = firestore.Client(project=project_id)
                self.error_client = error_reporting.Client(project=project_id)
            except Exception as e:
                logger.warning(f"Failed to initialize GCP clients: {e}")

    def parse_pytest_json_report(self, report_path: str) -> Dict[str, Any]:
        """Parse pytest JSON report file."""
        with open(report_path, "r") as f:
            data = json.load(f)

        summary = data.get("summary", {})
        tests = data.get("tests", [])

        # Calculate metrics
        total_tests = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)
        errors = summary.get("error", 0)
        duration = data.get("duration", 0)

        # Extract test details
        failed_tests = []
        slow_tests = []

        for test in tests:
            if test.get("outcome") == "failed":
                failed_tests.append(
                    {
                        "nodeid": test.get("nodeid"),
                        "duration": test.get("duration"),
                        "message": test.get("call", {}).get(
                            "longrepr", "No error message"
                        ),
                    }
                )

            # Consider tests > 5 seconds as slow
            if test.get("duration", 0) > 5.0:
                slow_tests.append(
                    {"nodeid": test.get("nodeid"), "duration": test.get("duration")}
                )

        return {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "duration": duration,
            "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "failed_tests": failed_tests,
            "slow_tests": slow_tests,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def parse_coverage_xml(self, coverage_path: str) -> Dict[str, Any]:
        """Parse coverage XML report."""
        tree = ET.parse(coverage_path)
        root = tree.getroot()

        # Extract coverage metrics
        coverage_percent = float(root.get("line-rate", 0)) * 100
        branch_coverage = float(root.get("branch-rate", 0)) * 100

        # Extract package-level coverage
        packages = []
        for package in root.findall(".//package"):
            pkg_name = package.get("name")
            pkg_line_rate = float(package.get("line-rate", 0)) * 100
            pkg_branch_rate = float(package.get("branch-rate", 0)) * 100

            packages.append(
                {
                    "name": pkg_name,
                    "line_coverage": pkg_line_rate,
                    "branch_coverage": pkg_branch_rate,
                }
            )

        # Find uncovered files
        uncovered_files = []
        for cls in root.findall(".//class"):
            line_rate = float(cls.get("line-rate", 0))
            if line_rate < 1.0:
                uncovered_files.append(
                    {"filename": cls.get("filename"), "coverage": line_rate * 100}
                )

        return {
            "line_coverage": coverage_percent,
            "branch_coverage": branch_coverage,
            "packages": packages,
            "uncovered_files": sorted(uncovered_files, key=lambda x: x["coverage"])[
                :10
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def send_metrics_to_monitoring(self, metrics: Dict[str, Any], metric_type: str):
        """Send metrics to Cloud Monitoring."""
        if not self.metrics_client:
            logger.info("Skipping Cloud Monitoring (not available)")
            return

        try:
            project_name = f"projects/{self.project_id}"

            # Create time series
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/sentinelops/{metric_type}"
            series.resource.type = "global"
            series.resource.labels["project_id"] = self.project_id

            # Add metric labels
            series.metric.labels["build_id"] = os.environ.get("GITHUB_RUN_ID", "local")
            series.metric.labels["branch"] = os.environ.get(
                "GITHUB_REF_NAME", "unknown"
            )
            series.metric.labels["commit"] = os.environ.get("GITHUB_SHA", "unknown")[:8]

            # Create points based on metric type
            now = datetime.utcnow()
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": int(now.timestamp())}}
            )

            if metric_type == "test_execution":
                # Test execution metrics
                points = [
                    self._create_point(interval, "test_total", metrics["total_tests"]),
                    self._create_point(interval, "test_passed", metrics["passed"]),
                    self._create_point(interval, "test_failed", metrics["failed"]),
                    self._create_point(interval, "test_duration", metrics["duration"]),
                    self._create_point(
                        interval, "test_pass_rate", metrics["pass_rate"]
                    ),
                ]
            elif metric_type == "coverage":
                # Coverage metrics
                points = [
                    self._create_point(
                        interval, "coverage_line", metrics["line_coverage"]
                    ),
                    self._create_point(
                        interval, "coverage_branch", metrics["branch_coverage"]
                    ),
                ]
            else:
                logger.warning(f"Unknown metric type: {metric_type}")
                return

            # Send each metric
            for point, metric_name in points:
                series_copy = monitoring_v3.TimeSeries()
                series_copy.CopyFrom(series)
                series_copy.metric.type = (
                    f"custom.googleapis.com/sentinelops/{metric_name}"
                )
                series_copy.points = [point]

                self.metrics_client.create_time_series(
                    name=project_name, time_series=[series_copy]
                )

            logger.info(f"Successfully sent {len(points)} metrics to Cloud Monitoring")

        except Exception as e:
            logger.error(f"Failed to send metrics to Cloud Monitoring: {e}")

    def _create_point(self, interval, metric_name: str, value: float):
        """Create a monitoring point."""
        point = monitoring_v3.Point(
            {"interval": interval, "value": {"double_value": value}}
        )
        return (point, metric_name)

    def save_to_bigquery(self, metrics: Dict[str, Any], table_name: str):
        """Save metrics to BigQuery."""
        if not self.bigquery_client:
            logger.info("Skipping BigQuery (not available)")
            return

        try:
            dataset_id = "test_metrics"
            table_id = f"{self.project_id}.{dataset_id}.{table_name}"

            # Add metadata
            metrics["build_id"] = os.environ.get("GITHUB_RUN_ID", "local")
            metrics["branch"] = os.environ.get("GITHUB_REF_NAME", "unknown")
            metrics["commit_sha"] = os.environ.get("GITHUB_SHA", "unknown")
            metrics["actor"] = os.environ.get("GITHUB_ACTOR", "unknown")
            metrics["workflow"] = os.environ.get("GITHUB_WORKFLOW", "unknown")
            metrics["event_name"] = os.environ.get("GITHUB_EVENT_NAME", "unknown")

            # Insert row
            errors = self.bigquery_client.insert_rows_json(table_id, [metrics])

            if errors:
                logger.error(f"Failed to insert rows to BigQuery: {errors}")
            else:
                logger.info(f"Successfully saved metrics to BigQuery table {table_id}")

        except Exception as e:
            logger.error(f"Failed to save to BigQuery: {e}")

    def save_to_firestore(self, metrics: Dict[str, Any], collection: str):
        """Save metrics to Firestore."""
        if not self.firestore_client:
            logger.info("Skipping Firestore (not available)")
            return

        try:
            # Create document reference
            doc_ref = self.firestore_client.collection(collection).document()

            # Add metadata
            metrics["build_id"] = os.environ.get("GITHUB_RUN_ID", "local")
            metrics["branch"] = os.environ.get("GITHUB_REF_NAME", "unknown")
            metrics["commit_sha"] = os.environ.get("GITHUB_SHA", "unknown")

            # Save document
            doc_ref.set(metrics)

            logger.info(
                f"Successfully saved metrics to Firestore collection {collection}"
            )

        except Exception as e:
            logger.error(f"Failed to save to Firestore: {e}")

    def track_test_failures(self, failed_tests: List[Dict[str, Any]]):
        """Track test failures for analysis."""
        if not failed_tests:
            return

        # Log to error reporting
        if self.error_client:
            for test in failed_tests:
                try:
                    self.error_client.report(
                        f"Test failed: {test['nodeid']}\n{test['message']}",
                        user=os.environ.get("GITHUB_ACTOR", "unknown"),
                    )
                except Exception as e:
                    logger.error(f"Failed to report error: {e}")

        # Save failure patterns to Firestore
        if self.firestore_client:
            try:
                for test in failed_tests:
                    # Create failure record
                    failure_record = {
                        "test_name": test["nodeid"],
                        "duration": test["duration"],
                        "message": test["message"][:1000],  # Truncate long messages
                        "timestamp": datetime.utcnow(),
                        "build_id": os.environ.get("GITHUB_RUN_ID", "local"),
                        "branch": os.environ.get("GITHUB_REF_NAME", "unknown"),
                        "commit_sha": os.environ.get("GITHUB_SHA", "unknown"),
                    }

                    # Save to failures collection
                    self.firestore_client.collection("test_failures").add(
                        failure_record
                    )

            except Exception as e:
                logger.error(f"Failed to track test failures: {e}")

    def get_historical_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get historical test metrics for comparison."""
        if not self.bigquery_client:
            return {}

        try:
            query = f"""
            SELECT 
                AVG(pass_rate) as avg_pass_rate,
                AVG(duration) as avg_duration,
                AVG(line_coverage) as avg_coverage,
                COUNT(*) as build_count
            FROM `{self.project_id}.test_metrics.test_results`
            WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
                AND branch = @branch
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "branch", "STRING", os.environ.get("GITHUB_REF_NAME", "main")
                    )
                ]
            )

            query_job = self.bigquery_client.query(query, job_config=job_config)
            results = list(query_job)

            if results:
                row = results[0]
                return {
                    "avg_pass_rate": row.avg_pass_rate or 0,
                    "avg_duration": row.avg_duration or 0,
                    "avg_coverage": row.avg_coverage or 0,
                    "build_count": row.build_count or 0,
                }

        except Exception as e:
            logger.error(f"Failed to get historical metrics: {e}")

        return {}

    def generate_summary_report(
        self,
        test_metrics: Dict[str, Any],
        coverage_metrics: Dict[str, Any],
        historical_metrics: Dict[str, Any],
    ) -> str:
        """Generate a summary report of test metrics."""
        report = f"""# Test Metrics Summary

## Test Execution Results
- **Total Tests**: {test_metrics['total_tests']}
- **Passed**: {test_metrics['passed']} ✅
- **Failed**: {test_metrics['failed']} ❌
- **Skipped**: {test_metrics['skipped']} ⏭️
- **Pass Rate**: {test_metrics['pass_rate']:.2f}%
- **Duration**: {test_metrics['duration']:.2f}s

## Code Coverage
- **Line Coverage**: {coverage_metrics['line_coverage']:.2f}%
- **Branch Coverage**: {coverage_metrics['branch_coverage']:.2f}%
"""

        # Add historical comparison if available
        if historical_metrics:
            report += f"""
## Historical Comparison (Last {historical_metrics.get('build_count', 0)} builds)
- **Average Pass Rate**: {historical_metrics['avg_pass_rate']:.2f}%
- **Average Duration**: {historical_metrics['avg_duration']:.2f}s
- **Average Coverage**: {historical_metrics['avg_coverage']:.2f}%
"""

        # Add failed tests if any
        if test_metrics["failed_tests"]:
            report += "\n## Failed Tests\n"
            for test in test_metrics["failed_tests"][:5]:  # Show top 5
                report += f"- `{test['nodeid']}` ({test['duration']:.2f}s)\n"

        # Add slow tests if any
        if test_metrics["slow_tests"]:
            report += "\n## Slow Tests (>5s)\n"
            for test in test_metrics["slow_tests"][:5]:  # Show top 5
                report += f"- `{test['nodeid']}` ({test['duration']:.2f}s)\n"

        # Add low coverage files
        if coverage_metrics["uncovered_files"]:
            report += "\n## Files with Low Coverage\n"
            for file in coverage_metrics["uncovered_files"][:5]:  # Show top 5
                report += f"- `{file['filename']}` ({file['coverage']:.2f}%)\n"

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Collect and publish test metrics")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--test-report", help="Path to pytest JSON report")
    parser.add_argument("--coverage-report", help="Path to coverage XML report")
    parser.add_argument("--build-id", help="Build ID for tracking")
    parser.add_argument(
        "--historical-days",
        type=int,
        default=7,
        help="Days of historical data to compare",
    )

    args = parser.parse_args()

    # Initialize collector
    collector = TestMetricsCollector(args.project_id)

    # Collect metrics
    test_metrics = {}
    coverage_metrics = {}

    if args.test_report and os.path.exists(args.test_report):
        logger.info(f"Processing test report: {args.test_report}")
        test_metrics = collector.parse_pytest_json_report(args.test_report)

        # Send to monitoring
        collector.send_metrics_to_monitoring(test_metrics, "test_execution")

        # Save to BigQuery
        collector.save_to_bigquery(test_metrics, "test_results")

        # Save to Firestore
        collector.save_to_firestore(test_metrics, "test_runs")

        # Track failures
        collector.track_test_failures(test_metrics.get("failed_tests", []))

    if args.coverage_report and os.path.exists(args.coverage_report):
        logger.info(f"Processing coverage report: {args.coverage_report}")
        coverage_metrics = collector.parse_coverage_xml(args.coverage_report)

        # Send to monitoring
        collector.send_metrics_to_monitoring(coverage_metrics, "coverage")

        # Save to BigQuery
        collector.save_to_bigquery(coverage_metrics, "coverage_results")

    # Get historical metrics
    historical_metrics = collector.get_historical_metrics(args.historical_days)

    # Generate summary report
    if test_metrics or coverage_metrics:
        summary = collector.generate_summary_report(
            test_metrics
            or {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "pass_rate": 0,
                "duration": 0,
                "failed_tests": [],
                "slow_tests": [],
            },
            coverage_metrics
            or {
                "line_coverage": 0,
                "branch_coverage": 0,
                "packages": [],
                "uncovered_files": [],
            },
            historical_metrics,
        )

        print("\n" + summary)

        # Save summary to file
        with open("test-metrics-summary.md", "w") as f:
            f.write(summary)

    logger.info("Test metrics collection completed")


if __name__ == "__main__":
    main()

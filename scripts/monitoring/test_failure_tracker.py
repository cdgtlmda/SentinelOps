#!/usr/bin/env python3
"""Test Failure Tracker - Tracks and analyzes test failures over time."""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from google.cloud import bigquery, firestore, monitoring_v3
except ImportError:
    print("Warning: Google Cloud libraries not installed. Running in mock mode.")
    firestore = None
    bigquery = None
    monitoring_v3 = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestFailureTracker:
    """Tracks and analyzes test failures to identify patterns and flaky tests."""

    def __init__(self, project_id: Optional[str] = None):
        """Initialize the failure tracker."""
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID")
        self.firestore_client = None
        self.bigquery_client = None
        self.monitoring_client = None

        if self.project_id and firestore:
            try:
                self.firestore_client = firestore.Client(project=self.project_id)
                self.bigquery_client = bigquery.Client(project=self.project_id)
                self.monitoring_client = monitoring_v3.MetricServiceClient()
            except Exception as e:
                logger.warning(f"Failed to initialize GCP clients: {e}")

    def record_failure(
        self,
        test_name: str,
        error_message: str,
        duration: float = 0.0,
        metadata: Dict[str, Any] = None,
    ):
        """Record a test failure."""
        if not self.firestore_client:
            logger.info("Skipping failure recording (Firestore not available)")
            return

        try:
            failure_data = {
                "test_name": test_name,
                "error_message": error_message[:1000],  # Truncate long messages
                "duration": duration,
                "timestamp": datetime.utcnow(),
                "build_id": os.environ.get("GITHUB_RUN_ID", "local"),
                "branch": os.environ.get("GITHUB_REF_NAME", "unknown"),
                "commit_sha": os.environ.get("GITHUB_SHA", "unknown"),
                "actor": os.environ.get("GITHUB_ACTOR", "unknown"),
                "workflow": os.environ.get("GITHUB_WORKFLOW", "unknown"),
                "metadata": metadata or {},
            }

            # Save to Firestore
            self.firestore_client.collection("test_failures").add(failure_data)
            logger.info(f"Recorded failure for test: {test_name}")

        except Exception as e:
            logger.error(f"Failed to record test failure: {e}")

    def analyze_failures(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze test failures over the specified time period."""
        if not self.firestore_client:
            logger.info("Skipping failure analysis (Firestore not available)")
            return self._get_mock_analysis()

        try:
            # Query recent failures
            start_time = datetime.utcnow() - timedelta(hours=hours)
            failures_ref = self.firestore_client.collection("test_failures")
            query = failures_ref.where("timestamp", ">=", start_time)

            failures = []
            for doc in query.stream():
                failures.append(doc.to_dict())

            # Analyze patterns
            analysis = self._analyze_failure_patterns(failures)

            # Identify flaky tests
            flaky_tests = self._identify_flaky_tests(failures)
            analysis["flaky_tests"] = flaky_tests

            # Calculate failure trends
            trends = self._calculate_failure_trends(failures)
            analysis["trends"] = trends

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze failures: {e}")
            return self._get_mock_analysis()

    def _analyze_failure_patterns(
        self, failures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze patterns in test failures."""
        if not failures:
            return {
                "total_failures": 0,
                "unique_tests": 0,
                "failure_rate": 0,
                "common_errors": [],
                "affected_branches": [],
                "failure_by_test": {},
            }

        # Count failures by test
        failure_counts = defaultdict(int)
        error_patterns = defaultdict(int)
        branch_failures = defaultdict(int)

        for failure in failures:
            test_name = failure.get("test_name", "unknown")
            error_msg = failure.get("error_message", "")
            branch = failure.get("branch", "unknown")

            failure_counts[test_name] += 1
            branch_failures[branch] += 1

            # Extract error pattern (first line of error)
            error_pattern = error_msg.split("\n")[0][:100]
            if error_pattern:
                error_patterns[error_pattern] += 1

        # Sort by frequency
        sorted_failures = sorted(
            failure_counts.items(), key=lambda x: x[1], reverse=True
        )
        sorted_errors = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
        sorted_branches = sorted(
            branch_failures.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "total_failures": len(failures),
            "unique_tests": len(failure_counts),
            "failure_rate": len(failures)
            / max(len(set(f.get("build_id") for f in failures)), 1),
            "common_errors": [{"pattern": p, "count": c} for p, c in sorted_errors[:5]],
            "affected_branches": [
                {"branch": b, "count": c} for b, c in sorted_branches
            ],
            "failure_by_test": dict(sorted_failures[:10]),  # Top 10 failing tests
        }

    def _identify_flaky_tests(
        self, failures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify potentially flaky tests based on failure patterns."""
        # Group failures by test and build
        test_builds = defaultdict(lambda: {"passes": 0, "failures": 0, "builds": set()})

        for failure in failures:
            test_name = failure.get("test_name", "unknown")
            build_id = failure.get("build_id", "unknown")
            test_builds[test_name]["failures"] += 1
            test_builds[test_name]["builds"].add(build_id)

        # Query for successful runs (this is approximate without full test results)
        # In a real implementation, we'd also track successful test runs

        flaky_tests = []
        for test_name, stats in test_builds.items():
            build_count = len(stats["builds"])
            failure_count = stats["failures"]

            # Consider a test flaky if it fails intermittently (not every build)
            if build_count > 1 and failure_count < build_count * 2:
                flakiness_score = (failure_count / build_count) * 100
                if 20 < flakiness_score < 80:  # Fails 20-80% of the time
                    flaky_tests.append(
                        {
                            "test_name": test_name,
                            "failure_count": failure_count,
                            "build_count": build_count,
                            "flakiness_score": flakiness_score,
                        }
                    )

        # Sort by flakiness score
        return sorted(flaky_tests, key=lambda x: x["flakiness_score"], reverse=True)

    def _calculate_failure_trends(
        self, failures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate failure trends over time."""
        if not failures:
            return {"hourly": [], "daily": []}

        # Group failures by hour
        hourly_failures = defaultdict(int)
        daily_failures = defaultdict(int)

        for failure in failures:
            timestamp = failure.get("timestamp")
            if isinstance(timestamp, datetime):
                hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                day_key = timestamp.strftime("%Y-%m-%d")
                hourly_failures[hour_key] += 1
                daily_failures[day_key] += 1

        # Convert to sorted lists
        hourly_trend = sorted(
            [{"hour": k, "count": v} for k, v in hourly_failures.items()],
            key=lambda x: x["hour"],
        )

        daily_trend = sorted(
            [{"day": k, "count": v} for k, v in daily_failures.items()],
            key=lambda x: x["day"],
        )

        return {
            "hourly": hourly_trend[-24:],  # Last 24 hours
            "daily": daily_trend[-7:],  # Last 7 days
        }

    def _get_mock_analysis(self) -> Dict[str, Any]:
        """Return mock analysis data for testing."""
        return {
            "total_failures": 0,
            "unique_tests": 0,
            "failure_rate": 0,
            "common_errors": [],
            "affected_branches": [],
            "failure_by_test": {},
            "flaky_tests": [],
            "trends": {"hourly": [], "daily": []},
        }

    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable report from the analysis."""
        report = f"""# Test Failure Analysis Report

Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Summary
- **Total Failures**: {analysis['total_failures']}
- **Unique Failing Tests**: {analysis['unique_tests']}
- **Average Failure Rate**: {analysis['failure_rate']:.2f} per build

## Top Failing Tests
"""

        # Add failing tests
        for test, count in list(analysis["failure_by_test"].items())[:10]:
            report += f"- `{test}`: {count} failures\n"

        # Add common errors
        if analysis["common_errors"]:
            report += "\n## Common Error Patterns\n"
            for error in analysis["common_errors"]:
                report += f"- `{error['pattern']}`: {error['count']} occurrences\n"

        # Add flaky tests
        if analysis["flaky_tests"]:
            report += "\n## Potentially Flaky Tests\n"
            for test in analysis["flaky_tests"][:5]:
                report += f"- `{test['test_name']}`: {test['flakiness_score']:.1f}% flakiness score\n"

        # Add affected branches
        if analysis["affected_branches"]:
            report += "\n## Affected Branches\n"
            for branch in analysis["affected_branches"]:
                report += f"- `{branch['branch']}`: {branch['count']} failures\n"

        return report

    def alert_on_failure_spike(self, threshold: int = 10):
        """Alert if failure count exceeds threshold in the last hour."""
        if not self.monitoring_client:
            logger.info("Skipping failure spike alerting (monitoring not available)")
            return

        try:
            # Query failures in last hour
            analysis = self.analyze_failures(hours=1)

            if analysis["total_failures"] > threshold:
                # Send alert metric
                project_name = f"projects/{self.project_id}"
                series = monitoring_v3.TimeSeries()
                series.metric.type = (
                    "custom.googleapis.com/sentinelops/test_failure_spike"
                )
                series.resource.type = "global"
                series.resource.labels["project_id"] = self.project_id

                now = datetime.utcnow()
                interval = monitoring_v3.TimeInterval(
                    {"end_time": {"seconds": int(now.timestamp())}}
                )
                point = monitoring_v3.Point(
                    {
                        "interval": interval,
                        "value": {"int64_value": analysis["total_failures"]},
                    }
                )
                series.points = [point]

                self.monitoring_client.create_time_series(
                    name=project_name, time_series=[series]
                )

                logger.warning(
                    f"Test failure spike detected: {analysis['total_failures']} failures"
                )

        except Exception as e:
            logger.error(f"Failed to check for failure spike: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Track and analyze test failures")
    parser.add_argument(
        "action", choices=["record", "analyze", "report"], help="Action to perform"
    )
    parser.add_argument("--project-id", help="GCP project ID")
    parser.add_argument("--test-name", help="Test name (for record action)")
    parser.add_argument("--error-message", help="Error message (for record action)")
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours to analyze (for analyze action)"
    )
    parser.add_argument(
        "--threshold", type=int, default=10, help="Failure spike threshold"
    )

    args = parser.parse_args()

    # Initialize tracker
    tracker = TestFailureTracker(args.project_id)

    if args.action == "record":
        if not args.test_name or not args.error_message:
            parser.error("--test-name and --error-message required for record action")
        tracker.record_failure(args.test_name, args.error_message)

    elif args.action == "analyze":
        analysis = tracker.analyze_failures(args.hours)
        print(json.dumps(analysis, indent=2, default=str))

        # Check for failure spike
        tracker.alert_on_failure_spike(args.threshold)

    elif args.action == "report":
        analysis = tracker.analyze_failures(args.hours)
        report = tracker.generate_report(analysis)
        print(report)

        # Save report to file
        with open("test-failure-report.md", "w") as f:
            f.write(report)


if __name__ == "__main__":
    main()

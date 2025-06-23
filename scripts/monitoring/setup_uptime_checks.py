#!/usr/bin/env python3
"""
Set Up Uptime Checks for SentinelOps

This script creates uptime checks for all SentinelOps services to monitor
availability and response times.
"""

import json
import os
import sys
from typing import Any, Dict, List

from google.api_core import exceptions
from google.cloud import monitoring_v3

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.logger import Logger  # noqa: E402

# Initialize logger
logger = Logger(__name__).logger


class UptimeCheckManager:
    """Manages uptime checks for SentinelOps services."""

    def __init__(self, project_id: str):
        """
        Initialize Uptime Check Manager.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.client = monitoring_v3.UptimeCheckServiceClient()
        self.project_path = f"projects/{project_id}"

    def create_http_uptime_check(
        self,
        display_name: str,
        host: str,
        path: str = "/health",
        port: int = 443,
        use_ssl: bool = True,
        check_interval: int = 60,
    ) -> str:
        """
        Create an HTTP(S) uptime check.

        Args:
            display_name: Display name for the uptime check
            host: Hostname to check
            path: Path to check (default: /health)
            port: Port number (default: 443)
            use_ssl: Use HTTPS (default: True)
            check_interval: Check interval in seconds (default: 60)

        Returns:
            Name of created uptime check
        """
        logger.info(f"Creating uptime check for {display_name}...")

        # Create uptime check configuration
        config = monitoring_v3.UptimeCheckConfig()
        config.display_name = display_name
        config.timeout = {"seconds": 10}
        config.period = {"seconds": check_interval}

        # Configure monitored resource
        config.monitored_resource = monitoring_v3.MonitoredResource()
        config.monitored_resource.type = "uptime_url"
        config.monitored_resource.labels = {"project_id": self.project_id, "host": host}

        # Configure HTTP check
        config.http_check = monitoring_v3.UptimeCheckConfig.HttpCheck()
        config.http_check.path = path
        config.http_check.port = port
        config.http_check.use_ssl = use_ssl
        config.http_check.validate_ssl = use_ssl

        # Add request method
        config.http_check.request_method = (
            monitoring_v3.UptimeCheckConfig.HttpCheck.RequestMethod.GET
        )

        # Add headers for authentication if needed
        config.http_check.headers = {"User-Agent": "SentinelOps-UptimeCheck/1.0"}

        # Configure response validation
        config.http_check.accepted_response_status_codes.append(
            monitoring_v3.UptimeCheckConfig.HttpCheck.ResponseStatusCode(
                status_value=200
            )
        )

        # Configure content matchers
        config.content_matchers.append(
            monitoring_v3.UptimeCheckConfig.ContentMatcher(
                content="healthy",
                matcher=monitoring_v3.UptimeCheckConfig.ContentMatcher.ContentMatcherOption.CONTAINS,
            )
        )

        # Select check locations
        config.selected_regions = [
            monitoring_v3.UptimeCheckRegion.USA,
            monitoring_v3.UptimeCheckRegion.EUROPE,
            monitoring_v3.UptimeCheckRegion.ASIA_PACIFIC,
        ]

        try:
            # Create the uptime check
            response = self.client.create_uptime_check_config(
                parent=self.project_path, uptime_check_config=config
            )

            logger.info(f"Created uptime check: {response.name}")
            return response.name

        except exceptions.AlreadyExists:
            logger.info(f"Uptime check for {display_name} already exists")
            # Find existing check
            for check in self.client.list_uptime_check_configs(
                parent=self.project_path
            ):
                if check.display_name == display_name:
                    return check.name
            return f"{self.project_path}/uptimeCheckConfigs/{display_name.lower().replace(' ', '-')}"
        except Exception as e:
            logger.error(f"Failed to create uptime check for {display_name}: {e}")
            raise

    def create_cloud_run_uptime_check(
        self, service_name: str, region: str = "us-central1"
    ) -> str:
        """
        Create uptime check for a Cloud Run service.

        Args:
            service_name: Name of the Cloud Run service
            region: Region where service is deployed

        Returns:
            Name of created uptime check
        """
        # Cloud Run services have URLs in format: https://SERVICE-NAME-PROJECT_ID.REGION.run.app
        host = f"{service_name}-{self.project_id.replace(':', '-')}.{region}.run.app"

        return self.create_http_uptime_check(
            display_name=f"SentinelOps - {service_name}",
            host=host,
            path="/health",
            check_interval=60,  # Check every minute
        )

    def create_tcp_uptime_check(
        self, display_name: str, host: str, port: int, check_interval: int = 60
    ) -> str:
        """
        Create a TCP uptime check.

        Args:
            display_name: Display name for the uptime check
            host: Hostname or IP to check
            port: Port number
            check_interval: Check interval in seconds

        Returns:
            Name of created uptime check
        """
        logger.info(f"Creating TCP uptime check for {display_name}...")

        config = monitoring_v3.UptimeCheckConfig()
        config.display_name = display_name
        config.timeout = {"seconds": 10}
        config.period = {"seconds": check_interval}

        # Configure monitored resource
        config.monitored_resource = monitoring_v3.MonitoredResource()
        config.monitored_resource.type = "uptime_url"
        config.monitored_resource.labels = {"project_id": self.project_id, "host": host}

        # Configure TCP check
        config.tcp_check = monitoring_v3.UptimeCheckConfig.TcpCheck()
        config.tcp_check.port = port

        # Select check locations
        config.selected_regions = [
            monitoring_v3.UptimeCheckRegion.USA,
            monitoring_v3.UptimeCheckRegion.EUROPE,
            monitoring_v3.UptimeCheckRegion.ASIA_PACIFIC,
        ]

        try:
            response = self.client.create_uptime_check_config(
                parent=self.project_path, uptime_check_config=config
            )

            logger.info(f"Created TCP uptime check: {response.name}")
            return response.name

        except exceptions.AlreadyExists:
            logger.info(f"TCP uptime check for {display_name} already exists")
            return f"{self.project_path}/uptimeCheckConfigs/{display_name.lower().replace(' ', '-')}"
        except Exception as e:
            logger.error(f"Failed to create TCP uptime check for {display_name}: {e}")
            raise

    def create_all_uptime_checks(self) -> Dict[str, Any]:
        """Create uptime checks for all SentinelOps services."""
        logger.info("Creating uptime checks for all services...")

        uptime_checks = {
            "timestamp": os.environ.get("BUILD_TIMESTAMP", "manual"),
            "project_id": self.project_id,
            "checks_created": {},
        }

        # Cloud Run services
        cloud_run_services = [
            "detection-agent",
            "analysis-agent",
            "communication-agent",
            "orchestration-agent",
        ]

        for service in cloud_run_services:
            try:
                check_name = self.create_cloud_run_uptime_check(service)
                uptime_checks["checks_created"][service] = {
                    "name": check_name,
                    "type": "http",
                    "status": "created",
                }
            except Exception as e:
                uptime_checks["checks_created"][service] = {
                    "status": "failed",
                    "error": str(e),
                }

        # External endpoints (if any)
        external_endpoints = [
            {
                "name": "API Gateway",
                "host": f"api.sentinelops.{self.project_id}.com",
                "path": "/health",
                "enabled": False,  # Enable when API Gateway is set up
            },
            {
                "name": "Web Dashboard",
                "host": f"dashboard.sentinelops.{self.project_id}.com",
                "path": "/",
                "enabled": False,  # Enable when dashboard is deployed
            },
        ]

        for endpoint in external_endpoints:
            if endpoint.get("enabled", False):
                try:
                    check_name = self.create_http_uptime_check(
                        display_name=f"SentinelOps - {endpoint['name']}",
                        host=endpoint["host"],
                        path=endpoint.get("path", "/"),
                    )
                    uptime_checks["checks_created"][endpoint["name"]] = {
                        "name": check_name,
                        "type": "http",
                        "status": "created",
                    }
                except Exception as e:
                    uptime_checks["checks_created"][endpoint["name"]] = {
                        "status": "failed",
                        "error": str(e),
                    }

        # Database connections (TCP checks)
        database_endpoints = [
            {
                "name": "BigQuery API",
                "host": "bigquery.googleapis.com",
                "port": 443,
                "enabled": True,
            },
            {
                "name": "Firestore API",
                "host": "firestore.googleapis.com",
                "port": 443,
                "enabled": True,
            },
        ]

        for db in database_endpoints:
            if db.get("enabled", False):
                try:
                    check_name = self.create_tcp_uptime_check(
                        display_name=f"SentinelOps - {db['name']}",
                        host=db["host"],
                        port=db["port"],
                    )
                    uptime_checks["checks_created"][db["name"]] = {
                        "name": check_name,
                        "type": "tcp",
                        "status": "created",
                    }
                except Exception as e:
                    uptime_checks["checks_created"][db["name"]] = {
                        "status": "failed",
                        "error": str(e),
                    }

        # Count successful creations
        uptime_checks["total_checks"] = len(uptime_checks["checks_created"])
        uptime_checks["successful_checks"] = sum(
            1
            for check in uptime_checks["checks_created"].values()
            if check.get("status") == "created"
        )

        # Create alert policy for uptime checks
        self._create_uptime_alert_policy()

        # Save summary
        summary_path = os.path.join(
            os.path.dirname(__file__), "uptime_checks_summary.json"
        )

        with open(summary_path, "w") as f:
            json.dump(uptime_checks, f, indent=2)

        logger.info(f"Uptime checks summary saved to: {summary_path}")

        return uptime_checks

    def _create_uptime_alert_policy(self):
        """Create alert policy for uptime check failures."""
        logger.info("Creating uptime check alert policy...")

        try:
            alert_client = monitoring_v3.AlertPolicyServiceClient()
            channel_client = monitoring_v3.NotificationChannelServiceClient()

            # Find or create notification channel
            notification_channels = []
            for channel in channel_client.list_notification_channels(
                name=self.project_path
            ):
                if (
                    channel.type_ == "email"
                    and "alerts@sentinelops.com"
                    in channel.labels.get("email_address", "")
                ):
                    notification_channels.append(channel.name)
                    break

            # Create alert policy
            alert_policy = monitoring_v3.AlertPolicy()
            alert_policy.display_name = "SentinelOps - Uptime Check Failure"
            alert_policy.conditions.append(
                monitoring_v3.AlertPolicy.Condition(
                    display_name="Uptime check failed",
                    condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                        filter="""
                            metric.type="monitoring.googleapis.com/uptime_check/check_passed" AND
                            resource.type="uptime_url"
                        """,
                        comparison=monitoring_v3.ComparisonType.COMPARISON_LT,
                        threshold_value=1,
                        duration={"seconds": 60},
                        aggregations=[
                            monitoring_v3.Aggregation(
                                alignment_period={"seconds": 60},
                                per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_FRACTION_TRUE,
                                cross_series_reducer=monitoring_v3.Aggregation.Reducer.REDUCE_MEAN,
                                group_by_fields=["resource.label.host"],
                            )
                        ],
                        trigger=monitoring_v3.AlertPolicy.Condition.Trigger(
                            count=2  # Alert after 2 consecutive failures
                        ),
                    ),
                )
            )

            alert_policy.notification_channels.extend(notification_channels)
            alert_policy.alert_strategy = monitoring_v3.AlertPolicy.AlertStrategy(
                auto_close={"seconds": 1800}  # Auto-close after 30 minutes
            )

            created_policy = alert_client.create_alert_policy(
                name=self.project_path, alert_policy=alert_policy
            )

            logger.info(f"Created uptime alert policy: {created_policy.name}")

        except Exception as e:
            logger.error(f"Failed to create uptime alert policy: {e}")

    def list_uptime_checks(self) -> List[Dict[str, Any]]:
        """List all uptime checks in the project."""
        uptime_checks = []

        try:
            for check in self.client.list_uptime_check_configs(
                parent=self.project_path
            ):
                check_info = {
                    "name": check.name,
                    "display_name": check.display_name,
                    "host": check.monitored_resource.labels.get("host", "N/A"),
                    "period": check.period.seconds,
                    "timeout": check.timeout.seconds,
                    "regions": [region.name for region in check.selected_regions],
                }

                if hasattr(check, "http_check") and check.http_check:
                    check_info["type"] = "http"
                    check_info["path"] = check.http_check.path
                    check_info["port"] = check.http_check.port
                    check_info["use_ssl"] = check.http_check.use_ssl
                elif hasattr(check, "tcp_check") and check.tcp_check:
                    check_info["type"] = "tcp"
                    check_info["port"] = check.tcp_check.port

                uptime_checks.append(check_info)

        except Exception as e:
            logger.error(f"Failed to list uptime checks: {e}")

        return uptime_checks


def main():
    """Main function to set up uptime checks."""
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(description="Set up uptime checks for SentinelOps")
    parser.add_argument(
        "--project-id",
        default=os.environ.get("GCP_PROJECT_ID", "sentinelops-project"),
        help="GCP Project ID",
    )
    parser.add_argument(
        "--service", help="Create uptime check for specific service only"
    )
    parser.add_argument(
        "--list", action="store_true", help="List existing uptime checks"
    )

    args = parser.parse_args()

    try:
        # Initialize uptime check manager
        manager = UptimeCheckManager(args.project_id)

        if args.list:
            # List existing uptime checks
            checks = manager.list_uptime_checks()
            print("\nExisting uptime checks ({len(checks)}):")
            for check in checks:
                print("\n{check['display_name']}:")
                print("  Type: {check.get('type', 'unknown')}")
                print("  Host: {check['host']}")
                if "path" in check:
                    print("  Path: {check['path']}")
                print("  Interval: {check['period']}s")
                print("  Regions: {', '.join(check['regions'])}")

        elif args.service:
            # Create uptime check for specific service
            check_name = manager.create_cloud_run_uptime_check(args.service)
            print("\nCreated uptime check for {args.service}: {check_name}")

        else:
            # Create all uptime checks
            results = manager.create_all_uptime_checks()

            print(
                f"\nCreated {results['successful_checks']}/{results['total_checks']} uptime checks"
            )

            for service, check_info in results["checks_created"].items():
                if check_info.get("status") == "created":
                    print("  ✓ {service}: {check_info['type']} check")
                else:
                    print("  ✗ {service}: {check_info.get('error', 'Failed')}")

        print(
            f"\nView uptime checks at: https://console.cloud.google.com/monitoring/uptime?project={args.project_id}"
        )

    except Exception as e:
        logger.error(f"Uptime check setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

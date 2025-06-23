#!/usr/bin/env python3
"""
Configure Monitoring Alerts for SentinelOps

This script creates and configures monitoring alert policies for all
SentinelOps services using the Google Cloud Monitoring API.
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


class AlertConfigurer:
    """Configures monitoring alerts for SentinelOps."""

    def __init__(self, project_id: str):
        """
        Initialize Alert Configurer.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.alert_client = monitoring_v3.AlertPolicyServiceClient()
        self.channel_client = monitoring_v3.NotificationChannelServiceClient()
        self.project_name = f"projects/{project_id}"

        # Default notification channels
        self.notification_channels = []

    def create_notification_channels(self) -> List[str]:
        """Create notification channels for alerts."""
        logger.info("Creating notification channels...")

        channels = []

        # Email notification channel
        email_channel = monitoring_v3.NotificationChannel()
        email_channel.type_ = "email"
        email_channel.display_name = "SentinelOps Alerts - Email"
        email_channel.labels = {"email_address": "alerts@sentinelops.com"}
        email_channel.enabled = True

        try:
            created_channel = self.channel_client.create_notification_channel(
                name=self.project_name, notification_channel=email_channel
            )
            channels.append(created_channel.name)
            logger.info(f"Created email notification channel: {created_channel.name}")
        except exceptions.AlreadyExists:
            # Find existing channel
            for channel in self.channel_client.list_notification_channels(
                name=self.project_name
            ):
                if (
                    channel.type_ == "email"
                    and channel.labels.get("email_address") == "alerts@sentinelops.com"
                ):
                    channels.append(channel.name)
                    break

        # Pub/Sub notification channel
        pubsub_channel = monitoring_v3.NotificationChannel()
        pubsub_channel.type_ = "pubsub"
        pubsub_channel.display_name = "SentinelOps Alerts - Pub/Sub"
        pubsub_channel.labels = {
            "topic": f"projects/{self.project_id}/topics/monitoring-alerts"
        }
        pubsub_channel.enabled = True

        try:
            created_channel = self.channel_client.create_notification_channel(
                name=self.project_name, notification_channel=pubsub_channel
            )
            channels.append(created_channel.name)
            logger.info(f"Created Pub/Sub notification channel: {created_channel.name}")
        except exceptions.AlreadyExists:
            # Find existing channel
            for channel in self.channel_client.list_notification_channels(
                name=self.project_name
            ):
                if (
                    channel.type_ == "pubsub"
                    and "monitoring-alerts" in channel.labels.get("topic", "")
                ):
                    channels.append(channel.name)
                    break

        self.notification_channels = channels
        return channels

    def create_service_alerts(self, service_name: str) -> List[str]:
        """Create alerts for a specific service."""
        logger.info(f"Creating alerts for {service_name}...")

        alert_policies = []

        # High Error Rate Alert
        error_rate_policy = monitoring_v3.AlertPolicy()
        error_rate_policy.display_name = f"{service_name} - High Error Rate"
        error_rate_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="Error rate > 5%",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter=f"""
                        resource.type="cloud_run_revision" AND
                        resource.label.service_name="{service_name}" AND
                        metric.type="run.googleapis.com/request_count"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=0.05,
                    duration={"seconds": 300},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
                            cross_series_reducer=monitoring_v3.Aggregation.Reducer.REDUCE_MEAN,
                            group_by_fields=["metric.label.response_code_class"],
                        )
                    ],
                    trigger=monitoring_v3.AlertPolicy.Condition.Trigger(count=1),
                ),
            )
        )
        error_rate_policy.notification_channels.extend(self.notification_channels)
        error_rate_policy.alert_strategy = monitoring_v3.AlertPolicy.AlertStrategy(
            auto_close={"seconds": 86400}  # 24 hours
        )

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=error_rate_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created error rate alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create error rate alert: {e}")

        # High Latency Alert
        latency_policy = monitoring_v3.AlertPolicy()
        latency_policy.display_name = f"{service_name} - High Latency"
        latency_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="P95 latency > 5s",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter=f"""
                        resource.type="cloud_run_revision" AND
                        resource.label.service_name="{service_name}" AND
                        metric.type="run.googleapis.com/request_latencies"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=5000,  # 5 seconds in milliseconds
                    duration={"seconds": 300},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_PERCENTILE_95,
                        )
                    ],
                ),
            )
        )
        latency_policy.notification_channels.extend(self.notification_channels)

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=latency_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created latency alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create latency alert: {e}")

        # Service Down Alert
        uptime_policy = monitoring_v3.AlertPolicy()
        uptime_policy.display_name = f"{service_name} - Service Down"
        uptime_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="No successful requests",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter=f"""
                        resource.type="cloud_run_revision" AND
                        resource.label.service_name="{service_name}" AND
                        metric.type="run.googleapis.com/request_count" AND
                        metric.label.response_code_class="2xx"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_LT,
                    threshold_value=1,
                    duration={"seconds": 180},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
                        )
                    ],
                ),
            )
        )
        uptime_policy.notification_channels.extend(self.notification_channels)
        uptime_policy.alert_strategy = monitoring_v3.AlertPolicy.AlertStrategy(
            notification_rate_limit=monitoring_v3.AlertPolicy.AlertStrategy.NotificationRateLimit(
                period={"seconds": 3600}  # Max 1 notification per hour
            )
        )

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=uptime_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created uptime alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create uptime alert: {e}")

        # High CPU Alert
        cpu_policy = monitoring_v3.AlertPolicy()
        cpu_policy.display_name = f"{service_name} - High CPU Usage"
        cpu_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="CPU utilization > 80%",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter=f"""
                        resource.type="cloud_run_revision" AND
                        resource.label.service_name="{service_name}" AND
                        metric.type="run.googleapis.com/container/cpu/utilizations"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=0.8,
                    duration={"seconds": 600},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                        )
                    ],
                ),
            )
        )
        cpu_policy.notification_channels.extend(self.notification_channels)

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=cpu_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created CPU alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create CPU alert: {e}")

        return alert_policies

    def create_security_alerts(self) -> List[str]:
        """Create security-related alerts."""
        logger.info("Creating security alerts...")

        alert_policies = []

        # Suspicious Activity Alert
        suspicious_policy = monitoring_v3.AlertPolicy()
        suspicious_policy.display_name = "Security - Suspicious Activity Detected"
        suspicious_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="Multiple failed auth attempts",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter="""
                        metric.type="logging.googleapis.com/user/failed_auth_attempts"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=5,
                    duration={"seconds": 300},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
                        )
                    ],
                ),
            )
        )
        suspicious_policy.notification_channels.extend(self.notification_channels)
        suspicious_policy.severity = (
            monitoring_v3.AlertPolicy.Severity.SEVERITY_CRITICAL
        )

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=suspicious_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created suspicious activity alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create suspicious activity alert: {e}")

        # High Severity Incident Alert
        incident_policy = monitoring_v3.AlertPolicy()
        incident_policy.display_name = "Security - High Severity Incident"
        incident_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="High/Critical severity incident detected",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter="""
                        metric.type="custom.googleapis.com/security/incident_severity" AND
                        metric.label.severity=("HIGH" OR "CRITICAL")
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=0,
                    duration={"seconds": 0},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_COUNT,
                        )
                    ],
                ),
            )
        )
        incident_policy.notification_channels.extend(self.notification_channels)
        incident_policy.severity = monitoring_v3.AlertPolicy.Severity.SEVERITY_CRITICAL

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=incident_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created incident alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create incident alert: {e}")

        return alert_policies

    def create_infrastructure_alerts(self) -> List[str]:
        """Create infrastructure-related alerts."""
        logger.info("Creating infrastructure alerts...")

        alert_policies = []

        # BigQuery Query Cost Alert
        bq_cost_policy = monitoring_v3.AlertPolicy()
        bq_cost_policy.display_name = "Infrastructure - BigQuery High Cost Query"
        bq_cost_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="Query processes > 1TB",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter="""
                        resource.type="bigquery_project" AND
                        metric.type="bigquery.googleapis.com/query/scanned_bytes"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=1099511627776,  # 1TB in bytes
                    duration={"seconds": 0},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MAX,
                        )
                    ],
                ),
            )
        )
        bq_cost_policy.notification_channels.extend(self.notification_channels)

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=bq_cost_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created BigQuery cost alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create BigQuery cost alert: {e}")

        # Pub/Sub Message Backlog Alert
        pubsub_policy = monitoring_v3.AlertPolicy()
        pubsub_policy.display_name = "Infrastructure - Pub/Sub Message Backlog"
        pubsub_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="Message backlog > 1000",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter="""
                        resource.type="pubsub_subscription" AND
                        metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=1000,
                    duration={"seconds": 300},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MAX,
                            group_by_fields=["resource.label.subscription_id"],
                        )
                    ],
                ),
            )
        )
        pubsub_policy.notification_channels.extend(self.notification_channels)

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=pubsub_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created Pub/Sub backlog alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create Pub/Sub backlog alert: {e}")

        # Firestore Operation Rate Alert
        firestore_policy = monitoring_v3.AlertPolicy()
        firestore_policy.display_name = "Infrastructure - Firestore High Operation Rate"
        firestore_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="Operations > 10K/minute",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter="""
                        resource.type="firestore.googleapis.com/Database" AND
                        metric.type="firestore.googleapis.com/document/write_count"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=10000,
                    duration={"seconds": 60},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 60},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
                        )
                    ],
                ),
            )
        )
        firestore_policy.notification_channels.extend(self.notification_channels)

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=firestore_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created Firestore rate alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create Firestore rate alert: {e}")

        return alert_policies

    def create_budget_alerts(self) -> List[str]:
        """Create budget-related alerts."""
        logger.info("Creating budget alerts...")

        alert_policies = []

        # Daily Spend Alert
        daily_spend_policy = monitoring_v3.AlertPolicy()
        daily_spend_policy.display_name = "Budget - Daily Spend Exceeded"
        daily_spend_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="Daily spend > $500",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter="""
                        metric.type="custom.googleapis.com/cost/daily_spend"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=500,
                    duration={"seconds": 0},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 86400},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
                        )
                    ],
                ),
            )
        )
        daily_spend_policy.notification_channels.extend(self.notification_channels)
        daily_spend_policy.severity = (
            monitoring_v3.AlertPolicy.Severity.SEVERITY_WARNING
        )

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=daily_spend_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created daily spend alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create daily spend alert: {e}")

        # Cost Anomaly Alert
        anomaly_policy = monitoring_v3.AlertPolicy()
        anomaly_policy.display_name = "Budget - Cost Anomaly Detected"
        anomaly_policy.conditions.append(
            monitoring_v3.AlertPolicy.Condition(
                display_name="Cost spike > 50% above average",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter="""
                        metric.type="custom.googleapis.com/cost/anomaly_score"
                    """,
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=1.5,
                    duration={"seconds": 3600},
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period={"seconds": 3600},
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MAX,
                        )
                    ],
                ),
            )
        )
        anomaly_policy.notification_channels.extend(self.notification_channels)

        try:
            created_policy = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=anomaly_policy
            )
            alert_policies.append(created_policy.name)
            logger.info(f"Created cost anomaly alert: {created_policy.name}")
        except Exception as e:
            logger.error(f"Failed to create cost anomaly alert: {e}")

        return alert_policies

    def configure_all_alerts(self) -> Dict[str, Any]:
        """Configure all monitoring alerts."""
        logger.info("Configuring all monitoring alerts...")

        # Create notification channels first
        self.create_notification_channels()

        all_alerts = {
            "timestamp": os.environ.get("BUILD_TIMESTAMP", "manual"),
            "project_id": self.project_id,
            "notification_channels": self.notification_channels,
            "alert_policies": {},
        }

        # Create service alerts
        services = [
            "detection-agent",
            "analysis-agent",
            "communication-agent",
            "orchestration-agent",
        ]

        for service in services:
            all_alerts["alert_policies"][service] = self.create_service_alerts(service)

        # Create category alerts
        all_alerts["alert_policies"]["security"] = self.create_security_alerts()
        all_alerts["alert_policies"][
            "infrastructure"
        ] = self.create_infrastructure_alerts()
        all_alerts["alert_policies"]["budget"] = self.create_budget_alerts()

        # Count total alerts
        total_alerts = sum(
            len(alerts) for alerts in all_alerts["alert_policies"].values()
        )
        all_alerts["total_alerts_created"] = total_alerts

        # Save configuration summary
        summary_path = os.path.join(
            os.path.dirname(__file__), "alert_configuration_summary.json"
        )

        with open(summary_path, "w") as f:
            json.dump(all_alerts, f, indent=2)

        logger.info(f"Alert configuration summary saved to: {summary_path}")

        return all_alerts


def main():
    """Main function to configure monitoring alerts."""
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(
        description="Configure monitoring alerts for SentinelOps"
    )
    parser.add_argument(
        "--project-id",
        default=os.environ.get("GCP_PROJECT_ID", "sentinelops-project"),
        help="GCP Project ID",
    )
    parser.add_argument("--service", help="Configure alerts for specific service only")
    parser.add_argument(
        "--category",
        choices=["security", "infrastructure", "budget"],
        help="Configure alerts for specific category only",
    )

    args = parser.parse_args()

    try:
        # Initialize alert configurer
        configurer = AlertConfigurer(args.project_id)

        if args.service:
            # Configure alerts for specific service
            configurer.create_notification_channels()
            alerts = configurer.create_service_alerts(args.service)
            print("\nCreated {len(alerts)} alerts for {args.service}")

        elif args.category:
            # Configure alerts for specific category
            configurer.create_notification_channels()

            if args.category == "security":
                alerts = configurer.create_security_alerts()
            elif args.category == "infrastructure":
                alerts = configurer.create_infrastructure_alerts()
            elif args.category == "budget":
                alerts = configurer.create_budget_alerts()

            print("\nCreated {len(alerts)} {args.category} alerts")

        else:
            # Configure all alerts
            results = configurer.configure_all_alerts()
            print(
                f"\nCreated {results['total_alerts_created']} alerts across all categories"
            )
            print("\nNotification channels: {len(results['notification_channels'])}")

            for category, alerts in results["alert_policies"].items():
                print("  {category}: {len(alerts)} alerts")

        print(
            f"\nView alerts at: https://console.cloud.google.com/monitoring/alerting?project={args.project_id}"
        )

    except Exception as e:
        logger.error(f"Alert configuration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

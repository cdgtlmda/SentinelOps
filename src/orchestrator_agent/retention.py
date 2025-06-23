"""
Retention policy management for the orchestrator agent.
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from google.cloud import firestore_v1 as firestore

if TYPE_CHECKING:
    pass


class RetentionPeriod(Enum):
    """Standard retention periods."""

    HOURS_24 = timedelta(hours=24)
    DAYS_7 = timedelta(days=7)
    DAYS_30 = timedelta(days=30)
    DAYS_90 = timedelta(days=90)
    DAYS_180 = timedelta(days=180)
    DAYS_365 = timedelta(days=365)
    YEARS_7 = timedelta(days=2555)  # 7 years for compliance


class RetentionPolicy:
    """Defines retention policy for different data types."""

    def __init__(
        self,
        policy_name: str,
        retention_period: timedelta,
        applies_to: List[str],
        conditions: Optional[Dict[str, Any]] = None,
        archive_before_delete: bool = False,
    ):
        """
        Initialize retention policy.

        Args:
            policy_name: Name of the policy
            retention_period: How long to retain data
            applies_to: List of data types (incidents, audit_logs, metrics)
            conditions: Optional conditions for applying policy
            archive_before_delete: Whether to archive before deletion
        """
        self.policy_name = policy_name
        self.retention_period = retention_period
        self.applies_to = applies_to
        self.conditions = conditions or {}
        self.archive_before_delete = archive_before_delete


class RetentionManager:
    """Manages data retention policies for the orchestrator agent."""

    def __init__(self, agent_id: str, db: "firestore.Client", config: Dict[str, Any]):
        """Initialize retention manager."""
        self.agent_id = agent_id
        self.db = db
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_id}")

        # Load retention policies from config
        self.policies = self._load_policies()

        # Track last cleanup time
        self.last_cleanup: Dict[str, datetime] = {}

        # Archive settings
        self.archive_enabled = config.get("retention", {}).get("archive_enabled", False)
        self.archive_bucket = config.get("retention", {}).get("archive_bucket", "")

    def _load_policies(self) -> List[RetentionPolicy]:
        """Load retention policies from configuration."""
        policies = []
        retention_config = self.config.get("retention", {}).get("policies", {})

        # Default policies if none configured
        if not retention_config:
            policies.extend(
                [
                    RetentionPolicy(
                        "default_incident_retention",
                        RetentionPeriod.DAYS_90.value,
                        ["incidents"],
                        conditions={"status": ["closed", "resolved"]},
                    ),
                    RetentionPolicy(
                        "default_audit_retention",
                        RetentionPeriod.YEARS_7.value,
                        ["audit_logs"],
                        archive_before_delete=True,
                    ),
                    RetentionPolicy(
                        "default_metrics_retention",
                        RetentionPeriod.DAYS_30.value,
                        ["metrics"],
                    ),
                ]
            )
        else:
            # Load from config
            for policy_name, policy_config in retention_config.items():
                retention_days = policy_config.get("retention_days", 90)
                policies.append(
                    RetentionPolicy(
                        policy_name,
                        timedelta(days=retention_days),
                        policy_config.get("applies_to", []),
                        policy_config.get("conditions"),
                        policy_config.get("archive_before_delete", False),
                    )
                )

        # Add severity-based policies
        severity_retention = self.config.get("retention", {}).get("by_severity", {})
        for severity, days in severity_retention.items():
            policies.append(
                RetentionPolicy(
                    f"severity_{severity}_retention",
                    timedelta(days=days),
                    ["incidents"],
                    conditions={"severity": severity},
                )
            )

        return policies

    async def apply_retention_policies(self) -> Dict[str, int]:
        """
        Apply all retention policies and clean up old data.

        Returns:
            Dict mapping data type to number of items cleaned up
        """
        cleanup_stats = {"incidents": 0, "audit_logs": 0, "metrics": 0}

        try:
            # Apply policies for each data type
            for data_type in ["incidents", "audit_logs", "metrics"]:
                count = await self._apply_policies_for_type(data_type)
                cleanup_stats[data_type] = count

            self.logger.info("Retention cleanup completed: %s", cleanup_stats)

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            self.logger.error("Failed to cleanup expired data: %s", e)
            return {}

        return cleanup_stats

    async def _apply_policies_for_type(self, data_type: str) -> int:
        """Apply retention policies for a specific data type."""
        # Get applicable policies
        applicable_policies = [p for p in self.policies if data_type in p.applies_to]
        if not applicable_policies:
            return 0

        # Get collection reference
        collection_map = {
            "incidents": "incidents",
            "audit_logs": "audit_logs",
            "metrics": "orchestrator_metrics",
        }
        collection = self.db.collection(collection_map[data_type])

        deleted_count = 0
        now = datetime.now(timezone.utc)

        # Process each policy
        for policy in applicable_policies:
            cutoff_date = now - policy.retention_period

            # Build query
            query = collection.where("created_at", "<", cutoff_date.isoformat())

            # Apply conditions
            if policy.conditions:
                if "status" in policy.conditions:
                    if isinstance(policy.conditions["status"], list):
                        query = query.where("status", "in", policy.conditions["status"])
                    else:
                        query = query.where("status", "==", policy.conditions["status"])

                if "severity" in policy.conditions:
                    query = query.where("severity", "==", policy.conditions["severity"])

            # Execute query in batches
            batch_size = 100
            docs = query.limit(batch_size).stream()

            for doc in docs:
                doc_data = doc.to_dict()

                # Archive if required
                if policy.archive_before_delete and self.archive_enabled:
                    await self._archive_document(data_type, doc.id, doc_data)

                # Delete document
                doc.reference.delete()
                deleted_count += 1

                # Log high-value deletions
                if data_type == "incidents" and doc_data.get("severity") in [
                    "critical",
                    "high",
                ]:
                    self.logger.info(
                        "Deleted %s incident %s per policy %s",
                        doc_data.get("severity"),
                        doc.id,
                        policy.policy_name,
                    )

        return deleted_count

    async def _archive_document(
        self, data_type: str, doc_id: str, doc_data: Dict[str, Any]
    ) -> bool:
        """Archive a document before deletion."""
        if not self.archive_bucket:
            self.logger.warning("Archive bucket not configured, skipping archive")
            return False

        try:
            # Add to archive collection
            archive_collection = self.db.collection(f"archive_{data_type}")
            archive_data = doc_data.copy()
            archive_data["archived_at"] = datetime.now(timezone.utc).isoformat()
            archive_data["archived_by"] = self.agent_id
            archive_data["original_id"] = doc_id

            archive_collection.add(archive_data)

            return True

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            self.logger.error("Failed to archive data: %s", e)
            return False

    async def get_retention_summary(self) -> Dict[str, Any]:
        """Get summary of retention policies and upcoming cleanups."""
        summary: Dict[str, Any] = {
            "policies": [],
            "next_cleanup": {},
            "data_counts": {},
        }

        # Policy details
        for policy in self.policies:
            summary["policies"].append(
                {
                    "name": policy.policy_name,
                    "retention_days": policy.retention_period.days,
                    "applies_to": policy.applies_to,
                    "conditions": policy.conditions,
                    "archive_enabled": policy.archive_before_delete,
                }
            )

        # Next cleanup times
        now = datetime.now(timezone.utc)
        cleanup_interval = timedelta(hours=24)  # Daily cleanup

        for data_type in ["incidents", "audit_logs", "metrics"]:
            last = self.last_cleanup.get(data_type, now - cleanup_interval)
            next_cleanup = last + cleanup_interval
            summary["next_cleanup"][data_type] = next_cleanup.isoformat()

        # Current data counts
        try:
            summary["data_counts"]["incidents"] = len(
                list(self.db.collection("incidents").limit(1000).stream())
            )
            summary["data_counts"]["audit_logs"] = len(
                list(self.db.collection("audit_logs").limit(1000).stream())
            )
            summary["data_counts"]["metrics"] = len(
                list(self.db.collection("orchestrator_metrics").limit(1000).stream())
            )
        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            self.logger.error("Error getting data counts: %s", e)

        return summary

    def should_run_cleanup(self, data_type: str) -> bool:
        """Check if cleanup should run for a data type."""
        cleanup_interval = timedelta(hours=24)  # Run daily
        last = self.last_cleanup.get(
            data_type, datetime.min.replace(tzinfo=timezone.utc)
        )
        return datetime.now(timezone.utc) - last > cleanup_interval

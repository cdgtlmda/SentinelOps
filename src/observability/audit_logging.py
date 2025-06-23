"""
Comprehensive audit logging system for SentinelOps.

This module provides detailed audit logging for security compliance,
user actions, system changes, and data access tracking.
"""

import asyncio
import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from google.cloud import bigquery
from google.cloud import firestore_v1 as firestore
from google.cloud import logging as cloud_logging
from google.cloud import pubsub_v1
from google.cloud.exceptions import GoogleCloudError

from src.common.models import SeverityLevel
from src.common.secure_query_builder import SecureQueryBuilder


class AuditEventType(Enum):
    """Types of audit events."""

    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_SESSION_EXPIRED = "auth.session.expired"
    AUTH_MFA_SUCCESS = "auth.mfa.success"
    AUTH_MFA_FAILURE = "auth.mfa.failure"

    # Authorization events
    AUTHZ_ACCESS_GRANTED = "authz.access.granted"
    AUTHZ_ACCESS_DENIED = "authz.access.denied"
    AUTHZ_PERMISSION_CHANGED = "authz.permission.changed"
    AUTHZ_ROLE_ASSIGNED = "authz.role.assigned"
    AUTHZ_ROLE_REVOKED = "authz.role.revoked"

    # Data access events
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"

    # Configuration changes
    CONFIG_CREATED = "config.created"
    CONFIG_UPDATED = "config.updated"
    CONFIG_DELETED = "config.deleted"
    CONFIG_EXPORTED = "config.exported"

    # Security events
    SECURITY_THREAT_DETECTED = "security.threat.detected"
    SECURITY_INCIDENT_CREATED = "security.incident.created"
    SECURITY_INCIDENT_UPDATED = "security.incident.updated"
    SECURITY_INCIDENT_RESOLVED = "security.incident.resolved"
    SECURITY_REMEDIATION_EXECUTED = "security.remediation.executed"
    SECURITY_POLICY_VIOLATION = "security.policy.violation"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"

    # Compliance events
    COMPLIANCE_SCAN_STARTED = "compliance.scan.started"
    COMPLIANCE_SCAN_COMPLETED = "compliance.scan.completed"
    COMPLIANCE_VIOLATION_FOUND = "compliance.violation.found"
    COMPLIANCE_REPORT_GENERATED = "compliance.report.generated"


@dataclass
class AuditEvent:
    """Represents an audit event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditEventType = AuditEventType.SYSTEM_ERROR
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str = ""
    result: str = "success"  # success, failure, error
    severity: SeverityLevel = SeverityLevel.INFORMATIONAL
    details: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    compliance_standards: Set[str] = field(default_factory=set)
    data_classification: Optional[str] = None
    integrity_hash: Optional[str] = None


@dataclass
class AuditPolicy:
    """Audit policy configuration."""

    name: str
    description: str
    event_types: Set[AuditEventType]
    retention_days: int
    real_time_alert: bool = False
    alert_channels: List[str] = field(default_factory=list)
    compliance_standards: Set[str] = field(default_factory=set)
    filters: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """Comprehensive audit logging system."""

    def __init__(self, project_id: str, dataset_id: str = "audit_logs"):
        self.project_id = self._validate_bigquery_identifier(project_id, "project_id")
        self.dataset_id = self._validate_bigquery_identifier(dataset_id, "dataset_id")

        # Initialize clients
        self.bigquery_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.AsyncClient(project=self.project_id)
        self.pubsub_publisher = pubsub_v1.PublisherClient()
        self.cloud_logger = cloud_logging.Client(project=self.project_id).logger("audit")  # type: ignore

        # Audit configuration
        self._policies: Dict[str, AuditPolicy] = {}
        self._event_buffer: List[AuditEvent] = []
        self._buffer_lock = asyncio.Lock()

        # Real-time streaming
        self._stream_topic = f"projects/{self.project_id}/topics/audit-events"

        # Compliance mappings
        self._compliance_mappings = self._init_compliance_mappings()

        # Background tasks
        self._flush_task: Optional[asyncio.Task[Any]] = None
        self._retention_task: Optional[asyncio.Task[Any]] = None

        # Initialize audit infrastructure
        # Note: This creates a task in __init__ which may cause issues
        # TODO: Consider calling _initialize() explicitly after instantiation
        asyncio.create_task(self._initialize())

    def _validate_bigquery_identifier(
        self, identifier: str, identifier_type: str
    ) -> str:
        """Validate BigQuery identifiers to prevent SQL injection"""
        if not identifier:
            raise ValueError(f"{identifier_type} cannot be empty")
        if len(identifier) > 1024:
            raise ValueError(
                f"{identifier_type} exceeds maximum length of 1024 characters"
            )
        # Check for valid BigQuery identifier pattern
        if not re.match(r"^[a-zA-Z0-9_-]+$", identifier):
            raise ValueError(f"Invalid {identifier_type}: contains illegal characters")
        return identifier

    def _init_compliance_mappings(self) -> Dict[str, Set[AuditEventType]]:
        """Initialize compliance standard to event type mappings."""
        return {
            "SOC2": {
                AuditEventType.AUTH_LOGIN_SUCCESS,
                AuditEventType.AUTH_LOGIN_FAILURE,
                AuditEventType.AUTHZ_ACCESS_DENIED,
                AuditEventType.CONFIG_UPDATED,
                AuditEventType.DATA_READ,
                AuditEventType.SECURITY_INCIDENT_CREATED,
            },
            "PCI-DSS": {
                AuditEventType.AUTH_LOGIN_SUCCESS,
                AuditEventType.AUTH_LOGIN_FAILURE,
                AuditEventType.AUTHZ_ACCESS_GRANTED,
                AuditEventType.AUTHZ_ACCESS_DENIED,
                AuditEventType.DATA_READ,
                AuditEventType.DATA_WRITE,
                AuditEventType.CONFIG_UPDATED,
            },
            "HIPAA": {
                AuditEventType.AUTH_LOGIN_SUCCESS,
                AuditEventType.AUTH_LOGIN_FAILURE,
                AuditEventType.DATA_READ,
                AuditEventType.DATA_WRITE,
                AuditEventType.DATA_DELETE,
                AuditEventType.DATA_EXPORT,
            },
            "GDPR": {
                AuditEventType.DATA_READ,
                AuditEventType.DATA_WRITE,
                AuditEventType.DATA_DELETE,
                AuditEventType.DATA_EXPORT,
                AuditEventType.AUTHZ_ACCESS_GRANTED,
            },
        }

    async def _initialize(self) -> None:
        """Initialize audit logging infrastructure."""
        # Create BigQuery dataset and tables
        await self._create_bigquery_resources()

        # Load audit policies
        await self._load_audit_policies()

        # Start background tasks
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._retention_task = asyncio.create_task(self._retention_loop())

    async def _create_bigquery_resources(self) -> None:
        """Create BigQuery dataset and tables for audit logs."""
        # Create dataset
        dataset_id_full = f"{self.project_id}.{self.dataset_id}"
        dataset = bigquery.Dataset(dataset_id_full)
        dataset.location = "US"
        dataset.description = "Audit logs for SentinelOps security platform"

        try:
            dataset = self.bigquery_client.create_dataset(dataset, exists_ok=True)
        except GoogleCloudError as e:
            print(f"Error creating dataset: {e}")

        # Create audit events table
        table_id = f"{dataset_id_full}.events"
        schema = [
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("session_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("source_ip", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("resource_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("resource_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("action", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("result", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("severity", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("details", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
            bigquery.SchemaField("compliance_standards", "STRING", mode="REPEATED"),
            bigquery.SchemaField("data_classification", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("integrity_hash", "STRING", mode="NULLABLE"),
        ]

        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY, field="timestamp"
        )

        try:
            table = self.bigquery_client.create_table(table, exists_ok=True)
        except GoogleCloudError as e:
            print(f"Error creating table: {e}")

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: str = "",
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: Optional[SeverityLevel] = None,
        tags: Optional[Set[str]] = None,
        data_classification: Optional[str] = None,
    ) -> None:
        """Log an audit event."""
        # Determine severity if not provided
        if severity is None:
            if result == "failure":
                severity = SeverityLevel.MEDIUM
            elif result == "error":
                severity = SeverityLevel.HIGH
            else:
                severity = SeverityLevel.INFORMATIONAL

        # Determine compliance standards
        compliance_standards = set()
        for standard, event_types in self._compliance_mappings.items():
            if event_type in event_types:
                compliance_standards.add(standard)

        # Create audit event
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            source_ip=source_ip,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action or event_type.value,
            result=result,
            severity=severity,
            details=details or {},
            tags=tags or set(),
            compliance_standards=compliance_standards,
            data_classification=data_classification,
        )

        # Calculate integrity hash
        event.integrity_hash = self._calculate_integrity_hash(event)

        # Add to buffer
        async with self._buffer_lock:
            self._event_buffer.append(event)

        # Check for real-time alerts
        await self._check_real_time_alerts(event)

        # Stream to Pub/Sub if critical
        if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
            await self._stream_event(event)

    def _calculate_integrity_hash(self, event: AuditEvent) -> str:
        """Calculate integrity hash for an audit event."""
        # Create canonical representation
        canonical = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "action": event.action,
            "result": event.result,
            "details": json.dumps(event.details, sort_keys=True),
        }

        # Calculate SHA-256 hash
        canonical_str = json.dumps(canonical, sort_keys=True)
        return hashlib.sha256(canonical_str.encode()).hexdigest()

    async def _check_real_time_alerts(self, event: AuditEvent) -> None:
        """Check if event should trigger real-time alerts."""
        for policy in self._policies.values():
            if not policy.real_time_alert:
                continue

            if event.event_type not in policy.event_types:
                continue

            # Check filters
            if self._matches_filters(event, policy.filters):
                await self._send_alert(event, policy)

    def _matches_filters(self, event: AuditEvent, filters: Dict[str, Any]) -> bool:
        """Check if event matches policy filters."""
        for field_name, value in filters.items():
            event_value = getattr(event, field_name, None)

            if isinstance(value, list):
                if event_value not in value:
                    return False
            elif event_value != value:
                return False

        return True

    async def _send_alert(self, event: AuditEvent, policy: AuditPolicy) -> None:
        """Send alert for an audit event."""
        alert_data = {
            "policy_name": policy.name,
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "severity": event.severity.value,
            "user_id": event.user_id,
            "resource": f"{event.resource_type}/{event.resource_id}",
            "details": event.details,
        }

        # Send to configured channels
        for channel in policy.alert_channels:
            if channel == "pubsub":
                await self._publish_alert(alert_data)
            elif channel == "email":
                # Would send email alert
                pass
            elif channel == "slack":
                # Would send Slack alert
                pass

    async def _stream_event(self, event: AuditEvent) -> None:
        """Stream event to Pub/Sub for real-time processing."""
        try:
            # Convert event to JSON
            event_data = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "severity": event.severity.value,
                "resource": f"{event.resource_type}/{event.resource_id}",
                "details": event.details,
            }

            # Publish to Pub/Sub
            self.pubsub_publisher.publish(
                self._stream_topic,
                json.dumps(event_data).encode(),
                event_type=event.event_type.value,
                severity=event.severity.value,
            )

            # Don't wait for confirmation to avoid blocking

        except Exception as e:
            print(f"Error streaming audit event: {e}")

    async def _flush_loop(self) -> None:
        """Periodically flush audit events to storage."""
        while True:
            try:
                await asyncio.sleep(10)  # Flush every 10 seconds
                await self._flush_events()
            except Exception as e:
                print(f"Error flushing audit events: {e}")

    async def _flush_events(self) -> None:
        """Flush buffered events to BigQuery."""
        async with self._buffer_lock:
            if not self._event_buffer:
                return

            events_to_flush = self._event_buffer.copy()
            self._event_buffer.clear()

        # Convert events to BigQuery rows
        rows = []
        for event in events_to_flush:
            row = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "source_ip": event.source_ip,
                "user_agent": event.user_agent,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "action": event.action,
                "result": event.result,
                "severity": event.severity.value,
                "details": json.dumps(event.details) if event.details else None,
                "tags": list(event.tags),
                "compliance_standards": list(event.compliance_standards),
                "data_classification": event.data_classification,
                "integrity_hash": event.integrity_hash,
            }
            rows.append(row)

        # Insert into BigQuery
        table_id = f"{self.project_id}.{self.dataset_id}.events"
        errors = self.bigquery_client.insert_rows_json(table_id, rows)

        if errors:
            print(f"Error inserting audit events: {errors}")
            # Would implement retry logic here

    async def _retention_loop(self) -> None:
        """Periodically clean up old audit logs based on retention policies."""
        while True:
            try:
                await asyncio.sleep(86400)  # Run daily
                await self._apply_retention_policies()
            except Exception as e:
                print(f"Error applying retention policies: {e}")

    async def _apply_retention_policies(self) -> None:
        """Apply retention policies to audit logs."""
        for policy in self._policies.values():
            if policy.retention_days <= 0:
                continue

            # Calculate cutoff date
            cutoff_date = datetime.now(timezone.utc) - timedelta(
                days=policy.retention_days
            )

            # Build deletion query using secure query builder
            try:
                table_identifier = f"{self.project_id}.{self.dataset_id}.events"
                query = SecureQueryBuilder.build_delete_query(
                    table_identifier,
                    [
                        "timestamp < @cutoff_date",
                        "event_type IN UNNEST(@event_types)"
                    ]
                )
            except ValueError as e:
                self.cloud_logger.log_text(f"Invalid table identifier for deletion: {e}", severity='ERROR')
                continue

            # Execute deletion
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "cutoff_date", "TIMESTAMP", cutoff_date
                    ),
                    bigquery.ArrayQueryParameter(
                        "event_types", "STRING", [et.value for et in policy.event_types]
                    ),
                ]
            )

            query_job = self.bigquery_client.query(query, job_config=job_config)
            query_job.result()  # Wait for completion

    async def query_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: Optional[str] = None,
        compliance_standard: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Query audit events."""
        # Build where conditions
        where_conditions = ["timestamp BETWEEN @start_time AND @end_time"]

        query_parameters: list[
            bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter
        ] = [
            bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
            bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
        ]

        # Add filters
        if event_types:
            where_conditions.append("event_type IN UNNEST(@event_types)")
            query_parameters.append(
                bigquery.ArrayQueryParameter(
                    "event_types", "STRING", [et.value for et in event_types]
                )
            )

        if user_id:
            where_conditions.append("user_id = @user_id")
            query_parameters.append(
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            )

        if resource_type:
            where_conditions.append("resource_type = @resource_type")
            query_parameters.append(
                bigquery.ScalarQueryParameter("resource_type", "STRING", resource_type)
            )

        if resource_id:
            where_conditions.append("resource_id = @resource_id")
            query_parameters.append(
                bigquery.ScalarQueryParameter("resource_id", "STRING", resource_id)
            )

        if result:
            where_conditions.append("result = @result")
            query_parameters.append(
                bigquery.ScalarQueryParameter("result", "STRING", result)
            )

        if compliance_standard:
            where_conditions.append("@compliance_standard IN UNNEST(compliance_standards)")
            query_parameters.append(
                bigquery.ScalarQueryParameter(
                    "compliance_standard", "STRING", compliance_standard
                )
            )

        # Build query using secure query builder
        try:
            table_identifier = f"{self.project_id}.{self.dataset_id}.events"
            query = SecureQueryBuilder.build_select_query(
                table_identifier,
                ["*"],
                where_conditions,
                limit=limit
            )
            query += "\nORDER BY timestamp DESC"
        except ValueError as e:
            self.cloud_logger.log_text(f"Invalid table identifier for query: {e}", severity='ERROR')
            return []

        # Execute query
        job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
        query_job = self.bigquery_client.query(query, job_config=job_config)

        # Process results
        results = []
        for row in query_job:
            results.append(dict(row))

        return results

    async def verify_integrity(self, event_id: str) -> Tuple[bool, Optional[str]]:
        """Verify integrity of an audit event."""
        # Query event using secure query builder
        try:
            table_identifier = f"{self.project_id}.{self.dataset_id}.events"
            query = SecureQueryBuilder.build_select_query(
                table_identifier,
                ["*"],
                ["event_id = @event_id"]
            )
        except ValueError as e:
            self.cloud_logger.log_text(f"Invalid table identifier for integrity check: {e}", severity='ERROR')
            return False, f"Invalid table identifier: {e}"

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("event_id", "STRING", event_id)
            ]
        )

        query_job = self.bigquery_client.query(query, job_config=job_config)
        results = list(query_job)

        if not results:
            return False, "Event not found"

        row = dict(results[0])

        # Recreate event object
        event = AuditEvent(
            event_id=row["event_id"],
            timestamp=row["timestamp"],
            event_type=AuditEventType(row["event_type"]),
            user_id=row["user_id"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            action=row["action"],
            result=row["result"],
            details=json.loads(row["details"]) if row["details"] else {},
        )

        # Recalculate hash
        calculated_hash = self._calculate_integrity_hash(event)
        stored_hash = row["integrity_hash"]

        if calculated_hash == stored_hash:
            return True, None
        else:
            return False, "Integrity check failed"

    async def generate_compliance_report(
        self, compliance_standard: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for audit logs."""
        # Get required event types for standard
        required_events = self._compliance_mappings.get(compliance_standard, set())

        if not required_events:
            raise ValueError(f"Unknown compliance standard: {compliance_standard}")

        report: Dict[str, Any] = {
            "compliance_standard": compliance_standard,
            "reporting_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "event_summary": {},
            "user_activity": {},
            "data_access_summary": {},
            "security_incidents": [],
            "retention_compliance": True,
        }

        # Query events for the period
        events = await self.query_events(
            start_time=start_date,
            end_time=end_date,
            compliance_standard=compliance_standard,
            limit=10000,
        )

        # Analyze events
        for event in events:
            event_type = event["event_type"]

            # Event summary
            if event_type not in report["event_summary"]:
                report["event_summary"][event_type] = {
                    "count": 0,
                    "success": 0,
                    "failure": 0,
                }

            report["event_summary"][event_type]["count"] += 1
            if event["result"] == "success":
                report["event_summary"][event_type]["success"] += 1
            else:
                report["event_summary"][event_type]["failure"] += 1

            # User activity
            user_id = event.get("user_id", "anonymous")
            if user_id not in report["user_activity"]:
                report["user_activity"][user_id] = {
                    "event_count": 0,
                    "unique_resources": set(),
                    "unique_ips": set(),
                }

            report["user_activity"][user_id]["event_count"] += 1
            if event.get("resource_id"):
                report["user_activity"][user_id]["unique_resources"].add(
                    f"{event.get('resource_type', 'unknown')}/{event['resource_id']}"
                )
            if event.get("source_ip"):
                report["user_activity"][user_id]["unique_ips"].add(event["source_ip"])

            # Data access summary
            if event_type in ["data.read", "data.write", "data.delete", "data.export"]:
                classification = event.get("data_classification", "unclassified")
                if classification not in report["data_access_summary"]:
                    report["data_access_summary"][classification] = {
                        "read": 0,
                        "write": 0,
                        "delete": 0,
                        "export": 0,
                    }

                operation = event_type.split(".")[-1]
                report["data_access_summary"][classification][operation] += 1

            # Security incidents
            if event_type.startswith("security.incident"):
                report["security_incidents"].append(
                    {
                        "timestamp": event["timestamp"],
                        "event_type": event_type,
                        "severity": event.get("severity", "unknown"),
                        "details": json.loads(event.get("details", "{}")),
                    }
                )

        # Convert sets to lists for JSON serialization
        for user_data in report["user_activity"].values():
            user_data["unique_resources"] = list(user_data["unique_resources"])
            user_data["unique_ips"] = list(user_data["unique_ips"])

        return report

    async def register_policy(self, policy: AuditPolicy) -> None:
        """Register an audit policy."""
        self._policies[policy.name] = policy

        # Save to Firestore
        doc_ref = self.firestore_client.collection("audit_policies").document(
            policy.name
        )
        await doc_ref.set(
            {
                "name": policy.name,
                "description": policy.description,
                "event_types": [et.value for et in policy.event_types],
                "retention_days": policy.retention_days,
                "real_time_alert": policy.real_time_alert,
                "alert_channels": policy.alert_channels,
                "compliance_standards": list(policy.compliance_standards),
                "filters": policy.filters,
            }
        )

    async def _load_audit_policies(self) -> None:
        """Load audit policies from Firestore."""
        policies_ref = self.firestore_client.collection("audit_policies")

        async for doc in policies_ref.stream():
            data = doc.to_dict()
            if data is None:
                continue

            policy = AuditPolicy(
                name=data["name"],
                description=data["description"],
                event_types={AuditEventType(et) for et in data["event_types"]},
                retention_days=data["retention_days"],
                real_time_alert=data.get("real_time_alert", False),
                alert_channels=data.get("alert_channels", []),
                compliance_standards=set(data.get("compliance_standards", [])),
                filters=data.get("filters", {}),
            )

            self._policies[policy.name] = policy

    async def _publish_alert(self, alert_data: Dict[str, Any]) -> None:
        """Publish alert to Pub/Sub."""
        try:
            alert_topic = f"projects/{self.project_id}/topics/audit-alerts"

            self.pubsub_publisher.publish(
                alert_topic,
                json.dumps(alert_data).encode(),
                policy_name=alert_data["policy_name"],
                severity=alert_data["severity"],
            )

        except Exception as e:
            print(f"Error publishing audit alert: {e}")


# Pre-defined audit policies
def create_default_audit_policies() -> List[AuditPolicy]:
    """Create default audit policies."""
    policies = []

    # Security incident policy
    security_policy = AuditPolicy(
        name="security_incidents",
        description="Real-time alerts for security incidents",
        event_types={
            AuditEventType.SECURITY_THREAT_DETECTED,
            AuditEventType.SECURITY_INCIDENT_CREATED,
            AuditEventType.SECURITY_POLICY_VIOLATION,
        },
        retention_days=2555,  # 7 years
        real_time_alert=True,
        alert_channels=["pubsub", "email"],
        compliance_standards={"SOC2", "PCI-DSS"},
    )
    policies.append(security_policy)

    # Authentication failures policy
    auth_failure_policy = AuditPolicy(
        name="auth_failures",
        description="Monitor authentication failures",
        event_types={
            AuditEventType.AUTH_LOGIN_FAILURE,
            AuditEventType.AUTH_MFA_FAILURE,
        },
        retention_days=365,
        real_time_alert=True,
        alert_channels=["pubsub"],
        filters={"result": "failure"},
    )
    policies.append(auth_failure_policy)

    # Data access policy
    data_access_policy = AuditPolicy(
        name="sensitive_data_access",
        description="Track access to sensitive data",
        event_types={
            AuditEventType.DATA_READ,
            AuditEventType.DATA_WRITE,
            AuditEventType.DATA_DELETE,
            AuditEventType.DATA_EXPORT,
        },
        retention_days=2555,  # 7 years
        real_time_alert=False,
        compliance_standards={"HIPAA", "GDPR", "PCI-DSS"},
        filters={"data_classification": ["sensitive", "confidential", "restricted"]},
    )
    policies.append(data_access_policy)

    # Configuration changes policy
    config_policy = AuditPolicy(
        name="configuration_changes",
        description="Track all configuration changes",
        event_types={
            AuditEventType.CONFIG_CREATED,
            AuditEventType.CONFIG_UPDATED,
            AuditEventType.CONFIG_DELETED,
        },
        retention_days=1095,  # 3 years
        real_time_alert=False,
        compliance_standards={"SOC2", "ISO27001"},
    )
    policies.append(config_policy)

    return policies

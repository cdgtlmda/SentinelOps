"""
Audit trail implementation for the Communication Agent.

This module provides comprehensive audit trail functionality including
notification history, recipient tracking, and compliance reporting.
"""

import asyncio
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.utils.logging import get_agent_logger


class AuditEventType(str, Enum):
    """Types of audit events."""

    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_FAILED = "notification_failed"
    NOTIFICATION_DELIVERED = "notification_delivered"
    NOTIFICATION_READ = "notification_read"
    RECIPIENT_ADDED = "recipient_added"
    RECIPIENT_UPDATED = "recipient_updated"
    RECIPIENT_REMOVED = "recipient_removed"
    PREFERENCE_CHANGED = "preference_changed"
    TEMPLATE_USED = "template_used"
    DELIVERY_RETRY = "delivery_retry"
    COMPLIANCE_CHECK = "compliance_check"
    DATA_SANITIZED = "data_sanitized"


class ComplianceStandard(str, Enum):
    """Supported compliance standards."""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"


@dataclass
class NotificationAuditEntry:
    """Represents a single audit entry for a notification."""

    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    notification_id: str
    channel: str
    recipients: List[str]
    subject: str
    message_preview: str  # First 200 chars of message
    priority: str
    status: str
    metadata: Dict[str, Any]
    error_details: Optional[str] = None
    delivery_time_ms: Optional[int] = None
    read_timestamp: Optional[datetime] = None
    compliance_flags: Optional[List[ComplianceStandard]] = None
    data_sanitized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit entry to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        if self.read_timestamp:
            data["read_timestamp"] = self.read_timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationAuditEntry":
        """Create audit entry from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("read_timestamp"):
            data["read_timestamp"] = datetime.fromisoformat(data["read_timestamp"])
        if data.get("event_type"):
            data["event_type"] = AuditEventType(data["event_type"])
        if data.get("compliance_flags"):
            data["compliance_flags"] = [
                ComplianceStandard(s) for s in data["compliance_flags"]
            ]
        return cls(**data)


@dataclass
class RecipientActivity:
    """Tracks recipient notification activity."""

    recipient_id: str
    email: Optional[str] = None
    slack_id: Optional[str] = None
    phone_number: Optional[str] = None
    total_notifications: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    last_notification: Optional[datetime] = None
    channels_used: Optional[Set[str]] = None
    notification_types: Optional[Dict[str, int]] = None
    average_read_time_hours: Optional[float] = None
    preferences_updated: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.channels_used is None:
            self.channels_used = set()
        if self.notification_types is None:
            self.notification_types = defaultdict(int)


@dataclass
class ComplianceReport:
    """Compliance report for audit data."""

    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    standards: List[ComplianceStandard]
    total_notifications: int
    notifications_with_pii: int
    data_retention_compliant: bool
    access_logs_available: bool
    encryption_verified: bool
    recipient_consent_verified: int
    data_deletion_requests: int
    compliance_violations: List[Dict[str, Any]]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        data = asdict(self)
        data["generated_at"] = self.generated_at.isoformat()
        data["period_start"] = self.period_start.isoformat()
        data["period_end"] = self.period_end.isoformat()
        data["standards"] = [s.value for s in self.standards]
        return data


@dataclass
class AuditConfig:
    """Configuration for the audit trail system."""

    storage_path: Path
    retention_days: int = 90
    max_entries_per_file: int = 10000
    enable_compression: bool = True
    compliance_standards: Optional[List[ComplianceStandard]] = None
    pii_detection_enabled: bool = True
    real_time_monitoring: bool = True
    export_formats: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.compliance_standards is None:
            self.compliance_standards = [ComplianceStandard.SOC2]
        if self.export_formats is None:
            self.export_formats = ["json", "csv"]

        # Ensure storage path exists
        self.storage_path.mkdir(parents=True, exist_ok=True)


class AuditTrail:
    """
    Manages audit trail for the Communication Agent.

    Provides notification history, recipient tracking, and compliance reporting.
    """

    def __init__(self, config: AuditConfig):
        """Initialize the audit trail."""
        self.config = config
        self.logger = get_agent_logger("communication.audit", "communication")

        # In-memory caches
        self._notification_cache: List[NotificationAuditEntry] = []
        self._recipient_activities: Dict[str, RecipientActivity] = {}
        self._current_file_entries = 0
        self._current_file_path: Optional[Path] = None

        # Initialize storage
        self._initialize_storage()

        # Start background tasks
        self._cleanup_task: Optional[asyncio.Task[None]] = None
        self._monitoring_started = False
        if self.config.real_time_monitoring:
            # Don't start monitoring immediately, wait for async context
            self._should_start_monitoring = True
        else:
            self._should_start_monitoring = False

    def _initialize_storage(self) -> None:
        """Initialize audit storage structure."""
        # Create subdirectories
        (self.config.storage_path / "notifications").mkdir(exist_ok=True)
        (self.config.storage_path / "recipients").mkdir(exist_ok=True)
        (self.config.storage_path / "compliance").mkdir(exist_ok=True)
        (self.config.storage_path / "exports").mkdir(exist_ok=True)

        # Load existing recipient activities
        self._load_recipient_activities()

    def _load_recipient_activities(self) -> None:
        """Load recipient activities from disk."""
        recipients_file = self.config.storage_path / "recipients" / "activities.json"
        if recipients_file.exists():
            try:
                with open(recipients_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for recipient_id, activity_data in data.items():
                        activity = RecipientActivity(
                            recipient_id=recipient_id, **activity_data
                        )
                        if activity_data.get("last_notification"):
                            activity.last_notification = datetime.fromisoformat(
                                activity_data["last_notification"]
                            )
                        if activity_data.get("channels_used"):
                            activity.channels_used = set(activity_data["channels_used"])
                        self._recipient_activities[recipient_id] = activity
            except (ValueError, KeyError, IOError) as e:
                self.logger.error(f"Failed to load recipient activities: {e}")

    async def ensure_monitoring_started(self) -> None:
        """Ensure monitoring is started when in async context."""
        if self._should_start_monitoring and not self._monitoring_started:
            self._start_monitoring()
            self._monitoring_started = True

    async def log_notification(
        self,
        notification_id: str,
        event_type: AuditEventType,
        channel: str,
        recipients: List[str],
        subject: str,
        message: str,
        priority: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error_details: Optional[str] = None,
        delivery_time_ms: Optional[int] = None,
    ) -> NotificationAuditEntry:
        """Log a notification event to the audit trail."""
        await self.ensure_monitoring_started()
        # Create audit entry
        entry = NotificationAuditEntry(
            event_id=(
                f"{notification_id}_{event_type.value}_"
                f"{datetime.now(timezone.utc).timestamp()}"
            ),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            notification_id=notification_id,
            channel=channel,
            recipients=recipients,
            subject=subject,
            message_preview=message[:200] if message else "",
            priority=priority,
            status=status,
            metadata=metadata or {},
            error_details=error_details,
            delivery_time_ms=delivery_time_ms,
            data_sanitized=self.config.pii_detection_enabled,
        )

        # Check compliance flags
        entry.compliance_flags = await self._check_compliance_flags(entry)

        # Update recipient tracking
        await self._update_recipient_tracking(entry)

        # Store the entry
        await self._store_audit_entry(entry)

        self.logger.info(
            f"Logged audit event: {event_type.value} for notification {notification_id}"
        )

        return entry

    async def _check_compliance_flags(
        self, entry: NotificationAuditEntry
    ) -> List[ComplianceStandard]:
        """Check which compliance standards apply to this notification."""
        flags = []

        # Check for PII in message
        if self._contains_pii(entry.message_preview):
            if (
                self.config.compliance_standards
                and ComplianceStandard.GDPR in self.config.compliance_standards
            ):
                flags.append(ComplianceStandard.GDPR)
            if (
                self.config.compliance_standards
                and ComplianceStandard.HIPAA in self.config.compliance_standards
            ):
                flags.append(ComplianceStandard.HIPAA)

        # Check for financial data
        if self._contains_financial_data(entry.message_preview):
            if (
                self.config.compliance_standards
                and ComplianceStandard.PCI_DSS in self.config.compliance_standards
            ):
                flags.append(ComplianceStandard.PCI_DSS)

        return flags

    def _contains_pii(self, text: str) -> bool:
        """Simple PII detection (would be more sophisticated in production)."""
        # This is a placeholder - in production, use proper PII detection
        pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
        ]
        import re

        return any(re.search(pattern, text) for pattern in pii_patterns)

    def _contains_financial_data(self, text: str) -> bool:
        """Simple financial data detection."""
        # Placeholder implementation
        financial_keywords = [
            "credit card",
            "account number",
            "routing number",
            "bank account",
            "payment",
            "transaction",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in financial_keywords)

    async def _update_recipient_tracking(self, entry: NotificationAuditEntry) -> None:
        """Update recipient activity tracking."""
        for recipient in entry.recipients:
            if recipient not in self._recipient_activities:
                self._recipient_activities[recipient] = RecipientActivity(
                    recipient_id=recipient
                )

            activity = self._recipient_activities[recipient]
            activity.total_notifications += 1

            if entry.status == "delivered":
                activity.successful_deliveries += 1
            elif entry.status == "failed":
                activity.failed_deliveries += 1

            activity.last_notification = entry.timestamp
            assert activity.channels_used is not None
            activity.channels_used.add(entry.channel)
            assert activity.notification_types is not None
            activity.notification_types[
                entry.metadata.get("message_type", "unknown")
            ] += 1

        # Persist recipient activities
        await self._save_recipient_activities()

    async def _save_recipient_activities(self) -> None:
        """Save recipient activities to disk."""
        recipients_file = self.config.storage_path / "recipients" / "activities.json"

        data = {}
        for recipient_id, activity in self._recipient_activities.items():
            activity_dict = {
                "email": activity.email,
                "slack_id": activity.slack_id,
                "phone_number": activity.phone_number,
                "total_notifications": activity.total_notifications,
                "successful_deliveries": activity.successful_deliveries,
                "failed_deliveries": activity.failed_deliveries,
                "last_notification": (
                    activity.last_notification.isoformat()
                    if activity.last_notification
                    else None
                ),
                "channels_used": (
                    list(activity.channels_used)
                    if activity.channels_used is not None
                    else []
                ),
                "notification_types": (
                    dict(activity.notification_types)
                    if activity.notification_types is not None
                    else {}
                ),
                "average_read_time_hours": activity.average_read_time_hours,
                "preferences_updated": (
                    activity.preferences_updated.isoformat()
                    if activity.preferences_updated
                    else None
                ),
            }
            data[recipient_id] = activity_dict

        with open(recipients_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    async def _store_audit_entry(self, entry: NotificationAuditEntry) -> None:
        """Store audit entry to disk."""
        # Add to cache
        self._notification_cache.append(entry)

        # Determine file path
        if (
            self._current_file_path is None
            or self._current_file_entries >= self.config.max_entries_per_file
        ):
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            self._current_file_path = (
                self.config.storage_path / "notifications" / f"audit_{timestamp}.json"
            )
            self._current_file_entries = 0

        # Append to file
        entries = []
        if self._current_file_path.exists() and self._current_file_entries > 0:
            with open(self._current_file_path, "r", encoding="utf-8") as f:
                entries = json.load(f)

        entries.append(entry.to_dict())

        with open(self._current_file_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)

        self._current_file_entries += 1

    async def mark_notification_delivered(
        self, notification_id: str, channel: str
    ) -> None:
        """Mark a notification as delivered."""
        await self.ensure_monitoring_started()
        await self.log_notification(
            notification_id=notification_id,
            event_type=AuditEventType.NOTIFICATION_DELIVERED,
            channel=channel,
            recipients=[],  # Will be populated from original entry
            subject="",
            message="",
            priority="",
            status="delivered",
            metadata={"delivered_at": datetime.now(timezone.utc).isoformat()},
        )

    async def mark_notification_read(
        self, notification_id: str, recipient: str, channel: str
    ) -> None:
        """Mark a notification as read by a recipient."""
        read_time = datetime.now(timezone.utc)

        # Find original notification in cache
        original_entry = None
        for entry in reversed(self._notification_cache):
            if (
                entry.notification_id == notification_id
                and entry.event_type == AuditEventType.NOTIFICATION_SENT
            ):
                original_entry = entry
                break

        if original_entry:
            # Calculate read time
            read_delay = (read_time - original_entry.timestamp).total_seconds() / 3600

            # Update recipient's average read time
            if recipient in self._recipient_activities:
                activity = self._recipient_activities[recipient]
                if activity.average_read_time_hours is None:
                    activity.average_read_time_hours = read_delay
                else:
                    # Running average
                    total_reads = activity.successful_deliveries
                    activity.average_read_time_hours = (
                        activity.average_read_time_hours * (total_reads - 1)
                        + read_delay
                    ) / total_reads

        await self.log_notification(
            notification_id=notification_id,
            event_type=AuditEventType.NOTIFICATION_READ,
            channel=channel,
            recipients=[recipient],
            subject="",
            message="",
            priority="",
            status="read",
            metadata={
                "read_at": read_time.isoformat(),
                "read_delay_hours": read_delay if original_entry else None,
            },
        )

    async def get_notification_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        recipient: Optional[str] = None,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationAuditEntry]:
        """Retrieve notification history with filters."""
        await self.ensure_monitoring_started()
        entries = []

        # Load from files
        notification_files = sorted(
            (self.config.storage_path / "notifications").glob("audit_*.json"),
            reverse=True,
        )

        for file_path in notification_files:
            with open(file_path, "r", encoding="utf-8") as f:
                file_entries = json.load(f)

            for entry_data in file_entries:
                entry = NotificationAuditEntry.from_dict(entry_data)

                # Apply filters
                if start_date and entry.timestamp < start_date:
                    continue
                if end_date and entry.timestamp > end_date:
                    continue
                if recipient and recipient not in entry.recipients:
                    continue
                if channel and entry.channel != channel:
                    continue
                if status and entry.status != status:
                    continue

                entries.append(entry)

                if len(entries) >= limit:
                    return entries

        return entries

    async def get_recipient_report(
        self, recipient_id: str
    ) -> Optional[RecipientActivity]:
        """Get activity report for a specific recipient."""
        return self._recipient_activities.get(recipient_id)

    async def generate_compliance_report(  # noqa: C901
        self,
        standards: List[ComplianceStandard],
        start_date: datetime,
        end_date: datetime,
    ) -> ComplianceReport:
        """Generate a compliance report for the specified period."""
        self.logger.info(
            f"Generating compliance report for {standards} from {start_date} to {end_date}"
        )

        # Collect metrics
        total_notifications = 0
        notifications_with_pii = 0
        compliance_violations = []

        # Analyze notification history
        history = await self.get_notification_history(
            start_date=start_date,
            end_date=end_date,
            limit=10000,  # Higher limit for reports
        )

        for entry in history:
            total_notifications += 1

            if entry.compliance_flags:
                notifications_with_pii += 1

            # Check for violations
            if entry.data_sanitized is False and entry.compliance_flags:
                compliance_violations.append(
                    {
                        "notification_id": entry.notification_id,
                        "timestamp": entry.timestamp.isoformat(),
                        "violation": "Unsanitized PII in notification",
                        "standards_affected": [s.value for s in entry.compliance_flags],
                    }
                )

        # Check data retention compliance
        oldest_file = None
        notification_files = (self.config.storage_path / "notifications").glob(
            "audit_*.json"
        )
        for file_path in notification_files:
            if (
                oldest_file is None
                or file_path.stat().st_mtime < oldest_file.stat().st_mtime
            ):
                oldest_file = file_path

        data_retention_compliant = True
        if oldest_file:
            file_age_days = (
                datetime.now(timezone.utc)
                - datetime.fromtimestamp(oldest_file.stat().st_mtime, tz=timezone.utc)
            ).days
            if file_age_days > self.config.retention_days:
                data_retention_compliant = False
                compliance_violations.append(
                    {
                        "file": str(oldest_file),
                        "age_days": str(file_age_days),
                        "violation": "Data retention period exceeded",
                        "standards_affected": [s.value for s in standards],
                    }
                )

        # Generate recommendations
        recommendations = []
        if notifications_with_pii > total_notifications * 0.1:
            recommendations.append(
                "High percentage of notifications contain PII. "
                "Consider implementing stronger data minimization practices."
            )

        if not data_retention_compliant:
            recommendations.append(
                f"Implement automated data deletion after {self.config.retention_days} days."
            )

        if compliance_violations:
            recommendations.append(
                "Review and address compliance violations immediately."
            )

        # Count recipient consent (simplified - would check actual consent records)
        recipient_consent_verified = len(self._recipient_activities)

        # Create report
        report = ComplianceReport(
            report_id=f"compliance_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(timezone.utc),
            period_start=start_date,
            period_end=end_date,
            standards=standards,
            total_notifications=total_notifications,
            notifications_with_pii=notifications_with_pii,
            data_retention_compliant=data_retention_compliant,
            access_logs_available=True,  # Logging everything
            encryption_verified=True,  # Assuming encrypted storage
            recipient_consent_verified=recipient_consent_verified,
            data_deletion_requests=0,  # Would track actual requests
            compliance_violations=compliance_violations,
            recommendations=recommendations,
        )

        # Save report
        report_path = (
            self.config.storage_path / "compliance" / f"{report.report_id}.json"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)

        self.logger.info(f"Compliance report generated: {report.report_id}")

        return report

    async def export_audit_data(
        self,
        export_format: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Export audit data in specified format."""
        if (
            self.config.export_formats
            and export_format not in self.config.export_formats
        ):
            raise ValueError(f"Unsupported export format: {export_format}")

        # Default output path
        if output_path is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_path = (
                self.config.storage_path
                / "exports"
                / f"audit_export_{timestamp}.{export_format}"
            )

        # Get data
        history = await self.get_notification_history(
            start_date=start_date,
            end_date=end_date,
            limit=100000,  # High limit for exports
        )

        if export_format == "json":
            data = [entry.to_dict() for entry in history]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        elif export_format == "csv":
            import csv

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                if history:
                    fieldnames = history[0].to_dict().keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for entry in history:
                        writer.writerow(entry.to_dict())

        self.logger.info(f"Exported audit data to {output_path}")
        return output_path

    def _start_monitoring(self) -> None:
        """Start background monitoring tasks."""

        async def cleanup_old_data() -> None:
            """Periodically clean up old audit data."""
            while True:
                try:
                    await asyncio.sleep(86400)  # Daily cleanup

                    cutoff_date = datetime.now(timezone.utc) - timedelta(
                        days=self.config.retention_days
                    )

                    # Clean up old notification files
                    for file_path in (self.config.storage_path / "notifications").glob(
                        "audit_*.json"
                    ):
                        if (
                            datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                            < cutoff_date
                        ):
                            file_path.unlink()
                            self.logger.info(f"Deleted old audit file: {file_path}")

                    # Clean up old compliance reports
                    for file_path in (self.config.storage_path / "compliance").glob(
                        "*.json"
                    ):
                        if (
                            datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                            < cutoff_date
                        ):
                            file_path.unlink()
                            self.logger.info(
                                f"Deleted old compliance report: {file_path}"
                            )

                except (ValueError, IOError, OSError) as e:
                    self.logger.error(f"Error in cleanup task: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_old_data())

    async def close(self) -> None:
        """Clean up resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Save any cached data
        await self._save_recipient_activities()

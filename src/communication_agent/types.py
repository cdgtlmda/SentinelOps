"""
Common types and enums for the Communication Agent.
"""

from enum import Enum


class NotificationChannel(str, Enum):
    """Notification channel types."""

    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification status."""

    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class MessageType(str, Enum):
    """Message types."""

    INCIDENT_NOTIFICATION = "incident_notification"
    INCIDENT_DETECTED = "incident_detected"
    INCIDENT_ESCALATION = "incident_escalation"
    REMEDIATION_UPDATE = "remediation_update"
    REMEDIATION_STARTED = "remediation_started"
    REMEDIATION_COMPLETE = "remediation_complete"
    ANALYSIS_COMPLETE = "analysis_complete"
    STATUS_UPDATE = "status_update"
    SUMMARY_REPORT = "summary_report"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"
    ALERT = "alert"
    CRITICAL_ALERT = "critical_alert"
    SYSTEM_HEALTH = "system_health"

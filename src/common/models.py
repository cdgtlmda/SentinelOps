"""
Core domain models for SentinelOps.

This module contains all the core data structures used throughout the system.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from src.utils.datetime_utils import utcnow


class SeverityLevel(Enum):
    """Incident severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"

    def __lt__(self, other: "SeverityLevel") -> bool:
        """Compare severity levels for sorting."""
        if self.__class__ is other.__class__:
            severity_order = [
                SeverityLevel.INFORMATIONAL,
                SeverityLevel.LOW,
                SeverityLevel.MEDIUM,
                SeverityLevel.HIGH,
                SeverityLevel.CRITICAL,
            ]
            return severity_order.index(self) < severity_order.index(other)
        return NotImplemented

    def __le__(self, other: "SeverityLevel") -> bool:
        """Less than or equal comparison."""
        if self.__class__ is other.__class__:
            severity_order = [
                SeverityLevel.INFORMATIONAL,
                SeverityLevel.LOW,
                SeverityLevel.MEDIUM,
                SeverityLevel.HIGH,
                SeverityLevel.CRITICAL,
            ]
            return severity_order.index(self) <= severity_order.index(other)
        return NotImplemented

    def __gt__(self, other: "SeverityLevel") -> bool:
        """Greater than comparison."""
        if self.__class__ is other.__class__:
            severity_order = [
                SeverityLevel.INFORMATIONAL,
                SeverityLevel.LOW,
                SeverityLevel.MEDIUM,
                SeverityLevel.HIGH,
                SeverityLevel.CRITICAL,
            ]
            return severity_order.index(self) > severity_order.index(other)
        return NotImplemented

    def __ge__(self, other: "SeverityLevel") -> bool:
        """Greater than or equal comparison."""
        if self.__class__ is other.__class__:
            severity_order = [
                SeverityLevel.INFORMATIONAL,
                SeverityLevel.LOW,
                SeverityLevel.MEDIUM,
                SeverityLevel.HIGH,
                SeverityLevel.CRITICAL,
            ]
            return severity_order.index(self) >= severity_order.index(other)
        return NotImplemented


class IncidentStatus(Enum):
    """Incident lifecycle statuses."""

    DETECTED = "detected"
    ANALYZING = "analyzing"
    REMEDIATION_PENDING = "remediation_pending"
    APPROVAL_REQUIRED = "approval_required"
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class RemediationStatus(Enum):
    """Remediation action execution statuses."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class RemediationPriority(Enum):
    """Remediation action priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EventSource:
    """Represents the source of a security event."""

    source_type: str
    source_name: str
    source_id: str
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    resource_id: Optional[str] = None

    def validate(self) -> None:
        """Validate the event source data."""
        if not self.source_type:
            raise ValueError("source_type is required")
        if not self.source_name:
            raise ValueError("source_name is required")
        if not self.source_id:
            raise ValueError("source_id is required")


@dataclass
class SecurityEvent:
    """Represents a security event detected in the system."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = ""
    source: EventSource = field(default_factory=lambda: EventSource("", "", ""))
    severity: SeverityLevel = SeverityLevel.INFORMATIONAL
    description: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    actor: Optional[str] = None
    affected_resources: List[str] = field(default_factory=list)
    indicators: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the security event data."""
        if not self.event_type:
            raise ValueError("event_type is required")
        if not self.description:
            raise ValueError("description is required")
        self.source.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary representation."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "source": {
                "source_type": self.source.source_type,
                "source_name": self.source.source_name,
                "source_id": self.source.source_id,
                "resource_type": self.source.resource_type,
                "resource_name": self.source.resource_name,
                "resource_id": self.source.resource_id,
            },
            "severity": self.severity.value,
            "description": self.description,
            "raw_data": self.raw_data,
            "actor": self.actor,
            "affected_resources": self.affected_resources,
            "indicators": self.indicators,
        }


@dataclass
class AnalysisResult:
    """Represents the result of security event analysis."""

    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    incident_id: str = ""
    confidence_score: float = 0.0
    summary: str = ""
    detailed_analysis: str = ""
    related_events: List[SecurityEvent] = field(default_factory=list)
    attack_techniques: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    gemini_explanation: Optional[str] = None

    def validate(self) -> None:
        """Validate the analysis result data."""
        if not self.incident_id:
            raise ValueError("incident_id is required")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        if not self.summary:
            raise ValueError("summary is required")
        if not self.detailed_analysis:
            raise ValueError("detailed_analysis is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the analysis result to a dictionary representation."""
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp.isoformat(),
            "incident_id": self.incident_id,
            "confidence_score": self.confidence_score,
            "summary": self.summary,
            "detailed_analysis": self.detailed_analysis,
            "related_events": [event.to_dict() for event in self.related_events],
            "attack_techniques": self.attack_techniques,
            "recommendations": self.recommendations,
            "evidence": self.evidence,
            "gemini_explanation": self.gemini_explanation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        """Create an AnalysisResult from a dictionary."""
        # Make a copy to avoid modifying the original
        data = data.copy()

        # Remove fields that are not part of AnalysisResult
        data.pop("id", None)
        data.pop("created_at", None)

        # Convert timestamp
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert related events
        if "related_events" in data:
            events = []
            for event_data in data["related_events"]:
                # Convert event source
                if "source" in event_data:
                    event_data["source"] = EventSource(**event_data["source"])
                # Convert event severity
                if isinstance(event_data.get("severity"), str):
                    event_data["severity"] = SeverityLevel(event_data["severity"])
                # Convert event timestamp
                if isinstance(event_data.get("timestamp"), str):
                    event_data["timestamp"] = datetime.fromisoformat(
                        event_data["timestamp"]
                    )
                events.append(SecurityEvent(**event_data))
            data["related_events"] = events

        return cls(**data)


@dataclass
class RemediationAction:
    """Represents a remediation action to address a security incident."""

    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    incident_id: str = ""
    action_type: str = ""
    status: str = "pending"
    description: str = ""
    target_resource: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    approved_by: Optional[str] = None
    approval_time: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    automated: bool = True
    requires_approval: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the remediation action data."""
        if not self.incident_id:
            raise ValueError("incident_id is required")
        if not self.action_type:
            raise ValueError("action_type is required")
        if not self.description:
            raise ValueError("description is required")
        if not self.target_resource:
            raise ValueError("target_resource is required")
        valid_statuses = [
            "pending",
            "approved",
            "rejected",
            "executing",
            "completed",
            "failed",
        ]
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the remediation action to a dictionary representation."""
        return {
            "action_id": self.action_id,
            "timestamp": self.timestamp.isoformat(),
            "incident_id": self.incident_id,
            "action_type": self.action_type,
            "status": self.status,
            "description": self.description,
            "target_resource": self.target_resource,
            "params": self.params,
            "approved_by": self.approved_by,
            "approval_time": (
                self.approval_time.isoformat() if self.approval_time else None
            ),
            "execution_result": self.execution_result,
            "error_message": self.error_message,
            "automated": self.automated,
            "requires_approval": self.requires_approval,
            "metadata": self.metadata,
        }


@dataclass
class Notification:
    """Represents a notification sent regarding a security incident."""

    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    incident_id: str = ""
    notification_type: str = ""
    recipients: List[str] = field(default_factory=list)
    subject: str = ""
    content: str = ""
    status: str = "pending"
    error_message: Optional[str] = None

    def validate(self) -> None:
        """Validate the notification data."""
        if not self.incident_id:
            raise ValueError("incident_id is required")
        if not self.notification_type:
            raise ValueError("notification_type is required")
        if not self.recipients:
            raise ValueError("recipients list cannot be empty")
        if not self.subject:
            raise ValueError("subject is required")
        if not self.content:
            raise ValueError("content is required")
        valid_statuses = ["pending", "sent", "failed", "retrying"]
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the notification to a dictionary representation."""
        return {
            "notification_id": self.notification_id,
            "timestamp": self.timestamp.isoformat(),
            "incident_id": self.incident_id,
            "notification_type": self.notification_type,
            "recipients": self.recipients,
            "subject": self.subject,
            "content": self.content,
            "status": self.status,
            "error_message": self.error_message,
        }


@dataclass
class Incident:
    """Represents a security incident containing events, analysis, and actions."""

    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    title: str = ""
    description: str = ""
    severity: SeverityLevel = SeverityLevel.INFORMATIONAL
    status: IncidentStatus = IncidentStatus.DETECTED
    events: List[SecurityEvent] = field(default_factory=list)
    analysis: Optional[AnalysisResult] = None
    remediation_actions: List[RemediationAction] = field(default_factory=list)
    notifications: List[Notification] = field(default_factory=list)
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the incident data."""
        if not self.title:
            raise ValueError("title is required")
        if not self.description:
            raise ValueError("description is required")
        if not self.events:
            raise ValueError("incident must have at least one security event")

        # Validate all nested objects
        for event in self.events:
            event.validate()
        if self.analysis:
            self.analysis.validate()
        for action in self.remediation_actions:
            action.validate()
        for notification in self.notifications:
            notification.validate()

    def add_event(self, event: SecurityEvent) -> None:
        """Add a security event to the incident."""
        event.validate()
        self.events.append(event)
        self.updated_at = utcnow()
        # Update severity if the new event has higher severity
        if event.severity > self.severity:
            self.severity = event.severity

    def add_remediation_action(self, action: RemediationAction) -> None:
        """Add a remediation action to the incident."""
        action.validate()
        if action.incident_id != self.incident_id:
            action.incident_id = self.incident_id
        self.remediation_actions.append(action)
        self.updated_at = utcnow()

    def update_status(self, new_status: IncidentStatus) -> None:
        """Update the incident status."""
        self.status = new_status
        self.updated_at = utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the incident to a dictionary representation."""
        return {
            "incident_id": self.incident_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "events": [event.to_dict() for event in self.events],
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "remediation_actions": [
                action.to_dict() for action in self.remediation_actions
            ],
            "notifications": [notif.to_dict() for notif in self.notifications],
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Incident":
        """Create an Incident from a dictionary."""
        cls._convert_enums(data)
        cls._convert_timestamps(data)
        cls._convert_events(data)
        cls._convert_analysis(data)
        cls._convert_remediation_actions(data)
        cls._convert_notifications(data)
        return cls(**data)

    @classmethod
    def _convert_enums(cls, data: Dict[str, Any]) -> None:
        """Convert string values to enums."""
        if isinstance(data.get("severity"), str):
            data["severity"] = SeverityLevel(data["severity"])
        if isinstance(data.get("status"), str):
            data["status"] = IncidentStatus(data["status"])

    @classmethod
    def _convert_timestamps(cls, data: Dict[str, Any]) -> None:
        """Convert timestamp strings to datetime objects."""
        timestamp_fields = ["created_at", "updated_at"]
        for field_name in timestamp_fields:
            if isinstance(data.get(field_name), str):
                data[field_name] = datetime.fromisoformat(data[field_name])

    @classmethod
    def _convert_events(cls, data: Dict[str, Any]) -> None:
        """Convert event data."""
        if "events" not in data:
            return

        events = []
        for event_data in data["events"]:
            cls._convert_event_data(event_data)
            events.append(SecurityEvent(**event_data))
        data["events"] = events

    @classmethod
    def _convert_event_data(cls, event_data: Dict[str, Any]) -> None:
        """Convert individual event data."""
        if "source" in event_data:
            event_data["source"] = EventSource(**event_data["source"])
        if isinstance(event_data.get("severity"), str):
            event_data["severity"] = SeverityLevel(event_data["severity"])
        if isinstance(event_data.get("timestamp"), str):
            event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])

    @classmethod
    def _convert_analysis(cls, data: Dict[str, Any]) -> None:
        """Convert analysis data."""
        if data.get("analysis") and isinstance(data["analysis"], dict):
            analysis_data = data["analysis"]
            if isinstance(analysis_data.get("timestamp"), str):
                analysis_data["timestamp"] = datetime.fromisoformat(
                    analysis_data["timestamp"]
                )
            data["analysis"] = AnalysisResult(**analysis_data)

    @classmethod
    def _convert_remediation_actions(cls, data: Dict[str, Any]) -> None:
        """Convert remediation action data."""
        if "remediation_actions" not in data:
            return

        actions = []
        for action_data in data["remediation_actions"]:
            cls._convert_remediation_action_data(action_data)
            actions.append(RemediationAction(**action_data))
        data["remediation_actions"] = actions

    @classmethod
    def _convert_remediation_action_data(cls, action_data: Dict[str, Any]) -> None:
        """Convert individual remediation action data."""
        timestamp_fields = ["timestamp", "approval_time"]
        for field_name in timestamp_fields:
            if isinstance(action_data.get(field_name), str):
                action_data[field_name] = datetime.fromisoformat(
                    action_data[field_name]
                )

    @classmethod
    def _convert_notifications(cls, data: Dict[str, Any]) -> None:
        """Convert notification data."""
        if "notifications" not in data:
            return

        notifications = []
        for notif_data in data["notifications"]:
            cls._convert_notification_data(notif_data)
            notifications.append(Notification(**notif_data))
        data["notifications"] = notifications

    @classmethod
    def _convert_notification_data(cls, notif_data: Dict[str, Any]) -> None:
        """Convert individual notification data."""
        timestamp_fields = ["timestamp"]
        for field_name in timestamp_fields:
            if isinstance(notif_data.get(field_name), str):
                notif_data[field_name] = datetime.fromisoformat(notif_data[field_name])

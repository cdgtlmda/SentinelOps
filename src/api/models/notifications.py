"""Pydantic models for notification API endpoints."""

from datetime import datetime, time
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class NotificationChannelType(str, Enum):
    """Types of notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannelConfig(BaseModel):
    """Configuration for a notification channel."""

    # Email config
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    from_address: Optional[EmailStr] = None
    recipients: Optional[List[EmailStr]] = None

    # Slack config
    webhook_url: Optional[str] = None
    channel: Optional[str] = None
    mention_users: Optional[List[str]] = None

    # Teams config
    teams_webhook_url: Optional[str] = None
    teams_channel: Optional[str] = None

    # Generic webhook config
    url: Optional[str] = None
    method: Optional[str] = "POST"
    headers: Optional[Dict[str, str]] = None
    auth_type: Optional[str] = None  # none, basic, bearer, api_key

    class Config:
        schema_extra = {
            "example": {
                "recipients": ["security@company.com", "ops@company.com"],
                "from_address": "alerts@company.com",
            }
        }


class NotificationChannel(BaseModel):
    """Model for a notification channel."""

    channel_id: UUID
    channel_type: NotificationChannelType
    name: str
    description: Optional[str] = None
    enabled: bool = True
    config: NotificationChannelConfig
    test_mode: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_storage_model(cls, model: Any) -> "NotificationChannel":
        """Create from storage model."""
        return cls(
            channel_id=UUID(model.id),
            channel_type=model.channel_type,
            name=model.name,
            description=model.description,
            enabled=model.enabled,
            config=NotificationChannelConfig(**model.config),
            test_mode=model.test_mode,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    class Config:
        schema_extra = {
            "example": {
                "channel_id": "550e8400-e29b-41d4-a716-446655440000",
                "channel_type": "email",
                "name": "Security Team Email",
                "description": "Email notifications for security team",
                "enabled": True,
                "config": {
                    "recipients": ["security@company.com"],
                    "from_address": "alerts@company.com",
                },
                "test_mode": False,
                "created_at": "2024-01-15T10:30:00Z",
            }
        }


class NotificationSendRequest(BaseModel):
    """Request model for sending a notification."""

    incident_id: Optional[UUID] = Field(
        None, description="Associated incident ID if applicable"
    )
    notification_type: str = Field(
        ...,
        description="Type of notification (incident_detected, remediation_required, etc.)",
    )
    subject: str = Field(..., max_length=200)
    message: str = Field(..., max_length=5000)
    channels: List[str] = Field(
        ..., description="List of channel IDs to send notification to"
    )
    priority: NotificationPriority = NotificationPriority.MEDIUM
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {}, description="Additional metadata"
    )
    template_data: Optional[Dict[str, Any]] = Field(
        None, description="Data for template rendering if using templates"
    )

    @validator("channels")
    @classmethod
    def validate_channels(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one channel must be specified")
        if len(v) > 10:
            raise ValueError("Cannot send to more than 10 channels at once")
        return v

    class Config:
        schema_extra = {
            "example": {
                "incident_id": "660e8400-e29b-41d4-a716-446655440001",
                "notification_type": "incident_detected",
                "subject": "Critical Security Incident Detected",
                "message": (
                    "A critical security incident has been detected requiring "
                    "immediate attention."
                ),
                "channels": ["550e8400-e29b-41d4-a716-446655440000"],
                "priority": "critical",
                "metadata": {"source": "detection-agent", "rule_id": "rule-123"},
            }
        }


class NotificationSendResponse(BaseModel):
    """Response model for notification sending."""

    notification_id: UUID
    status: str  # sending, sent, failed, partially_sent
    channels_count: int
    message: str

    class Config:
        schema_extra = {
            "example": {
                "notification_id": "770e8400-e29b-41d4-a716-446655440000",
                "status": "sending",
                "channels_count": 2,
                "message": "Notifications are being sent",
            }
        }


class NotificationPreferences(BaseModel):
    """Model for user notification preferences."""

    user_id: str
    email_enabled: bool = True
    slack_enabled: bool = False
    teams_enabled: bool = False
    webhook_enabled: bool = False
    severity_filter: List[str] = Field(
        default_factory=lambda: ["critical", "high"],
        description="Minimum severity levels to notify for",
    )
    notification_types: List[str] = Field(
        default_factory=lambda: ["incident_detected", "remediation_required"],
        description="Types of notifications to receive",
    )
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    timezone: str = "UTC"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_storage_model(cls, model: Any) -> "NotificationPreferences":
        """Create from storage model."""
        return cls(
            user_id=model.user_id,
            email_enabled=model.email_enabled,
            slack_enabled=model.slack_enabled,
            teams_enabled=model.teams_enabled,
            webhook_enabled=model.webhook_enabled,
            severity_filter=model.severity_filter,
            notification_types=model.notification_types,
            quiet_hours_enabled=model.quiet_hours_enabled,
            quiet_hours_start=model.quiet_hours_start,
            quiet_hours_end=model.quiet_hours_end,
            timezone=model.timezone,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-123",
                "email_enabled": True,
                "slack_enabled": True,
                "teams_enabled": False,
                "webhook_enabled": False,
                "severity_filter": ["critical", "high", "medium"],
                "notification_types": [
                    "incident_detected",
                    "remediation_required",
                    "incident_resolved",
                ],
                "quiet_hours_enabled": True,
                "quiet_hours_start": "22:00:00",
                "quiet_hours_end": "08:00:00",
                "timezone": "America/New_York",
            }
        }


class NotificationPreferencesUpdate(BaseModel):
    """Model for updating notification preferences."""

    email_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    teams_enabled: Optional[bool] = None
    webhook_enabled: Optional[bool] = None
    severity_filter: Optional[List[str]] = None
    notification_types: Optional[List[str]] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    timezone: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "email_enabled": True,
                "severity_filter": ["critical", "high"],
                "quiet_hours_enabled": True,
                "quiet_hours_start": "22:00:00",
                "quiet_hours_end": "08:00:00",
            }
        }

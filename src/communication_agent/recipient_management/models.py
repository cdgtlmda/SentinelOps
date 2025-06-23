"""
Models for recipient management.

Defines data structures for recipients, contact information,
escalation chains, and on-call schedules.
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.communication_agent.types import NotificationChannel


class RecipientRole(str, Enum):
    """Roles for recipients in the system."""

    ADMIN = "admin"
    SECURITY_ENGINEER = "security_engineer"
    INCIDENT_RESPONDER = "incident_responder"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    ON_CALL = "on_call"
    EXTERNAL = "external"


class ContactStatus(str, Enum):
    """Status of a contact."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DO_NOT_DISTURB = "do_not_disturb"
    VACATION = "vacation"


@dataclass
class ContactInfo:
    """Contact information for a recipient."""

    channel: NotificationChannel
    address: str
    verified: bool = False
    preferred: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate contact info after initialization."""
        if not self.address:
            raise ValueError("Contact address cannot be empty")


@dataclass
class Recipient:
    """A recipient of notifications."""

    id: str
    name: str
    role: RecipientRole
    contacts: List[ContactInfo]
    status: ContactStatus = ContactStatus.ACTIVE
    timezone: str = "UTC"
    preferences: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_contact_for_channel(
        self,
        channel: NotificationChannel,
    ) -> Optional[ContactInfo]:
        """Get contact info for a specific channel."""
        # First try to find a preferred contact
        for contact in self.contacts:
            if contact.channel == channel and contact.preferred:
                return contact

        # Then find any contact for the channel
        for contact in self.contacts:
            if contact.channel == channel:
                return contact

        return None

    def get_all_contacts_for_channel(
        self,
        channel: NotificationChannel,
    ) -> List[ContactInfo]:
        """Get all contacts for a specific channel."""
        return [c for c in self.contacts if c.channel == channel]

    def is_available(self) -> bool:
        """Check if recipient is available for notifications."""
        return self.status == ContactStatus.ACTIVE

    def add_contact(self, contact: ContactInfo) -> None:
        """Add a contact to the recipient."""
        # Check if contact already exists
        for existing in self.contacts:
            if (
                existing.channel == contact.channel
                and existing.address == contact.address
            ):
                return

        self.contacts.append(contact)
        self.updated_at = datetime.now(timezone.utc)

    def remove_contact(
        self,
        channel: NotificationChannel,
        address: str,
    ) -> bool:
        """Remove a contact from the recipient."""
        original_count = len(self.contacts)
        self.contacts = [
            c
            for c in self.contacts
            if not (c.channel == channel and c.address == address)
        ]

        if len(self.contacts) < original_count:
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False


@dataclass
class EscalationLevel:
    """A level in an escalation chain."""

    level: int
    recipients: List[str]  # Recipient IDs
    delay_minutes: int = 0
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EscalationChain:
    """An escalation chain for incidents."""

    id: str
    name: str
    description: str
    levels: List[EscalationLevel]
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_recipients_for_level(self, level: int) -> List[str]:
        """Get recipients for a specific escalation level."""
        for esc_level in self.levels:
            if esc_level.level == level:
                return esc_level.recipients
        return []

    def get_next_level(self, current_level: int) -> Optional[EscalationLevel]:
        """Get the next escalation level."""
        next_level = current_level + 1
        for level in self.levels:
            if level.level == next_level:
                return level
        return None

    def add_level(self, level: EscalationLevel) -> None:
        """Add an escalation level."""
        # Keep levels sorted
        self.levels.append(level)
        self.levels.sort(key=lambda x: x.level)
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class OnCallShift:
    """A shift in an on-call schedule."""

    recipient_id: str
    start_time: datetime
    end_time: datetime
    is_primary: bool = True

    def is_active_at(self, timestamp: datetime) -> bool:
        """Check if shift is active at a given time."""
        return self.start_time <= timestamp < self.end_time


@dataclass
class OnCallSchedule:
    """An on-call schedule."""

    id: str
    name: str
    description: str
    shifts: List[OnCallShift]
    timezone: str = "UTC"
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_on_call_at(
        self,
        timestamp: datetime,
        primary_only: bool = False,
    ) -> List[str]:
        """Get on-call recipients at a specific time."""
        on_call = []
        for shift in self.shifts:
            if shift.is_active_at(timestamp):
                if not primary_only or shift.is_primary:
                    on_call.append(shift.recipient_id)
        return on_call

    def get_current_on_call(self, primary_only: bool = False) -> List[str]:
        """Get current on-call recipients."""
        return self.get_on_call_at(datetime.now(timezone.utc), primary_only)

    def add_shift(self, shift: OnCallShift) -> None:
        """Add a shift to the schedule."""
        # Validate no overlaps for primary shifts
        if shift.is_primary:
            for existing in self.shifts:
                if existing.is_primary and existing.recipient_id != shift.recipient_id:
                    # Check for overlap
                    if (
                        shift.start_time < existing.end_time
                        and shift.end_time > existing.start_time
                    ):
                        raise ValueError(
                            f"Primary shift overlaps with existing shift for "
                            f"recipient {existing.recipient_id}"
                        )

        self.shifts.append(shift)
        self.shifts.sort(key=lambda x: x.start_time)
        self.updated_at = datetime.now(timezone.utc)

    def remove_shifts_for_recipient(self, recipient_id: str) -> int:
        """Remove all shifts for a recipient."""
        original_count = len(self.shifts)
        self.shifts = [s for s in self.shifts if s.recipient_id != recipient_id]
        removed = original_count - len(self.shifts)

        if removed > 0:
            self.updated_at = datetime.now(timezone.utc)

        return removed


@dataclass
class NotificationPreferences:
    """Notification preferences for a recipient."""

    recipient_id: str
    channels: Dict[NotificationChannel, bool] = field(default_factory=dict)
    severity_threshold: str = "medium"
    quiet_hours_enabled: bool = False
    quiet_hours_start: time = time(22, 0)  # 10 PM
    quiet_hours_end: time = time(8, 0)  # 8 AM
    timezone: str = "UTC"
    frequency_limits: Dict[str, int] = field(default_factory=dict)
    excluded_types: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if a channel is enabled."""
        return self.channels.get(channel, True)

    def is_in_quiet_hours(self, timestamp: datetime) -> bool:
        """Check if a timestamp is within quiet hours."""
        if not self.quiet_hours_enabled:
            return False

        # Convert to recipient's timezone
        # For now, just use the time component
        current_time = timestamp.time()

        # Handle quiet hours that span midnight
        if self.quiet_hours_start > self.quiet_hours_end:
            return (
                current_time >= self.quiet_hours_start
                or current_time <= self.quiet_hours_end
            )
        else:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end

    def should_receive_notification(
        self,
        channel: NotificationChannel,
        notification_type: str,
        severity: str,
        timestamp: datetime,
    ) -> bool:
        """Check if recipient should receive a notification."""
        # Check if channel is enabled
        if not self.is_channel_enabled(channel):
            return False

        # Check if notification type is excluded
        if notification_type in self.excluded_types:
            return False

        # Check quiet hours (except for critical)
        if severity != "critical" and self.is_in_quiet_hours(timestamp):
            return False

        # Check severity threshold
        severity_levels = ["low", "medium", "high", "critical"]
        if severity in severity_levels:
            threshold_index = severity_levels.index(self.severity_threshold)
            severity_index = severity_levels.index(severity)
            if severity_index < threshold_index:
                return False

        return True

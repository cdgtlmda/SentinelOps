"""
Comprehensive tests for recipient management models.

Tests the data structures for recipients, contact information,
escalation chains, and on-call schedules with ≥90% statement coverage.

NO MOCKING - All tests use real implementation and production code.
COVERAGE REQUIREMENT: ≥90% statement coverage of recipient_management/models.py
VERIFICATION: python -m coverage run -m pytest tests/unit/communication_agent/recipient_management/test_models.py && python -m coverage report --include="*recipient_management/models.py" --show-missing
"""

import pytest
from datetime import datetime, time, timezone, timedelta

# Import the actual production code - NO MOCKS
from src.communication_agent.recipient_management.models import (
    RecipientRole,
    ContactStatus,
    ContactInfo,
    Recipient,
    EscalationLevel,
    EscalationChain,
    OnCallShift,
    OnCallSchedule,
    NotificationPreferences,
)
from src.communication_agent.types import NotificationChannel


class TestRecipientRole:
    """Test RecipientRole enum with real implementation."""

    def test_recipient_role_values(self) -> None:
        """Test all RecipientRole enum values."""
        assert RecipientRole.ADMIN.value == "admin"
        assert RecipientRole.SECURITY_ENGINEER.value == "security_engineer"
        assert RecipientRole.INCIDENT_RESPONDER.value == "incident_responder"
        assert RecipientRole.MANAGER.value == "manager"
        assert RecipientRole.EXECUTIVE.value == "executive"
        assert RecipientRole.ON_CALL.value == "on_call"
        assert RecipientRole.EXTERNAL.value == "external"

    def test_recipient_role_enum_behavior(self) -> None:
        """Test RecipientRole enum behavior."""
        # Test enum membership
        assert RecipientRole.ADMIN in RecipientRole
        assert "admin" == RecipientRole.ADMIN.value

        # Test iteration
        roles = list(RecipientRole)
        assert len(roles) == 7

    def test_recipient_role_string_representation(self) -> None:
        """Test string representation of roles."""
        assert str(RecipientRole.SECURITY_ENGINEER) == "security_engineer"
        assert repr(RecipientRole.MANAGER) == "<RecipientRole.MANAGER: 'manager'>"


class TestContactStatus:
    """Test ContactStatus enum with real implementation."""

    def test_contact_status_values(self) -> None:
        """Test all ContactStatus enum values."""
        assert ContactStatus.ACTIVE.value == "active"
        assert ContactStatus.INACTIVE.value == "inactive"
        assert ContactStatus.DO_NOT_DISTURB.value == "do_not_disturb"
        assert ContactStatus.VACATION.value == "vacation"

    def test_contact_status_enum_behavior(self) -> None:
        """Test ContactStatus enum behavior."""
        assert ContactStatus.ACTIVE in ContactStatus
        assert len(list(ContactStatus)) == 4

    def test_contact_status_comparison(self) -> None:
        """Test contact status comparisons."""
        assert ContactStatus.ACTIVE == ContactStatus.ACTIVE
        # Test different enum values
        active_status = ContactStatus.ACTIVE
        inactive_status = ContactStatus.INACTIVE
        assert active_status != inactive_status


class TestContactInfo:
    """Test ContactInfo model with real implementation."""

    def test_contact_info_creation(self) -> None:
        """Test basic ContactInfo creation."""
        contact = ContactInfo(
            channel=NotificationChannel.EMAIL,
            address="test@example.com",
            verified=True,
            preferred=False,
        )

        assert contact.channel == NotificationChannel.EMAIL
        assert contact.address == "test@example.com"
        assert contact.verified is True
        assert contact.preferred is False
        assert contact.metadata == {}

    def test_contact_info_with_preferences(self) -> None:
        """Test ContactInfo with preferred flag."""
        contact = ContactInfo(
            channel=NotificationChannel.SMS,
            address="+1234567890",
            verified=True,
            preferred=True,
        )

        assert contact.preferred is True

    def test_contact_info_with_metadata(self) -> None:
        """Test ContactInfo with metadata."""
        metadata = {"provider": "twilio", "region": "us-east-1"}

        contact = ContactInfo(
            channel=NotificationChannel.SMS,
            address="+1234567890",
            verified=False,
            metadata=metadata,
        )

        assert contact.metadata == metadata

    def test_contact_info_different_channels(self) -> None:
        """Test ContactInfo with different notification channels."""
        channels_addresses = [
            (NotificationChannel.EMAIL, "user@example.com"),
            (NotificationChannel.SMS, "+1234567890"),
            (NotificationChannel.SLACK, "@username"),
            (NotificationChannel.WEBHOOK, "https://api.example.com/webhook"),
        ]

        for channel, address in channels_addresses:
            contact = ContactInfo(channel=channel, address=address, verified=True)

            assert contact.channel == channel
            assert contact.address == address

    def test_contact_info_validation_empty_address(self) -> None:
        """Test ContactInfo validation with empty address."""
        with pytest.raises(ValueError, match="Contact address cannot be empty"):
            ContactInfo(channel=NotificationChannel.EMAIL, address="", verified=False)

    def test_contact_info_post_init_validation(self) -> None:
        """Test ContactInfo __post_init__ validation."""
        # Valid contact should not raise
        contact = ContactInfo(
            channel=NotificationChannel.EMAIL,
            address="valid@example.com",
            verified=True,
        )
        assert contact.address == "valid@example.com"

    def test_contact_info_edge_cases(self) -> None:
        """Test ContactInfo edge cases."""
        # Very long address
        long_address = "a" * 1000 + "@example.com"
        contact = ContactInfo(
            channel=NotificationChannel.EMAIL, address=long_address, verified=True
        )
        assert contact.address == long_address


class TestRecipient:
    """Test Recipient model with real implementation."""

    def test_recipient_creation_minimal(self) -> None:
        """Test Recipient creation with minimal data."""
        recipient = Recipient(
            id="user123",
            name="Test User",
            role=RecipientRole.SECURITY_ENGINEER,
            contacts=[],
        )

        assert recipient.id == "user123"
        assert recipient.name == "Test User"
        assert recipient.role == RecipientRole.SECURITY_ENGINEER
        assert recipient.contacts == []
        assert recipient.status == ContactStatus.ACTIVE  # Default
        assert recipient.timezone == "UTC"  # Default
        assert recipient.preferences == {}
        assert recipient.tags == set()
        assert isinstance(recipient.created_at, datetime)
        assert isinstance(recipient.updated_at, datetime)

    def test_recipient_creation_complete(self) -> None:
        """Test Recipient creation with complete data."""
        contacts = [
            ContactInfo(
                channel=NotificationChannel.EMAIL,
                address="user@example.com",
                verified=True,
            ),
            ContactInfo(
                channel=NotificationChannel.SMS, address="+1234567890", verified=True
            ),
        ]

        preferences = {"notification_frequency": "immediate"}
        tags = {"security", "on-call"}

        recipient = Recipient(
            id="complete_user",
            name="Complete User",
            role=RecipientRole.ADMIN,
            contacts=contacts,
            status=ContactStatus.ACTIVE,
            timezone="America/New_York",
            preferences=preferences,
            tags=tags,
        )

        assert recipient.id == "complete_user"
        assert recipient.name == "Complete User"
        assert recipient.role == RecipientRole.ADMIN
        assert len(recipient.contacts) == 2
        assert recipient.status == ContactStatus.ACTIVE
        assert recipient.timezone == "America/New_York"
        assert recipient.preferences == preferences
        assert recipient.tags == tags

    def test_recipient_get_contact_for_channel(self) -> None:
        """Test getting contact for specific channel."""
        contacts = [
            ContactInfo(
                channel=NotificationChannel.EMAIL,
                address="primary@example.com",
                verified=True,
                preferred=True,
            ),
            ContactInfo(
                channel=NotificationChannel.EMAIL,
                address="secondary@example.com",
                verified=True,
                preferred=False,
            ),
            ContactInfo(
                channel=NotificationChannel.SMS, address="+1234567890", verified=True
            ),
        ]

        recipient = Recipient(
            id="multi_contact",
            name="Multi Contact User",
            role=RecipientRole.INCIDENT_RESPONDER,
            contacts=contacts,
        )

        # Should return preferred email contact
        email_contact = recipient.get_contact_for_channel(NotificationChannel.EMAIL)
        assert email_contact is not None
        assert email_contact.address == "primary@example.com"
        assert email_contact.preferred is True

        # Should return SMS contact
        sms_contact = recipient.get_contact_for_channel(NotificationChannel.SMS)
        assert sms_contact is not None
        assert sms_contact.address == "+1234567890"

        # Should return None for non-existent channel
        webhook_contact = recipient.get_contact_for_channel(NotificationChannel.WEBHOOK)
        assert webhook_contact is None

    def test_recipient_get_contact_for_channel_no_preferred(self) -> None:
        """Test getting contact when no preferred contact exists."""
        contacts = [
            ContactInfo(
                channel=NotificationChannel.EMAIL,
                address="first@example.com",
                verified=True,
                preferred=False,
            ),
            ContactInfo(
                channel=NotificationChannel.EMAIL,
                address="second@example.com",
                verified=True,
                preferred=False,
            ),
        ]

        recipient = Recipient(
            id="no_preferred",
            name="No Preferred User",
            role=RecipientRole.SECURITY_ENGINEER,
            contacts=contacts,
        )

        # Should return first available contact
        email_contact = recipient.get_contact_for_channel(NotificationChannel.EMAIL)
        assert email_contact is not None
        assert email_contact.address in ["first@example.com", "second@example.com"]

    def test_recipient_get_all_contacts_for_channel(self) -> None:
        """Test getting all contacts for a channel."""
        contacts = [
            ContactInfo(
                channel=NotificationChannel.EMAIL,
                address="email1@example.com",
                verified=True,
            ),
            ContactInfo(
                channel=NotificationChannel.EMAIL,
                address="email2@example.com",
                verified=True,
            ),
            ContactInfo(
                channel=NotificationChannel.SMS, address="+1111111111", verified=True
            ),
        ]

        recipient = Recipient(
            id="multiple_emails",
            name="Multiple Emails User",
            role=RecipientRole.MANAGER,
            contacts=contacts,
        )

        email_contacts = recipient.get_all_contacts_for_channel(
            NotificationChannel.EMAIL
        )
        assert len(email_contacts) == 2

        sms_contacts = recipient.get_all_contacts_for_channel(NotificationChannel.SMS)
        assert len(sms_contacts) == 1

        slack_contacts = recipient.get_all_contacts_for_channel(
            NotificationChannel.SLACK
        )
        assert len(slack_contacts) == 0

    def test_recipient_is_available(self) -> None:
        """Test recipient availability check."""
        # Active recipient should be available
        active_recipient = Recipient(
            id="active_user",
            name="Active User",
            role=RecipientRole.SECURITY_ENGINEER,
            contacts=[],
            status=ContactStatus.ACTIVE,
        )
        assert active_recipient.is_available() is True

        # Inactive recipient should not be available
        inactive_recipient = Recipient(
            id="inactive_user",
            name="Inactive User",
            role=RecipientRole.SECURITY_ENGINEER,
            contacts=[],
            status=ContactStatus.INACTIVE,
        )
        assert inactive_recipient.is_available() is False

        # Do not disturb recipient should not be available
        dnd_recipient = Recipient(
            id="dnd_user",
            name="DND User",
            role=RecipientRole.SECURITY_ENGINEER,
            contacts=[],
            status=ContactStatus.DO_NOT_DISTURB,
        )
        assert dnd_recipient.is_available() is False

    def test_recipient_add_contact(self) -> None:
        """Test adding contact to recipient."""
        recipient = Recipient(
            id="add_contact_user",
            name="Add Contact User",
            role=RecipientRole.ADMIN,
            contacts=[],
        )

        initial_updated_at = recipient.updated_at

        # Add new contact
        new_contact = ContactInfo(
            channel=NotificationChannel.EMAIL, address="new@example.com", verified=True
        )

        recipient.add_contact(new_contact)

        assert len(recipient.contacts) == 1
        assert recipient.contacts[0].address == "new@example.com"
        assert recipient.updated_at > initial_updated_at

    def test_recipient_add_duplicate_contact(self) -> None:
        """Test adding duplicate contact (should not add)."""
        existing_contact = ContactInfo(
            channel=NotificationChannel.EMAIL,
            address="existing@example.com",
            verified=True,
        )

        recipient = Recipient(
            id="duplicate_user",
            name="Duplicate User",
            role=RecipientRole.SECURITY_ENGINEER,
            contacts=[existing_contact],
        )

        # Try to add duplicate
        duplicate_contact = ContactInfo(
            channel=NotificationChannel.EMAIL,
            address="existing@example.com",
            verified=False,  # Different verification status
        )

        recipient.add_contact(duplicate_contact)

        # Should still have only one contact
        assert len(recipient.contacts) == 1

    def test_recipient_remove_contact(self) -> None:
        """Test removing contact from recipient."""
        contact_to_remove = ContactInfo(
            channel=NotificationChannel.SMS, address="+1234567890", verified=True
        )

        contact_to_keep = ContactInfo(
            channel=NotificationChannel.EMAIL, address="keep@example.com", verified=True
        )

        recipient = Recipient(
            id="remove_contact_user",
            name="Remove Contact User",
            role=RecipientRole.MANAGER,
            contacts=[contact_to_remove, contact_to_keep],
        )

        initial_updated_at = recipient.updated_at

        # Remove contact
        removed = recipient.remove_contact(NotificationChannel.SMS, "+1234567890")

        assert removed is True
        assert len(recipient.contacts) == 1
        assert recipient.contacts[0].address == "keep@example.com"
        assert recipient.updated_at > initial_updated_at

    def test_recipient_remove_nonexistent_contact(self) -> None:
        """Test removing non-existent contact."""
        recipient = Recipient(
            id="no_remove_user",
            name="No Remove User",
            role=RecipientRole.SECURITY_ENGINEER,
            contacts=[],
        )

        # Try to remove non-existent contact
        removed = recipient.remove_contact(
            NotificationChannel.EMAIL, "nonexistent@example.com"
        )

        assert removed is False
        assert len(recipient.contacts) == 0


class TestEscalationLevel:
    """Test EscalationLevel dataclass with real implementation."""

    def test_escalation_level_creation(self) -> None:
        """Test EscalationLevel creation."""
        level = EscalationLevel(
            level=1,
            recipients=["user1", "user2"],
            delay_minutes=15,
            conditions={"severity": "high"},
        )

        assert level.level == 1
        assert level.recipients == ["user1", "user2"]
        assert level.delay_minutes == 15
        assert level.conditions == {"severity": "high"}

    def test_escalation_level_defaults(self) -> None:
        """Test EscalationLevel with default values."""
        level = EscalationLevel(level=2, recipients=["user3"])

        assert level.level == 2
        assert level.recipients == ["user3"]
        assert level.delay_minutes == 0  # Default
        assert level.conditions == {}  # Default

    def test_escalation_level_empty_recipients(self) -> None:
        """Test EscalationLevel with empty recipients."""
        level = EscalationLevel(level=0, recipients=[])

        assert level.recipients == []

    def test_escalation_level_complex_conditions(self) -> None:
        """Test EscalationLevel with complex conditions."""
        conditions = {
            "severity": ["high", "critical"],
            "time_of_day": "business_hours",
            "incident_type": "security",
        }

        level = EscalationLevel(
            level=3,
            recipients=["manager1", "manager2"],
            delay_minutes=30,
            conditions=conditions,
        )

        assert level.conditions == conditions


class TestEscalationChain:
    """Test EscalationChain model with real implementation."""

    def test_escalation_chain_creation(self) -> None:
        """Test EscalationChain creation."""
        chain = EscalationChain(
            id="chain123",
            name="Security Team Escalation",
            description="Escalation chain for security incidents",
            levels=[],
        )

        assert chain.id == "chain123"
        assert chain.name == "Security Team Escalation"
        assert chain.description == "Escalation chain for security incidents"
        assert chain.levels == []
        assert chain.enabled is True  # Default
        assert chain.tags == set()
        assert isinstance(chain.created_at, datetime)
        assert isinstance(chain.updated_at, datetime)

    def test_escalation_chain_with_levels(self) -> None:
        """Test EscalationChain with escalation levels."""
        levels = [
            EscalationLevel(level=1, recipients=["user1"], delay_minutes=0),
            EscalationLevel(level=2, recipients=["user2"], delay_minutes=15),
            EscalationLevel(level=3, recipients=["manager1"], delay_minutes=30),
        ]

        chain = EscalationChain(
            id="full_chain",
            name="Full Escalation Chain",
            description="Complete escalation with multiple levels",
            levels=levels,
            enabled=True,
            tags={"security", "critical"},
        )

        assert len(chain.levels) == 3
        assert chain.levels[0].level == 1
        assert chain.levels[1].delay_minutes == 15
        assert chain.levels[2].recipients == ["manager1"]
        assert "security" in chain.tags

    def test_escalation_chain_get_recipients_for_level(self) -> None:
        """Test getting recipients for specific level."""
        levels = [
            EscalationLevel(level=1, recipients=["user1", "user2"]),
            EscalationLevel(level=2, recipients=["manager1"]),
            EscalationLevel(level=3, recipients=["executive1"]),
        ]

        chain = EscalationChain(
            id="test_chain",
            name="Test Chain",
            description="Test escalation chain",
            levels=levels,
        )

        level1_recipients = chain.get_recipients_for_level(1)
        assert level1_recipients == ["user1", "user2"]

        level2_recipients = chain.get_recipients_for_level(2)
        assert level2_recipients == ["manager1"]

        nonexistent_recipients = chain.get_recipients_for_level(99)
        assert nonexistent_recipients == []

    def test_escalation_chain_get_next_level(self) -> None:
        """Test getting next escalation level."""
        levels = [
            EscalationLevel(level=1, recipients=["user1"]),
            EscalationLevel(level=3, recipients=["user3"]),  # Skip level 2
            EscalationLevel(level=4, recipients=["user4"]),
        ]

        chain = EscalationChain(
            id="next_level_chain",
            name="Next Level Chain",
            description="Chain for testing next level",
            levels=levels,
        )

        # Level 2 should return level 3
        next_level = chain.get_next_level(1)
        assert next_level is None  # No level 2

        # Level 3 should return level 4
        next_level = chain.get_next_level(3)
        assert next_level is not None
        assert next_level.level == 4

        # Last level should return None
        next_level = chain.get_next_level(4)
        assert next_level is None

    def test_escalation_chain_add_level(self) -> None:
        """Test adding escalation level."""
        chain = EscalationChain(
            id="add_level_chain",
            name="Add Level Chain",
            description="Chain for testing add level",
            levels=[],
        )

        initial_updated_at = chain.updated_at

        # Add first level
        level1 = EscalationLevel(level=1, recipients=["user1"])
        chain.add_level(level1)

        assert len(chain.levels) == 1
        assert chain.levels[0].level == 1
        assert chain.updated_at > initial_updated_at

        # Add level out of order (should be sorted)
        level3 = EscalationLevel(level=3, recipients=["user3"])
        level2 = EscalationLevel(level=2, recipients=["user2"])

        chain.add_level(level3)
        chain.add_level(level2)

        assert len(chain.levels) == 3
        # Should be sorted by level
        assert chain.levels[0].level == 1
        assert chain.levels[1].level == 2
        assert chain.levels[2].level == 3

    def test_escalation_chain_disabled(self) -> None:
        """Test disabled escalation chain."""
        chain = EscalationChain(
            id="disabled_chain",
            name="Disabled Chain",
            description="Disabled escalation chain",
            levels=[],
            enabled=False,
        )

        assert chain.enabled is False


class TestOnCallShift:
    """Test OnCallShift model with real implementation."""

    def test_on_call_shift_creation(self) -> None:
        """Test OnCallShift creation."""
        start_time = datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc)

        shift = OnCallShift(
            recipient_id="user123",
            start_time=start_time,
            end_time=end_time,
            is_primary=True,
        )

        assert shift.recipient_id == "user123"
        assert shift.start_time == start_time
        assert shift.end_time == end_time
        assert shift.is_primary is True

    def test_on_call_shift_secondary(self) -> None:
        """Test OnCallShift as secondary."""
        start_time = datetime(2025, 6, 14, 18, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 6, 15, 6, 0, tzinfo=timezone.utc)

        shift = OnCallShift(
            recipient_id="backup_user",
            start_time=start_time,
            end_time=end_time,
            is_primary=False,
        )

        assert shift.is_primary is False

    def test_on_call_shift_is_active_at(self) -> None:
        """Test checking if shift is active at specific time."""
        start_time = datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc)

        shift = OnCallShift(
            recipient_id="test_user", start_time=start_time, end_time=end_time
        )

        # Before shift
        before_shift = datetime(2025, 6, 14, 8, 59, tzinfo=timezone.utc)
        assert shift.is_active_at(before_shift) is False

        # During shift
        during_shift = datetime(2025, 6, 14, 12, 0, tzinfo=timezone.utc)
        assert shift.is_active_at(during_shift) is True

        # At start time (inclusive)
        at_start = start_time
        assert shift.is_active_at(at_start) is True

        # At end time (exclusive)
        at_end = end_time
        assert shift.is_active_at(at_end) is False

        # After shift
        after_shift = datetime(2025, 6, 14, 17, 1, tzinfo=timezone.utc)
        assert shift.is_active_at(after_shift) is False


class TestOnCallSchedule:
    """Test OnCallSchedule model with real implementation."""

    def test_on_call_schedule_creation(self) -> None:
        """Test OnCallSchedule creation."""
        schedule = OnCallSchedule(
            id="schedule123",
            name="Security Team Schedule",
            description="On-call schedule for security team",
            shifts=[],
        )

        assert schedule.id == "schedule123"
        assert schedule.name == "Security Team Schedule"
        assert schedule.description == "On-call schedule for security team"
        assert schedule.shifts == []
        assert schedule.timezone == "UTC"  # Default
        assert schedule.enabled is True  # Default
        assert schedule.tags == set()
        assert isinstance(schedule.created_at, datetime)
        assert isinstance(schedule.updated_at, datetime)

    def test_on_call_schedule_with_shifts(self) -> None:
        """Test OnCallSchedule with shifts."""
        shift1 = OnCallShift(
            recipient_id="user1",
            start_time=datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        shift2 = OnCallShift(
            recipient_id="user2",
            start_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 15, 9, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        schedule = OnCallSchedule(
            id="shift_schedule",
            name="24/7 Schedule",
            description="24/7 on-call coverage",
            shifts=[shift1, shift2],
            timezone="America/New_York",
            tags={"24x7", "critical"},
        )

        assert len(schedule.shifts) == 2
        assert schedule.timezone == "America/New_York"
        assert "24x7" in schedule.tags

    def test_on_call_schedule_get_on_call_at(self) -> None:
        """Test getting on-call recipients at specific time."""
        shift1 = OnCallShift(
            recipient_id="day_user",
            start_time=datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        shift2 = OnCallShift(
            recipient_id="night_user",
            start_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 15, 9, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        shift3 = OnCallShift(
            recipient_id="backup_user",
            start_time=datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 15, 9, 0, tzinfo=timezone.utc),
            is_primary=False,
        )

        schedule = OnCallSchedule(
            id="complex_schedule",
            name="Complex Schedule",
            description="Schedule with primary and backup",
            shifts=[shift1, shift2, shift3],
        )

        # During day shift
        day_time = datetime(2025, 6, 14, 12, 0, tzinfo=timezone.utc)
        on_call = schedule.get_on_call_at(day_time)
        assert "day_user" in on_call
        assert "backup_user" in on_call
        assert len(on_call) == 2

        # Primary only during day shift
        primary_only = schedule.get_on_call_at(day_time, primary_only=True)
        assert primary_only == ["day_user"]

        # During night shift
        night_time = datetime(2025, 6, 14, 22, 0, tzinfo=timezone.utc)
        on_call = schedule.get_on_call_at(night_time)
        assert "night_user" in on_call
        assert "backup_user" in on_call

    def test_on_call_schedule_get_current_on_call(self) -> None:
        """Test getting current on-call recipients."""
        # Create a shift that's currently active (using current time)
        now = datetime.now(timezone.utc)
        current_shift = OnCallShift(
            recipient_id="current_user",
            start_time=now - timedelta(hours=1),  # Started 1 hour ago
            end_time=now + timedelta(hours=1),  # Ends in 1 hour
            is_primary=True,
        )

        schedule = OnCallSchedule(
            id="current_schedule",
            name="Current Schedule",
            description="Schedule for testing current on-call",
            shifts=[current_shift],
        )

        current_on_call = schedule.get_current_on_call()
        assert "current_user" in current_on_call

    def test_on_call_schedule_add_shift(self) -> None:
        """Test adding shift to schedule."""
        schedule = OnCallSchedule(
            id="add_shift_schedule",
            name="Add Shift Schedule",
            description="Schedule for testing add shift",
            shifts=[],
        )

        initial_updated_at = schedule.updated_at

        shift = OnCallShift(
            recipient_id="new_user",
            start_time=datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        schedule.add_shift(shift)

        assert len(schedule.shifts) == 1
        assert schedule.shifts[0].recipient_id == "new_user"
        assert schedule.updated_at > initial_updated_at

    def test_on_call_schedule_add_shift_overlap_validation(self) -> None:
        """Test validation of overlapping primary shifts."""
        existing_shift = OnCallShift(
            recipient_id="existing_user",
            start_time=datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        schedule = OnCallSchedule(
            id="overlap_schedule",
            name="Overlap Schedule",
            description="Schedule for testing overlaps",
            shifts=[existing_shift],
        )

        # Try to add overlapping primary shift
        overlapping_shift = OnCallShift(
            recipient_id="overlapping_user",
            start_time=datetime(2025, 6, 14, 12, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 20, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        with pytest.raises(ValueError, match="Primary shift overlaps"):
            schedule.add_shift(overlapping_shift)

    def test_on_call_schedule_add_shift_no_overlap_same_user(self) -> None:
        """Test that same user can have overlapping shifts."""
        user_shift1 = OnCallShift(
            recipient_id="same_user",
            start_time=datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        schedule = OnCallSchedule(
            id="same_user_schedule",
            name="Same User Schedule",
            description="Schedule for same user testing",
            shifts=[user_shift1],
        )

        # Same user can have overlapping shifts
        user_shift2 = OnCallShift(
            recipient_id="same_user",
            start_time=datetime(2025, 6, 14, 12, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 20, 0, tzinfo=timezone.utc),
            is_primary=True,
        )

        # Should not raise exception
        schedule.add_shift(user_shift2)
        assert len(schedule.shifts) == 2

    def test_on_call_schedule_add_shift_sorting(self) -> None:
        """Test that shifts are sorted by start time."""
        schedule = OnCallSchedule(
            id="sort_schedule",
            name="Sort Schedule",
            description="Schedule for testing sorting",
            shifts=[],
        )

        # Add shifts out of order
        shift3 = OnCallShift(
            recipient_id="user3",
            start_time=datetime(2025, 6, 14, 15, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 23, 0, tzinfo=timezone.utc),
        )

        shift1 = OnCallShift(
            recipient_id="user1",
            start_time=datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
        )

        shift2 = OnCallShift(
            recipient_id="user2",
            start_time=datetime(2025, 6, 14, 12, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 6, 14, 20, 0, tzinfo=timezone.utc),
        )

        schedule.add_shift(shift3)
        schedule.add_shift(shift1)
        schedule.add_shift(shift2)

        # Should be sorted by start time
        assert schedule.shifts[0].recipient_id == "user1"
        assert schedule.shifts[1].recipient_id == "user2"
        assert schedule.shifts[2].recipient_id == "user3"

    def test_on_call_schedule_remove_shifts_for_recipient(self) -> None:
        """Test removing all shifts for a recipient."""
        shifts = [
            OnCallShift(
                recipient_id="user1",
                start_time=datetime(2025, 6, 14, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
            ),
            OnCallShift(
                recipient_id="user2",
                start_time=datetime(2025, 6, 14, 17, 0, tzinfo=timezone.utc),
                end_time=datetime(2025, 6, 15, 9, 0, tzinfo=timezone.utc),
            ),
            OnCallShift(
                recipient_id="user1",
                start_time=datetime(2025, 6, 15, 9, 0, tzinfo=timezone.utc),
                end_time=datetime(2025, 6, 15, 17, 0, tzinfo=timezone.utc),
            ),
        ]

        schedule = OnCallSchedule(
            id="remove_schedule",
            name="Remove Schedule",
            description="Schedule for testing removal",
            shifts=shifts,
        )

        initial_updated_at = schedule.updated_at

        # Remove all shifts for user1
        removed_count = schedule.remove_shifts_for_recipient("user1")

        assert removed_count == 2
        assert len(schedule.shifts) == 1
        assert schedule.shifts[0].recipient_id == "user2"
        assert schedule.updated_at > initial_updated_at

        # Try to remove shifts for non-existent user
        removed_count = schedule.remove_shifts_for_recipient("nonexistent")
        assert removed_count == 0


class TestNotificationPreferences:
    """Test NotificationPreferences model with real implementation."""

    def test_notification_preferences_creation(self) -> None:
        """Test NotificationPreferences creation."""
        preferences = NotificationPreferences(recipient_id="user123")

        assert preferences.recipient_id == "user123"
        assert preferences.channels == {}  # Default
        assert preferences.severity_threshold == "medium"  # Default
        assert preferences.quiet_hours_enabled is False  # Default
        assert preferences.quiet_hours_start == time(22, 0)  # Default
        assert preferences.quiet_hours_end == time(8, 0)  # Default
        assert preferences.timezone == "UTC"  # Default
        assert preferences.frequency_limits == {}
        assert preferences.excluded_types == set()
        assert preferences.metadata == {}

    def test_notification_preferences_complete(self) -> None:
        """Test NotificationPreferences with complete configuration."""
        channels = {
            NotificationChannel.EMAIL: True,
            NotificationChannel.SMS: True,
            NotificationChannel.SLACK: False,
        }

        frequency_limits = {"per_hour": 10, "per_day": 50}
        excluded_types = {"maintenance", "test"}
        metadata = {"last_updated": "2025-06-14", "version": "1.0"}

        preferences = NotificationPreferences(
            recipient_id="complete_user",
            channels=channels,
            severity_threshold="high",
            quiet_hours_enabled=True,
            quiet_hours_start=time(23, 0),
            quiet_hours_end=time(7, 0),
            timezone="America/New_York",
            frequency_limits=frequency_limits,
            excluded_types=excluded_types,
            metadata=metadata,
        )

        assert preferences.channels == channels
        assert preferences.severity_threshold == "high"
        assert preferences.quiet_hours_enabled is True
        assert preferences.quiet_hours_start == time(23, 0)
        assert preferences.quiet_hours_end == time(7, 0)
        assert preferences.timezone == "America/New_York"
        assert preferences.frequency_limits == frequency_limits
        assert preferences.excluded_types == excluded_types
        assert preferences.metadata == metadata

    def test_notification_preferences_is_channel_enabled(self) -> None:
        """Test checking if channel is enabled."""
        channels = {NotificationChannel.EMAIL: True, NotificationChannel.SMS: False}

        preferences = NotificationPreferences(
            recipient_id="channel_test", channels=channels
        )

        # Explicitly enabled
        assert preferences.is_channel_enabled(NotificationChannel.EMAIL) is True

        # Explicitly disabled
        assert preferences.is_channel_enabled(NotificationChannel.SMS) is False

        # Not specified (should default to True)
        assert preferences.is_channel_enabled(NotificationChannel.SLACK) is True

    def test_notification_preferences_is_in_quiet_hours(self) -> None:
        """Test checking if timestamp is in quiet hours."""
        preferences = NotificationPreferences(
            recipient_id="quiet_test",
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),  # 10 PM
            quiet_hours_end=time(8, 0),  # 8 AM
        )

        # During quiet hours (midnight)
        midnight = datetime(2025, 6, 14, 0, 0, tzinfo=timezone.utc)
        assert preferences.is_in_quiet_hours(midnight) is True

        # During quiet hours (6 AM)
        early_morning = datetime(2025, 6, 14, 6, 0, tzinfo=timezone.utc)
        assert preferences.is_in_quiet_hours(early_morning) is True

        # Not in quiet hours (noon)
        noon = datetime(2025, 6, 14, 12, 0, tzinfo=timezone.utc)
        assert preferences.is_in_quiet_hours(noon) is False

        # At quiet hours start (inclusive)
        start_time = datetime(2025, 6, 14, 22, 0, tzinfo=timezone.utc)
        assert preferences.is_in_quiet_hours(start_time) is True

        # At quiet hours end (inclusive)
        end_time = datetime(2025, 6, 14, 8, 0, tzinfo=timezone.utc)
        assert preferences.is_in_quiet_hours(end_time) is True

    def test_notification_preferences_quiet_hours_disabled(self) -> None:
        """Test quiet hours when disabled."""
        preferences = NotificationPreferences(
            recipient_id="no_quiet_test", quiet_hours_enabled=False
        )

        # Should never be in quiet hours when disabled
        midnight = datetime(2025, 6, 14, 0, 0, tzinfo=timezone.utc)
        assert preferences.is_in_quiet_hours(midnight) is False

    def test_notification_preferences_should_receive_notification(self) -> None:
        """Test comprehensive notification decision logic."""
        preferences = NotificationPreferences(
            recipient_id="decision_test",
            channels={NotificationChannel.EMAIL: True, NotificationChannel.SMS: False},
            severity_threshold="medium",
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
            excluded_types={"maintenance"},
        )

        # Test time during business hours
        business_time = datetime(2025, 6, 14, 12, 0, tzinfo=timezone.utc)

        # Should receive - enabled channel, above threshold
        assert (
            preferences.should_receive_notification(
                NotificationChannel.EMAIL, "incident", "high", business_time
            )
            is True
        )

        # Should not receive - disabled channel
        assert (
            preferences.should_receive_notification(
                NotificationChannel.SMS, "incident", "high", business_time
            )
            is False
        )

        # Should not receive - excluded type
        assert (
            preferences.should_receive_notification(
                NotificationChannel.EMAIL, "maintenance", "high", business_time
            )
            is False
        )

        # Should not receive - below severity threshold
        assert (
            preferences.should_receive_notification(
                NotificationChannel.EMAIL, "incident", "low", business_time
            )
            is False
        )

        # Test time during quiet hours
        quiet_time = datetime(2025, 6, 14, 2, 0, tzinfo=timezone.utc)

        # Should not receive during quiet hours (non-critical)
        assert (
            preferences.should_receive_notification(
                NotificationChannel.EMAIL, "incident", "high", quiet_time
            )
            is False
        )

        # Should receive during quiet hours (critical overrides)
        assert (
            preferences.should_receive_notification(
                NotificationChannel.EMAIL, "incident", "critical", quiet_time
            )
            is True
        )

    def test_notification_preferences_severity_levels(self) -> None:
        """Test severity level thresholds."""
        # Test each threshold level
        thresholds = ["low", "medium", "high", "critical"]

        for threshold in thresholds:
            preferences = NotificationPreferences(
                recipient_id=f"severity_{threshold}", severity_threshold=threshold
            )

            business_time = datetime(2025, 6, 14, 12, 0, tzinfo=timezone.utc)

            # Test all severity levels against this threshold
            severities = ["low", "medium", "high", "critical"]
            for severity in severities:
                should_receive = preferences.should_receive_notification(
                    NotificationChannel.EMAIL, "test", severity, business_time
                )

                threshold_index = severities.index(threshold)
                severity_index = severities.index(severity)

                if severity_index >= threshold_index:
                    assert (
                        should_receive is True
                    ), f"Should receive {severity} with threshold {threshold}"
                else:
                    assert (
                        should_receive is False
                    ), f"Should not receive {severity} with threshold {threshold}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

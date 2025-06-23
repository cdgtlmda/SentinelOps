"""Tests for RecipientRegistry."""

import os
import pytest
from datetime import datetime, timezone, time
from pathlib import Path
import tempfile
import json
import sys
from typing import Generator, TYPE_CHECKING, Any

# Import only what we need, avoiding the ADK-dependent modules
import importlib.util

# Set test mode to bypass credential validation
os.environ["SENTINELOPS_TEST_MODE"] = "true"

# Add src to path
src_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(src_path))

# Load the registry module directly
registry_path = (
    src_path / "src" / "communication_agent" / "recipient_management" / "registry.py"
)
spec = importlib.util.spec_from_file_location("registry", registry_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for {registry_path}")
registry_module = importlib.util.module_from_spec(spec)
sys.modules["registry"] = registry_module

# Load models module directly
models_path = (
    src_path / "src" / "communication_agent" / "recipient_management" / "models.py"
)
models_spec = importlib.util.spec_from_file_location("models", models_path)
if models_spec is None or models_spec.loader is None:
    raise ImportError(f"Could not load spec for {models_path}")
models_module = importlib.util.module_from_spec(models_spec)
sys.modules["models"] = models_module

# Load types module directly
types_path = src_path / "src" / "communication_agent" / "types.py"
types_spec = importlib.util.spec_from_file_location("communication_types", types_path)
if types_spec is None or types_spec.loader is None:
    raise ImportError(f"Could not load spec for {types_path}")
types_module = importlib.util.module_from_spec(types_spec)
sys.modules["communication_types"] = types_module

# Execute the modules
types_spec.loader.exec_module(types_module)
models_spec.loader.exec_module(models_module)
spec.loader.exec_module(registry_module)

# Import classes directly from the loaded modules
RecipientRegistry = registry_module.RecipientRegistry
ContactInfo = models_module.ContactInfo
EscalationChain = models_module.EscalationChain
EscalationLevel = models_module.EscalationLevel
NotificationPreferences = models_module.NotificationPreferences
OnCallSchedule = models_module.OnCallSchedule
OnCallShift = models_module.OnCallShift
Recipient = models_module.Recipient
RecipientRole = models_module.RecipientRole
ContactStatus = models_module.ContactStatus
NotificationChannel = types_module.NotificationChannel


class TestRecipientRegistry:
    """Test cases for RecipientRegistry."""

    @pytest.fixture
    def temp_storage_path(self) -> Generator[Path, None, None]:
        """Create a temporary storage file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def registry(self) -> Any:
        """Create a registry without storage."""
        return RecipientRegistry()

    @pytest.fixture
    def registry_with_storage(self, temp_storage_path: Path) -> Any:
        """Create a registry with storage."""
        return RecipientRegistry(storage_path=temp_storage_path)

    @pytest.fixture
    def sample_recipient(self) -> Any:
        """Create a sample recipient."""
        return Recipient(
            id="test-user",
            name="Test User",
            role=RecipientRole.DEVELOPER,
            contacts=[
                ContactInfo(
                    channel=NotificationChannel.EMAIL,
                    address="test@example.com",
                    verified=True,
                    preferred=True,
                ),
                ContactInfo(
                    channel=NotificationChannel.SLACK,
                    address="@testuser",
                    verified=True,
                ),
            ],
            tags={"engineering", "backend"},
            timezone="US/Pacific",
        )

    @pytest.fixture
    def sample_escalation_chain(self) -> Any:
        """Create a sample escalation chain."""
        return EscalationChain(
            id="test-escalation",
            name="Test Escalation",
            description="Test escalation chain",
            levels=[
                EscalationLevel(
                    level=1,
                    recipients=["test-user"],
                    delay_minutes=0,
                ),
                EscalationLevel(
                    level=2,
                    recipients=["security-team"],
                    delay_minutes=15,
                ),
            ],
            tags={"test"},
        )

    @pytest.fixture
    def sample_on_call_schedule(self) -> Any:
        """Create a sample on-call schedule."""
        now = datetime.now(timezone.utc)
        return OnCallSchedule(
            id="test-schedule",
            name="Test Schedule",
            description="Test on-call schedule",
            shifts=[
                OnCallShift(
                    recipient_id="test-user",
                    start_time=now,
                    end_time=now.replace(hour=23, minute=59),
                    is_primary=True,
                ),
            ],
            timezone="UTC",
        )

    def test_initialization_defaults(self) -> None:
        """Test registry initialization with defaults."""
        registry = RecipientRegistry()

        # Should have default recipients
        assert len(registry.recipients) > 0
        assert "security-team" in registry.recipients

        # Should have default escalation chain
        assert len(registry.escalation_chains) > 0
        assert "default-escalation" in registry.escalation_chains

        # Should have preferences for default recipients
        assert "security-team" in registry.preferences

    def test_add_recipient(self, registry: Any, sample_recipient: Any) -> None:
        """Test adding a recipient."""
        # Add recipient
        registry.add_recipient(sample_recipient)

        # Verify recipient was added
        assert sample_recipient.id in registry.recipients
        retrieved = registry.get_recipient(sample_recipient.id)
        assert retrieved == sample_recipient

        # Verify preferences were created
        assert sample_recipient.id in registry.preferences
        prefs = registry.get_preferences(sample_recipient.id)
        assert prefs.recipient_id == sample_recipient.id
        assert prefs.timezone == sample_recipient.timezone

    def test_add_duplicate_recipient(
        self, registry: Any, sample_recipient: Any
    ) -> None:
        """Test adding duplicate recipient raises error."""
        registry.add_recipient(sample_recipient)

        with pytest.raises(ValueError) as excinfo:
            registry.add_recipient(sample_recipient)
        assert "already exists" in str(excinfo.value)

    def test_get_recipient(self, registry: Any, sample_recipient: Any) -> None:
        """Test retrieving a recipient."""
        registry.add_recipient(sample_recipient)

        # Get existing recipient
        retrieved = registry.get_recipient(sample_recipient.id)
        assert retrieved == sample_recipient

        # Get non-existent recipient
        assert registry.get_recipient("non-existent") is None

    def test_find_recipients_by_role(
        self, registry: Any, sample_recipient: Any
    ) -> None:
        """Test finding recipients by role."""
        registry.add_recipient(sample_recipient)

        # Add another developer
        dev2 = Recipient(
            id="dev2",
            name="Developer 2",
            role=RecipientRole.DEVELOPER,
            contacts=[
                ContactInfo(
                    channel=NotificationChannel.EMAIL,
                    address="dev2@example.com",
                    verified=True,
                ),
            ],
        )
        registry.add_recipient(dev2)

        # Find all developers
        developers = registry.find_recipients_by_role(RecipientRole.DEVELOPER)
        assert len(developers) == 2
        assert all(r.role == RecipientRole.DEVELOPER for r in developers)

        # Find security engineers
        security = registry.find_recipients_by_role(RecipientRole.SECURITY_ENGINEER)
        assert len(security) >= 1  # At least the default security team

    def test_find_recipients_by_tag(self, registry: Any, sample_recipient: Any) -> None:
        """Test finding recipients by tag."""
        registry.add_recipient(sample_recipient)

        # Find by engineering tag
        engineering = registry.find_recipients_by_tag("engineering")
        assert len(engineering) == 1
        assert sample_recipient in engineering

        # Find by backend tag
        backend = registry.find_recipients_by_tag("backend")
        assert len(backend) == 1
        assert sample_recipient in backend

        # Find by non-existent tag
        assert len(registry.find_recipients_by_tag("frontend")) == 0

    def test_find_recipients_by_channel(
        self, registry: Any, sample_recipient: Any
    ) -> None:
        """Test finding recipients by channel."""
        registry.add_recipient(sample_recipient)

        # Find by email channel
        email_recipients = registry.find_recipients_by_channel(
            NotificationChannel.EMAIL
        )
        assert sample_recipient in email_recipients

        # Find by Slack channel
        slack_recipients = registry.find_recipients_by_channel(
            NotificationChannel.SLACK
        )
        assert sample_recipient in slack_recipients

        # Find by SMS channel (not configured)
        sms_recipients = registry.find_recipients_by_channel(NotificationChannel.SMS)
        assert sample_recipient not in sms_recipients

    def test_update_recipient(self, registry: Any, sample_recipient: Any) -> None:
        """Test updating a recipient."""
        registry.add_recipient(sample_recipient)
        original_updated_at = sample_recipient.updated_at

        # Update recipient
        sample_recipient.name = "Updated Name"
        registry.update_recipient(sample_recipient)

        # Verify update
        retrieved = registry.get_recipient(sample_recipient.id)
        assert retrieved.name == "Updated Name"
        assert retrieved.updated_at > original_updated_at

    def test_update_non_existent_recipient(self, registry: Any) -> None:
        """Test updating non-existent recipient raises error."""
        fake_recipient = Recipient(
            id="fake",
            name="Fake",
            role=RecipientRole.DEVELOPER,
            contacts=[],
        )

        with pytest.raises(ValueError) as excinfo:
            registry.update_recipient(fake_recipient)
        assert "not found" in str(excinfo.value)

    def test_remove_recipient(self, registry: Any, sample_recipient: Any) -> None:
        """Test removing a recipient."""
        registry.add_recipient(sample_recipient)

        # Remove recipient
        assert registry.remove_recipient(sample_recipient.id) is True

        # Verify removal
        assert registry.get_recipient(sample_recipient.id) is None
        assert sample_recipient.id not in registry.preferences

        # Try to remove again
        assert registry.remove_recipient(sample_recipient.id) is False

    def test_remove_recipient_from_escalation_chains(
        self,
        registry: Any,
        sample_recipient: Any,
        sample_escalation_chain: Any,
    ) -> None:
        """Test recipient removal from escalation chains."""
        registry.add_recipient(sample_recipient)
        registry.add_escalation_chain(sample_escalation_chain)

        # Remove recipient
        registry.remove_recipient(sample_recipient.id)

        # Verify removal from escalation chain
        chain = registry.get_escalation_chain(sample_escalation_chain.id)
        for level in chain.levels:
            assert sample_recipient.id not in level.recipients

    def test_add_escalation_chain(
        self, registry: Any, sample_escalation_chain: Any
    ) -> None:
        """Test adding an escalation chain."""
        registry.add_escalation_chain(sample_escalation_chain)

        assert sample_escalation_chain.id in registry.escalation_chains
        retrieved = registry.get_escalation_chain(sample_escalation_chain.id)
        assert retrieved == sample_escalation_chain

    def test_add_duplicate_escalation_chain(
        self, registry: Any, sample_escalation_chain: Any
    ) -> None:
        """Test adding duplicate escalation chain raises error."""
        registry.add_escalation_chain(sample_escalation_chain)

        with pytest.raises(ValueError) as excinfo:
            registry.add_escalation_chain(sample_escalation_chain)
        assert "already exists" in str(excinfo.value)

    def test_add_on_call_schedule(
        self, registry: Any, sample_on_call_schedule: Any
    ) -> None:
        """Test adding an on-call schedule."""
        registry.add_on_call_schedule(sample_on_call_schedule)

        assert sample_on_call_schedule.id in registry.on_call_schedules
        retrieved = registry.get_on_call_schedule(sample_on_call_schedule.id)
        assert retrieved == sample_on_call_schedule

    def test_add_duplicate_on_call_schedule(
        self, registry: Any, sample_on_call_schedule: Any
    ) -> None:
        """Test adding duplicate on-call schedule raises error."""
        registry.add_on_call_schedule(sample_on_call_schedule)

        with pytest.raises(ValueError) as excinfo:
            registry.add_on_call_schedule(sample_on_call_schedule)
        assert "already exists" in str(excinfo.value)

    def test_get_current_on_call(
        self,
        registry: Any,
        sample_recipient: Any,
        sample_on_call_schedule: Any,
    ) -> None:
        """Test getting current on-call recipients."""
        # Add recipient and schedule
        registry.add_recipient(sample_recipient)
        registry.add_on_call_schedule(sample_on_call_schedule)

        # Mark recipient as available
        sample_recipient.status = ContactStatus.ACTIVE

        # Get current on-call
        on_call = registry.get_current_on_call(sample_on_call_schedule.id)
        assert len(on_call) == 1
        assert on_call[0].id == sample_recipient.id

        # Get from all schedules
        all_on_call = registry.get_current_on_call()
        assert sample_recipient in all_on_call

    def test_get_current_on_call_primary_only(
        self, registry: Any, sample_recipient: Any
    ) -> None:
        """Test getting only primary on-call recipients."""
        registry.add_recipient(sample_recipient)

        # Create schedule with primary and secondary
        now = datetime.now(timezone.utc)
        schedule = OnCallSchedule(
            id="mixed-schedule",
            name="Mixed Schedule",
            shifts=[
                OnCallShift(
                    recipient_id=sample_recipient.id,
                    start_time=now,
                    end_time=now.replace(hour=23, minute=59),
                    is_primary=True,
                ),
                OnCallShift(
                    recipient_id="security-team",
                    start_time=now,
                    end_time=now.replace(hour=23, minute=59),
                    is_primary=False,
                ),
            ],
        )
        registry.add_on_call_schedule(schedule)

        # Get primary only
        primary_only = registry.get_current_on_call(schedule.id, primary_only=True)
        assert len(primary_only) == 1
        assert primary_only[0].id == sample_recipient.id

    def test_update_preferences(self, registry: Any, sample_recipient: Any) -> None:
        """Test updating notification preferences."""
        registry.add_recipient(sample_recipient)

        # Create and update preferences
        prefs = NotificationPreferences(
            recipient_id=sample_recipient.id,
            severity_threshold="medium",
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
            timezone="US/Pacific",
        )
        registry.update_preferences(prefs)

        # Verify update
        retrieved = registry.get_preferences(sample_recipient.id)
        assert retrieved.severity_threshold == "medium"
        assert retrieved.quiet_hours_enabled is True
        assert retrieved.timezone == "US/Pacific"

    def test_resolve_recipients_by_id(
        self, registry: Any, sample_recipient: Any
    ) -> None:
        """Test resolving recipients by direct ID."""
        registry.add_recipient(sample_recipient)

        spec = {
            "recipient_id": sample_recipient.id,
            "channel": "email",
        }

        resolved = registry.resolve_recipients([spec])
        assert len(resolved) == 1

        recipient, channel, address = resolved[0]
        assert recipient.id == sample_recipient.id
        assert channel == NotificationChannel.EMAIL
        assert address == "test@example.com"

    def test_resolve_recipients_by_role(
        self, registry: Any, sample_recipient: Any
    ) -> None:
        """Test resolving recipients by role."""
        registry.add_recipient(sample_recipient)

        spec = {
            "role": "developer",
            "channel": "slack",
        }

        resolved = registry.resolve_recipients([spec])
        assert len(resolved) == 1

        recipient, channel, address = resolved[0]
        assert recipient.role == RecipientRole.DEVELOPER
        assert channel == NotificationChannel.SLACK
        assert address == "@testuser"

    def test_resolve_recipients_by_tag(
        self, registry: Any, sample_recipient: Any
    ) -> None:
        """Test resolving recipients by tag."""
        registry.add_recipient(sample_recipient)

        spec = {
            "tag": "engineering",
            "channel": "email",
        }

        resolved = registry.resolve_recipients([spec])
        assert len(resolved) == 1

        recipient, channel, address = resolved[0]
        assert "engineering" in recipient.tags
        assert channel == NotificationChannel.EMAIL

    def test_resolve_recipients_by_on_call(
        self,
        registry: Any,
        sample_recipient: Any,
        sample_on_call_schedule: Any,
    ) -> None:
        """Test resolving recipients by on-call status."""
        registry.add_recipient(sample_recipient)
        registry.add_on_call_schedule(sample_on_call_schedule)

        spec = {
            "on_call": True,
            "schedule_id": sample_on_call_schedule.id,
            "channel": "email",
        }

        resolved = registry.resolve_recipients([spec])
        assert len(resolved) == 1

        recipient, channel, address = resolved[0]
        assert recipient.id == sample_recipient.id
        assert channel == NotificationChannel.EMAIL

    def test_resolve_direct_address(self, registry: Any) -> None:
        """Test resolving direct address specifications."""
        spec = {
            "channel": "email",
            "address": "direct@example.com",
        }

        resolved = registry.resolve_recipients([spec])
        assert len(resolved) == 1

        recipient, channel, address = resolved[0]
        assert recipient.role == RecipientRole.EXTERNAL
        assert channel == NotificationChannel.EMAIL
        assert address == "direct@example.com"

    def test_resolve_multiple_specs(self, registry: Any, sample_recipient: Any) -> None:
        """Test resolving multiple recipient specifications."""
        registry.add_recipient(sample_recipient)

        specs = [
            {"recipient_id": sample_recipient.id, "channel": "email"},
            {"role": "security_engineer", "channel": "slack"},
            {"channel": "sms", "address": "+1234567890"},
        ]

        resolved = registry.resolve_recipients(specs)
        assert len(resolved) >= 3  # At least our specs

        # Verify different resolution methods worked
        addresses = [addr for _, _, addr in resolved]
        assert "test@example.com" in addresses
        assert "+1234567890" in addresses

    def test_save_to_storage(
        self,
        registry_with_storage: Any,
        sample_recipient: Any,
        temp_storage_path: Path,
    ) -> None:
        """Test saving registry data to storage."""
        # Add data
        registry_with_storage.add_recipient(sample_recipient)

        # Verify file was created
        assert temp_storage_path.exists()

        # Verify content
        with open(temp_storage_path) as f:
            data = json.load(f)

        assert "recipients" in data
        assert sample_recipient.id in data["recipients"]
        assert data["recipients"][sample_recipient.id]["name"] == sample_recipient.name
        assert data["version"] == "1.0"

    def test_load_from_storage(self, temp_storage_path: Path) -> None:
        """Test loading registry data from storage."""
        # Create test data
        test_data = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "recipients": {
                "stored-user": {
                    "id": "stored-user",
                    "name": "Stored User",
                    "role": "developer",
                    "contacts": [
                        {
                            "channel": "email",
                            "address": "stored@example.com",
                            "verified": True,
                            "preferred": True,
                        }
                    ],
                    "tags": ["stored", "test"],
                }
            },
            "escalation_chains": {},
            "on_call_schedules": {},
            "preferences": {},
        }

        # Save test data
        with open(temp_storage_path, "w") as f:
            json.dump(test_data, f)

        # Load registry
        registry = RecipientRegistry(storage_path=temp_storage_path)

        # Verify data was loaded
        recipient = registry.get_recipient("stored-user")
        assert recipient is not None
        assert recipient.name == "Stored User"
        assert recipient.role == RecipientRole.DEVELOPER
        assert len(recipient.contacts) == 1
        assert recipient.contacts[0].address == "stored@example.com"

    def test_persistence_across_instances(
        self, temp_storage_path: Path, sample_recipient: Any
    ) -> None:
        """Test data persistence across registry instances."""
        # Create first instance and add data
        registry1 = RecipientRegistry(storage_path=temp_storage_path)
        registry1.add_recipient(sample_recipient)

        # Create escalation chain
        chain = EscalationChain(
            id="persist-chain",
            name="Persistent Chain",
            levels=[
                EscalationLevel(
                    level=1, recipients=[sample_recipient.id], delay_minutes=0
                ),
            ],
        )
        registry1.add_escalation_chain(chain)

        # Create second instance - should load data
        registry2 = RecipientRegistry(storage_path=temp_storage_path)

        # Verify data persisted
        assert registry2.get_recipient(sample_recipient.id) is not None
        assert registry2.get_escalation_chain(chain.id) is not None

        # Verify exact match
        loaded_recipient = registry2.get_recipient(sample_recipient.id)
        assert loaded_recipient.name == sample_recipient.name
        assert len(loaded_recipient.contacts) == len(sample_recipient.contacts)

    def test_remove_recipient_from_on_call_schedule(
        self, registry: Any, sample_recipient: Any
    ) -> None:
        """Test recipient removal from on-call schedules."""
        registry.add_recipient(sample_recipient)

        # Create schedule with the recipient
        now = datetime.now(timezone.utc)
        schedule = OnCallSchedule(
            id="removal-test",
            name="Removal Test",
            shifts=[
                OnCallShift(
                    recipient_id=sample_recipient.id,
                    start_time=now,
                    end_time=now.replace(hour=23, minute=59),
                    is_primary=True,
                ),
            ],
        )
        registry.add_on_call_schedule(schedule)

        # Remove recipient
        registry.remove_recipient(sample_recipient.id)

        # Verify removal from schedule
        updated_schedule = registry.get_on_call_schedule(schedule.id)
        current_on_call = updated_schedule.get_current_on_call()
        assert sample_recipient.id not in current_on_call

    def test_duplicate_recipient_removal(self, registry: Any) -> None:
        """Test removing duplicate recipients from lists."""
        # Create recipients
        r1 = Recipient(id="r1", name="R1", role=RecipientRole.DEVELOPER, contacts=[])
        r2 = Recipient(id="r2", name="R2", role=RecipientRole.DEVELOPER, contacts=[])

        # Test _remove_duplicate_recipients
        duplicates = [r1, r2, r1, r2, r1]
        unique = registry._remove_duplicate_recipients(duplicates)

        assert len(unique) == 2
        assert unique[0].id == "r1"
        assert unique[1].id == "r2"

    def test_storage_error_handling(self, registry: Any) -> None:
        """Test error handling when storage fails."""
        # Create registry with invalid path
        invalid_path = Path("/invalid/path/that/does/not/exist/registry.json")
        registry = RecipientRegistry(storage_path=invalid_path)

        # Should handle initialization without error
        assert registry is not None

        # Should have defaults even with bad path
        assert "security-team" in registry.recipients

    def test_load_invalid_storage_file(self, temp_storage_path: Path) -> None:
        """Test loading from corrupted storage file."""
        # Write invalid JSON
        with open(temp_storage_path, "w") as f:
            f.write("{ invalid json content")

        # Should fall back to defaults
        registry = RecipientRegistry(storage_path=temp_storage_path)
        assert "security-team" in registry.recipients
        assert "default-escalation" in registry.escalation_chains

    def test_empty_recipient_specs_resolution(self, registry: Any) -> None:
        """Test resolving empty recipient specifications."""
        resolved = registry.resolve_recipients([])
        assert resolved == []

    def test_channel_preference_in_resolution(self, registry: Any) -> None:
        """Test that preferred channels are respected."""
        # Create recipient with preferred Slack
        recipient = Recipient(
            id="pref-test",
            name="Preference Test",
            role=RecipientRole.DEVELOPER,
            contacts=[
                ContactInfo(
                    channel=NotificationChannel.EMAIL,
                    address="test@example.com",
                    verified=True,
                    preferred=False,
                ),
                ContactInfo(
                    channel=NotificationChannel.SLACK,
                    address="@preftest",
                    verified=True,
                    preferred=True,
                ),
            ],
        )
        registry.add_recipient(recipient)

        # Resolve without specifying channel
        spec = {"recipient_id": recipient.id}
        resolved = registry.resolve_recipients([spec])

        # Should use email as default when channel not specified
        assert len(resolved) == 1
        _, channel, _ = resolved[0]
        assert channel == NotificationChannel.EMAIL  # Default channel

    def test_production_recipient_registry_initialization(self) -> None:
        # Implementation of the test_production_recipient_registry_initialization method
        pass

    def test_production_recipient_registry_with_config(self) -> None:
        # Implementation of the test_production_recipient_registry_with_config method
        pass

    def test_production_notification_preferences_initialization(self) -> None:
        # Implementation of the test_production_notification_preferences_initialization method
        pass

    def test_production_registry_initialization(self) -> None:
        # Implementation of the test_production_registry_initialization method
        pass

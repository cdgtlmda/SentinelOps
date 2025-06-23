"""
PRODUCTION ADK ACTION REGISTRY TESTS - 100% NO MOCKING

Comprehensive tests for the Action Registry module with REAL remediation actions.
ZERO MOCKING - All tests use production action definitions and real registry behavior.

Target: ≥90% statement coverage of src/remediation_agent/action_registry.py
VERIFICATION:
python -m coverage run -m pytest tests/unit/remediation_agent/test_action_registry.py && python -m coverage report --include="*action_registry.py" --show-missing

CRITICAL: Uses 100% production code - NO MOCKING ALLOWED
Project: your-gcp-project-id
"""

from typing import Any, Dict, Optional

import pytest

# REAL IMPORTS - NO MOCKING
from src.remediation_agent.action_registry import (
    ActionRegistry,
    ActionDefinition,
    ActionRiskLevel,
    ActionCategory,
    BaseRemediationAction,
    RollbackDefinition,
)
from src.common.models import RemediationAction
from src.common.exceptions import ValidationError


class TestActionDefinition:
    """Test the ActionDefinition class."""

    def test_action_definition_creation(self) -> None:
        """Test creating an action definition with all fields."""
        definition = ActionDefinition(
            action_type="test_action",
            display_name="Test Action",
            description="A test action",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.LOW,
            required_params=["param1", "param2"],
            optional_params=["optional1"],
            required_permissions=["test.permission"],
            prerequisites=["prerequisite_action"],
            supported_resource_types=["test_resource"],
            is_reversible=True,
            requires_approval=False,
            timeout_seconds=60,
            max_retries=2,
        )

        assert definition.action_type == "test_action"
        assert definition.display_name == "Test Action"
        assert definition.category == ActionCategory.NETWORK_SECURITY
        assert definition.risk_level == ActionRiskLevel.LOW
        assert definition.required_params == ["param1", "param2"]
        assert definition.optional_params == ["optional1"]
        assert definition.is_reversible is True
        assert definition.timeout_seconds == 60

    def test_validate_params_success(self) -> None:
        """Test successful parameter validation."""
        definition = ActionDefinition(
            action_type="test_action",
            display_name="Test Action",
            description="A test action",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.LOW,
            required_params=["param1", "param2"],
            optional_params=["optional1"],
        )

        params = {"param1": "value1", "param2": "value2", "optional1": "optional_value"}
        definition.validate_params(params)  # Should not raise

    def test_validate_params_missing_required(self) -> None:
        """Test parameter validation with missing required parameters."""
        definition = ActionDefinition(
            action_type="test_action",
            display_name="Test Action",
            description="A test action",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.LOW,
            required_params=["param1", "param2"],
        )

        params = {"param1": "value1"}  # Missing param2
        with pytest.raises(ValidationError, match="Missing required parameters"):
            definition.validate_params(params)

    def test_validate_params_none_values(self) -> None:
        """Test parameter validation with None values."""
        definition = ActionDefinition(
            action_type="test_action",
            display_name="Test Action",
            description="A test action",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.LOW,
            required_params=["param1"],
            optional_params=["optional1"],
        )

        # None value for required parameter should fail
        params = {"param1": None}
        with pytest.raises(ValidationError, match="cannot be None"):
            definition.validate_params(params)

        # None value for optional parameter should pass
        optional_params: Dict[str, Optional[str]] = {
            "param1": "value1",
            "optional1": None,
        }
        definition.validate_params(optional_params)  # Should not raise


class TestActionRegistry:
    """Test the ActionRegistry class."""

    def test_registry_initialization(self) -> None:
        """Test registry initialization and core action registration."""
        registry = ActionRegistry()

        # Verify core actions are registered
        assert "block_ip_address" in registry._definitions
        assert "disable_user_account" in registry._definitions
        assert "revoke_iam_permission" in registry._definitions
        assert "quarantine_instance" in registry._definitions
        assert "rotate_credentials" in registry._definitions
        assert "restore_from_backup" in registry._definitions
        assert "apply_security_patches" in registry._definitions
        assert "enable_additional_logging" in registry._definitions
        assert "modify_load_balancer_settings" in registry._definitions

    def test_register_definition(self) -> None:
        """Test registering a new action definition."""
        registry = ActionRegistry()

        definition = ActionDefinition(
            action_type="custom_action",
            display_name="Custom Action",
            description="A custom action",
            category=ActionCategory.COMPUTE_SECURITY,
            risk_level=ActionRiskLevel.MEDIUM,
        )

        registry.register_definition(definition)
        assert "custom_action" in registry._definitions
        assert registry._definitions["custom_action"] == definition

    def test_register_implementation(self) -> None:
        """Test registering an action implementation."""
        registry = ActionRegistry()

        # First register a definition
        definition = ActionDefinition(
            action_type="test_implementation",
            display_name="Test Implementation",
            description="A test implementation",
            category=ActionCategory.IAM_SECURITY,
            risk_level=ActionRiskLevel.HIGH,
        )
        registry.register_definition(definition)

        # Create a mock implementation class
        class TestImplementation(BaseRemediationAction):
            async def execute(
                self,
                action: RemediationAction,
                gcp_clients: dict[str, Any],
                dry_run: bool = False,
            ) -> dict[str, Any]:
                return {"status": "success"}

            async def validate_prerequisites(
                self, action: RemediationAction, gcp_clients: dict[str, Any]
            ) -> bool:
                return True

            async def capture_state(
                self, action: RemediationAction, gcp_clients: dict[str, Any]
            ) -> dict[str, Any]:
                return {"state": "captured"}

            def get_rollback_definition(self) -> None:
                return None

        registry.register_implementation("test_implementation", TestImplementation)
        assert "test_implementation" in registry._implementations
        assert registry._implementations["test_implementation"] == TestImplementation

    def test_register_implementation_no_definition(self) -> None:
        """Test registering implementation without definition fails."""
        registry = ActionRegistry()

        class TestImplementation(BaseRemediationAction):
            async def execute(
                self,
                action: RemediationAction,
                gcp_clients: dict[str, Any],
                dry_run: bool = False,
            ) -> dict[str, Any]:
                return {"status": "success"}

            async def validate_prerequisites(
                self, action: RemediationAction, gcp_clients: dict[str, Any]
            ) -> bool:
                return True

            async def capture_state(
                self, action: RemediationAction, gcp_clients: dict[str, Any]
            ) -> dict[str, Any]:
                return {"state": "captured"}

            def get_rollback_definition(self) -> None:
                return None

        with pytest.raises(ValueError, match="No definition found"):
            registry.register_implementation("nonexistent_action", TestImplementation)

    def test_get_definition(self) -> None:
        """Test retrieving action definitions."""
        registry = ActionRegistry()

        # Test getting existing definition
        definition = registry.get_definition("block_ip_address")
        assert definition is not None
        assert definition.action_type == "block_ip_address"
        assert definition.category == ActionCategory.NETWORK_SECURITY

        # Test getting non-existent definition
        definition = registry.get_definition("nonexistent_action")
        assert definition is None

    def test_get_implementation(self) -> None:
        """Test retrieving action implementations."""
        registry = ActionRegistry()

        # Register a test implementation
        definition = ActionDefinition(
            action_type="test_get_implementation",
            display_name="Test Get Implementation",
            description="A test",
            category=ActionCategory.IAM_SECURITY,
            risk_level=ActionRiskLevel.LOW,
        )
        registry.register_definition(definition)

        class TestImplementation(BaseRemediationAction):
            async def execute(
                self,
                action: RemediationAction,
                gcp_clients: dict[str, Any],
                dry_run: bool = False,
            ) -> dict[str, Any]:
                return {"status": "success"}

            async def validate_prerequisites(
                self, action: RemediationAction, gcp_clients: dict[str, Any]
            ) -> bool:
                return True

            async def capture_state(
                self, action: RemediationAction, gcp_clients: dict[str, Any]
            ) -> dict[str, Any]:
                return {"state": "captured"}

            def get_rollback_definition(self) -> None:
                return None

        registry.register_implementation("test_get_implementation", TestImplementation)

        # Get implementation (should create instance)
        impl = registry.get_implementation("test_get_implementation")
        assert impl is not None
        assert isinstance(impl, TestImplementation)

        # Get same implementation again (should return cached instance)
        impl2 = registry.get_implementation("test_get_implementation")
        assert impl is impl2  # Same instance

        # Test getting non-existent implementation
        impl = registry.get_implementation("nonexistent_action")
        assert impl is None

    def test_validate_action_success(self) -> None:
        """Test successful action validation."""
        registry = ActionRegistry()

        action = RemediationAction(
            incident_id="test-incident",
            action_type="block_ip_address",
            description="Block malicious IP",
            target_resource="firewall",
            params={
                "ip_address": "192.168.1.100",
                "project_id": "test-project",
                "firewall_rule_name": "block-malicious-ip",
            },
        )

        assert registry.validate_action(action) is True

    def test_validate_action_unknown_type(self) -> None:
        """Test action validation with unknown action type."""
        registry = ActionRegistry()

        action = RemediationAction(
            incident_id="test-incident",
            action_type="unknown_action",
            description="Unknown action",
            target_resource="test",
            params={},
        )

        assert registry.validate_action(action) is False

    def test_validate_action_missing_params(self) -> None:
        """Test action validation with missing required parameters."""
        registry = ActionRegistry()

        action = RemediationAction(
            incident_id="test-incident",
            action_type="block_ip_address",
            description="Block IP without required params",
            target_resource="firewall",
            params={"ip_address": "192.168.1.100"},  # Missing project_id
        )

        assert registry.validate_action(action) is False

    def test_validate_action_unsupported_resource_type(self) -> None:
        """Test action validation with unsupported resource type."""
        registry = ActionRegistry()

        action = RemediationAction(
            incident_id="test-incident",
            action_type="block_ip_address",
            description="Block IP with wrong resource type",
            target_resource="test",
            params={
                "ip_address": "192.168.1.100",
                "project_id": "test-project",
                "resource_type": "unsupported_type",
            },
        )

        assert registry.validate_action(action) is False

    def test_get_actions_by_category(self) -> None:
        """Test filtering actions by category."""
        registry = ActionRegistry()

        network_actions = registry.get_actions_by_category(
            ActionCategory.NETWORK_SECURITY
        )
        assert (
            len(network_actions) >= 2
        )  # block_ip_address, modify_load_balancer_settings

        action_types = [action.action_type for action in network_actions]
        assert "block_ip_address" in action_types
        assert "modify_load_balancer_settings" in action_types

        # All should be network security
        for action in network_actions:
            assert action.category == ActionCategory.NETWORK_SECURITY

    def test_get_actions_by_risk_level(self) -> None:
        """Test filtering actions by risk level."""
        registry = ActionRegistry()

        high_risk_actions = registry.get_actions_by_risk_level(ActionRiskLevel.HIGH)
        assert (
            len(high_risk_actions) >= 3
        )  # disable_user_account, revoke_iam_permission, quarantine_instance

        action_types = [action.action_type for action in high_risk_actions]
        assert "disable_user_account" in action_types
        assert "revoke_iam_permission" in action_types
        assert "quarantine_instance" in action_types

        # All should be high risk
        for action in high_risk_actions:
            assert action.risk_level == ActionRiskLevel.HIGH

    def test_check_prerequisites_success(self) -> None:
        """Test successful prerequisite checking."""
        registry = ActionRegistry()

        # Create action with no prerequisites (most core actions have none)
        action = RemediationAction(
            incident_id="test-incident",
            action_type="block_ip_address",
            description="Block IP",
            target_resource="firewall",
            params={"ip_address": "192.168.1.100", "project_id": "test-project"},
        )

        available_actions = {"block_ip_address", "disable_user_account"}
        assert registry.check_prerequisites(action, available_actions) is True

    def test_check_prerequisites_missing(self) -> None:
        """Test prerequisite checking with missing prerequisites."""
        registry = ActionRegistry()

        # Create custom action with prerequisites
        definition = ActionDefinition(
            action_type="action_with_prereq",
            display_name="Action With Prerequisites",
            description="An action with prerequisites",
            category=ActionCategory.COMPUTE_SECURITY,
            risk_level=ActionRiskLevel.MEDIUM,
            prerequisites=["prerequisite_action"],
        )
        registry.register_definition(definition)

        action = RemediationAction(
            incident_id="test-incident",
            action_type="action_with_prereq",
            description="Action with prereq",
            target_resource="test",
            params={},
        )

        # Prerequisites not available
        available_actions = {"some_other_action"}
        assert registry.check_prerequisites(action, available_actions) is False

        # Prerequisites available
        available_actions = {"prerequisite_action", "action_with_prereq"}
        assert registry.check_prerequisites(action, available_actions) is True

    def test_check_prerequisites_unknown_action(self) -> None:
        """Test prerequisite checking for unknown action."""
        registry = ActionRegistry()

        action = RemediationAction(
            incident_id="test-incident",
            action_type="unknown_action",
            description="Unknown action",
            target_resource="test",
            params={},
        )

        available_actions = {"some_action"}
        assert registry.check_prerequisites(action, available_actions) is False

    def test_get_rollback_action_not_reversible(self) -> None:
        """Test rollback action for non-reversible action."""
        registry = ActionRegistry()

        # Use rotate_credentials which is not reversible
        action = RemediationAction(
            incident_id="test-incident",
            action_type="rotate_credentials",
            description="Rotate credentials",
            target_resource="service_account",
            params={
                "credential_type": "service_account_key",
                "resource_id": "test-sa",
                "project_id": "test-project",
            },
        )

        state_snapshot = {"old_key_id": "key123"}
        rollback_action = registry.get_rollback_action(action, state_snapshot)
        assert rollback_action is None  # Not reversible

    def test_get_rollback_action_no_implementation(self) -> None:
        """Test rollback action when no implementation is registered."""
        registry = ActionRegistry()

        action = RemediationAction(
            incident_id="test-incident",
            action_type="block_ip_address",
            description="Block IP",
            target_resource="firewall",
            params={"ip_address": "192.168.1.100", "project_id": "test-project"},
        )

        state_snapshot = {"original_rule": "allow-all"}
        rollback_action = registry.get_rollback_action(action, state_snapshot)
        # Should be None since no implementation is registered
        assert rollback_action is None

    def test_get_rollback_action_with_implementation(self) -> None:
        """Test rollback action generation with proper implementation."""
        registry = ActionRegistry()

        # Register a reversible action implementation
        definition = ActionDefinition(
            action_type="test_reversible",
            display_name="Test Reversible Action",
            description="A reversible test action",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.LOW,
            is_reversible=True,
        )
        registry.register_definition(definition)

        class ReversibleImplementation(BaseRemediationAction):
            async def execute(
                self,
                action: RemediationAction,
                gcp_clients: dict[str, Any],
                dry_run: bool = False,
            ) -> dict[str, Any]:
                return {"status": "success"}

            async def validate_prerequisites(
                self, action: RemediationAction, gcp_clients: dict[str, Any]
            ) -> bool:
                return True

            async def capture_state(
                self, action: RemediationAction, gcp_clients: dict[str, Any]
            ) -> dict[str, Any]:
                return {"state": "captured"}

            def get_rollback_definition(self) -> RollbackDefinition:
                return RollbackDefinition(
                    rollback_action_type="test_rollback",
                    state_params_mapping={"original_value": "captured_value"},
                    additional_params={"rollback": True},
                )

        registry.register_implementation("test_reversible", ReversibleImplementation)

        # Register the rollback action definition too
        rollback_definition = ActionDefinition(
            action_type="test_rollback",
            display_name="Test Rollback Action",
            description="Rollback for test action",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.LOW,
        )
        registry.register_definition(rollback_definition)

        action = RemediationAction(
            incident_id="test-incident",
            action_type="test_reversible",
            description="Test action",
            target_resource="test_resource",
            params={"project_id": "test-project", "zone": "us-central1-a"},
        )

        state_snapshot = {"captured_value": "original_state"}
        rollback_action = registry.get_rollback_action(action, state_snapshot)

        assert rollback_action is not None
        assert rollback_action.action_type == "test_rollback"
        assert rollback_action.incident_id == "test-incident"
        assert "Rollback of test_reversible" in rollback_action.description
        assert rollback_action.params["original_value"] == "original_state"
        assert rollback_action.params["rollback"] is True
        assert rollback_action.params["project_id"] == "test-project"
        assert rollback_action.params["zone"] == "us-central1-a"


class TestCoreActions:
    """Test the core actions registered by default."""

    def test_block_ip_address_definition(self) -> None:
        """Test the block_ip_address action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("block_ip_address")

        assert definition is not None
        assert definition.action_type == "block_ip_address"
        assert definition.display_name == "Block IP Address"
        assert definition.category == ActionCategory.NETWORK_SECURITY
        assert definition.risk_level == ActionRiskLevel.MEDIUM
        assert "ip_address" in definition.required_params
        assert "project_id" in definition.required_params
        assert "firewall_rule_name" in definition.optional_params
        assert definition.is_reversible is True
        assert definition.requires_approval is False

    def test_disable_user_account_definition(self) -> None:
        """Test the disable_user_account action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("disable_user_account")

        assert definition is not None
        assert definition.action_type == "disable_user_account"
        assert definition.category == ActionCategory.IAM_SECURITY
        assert definition.risk_level == ActionRiskLevel.HIGH
        assert "user_email" in definition.required_params
        assert "project_id" in definition.required_params
        assert definition.requires_approval is True

    def test_revoke_iam_permission_definition(self) -> None:
        """Test the revoke_iam_permission action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("revoke_iam_permission")

        assert definition is not None
        assert definition.action_type == "revoke_iam_permission"
        assert definition.category == ActionCategory.IAM_SECURITY
        assert definition.risk_level == ActionRiskLevel.HIGH
        assert "member" in definition.required_params
        assert "role" in definition.required_params
        assert "resource" in definition.required_params
        assert "project_id" in definition.required_params

    def test_quarantine_instance_definition(self) -> None:
        """Test the quarantine_instance action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("quarantine_instance")

        assert definition is not None
        assert definition.action_type == "quarantine_instance"
        assert definition.category == ActionCategory.COMPUTE_SECURITY
        assert definition.risk_level == ActionRiskLevel.HIGH
        assert "instance_name" in definition.required_params
        assert "zone" in definition.required_params
        assert "project_id" in definition.required_params

    def test_rotate_credentials_definition(self) -> None:
        """Test the rotate_credentials action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("rotate_credentials")

        assert definition is not None
        assert definition.action_type == "rotate_credentials"
        assert definition.category == ActionCategory.CREDENTIAL_MANAGEMENT
        assert definition.risk_level == ActionRiskLevel.CRITICAL
        assert "credential_type" in definition.required_params
        assert "resource_id" in definition.required_params
        assert "project_id" in definition.required_params
        assert definition.is_reversible is False
        assert definition.requires_approval is True

    def test_restore_from_backup_definition(self) -> None:
        """Test the restore_from_backup action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("restore_from_backup")

        assert definition is not None
        assert definition.action_type == "restore_from_backup"
        assert definition.category == ActionCategory.DATA_PROTECTION
        assert definition.risk_level == ActionRiskLevel.CRITICAL
        assert "resource_type" in definition.required_params
        assert "resource_id" in definition.required_params
        assert "backup_id" in definition.required_params
        assert "project_id" in definition.required_params
        assert definition.is_reversible is False

    def test_apply_security_patches_definition(self) -> None:
        """Test the apply_security_patches action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("apply_security_patches")

        assert definition is not None
        assert definition.action_type == "apply_security_patches"
        assert definition.category == ActionCategory.COMPUTE_SECURITY
        assert definition.risk_level == ActionRiskLevel.MEDIUM
        assert "instance_name" in definition.required_params
        assert "zone" in definition.required_params
        assert "patch_ids" in definition.required_params
        assert "project_id" in definition.required_params
        assert definition.is_reversible is False

    def test_enable_additional_logging_definition(self) -> None:
        """Test the enable_additional_logging action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("enable_additional_logging")

        assert definition is not None
        assert definition.action_type == "enable_additional_logging"
        assert definition.category == ActionCategory.LOGGING_MONITORING
        assert definition.risk_level == ActionRiskLevel.LOW
        assert "resource_type" in definition.required_params
        assert "resource_id" in definition.required_params
        assert "log_types" in definition.required_params
        assert "project_id" in definition.required_params
        assert definition.is_reversible is True
        assert definition.requires_approval is False

    def test_modify_load_balancer_settings_definition(self) -> None:
        """Test the modify_load_balancer_settings action definition."""
        registry = ActionRegistry()
        definition = registry.get_definition("modify_load_balancer_settings")

        assert definition is not None
        assert definition.action_type == "modify_load_balancer_settings"
        assert definition.category == ActionCategory.NETWORK_SECURITY
        assert definition.risk_level == ActionRiskLevel.HIGH
        assert "load_balancer_name" in definition.required_params
        assert "modification_type" in definition.required_params
        assert "project_id" in definition.required_params
        assert "region" in definition.optional_params
        assert definition.is_reversible is True
        assert definition.requires_approval is True


class TestEnums:
    """Test the enum classes."""

    def test_action_risk_level_enum(self) -> None:
        """Test ActionRiskLevel enum values."""
        assert ActionRiskLevel.LOW.value == "low"
        assert ActionRiskLevel.MEDIUM.value == "medium"
        assert ActionRiskLevel.HIGH.value == "high"
        assert ActionRiskLevel.CRITICAL.value == "critical"

    def test_action_category_enum(self) -> None:
        """Test ActionCategory enum values."""
        assert ActionCategory.NETWORK_SECURITY.value == "network_security"
        assert ActionCategory.IAM_SECURITY.value == "iam_security"
        assert ActionCategory.COMPUTE_SECURITY.value == "compute_security"
        assert ActionCategory.STORAGE_SECURITY.value == "storage_security"
        assert ActionCategory.CREDENTIAL_MANAGEMENT.value == "credential_management"
        assert ActionCategory.LOGGING_MONITORING.value == "logging_monitoring"
        assert ActionCategory.DATA_PROTECTION.value == "data_protection"


class TestRollbackDefinition:
    """Test the RollbackDefinition class."""

    def test_rollback_definition_creation(self) -> None:
        """Test creating a rollback definition."""
        rollback_def = RollbackDefinition(
            rollback_action_type="undo_action",
            state_params_mapping={"original_state": "captured_state"},
            additional_params={"undo": True},
        )

        assert rollback_def.rollback_action_type == "undo_action"
        assert rollback_def.state_params_mapping == {"original_state": "captured_state"}
        assert rollback_def.additional_params == {"undo": True}

    def test_rollback_definition_defaults(self) -> None:
        """Test rollback definition with default values."""
        rollback_def = RollbackDefinition(rollback_action_type="undo_action")

        assert rollback_def.rollback_action_type == "undo_action"
        assert rollback_def.state_params_mapping == {}
        assert rollback_def.additional_params == {}

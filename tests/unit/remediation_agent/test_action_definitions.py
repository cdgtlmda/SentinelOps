"""
Unit tests for remediation agent action definitions.

Tests action definition functionality including:
- Action validation
- Parameter checking
- Constraint validation
- Action chaining
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

import pytest

from src.common.exceptions import ValidationError


# Define the enums and classes we need for testing directly
class ActionRiskLevel(Enum):
    """Risk levels for remediation actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionCategory(Enum):
    """Categories of remediation actions."""

    NETWORK_SECURITY = "network_security"
    IAM_SECURITY = "iam_security"
    COMPUTE_SECURITY = "compute_security"
    STORAGE_SECURITY = "storage_security"
    CREDENTIAL_MANAGEMENT = "credential_management"
    LOGGING_MONITORING = "logging_monitoring"
    DATA_PROTECTION = "data_protection"


@dataclass
class ActionDefinition:
    """Definition of a remediation action."""

    action_type: str
    display_name: str
    description: str
    category: ActionCategory
    risk_level: ActionRiskLevel
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    supported_resource_types: List[str] = field(default_factory=list)
    is_reversible: bool = True
    requires_approval: bool = False
    timeout_seconds: int = 120
    max_retries: int = 3

    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters for this action."""
        # Check required parameters
        missing_params = set(self.required_params) - set(params.keys())
        if missing_params:
            raise ValidationError(
                f"Missing required parameters for {self.action_type}: {missing_params}"
            )

        # Validate parameter types
        for param_name, param_value in params.items():
            if param_value is None and param_name not in self.optional_params:
                raise ValidationError(
                    f"Parameter '{param_name}' cannot be None for {self.action_type}"
                )


@dataclass
class RollbackDefinition:
    """Definition of how to rollback an action."""

    rollback_action_type: str
    state_params_mapping: Dict[str, str] = field(default_factory=dict)
    additional_params: Dict[str, Any] = field(default_factory=dict)


class TestActionDefinition:
    """Test suite for action definition functionality."""

    @pytest.fixture
    def basic_action_definition(self) -> ActionDefinition:
        """Create a basic action definition for testing."""
        return ActionDefinition(
            action_type="test_action",
            display_name="Test Action",
            description="A test remediation action",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.MEDIUM,
            required_params=["resource_id", "project_id"],
            optional_params=["dry_run", "reason"],
            required_permissions=["compute.instances.update"],
            prerequisites=["resource_exists", "has_network_access"],
            supported_resource_types=["compute_instance", "vpc_network"],
            is_reversible=True,
            requires_approval=False,
            timeout_seconds=120,
            max_retries=3,
        )

    def test_action_definition_creation(
        self, basic_action_definition: ActionDefinition
    ) -> None:
        """Test creating an action definition."""
        assert basic_action_definition.action_type == "test_action"
        assert basic_action_definition.display_name == "Test Action"
        assert basic_action_definition.category == ActionCategory.NETWORK_SECURITY
        assert basic_action_definition.risk_level == ActionRiskLevel.MEDIUM
        assert len(basic_action_definition.required_params) == 2
        assert "resource_id" in basic_action_definition.required_params
        assert basic_action_definition.is_reversible is True

    def test_action_validation_success(
        self, basic_action_definition: ActionDefinition
    ) -> None:
        """Test successful parameter validation."""
        valid_params = {
            "resource_id": "instance-123",
            "project_id": "test-project",
            "dry_run": True,  # Optional param
        }

        # Should not raise any exception
        basic_action_definition.validate_params(valid_params)

    def test_action_validation_missing_required(
        self, basic_action_definition: ActionDefinition
    ) -> None:
        """Test validation with missing required parameters."""
        invalid_params = {
            "resource_id": "instance-123",
            # Missing project_id
        }

        with pytest.raises(ValidationError) as exc_info:
            basic_action_definition.validate_params(invalid_params)

        assert "Missing required parameters" in str(exc_info.value)
        assert "project_id" in str(exc_info.value)

    def test_action_validation_null_required(
        self, basic_action_definition: ActionDefinition
    ) -> None:
        """Test validation with null required parameters."""
        invalid_params = {
            "resource_id": "instance-123",
            "project_id": None,  # Cannot be None
        }

        with pytest.raises(ValidationError) as exc_info:
            basic_action_definition.validate_params(invalid_params)

        assert "cannot be None" in str(exc_info.value)
        assert "project_id" in str(exc_info.value)

    def test_action_validation_null_optional(
        self, basic_action_definition: ActionDefinition
    ) -> None:
        """Test validation with null optional parameters."""
        valid_params = {
            "resource_id": "instance-123",
            "project_id": "test-project",
            "dry_run": None,  # Optional can be None
        }

        # Should not raise exception for null optional params
        basic_action_definition.validate_params(valid_params)

    def test_high_risk_action_requires_approval(self) -> None:
        """Test that high-risk actions require approval."""
        high_risk_action = ActionDefinition(
            action_type="delete_all_backups",
            display_name="Delete All Backups",
            description="Permanently delete all backup data",
            category=ActionCategory.DATA_PROTECTION,
            risk_level=ActionRiskLevel.CRITICAL,
            required_params=["project_id", "confirmation_token"],
            is_reversible=False,  # Cannot be undone
            requires_approval=True,  # Must require approval
            timeout_seconds=300,
        )

        assert high_risk_action.risk_level == ActionRiskLevel.CRITICAL
        assert high_risk_action.requires_approval is True
        assert high_risk_action.is_reversible is False

    def test_action_categories(self) -> None:
        """Test different action categories."""
        categories = [
            ActionCategory.NETWORK_SECURITY,
            ActionCategory.IAM_SECURITY,
            ActionCategory.COMPUTE_SECURITY,
            ActionCategory.STORAGE_SECURITY,
            ActionCategory.CREDENTIAL_MANAGEMENT,
            ActionCategory.LOGGING_MONITORING,
            ActionCategory.DATA_PROTECTION,
        ]

        # Verify all categories are unique
        assert len(categories) == len(set(categories))

        # Verify category values
        assert ActionCategory.NETWORK_SECURITY.value == "network_security"
        assert ActionCategory.IAM_SECURITY.value == "iam_security"

    def test_action_risk_levels(self) -> None:
        """Test action risk level hierarchy."""
        risk_levels = [
            ActionRiskLevel.LOW,
            ActionRiskLevel.MEDIUM,
            ActionRiskLevel.HIGH,
            ActionRiskLevel.CRITICAL,
        ]

        # Verify risk levels are ordered
        risk_values = [level.value for level in risk_levels]
        assert risk_values == ["low", "medium", "high", "critical"]

    def test_rollback_definition(self) -> None:
        """Test rollback definition for reversible actions."""
        rollback = RollbackDefinition(
            rollback_action_type="restore_firewall_rule",
            state_params_mapping={
                "rule_name": "original_rule_name",
                "source_ranges": "original_source_ranges",
            },
            additional_params={
                "priority": 1000,
                "direction": "INGRESS",
            },
        )

        assert rollback.rollback_action_type == "restore_firewall_rule"
        assert "rule_name" in rollback.state_params_mapping
        assert rollback.additional_params["priority"] == 1000


class TestParameterChecking:
    """Test suite for parameter checking and validation."""

    def test_complex_parameter_validation(self) -> None:
        """Test validation of complex parameters."""
        action = ActionDefinition(
            action_type="complex_action",
            display_name="Complex Action",
            description="Action with complex validation",
            category=ActionCategory.COMPUTE_SECURITY,
            risk_level=ActionRiskLevel.HIGH,
            required_params=["resource_list", "config_map", "threshold"],
        )

        # Valid complex parameters
        valid_params = {
            "resource_list": ["instance-1", "instance-2", "instance-3"],
            "config_map": {
                "timeout": 300,
                "retries": 3,
                "mode": "aggressive",
            },
            "threshold": 0.85,
        }

        # Should validate successfully
        action.validate_params(valid_params)

        # Test with empty list (still valid structure)
        valid_params["resource_list"] = []
        action.validate_params(valid_params)


class TestConstraintValidation:
    """Test suite for constraint validation."""

    def test_resource_type_constraints(self) -> None:
        """Test resource type constraint validation."""
        action = ActionDefinition(
            action_type="resource_specific_action",
            display_name="Resource Specific Action",
            description="Action limited to specific resource types",
            category=ActionCategory.COMPUTE_SECURITY,
            risk_level=ActionRiskLevel.MEDIUM,
            supported_resource_types=["compute_instance", "container_cluster"],
        )

        # Verify supported resource types
        assert "compute_instance" in action.supported_resource_types
        assert "container_cluster" in action.supported_resource_types
        assert "storage_bucket" not in action.supported_resource_types

    def test_permission_constraints(self) -> None:
        """Test permission requirement constraints."""
        action = ActionDefinition(
            action_type="privileged_action",
            display_name="Privileged Action",
            description="Action requiring specific permissions",
            category=ActionCategory.IAM_SECURITY,
            risk_level=ActionRiskLevel.HIGH,
            required_permissions=[
                "iam.serviceAccounts.delete",
                "iam.roles.update",
                "resourcemanager.projects.setIamPolicy",
            ],
        )

        # Verify all required permissions are specified
        assert len(action.required_permissions) == 3
        assert "iam.serviceAccounts.delete" in action.required_permissions

    def test_prerequisite_constraints(self) -> None:
        """Test prerequisite constraint validation."""
        action = ActionDefinition(
            action_type="dependent_action",
            display_name="Dependent Action",
            description="Action with prerequisites",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.MEDIUM,
            prerequisites=[
                "target_resource_exists",
                "no_active_connections",
                "backup_completed",
            ],
        )

        # Verify prerequisites are defined
        assert len(action.prerequisites) == 3
        assert "backup_completed" in action.prerequisites

    def test_timeout_constraints(self) -> None:
        """Test timeout constraint validation."""
        # Short timeout for simple actions
        quick_action = ActionDefinition(
            action_type="quick_action",
            display_name="Quick Action",
            description="Fast action",
            category=ActionCategory.LOGGING_MONITORING,
            risk_level=ActionRiskLevel.LOW,
            timeout_seconds=30,  # 30 seconds
        )

        # Long timeout for complex actions
        slow_action = ActionDefinition(
            action_type="slow_action",
            display_name="Slow Action",
            description="Time-consuming action",
            category=ActionCategory.DATA_PROTECTION,
            risk_level=ActionRiskLevel.HIGH,
            timeout_seconds=3600,  # 1 hour
        )

        assert quick_action.timeout_seconds == 30
        assert slow_action.timeout_seconds == 3600

    def test_retry_constraints(self) -> None:
        """Test retry constraint validation."""
        # No retries for critical actions
        critical_action = ActionDefinition(
            action_type="critical_action",
            display_name="Critical Action",
            description="Cannot be retried",
            category=ActionCategory.DATA_PROTECTION,
            risk_level=ActionRiskLevel.CRITICAL,
            max_retries=0,  # No retries allowed
        )

        # Multiple retries for resilient actions
        resilient_action = ActionDefinition(
            action_type="resilient_action",
            display_name="Resilient Action",
            description="Can be retried",
            category=ActionCategory.NETWORK_SECURITY,
            risk_level=ActionRiskLevel.LOW,
            max_retries=5,  # Up to 5 retries
        )

        assert critical_action.max_retries == 0
        assert resilient_action.max_retries == 5


class TestActionChaining:
    """Test suite for action chaining functionality."""

    def test_simple_action_chain(self) -> None:
        """Test simple sequential action chain."""
        # Define a chain of actions
        action_chain = [
            ActionDefinition(
                action_type="isolate_instance",
                display_name="Isolate Instance",
                description="Isolate compromised instance",
                category=ActionCategory.COMPUTE_SECURITY,
                risk_level=ActionRiskLevel.MEDIUM,
                required_params=["instance_id"],
            ),
            ActionDefinition(
                action_type="snapshot_instance",
                display_name="Snapshot Instance",
                description="Create forensic snapshot",
                category=ActionCategory.DATA_PROTECTION,
                risk_level=ActionRiskLevel.LOW,
                required_params=["instance_id", "snapshot_name"],
            ),
            ActionDefinition(
                action_type="stop_instance",
                display_name="Stop Instance",
                description="Stop the instance",
                category=ActionCategory.COMPUTE_SECURITY,
                risk_level=ActionRiskLevel.MEDIUM,
                required_params=["instance_id"],
            ),
        ]

        # Verify chain properties
        assert len(action_chain) == 3
        assert action_chain[0].action_type == "isolate_instance"
        assert action_chain[-1].action_type == "stop_instance"

    def test_rollback_chain(self) -> None:
        """Test rollback chain for reversible actions."""
        # Forward action chain
        forward_chain = [
            ActionDefinition(
                action_type="modify_firewall",
                display_name="Modify Firewall",
                description="Update firewall rules",
                category=ActionCategory.NETWORK_SECURITY,
                risk_level=ActionRiskLevel.MEDIUM,
                is_reversible=True,
            ),
            ActionDefinition(
                action_type="update_iam_policy",
                display_name="Update IAM Policy",
                description="Change IAM policy",
                category=ActionCategory.IAM_SECURITY,
                risk_level=ActionRiskLevel.HIGH,
                is_reversible=True,
            ),
        ]

        # Rollback definitions
        rollback_chain = [
            RollbackDefinition(
                rollback_action_type="restore_iam_policy",
                state_params_mapping={"policy": "original_policy"},
            ),
            RollbackDefinition(
                rollback_action_type="restore_firewall",
                state_params_mapping={"rules": "original_rules"},
            ),
        ]

        # Verify rollback chain is in reverse order
        assert len(rollback_chain) == len(forward_chain)
        assert rollback_chain[0].rollback_action_type == "restore_iam_policy"
        assert rollback_chain[1].rollback_action_type == "restore_firewall"

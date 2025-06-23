"""
Action Registry for the Remediation Agent.

This module provides the action registry system that manages remediation action
definitions, validation, prerequisites checking, and rollback capabilities.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type

from src.common.exceptions import ValidationError
from src.common.models import RemediationAction


class ActionRiskLevel(Enum):
    """Risk levels for remediation actions."""

    LOW = "low"  # Minimal impact, easily reversible
    MEDIUM = "medium"  # Moderate impact, reversible with effort
    HIGH = "high"  # Significant impact, difficult to reverse
    CRITICAL = "critical"  # Major impact, may be irreversible


class ActionCategory(Enum):
    """Categories of remediation actions."""

    NETWORK_SECURITY = "network_security"
    IAM_SECURITY = "iam_security"
    COMPUTE_SECURITY = "compute_security"
    STORAGE_SECURITY = "storage_security"
    CREDENTIAL_MANAGEMENT = "credential_management"
    LOGGING_MONITORING = "logging_monitoring"
    DATA_PROTECTION = "data_protection"
    INFRASTRUCTURE = "infrastructure"
    FORENSICS = "forensics"


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
        """
        Validate parameters for this action.

        Args:
            params: Parameters to validate

        Raises:
            ValidationError: If validation fails
        """
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


class BaseRemediationAction(ABC):
    """Abstract base class for remediation actions."""

    def __init__(self, definition: ActionDefinition):
        """
        Initialize the base remediation action.

        Args:
            definition: Action definition
        """
        self.definition = definition
        self.logger = logging.getLogger(f"remediation.{definition.action_type}")

    @abstractmethod
    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute the remediation action.

        Args:
            action: The remediation action to execute
            gcp_clients: Dictionary of initialized GCP clients
            dry_run: Whether to perform a dry run

        Returns:
            Execution result dictionary
        """

    @abstractmethod
    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """
        Validate prerequisites for the action.

        Args:
            action: The remediation action to validate
            gcp_clients: Dictionary of initialized GCP clients

        Returns:
            True if prerequisites are met, False otherwise
        """

    @abstractmethod
    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Capture current state for rollback.

        Args:
            action: The remediation action
            gcp_clients: Dictionary of initialized GCP clients

        Returns:
            State snapshot dictionary
        """

    @abstractmethod
    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """
        Get the rollback definition for this action.

        Returns:
            Rollback definition or None if not reversible
        """


class ActionRegistry:
    """Registry for managing remediation actions."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the action registry.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._definitions: Dict[str, ActionDefinition] = {}
        self._implementations: Dict[str, Type[BaseRemediationAction]] = {}
        self._instances: Dict[str, BaseRemediationAction] = {}

        # Register core actions
        self._register_core_actions()

    def _register_core_actions(self) -> None:
        """Register core remediation action definitions."""

        # Network Security Actions
        self.register_definition(
            ActionDefinition(
                action_type="block_ip_address",
                display_name="Block IP Address",
                description="Block a suspicious IP address using firewall rules",
                category=ActionCategory.NETWORK_SECURITY,
                risk_level=ActionRiskLevel.MEDIUM,
                required_params=["ip_address", "project_id"],
                optional_params=["firewall_rule_name", "priority", "description"],
                required_permissions=[
                    "compute.firewalls.create",
                    "compute.firewalls.update",
                ],
                supported_resource_types=["firewall_rule"],
                is_reversible=True,
                requires_approval=False,
                timeout_seconds=60,
            )
        )

        self.register_definition(
            ActionDefinition(
                action_type="disable_user_account",
                display_name="Disable User Account",
                description="Disable a compromised user account",
                category=ActionCategory.IAM_SECURITY,
                risk_level=ActionRiskLevel.HIGH,
                required_params=["user_email", "project_id"],
                optional_params=["reason", "notification_emails"],
                required_permissions=["resourcemanager.projects.setIamPolicy"],
                supported_resource_types=["iam_user"],
                is_reversible=True,
                requires_approval=True,
                timeout_seconds=30,
            )
        )

        self.register_definition(
            ActionDefinition(
                action_type="revoke_iam_permission",
                display_name="Revoke IAM Permission",
                description="Revoke suspicious IAM permissions",
                category=ActionCategory.IAM_SECURITY,
                risk_level=ActionRiskLevel.HIGH,
                required_params=["member", "role", "resource", "project_id"],
                optional_params=["reason"],
                required_permissions=["resourcemanager.projects.setIamPolicy"],
                supported_resource_types=["iam_policy"],
                is_reversible=True,
                requires_approval=True,
                timeout_seconds=30,
            )
        )

        self.register_definition(
            ActionDefinition(
                action_type="quarantine_instance",
                display_name="Quarantine Instance",
                description="Isolate an infected compute instance",
                category=ActionCategory.COMPUTE_SECURITY,
                risk_level=ActionRiskLevel.HIGH,
                required_params=["instance_name", "zone", "project_id"],
                optional_params=["quarantine_network", "quarantine_tags"],
                required_permissions=[
                    "compute.instances.setTags",
                    "compute.instances.updateNetworkInterface",
                ],
                supported_resource_types=["compute_instance"],
                is_reversible=True,
                requires_approval=True,
                timeout_seconds=120,
            )
        )

        self.register_definition(
            ActionDefinition(
                action_type="rotate_credentials",
                display_name="Rotate Credentials",
                description="Rotate compromised credentials",
                category=ActionCategory.CREDENTIAL_MANAGEMENT,
                risk_level=ActionRiskLevel.CRITICAL,
                required_params=["credential_type", "resource_id", "project_id"],
                optional_params=["notification_emails", "grace_period_minutes"],
                required_permissions=[
                    "iam.serviceAccountKeys.create",
                    "iam.serviceAccountKeys.delete",
                ],
                supported_resource_types=["service_account", "api_key"],
                is_reversible=False,
                requires_approval=True,
                timeout_seconds=180,
            )
        )

        self.register_definition(
            ActionDefinition(
                action_type="restore_from_backup",
                display_name="Restore from Backup",
                description="Restore resource from backup",
                category=ActionCategory.DATA_PROTECTION,
                risk_level=ActionRiskLevel.CRITICAL,
                required_params=[
                    "resource_type",
                    "resource_id",
                    "backup_id",
                    "project_id",
                ],
                optional_params=["restore_point_time"],
                required_permissions=[
                    "compute.disks.create",
                    "compute.snapshots.useReadOnly",
                ],
                supported_resource_types=["compute_disk", "storage_bucket"],
                is_reversible=False,
                requires_approval=True,
                timeout_seconds=300,
            )
        )

        self.register_definition(
            ActionDefinition(
                action_type="apply_security_patches",
                display_name="Apply Security Patches",
                description="Apply critical security patches to instances",
                category=ActionCategory.COMPUTE_SECURITY,
                risk_level=ActionRiskLevel.MEDIUM,
                required_params=["instance_name", "zone", "patch_ids", "project_id"],
                optional_params=["maintenance_window", "reboot_required"],
                required_permissions=[
                    "compute.instances.setMetadata",
                    "osconfig.patchJobs.create",
                ],
                supported_resource_types=["compute_instance"],
                is_reversible=False,
                requires_approval=True,
                timeout_seconds=600,
            )
        )

        self.register_definition(
            ActionDefinition(
                action_type="enable_additional_logging",
                display_name="Enable Additional Logging",
                description="Enable enhanced logging for investigation",
                category=ActionCategory.LOGGING_MONITORING,
                risk_level=ActionRiskLevel.LOW,
                required_params=[
                    "resource_type",
                    "resource_id",
                    "log_types",
                    "project_id",
                ],
                optional_params=["retention_days", "log_sink"],
                required_permissions=["logging.sinks.create", "logging.logs.list"],
                supported_resource_types=[
                    "compute_instance",
                    "storage_bucket",
                    "iam_policy",
                ],
                is_reversible=True,
                requires_approval=False,
                timeout_seconds=60,
            )
        )

        self.register_definition(
            ActionDefinition(
                action_type="modify_load_balancer_settings",
                display_name="Modify Load Balancer Settings",
                description="Modify load balancer configuration for security remediation",
                category=ActionCategory.NETWORK_SECURITY,
                risk_level=ActionRiskLevel.HIGH,
                required_params=[
                    "load_balancer_name",
                    "modification_type",
                    "project_id",
                ],
                optional_params=[
                    "region",
                    "backend_instance_group",
                    "security_policy_name",
                    "allowed_source_ranges",
                    "sample_rate",
                ],
                required_permissions=[
                    "compute.backendServices.get",
                    "compute.backendServices.update",
                    "compute.securityPolicies.create",
                    "compute.forwardingRules.list",
                ],
                supported_resource_types=["load_balancer"],
                is_reversible=True,
                requires_approval=True,
                timeout_seconds=180,
            )
        )

    def register_definition(self, definition: ActionDefinition) -> None:
        """
        Register an action definition.

        Args:
            definition: Action definition to register
        """
        self._definitions[definition.action_type] = definition
        self.logger.info(f"Registered action definition: {definition.action_type}")

    def register_implementation(
        self, action_type: str, implementation_class: Type[BaseRemediationAction]
    ) -> None:
        """
        Register an action implementation.

        Args:
            action_type: Type of action
            implementation_class: Implementation class
        """
        if action_type not in self._definitions:
            raise ValueError(f"No definition found for action type: {action_type}")

        self._implementations[action_type] = implementation_class
        self.logger.info(f"Registered action implementation: {action_type}")

    def get_definition(self, action_type: str) -> Optional[ActionDefinition]:
        """
        Get an action definition.

        Args:
            action_type: Type of action

        Returns:
            Action definition or None
        """
        return self._definitions.get(action_type)

    def get_implementation(self, action_type: str) -> Optional[BaseRemediationAction]:
        """
        Get an action implementation instance.

        Args:
            action_type: Type of action

        Returns:
            Action implementation instance or None
        """
        if action_type not in self._instances:
            implementation_class = self._implementations.get(action_type)
            if implementation_class:
                definition = self._definitions[action_type]
                self._instances[action_type] = implementation_class(definition)

        return self._instances.get(action_type)

    def validate_action(self, action: RemediationAction) -> bool:
        """
        Validate a remediation action.

        Args:
            action: Action to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if action type exists
            definition = self.get_definition(action.action_type)
            if not definition:
                self.logger.error(f"Unknown action type: {action.action_type}")
                return False

            # Validate parameters
            definition.validate_params(action.params)

            # Validate resource type if specified
            if definition.supported_resource_types:
                resource_type = action.params.get("resource_type", "")
                if (
                    resource_type
                    and resource_type not in definition.supported_resource_types
                ):
                    self.logger.error(
                        "Unsupported resource type '%s' for action %s",
                        resource_type,
                        action.action_type,
                    )
                    return False

            return True

        except ValidationError as e:
            self.logger.error("Action validation failed: %s", e)
            return False
        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error("Unexpected error during validation: %s", e)
            return False

    def get_actions_by_category(
        self, category: ActionCategory
    ) -> List[ActionDefinition]:
        """
        Get all actions in a category.

        Args:
            category: Action category

        Returns:
            List of action definitions
        """
        return [
            definition
            for definition in self._definitions.values()
            if definition.category == category
        ]

    def get_actions_by_risk_level(
        self, risk_level: ActionRiskLevel
    ) -> List[ActionDefinition]:
        """
        Get all actions with a specific risk level.

        Args:
            risk_level: Risk level

        Returns:
            List of action definitions
        """
        return [
            definition
            for definition in self._definitions.values()
            if definition.risk_level == risk_level
        ]

    def check_prerequisites(
        self, action: RemediationAction, available_actions: Set[str]
    ) -> bool:
        """
        Check if prerequisites for an action are met.

        Args:
            action: Action to check
            available_actions: Set of available action types

        Returns:
            True if prerequisites are met, False otherwise
        """
        definition = self.get_definition(action.action_type)
        if not definition:
            return False

        # Check if all prerequisite actions are available
        for prerequisite in definition.prerequisites:
            if prerequisite not in available_actions:
                self.logger.warning(
                    f"Prerequisite '{prerequisite}' not available for action {action.action_type}"
                )
                return False

        return True

    def get_rollback_action(
        self, original_action: RemediationAction, state_snapshot: Dict[str, Any]
    ) -> Optional[RemediationAction]:
        """
        Get a rollback action for a completed action.

        Args:
            original_action: The original action that was executed
            state_snapshot: State captured before the action

        Returns:
            Rollback action or None if not reversible
        """
        definition = self.get_definition(original_action.action_type)
        if not definition or not definition.is_reversible:
            return None

        implementation = self.get_implementation(original_action.action_type)
        if not implementation:
            return None

        rollback_def = implementation.get_rollback_definition()
        if not rollback_def:
            return None

        # Create rollback action
        rollback_params = {}

        # Map state parameters
        for param_name, state_key in rollback_def.state_params_mapping.items():
            if state_key in state_snapshot:
                rollback_params[param_name] = state_snapshot[state_key]

        # Add additional parameters
        rollback_params.update(rollback_def.additional_params)

        # Copy some parameters from original action
        for param in ["project_id", "zone", "region"]:
            if param in original_action.params:
                rollback_params[param] = original_action.params[param]

        return RemediationAction(
            incident_id=original_action.incident_id,
            action_type=rollback_def.rollback_action_type,
            description=f"Rollback of {original_action.action_type}",
            target_resource=original_action.target_resource,
            params=rollback_params,
        )

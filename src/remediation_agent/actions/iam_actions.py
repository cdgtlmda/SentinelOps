"""
Google Cloud IAM remediation actions.

This module contains implementations for IAM-specific remediation actions.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.api_core import exceptions as google_exceptions

from src.common.exceptions import RemediationAgentError
from src.common.models import RemediationAction
from src.remediation_agent.action_registry import (
    BaseRemediationAction,
    RollbackDefinition,
)


class IAMActionBase(BaseRemediationAction):
    """Base class for IAM actions."""

    def parse_member(self, member: str) -> tuple[str, str]:
        """Parse a member string into type and identity."""
        parts = member.split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid member format: {member}")
        return parts[0], parts[1]

    def validate_member_format(self, member: str) -> bool:
        """Validate member string format."""
        valid_prefixes = [
            "user",
            "serviceAccount",
            "group",
            "domain",
            "projectOwner",
            "projectEditor",
            "projectViewer",
        ]
        try:
            member_type, _ = self.parse_member(member)
            return member_type in valid_prefixes
        except ValueError:
            return False

    def validate_role_format(self, role: str) -> bool:
        """Validate role string format."""
        return (
            role.startswith("roles/")
            or role.startswith("projects/")
            or role.startswith("organizations/")
        )


class RemoveServiceAccountKeyAction(IAMActionBase):
    """Implementation for removing service account keys."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Remove a service account key."""
        try:
            service_account_email = action.params["service_account_email"]
            key_id = action.params.get("key_id")
            project_id = action.params["project_id"]

            if dry_run:
                return {
                    "dry_run": True,
                    "service_account": service_account_email,
                    "action": "would_remove_keys",
                    "key_id": key_id,
                }

            # Get IAM admin client from resource manager
            if "iam_admin" not in gcp_clients:
                raise RemediationAgentError(
                    "IAM admin client not available in resource manager"
                )

            iam_client = gcp_clients["iam_admin"]

            keys_deleted = []
            errors = []

            if key_id:
                # Delete specific key
                try:
                    key_name = (f"projects/{project_id}/serviceAccounts/"
                                f"{service_account_email}/keys/{key_id}")
                    iam_client.delete_service_account_key(name=key_name)
                    keys_deleted.append(key_id)
                except google_exceptions.GoogleAPIError as e:
                    errors.append(f"Failed to delete key {key_id}: {str(e)}")
            else:
                # List and delete all keys except the system-managed key
                try:
                    # List all keys
                    service_account_name = (
                        f"projects/{project_id}/serviceAccounts/{service_account_email}"
                    )
                    keys_response = iam_client.list_service_account_keys(
                        name=service_account_name
                    )

                    for key in keys_response.keys:
                        # Skip system-managed keys (key_type == SYSTEM_MANAGED)
                        if (hasattr(key, 'key_type') and
                                key.key_type == "USER_MANAGED"):
                            try:
                                iam_client.delete_service_account_key(name=key.name)
                                # Extract key ID from full name
                                key_id_from_name = key.name.split("/")[-1]
                                keys_deleted.append(key_id_from_name)
                            except google_exceptions.GoogleAPIError as e:
                                errors.append(
                                    f"Failed to delete key {key.name}: {str(e)}"
                                )

                except google_exceptions.GoogleAPIError as e:
                    errors.append(f"Failed to list keys: {str(e)}")

            return {
                "service_account": service_account_email,
                "status": "partial_success" if errors else "success",
                "keys_deleted": keys_deleted,
                "errors": errors,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(
                f"Failed to remove service account key: {e}"
            ) from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        return all(
            action.params.get(p) for p in ["service_account_email", "project_id"]
        )

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture state before removing keys."""
        try:
            project_id = action.params["project_id"]
            service_account_email = action.params["service_account_email"]

            # Get IAM admin client from resource manager
            if "iam_admin" not in gcp_clients:
                raise RemediationAgentError(
                    "IAM admin client not available in resource manager"
                )

            iam_client = gcp_clients["iam_admin"]

            # List current keys
            service_account_name = (
                f"projects/{project_id}/serviceAccounts/{service_account_email}"
            )
            keys_response = iam_client.list_service_account_keys(
                name=service_account_name
            )

            existing_keys = []
            for key in keys_response.keys:
                existing_keys.append(
                    {
                        "key_id": key.name.split("/")[-1],
                        "key_type": str(key.key_type),
                        "valid_after_time": (
                            key.valid_after_time.isoformat()
                            if key.valid_after_time
                            else None
                        ),
                        "valid_before_time": (
                            key.valid_before_time.isoformat()
                            if key.valid_before_time
                            else None
                        ),
                    }
                )

            return {
                "service_account": service_account_email,
                "existing_keys": existing_keys,
            }
        except (ValueError, AttributeError, google_exceptions.GoogleAPIError) as e:
            return {
                "service_account": action.params.get("service_account_email"),
                "existing_keys": [],
                "error": str(e),
            }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        # Key deletion is not reversible
        return None


class EnableMFARequirementAction(IAMActionBase):
    """Implementation for enabling MFA requirements."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Enable MFA requirement for users or groups."""
        try:
            target_type = action.params["target_type"]  # "user" or "group"
            target_identity = action.params["target_identity"]
            project_id = action.params["project_id"]

            if dry_run:
                return {
                    "dry_run": True,
                    "target": f"{target_type}:{target_identity}",
                    "action": "would_enable_mfa_requirement",
                }

            # Note: Google Cloud doesn't have a direct API to enforce MFA on specific users
            # This would typically be done through Google Workspace Admin SDK
            # For this implementation, we'll add a conditional binding that requires MFA

            resource_manager = gcp_clients["resource_manager"]
            project_name = f"projects/{project_id}"

            # Get current policy
            policy = resource_manager.get_iam_policy(resource=project_name)

            # Create a new conditional binding for MFA
            member = f"{target_type}:{target_identity}"

            # Find existing bindings for this member and add MFA condition
            bindings_updated = []

            for binding in policy.bindings:
                if member in binding.members:
                    # Create a new binding with MFA condition
                    new_binding = policy.bindings.add()
                    new_binding.role = binding.role
                    new_binding.members.append(member)

                    # Add condition requiring MFA
                    new_binding.condition.expression = (
                        'request.auth.access_levels.contains("mfa")'
                    )
                    new_binding.condition.title = "Require MFA"
                    new_binding.condition.description = (
                        f"MFA required for {member} - SentinelOps"
                    )

                    # Remove member from original binding
                    binding.members.remove(member)

                    # Add new conditional binding
                    policy.bindings.append(new_binding)
                    bindings_updated.append(binding.role)

            if bindings_updated:
                # Update the policy
                resource_manager.set_iam_policy(resource=project_name, policy=policy)

                return {
                    "target": f"{target_type}:{target_identity}",
                    "roles_updated": bindings_updated,
                    "status": "mfa_required",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                return {
                    "target": f"{target_type}:{target_identity}",
                    "status": "no_roles_found",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(f"Failed to enable MFA requirement: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        if not all(
            action.params.get(p)
            for p in ["target_type", "target_identity", "project_id"]
        ):
            return False

        target_type = action.params["target_type"]
        return target_type in ["user", "group"]

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture state before enabling MFA."""
        try:
            resource_manager = gcp_clients["resource_manager"]
            project_name = f"projects/{action.params['project_id']}"

            policy = resource_manager.get_iam_policy(resource=project_name)

            member = (
                f"{action.params['target_type']}:{action.params['target_identity']}"
            )
            existing_bindings = []

            for binding in policy.bindings:
                if member in binding.members:
                    existing_bindings.append(
                        {
                            "role": binding.role,
                            "has_condition": binding.condition is not None,
                        }
                    )

            return {"member": member, "existing_bindings": existing_bindings}
        except (ValueError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="remove_mfa_requirement",
            state_params_mapping={
                "target_type": "target_type",
                "target_identity": "target_identity",
                "bindings": "existing_bindings",
            },
        )


class UpdateIAMPolicyAction(IAMActionBase):
    """Implementation for updating IAM policies."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Update an IAM policy."""
        try:
            resource = action.params["resource"]
            policy_updates = action.params["policy_updates"]

            if dry_run:
                return {
                    "dry_run": True,
                    "resource": resource,
                    "updates": policy_updates,
                }

            # Get and update policy
            changes_made = await self._update_iam_policy(
                resource, policy_updates, gcp_clients
            )

            return {
                "resource": resource,
                "changes_made": changes_made,
                "status": "updated" if changes_made else "no_changes",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(f"Failed to update IAM policy: {e}") from e

    async def _update_iam_policy(
        self,
        resource: str,
        policy_updates: List[Dict[str, Any]],
        gcp_clients: Dict[str, Any],
    ) -> List[str]:
        """Update IAM policy with the specified changes."""
        resource_manager = gcp_clients["resource_manager"]
        policy = resource_manager.get_iam_policy(resource=resource)
        changes_made = []

        for update in policy_updates:
            update_type = update["type"]

            if update_type == "add_binding":
                changes = self._add_binding(policy, update["role"], update["members"])
                changes_made.extend(changes)

            elif update_type == "remove_binding":
                changes = self._remove_binding(
                    policy, update["role"], update["members"]
                )
                changes_made.extend(changes)

            elif update_type == "set_condition":
                changes = self._set_condition(
                    policy, update["role"], update["condition"]
                )
                changes_made.extend(changes)

        # Update the policy if changes were made
        if changes_made:
            resource_manager.set_iam_policy(resource=resource, policy=policy)

        return changes_made

    def _add_binding(self, policy: Any, role: str, members: List[str]) -> List[str]:
        """Add members to a role binding."""
        changes_made = []

        # Find or create binding for role
        binding = None
        for b in policy.bindings:
            if b.role == role:
                binding = b
                break

        if not binding:
            binding = policy.bindings.add()
            binding.role = role

        # Add members
        for member in members:
            if member not in binding.members:
                binding.members.append(member)
                changes_made.append(f"Added {member} to {role}")

        return changes_made

    def _remove_binding(self, policy: Any, role: str, members: List[str]) -> List[str]:
        """Remove members from a role binding."""
        changes_made = []

        # Find binding for role
        for binding in policy.bindings:
            if binding.role == role:
                for member in members:
                    if member in binding.members:
                        binding.members.remove(member)
                        changes_made.append(f"Removed {member} from {role}")

        return changes_made

    def _set_condition(self, policy: Any, role: str, condition: Any) -> List[str]:
        """Set condition on a role binding."""
        changes_made = []

        for binding in policy.bindings:
            if binding.role == role:
                binding.condition.CopyFrom(condition)
                changes_made.append(f"Set condition on {role}")

        return changes_made

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        if not all(action.params.get(p) for p in ["resource", "policy_updates"]):
            return False

        # Validate policy updates format
        for update in action.params["policy_updates"]:
            if "type" not in update:
                return False

            if update["type"] in ["add_binding", "remove_binding"]:
                if not all(k in update for k in ["role", "members"]):
                    return False

        return True

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current policy state."""
        try:
            resource_manager = gcp_clients["resource_manager"]
            policy = resource_manager.get_iam_policy(resource=action.params["resource"])

            return {
                "resource": action.params["resource"],
                "policy_snapshot": json.dumps(policy.__dict__),
            }
        except (ValueError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="restore_iam_policy",
            state_params_mapping={"resource": "resource", "policy": "policy_snapshot"},
        )

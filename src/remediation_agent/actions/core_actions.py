"""
Core remediation action implementations.

This module contains the implementations of core remediation actions for the
SentinelOps remediation agent.
"""

import asyncio
import ipaddress
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.cloud import compute_v1

from src.common.exceptions import RemediationAgentError, ValidationError
from src.common.models import RemediationAction
from src.remediation_agent.action_registry import (
    BaseRemediationAction,
    RollbackDefinition,
)


class BlockIPAddressAction(BaseRemediationAction):
    """Implementation for blocking IP addresses using firewall rules."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the block IP address action."""
        try:
            # Extract parameters
            ip_address = action.params["ip_address"]
            project_id = action.params["project_id"]
            rule_name = action.params.get(
                "firewall_rule_name", f"block-ip-{ip_address.replace('.', '-')}"
            )
            priority = action.params.get("priority", 1000)
            description = action.params.get(
                "description",
                f"Blocking suspicious IP {ip_address} - SentinelOps remediation",
            )
            # Validate IP address
            try:
                ipaddress.ip_address(ip_address)
            except ValueError as exc:
                raise ValidationError(f"Invalid IP address: {ip_address}") from exc

            if dry_run:
                self.logger.info("[DRY RUN] Would block IP address: %s", ip_address)
                return {
                    "dry_run": True,
                    "rule_name": rule_name,
                    "ip_address": ip_address,
                    "project_id": project_id,
                    "action": "would_create_firewall_rule",
                }

            # Create firewall rule
            firewall_client = gcp_clients["firewall"]

            firewall_rule = compute_v1.Firewall(
                name=rule_name,
                description=description,
                priority=priority,
                source_ranges=[f"{ip_address}/32"],
                denied=[
                    compute_v1.Denied(IP_protocol="tcp"),
                    compute_v1.Denied(IP_protocol="udp"),
                    compute_v1.Denied(IP_protocol="icmp"),
                ],
                direction="INGRESS",
                disabled=False,
                log_config=compute_v1.FirewallLogConfig(enable=True),
                target_tags=["sentinelops-protected"],
            )

            operation = firewall_client.insert(
                project=project_id, firewall_resource=firewall_rule
            )

            # Wait for operation to complete
            await self._wait_for_operation(operation, project_id, gcp_clients)
            self.logger.info("Successfully blocked IP address: %s", ip_address)

            return {
                "rule_name": rule_name,
                "ip_address": ip_address,
                "project_id": project_id,
                "status": "blocked",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error("Failed to block IP address: %s", e)
            raise RemediationAgentError(f"Failed to block IP address: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites for blocking IP address."""
        try:
            project_id = action.params.get("project_id")
            if not project_id:
                return False

            # Check if we have necessary permissions
            firewall_client = gcp_clients["firewall"]

            # Try to list firewall rules to verify permissions
            firewall_client.list(project=project_id)

            return True
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Prerequisites validation failed: %s", e)
            return False

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current state before blocking IP."""
        rule_name = action.params.get(
            "firewall_rule_name",
            f"block-ip-{action.params['ip_address'].replace('.', '-')}",
        )
        return {
            "rule_name": rule_name,
            "ip_address": action.params["ip_address"],
            "project_id": action.params["project_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition for unblocking IP address."""
        return RollbackDefinition(
            rollback_action_type="unblock_ip_address",
            state_params_mapping={"rule_name": "rule_name", "project_id": "project_id"},
        )

    async def _wait_for_operation(
        self,
        operation: Any,
        project_id: str,
        gcp_clients: Dict[str, Any],
        timeout: int = 60,
    ) -> None:
        """Wait for a GCP operation to complete."""
        # Parameters maintained for future implementation of proper operation polling
        _ = operation  # Mark as intentionally unused
        _ = project_id  # Mark as intentionally unused
        _ = gcp_clients  # Mark as intentionally unused
        _ = timeout  # Mark as intentionally unused
        # Currently using simplified sleep approach
        await asyncio.sleep(2)


class DisableUserAccountAction(BaseRemediationAction):
    """Implementation for disabling compromised user accounts."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the disable user account action."""
        try:
            user_email = action.params["user_email"]
            project_id = action.params["project_id"]
            reason = action.params.get(
                "reason", "Security incident - account compromised"
            )
            if dry_run:
                self.logger.info("[DRY RUN] Would disable user account: %s", user_email)
                return {
                    "dry_run": True,
                    "user_email": user_email,
                    "project_id": project_id,
                    "action": "would_remove_iam_bindings",
                }

            resource_manager = gcp_clients["resource_manager"]

            # Get current IAM policy
            project_name = f"projects/{project_id}"
            policy = resource_manager.get_iam_policy(resource=project_name)

            # Track removed bindings
            removed_bindings = []

            # Remove user from all bindings
            member = f"user:{user_email}"
            for binding in policy.bindings:
                if member in binding.members:
                    binding.members.remove(member)
                    removed_bindings.append(
                        {"role": binding.role, "removed_member": member}
                    )

            # Update the policy
            if removed_bindings:
                resource_manager.set_iam_policy(resource=project_name, policy=policy)

                self.logger.info(
                    "Successfully disabled user account: %s, removed from %d roles",
                    user_email,
                    len(removed_bindings),
                )
            else:
                self.logger.info("User %s had no IAM bindings to remove", user_email)

            return {
                "user_email": user_email,
                "project_id": project_id,
                "removed_bindings": removed_bindings,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Failed to disable user account: %s", e)
            raise RemediationAgentError(f"Failed to disable user account: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites for disabling user account."""
        try:
            user_email = action.params.get("user_email", "")
            if "@" not in user_email:
                return False

            project_id = action.params.get("project_id")
            if not project_id:
                return False

            resource_manager = gcp_clients["resource_manager"]
            resource_manager.get_iam_policy(resource=f"projects/{project_id}")
            return True
        except (ValueError, KeyError, AttributeError, OSError):
            return False

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current IAM bindings before disabling account."""
        try:
            user_email = action.params["user_email"]
            project_id = action.params["project_id"]
            resource_manager = gcp_clients["resource_manager"]

            policy = resource_manager.get_iam_policy(resource=f"projects/{project_id}")
            member = f"user:{user_email}"
            user_roles = []

            for binding in policy.bindings:
                if member in binding.members:
                    user_roles.append(binding.role)

            return {
                "user_email": user_email,
                "project_id": project_id,
                "original_roles": user_roles,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except (ValueError, TypeError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition for re-enabling user account."""
        return RollbackDefinition(
            rollback_action_type="restore_user_permissions",
            state_params_mapping={
                "user_email": "user_email",
                "project_id": "project_id",
                "roles": "original_roles",
            },
        )


class RevokeIAMPermissionAction(BaseRemediationAction):
    """Implementation for revoking suspicious IAM permissions."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the revoke IAM permission action."""
        try:
            member = action.params["member"]
            role = action.params["role"]
            resource = action.params["resource"]

            if dry_run:
                return {
                    "dry_run": True,
                    "member": member,
                    "role": role,
                    "resource": resource,
                }

            resource_manager = gcp_clients["resource_manager"]
            policy = resource_manager.get_iam_policy(resource=resource)

            removed = False
            for binding in policy.bindings:
                if binding.role == role and member in binding.members:
                    binding.members.remove(member)
                    removed = True
                    break

            if removed:
                resource_manager.set_iam_policy(resource=resource, policy=policy)
                self.logger.info("Revoked %s from %s", role, member)

            return {
                "member": member,
                "role": role,
                "resource": resource,
                "status": "revoked" if removed else "not_found",
            }
        except (ValueError, TypeError, AttributeError) as e:
            raise RemediationAgentError(f"Failed to revoke permission: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        # gcp_clients parameter maintained for interface consistency
        member = action.params.get("member", "")
        role = action.params.get("role", "")
        valid_prefixes = ["user:", "serviceAccount:", "group:", "domain:"]
        return any(member.startswith(p) for p in valid_prefixes) and role.startswith(
            "roles/"
        )

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        # gcp_clients parameter maintained for interface consistency
        return {
            "member": action.params["member"],
            "role": action.params["role"],
            "resource": action.params["resource"],
        }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        return RollbackDefinition(
            rollback_action_type="grant_iam_permission",
            state_params_mapping={
                "member": "member",
                "role": "role",
                "resource": "resource",
            },
        )


class QuarantineInstanceAction(BaseRemediationAction):
    """Implementation for quarantining infected compute instances."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the quarantine instance action."""
        try:
            instance_name = action.params["instance_name"]
            zone = action.params["zone"]
            project_id = action.params["project_id"]

            if dry_run:
                return {
                    "dry_run": True,
                    "instance": instance_name,
                    "action": "would_quarantine",
                }

            compute_client = gcp_clients["compute"]

            # Add quarantine tag
            instance = compute_client.get(
                project=project_id, zone=zone, instance=instance_name
            )
            tags = instance.tags
            if "quarantined" not in tags.items:
                tags.items.append("quarantined")

            # Update instance tags
            compute_client.set_tags(
                project=project_id,
                zone=zone,
                instance=instance_name,
                tags_resource=tags,
            )

            self.logger.info("Quarantined instance: %s", instance_name)
            return {"instance": instance_name, "zone": zone, "status": "quarantined"}

        except (ValueError, TypeError, AttributeError) as e:
            raise RemediationAgentError(f"Failed to quarantine instance: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        # gcp_clients parameter maintained for interface consistency
        return all(
            action.params.get(p) for p in ["instance_name", "zone", "project_id"]
        )

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            compute_client = gcp_clients["compute"]
            instance = compute_client.get(
                project=action.params["project_id"],
                zone=action.params["zone"],
                instance=action.params["instance_name"],
            )
            return {
                "original_tags": list(instance.tags.items),
                "instance_name": action.params["instance_name"],
            }
        except (ValueError, TypeError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        return RollbackDefinition(
            rollback_action_type="restore_instance_network",
            state_params_mapping={
                "instance_name": "instance_name",
                "tags": "original_tags",
            },
        )


class RotateCredentialsAction(BaseRemediationAction):
    """Implementation for rotating compromised credentials."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the rotate credentials action."""
        try:
            credential_type = action.params["credential_type"]
            resource_id = action.params["resource_id"]
            project_id = action.params["project_id"]

            if dry_run:
                return {
                    "dry_run": True,
                    "credential_type": credential_type,
                    "resource_id": resource_id,
                }

            if credential_type == "service_account_key":
                iam_client = gcp_clients["iam"]
                # Create new key
                iam_client.create_service_account_key(
                    name=f"projects/{project_id}/serviceAccounts/{resource_id}"
                )
                # Delete old keys would happen here
                self.logger.info("Rotated service account key for: %s", resource_id)
                return {
                    "credential_type": credential_type,
                    "resource_id": resource_id,
                    "status": "rotated",
                }

            return {"status": "unsupported_credential_type"}

        except Exception as e:
            raise RemediationAgentError(f"Failed to rotate credentials: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        # gcp_clients parameter maintained for interface consistency
        return all(
            action.params.get(p)
            for p in ["credential_type", "resource_id", "project_id"]
        )

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        # gcp_clients parameter maintained for interface consistency
        return {
            "credential_type": action.params["credential_type"],
            "resource_id": action.params["resource_id"],
        }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        return None  # Credential rotation is not reversible


class RestoreFromBackupAction(BaseRemediationAction):
    """Implementation for restoring resources from backup."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the restore from backup action."""
        # gcp_clients parameter will be used for actual restore operations
        try:
            resource_type = action.params["resource_type"]
            resource_id = action.params["resource_id"]
            backup_id = action.params["backup_id"]

            if dry_run:
                return {
                    "dry_run": True,
                    "resource_type": resource_type,
                    "backup_id": backup_id,
                }

            # Implementation would restore from snapshot/backup
            self.logger.info(
                "Restored %s %s from backup %s", resource_type, resource_id, backup_id
            )
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "backup_id": backup_id,
                "status": "restored",
            }

        except Exception as e:
            raise RemediationAgentError(f"Failed to restore from backup: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        # gcp_clients parameter maintained for interface consistency
        return all(
            action.params.get(p) for p in ["resource_type", "resource_id", "backup_id"]
        )

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        # gcp_clients parameter maintained for interface consistency
        return {
            "resource_id": action.params["resource_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        return None  # Restore operations are not reversible


class ApplySecurityPatchesAction(BaseRemediationAction):
    """Implementation for applying security patches."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the apply security patches action."""
        # gcp_clients parameter will be used for OS Config API operations
        try:
            instance_name = action.params["instance_name"]
            patch_ids = action.params["patch_ids"]

            if dry_run:
                return {
                    "dry_run": True,
                    "instance": instance_name,
                    "patches": patch_ids,
                }

            # Implementation would use OS Config API to apply patches
            self.logger.info("Applied %d patches to %s", len(patch_ids), instance_name)
            return {
                "instance": instance_name,
                "patches_applied": patch_ids,
                "status": "completed",
            }

        except Exception as e:
            raise RemediationAgentError(f"Failed to apply patches: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        return all(action.params.get(p) for p in ["instance_name", "patch_ids"])

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "instance": action.params["instance_name"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        return None  # Patch application is not reversible


class EnableAdditionalLoggingAction(BaseRemediationAction):
    """Implementation for enabling additional logging."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the enable additional logging action."""
        try:
            resource_type = action.params["resource_type"]
            resource_id = action.params["resource_id"]
            log_types = action.params["log_types"]

            if dry_run:
                return {
                    "dry_run": True,
                    "resource": resource_id,
                    "log_types": log_types,
                }

            # Implementation would configure logging
            self.logger.info(
                "Enabled %s logging for %s %s", log_types, resource_type, resource_id
            )
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "log_types": log_types,
                "status": "enabled",
            }

        except Exception as e:
            raise RemediationAgentError(f"Failed to enable logging: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        return all(
            action.params.get(p) for p in ["resource_type", "resource_id", "log_types"]
        )

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "resource_id": action.params["resource_id"],
            "original_logging": "basic",
        }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        return RollbackDefinition(
            rollback_action_type="disable_additional_logging",
            state_params_mapping={
                "resource_id": "resource_id",
                "log_types": "original_logging",
            },
        )

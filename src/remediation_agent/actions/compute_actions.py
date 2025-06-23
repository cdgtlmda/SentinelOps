"""
Google Cloud Compute Engine remediation actions.

This module contains implementations for Compute Engine-specific remediation actions.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.api_core import exceptions as gcp_exceptions
from google.cloud import compute_v1

from src.common.exceptions import RemediationAgentError
from src.common.models import RemediationAction
from src.remediation_agent.action_registry import (
    BaseRemediationAction,
    RollbackDefinition,
)


class ComputeEngineActionBase(BaseRemediationAction):
    """Base class for Compute Engine actions."""

    async def wait_for_operation(
        self,
        operation: Any,  # Can be Operation or ExtendedOperation
        project_id: str,
        zone: Optional[str] = None,
        region: Optional[str] = None,
        timeout: int = 300,
    ) -> None:
        """Wait for a Compute Engine operation to complete."""
        start_time = datetime.now(timezone.utc)

        operations_client: Any

        if zone:
            operations_client = compute_v1.ZoneOperationsClient()

            def get_operation() -> Any:
                return operations_client.get(
                    project=project_id, zone=zone, operation=operation.name
                )

        elif region:
            operations_client = compute_v1.RegionOperationsClient()

            def get_operation() -> Any:
                return operations_client.get(
                    project=project_id, region=region, operation=operation.name
                )

        else:
            operations_client = compute_v1.GlobalOperationsClient()

            def get_operation() -> Any:
                return operations_client.get(
                    project=project_id, operation=operation.name
                )

        while True:
            result = get_operation()

            if result.status == "DONE":
                if result.error:
                    error_messages = [error.message for error in result.error.errors]
                    raise RemediationAgentError(
                        f"Operation failed: {', '.join(error_messages)}"
                    )
                return

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed > timeout:
                raise RemediationAgentError(
                    f"Operation timed out after {timeout} seconds"
                )

            await asyncio.sleep(2)


class UpdateFirewallRuleAction(ComputeEngineActionBase):
    """Implementation for creating/updating firewall rules."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Create or update a firewall rule."""
        try:
            project_id = action.params["project_id"]
            rule_name = action.params["rule_name"]
            source_ranges = action.params.get("source_ranges", [])
            allowed = action.params.get("allowed", [])
            denied = action.params.get("denied", [])
            priority = action.params.get("priority", 1000)

            if dry_run:
                return {
                    "dry_run": True,
                    "rule_name": rule_name,
                    "action": "would_update_firewall_rule",
                }

            firewall_client = gcp_clients["firewall"]

            # Build firewall rule
            firewall_rule = compute_v1.Firewall(
                name=rule_name,
                description=action.params.get(
                    "description", "SentinelOps managed rule"
                ),
                priority=priority,
                source_ranges=source_ranges,
                direction=action.params.get("direction", "INGRESS"),
                disabled=False,
                log_config=compute_v1.FirewallLogConfig(enable=True),
            )

            # Add allowed rules
            if allowed:
                firewall_rule.allowed = [compute_v1.Allowed(**rule) for rule in allowed]

            # Add denied rules
            if denied:
                firewall_rule.denied = [compute_v1.Denied(**rule) for rule in denied]

            # Try to update existing rule first
            try:
                firewall_client.get(project=project_id, firewall=rule_name)
                operation = firewall_client.update(
                    project=project_id,
                    firewall=rule_name,
                    firewall_resource=firewall_rule,
                )
                action_taken = "updated"
            except gcp_exceptions.NotFound:
                # Create new rule
                operation = firewall_client.insert(
                    project=project_id, firewall_resource=firewall_rule
                )
                action_taken = "created"

            await self.wait_for_operation(operation, project_id)

            return {
                "rule_name": rule_name,
                "action": action_taken,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            raise RemediationAgentError(f"Failed to update firewall rule: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        # gcp_clients parameter maintained for interface consistency
        return all(action.params.get(p) for p in ["project_id", "rule_name"])

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current firewall rule state."""
        try:
            firewall_client = gcp_clients["firewall"]
            rule = firewall_client.get(
                project=action.params["project_id"], firewall=action.params["rule_name"]
            )

            return {
                "rule_name": rule.name,
                "source_ranges": list(rule.source_ranges),
                "allowed": (
                    [
                        {"IPProtocol": a.I_p_protocol, "ports": list(a.ports)}
                        for a in rule.allowed
                    ]
                    if rule.allowed
                    else []
                ),
                "denied": (
                    [
                        {"IPProtocol": d.I_p_protocol, "ports": list(d.ports)}
                        for d in rule.denied
                    ]
                    if rule.denied
                    else []
                ),
                "priority": rule.priority,
                "existed": True,
            }
        except gcp_exceptions.NotFound:
            return {"existed": False}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="restore_firewall_rule",
            state_params_mapping={
                "rule_name": "rule_name",
                "source_ranges": "source_ranges",
                "allowed": "allowed",
                "denied": "denied",
                "priority": "priority",
            },
        )


class StopInstanceAction(ComputeEngineActionBase):
    """Implementation for stopping compute instances."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Stop a compute instance."""
        try:
            instance_name = action.params["instance_name"]
            zone = action.params["zone"]
            project_id = action.params["project_id"]

            if dry_run:
                return {
                    "dry_run": True,
                    "instance": instance_name,
                    "action": "would_stop_instance",
                }

            compute_client = gcp_clients["compute"]

            # Check current instance status
            instance = compute_client.get(
                project=project_id, zone=zone, instance=instance_name
            )

            if instance.status == "TERMINATED":
                return {
                    "instance": instance_name,
                    "status": "already_stopped",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            # Stop the instance
            operation = compute_client.stop(
                project=project_id, zone=zone, instance=instance_name
            )

            await self.wait_for_operation(operation, project_id, zone=zone)

            return {
                "instance": instance_name,
                "zone": zone,
                "status": "stopped",
                "previous_status": instance.status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, TypeError, AttributeError) as e:
            raise RemediationAgentError(f"Failed to stop instance: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        # gcp_clients parameter maintained for interface consistency
        return all(
            action.params.get(p) for p in ["instance_name", "zone", "project_id"]
        )

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture instance state before stopping."""
        try:
            compute_client = gcp_clients["compute"]
            instance = compute_client.get(
                project=action.params["project_id"],
                zone=action.params["zone"],
                instance=action.params["instance_name"],
            )

            return {
                "instance_name": instance.name,
                "zone": action.params["zone"],
                "status": instance.status,
                "machine_type": instance.machine_type,
                "tags": list(instance.tags.items) if instance.tags else [],
            }
        except (ValueError, KeyError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="start_instance",
            state_params_mapping={"instance_name": "instance_name", "zone": "zone"},
        )


class SnapshotInstanceAction(ComputeEngineActionBase):
    """Implementation for creating instance snapshots."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Create a snapshot of instance disks."""
        try:
            instance_name = action.params["instance_name"]
            zone = action.params["zone"]
            project_id = action.params["project_id"]
            snapshot_prefix = action.params.get(
                "snapshot_prefix",
                f"sentinelops-{instance_name}-"
                f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            )

            if dry_run:
                return {
                    "dry_run": True,
                    "instance": instance_name,
                    "action": "would_create_snapshots",
                }

            compute_client = gcp_clients["compute"]
            snapshots_client = compute_v1.SnapshotsClient()

            # Get instance to find attached disks
            instance = compute_client.get(
                project=project_id, zone=zone, instance=instance_name
            )

            snapshots_created = []

            # Create snapshot for each disk
            for disk_info in instance.disks:
                disk_name = disk_info.source.split("/")[-1]
                snapshot_name = f"{snapshot_prefix}-{disk_name}"

                snapshot = compute_v1.Snapshot(
                    name=snapshot_name,
                    description=f"SentinelOps snapshot of {disk_name} from {instance_name}",
                    source_disk=disk_info.source,
                    labels={
                        "sentinelops": "true",
                        "instance": instance_name,
                        "incident_id": action.incident_id,
                    },
                )

                operation = snapshots_client.insert(
                    project=project_id, snapshot_resource=snapshot
                )

                await self.wait_for_operation(operation, project_id)

                snapshots_created.append({"disk": disk_name, "snapshot": snapshot_name})

            return {
                "instance": instance_name,
                "zone": zone,
                "snapshots_created": snapshots_created,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            raise RemediationAgentError(f"Failed to create snapshots: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        # gcp_clients parameter maintained for interface consistency
        return all(
            action.params.get(p) for p in ["instance_name", "zone", "project_id"]
        )

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture state before creating snapshots."""
        # gcp_clients parameter maintained for interface consistency
        return {
            "instance_name": action.params["instance_name"],
            "zone": action.params["zone"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        # Snapshots don't need rollback - they can be deleted if needed
        return None

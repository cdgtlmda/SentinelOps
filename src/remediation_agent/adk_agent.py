"""
Remediation Agent using Google ADK - PRODUCTION IMPLEMENTATION

This agent executes REAL remediation actions based on security incident analysis.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, cast
from enum import Enum

from google.adk.agents.run_config import RunConfig
from google.adk.tools import BaseTool, ToolContext
# Import removed - will use googleapiclient.discovery
from google.api_core import exceptions

from src.common.adk_agent_base import SentinelOpsBaseAgent
from src.tools.transfer_tools import (
    TransferToCommunicationAgentTool,
    TransferToOrchestratorAgentTool,
)

logger = logging.getLogger(__name__)


class ActionRiskLevel(Enum):
    """Risk levels for remediation actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BlockIPTool(BaseTool):
    """Production tool for blocking malicious IPs in firewall rules."""

    def __init__(self, compute_client: Any, project_id: str, dry_run: bool = True):
        """Initialize with Compute Engine client."""
        super().__init__(
            name="block_ip_tool",
            description="Block malicious IPs by updating firewall rules",
        )
        self.compute_client = compute_client
        self.project_id = project_id
        self.dry_run = dry_run

    async def execute(
        self, context: ToolContext, **kwargs: Any
    ) -> Dict[str, Any]:
        """Block specified IPs in GCP firewall rules."""
        ips_to_block = kwargs.get("ips", [])
        rule_name = kwargs.get("rule_name", "sentinelops-blocked-ips")
        priority = kwargs.get("priority", 1000)

        # Log context metadata if available
        if hasattr(context, 'metadata') and context.metadata:
            logger.info("Executing BlockIPTool with context: %s", context.metadata)

        try:
            if not ips_to_block:
                return {"status": "error", "error": "No IPs provided to block"}

            # Validate IPs
            import ipaddress

            validated_ips = []
            for ip in ips_to_block:
                try:
                    # Ensure CIDR notation
                    if "/" not in ip:
                        ip = f"{ip}/32"
                    ipaddress.ip_network(ip)
                    validated_ips.append(ip)
                except ValueError:
                    logger.warning("Invalid IP address: %s", ip)

            if not validated_ips:
                return {"status": "error", "error": "No valid IPs to block"}

            if self.dry_run:
                logger.info("[DRY RUN] Would block IPs: %s", validated_ips)
                return {
                    "status": "success",
                    "dry_run": True,
                    "action": "block_ip",
                    "ips_blocked": validated_ips,
                    "rule_name": rule_name,
                }

            # Check if rule exists
            try:
                existing_rule = self.compute_client.firewalls.get(
                    project=self.project_id, firewall=rule_name
                ).execute()

                # Update existing rule
                current_ranges = existing_rule.get("sourceRanges", [])
                updated_ranges = list(set(current_ranges + validated_ips))

                existing_rule["sourceRanges"] = updated_ranges

                operation = self.compute_client.firewalls.update(
                    project=self.project_id, firewall=rule_name, body=existing_rule
                ).execute()

                action_taken = "updated"

            except exceptions.NotFound:
                # Create new rule
                firewall_rule = {
                    "name": rule_name,
                    "description": "SentinelOps automated IP blocking rule",
                    "priority": priority,
                    "sourceRanges": validated_ips,
                    "denied": [{"IPProtocol": "all"}],
                    "direction": "INGRESS",
                    "logConfig": {"enable": True},
                }

                operation = self.compute_client.firewalls.insert(
                    project=self.project_id, body=firewall_rule
                ).execute()

                action_taken = "created"

            return {
                "status": "success",
                "action": "block_ip",
                "ips_blocked": validated_ips,
                "rule_name": rule_name,
                "action_taken": action_taken,
                "operation_id": operation.get("name"),
            }

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("Error blocking IPs: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class IsolateVMTool(BaseTool):
    """Production tool for isolating compromised VMs."""

    def __init__(self, compute_client: Any, project_id: str, dry_run: bool = True):
        """Initialize with Compute Engine client."""
        super().__init__(
            name="isolate_vm_tool",
            description="Isolate compromised VMs by modifying network tags",
        )
        self.compute_client = compute_client
        self.project_id = project_id
        self.dry_run = dry_run
        self.isolation_tag = "sentinelops-isolated"

    async def execute(
        self, context: ToolContext, **kwargs: Any
    ) -> Dict[str, Any]:
        """Isolate VM by applying restrictive network tags."""
        instance_name = kwargs.get("instance_name")
        zone = kwargs.get("zone")

        # Log context metadata if available
        if hasattr(context, 'metadata') and context.metadata:
            logger.info("Executing IsolateVMTool with context: %s", context.metadata)

        try:
            if not instance_name or not zone:
                return {
                    "status": "error",
                    "error": "Instance name and zone are required",
                }

            # Get instance details
            instance = self.compute_client.instances.get(
                project=self.project_id, zone=zone, instance=instance_name
            ).execute()

            current_tags = instance.get("tags", {}).get("items", [])

            if self.isolation_tag in current_tags:
                return {
                    "status": "success",
                    "message": "Instance already isolated",
                    "instance": instance_name,
                }

            if self.dry_run:
                logger.info("[DRY RUN] Would isolate instance: %s", instance_name)
                return {
                    "status": "success",
                    "dry_run": True,
                    "action": "isolate_vm",
                    "instance": instance_name,
                    "zone": zone,
                }

            # Add isolation tag
            updated_tags = current_tags + [self.isolation_tag]

            # Update instance tags
            tags_body = {
                "items": updated_tags,
                "fingerprint": instance.get("tags", {}).get("fingerprint"),
            }

            operation = self.compute_client.instances.setTags(
                project=self.project_id,
                zone=zone,
                instance=instance_name,
                body=tags_body,
            ).execute()

            # Create isolation firewall rule if needed
            await self._ensure_isolation_firewall_rule()

            return {
                "status": "success",
                "action": "isolate_vm",
                "instance": instance_name,
                "zone": zone,
                "isolation_tag": self.isolation_tag,
                "operation_id": operation.get("name"),
            }

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("Error isolating VM: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _ensure_isolation_firewall_rule(self) -> None:
        """Ensure isolation firewall rule exists."""
        rule_name = "sentinelops-vm-isolation"

        try:
            self.compute_client.firewalls.get(
                project=self.project_id, firewall=rule_name
            ).execute()
        except exceptions.NotFound:
            # Create isolation rule
            isolation_rule = {
                "name": rule_name,
                "description": "SentinelOps VM isolation rule - blocks all traffic",
                "priority": 100,
                "targetTags": [self.isolation_tag],
                "denied": [{"IPProtocol": "all"}],
                "direction": "INGRESS",
                "logConfig": {"enable": True},
            }

            self.compute_client.firewalls.insert(
                project=self.project_id, body=isolation_rule
            ).execute()


class RevokeCredentialsTool(BaseTool):
    """Production tool for revoking compromised credentials."""

    def __init__(self, iam_client: Any, project_id: str, dry_run: bool = True):
        """Initialize with IAM client."""
        super().__init__(
            name="revoke_credentials_tool",
            description="Revoke compromised service account credentials",
        )
        self.iam_client = iam_client
        self.project_id = project_id
        self.dry_run = dry_run

    async def execute(
        self, context: ToolContext, **kwargs: Any
    ) -> Dict[str, Any]:
        """Revoke service account keys or disable accounts."""
        service_account = kwargs.get("service_account")
        action = kwargs.get("action", "disable")  # disable or delete_keys

        # Log context metadata if available
        if hasattr(context, 'metadata') and context.metadata:
            logger.info("Executing RevokeCredentialsTool with context: %s", context.metadata)

        try:
            if not service_account:
                return {"status": "error", "error": "Service account email required"}

            # Ensure full service account name
            if "@" not in service_account:
                service_account = (
                    f"{service_account}@{self.project_id}.iam.gserviceaccount.com"
                )

            if self.dry_run:
                logger.info(
                    "[DRY RUN] Would %s service account: %s", action, service_account
                )
                return {
                    "status": "success",
                    "dry_run": True,
                    "action": "revoke_credentials",
                    "service_account": service_account,
                    "action_taken": action,
                }

            results: Dict[str, Any] = {
                "status": "success",
                "service_account": service_account,
                "actions_taken": [],
            }

            if action in ["disable", "both"]:
                # Disable service account
                request = (
                    self.iam_client.projects()
                    .serviceAccounts()
                    .disable(
                        name=f"projects/{self.project_id}/serviceAccounts/{service_account}"
                    )
                )
                request.execute()
                if isinstance(results["actions_taken"], list):
                    results["actions_taken"].append("disabled_account")

            if action in ["delete_keys", "both"]:
                # List and delete all keys
                keys_request = (
                    self.iam_client.projects()
                    .serviceAccounts()
                    .keys()
                    .list(
                        name=f"projects/{self.project_id}/serviceAccounts/{service_account}"
                    )
                )
                keys_response = keys_request.execute()

                deleted_keys = []
                for key in keys_response.get("keys", []):
                    # Skip system-managed keys
                    if key.get("keyType") == "USER_MANAGED":
                        key_name = key.get("name")
                        delete_request = (
                            self.iam_client.projects()
                            .serviceAccounts()
                            .keys()
                            .delete(name=key_name)
                        )
                        delete_request.execute()
                        deleted_keys.append(key_name.split("/")[-1])

                if isinstance(results["actions_taken"], list):
                    results["actions_taken"].append(f"deleted_{len(deleted_keys)}_keys")
                results["deleted_keys"] = deleted_keys

            return results

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("Error revoking credentials: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class UpdateFirewallTool(BaseTool):
    """Production tool for updating firewall rules."""

    def __init__(self, compute_client: Any, project_id: str, dry_run: bool = True):
        """Initialize with Compute Engine client."""
        super().__init__(
            name="update_firewall_tool",
            description="Update firewall rules to mitigate security risks",
        )
        self.compute_client = compute_client
        self.project_id = project_id
        self.dry_run = dry_run

    async def execute(
        self, context: ToolContext, **kwargs: Any
    ) -> Dict[str, Any]:
        """Update firewall rules based on security recommendations."""
        rule_name = kwargs.get("rule_name")
        action = kwargs.get("action")  # restrict, delete, modify
        modifications = kwargs.get("modifications", {})

        # Log context metadata if available
        if hasattr(context, 'metadata') and context.metadata:
            logger.info("Executing UpdateFirewallTool with context: %s", context.metadata)

        try:
            if not rule_name or not action:
                return {"status": "error", "error": "Rule name and action required"}

            # Get existing rule
            try:
                rule = self.compute_client.firewalls.get(
                    project=self.project_id, firewall=rule_name
                ).execute()
            except exceptions.NotFound:
                return {
                    "status": "error",
                    "error": f"Firewall rule {rule_name} not found",
                }

            if self.dry_run:
                logger.info("[DRY RUN] Would %s firewall rule: %s", action, rule_name)
                return {
                    "status": "success",
                    "dry_run": True,
                    "action": "update_firewall",
                    "rule_name": rule_name,
                    "action_taken": action,
                }

            if action == "delete":
                # Delete the rule
                operation = self.compute_client.firewalls.delete(
                    project=self.project_id, firewall=rule_name
                ).execute()

                return {
                    "status": "success",
                    "action": "update_firewall",
                    "rule_name": rule_name,
                    "action_taken": "deleted",
                    "operation_id": operation.get("name"),
                }

            elif action == "restrict":
                # Make rule more restrictive
                if "0.0.0.0/0" in rule.get("sourceRanges", []):
                    # Replace with more specific ranges
                    rule["sourceRanges"] = modifications.get(
                        "sourceRanges", ["10.0.0.0/8"]
                    )

                # Reduce allowed ports if any
                if rule.get("allowed"):
                    for allowed in rule["allowed"]:
                        if allowed.get("ports") is None:  # All ports allowed
                            allowed["ports"] = modifications.get("ports", ["443", "80"])

            elif action == "modify":
                # Apply specific modifications
                for key, value in modifications.items():
                    if key in rule:
                        rule[key] = value

            # Update the rule
            operation = self.compute_client.firewalls.update(
                project=self.project_id, firewall=rule_name, body=rule
            ).execute()

            return {
                "status": "success",
                "action": "update_firewall",
                "rule_name": rule_name,
                "action_taken": action,
                "modifications": modifications,
                "operation_id": operation.get("name"),
            }

        except (exceptions.GoogleAPICallError, ValueError, RuntimeError) as e:
            logger.error("Error updating firewall: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}


class RemediationAgent(SentinelOpsBaseAgent):
    """Production ADK Remediation Agent for executing security remediation actions."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Remediation Agent with production configuration."""
        # Extract configuration - use object.__setattr__ to bypass Pydantic validation
        # Note: project_id is available via inherited property, no need to set it
        object.__setattr__(self, "dry_run", config.get("dry_run_mode", True))
        object.__setattr__(self, "approval_required", config.get("approval_required", True))
        object.__setattr__(self, "auto_approve_low_risk", config.get("auto_approve_low_risk", True))
        object.__setattr__(self, "max_concurrent_actions", config.get("max_concurrent_actions", 5))

        # Initialize GCP clients - using the REST API discovery clients
        import googleapiclient.discovery
        compute_client = googleapiclient.discovery.build('compute', 'v1')
        iam_client = googleapiclient.discovery.build('iam', 'v1')

        # Initialize production tools
        tools = [
            BlockIPTool(compute_client, self.project_id, getattr(self, 'dry_run')),
            IsolateVMTool(compute_client, self.project_id, getattr(self, 'dry_run')),
            RevokeCredentialsTool(iam_client, self.project_id, getattr(self, 'dry_run')),
            UpdateFirewallTool(compute_client, self.project_id, getattr(self, 'dry_run')),
            TransferToCommunicationAgentTool(),
            TransferToOrchestratorAgentTool(),
        ]

        # Initialize base agent
        super().__init__(
            name="remediation_agent",
            description="Production security remediation agent with safety controls",
            config=config,
            model="gemini-pro",
            tools=tools,
        )

        # Track active remediations - use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, "active_remediations", set())
        object.__setattr__(self, "remediation_history", [])

    async def run(
        self,
        context: Optional[Any] = None,
        config: Optional[RunConfig] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the production remediation workflow."""
        try:
            # Handle incoming transfer
            remediation_request = None
            if context and hasattr(context, "data") and context.data:
                transfer_data = context.data
                remediation_request = transfer_data.get("results", {})
            elif kwargs.get("remediation_request"):
                remediation_request = kwargs["remediation_request"]

            if not remediation_request:
                return {"status": "error", "error": "No remediation request provided"}

            # Execute remediation
            return await self._execute_remediation(remediation_request, context, config)

        except (ValueError, RuntimeError, AttributeError) as e:
            logger.error("Error in remediation agent: %s", e, exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _execute_remediation(
        self, request: Dict[str, Any], context: Any, _config: Optional[RunConfig]
    ) -> Dict[str, Any]:
        """Execute remediation actions based on analysis recommendations."""
        remediation_results: Dict[str, Any] = {
            "status": "success",
            "incident_id": request.get("incident_id"),
            "remediation_id": f"rem_{datetime.utcnow().timestamp()}",
            "start_time": datetime.utcnow().isoformat(),
            "actions_executed": [],
            "actions_skipped": [],
            "errors": [],
        }

        try:
            # Create tool context - ToolContext requires invocation_context parameter
            if isinstance(context, ToolContext):
                tool_context = context
            else:
                # Create a default invocation context
                from google.adk.agents.invocation_context import InvocationContext
                # Create a minimal InvocationContext for tool execution
                default_invocation_context = InvocationContext(
                    session_service=None,  # type: ignore
                    invocation_id="default",
                    agent=self,
                    session=None  # type: ignore
                )
                tool_context = ToolContext(invocation_context=default_invocation_context)

            # Extract recommendations
            recommendations = request.get("recommendations", [])
            auto_approve = request.get("auto_approve", False)
            incident_metadata = request.get("analysis", {}).get("impact_analysis", {})

            # Validate concurrent action limit
            if len(getattr(self, 'active_remediations')) >= getattr(self, 'max_concurrent_actions'):
                remediation_results["status"] = "throttled"
                remediation_results["error"] = "Maximum concurrent remediations reached"
                return remediation_results

            # Track this remediation
            remediation_id = remediation_results["remediation_id"]
            getattr(self, 'active_remediations').add(remediation_id)

            try:
                # Process each recommendation
                for rec in recommendations:
                    action = rec.get("action", "")
                    priority = rec.get("priority", "medium")
                    automation_possible = rec.get("automation_possible", False)

                    if not automation_possible:
                        remediation_results["actions_skipped"].append(
                            {"action": action, "reason": "Manual intervention required"}
                        )
                        continue

                    # Determine risk level
                    risk_level = self._assess_action_risk(action, priority)

                    # Check approval requirements
                    needs_approval = self._needs_approval(risk_level, auto_approve)

                    if needs_approval and not auto_approve:
                        remediation_results["actions_skipped"].append(
                            {
                                "action": action,
                                "reason": "Approval required",
                                "risk_level": risk_level.value,
                            }
                        )

                        # Notify for approval
                        await self._request_approval(
                            action, risk_level, incident_metadata, tool_context
                        )
                        continue

                    # Execute the action
                    action_result = await self._execute_action(
                        action, incident_metadata, tool_context
                    )

                    if action_result.get("status") == "success":
                        remediation_results["actions_executed"].append(
                            {
                                "action": action,
                                "result": action_result,
                                "risk_level": risk_level.value,
                                "executed_at": datetime.utcnow().isoformat(),
                            }
                        )
                    else:
                        remediation_results["errors"].append(
                            {
                                "action": action,
                                "error": action_result.get("error", "Unknown error"),
                            }
                        )

                # Update remediation status
                if remediation_results["errors"]:
                    remediation_results["status"] = "partial"
                elif not remediation_results["actions_executed"]:
                    remediation_results["status"] = "no_actions"

                # Report results back to orchestrator
                orchestrator_tool = self.tools[5]  # TransferToOrchestratorAgentTool
                if hasattr(orchestrator_tool, 'execute'):
                    await orchestrator_tool.execute(
                        tool_context,
                        incident_id=request.get("incident_id"),
                        workflow_stage="remediation_complete",
                        results=remediation_results,
                    )

                # Send notification if critical actions were taken
                if any(
                    a["risk_level"] in ["high", "critical"]
                    for a in remediation_results["actions_executed"]
                ):
                    comm_tool = self.tools[4]  # TransferToCommunicationAgentTool
                    if hasattr(comm_tool, 'execute'):
                        await comm_tool.execute(
                            tool_context,
                            incident_id=request.get("incident_id"),
                            workflow_stage="remediation_notification",
                            results={
                                "actions_taken": remediation_results["actions_executed"],
                                "priority": "high",
                            },
                        )

            finally:
                # Remove from active remediations
                getattr(self, 'active_remediations').discard(remediation_id)

                # Add to history
                getattr(self, 'remediation_history').append(
                    {
                        "id": remediation_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "actions": len(remediation_results["actions_executed"]),
                        "status": remediation_results["status"],
                    }
                )

            remediation_results["end_time"] = datetime.utcnow().isoformat()
            remediation_results["duration_seconds"] = (
                datetime.utcnow()
                - datetime.fromisoformat(remediation_results["start_time"])
            ).total_seconds()

            logger.info(
                "Remediation complete: %d actions executed, %d skipped",
                len(remediation_results["actions_executed"]),
                len(remediation_results["actions_skipped"]),
            )

            return remediation_results

        except (ValueError, RuntimeError, AttributeError) as e:
            logger.error("Error during remediation execution: %s", e, exc_info=True)
            remediation_results["status"] = "error"
            remediation_results["error"] = str(e)
            return remediation_results

    def _assess_action_risk(self, action: str, priority: str) -> ActionRiskLevel:
        """Assess the risk level of a remediation action."""
        # High risk actions
        high_risk_keywords = ["delete", "destroy", "terminate", "disable", "revoke"]

        # Critical risk actions
        critical_risk_keywords = ["production", "critical", "all"]

        action_lower = action.lower()
        # Check for critical risk
        if any(keyword in action_lower for keyword in critical_risk_keywords):
            return ActionRiskLevel.CRITICAL

        # Check for high risk
        if any(keyword in action_lower for keyword in high_risk_keywords):
            return ActionRiskLevel.HIGH

        # Use priority as fallback
        if priority == "critical":
            return ActionRiskLevel.HIGH
        elif priority == "high":
            return ActionRiskLevel.MEDIUM
        else:
            return ActionRiskLevel.LOW

    def _needs_approval(self, risk_level: ActionRiskLevel, auto_approve: bool) -> bool:
        """Determine if an action needs approval."""
        if not getattr(self, 'approval_required'):
            return False

        if auto_approve:
            return False

        if getattr(self, 'auto_approve_low_risk') and risk_level == ActionRiskLevel.LOW:
            return False

        return True

    async def _execute_action(
        self, action: str, metadata: Dict[str, Any], context: ToolContext
    ) -> Dict[str, Any]:
        """Execute a specific remediation action."""
        action_lower = action.lower()

        # Map actions to tools
        if "block" in action_lower and "ip" in action_lower:
            # Extract IPs from metadata
            source_ip = metadata.get("source_ip", "")
            if source_ip and source_ip != "unknown":
                tool = self.tools[0]  # BlockIPTool
                if hasattr(tool, 'execute'):
                    result = await tool.execute(context, ips=[source_ip])
                    return cast(Dict[str, Any], result)
                return {"status": "error", "error": "Tool execute method not found"}

        elif "isolate" in action_lower and (
            "vm" in action_lower or "instance" in action_lower
        ):
            # Extract instance info
            affected_resources = metadata.get("affected_resources", [])
            for resource in affected_resources:
                if "compute.googleapis.com/instances" in resource:
                    # Parse instance details
                    parts = resource.split("/")
                    if len(parts) >= 4:
                        zone = parts[-3]
                        instance = parts[-1]
                        tool = self.tools[1]  # IsolateVMTool
                        if hasattr(tool, 'execute'):
                            result = await tool.execute(
                                context, instance_name=instance, zone=zone
                            )
                            return cast(Dict[str, Any], result)
                        return {"status": "error", "error": "Tool execute method not found"}

        elif "revoke" in action_lower or "disable" in action_lower:
            # Extract service account
            actor = metadata.get("actor", "")
            if actor and "@" in actor:
                tool = self.tools[2]  # RevokeCredentialsTool
                if hasattr(tool, 'execute'):
                    result = await tool.execute(
                        context, service_account=actor, action="disable"
                    )
                    return cast(Dict[str, Any], result)
                return {"status": "error", "error": "Tool execute method not found"}

        elif "firewall" in action_lower:
            # Update firewall rules
            tool = self.tools[3]  # UpdateFirewallTool
            if hasattr(tool, 'execute'):
                result = await tool.execute(
                    context,
                    rule_name="default-allow-internal",
                    action="restrict",
                    modifications={"sourceRanges": ["10.0.0.0/8"]},
                )
                return cast(Dict[str, Any], result)
            return {"status": "error", "error": "Tool execute method not found"}

        return {
            "status": "error",
            "error": f"No tool mapping found for action: {action}",
        }

    async def _request_approval(
        self,
        action: str,
        risk_level: ActionRiskLevel,
        metadata: Dict[str, Any],
        context: ToolContext,
    ) -> None:
        """Request approval for high-risk actions."""
        comm_tool = self.tools[4]  # TransferToCommunicationAgentTool

        if hasattr(comm_tool, 'execute'):
            await comm_tool.execute(
                context,
                incident_id=metadata.get("incident_id"),
                workflow_stage="approval_request",
                results={
                    "action": action,
                    "risk_level": risk_level.value,
                    "metadata": metadata,
                    "channels": ["slack", "email"],
                },
            )

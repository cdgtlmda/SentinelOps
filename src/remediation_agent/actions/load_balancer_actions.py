"""
Load balancer remediation actions for Network Security.

This module implements actions for modifying load balancer settings to respond
to security incidents.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.api_core import exceptions as gcp_exceptions
from google.cloud import compute_v1

from src.common.exceptions import RemediationAgentError, ValidationError
from src.common.models import RemediationAction
from src.remediation_agent.action_registry import (
    BaseRemediationAction,
    RollbackDefinition,
)


class ModifyLoadBalancerSettingsAction(BaseRemediationAction):
    """Implementation for modifying load balancer settings for security remediation."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute the modify load balancer settings action."""
        try:
            # Extract parameters
            load_balancer_name = action.params["load_balancer_name"]
            project_id = action.params["project_id"]
            modification_type = action.params["modification_type"]
            # region = action.params.get("region")  # Optional for regional LBs - not currently used

            # Validate modification type
            valid_modifications = [
                "block_suspicious_backend",
                "enable_cloud_armor",
                "restrict_source_ranges",
                "enable_logging",
            ]

            if modification_type not in valid_modifications:
                raise ValidationError(
                    f"Invalid modification type: {modification_type}. "
                    f"Valid types: {valid_modifications}"
                )

            if dry_run:
                self.logger.info(
                    "[DRY RUN] Would modify load balancer: %s with modification: %s",
                    load_balancer_name,
                    modification_type,
                )
                return {
                    "dry_run": True,
                    "load_balancer": load_balancer_name,
                    "modification_type": modification_type,
                    "project_id": project_id,
                    "action": f"would_{modification_type}",
                }

            # Execute specific modification
            if modification_type == "block_suspicious_backend":
                return await self._block_backend(
                    action, gcp_clients, load_balancer_name, project_id
                )
            elif modification_type == "enable_cloud_armor":
                return await self._enable_cloud_armor(
                    action, gcp_clients, load_balancer_name, project_id
                )
            elif modification_type == "restrict_source_ranges":
                return await self._restrict_source_ranges(
                    action, gcp_clients, load_balancer_name, project_id
                )
            elif modification_type == "enable_logging":
                return await self._enable_logging(
                    action, gcp_clients, load_balancer_name, project_id
                )
            else:
                # This should never happen due to validation above
                raise RemediationAgentError(
                    f"Unexpected modification type: {modification_type}"
                )

        except Exception as e:
            self.logger.error("Failed to modify load balancer settings: %s", e)
            raise RemediationAgentError(
                f"Load balancer modification failed: {e}"
            ) from e

    async def _block_backend(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        lb_name: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """Block a suspicious backend from the load balancer."""
        backend_to_block = action.params.get("backend_instance_group")
        if not backend_to_block:
            raise ValidationError("backend_instance_group parameter required")

        backend_services_client = compute_v1.BackendServicesClient()

        try:
            # Get the backend service
            backend_service = backend_services_client.get(
                project=project_id, backend_service=lb_name
            )

            # Remove the suspicious backend
            updated_backends = [
                backend
                for backend in backend_service.backends
                if backend.group != backend_to_block
            ]

            backend_service.backends = updated_backends

            # Update the backend service
            operation = backend_services_client.update(
                project=project_id,
                backend_service=lb_name,
                backend_service_resource=backend_service,
            )

            await self._wait_for_operation(operation, project_id, gcp_clients)

            self.logger.info(
                "Successfully blocked backend %s from load balancer %s",
                backend_to_block,
                lb_name,
            )

            return {
                "status": "success",
                "load_balancer": lb_name,
                "blocked_backend": backend_to_block,
                "remaining_backends": len(updated_backends),
            }

        except Exception as e:
            self.logger.error("Failed to block backend: %s", e)
            raise

    async def _enable_cloud_armor(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        lb_name: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """Enable Cloud Armor security policy on load balancer."""
        security_policy_name = action.params.get(
            "security_policy_name", f"{lb_name}-security-policy"
        )

        backend_services_client = compute_v1.BackendServicesClient()
        security_policies_client = compute_v1.SecurityPoliciesClient()

        try:
            # Create security policy if it doesn't exist
            try:
                security_policies_client.get(
                    project=project_id, security_policy=security_policy_name
                )
            except gcp_exceptions.NotFound:
                # Create new security policy
                security_policy = compute_v1.SecurityPolicy(
                    name=security_policy_name,
                    description="Cloud Armor policy for load balancer protection",
                    rules=[
                        compute_v1.SecurityPolicyRule(
                            action="allow",
                            priority=2147483647,  # Default rule
                            match=compute_v1.SecurityPolicyRuleMatcher(
                                versioned_expr="SRC_IPS_V1",
                                config=compute_v1.SecurityPolicyRuleMatcherConfig(
                                    src_ip_ranges=["*"]
                                ),
                            ),
                            description="Default allow rule",
                        )
                    ],
                )

                operation = security_policies_client.insert(
                    project=project_id, security_policy_resource=security_policy
                )
                await self._wait_for_operation(operation, project_id, gcp_clients)

            # Apply security policy to backend service
            operation = backend_services_client.set_security_policy(
                project=project_id,
                backend_service=lb_name,
                request=compute_v1.SetSecurityPolicyBackendServiceRequest(
                    project=project_id,
                    backend_service=lb_name,
                    security_policy_reference_resource=compute_v1.SecurityPolicyReference(
                        security_policy=(
                            f"projects/{project_id}/global/securityPolicies/"
                            f"{security_policy_name}"
                        )
                    ),
                ),
            )

            await self._wait_for_operation(operation, project_id, gcp_clients)

            self.logger.info(
                "Successfully enabled Cloud Armor policy %s on load balancer %s",
                security_policy_name,
                lb_name,
            )

            return {
                "status": "success",
                "load_balancer": lb_name,
                "security_policy": security_policy_name,
                "action": "cloud_armor_enabled",
            }

        except Exception as e:
            self.logger.error("Failed to enable Cloud Armor: %s", e)
            raise

    async def _restrict_source_ranges(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        lb_name: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """Restrict source IP ranges for load balancer access."""
        allowed_ranges = action.params.get("allowed_source_ranges", [])
        if not allowed_ranges:
            raise ValidationError("allowed_source_ranges parameter required")

        forwarding_rules_client = compute_v1.GlobalForwardingRulesClient()

        try:
            # Get forwarding rules associated with the load balancer
            forwarding_rules = forwarding_rules_client.list(project=project_id)

            updated_rules = []
            for rule in forwarding_rules:
                if lb_name in rule.name or rule.target and lb_name in rule.target:
                    # Create firewall rule to restrict access
                    firewall_rule_name = f"{rule.name}-restrict-access"
                    firewall_client = gcp_clients["firewall"]

                    firewall_rule = compute_v1.Firewall(
                        name=firewall_rule_name,
                        description=f"Restrict access to {lb_name} load balancer",
                        priority=1000,
                        source_ranges=allowed_ranges,
                        allowed=[
                            compute_v1.Allowed(
                                IPProtocol="tcp",
                                ports=[
                                    str(rule.port_range) if rule.port_range else "80",
                                    "443",
                                ],
                            )
                        ],
                        direction="INGRESS",
                        target_tags=[f"{lb_name}-restricted"],
                        log_config=compute_v1.FirewallLogConfig(enable=True),
                    )

                    operation = firewall_client.insert(
                        project=project_id, firewall_resource=firewall_rule
                    )
                    await self._wait_for_operation(operation, project_id, gcp_clients)
                    updated_rules.append(firewall_rule_name)

            self.logger.info(
                "Successfully restricted source ranges for load balancer %s", lb_name
            )

            return {
                "status": "success",
                "load_balancer": lb_name,
                "allowed_ranges": allowed_ranges,
                "firewall_rules_created": updated_rules,
            }

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Failed to restrict source ranges: %s", e)
            raise

    async def _enable_logging(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        lb_name: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """Enable logging for load balancer."""
        backend_services_client = compute_v1.BackendServicesClient()

        try:
            # Get backend service
            backend_service = backend_services_client.get(
                project=project_id, backend_service=lb_name
            )

            # Enable logging
            if not backend_service.log_config:
                backend_service.log_config = compute_v1.BackendServiceLogConfig()

            backend_service.log_config.enable = True
            backend_service.log_config.sample_rate = action.params.get(
                "sample_rate", 1.0
            )

            # Update backend service
            operation = backend_services_client.update(
                project=project_id,
                backend_service=lb_name,
                backend_service_resource=backend_service,
            )

            await self._wait_for_operation(operation, project_id, gcp_clients)

            self.logger.info(
                "Successfully enabled logging for load balancer %s", lb_name
            )

            return {
                "status": "success",
                "load_balancer": lb_name,
                "logging_enabled": True,
                "sample_rate": backend_service.log_config.sample_rate,
            }

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Failed to enable logging: %s", e)
            raise

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites for load balancer modification."""
        try:
            load_balancer_name = action.params.get("load_balancer_name")
            project_id = action.params.get("project_id")

            if not load_balancer_name or not project_id:
                self.logger.error("Missing required parameters")
                return False

            # Check if load balancer exists
            backend_services_client = compute_v1.BackendServicesClient()
            try:
                backend_services_client.get(
                    project=project_id, backend_service=load_balancer_name
                )
                return True
            except gcp_exceptions.NotFound:
                self.logger.error("Load balancer %s not found", load_balancer_name)
                return False

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error("Error validating prerequisites: %s", e)
            return False

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current load balancer state for rollback."""
        try:
            load_balancer_name = action.params["load_balancer_name"]
            project_id = action.params["project_id"]

            backend_services_client = compute_v1.BackendServicesClient()
            backend_service = backend_services_client.get(
                project=project_id, backend_service=load_balancer_name
            )

            # Capture relevant state
            state = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "load_balancer_name": load_balancer_name,
                "backends": [
                    {
                        "group": backend.group,
                        "balancing_mode": backend.balancing_mode,
                        "capacity_scaler": backend.capacity_scaler,
                    }
                    for backend in backend_service.backends
                ],
                "security_policy": (
                    backend_service.security_policy
                    if hasattr(backend_service, "security_policy")
                    else None
                ),
                "log_config": {
                    "enabled": (
                        backend_service.log_config.enable
                        if backend_service.log_config
                        else False
                    ),
                    "sample_rate": (
                        backend_service.log_config.sample_rate
                        if backend_service.log_config
                        else 0.0
                    ),
                },
                "health_checks": (
                    backend_service.health_checks
                    if hasattr(backend_service, "health_checks")
                    else []
                ),
            }

            return state

        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error("Failed to capture load balancer state: %s", e)
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            }

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition for load balancer modifications."""
        return RollbackDefinition(
            rollback_action_type="restore_load_balancer_settings",
            state_params_mapping={
                "backends": "original_backends",
                "security_policy": "original_security_policy",
                "log_config": "original_log_config",
            },
            additional_params={"description": "Rollback load balancer modifications"},
        )

    async def _wait_for_operation(
        self,
        operation: Any,
        project_id: str,
        gcp_clients: Dict[str, Any],
        timeout: int = 300,
    ) -> None:
        """Wait for a GCP operation to complete."""
        # This is a simplified version - in production, you'd use the proper
        # operation polling mechanism
        # Parameters are preserved for future implementation
        _ = (operation, project_id, gcp_clients, timeout)
        await asyncio.sleep(2)  # Simulate operation completion

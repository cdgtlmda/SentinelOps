"""
Google Cloud Network Security remediation actions.

This module contains implementations for network security-specific remediation actions.
"""

import ipaddress
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


class NetworkSecurityActionBase(BaseRemediationAction):
    """Base class for Network Security actions."""

    def validate_ip_range(self, ip_range: str) -> bool:
        """Validate an IP range in CIDR format."""
        try:
            ipaddress.ip_network(ip_range)
            return True
        except ValueError:
            return False

    def validate_port_range(self, port_range: str) -> bool:
        """Validate a port range (e.g., '80', '80-443')."""
        if "-" in port_range:
            parts = port_range.split("-")
            if len(parts) != 2:
                return False
            try:
                start, end = int(parts[0]), int(parts[1])
                return 0 <= start <= 65535 and 0 <= end <= 65535 and start <= end
            except ValueError:
                return False
        else:
            try:
                port = int(port_range)
                return 0 <= port <= 65535
            except ValueError:
                return False


class UpdateVPCFirewallRulesAction(NetworkSecurityActionBase):
    """Implementation for updating VPC firewall rules."""

    async def _restrict_source_ranges(
        self, firewall_client: Any, project_id: str, update: Dict[str, Any]
    ) -> Optional[str]:
        """Restrict source ranges for a firewall rule."""
        rule_name = update["rule_name"]
        new_source_ranges = update["source_ranges"]

        try:
            # Get existing rule
            rule = firewall_client.get(project=project_id, firewall=rule_name)
            # Update source ranges
            rule.source_ranges = new_source_ranges
            # Update the rule
            _ = firewall_client.update(
                project=project_id, firewall=rule_name, firewall_resource=rule
            )
            return f"Updated source ranges for {rule_name}"
        except gcp_exceptions.NotFound:
            self.logger.warning("Firewall rule %s not found", rule_name)
            return None

    async def _disable_rule(
        self, firewall_client: Any, project_id: str, update: Dict[str, Any]
    ) -> Optional[str]:
        """Disable a firewall rule."""
        rule_name = update["rule_name"]

        try:
            rule = firewall_client.get(project=project_id, firewall=rule_name)
            rule.disabled = True
            _ = firewall_client.update(
                project=project_id, firewall=rule_name, firewall_resource=rule
            )
            return f"Disabled firewall rule {rule_name}"
        except gcp_exceptions.NotFound:
            self.logger.warning("Firewall rule %s not found", rule_name)
            return None

    async def _create_deny_rule(
        self,
        firewall_client: Any,
        project_id: str,
        vpc_network: str,
        update: Dict[str, Any],
    ) -> str:
        """Create a new deny rule."""
        rule_name = update["rule_name"]
        source_ranges = update.get("source_ranges", ["0.0.0.0/0"])
        denied_ports = update.get("denied_ports", [])

        firewall_rule = compute_v1.Firewall(
            name=rule_name,
            description=f"SentinelOps security rule - {update.get('description', '')}",
            network=f"projects/{project_id}/global/networks/{vpc_network}",
            priority=update.get("priority", 1000),
            source_ranges=source_ranges,
            denied=[
                compute_v1.Denied(
                    IP_protocol=port_spec.get("protocol", "tcp"),
                    ports=port_spec.get("ports", []),
                )
                for port_spec in denied_ports
            ],
            direction="INGRESS",
            disabled=False,
            log_config=compute_v1.FirewallLogConfig(enable=True),
        )

        firewall_client.insert(project=project_id, firewall_resource=firewall_rule)
        return f"Created deny rule {rule_name}"

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Update VPC firewall rules."""
        try:
            project_id = action.params["project_id"]
            vpc_network = action.params.get("vpc_network", "default")
            rule_updates = action.params["rule_updates"]

            if dry_run:
                return {
                    "dry_run": True,
                    "vpc_network": vpc_network,
                    "updates_count": len(rule_updates),
                }

            firewall_client = gcp_clients["firewall"]
            changes_made = []

            for update in rule_updates:
                update_type = update["type"]
                result = None

                if update_type == "restrict_source_ranges":
                    result = await self._restrict_source_ranges(
                        firewall_client, project_id, update
                    )
                elif update_type == "disable_rule":
                    result = await self._disable_rule(
                        firewall_client, project_id, update
                    )
                elif update_type == "create_deny_rule":
                    result = await self._create_deny_rule(
                        firewall_client, project_id, vpc_network, update
                    )

                if result:
                    changes_made.append(result)

            return {
                "vpc_network": vpc_network,
                "changes_made": changes_made,
                "status": "updated" if changes_made else "no_changes",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(
                f"Failed to update VPC firewall rules: {e}"
            ) from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        if not all(action.params.get(p) for p in ["project_id", "rule_updates"]):
            return False

        # Validate rule updates
        for update in action.params["rule_updates"]:
            if "type" not in update:
                return False

            if update["type"] in ["restrict_source_ranges", "disable_rule"]:
                if "rule_name" not in update:
                    return False

            if update["type"] == "restrict_source_ranges":
                source_ranges = update.get("source_ranges", [])
                if not all(self.validate_ip_range(r) for r in source_ranges):
                    return False

        return True

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current firewall rules state."""
        state = {
            "project_id": action.params["project_id"],
            "vpc_network": action.params.get("vpc_network", "default"),
            "rules_state": [],
        }

        try:
            firewall_client = gcp_clients["firewall"]

            # Capture state of rules that will be modified
            for update in action.params["rule_updates"]:
                if "rule_name" in update:
                    try:
                        rule = firewall_client.get(
                            project=action.params["project_id"],
                            firewall=update["rule_name"],
                        )

                        state["rules_state"].append(
                            {
                                "rule_name": rule.name,
                                "source_ranges": list(rule.source_ranges),
                                "disabled": rule.disabled,
                                "priority": rule.priority,
                            }
                        )
                    except gcp_exceptions.NotFound:
                        pass

        except (ValueError, AttributeError):
            pass

        return state

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="restore_firewall_rules",
            state_params_mapping={
                "project_id": "project_id",
                "rules_state": "rules_state",
            },
        )


class ConfigureCloudArmorPolicyAction(NetworkSecurityActionBase):
    """Implementation for configuring Cloud Armor security policies."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Configure Cloud Armor security policy."""
        try:
            project_id = action.params["project_id"]
            policy_name = action.params["policy_name"]
            policy_action = action.params["policy_action"]

            if dry_run:
                return {
                    "dry_run": True,
                    "policy_name": policy_name,
                    "action": f"would_{policy_action}",
                }

            security_policies_client = compute_v1.SecurityPoliciesClient()

            if policy_action == "create_ip_blacklist":
                # Create a new security policy with IP blacklist rules
                ip_addresses = action.params.get("ip_addresses", [])

                # Create security policy
                security_policy = compute_v1.SecurityPolicy(
                    name=policy_name,
                    description="SentinelOps managed security policy",
                    rules=[
                        compute_v1.SecurityPolicyRule(
                            action="deny(403)",
                            priority=1000 + idx,
                            match=compute_v1.SecurityPolicyRuleMatcher(
                                src_ip_ranges=[ip]
                            ),
                            description=f"Block suspicious IP {ip}",
                        )
                        for idx, ip in enumerate(ip_addresses)
                    ]
                    + [
                        # Add default rule
                        compute_v1.SecurityPolicyRule(
                            action="allow",
                            priority=2147483647,  # Max priority (lowest precedence)
                            match=compute_v1.SecurityPolicyRuleMatcher(
                                src_ip_ranges=["*"]
                            ),
                            description="Default allow rule",
                        )
                    ],
                )

                _ = security_policies_client.insert(
                    project=project_id, security_policy_resource=security_policy
                )

                return {
                    "policy_name": policy_name,
                    "action": "created",
                    "ip_addresses_blocked": ip_addresses,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            elif policy_action == "add_rate_limiting":
                # Add rate limiting rules to existing policy
                rate_limit_threshold = action.params.get("rate_limit_threshold", 100)

                # Get existing policy
                policy = security_policies_client.get(
                    project=project_id, security_policy=policy_name
                )

                # Add rate limiting rule
                rate_limit_rule = compute_v1.SecurityPolicyRule(
                    action="rate_based_ban",
                    priority=900,
                    rate_limit_options=compute_v1.SecurityPolicyRuleRateLimitOptions(
                        rate_limit_threshold=compute_v1.SecurityPolicyRuleRateLimitOptionsThreshold(
                            count=rate_limit_threshold, interval_sec=60
                        ),
                        ban_duration_sec=600,  # 10 minute ban
                        conform_action="allow",
                        exceed_action="deny(429)",
                    ),
                    match=compute_v1.SecurityPolicyRuleMatcher(src_ip_ranges=["*"]),
                    description="SentinelOps rate limiting rule",
                )

                _ = security_policies_client.add_rule(
                    project=project_id,
                    security_policy=policy_name,
                    security_policy_rule_resource=rate_limit_rule,
                )

                return {
                    "policy_name": policy_name,
                    "action": "rate_limiting_added",
                    "threshold": rate_limit_threshold,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            elif policy_action == "enable_ddos_protection":
                # Enable adaptive protection (DDoS protection)
                policy = security_policies_client.get(
                    project=project_id, security_policy=policy_name
                )

                config = compute_v1.SecurityPolicyAdaptiveProtectionConfig(
                    layer_7_ddos_defense_config=(
                        compute_v1.SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfig(
                            enable=True, rule_visibility="STANDARD"
                        )
                    )
                )
                policy.adaptive_protection_config = config

                security_policies_client.patch(
                    project=project_id,
                    security_policy=policy_name,
                    security_policy_resource=policy,
                )

                return {
                    "policy_name": policy_name,
                    "action": "ddos_protection_enabled",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            else:
                raise RemediationAgentError(
                    f"Unsupported policy action: {policy_action}"
                )

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(
                f"Failed to configure Cloud Armor policy: {e}"
            ) from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        if not all(
            action.params.get(p) for p in ["project_id", "policy_name", "policy_action"]
        ):
            return False

        policy_action = action.params["policy_action"]
        valid_actions = [
            "create_ip_blacklist",
            "add_rate_limiting",
            "enable_ddos_protection",
        ]

        if policy_action not in valid_actions:
            return False

        if policy_action == "create_ip_blacklist":
            ip_addresses = action.params.get("ip_addresses", [])
            return all(self.validate_ip_range(ip) for ip in ip_addresses)

        return True

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current security policy state."""
        state = {
            "project_id": action.params["project_id"],
            "policy_name": action.params["policy_name"],
        }

        try:
            security_policies_client = compute_v1.SecurityPoliciesClient()

            policy = security_policies_client.get(
                project=action.params["project_id"],
                security_policy=action.params["policy_name"],
            )

            state["existed"] = True
            state["rules_count"] = len(policy.rules)

        except gcp_exceptions.NotFound:
            state["existed"] = False

        return state

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="remove_cloud_armor_policy",
            state_params_mapping={
                "project_id": "project_id",
                "policy_name": "policy_name",
            },
        )

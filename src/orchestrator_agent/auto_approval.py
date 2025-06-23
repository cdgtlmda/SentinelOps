"""
Auto-approval rules engine for remediation actions.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class ApprovalRule:
    """Defines an auto-approval rule."""

    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    action_patterns: List[str]
    max_risk_score: float
    enabled: bool = True

    def matches_action(self, action: Dict[str, Any]) -> bool:
        """Check if an action matches this rule's patterns."""
        action_type = action.get("action_type", "")

        for pattern in self.action_patterns:
            if re.match(pattern, action_type):
                return True
        return False

    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate if all conditions are met."""
        for condition_key, expected_value in self.conditions.items():
            actual_value = context.get(condition_key)

            if isinstance(expected_value, dict):
                # Handle complex conditions
                operator = expected_value.get("operator", "equals")
                value = expected_value.get("value")

                if operator == "equals" and actual_value != value:
                    return False
                elif (
                    operator == "less_than"
                    and actual_value is not None
                    and value is not None
                    and actual_value >= value
                ):
                    return False
                elif (
                    operator == "greater_than"
                    and actual_value is not None
                    and value is not None
                    and actual_value <= value
                ):
                    return False
                elif (
                    operator == "in"
                    and actual_value is not None
                    and value is not None
                    and actual_value not in value
                ):
                    return False
                elif (
                    operator == "contains"
                    and value is not None
                    and actual_value is not None
                    and value not in str(actual_value)
                ):
                    return False
            else:
                # Simple equality check
                if actual_value != expected_value:
                    return False

        return True


class AutoApprovalEngine:
    """Manages auto-approval rules for remediation actions."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the auto-approval engine."""
        self.config = config
        self.rules = self._load_rules()
        self.approval_history: List[Dict[str, Any]] = []

    def _load_rules(self) -> List[ApprovalRule]:
        """Load auto-approval rules from configuration."""
        rules = []

        # Default safe action rules
        rules.append(
            ApprovalRule(
                rule_id="safe_readonly",
                name="Safe Read-Only Actions",
                description="Auto-approve read-only diagnostic actions",
                conditions={
                    "severity": {"operator": "in", "value": ["low", "medium"]},
                    "confidence_score": {"operator": "greater_than", "value": 0.7},
                },
                action_patterns=["get_.*", "list_.*", "describe_.*", "show_.*"],
                max_risk_score=0.2,
            )
        )

        rules.append(
            ApprovalRule(
                rule_id="isolate_compromised",
                name="Isolate Compromised Resources",
                description="Auto-approve isolation of confirmed compromised resources",
                conditions={
                    "severity": {"operator": "in", "value": ["high", "critical"]},
                    "confidence_score": {"operator": "greater_than", "value": 0.85},
                    "threat_confirmed": True,
                },
                action_patterns=[
                    "isolate_instance",
                    "block_ip_address",
                    "disable_user_account",
                ],
                max_risk_score=0.5,
            )
        )

        rules.append(
            ApprovalRule(
                rule_id="revoke_suspicious_access",
                name="Revoke Suspicious Access",
                description="Auto-approve revoking access for suspicious activities",
                conditions={
                    "confidence_score": {"operator": "greater_than", "value": 0.8},
                    "attack_type": {
                        "operator": "in",
                        "value": ["unauthorized_access", "privilege_escalation"],
                    },
                },
                action_patterns=[
                    "revoke_iam_permissions",
                    "remove_ssh_key",
                    "expire_credentials",
                ],
                max_risk_score=0.4,
            )
        )

        # Load custom rules from config
        custom_rules = self.config.get("approval_rules", [])
        for rule_config in custom_rules:
            rules.append(ApprovalRule(**rule_config))

        return [rule for rule in rules if rule.enabled]

    def can_auto_approve(
        self, incident: Dict[str, Any], actions: List[Dict[str, Any]]
    ) -> tuple[bool, List[str]]:
        """
        Determine if actions can be auto-approved.

        Returns:
            (can_approve, reasons): Whether to auto-approve and list of reasons
        """
        reasons = []

        # Check if auto-approval is enabled
        if not self.config.get("auto_remediation", {}).get("enabled", False):
            return False, ["Auto-remediation is disabled"]

        # Build context for rule evaluation
        context = {
            "severity": incident.get("severity", "unknown"),
            "confidence_score": incident.get("analysis", {}).get("confidence_score", 0),
            "attack_type": incident.get("analysis", {}).get("attack_type"),
            "threat_confirmed": incident.get("analysis", {}).get(
                "threat_confirmed", False
            ),
            "incident_age_hours": self._get_incident_age_hours(incident),
            "previous_actions_count": len(incident.get("remediation_actions", [])),
        }

        # Check each action against rules
        approved_actions = []
        for action in actions:
            action_approved = False
            risk_score = self._calculate_risk_score(action, incident)

            for rule in self.rules:
                if rule.matches_action(action) and rule.evaluate_conditions(context):
                    if risk_score <= rule.max_risk_score:
                        action_approved = True
                        reasons.append(
                            f"Action '{action['action_type']}' approved by rule '{rule.name}'"
                        )
                        break
                    else:
                        reasons.append(
                            f"Action '{action['action_type']}' risk score {risk_score:.2f} "
                            f"exceeds rule limit {rule.max_risk_score}"
                        )

            if action_approved:
                approved_actions.append(action)
            else:
                reasons.append(
                    f"No matching auto-approval rule for action '{action['action_type']}'"
                )

        # All actions must be approved
        all_approved = len(approved_actions) == len(actions)

        if all_approved:
            # Record approval decision
            self._record_approval_decision(incident, actions, True, reasons)

        return all_approved, reasons

    def _calculate_risk_score(
        self, action: Dict[str, Any], incident: Dict[str, Any]
    ) -> float:
        """Calculate risk score for an action (0.0 to 1.0)."""
        base_score = 0.0

        # Action type risk
        high_risk_actions = ["delete_", "modify_production", "change_security"]
        medium_risk_actions = ["update_", "modify_", "change_"]
        low_risk_actions = ["isolate_", "block_", "disable_"]

        action_type = action.get("action_type", "")

        if any(action_type.startswith(prefix) for prefix in high_risk_actions):
            base_score += 0.7
        elif any(action_type.startswith(prefix) for prefix in medium_risk_actions):
            base_score += 0.4
        elif any(action_type.startswith(prefix) for prefix in low_risk_actions):
            base_score += 0.2
        else:
            base_score += 0.1

        # Resource criticality
        target_resource = action.get("target_resource", "")
        if "production" in target_resource.lower():
            base_score += 0.2
        elif "staging" in target_resource.lower():
            base_score += 0.1

        # Adjust based on confidence
        confidence = incident.get("analysis", {}).get("confidence_score", 0.5)
        base_score *= 2.0 - confidence  # Lower confidence increases risk

        return float(min(base_score, 1.0))

    def _get_incident_age_hours(self, incident: Dict[str, Any]) -> float:
        """Calculate how old the incident is in hours."""
        created_at = incident.get("created_at")
        if not created_at:
            return 0.0

        try:
            created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - created_time.replace(tzinfo=None)
            total_seconds = age.total_seconds()
            return float(total_seconds / 3600)
        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            print(f"Failed to calculate incident age: {e}")
            return 0.0

    def _record_approval_decision(
        self,
        incident: Dict[str, Any],
        actions: List[Dict[str, Any]],
        approved: bool,
        reasons: List[str],
    ) -> None:
        """Record an approval decision for audit purposes."""
        decision = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident_id": incident.get("incident_id"),
            "actions": [a.get("action_type") for a in actions],
            "approved": approved,
            "reasons": reasons,
            "rules_evaluated": len(self.rules),
        }

        self.approval_history.append(decision)

        # Keep only last 1000 decisions
        if len(self.approval_history) > 1000:
            self.approval_history = self.approval_history[-1000:]

        try:
            # Store decision in database
            # This is a placeholder and should be replaced with actual database storage logic
            print(f"Decision stored: {decision}")
        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            print(f"Failed to store decision: {e}")

    def get_approval_policy(self) -> Dict[str, Any]:
        """Get the current approval policy configuration."""
        return {
            "auto_approval_enabled": self.config.get("auto_remediation", {}).get(
                "enabled", False
            ),
            "rules_count": len(self.rules),
            "active_rules": [{"id": r.rule_id, "name": r.name} for r in self.rules],
            "recent_decisions": len(self.approval_history),
        }

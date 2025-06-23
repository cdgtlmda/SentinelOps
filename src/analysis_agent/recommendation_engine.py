"""
Recommendation engine for the Analysis Agent.

This module handles generating actionable remediation recommendations based on
incident analysis and attack patterns.
"""

import logging
from typing import Any, Dict, List, Optional

from src.common.models import SeverityLevel


class RecommendationEngine:
    """Generates prioritized remediation recommendations for security incidents."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize the recommendation engine.

        Args:
            logger: Logger instance for logging
        """
        self.logger = logger

        # Define recommendation templates for common incident types
        self.recommendation_templates = {
            "unauthorized_access": {
                "immediate_actions": [
                    "Disable the compromised user account immediately",
                    "Revoke all active sessions for the affected user",
                    "Reset credentials for the compromised account",
                    "Review and revoke any API keys or service account keys",
                ],
                "investigation_steps": [
                    "Review authentication logs for the past 30 days",
                    "Check for any privilege escalation attempts",
                    "Identify all resources accessed by the compromised account",
                    "Look for lateral movement to other accounts",
                ],
                "preventive_measures": [
                    "Enable multi-factor authentication (MFA) for all accounts",
                    "Implement conditional access policies",
                    "Review and tighten access permissions",
                    "Set up anomaly detection alerts for unusual login patterns",
                ],
            },
            "data_exfiltration": {
                "immediate_actions": [
                    "Block the source IP addresses at the firewall level",
                    "Disable the compromised service accounts",
                    "Revoke access to affected storage buckets or databases",
                    "Enable detailed audit logging on all data resources",
                ],
                "investigation_steps": [
                    "Identify all data accessed or downloaded",
                    "Review storage bucket access logs",
                    "Check for any data staging locations",
                    "Analyze network traffic for large data transfers",
                ],
                "preventive_measures": [
                    "Implement DLP (Data Loss Prevention) policies",
                    "Enable VPC Service Controls",
                    "Set up alerts for large data downloads",
                    "Encrypt sensitive data at rest and in transit",
                ],
            },
            "privilege_escalation": {
                "immediate_actions": [
                    "Revoke elevated permissions immediately",
                    "Disable the affected user or service account",
                    "Review and reset IAM policies to baseline",
                    "Enable break-glass account monitoring",
                ],
                "investigation_steps": [
                    "Audit all recent IAM changes",
                    "Review role bindings and custom roles",
                    "Check for persistence mechanisms",
                    "Identify the initial compromise vector",
                ],
                "preventive_measures": [
                    "Implement least privilege access principles",
                    "Enable IAM recommender for permission optimization",
                    "Set up alerts for privilege changes",
                    "Require approval workflows for sensitive permissions",
                ],
            },
            "malware_infection": {
                "immediate_actions": [
                    "Isolate affected systems from the network",
                    "Take snapshots of affected instances for forensics",
                    "Terminate compromised compute instances",
                    "Block malicious domains and IPs",
                ],
                "investigation_steps": [
                    "Scan all systems for indicators of compromise",
                    "Review process execution logs",
                    "Check for persistence mechanisms",
                    "Analyze network connections from affected systems",
                ],
                "preventive_measures": [
                    "Deploy endpoint detection and response (EDR) solutions",
                    "Enable OS Login for SSH access",
                    "Implement application whitelisting",
                    "Regular security patching schedule",
                ],
            },
            "account_compromise": {
                "immediate_actions": [
                    "Force password reset for affected accounts",
                    "Terminate all active sessions",
                    "Review and revoke OAuth tokens",
                    "Enable additional authentication factors",
                ],
                "investigation_steps": [
                    "Review login history and patterns",
                    "Check for unauthorized application access",
                    "Identify any data accessed or modified",
                    "Look for evidence of account selling or sharing",
                ],
                "preventive_measures": [
                    "Implement adaptive authentication",
                    "Enable impossible travel detection",
                    "Regular security awareness training",
                    "Implement password policies and rotation",
                ],
            },
            "ddos_attack": {
                "immediate_actions": [
                    "Enable Cloud Armor DDoS protection",
                    "Implement rate limiting on affected services",
                    "Scale up resources to handle load",
                    "Block source IPs showing malicious patterns",
                ],
                "investigation_steps": [
                    "Analyze traffic patterns and sources",
                    "Identify the attack vector (volumetric, protocol, application)",
                    "Review CDN and load balancer logs",
                    "Check for any data breach attempts during the attack",
                ],
                "preventive_measures": [
                    "Implement Cloud CDN for static content",
                    "Set up auto-scaling policies",
                    "Configure Cloud Armor security policies",
                    "Implement CAPTCHA for critical endpoints",
                ],
            },
            "configuration_drift": {
                "immediate_actions": [
                    "Revert unauthorized configuration changes",
                    "Lock down configuration management access",
                    "Enable configuration change alerts",
                    "Review recent terraform or deployment logs",
                ],
                "investigation_steps": [
                    "Compare current config with known-good baseline",
                    "Identify who made the changes and when",
                    "Check for any security implications",
                    "Review infrastructure as code repositories",
                ],
                "preventive_measures": [
                    "Implement Policy as Code validation",
                    "Use Config Validator for compliance",
                    "Enable Organization Policy constraints",
                    "Implement GitOps with approval workflows",
                ],
            },
        }

        # Define severity-based priority multipliers
        self.severity_multipliers = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.6,
            SeverityLevel.LOW: 0.4,
            SeverityLevel.INFORMATIONAL: 0.2,
        }

    def generate_recommendations(
        self,
        incident_type: str,
        attack_techniques: List[str],
        severity: SeverityLevel,
        correlation_results: Dict[str, Any],
        custom_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate prioritized recommendations based on incident analysis.

        Args:
            incident_type: Type of security incident
            attack_techniques: List of identified attack techniques
            severity: Incident severity level
            correlation_results: Results from event correlation
            custom_context: Additional context for customization

        Returns:
            Dictionary containing prioritized recommendations
        """
        recommendations: Dict[str, Any] = {
            "immediate_actions": [],
            "investigation_steps": [],
            "preventive_measures": [],
            "priority_score": 0.0,
            "estimated_time": {},
            "automation_possible": [],
        }

        # Get base recommendations from templates
        base_recommendations = self._get_template_recommendations(
            incident_type, attack_techniques
        )

        # Enhance with correlation insights
        enhanced_recommendations = self._enhance_with_correlation_insights(
            base_recommendations, correlation_results
        )

        # Add custom context-based recommendations
        if custom_context:
            enhanced_recommendations = self._add_context_specific_recommendations(
                enhanced_recommendations, custom_context
            )

        # Prioritize recommendations
        recommendations["immediate_actions"] = self._prioritize_actions(
            enhanced_recommendations.get("immediate_actions", []), severity
        )

        recommendations["investigation_steps"] = enhanced_recommendations.get(
            "investigation_steps", []
        )

        recommendations["preventive_measures"] = enhanced_recommendations.get(
            "preventive_measures", []
        )

        # Calculate priority score
        recommendations["priority_score"] = self._calculate_priority_score(
            severity, correlation_results
        )

        # Estimate time for actions
        recommendations["estimated_time"] = self._estimate_action_time(recommendations)

        # Identify automatable actions
        recommendations["automation_possible"] = self._identify_automatable_actions(
            recommendations["immediate_actions"]
        )

        self.logger.info(
            f"Generated recommendations for {incident_type} incident with "
            f"{len(recommendations['immediate_actions'])} immediate actions"
        )

        return recommendations

    def _get_template_recommendations(
        self, incident_type: str, attack_techniques: List[str]
    ) -> Dict[str, List[str]]:
        """Get base recommendations from templates."""
        recommendations: Dict[str, List[str]] = {
            "immediate_actions": [],
            "investigation_steps": [],
            "preventive_measures": [],
        }

        # Map attack techniques to incident types
        technique_mapping = {
            "unauthorized": "unauthorized_access",
            "exfiltration": "data_exfiltration",
            "privilege": "privilege_escalation",
            "malware": "malware_infection",
            "compromise": "account_compromise",
            "ddos": "ddos_attack",
            "configuration": "configuration_drift",
        }

        # Find matching templates
        matched_types = set()

        # Check incident type
        for key, value in technique_mapping.items():
            if key in incident_type.lower():
                matched_types.add(value)

        # Check attack techniques
        for technique in attack_techniques:
            for key, value in technique_mapping.items():
                if key in technique.lower():
                    matched_types.add(value)

        # Aggregate recommendations from all matched templates
        for template_key in matched_types:
            if template_key in self.recommendation_templates:
                template = self.recommendation_templates[template_key]
                recommendations["immediate_actions"].extend(
                    template.get("immediate_actions", [])
                )
                recommendations["investigation_steps"].extend(
                    template.get("investigation_steps", [])
                )
                recommendations["preventive_measures"].extend(
                    template.get("preventive_measures", [])
                )

        # Remove duplicates while preserving order
        for key in recommendations:
            recommendations[key] = list(dict.fromkeys(recommendations[key]))

        return recommendations

    def _enhance_with_correlation_insights(
        self,
        base_recommendations: Dict[str, List[str]],
        correlation_results: Dict[str, Any],
    ) -> Dict[str, List[str]]:
        """Enhance recommendations based on correlation insights."""
        enhanced = base_recommendations.copy()

        # Add recommendations based on suspicious actors
        suspicious_actors = correlation_results.get("actor_patterns", {}).get(
            "suspicious_actors", []
        )
        if suspicious_actors:
            for actor_info in suspicious_actors:
                actor = actor_info.get("actor", "unknown")
                enhanced["immediate_actions"].insert(
                    0, f"Immediately review and suspend account: {actor}"
                )
                enhanced["investigation_steps"].append(
                    f"Conduct detailed audit of all activities by user: {actor}"
                )

        # Add recommendations based on resource targeting
        targeted_resources = correlation_results.get("spatial_patterns", {}).get(
            "resource_targeting", {}
        )
        if targeted_resources:
            top_targets = list(targeted_resources.keys())[:3]
            for resource in top_targets:
                enhanced["immediate_actions"].append(
                    f"Review and restrict access to frequently targeted resource: {resource}"
                )

        # Add recommendations based on temporal patterns
        burst_periods = correlation_results.get("temporal_patterns", {}).get(
            "burst_periods", []
        )
        if burst_periods:
            enhanced["investigation_steps"].append(
                "Analyze activity during identified burst periods for attack patterns"
            )
            enhanced["preventive_measures"].append(
                "Implement rate limiting to prevent activity bursts"
            )

        # Add recommendations based on causal patterns
        cause_effect_pairs = correlation_results.get("causal_patterns", {}).get(
            "cause_effect_pairs", []
        )
        if cause_effect_pairs:
            enhanced["investigation_steps"].append(
                "Review identified cause-effect chains to understand attack progression"
            )

        return enhanced

    def _add_context_specific_recommendations(
        self, recommendations: Dict[str, List[str]], custom_context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Add recommendations based on custom context."""
        enhanced = recommendations.copy()

        # Add recommendations based on affected services
        affected_services = custom_context.get("affected_services", [])
        for service in affected_services:
            if "database" in service.lower():
                enhanced["immediate_actions"].append(
                    f"Review and audit database access logs for {service}"
                )
            elif "storage" in service.lower():
                enhanced["immediate_actions"].append(
                    f"Enable versioning and audit logs for {service}"
                )
            elif "compute" in service.lower():
                enhanced["immediate_actions"].append(
                    f"Review running processes and network connections on {service}"
                )

        # Add recommendations based on data sensitivity
        if custom_context.get("involves_sensitive_data", False):
            enhanced["immediate_actions"].insert(
                0, "Notify data protection officer and legal team immediately"
            )
            enhanced["investigation_steps"].insert(
                0, "Determine the full scope of sensitive data exposure"
            )

        return enhanced

    def _prioritize_actions(
        self, actions: List[str], severity: SeverityLevel
    ) -> List[str]:
        """Prioritize actions based on severity and impact."""
        # Define action priority keywords
        high_priority_keywords = [
            "immediately",
            "disable",
            "revoke",
            "block",
            "terminate",
            "isolate",
        ]
        medium_priority_keywords = ["review", "audit", "check", "enable", "configure"]

        # Score each action
        scored_actions = []
        for action in actions:
            score = 0.5  # Base score

            # Adjust based on keywords
            action_lower = action.lower()
            if any(keyword in action_lower for keyword in high_priority_keywords):
                score += 0.3
            elif any(keyword in action_lower for keyword in medium_priority_keywords):
                score += 0.1

            # Apply severity multiplier
            score *= self.severity_multipliers.get(severity, 0.5)

            scored_actions.append((score, action))

        # Sort by score (descending) and return actions
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        return [action for _, action in scored_actions]

    def _calculate_priority_score(
        self, severity: SeverityLevel, correlation_results: Dict[str, Any]
    ) -> float:
        """Calculate overall priority score for the recommendations."""
        base_score = self.severity_multipliers.get(severity, 0.5)

        # Adjust based on correlation scores
        correlation_scores = correlation_results.get("correlation_scores", {})
        overall_correlation = correlation_scores.get("overall_score", 0.5)

        # High correlation indicates more sophisticated attack
        priority_score: float = base_score * (1 + overall_correlation * 0.5)

        # Boost if suspicious actors identified
        if correlation_results.get("actor_patterns", {}).get("suspicious_actors"):
            priority_score *= 1.2

        # Ensure score is between 0 and 1
        return min(1.0, priority_score)

    def _estimate_action_time(self, recommendations: Dict[str, Any]) -> Dict[str, str]:
        """Estimate time required for different action categories."""
        estimates = {}

        # Immediate actions: typically 5-15 minutes each
        immediate_count = len(recommendations.get("immediate_actions", []))
        immediate_time = immediate_count * 10  # 10 minutes average per action
        estimates["immediate_actions"] = (
            f"{immediate_time}-{immediate_time * 1.5} minutes"
        )

        # Investigation: typically 1-4 hours
        investigation_count = len(recommendations.get("investigation_steps", []))
        investigation_time = max(
            60, investigation_count * 30
        )  # 30 min per step, min 1 hour
        estimates["investigation_steps"] = (
            f"{investigation_time // 60}-{investigation_time // 30} hours"
        )

        # Preventive measures: typically days to weeks
        preventive_count = len(recommendations.get("preventive_measures", []))
        if preventive_count > 0:
            estimates["preventive_measures"] = (
                f"{preventive_count}-{preventive_count * 2} days"
            )

        estimates["total_initial_response"] = f"{immediate_time + 60} minutes"

        return estimates

    def _identify_automatable_actions(self, actions: List[str]) -> List[Dict[str, str]]:
        """Identify which actions can be automated."""
        automatable = []

        # Define automation patterns
        automation_patterns = {
            "disable.*account": {
                "action_type": "account_disable",
                "gcp_api": "admin.googleapis.com",
                "complexity": "low",
            },
            "revoke.*session": {
                "action_type": "session_revocation",
                "gcp_api": "admin.googleapis.com",
                "complexity": "low",
            },
            "block.*ip": {
                "action_type": "firewall_rule",
                "gcp_api": "compute.googleapis.com",
                "complexity": "medium",
            },
            "terminate.*instance": {
                "action_type": "instance_termination",
                "gcp_api": "compute.googleapis.com",
                "complexity": "low",
            },
            "revoke.*permission": {
                "action_type": "iam_modification",
                "gcp_api": "iam.googleapis.com",
                "complexity": "medium",
            },
            "enable.*logging": {
                "action_type": "logging_configuration",
                "gcp_api": "logging.googleapis.com",
                "complexity": "low",
            },
        }

        for action in actions:
            action_lower = action.lower()
            for pattern, details in automation_patterns.items():
                if (
                    pattern in action_lower
                    or action_lower.find(pattern.replace(".*", " ")) != -1
                ):
                    automatable.append(
                        {
                            "action": action,
                            "automation_type": details["action_type"],
                            "required_api": details["gcp_api"],
                            "complexity": details["complexity"],
                        }
                    )
                    break

        return automatable

    def format_recommendations_for_display(  # noqa: C901
        self, recommendations: Dict[str, Any]
    ) -> str:
        """Format recommendations for human-readable display."""
        formatted = []

        # Header with priority
        priority = recommendations.get("priority_score", 0)
        priority_text = (
            "CRITICAL" if priority > 0.8 else "HIGH" if priority > 0.6 else "MEDIUM"
        )
        formatted.append(f"=== RECOMMENDATIONS (Priority: {priority_text}) ===\n")

        # Immediate actions
        if recommendations.get("immediate_actions"):
            formatted.append("IMMEDIATE ACTIONS REQUIRED:")
            for i, action in enumerate(recommendations["immediate_actions"], 1):
                formatted.append(f"  {i}. {action}")
            formatted.append("")

        # Time estimates
        if recommendations.get("estimated_time"):
            formatted.append("ESTIMATED RESPONSE TIME:")
            for category, time_est in recommendations["estimated_time"].items():
                formatted.append(
                    f"  - {category.replace('_', ' ').title()}: {time_est}"
                )
            formatted.append("")

        # Automation possibilities
        if recommendations.get("automation_possible"):
            formatted.append("AUTOMATABLE ACTIONS:")
            for auto in recommendations["automation_possible"]:
                formatted.append(
                    f"  - {auto['action']} "
                    f"[Type: {auto['automation_type']}, "
                    f"Complexity: {auto['complexity']}]"
                )
            formatted.append("")

        # Investigation steps
        if recommendations.get("investigation_steps"):
            formatted.append("INVESTIGATION STEPS:")
            for i, step in enumerate(recommendations["investigation_steps"], 1):
                formatted.append(f"  {i}. {step}")
            formatted.append("")

        # Preventive measures
        if recommendations.get("preventive_measures"):
            formatted.append("PREVENTIVE MEASURES (Long-term):")
            for i, measure in enumerate(recommendations["preventive_measures"], 1):
                formatted.append(f"  {i}. {measure}")

        return "\n".join(formatted)

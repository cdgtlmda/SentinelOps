"""
Analysis Agent integration for the Communication Agent.

Handles analysis results, risk assessments, and recommendation
notifications from the Analysis Agent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.communication_agent.formatting import MessageFormatter
from src.communication_agent.types import MessageType, NotificationPriority

if TYPE_CHECKING:
    from src.communication_agent.agent import CommunicationAgent
# pylint: disable=wrong-import-position
from src.utils.logging import get_logger

# pylint: enable=wrong-import-position

logger = get_logger(__name__)


class AnalysisAgentIntegration:
    """
    Integration between Analysis Agent and Communication Agent.

    Handles:
    - Analysis completion notifications
    - Risk assessment communication
    - Recommendation distribution
    - Threat intelligence updates
    """

    def __init__(
        self,
        communication_agent: "CommunicationAgent",
        formatter: Optional[MessageFormatter] = None,
    ):
        """
        Initialize Analysis Agent integration.

        Args:
            communication_agent: Communication agent instance
            formatter: Optional message formatter
        """
        self.comm_agent = communication_agent
        self.formatter = formatter or MessageFormatter()

        # Risk level to priority mapping
        self.risk_to_priority = {
            "critical": NotificationPriority.HIGH,
            "high": NotificationPriority.HIGH,
            "medium": NotificationPriority.MEDIUM,
            "low": NotificationPriority.LOW,
            "minimal": NotificationPriority.LOW,
        }

        logger.info("Analysis Agent integration initialized")

    async def handle_analysis_complete(
        self,
        analysis_data: Dict[str, Any],
        incident_id: str,
        custom_recipients: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Handle analysis completion notification.

        Args:
            analysis_data: Analysis results from Analysis Agent
            incident_id: Related incident ID
            custom_recipients: Optional custom recipients

        Returns:
            Notification result
        """
        try:
            # Extract analysis details
            risk_level = (
                analysis_data.get("risk_assessment", {}).get("level", "medium").lower()
            )

            logger.info(
                "Processing analysis completion notification",
                extra={
                    "incident_id": incident_id,
                    "risk_level": risk_level,
                },
            )

            # Map risk level to priority
            priority = self.risk_to_priority.get(
                risk_level,
                NotificationPriority.MEDIUM,
            )

            # Prepare context for template
            context = {
                "incident_id": incident_id,
                "risk_level": risk_level.title(),
                "impact_assessment": self._format_impact_assessment(
                    analysis_data.get("impact_assessment", {})
                ),
                "root_cause": analysis_data.get("root_cause_analysis", {}).get(
                    "primary_cause", "Under investigation"
                ),
                "affected_systems": self._format_affected_systems(
                    analysis_data.get("affected_systems", [])
                ),
                "findings_list": self._format_findings(
                    analysis_data.get("findings", [])
                ),
                "recommended_actions": self._format_recommendations(
                    analysis_data.get("recommendations", {})
                ),
                "next_steps": self._determine_next_steps(analysis_data),
                "analysis_link": self._generate_analysis_link(incident_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Add threat intelligence if available
            if "threat_intelligence" in analysis_data:
                context["threat_intelligence"] = self._format_threat_intel(
                    analysis_data["threat_intelligence"]
                )

            # Determine recipients
            if custom_recipients:
                recipients = custom_recipients
            else:
                recipients = self._get_analysis_recipients(risk_level, analysis_data)

            # Send notification
            result = self.comm_agent.process(
                {
                    "message_type": MessageType.ANALYSIS_COMPLETE.value,
                    "recipients": recipients,
                    "context": context,
                    "priority": priority.value,
                }
            )

            # Send additional notifications based on findings
            await self._handle_special_findings(analysis_data, incident_id)

            return {
                "status": "notification_sent",
                "incident_id": incident_id,
                "risk_level": risk_level,
                "result": result,
            }

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Error handling analysis completion: %s",
                e,
                extra={
                    "incident_id": incident_id,
                    "analysis_data": analysis_data,
                },
                exc_info=True,
            )
            return {
                "status": "error",
                "error": str(e),
            }

    def _format_impact_assessment(
        self,
        impact_data: Dict[str, Any],
    ) -> str:
        """Format impact assessment for notification."""
        if not impact_data:
            return "Impact assessment pending"

        parts = []

        # Business impact
        if "business_impact" in impact_data:
            parts.append(f"Business: {impact_data['business_impact']}")

        # Technical impact
        if "technical_impact" in impact_data:
            parts.append(f"Technical: {impact_data['technical_impact']}")

        # Data impact
        if "data_impact" in impact_data:
            parts.append(f"Data: {impact_data['data_impact']}")

        # User impact
        if "affected_users" in impact_data:
            count = impact_data["affected_users"]
            parts.append(f"Affected users: {count}")

        # Financial impact
        if "estimated_cost" in impact_data:
            cost = impact_data["estimated_cost"]
            parts.append(f"Estimated cost: ${cost:,.2f}")

        return " | ".join(parts) if parts else "No significant impact identified"

    def _format_affected_systems(
        self,
        systems: List[Any],
    ) -> str:
        """Format affected systems list."""
        if not systems:
            return "No specific systems identified"

        system_names = []
        for system in systems[:5]:  # Limit to 5 for brevity
            if isinstance(system, dict):
                name = system.get("name", system.get("id", "Unknown"))
                criticality = system.get("criticality", "")
                if criticality:
                    system_names.append(f"{name} ({criticality})")
                else:
                    system_names.append(str(name) if name is not None else "Unknown")
            else:
                system_names.append(str(system))

        result = ", ".join(system_names)
        if len(systems) > 5:
            result += f" and {len(systems) - 5} more"

        return result

    def _format_findings(
        self,
        findings: List[Dict[str, Any]],
    ) -> List[str]:
        """Format analysis findings as a list."""
        if not findings:
            return ["No specific findings to report"]

        formatted_findings = []

        for finding in findings[:10]:  # Limit to 10 findings
            # Findings should always be dicts based on the type annotation
            title = finding.get("title", "Finding")
            severity = finding.get("severity", "")
            confidence = finding.get("confidence", 0)

            finding_text = title
            if severity:
                finding_text = f"[{severity.upper()}] {finding_text}"
            if confidence > 0:
                finding_text += f" (Confidence: {confidence}%)"

            formatted_findings.append(finding_text)

        if len(findings) > 10:
            formatted_findings.append(f"... and {len(findings) - 10} more findings")

        return formatted_findings

    def _format_recommendations(
        self,
        recommendations: Dict[str, Any],
    ) -> str:
        """Format recommendations for notification."""
        if not recommendations:
            return "Awaiting recommendation generation"

        formatted_recs: List[str] = []

        # Process each recommendation type
        self._add_immediate_recommendations(recommendations, formatted_recs)
        self._add_short_term_recommendations(recommendations, formatted_recs)
        self._add_long_term_recommendations(recommendations, formatted_recs)

        return "\n".join(formatted_recs)

    def _add_immediate_recommendations(
        self, recommendations: Dict[str, Any], formatted_recs: List[str]
    ) -> None:
        """Add immediate recommendations to the list."""
        if "immediate" not in recommendations:
            return

        immediate = recommendations["immediate"]
        if not isinstance(immediate, list):
            return

        for i, action in enumerate(immediate[:3], 1):
            formatted_recs.append(f"{i}. [IMMEDIATE] {action}")

    def _add_short_term_recommendations(
        self, recommendations: Dict[str, Any], formatted_recs: List[str]
    ) -> None:
        """Add short-term recommendations to the list."""
        if "short_term" not in recommendations:
            return

        short_term = recommendations["short_term"]
        if not isinstance(short_term, list):
            return

        start_num = len(formatted_recs) + 1
        for i, action in enumerate(short_term[:3], start_num):
            formatted_recs.append(f"{i}. {action}")

    def _add_long_term_recommendations(
        self, recommendations: Dict[str, Any], formatted_recs: List[str]
    ) -> None:
        """Add long-term recommendations to the list."""
        if "long_term" not in recommendations or len(formatted_recs) >= 6:
            return

        long_term = recommendations["long_term"]
        if not isinstance(long_term, list):
            return

        start_num = len(formatted_recs) + 1
        remaining = 6 - len(formatted_recs)
        for i, action in enumerate(long_term[:remaining], start_num):
            formatted_recs.append(f"{i}. [LONG-TERM] {action}")

    def _determine_next_steps(
        self,
        analysis_data: Dict[str, Any],
    ) -> str:
        """Determine next steps based on analysis."""
        risk_level = (
            analysis_data.get("risk_assessment", {}).get("level", "medium").lower()
        )

        if risk_level in ["critical", "high"]:
            return (
                "1. Review and approve recommended immediate actions\n"
                "2. Initiate incident response procedures\n"
                "3. Prepare remediation plan\n"
                "4. Schedule emergency response meeting"
            )
        elif risk_level == "medium":
            return (
                "1. Review analysis findings in detail\n"
                "2. Prioritize remediation actions\n"
                "3. Schedule follow-up assessment\n"
                "4. Update security policies as needed"
            )
        else:
            return (
                "1. Document findings for future reference\n"
                "2. Implement preventive measures\n"
                "3. Monitor for similar patterns\n"
                "4. Update security baselines"
            )

    def _format_threat_intel(
        self,
        threat_intel: Dict[str, Any],
    ) -> str:
        """Format threat intelligence information."""
        parts = []

        if "threat_actors" in threat_intel:
            actors = threat_intel["threat_actors"]
            if isinstance(actors, list) and actors:
                parts.append(f"Threat actors: {', '.join(actors[:3])}")

        if "ttps" in threat_intel:
            ttps = threat_intel["ttps"]
            if isinstance(ttps, list) and ttps:
                parts.append(f"TTPs identified: {len(ttps)}")

        if "iocs" in threat_intel:
            iocs = threat_intel["iocs"]
            if isinstance(iocs, list):
                parts.append(f"IoCs found: {len(iocs)}")

        if "related_campaigns" in threat_intel:
            campaigns = threat_intel["related_campaigns"]
            if isinstance(campaigns, list) and campaigns:
                parts.append(f"Related campaigns: {', '.join(campaigns[:2])}")

        return " | ".join(parts) if parts else ""

    def _generate_analysis_link(self, incident_id: str) -> str:
        """Generate analysis report link."""
        base_url = "https://sentinelops.example.com/analysis"
        return f"{base_url}/incidents/{incident_id}/report"

    def _get_analysis_recipients(
        self,
        risk_level: str,
        analysis_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Determine recipients based on risk level and analysis."""
        recipients = []

        # Always include security team
        recipients.append({"role": "security_engineer"})

        # Risk-based recipients
        if risk_level in ["critical", "high"]:
            recipients.append({"role": "incident_responder"})
            recipients.append({"role": "manager"})

        if risk_level == "critical":
            recipients.append({"role": "executive"})

        # Add specialized teams based on findings
        findings = analysis_data.get("findings", [])
        for finding in findings:
            if isinstance(finding, dict):
                category = finding.get("category", "").lower()

                if "malware" in category:
                    recipients.append({"tag": "malware_team"})
                elif "vulnerability" in category:
                    recipients.append({"tag": "vulnerability_team"})
                elif "data" in category or "exfiltration" in category:
                    recipients.append({"tag": "data_protection_team"})

        # Remove duplicates
        unique_recipients = []
        seen = set()
        for recipient in recipients:
            key = str(recipient)
            if key not in seen:
                seen.add(key)
                unique_recipients.append(recipient)

        return unique_recipients

    async def _handle_special_findings(
        self,
        analysis_data: Dict[str, Any],
        incident_id: str,
    ) -> None:
        """Handle special findings that require additional notifications."""
        findings = analysis_data.get("findings", [])

        for finding in findings:
            if isinstance(finding, dict):
                # Check for data breach indicators
                if finding.get("category") == "data_breach":
                    await self._notify_data_breach(finding, incident_id)

                # Check for compliance violations
                elif finding.get("category") == "compliance_violation":
                    await self._notify_compliance_violation(finding, incident_id)

                # Check for APT indicators
                elif finding.get("category") == "apt_activity":
                    await self._notify_apt_activity(finding, incident_id)

    async def _notify_data_breach(
        self,
        finding: Dict[str, Any],
        incident_id: str,
    ) -> None:
        """Send specialized notification for data breach."""
        context = {
            "incident_id": incident_id,
            "breach_type": finding.get("breach_type", "Unknown"),
            "data_types": finding.get("data_types", []),
            "estimated_records": finding.get("estimated_records", "Unknown"),
            "exposure_duration": finding.get("exposure_duration", "Unknown"),
            "regulatory_impact": finding.get("regulatory_impact", []),
        }

        # Notify legal and compliance teams
        self.comm_agent.process(
            {
                "message_type": MessageType.CRITICAL_ALERT.value,
                "recipients": [
                    {"role": "executive"},
                    {"tag": "legal_team"},
                    {"tag": "compliance_team"},
                    {"tag": "data_protection_team"},
                ],
                "context": {
                    "alert_type": "DATA BREACH DETECTED",
                    "message": (
                        f"Critical data breach detected in incident {incident_id}. "
                        f"Estimated {context['estimated_records']} records affected. "
                        "Immediate action required for regulatory compliance."
                    ),
                    **context,
                },
                "priority": NotificationPriority.CRITICAL.value,
            }
        )

    async def _notify_compliance_violation(
        self,
        finding: Dict[str, Any],
        incident_id: str,
    ) -> None:
        """Send specialized notification for compliance violation."""
        # Similar implementation for compliance violations

    async def _notify_apt_activity(
        self,
        finding: Dict[str, Any],
        incident_id: str,
    ) -> None:
        """Send specialized notification for APT activity."""
        # Similar implementation for APT activity

    async def handle_threat_intelligence_update(
        self,
        threat_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle threat intelligence updates from Analysis Agent.

        Args:
            threat_data: Threat intelligence data

        Returns:
            Notification result
        """
        try:
            severity = threat_data.get("severity", "medium").lower()
            priority = self.risk_to_priority.get(
                severity,
                NotificationPriority.MEDIUM,
            )

            # Format threat intelligence update
            context = {
                "update_type": "Threat Intelligence Update",
                "severity": severity,
                "threat_name": threat_data.get("name", "Unknown Threat"),
                "description": threat_data.get("description", ""),
                "indicators_count": len(threat_data.get("indicators", [])),
                "affected_systems": threat_data.get("potentially_affected", []),
                "mitigation_available": threat_data.get("mitigation_available", False),
                "action_required": threat_data.get(
                    "action_required", "Review and assess"
                ),
            }

            # Send to security team
            result = self.comm_agent.process(
                {
                    "message_type": MessageType.STATUS_UPDATE.value,
                    "recipients": [
                        {"role": "security_engineer"},
                        {"tag": "threat_intelligence_team"},
                    ],
                    "context": context,
                    "priority": priority.value,
                }
            )

            return {
                "status": "notification_sent",
                "threat_name": context["threat_name"],
                "result": result,
            }

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Error handling threat intelligence update: %s",
                e,
                exc_info=True,
            )
            return {
                "status": "error",
                "error": str(e),
            }

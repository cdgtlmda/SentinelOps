"""
Detection Agent integration for the Communication Agent.

Handles incident notifications, alert formatting, and severity mapping
from the Detection Agent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.communication_agent.formatting import MessageFormatter
from src.communication_agent.types import (
    MessageType,
    NotificationChannel,
    NotificationPriority,
)

if TYPE_CHECKING:
    from src.communication_agent.agent import CommunicationAgent
# pylint: disable=wrong-import-position
from src.utils.logging import get_logger

# pylint: enable=wrong-import-position

logger = get_logger(__name__)


class DetectionAgentIntegration:
    """
    Integration between Detection Agent and Communication Agent.

    Handles:
    - Incident detection notifications
    - Alert severity mapping
    - Incident formatting for notifications
    - Escalation triggers
    """

    def __init__(
        self,
        communication_agent: "CommunicationAgent",
        formatter: Optional[MessageFormatter] = None,
    ):
        """
        Initialize Detection Agent integration.

        Args:
            communication_agent: Communication agent instance
            formatter: Optional message formatter
        """
        self.comm_agent = communication_agent
        self.formatter = formatter or MessageFormatter()

        # Severity mapping
        self.severity_to_priority = {
            "critical": NotificationPriority.CRITICAL,
            "high": NotificationPriority.HIGH,
            "medium": NotificationPriority.MEDIUM,
            "low": NotificationPriority.LOW,
            "info": NotificationPriority.LOW,
        }

        # Default notification settings
        self.default_channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK]
        self.critical_channels = [
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
            NotificationChannel.SMS,
        ]

        logger.info("Detection Agent integration initialized")

    async def handle_incident_detected(
        self,
        incident_data: Dict[str, Any],
        custom_recipients: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Handle a new incident detection from Detection Agent.

        Args:
            incident_data: Incident data from Detection Agent
            custom_recipients: Optional custom recipients

        Returns:
            Notification result
        """
        try:
            # Extract incident details
            incident_id = incident_data.get("incident_id", "UNKNOWN")
            incident_type = incident_data.get("type", "Security Incident")
            severity = incident_data.get("severity", "medium").lower()

            logger.info(
                "Processing incident detection notification",
                extra={
                    "incident_id": incident_id,
                    "type": incident_type,
                    "severity": severity,
                },
            )

            # Map severity to priority
            priority = self.severity_to_priority.get(
                severity,
                NotificationPriority.MEDIUM,
            )

            # Determine channels based on severity
            if severity == "critical":
                channels = self.critical_channels
            else:
                channels = self.default_channels

            # Format incident for notification
            formatted_incident = self._format_incident_data(incident_data)

            # Prepare context for template
            context = {
                "incident_id": incident_id,
                "incident_type": incident_type,
                "severity": severity,
                "timestamp": incident_data.get(
                    "detected_at",
                    datetime.now(timezone.utc).isoformat(),
                ),
                "detection_source": incident_data.get("source", "Unknown"),
                "affected_resources_list": formatted_incident.get(
                    "affected_resources",
                    [],
                ),
                "affected_resources_count": len(
                    incident_data.get("affected_resources", [])
                ),
                "initial_assessment": formatted_incident.get(
                    "assessment",
                    "Automated detection - analysis pending",
                ),
                "dashboard_link": self._generate_dashboard_link(incident_id),
                **formatted_incident.get("additional_context", {}),
            }

            # Determine recipients
            if custom_recipients:
                recipients = custom_recipients
            else:
                recipients = self._get_default_recipients(severity, incident_type)

            # Send notifications for each channel
            results = {}
            for channel in channels:
                channel_recipients = [
                    r
                    for r in recipients
                    if r.get("channel") == channel.value or "channel" not in r
                ]

                if not channel_recipients:
                    continue

                # Add channel to recipients that don't have it
                for recipient in channel_recipients:
                    if "channel" not in recipient:
                        recipient["channel"] = channel.value

                result = self.comm_agent.process(
                    {
                        "message_type": MessageType.INCIDENT_DETECTED.value,
                        "recipients": channel_recipients,
                        "context": context,
                        "priority": priority.value,
                    }
                )

                results[channel.value] = result

            # Handle escalation for critical incidents
            if severity == "critical":
                await self._trigger_escalation(incident_data, context)

            return {
                "status": "notifications_sent",
                "incident_id": incident_id,
                "channels": list(results.keys()),
                "results": results,
            }

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Error handling incident detection: %s",
                e,
                extra={"incident_data": incident_data},
                exc_info=True,
            )
            return {
                "status": "error",
                "error": str(e),
            }

    def _format_incident_data(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format incident data for notification."""
        formatted: Dict[str, Any] = {}

        # Format affected resources
        self._format_affected_resources(incident_data, formatted)

        # Format assessment
        self._format_assessment(incident_data, formatted)

        # Add additional context
        self._add_additional_context(incident_data, formatted)

        return formatted

    def _format_affected_resources(
        self, incident_data: Dict[str, Any], formatted: Dict[str, Any]
    ) -> None:
        """Format affected resources for the incident."""
        resources = incident_data.get("affected_resources", [])
        if not resources:
            return

        formatted_resources = []
        for resource in resources:
            formatted_resource = self._format_single_resource(resource)
            formatted_resources.append(formatted_resource)

        formatted["affected_resources"] = formatted_resources

    def _format_single_resource(self, resource: Any) -> Dict[str, Any]:
        """Format a single resource."""
        if not isinstance(resource, dict):
            return {"resource": str(resource)}

        name = resource.get("name", resource.get("id", "Unknown"))
        resource_type = resource.get("type", "Resource")
        status = resource.get("status", "")

        formatted_resource = {
            "name": name,
            "type": resource_type,
        }
        if status:
            formatted_resource["status"] = status

        return formatted_resource

    def _format_assessment(
        self, incident_data: Dict[str, Any], formatted: Dict[str, Any]
    ) -> None:
        """Format assessment information."""
        assessment_parts: List[str] = []

        self._add_detection_details(incident_data, assessment_parts)
        self._add_indicators(incident_data, assessment_parts)
        self._add_threat_level(incident_data, assessment_parts)

        if assessment_parts:
            formatted["assessment"] = "\n".join(assessment_parts)

    def _add_detection_details(
        self, incident_data: Dict[str, Any], assessment_parts: List[str]
    ) -> None:
        """Add detection details to assessment."""
        if "detection_details" not in incident_data:
            return

        details = incident_data["detection_details"]
        if isinstance(details, dict):
            for key, value in details.items():
                assessment_parts.append(f"{key.title()}: {value}")
        else:
            assessment_parts.append(str(details))

    def _add_indicators(
        self, incident_data: Dict[str, Any], assessment_parts: List[str]
    ) -> None:
        """Add indicators to assessment."""
        if "indicators" not in incident_data:
            return

        indicators = incident_data["indicators"]
        if isinstance(indicators, list):
            assessment_parts.append(
                f"Indicators detected: {', '.join(str(i) for i in indicators)}"
            )

    def _add_threat_level(
        self, incident_data: Dict[str, Any], assessment_parts: List[str]
    ) -> None:
        """Add threat level to assessment."""
        if "threat_level" in incident_data:
            assessment_parts.append(f"Threat level: {incident_data['threat_level']}")

    def _add_additional_context(
        self, incident_data: Dict[str, Any], formatted: Dict[str, Any]
    ) -> None:
        """Add additional context to formatted data."""
        additional_context: Dict[str, Any] = {}

        self._add_metrics(incident_data, additional_context)
        self._add_tags(incident_data, additional_context)

        if additional_context:
            formatted["additional_context"] = additional_context

    def _add_metrics(
        self, incident_data: Dict[str, Any], additional_context: Dict[str, Any]
    ) -> None:
        """Add metrics to additional context."""
        if "metrics" not in incident_data:
            return

        metrics = incident_data["metrics"]
        if isinstance(metrics, dict):
            for metric, value in metrics.items():
                additional_context[f"metric_{metric}"] = value

    def _add_tags(
        self, incident_data: Dict[str, Any], additional_context: Dict[str, Any]
    ) -> None:
        """Add tags to additional context."""
        if "tags" in incident_data:
            additional_context["tags"] = ", ".join(incident_data["tags"])

    def _get_default_recipients(
        self,
        severity: str,
        incident_type: str,
    ) -> List[Dict[str, Any]]:
        """Get default recipients based on severity and type."""
        recipients = []

        # Always include security team
        recipients.append({"role": "security_engineer"})

        # Add based on severity
        if severity in ["critical", "high"]:
            recipients.append({"role": "incident_responder"})
            recipients.append({"on_call": "true", "primary_only": "true"})

        if severity == "critical":
            recipients.append({"role": "manager"})

            # For specific incident types, add executives
            if incident_type.lower() in ["data_breach", "ransomware", "apt"]:
                recipients.append({"role": "executive"})

        # Add based on incident type
        type_lower = incident_type.lower()
        if "compliance" in type_lower or "policy" in type_lower:
            recipients.append({"tag": "compliance_team"})

        if "network" in type_lower:
            recipients.append({"tag": "network_team"})

        if "application" in type_lower or "web" in type_lower:
            recipients.append({"tag": "application_team"})

        return recipients

    def _generate_dashboard_link(self, incident_id: str) -> str:
        """Generate a dashboard link for the incident."""
        # In production, this would use actual dashboard URL
        base_url = "https://sentinelops.example.com/dashboard"
        return f"{base_url}/incidents/{incident_id}"

    async def _trigger_escalation(
        self,
        incident_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> None:
        """Trigger escalation for critical incidents."""
        try:
            escalation_context = {
                **context,
                "escalation_reason": "Critical severity incident detected",
                "escalation_level": "1",
                "escalation_contacts": "Security Manager, On-Call Lead",
                "response_deadline": "15 minutes",
                "critical_info": (
                    f"Critical {context['incident_type']} affecting "
                    f"{context['affected_resources_count']} resources"
                ),
                "immediate_actions": [
                    "Review incident details in dashboard",
                    "Assess immediate impact",
                    "Initiate incident response procedures",
                    "Prepare for executive briefing if needed",
                ],
                "emergency_link": f"{context['dashboard_link']}/emergency",
            }

            # Send escalation notification
            self.comm_agent.process(
                {
                    "message_type": MessageType.INCIDENT_ESCALATION.value,
                    "recipients": [
                        {"role": "manager"},
                        {"role": "incident_responder"},
                        {"on_call": True},
                    ],
                    "context": escalation_context,
                    "priority": NotificationPriority.CRITICAL.value,
                }
            )

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Error triggering escalation: %s",
                e,
                extra={"incident_id": incident_data.get("incident_id")},
                exc_info=True,
            )

    async def handle_alert_batch(
        self,
        alerts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Handle a batch of alerts from Detection Agent.

        Args:
            alerts: List of alert data

        Returns:
            Batch processing result
        """
        # Group alerts by severity and type
        grouped_alerts = self._group_alerts(alerts)

        results = []
        for group_key, group_alerts in grouped_alerts.items():
            severity, alert_type = group_key

            # Create summary for grouped alerts
            summary_data = {
                "incident_id": f"BATCH-{datetime.now(timezone.utc).timestamp()}",
                "type": f"Multiple {alert_type}",
                "severity": severity,
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "source": "Detection Agent Batch",
                "affected_resources": self._extract_resources_from_alerts(group_alerts),
                "detection_details": {
                    "alert_count": len(group_alerts),
                    "first_alert": group_alerts[0].get("timestamp"),
                    "last_alert": group_alerts[-1].get("timestamp"),
                },
                "indicators": self._extract_indicators_from_alerts(group_alerts),
            }

            # Send grouped notification
            result = await self.handle_incident_detected(summary_data)
            results.append(result)

        return {
            "status": "batch_processed",
            "total_alerts": len(alerts),
            "groups_created": len(grouped_alerts),
            "results": results,
        }

    def _group_alerts(
        self,
        alerts: List[Dict[str, Any]],
    ) -> Dict[tuple[str, ...], List[Dict[str, Any]]]:
        """Group alerts by severity and type."""
        grouped: Dict[tuple[str, ...], List[Dict[str, Any]]] = {}

        for alert in alerts:
            severity = alert.get("severity", "medium").lower()
            alert_type = alert.get("type", "Unknown")

            key = (severity, alert_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(alert)

        return grouped

    def _extract_resources_from_alerts(
        self,
        alerts: List[Dict[str, Any]],
    ) -> List[Any]:
        """Extract unique affected resources from alerts."""
        resources = []
        seen = set()

        for alert in alerts:
            alert_resources = alert.get("affected_resources", [])
            for resource in alert_resources:
                # Create unique key for resource
                if isinstance(resource, dict):
                    key = resource.get("id", resource.get("name", str(resource)))
                else:
                    key = str(resource)

                if key not in seen:
                    seen.add(key)
                    resources.append(resource)

        return resources

    def _extract_indicators_from_alerts(
        self,
        alerts: List[Dict[str, Any]],
    ) -> List[str]:
        """Extract unique indicators from alerts."""
        indicators = set()

        for alert in alerts:
            alert_indicators = alert.get("indicators", [])
            for indicator in alert_indicators:
                indicators.add(str(indicator))

        return list(indicators)

    def register_custom_formatter(
        self,
        incident_type: str,
    ) -> None:
        """Register a custom formatter for specific incident types."""
        # This would allow custom formatting for specific incident types
        logger.info("Registered custom formatter for incident type: %s", incident_type)

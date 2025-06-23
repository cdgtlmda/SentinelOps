"""
Integration points for the Remediation Agent.

This module handles integration with Analysis Agent, Orchestration Agent,
and Communication Agent.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud.pubsub_v1 import PublisherClient

from src.common.models import (
    AnalysisResult,
    IncidentStatus,
    RemediationAction,
)


class AnalysisAgentIntegration:
    """Handles integration with the Analysis Agent."""

    def __init__(
        self,
        publisher_client: PublisherClient,
        project_id: str,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Analysis Agent integration.

        Args:
            publisher_client: Pub/Sub publisher client
            project_id: GCP project ID
            logger: Logger instance
        """
        self.publisher = publisher_client
        self.project_id = project_id
        self.logger = logger or logging.getLogger(__name__)

    def parse_remediation_recommendations(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """
        Parse remediation recommendations from analysis results.

        Args:
            analysis_result: Analysis result containing recommendations

        Returns:
            List of parsed action specifications
        """
        parsed_actions = []

        # Parse recommendations into action specifications
        for recommendation in analysis_result.recommendations:
            action_spec = self._parse_recommendation(recommendation)
            if action_spec:
                parsed_actions.append(action_spec)

        # Also check for specific attack techniques that map to actions
        for technique in analysis_result.attack_techniques:
            technique_actions = self._get_actions_for_technique(technique)
            parsed_actions.extend(technique_actions)

        # Deduplicate actions
        seen = set()
        unique_actions = []
        for action in parsed_actions:
            action_key = f"{action['action_type']}:{action.get('target_resource', '')}"
            if action_key not in seen:
                seen.add(action_key)
                unique_actions.append(action)

        self.logger.info(f"Parsed {len(unique_actions)} unique actions from analysis")

        return unique_actions

    def _parse_recommendation(self, recommendation: str) -> Optional[Dict[str, Any]]:
        """Parse a single recommendation into an action specification."""
        # Map recommendation patterns to actions
        recommendation_lower = recommendation.lower()

        if "block ip" in recommendation_lower or "blacklist ip" in recommendation_lower:
            # Extract IP address
            import re

            ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", recommendation)
            if ip_match:
                return {
                    "action_type": "block_ip_address",
                    "description": "Block suspicious IP based on analysis",
                    "target_resource": ip_match.group(),
                    "params": {
                        "ip_address": ip_match.group(),
                    },
                }

        elif (
            "disable user" in recommendation_lower
            or "suspend account" in recommendation_lower
        ):
            # Extract email
            import re

            email_match = re.search(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", recommendation
            )
            if email_match:
                return {
                    "action_type": "disable_user_account",
                    "description": "Disable compromised user account",
                    "target_resource": email_match.group(),
                    "params": {
                        "user_email": email_match.group(),
                    },
                }

        elif (
            "quarantine" in recommendation_lower and "instance" in recommendation_lower
        ):
            # Extract instance name
            import re

            instance_match = re.search(
                r"instance[:\s]+([a-z0-9-]+)", recommendation_lower
            )
            if instance_match:
                return {
                    "action_type": "quarantine_instance",
                    "description": "Quarantine infected instance",
                    "target_resource": instance_match.group(1),
                    "params": {
                        "instance_name": instance_match.group(1),
                    },
                }

        elif "rotate" in recommendation_lower and "credential" in recommendation_lower:
            return {
                "action_type": "rotate_credentials",
                "description": "Rotate potentially compromised credentials",
                "target_resource": "service_accounts",
                "params": {
                    "credential_type": "service_account_key",
                },
            }

        elif "enable" in recommendation_lower and "logging" in recommendation_lower:
            return {
                "action_type": "enable_additional_logging",
                "description": "Enable enhanced logging for investigation",
                "target_resource": "project",
                "params": {
                    "log_types": ["audit", "data_access", "admin_activity"],
                },
            }

        return None

    def _get_actions_for_technique(self, technique: str) -> List[Dict[str, Any]]:
        """Get remediation actions for specific attack techniques."""
        technique_actions = {
            "T1190": [  # Exploit Public-Facing Application
                {
                    "action_type": "update_firewall_rule",
                    "description": "Restrict access to vulnerable application",
                    "params": {"rule_updates": [{"type": "restrict_source_ranges"}]},
                }
            ],
            "T1078": [  # Valid Accounts
                {
                    "action_type": "enable_mfa_requirement",
                    "description": "Enforce MFA for compromised accounts",
                    "params": {"target_type": "user"},
                }
            ],
            "T1110": [  # Brute Force
                {
                    "action_type": "configure_cloud_armor_policy",
                    "description": "Enable rate limiting to prevent brute force",
                    "params": {"policy_action": "add_rate_limiting"},
                }
            ],
            "T1486": [  # Data Encrypted for Impact
                {
                    "action_type": "snapshot_instance",
                    "description": "Create snapshot before ransomware spreads",
                    "params": {},
                },
                {
                    "action_type": "restore_from_backup",
                    "description": "Restore from clean backup",
                    "params": {},
                },
            ],
        }

        return technique_actions.get(technique, [])

    def map_to_available_actions(
        self, action_specs: List[Dict[str, Any]], available_actions: List[str]
    ) -> List[RemediationAction]:
        """
        Map action specifications to available remediation actions.

        Args:
            action_specs: List of action specifications
            available_actions: List of available action types

        Returns:
            List of remediation actions
        """
        mapped_actions = []

        for spec in action_specs:
            action_type = spec.get("action_type")

            if action_type not in available_actions:
                self.logger.warning(
                    f"Action type '{action_type}' not available, skipping"
                )
                continue

            # Create RemediationAction
            action = RemediationAction(
                incident_id=spec.get("incident_id", ""),
                action_type=action_type,
                description=spec.get("description", f"Execute {action_type}"),
                target_resource=spec.get("target_resource", ""),
                params=spec.get("params", {}),
            )

            mapped_actions.append(action)

        return mapped_actions


class OrchestrationAgentIntegration:
    """Handles integration with the Orchestration Agent."""

    def __init__(
        self,
        publisher_client: PublisherClient,
        project_id: str,
        topic_name: str,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Orchestration Agent integration.

        Args:
            publisher_client: Pub/Sub publisher client
            project_id: GCP project ID
            topic_name: Topic for orchestration updates
            logger: Logger instance
        """
        self.publisher = publisher_client
        self.project_id = project_id
        self.topic_name = topic_name
        self.topic_path = publisher_client.topic_path(project_id, topic_name)
        self.logger = logger or logging.getLogger(__name__)

    async def report_status(
        self,
        action: RemediationAction,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Report action status to the Orchestration Agent.

        Args:
            action: The remediation action
            status: Current status
            details: Additional details
        """
        status_update = {
            "action_id": action.action_id,
            "incident_id": action.incident_id,
            "action_type": action.action_type,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }

        try:
            message_data = json.dumps(status_update).encode("utf-8")
            future = self.publisher.publish(self.topic_path, message_data)
            future.result()

            self.logger.debug(
                "Reported status '%s' for action %s", status, action.action_id
            )

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Failed to report status: %s", e)

    async def report_progress(
        self, action: RemediationAction, progress_percentage: float, message: str
    ) -> None:
        """
        Report action progress to the Orchestration Agent.

        Args:
            action: The remediation action
            progress_percentage: Progress percentage (0-100)
            message: Progress message
        """
        progress_update = {
            "action_id": action.action_id,
            "incident_id": action.incident_id,
            "progress_percentage": progress_percentage,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            message_data = json.dumps(progress_update).encode("utf-8")
            future = self.publisher.publish(self.topic_path, message_data)
            future.result()

            self.logger.debug(
                "Reported %s%% progress for action %s",
                progress_percentage,
                action.action_id,
            )

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Failed to report progress: %s", e)

    async def report_completion(
        self, action: RemediationAction, result: Dict[str, Any]
    ) -> None:
        """
        Report action completion to the Orchestration Agent.

        Args:
            action: The completed action
            result: Execution result
        """
        completion_update = {
            "action_id": action.action_id,
            "incident_id": action.incident_id,
            "action_type": action.action_type,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            message_data = json.dumps(completion_update).encode("utf-8")
            future = self.publisher.publish(self.topic_path, message_data)
            future.result()

            self.logger.info("Reported completion for action %s", action.action_id)

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Failed to report completion: %s", e)

    def update_incident_status(
        self, incident_id: str, new_status: IncidentStatus, reason: str
    ) -> None:
        """
        Request incident status update from Orchestration Agent.

        Args:
            incident_id: ID of the incident
            new_status: New incident status
            reason: Reason for status change
        """
        status_change = {
            "incident_id": incident_id,
            "new_status": new_status.value,
            "reason": reason,
            "source": "remediation_agent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            message_data = json.dumps(status_change).encode("utf-8")
            future = self.publisher.publish(self.topic_path, message_data)
            future.result()

            self.logger.info(
                "Requested status change to %s for incident %s",
                new_status.value,
                incident_id,
            )

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Failed to update incident status: %s", e)


class CommunicationAgentIntegration:
    """Handles integration with the Communication Agent."""

    def __init__(
        self,
        publisher_client: PublisherClient,
        project_id: str,
        notifications_topic: str,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Communication Agent integration.

        Args:
            publisher_client: Pub/Sub publisher client
            project_id: GCP project ID
            notifications_topic: Topic for notifications
            logger: Logger instance
        """
        self.publisher = publisher_client
        self.project_id = project_id
        self.notifications_topic = notifications_topic
        self.topic_path = publisher_client.topic_path(project_id, notifications_topic)
        self.logger = logger or logging.getLogger(__name__)

    async def send_action_notification(
        self,
        action: RemediationAction,
        notification_type: str,
        recipients: List[str],
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send notification about a remediation action.

        Args:
            action: The remediation action
            notification_type: Type of notification
            recipients: List of recipient emails/channels
            additional_context: Additional context for the notification
        """
        notification = {
            "notification_type": notification_type,
            "incident_id": action.incident_id,
            "action_id": action.action_id,
            "action_type": action.action_type,
            "recipients": recipients,
            "subject": self._generate_subject(action, notification_type),
            "content": self._generate_content(
                action, notification_type, additional_context
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": self._determine_priority(action, notification_type),
        }

        try:
            message_data = json.dumps(notification).encode("utf-8")
            future = self.publisher.publish(self.topic_path, message_data)
            future.result()

            self.logger.info(
                "Sent %s notification for action %s",
                notification_type,
                action.action_id,
            )

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Failed to send notification: %s", e)

    def _generate_subject(
        self, action: RemediationAction, notification_type: str
    ) -> str:
        """Generate notification subject."""
        subjects = {
            "action_started": f"Remediation Started: {action.action_type}",
            "action_completed": f"Remediation Completed: {action.action_type}",
            "action_failed": f"⚠️ Remediation Failed: {action.action_type}",
            "approval_required": f"🔔 Approval Required: {action.action_type}",
            "rollback_executed": f"↩️ Rollback Executed: {action.action_type}",
        }

        return subjects.get(
            notification_type, f"Remediation Update: {action.action_type}"
        )

    def _generate_content(
        self,
        action: RemediationAction,
        notification_type: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate notification content."""
        context = additional_context or {}

        base_content = f"""
Incident ID: {action.incident_id}
Action ID: {action.action_id}
Action Type: {action.action_type}
Target Resource: {action.target_resource}
Description: {action.description}
"""

        if notification_type == "action_failed":
            error_msg = context.get("error_message", "Unknown error")
            base_content += f"\nError: {error_msg}"

        elif notification_type == "action_completed":
            execution_time = context.get("execution_time", "N/A")
            base_content += f"\nExecution Time: {execution_time}s"

        elif notification_type == "approval_required":
            risk_level = context.get("risk_level", "Unknown")
            base_content += f"\nRisk Level: {risk_level}"

        return base_content

    def _determine_priority(
        self, action: RemediationAction, notification_type: str
    ) -> str:
        """Determine notification priority."""
        _ = action  # Mark as intentionally unused for now
        if notification_type in ["action_failed", "approval_required"]:
            return "high"
        elif notification_type == "rollback_executed":
            return "medium"
        else:
            return "normal"

    async def send_approval_request(
        self,
        action: RemediationAction,
        approval_id: str,
        approvers: List[str],
        risk_assessment: Dict[str, Any],
    ) -> None:
        """
        Send approval request notification.

        Args:
            action: The action requiring approval
            approval_id: ID of the approval request
            approvers: List of approver emails
            risk_assessment: Risk assessment details
        """
        await self.send_action_notification(
            action=action,
            notification_type="approval_required",
            recipients=approvers,
            additional_context={
                "approval_id": approval_id,
                "risk_assessment": risk_assessment,
                "approval_link": f"https://sentinelops.example.com/approvals/{approval_id}",
            },
        )

    async def send_status_update(
        self, action: RemediationAction, status: str, stakeholders: List[str]
    ) -> None:
        """
        Send status update to stakeholders.

        Args:
            action: The remediation action
            status: Current status
            stakeholders: List of stakeholder emails
        """
        notification_type = {
            "executing": "action_started",
            "completed": "action_completed",
            "failed": "action_failed",
        }.get(status, "action_update")

        await self.send_action_notification(
            action=action,
            notification_type=notification_type,
            recipients=stakeholders,
            additional_context={"status": status},
        )


class IntegrationManager:
    """Manages all integration points for the Remediation Agent."""

    def __init__(
        self,
        publisher_client: PublisherClient,
        project_id: str,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the integration manager.

        Args:
            publisher_client: Pub/Sub publisher client
            project_id: GCP project ID
            config: Configuration dictionary
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize integrations
        self.analysis_integration = AnalysisAgentIntegration(
            publisher_client, project_id, self.logger
        )

        self.orchestration_integration = OrchestrationAgentIntegration(
            publisher_client,
            project_id,
            config.get("orchestration_topic", "orchestration-updates"),
            self.logger,
        )

        self.communication_integration = CommunicationAgentIntegration(
            publisher_client,
            project_id,
            config.get("notifications_topic", "notifications"),
            self.logger,
        )

    async def handle_analysis_result(
        self,
        incident_id: str,
        analysis_result: AnalysisResult,
        available_actions: List[str],
    ) -> List[RemediationAction]:
        """
        Handle analysis results and generate remediation actions.

        Args:
            incident_id: ID of the incident
            analysis_result: Analysis results
            available_actions: List of available action types

        Returns:
            List of remediation actions
        """
        # Parse recommendations
        action_specs = self.analysis_integration.parse_remediation_recommendations(
            analysis_result
        )

        # Add incident ID to all specs
        for spec in action_specs:
            spec["incident_id"] = incident_id

        # Map to available actions
        actions = self.analysis_integration.map_to_available_actions(
            action_specs, available_actions
        )

        return actions

    async def report_action_lifecycle(
        self,
        action: RemediationAction,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Report action lifecycle events to all relevant agents.

        Args:
            action: The remediation action
            event_type: Type of event (started, completed, failed, etc.)
            details: Event details
        """
        # Report to orchestration agent
        if event_type == "started":
            await self.orchestration_integration.report_status(
                action, "executing", details
            )
        elif event_type == "completed":
            await self.orchestration_integration.report_completion(
                action, details or {}
            )
        elif event_type == "failed":
            await self.orchestration_integration.report_status(
                action, "failed", details
            )

        # Send notifications for important events
        if event_type in ["started", "completed", "failed"]:
            # Get stakeholders (would come from config or incident data)
            stakeholders = ["security-team@example.com"]

            await self.communication_integration.send_status_update(
                action, action.status, stakeholders
            )

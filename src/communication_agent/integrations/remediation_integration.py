"""
Remediation Agent integration for the Communication Agent.

Handles action notifications, approval requests, completion updates,
and verification results from the Remediation Agent.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from src.communication_agent.formatting import MessageFormatter
from src.communication_agent.types import MessageType, NotificationPriority

if TYPE_CHECKING:
    from src.communication_agent.agent import CommunicationAgent
# pylint: disable=wrong-import-position
from src.utils.logging import get_logger

# pylint: enable=wrong-import-position

logger = get_logger(__name__)


class ApprovalRequest:
    """Represents a pending approval request."""

    def __init__(
        self,
        request_id: str,
        action_id: str,
        incident_id: str,
        action_type: str,
        risk_level: str,
        timeout_minutes: int = 30,
    ):
        """Initialize approval request."""
        self.request_id = request_id
        self.action_id = action_id
        self.incident_id = incident_id
        self.action_type = action_type
        self.risk_level = risk_level
        self.created_at = datetime.now(timezone.utc)
        self.timeout_at = self.created_at + timedelta(minutes=timeout_minutes)
        self.status = "pending"
        self.approver: Optional[str] = None
        self.approval_time: Optional[datetime] = None
        self.comments: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if approval request has expired."""
        return datetime.now(timezone.utc) > self.timeout_at

    def approve(self, approver: str, comments: Optional[str] = None) -> None:
        """Approve the request."""
        self.status = "approved"
        self.approver = approver
        self.approval_time = datetime.now(timezone.utc)
        self.comments = comments

    def reject(self, approver: str, comments: Optional[str] = None) -> None:
        """Reject the request."""
        self.status = "rejected"
        self.approver = approver
        self.approval_time = datetime.now(timezone.utc)
        self.comments = comments


class RemediationAgentIntegration:
    """
    Integration between Remediation Agent and Communication Agent.

    Handles:
    - Remediation action notifications
    - Approval request management
    - Completion status updates
    - Verification result communication
    """

    def __init__(
        self,
        communication_agent: "CommunicationAgent",
        formatter: Optional[MessageFormatter] = None,
        require_approval_for: Optional[List[str]] = None,
    ):
        """
        Initialize Remediation Agent integration.

        Args:
            communication_agent: Communication agent instance
            formatter: Optional message formatter
            require_approval_for: List of action types requiring approval
        """
        self.comm_agent = communication_agent
        self.formatter = formatter or MessageFormatter()

        # Actions requiring approval
        self.require_approval_for = require_approval_for or [
            "system_restart",
            "service_shutdown",
            "firewall_rule_change",
            "user_account_disable",
            "data_deletion",
            "configuration_rollback",
        ]

        # Approval tracking
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self._approval_callbacks: Dict[str, Any] = {}

        # Risk to priority mapping
        self.risk_to_priority = {
            "critical": NotificationPriority.HIGH,
            "high": NotificationPriority.HIGH,
            "medium": NotificationPriority.MEDIUM,
            "low": NotificationPriority.LOW,
        }

        logger.info("Remediation Agent integration initialized")

    async def handle_remediation_start(
        self,
        remediation_data: Dict[str, Any],
        incident_id: str,
        requires_approval: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Handle remediation start notification.

        Args:
            remediation_data: Remediation action data
            incident_id: Related incident ID
            requires_approval: Override approval requirement

        Returns:
            Notification result or approval request
        """
        try:
            action_id = remediation_data.get("action_id", str(uuid4()))
            action_type = remediation_data.get("action_type", "Unknown")
            risk_level = remediation_data.get("risk_level", "medium").lower()

            logger.info(
                "Processing remediation start notification",
                extra={
                    "action_id": action_id,
                    "action_type": action_type,
                    "incident_id": incident_id,
                    "risk_level": risk_level,
                },
            )

            # Check if approval is required
            if requires_approval is None:
                requires_approval = (
                    action_type in self.require_approval_for
                    or risk_level in ["critical", "high"]
                )

            if requires_approval:
                return await self._create_approval_request(
                    remediation_data,
                    incident_id,
                )

            # No approval needed - send start notification
            priority = self.risk_to_priority.get(
                risk_level,
                NotificationPriority.MEDIUM,
            )

            context = {
                "incident_id": incident_id,
                "action_type": action_type,
                "remediation_type": remediation_data.get("type", "Automated"),
                "target_resources": self._format_target_resources(
                    remediation_data.get("target_resources", [])
                ),
                "expected_duration": remediation_data.get(
                    "estimated_duration", "Unknown"
                ),
                "initiated_by": remediation_data.get("initiated_by", "System"),
                "remediation_actions": self._format_actions(
                    remediation_data.get("actions", [])
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Send notification
            result = self.comm_agent.process(
                {
                    "message_type": MessageType.REMEDIATION_STARTED.value,
                    "recipients": self._get_remediation_recipients(
                        risk_level,
                        action_type,
                    ),
                    "context": context,
                    "priority": priority.value,
                }
            )

            return {
                "status": "notification_sent",
                "action_id": action_id,
                "requires_approval": False,
                "result": result,
            }

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Error handling remediation start: %s",
                e,
                extra={
                    "incident_id": incident_id,
                    "remediation_data": remediation_data,
                },
                exc_info=True,
            )
            return {
                "status": "error",
                "error": str(e),
            }

    async def _create_approval_request(
        self,
        remediation_data: Dict[str, Any],
        incident_id: str,
    ) -> Dict[str, Any]:
        """Create and send approval request."""
        action_id = remediation_data.get("action_id", str(uuid4()))
        action_type = remediation_data.get("action_type", "Unknown")
        risk_level = remediation_data.get("risk_level", "medium").lower()

        # Create approval request
        request_id = f"APPROVAL-{uuid4().hex[:8]}"
        approval_request = ApprovalRequest(
            request_id=request_id,
            action_id=action_id,
            incident_id=incident_id,
            action_type=action_type,
            risk_level=risk_level,
            timeout_minutes=remediation_data.get("approval_timeout", 30),
        )

        self.pending_approvals[request_id] = approval_request

        # Prepare approval context
        context = {
            "incident_id": incident_id,
            "approval_request_id": request_id,
            "action_type": action_type,
            "risk_level": risk_level.upper(),
            "action_description": remediation_data.get(
                "description", f"Execute {action_type} remediation"
            ),
            "target_resources": self._format_target_resources(
                remediation_data.get("target_resources", [])
            ),
            "potential_impact": remediation_data.get(
                "impact_assessment", "See incident details for impact assessment"
            ),
            "approval_timeout": f"{approval_request.timeout_at.strftime('%H:%M UTC')}",
            "approval_link": self._generate_approval_link(request_id),
            "reject_link": self._generate_reject_link(request_id),
        }

        # Add justification
        if "justification" in remediation_data:
            context["justification"] = remediation_data["justification"]

        # Send approval request with CRITICAL priority
        result = self.comm_agent.process(
            {
                "message_type": MessageType.CRITICAL_ALERT.value,
                "recipients": self._get_approvers(risk_level),
                "context": {
                    "alert_type": "APPROVAL REQUIRED",
                    "message": (
                        f"Approval required for {action_type} remediation action "
                        f"for incident {incident_id}. "
                        f"Risk level: {risk_level.upper()}. "
                        f"Timeout: {approval_request.timeout_at.strftime('%H:%M UTC')}"
                    ),
                    **context,
                },
                "priority": NotificationPriority.CRITICAL.value,
            }
        )

        # Schedule timeout check
        asyncio.create_task(self._check_approval_timeout(request_id))

        return {
            "status": "approval_requested",
            "action_id": action_id,
            "approval_request_id": request_id,
            "requires_approval": True,
            "timeout_at": approval_request.timeout_at.isoformat(),
            "result": result,
        }

    async def handle_remediation_complete(
        self,
        completion_data: Dict[str, Any],
        incident_id: str,
    ) -> Dict[str, Any]:
        """
        Handle remediation completion notification.

        Args:
            completion_data: Completion data from Remediation Agent
            incident_id: Related incident ID

        Returns:
            Notification result
        """
        try:
            action_id = completion_data.get("action_id", "Unknown")
            success = completion_data.get("success", False)

            logger.info(
                "Processing remediation completion notification",
                extra={
                    "action_id": action_id,
                    "incident_id": incident_id,
                    "success": success,
                },
            )

            # Prepare context
            context = {
                "incident_id": incident_id,
                "status": "SUCCESS" if success else "FAILED",
                "duration": completion_data.get("duration", "Unknown"),
                "actions_taken": self._format_completed_actions(
                    completion_data.get("actions", [])
                ),
                "resources_modified": self._format_modified_resources(
                    completion_data.get("modified_resources", [])
                ),
                "verification_results": self._format_verification(
                    completion_data.get("verification", {})
                ),
                "post_remediation_status": completion_data.get(
                    "post_status", "Verification pending"
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Add failure details if applicable
            if not success:
                context["failure_reason"] = completion_data.get(
                    "error", "Unknown error"
                )
                context["rollback_status"] = completion_data.get(
                    "rollback_status", "Not attempted"
                )

            # Determine priority based on success
            priority = (
                NotificationPriority.MEDIUM if success else NotificationPriority.HIGH
            )

            # Send notification
            result = self.comm_agent.process(
                {
                    "message_type": MessageType.REMEDIATION_COMPLETE.value,
                    "recipients": self._get_completion_recipients(
                        success,
                    ),
                    "context": context,
                    "priority": priority.value,
                }
            )

            return {
                "status": "notification_sent",
                "action_id": action_id,
                "success": success,
                "result": result,
            }

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Error handling remediation completion: %s",
                e,
                exc_info=True,
            )
            return {
                "status": "error",
                "error": str(e),
            }

    async def handle_approval_response(
        self,
        request_id: str,
        approved: bool,
        approver: str,
        comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle approval response for a remediation action.

        Args:
            request_id: Approval request ID
            approved: Whether approved or rejected
            approver: Approver identifier
            comments: Optional comments

        Returns:
            Response handling result
        """
        if request_id not in self.pending_approvals:
            return {
                "status": "error",
                "error": "Approval request not found or already processed",
            }

        approval_request = self.pending_approvals[request_id]

        # Check if expired
        if approval_request.is_expired():
            return {
                "status": "error",
                "error": "Approval request has expired",
            }

        # Update approval status
        if approved:
            approval_request.approve(approver, comments)
        else:
            approval_request.reject(approver, comments)

        # Execute callback if registered
        if request_id in self._approval_callbacks:
            callback = self._approval_callbacks[request_id]
            try:
                await callback(approved, approver, comments)
            except (ValueError, KeyError, AttributeError) as e:
                logger.error(
                    "Error executing approval callback: %s",
                    e,
                    exc_info=True,
                )

        # Send confirmation notification
        self.comm_agent.process(
            {
                "message_type": MessageType.STATUS_UPDATE.value,
                "recipients": [{"role": "security_engineer"}],
                "context": {
                    "update_title": f"Remediation {'Approved' if approved else 'Rejected'}",
                    "update_message": (
                        f"Remediation action {approval_request.action_type} for "
                        f"incident {approval_request.incident_id} has been "
                        f"{'approved' if approved else 'rejected'} by {approver}."
                    ),
                    "status_details": {
                        "Action ID": approval_request.action_id,
                        "Decision": "Approved" if approved else "Rejected",
                        "Approver": approver,
                        "Comments": comments or "None provided",
                        "Decision Time": datetime.now(timezone.utc).isoformat(),
                    },
                },
                "priority": NotificationPriority.MEDIUM.value,
            }
        )

        # Clean up
        del self.pending_approvals[request_id]
        if request_id in self._approval_callbacks:
            del self._approval_callbacks[request_id]

        return {
            "status": "processed",
            "approved": approved,
            "action_id": approval_request.action_id,
        }

    def register_approval_callback(
        self,
        request_id: str,
        callback: Any,
    ) -> None:
        """Register a callback for when approval is received."""
        self._approval_callbacks[request_id] = callback

    async def _check_approval_timeout(self, request_id: str) -> None:
        """Check for approval timeout and send escalation if needed."""
        # Wait until timeout
        if request_id not in self.pending_approvals:
            return

        approval_request = self.pending_approvals[request_id]
        wait_time = (
            approval_request.timeout_at - datetime.now(timezone.utc)
        ).total_seconds()

        if wait_time > 0:
            await asyncio.sleep(wait_time)

        # Check if still pending
        if (
            request_id in self.pending_approvals
            and self.pending_approvals[request_id].status == "pending"
        ):

            # Send timeout notification
            self.comm_agent.process(
                {
                    "message_type": MessageType.INCIDENT_ESCALATION.value,
                    "recipients": [
                        {"role": "manager"},
                        {"on_call": True},
                    ],
                    "context": {
                        "incident_id": approval_request.incident_id,
                        "escalation_reason": "Remediation approval timeout",
                        "severity": approval_request.risk_level,
                        "duration": "30 minutes",
                        "failed_actions": f"Approval for {approval_request.action_type}",
                        "current_impact": "Remediation action blocked pending approval",
                        "required_actions": [
                            f"Review and approve/reject remediation action: "
                            f"{approval_request.action_type}",
                            f"Approval request ID: {request_id}",
                            "Contact on-call team if approvers unavailable",
                        ],
                    },
                    "priority": NotificationPriority.CRITICAL.value,
                }
            )

            # Mark as timed out
            approval_request.status = "timed_out"

    def _format_target_resources(self, resources: List[Any]) -> str:
        """Format target resources for notification."""
        if not resources:
            return "No specific resources"

        formatted = []
        for resource in resources[:5]:
            if isinstance(resource, dict):
                name = resource.get("name", resource.get("id", "Unknown"))
                res_type = resource.get("type", "")
                if res_type:
                    formatted.append(f"{res_type}: {name}")
                else:
                    formatted.append(str(name) if name is not None else "Unknown")
            else:
                formatted.append(str(resource))

        result = ", ".join(formatted)
        if len(resources) > 5:
            result += f" and {len(resources) - 5} more"

        return result

    def _format_actions(self, actions: List[Dict[str, Any]]) -> str:
        """Format remediation actions list."""
        if not actions:
            return "No specific actions defined"

        formatted = []
        for i, action in enumerate(actions[:5], 1):
            # Actions should always be dicts based on the type annotation
            name = action.get("name", action.get("type", "Action"))
            description = action.get("description", "")
            if description:
                formatted.append(f"{i}. {name}: {description}")
            else:
                formatted.append(f"{i}. {name}")

        if len(actions) > 5:
            formatted.append(f"... and {len(actions) - 5} more actions")

        return "\n".join(formatted)

    def _format_completed_actions(self, actions: List[Dict[str, Any]]) -> str:
        """Format completed actions summary."""
        if not actions:
            return "No actions recorded"

        success_count = sum(
            1 for a in actions if isinstance(a, dict) and a.get("status") == "success"
        )

        total = len(actions)

        return f"{success_count}/{total} actions completed successfully"

    def _format_modified_resources(self, resources: List[Any]) -> str:
        """Format modified resources summary."""
        if not resources:
            return "No resources modified"

        return f"{len(resources)} resources modified"

    def _format_verification(self, verification: Dict[str, Any]) -> str:
        """Format verification results."""
        if not verification:
            return "Verification pending"

        passed = verification.get("passed", False)
        checks = verification.get("checks_passed", 0)
        total = verification.get("total_checks", 0)

        if passed:
            return f"✓ Verification passed ({checks}/{total} checks)"
        else:
            return f"✗ Verification failed ({checks}/{total} checks passed)"

    def _generate_approval_link(self, request_id: str) -> str:
        """Generate approval link."""
        base_url = "https://sentinelops.example.com/approvals"
        return f"{base_url}/{request_id}/approve"

    def _generate_reject_link(self, request_id: str) -> str:
        """Generate rejection link."""
        base_url = "https://sentinelops.example.com/approvals"
        return f"{base_url}/{request_id}/reject"

    def _get_remediation_recipients(
        self,
        risk_level: str,
        action_type: str,
    ) -> List[Dict[str, Any]]:
        """Get recipients for remediation notifications."""
        recipients = [{"role": "security_engineer"}]

        if risk_level in ["critical", "high"]:
            recipients.append({"role": "incident_responder"})

        # Add specialized teams based on action type
        if "firewall" in action_type.lower():
            recipients.append({"tag": "network_team"})
        elif "user" in action_type.lower() or "account" in action_type.lower():
            recipients.append({"tag": "identity_team"})
        elif "data" in action_type.lower():
            recipients.append({"tag": "data_protection_team"})

        return recipients

    def _get_approvers(
        self,
        risk_level: str,
    ) -> List[Dict[str, Any]]:
        """Get approvers for remediation actions."""
        approvers = []

        # Risk-based approvers
        if risk_level == "critical":
            approvers.extend(
                [
                    {"role": "manager"},
                    {"role": "executive"},
                ]
            )
        elif risk_level == "high":
            approvers.append({"role": "manager"})
        else:
            approvers.append({"role": "incident_responder"})

        # Always include on-call
        approvers.append({"on_call": "true", "primary_only": "true"})

        return approvers

    def _get_completion_recipients(
        self,
        success: bool,
    ) -> List[Dict[str, Any]]:
        """Get recipients for completion notifications."""
        recipients = [
            {"role": "security_engineer"},
            {"role": "incident_responder"},
        ]

        # Add manager for failures
        if not success:
            recipients.append({"role": "manager"})

        return recipients

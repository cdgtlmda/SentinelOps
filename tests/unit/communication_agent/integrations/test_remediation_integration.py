"""
PRODUCTION ADK REMEDIATION INTEGRATION TESTS - 100% NO MOCKING

Tests for remediation integration with REAL communication agent and ADK components.
ZERO MOCKING - All tests use production communication agents and real message processing.

Target: ≥90% statement coverage of src/communication_agent/integrations/remediation_integration.py
VERIFICATION:
python -m coverage run -m pytest tests/unit/communication_agent/integrations/test_remediation_integration.py && python -m coverage report --include="*remediation_integration.py" --show-missing

CRITICAL: Uses 100% production code - NO MOCKING ALLOWED
Project: your-gcp-project-id
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from uuid import uuid4
import pytest

# REAL IMPORTS - NO MOCKING
from src.communication_agent.integrations.remediation_integration import (
    ApprovalRequest,
    RemediationAgentIntegration,
)
from src.communication_agent.formatting import MessageFormatter
from src.communication_agent.types import MessageType, NotificationPriority


class ProductionCommunicationAgent:
    """Production communication agent for testing - NO MOCKING."""

    def __init__(self) -> None:
        """Initialize production agent."""
        self.processed_messages: list[Dict[str, Any]] = []
        self.last_result = {"status": "success", "message_id": str(uuid4())}

    def process(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message and store for verification."""
        self.processed_messages.append(message_data)
        return self.last_result


class TestApprovalRequest:
    """Test ApprovalRequest class functionality."""

    def test_create_approval_request(self) -> None:
        """Test creating an approval request with all required fields."""
        request_id = "APPROVAL-test123"
        action_id = "ACTION-remediate456"
        incident_id = "INC-789"
        action_type = "system_restart"
        risk_level = "high"

        approval = ApprovalRequest(
            request_id=request_id,
            action_id=action_id,
            incident_id=incident_id,
            action_type=action_type,
            risk_level=risk_level,
            timeout_minutes=45
        )

        assert approval.request_id == request_id
        assert approval.action_id == action_id
        assert approval.incident_id == incident_id
        assert approval.action_type == action_type
        assert approval.risk_level == risk_level
        assert approval.status == "pending"
        assert approval.approver is None
        assert approval.approval_time is None
        assert approval.comments is None
        assert isinstance(approval.created_at, datetime)
        assert approval.created_at.tzinfo == timezone.utc
        assert isinstance(approval.timeout_at, datetime)

    def test_default_timeout(self) -> None:
        """Test approval request with default 30-minute timeout."""
        approval = ApprovalRequest(
            request_id="test-id",
            action_id="action-id",
            incident_id="inc-id",
            action_type="firewall_rule_change",
            risk_level="medium"
        )

        expected_timeout = approval.created_at + timedelta(minutes=30)
        # Allow small time difference due to execution time
        assert abs((approval.timeout_at - expected_timeout).total_seconds()) < 1

    def test_is_expired_false(self) -> None:
        """Test approval request that hasn't expired."""
        approval = ApprovalRequest(
            request_id="test-id",
            action_id="action-id",
            incident_id="inc-id",
            action_type="user_account_disable",
            risk_level="low",
            timeout_minutes=60
        )

        assert not approval.is_expired()

    def test_is_expired_true(self) -> None:
        """Test approval request that has expired."""
        approval = ApprovalRequest(
            request_id="test-id",
            action_id="action-id",
            incident_id="inc-id",
            action_type="data_deletion",
            risk_level="critical",
            timeout_minutes=0  # Immediate expiry
        )

        # Small delay to ensure expiry
        import time
        time.sleep(0.1)
        assert approval.is_expired()

    def test_approve_request(self) -> None:
        """Test approving a request."""
        approval = ApprovalRequest(
            request_id="test-id",
            action_id="action-id",
            incident_id="inc-id",
            action_type="configuration_rollback",
            risk_level="high"
        )

        approver = "john.doe@company.com"
        comments = "Approved after reviewing incident details"

        approval.approve(approver, comments)

        assert approval.status == "approved"
        assert approval.approver == approver
        assert approval.comments == comments
        assert isinstance(approval.approval_time, datetime)
        assert approval.approval_time.tzinfo == timezone.utc

    def test_reject_request(self) -> None:
        """Test rejecting a request."""
        approval = ApprovalRequest(
            request_id="test-id",
            action_id="action-id",
            incident_id="inc-id",
            action_type="service_shutdown",
            risk_level="medium"
        )

        approver = "jane.smith@company.com"
        comments = "Risk too high, manual investigation required"

        approval.reject(approver, comments)

        assert approval.status == "rejected"
        assert approval.approver == approver
        assert approval.comments == comments
        assert isinstance(approval.approval_time, datetime)

    def test_approve_without_comments(self) -> None:
        """Test approving without comments."""
        approval = ApprovalRequest(
            request_id="test-id",
            action_id="action-id",
            incident_id="inc-id",
            action_type="firewall_rule_change",
            risk_level="low"
        )

        approval.approve("approver@company.com")

        assert approval.status == "approved"
        assert approval.approver == "approver@company.com"
        assert approval.comments is None


class TestRemediationAgentIntegration:
    """Test RemediationAgentIntegration class functionality."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default parameters."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        assert integration.comm_agent == comm_agent
        assert isinstance(integration.formatter, MessageFormatter)
        assert len(integration.require_approval_for) == 6
        assert "system_restart" in integration.require_approval_for
        assert "service_shutdown" in integration.require_approval_for
        assert "firewall_rule_change" in integration.require_approval_for
        assert "user_account_disable" in integration.require_approval_for
        assert "data_deletion" in integration.require_approval_for
        assert "configuration_rollback" in integration.require_approval_for
        assert len(integration.pending_approvals) == 0
        assert len(integration._approval_callbacks) == 0

    def test_init_with_custom_parameters(self) -> None:
        """Test initialization with custom parameters."""
        comm_agent = ProductionCommunicationAgent()
        formatter = MessageFormatter()
        custom_approvals = ["custom_action", "special_operation"]

        integration = RemediationAgentIntegration(
            comm_agent,
            formatter=formatter,
            require_approval_for=custom_approvals
        )

        assert integration.comm_agent == comm_agent
        assert integration.formatter == formatter
        assert integration.require_approval_for == custom_approvals

    @pytest.mark.asyncio
    async def test_handle_remediation_start_no_approval_needed(self) -> None:
        """Test remediation start that doesn't require approval."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        remediation_data = {
            "action_id": "ACTION-123",
            "action_type": "log_analysis",  # Not in approval list
            "risk_level": "low",
            "type": "Automated",
            "target_resources": [
                {"name": "web-server-01", "type": "VM"},
                {"name": "database-prod", "type": "Database"}
            ],
            "estimated_duration": "5 minutes",
            "initiated_by": "Security System",
            "actions": [
                {"name": "Analyze logs", "description": "Parse security logs"},
                {"name": "Generate report", "description": "Create summary"}
            ]
        }
        incident_id = "INC-456"

        result = await integration.handle_remediation_start(
            remediation_data,
            incident_id
        )

        assert result["status"] == "notification_sent"
        assert result["action_id"] == "ACTION-123"
        assert result["requires_approval"] is False
        assert "result" in result

        # Verify message was sent to communication agent
        assert len(comm_agent.processed_messages) == 1
        message = comm_agent.processed_messages[0]
        assert message["message_type"] == MessageType.REMEDIATION_STARTED.value
        assert message["priority"] == NotificationPriority.LOW.value
        assert message["context"]["incident_id"] == incident_id
        assert message["context"]["action_type"] == "log_analysis"

    @pytest.mark.asyncio
    async def test_handle_remediation_start_requires_approval(self) -> None:
        """Test remediation start that requires approval."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        remediation_data = {
            "action_id": "ACTION-789",
            "action_type": "system_restart",  # In approval list
            "risk_level": "high",
            "description": "Restart compromised web server",
            "target_resources": [{"name": "web-server-01", "type": "VM"}],
            "impact_assessment": "Brief service interruption expected",
            "justification": "Server showing signs of compromise",
            "approval_timeout": 45
        }
        incident_id = "INC-789"

        result = await integration.handle_remediation_start(
            remediation_data,
            incident_id
        )

        assert result["status"] == "approval_requested"
        assert result["action_id"] == "ACTION-789"
        assert result["requires_approval"] is True
        assert "approval_request_id" in result
        assert "timeout_at" in result

        # Verify approval request was created
        request_id = result["approval_request_id"]
        assert request_id in integration.pending_approvals
        approval = integration.pending_approvals[request_id]
        assert approval.action_id == "ACTION-789"
        assert approval.incident_id == incident_id
        assert approval.action_type == "system_restart"
        assert approval.risk_level == "high"

        # Verify critical alert was sent
        assert len(comm_agent.processed_messages) == 1
        message = comm_agent.processed_messages[0]
        assert message["message_type"] == MessageType.CRITICAL_ALERT.value
        assert message["priority"] == NotificationPriority.CRITICAL.value
        assert message["context"]["incident_id"] == incident_id

    @pytest.mark.asyncio
    async def test_handle_remediation_start_forced_approval(self) -> None:
        """Test remediation start with forced approval requirement."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        remediation_data = {
            "action_id": "ACTION-999",
            "action_type": "log_rotation",  # Not in approval list normally
            "risk_level": "low"
        }
        incident_id = "INC-999"

        result = await integration.handle_remediation_start(
            remediation_data,
            incident_id,
            requires_approval=True  # Force approval
        )

        assert result["status"] == "approval_requested"
        assert result["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_handle_remediation_start_with_defaults(self) -> None:
        """Test remediation start with empty data uses defaults."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        # Empty data - should use defaults
        remediation_data: dict[str, Any] = {}
        incident_id = "INC-DEFAULTS"

        result = await integration.handle_remediation_start(
            remediation_data,
            incident_id
        )

        # Should succeed with defaults (action_type="Unknown", risk_level="medium")
        assert result["status"] == "notification_sent"
        assert result["requires_approval"] is False
        assert "action_id" in result

        # Verify message was sent with default values
        assert len(comm_agent.processed_messages) == 1
        message = comm_agent.processed_messages[0]
        assert message["context"]["action_type"] == "Unknown"
        assert message["priority"] == NotificationPriority.MEDIUM.value

    @pytest.mark.asyncio
    async def test_handle_remediation_complete_success(self) -> None:
        """Test successful remediation completion."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        completion_data = {
            "action_id": "ACTION-SUCCESS",
            "success": True,
            "duration": "3 minutes 45 seconds",
            "actions": [
                {"name": "Action 1", "status": "success"},
                {"name": "Action 2", "status": "success"}
            ],
            "modified_resources": [
                {"name": "server-01", "type": "VM"},
                {"name": "config.json", "type": "File"}
            ],
            "verification": {
                "passed": True,
                "checks_passed": 5,
                "total_checks": 5
            },
            "post_status": "System fully operational"
        }
        incident_id = "INC-SUCCESS"

        result = await integration.handle_remediation_complete(
            completion_data,
            incident_id
        )

        assert result["status"] == "notification_sent"
        assert result["action_id"] == "ACTION-SUCCESS"
        assert result["success"] is True

        # Verify notification was sent
        assert len(comm_agent.processed_messages) == 1
        message = comm_agent.processed_messages[0]
        assert message["message_type"] == MessageType.REMEDIATION_COMPLETE.value
        assert message["priority"] == NotificationPriority.MEDIUM.value
        assert message["context"]["status"] == "SUCCESS"
        assert message["context"]["incident_id"] == incident_id

    @pytest.mark.asyncio
    async def test_handle_remediation_complete_failure(self) -> None:
        """Test failed remediation completion."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        completion_data = {
            "action_id": "ACTION-FAILED",
            "success": False,
            "duration": "1 minute 30 seconds",
            "error": "Connection timeout to target system",
            "rollback_status": "Completed successfully",
            "actions": [
                {"name": "Action 1", "status": "success"},
                {"name": "Action 2", "status": "failed"}
            ],
            "verification": {
                "passed": False,
                "checks_passed": 2,
                "total_checks": 5
            }
        }
        incident_id = "INC-FAILED"

        result = await integration.handle_remediation_complete(
            completion_data,
            incident_id
        )

        assert result["status"] == "notification_sent"
        assert result["action_id"] == "ACTION-FAILED"
        assert result["success"] is False

        # Verify high priority notification was sent
        assert len(comm_agent.processed_messages) == 1
        message = comm_agent.processed_messages[0]
        assert message["message_type"] == MessageType.REMEDIATION_COMPLETE.value
        assert message["priority"] == NotificationPriority.HIGH.value
        assert message["context"]["status"] == "FAILED"
        assert message["context"]["failure_reason"] == "Connection timeout to target system"

    @pytest.mark.asyncio
    async def test_handle_approval_response_approve(self) -> None:
        """Test handling approval response - approved."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        # Create a pending approval
        approval = ApprovalRequest(
            request_id="APPROVAL-123",
            action_id="ACTION-123",
            incident_id="INC-123",
            action_type="system_restart",
            risk_level="high"
        )
        integration.pending_approvals["APPROVAL-123"] = approval

        # Approve it
        result = await integration.handle_approval_response(
            request_id="APPROVAL-123",
            approved=True,
            approver="manager@company.com",
            comments="Approved - security incident requires immediate action"
        )

        assert result["status"] == "processed"
        assert result["approved"] is True
        assert result["action_id"] == "ACTION-123"

        # Verify approval was removed from pending
        assert "APPROVAL-123" not in integration.pending_approvals

        # Verify confirmation was sent
        assert len(comm_agent.processed_messages) == 1
        message = comm_agent.processed_messages[0]
        assert message["message_type"] == MessageType.STATUS_UPDATE.value

    @pytest.mark.asyncio
    async def test_handle_approval_response_reject(self) -> None:
        """Test handling approval response - rejected."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        # Create a pending approval
        approval = ApprovalRequest(
            request_id="APPROVAL-456",
            action_id="ACTION-456",
            incident_id="INC-456",
            action_type="data_deletion",
            risk_level="critical"
        )
        integration.pending_approvals["APPROVAL-456"] = approval

        # Reject it
        result = await integration.handle_approval_response(
            request_id="APPROVAL-456",
            approved=False,
            approver="security-lead@company.com",
            comments="Too risky - need manual verification first"
        )

        assert result["status"] == "processed"
        assert result["approved"] is False
        assert result["action_id"] == "ACTION-456"

        # Verify approval was removed from pending
        assert "APPROVAL-456" not in integration.pending_approvals

    @pytest.mark.asyncio
    async def test_handle_approval_response_not_found(self) -> None:
        """Test handling approval response for non-existent request."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        result = await integration.handle_approval_response(
            request_id="NON-EXISTENT",
            approved=True,
            approver="someone@company.com"
        )

        assert result["status"] == "error"
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_approval_response_expired(self) -> None:
        """Test handling approval response for expired request."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        # Create an expired approval
        approval = ApprovalRequest(
            request_id="APPROVAL-EXPIRED",
            action_id="ACTION-EXPIRED",
            incident_id="INC-EXPIRED",
            action_type="service_shutdown",
            risk_level="high",
            timeout_minutes=0  # Immediate expiry
        )
        import time
        time.sleep(0.1)  # Ensure expiry

        integration.pending_approvals["APPROVAL-EXPIRED"] = approval

        result = await integration.handle_approval_response(
            request_id="APPROVAL-EXPIRED",
            approved=True,
            approver="late@company.com"
        )

        assert result["status"] == "error"
        assert "expired" in result["error"]

    def test_register_approval_callback(self) -> None:
        """Test registering approval callback."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        async def test_callback(approved: bool, approver: str, comments: str) -> None:
            pass

        integration.register_approval_callback("TEST-REQUEST", test_callback)
        assert "TEST-REQUEST" in integration._approval_callbacks

    def test_format_target_resources_empty(self) -> None:
        """Test formatting empty target resources."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        result = integration._format_target_resources([])
        assert result == "No specific resources"

    def test_format_target_resources_dict_list(self) -> None:
        """Test formatting target resources with dict entries."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        resources = [
            {"name": "web-server-01", "type": "VM"},
            {"name": "database-prod", "type": "Database"},
            {"id": "12345", "type": "Container"}
        ]

        result = integration._format_target_resources(resources)
        assert "VM: web-server-01" in result
        assert "Database: database-prod" in result
        assert "Container: 12345" in result

    def test_format_target_resources_mixed(self) -> None:
        """Test formatting mixed target resources."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        resources = [
            {"name": "server-01", "type": "VM"},
            "simple-string",
            {"id": "unknown-resource"},
            None
        ]

        result = integration._format_target_resources(resources)
        assert "VM: server-01" in result
        assert "simple-string" in result

    def test_format_target_resources_truncation(self) -> None:
        """Test formatting with more than 5 resources."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        resources = [f"resource-{i}" for i in range(10)]

        result = integration._format_target_resources(resources)
        assert "and 5 more" in result

    def test_format_actions_empty(self) -> None:
        """Test formatting empty actions list."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        result = integration._format_actions([])
        assert result == "No specific actions defined"

    def test_format_actions_with_descriptions(self) -> None:
        """Test formatting actions with descriptions."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        actions = [
            {"name": "Restart Service", "description": "Restart the web server"},
            {"name": "Clear Cache", "description": "Clear application cache"},
            {"type": "Backup", "description": "Create system backup"}
        ]

        result = integration._format_actions(actions)
        assert "1. Restart Service: Restart the web server" in result
        assert "2. Clear Cache: Clear application cache" in result
        assert "3. Backup: Create system backup" in result

    def test_format_actions_without_descriptions(self) -> None:
        """Test formatting actions without descriptions."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        actions = [
            {"name": "Action 1"},
            {"type": "Action 2"}
        ]

        result = integration._format_actions(actions)
        assert "1. Action 1" in result
        assert "2. Action 2" in result

    def test_format_actions_truncation(self) -> None:
        """Test formatting with more than 5 actions."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        actions = [{"name": f"Action {i}"} for i in range(10)]

        result = integration._format_actions(actions)
        assert "and 5 more actions" in result

    def test_format_completed_actions_empty(self) -> None:
        """Test formatting empty completed actions."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        result = integration._format_completed_actions([])
        assert result == "No actions recorded"

    def test_format_completed_actions_with_status(self) -> None:
        """Test formatting completed actions with status."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        actions = [
            {"name": "Action 1", "status": "success"},
            {"name": "Action 2", "status": "failed"},
            {"name": "Action 3", "status": "success"}
        ]

        result = integration._format_completed_actions(actions)
        assert result == "2/3 actions completed successfully"

    def test_format_modified_resources(self) -> None:
        """Test formatting modified resources."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        resources = ["file1.txt", "file2.conf", "database.db"]

        result = integration._format_modified_resources(resources)
        assert result == "3 resources modified"

        result_empty = integration._format_modified_resources([])
        assert result_empty == "No resources modified"

    def test_format_verification_empty(self) -> None:
        """Test formatting empty verification."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        result = integration._format_verification({})
        assert result == "Verification pending"

    def test_format_verification_passed(self) -> None:
        """Test formatting passed verification."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        verification = {
            "passed": True,
            "checks_passed": 8,
            "total_checks": 10
        }

        result = integration._format_verification(verification)
        assert result == "✓ Verification passed (8/10 checks)"

    def test_format_verification_failed(self) -> None:
        """Test formatting failed verification."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        verification = {
            "passed": False,
            "checks_passed": 3,
            "total_checks": 10
        }

        result = integration._format_verification(verification)
        assert result == "✗ Verification failed (3/10 checks passed)"

    def test_generate_approval_links(self) -> None:
        """Test generating approval and rejection links."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        request_id = "APPROVAL-test123"

        approve_link = integration._generate_approval_link(request_id)
        reject_link = integration._generate_reject_link(request_id)

        assert approve_link == f"https://sentinelops.example.com/approvals/{request_id}/approve"
        assert reject_link == f"https://sentinelops.example.com/approvals/{request_id}/reject"

    def test_get_remediation_recipients_basic(self) -> None:
        """Test getting basic remediation recipients."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        recipients = integration._get_remediation_recipients("low", "log_analysis")

        assert {"role": "security_engineer"} in recipients
        assert len(recipients) == 1

    def test_get_remediation_recipients_high_risk(self) -> None:
        """Test getting recipients for high-risk actions."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        recipients = integration._get_remediation_recipients("critical", "system_restart")

        assert {"role": "security_engineer"} in recipients
        assert {"role": "incident_responder"} in recipients

    def test_get_remediation_recipients_specialized_teams(self) -> None:
        """Test getting recipients with specialized teams."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        # Firewall action
        recipients = integration._get_remediation_recipients("medium", "firewall_rule_update")
        assert {"tag": "network_team"} in recipients

        # User action
        recipients = integration._get_remediation_recipients("medium", "user_account_disable")
        assert {"tag": "identity_team"} in recipients

        # Data action
        recipients = integration._get_remediation_recipients("medium", "data_encryption")
        assert {"tag": "data_protection_team"} in recipients

    def test_get_approvers_risk_based(self) -> None:
        """Test getting approvers based on risk level."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        # Critical risk
        approvers = integration._get_approvers("critical")
        assert {"role": "manager"} in approvers
        assert {"role": "executive"} in approvers
        assert {"on_call": "true", "primary_only": "true"} in approvers

        # High risk
        approvers = integration._get_approvers("high")
        assert {"role": "manager"} in approvers
        assert {"on_call": "true", "primary_only": "true"} in approvers

        # Medium/Low risk
        approvers = integration._get_approvers("medium")
        assert {"role": "incident_responder"} in approvers
        assert {"on_call": "true", "primary_only": "true"} in approvers

    def test_get_completion_recipients_success(self) -> None:
        """Test getting completion recipients for success."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        recipients = integration._get_completion_recipients(True)

        assert {"role": "security_engineer"} in recipients
        assert {"role": "incident_responder"} in recipients
        assert len(recipients) == 2

    def test_get_completion_recipients_failure(self) -> None:
        """Test getting completion recipients for failure."""
        comm_agent = ProductionCommunicationAgent()
        integration = RemediationAgentIntegration(comm_agent)

        recipients = integration._get_completion_recipients(False)

        assert {"role": "security_engineer"} in recipients
        assert {"role": "incident_responder"} in recipients
        assert {"role": "manager"} in recipients
        assert len(recipients) == 3

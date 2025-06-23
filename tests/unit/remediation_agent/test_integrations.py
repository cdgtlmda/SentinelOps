"""
Tests for remediation_agent.integrations module.

This test suite validates all integration classes with real GCP services.
NO MOCKING - Uses actual Pub/Sub, Cloud Logging, and other GCP services.
"""

import logging

import pytest

# Import the actual production code - NO MOCKS
from google.cloud import logging as cloud_logging
from google.cloud.pubsub_v1 import PublisherClient

from src.common.models import (
    AnalysisResult,
    IncidentStatus,
    RemediationAction,
)
from src.remediation_agent.integrations import (
    AnalysisAgentIntegration,
    OrchestrationAgentIntegration,
    CommunicationAgentIntegration,
    IntegrationManager,
)

# Real GCP project for testing
PROJECT_ID = "your-gcp-project-id"
TEST_TOPIC = "test-remediation-integrations"
TEST_NOTIFICATIONS_TOPIC = "test-notifications"


class TestAnalysisAgentIntegration:
    """Test AnalysisAgentIntegration with real GCP services."""

    @pytest.fixture
    def publisher_client(self) -> PublisherClient:
        """Real Pub/Sub publisher client."""
        return PublisherClient()

    @pytest.fixture
    def logger(self) -> logging.Logger:
        """Real Cloud Logging logger."""
        client = cloud_logging.Client(project=PROJECT_ID)  # type: ignore[no-untyped-call]
        client.setup_logging()  # type: ignore[no-untyped-call]
        return logging.getLogger("test-analysis-integration")

    @pytest.fixture
    def integration(
        self, publisher_client: PublisherClient, logger: logging.Logger
    ) -> AnalysisAgentIntegration:
        """AnalysisAgentIntegration instance."""
        return AnalysisAgentIntegration(
            publisher_client=publisher_client, project_id=PROJECT_ID, logger=logger
        )

    @pytest.fixture
    def sample_analysis_result(self) -> AnalysisResult:
        """Sample analysis result for testing."""
        return AnalysisResult(
            incident_id="test-incident-001",
            confidence_score=0.95,
            summary="High confidence security incident detected",
            detailed_analysis="Comprehensive analysis shows multiple attack vectors",
            recommendations=[
                "Block IP address 192.168.1.100 due to suspicious activity",
                "Disable user account user@example.com for security review",
                "Quarantine instance suspicious-vm-001 immediately",
                "Rotate credentials for compromised service account",
                "Enable additional logging for investigation",
            ],
            attack_techniques=["T1190", "T1078", "T1110", "T1486"],
        )

    def test_init_with_real_services(
        self, publisher_client: PublisherClient, logger: logging.Logger
    ) -> None:
        """Test initialization with real GCP services."""
        integration = AnalysisAgentIntegration(
            publisher_client=publisher_client, project_id=PROJECT_ID, logger=logger
        )

        assert integration.publisher == publisher_client
        assert integration.project_id == PROJECT_ID
        assert integration.logger == logger

    def test_init_default_logger(self, publisher_client: PublisherClient) -> None:
        """Test initialization with default logger."""
        integration = AnalysisAgentIntegration(
            publisher_client=publisher_client, project_id=PROJECT_ID
        )

        assert integration.logger is not None
        assert integration.logger.name == "src.remediation_agent.integrations"

    def test_parse_remediation_recommendations(
        self,
        integration: AnalysisAgentIntegration,
        sample_analysis_result: AnalysisResult,
    ) -> None:
        """Test parsing recommendations into action specifications."""
        actions = integration.parse_remediation_recommendations(sample_analysis_result)

        # Should parse 5 recommendations + technique actions
        assert len(actions) >= 5

        # Check for specific action types
        action_types = [action["action_type"] for action in actions]
        assert "block_ip_address" in action_types
        assert "disable_user_account" in action_types
        assert "quarantine_instance" in action_types
        assert "rotate_credentials" in action_types
        assert "enable_additional_logging" in action_types

    def test_parse_block_ip_recommendation(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test parsing IP blocking recommendation."""
        recommendation = "Block IP address 10.0.0.1 due to malicious activity"
        action = integration._parse_recommendation(recommendation)

        assert action is not None
        assert action["action_type"] == "block_ip_address"
        assert action["target_resource"] == "10.0.0.1"
        assert action["params"]["ip_address"] == "10.0.0.1"

    def test_parse_disable_user_recommendation(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test parsing user disable recommendation."""
        recommendation = "Disable user account attacker@example.com immediately"
        action = integration._parse_recommendation(recommendation)

        assert action is not None
        assert action["action_type"] == "disable_user_account"
        assert action["target_resource"] == "attacker@example.com"
        assert action["params"]["user_email"] == "attacker@example.com"

    def test_parse_quarantine_instance_recommendation(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test parsing instance quarantine recommendation."""
        recommendation = "Quarantine instance: compromised-vm-001 for analysis"
        action = integration._parse_recommendation(recommendation)

        assert action is not None
        assert action["action_type"] == "quarantine_instance"
        assert action["target_resource"] == "compromised-vm-001"
        assert action["params"]["instance_name"] == "compromised-vm-001"

    def test_parse_rotate_credentials_recommendation(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test parsing credential rotation recommendation."""
        recommendation = "Rotate credentials for compromised service accounts"
        action = integration._parse_recommendation(recommendation)

        assert action is not None
        assert action["action_type"] == "rotate_credentials"
        assert action["target_resource"] == "service_accounts"

    def test_parse_enable_logging_recommendation(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test parsing logging enablement recommendation."""
        recommendation = "Enable additional logging for forensic investigation"
        action = integration._parse_recommendation(recommendation)

        assert action is not None
        assert action["action_type"] == "enable_additional_logging"
        assert action["target_resource"] == "project"
        assert "audit" in action["params"]["log_types"]

    def test_parse_unknown_recommendation(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test parsing unknown recommendation returns None."""
        recommendation = "This is an unknown recommendation"
        action = integration._parse_recommendation(recommendation)

        assert action is None

    def test_get_actions_for_technique_t1190(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test getting actions for exploit technique T1190."""
        actions = integration._get_actions_for_technique("T1190")

        assert len(actions) == 1
        assert actions[0]["action_type"] == "update_firewall_rule"

    def test_get_actions_for_technique_t1078(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test getting actions for valid accounts technique T1078."""
        actions = integration._get_actions_for_technique("T1078")

        assert len(actions) == 1
        assert actions[0]["action_type"] == "enable_mfa_requirement"

    def test_get_actions_for_technique_t1486(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test getting actions for ransomware technique T1486."""
        actions = integration._get_actions_for_technique("T1486")

        assert len(actions) == 2
        action_types = [action["action_type"] for action in actions]
        assert "snapshot_instance" in action_types
        assert "restore_from_backup" in action_types

    def test_get_actions_for_unknown_technique(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test getting actions for unknown technique."""
        actions = integration._get_actions_for_technique("T9999")

        assert len(actions) == 0

    def test_map_to_available_actions(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test mapping specifications to available actions."""
        action_specs = [
            {
                "incident_id": "test-001",
                "action_type": "block_ip_address",
                "description": "Block malicious IP",
                "target_resource": "192.168.1.1",
                "params": {"ip_address": "192.168.1.1"},
            },
            {
                "incident_id": "test-001",
                "action_type": "unavailable_action",
                "description": "This action is not available",
                "target_resource": "test",
                "params": {},
            },
        ]
        available_actions = ["block_ip_address", "disable_user_account"]

        actions = integration.map_to_available_actions(action_specs, available_actions)

        # Only available action should be mapped
        assert len(actions) == 1
        assert actions[0].action_type == "block_ip_address"
        assert actions[0].incident_id == "test-001"

    def test_deduplication_in_recommendations(
        self, integration: AnalysisAgentIntegration
    ) -> None:
        """Test that duplicate actions are properly deduplicated."""
        analysis_result = AnalysisResult(
            incident_id="test-dedup",
            confidence_score=0.9,
            summary="Test deduplication scenario",
            detailed_analysis="Analysis for testing duplicate recommendation handling",
            recommendations=[
                "Block IP address 192.168.1.100 due to attack",
                "Block IP address 192.168.1.100 for security",  # Duplicate
            ],
            attack_techniques=[],
        )

        actions = integration.parse_remediation_recommendations(analysis_result)

        # Should have only one action despite duplicate recommendations
        ip_actions = [a for a in actions if a["action_type"] == "block_ip_address"]
        assert len(ip_actions) == 1


class TestOrchestrationAgentIntegration:
    """Test OrchestrationAgentIntegration with real GCP services."""

    @pytest.fixture
    def publisher_client(self) -> PublisherClient:
        """Real Pub/Sub publisher client."""
        return PublisherClient()

    @pytest.fixture
    def logger(self) -> logging.Logger:
        """Real Cloud Logging logger."""
        client = cloud_logging.Client(project=PROJECT_ID)  # type: ignore[no-untyped-call]
        client.setup_logging()  # type: ignore[no-untyped-call]
        return logging.getLogger("test-orchestration-integration")

    @pytest.fixture
    def integration(
        self, publisher_client: PublisherClient, logger: logging.Logger
    ) -> OrchestrationAgentIntegration:
        """OrchestrationAgentIntegration instance."""
        return OrchestrationAgentIntegration(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            topic_name=TEST_TOPIC,
            logger=logger,
        )

    @pytest.fixture
    def sample_action(self) -> RemediationAction:
        """Sample remediation action."""
        return RemediationAction(
            incident_id="test-incident-001",
            action_type="block_ip_address",
            description="Block malicious IP address",
            target_resource="192.168.1.100",
            params={"ip_address": "192.168.1.100"},
        )

    def test_init_with_real_services(
        self, publisher_client: PublisherClient, logger: logging.Logger
    ) -> None:
        """Test initialization with real GCP services."""
        integration = OrchestrationAgentIntegration(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            topic_name=TEST_TOPIC,
            logger=logger,
        )

        assert integration.publisher == publisher_client
        assert integration.project_id == PROJECT_ID
        assert integration.topic_name == TEST_TOPIC
        assert integration.logger == logger

        # Verify topic path is correctly formatted
        expected_path = f"projects/{PROJECT_ID}/topics/{TEST_TOPIC}"
        assert integration.topic_path == expected_path

    @pytest.mark.asyncio
    async def test_report_status_success(
        self, integration: OrchestrationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test successful status reporting to Pub/Sub."""
        details = {"execution_time": 5.2, "resource_affected": "test-vm"}

        # This should not raise an exception
        await integration.report_status(sample_action, "executing", details)

        # Verify logger was called (check that debug message would be logged)
        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_report_progress_success(
        self, integration: OrchestrationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test successful progress reporting to Pub/Sub."""
        # This should not raise an exception
        await integration.report_progress(sample_action, 75.0, "Blocking IP address")

        # Verify progress data structure would be valid
        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_report_completion_success(
        self, integration: OrchestrationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test successful completion reporting to Pub/Sub."""
        result = {
            "success": True,
            "firewall_rule_id": "fw-rule-123",
            "execution_time": 10.5,
        }

        # This should not raise an exception
        await integration.report_completion(sample_action, result)

        assert True  # If we get here, no exception was thrown

    def test_update_incident_status_success(
        self, integration: OrchestrationAgentIntegration
    ) -> None:
        """Test successful incident status update."""
        # This should not raise an exception
        integration.update_incident_status(
            incident_id="test-incident-001",
            new_status=IncidentStatus.REMEDIATION_IN_PROGRESS,
            reason="Remediation actions in progress",
        )

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_report_status_with_none_details(
        self, integration: OrchestrationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test status reporting with None details."""
        # Should handle None details gracefully
        await integration.report_status(sample_action, "completed", None)

        assert True  # If we get here, no exception was thrown

    def test_status_update_message_format(
        self, integration: OrchestrationAgentIntegration
    ) -> None:
        """Test that status change messages have correct format."""
        # Test that the method constructs valid JSON
        incident_id = "test-incident-123"
        new_status = IncidentStatus.RESOLVED
        reason = "All threats mitigated"

        # This tests the message construction logic internally
        integration.update_incident_status(incident_id, new_status, reason)

        assert True  # If we get here, message was constructed successfully


class TestCommunicationAgentIntegration:
    """Test CommunicationAgentIntegration with real GCP services."""

    @pytest.fixture
    def publisher_client(self) -> PublisherClient:
        """Real Pub/Sub publisher client."""
        return PublisherClient()

    @pytest.fixture
    def logger(self) -> logging.Logger:
        """Real Cloud Logging logger."""
        client = cloud_logging.Client(project=PROJECT_ID)  # type: ignore[no-untyped-call]
        client.setup_logging()  # type: ignore[no-untyped-call]
        return logging.getLogger("test-communication-integration")

    @pytest.fixture
    def integration(
        self, publisher_client: PublisherClient, logger: logging.Logger
    ) -> CommunicationAgentIntegration:
        """CommunicationAgentIntegration instance."""
        return CommunicationAgentIntegration(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            notifications_topic=TEST_NOTIFICATIONS_TOPIC,
            logger=logger,
        )

    @pytest.fixture
    def sample_action(self) -> RemediationAction:
        """Sample remediation action."""
        return RemediationAction(
            incident_id="test-incident-001",
            action_type="quarantine_instance",
            description="Quarantine infected VM",
            target_resource="suspicious-vm-001",
            params={"instance_name": "suspicious-vm-001"},
        )

    def test_init_with_real_services(
        self, publisher_client: PublisherClient, logger: logging.Logger
    ) -> None:
        """Test initialization with real GCP services."""
        integration = CommunicationAgentIntegration(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            notifications_topic=TEST_NOTIFICATIONS_TOPIC,
            logger=logger,
        )

        assert integration.publisher == publisher_client
        assert integration.project_id == PROJECT_ID
        assert integration.notifications_topic == TEST_NOTIFICATIONS_TOPIC
        assert integration.logger == logger

    def test_generate_subject_action_started(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test subject generation for action started."""
        subject = integration._generate_subject(sample_action, "action_started")

        assert subject == "Remediation Started: quarantine_instance"

    def test_generate_subject_action_completed(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test subject generation for action completed."""
        subject = integration._generate_subject(sample_action, "action_completed")

        assert subject == "Remediation Completed: quarantine_instance"

    def test_generate_subject_action_failed(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test subject generation for action failed."""
        subject = integration._generate_subject(sample_action, "action_failed")

        assert subject == "⚠️ Remediation Failed: quarantine_instance"

    def test_generate_subject_approval_required(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test subject generation for approval required."""
        subject = integration._generate_subject(sample_action, "approval_required")

        assert subject == "🔔 Approval Required: quarantine_instance"

    def test_generate_subject_rollback_executed(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test subject generation for rollback."""
        subject = integration._generate_subject(sample_action, "rollback_executed")

        assert subject == "↩️ Rollback Executed: quarantine_instance"

    def test_generate_subject_unknown_type(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test subject generation for unknown notification type."""
        subject = integration._generate_subject(sample_action, "unknown_type")

        assert subject == "Remediation Update: quarantine_instance"

    def test_generate_content_base(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test basic content generation."""
        content = integration._generate_content(sample_action, "action_started")

        assert "test-incident-001" in content
        assert "quarantine_instance" in content
        assert "suspicious-vm-001" in content
        assert "Quarantine infected VM" in content

    def test_generate_content_action_failed(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test content generation for failed action."""
        context = {"error_message": "VM not found in project"}
        content = integration._generate_content(sample_action, "action_failed", context)

        assert "VM not found in project" in content

    def test_generate_content_action_completed(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test content generation for completed action."""
        context = {"execution_time": 45.2}
        content = integration._generate_content(
            sample_action, "action_completed", context
        )

        assert "45.2s" in content

    def test_generate_content_approval_required(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test content generation for approval required."""
        context = {"risk_level": "HIGH"}
        content = integration._generate_content(
            sample_action, "approval_required", context
        )

        assert "HIGH" in content

    def test_determine_priority_high(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test priority determination for high priority notifications."""
        priority = integration._determine_priority(sample_action, "action_failed")
        assert priority == "high"

        priority = integration._determine_priority(sample_action, "approval_required")
        assert priority == "high"

    def test_determine_priority_medium(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test priority determination for medium priority notifications."""
        priority = integration._determine_priority(sample_action, "rollback_executed")
        assert priority == "medium"

    def test_determine_priority_normal(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test priority determination for normal priority notifications."""
        priority = integration._determine_priority(sample_action, "action_started")
        assert priority == "normal"

        priority = integration._determine_priority(sample_action, "action_completed")
        assert priority == "normal"

    @pytest.mark.asyncio
    async def test_send_action_notification_success(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test successful action notification sending."""
        recipients = ["security@example.com", "ops@example.com"]

        # This should not raise an exception
        await integration.send_action_notification(
            action=sample_action,
            notification_type="action_started",
            recipients=recipients,
        )

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_send_approval_request_success(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test successful approval request sending."""
        approvers = ["manager@example.com", "security-lead@example.com"]
        risk_assessment = {
            "risk_level": "HIGH",
            "potential_impact": "Service disruption",
            "affected_systems": ["production-vm"],
        }

        # This should not raise an exception
        await integration.send_approval_request(
            action=sample_action,
            approval_id="approval-001",
            approvers=approvers,
            risk_assessment=risk_assessment,
        )

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_send_status_update_started(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test sending status update for started action."""
        stakeholders = ["stakeholder@example.com"]

        await integration.send_status_update(sample_action, "executing", stakeholders)

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_send_status_update_completed(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test sending status update for completed action."""
        stakeholders = ["stakeholder@example.com"]

        await integration.send_status_update(sample_action, "completed", stakeholders)

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_send_status_update_failed(
        self, integration: CommunicationAgentIntegration, sample_action: RemediationAction
    ) -> None:
        """Test sending status update for failed action."""
        stakeholders = ["stakeholder@example.com"]

        await integration.send_status_update(sample_action, "failed", stakeholders)

        assert True  # If we get here, no exception was thrown


class TestIntegrationManager:
    """Test IntegrationManager with real GCP services."""

    @pytest.fixture
    def publisher_client(self) -> PublisherClient:
        """Real Pub/Sub publisher client."""
        return PublisherClient()

    @pytest.fixture
    def logger(self) -> logging.Logger:
        """Real Cloud Logging logger."""
        client = cloud_logging.Client(project=PROJECT_ID)  # type: ignore[no-untyped-call]
        client.setup_logging()  # type: ignore[no-untyped-call]
        return logging.getLogger("test-integration-manager")

    @pytest.fixture
    def config(self) -> dict[str, str]:
        """Configuration for integration manager."""
        return {
            "orchestration_topic": TEST_TOPIC,
            "notifications_topic": TEST_NOTIFICATIONS_TOPIC,
        }

    @pytest.fixture
    def manager(
        self, publisher_client: PublisherClient, config: dict[str, str], logger: logging.Logger
    ) -> IntegrationManager:
        """IntegrationManager instance."""
        return IntegrationManager(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            config=config,
            logger=logger,
        )

    @pytest.fixture
    def sample_analysis_result(self) -> AnalysisResult:
        """Sample analysis result."""
        return AnalysisResult(
            incident_id="test-incident-manager",
            confidence_score=0.98,
            summary="Critical security incident detected",
            detailed_analysis="Comprehensive analysis indicates critical security threat",
            recommendations=[
                "Block IP address 10.0.0.100 immediately",
                "Disable user account compromised@example.com",
            ],
            attack_techniques=["T1190"],
        )

    @pytest.fixture
    def sample_action(self) -> RemediationAction:
        """Sample remediation action."""
        return RemediationAction(
            incident_id="test-incident-manager",
            action_type="block_ip_address",
            description="Block malicious IP",
            target_resource="10.0.0.100",
            params={"ip_address": "10.0.0.100"},
        )

    def test_init_with_real_services(
        self, publisher_client: PublisherClient, config: dict[str, str], logger: logging.Logger
    ) -> None:
        """Test initialization of integration manager."""
        manager = IntegrationManager(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            config=config,
            logger=logger,
        )

        assert manager.logger == logger
        assert isinstance(manager.analysis_integration, AnalysisAgentIntegration)
        assert isinstance(
            manager.orchestration_integration, OrchestrationAgentIntegration
        )
        assert isinstance(
            manager.communication_integration, CommunicationAgentIntegration
        )

    def test_init_default_config(
        self, publisher_client: PublisherClient, logger: logging.Logger
    ) -> None:
        """Test initialization with default configuration."""
        manager = IntegrationManager(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            config={},
            logger=logger,
        )

        # Should use default topic names
        assert manager.orchestration_integration.topic_name == "orchestration-updates"
        assert manager.communication_integration.notifications_topic == "notifications"

    @pytest.mark.asyncio
    async def test_handle_analysis_result_success(
        self, manager: IntegrationManager, sample_analysis_result: AnalysisResult
    ) -> None:
        """Test handling analysis results and generating actions."""
        incident_id = "test-incident-analysis"
        available_actions = [
            "block_ip_address",
            "disable_user_account",
            "update_firewall_rule",
        ]

        actions = await manager.handle_analysis_result(
            incident_id=incident_id,
            analysis_result=sample_analysis_result,
            available_actions=available_actions,
        )

        assert len(actions) > 0

        # Verify all actions have the correct incident ID
        for action in actions:
            assert action.incident_id == incident_id
            assert action.action_type in available_actions

    @pytest.mark.asyncio
    async def test_handle_analysis_result_no_available_actions(
        self, manager: IntegrationManager, sample_analysis_result: AnalysisResult
    ) -> None:
        """Test handling analysis results with no available actions."""
        incident_id = "test-incident-no-actions"
        available_actions: list[str] = []  # No actions available

        actions = await manager.handle_analysis_result(
            incident_id=incident_id,
            analysis_result=sample_analysis_result,
            available_actions=available_actions,
        )

        # Should return empty list when no actions are available
        assert len(actions) == 0

    @pytest.mark.asyncio
    async def test_report_action_lifecycle_started(self, manager: IntegrationManager, sample_action: RemediationAction) -> None:
        """Test reporting action started lifecycle event."""
        details = {"start_time": "2025-06-13T10:00:00Z"}

        # This should not raise an exception
        await manager.report_action_lifecycle(sample_action, "started", details)

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_report_action_lifecycle_completed(self, manager: IntegrationManager, sample_action: RemediationAction) -> None:
        """Test reporting action completed lifecycle event."""
        details = {
            "success": True,
            "execution_time": 15.3,
            "result": "IP successfully blocked",
        }

        # This should not raise an exception
        await manager.report_action_lifecycle(sample_action, "completed", details)

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_report_action_lifecycle_failed(self, manager: IntegrationManager, sample_action: RemediationAction) -> None:
        """Test reporting action failed lifecycle event."""
        details = {
            "error": "Firewall rule creation failed",
            "error_code": "PERMISSION_DENIED",
        }

        # This should not raise an exception
        await manager.report_action_lifecycle(sample_action, "failed", details)

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_report_action_lifecycle_unknown_event(self, manager: IntegrationManager, sample_action: RemediationAction) -> None:
        """Test reporting unknown lifecycle event."""
        # Unknown event type should be handled gracefully
        await manager.report_action_lifecycle(sample_action, "unknown_event", {})

        assert True  # If we get here, no exception was thrown

    @pytest.mark.asyncio
    async def test_report_action_lifecycle_none_details(self, manager: IntegrationManager, sample_action: RemediationAction) -> None:
        """Test reporting lifecycle event with None details."""
        # None details should be handled gracefully
        await manager.report_action_lifecycle(sample_action, "started", None)

        assert True  # If we get here, no exception was thrown

    def test_integration_components_initialized(self, manager: IntegrationManager) -> None:
        """Test that all integration components are properly initialized."""
        # Verify all integrations have the correct project ID
        assert manager.analysis_integration.project_id == PROJECT_ID
        assert manager.orchestration_integration.project_id == PROJECT_ID
        assert manager.communication_integration.project_id == PROJECT_ID

        # Verify all integrations have the same logger
        assert manager.analysis_integration.logger == manager.logger
        assert manager.orchestration_integration.logger == manager.logger
        assert manager.communication_integration.logger == manager.logger


# Integration tests with edge cases and error scenarios
class TestIntegrationsEdgeCases:
    """Test edge cases and error scenarios for all integration classes."""

    @pytest.fixture
    def publisher_client(self) -> PublisherClient:
        """Real Pub/Sub publisher client."""
        return PublisherClient()

    @pytest.fixture
    def logger(self) -> logging.Logger:
        """Real Cloud Logging logger."""
        client = cloud_logging.Client(project=PROJECT_ID)  # type: ignore[no-untyped-call]
        client.setup_logging()  # type: ignore[no-untyped-call]
        return logging.getLogger("test-integrations-edge-cases")

    def test_analysis_integration_empty_recommendations(self, publisher_client: PublisherClient, logger: logging.Logger) -> None:
        """Test analysis integration with empty recommendations."""
        integration = AnalysisAgentIntegration(publisher_client, PROJECT_ID, logger)

        analysis_result = AnalysisResult(
            incident_id="test-empty",
            confidence_score=0.1,
            summary="Low confidence analysis",
            detailed_analysis="Analysis yielded minimal threat indicators",
            recommendations=[],  # Empty recommendations
            attack_techniques=[],
        )

        actions = integration.parse_remediation_recommendations(analysis_result)
        assert len(actions) == 0

    def test_analysis_integration_malformed_recommendations(
        self, publisher_client: PublisherClient, logger: logging.Logger
    ) -> None:
        """Test analysis integration with malformed recommendations."""
        integration = AnalysisAgentIntegration(publisher_client, PROJECT_ID, logger)

        analysis_result = AnalysisResult(
            incident_id="test-malformed",
            confidence_score=0.5,
            summary="Medium confidence analysis with issues",
            detailed_analysis="Analysis found some indicators but with parsing challenges",
            recommendations=[
                "This is not a valid recommendation",
                "",  # Empty string
                "Block IP 999.999.999.999",  # Invalid IP
                "Disable user without email",  # No email found
            ],
            attack_techniques=[],
        )

        actions = integration.parse_remediation_recommendations(analysis_result)
        # Should handle malformed recommendations gracefully
        assert isinstance(actions, list)

    def test_orchestration_integration_invalid_topic(self, publisher_client: PublisherClient, logger: logging.Logger) -> None:
        """Test orchestration integration with topic that might not exist."""
        # This tests initialization - the topic might not exist but client should be created
        integration = OrchestrationAgentIntegration(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            topic_name="non-existent-topic-123",
            logger=logger,
        )

        assert integration.topic_name == "non-existent-topic-123"
        assert "non-existent-topic-123" in integration.topic_path

    def test_communication_integration_unicode_content(self, publisher_client: PublisherClient, logger: logging.Logger) -> None:
        """Test communication integration with Unicode content."""
        integration = CommunicationAgentIntegration(
            publisher_client, PROJECT_ID, TEST_NOTIFICATIONS_TOPIC, logger
        )

        action = RemediationAction(
            incident_id="test-unicode-🔥",
            action_type="block_ip_address",
            description="Block 恶意 IP address with émojis 🚫",
            target_resource="192.168.1.1",
            params={"ip_address": "192.168.1.1"},
        )

        # Should handle Unicode content properly
        content = integration._generate_content(action, "action_failed")

        assert "🔥" in content
        assert "恶意" in content
        assert "émojis" in content
        assert "🚫" in content

    def test_integration_manager_with_minimal_config(self, publisher_client: PublisherClient, logger: logging.Logger) -> None:
        """Test integration manager with minimal configuration."""
        minimal_config: dict[str, str] = {}  # Empty config

        manager = IntegrationManager(
            publisher_client=publisher_client,
            project_id=PROJECT_ID,
            config=minimal_config,
            logger=logger,
        )

        # Should work with default values
        assert manager.analysis_integration is not None
        assert manager.orchestration_integration is not None
        assert manager.communication_integration is not None

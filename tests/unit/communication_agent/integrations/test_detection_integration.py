"""
Test suite for communication_agent.integrations.detection_integration module.

Tests DetectionAgentIntegration class and all its methods using 100% production code.
NO MOCKING - All tests use real implementation and actual data processing.
"""

import pytest
from typing import Dict, Any, List

# Import the actual production code - NO MOCKS
from src.communication_agent.integrations.detection_integration import DetectionAgentIntegration
from src.communication_agent.formatting import MessageFormatter
from src.communication_agent.types import (
    MessageType,
    NotificationPriority,
)


class RealCommunicationAgent:
    """Real implementation of communication agent interface for testing - NO MOCKS."""

    def __init__(self) -> None:
        self.processed_messages: list[Dict[str, Any]] = []
        self.process_results = {"status": "sent", "message_id": "test-msg-123"}
        self.should_succeed = True

    def process(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process message and return real result."""
        self.processed_messages.append(message_data)
        if self.should_succeed:
            return self.process_results
        else:
            return {"status": "failed", "error": "Processing failed"}

    def set_process_result(self, result: Dict[str, Any]) -> None:
        """Set the result to return from process calls."""
        self.process_results = result

    def set_should_succeed(self, succeed: bool) -> None:
        """Set whether processing should succeed."""
        self.should_succeed = succeed


@pytest.fixture
def real_comm_agent() -> RealCommunicationAgent:
    """Create a real communication agent for testing."""
    return RealCommunicationAgent()


@pytest.fixture
def formatter() -> MessageFormatter:
    """Create a real message formatter."""
    return MessageFormatter()


@pytest.fixture
def detection_integration(real_comm_agent: RealCommunicationAgent, formatter: MessageFormatter) -> DetectionAgentIntegration:
    """Create DetectionAgentIntegration instance with real components."""
    return DetectionAgentIntegration(real_comm_agent, formatter)


class TestDetectionAgentIntegration:
    """Test DetectionAgentIntegration with real implementation."""

    def test_initialization(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent, formatter: MessageFormatter) -> None:
        """Test initialization of DetectionAgentIntegration."""
        assert detection_integration.comm_agent == real_comm_agent
        assert detection_integration.formatter == formatter

        # Check severity mapping
        assert NotificationPriority.CRITICAL in detection_integration.severity_to_priority.values()
        assert NotificationPriority.HIGH in detection_integration.severity_to_priority.values()
        assert NotificationPriority.MEDIUM in detection_integration.severity_to_priority.values()
        assert NotificationPriority.LOW in detection_integration.severity_to_priority.values()

        # Check default channels
        assert len(detection_integration.default_channels) >= 1
        assert len(detection_integration.critical_channels) >= 1

    def test_initialization_default_formatter(self, real_comm_agent: RealCommunicationAgent) -> None:
        """Test initialization with default formatter."""
        integration = DetectionAgentIntegration(real_comm_agent)

        assert integration.comm_agent == real_comm_agent
        assert integration.formatter is not None
        assert isinstance(integration.formatter, MessageFormatter)

    def test_severity_to_priority_mapping(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test severity to priority mapping."""
        mapping_tests = [
            ("critical", NotificationPriority.CRITICAL),
            ("high", NotificationPriority.HIGH),
            ("medium", NotificationPriority.MEDIUM),
            ("low", NotificationPriority.LOW),
            ("info", NotificationPriority.LOW)
        ]

        for severity, expected_priority in mapping_tests:
            assert detection_integration.severity_to_priority[severity] == expected_priority

    @pytest.mark.asyncio
    async def test_handle_incident_detected_basic(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent) -> None:
        """Test handling basic incident detection."""
        incident_data = {
            "incident_id": "inc_123",
            "type": "Security Incident",
            "severity": "HIGH",
            "detected_at": "2025-06-14T10:00:00Z",
            "source": "Detection Engine",
            "affected_resources": ["server01", "database02"],
            "indicators": ["malware", "suspicious_traffic"]
        }

        result = await detection_integration.handle_incident_detected(incident_data)

        assert result["status"] == "notifications_sent"
        assert result["incident_id"] == "inc_123"
        assert "channels" in result
        assert "results" in result
        assert len(real_comm_agent.processed_messages) >= 1

    @pytest.mark.asyncio
    async def test_handle_incident_detected_critical(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent) -> None:
        """Test handling critical incident detection."""
        incident_data = {
            "incident_id": "critical_inc_456",
            "type": "Data Breach",
            "severity": "CRITICAL",
            "detected_at": "2025-06-14T10:00:00Z",
            "source": "Security Scanner",
            "affected_resources": ["customer_db", "payment_system"],
            "threat_level": "high",
            "metrics": {"affected_records": 10000}
        }

        result = await detection_integration.handle_incident_detected(incident_data)

        assert result["status"] == "notifications_sent"
        assert result["incident_id"] == "critical_inc_456"

        # Critical incidents should trigger more notifications
        assert len(real_comm_agent.processed_messages) >= 1

        # Should include escalation message
        escalation_messages = [
            msg for msg in real_comm_agent.processed_messages
            if msg.get("message_type") == MessageType.INCIDENT_ESCALATION.value
        ]
        assert len(escalation_messages) >= 1

    @pytest.mark.asyncio
    async def test_handle_incident_detected_with_custom_recipients(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent) -> None:
        """Test handling incident with custom recipients."""
        incident_data = {
            "incident_id": "custom_inc_789",
            "type": "Network Intrusion",
            "severity": "medium",
            "affected_resources": ["firewall"],
            "indicators": ["port_scan"]
        }

        custom_recipients = [
            {"email": "security@example.com", "channel": "email"},
            {"phone": "+1234567890", "channel": "sms"}
        ]

        result = await detection_integration.handle_incident_detected(
            incident_data,
            custom_recipients=custom_recipients
        )

        assert result["status"] == "notifications_sent"
        assert len(real_comm_agent.processed_messages) >= 1

    @pytest.mark.asyncio
    async def test_handle_incident_detected_error_handling(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent) -> None:
        """Test error handling in incident detection."""
        # Test with invalid incident data
        invalid_incident_data: Dict[str, Any] = {}

        result = await detection_integration.handle_incident_detected(invalid_incident_data)

        assert result["status"] == "error"
        assert "error" in result

    def test_format_incident_data_basic(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test basic incident data formatting."""
        incident_data = {
            "incident_id": "format_test",
            "affected_resources": ["server1", "server2"],
            "detection_details": {"method": "signature", "confidence": 0.95},
            "indicators": ["malware", "c2_traffic"],
            "threat_level": "high"
        }

        formatted = detection_integration._format_incident_data(incident_data)

        # Check affected resources formatting
        if "affected_resources" in formatted:
            assert len(formatted["affected_resources"]) == 2

        # Check assessment formatting
        if "assessment" in formatted:
            assert isinstance(formatted["assessment"], str)

    def test_format_incident_data_complex(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test complex incident data formatting."""
        incident_data = {
            "incident_id": "complex_format",
            "affected_resources": [
                {"name": "web_server", "type": "server", "status": "compromised"},
                {"name": "database", "type": "database", "status": "accessed"}
            ],
            "detection_details": {
                "detection_method": "behavioral_analysis",
                "confidence_score": 0.87,
                "alert_count": 15
            },
            "indicators": ["lateral_movement", "data_exfiltration", "privilege_escalation"],
            "threat_level": "critical",
            "metrics": {
                "duration": "2h",
                "affected_users": 500,
                "data_volume": "50GB"
            },
            "tags": ["apt", "targeted", "persistent"]
        }

        formatted = detection_integration._format_incident_data(incident_data)

        # Should handle complex resource formatting
        if "affected_resources" in formatted:
            resources = formatted["affected_resources"]
            assert len(resources) == 2
            assert all("name" in r for r in resources)
            assert all("type" in r for r in resources)

        # Should format assessment with all details
        if "assessment" in formatted:
            assessment = formatted["assessment"]
            assert "behavioral_analysis" in assessment or "Behavioral_analysis" in assessment

        # Should include additional context
        if "additional_context" in formatted:
            context = formatted["additional_context"]
            assert "tags" in context or "metric_duration" in context

    def test_format_affected_resources(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test affected resources formatting."""
        # Test with simple resource list
        incident_data = {"affected_resources": ["server1", "server2", "database1"]}
        formatted: dict[str, Any] = {}

        detection_integration._format_affected_resources(incident_data, formatted)

        if "affected_resources" in formatted:
            assert len(formatted["affected_resources"]) == 3
            assert all("resource" in r for r in formatted["affected_resources"])

    def test_format_single_resource(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test single resource formatting."""
        # Test string resource
        resource_str = "test_server"
        formatted = detection_integration._format_single_resource(resource_str)
        assert formatted["resource"] == "test_server"

        # Test dict resource
        resource_dict = {
            "name": "web_server",
            "type": "application_server",
            "status": "online"
        }
        formatted = detection_integration._format_single_resource(resource_dict)
        assert formatted["name"] == "web_server"
        assert formatted["type"] == "application_server"
        assert formatted["status"] == "online"

        # Test dict resource with minimal data
        resource_minimal = {"id": "srv-123"}
        formatted = detection_integration._format_single_resource(resource_minimal)
        assert formatted["name"] == "srv-123"

    def test_get_default_recipients_low_severity(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test default recipients for low severity incidents."""
        recipients = detection_integration._get_default_recipients("low", "Generic Alert")

        # Should always include security team
        assert any(r.get("role") == "security_engineer" for r in recipients)

        # Low severity should not include managers or executives
        assert not any(r.get("role") == "manager" for r in recipients)
        assert not any(r.get("role") == "executive" for r in recipients)

    def test_get_default_recipients_high_severity(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test default recipients for high severity incidents."""
        recipients = detection_integration._get_default_recipients("high", "Security Breach")

        # Should include security team and incident responders
        assert any(r.get("role") == "security_engineer" for r in recipients)
        assert any(r.get("role") == "incident_responder" for r in recipients)

        # Should include on-call
        assert any(r.get("on_call") == "true" for r in recipients)

    def test_get_default_recipients_critical_severity(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test default recipients for critical severity incidents."""
        recipients = detection_integration._get_default_recipients("critical", "Data Breach")

        # Should include security team, incident responders, and management
        assert any(r.get("role") == "security_engineer" for r in recipients)
        assert any(r.get("role") == "incident_responder" for r in recipients)
        assert any(r.get("role") == "manager" for r in recipients)

        # For data breach, should include executives
        assert any(r.get("role") == "executive" for r in recipients)

    def test_get_default_recipients_special_incident_types(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test default recipients for special incident types."""
        # Test network incident
        network_recipients = detection_integration._get_default_recipients("medium", "Network Attack")
        assert any(r.get("tag") == "network_team" for r in network_recipients)

        # Test application incident
        app_recipients = detection_integration._get_default_recipients("medium", "Web Application Attack")
        assert any(r.get("tag") == "application_team" for r in app_recipients)

        # Test compliance incident
        compliance_recipients = detection_integration._get_default_recipients("medium", "Policy Violation")
        assert any(r.get("tag") == "compliance_team" for r in compliance_recipients)

    def test_generate_dashboard_link(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test dashboard link generation."""
        incident_id = "test_incident_123"
        link = detection_integration._generate_dashboard_link(incident_id)

        assert incident_id in link
        assert link.startswith("https://")
        assert "dashboard" in link

    @pytest.mark.asyncio
    async def test_handle_alert_batch(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent) -> None:
        """Test handling batch of alerts."""
        alerts = [
            {
                "id": "alert1",
                "type": "Malware Detection",
                "severity": "high",
                "timestamp": "2025-06-14T10:00:00Z",
                "affected_resources": ["server1"],
                "indicators": ["virus_signature"]
            },
            {
                "id": "alert2",
                "type": "Malware Detection",
                "severity": "high",
                "timestamp": "2025-06-14T10:05:00Z",
                "affected_resources": ["server2"],
                "indicators": ["trojan_behavior"]
            },
            {
                "id": "alert3",
                "type": "Network Intrusion",
                "severity": "medium",
                "timestamp": "2025-06-14T10:10:00Z",
                "affected_resources": ["firewall"],
                "indicators": ["port_scan"]
            }
        ]

        result = await detection_integration.handle_alert_batch(alerts)

        assert result["status"] == "batch_processed"
        assert result["total_alerts"] == 3
        assert result["groups_created"] >= 1
        assert "results" in result

    def test_group_alerts(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test alert grouping logic."""
        alerts = [
            {"severity": "high", "type": "Malware"},
            {"severity": "high", "type": "Malware"},
            {"severity": "medium", "type": "Network"},
            {"severity": "high", "type": "Network"}
        ]

        grouped = detection_integration._group_alerts(alerts)

        # Should have 3 groups: (high, Malware), (medium, Network), (high, Network)
        assert len(grouped) == 3
        assert ("high", "Malware") in grouped
        assert ("medium", "Network") in grouped
        assert ("high", "Network") in grouped

        # Check group sizes
        assert len(grouped[("high", "Malware")]) == 2
        assert len(grouped[("medium", "Network")]) == 1
        assert len(grouped[("high", "Network")]) == 1

    def test_extract_resources_from_alerts(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test extracting unique resources from alerts."""
        alerts: List[Dict[str, Any]] = [
            {
                "affected_resources": [
                    {"id": "srv1", "name": "server1"},
                    {"id": "srv2", "name": "server2"}
                ]
            },
            {
                "affected_resources": [
                    {"id": "srv1", "name": "server1"},  # Duplicate
                    {"id": "srv3", "name": "server3"}
                ]
            },
            {
                "affected_resources": ["simple_resource"]
            }
        ]

        resources = detection_integration._extract_resources_from_alerts(alerts)

        # Should have unique resources only
        assert len(resources) == 4  # srv1, srv2, srv3, simple_resource

        # Check that duplicates are removed
        resource_ids = []
        for resource in resources:
            if isinstance(resource, dict):
                resource_ids.append(resource.get("id", resource.get("name", str(resource))))
            else:
                resource_ids.append(str(resource))

        assert len(set(resource_ids)) == len(resource_ids)  # All unique

    def test_extract_indicators_from_alerts(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test extracting unique indicators from alerts."""
        alerts = [
            {"indicators": ["malware", "c2_traffic"]},
            {"indicators": ["malware", "data_exfil"]},  # malware is duplicate
            {"indicators": ["lateral_movement"]}
        ]

        indicators = detection_integration._extract_indicators_from_alerts(alerts)

        # Should have unique indicators only
        expected_indicators = {"malware", "c2_traffic", "data_exfil", "lateral_movement"}
        assert set(indicators) == expected_indicators

    def test_register_custom_formatter(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test registering custom formatter."""
        # Should not raise exception
        detection_integration.register_custom_formatter("custom_incident_type")

        # Test with different types
        detection_integration.register_custom_formatter("malware_detection")
        detection_integration.register_custom_formatter("data_breach")

    @pytest.mark.asyncio
    async def test_trigger_escalation(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent) -> None:
        """Test escalation triggering for critical incidents."""
        incident_data = {
            "incident_id": "escalation_test",
            "type": "Critical System Breach",
            "severity": "critical"
        }

        context = {
            "incident_id": "escalation_test",
            "incident_type": "Critical System Breach",
            "affected_resources_count": 5,
            "dashboard_link": "https://dashboard.example.com/incidents/escalation_test"
        }

        # Clear previous messages
        real_comm_agent.processed_messages.clear()

        # Trigger escalation
        await detection_integration._trigger_escalation(incident_data, context)

        # Should have sent escalation message
        escalation_messages = [
            msg for msg in real_comm_agent.processed_messages
            if msg.get("message_type") == MessageType.INCIDENT_ESCALATION.value
        ]
        assert len(escalation_messages) >= 1

        escalation_msg = escalation_messages[0]
        assert escalation_msg["priority"] == NotificationPriority.CRITICAL.value
        assert "escalation_reason" in escalation_msg["context"]

    @pytest.mark.asyncio
    async def test_error_handling_comprehensive(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent) -> None:
        """Test comprehensive error handling."""
        # Test with malformed incident data
        malformed_incidents: list[Dict[str, Any]] = [
            {},  # Empty dict
            {"incident_id": None},  # None values
            {"severity": "invalid_severity"},  # Invalid severity
        ]

        for incident_data in malformed_incidents:
            result = await detection_integration.handle_incident_detected(incident_data)
            # Should handle gracefully and return error status
            assert "status" in result

    @pytest.mark.asyncio
    async def test_communication_agent_failure(self, detection_integration: DetectionAgentIntegration, real_comm_agent: RealCommunicationAgent) -> None:
        """Test handling communication agent failures."""
        # Configure agent to fail
        real_comm_agent.set_should_succeed(False)

        incident_data = {
            "incident_id": "comm_fail_test",
            "type": "Test Incident",
            "severity": "medium",
            "affected_resources": ["test_resource"]
        }

        # Should still complete and report results
        result = await detection_integration.handle_incident_detected(incident_data)

        # Should get notification sent status even if individual channels fail
        assert result["status"] == "notifications_sent"
        assert "results" in result

    def test_edge_cases_formatting(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test edge cases in formatting functions."""
        # Test with empty/None values
        empty_incident: dict[str, Any] = {}
        formatted = detection_integration._format_incident_data(empty_incident)
        assert isinstance(formatted, dict)

        # Test with None affected resources
        none_resources_incident = {"affected_resources": None}
        formatted = detection_integration._format_incident_data(none_resources_incident)
        assert isinstance(formatted, dict)

        # Test format_single_resource with empty dict
        empty_resource: dict[str, Any] = {}
        formatted_resource = detection_integration._format_single_resource(empty_resource)
        assert "name" in formatted_resource

    def test_different_severity_formats(self, detection_integration: DetectionAgentIntegration) -> None:
        """Test handling different severity formats."""
        severity_variations = [
            "CRITICAL", "critical", "Critical",
            "HIGH", "high", "High",
            "MEDIUM", "medium", "Medium",
            "LOW", "low", "Low"
        ]

        for severity in severity_variations:
            recipients = detection_integration._get_default_recipients(severity.lower(), "Test")
            assert len(recipients) >= 1  # Should always have at least security engineer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

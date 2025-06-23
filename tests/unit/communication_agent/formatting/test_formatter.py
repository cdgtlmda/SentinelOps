"""REAL tests for communication_agent/formatting/formatter.py - Testing actual message formatting logic."""

import pytest
from typing import Any

# Import the actual production code
from src.communication_agent.formatting.formatter import MessageFormatter
from src.communication_agent.types import NotificationChannel


class TestMessageFormatterRealLogic:
    """Test MessageFormatter with REAL formatting logic - NO MOCKS."""

    @pytest.fixture
    def formatter(self) -> MessageFormatter:
        """Create real MessageFormatter instance."""
        return MessageFormatter()

    def test_format_incident_details_complete(self, formatter: MessageFormatter) -> None:
        """Test REAL incident formatting with all details."""
        # Real incident data structure
        incident = {
            "id": "INC-2024-001",
            "type": "Unauthorized Access",
            "severity": "critical",
            "status": "active",
            "detected_at": "2024-06-12T15:30:00Z",
            "detection_source": "Detection Agent",
            "description": "Multiple failed login attempts detected from suspicious IP addresses",
            "affected_resources": [
                {"type": "vm", "name": "web-server-01", "project": "production"},
                {"type": "database", "name": "users-db", "project": "production"},
            ],
            "timeline": [
                {
                    "timestamp": "2024-06-12T15:25:00Z",
                    "event": "First failed login attempt",
                    "details": "IP: 192.168.1.100",
                },
                {
                    "timestamp": "2024-06-12T15:30:00Z",
                    "event": "Threshold exceeded",
                    "details": "10 failed attempts in 5 minutes",
                },
            ],
        }

        # Execute real formatting
        result = formatter.format_incident_details(incident)

        # Verify real output contains expected elements
        assert "## Incident INC-2024-001: Unauthorized Access" in result
        assert "CRITICAL" in result  # Severity badge
        assert "| Incident ID | INC-2024-001 |" in result
        assert "| Type | Unauthorized Access |" in result
        assert "| Status | active |" in result
        assert "Multiple failed login attempts" in result
        assert "web-server-01" in result
        assert "users-db" in result

        # Verify markdown structure
        assert "###" in result  # Subheadings
        assert "|" in result  # Tables
        assert result.count("\n") > 10  # Multi-line output

    def test_format_analysis_results_with_real_data(self, formatter: MessageFormatter) -> None:
        """Test REAL analysis results formatting."""
        analysis = {
            "incident_id": "INC-2024-001",
            "risk_score": 8.5,
            "confidence": 0.92,
            "findings": [
                {
                    "type": "anomaly",
                    "description": "Login attempts from unusual location",
                    "severity": "high",
                },
                {
                    "type": "pattern",
                    "description": "Matches known brute-force attack pattern",
                    "severity": "critical",
                },
            ],
            "recommendations": [
                "Block source IP immediately",
                "Reset affected user credentials",
                "Enable MFA for all accounts",
            ],
            "context": {
                "similar_incidents": 3,
                "last_occurrence": "2024-05-15",
                "affected_users": 5,
            },
        }

        # Execute real formatting
        result = formatter.format_analysis_results(analysis)

        # Verify formatted output
        assert "Risk Score: 8.5/10" in result
        assert "Confidence: 92%" in result
        assert "Login attempts from unusual location" in result
        assert "Matches known brute-force attack pattern" in result
        assert "1. Block source IP immediately" in result
        assert "2. Reset affected user credentials" in result
        assert "3. Enable MFA for all accounts" in result
        assert "Similar incidents: 3" in result

    def test_format_remediation_summary_real_output(self, formatter: MessageFormatter) -> None:
        """Test REAL remediation summary formatting."""
        remediation = {
            "incident_id": "INC-2024-001",
            "actions": [
                {
                    "type": "block_ip",
                    "target": "192.168.1.100",
                    "status": "completed",
                    "timestamp": "2024-06-12T15:35:00Z",
                    "result": "Successfully blocked IP in firewall",
                },
                {
                    "type": "disable_account",
                    "target": "user@example.com",
                    "status": "completed",
                    "timestamp": "2024-06-12T15:36:00Z",
                    "result": "Account disabled",
                },
                {
                    "type": "notify_team",
                    "target": "security-team",
                    "status": "in_progress",
                    "timestamp": "2024-06-12T15:37:00Z",
                    "result": "Notification sent, awaiting acknowledgment",
                },
            ],
            "overall_status": "in_progress",
            "completion_percentage": 67,
        }

        # Execute real formatting
        result = formatter.format_remediation_summary(remediation)

        # Verify output
        assert "Remediation Progress: 67%" in result
        assert "✅ block_ip" in result  # Completed action
        assert "✅ disable_account" in result
        assert "⏳ notify_team" in result  # In progress action
        assert "192.168.1.100" in result
        assert "Successfully blocked IP in firewall" in result

    def test_format_for_channel_slack(self, formatter: MessageFormatter) -> None:
        """Test REAL Slack-specific formatting."""
        content = {
            "title": "Security Alert",
            "severity": "high",
            "description": "Suspicious activity detected",
            "fields": {
                "Source": "10.0.0.1",
                "Target": "Database Server",
                "Time": "2024-06-12T15:30:00Z",
            },
            "actions": ["Investigate", "Block", "Report"],
        }

        # Execute real Slack formatting
        # First format the incident details, then format for channel
        formatted_content = formatter.format_incident_details(content)
        result = formatter.format_for_channel(formatted_content, NotificationChannel.SLACK)

        # Verify Slack-specific formatting
        assert ":warning:" in result  # Slack emoji
        assert "*Security Alert*" in result  # Bold formatting
        assert "```" in result  # Code blocks
        assert "• Investigate" in result  # Bullet points

    def test_format_for_channel_email(self, formatter: MessageFormatter) -> None:
        """Test REAL email-specific formatting."""
        content = {
            "title": "Security Alert",
            "severity": "high",
            "description": "Suspicious activity detected",
            "fields": {
                "Source": "10.0.0.1",
                "Target": "Database Server",
                "Time": "2024-06-12T15:30:00Z",
            },
        }

        # Execute real email formatting
        # First format the incident details, then format for channel
        formatted_content = formatter.format_incident_details(content)
        result = formatter.format_for_channel(formatted_content, NotificationChannel.EMAIL)

        # Verify email-specific formatting (HTML)
        assert "<h2>" in result
        assert "</h2>" in result
        assert "<table>" in result
        assert "<tr>" in result
        assert "<td>" in result
        assert "style=" in result  # CSS styling

    def test_format_for_channel_sms_truncation(self, formatter: MessageFormatter) -> None:
        """Test REAL SMS channel truncation."""
        long_content = "A" * 500  # 500 character message

        # Test SMS limit (160 chars)
        sms_result = formatter.format_for_channel(long_content, NotificationChannel.SMS)
        assert len(sms_result) == 160
        assert sms_result.endswith("...")

        # Test that other channels don't truncate
        email_result = formatter.format_for_channel(long_content, NotificationChannel.EMAIL)
        assert len(email_result) == 500  # No truncation for email

    def test_create_summary_report_with_multiple_incidents(self, formatter: MessageFormatter) -> None:
        """Test REAL summary report with multiple incidents."""
        incidents: list[dict[str, Any]] = [
            {
                "id": "INC-101",
                "title": "Brute Force Attack Detected",
                "severity": "high",
                "status": "resolved",
                "created_at": "2024-06-12T08:00:00Z",
                "resolved_at": "2024-06-12T09:30:00Z",
                "affected_systems": ["auth-service"],
                "false_positive": False
            },
            {
                "id": "INC-102",
                "title": "Unusual Data Transfer",
                "severity": "critical",
                "status": "active",
                "created_at": "2024-06-12T14:00:00Z",
                "affected_systems": ["database", "api-gateway"],
                "data_volume": "500GB"
            },
            {
                "id": "INC-103",
                "title": "Malware Detected",
                "severity": "critical",
                "status": "contained",
                "created_at": "2024-06-12T16:00:00Z",
                "affected_systems": ["workstation-15"],
                "malware_family": "Emotet"
            }
        ]

        # Execute real summary report
        result = formatter.create_summary_report(incidents, period="daily", include_stats=True)

        # Verify comprehensive summary
        assert "Daily Summary Report" in result or "Summary Report" in result
        assert "3" in result  # Total incidents
        assert "INC-101" in result
        assert "INC-102" in result
        assert "INC-103" in result
        assert "Brute Force Attack" in result
        assert "critical" in result
        assert "resolved" in result
        assert "active" in result

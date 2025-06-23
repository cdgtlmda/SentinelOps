"""REAL tests for communication_agent/formatting/formatter.py - Testing actual message formatting logic."""

import pytest
from datetime import datetime, timezone
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

    def test_real_format_incident_details_basic(self, formatter: MessageFormatter) -> None:
        """Test REAL incident formatting with basic details."""
        # Minimal incident data
        incident = {
            "id": "INC-001",
            "type": "Security Alert",
            "severity": "high",
            "status": "active",
        }

        # Execute real formatting
        result = formatter.format_incident_details(
            incident, include_timeline=False, include_resources=False
        )

        # Verify output is real formatted text
        assert isinstance(result, str)
        assert "Incident INC-001: Security Alert" in result
        assert "HIGH" in result  # Severity should be uppercase
        assert "Incident ID" in result and "INC-001" in result
        assert "Status" in result and "active" in result
        print(f"\nBasic incident output:\n{result}")

    def test_real_format_incident_details_complete(self, formatter: MessageFormatter) -> None:
        """Test REAL incident formatting with all details."""
        # Complete incident data
        incident = {
            "id": "INC-2024-001",
            "type": "Unauthorized Access",
            "severity": "critical",
            "status": "investigating",
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
                    "actor": "unknown",
                    "details": "IP: 192.168.1.100",
                },
                {
                    "timestamp": "2024-06-12T15:30:00Z",
                    "event": "Threshold exceeded",
                    "actor": "system",
                    "details": "10 failed attempts in 5 minutes",
                },
            ],
            "indicators": {
                "source_ips": ["192.168.1.100", "192.168.1.101"],
                "target_accounts": ["admin", "root", "user1"],
                "attack_pattern": "brute_force",
            },
        }

        # Execute real formatting with all options
        result = formatter.format_incident_details(
            incident, include_timeline=True, include_resources=True
        )

        # Verify comprehensive output
        assert "Incident INC-2024-001: Unauthorized Access" in result
        assert "CRITICAL" in result
        assert "Multiple failed login attempts" in result
        assert "web-server-01" in result
        assert "Timeline" in result  # Should have timeline section
        assert "192.168.1.100" in result
        print(f"\nComplete incident output:\n{result}")
        print(f"\nComplete incident output length: {len(result)} characters")

    def test_real_format_analysis_results(self, formatter: MessageFormatter) -> None:
        """Test REAL analysis results formatting."""
        analysis = {
            "incident_id": "INC-2024-001",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "risk_assessment": {
                "risk_score": 8.5,
                "confidence": 0.92,
                "factors": [
                    {"factor": "Multiple IPs", "weight": 0.3},
                    {"factor": "Admin accounts targeted", "weight": 0.5},
                    {"factor": "Known attack pattern", "weight": 0.2},
                ],
            },
            "findings": [
                {
                    "type": "anomaly",
                    "description": "Login attempts from 2 different geographic locations within 5 minutes",
                    "confidence": 0.95,
                },
                {
                    "type": "correlation",
                    "description": "Similar attacks reported in the region",
                    "confidence": 0.78,
                },
            ],
            "recommendations": [
                {
                    "action": "Block IPs",
                    "priority": "immediate",
                    "impact": "high",
                    "details": "Block source IPs 192.168.1.100-101 at firewall level",
                },
                {
                    "action": "Force password reset",
                    "priority": "high",
                    "impact": "medium",
                    "details": "Reset passwords for targeted accounts",
                },
            ],
            "similar_incidents": [
                {"id": "INC-2024-050", "similarity": 0.89, "date": "2024-05-15"},
                {"id": "INC-2024-032", "similarity": 0.76, "date": "2024-04-20"},
            ],
        }

        # Execute real formatting
        result = formatter.format_analysis_results(analysis)

        # Verify formatted output
        assert isinstance(result, str)
        assert "Risk" in result and "8.5" in result
        assert "92%" in result or "0.92" in result
        assert "Login attempts from 2 different geographic locations" in result
        assert "Block IPs" in result
        assert "INC-2024-050" in result
        print(f"\nAnalysis results output contains {result.count('\\n')} lines")

    def test_real_format_remediation_summary(self, formatter: MessageFormatter) -> None:
        """Test REAL remediation summary formatting."""
        remediation = {
            "incident_id": "INC-2024-001",
            "started_at": "2024-06-12T15:35:00Z",
            "status": "in_progress",
            "total_actions": 5,
            "completed_actions": 3,
            "failed_actions": 0,
            "actions": [
                {
                    "id": "REM-001",
                    "type": "block_ip",
                    "status": "completed",
                    "started_at": "2024-06-12T15:35:00Z",
                    "completed_at": "2024-06-12T15:35:30Z",
                    "details": {
                        "target": "192.168.1.100",
                        "method": "firewall_rule",
                        "rule_id": "block-suspicious-001",
                    },
                    "result": "Successfully blocked IP",
                },
                {
                    "id": "REM-002",
                    "type": "disable_account",
                    "status": "completed",
                    "started_at": "2024-06-12T15:36:00Z",
                    "completed_at": "2024-06-12T15:36:15Z",
                    "details": {"target": "admin", "method": "iam_policy"},
                    "result": "Account disabled",
                },
                {
                    "id": "REM-003",
                    "type": "isolate_vm",
                    "status": "in_progress",
                    "started_at": "2024-06-12T15:37:00Z",
                    "details": {
                        "target": "web-server-01",
                        "method": "network_isolation",
                    },
                },
            ],
            "impact_assessment": {
                "services_affected": ["web", "api"],
                "users_affected": 150,
                "estimated_downtime": "30 minutes",
            },
        }

        # Execute real formatting
        result = formatter.format_remediation_summary(remediation)

        # Verify output
        assert "Remediation" in result
        assert "3" in result or "60%" in result  # Progress
        assert "block_ip" in result
        assert "192.168.1.100" in result
        assert "Successfully blocked IP" in result
        assert "in_progress" in result
        assert "web-server-01" in result
        print("\nRemediation summary formatted")

    def test_real_format_for_channel_slack(self, formatter: MessageFormatter) -> None:
        """Test REAL Slack channel formatting."""
        # First create formatted content
        incident = {
            "id": "INC-2024-001",
            "type": "Security Alert",
            "severity": "high",
            "description": "Suspicious login activity detected",
            "affected_resources": [{"type": "database", "name": "Production DB"}],
        }

        # Format the incident first
        content = formatter.format_incident_details(
            incident, include_timeline=False, include_resources=True
        )

        # Then format for Slack channel
        result = formatter.format_for_channel(content, NotificationChannel.SLACK)

        # Verify Slack-specific formatting
        assert isinstance(result, str)
        # Slack format should contain the incident details
        assert "INC-2024-001" in result
        assert "Security Alert" in result
        assert "Production DB" in result
        print(f"\nSlack formatted message preview: {result[:200]}...")

    def test_real_format_for_channel_email(self, formatter: MessageFormatter) -> None:
        """Test REAL email channel formatting."""
        # Create incident data
        incident = {
            "id": "INC-2024-001",
            "type": "Unauthorized Access",
            "severity": "critical",
            "description": "Multiple failed login attempts have been detected on production systems.",
            "affected_resources": [
                {"type": "vm", "name": "web-server-01"},
                {"type": "database", "name": "database-prod"},
            ],
        }

        # Format the incident first
        content = formatter.format_incident_details(incident)

        # Execute email formatting (email supports full markdown)
        result = formatter.format_for_channel(content, NotificationChannel.EMAIL)

        # Verify email formatting (should preserve markdown)
        assert isinstance(result, str)
        assert content == result  # Email preserves original markdown
        assert "Unauthorized Access" in result
        assert "CRITICAL" in result
        print(f"\nEmail formatted message length: {len(result)}")

    def test_real_create_summary_report(self, formatter: MessageFormatter) -> None:
        """Test REAL summary report creation with incidents."""
        # Create a summary using available methods
        incidents = [
            {
                "id": "INC-001",
                "severity": "critical",
                "type": "Security Alert",
                "detected_at": "2024-06-12T10:00:00Z",
                "status": "active",
            },
            {
                "id": "INC-002",
                "severity": "high",
                "type": "Unauthorized Access",
                "detected_at": "2024-06-12T11:00:00Z",
                "status": "resolved",
            },
            {
                "id": "INC-003",
                "severity": "high",
                "type": "Unauthorized Access",
                "detected_at": "2024-06-12T12:00:00Z",
                "status": "active",
            },
            {
                "id": "INC-004",
                "severity": "medium",
                "type": "Malware Detection",
                "detected_at": "2024-06-12T13:00:00Z",
                "status": "investigating",
            },
        ]

        # Format summary using actual create_summary_report method
        result = formatter.create_summary_report(
            incidents=incidents, period="daily", include_stats=True
        )

        # Verify report structure
        assert isinstance(result, str)
        assert "Daily Security Summary" in result
        assert "Statistics" in result
        assert "Total Incidents:** 4" in result
        assert "critical" in result.lower()
        assert "Critical Incidents" in result
        assert "INC-001" in result
        print(f"\nSummary report created with {len(result)} characters")

    def test_real_markdown_table_generation(self, formatter: MessageFormatter) -> None:
        """Test REAL markdown table generation through formatter."""
        # Test the markdown formatter's table generation
        headers = ["Metric", "Current", "Previous", "Change"]
        rows = [
            ["CPU Usage", "75%", "45%", "+30%"],
            ["Memory", "8.2 GB", "6.1 GB", "+2.1 GB"],
            ["Requests/sec", "1,250", "980", "+27.6%"],
        ]

        # The formatter uses its markdown instance
        table = formatter.markdown.table(headers, rows)

        # Verify table structure
        assert (
            "Metric" in table
            and "Current" in table
            and "Previous" in table
            and "Change" in table
        )
        assert "---" in table  # Separator
        assert (
            "CPU Usage" in table
            and "75%" in table
            and "45%" in table
            and "+30%" in table
        )
        print(f"\nGenerated markdown table:\n{table}")

    def test_real_severity_badge_formatting(self, formatter: MessageFormatter) -> None:
        """Test REAL severity badge formatting."""
        severities = ["low", "medium", "high", "critical"]

        for severity in severities:
            badge = formatter.markdown.format_severity_badge(severity)
            assert severity.upper() in badge
            # Should have some visual indicator (emoji, color code, etc)
            assert len(badge) > len(severity)  # More than just the text

        print(f"\nSeverity badges generated for: {severities}")

    def test_real_timestamp_formatting(self, formatter: MessageFormatter) -> None:
        """Test REAL timestamp formatting."""
        timestamps = [
            "2024-06-12T15:30:00Z",
            "2024-06-12T15:30:00+00:00",
            datetime.now(timezone.utc).isoformat(),
        ]

        for ts in timestamps:
            formatted = formatter.markdown.format_timestamp(ts)
            assert formatted  # Should return something
            assert "2024" in formatted or ":" in formatted  # Date or time components

        print("\nTimestamps formatted successfully")

    def test_format_with_empty_data(self, formatter: MessageFormatter) -> None:
        """Test REAL formatting with empty or minimal data."""
        # Empty incident
        empty_incident: dict[str, Any] = {}
        result = formatter.format_incident_details(empty_incident)
        assert "Unknown" in result  # Should handle missing fields gracefully

        # Empty analysis
        empty_analysis = {"incident_id": "INC-001"}
        result = formatter.format_analysis_results(empty_analysis)
        assert isinstance(result, str)
        assert len(result) > 0  # Should produce some output

        print("\nEmpty data handling verified")

    def test_format_with_special_characters(self, formatter: MessageFormatter) -> None:
        """Test REAL formatting with special characters."""
        incident = {
            "id": "INC-001",
            "description": "SQL injection attempt: '; DROP TABLE users; --",
            "affected_resources": [
                {
                    "name": "db-server-01",
                    "query": "SELECT * FROM users WHERE id='1' OR '1'='1'",
                }
            ],
        }

        result = formatter.format_incident_details(incident)

        # Special characters should be preserved or properly escaped
        assert "DROP TABLE" in result
        # Check that the resource was included (query field may not be displayed)
        assert "db-server-01" in result
        print("\nSpecial character handling verified")

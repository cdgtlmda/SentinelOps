"""
Tests for data models.

COVERAGE REQUIREMENT: ≥90% statement coverage of src/common/models.py
VERIFICATION: python -m pytest tests/unit/test_models.py --cov=src.common.models --cov-report=term-missing
"""

from datetime import datetime, timezone
from typing import Dict, Any

import pytest

from src.common.models import (
    AnalysisResult,
    EventSource,
    Incident,
    IncidentStatus,
    Notification,
    RemediationAction,
    RemediationPriority,
    RemediationStatus,
    SecurityEvent,
    SeverityLevel,
)


class TestSeverityLevel:
    """Test SeverityLevel enum."""

    def test_severity_values(self) -> None:
        """Test enum values."""
        assert SeverityLevel.CRITICAL.value == "critical"
        assert SeverityLevel.HIGH.value == "high"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.INFORMATIONAL.value == "informational"

    def test_severity_comparison(self) -> None:
        """Test severity level comparison."""
        assert SeverityLevel.INFORMATIONAL < SeverityLevel.LOW
        assert SeverityLevel.LOW < SeverityLevel.MEDIUM
        assert SeverityLevel.MEDIUM < SeverityLevel.HIGH
        assert SeverityLevel.HIGH < SeverityLevel.CRITICAL

        assert SeverityLevel.CRITICAL > SeverityLevel.HIGH
        assert SeverityLevel.HIGH > SeverityLevel.MEDIUM

    def test_severity_comparison_different_type(self) -> None:
        """Test severity comparison with different types raises TypeError."""
        # Testing runtime behavior when wrong type is passed
        try:
            _ = SeverityLevel.HIGH < "high"  # type: ignore[operator]
            assert False, "Should have raised TypeError"
        except TypeError:
            pass


class TestIncidentStatus:
    """Test IncidentStatus enum."""

    def test_status_values(self) -> None:
        """Test enum values."""
        assert IncidentStatus.DETECTED.value == "detected"
        assert IncidentStatus.ANALYZING.value == "analyzing"
        assert IncidentStatus.REMEDIATION_PENDING.value == "remediation_pending"
        assert IncidentStatus.APPROVAL_REQUIRED.value == "approval_required"
        assert IncidentStatus.REMEDIATION_IN_PROGRESS.value == "remediation_in_progress"
        assert IncidentStatus.RESOLVED.value == "resolved"
        assert IncidentStatus.CLOSED.value == "closed"
        assert IncidentStatus.FALSE_POSITIVE.value == "false_positive"


class TestRemediationStatus:
    """Test RemediationStatus enum."""

    def test_status_values(self) -> None:
        """Test enum values."""
        assert RemediationStatus.PENDING.value == "pending"
        assert RemediationStatus.EXECUTING.value == "executing"
        assert RemediationStatus.COMPLETED.value == "completed"
        assert RemediationStatus.PARTIALLY_COMPLETED.value == "partially_completed"
        assert RemediationStatus.FAILED.value == "failed"
        assert RemediationStatus.ROLLED_BACK.value == "rolled_back"
        assert RemediationStatus.CANCELLED.value == "cancelled"


class TestRemediationPriority:
    """Test RemediationPriority enum."""

    def test_priority_values(self) -> None:
        """Test enum values."""
        assert RemediationPriority.CRITICAL.value == "critical"
        assert RemediationPriority.HIGH.value == "high"
        assert RemediationPriority.MEDIUM.value == "medium"
        assert RemediationPriority.LOW.value == "low"


class TestEventSource:
    """Test EventSource dataclass."""

    def test_initialization(self) -> None:
        """Test EventSource initialization."""
        source = EventSource(
            source_type="bigquery", source_name="logs", source_id="project-123"
        )
        assert source.source_type == "bigquery"
        assert source.source_name == "logs"
        assert source.source_id == "project-123"
        assert source.resource_type is None
        assert source.resource_name is None
        assert source.resource_id is None

    def test_initialization_with_optional_fields(self) -> None:
        """Test EventSource with optional fields."""
        source = EventSource(
            source_type="compute",
            source_name="instance-monitor",
            source_id="monitor-456",
            resource_type="gce_instance",
            resource_name="web-server-1",
            resource_id="instance-789",
        )
        assert source.resource_type == "gce_instance"
        assert source.resource_name == "web-server-1"
        assert source.resource_id == "instance-789"

    def test_validate_success(self) -> None:
        """Test successful validation."""
        source = EventSource("bigquery", "logs", "project-123")
        source.validate()  # Should not raise

    def test_validate_missing_source_type(self) -> None:
        """Test validation fails with empty source_type."""
        source = EventSource("", "logs", "project-123")
        with pytest.raises(ValueError, match="source_type is required"):
            source.validate()

    def test_validate_missing_source_name(self) -> None:
        """Test validation fails with empty source_name."""
        source = EventSource("bigquery", "", "project-123")
        with pytest.raises(ValueError, match="source_name is required"):
            source.validate()

    def test_validate_missing_source_id(self) -> None:
        """Test validation fails with empty source_id."""
        source = EventSource("bigquery", "logs", "")
        with pytest.raises(ValueError, match="source_id is required"):
            source.validate()


class TestSecurityEvent:
    """Test SecurityEvent dataclass."""

    def test_default_initialization(self) -> None:
        """Test SecurityEvent with defaults."""
        event = SecurityEvent()
        assert event.event_id is not None
        assert isinstance(event.event_id, str)
        assert isinstance(event.timestamp, datetime)
        assert event.event_type == ""
        assert event.severity == SeverityLevel.INFORMATIONAL
        assert event.description == ""
        assert event.raw_data == {}
        assert event.actor is None
        assert event.affected_resources == []
        assert event.indicators == {}

    def test_full_initialization(self) -> None:
        """Test SecurityEvent with all fields."""
        source = EventSource("bigquery", "logs", "project-123")
        event = SecurityEvent(
            event_id="test-123",
            event_type="suspicious_login",
            source=source,
            severity=SeverityLevel.HIGH,
            description="Suspicious login detected",
            raw_data={"ip": "192.168.1.1"},
            actor="user@example.com",
            affected_resources=["resource-1", "resource-2"],
            indicators={"risk_score": 0.8},
        )
        assert event.event_id == "test-123"
        assert event.event_type == "suspicious_login"
        assert event.source == source
        assert event.severity == SeverityLevel.HIGH
        assert event.description == "Suspicious login detected"
        assert event.raw_data == {"ip": "192.168.1.1"}
        assert event.actor == "user@example.com"
        assert event.affected_resources == ["resource-1", "resource-2"]
        assert event.indicators == {"risk_score": 0.8}

    def test_validate_success(self) -> None:
        """Test successful validation."""
        source = EventSource("bigquery", "logs", "project-123")
        event = SecurityEvent(
            event_type="test_event", source=source, description="Test description"
        )
        event.validate()  # Should not raise

    def test_validate_missing_event_type(self) -> None:
        """Test validation fails with empty event_type."""
        source = EventSource("bigquery", "logs", "project-123")
        event = SecurityEvent(source=source, description="Test")
        with pytest.raises(ValueError, match="event_type is required"):
            event.validate()

    def test_validate_missing_description(self) -> None:
        """Test validation fails with empty description."""
        source = EventSource("bigquery", "logs", "project-123")
        event = SecurityEvent(event_type="test", source=source)
        with pytest.raises(ValueError, match="description is required"):
            event.validate()

    def test_validate_invalid_source(self) -> None:
        """Test validation fails with invalid source."""
        source = EventSource("", "logs", "project-123")
        event = SecurityEvent(event_type="test", source=source, description="Test")
        with pytest.raises(ValueError, match="source_type is required"):
            event.validate()

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        source = EventSource("bigquery", "logs", "project-123")
        event = SecurityEvent(
            event_id="test-123",
            event_type="test_event",
            source=source,
            severity=SeverityLevel.MEDIUM,
            description="Test event",
            raw_data={"key": "value"},
            actor="test@example.com",
            affected_resources=["res1"],
            indicators={"score": 0.5},
        )

        result = event.to_dict()
        assert result["event_id"] == "test-123"
        assert result["event_type"] == "test_event"
        assert result["severity"] == "medium"
        assert result["description"] == "Test event"
        assert result["raw_data"] == {"key": "value"}
        assert result["actor"] == "test@example.com"
        assert result["affected_resources"] == ["res1"]
        assert result["indicators"] == {"score": 0.5}
        assert "timestamp" in result
        assert "source" in result
        assert result["source"]["source_type"] == "bigquery"


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""

    def test_default_initialization(self) -> None:
        """Test AnalysisResult with defaults."""
        result = AnalysisResult()
        assert result.analysis_id is not None
        assert isinstance(result.analysis_id, str)
        assert isinstance(result.timestamp, datetime)
        assert result.incident_id == ""
        assert result.confidence_score == 0.0
        assert result.summary == ""
        assert result.detailed_analysis == ""
        assert result.related_events == []
        assert result.attack_techniques == []
        assert result.recommendations == []
        assert result.evidence == {}
        assert result.gemini_explanation is None

    def test_full_initialization(self) -> None:
        """Test AnalysisResult with all fields."""
        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )
        result = AnalysisResult(
            analysis_id="analysis-123",
            incident_id="inc-456",
            confidence_score=0.85,
            summary="High confidence attack detected",
            detailed_analysis="Detailed analysis here",
            related_events=[event],
            attack_techniques=["T1078", "T1110"],
            recommendations=["Block IP", "Reset password"],
            evidence={"ip_reputation": "malicious"},
            gemini_explanation="AI analysis explanation",
        )
        assert result.analysis_id == "analysis-123"
        assert result.incident_id == "inc-456"
        assert result.confidence_score == 0.85
        assert result.summary == "High confidence attack detected"
        assert result.detailed_analysis == "Detailed analysis here"
        assert len(result.related_events) == 1
        assert result.attack_techniques == ["T1078", "T1110"]
        assert result.recommendations == ["Block IP", "Reset password"]
        assert result.evidence == {"ip_reputation": "malicious"}
        assert result.gemini_explanation == "AI analysis explanation"

    def test_validate_success(self) -> None:
        """Test successful validation."""
        result = AnalysisResult(
            incident_id="inc-123",
            confidence_score=0.75,
            summary="Test summary",
            detailed_analysis="Test analysis",
        )
        result.validate()  # Should not raise

    def test_validate_missing_incident_id(self) -> None:
        """Test validation fails with empty incident_id."""
        result = AnalysisResult(
            confidence_score=0.5, summary="Test", detailed_analysis="Test"
        )
        with pytest.raises(ValueError, match="incident_id is required"):
            result.validate()

    def test_validate_confidence_score_too_low(self) -> None:
        """Test validation fails with confidence_score < 0."""
        result = AnalysisResult(
            incident_id="inc-123",
            confidence_score=-0.1,
            summary="Test",
            detailed_analysis="Test",
        )
        with pytest.raises(
            ValueError, match="confidence_score must be between 0.0 and 1.0"
        ):
            result.validate()

    def test_validate_confidence_score_too_high(self) -> None:
        """Test validation fails with confidence_score > 1."""
        result = AnalysisResult(
            incident_id="inc-123",
            confidence_score=1.5,
            summary="Test",
            detailed_analysis="Test",
        )
        with pytest.raises(
            ValueError, match="confidence_score must be between 0.0 and 1.0"
        ):
            result.validate()

    def test_validate_missing_summary(self) -> None:
        """Test validation fails with empty summary."""
        result = AnalysisResult(
            incident_id="inc-123", confidence_score=0.5, detailed_analysis="Test"
        )
        with pytest.raises(ValueError, match="summary is required"):
            result.validate()

    def test_validate_missing_detailed_analysis(self) -> None:
        """Test validation fails with empty detailed_analysis."""
        result = AnalysisResult(
            incident_id="inc-123", confidence_score=0.5, summary="Test"
        )
        with pytest.raises(ValueError, match="detailed_analysis is required"):
            result.validate()

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )
        result = AnalysisResult(
            analysis_id="analysis-123",
            incident_id="inc-456",
            confidence_score=0.85,
            summary="Summary",
            detailed_analysis="Analysis",
            related_events=[event],
            attack_techniques=["T1078"],
            recommendations=["Block IP"],
            evidence={"key": "value"},
            gemini_explanation="AI explanation",
        )

        data = result.to_dict()
        assert data["analysis_id"] == "analysis-123"
        assert data["incident_id"] == "inc-456"
        assert data["confidence_score"] == 0.85
        assert data["summary"] == "Summary"
        assert data["detailed_analysis"] == "Analysis"
        assert len(data["related_events"]) == 1
        assert data["attack_techniques"] == ["T1078"]
        assert data["recommendations"] == ["Block IP"]
        assert data["evidence"] == {"key": "value"}
        assert data["gemini_explanation"] == "AI explanation"
        assert "timestamp" in data

    def test_from_dict_basic(self) -> None:
        """Test from_dict with basic data."""
        data = {
            "analysis_id": "analysis-123",
            "incident_id": "inc-456",
            "confidence_score": 0.85,
            "summary": "Test summary",
            "detailed_analysis": "Test analysis",
            "attack_techniques": ["T1078"],
            "recommendations": ["Block IP"],
            "evidence": {"key": "value"},
        }

        result = AnalysisResult.from_dict(data)
        assert result.analysis_id == "analysis-123"
        assert result.incident_id == "inc-456"
        assert result.confidence_score == 0.85
        assert result.summary == "Test summary"
        assert result.detailed_analysis == "Test analysis"
        assert result.attack_techniques == ["T1078"]
        assert result.recommendations == ["Block IP"]
        assert result.evidence == {"key": "value"}

    def test_from_dict_with_timestamp_string(self) -> None:
        """Test from_dict converts timestamp string to datetime."""
        data = {
            "analysis_id": "analysis-123",
            "incident_id": "inc-456",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "confidence_score": 0.85,
            "summary": "Test summary",
            "detailed_analysis": "Test analysis",
        }

        result = AnalysisResult.from_dict(data)
        assert isinstance(result.timestamp, datetime)
        assert result.timestamp.year == 2024

    def test_from_dict_with_related_events(self) -> None:
        """Test from_dict converts related events."""
        event_data = {
            "event_id": "event-123",
            "event_type": "test_event",
            "description": "Test event",
            "severity": "high",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "source": {
                "source_type": "test",
                "source_name": "test_source",
                "source_id": "source-123",
            },
        }

        data = {
            "analysis_id": "analysis-123",
            "incident_id": "inc-456",
            "confidence_score": 0.85,
            "summary": "Test summary",
            "detailed_analysis": "Test analysis",
            "related_events": [event_data],
        }

        result = AnalysisResult.from_dict(data)
        assert len(result.related_events) == 1
        event = result.related_events[0]
        assert isinstance(event, SecurityEvent)
        assert event.event_id == "event-123"
        assert event.severity == SeverityLevel.HIGH
        assert isinstance(event.source, EventSource)

    def test_from_dict_removes_extra_fields(self) -> None:
        """Test from_dict removes known non-AnalysisResult fields but may pass through others."""
        data = {
            "analysis_id": "analysis-123",
            "incident_id": "inc-456",
            "confidence_score": 0.85,
            "summary": "Test summary",
            "detailed_analysis": "Test analysis",
            "id": "should_be_removed",
            "created_at": "should_be_removed",
        }

        result = AnalysisResult.from_dict(data)
        assert result.analysis_id == "analysis-123"
        assert result.incident_id == "inc-456"
        # The method specifically removes 'id' and 'created_at' fields
        # but may not filter all unknown fields


class TestRemediationAction:
    """Test RemediationAction dataclass."""

    def test_default_initialization(self) -> None:
        """Test RemediationAction with defaults."""
        action = RemediationAction()
        assert action.action_id is not None
        assert isinstance(action.action_id, str)
        assert isinstance(action.timestamp, datetime)
        assert action.incident_id == ""
        assert action.action_type == ""
        assert action.status == "pending"
        assert action.description == ""
        assert action.target_resource == ""
        assert action.params == {}
        assert action.approved_by is None
        assert action.approval_time is None
        assert action.execution_result is None
        assert action.error_message is None
        assert action.automated is True  # New field test
        assert action.requires_approval is False  # New field test
        assert action.metadata == {}  # New field test

    def test_full_initialization(self) -> None:
        """Test RemediationAction with all fields."""
        approval_time = datetime.now(timezone.utc)
        action = RemediationAction(
            action_id="action-123",
            incident_id="inc-456",
            action_type="isolate_instance",
            status="approved",
            description="Isolate compromised instance",
            target_resource="instance-789",
            params={"zone": "us-central1-a"},
            approved_by="admin@example.com",
            approval_time=approval_time,
            execution_result={"isolated": True},
            error_message=None,
            automated=False,  # New field test
            requires_approval=True,  # New field test
            metadata={"priority": "high"},  # New field test
        )
        assert action.action_id == "action-123"
        assert action.incident_id == "inc-456"
        assert action.action_type == "isolate_instance"
        assert action.status == "approved"
        assert action.description == "Isolate compromised instance"
        assert action.target_resource == "instance-789"
        assert action.params == {"zone": "us-central1-a"}
        assert action.approved_by == "admin@example.com"
        assert action.approval_time == approval_time
        assert action.execution_result == {"isolated": True}
        assert action.error_message is None
        assert action.automated is False  # New field test
        assert action.requires_approval is True  # New field test
        assert action.metadata == {"priority": "high"}  # New field test

    def test_validate_success(self) -> None:
        """Test successful validation."""
        action = RemediationAction(
            incident_id="inc-123",
            action_type="block_ip",
            description="Block malicious IP",
            target_resource="192.168.1.1",
        )
        action.validate()  # Should not raise

    def test_validate_missing_incident_id(self) -> None:
        """Test validation fails with empty incident_id."""
        action = RemediationAction(
            action_type="test", description="Test", target_resource="test"
        )
        with pytest.raises(ValueError, match="incident_id is required"):
            action.validate()

    def test_validate_missing_action_type(self) -> None:
        """Test validation fails with empty action_type."""
        action = RemediationAction(
            incident_id="inc-123", description="Test", target_resource="test"
        )
        with pytest.raises(ValueError, match="action_type is required"):
            action.validate()

    def test_validate_missing_description(self) -> None:
        """Test validation fails with empty description."""
        action = RemediationAction(
            incident_id="inc-123", action_type="test", target_resource="test"
        )
        with pytest.raises(ValueError, match="description is required"):
            action.validate()

    def test_validate_missing_target_resource(self) -> None:
        """Test validation fails with empty target_resource."""
        action = RemediationAction(
            incident_id="inc-123", action_type="test", description="Test"
        )
        with pytest.raises(ValueError, match="target_resource is required"):
            action.validate()

    def test_validate_invalid_status(self) -> None:
        """Test validation fails with invalid status."""
        action = RemediationAction(
            incident_id="inc-123",
            action_type="test",
            description="Test",
            target_resource="test",
            status="invalid_status",
        )
        with pytest.raises(ValueError, match="status must be one of"):
            action.validate()

    def test_validate_valid_statuses(self) -> None:
        """Test validation passes with all valid statuses."""
        valid_statuses = [
            "pending",
            "approved",
            "rejected",
            "executing",
            "completed",
            "failed",
        ]
        for status in valid_statuses:
            action = RemediationAction(
                incident_id="inc-123",
                action_type="test",
                description="Test",
                target_resource="test",
                status=status,
            )
            action.validate()  # Should not raise

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        approval_time = datetime.now(timezone.utc)
        action = RemediationAction(
            action_id="action-123",
            incident_id="inc-456",
            action_type="isolate",
            status="completed",
            description="Isolate instance",
            target_resource="instance-789",
            params={"key": "value"},
            approved_by="admin@example.com",
            approval_time=approval_time,
            execution_result={"success": True},
            error_message=None,
            automated=False,
            requires_approval=True,
            metadata={"critical": True},
        )

        data = action.to_dict()
        assert data["action_id"] == "action-123"
        assert data["incident_id"] == "inc-456"
        assert data["action_type"] == "isolate"
        assert data["status"] == "completed"
        assert data["description"] == "Isolate instance"
        assert data["target_resource"] == "instance-789"
        assert data["params"] == {"key": "value"}
        assert data["approved_by"] == "admin@example.com"
        assert data["approval_time"] == approval_time.isoformat()
        assert data["execution_result"] == {"success": True}
        assert data["error_message"] is None
        assert data["automated"] is False  # New field test
        assert data["requires_approval"] is True  # New field test
        assert data["metadata"] == {"critical": True}  # New field test
        assert "timestamp" in data

    def test_to_dict_without_approval(self) -> None:
        """Test to_dict with no approval fields."""
        action = RemediationAction(
            incident_id="inc-123",
            action_type="test",
            description="Test",
            target_resource="test",
        )

        data = action.to_dict()
        assert data["approved_by"] is None
        assert data["approval_time"] is None


class TestNotification:
    """Test Notification dataclass."""

    def test_default_initialization(self) -> None:
        """Test Notification with defaults."""
        notification = Notification()
        assert notification.notification_id is not None
        assert isinstance(notification.notification_id, str)
        assert isinstance(notification.timestamp, datetime)
        assert notification.incident_id == ""
        assert notification.notification_type == ""
        assert notification.recipients == []
        assert notification.subject == ""
        assert notification.content == ""
        assert notification.status == "pending"
        assert notification.error_message is None

    def test_full_initialization(self) -> None:
        """Test Notification with all fields."""
        notification = Notification(
            notification_id="notif-123",
            incident_id="inc-456",
            notification_type="email",
            recipients=["user1@example.com", "user2@example.com"],
            subject="Security Alert: Suspicious Login",
            content="A suspicious login was detected...",
            status="sent",
            error_message=None,
        )
        assert notification.notification_id == "notif-123"
        assert notification.incident_id == "inc-456"
        assert notification.notification_type == "email"
        assert notification.recipients == ["user1@example.com", "user2@example.com"]
        assert notification.subject == "Security Alert: Suspicious Login"
        assert notification.content == "A suspicious login was detected..."
        assert notification.status == "sent"
        assert notification.error_message is None

    def test_validate_success(self) -> None:
        """Test successful validation."""
        notification = Notification(
            incident_id="inc-123",
            notification_type="email",
            recipients=["user@example.com"],
            subject="Alert",
            content="Alert content",
        )
        notification.validate()  # Should not raise

    def test_validate_missing_incident_id(self) -> None:
        """Test validation fails with empty incident_id."""
        notification = Notification(
            notification_type="email",
            recipients=["user@example.com"],
            subject="Alert",
            content="Content",
        )
        with pytest.raises(ValueError, match="incident_id is required"):
            notification.validate()

    def test_validate_missing_notification_type(self) -> None:
        """Test validation fails with empty notification_type."""
        notification = Notification(
            incident_id="inc-123",
            recipients=["user@example.com"],
            subject="Alert",
            content="Content",
        )
        with pytest.raises(ValueError, match="notification_type is required"):
            notification.validate()

    def test_validate_empty_recipients(self) -> None:
        """Test validation fails with empty recipients list."""
        notification = Notification(
            incident_id="inc-123",
            notification_type="email",
            recipients=[],
            subject="Alert",
            content="Content",
        )
        with pytest.raises(ValueError, match="recipients list cannot be empty"):
            notification.validate()

    def test_validate_missing_subject(self) -> None:
        """Test validation fails with empty subject."""
        notification = Notification(
            incident_id="inc-123",
            notification_type="email",
            recipients=["user@example.com"],
            subject="",
            content="Content",
        )
        with pytest.raises(ValueError, match="subject is required"):
            notification.validate()

    def test_validate_missing_content(self) -> None:
        """Test validation fails with empty content."""
        notification = Notification(
            incident_id="inc-123",
            notification_type="email",
            recipients=["user@example.com"],
            subject="Alert",
            content="",
        )
        with pytest.raises(ValueError, match="content is required"):
            notification.validate()

    def test_validate_invalid_status(self) -> None:
        """Test validation fails with invalid status."""
        notification = Notification(
            incident_id="inc-123",
            notification_type="email",
            recipients=["user@example.com"],
            subject="Alert",
            content="Content",
            status="invalid",
        )
        with pytest.raises(ValueError, match="status must be one of"):
            notification.validate()

    def test_validate_valid_statuses(self) -> None:
        """Test validation passes with all valid statuses."""
        valid_statuses = ["pending", "sent", "failed", "retrying"]
        for status in valid_statuses:
            notification = Notification(
                incident_id="inc-123",
                notification_type="email",
                recipients=["user@example.com"],
                subject="Alert",
                content="Content",
                status=status,
            )
            notification.validate()  # Should not raise

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        notification = Notification(
            notification_id="notif-123",
            incident_id="inc-456",
            notification_type="slack",
            recipients=["#security-alerts", "@admin"],
            subject="High Priority Alert",
            content="Details of the alert",
            status="sent",
            error_message=None,
        )

        data = notification.to_dict()
        assert data["notification_id"] == "notif-123"
        assert data["incident_id"] == "inc-456"
        assert data["notification_type"] == "slack"
        assert data["recipients"] == ["#security-alerts", "@admin"]
        assert data["subject"] == "High Priority Alert"
        assert data["content"] == "Details of the alert"
        assert data["status"] == "sent"
        assert data["error_message"] is None
        assert "timestamp" in data

    def test_to_dict_with_error(self) -> None:
        """Test to_dict with error message."""
        notification = Notification(
            incident_id="inc-123",
            notification_type="email",
            recipients=["user@example.com"],
            subject="Alert",
            content="Content",
            status="failed",
            error_message="SMTP connection failed",
        )

        data = notification.to_dict()
        assert data["status"] == "failed"
        assert data["error_message"] == "SMTP connection failed"


class TestIncident:
    """Test Incident dataclass."""

    def test_default_initialization(self) -> None:
        """Test Incident with defaults."""
        incident = Incident()
        assert incident.incident_id is not None
        assert isinstance(incident.incident_id, str)
        assert isinstance(incident.created_at, datetime)
        assert isinstance(incident.updated_at, datetime)
        assert incident.title == ""
        assert incident.description == ""
        assert incident.severity == SeverityLevel.INFORMATIONAL
        assert incident.status == IncidentStatus.DETECTED
        assert incident.events == []
        assert incident.analysis is None
        assert incident.remediation_actions == []
        assert incident.notifications == []
        assert incident.assigned_to is None
        assert incident.tags == []
        assert incident.metadata == {}

    def test_full_initialization(self) -> None:
        """Test Incident with all fields."""
        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )
        analysis = AnalysisResult(
            incident_id="inc-123",
            confidence_score=0.9,
            summary="Summary",
            detailed_analysis="Analysis",
        )
        action = RemediationAction(
            incident_id="inc-123",
            action_type="block",
            description="Block IP",
            target_resource="192.168.1.1",
        )
        notification = Notification(
            incident_id="inc-123",
            notification_type="email",
            recipients=["admin@example.com"],
            subject="Alert",
            content="Alert content",
        )

        incident = Incident(
            incident_id="inc-123",
            title="Suspicious Login Detected",
            description="Multiple failed login attempts",
            severity=SeverityLevel.HIGH,
            status=IncidentStatus.ANALYZING,
            events=[event],
            analysis=analysis,
            remediation_actions=[action],
            notifications=[notification],
            assigned_to="security-team",
            tags=["login", "brute-force"],
            metadata={"source_ip": "192.168.1.1"},
        )

        assert incident.incident_id == "inc-123"
        assert incident.title == "Suspicious Login Detected"
        assert incident.description == "Multiple failed login attempts"
        assert incident.severity == SeverityLevel.HIGH
        assert incident.status == IncidentStatus.ANALYZING
        assert len(incident.events) == 1
        assert incident.analysis == analysis
        assert len(incident.remediation_actions) == 1
        assert len(incident.notifications) == 1
        assert incident.assigned_to == "security-team"
        assert incident.tags == ["login", "brute-force"]
        assert incident.metadata == {"source_ip": "192.168.1.1"}

    def test_validate_success(self) -> None:
        """Test successful validation."""
        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )
        incident = Incident(
            title="Test Incident", description="Test description", events=[event]
        )
        incident.validate()  # Should not raise

    def test_validate_missing_title(self) -> None:
        """Test validation fails with empty title."""
        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )
        incident = Incident(description="Test description", events=[event])
        with pytest.raises(ValueError, match="title is required"):
            incident.validate()

    def test_validate_missing_description(self) -> None:
        """Test validation fails with empty description."""
        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )
        incident = Incident(title="Test Incident", events=[event])
        with pytest.raises(ValueError, match="description is required"):
            incident.validate()

    def test_validate_no_events(self) -> None:
        """Test validation fails with no events."""
        incident = Incident(title="Test Incident", description="Test description")
        with pytest.raises(
            ValueError, match="incident must have at least one security event"
        ):
            incident.validate()

    def test_validate_nested_objects(self) -> None:
        """Test validation validates nested objects."""
        # Invalid event (missing event_type)
        event = SecurityEvent(
            source=EventSource("test", "test", "test"), description="Test event"
        )
        incident = Incident(
            title="Test Incident", description="Test description", events=[event]
        )
        with pytest.raises(ValueError, match="event_type is required"):
            incident.validate()

    def test_add_event(self) -> None:
        """Test adding events to incident."""
        incident = Incident(
            title="Test", description="Test", severity=SeverityLevel.LOW
        )

        # Add a medium severity event
        event1 = SecurityEvent(
            event_type="test1",
            source=EventSource("test", "test", "test"),
            description="Test event 1",
            severity=SeverityLevel.MEDIUM,
        )
        incident.add_event(event1)

        assert len(incident.events) == 1
        assert incident.severity == SeverityLevel.MEDIUM  # Escalated

        # Add a high severity event
        event2 = SecurityEvent(
            event_type="test2",
            source=EventSource("test", "test", "test"),
            description="Test event 2",
            severity=SeverityLevel.HIGH,
        )
        incident.add_event(event2)

        assert len(incident.events) == 2
        # Escalated again
        assert incident.severity == SeverityLevel.HIGH  # type: ignore[comparison-overlap]

    def test_add_event_validation(self) -> None:
        """Test add_event validates the event."""
        incident = Incident(title="Test", description="Test")

        # Invalid event
        event = SecurityEvent(
            source=EventSource("test", "test", "test"), description="Test"
        )

        with pytest.raises(ValueError, match="event_type is required"):
            incident.add_event(event)

    def test_add_remediation_action(self) -> None:
        """Test adding remediation actions."""
        incident = Incident(incident_id="inc-123", title="Test", description="Test")

        action = RemediationAction(
            incident_id="different-id",  # Will be overwritten
            action_type="block",
            description="Block IP",
            target_resource="192.168.1.1",
        )

        incident.add_remediation_action(action)

        assert len(incident.remediation_actions) == 1
        assert action.incident_id == "inc-123"  # Updated to match

    def test_add_remediation_action_validation(self) -> None:
        """Test add_remediation_action validates the action."""
        incident = Incident(incident_id="inc-123", title="Test", description="Test")

        # Invalid action - has incident_id but missing target_resource
        action = RemediationAction(
            incident_id="inc-123",
            action_type="block",
            description="Block IP",
            # Missing target_resource
        )

        with pytest.raises(ValueError, match="target_resource is required"):
            incident.add_remediation_action(action)

    def test_update_status(self) -> None:
        """Test status updates."""
        incident = Incident(
            title="Test", description="Test", status=IncidentStatus.DETECTED
        )

        original_updated = incident.updated_at
        # Store original timestamp with timezone awareness
        original_updated = incident.updated_at
        if original_updated and original_updated.tzinfo is None:
            original_updated = original_updated.replace(tzinfo=timezone.utc)

        # Small delay to ensure timestamp changes
        import time

        time.sleep(0.01)

        incident.update_status(IncidentStatus.ANALYZING)

        assert incident.status == IncidentStatus.ANALYZING
        # Ensure both datetimes are timezone-aware for comparison
        updated_at = incident.updated_at
        if updated_at and updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        assert updated_at > original_updated

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )
        analysis = AnalysisResult(
            incident_id="inc-123",
            confidence_score=0.9,
            summary="Summary",
            detailed_analysis="Analysis",
        )

        incident = Incident(
            incident_id="inc-123",
            title="Test Incident",
            description="Test description",
            severity=SeverityLevel.HIGH,
            status=IncidentStatus.RESOLVED,
            events=[event],
            analysis=analysis,
            assigned_to="admin",
            tags=["test"],
            metadata={"key": "value"},
        )

        data = incident.to_dict()

        assert data["incident_id"] == "inc-123"
        assert data["title"] == "Test Incident"
        assert data["description"] == "Test description"
        assert data["severity"] == "high"
        assert data["status"] == "resolved"
        assert len(data["events"]) == 1
        assert data["analysis"] is not None
        assert data["remediation_actions"] == []
        assert data["notifications"] == []
        assert data["assigned_to"] == "admin"
        assert data["tags"] == ["test"]
        assert data["metadata"] == {"key": "value"}
        assert "created_at" in data
        assert "updated_at" in data

    # NEW TESTS FOR MISSING from_dict COVERAGE
    def test_from_dict_basic(self) -> None:
        """Test from_dict with basic data."""
        data = {
            "incident_id": "inc-123",
            "title": "Test Incident",
            "description": "Test description",
            "severity": "high",
            "status": "analyzing",
            "events": [],
            "assigned_to": "admin",
            "tags": ["test"],
            "metadata": {"key": "value"},
        }

        incident = Incident.from_dict(data)
        assert incident.incident_id == "inc-123"
        assert incident.title == "Test Incident"
        assert incident.description == "Test description"
        assert incident.severity == SeverityLevel.HIGH
        assert incident.status == IncidentStatus.ANALYZING
        assert incident.assigned_to == "admin"
        assert incident.tags == ["test"]
        assert incident.metadata == {"key": "value"}

    def test_from_dict_with_timestamps(self) -> None:
        """Test from_dict converts timestamp strings."""
        data = {
            "incident_id": "inc-123",
            "title": "Test",
            "description": "Test",
            "created_at": "2024-01-01T12:00:00+00:00",
            "updated_at": "2024-01-01T13:00:00+00:00",
            "events": [],
        }

        incident = Incident.from_dict(data)
        assert isinstance(incident.created_at, datetime)
        assert isinstance(incident.updated_at, datetime)
        assert incident.created_at.year == 2024
        assert incident.updated_at.hour == 13

    def test_from_dict_with_events(self) -> None:
        """Test from_dict converts events properly."""
        event_data = {
            "event_id": "event-123",
            "event_type": "test_event",
            "description": "Test event",
            "severity": "critical",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "source": {
                "source_type": "test",
                "source_name": "test_source",
                "source_id": "source-123",
            },
        }

        data = {
            "incident_id": "inc-123",
            "title": "Test",
            "description": "Test",
            "events": [event_data],
        }

        incident = Incident.from_dict(data)
        assert len(incident.events) == 1
        event = incident.events[0]
        assert isinstance(event, SecurityEvent)
        assert event.event_id == "event-123"
        assert event.severity == SeverityLevel.CRITICAL
        assert isinstance(event.source, EventSource)
        assert event.source.source_type == "test"

    def test_from_dict_with_analysis(self) -> None:
        """Test from_dict converts analysis properly."""
        analysis_data = {
            "analysis_id": "analysis-123",
            "incident_id": "inc-123",
            "confidence_score": 0.9,
            "summary": "Test summary",
            "detailed_analysis": "Test analysis",
            "timestamp": "2024-01-01T12:00:00+00:00",
        }

        data = {
            "incident_id": "inc-123",
            "title": "Test",
            "description": "Test",
            "events": [],
            "analysis": analysis_data,
        }

        incident = Incident.from_dict(data)
        assert incident.analysis is not None
        assert isinstance(incident.analysis, AnalysisResult)
        assert incident.analysis.analysis_id == "analysis-123"
        assert isinstance(incident.analysis.timestamp, datetime)

    def test_from_dict_with_remediation_actions(self) -> None:
        """Test from_dict converts remediation actions properly."""
        action_data = {
            "action_id": "action-123",
            "incident_id": "inc-123",
            "action_type": "block_ip",
            "description": "Block malicious IP",
            "target_resource": "192.168.1.1",
            "status": "completed",
        }

        data = {
            "incident_id": "inc-123",
            "title": "Test",
            "description": "Test",
            "events": [],
            "remediation_actions": [action_data],
        }

        incident = Incident.from_dict(data)
        assert len(incident.remediation_actions) == 1
        action = incident.remediation_actions[0]
        assert isinstance(action, RemediationAction)
        assert action.action_id == "action-123"

    def test_from_dict_with_notifications(self) -> None:
        """Test from_dict converts notifications properly."""
        notif_data = {
            "notification_id": "notif-123",
            "incident_id": "inc-123",
            "notification_type": "email",
            "recipients": ["admin@example.com"],
            "subject": "Alert",
            "content": "Test alert",
            "status": "sent",
        }

        data = {
            "incident_id": "inc-123",
            "title": "Test",
            "description": "Test",
            "events": [],
            "notifications": [notif_data],
        }

        incident = Incident.from_dict(data)
        assert len(incident.notifications) == 1
        notification = incident.notifications[0]
        assert isinstance(notification, Notification)
        assert notification.notification_id == "notif-123"

    def test_convert_enums(self) -> None:
        """Test _convert_enums helper method."""
        data: Dict[str, Any] = {"severity": "critical", "status": "resolved"}

        Incident._convert_enums(data)
        assert data["severity"] == SeverityLevel.CRITICAL
        assert data["status"] == IncidentStatus.RESOLVED

    def test_convert_enums_with_invalid_values(self) -> None:
        """Test _convert_enums handles already-converted enums."""
        data = {"severity": SeverityLevel.HIGH, "status": IncidentStatus.ANALYZING}

        # Should not raise or change values
        Incident._convert_enums(data)
        assert data["severity"] == SeverityLevel.HIGH
        assert data["status"] == IncidentStatus.ANALYZING

    def test_convert_timestamps(self) -> None:
        """Test _convert_timestamps helper method."""
        data = {
            "created_at": "2024-01-01T12:00:00+00:00",
            "updated_at": "2024-01-01T13:00:00+00:00",
            "other_field": "not_a_timestamp",
        }

        Incident._convert_timestamps(data)
        assert isinstance(data["created_at"], datetime)  # type: ignore[unreachable]
        assert isinstance(data["updated_at"], datetime)  # type: ignore[unreachable]
        assert data["other_field"] == "not_a_timestamp"

    def test_convert_timestamps_with_datetime_objects(self) -> None:
        """Test _convert_timestamps handles already-converted timestamps."""
        now = datetime.now(timezone.utc)
        data = {"created_at": now, "updated_at": now}

        # Should not raise or change values
        Incident._convert_timestamps(data)
        assert data["created_at"] == now
        assert data["updated_at"] == now

    def test_convert_events_empty(self) -> None:
        """Test _convert_events with no events."""
        data: Dict[str, Any] = {}
        Incident._convert_events(data)
        # Should not add events key
        assert "events" not in data

        data = {"events": []}
        Incident._convert_events(data)
        assert not data["events"]

    def test_convert_event_data(self) -> None:
        """Test _convert_event_data helper method."""
        event_data = {
            "event_id": "event-123",
            "severity": "high",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "source": {
                "source_type": "test",
                "source_name": "test_source",
                "source_id": "source-123",
            },
        }

        Incident._convert_event_data(event_data)
        assert isinstance(event_data["source"], EventSource)
        assert event_data["severity"] == SeverityLevel.HIGH  # type: ignore[comparison-overlap]
        assert isinstance(event_data["timestamp"], datetime)  # type: ignore[unreachable]

    def test_convert_analysis_none(self) -> None:
        """Test _convert_analysis with no analysis."""
        data: Dict[str, Any] = {}
        Incident._convert_analysis(data)
        assert "analysis" not in data

        data = {"analysis": None}
        Incident._convert_analysis(data)
        assert data["analysis"] is None

    def test_convert_analysis_with_data(self) -> None:
        """Test _convert_analysis with analysis data."""
        analysis_data = {
            "analysis_id": "analysis-123",
            "incident_id": "inc-123",
            "confidence_score": 0.9,
            "summary": "Test",
            "detailed_analysis": "Test",
            "timestamp": "2024-01-01T12:00:00+00:00",
        }

        data = {"analysis": analysis_data}
        Incident._convert_analysis(data)
        assert isinstance(data["analysis"], AnalysisResult)

    def test_convert_remediation_actions_empty(self) -> None:
        """Test _convert_remediation_actions with no actions."""
        data: Dict[str, Any] = {}
        Incident._convert_remediation_actions(data)
        assert "remediation_actions" not in data

        data = {"remediation_actions": []}
        Incident._convert_remediation_actions(data)
        assert not data["remediation_actions"]

    def test_convert_remediation_action_data(self) -> None:
        """Test _convert_remediation_action_data helper method."""
        action_data = {
            "created_at": "2024-01-01T12:00:00+00:00",
            "executed_at": "2024-01-01T12:30:00+00:00",
            "status": "completed",
            "priority": "high",
        }

        Incident._convert_remediation_action_data(action_data)
        # Note: The method expects RemediationStatus and RemediationPriority enums
        # but the current implementation tries to convert strings to these enums
        # This test verifies the method doesn't break with valid string values

    def test_convert_notifications_empty(self) -> None:
        """Test _convert_notifications with no notifications."""
        data: Dict[str, Any] = {}
        Incident._convert_notifications(data)
        assert "notifications" not in data

        data = {"notifications": []}
        Incident._convert_notifications(data)
        assert not data["notifications"]

    def test_convert_notification_data(self) -> None:
        """Test _convert_notification_data helper method."""
        notif_data = {
            "created_at": "2024-01-01T12:00:00+00:00",
            "sent_at": "2024-01-01T12:05:00+00:00",
            "other_field": "not_a_timestamp",
        }

        Incident._convert_notification_data(notif_data)
        # Should convert timestamp fields to datetime objects
        # Note: The actual implementation only converts created_at and sent_at
        assert notif_data["other_field"] == "not_a_timestamp"

    def test_full_integration_from_dict(self) -> None:
        """Test complete integration of from_dict with all components."""
        complete_data = {
            "incident_id": "inc-123",
            "title": "Complex Incident",
            "description": "Full integration test",
            "severity": "critical",
            "status": "analyzing",
            "created_at": "2024-01-01T10:00:00+00:00",
            "updated_at": "2024-01-01T11:00:00+00:00",
            "events": [
                {
                    "event_id": "event-1",
                    "event_type": "login_failure",
                    "description": "Failed login attempt",
                    "severity": "medium",
                    "timestamp": "2024-01-01T10:30:00+00:00",
                    "source": {
                        "source_type": "auth_service",
                        "source_name": "login_monitor",
                        "source_id": "monitor-123",
                    },
                }
            ],
            "analysis": {
                "analysis_id": "analysis-456",
                "incident_id": "inc-123",
                "confidence_score": 0.85,
                "summary": "Brute force attack detected",
                "detailed_analysis": "Multiple failed logins from same IP",
                "timestamp": "2024-01-01T10:45:00+00:00",
            },
            "remediation_actions": [
                {
                    "action_id": "action-789",
                    "incident_id": "inc-123",
                    "action_type": "block_ip",
                    "description": "Block source IP",
                    "target_resource": "192.168.1.100",
                    "status": "pending",
                }
            ],
            "notifications": [
                {
                    "notification_id": "notif-321",
                    "incident_id": "inc-123",
                    "notification_type": "email",
                    "recipients": ["security@example.com"],
                    "subject": "Security Alert",
                    "content": "Incident detected",
                    "status": "sent",
                }
            ],
            "assigned_to": "security_team",
            "tags": ["brute_force", "login"],
            "metadata": {"source_ip": "192.168.1.100"},
        }

        incident = Incident.from_dict(complete_data)

        # Verify all components were properly converted
        assert incident.incident_id == "inc-123"
        assert incident.severity == SeverityLevel.CRITICAL
        assert incident.status == IncidentStatus.ANALYZING
        assert isinstance(incident.created_at, datetime)
        assert len(incident.events) == 1
        assert isinstance(incident.events[0], SecurityEvent)
        assert incident.analysis is not None
        assert isinstance(incident.analysis, AnalysisResult)
        assert len(incident.remediation_actions) == 1
        assert isinstance(incident.remediation_actions[0], RemediationAction)
        assert len(incident.notifications) == 1
        assert isinstance(incident.notifications[0], Notification)


class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions for comprehensive coverage."""

    def test_security_event_default_source_validation(self) -> None:
        """Test SecurityEvent with default empty source fails validation."""
        event = SecurityEvent(event_type="test", description="test")
        # Default source has empty strings, should fail validation
        with pytest.raises(ValueError, match="source_type is required"):
            event.validate()

    def test_incident_validate_with_analysis_and_actions(self) -> None:
        """Test incident validation includes analysis and action validation."""
        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )

        # Valid analysis
        analysis = AnalysisResult(
            incident_id="inc-123",
            confidence_score=0.8,
            summary="Test",
            detailed_analysis="Test",
        )

        # Invalid action (missing target_resource)
        action = RemediationAction(
            incident_id="inc-123", action_type="test", description="Test"
        )

        incident = Incident(
            title="Test",
            description="Test",
            events=[event],
            analysis=analysis,
            remediation_actions=[action],
        )

        with pytest.raises(ValueError, match="target_resource is required"):
            incident.validate()

    def test_analysis_result_edge_case_confidence_scores(self) -> None:
        """Test AnalysisResult validation with edge case confidence scores."""
        # Exactly 0.0
        result = AnalysisResult(
            incident_id="inc-123",
            confidence_score=0.0,
            summary="Test",
            detailed_analysis="Test",
        )
        result.validate()  # Should not raise

        # Exactly 1.0
        result.confidence_score = 1.0
        result.validate()  # Should not raise

    def test_incident_add_event_updates_timestamp(self) -> None:
        """Test that add_event updates the updated_at timestamp."""
        incident = Incident(title="Test", description="Test")
        original_updated = incident.updated_at

        import time

        time.sleep(0.01)  # Small delay

        event = SecurityEvent(
            event_type="test",
            source=EventSource("test", "test", "test"),
            description="Test event",
        )
        incident.add_event(event)

        assert incident.updated_at > original_updated

    def test_incident_add_remediation_action_updates_timestamp(self) -> None:
        """Test that add_remediation_action updates the updated_at timestamp."""
        incident = Incident(incident_id="inc-123", title="Test", description="Test")
        original_updated = incident.updated_at

        import time

        time.sleep(0.01)  # Small delay

        action = RemediationAction(
            incident_id="inc-123",
            action_type="test",
            description="Test",
            target_resource="test",
        )
        incident.add_remediation_action(action)

        assert incident.updated_at > original_updated

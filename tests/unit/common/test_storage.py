"""Tests for common/storage.py using REAL file I/O operations."""

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

import pytest
import pytest_asyncio

from src.common.models import (
    AnalysisResult,
    Incident,
    IncidentStatus,
    SeverityLevel,
)
from src.common.storage import Storage
from src.detection_agent.rules_engine import DetectionRule, RuleStatus


@pytest_asyncio.fixture
async def storage() -> AsyncGenerator[Storage, None]:
    """Create Storage instance with real temporary directory."""
    # Create real temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_sentinelops_")
    storage_instance = Storage(base_path=temp_dir)
    yield storage_instance

    # Cleanup: Remove all files and directories
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_incident() -> Incident:
    """Create a sample incident."""
    return Incident(
        incident_id="test-incident-123",
        title="Test Security Incident",
        description="A test incident for unit testing",
        severity=SeverityLevel.MEDIUM,
        status=IncidentStatus.DETECTED,
        created_at=datetime.now(timezone.utc),
        metadata={
            "region": "us-central1",
            "zone": "us-central1-a",
            "labels": {"env": "test"},
            "resource_type": "compute.googleapis.com/Instance",
            "resource_name": "test-vm-instance",
            "project_id": "test-project",
            "detection_source": "test-detector",
        },
    )


@pytest.fixture
def sample_analysis() -> AnalysisResult:
    """Create a sample analysis result."""
    return AnalysisResult(
        incident_id="test-incident-123",
        confidence_score=0.85,
        summary="Test incident analysis summary",
        detailed_analysis="Detailed analysis of the test incident",
        attack_techniques=["T1078", "T1190"],
        recommendations=["Isolate the affected resource", "Review access logs"],
        evidence={
            "severity_assessment": "MEDIUM",
            "impact_assessment": "Medium impact on test resources",
            "root_cause_analysis": "Test root cause",
            "threat_indicators": ["indicator1", "indicator2"],
        },
        gemini_explanation="AI-generated explanation of the incident",
    )


@pytest.fixture
def sample_rule() -> DetectionRule:
    """Create a sample detection rule."""
    return DetectionRule(
        rule_id="test-rule-123",
        name="Test Detection Rule",
        description="Rule for unit testing",
        severity=SeverityLevel.MEDIUM,
        query="resource.type='gce_instance' AND severity='ERROR'",
        status=RuleStatus.ENABLED,
        tags=["test", "vm", "security"],
        metadata={
            "category": "infrastructure",
            "source": "test",
            "rule_type": "log_based",
        },
    )


class TestStorageInitialization:
    """Test Storage initialization."""

    @pytest.mark.asyncio
    async def test_initialization_creates_directories(self, store: Storage) -> None:
        """Test that initialization creates all required directories."""
        # Verify base path exists
        assert store.base_path.exists()
        assert store.base_path.is_dir()

        # Verify subdirectories exist
        assert store.incidents_path.exists()
        assert store.analyses_path.exists()
        assert store.rules_path.exists()
        assert store.feedback_path.exists()

    def test_initialization_with_custom_path(self) -> None:
        """Test initialization with custom base path."""
        custom_path = tempfile.mkdtemp(prefix="custom_test_")
        storage_instance = Storage(base_path=custom_path)

        assert storage_instance.base_path == Path(custom_path)
        assert storage_instance.base_path.exists()

        # Cleanup
        import shutil

        shutil.rmtree(custom_path, ignore_errors=True)


class TestIncidentOperations:
    """Test incident CRUD operations with real file I/O."""

    @pytest.mark.asyncio
    async def test_create_incident(
        self, storage_instance: Storage, incident_data: Incident
    ) -> None:
        """Test creating an incident writes to disk."""
        # Create incident
        incident_id = await storage_instance.create_incident(incident_data)

        # Verify ID was assigned
        assert incident_id is not None
        assert len(incident_id) > 0

        # Verify file exists on disk
        file_path = storage_instance.incidents_path / f"{incident_id}.json"
        assert file_path.exists()

        # Verify file contents
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["title"] == incident_data.title
            assert data["severity"] == incident_data.severity.value

    @pytest.mark.asyncio
    async def test_get_incident(
        self, storage_instance: Storage, incident_data: Incident
    ) -> None:
        """Test getting an incident reads from disk."""
        # Create incident first
        incident_id = await storage_instance.create_incident(incident_data)

        # Get incident
        retrieved = await storage_instance.get_incident(incident_id)

        assert retrieved is not None
        assert retrieved.incident_id == incident_id
        assert retrieved.title == incident_data.title
        assert retrieved.severity == incident_data.severity

    @pytest.mark.asyncio
    async def test_get_nonexistent_incident(self, storage_instance: Storage) -> None:
        """Test getting non-existent incident returns None."""
        result = await storage_instance.get_incident("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_incident(
        self, storage_instance: Storage, incident_data: Incident
    ) -> None:
        """Test updating an incident modifies disk file."""
        # Create incident
        incident_id = await storage_instance.create_incident(incident_data)

        # Get original timestamp
        original = await storage_instance.get_incident(incident_id)
        assert original is not None
        original_updated_at = original.updated_at

        # Update incident
        incident_data.status = IncidentStatus.ANALYZING
        incident_data.severity = SeverityLevel.HIGH
        success = await storage_instance.update_incident(incident_id, incident_data)

        assert success is True

        # Verify changes persisted
        updated = await storage_instance.get_incident(incident_id)
        assert updated is not None
        assert updated.status == IncidentStatus.ANALYZING
        assert updated.severity == SeverityLevel.HIGH
        assert updated.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_delete_incident(
        self,
        storage_instance: Storage,
        incident_data: Incident,
        analysis_data: AnalysisResult,
    ) -> None:
        """Test deleting incident removes files from disk."""
        # Create incident and analysis
        incident_id = await storage_instance.create_incident(incident_data)
        await storage_instance.store_analysis(incident_id, analysis_data)

        # Verify files exist
        incident_file = storage_instance.incidents_path / f"{incident_id}.json"
        analysis_file = storage_instance.analyses_path / f"{incident_id}.json"
        assert incident_file.exists()
        assert analysis_file.exists()

        # Delete incident
        success = await storage_instance.delete_incident(incident_id)
        assert success is True

        # Verify files removed
        assert not incident_file.exists()
        assert not analysis_file.exists()

    @pytest.mark.asyncio
    async def test_get_incidents_with_filters(self, storage_instance: Storage) -> None:
        """Test getting incidents with status and severity filters."""
        # Create incidents with different statuses and severities
        incidents = [
            Incident(
                title=f"Incident {i}",
                description=f"Test incident {i}",
                severity=SeverityLevel.HIGH if i % 2 == 0 else SeverityLevel.LOW,
                status=IncidentStatus.DETECTED if i < 3 else IncidentStatus.RESOLVED,
                created_at=datetime.now(timezone.utc),
                metadata={"test": f"value{i}"},
            )
            for i in range(5)
        ]

        # Store all incidents
        incident_ids = []
        for incident in incidents:
            incident_id = await storage_instance.create_incident(incident)
            incident_ids.append(incident_id)

        # Test filtering by status
        detected_incidents = await storage_instance.get_incidents(
            status=IncidentStatus.DETECTED, limit=10
        )
        assert len(detected_incidents) == 3

        # Test filtering by severity
        high_severity_incidents = await storage_instance.get_incidents(
            severity=SeverityLevel.HIGH, limit=10
        )
        assert len(high_severity_incidents) == 3

    @pytest.mark.asyncio
    async def test_get_incidents_pagination(self, storage_instance: Storage) -> None:
        """Test incident pagination."""
        # Create multiple incidents
        incidents = [
            Incident(
                title=f"Incident {i}",
                description=f"Test incident {i}",
                severity=SeverityLevel.MEDIUM,
                status=IncidentStatus.DETECTED,
                created_at=datetime.now(timezone.utc),
                metadata={"test": f"value{i}"},
            )
            for i in range(10)
        ]

        # Store all incidents
        for incident in incidents:
            await storage_instance.create_incident(incident)

        # Test pagination
        page1 = await storage_instance.get_incidents(limit=5, offset=0)
        page2 = await storage_instance.get_incidents(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) == 5

        # Verify no overlap
        page1_ids = [incident.incident_id for incident in page1]
        page2_ids = [incident.incident_id for incident in page2]
        assert len(set(page1_ids) & set(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_count_incidents(self, storage_instance: Storage) -> None:
        """Test counting incidents with filters."""
        # Create incidents with different statuses
        incidents = [
            Incident(
                title=f"Incident {i}",
                description=f"Test incident {i}",
                severity=SeverityLevel.MEDIUM,
                status=IncidentStatus.DETECTED if i < 3 else IncidentStatus.RESOLVED,
                created_at=datetime.now(timezone.utc),
                metadata={"test": f"value{i}"},
            )
            for i in range(5)
        ]

        # Store all incidents
        for incident in incidents:
            await storage_instance.create_incident(incident)

        # Count all incidents
        total_count = await storage_instance.count_incidents()
        assert total_count == 5

        # Count with status filter
        detected_count = await storage_instance.count_incidents(
            status=IncidentStatus.DETECTED
        )
        assert detected_count == 3

        resolved_count = await storage_instance.count_incidents(
            status=IncidentStatus.RESOLVED
        )
        assert resolved_count == 2

    @pytest.mark.asyncio
    async def test_get_incident_stats(self, storage_instance: Storage) -> None:
        """Test getting incident statistics."""
        # Create incidents with various statuses and severities
        test_data = [
            (IncidentStatus.DETECTED, SeverityLevel.HIGH),
            (IncidentStatus.DETECTED, SeverityLevel.HIGH),
            (IncidentStatus.ANALYZING, SeverityLevel.MEDIUM),
            (IncidentStatus.RESOLVED, SeverityLevel.LOW),
            (IncidentStatus.RESOLVED, SeverityLevel.LOW),
        ]

        # Create incidents
        for status, severity in test_data:
            incident = Incident(
                title="Test Incident",
                description="Test description",
                severity=severity,
                status=status,
                created_at=datetime.now(timezone.utc),
                metadata={"test": "value"},
            )
            await storage_instance.create_incident(incident)

        # Get statistics
        stats = await storage_instance.get_incident_stats()

        # Verify counts
        assert stats["total"] == 5
        assert stats["by_status"][IncidentStatus.DETECTED.value] == 2
        assert stats["by_status"][IncidentStatus.ANALYZING.value] == 1
        assert stats["by_status"][IncidentStatus.RESOLVED.value] == 2
        assert stats["by_severity"][SeverityLevel.HIGH.value] == 2
        assert stats["by_severity"][SeverityLevel.MEDIUM.value] == 1
        assert stats["by_severity"][SeverityLevel.LOW.value] == 2

        # Verify time-based stats
        assert "created_last_24h" in stats
        assert "created_last_7d" in stats
        assert stats["created_last_24h"] == 5  # All created today
        assert stats["created_last_7d"] == 5  # All created this week


class TestAnalysisOperations:
    """Test analysis operations with real file I/O."""

    @pytest.mark.asyncio
    async def test_store_and_get_analysis(
        self, storage_instance: Storage, analysis_data: AnalysisResult
    ) -> None:
        """Test storing and retrieving analysis."""
        incident_id = "test-incident-123"

        # Store analysis
        success = await storage_instance.store_analysis(incident_id, analysis_data)
        assert success is True

        # Verify file exists
        file_path = storage_instance.analyses_path / f"{incident_id}.json"
        assert file_path.exists()

        # Get analysis
        retrieved = await storage_instance.get_analysis(incident_id)
        assert retrieved is not None
        assert retrieved.incident_id == analysis_data.incident_id
        assert retrieved.confidence_score == analysis_data.confidence_score

    @pytest.mark.asyncio
    async def test_get_recent_analyses(self, storage_instance: Storage) -> None:
        """Test getting recent analyses."""
        # Create multiple analyses with different timestamps
        analyses = []
        for i in range(5):
            analysis = AnalysisResult(
                incident_id=f"incident-{i}",
                confidence_score=0.8 + (i * 0.02),
                summary=f"Analysis {i}",
                detailed_analysis=f"Detailed analysis {i}",
                attack_techniques=[f"T{1000 + i}"],
                recommendations=[f"Recommendation {i}"],
                evidence={"test": f"evidence{i}"},
                gemini_explanation=f"AI explanation {i}",
            )
            analyses.append(analysis)

            # Store with slight delay to ensure different timestamps
            await storage_instance.store_analysis(f"incident-{i}", analysis)
            await asyncio.sleep(0.01)

        # Get recent analyses
        recent = await storage_instance.get_recent_analyses(limit=3)

        assert len(recent) == 3
        # Should be in reverse chronological order (most recent first)
        assert recent[0].incident_id == "incident-4"
        assert recent[1].incident_id == "incident-3"
        assert recent[2].incident_id == "incident-2"


class TestRuleOperations:
    """Test rule operations with real file I/O."""

    @pytest.mark.asyncio
    async def test_create_and_get_rule(
        self, storage_instance: Storage, rule_data: DetectionRule
    ) -> None:
        """Test creating and getting a rule."""
        # Create rule
        rule_id = await storage_instance.create_rule(rule_data)
        assert rule_id is not None

        # Verify file exists
        file_path = storage_instance.rules_path / f"{rule_id}.json"
        assert file_path.exists()

        # Get rule
        retrieved = await storage_instance.get_rule(rule_id)
        assert retrieved is not None
        assert retrieved.name == rule_data.name
        assert retrieved.severity == rule_data.severity

    @pytest.mark.asyncio
    async def test_update_rule(
        self, storage_instance: Storage, rule_data: DetectionRule
    ) -> None:
        """Test updating a rule."""
        # Create rule
        rule_id = await storage_instance.create_rule(rule_data)

        # Update rule
        rule_data.description = "Updated description"
        rule_data.severity = SeverityLevel.CRITICAL
        success = await storage_instance.update_rule(rule_id, rule_data)
        assert success is True

        # Verify update
        updated = await storage_instance.get_rule(rule_id)
        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.severity == SeverityLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_delete_rule(
        self, storage_instance: Storage, rule_data: DetectionRule
    ) -> None:
        """Test deleting a rule."""
        # Create rule
        rule_id = await storage_instance.create_rule(rule_data)

        # Delete rule
        success = await storage_instance.delete_rule(rule_id)
        assert success is True

        # Verify file deleted
        file_path = storage_instance.rules_path / f"{rule_id}.json"
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_get_rules_with_filter(self, storage_instance: Storage) -> None:
        """Test getting rules with filters."""
        # Create rules with different severities and statuses
        rules = [
            DetectionRule(
                rule_id=f"rule_{i}",
                name=f"Rule {i}",
                description=f"Test rule {i}",
                severity=SeverityLevel.HIGH if i % 2 == 0 else SeverityLevel.LOW,
                query=f"SELECT timestamp FROM table WHERE timestamp > TIMESTAMP('{{last_scan_time}}') AND timestamp <= TIMESTAMP('{{current_time}}') AND test_field = 'test query {i}'",
                status=RuleStatus.ENABLED if i < 3 else RuleStatus.DISABLED,
                tags=[f"tag{i}"],
                metadata={"test": f"value{i}"},
            )
            for i in range(5)
        ]

        # Store all rules
        for rule in rules:
            await storage_instance.create_rule(rule)

        # Test filtering by enabled status
        enabled_rules = await storage_instance.get_rules(enabled=True)
        assert len(enabled_rules) == 3

        # Test disabled rules
        disabled_rules = await storage_instance.get_rules(enabled=False)
        assert len(disabled_rules) == 2


class TestFeedbackOperations:
    """Test feedback operations with real file I/O."""

    @pytest.mark.asyncio
    async def test_store_feedback(self, storage_instance: Storage) -> None:
        """Test storing feedback."""
        # Store feedback
        feedback_id = await storage_instance.store_feedback(
            feedback_type="accuracy",
            feedback_data={
                "incident_id": "test-incident-123",
                "user_id": "test-user",
                "rating": 4,
                "comments": "Good analysis",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {"source": "web_ui"},
            },
        )
        assert feedback_id is not None

        # Verify file exists
        feedback_files = list(storage_instance.feedback_path.glob("*.json"))
        assert len(feedback_files) >= 1

        # Verify content
        with open(feedback_files[0], "r", encoding="utf-8") as f:
            stored_data = json.load(f)
            assert stored_data["rating"] == 4
            assert stored_data["incident_id"] == "test-incident-123"


class TestRemediationOperations:
    """Test remediation operations with real file I/O."""

    @pytest.mark.asyncio
    async def test_create_remediation_execution(
        self, storage_instance: Storage
    ) -> None:
        """Test creating remediation execution."""
        execution_id = await storage_instance.create_remediation_execution(
            action_id="test-action-123",
            executed_by="test-user",
            parameters={"target": "192.168.1.100"},
            dry_run=False,
        )
        assert execution_id is not None

        # Verify execution can be retrieved
        retrieved = await storage_instance.get_remediation_execution(execution_id)
        assert retrieved is not None
        assert retrieved.action_id == "test-action-123"

    @pytest.mark.asyncio
    async def test_get_remediation_history(self, storage_instance: Storage) -> None:
        """Test getting remediation history."""
        # Create multiple executions for the same incident
        incident_id = "test-incident-123"
        executions = []

        for i in range(3):
            execution_id = await storage_instance.create_remediation_execution(
                action_id=f"action-{i}",
                executed_by="test-user",
                parameters={"target": f"192.168.1.{100 + i}"},
                dry_run=False,
            )
            executions.append(execution_id)

        # Get history
        history = await storage_instance.get_remediation_history(incident_id)

        assert len(history) == 3
        # Verify all executions are for the correct incident
        for execution in history:
            assert hasattr(execution, "action_id")

    @pytest.mark.asyncio
    async def test_create_remediation_rollback(self, storage_instance: Storage) -> None:
        """Test creating remediation rollback."""
        # First create an execution
        execution_id = await storage_instance.create_remediation_execution(
            action_id="test-action-123",
            executed_by="test-user",
            parameters={"target": "192.168.1.100"},
            dry_run=False,
        )

        # Create rollback
        rollback_id = await storage_instance.create_remediation_rollback(
            execution_id=execution_id,
            reason="False positive detected",
            initiated_by="test-user",
        )
        assert rollback_id is not None


class TestNotificationOperations:
    """Test notification operations with real file I/O."""

    @pytest.mark.asyncio
    async def test_create_and_update_notification(
        self, storage_instance: Storage
    ) -> None:
        """Test creating and updating notifications."""
        # Create notification
        notification_id = await storage_instance.create_notification(
            incident_id="test-incident-123",
            notification_type="email",
            subject="Security Alert",
            message="Test notification message",
            channels=["admin@example.com"],
            priority="high",
            metadata={"recipient": "admin@example.com"},
            created_by="system",
        )
        assert notification_id is not None

        # Update notification status
        success = await storage_instance.update_notification(
            notification_id,
            status="sent",
            sent_at=datetime.now(timezone.utc).isoformat(),
        )
        assert success is True

        # Verify update
        updated = await storage_instance.get_notification(notification_id)
        assert updated is not None
        assert updated["status"] == "sent"
        assert "sent_at" in updated

    @pytest.mark.asyncio
    async def test_notification_preferences(self, storage_instance: Storage) -> None:
        """Test notification preferences."""
        user_id = "test-user"
        preferences = {
            "email_enabled": True,
            "sms_enabled": False,
            "slack_enabled": True,
            "email_address": "user@example.com",
            "slack_channel": "#security-alerts",
        }

        # Set preferences
        success = await storage_instance.update_notification_preferences(
            user_id, preferences
        )
        assert success is True

        # Get preferences
        retrieved = await storage_instance.get_notification_preferences(user_id)
        assert retrieved is not None
        assert retrieved["email_enabled"] is True
        assert retrieved["sms_enabled"] is False


class TestConcurrentOperations:
    """Test concurrent operations on storage."""

    @pytest.mark.asyncio
    async def test_concurrent_incident_creation(
        self, storage_instance: Storage
    ) -> None:
        """Test concurrent incident creation."""

        async def create_incident(i: int) -> str:
            incident = Incident(
                title=f"Concurrent Incident {i}",
                description=f"Test incident {i}",
                severity=SeverityLevel.MEDIUM,
                status=IncidentStatus.DETECTED,
                created_at=datetime.now(timezone.utc),
                metadata={"test": f"value{i}"},
            )
            return await storage_instance.create_incident(incident)

        # Create 10 incidents concurrently
        tasks = [create_incident(i) for i in range(10)]
        incident_ids = await asyncio.gather(*tasks)

        # Verify all incidents were created
        assert len(incident_ids) == 10
        assert len(set(incident_ids)) == 10  # All IDs should be unique

        # Verify all files exist
        for incident_id in incident_ids:
            file_path = storage_instance.incidents_path / f"{incident_id}.json"
            assert file_path.exists()

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self, storage_instance: Storage) -> None:
        """Test concurrent read and write operations."""
        # Create initial incident
        incident = Incident(
            title="Concurrent Test Incident",
            description="Test incident for concurrent operations",
            severity=SeverityLevel.HIGH,
            status=IncidentStatus.DETECTED,
            created_at=datetime.now(timezone.utc),
            metadata={"test": "initial"},
        )
        incident_id = await storage_instance.create_incident(incident)

        async def read_incident() -> Optional[Incident]:
            return await storage_instance.get_incident(incident_id)

        async def update_incident(status: IncidentStatus) -> bool:
            incident_copy = await storage_instance.get_incident(incident_id)
            if incident_copy:
                incident_copy.status = status
                return await storage_instance.update_incident(
                    incident_id, incident_copy
                )
            return False

        # Perform concurrent reads and writes
        tasks = [
            read_incident(),
            update_incident(IncidentStatus.ANALYZING),
            read_incident(),
            update_incident(IncidentStatus.RESOLVED),
            read_incident(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception)

        # Verify final state
        final_incident = await storage_instance.get_incident(incident_id)
        assert final_incident is not None
        assert final_incident.status in [
            IncidentStatus.ANALYZING,
            IncidentStatus.RESOLVED,
        ]


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_corrupted_file_handling(self, storage_instance: Storage) -> None:
        """Test handling of corrupted JSON files."""
        # Create a corrupted file
        corrupted_file = storage_instance.incidents_path / "corrupted.json"
        with open(corrupted_file, "w", encoding="utf-8") as f:
            f.write("invalid json content {")

        # Attempt to read corrupted file
        result = await storage_instance.get_incident("corrupted")
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_directory_recovery(self, storage_instance: Storage) -> None:
        """Test recovery when storage directories are missing."""
        # Remove incidents directory
        import shutil

        shutil.rmtree(storage_instance.incidents_path)

        # Create incident should recreate directory
        incident = Incident(
            title="Recovery Test",
            description="Test incident for directory recovery",
            severity=SeverityLevel.LOW,
            status=IncidentStatus.DETECTED,
            created_at=datetime.now(timezone.utc),
            metadata={"test": "recovery"},
        )

        incident_id = await storage_instance.create_incident(incident)
        assert incident_id is not None

        # Verify directory was recreated
        assert storage_instance.incidents_path.exists()

        # Verify incident was stored
        retrieved = await storage_instance.get_incident(incident_id)
        assert retrieved is not None
        assert retrieved.title == "Recovery Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

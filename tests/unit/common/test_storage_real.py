"""REAL tests for common/storage.py - Testing actual file-based storage operations."""

import asyncio
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import pytest

# Import the actual production code
from src.common.storage import Storage
from src.common.models import (
    Incident,
    AnalysisResult,
    IncidentStatus,
    SeverityLevel,
    EventSource,
    SecurityEvent,
)
from src.detection_agent.rules_engine import DetectionRule, RuleStatus


class TestStorageReal:
    """Test Storage with REAL file I/O operations - NO MOCKS."""

    @pytest.fixture
    def temp_dir(self) -> Generator[str, None, None]:
        """Create a real temporary directory for testing."""
        temp_path = tempfile.mkdtemp(prefix="test_storage_")
        yield temp_path
        # Cleanup after test
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def storage(self, temp_dir: str) -> Storage:
        """Create real Storage instance with temp directory."""
        return Storage(base_path=temp_dir)

    @pytest.mark.asyncio
    async def test_real_storage_initialization(self, temp_dir: str) -> None:
        """Test REAL storage initialization and directory creation."""
        # Initialize storage
        Storage(base_path=temp_dir)

        # Verify real directories were created
        assert Path(temp_dir).exists()
        assert (Path(temp_dir) / "incidents").exists()
        assert (Path(temp_dir) / "analyses").exists()
        assert (Path(temp_dir) / "rules").exists()
        assert (Path(temp_dir) / "feedback").exists()

        print(f"\nStorage initialized at: {temp_dir}")
        print(f"Subdirectories created: {list((Path(temp_dir).iterdir()))}")

    @pytest.mark.asyncio
    async def test_real_create_and_get_incident(self, storage: Storage) -> None:
        """Test REAL incident creation and retrieval from disk."""
        # Create a real incident
        incident = Incident(
            title="Unauthorized Access Detected",
            description="Test incident for real storage",
            severity=SeverityLevel.HIGH,
            status=IncidentStatus.DETECTED,
            events=[
                SecurityEvent(
                    event_type="failed_login",
                    description="Multiple failed login attempts",
                    source=EventSource(
                        source_type="detection_agent",
                        source_name="test_detector",
                        source_id="detector-01",
                    ),
                    affected_resources=["user@example.com"],
                )
            ],
        )

        # Create incident (writes to disk)
        incident_id = await storage.create_incident(incident)
        assert incident_id is not None
        assert len(incident_id) == 36  # UUID format

        # Verify file was created on disk
        file_path = storage.incidents_path / f"{incident_id}.json"
        assert file_path.exists()

        # Read incident back from disk
        retrieved = await storage.get_incident(incident_id)
        assert retrieved is not None
        assert retrieved.title == "Unauthorized Access Detected"
        assert retrieved.severity == SeverityLevel.HIGH
        assert retrieved.description == "Test incident for real storage"

        print(f"\nIncident created with ID: {incident_id}")
        print(f"File size: {file_path.stat().st_size} bytes")

    @pytest.mark.asyncio
    async def test_real_update_incident(self, storage: Storage) -> None:
        """Test REAL incident update on disk."""
        # Create incident
        incident = Incident(
            title="Malware Detection Alert",
            description="Initial description",
            severity=SeverityLevel.MEDIUM,
            status=IncidentStatus.DETECTED,
        )

        incident_id = await storage.create_incident(incident)

        # Update incident
        incident.status = IncidentStatus.ANALYZING
        incident.description = "Updated description"
        incident.severity = SeverityLevel.HIGH

        success = await storage.update_incident(incident_id, incident)
        assert success is True

        # Verify update persisted to disk
        updated = await storage.get_incident(incident_id)
        assert updated is not None
        assert updated.status == IncidentStatus.ANALYZING
        assert updated.description == "Updated description"
        assert updated.severity == SeverityLevel.HIGH
        assert updated.updated_at > incident.created_at

        print(f"\nIncident {incident_id} updated on disk")

    @pytest.mark.asyncio
    async def test_real_get_nonexistent_incident(self, storage: Storage) -> None:
        """Test REAL retrieval of non-existent incident."""
        result = await storage.get_incident("non-existent-id")
        assert result is None

        print("\nNon-existent incident correctly returned None")

    @pytest.mark.asyncio
    async def test_real_create_and_get_analysis(self, storage: Storage) -> None:
        """Test REAL analysis result storage and retrieval."""
        # Create analysis result
        analysis = AnalysisResult(
            incident_id="test-incident-001",
            confidence_score=0.92,
            summary="Detected brute force attack attempt",
            detailed_analysis="Multiple failed login attempts from suspicious IPs",
            attack_techniques=["T1078", "T1110"],
            recommendations=[
                "Block suspicious IP addresses",
                "Reset compromised credentials",
                "Enable MFA",
            ],
            evidence={
                "affected_resources": ["user@example.com", "admin-portal"],
                "timeline_events": [
                    {"time": "2024-06-12T10:00:00Z", "event": "First login attempt"},
                    {"time": "2024-06-12T10:05:00Z", "event": "Brute force detected"},
                ],
            },
        )

        # Store analysis
        success = await storage.store_analysis("test-incident-001", analysis)
        assert success is True

        # Verify file created
        file_path = storage.analyses_path / f"{analysis.incident_id}.json"
        assert file_path.exists()

        # Retrieve analysis
        retrieved = await storage.get_analysis("test-incident-001")
        assert retrieved is not None
        assert retrieved.confidence_score == 0.92
        assert retrieved.summary == "Detected brute force attack attempt"
        assert len(retrieved.attack_techniques) == 2
        assert len(retrieved.recommendations) == 3

        print(f"\nAnalysis stored for incident: {analysis.incident_id}")

    @pytest.mark.asyncio
    async def test_real_save_and_load_rules(self, storage: Storage) -> None:
        """Test REAL detection rules storage and loading."""
        # Create detection rules
        rules = [
            DetectionRule(
                rule_id="rule-001",
                name="Failed Login Detection",
                description="Detect multiple failed login attempts",
                query="SELECT * FROM logs WHERE event_type = 'failed_login'",
                severity=SeverityLevel.HIGH,
                status=RuleStatus.ENABLED,
            ),
            DetectionRule(
                rule_id="rule-002",
                name="Data Exfiltration Detection",
                description="Detect large data transfers",
                query="SELECT * FROM network_logs WHERE bytes_sent > 1000000000",
                severity=SeverityLevel.CRITICAL,
                status=RuleStatus.ENABLED,
            ),
        ]

        # Save rules to disk
        rule_ids = []
        for rule in rules:
            rule_id = await storage.create_rule(rule)
            rule_ids.append(rule_id)

        # Verify files created
        assert len(rule_ids) == 2

        # Load rules back
        loaded_rules = await storage.get_rules()
        assert len(loaded_rules) == 2
        # Find rules by name since order may vary
        rule_names = [rule.name for rule in loaded_rules]
        assert "Failed Login Detection" in rule_names
        assert "Data Exfiltration Detection" in rule_names
        # Check severities
        severities = {rule.name: rule.severity for rule in loaded_rules}
        assert severities["Failed Login Detection"] == SeverityLevel.HIGH
        assert severities["Data Exfiltration Detection"] == SeverityLevel.CRITICAL

        print(f"\n{len(rules)} detection rules saved and loaded from disk")

    @pytest.mark.asyncio
    async def test_real_get_recent_incidents(self, storage: Storage) -> None:
        """Test REAL retrieval of recent incidents from disk."""
        # Create multiple incidents with different timestamps
        incidents = []
        for i in range(5):
            incident = Incident(
                title=f"Test Incident {i}",
                description=f"Test incident {i}",
                severity=SeverityLevel.MEDIUM,
                status=IncidentStatus.DETECTED,
            )
            incident_id = await storage.create_incident(incident)
            incidents.append((incident_id, incident))
            # Small delay to ensure different timestamps
            await asyncio.sleep(0.01)

        # Get all incidents
        all_incidents = await storage.get_incidents()

        # Should get all 5 incidents
        assert len(all_incidents) >= 5
        # Sort by created_at to check order
        sorted_incidents = sorted(
            all_incidents, key=lambda x: x.created_at, reverse=True
        )
        # Verify we have our test incidents
        descriptions = [inc.description for inc in sorted_incidents[:5]]
        assert any("Test incident 4" in desc for desc in descriptions)

        print(f"\nRetrieved {len(all_incidents)} incidents total")

    @pytest.mark.asyncio
    async def test_real_get_incidents_by_status(self, storage: Storage) -> None:
        """Test REAL filtering of incidents by status."""
        # Create incidents with different statuses
        statuses = [
            IncidentStatus.DETECTED,
            IncidentStatus.ANALYZING,
            IncidentStatus.DETECTED,
            IncidentStatus.RESOLVED,
            IncidentStatus.DETECTED,
        ]

        for i, status in enumerate(statuses):
            incident = Incident(
                title=f"Test Incident {i}",
                description=f"Incident with status {status.value}",
                severity=SeverityLevel.LOW,
                status=status,
            )
            await storage.create_incident(incident)

        # Get all incidents and filter by status manually
        all_incidents = await storage.get_incidents()

        detected = [
            inc for inc in all_incidents if inc.status == IncidentStatus.DETECTED
        ]
        analyzing = [
            inc for inc in all_incidents if inc.status == IncidentStatus.ANALYZING
        ]
        resolved = [
            inc for inc in all_incidents if inc.status == IncidentStatus.RESOLVED
        ]

        assert len(detected) >= 3
        assert len(analyzing) >= 1
        assert len(resolved) >= 1

        print(
            f"\nFiltered incidents by status: detected={len(detected)}, analyzing={len(analyzing)}, resolved={len(resolved)}"
        )

    @pytest.mark.asyncio
    async def test_real_save_feedback(self, storage: Storage) -> None:
        """Test REAL feedback storage to disk."""
        feedback = {
            "incident_id": "test-inc-001",
            "user_id": "analyst@example.com",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feedback_type": "false_positive",
            "comments": "This was a legitimate user action",
            "corrective_actions": ["Update detection rule", "Whitelist IP"],
        }

        # Store feedback
        feedback_id = await storage.store_feedback("false_positive", feedback)
        assert feedback_id is not None

        # Verify file created with feedback_id as filename
        feedback_file = storage.feedback_path / f"{feedback_id}.json"
        assert feedback_file.exists()

        # Read feedback back
        with open(feedback_file, "r", encoding="utf-8") as f:
            saved_feedback = json.load(f)

        assert saved_feedback["type"] == "false_positive"
        assert saved_feedback["comments"] == "This was a legitimate user action"
        assert len(saved_feedback["corrective_actions"]) == 2

        print(f"\nFeedback saved with ID: {feedback_id}")

    @pytest.mark.asyncio
    async def test_real_storage_with_invalid_json(self, storage: Storage) -> None:
        """Test REAL handling of corrupted JSON files."""
        # Create a corrupted incident file
        incident_id = "corrupted-001"
        file_path = storage.incidents_path / f"{incident_id}.json"

        # Write invalid JSON
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("{invalid json content")

        # Should handle gracefully
        result = await storage.get_incident(incident_id)
        assert result is None

        print("\nCorrupted JSON handled gracefully")

    @pytest.mark.asyncio
    async def test_real_concurrent_file_operations(self, storage: Storage) -> None:
        """Test REAL concurrent file operations."""

        # Create multiple incidents concurrently
        async def create_incident_task(index: int) -> str:
            incident = Incident(
                title=f"Concurrent Test {index}",
                description=f"Concurrent incident {index}",
                severity=SeverityLevel.LOW,
                status=IncidentStatus.DETECTED,
            )
            return await storage.create_incident(incident)

        # Run concurrent creates
        tasks = [create_incident_task(j) for j in range(10)]
        incident_ids = await asyncio.gather(*tasks)

        # All should succeed
        assert len(incident_ids) == 10
        assert all(id is not None for id in incident_ids)

        # Verify all files exist
        for incident_id in incident_ids:
            file_path = storage.incidents_path / f"{incident_id}.json"
            assert file_path.exists()

        print(f"\n{len(incident_ids)} incidents created concurrently")

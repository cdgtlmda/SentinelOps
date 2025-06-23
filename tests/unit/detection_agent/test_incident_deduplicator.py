"""
Comprehensive tests for the Detection Agent Incident Deduplicator.

This test suite provides 100% production code testing with NO MOCKING.
Tests cover all incident deduplication functionality including similarity detection,
merging, hashing, and cache management for real security operations.

Coverage target: ≥90% statement coverage of src/detection_agent/incident_deduplicator.py
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.detection_agent.incident_deduplicator import IncidentDeduplicator
from src.common.models import (
    Incident,
    SecurityEvent,
    EventSource,
    SeverityLevel,
    IncidentStatus,
)


class TestIncidentDeduplicator:
    """Test the IncidentDeduplicator class with comprehensive coverage."""

    @pytest.fixture
    def deduplicator(self) -> IncidentDeduplicator:
        """Create a deduplicator with default settings."""
        return IncidentDeduplicator()

    @pytest.fixture
    def custom_deduplicator(self) -> IncidentDeduplicator:
        """Create a deduplicator with custom settings."""
        return IncidentDeduplicator(similarity_threshold=0.9, time_window_hours=12)

    @pytest.fixture
    def sample_event_source(self) -> EventSource:
        """Create a sample event source."""
        return EventSource(
            source_type="gcp",
            source_name="cloud-logging",
            source_id="projects/test-project/logs/security",
            resource_type="gce_instance",
            resource_name="web-server-1",
            resource_id="12345678901",
        )

    @pytest.fixture
    def sample_security_event(self, sample_event_source: EventSource) -> SecurityEvent:
        """Create a sample security event."""
        return SecurityEvent(
            event_id="event-123",
            timestamp=datetime.now(timezone.utc),
            event_type="unauthorized_access",
            source=sample_event_source,
            severity=SeverityLevel.HIGH,
            description="Suspicious login attempt from unknown IP",
            actor="user@example.com",
            affected_resources=["web-server-1", "database-server"],
            indicators={"ip_address": "192.168.1.100", "user_agent": "suspicious-bot"},
        )

    @pytest.fixture
    def sample_incident(self, sample_security_event: SecurityEvent) -> Incident:
        """Create a sample incident."""
        return Incident(
            incident_id="incident-123",
            created_at=datetime.now(timezone.utc),
            title="Security Breach Detected",
            description="Unauthorized access attempt detected",
            severity=SeverityLevel.HIGH,
            status=IncidentStatus.DETECTED,
            events=[sample_security_event],
            tags=["security", "unauthorized_access"],
            metadata={"detection_rule": "rule-001", "event_count": 1},
        )

    def test_init_default_parameters(self) -> None:
        """Test initialization with default parameters."""
        deduplicator = IncidentDeduplicator()

        assert deduplicator.similarity_threshold == 0.8
        assert deduplicator.time_window == timedelta(hours=24)
        assert not deduplicator._recent_incidents
        assert not deduplicator._incident_hashes

    def test_init_custom_parameters(self) -> None:
        """Test initialization with custom parameters."""
        deduplicator = IncidentDeduplicator(
            similarity_threshold=0.9, time_window_hours=12
        )

        assert deduplicator.similarity_threshold == 0.9
        assert deduplicator.time_window == timedelta(hours=12)
        assert not deduplicator._recent_incidents
        assert not deduplicator._incident_hashes

    def test_is_duplicate_exact_hash_match(
        self, deduplicator: IncidentDeduplicator, sample_incident: Incident
    ) -> None:
        """Test duplicate detection with exact hash match."""
        # Create identical incident
        duplicate_incident = Incident(
            incident_id="incident-456",
            created_at=datetime.now(timezone.utc),
            title="Different Title",  # Title doesn't affect hash
            description="Different description",  # Description doesn't affect hash
            severity=SeverityLevel.HIGH,
            events=sample_incident.events,  # Same events = same hash
            tags=["security", "unauthorized_access"],
            metadata={"detection_rule": "rule-001"},
        )

        # Should find duplicate
        result = deduplicator.is_duplicate(duplicate_incident, [sample_incident])
        assert result == sample_incident

    def test_is_duplicate_no_exact_match_high_similarity(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test duplicate detection with high similarity but no exact hash match."""
        # Create base event
        event1 = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor="user@example.com",
            affected_resources=["server-1"],
            severity=SeverityLevel.HIGH,
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        # Create similar event with different ID
        event2 = SecurityEvent(
            event_id="event-2",  # Different event ID
            event_type="login_attempt",  # Same type
            actor="user@example.com",  # Same actor
            affected_resources=["server-1"],  # Same resources
            severity=SeverityLevel.HIGH,  # Same severity
            source=EventSource("gcp", "cloud-logging", "log-2"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            created_at=datetime.now(timezone.utc),
            title="First Incident",
            description="Login attempt detected",
            events=[event1],
            tags=["security", "login"],
        )

        incident2 = Incident(
            incident_id="incident-2",
            created_at=datetime.now(timezone.utc),
            title="Second Incident",
            description="Another login attempt",
            events=[event2],
            tags=["security", "login"],
        )

        # Should find duplicate due to high similarity
        result = deduplicator.is_duplicate(incident2, [incident1])
        assert result == incident1

    def test_is_duplicate_low_similarity(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test that incidents with low similarity are not considered duplicates."""
        event1 = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor="user1@example.com",
            affected_resources=["server-1"],
            severity=SeverityLevel.HIGH,
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        event2 = SecurityEvent(
            event_id="event-2",
            event_type="file_access",  # Different type
            actor="user2@example.com",  # Different actor
            affected_resources=["server-2"],  # Different resources
            severity=SeverityLevel.LOW,  # Different severity
            source=EventSource("aws", "cloudtrail", "log-2"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            created_at=datetime.now(timezone.utc),
            title="Login Incident",
            description="Login attempt detected",
            events=[event1],
            tags=["security", "login"],
        )

        incident2 = Incident(
            incident_id="incident-2",
            created_at=datetime.now(timezone.utc),
            title="File Access Incident",
            description="File access detected",
            events=[event2],
            tags=["data", "file_access"],
        )

        # Should not find duplicate due to low similarity
        result = deduplicator.is_duplicate(incident2, [incident1])
        assert result is None

    def test_is_duplicate_outside_time_window(
        self, deduplicator: IncidentDeduplicator, sample_incident: Incident
    ) -> None:
        """Test that incidents outside time window are not considered duplicates."""
        # Create old incident (outside 24-hour window)
        old_incident = Incident(
            incident_id="old-incident",
            created_at=datetime.now(timezone.utc) - timedelta(hours=25),
            title="Old Incident",
            description="Old incident",
            events=sample_incident.events,  # Same events
            tags=sample_incident.tags,
            metadata=sample_incident.metadata,
        )

        # Should not find duplicate due to time window
        result = deduplicator.is_duplicate(sample_incident, [old_incident])
        assert result is None

    def test_is_duplicate_within_time_window(
        self, custom_deduplicator: IncidentDeduplicator, sample_incident: Incident
    ) -> None:
        """Test that incidents within custom time window are considered."""
        # Create incident within 12-hour window
        recent_incident = Incident(
            incident_id="recent-incident",
            created_at=datetime.now(timezone.utc) - timedelta(hours=11),
            title="Recent Incident",
            description="Recent incident",
            events=sample_incident.events,  # Same events
            tags=sample_incident.tags,
            metadata=sample_incident.metadata,
        )

        # Should find duplicate within custom time window
        result = custom_deduplicator.is_duplicate(sample_incident, [recent_incident])
        assert result == recent_incident

    def test_merge_incidents_basic(self, deduplicator: IncidentDeduplicator) -> None:
        """Test basic incident merging functionality."""
        event1 = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor="user@example.com",
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        event2 = SecurityEvent(
            event_id="event-2",
            event_type="file_access",
            actor="user@example.com",
            source=EventSource("gcp", "cloud-logging", "log-2"),
        )

        primary = Incident(
            incident_id="primary-123",
            title="Primary Incident",
            description="Primary incident description",
            severity=SeverityLevel.MEDIUM,
            events=[event1],
            tags=["security"],
            metadata={"event_count": 1},
        )

        duplicate = Incident(
            incident_id="duplicate-456",
            title="Duplicate Incident",
            description="Duplicate incident description",
            severity=SeverityLevel.HIGH,
            events=[event2],
            tags=["data_access"],
            metadata={"event_count": 1},
        )

        merged = deduplicator.merge_incidents(primary, duplicate)

        # Check merged events
        assert len(merged.events) == 2
        assert event1 in merged.events
        assert event2 in merged.events

        # Check merged tags
        assert "security" in merged.tags
        assert "data_access" in merged.tags

        # Check severity updated to highest
        assert merged.severity == SeverityLevel.HIGH

        # Check description updated
        assert "Primary incident description" in merged.description
        assert "Merged with incident duplicate-456" in merged.description

        # Check metadata
        assert "merged_incidents" in merged.metadata
        assert merged.metadata["event_count"] == 2
        assert "first_event_time" in merged.metadata
        assert "last_event_time" in merged.metadata

    def test_merge_incidents_duplicate_events(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test merging incidents with duplicate events."""
        shared_event = SecurityEvent(
            event_id="shared-event",
            event_type="login_attempt",
            actor="user@example.com",
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        unique_event = SecurityEvent(
            event_id="unique-event",
            event_type="file_access",
            actor="user@example.com",
            source=EventSource("gcp", "cloud-logging", "log-2"),
        )

        primary = Incident(
            incident_id="primary-123",
            title="Primary Incident",
            description="Primary incident",
            events=[shared_event],
            tags=["primary"],
            metadata={},
        )

        duplicate = Incident(
            incident_id="duplicate-456",
            title="Duplicate Incident",
            description="Duplicate incident",
            events=[shared_event, unique_event],  # Contains shared event
            tags=["duplicate"],
            metadata={},
        )

        merged = deduplicator.merge_incidents(primary, duplicate)

        # Should only have unique events
        assert len(merged.events) == 2
        event_ids = {e.event_id for e in merged.events}
        assert "shared-event" in event_ids
        assert "unique-event" in event_ids

    def test_calculate_incident_hash_consistent(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test that hash calculation is consistent for identical incidents."""
        event = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor="user@example.com",
            affected_resources=["server-1", "server-2"],
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            title="First Incident",
            description="Different description",  # Should not affect hash
            events=[event],
            metadata={"detection_rule": "rule-001"},
        )

        incident2 = Incident(
            incident_id="incident-2",
            title="Second Incident",
            description="Another different description",  # Should not affect hash
            events=[event],
            metadata={"detection_rule": "rule-001"},
        )

        hash1 = deduplicator._calculate_incident_hash(incident1)
        hash2 = deduplicator._calculate_incident_hash(incident2)

        assert hash1 == hash2
        assert hash1 in deduplicator._incident_hashes.values()

    def test_calculate_incident_hash_different(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test that hash calculation produces different hashes for different incidents."""
        event1 = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor="user1@example.com",
            affected_resources=["server-1"],
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        event2 = SecurityEvent(
            event_id="event-2",
            event_type="file_access",  # Different type
            actor="user2@example.com",  # Different actor
            affected_resources=["server-2"],  # Different resources
            source=EventSource("gcp", "cloud-logging", "log-2"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            events=[event1],
            metadata={"detection_rule": "rule-001"},
        )

        incident2 = Incident(
            incident_id="incident-2",
            events=[event2],
            metadata={"detection_rule": "rule-002"},  # Different rule
        )

        hash1 = deduplicator._calculate_incident_hash(incident1)
        hash2 = deduplicator._calculate_incident_hash(incident2)

        assert hash1 != hash2

    def test_calculate_similarity_identical_incidents(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test similarity calculation for identical incidents."""
        event = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor="user@example.com",
            affected_resources=["server-1"],
            severity=SeverityLevel.HIGH,
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            created_at=datetime.now(timezone.utc),
            events=[event],
            tags=["security", "login"],
        )

        incident2 = Incident(
            incident_id="incident-2",
            created_at=datetime.now(timezone.utc),
            events=[event],
            tags=["security", "login"],
        )

        similarity = deduplicator._calculate_similarity(incident1, incident2)
        assert similarity >= 0.9  # Should be very high

    def test_calculate_similarity_different_incidents(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test similarity calculation for completely different incidents."""
        event1 = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor="user1@example.com",
            affected_resources=["server-1"],
            severity=SeverityLevel.HIGH,
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        event2 = SecurityEvent(
            event_id="event-2",
            event_type="file_access",
            actor="user2@example.com",
            affected_resources=["server-2"],
            severity=SeverityLevel.LOW,
            source=EventSource("aws", "cloudtrail", "log-2"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            created_at=datetime.now(timezone.utc),
            events=[event1],
            tags=["security", "login"],
        )

        incident2 = Incident(
            incident_id="incident-2",
            created_at=datetime.now(timezone.utc)
            - timedelta(hours=12),  # Different time
            events=[event2],
            tags=["data", "file_access"],
        )

        similarity = deduplicator._calculate_similarity(incident1, incident2)
        assert similarity < 0.5  # Should be low

    def test_calculate_similarity_time_proximity(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test time proximity component of similarity calculation."""
        event = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        now = datetime.now(timezone.utc)

        incident1 = Incident(incident_id="incident-1", created_at=now, events=[event])

        # Test different time gaps
        incident_1_hour = Incident(
            incident_id="incident-2",
            created_at=now - timedelta(hours=1),
            events=[event],
        )

        incident_12_hours = Incident(
            incident_id="incident-3",
            created_at=now - timedelta(hours=12),
            events=[event],
        )

        incident_24_hours = Incident(
            incident_id="incident-4",
            created_at=now - timedelta(hours=24),
            events=[event],
        )

        # Closer in time should have higher similarity
        sim_1_hour = deduplicator._calculate_similarity(incident1, incident_1_hour)
        sim_12_hours = deduplicator._calculate_similarity(incident1, incident_12_hours)
        sim_24_hours = deduplicator._calculate_similarity(incident1, incident_24_hours)

        assert sim_1_hour > sim_12_hours > sim_24_hours

    def test_calculate_similarity_empty_sets(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test similarity calculation with empty sets."""
        event1 = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor=None,  # No actor
            affected_resources=[],  # No resources
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        event2 = SecurityEvent(
            event_id="event-2",
            event_type="file_access",
            actor=None,  # No actor
            affected_resources=[],  # No resources
            source=EventSource("gcp", "cloud-logging", "log-2"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            created_at=datetime.now(timezone.utc),
            events=[event1],
            tags=[],  # No tags
        )

        incident2 = Incident(
            incident_id="incident-2",
            created_at=datetime.now(timezone.utc),
            events=[event2],
            tags=[],  # No tags
        )

        # Should handle empty sets gracefully
        similarity = deduplicator._calculate_similarity(incident1, incident2)
        assert 0.0 <= similarity <= 1.0

    def test_update_existing_incident_new_events(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test updating existing incident with new events."""
        existing_event = SecurityEvent(
            event_id="existing-event",
            event_type="login_attempt",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        new_event1 = SecurityEvent(
            event_id="new-event-1",
            event_type="file_access",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=15),
            source=EventSource("gcp", "cloud-logging", "log-2"),
        )

        new_event2 = SecurityEvent(
            event_id="new-event-2",
            event_type="network_connection",
            timestamp=datetime.now(timezone.utc),
            source=EventSource("gcp", "cloud-logging", "log-3"),
        )

        existing_incident = Incident(
            incident_id="incident-123",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            title="Existing Incident",
            description="Original description",
            events=[existing_event],
            metadata={"event_count": 1, "updates": 0},
        )

        updated_incident = deduplicator.update_existing_incident(
            existing_incident, [new_event1, new_event2]
        )

        # Check events were added
        assert len(updated_incident.events) == 3
        event_ids = {e.event_id for e in updated_incident.events}
        assert "existing-event" in event_ids
        assert "new-event-1" in event_ids
        assert "new-event-2" in event_ids

        # Check metadata updates
        assert updated_incident.metadata["event_count"] == 3
        assert updated_incident.metadata["updates"] == 1
        assert "last_updated" in updated_incident.metadata
        assert "first_event_time" in updated_incident.metadata
        assert "last_event_time" in updated_incident.metadata

        # Check description update
        assert "Updated with 2 new events" in updated_incident.description

    def test_update_existing_incident_duplicate_events(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test updating incident with duplicate events."""
        existing_event = SecurityEvent(
            event_id="existing-event",
            event_type="login_attempt",
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        duplicate_event = SecurityEvent(
            event_id="existing-event",  # Same ID as existing
            event_type="login_attempt",
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        existing_incident = Incident(
            incident_id="incident-123",
            title="Existing Incident",
            description="Original description",
            events=[existing_event],
            metadata={"event_count": 1, "updates": 0},
        )

        updated_incident = deduplicator.update_existing_incident(
            existing_incident, [duplicate_event]
        )

        # Should not add duplicate event
        assert len(updated_incident.events) == 1
        assert updated_incident.metadata["event_count"] == 1
        assert updated_incident.metadata["updates"] == 0  # No update should occur
        assert "Updated with" not in updated_incident.description

    def test_update_existing_incident_no_new_events(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test updating incident with empty event list."""
        existing_event = SecurityEvent(
            event_id="existing-event",
            event_type="login_attempt",
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        existing_incident = Incident(
            incident_id="incident-123",
            title="Existing Incident",
            description="Original description",
            events=[existing_event],
            metadata={"event_count": 1, "updates": 0},
        )

        original_description = existing_incident.description

        updated_incident = deduplicator.update_existing_incident(existing_incident, [])

        # Should remain unchanged
        assert len(updated_incident.events) == 1
        assert updated_incident.metadata["event_count"] == 1
        assert updated_incident.metadata["updates"] == 0
        assert updated_incident.description == original_description

    def test_cleanup_old_incidents(self, deduplicator: IncidentDeduplicator) -> None:
        """Test cleanup of old incidents from cache."""
        now = datetime.now(timezone.utc)

        # Add incidents to cache manually
        old_incident1 = Incident(
            incident_id="old-1",
            created_at=now - timedelta(hours=25),
            title="Old Incident 1",
        )

        old_incident2 = Incident(
            incident_id="old-2",
            created_at=now - timedelta(hours=30),
            title="Old Incident 2",
        )

        recent_incident = Incident(
            incident_id="recent-1",
            created_at=now - timedelta(hours=5),
            title="Recent Incident",
        )

        # Manually add to cache
        deduplicator._recent_incidents["old-1"] = old_incident1
        deduplicator._recent_incidents["old-2"] = old_incident2
        deduplicator._recent_incidents["recent-1"] = recent_incident
        deduplicator._incident_hashes["old-1"] = "hash1"
        deduplicator._incident_hashes["old-2"] = "hash2"
        deduplicator._incident_hashes["recent-1"] = "hash3"

        removed_count = deduplicator.cleanup_old_incidents()

        # Should remove 2 old incidents
        assert removed_count == 2
        assert "old-1" not in deduplicator._recent_incidents
        assert "old-2" not in deduplicator._recent_incidents
        assert "recent-1" in deduplicator._recent_incidents
        assert "old-1" not in deduplicator._incident_hashes
        assert "old-2" not in deduplicator._incident_hashes
        assert "recent-1" in deduplicator._incident_hashes

    def test_cleanup_old_incidents_empty_cache(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test cleanup with empty cache."""
        removed_count = deduplicator.cleanup_old_incidents()
        assert removed_count == 0

    def test_clear_cache(self, deduplicator: IncidentDeduplicator) -> None:
        """Test cache clearing functionality."""
        # Add some data to cache
        incident = Incident(incident_id="test-incident", title="Test Incident")

        deduplicator._recent_incidents["test-incident"] = incident
        deduplicator._incident_hashes["test-incident"] = "test-hash"

        # Verify cache has data
        assert len(deduplicator._recent_incidents) == 1
        assert len(deduplicator._incident_hashes) == 1

        # Clear cache
        deduplicator.clear_cache()

        # Verify cache is empty
        assert len(deduplicator._recent_incidents) == 0
        assert len(deduplicator._incident_hashes) == 0

    def test_hash_caching_behavior(self, deduplicator: IncidentDeduplicator) -> None:
        """Test that hashes are properly cached."""
        event = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        incident = Incident(incident_id="incident-123", events=[event])

        # Calculate hash first time
        hash1 = deduplicator._calculate_incident_hash(incident)

        # Verify hash is cached
        assert incident.incident_id in deduplicator._incident_hashes
        assert deduplicator._incident_hashes[incident.incident_id] == hash1

        # Calculate hash again - should use cached value
        hash2 = deduplicator._calculate_incident_hash(incident)
        assert hash1 == hash2

    def test_edge_case_high_similarity_threshold(self) -> None:
        """Test behavior with very high similarity threshold."""
        # Set very high threshold
        deduplicator = IncidentDeduplicator(similarity_threshold=0.99)

        event1 = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            actor="user@example.com",
            affected_resources=["server-1"],
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        # Very similar event but slightly different
        event2 = SecurityEvent(
            event_id="event-2",
            event_type="login_attempt",
            actor="user@example.com",
            affected_resources=["server-1", "server-2"],  # One additional resource
            source=EventSource("gcp", "cloud-logging", "log-2"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            created_at=datetime.now(timezone.utc),
            events=[event1],
            tags=["security"],
        )

        incident2 = Incident(
            incident_id="incident-2",
            created_at=datetime.now(timezone.utc),
            events=[event2],
            tags=["security"],
        )

        # Should not consider as duplicate due to high threshold
        result = deduplicator.is_duplicate(incident2, [incident1])
        assert result is None

    def test_edge_case_zero_similarity_threshold(self) -> None:
        """Test behavior with zero similarity threshold."""
        # Set zero threshold (everything is a duplicate)
        deduplicator = IncidentDeduplicator(similarity_threshold=0.0)

        event1 = SecurityEvent(
            event_id="event-1",
            event_type="login_attempt",
            source=EventSource("gcp", "cloud-logging", "log-1"),
        )

        event2 = SecurityEvent(
            event_id="event-2",
            event_type="completely_different",
            source=EventSource("aws", "cloudtrail", "log-2"),
        )

        incident1 = Incident(
            incident_id="incident-1",
            created_at=datetime.now(timezone.utc),
            events=[event1],
            tags=["tag1"],
        )

        incident2 = Incident(
            incident_id="incident-2",
            created_at=datetime.now(timezone.utc),
            events=[event2],
            tags=["tag2"],
        )

        # Should consider as duplicate due to zero threshold
        result = deduplicator.is_duplicate(incident2, [incident1])
        assert result == incident1

    def test_comprehensive_incident_workflow(
        self, deduplicator: IncidentDeduplicator
    ) -> None:
        """Test complete incident deduplication workflow."""
        # Create initial incident
        event1 = SecurityEvent(
            event_id="event-1",
            event_type="suspicious_login",
            actor="malicious@example.com",
            affected_resources=["web-server-1"],
            severity=SeverityLevel.HIGH,
            source=EventSource("gcp", "cloud-logging", "security-logs"),
        )

        incident1 = Incident(
            incident_id="incident-001",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            title="Suspicious Login Activity",
            description="Multiple failed login attempts detected",
            severity=SeverityLevel.HIGH,
            events=[event1],
            tags=["security", "authentication"],
            metadata={"detection_rule": "login-anomaly", "event_count": 1},
        )

        # Create similar incident (should be detected as duplicate)
        event2 = SecurityEvent(
            event_id="event-2",
            event_type="suspicious_login",
            actor="malicious@example.com",  # Same actor
            affected_resources=["web-server-1"],  # Same resource
            severity=SeverityLevel.HIGH,
            source=EventSource("gcp", "cloud-logging", "security-logs"),
        )

        incident2 = Incident(
            incident_id="incident-002",
            created_at=datetime.now(timezone.utc),
            title="Another Suspicious Login",
            description="More failed login attempts",
            severity=SeverityLevel.MEDIUM,  # Lower severity
            events=[event2],
            tags=["security", "authentication", "brute_force"],
            metadata={"detection_rule": "login-anomaly", "event_count": 1},
        )

        # Test duplicate detection
        duplicate_result = deduplicator.is_duplicate(incident2, [incident1])
        assert duplicate_result == incident1

        # Test merging
        merged_incident = deduplicator.merge_incidents(incident1, incident2)

        # Verify merge results
        assert len(merged_incident.events) == 2
        assert merged_incident.severity == SeverityLevel.HIGH  # Kept higher severity
        assert "security" in merged_incident.tags
        assert "authentication" in merged_incident.tags
        assert "brute_force" in merged_incident.tags  # Added from duplicate
        assert "Merged with incident incident-002" in merged_incident.description
        assert merged_incident.metadata["event_count"] == 2
        assert "merged_incidents" in merged_incident.metadata

        # Test adding more events to the merged incident
        event3 = SecurityEvent(
            event_id="event-3",
            event_type="account_lockout",
            actor="malicious@example.com",
            affected_resources=["web-server-1"],
            source=EventSource("gcp", "cloud-logging", "security-logs"),
        )

        updated_incident = deduplicator.update_existing_incident(
            merged_incident, [event3]
        )

        # Verify update results
        assert len(updated_incident.events) == 3
        assert updated_incident.metadata["event_count"] == 3
        assert updated_incident.metadata["updates"] == 1
        assert "Updated with 1 new events" in updated_incident.description

        # Test cache cleanup
        removed_count = deduplicator.cleanup_old_incidents()
        # Should be 0 since all incidents are within time window
        assert removed_count == 0


if __name__ == "__main__":
    pytest.main([__file__])

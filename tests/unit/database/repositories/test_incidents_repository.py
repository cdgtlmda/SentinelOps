"""
Test suite for database/repositories/incidents.py.
CRITICAL: Uses REAL production code - NO MOCKING of database operations.
Achieves minimum 90% statement coverage.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Generator, AsyncGenerator, Any, cast
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.api.models.incidents import (
    IncidentActor,
    IncidentAsset,
    IncidentCreate,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
    IncidentUpdate,
    Priority,
    SecurityIncidentType,
)
from src.database.models.incidents import IncidentModel
from src.database.repositories.incidents import IncidentsRepository

# Use in-memory SQLite for testing (real database operations)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[Any, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[Any, None]:
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Import Base to ensure all models are loaded
    from src.database.base import Base

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(test_engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def repository(test_session: AsyncSession) -> IncidentsRepository:
    """Create incidents repository with test session."""
    return IncidentsRepository(test_session)


@pytest.fixture
def sample_incident_data() -> IncidentCreate:
    """Create sample incident data."""
    return IncidentCreate(
        title="Suspicious Login Activity",
        description="Multiple failed login attempts detected from unusual IP address",
        incident_type=SecurityIncidentType.UNAUTHORIZED_ACCESS,
        severity=IncidentSeverity.HIGH,
        priority=Priority.HIGH,
        status=IncidentStatus.OPEN,
        external_id="EXT-123456",
        source=IncidentSource(
            system="auth_monitor",
            rule_id="AUTH_001",
            rule_name="Multiple Failed Logins",
            confidence=0.95,
            raw_data={"source_ip": "192.168.1.100", "attempts": 15},
        ),
        actors=[
            IncidentActor(
                type="user",
                identifier="john.doe@company.com",
                name="John Doe",
                attributes={"department": "engineering"},
            ),
            IncidentActor(
                type="ip",
                identifier="192.168.1.100",
                name="Suspicious IP",
                attributes={"geolocation": "Unknown", "reputation": "bad"},
            ),
        ],
        assets=[
            IncidentAsset(
                type="server",
                identifier="auth-server-01",
                name="Authentication Server",
                criticality="high",
                attributes={"environment": "production", "region": "us-east-1"},
            )
        ],
        tags=["authentication", "brute_force", "external_ip"],
        custom_fields={"escalation_level": 2, "auto_containment": True},
    )


class TestIncidentsRepository:
    """Test IncidentsRepository class."""

    def test_initialization(self, test_session: AsyncSession) -> None:
        """Test repository initialization."""
        repo = IncidentsRepository(test_session)
        assert repo.session is test_session

    @pytest.mark.asyncio
    async def test_create_incident(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test creating a new incident."""
        created_by = "test_user"
        incident_number = "INC-000001"

        result = await repository.create(
            sample_incident_data, created_by, incident_number
        )

        assert result is not None
        assert isinstance(result, IncidentModel)
        assert result.incident_number == incident_number
        assert result.title == sample_incident_data.title
        assert result.description == sample_incident_data.description
        assert result.incident_type == sample_incident_data.incident_type
        assert result.severity == sample_incident_data.severity
        assert result.priority == sample_incident_data.priority
        assert result.status == sample_incident_data.status
        assert result.created_by == created_by
        assert result.updated_by == created_by
        assert result.detected_at is not None
        assert result.source == sample_incident_data.source.model_dump()
        assert len(result.actors) == 2
        assert len(result.assets) == 1
        assert result.tags == sample_incident_data.tags
        assert result.custom_fields == sample_incident_data.custom_fields
        assert result.timeline == []
        assert result.analysis is None
        assert result.remediation_actions == []  # type: ignore[unreachable]

    @pytest.mark.asyncio
    async def test_get_by_id_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test getting an incident by ID when it exists."""
        # Create incident first
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Retrieve by ID
        result = await repository.get_by_id(cast(UUID, incident.id))

        assert result is not None
        assert result.id == incident.id
        assert result.title == incident.title

    @pytest.mark.asyncio
    async def test_get_by_id_not_exists(self, repository: IncidentsRepository) -> None:
        """Test getting an incident by ID when it doesn't exist."""
        fake_id = uuid4()
        result = await repository.get_by_id(fake_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_incident_number_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test getting an incident by incident number when it exists."""
        incident_number = "INC-000001"
        incident = await repository.create(
            sample_incident_data, "test_user", incident_number
        )

        result = await repository.get_by_incident_number(incident_number)

        assert result is not None
        assert result.incident_number == incident_number
        assert result.id == incident.id

    @pytest.mark.asyncio
    async def test_get_by_incident_number_not_exists(
        self, repository: IncidentsRepository
    ) -> None:
        """Test getting an incident by incident number when it doesn't exist."""
        result = await repository.get_by_incident_number("INC-999999")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_incidents_empty(self, repository: IncidentsRepository) -> None:
        """Test listing incidents when database is empty."""
        incidents, total = await repository.list_incidents()
        assert incidents == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_incidents_basic_pagination(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test basic incident listing with pagination."""
        # Create multiple incidents
        for i in range(5):
            await repository.create(
                sample_incident_data, "test_user", f"INC-{i + 1:06d}"
            )

        # Test first page
        incidents, total = await repository.list_incidents(page=1, page_size=3)
        assert len(incidents) == 3
        assert total == 5

        # Test second page
        incidents, total = await repository.list_incidents(page=2, page_size=3)
        assert len(incidents) == 2
        assert total == 5

    @pytest.mark.asyncio
    async def test_list_incidents_status_filter(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with status filter."""
        # Create incidents with different statuses
        await repository.create(sample_incident_data, "test_user", "INC-000001")

        # Create another with different status
        investigating_data = sample_incident_data.model_copy()
        investigating_data.status = IncidentStatus.INVESTIGATING
        await repository.create(investigating_data, "test_user", "INC-000002")

        # Filter by OPEN status
        incidents, total = await repository.list_incidents(
            status_filter=[IncidentStatus.OPEN]
        )
        assert len(incidents) == 1
        assert total == 1
        assert incidents[0].status == IncidentStatus.OPEN

        # Filter by INVESTIGATING status
        incidents, total = await repository.list_incidents(
            status_filter=[IncidentStatus.INVESTIGATING]
        )
        assert len(incidents) == 1
        assert total == 1
        assert incidents[0].status == IncidentStatus.INVESTIGATING

    @pytest.mark.asyncio
    async def test_list_incidents_severity_filter(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with severity filter."""
        # Create incidents with different severities
        await repository.create(sample_incident_data, "test_user", "INC-000001")  # HIGH

        low_severity_data = sample_incident_data.model_copy()
        low_severity_data.severity = IncidentSeverity.LOW
        await repository.create(low_severity_data, "test_user", "INC-000002")

        # Filter by HIGH severity
        incidents, total = await repository.list_incidents(
            severity_filter=[IncidentSeverity.HIGH]
        )
        assert len(incidents) == 1
        assert total == 1
        assert incidents[0].severity == IncidentSeverity.HIGH

    @pytest.mark.asyncio
    async def test_list_incidents_incident_type_filter(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with incident type filter."""
        # Create incidents with different types
        await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )  # UNAUTHORIZED_ACCESS

        malware_data = sample_incident_data.model_copy()
        malware_data.incident_type = SecurityIncidentType.MALWARE
        await repository.create(malware_data, "test_user", "INC-000002")

        # Filter by UNAUTHORIZED_ACCESS type
        incidents, total = await repository.list_incidents(
            incident_type_filter=[SecurityIncidentType.UNAUTHORIZED_ACCESS]
        )
        assert len(incidents) == 1
        assert total == 1
        assert incidents[0].incident_type == SecurityIncidentType.UNAUTHORIZED_ACCESS

    @pytest.mark.asyncio
    async def test_list_incidents_assigned_to_filter(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with assigned_to filter."""
        # Create incident and assign it
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )
        await repository.assign_incident(cast(UUID, incident.id), "assigned_user", "test_user")

        # Create unassigned incident
        await repository.create(sample_incident_data, "test_user", "INC-000002")

        # Filter by assigned user
        incidents, total = await repository.list_incidents(assigned_to="assigned_user")
        assert len(incidents) == 1
        assert total == 1
        assert incidents[0].assigned_to == "assigned_user"

    @pytest.mark.asyncio
    async def test_list_incidents_date_filters(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with date filters."""
        # Create incident
        await repository.create(sample_incident_data, "test_user", "INC-000001")

        # Test created_after filter (should find incident)
        incidents, total = await repository.list_incidents(
            created_after=datetime.utcnow() - timedelta(minutes=5)
        )
        assert len(incidents) == 1
        assert total == 1

        # Test created_after filter (should not find incident)
        incidents, total = await repository.list_incidents(
            created_after=datetime.utcnow() + timedelta(minutes=5)
        )
        assert len(incidents) == 0
        assert total == 0

        # Test created_before filter (should find incident)
        incidents, total = await repository.list_incidents(
            created_before=datetime.utcnow() + timedelta(minutes=5)
        )
        assert len(incidents) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_list_incidents_tags_filter(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with tags filter."""
        await repository.create(sample_incident_data, "test_user", "INC-000001")

        # Create incident with different tags
        different_tags_data = sample_incident_data.model_copy()
        different_tags_data.tags = ["network", "ddos"]
        await repository.create(different_tags_data, "test_user", "INC-000002")

        # Filter by authentication tag
        incidents, total = await repository.list_incidents(tags=["authentication"])
        assert len(incidents) == 1
        assert total == 1
        assert "authentication" in incidents[0].tags

        # Filter by network tag
        incidents, total = await repository.list_incidents(tags=["network"])
        assert len(incidents) == 1
        assert total == 1
        assert "network" in incidents[0].tags

    @pytest.mark.asyncio
    async def test_list_incidents_search_filter(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with search filter."""
        await repository.create(sample_incident_data, "test_user", "INC-000001")

        # Create incident with different title/description
        different_data = sample_incident_data.model_copy()
        different_data.title = "Malware Detection Alert"
        different_data.description = "Virus found in system files"
        await repository.create(different_data, "test_user", "INC-000002")

        # Search by title keyword
        incidents, total = await repository.list_incidents(search="Suspicious")
        assert len(incidents) == 1
        assert total == 1
        assert "Suspicious" in incidents[0].title

        # Search by description keyword
        incidents, total = await repository.list_incidents(search="login")
        assert len(incidents) == 1
        assert total == 1
        assert "login" in incidents[0].description

        # Search with no matches
        incidents, total = await repository.list_incidents(search="nonexistent")
        assert len(incidents) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_incidents_sorting(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with sorting."""
        # Create incidents with delays to test sorting
        incident1 = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Add small delay and create second incident
        await asyncio.sleep(0.001)
        different_data = sample_incident_data.model_copy()
        different_data.title = "B Title"  # For title sorting
        incident2 = await repository.create(different_data, "test_user", "INC-000002")

        # Test default sorting (created_at desc)
        incidents, total = await repository.list_incidents()
        assert len(incidents) == 2
        assert incidents[0].id == incident2.id  # Latest first
        assert incidents[1].id == incident1.id

        # Test created_at asc
        incidents, total = await repository.list_incidents(
            sort_by="created_at", sort_order="asc"
        )
        assert len(incidents) == 2
        assert incidents[0].id == incident1.id  # Earliest first
        assert incidents[1].id == incident2.id

        # Test title sorting
        incidents, total = await repository.list_incidents(
            sort_by="title", sort_order="asc"
        )
        assert len(incidents) == 2
        assert incidents[0].title == "B Title"  # Alphabetically first

    @pytest.mark.asyncio
    async def test_update_incident_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test updating an existing incident."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )
        original_updated_at = incident.updated_at

        # Update incident
        update_data = IncidentUpdate(
            title="Updated Title",
            description="Updated incident",
            severity=IncidentSeverity.CRITICAL,
            tags=["updated", "critical"],
        )

        # Add small delay to ensure updated_at changes
        await asyncio.sleep(0.001)

        result = await repository.update(cast(UUID, incident.id), update_data, "updated_user")

        assert result is not None
        assert result.id == incident.id
        assert result.title == "Updated Title"
        assert result.severity == IncidentSeverity.CRITICAL
        assert result.tags == ["updated", "critical"]
        assert result.updated_by == "updated_user"
        assert result.updated_at > original_updated_at
        # Other fields should remain unchanged
        assert result.description == sample_incident_data.description

    @pytest.mark.asyncio
    async def test_update_incident_not_exists(
        self, repository: IncidentsRepository
    ) -> None:
        """Test updating a non-existent incident."""
        fake_id = uuid4()
        update_data = IncidentUpdate(title="Updated Title", description="Updated incident")

        result = await repository.update(fake_id, update_data, "updated_user")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_incident_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test deleting an existing incident."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Delete incident
        result = await repository.delete(cast(UUID, incident.id))
        assert result is True

        # Verify it's deleted
        deleted_incident = await repository.get_by_id(cast(UUID, incident.id))
        assert deleted_incident is None

    @pytest.mark.asyncio
    async def test_delete_incident_not_exists(
        self, repository: IncidentsRepository
    ) -> None:
        """Test deleting a non-existent incident."""
        fake_id = uuid4()
        result = await repository.delete(fake_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_status_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test updating status of an existing incident."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Update status to INVESTIGATING
        result = await repository.update_status(
            cast(UUID, incident.id), IncidentStatus.INVESTIGATING, "investigator"
        )

        assert result is not None
        assert result.status == IncidentStatus.INVESTIGATING
        assert result.updated_by == "investigator"
        assert result.resolved_at is None  # Not resolved yet
        assert result.time_to_resolve is None  # type: ignore[unreachable]

    @pytest.mark.asyncio
    async def test_update_status_to_resolved(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test updating status to a resolved state."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Update status to CLOSED (resolved state)
        result = await repository.update_status(
            cast(UUID, incident.id), IncidentStatus.CLOSED, "resolver"
        )

        assert result is not None
        assert result.status == IncidentStatus.CLOSED
        assert result.resolved_at is not None
        assert result.time_to_resolve is not None
        assert result.time_to_resolve > 0

    @pytest.mark.asyncio
    async def test_update_status_to_false_positive(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test updating status to FALSE_POSITIVE."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Update status to FALSE_POSITIVE
        result = await repository.update_status(
            cast(UUID, incident.id), IncidentStatus.FALSE_POSITIVE, "analyst"
        )

        assert result is not None
        assert result.status == IncidentStatus.FALSE_POSITIVE
        assert result.resolved_at is not None
        assert result.time_to_resolve is not None

    @pytest.mark.asyncio
    async def test_update_status_not_exists(
        self, repository: IncidentsRepository
    ) -> None:
        """Test updating status of a non-existent incident."""
        fake_id = uuid4()
        result = await repository.update_status(fake_id, IncidentStatus.CLOSED, "user")
        assert result is None

    @pytest.mark.asyncio
    async def test_add_timeline_entry_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test adding timeline entry to an existing incident."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Add timeline entry
        timeline_entry = {
            "event_type": "investigation_started",
            "description": "Investigation started by security team",
            "details": {"investigator": "analyst1", "priority": "high"},
        }

        result = await repository.add_timeline_entry(
            cast(UUID, incident.id), timeline_entry, "analyst1"
        )

        assert result is not None
        assert len(result.timeline) == 1
        assert result.timeline[0]["event_type"] == "investigation_started"
        assert (
            result.timeline[0]["description"]
            == "Investigation started by security team"
        )
        assert "timestamp" in result.timeline[0]  # Should be added automatically
        assert result.updated_by == "analyst1"

    @pytest.mark.asyncio
    async def test_add_timeline_entry_with_timestamp(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test adding timeline entry with explicit timestamp."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Add timeline entry with timestamp
        custom_timestamp = datetime.utcnow().isoformat()
        timeline_entry = {
            "timestamp": custom_timestamp,
            "event_type": "user_action",
            "description": "User manually reviewed incident",
        }

        result = await repository.add_timeline_entry(
            cast(UUID, incident.id), timeline_entry, "user1"
        )

        assert result is not None
        assert len(result.timeline) == 1
        assert result.timeline[0]["timestamp"] == custom_timestamp

    @pytest.mark.asyncio
    async def test_add_timeline_entry_not_exists(
        self, repository: IncidentsRepository
    ) -> None:
        """Test adding timeline entry to a non-existent incident."""
        fake_id = uuid4()
        timeline_entry = {"event_type": "test", "description": "test"}

        result = await repository.add_timeline_entry(fake_id, timeline_entry, "user")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_analysis_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test updating analysis of an existing incident."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Update analysis
        analysis = {
            "summary": "Confirmed brute force attack from external IP",
            "risk_score": 85.5,
            "attack_patterns": ["brute_force", "credential_stuffing"],
            "indicators": [{"type": "ip", "value": "192.168.1.100"}],
            "recommendations": ["Block IP", "Force password reset"],
            "confidence": 0.9,
        }

        result = await repository.update_analysis(cast(UUID, incident.id), analysis, "ai_analyst")

        assert result is not None
        assert result.analysis == analysis
        assert result.updated_by == "ai_analyst"
        assert result.time_to_respond is not None  # Should be set on first analysis
        assert result.time_to_respond > 0

    @pytest.mark.asyncio
    async def test_update_analysis_second_time(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test updating analysis a second time (time_to_respond shouldn't change)."""
        # Create incident and add initial analysis
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        initial_analysis = {"summary": "Initial analysis"}
        await repository.update_analysis(cast(UUID, incident.id), initial_analysis, "analyst1")

        # Get the incident to check time_to_respond
        incident_after_first = await repository.get_by_id(cast(UUID, incident.id))
        assert incident_after_first is not None
        initial_time_to_respond = incident_after_first.time_to_respond

        # Add delay and update analysis again
        await asyncio.sleep(0.001)
        updated_analysis = {"summary": "Updated analysis", "confidence": 0.95}
        result = await repository.update_analysis(
            cast(UUID, incident.id), updated_analysis, "analyst2"
        )

        assert result is not None
        assert result.analysis == updated_analysis
        assert result.time_to_respond == initial_time_to_respond  # Should not change

    @pytest.mark.asyncio
    async def test_update_analysis_not_exists(
        self, repository: IncidentsRepository
    ) -> None:
        """Test updating analysis of a non-existent incident."""
        fake_id = uuid4()
        analysis = {"summary": "test"}

        result = await repository.update_analysis(fake_id, analysis, "user")
        assert result is None

    @pytest.mark.asyncio
    async def test_add_remediation_action_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test adding remediation action to an existing incident."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Add remediation action
        action = {
            "action_id": "REM-001",
            "action_type": "block_ip",
            "description": "Block malicious IP address",
            "status": "completed",
            "automated": True,
            "executed_at": datetime.utcnow().isoformat(),
            "executed_by": "auto_system",
            "result": {"success": True, "blocked_ips": ["192.168.1.100"]},
        }

        result = await repository.add_remediation_action(cast(UUID, incident.id), action, "system")

        assert result is not None
        assert len(result.remediation_actions) == 1
        assert result.remediation_actions[0] == action
        assert result.updated_by == "system"

    @pytest.mark.asyncio
    async def test_add_remediation_action_not_exists(
        self, repository: IncidentsRepository
    ) -> None:
        """Test adding remediation action to a non-existent incident."""
        fake_id = uuid4()
        action = {"action_id": "test", "action_type": "test"}

        result = await repository.add_remediation_action(fake_id, action, "user")
        assert result is None

    @pytest.mark.asyncio
    async def test_assign_incident_exists(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test assigning an existing incident."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Assign incident
        result = await repository.assign_incident(
            cast(UUID, incident.id), "security_team", "manager"
        )

        assert result is not None
        assert result.assigned_to == "security_team"
        assert result.updated_by == "manager"

    @pytest.mark.asyncio
    async def test_assign_incident_not_exists(
        self, repository: IncidentsRepository
    ) -> None:
        """Test assigning a non-existent incident."""
        fake_id = uuid4()
        result = await repository.assign_incident(fake_id, "user", "manager")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_next_incident_number_empty_db(
        self, repository: IncidentsRepository
    ) -> None:
        """Test getting next incident number when database is empty."""
        result = await repository.get_next_incident_number()
        assert result == "INC-000001"

    @pytest.mark.asyncio
    async def test_get_next_incident_number_with_existing(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test getting next incident number with existing incidents."""
        # Create incidents with specific numbers
        await repository.create(sample_incident_data, "test_user", "INC-000001")
        await repository.create(sample_incident_data, "test_user", "INC-000005")
        await repository.create(sample_incident_data, "test_user", "INC-000003")

        # Should return the next number after the highest
        result = await repository.get_next_incident_number()
        assert result == "INC-000006"

    @pytest.mark.asyncio
    async def test_get_next_incident_number_invalid_format(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test getting next incident number with invalid format in database."""
        # Create incident with invalid number format
        await repository.create(sample_incident_data, "test_user", "INVALID-FORMAT")

        # Should fallback to default
        result = await repository.get_next_incident_number()
        assert result == "INC-000001"

    @pytest.mark.asyncio
    async def test_get_incident_stats_empty_db(
        self, repository: IncidentsRepository
    ) -> None:
        """Test getting incident statistics from empty database."""
        result = await repository.get_incident_stats()

        assert result["total_incidents"] == 0
        assert result["open_incidents"] == 0
        assert result["by_status"] == {}
        assert result["by_severity"] == {}

    @pytest.mark.asyncio
    async def test_get_incident_stats_with_data(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test getting incident statistics with actual data."""
        # Create incidents with different statuses and severities
        await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )  # OPEN, HIGH

        investigating_data = sample_incident_data.model_copy()
        investigating_data.status = IncidentStatus.INVESTIGATING
        investigating_data.severity = IncidentSeverity.CRITICAL
        await repository.create(investigating_data, "test_user", "INC-000002")

        low_data = sample_incident_data.model_copy()
        low_data.severity = IncidentSeverity.LOW
        await repository.create(low_data, "test_user", "INC-000003")  # OPEN, LOW

        result = await repository.get_incident_stats()

        assert result["total_incidents"] == 3
        assert result["open_incidents"] == 2  # Two OPEN incidents
        assert result["by_status"] == {
            IncidentStatus.OPEN.value: 2,
            IncidentStatus.INVESTIGATING.value: 1,
        }
        assert result["by_severity"] == {
            IncidentSeverity.HIGH.value: 1,
            IncidentSeverity.CRITICAL.value: 1,
            IncidentSeverity.LOW.value: 1,
        }

    @pytest.mark.asyncio
    async def test_complex_filtering_scenario(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test complex filtering with multiple criteria."""
        # Create base incident
        await repository.create(sample_incident_data, "test_user", "INC-000001")

        # Create incident with different properties
        different_data = sample_incident_data.model_copy()
        different_data.severity = IncidentSeverity.CRITICAL
        different_data.status = IncidentStatus.INVESTIGATING
        different_data.incident_type = SecurityIncidentType.MALWARE
        different_data.tags = ["malware", "critical"]
        incident2 = await repository.create(different_data, "test_user", "INC-000002")

        # Assign the second incident
        await repository.assign_incident(cast(UUID, incident2.id), "security_analyst", "manager")

        # Filter with multiple criteria
        incidents, total = await repository.list_incidents(
            status_filter=[IncidentStatus.INVESTIGATING],
            severity_filter=[IncidentSeverity.CRITICAL],
            incident_type_filter=[SecurityIncidentType.MALWARE],
            assigned_to="security_analyst",
            tags=["malware"],
        )

        assert len(incidents) == 1
        assert total == 1
        assert incidents[0].incident_number == "INC-000002"
        assert incidents[0].severity == IncidentSeverity.CRITICAL
        assert incidents[0].status == IncidentStatus.INVESTIGATING
        assert incidents[0].assigned_to == "security_analyst"

    @pytest.mark.asyncio
    async def test_timeline_with_none_list(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test adding timeline entry when timeline is not a list."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Manually set timeline to None (simulating database corruption or migration issue)
        setattr(incident, "timeline", None)
        await repository.session.commit()

        # Add timeline entry - should handle None timeline gracefully
        timeline_entry = {"event_type": "test", "description": "test entry"}
        result = await repository.add_timeline_entry(
            cast(UUID, incident.id), timeline_entry, "user"
        )

        assert result is not None
        assert isinstance(result.timeline, list)  # type: ignore[unreachable]
        assert len(result.timeline) == 1  # type: ignore[unreachable]

    @pytest.mark.asyncio
    async def test_remediation_actions_with_none_list(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test adding remediation action when remediation_actions is not a list."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )

        # Manually set remediation_actions to None
        setattr(incident, "remediation_actions", None)
        await repository.session.commit()

        # Add remediation action - should handle None list gracefully
        action = {"action_id": "test", "action_type": "test"}
        result = await repository.add_remediation_action(cast(UUID, incident.id), action, "user")

        assert result is not None
        assert isinstance(result.remediation_actions, list)  # type: ignore[unreachable]
        assert len(result.remediation_actions) == 1  # type: ignore[unreachable]

    @pytest.mark.asyncio
    async def test_update_partial_fields(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test updating only specific fields."""
        # Create incident
        incident = await repository.create(
            sample_incident_data, "test_user", "INC-000001"
        )
        original_description = incident.description

        # Update only priority
        update_data = IncidentUpdate(priority=Priority.CRITICAL)  # type: ignore[call-arg]
        result = await repository.update(cast(UUID, incident.id), update_data, "updater")

        assert result is not None
        assert result.priority == Priority.CRITICAL
        assert result.description == original_description  # Should remain unchanged
        assert (
            result.severity == sample_incident_data.severity
        )  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_list_incidents_all_filters_combined(
        self, repository: IncidentsRepository, sample_incident_data: IncidentCreate
    ) -> None:
        """Test listing incidents with all possible filters combined."""
        # Create specific incident for this test
        specific_data = sample_incident_data.model_copy()
        specific_data.title = "SearchableTitle"
        specific_data.description = "SearchableDescription"
        specific_data.tags = ["specific", "test"]
        incident = await repository.create(specific_data, "test_user", "INC-000001")

        # Assign incident
        await repository.assign_incident(cast(UUID, incident.id), "test_assignee", "manager")

        # Create additional incident that shouldn't match
        other_data = sample_incident_data.model_copy()
        other_data.severity = IncidentSeverity.LOW
        other_data.status = IncidentStatus.CLOSED
        other_data.tags = ["other"]
        await repository.create(other_data, "test_user", "INC-000002")

        # Apply all filters
        incidents, total = await repository.list_incidents(
            page=1,
            page_size=10,
            status_filter=[IncidentStatus.OPEN],
            severity_filter=[IncidentSeverity.HIGH],
            incident_type_filter=[SecurityIncidentType.UNAUTHORIZED_ACCESS],
            assigned_to="test_assignee",
            created_after=datetime.utcnow() - timedelta(minutes=5),
            created_before=datetime.utcnow() + timedelta(minutes=5),
            tags=["specific"],
            search="Searchable",
            sort_by="created_at",
            sort_order="desc",
        )

        assert len(incidents) == 1
        assert total == 1
        assert incidents[0].id == incident.id

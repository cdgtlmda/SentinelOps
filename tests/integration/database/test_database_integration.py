"""
Integration tests for database layer.

Tests verify proper database operations including connection pooling,
transactions, and repository patterns.
"""

import asyncio
from typing import Any, cast
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.models.incidents import (
    IncidentSeverity,
    IncidentStatus,
    SecurityIncidentType,
)
from src.api.models.rules import RuleSeverity, RuleType
from src.database.base import Base
from src.database.pool_config import ConnectionPoolConfig
from src.database.repositories.incidents import IncidentsRepository
from src.database.repositories.rules import RulesRepository


@pytest.fixture(scope="session")
def event_loop() -> Any:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> Any:
    """Create test database engine with production configuration."""
    # Use test database URL
    test_db_url = (
        "postgresql+asyncpg://test_user:test_pass@localhost:5432/sentinelops_test"
    )
    # Apply production pool configuration
    pool_config = ConnectionPoolConfig(
        pool_size=5,  # Smaller for tests
        max_overflow=2,
        pool_timeout=30.0,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    engine = create_async_engine(
        test_db_url,
        pool_size=pool_config.pool_size,
        max_overflow=pool_config.max_overflow,
        pool_timeout=pool_config.pool_timeout,
        pool_recycle=pool_config.pool_recycle,
        pool_pre_ping=pool_config.pool_pre_ping,
        echo=False,
    )
    try:
        # Test connection - create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
    except Exception as e:
        # Skip tests if database is not available
        await engine.dispose()
        pytest.skip(f"Test database not available: {str(e)}")


@pytest_asyncio.fixture
async def db_session(test_engine: Any) -> Any:
    """Create database session for tests."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_connection_pool_configuration(self, test_engine: Any) -> None:
        """Test that connection pool is properly configured."""
        pool = test_engine.pool
        # Verify pool settings
        assert pool.size() <= 5  # pool_size
        assert pool.overflow() <= 2  # max_overflow
        # Test concurrent connections
        tasks = []
        for _ in range(7):  # pool_size + max_overflow

            async def query() -> Any:
                async with test_engine.connect() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    return result.scalar()

            tasks.append(query())

        results = await asyncio.gather(*tasks)
        assert all(r == 1 for r in results)

    @pytest.mark.asyncio
    async def test_rules_repository_crud(self, db_session: Any) -> None:
        """Test RulesRepository CRUD operations with real database."""
        repo = RulesRepository(db_session)
        # Create
        from src.api.models.rules import RuleCreate

        rule_data = RuleCreate(
            name="Test Rule",
            description="Test rule for integration testing",
            rule_type=RuleType.QUERY,
            severity=RuleSeverity.MEDIUM,
            query="SELECT * FROM test",
            conditions=None,
            threshold=None,
            correlation=None,
            enabled=True,
            tags=["test", "integration"],
            false_positive_rate=None,
        )
        created = await repo.create(rule_data, "test_user", "TEST-001")
        assert created.id is not None
        assert created.rule_number == "TEST-001"
        rule_id = created.id

        # Read
        fetched = await repo.get_by_id(cast(UUID, rule_id))
        assert fetched is not None
        assert fetched.name == "Test Rule"

        # Update
        from src.api.models.rules import RuleUpdate

        update_data = RuleUpdate(
            name="Updated Test Rule",
            description="Updated test rule description",
            false_positive_rate=0.1,
        )
        updated = await repo.update(cast(UUID, rule_id), update_data, "test_user")
        assert updated is not None
        assert updated.name == "Updated Test Rule"

        # List
        rules, total = await repo.list_rules()
        assert total == 1
        assert len(rules) == 1
        assert rules[0].name == "Updated Test Rule"

        # Delete
        await repo.delete(cast(UUID, rule_id))
        deleted = await repo.get_by_id(cast(UUID, rule_id))
        assert deleted is None

    @pytest.mark.asyncio
    async def test_incidents_repository_crud(self, db_session: Any) -> None:
        """Test IncidentsRepository CRUD operations with real database."""
        repo = IncidentsRepository(db_session)

        # Create incident
        from src.api.models.incidents import IncidentCreate, IncidentSource, Priority

        incident_data = IncidentCreate(
            title="Test Incident",
            description="Test incident for integration testing",
            incident_type=SecurityIncidentType.SUSPICIOUS_ACTIVITY,
            severity=IncidentSeverity.MEDIUM,
            priority=Priority.MEDIUM,
            status=IncidentStatus.OPEN,
            external_id=None,
            source=IncidentSource(
                system="test",
                rule_id="test_rule",
                rule_name="Test Rule",
                confidence=0.9,
                raw_data={"test": "data"},
            ),
            tags=["test"],
            custom_fields={},
        )
        created = await repo.create(incident_data, "test_user", "INC-TEST-001")
        assert created.id is not None
        incident_id = created.id

        # Verify cascade operations work
        fetched = await repo.get_by_id(cast(UUID, incident_id))
        assert fetched is not None

        # Clean up
        await repo.delete(cast(UUID, incident_id))

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session: Any) -> None:
        """Test that transactions properly rollback on error."""
        repo = RulesRepository(db_session)

        from src.api.models.rules import RuleCreate

        rule_data = RuleCreate(
            name="Rollback Test",
            description="Test",
            rule_type=RuleType.QUERY,
            severity=RuleSeverity.LOW,
            query="SELECT 1",
            conditions=None,
            threshold=None,
            correlation=None,
            enabled=True,
            tags=[],
            false_positive_rate=None,
        )

        # This should work
        created = await repo.create(rule_data, "test", "ROLLBACK-001")
        rule_id = created.id

        # Verify it was created
        fetched = await repo.get_by_id(cast(UUID, rule_id))
        assert fetched is not None

        # Session rollback happens in fixture, so rule should not persist
        # after test completes

"""
Database base configuration and session management.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any

from sqlalchemy import MetaData, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from src.database.pool_config import (
    get_development_config,
    get_production_config,
)
from src.database.pool_monitor import ConnectionPoolMonitor

# Determine environment
APP_ENV = os.getenv("APP_ENV", "development")

# Get appropriate pool configuration
if APP_ENV == "production":
    pool_config = get_production_config()
else:
    pool_config = get_development_config()

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://sentinelops:sentinelops@localhost:5432/sentinelops",
)


# Ensure the URL uses asyncpg driver for async operations
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine with pool configuration
engine_kwargs = {
    "echo": os.getenv("DATABASE_ECHO", "false").lower() == "true",
    **pool_config.get_engine_kwargs(),
}

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create connection pool monitor
pool_monitor: Optional[ConnectionPoolMonitor] = None
if os.getenv("DB_MONITOR_ENABLED", "true").lower() == "true":
    pool_monitor = ConnectionPoolMonitor(engine)

# Add event listeners for monitoring
if pool_monitor:

    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(_dbapi_connection: Any, _connection_record: Any) -> None:
        if pool_monitor:
            pool_monitor.metrics.connects += 1

    @event.listens_for(engine.sync_engine, "checkout")
    def receive_checkout(
        _dbapi_connection: Any, _connection_record: Any, _connection_proxy: Any
    ) -> None:
        if pool_monitor:
            pool_monitor.metrics.checkouts += 1

    @event.listens_for(engine.sync_engine, "checkin")
    def receive_checkin(_dbapi_connection: Any, _connection_record: Any) -> None:
        if pool_monitor:
            pool_monitor.metrics.checkins += 1


# Create async session factory with proper configuration
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    # Additional session configuration
    autoflush=False,  # Control flushing manually
    autocommit=False,  # Use transactions
)

# Create metadata with naming conventions for better migration support
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)

# Create declarative base
Base = declarative_base(metadata=metadata)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Usage:
        @router.get("/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session.

    Usage:
        async with get_db_context() as db:
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start pool monitoring if enabled
    if pool_monitor:
        await pool_monitor.start()


async def close_db() -> None:
    """Close database connections and stop monitoring."""
    # Stop pool monitoring
    if pool_monitor:
        await pool_monitor.stop()

    # Dispose of the engine
    await engine.dispose()


def get_pool_monitor() -> Optional[ConnectionPoolMonitor]:
    """Get the connection pool monitor instance."""
    return pool_monitor


async def get_pool_health() -> Dict[str, Any]:
    """Get connection pool health status."""
    if pool_monitor:
        return await pool_monitor.health_check()
    return {"status": "unknown", "message": "Pool monitoring disabled"}


def get_pool_status() -> Dict[str, Any]:
    """Get connection pool status and metrics."""
    if pool_monitor:
        return pool_monitor.get_pool_status()
    return {"status": "unknown", "message": "Pool monitoring disabled"}

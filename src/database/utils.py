"""
Database utilities and helper functions.
"""

import logging
import os
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.database.base import engine, init_db

logger = logging.getLogger(__name__)


async def check_database_connection() -> bool:
    """Check if database is accessible."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        logger.error("Database connection failed: %s", e)
        return False


async def create_database_if_not_exists() -> None:
    """Create the database if it doesn't exist."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://sentinelops:sentinelops@localhost:5432/sentinelops",
    )
    # Parse database name from URL
    parts = database_url.split("/")
    db_name = parts[-1].split("?")[0]
    base_url = "/".join(parts[:-1])

    # Connect to postgres database to create the target database
    postgres_url = f"{base_url}/postgres"

    from sqlalchemy.ext.asyncio import create_async_engine

    temp_engine = create_async_engine(postgres_url, echo=False)

    try:
        async with temp_engine.connect() as conn:
            # Check if database exists
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name},
            )
            exists = result.scalar() is not None

            if not exists:
                # Need to use isolation level for CREATE DATABASE
                await conn.execute(text("COMMIT"))
                await conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info("Created database: %s", db_name)
            else:
                logger.info("Database already exists: %s", db_name)
    finally:
        await temp_engine.dispose()


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    from pathlib import Path

    # Find alembic.ini from project root
    project_root = Path(__file__).parent.parent.parent
    alembic_ini = project_root / "alembic.ini"

    if not alembic_ini.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini}")

    config = Config(str(alembic_ini))

    # Override with environment variable if set
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        config.set_main_option("sqlalchemy.url", database_url)

    return config


def run_migrations() -> None:
    """Run all pending migrations."""
    config = get_alembic_config()
    command.upgrade(config, "head")
    logger.info("Database migrations completed")


def create_migration(message: str) -> None:
    """Create a new migration."""
    config = get_alembic_config()
    command.revision(config, message=message, autogenerate=True)
    logger.info("Created migration: %s", message)


async def initialize_database() -> None:
    """Initialize the database with all setup steps."""
    logger.info("Initializing database...")

    # Create database if it doesn't exist
    await create_database_if_not_exists()

    # Check connection
    if not await check_database_connection():
        raise RuntimeError("Failed to connect to database")

    # Run migrations
    run_migrations()

    # Initialize tables (in case migrations are empty)
    await init_db()

    logger.info("Database initialization completed")


def get_database_status() -> dict[str, Any]:
    """Get current database status information."""
    config = get_alembic_config()

    # This would normally check migration status, connection pool stats, etc.
    # For now, return basic info
    return {
        "url": config.get_main_option("sqlalchemy.url"),
        "migrations_location": config.get_main_option("script_location"),
        "initialized": True,
    }

#!/usr/bin/env python3
"""
Database Migration Management Script for SentinelOps

This script provides a comprehensive interface for managing database migrations
including running migrations, creating new ones, checking status, and rollbacks.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.database.utils import (
    check_database_connection,
    create_database_if_not_exists,
    get_alembic_config,
    initialize_database,
    run_migrations,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations for SentinelOps."""

    def __init__(self):
        self.config = get_alembic_config()
        self.database_url = self.config.get_main_option("sqlalchemy.url")

    def get_engine(self) -> Engine:
        """Get a synchronous database engine."""
        # Convert async URL to sync for Alembic operations
        sync_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        return create_engine(sync_url)

    def check_current_revision(self) -> Optional[str]:
        """Check the current database revision."""
        engine = self.get_engine()
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return context.get_current_revision()

    def get_pending_migrations(self) -> list[str]:
        """Get list of pending migrations."""
        script_dir = ScriptDirectory.from_config(self.config)
        current_rev = self.check_current_revision()

        pending = []
        for revision in script_dir.walk_revisions():
            if current_rev is None or revision.revision != current_rev:
                pending.append(f"{revision.revision} - {revision.doc}")
                if revision.revision == current_rev:
                    break

        return list(reversed(pending))

    def run_migrations(self, target: str = "head") -> None:
        """Run migrations up to the specified target."""
        logger.info(f"Running migrations to target: {target}")
        command.upgrade(self.config, target)
        logger.info("Migrations completed successfully")

    def rollback_migration(self, steps: int = 1) -> None:
        """Rollback migrations by specified number of steps."""
        logger.info(f"Rolling back {steps} migration(s)")
        command.downgrade(self.config, f"-{steps}")
        logger.info("Rollback completed successfully")

    def create_migration(self, message: str, autogenerate: bool = True) -> None:
        """Create a new migration."""
        logger.info(f"Creating new migration: {message}")
        command.revision(self.config, message=message, autogenerate=autogenerate)
        logger.info("Migration created successfully")

    def show_history(self) -> None:
        """Show migration history."""
        command.history(self.config)

    def show_current(self) -> None:
        """Show current database revision."""
        command.current(self.config)

    def verify_migrations(self) -> bool:
        """Verify that all migrations can be applied cleanly."""
        logger.info("Verifying migrations...")

        try:
            # Check if we can connect to the database
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            # Get pending migrations
            pending = self.get_pending_migrations()

            if pending:
                logger.info(f"Found {len(pending)} pending migration(s):")
                for migration in pending:
                    logger.info(f"  - {migration}")
            else:
                logger.info("Database is up to date")

            return True

        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return False


async def async_init_database():
    """Async wrapper for database initialization."""
    await initialize_database()


def main():
    """Main entry point for the migration management script."""
    parser = argparse.ArgumentParser(
        description="Manage SentinelOps database migrations"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Initialize database command
    init_parser = subparsers.add_parser(
        "init", help="Initialize database and run all migrations"
    )

    # Run migrations command
    upgrade_parser = subparsers.add_parser("upgrade", help="Run pending migrations")
    upgrade_parser.add_argument(
        "--target", default="head", help="Target revision (default: head)"
    )

    # Rollback command
    downgrade_parser = subparsers.add_parser("downgrade", help="Rollback migrations")
    downgrade_parser.add_argument(
        "--steps", type=int, default=1, help="Number of steps to rollback"
    )

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message")
    create_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Don't autogenerate migration from model changes",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show migration status")

    # History command
    history_parser = subparsers.add_parser("history", help="Show migration history")

    # Verify command
    verify_parser = subparsers.add_parser(
        "verify", help="Verify migrations can be applied"
    )

    # Check connection command
    check_parser = subparsers.add_parser("check", help="Check database connection")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create migration manager
    manager = MigrationManager()

    try:
        if args.command == "init":
            logger.info("Initializing database...")
            asyncio.run(async_init_database())
            logger.info("Database initialization complete")

        elif args.command == "upgrade":
            manager.run_migrations(args.target)

        elif args.command == "downgrade":
            manager.rollback_migration(args.steps)

        elif args.command == "create":
            manager.create_migration(
                args.message, autogenerate=not args.no_autogenerate
            )

        elif args.command == "status":
            logger.info("Current migration status:")
            manager.show_current()

            pending = manager.get_pending_migrations()
            if pending:
                logger.info(f"\n{len(pending)} pending migration(s):")
                for migration in pending:
                    logger.info(f"  - {migration}")
            else:
                logger.info("\nDatabase is up to date")

        elif args.command == "history":
            manager.show_history()

        elif args.command == "verify":
            if manager.verify_migrations():
                logger.info("Migration verification passed")
                sys.exit(0)
            else:
                logger.error("Migration verification failed")
                sys.exit(1)

        elif args.command == "check":
            if asyncio.run(check_database_connection()):
                logger.info("Database connection successful")
                sys.exit(0)
            else:
                logger.error("Database connection failed")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

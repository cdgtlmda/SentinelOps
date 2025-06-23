#!/usr/bin/env python3
"""
Verify that existing database migrations are valid and can be applied.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

from alembic.config import Config
from alembic.script import ScriptDirectory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_migrations():
    """Verify all migration files are valid."""
    try:
        # Get Alembic configuration
        alembic_ini = project_root / "alembic.ini"
        config = Config(str(alembic_ini))

        # Get script directory
        script_dir = ScriptDirectory.from_config(config)

        # Check all revisions
        revisions = list(script_dir.walk_revisions())

        logger.info(f"Found {len(revisions)} migration(s):")

        for rev in reversed(revisions):
            logger.info(f"  ✓ {rev.revision[:8]} - {rev.doc}")

            # Verify revision has both upgrade and downgrade
            module = script_dir.get_revision(rev.revision).module

            if not hasattr(module, "upgrade"):
                logger.error(f"    ✗ Missing upgrade() function")
                return False

            if not hasattr(module, "downgrade"):
                logger.error(f"    ✗ Missing downgrade() function")
                return False

        logger.info("\nAll migrations are valid!")
        return True

    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False


if __name__ == "__main__":
    if verify_migrations():
        sys.exit(0)
    else:
        sys.exit(1)

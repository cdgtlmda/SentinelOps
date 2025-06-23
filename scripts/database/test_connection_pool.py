#!/usr/bin/env python3
"""
Test script to verify database connection pool configuration.

This script tests the connection pool setup and monitoring functionality.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Set test mode to bypass credential validation
os.environ["SENTINELOPS_TEST_MODE"] = "true"

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.base import (
    engine,
    get_db_context,
    get_pool_health,
    get_pool_status,
    init_db,
    pool_monitor,
)
from src.database.health_checks import check_database_connectivity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_connectivity():
    """Test basic database connectivity."""
    logger.info("Testing basic connectivity...")
    result = await check_database_connectivity()

    if result["connected"]:
        logger.info("✓ Database connection successful")
    else:
        logger.error(f"✗ Database connection failed: {result['error']}")
        return False

    return True


async def test_pool_configuration():
    """Test pool configuration."""
    logger.info("\nTesting pool configuration...")

    pool = engine.pool
    logger.info(f"Pool class: {pool.__class__.__name__}")

    # Get pool configuration from environment
    expected_size = int(os.getenv("DB_POOL_SIZE", "20"))
    expected_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    if hasattr(pool, "size"):
        logger.info(f"Pool size: {pool.size()} (expected: {expected_size})")

    if hasattr(pool, "_max_overflow"):
        logger.info(
            f"Max overflow: {pool._max_overflow} (expected: {expected_overflow})"
        )

    return True


async def test_concurrent_connections():
    """Test concurrent connection handling."""
    logger.info("\nTesting concurrent connections...")

    async def execute_query(query_id: int):
        """Execute a simple query."""
        try:
            async with get_db_context() as db:
                result = await db.execute(text("SELECT pg_sleep(0.1), %s"), [query_id])
                return True
        except Exception as e:
            logger.error(f"Query {query_id} failed: {e}")
            return False

    # Import here to avoid circular dependency
    from sqlalchemy import text

    # Run 10 concurrent queries
    tasks = [execute_query(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    successful = sum(results)
    logger.info(f"✓ {successful}/10 concurrent queries succeeded")

    return all(results)


async def test_pool_monitoring():
    """Test pool monitoring functionality."""
    logger.info("\nTesting pool monitoring...")

    if not pool_monitor:
        logger.warning("Pool monitoring is disabled")
        return True

    # Get pool status
    status = get_pool_status()
    logger.info(f"Pool status retrieved: {status.get('pool_class')}")

    # Check metrics
    metrics = status.get("metrics", {})
    connections = metrics.get("connections", {})
    logger.info(f"Active connections: {connections.get('active', 0)}")
    logger.info(f"Total connections: {connections.get('total', 0)}")

    # Get pool health
    health = await get_pool_health()
    logger.info(f"Pool health status: {health.get('status')}")

    return health.get("status") in ["healthy", "degraded"]


async def test_pool_saturation():
    """Test pool behavior under saturation."""
    logger.info("\nTesting pool saturation handling...")

    # This test is informational only
    pool = engine.pool
    if hasattr(pool, "size") and hasattr(pool, "checked_out"):
        logger.info(f"Current utilization: {pool.checked_out()}/{pool.size()}")

    return True


async def main():
    """Run all tests."""
    logger.info("Starting database connection pool tests...")

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Run tests
        tests = [
            ("Basic Connectivity", test_basic_connectivity),
            ("Pool Configuration", test_pool_configuration),
            ("Concurrent Connections", test_concurrent_connections),
            ("Pool Monitoring", test_pool_monitoring),
            ("Pool Saturation", test_pool_saturation),
        ]

        results = []
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*50}")

            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"Test failed with exception: {e}")
                results.append((test_name, False))

        # Summary
        logger.info(f"\n{'='*50}")
        logger.info("Test Summary:")
        logger.info(f"{'='*50}")

        for test_name, result in results:
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")

        all_passed = all(result for _, result in results)

        if all_passed:
            logger.info("\n✓ All tests passed!")
        else:
            logger.error("\n✗ Some tests failed!")

        return 0 if all_passed else 1

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return 1
    finally:
        # Cleanup
        await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

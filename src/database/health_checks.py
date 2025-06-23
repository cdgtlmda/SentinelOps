"""
Database health checks for SentinelOps.

This module provides health check implementations for database connectivity
and connection pool monitoring.
"""

import logging
import time
from typing import Any, Dict

from sqlalchemy import text

from src.api.health import ComponentHealth, HealthStatus
from src.database.base import engine, get_pool_health, get_pool_status, pool_monitor

logger = logging.getLogger(__name__)


async def check_database_health() -> ComponentHealth:
    """
    Comprehensive database health check.

    Checks:
    - Basic connectivity
    - Query execution
    - Connection pool health
    - Pool metrics

    Returns:
        ComponentHealth with database status
    """
    metadata: Dict[str, Any] = {}

    try:
        # Test basic connectivity and query execution
        start_time = time.time()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        query_time = time.time() - start_time

        metadata["query_time_ms"] = round(query_time * 1000, 2)

        # Get pool health if monitoring is enabled
        if pool_monitor:
            pool_health = await get_pool_health()
            metadata["pool_health"] = pool_health

            # Get pool status
            pool_status = get_pool_status()
            metadata["pool_metrics"] = pool_status.get("metrics", {})

            # Determine overall health based on pool status
            if pool_health.get("status") == "unhealthy":
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database pool is unhealthy",
                    metadata=metadata,
                )

            # Check for warnings (high utilization, slow queries)
            pool_checks = pool_health.get("checks", {})
            warnings = []

            if pool_checks.get("pool_saturation", {}).get("status") == "warn":
                warnings.append("High connection pool utilization")

            if pool_checks.get("slow_queries", {}).get("status") == "warn":
                warnings.append("High slow query rate")

            if warnings:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="; ".join(warnings),
                    metadata=metadata,
                )

        # Everything is healthy
        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database is healthy",
            metadata=metadata,
        )

    except (ConnectionError, RuntimeError, ValueError) as e:
        logger.error("Database health check failed: %s", e)
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}",
            metadata=metadata,
        )


async def check_database_connectivity() -> Dict[str, Any]:
    """
    Simple database connectivity check.

    Returns:
        Dict with connection status
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"connected": True, "error": None}
    except (ConnectionError, RuntimeError, ValueError) as e:
        return {"connected": False, "error": str(e)}

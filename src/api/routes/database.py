"""
Database pool monitoring API endpoints.

This module provides API endpoints for monitoring database connection pool
health and metrics.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.database.base import get_pool_health, get_pool_status, pool_monitor

router = APIRouter(
    prefix="/api/v1/database",
    tags=["database"],
    responses={
        503: {"description": "Database unavailable"},
    },
)


class PoolStatus(BaseModel):
    """Database connection pool status response."""

    pool_class: str
    metrics: Dict[str, Any]
    pool_config: Optional[Dict[str, Any]] = None


class PoolHealth(BaseModel):
    """Database connection pool health response."""

    status: str
    timestamp: str
    checks: Dict[str, Any]


@router.get("/pool/status", response_model=PoolStatus)
async def get_database_pool_status() -> PoolStatus:
    """
    Get current database connection pool status and metrics.

    Returns detailed information about:
    - Active/idle connections
    - Performance metrics
    - Pool configuration
    - Event counters
    """
    if not pool_monitor:
        raise HTTPException(status_code=503, detail="Pool monitoring is disabled")

    status = get_pool_status()
    return PoolStatus(**status)


@router.get("/pool/health", response_model=PoolHealth)
async def get_database_pool_health() -> PoolHealth:
    """
    Get database connection pool health check results.

    Checks:
    - Connection availability
    - Pool saturation
    - Slow query rate

    Returns health status with detailed check results.
    """
    if not pool_monitor:
        raise HTTPException(status_code=503, detail="Pool monitoring is disabled")

    health = await get_pool_health()
    return PoolHealth(**health)


@router.post("/pool/reset-metrics")
async def reset_pool_metrics() -> Dict[str, str]:
    """
    Reset database pool metrics.

    Clears accumulated metrics like query times and connection times.
    Useful for starting fresh measurements after configuration changes.
    """
    if not pool_monitor:
        raise HTTPException(status_code=503, detail="Pool monitoring is disabled")

    # Reset the metric lists
    pool_monitor._query_times = []
    pool_monitor._connection_times = []
    pool_monitor.metrics.slow_queries = 0
    pool_monitor.metrics.failed_connections = 0

    return {"message": "Pool metrics reset successfully"}

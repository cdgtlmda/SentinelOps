"""
Database connection pool monitoring and metrics.

This module provides monitoring capabilities for the database connection pool,
including health checks, metrics collection, and pool status reporting.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DatabaseError

logger = logging.getLogger(__name__)


@dataclass
class PoolMetrics:
    """Metrics for database connection pool."""

    # Connection metrics
    active_connections: int = 0
    idle_connections: int = 0
    total_connections: int = 0
    overflow_connections: int = 0

    # Performance metrics
    avg_connection_time: float = 0.0
    avg_query_time: float = 0.0
    slow_queries: int = 0
    failed_connections: int = 0

    # Pool events
    checkouts: int = 0
    checkins: int = 0
    connects: int = 0
    disconnects: int = 0

    # Timestamps
    last_updated: datetime = field(default_factory=datetime.utcnow)
    uptime_seconds: float = 0.0


class ConnectionPoolMonitor:
    """Monitor database connection pool health and performance."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.metrics = PoolMetrics()
        self.start_time = time.time()
        self._query_times: List[float] = []
        self._connection_times: List[float] = []
        self._monitoring_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """Start monitoring the connection pool."""
        logger.info("Starting connection pool monitoring")
        self._monitoring_task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop monitoring the connection pool."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped connection pool monitoring")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                await self._update_metrics()
                await asyncio.sleep(10)  # Update every 10 seconds
            except asyncio.CancelledError:
                break
            except (AttributeError, ValueError, RuntimeError) as e:
                logger.error("Error in pool monitoring: %s", e)
                await asyncio.sleep(30)  # Back off on error

    async def _update_metrics(self) -> None:
        """Update pool metrics."""
        pool = self.engine.pool

        if isinstance(pool, QueuePool):
            self.metrics.active_connections = pool.checkedout()
            self.metrics.total_connections = pool.size()
            self.metrics.overflow_connections = pool.overflow()
            self.metrics.idle_connections = pool.size() - pool.checkedout()

        # Update performance metrics
        if self._query_times:
            self.metrics.avg_query_time = sum(self._query_times) / len(
                self._query_times
            )
            self.metrics.slow_queries = sum(1 for t in self._query_times if t > 1.0)

        if self._connection_times:
            self.metrics.avg_connection_time = sum(self._connection_times) / len(
                self._connection_times
            )

        # Update uptime
        self.metrics.uptime_seconds = time.time() - self.start_time
        self.metrics.last_updated = datetime.utcnow()

        # Keep only recent measurements
        self._query_times = self._query_times[-1000:]
        self._connection_times = self._connection_times[-1000:]

    def record_query_time(self, duration: float) -> None:
        """Record query execution time."""
        self._query_times.append(duration)

    def record_connection_time(self, duration: float) -> None:
        """Record connection establishment time."""
        self._connection_times.append(duration)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on connection pool."""
        health_status: Dict[str, Any] = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }

        # Check connection availability
        try:
            start = time.time()
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            connection_time = time.time() - start

            health_status["checks"]["connection"] = {
                "status": "pass",
                "time_ms": round(connection_time * 1000, 2),
            }

            self.record_connection_time(connection_time)

        except (OperationalError, DatabaseError, AttributeError, ValueError) as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["connection"] = {"status": "fail", "error": str(e)}
            self.metrics.failed_connections += 1

        # Check pool saturation
        pool = self.engine.pool
        if isinstance(pool, QueuePool):
            utilization = pool.checkedout() / pool.size() if pool.size() > 0 else 0

            health_status["checks"]["pool_saturation"] = {
                "status": "pass" if utilization < 0.9 else "warn",
                "utilization": round(utilization * 100, 2),
                "active": pool.checkedout(),
                "size": pool.size(),
            }

        # Check slow query rate
        if self._query_times:
            slow_query_rate = self.metrics.slow_queries / len(self._query_times)
            health_status["checks"]["slow_queries"] = {
                "status": "pass" if slow_query_rate < 0.05 else "warn",
                "rate": round(slow_query_rate * 100, 2),
                "count": self.metrics.slow_queries,
            }

        return health_status

    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and metrics."""
        pool = self.engine.pool

        status = {
            "pool_class": pool.__class__.__name__,
            "metrics": {
                "connections": {
                    "active": self.metrics.active_connections,
                    "idle": self.metrics.idle_connections,
                    "total": self.metrics.total_connections,
                    "overflow": self.metrics.overflow_connections,
                    "failed": self.metrics.failed_connections,
                },
                "performance": {
                    "avg_connection_time_ms": round(
                        self.metrics.avg_connection_time * 1000, 2
                    ),
                    "avg_query_time_ms": round(self.metrics.avg_query_time * 1000, 2),
                    "slow_queries": self.metrics.slow_queries,
                },
                "events": {
                    "checkouts": self.metrics.checkouts,
                    "checkins": self.metrics.checkins,
                    "connects": self.metrics.connects,
                    "disconnects": self.metrics.disconnects,
                },
                "uptime": {
                    "seconds": round(self.metrics.uptime_seconds, 2),
                    "last_updated": self.metrics.last_updated.isoformat(),
                },
            },
        }

        # Add pool-specific info
        if isinstance(pool, QueuePool):
            status["pool_config"] = {
                "size": pool.size(),
                "timeout": pool.timeout(),
                # recycle and pre_ping are not QueuePool attributes directly
            }

        return status

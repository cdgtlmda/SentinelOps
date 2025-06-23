"""
Health check endpoints for SentinelOps.
"""

import asyncio
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import psutil

from ..config.logging_config import get_logger
from ..integrations.gcp_logging import get_gcp_logging
from ..utils.gcp_utils import check_gcp_connectivity

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a single component."""

    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Component health status")
    message: Optional[str] = Field(None, description="Additional status message")
    last_check: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last health check timestamp",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional component metadata"
    )


class SystemHealth(BaseModel):
    """Overall system health status."""

    status: HealthStatus = Field(..., description="Overall system status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Health check timestamp",
    )
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    components: List[ComponentHealth] = Field(
        default_factory=list, description="Individual component health statuses"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional system metadata"
    )


class HealthChecker:
    """Manages health checks for all system components."""

    def __init__(self) -> None:
        self.checks: Dict[str, Callable[[], Awaitable[ComponentHealth]]] = {}
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health checks."""
        self.register("api", self._check_api_health)
        self.register("google_cloud", self._check_gcp_health)
        self.register("logging", self._check_logging_health)
        self.register("agents", self._check_agents_health)

    def register(
        self, name: str, check_func: Callable[[], Awaitable[ComponentHealth]]
    ) -> None:
        """
        Register a health check function.

        Args:
            name: Component name
            check_func: Async function that returns ComponentHealth
        """
        self.checks[name] = check_func

    async def _check_api_health(self) -> ComponentHealth:
        """Check API server health."""
        try:
            # Basic API health - if we're running, we're healthy
            return ComponentHealth(
                name="api",
                status=HealthStatus.HEALTHY,
                message="API is running",
                metadata={
                    "uptime_seconds": getattr(self, "_uptime", 0),
                    "request_count": getattr(self, "_request_count", 0),
                },
            )
        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("API health check failed: %s", e)
            return ComponentHealth(
                name="api", status=HealthStatus.UNHEALTHY, message=str(e)
            )

    async def _check_gcp_health(self) -> ComponentHealth:
        """Check Google Cloud connectivity."""
        try:
            is_connected = await check_gcp_connectivity()

            if is_connected:
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "unknown")
                return ComponentHealth(
                    name="google_cloud",
                    status=HealthStatus.HEALTHY,
                    message="Connected to Google Cloud",
                    metadata={"project_id": project_id},
                )
            else:
                return ComponentHealth(
                    name="google_cloud",
                    status=HealthStatus.UNHEALTHY,
                    message="Cannot connect to Google Cloud",
                )

        except (OSError, ConnectionError, RuntimeError, ValueError) as e:
            logger.error("GCP health check failed: %s", e)
            return ComponentHealth(
                name="google_cloud", status=HealthStatus.UNHEALTHY, message=str(e)
            )

    async def _check_logging_health(self) -> ComponentHealth:
        """Check logging system health."""
        try:
            # Test local logging
            test_message = f"Health check at {datetime.now(timezone.utc)}"
            logger.info(test_message)

            # Check if Cloud Logging is configured
            gcp_logging = get_gcp_logging()
            cloud_logging_enabled = gcp_logging.client is not None

            return ComponentHealth(
                name="logging",
                status=HealthStatus.HEALTHY,
                message="Logging system operational",
                metadata={
                    "cloud_logging_enabled": cloud_logging_enabled,
                    "log_level": os.getenv("LOG_LEVEL", "INFO"),
                },
            )

        except (OSError, RuntimeError, ValueError) as e:
            logger.error("Logging health check failed: %s", e)
            return ComponentHealth(
                name="logging",
                status=HealthStatus.DEGRADED,
                message=f"Logging issues: {e}",
            )

    async def _check_agents_health(self) -> ComponentHealth:  # noqa: C901
        """Check agent system health."""
        try:
            # Check for agent processes or services
            if psutil is None:
                return ComponentHealth(
                    name="agents",
                    status=HealthStatus.DEGRADED,
                    message="psutil not available for process monitoring",
                    metadata={"monitoring": "limited"},
                )

            agent_statuses = {}
            agent_types = [
                "detection_agent",
                "analysis_agent",
                "remediation_agent",
                "communication_agent",
                "orchestrator_agent",
            ]

            # Check environment variables for agent status
            for agent_type in agent_types:
                # Check if agent is enabled in environment
                env_key = f"{agent_type.upper()}_ENABLED"
                is_enabled = os.environ.get(env_key, "true").lower() == "true"

                if not is_enabled:
                    agent_statuses[agent_type] = "disabled"
                    continue

                # Check for running processes (simple check)
                agent_running = False
                try:
                    for proc in psutil.process_iter(["name", "cmdline"]):
                        try:
                            cmdline = " ".join(proc.info.get("cmdline", []))
                            if agent_type in cmdline:
                                agent_running = True
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except (psutil.Error, OSError, AttributeError):
                    pass
                # Check Cloud Run service status if available
                if not agent_running:
                    service_env = f"{agent_type.upper()}_SERVICE"
                    if os.environ.get(service_env):
                        # Service is configured
                        agent_statuses[agent_type] = "deployed"
                    else:
                        agent_statuses[agent_type] = "not_started"
                else:
                    agent_statuses[agent_type] = "running"

            # Determine overall agent health
            running_count = sum(
                1 for s in agent_statuses.values() if s in ["running", "deployed"]
            )
            total_enabled = sum(1 for s in agent_statuses.values() if s != "disabled")

            if total_enabled == 0:
                health_status = HealthStatus.UNHEALTHY
                message = "No agents enabled"
            elif running_count == total_enabled:
                health_status = HealthStatus.HEALTHY
                message = f"All {running_count} enabled agents operational"
            elif running_count > 0:
                health_status = HealthStatus.DEGRADED
                message = f"{running_count}/{total_enabled} agents operational"
            else:
                health_status = HealthStatus.UNHEALTHY
                message = "No agents running"

            return ComponentHealth(
                name="agents",
                status=health_status,
                message=message,
                metadata={"agent_statuses": agent_statuses},
            )

        except (OSError, RuntimeError, ValueError) as e:
            logger.error("Agent health check failed: %s", e)
            return ComponentHealth(
                name="agents", status=HealthStatus.UNHEALTHY, message=str(e)
            )

    async def check_all(self) -> SystemHealth:
        """Run all registered health checks."""
        # Get basic system info
        version = os.getenv("APP_VERSION", "0.1.0")
        environment = os.getenv("APP_ENV", "development")

        # Run all health checks concurrently
        check_tasks = [check_func() for check_func in self.checks.values()]
        components = await asyncio.gather(*check_tasks, return_exceptions=True)

        # Handle any exceptions in health checks
        valid_components = []
        for component in components:
            if isinstance(component, Exception):
                logger.error("Health check exception: %s", component)
                valid_components.append(
                    ComponentHealth(
                        name="unknown",
                        status=HealthStatus.UNHEALTHY,
                        message=str(component),
                    )
                )
            elif isinstance(component, ComponentHealth):
                valid_components.append(component)

        # Determine overall system status
        statuses = [c.status for c in valid_components]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        return SystemHealth(
            status=overall_status,
            version=version,
            environment=environment,
            components=valid_components,
            metadata={
                "total_components": len(valid_components),
                "healthy_components": sum(
                    1 for c in valid_components if c.status == HealthStatus.HEALTHY
                ),
            },
        )


# Global health checker instance
_health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return _health_checker


@router.get(
    "/",
    response_model=SystemHealth,
    summary="Get system health",
    description="Returns comprehensive health status of all system components",
)
async def get_health() -> SystemHealth:
    """Get overall system health status."""
    checker = get_health_checker()
    return await checker.check_all()


@router.get(
    "/live",
    summary="Liveness probe",
    description="Simple liveness check for container orchestration",
    responses={
        200: {"description": "Service is alive"},
        503: {"description": "Service is not alive"},
    },
)
async def liveness() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the service is alive and able to handle requests.
    """
    try:
        # Basic liveness check - if we can respond, we're alive
        return {"status": "alive", "timestamp": datetime.now(timezone.utc)}
    except (OSError, RuntimeError) as e:
        logger.error("Liveness check failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not alive",
        ) from e


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Readiness check for container orchestration",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness() -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.

    Returns 200 if the service is ready to handle requests.
    Checks critical dependencies like database and external services.
    """
    checker = get_health_checker()
    health = await checker.check_all()

    if health.status == HealthStatus.HEALTHY:
        return {
            "status": "ready",
            "timestamp": health.timestamp,
            "components": len(health.components),
        }
    else:
        # Return 503 if any critical component is unhealthy
        critical_components = ["google_cloud", "api"]
        critical_unhealthy = [
            c
            for c in health.components
            if c.name in critical_components and c.status == HealthStatus.UNHEALTHY
        ]

        if critical_unhealthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "not ready",
                    "reason": (
                        f"Critical components unhealthy: "
                        f"{[c.name for c in critical_unhealthy]}"
                    ),
                },
            )

        # If only non-critical components are unhealthy, still return ready
        return {
            "status": "ready (degraded)",
            "timestamp": health.timestamp,
            "degraded_components": [
                c.name for c in health.components if c.status != HealthStatus.HEALTHY
            ],
        }


@router.get(
    "/component/{component_name}",
    response_model=ComponentHealth,
    summary="Get component health",
    description="Returns health status of a specific component",
)
async def get_component_health(component_name: str) -> ComponentHealth:
    """Get health status of a specific component."""
    checker = get_health_checker()

    if component_name not in checker.checks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component '{component_name}' not found",
        )

    try:
        return await checker.checks[component_name]()
    except (OSError, ConnectionError, RuntimeError, ValueError) as e:
        logger.error("Component health check failed for %s: %s", component_name, e)
        return ComponentHealth(
            name=component_name,
            status=HealthStatus.UNHEALTHY,
            message=f"Health check failed: {e}",
        )


# Utility functions for adding custom health checks
def register_health_check(
    name: str, check_func: Callable[[], Awaitable[ComponentHealth]]
) -> None:
    """
    Register a custom health check.

    Args:
        name: Component name
        check_func: Async function that returns ComponentHealth

    Example:
        async def check_database() -> ComponentHealth:
            # Check database connection
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY
            )

        register_health_check("database", check_database)
    """
    checker = get_health_checker()
    checker.register(name, check_func)


# Agent-specific health check registration
async def check_agent_health(agent_name: str, agent_instance: Any) -> ComponentHealth:
    """
    Generic agent health check.

    Args:
        agent_name: Name of the agent
        agent_instance: The agent instance to check

    Returns:
        ComponentHealth for the agent
    """
    try:
        # Check if agent has a health check method
        if hasattr(agent_instance, "health_check"):
            health_info = await agent_instance.health_check()
            return ComponentHealth(
                name=agent_name,
                status=health_info.get("status", HealthStatus.HEALTHY),
                message=health_info.get("message"),
                metadata=health_info.get("metadata", {}),
            )

        # Basic check - if agent exists and has required attributes
        if hasattr(agent_instance, "name") and hasattr(agent_instance, "initialized"):
            if agent_instance.initialized:
                return ComponentHealth(
                    name=agent_name,
                    status=HealthStatus.HEALTHY,
                    message=f"{agent_name} is initialized",
                )
            else:
                return ComponentHealth(
                    name=agent_name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"{agent_name} is not initialized",
                )

        # Fallback
        return ComponentHealth(
            name=agent_name,
            status=HealthStatus.UNHEALTHY,
            message="Agent instance not properly configured",
        )

    except (OSError, RuntimeError, ValueError) as e:
        logger.error("Agent health check failed for %s: %s", agent_name, e)
        return ComponentHealth(
            name=agent_name, status=HealthStatus.UNHEALTHY, message=str(e)
        )

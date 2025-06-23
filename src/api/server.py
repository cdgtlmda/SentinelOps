"""
FastAPI server for SentinelOps API endpoints

This module sets up the main API server with all routes including
the natural language processing endpoints.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.auth_routes import router as auth_router
from src.api.docs import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    TAGS_METADATA,
    custom_openapi_schema,
)
from src.api.exceptions import SentinelOpsException as SentinelOpsAPIException
from src.api.health import register_health_check
from src.api.health import router as health_router
from src.api.middleware.correlation_id import CorrelationIdMiddleware
from src.api.middleware.logging_middleware import LoggingMiddleware
from src.api.nlp_routes import router as nlp_router
from src.api.routes.analysis import router as analysis_router
from src.api.routes.database import router as database_router
from src.api.routes.incidents import router as incidents_router
from src.api.routes.notifications import router as notifications_router
from src.api.routes.remediation import router as remediation_router
from src.api.routes.rules import router as rules_router
from src.api.routes.threat_simulation import router as threat_simulation_router
from src.api.routes.live_demo import router as live_demo_router
from src.api.security import setup_rate_limiting, setup_security_headers
from src.api.websocket import websocket_endpoint
from src.database.base import close_db, init_db
from src.database.health_checks import check_database_health
from src.integrations.gemini import VertexAIGeminiClient as GeminiIntegration

logger = logging.getLogger(__name__)

# Global Gemini instance is stored in app.state, not as a module variable


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle
    """
    # pylint: disable=global-statement

    # Startup
    logger.info("Starting SentinelOps API server...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")

        # Register database health check
        register_health_check("database", check_database_health)
        logger.info("Database health check registered")
    except (ValueError, RuntimeError, ConnectionError) as e:
        logger.error("Failed to initialize database: %s", e)
        raise

    # Initialize Gemini client
    gemini_client = GeminiIntegration()
    logger.info("Gemini client initialized")

    # Make it available to routes
    fastapi_app.state.gemini = gemini_client

    yield

    # Shutdown
    logger.info("Shutting down SentinelOps API server...")

    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except (ValueError, RuntimeError, ConnectionError) as e:
        logger.error("Error closing database connections: %s", e)

    if gemini_client:
        # Cleanup if needed
        pass


# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(LoggingMiddleware)

# Configure security features
setup_rate_limiting(app)
setup_security_headers(app)

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(nlp_router)
app.include_router(incidents_router)
app.include_router(rules_router)
app.include_router(analysis_router)
app.include_router(remediation_router)
app.include_router(notifications_router)
app.include_router(database_router)

# Threat simulation routes
app.include_router(threat_simulation_router)

# Live demo routes
app.include_router(live_demo_router)

# You can add more routers here as they're created:
# app.include_router(detection_router)
# app.include_router(communication_router)

# WebSocket endpoint
app.websocket("/ws")(websocket_endpoint)


@app.get("/api/v1/websocket/status")
async def websocket_status() -> dict[str, Any]:
    """Get WebSocket connection status."""
    from src.api.websocket import get_websocket_status

    return await get_websocket_status()


@app.exception_handler(SentinelOpsAPIException)
async def sentinelops_exception_handler(
    request: Request, exc: SentinelOpsAPIException  # pylint: disable=unused-argument
) -> JSONResponse:
    """
    Handle SentinelOps-specific API exceptions
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception  # pylint: disable=unused-argument
) -> JSONResponse:
    """
    Handle unexpected exceptions
    """
    logger.error("Unexpected error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": None,
        },
    )


@app.get("/")
async def root() -> dict[str, Any]:
    """
    Root endpoint
    """
    return {
        "service": "SentinelOps API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "incidents": "/api/v1/incidents",
            "rules": "/api/v1/rules",
            "analysis": "/api/v1/analysis",
            "remediation": "/api/v1/remediation",
            "notifications": "/api/v1/notifications",
            "nlp": "/api/v1/nlp",
            "websocket": "/ws",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


# Customize OpenAPI schema
def get_openapi() -> dict[str, Any]:
    """Get customized OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi as fastapi_get_openapi

    openapi_schema = fastapi_get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )

    # Apply custom modifications
    openapi_schema = custom_openapi_schema(openapi_schema)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Override the default OpenAPI function
setattr(app, "openapi", get_openapi)


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the server
    uvicorn.run(
        "server:app", host="127.0.0.1", port=8000, reload=True, log_level="info"
    )

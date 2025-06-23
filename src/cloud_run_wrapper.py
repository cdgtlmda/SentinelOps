#!/usr/bin/env python3
"""
Cloud Run wrapper for SentinelOps agents.
Provides HTTP endpoints for health checks and Pub/Sub push subscriptions.
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="SentinelOps Agent")

# Global agent instance
agent: Optional[Any] = None
agent_type = os.environ.get("AGENT_TYPE", "unknown")

# Metrics tracking
metrics_data = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_failed": 0,
    "messages_processed": 0,
    "health_checks": 0,
    "errors_total": 0,
    "last_message_timestamp": 0,
    "uptime_seconds": 0
}
startup_time = time.time()
project_id = os.environ.get("PROJECT_ID", "your-gcp-project-id")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the agent on startup"""
    global agent  # pylint: disable=global-statement

    # Create a basic config
    config = {
        "project_id": project_id,
        "agent_type": agent_type
    }

    try:
        if agent_type == "detection":
            from src.detection_agent.adk_agent import DetectionAgent

            agent = DetectionAgent(config)
        elif agent_type == "analysis":
            from src.analysis_agent.adk_agent import AnalysisAgent

            agent = AnalysisAgent(config)
        elif agent_type == "remediation":
            from src.remediation_agent.adk_agent import RemediationAgent

            agent = RemediationAgent(config)
        elif agent_type == "communication":
            from src.communication_agent.adk_agent import CommunicationAgent

            agent = CommunicationAgent(config)
        elif agent_type == "orchestrator":
            from src.orchestrator_agent.adk_agent import OrchestratorAgent

            agent = OrchestratorAgent(config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        logger.info("Initialized %s agent for project %s", agent_type, project_id)

        # Start the agent's main loop in the background
        asyncio.create_task(run_agent())

    except Exception as e:
        logger.error("Failed to initialize agent: %s", e)
        raise


async def run_agent() -> None:
    """Run the agent's main loop"""
    try:
        if agent and hasattr(agent, "run"):
            await agent.run()
        else:
            # For agents without async run, create a simple loop
            while True:
                await asyncio.sleep(30)  # Keep alive
    except Exception as e:
        logger.error("Agent run error: %s", e)


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "SentinelOps",
        "agent": agent_type,
        "status": "running",
        "project": project_id,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for Cloud Run"""
    metrics_data["health_checks"] += 1
    return {"status": "healthy", "agent": agent_type}


@app.get("/ready")
async def ready() -> dict[str, Any]:
    """Readiness check endpoint"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {"status": "ready", "agent": agent_type}


@app.post("/pubsub/push")
async def pubsub_push(request: Request) -> Response:
    """Handle Pub/Sub push messages"""
    metrics_data["requests_total"] += 1
    try:
        # Parse Pub/Sub message
        envelope = await request.json()

        if not envelope:
            metrics_data["requests_failed"] += 1
            raise HTTPException(status_code=400, detail="Empty request")

        # Extract the Pub/Sub message
        message = envelope.get("message", {})

        if not message:
            metrics_data["requests_failed"] += 1
            raise HTTPException(status_code=400, detail="No message in request")

        # Decode message data
        import base64

        data = base64.b64decode(message.get("data", "")).decode("utf-8")

        # Parse JSON data
        try:
            message_data = json.loads(data)
        except json.JSONDecodeError:
            message_data = {"raw_data": data}

        # Get message attributes
        attributes = message.get("attributes", {})

        logger.info("Received Pub/Sub message: %s", message_data)

        # Process message based on agent type
        if agent:
            if hasattr(agent, "handle_message"):
                await agent.handle_message(message_data, attributes)
                metrics_data["messages_processed"] += 1
                metrics_data["last_message_timestamp"] = int(time.time())
            else:
                logger.warning("Agent %s has no handle_message method", agent_type)

        metrics_data["requests_success"] += 1
        # Acknowledge message
        return Response(status_code=204)

    except Exception as e:
        metrics_data["requests_failed"] += 1
        metrics_data["errors_total"] += 1
        logger.error("Error processing Pub/Sub message: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/trigger/{action}")
async def trigger_action(action: str, request: Request) -> JSONResponse:
    """Manually trigger agent actions (for testing)"""
    try:
        data = await request.json()

        if agent and hasattr(agent, f"handle_{action}"):
            handler = getattr(agent, f"handle_{action}")
            result = await handler(data)
            return JSONResponse(content={"status": "success", "result": result})
        else:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Action {action} not found"},
            )
    except Exception as e:
        logger.error("Error triggering action %s: %s", action, e)
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint"""
    # Calculate uptime
    metrics_data["uptime_seconds"] = int(time.time() - startup_time)

    # Build Prometheus metrics format
    metrics_lines = []

    # Agent up metric
    metrics_lines.append("# HELP sentinelops_agent_up Agent status (1 = up, 0 = down)")
    metrics_lines.append("# TYPE sentinelops_agent_up gauge")
    metrics_lines.append(f'sentinelops_agent_up{{agent_type="{agent_type}"}} 1')
    metrics_lines.append("")

    # Request metrics
    metrics_lines.append("# HELP sentinelops_requests_total Total number of requests")
    metrics_lines.append("# TYPE sentinelops_requests_total counter")
    metrics_lines.append(
        f'sentinelops_requests_total{{agent_type="{agent_type}"}} '
        f'{metrics_data["requests_total"]}'
    )
    metrics_lines.append("")

    # Success/failure metrics
    metrics_lines.append("# HELP sentinelops_requests_success Total successful requests")
    metrics_lines.append("# TYPE sentinelops_requests_success counter")
    metrics_lines.append(
        f'sentinelops_requests_success{{agent_type="{agent_type}"}} '
        f'{metrics_data["requests_success"]}'
    )
    metrics_lines.append("")

    metrics_lines.append("# HELP sentinelops_requests_failed Total failed requests")
    metrics_lines.append("# TYPE sentinelops_requests_failed counter")
    metrics_lines.append(
        f'sentinelops_requests_failed{{agent_type="{agent_type}"}} '
        f'{metrics_data["requests_failed"]}'
    )
    metrics_lines.append("")

    # Message processing metrics
    metrics_lines.append("# HELP sentinelops_messages_processed Total messages processed")
    metrics_lines.append("# TYPE sentinelops_messages_processed counter")
    metrics_lines.append(
        f'sentinelops_messages_processed{{agent_type="{agent_type}"}} '
        f'{metrics_data["messages_processed"]}'
    )
    metrics_lines.append("")

    # Health check metrics
    metrics_lines.append("# HELP sentinelops_health_checks_total Total health checks")
    metrics_lines.append("# TYPE sentinelops_health_checks_total counter")
    metrics_lines.append(
        f'sentinelops_health_checks_total{{agent_type="{agent_type}"}} '
        f'{metrics_data["health_checks"]}'
    )
    metrics_lines.append("")

    # Error metrics
    metrics_lines.append("# HELP sentinelops_errors_total Total errors encountered")
    metrics_lines.append("# TYPE sentinelops_errors_total counter")
    metrics_lines.append(
        f'sentinelops_errors_total{{agent_type="{agent_type}"}} '
        f'{metrics_data["errors_total"]}'
    )
    metrics_lines.append("")

    # Uptime metric
    metrics_lines.append("# HELP sentinelops_uptime_seconds Agent uptime in seconds")
    metrics_lines.append("# TYPE sentinelops_uptime_seconds gauge")
    metrics_lines.append(
        f'sentinelops_uptime_seconds{{agent_type="{agent_type}"}} '
        f'{metrics_data["uptime_seconds"]}'
    )
    metrics_lines.append("")

    # Last message timestamp
    metrics_lines.append(
        "# HELP sentinelops_last_message_timestamp Timestamp of last processed message"
    )
    metrics_lines.append("# TYPE sentinelops_last_message_timestamp gauge")
    metrics_lines.append(
        f'sentinelops_last_message_timestamp{{agent_type="{agent_type}"}} '
        f'{metrics_data["last_message_timestamp"]}'
    )

    return Response(
        content="\n".join(metrics_lines) + "\n",
        media_type="text/plain",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")  # nosec B104 - Cloud Run requires binding to 0.0.0.0
    uvicorn.run(app, host=host, port=port)

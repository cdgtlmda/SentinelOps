#!/usr/bin/env python3
"""
Cloud Run wrapper for SentinelOps agents.
Provides HTTP endpoints and proper agent integration for Cloud Run deployment.
"""

import asyncio
import base64
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import FrameType
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SentinelOps Agent",
    description="Cloud Run wrapper for SentinelOps agents",
    version="1.0.0",
)

# Global variables
AGENT = None
AGENT_TASK = None
agent_type = os.environ.get("AGENT_TYPE", "detection")
project_id = os.environ.get("PROJECT_ID", "your-gcp-project-id")
shutdown_event = asyncio.Event()

# Message queue for async processing
message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1000)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the agent on startup"""
    global AGENT, AGENT_TASK  # pylint: disable=global-statement

    try:
        logger.info("Starting %s agent for project %s", agent_type, project_id)

        # Import and initialize the appropriate agent using factory
        from src.agent_factory import create_agent

        AGENT = create_agent(agent_type, project_id)

        logger.info("Successfully initialized %s agent", agent_type)

        # Start the agent's background processing
        AGENT_TASK = asyncio.create_task(run_agent_with_error_handling())

        # Start message processor
        asyncio.create_task(process_messages())

    except Exception as e:
        logger.error("Failed to initialize agent: %s", e, exc_info=True)
        # Don't raise here - let the health endpoint report unhealthy


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Gracefully shutdown the agent"""
    logger.info("Shutting down agent...")
    shutdown_event.set()

    if AGENT_TASK:
        AGENT_TASK.cancel()
        try:
            await AGENT_TASK
        except asyncio.CancelledError:
            pass

    logger.info("Agent shutdown complete")


async def run_agent_with_error_handling() -> None:
    """Run the agent with error handling and restart logic"""
    while not shutdown_event.is_set():
        try:
            if AGENT and hasattr(AGENT, "run"):
                logger.info("Starting %s agent run loop", agent_type)
                await AGENT.run()
            else:
                # For agents without async run, just keep alive
                logger.info(
                    "%s agent doesn't have run method, keeping alive", agent_type
                )
                await shutdown_event.wait()
        except asyncio.CancelledError:
            logger.info("Agent task cancelled")
            break
        except Exception as e:
            logger.error("Agent error: %s", e, exc_info=True)
            # Wait before restart
            await asyncio.sleep(30)
            if not shutdown_event.is_set():
                logger.info("Restarting agent after error...")


async def process_messages() -> None:
    """Process messages from the queue"""
    while not shutdown_event.is_set():
        try:
            # Get message with timeout
            message = await asyncio.wait_for(message_queue.get(), timeout=5.0)

            logger.info(
                "Processing queued message: %s", message.get("message_id", "unknown")
            )

            # Process based on agent type
            if AGENT:
                if hasattr(AGENT, "handle_pubsub_message"):
                    await AGENT.handle_pubsub_message(message)
                elif hasattr(AGENT, "handle_message"):
                    await AGENT.handle_message(
                        message.get("data", {}), message.get("attributes", {})
                    )
                else:
                    logger.warning("Agent %s has no message handler", agent_type)

        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error("Error processing message: %s", e, exc_info=True)


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "SentinelOps",
        "agent": agent_type,
        "status": "running" if AGENT else "initializing",
        "project": project_id,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint for Cloud Run"""
    if AGENT is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return {
        "status": "healthy",
        "agent": agent_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
async def ready() -> Dict[str, Any]:
    """Readiness check endpoint"""
    if AGENT is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Check if agent has specific readiness method
    if hasattr(AGENT, "is_ready"):
        if not await AGENT.is_ready():
            raise HTTPException(status_code=503, detail="Agent not ready")

    return {"status": "ready", "agent": agent_type, "queue_size": message_queue.qsize()}


@app.post("/pubsub/push")
async def pubsub_push(request: Request) -> Response:
    """Handle Pub/Sub push messages"""
    try:
        # Parse Pub/Sub message
        envelope = await request.json()

        if not envelope:
            logger.warning("Empty Pub/Sub request")
            return Response(status_code=204)

        # Extract the Pub/Sub message
        message = envelope.get("message", {})

        if not message:
            logger.warning("No message in Pub/Sub request")
            return Response(status_code=204)

        # Decode message data
        data = base64.b64decode(message.get("data", "")).decode("utf-8")

        # Parse JSON data
        try:
            message_data = json.loads(data)
        except json.JSONDecodeError:
            message_data = {"raw_data": data}

        # Get message attributes
        attributes = message.get("attributes", {})
        message_id = message.get("messageId", "unknown")
        publish_time = message.get("publishTime")

        logger.info("Received Pub/Sub message %s for %s", message_id, agent_type)

        # Queue message for async processing
        try:
            message_queue.put_nowait(
                {
                    "data": message_data,
                    "attributes": attributes,
                    "message_id": message_id,
                    "publish_time": publish_time,
                }
            )
        except asyncio.QueueFull as exc:
            logger.error("Message queue is full, dropping message")
            raise HTTPException(status_code=503, detail="Message queue full") from exc

        # Acknowledge message immediately
        return Response(status_code=204)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing Pub/Sub message: %s", e, exc_info=True)
        # Return 204 to acknowledge and prevent redelivery of bad messages
        return Response(status_code=204)


@app.post("/trigger/{action}")
async def trigger_action(action: str, request: Request) -> JSONResponse:
    """Manually trigger agent actions (for testing)"""
    if AGENT is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        data = (
            await request.json()
            if request.headers.get("content-type") == "application/json"
            else {}
        )

        # Check for specific action handlers
        if hasattr(AGENT, f"handle_{action}"):
            handler = getattr(AGENT, f"handle_{action}")
            result = (
                await handler(data)
                if asyncio.iscoroutinefunction(handler)
                else handler(data)
            )
            return JSONResponse(content={"status": "success", "result": result})
        elif hasattr(AGENT, action):
            method = getattr(AGENT, action)
            result = await method() if asyncio.iscoroutinefunction(method) else method()
            return JSONResponse(content={"status": "success", "result": result})
        else:
            raise HTTPException(status_code=404, detail=f"Action {action} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error triggering action %s: %s", action, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/status")
async def status() -> Dict[str, Any]:
    """Detailed status endpoint"""
    status_info = {
        "agent_type": agent_type,
        "project_id": project_id,
        "agent_initialized": AGENT is not None,
        "queue_size": message_queue.qsize(),
        "queue_max_size": message_queue.maxsize,
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "port": os.environ.get("PORT", "8080"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Add agent-specific status if available
    if AGENT and hasattr(AGENT, "get_status"):
        try:
            agent_status = (
                await AGENT.get_status()
                if asyncio.iscoroutinefunction(AGENT.get_status)
                else AGENT.get_status()
            )
            status_info["agent_status"] = agent_status
        except Exception as e:
            logger.error("Error getting agent status: %s", e)
            status_info["agent_status"] = {"error": str(e)}

    return status_info


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint"""
    metrics_lines = [
        "# HELP sentinelops_agent_up Agent status",
        "# TYPE sentinelops_agent_up gauge",
        f'sentinelops_agent_up{{agent_type="{agent_type}",project_id="{project_id}"}} '
        f"{1 if AGENT else 0}",
        "",
        "# HELP sentinelops_message_queue_size Number of messages in queue",
        "# TYPE sentinelops_message_queue_size gauge",
        f'sentinelops_message_queue_size{{agent_type="{agent_type}"}} {message_queue.qsize()}',
        "",
        "# HELP sentinelops_message_queue_capacity Queue capacity",
        "# TYPE sentinelops_message_queue_capacity gauge",
        f'sentinelops_message_queue_capacity{{agent_type="{agent_type}"}} {message_queue.maxsize}',
    ]

    # Add agent-specific metrics if available
    if AGENT and hasattr(AGENT, "get_metrics"):
        try:
            agent_metrics = AGENT.get_metrics()
            for metric_name, metric_value in agent_metrics.items():
                metrics_lines.extend(
                    [
                        "",
                        f"# HELP sentinelops_{metric_name} {metric_name}",
                        f"# TYPE sentinelops_{metric_name} gauge",
                        f'sentinelops_{metric_name}{{agent_type="{agent_type}"}} {metric_value}',
                    ]
                )
        except Exception as e:
            logger.error("Error getting agent metrics: %s", e)

    return Response(content="\n".join(metrics_lines), media_type="text/plain")


def handle_signal(signum: int, _frame: Optional[FrameType]) -> None:
    """Handle shutdown signals"""
    logger.info("Received signal %d", signum)
    shutdown_event.set()


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Get port from environment
    port = int(os.environ.get("PORT", 8080))

    logger.info("Starting %s agent HTTP server on port %d", agent_type, port)

    # Run the server
    host = os.environ.get("HOST", "0.0.0.0")  # Cloud Run requires 0.0.0.0  # nosec B104
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)

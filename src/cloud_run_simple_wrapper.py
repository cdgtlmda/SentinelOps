#!/usr/bin/env python3
"""
Simple Cloud Run wrapper for individual agents
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request, Response

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="SentinelOps Agent")

# Global state
AGENT = None
agent_type = os.environ.get("AGENT_TYPE", "detection")
project_id = os.environ.get("PROJECT_ID", "your-gcp-project-id")
message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1000)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the agent on startup"""
    logger.info("Starting %s agent for project %s", agent_type, project_id)

    # For now, just log that we're ready
    # In production, initialize the actual agent here
    logger.info("%s agent ready (simplified mode)", agent_type)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "service": "SentinelOps",
        "agent": agent_type,
        "status": "running",
        "project": project_id,
        "mode": "simplified",
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "agent": agent_type}


@app.get("/ready")
async def ready() -> Dict[str, str]:
    """Readiness check endpoint"""
    return {"status": "ready", "agent": agent_type}


@app.get("/status")
async def status() -> Dict[str, Any]:
    """Detailed status endpoint"""
    return {
        "agent_type": agent_type,
        "project_id": project_id,
        "agent_initialized": True,
        "queue_size": message_queue.qsize(),
        "queue_max_size": 1000,
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "port": os.environ.get("PORT", "8080"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/pubsub/push")
async def pubsub_push(request: Request) -> Response:
    """Handle Pub/Sub push messages"""
    try:
        # Parse Pub/Sub message
        envelope = await request.json()

        if not envelope:
            return Response(status_code=400, content="Empty request")

        # Extract the Pub/Sub message
        message = envelope.get("message", {})

        if not message:
            return Response(status_code=400, content="No message in request")

        # Decode message data
        import base64

        data = base64.b64decode(message.get("data", "")).decode("utf-8")

        # Parse JSON data
        try:
            message_data = json.loads(data)
        except json.JSONDecodeError:
            message_data = {"raw_data": data}

        # Log the message
        logger.info("Received Pub/Sub message: %s", message_data)

        # Queue for processing
        try:
            message_queue.put_nowait(
                {
                    "data": message_data,
                    "attributes": message.get("attributes", {}),
                    "message_id": message.get("messageId"),
                    "publish_time": message.get("publishTime"),
                }
            )
        except asyncio.QueueFull:
            logger.warning("Message queue full, dropping message")
            return Response(status_code=503, content="Queue full")

        # Acknowledge message
        return Response(status_code=204)

    except Exception as e:
        logger.error("Error processing Pub/Sub message: %s", e)
        return Response(status_code=500, content=str(e))


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint"""
    queue_size = message_queue.qsize()
    metrics_text = f"""# HELP sentinelops_agent_up Agent status
# TYPE sentinelops_agent_up gauge
sentinelops_agent_up 1

# HELP sentinelops_message_queue_size Number of messages in queue
# TYPE sentinelops_message_queue_size gauge
sentinelops_message_queue_size {queue_size}

# HELP sentinelops_agent_info Agent information
# TYPE sentinelops_agent_info gauge
sentinelops_agent_info{{agent_type="{agent_type}",project_id="{project_id}"}} 1
"""
    return Response(content=metrics_text, media_type="text/plain")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starting %s agent on port %d", agent_type, port)
    host = os.environ.get(
        "HOST", "0.0.0.0"
    )  # nosec B104 - Cloud Run requires binding to 0.0.0.0
    uvicorn.run(app, host=host, port=port)

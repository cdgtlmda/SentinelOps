#!/usr/bin/env python3
"""
Minimal Cloud Run wrapper for SentinelOps agents.
Provides basic HTTP endpoints without importing agent modules.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="SentinelOps Agent")

# Agent configuration
agent_type = os.environ.get(
    "AGENT_TYPE", sys.argv[1] if len(sys.argv) > 1 else "unknown"
)
project_id = os.environ.get("PROJECT_ID", "your-gcp-project-id")

# Simple in-memory queue for messages
message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize on startup"""
    logger.info("Starting %s agent wrapper for project %s", agent_type, project_id)
    # Start message processor in background
    asyncio.create_task(process_messages())


async def process_messages() -> None:
    """Process messages from the queue"""
    while True:
        try:
            message = await message_queue.get()
            logger.info("Processing message: %s", message)

            # Process message based on type
            message_type = message.get('type', 'unknown')

            if message_type == 'alert':
                # Process alert messages
                severity = message.get('severity', 'info')
                description = message.get('description', '')
                logger.info("Processing alert: %s - %s", severity, description)
                # In production, this would trigger alert handling

            elif message_type == 'metric':
                # Process metric messages
                metric_name = message.get('name', '')
                value = message.get('value', 0)
                logger.info("Processing metric: %s = %s", metric_name, value)
                # In production, this would store metrics

            elif message_type == 'log':
                # Process log messages
                log_level = message.get('level', 'info')
                log_message = message.get('message', '')
                logger.info("Processing log: [%s] %s", log_level, log_message)
                # In production, this would route logs appropriately

            else:
                logger.warning("Unknown message type: %s", message_type)

            # Mark message as processed
            message_queue.task_done()

        except Exception as e:
            logger.error("Error processing message: %s", e)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "service": "SentinelOps",
        "agent": agent_type,
        "status": "running",
        "project": project_id,
        "version": "1.0.0",
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "agent": agent_type}


@app.get("/ready")
async def ready() -> Dict[str, str]:
    """Readiness check endpoint"""
    return {"status": "ready", "agent": agent_type}


@app.post("/pubsub/push")
async def pubsub_push(request: Request) -> Response:
    """Handle Pub/Sub push messages"""
    try:
        # Parse Pub/Sub message
        envelope = await request.json()

        if not envelope:
            raise HTTPException(status_code=400, detail="Empty request")

        # Extract the Pub/Sub message
        message = envelope.get("message", {})

        if not message:
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

        logger.info("Received Pub/Sub message for %s: %s", agent_type, message_data)

        # Queue message for processing
        await message_queue.put(
            {
                "data": message_data,
                "attributes": attributes,
                "message_id": message.get("messageId"),
                "publish_time": message.get("publishTime"),
            }
        )

        # Acknowledge message immediately
        return Response(status_code=204)

    except Exception as e:
        logger.error("Error processing Pub/Sub message: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


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


@app.get("/status")
async def status() -> Dict[str, Any]:
    """Detailed status endpoint"""
    return {
        "agent_type": agent_type,
        "project_id": project_id,
        "queue_size": message_queue.qsize(),
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "port": os.environ.get("PORT", "8080"),
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starting %s agent on port %d", agent_type, port)
    host = os.environ.get("HOST", "0.0.0.0")  # nosec B104 - Cloud Run requires binding to 0.0.0.0
    uvicorn.run(app, host=host, port=port)

"""WebSocket support for real-time updates in SentinelOps."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
from uuid import uuid4

from fastapi import Depends, Query, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from .auth import get_auth_backend

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self) -> None:
        # Active connections indexed by client ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Subscriptions: event_type -> set of client IDs
        self.subscriptions: Dict[str, Set[str]] = {}
        # Client metadata
        self.client_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_metadata[client_id] = {
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "subscriptions": set(),
        }
        logger.info("WebSocket client %s connected", client_id)

    def disconnect(self, client_id: str) -> None:
        """Handle client disconnection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from all subscriptions
        for _, subscribers in self.subscriptions.items():
            subscribers.discard(client_id)

        # Clean up metadata
        if client_id in self.client_metadata:
            del self.client_metadata[client_id]

        logger.info("WebSocket client %s disconnected", client_id)

    async def subscribe(self, client_id: str, event_type: str) -> bool:
        """Subscribe a client to an event type."""
        if client_id not in self.active_connections:
            return False

        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = set()

        self.subscriptions[event_type].add(client_id)
        self.client_metadata[client_id]["subscriptions"].add(event_type)

        logger.info("Client %s subscribed to %s", client_id, event_type)
        return True

    async def unsubscribe(self, client_id: str, event_type: str) -> bool:
        """Unsubscribe a client from an event type."""
        if event_type in self.subscriptions:
            self.subscriptions[event_type].discard(client_id)

        if client_id in self.client_metadata:
            self.client_metadata[client_id]["subscriptions"].discard(event_type)

        logger.info("Client %s unsubscribed from %s", client_id, event_type)
        return True

    async def send_personal_message(
        self, message: Dict[str, Any], client_id: str
    ) -> None:
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    logger.warning(
                        "WebSocket for client %s is not connected", client_id
                    )
                    self.disconnect(client_id)
            except (ConnectionError, OSError) as e:
                logger.error("Error sending message to client %s: %s", client_id, e)
                self.disconnect(client_id)

    async def broadcast(self, message: Dict[str, Any], event_type: str) -> None:
        """Broadcast a message to all subscribers of an event type."""
        if event_type not in self.subscriptions:
            return

        # Get list of subscribers to avoid modification during iteration
        subscribers = list(self.subscriptions[event_type])
        disconnected_clients = []

        for client_id in subscribers:
            if client_id in self.active_connections:
                try:
                    await self.send_personal_message(message, client_id)
                except (ConnectionError, OSError) as e:
                    logger.error("Failed to send to client %s: %s", client_id, e)
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about active connections."""
        return {
            "total_connections": len(self.active_connections),
            "subscriptions": {
                event_type: len(subscribers)
                for event_type, subscribers in self.subscriptions.items()
            },
            "clients": [
                {
                    "client_id": client_id,
                    "connected_at": metadata.get("connected_at"),
                    "subscriptions": list(metadata.get("subscriptions", [])),
                }
                for client_id, metadata in self.client_metadata.items()
            ],
        }


# Global connection manager instance
manager = ConnectionManager()


async def get_websocket_auth(
    websocket: WebSocket, token: Optional[str] = Query(None)
) -> Optional[Dict[str, Any]]:
    """Authenticate WebSocket connection."""
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return None

    auth_backend = get_auth_backend()
    token_data = auth_backend.verify_token(token)

    if not token_data:
        await websocket.close(code=1008, reason="Invalid authentication token")
        return None

    return {"sub": token_data.sub, "scopes": token_data.scopes}


async def websocket_endpoint(  # noqa: C901
    websocket: WebSocket,
    client_id: Optional[str] = None,
    auth: Optional[Dict[str, Any]] = Depends(get_websocket_auth),
) -> None:
    """WebSocket endpoint for real-time updates."""
    if not auth:
        return

    # Generate client ID if not provided
    if not client_id:
        client_id = f"ws-{uuid4()}"

    await manager.connect(websocket, client_id)

    # Send welcome message
    await manager.send_personal_message(
        {
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "available_events": [
                "incident.detected",
                "incident.updated",
                "incident.resolved",
                "analysis.started",
                "analysis.completed",
                "remediation.started",
                "remediation.completed",
                "remediation.failed",
                "system.status",
            ],
        },
        client_id,
    )

    try:
        while True:
            # Receive and process messages
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "subscribe":
                event_type = data.get("event_type")
                if event_type:
                    success = await manager.subscribe(client_id, event_type)
                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "event_type": event_type,
                            "status": "subscribed" if success else "failed",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        client_id,
                    )

            elif message_type == "unsubscribe":
                event_type = data.get("event_type")
                if event_type:
                    success = await manager.unsubscribe(client_id, event_type)
                    await manager.send_personal_message(
                        {
                            "type": "subscription",
                            "event_type": event_type,
                            "status": "unsubscribed" if success else "failed",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        client_id,
                    )

            elif message_type == "ping":
                # Respond to ping with pong
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    client_id,
                )

            else:
                # Unknown message type
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    client_id,
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info("WebSocket client %s disconnected normally", client_id)
    except (ConnectionError, OSError, ValueError) as e:
        logger.error("WebSocket error for client %s: %s", client_id, e)
        manager.disconnect(client_id)


# Event broadcasting functions
async def broadcast_incident_event(
    incident_id: str, event_type: str, details: Dict[str, Any]
) -> None:
    """Broadcast an incident-related event."""
    message = {
        "type": "event",
        "event_type": event_type,
        "incident_id": incident_id,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(message, event_type)


async def broadcast_analysis_event(
    incident_id: str, analysis_id: str, event_type: str, details: Dict[str, Any]
) -> None:
    """Broadcast an analysis-related event."""
    message = {
        "type": "event",
        "event_type": event_type,
        "incident_id": incident_id,
        "analysis_id": analysis_id,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(message, event_type)


async def broadcast_remediation_event(
    execution_id: str, event_type: str, details: Dict[str, Any]
) -> None:
    """Broadcast a remediation-related event."""
    message = {
        "type": "event",
        "event_type": event_type,
        "execution_id": execution_id,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(message, event_type)


async def broadcast_system_status(status: str, details: Dict[str, Any]) -> None:
    """Broadcast system status update."""
    message = {
        "type": "event",
        "event_type": "system.status",
        "status": status,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(message, "system.status")


# API endpoint to get WebSocket status
async def get_websocket_status() -> Dict[str, Any]:
    """Get current WebSocket connection status."""
    return manager.get_connection_info()

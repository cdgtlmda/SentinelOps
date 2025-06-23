# WebSocket API Reference

**Last Updated**: June 11, 2025

## Overview

SentinelOps provides a WebSocket API for real-time event streaming and bidirectional communication. This enables instant notifications about security incidents, analysis results, and system status changes.

**WebSocket Endpoint**: `wss://api.sentinelops.yourdomain.com/ws`

## Connection

### Authentication

WebSocket connections must be authenticated using one of these methods:

#### 1. JWT Token (Recommended)
```javascript
const ws = new WebSocket('wss://api.sentinelops.yourdomain.com/ws', {
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  }
});
```

#### 2. API Key via Query Parameter
```javascript
const ws = new WebSocket('wss://api.sentinelops.yourdomain.com/ws?api_key=YOUR_API_KEY');
```

#### 3. Authentication After Connection
```javascript
const ws = new WebSocket('wss://api.sentinelops.yourdomain.com/ws');

ws.on('open', () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'YOUR_JWT_TOKEN'
  }));
});
```

### Connection Lifecycle

1. **Handshake**: Client initiates WebSocket connection
2. **Authentication**: Server validates credentials
3. **Ready**: Server sends `connection.ready` event
4. **Subscription**: Client subscribes to events
5. **Streaming**: Real-time event delivery
6. **Heartbeat**: Periodic ping/pong to maintain connection
7. **Disconnection**: Clean closure or timeout

## Message Format

All messages use JSON format:

```typescript
interface WebSocketMessage {
  id?: string;          // Message ID for request/response correlation
  type: string;         // Message type
  event?: string;       // Event name (for event messages)
  data?: any;          // Message payload
  timestamp: string;    // ISO 8601 timestamp
  error?: {            // Error details (for error messages)
    code: string;
    message: string;
  };
}
```

## Client-to-Server Messages

### Authentication
```json
{
  "type": "auth",
  "token": "YOUR_JWT_TOKEN_OR_API_KEY"
}
```

### Subscribe to Events
```json
{
  "id": "sub_123",
  "type": "subscribe",
  "data": {
    "events": [
      "incident.*",
      "analysis.completed",
      "remediation.*"
    ],
    "filters": {
      "severity": ["CRITICAL", "HIGH"],
      "projects": ["my-project-1", "my-project-2"]
    }
  }
}
```

### Unsubscribe from Events
```json
{
  "id": "unsub_456",
  "type": "unsubscribe",
  "data": {
    "events": ["incident.created"]
  }
}
```

### Request Incident Updates
```json
{
  "id": "req_789",
  "type": "request",
  "data": {
    "action": "get_incident",
    "incident_id": "inc_123456"
  }
}
```

### Heartbeat (Ping)
```json
{
  "type": "ping"
}
```

## Server-to-Client Messages

### Connection Ready
```json
{
  "type": "connection.ready",
  "data": {
    "connection_id": "conn_abc123",
    "server_time": "2025-06-11T10:00:00Z",
    "capabilities": ["subscribe", "request", "command"]
  }
}
```

### Subscription Confirmation
```json
{
  "id": "sub_123",
  "type": "subscription.confirmed",
  "data": {
    "subscribed_events": ["incident.*", "analysis.completed"],
    "active_filters": {
      "severity": ["CRITICAL", "HIGH"]
    }
  }
}
```

### Event Messages

#### Incident Created
```json
{
  "type": "event",
  "event": "incident.created",
  "data": {
    "incident": {
      "id": "inc_123456",
      "incident_id": "INC-2025-001",
      "type": "suspicious_login",
      "severity": "HIGH",
      "status": "OPEN",
      "affected_resources": ["user@example.com"],
      "created_at": "2025-06-11T10:00:00Z"
    }
  },
  "timestamp": "2025-06-11T10:00:01Z"
}
```

#### Incident Updated
```json
{
  "type": "event",
  "event": "incident.updated",
  "data": {
    "incident_id": "inc_123456",
    "changes": {
      "status": {
        "old": "OPEN",
        "new": "INVESTIGATING"
      },
      "assigned_to": {
        "old": null,
        "new": "security-analyst-1"
      }
    },
    "updated_by": "orchestrator-agent",
    "updated_at": "2025-06-11T10:05:00Z"
  },
  "timestamp": "2025-06-11T10:05:01Z"
}
```

#### Analysis Completed
```json
{
  "type": "event",
  "event": "analysis.completed",
  "data": {
    "analysis_id": "ana_789012",
    "incident_id": "inc_123456",
    "results": {
      "root_cause": "Credential stuffing attack",
      "confidence": 0.89,
      "recommendations": [
        {
          "action": "block_ip",
          "priority": "HIGH"
        }
      ]
    },
    "duration_ms": 3500
  },
  "timestamp": "2025-06-11T10:08:00Z"
}
```

#### Remediation Started
```json
{
  "type": "event",
  "event": "remediation.started",
  "data": {
    "action_id": "rem_345678",
    "incident_id": "inc_123456",
    "action": "block_ip",
    "parameters": {
      "ip_addresses": ["192.168.1.1"],
      "duration": 86400
    },
    "initiated_by": "remediation-agent"
  },
  "timestamp": "2025-06-11T10:10:00Z"
}
```

#### System Status
```json
{
  "type": "event",
  "event": "system.status",
  "data": {
    "agents": {
      "detection": {
        "status": "active",
        "last_heartbeat": "2025-06-11T10:14:30Z"
      },
      "analysis": {
        "status": "active",
        "queue_size": 3
      }
    },
    "health": "healthy"
  },
  "timestamp": "2025-06-11T10:15:00Z"
}
```

### Error Messages
```json
{
  "id": "req_789",
  "type": "error",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Unknown event type: invalid.event"
  },
  "timestamp": "2025-06-11T10:00:00Z"
}
```

### Heartbeat Response (Pong)
```json
{
  "type": "pong",
  "timestamp": "2025-06-11T10:00:00Z"
}
```

## Event Types

### Incident Events
- `incident.created` - New incident detected
- `incident.updated` - Incident details changed
- `incident.assigned` - Incident assigned to user/team
- `incident.resolved` - Incident marked as resolved
- `incident.reopened` - Previously resolved incident reopened
- `incident.merged` - Incidents merged together

### Analysis Events
- `analysis.started` - AI analysis initiated
- `analysis.progress` - Analysis progress update
- `analysis.completed` - Analysis finished
- `analysis.failed` - Analysis encountered error

### Remediation Events
- `remediation.started` - Remediation action initiated
- `remediation.progress` - Remediation progress update
- `remediation.completed` - Remediation successfully completed
- `remediation.failed` - Remediation failed
- `remediation.approval_required` - Action needs approval
- `remediation.approved` - Action approved
- `remediation.rejected` - Action rejected
- `remediation.rolled_back` - Action rolled back

### Rule Events
- `rule.triggered` - Detection rule matched
- `rule.created` - New rule created
- `rule.updated` - Rule modified
- `rule.enabled` - Rule activated
- `rule.disabled` - Rule deactivated
- `rule.deleted` - Rule removed

### System Events
- `system.status` - Periodic system health update
- `system.alert` - System-level alert
- `system.maintenance` - Maintenance notification
- `agent.status_change` - Agent status changed
- `agent.error` - Agent encountered error

## Filtering

Subscribe to specific events with filters:

```json
{
  "type": "subscribe",
  "data": {
    "events": ["incident.*"],
    "filters": {
      "severity": ["CRITICAL", "HIGH"],      // Only high severity
      "type": ["ddos_attack", "intrusion"], // Specific incident types
      "projects": ["prod-*"],               // Wildcard matching
      "regions": ["us-central1"],           // Specific regions
      "time_window": {                      // Recent events only
        "minutes": 60
      }
    }
  }
}
```

## Rate Limiting

WebSocket connections have the following limits:

| Limit Type | Value | Window |
|------------|-------|---------|
| Messages per connection | 100 | 1 minute |
| Subscriptions per connection | 50 | Total |
| Connections per user | 5 | Concurrent |

When rate limited, you'll receive:
```json
{
  "type": "error",
  "error": {
    "code": "RATE_LIMITED",
    "message": "Message rate limit exceeded",
    "retry_after": 60
  }
}
```

## Connection Management

### Heartbeat

Send periodic ping messages to keep connection alive:
```javascript
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000); // Every 30 seconds
```

### Automatic Reconnection

Example reconnection logic:
```javascript
class ResilientWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.options = options;
    this.reconnectInterval = options.reconnectInterval || 5000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
    this.reconnectAttempts = 0;
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('Connected');
      this.reconnectAttempts = 0;
      this.authenticate();
    };
    
    this.ws.onclose = (event) => {
      console.log('Disconnected:', event.code, event.reason);
      this.reconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onmessage = (event) => {
      this.handleMessage(JSON.parse(event.data));
    };
  }
  
  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connect(), this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
  
  authenticate() {
    this.send({
      type: 'auth',
      token: this.options.token
    });
  }
  
  send(data) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket not connected');
    }
  }
  
  handleMessage(message) {
    // Handle incoming messages
    console.log('Received:', message);
  }
}

// Usage
const ws = new ResilientWebSocket('wss://api.sentinelops.yourdomain.com/ws', {
  token: 'YOUR_TOKEN',
  reconnectInterval: 5000,
  maxReconnectAttempts: 10
});
```

## Error Handling

### Connection Errors

| Code | Description | Action |
|------|-------------|--------|
| 1000 | Normal closure | No action needed |
| 1001 | Going away | Reconnect |
| 1006 | Abnormal closure | Reconnect with backoff |
| 1008 | Policy violation | Check authentication |
| 1011 | Server error | Reconnect after delay |
| 4000 | Invalid authentication | Re-authenticate |
| 4001 | Token expired | Refresh token |
| 4002 | Insufficient permissions | Check permissions |
| 4003 | Rate limited | Reduce message frequency |

### Message Errors

```json
{
  "type": "error",
  "error": {
    "code": "INVALID_MESSAGE",
    "message": "Message type 'unknown' not recognized"
  }
}
```

Common error codes:
- `INVALID_MESSAGE` - Malformed message
- `INVALID_REQUEST` - Invalid request parameters
- `UNAUTHORIZED` - Not authenticated
- `FORBIDDEN` - Lack permissions
- `NOT_FOUND` - Resource not found
- `RATE_LIMITED` - Too many requests
- `INTERNAL_ERROR` - Server error

## Usage Examples

### JavaScript/Node.js

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('wss://api.sentinelops.yourdomain.com/ws', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
});

ws.on('open', () => {
  console.log('Connected to SentinelOps');
  
  // Subscribe to critical incidents
  ws.send(JSON.stringify({
    type: 'subscribe',
    data: {
      events: ['incident.*', 'remediation.*'],
      filters: {
        severity: ['CRITICAL', 'HIGH']
      }
    }
  }));
});

ws.on('message', (data) => {
  const message = JSON.parse(data);
  
  if (message.type === 'event') {
    console.log(`Event: ${message.event}`, message.data);
    
    // Handle specific events
    switch (message.event) {
      case 'incident.created':
        handleNewIncident(message.data.incident);
        break;
      case 'remediation.approval_required':
        notifyApprovers(message.data);
        break;
    }
  }
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error);
});

ws.on('close', (code, reason) => {
  console.log(`Disconnected: ${code} - ${reason}`);
  // Implement reconnection logic
});

// Heartbeat
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

### Python

```python
import asyncio
import json
import websockets

async def handle_sentinelops():
    uri = "wss://api.sentinelops.yourdomain.com/ws"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # Subscribe to events
        await websocket.send(json.dumps({
            "type": "subscribe",
            "data": {
                "events": ["incident.*", "analysis.*"],
                "filters": {
                    "severity": ["CRITICAL", "HIGH"]
                }
            }
        }))
        
        # Handle messages
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "event":
                print(f"Event: {data['event']}")
                await handle_event(data)
            elif data["type"] == "error":
                print(f"Error: {data['error']}")

async def handle_event(message):
    event = message["event"]
    data = message["data"]
    
    if event == "incident.created":
        print(f"New incident: {data['incident']['id']}")
    elif event == "analysis.completed":
        print(f"Analysis complete: {data['results']['root_cause']}")

# Run the client
asyncio.run(handle_sentinelops())
```

### Go

```go
package main

import (
    "encoding/json"
    "log"
    "net/http"
    "time"
    
    "github.com/gorilla/websocket"
)

type Message struct {
    ID        string      `json:"id,omitempty"`
    Type      string      `json:"type"`
    Event     string      `json:"event,omitempty"`
    Data      interface{} `json:"data,omitempty"`
    Timestamp string      `json:"timestamp,omitempty"`
}

func main() {
    headers := http.Header{}
    headers.Add("Authorization", "Bearer YOUR_TOKEN")
    
    c, _, err := websocket.DefaultDialer.Dial("wss://api.sentinelops.yourdomain.com/ws", headers)
    if err != nil {
        log.Fatal("dial:", err)
    }
    defer c.Close()
    
    // Subscribe to events
    subscribe := Message{
        Type: "subscribe",
        Data: map[string]interface{}{
            "events": []string{"incident.*", "remediation.*"},
            "filters": map[string]interface{}{
                "severity": []string{"CRITICAL", "HIGH"},
            },
        },
    }
    
    if err := c.WriteJSON(subscribe); err != nil {
        log.Fatal("subscribe:", err)
    }
    
    // Handle messages
    go func() {
        for {
            var msg Message
            err := c.ReadJSON(&msg)
            if err != nil {
                log.Println("read:", err)
                return
            }
            
            switch msg.Type {
            case "event":
                log.Printf("Event: %s - %v\n", msg.Event, msg.Data)
            case "error":
                log.Printf("Error: %v\n", msg.Data)
            }
        }
    }()
    
    // Heartbeat
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        if err := c.WriteJSON(Message{Type: "ping"}); err != nil {
            log.Println("ping:", err)
            return
        }
    }
}
```

## Best Practices

1. **Authentication**: Always authenticate before subscribing
2. **Heartbeat**: Implement heartbeat to detect connection issues
3. **Reconnection**: Build robust reconnection logic
4. **Error Handling**: Handle all error scenarios gracefully
5. **Filtering**: Use filters to reduce unnecessary traffic
6. **Rate Limiting**: Respect rate limits to avoid disconnection
7. **Message IDs**: Use message IDs for request/response correlation
8. **Logging**: Log all connection events for debugging

## Testing

Test WebSocket connection using wscat:

```bash
# Install wscat
npm install -g wscat

# Connect with authentication
wscat -c wss://api.sentinelops.yourdomain.com/ws \
  -H "Authorization: Bearer YOUR_TOKEN"

# After connection, send messages
> {"type": "subscribe", "data": {"events": ["incident.*"]}}
> {"type": "ping"}
```

## Related Documentation

- [API Reference](./api-reference.md)
- [Agent Communication API](../02-architecture/agent-communication-api.md)
- [Real-time Notifications Guide](../04-operations/real-time-notifications.md)
- [Authentication Guide](../03-deployment/authentication-guide.md)
# WebSocket Integration Documentation

## Overview

The SentinelOps frontend includes comprehensive WebSocket integration for real-time features, providing live updates across all system components with automatic reconnection, message queuing, and offline support.

## Architecture

### Core Components

1. **WebSocket Client** (`lib/websocket/websocket-client.ts`)
   - Manages WebSocket connections
   - Handles automatic reconnection with exponential backoff
   - Tracks connection state and metrics
   - Implements message queuing for offline scenarios

2. **Message Queue** (`lib/websocket/message-queue.ts`)
   - Priority-based message queuing
   - Persists messages to localStorage
   - Handles retry logic
   - Manages queue size limits

3. **WebSocket Context** (`context/websocket-context.tsx`)
   - Global WebSocket provider
   - Connection state management
   - Event subscription system
   - Metrics tracking

4. **WebSocket Hooks** (`hooks/use-websocket.ts`)
   - React hooks for WebSocket usage
   - Channel-specific hooks (incidents, agents, chat, etc.)
   - Automatic subscription management

## Features

### Real-time Updates
- Live incident updates (create, update, resolve, escalate)
- Agent status changes
- Chat messaging with delivery/read receipts
- Activity feed with system events
- Alert notifications

### Connection Management
- **Automatic Reconnection**: Exponential backoff strategy (1s → 30s max)
- **Connection States**: Connecting, Connected, Disconnected, Reconnecting, Error
- **Latency Monitoring**: Ping/pong mechanism every 30 seconds
- **Connection Quality**: Visual indicators with latency display

### Message Handling
- **Priority Levels**: Critical, High, Normal, Low
- **Offline Queue**: Messages persist in localStorage
- **Delivery Guarantees**: Retry logic with max attempts
- **Queue Management**: Size limits and overflow handling

### Security
- **Authentication**: Token-based authentication via query params
- **Channel Authorization**: Server-side channel access control
- **Message Validation**: Type-safe message handling

## Usage

### Basic WebSocket Hook

```typescript
import { useWebSocket } from '@/hooks/use-websocket';

function MyComponent() {
  const { connectionState, send, latency, isConnected } = useWebSocket({
    channel: ChannelType.INCIDENTS,
    onMessage: (message) => {
      console.log('Received:', message);
    },
    onConnect: () => console.log('Connected'),
    onError: (error) => console.error('Error:', error)
  });

  const sendMessage = () => {
    send({
      type: 'incident.update',
      channel: ChannelType.INCIDENTS,
      payload: { id: '123', status: 'resolved' }
    });
  };
}
```

### Channel-Specific Hooks

```typescript
// Incident updates
const { isConnected } = useIncidentUpdates((update) => {
  console.log('Incident update:', update);
});

// Agent status
const { isConnected } = useAgentStatus((status) => {
  console.log('Agent status:', status);
});

// Chat messages
const { sendMessage, isConnected } = useChatMessages('conv-1', (message) => {
  console.log('New message:', message);
});

// Activity feed
const { isConnected } = useActivityFeed((activity) => {
  console.log('Activity:', activity);
});
```

### Connection Status Component

```typescript
import { ConnectionStatus } from '@/components/realtime/connection-status';

// Compact view
<ConnectionStatus compact />

// Detailed view
<ConnectionStatus showDetails />
```

## Configuration

### Environment Variables

```env
# WebSocket server URL
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:3001

# Feature flags
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
NEXT_PUBLIC_ENABLE_OFFLINE_MODE=true
NEXT_PUBLIC_ENABLE_MESSAGE_QUEUE=true
```

### WebSocket Provider Options

```typescript
<WebSocketProvider
  url="ws://localhost:3001"
  autoConnect={true}
  debug={true}
>
  {children}
</WebSocketProvider>
```

### Connection Options

```typescript
{
  url: string;              // WebSocket server URL
  reconnect?: boolean;      // Enable auto-reconnection (default: true)
  reconnectInterval?: number; // Initial reconnect delay (default: 1000ms)
  maxReconnectInterval?: number; // Max reconnect delay (default: 30000ms)
  reconnectDecay?: number;  // Backoff multiplier (default: 1.5)
  maxReconnectAttempts?: number; // Max attempts (default: Infinity)
  timeout?: number;         // Connection timeout (default: 10000ms)
  debug?: boolean;          // Enable debug logging (default: false)
}
```

## Message Types

### WebSocket Message Format

```typescript
interface WebSocketMessage {
  id: string;
  type: string;
  channel: ChannelType;
  payload: any;
  timestamp: number;
  priority?: MessagePriority;
}
```

### Channel Types

- `incidents`: Incident-related updates
- `agents`: Agent status changes
- `chat`: Chat messages
- `alerts`: System alerts
- `activity`: Activity feed events
- `system`: System messages (ping/pong, subscribe/unsubscribe)

### Event Examples

#### Incident Update
```json
{
  "type": "incident.updated",
  "channel": "incidents",
  "payload": {
    "incidentId": "inc-123",
    "type": "updated",
    "data": {
      "status": "investigating",
      "assignedTo": "agent-456"
    }
  }
}
```

#### Agent Status
```json
{
  "type": "agent.status",
  "channel": "agents",
  "payload": {
    "agentId": "agent-123",
    "status": "online",
    "lastSeen": 1234567890
  }
}
```

#### Chat Message
```json
{
  "type": "chat.message",
  "channel": "chat",
  "payload": {
    "id": "msg-123",
    "conversationId": "conv-456",
    "senderId": "agent-789",
    "content": "Investigation update",
    "timestamp": 1234567890
  }
}
```

## Performance Considerations

### Message Queue Limits
- Maximum queue size: 1000 messages
- Low priority messages dropped first when full
- Critical messages always preserved

### Reconnection Strategy
- Initial delay: 1 second
- Maximum delay: 30 seconds
- Backoff multiplier: 1.5x
- Gives up after connection failure

### Battery Optimization
- Ping interval: 30 seconds (mobile-friendly)
- Message batching for bulk updates
- Connection pooling for multiple channels

## Testing

### Mock WebSocket Server

```javascript
// mock-ws-server.js
const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 3001 });

wss.on('connection', (ws) => {
  console.log('Client connected');

  // Send test incident update
  setTimeout(() => {
    ws.send(JSON.stringify({
      id: '123',
      type: 'incident.created',
      channel: 'incidents',
      payload: {
        incidentId: 'inc-999',
        type: 'created',
        data: {
          title: 'Test Incident',
          severity: 'high',
          status: 'new'
        }
      },
      timestamp: Date.now()
    }));
  }, 2000);

  ws.on('message', (data) => {
    const message = JSON.parse(data);
    console.log('Received:', message);
    
    // Echo back for testing
    if (message.type === 'ping') {
      ws.send(JSON.stringify({
        type: 'pong',
        channel: 'system',
        payload: message.payload,
        timestamp: Date.now()
      }));
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

console.log('WebSocket server running on ws://localhost:3001');
```

### Component Testing

```typescript
// Test connection status
render(
  <WebSocketProvider url="ws://localhost:3001">
    <ConnectionStatus showDetails />
  </WebSocketProvider>
);

// Test real-time updates
const { result } = renderHook(() => useIncidentUpdates(jest.fn()), {
  wrapper: WebSocketProvider
});

expect(result.current.isConnected).toBe(false);
// Simulate connection...
```

## Troubleshooting

### Common Issues

1. **Connection Fails**
   - Check WebSocket URL in environment variables
   - Verify server is running
   - Check for proxy/firewall issues

2. **Messages Not Delivered**
   - Check connection status
   - Verify channel subscriptions
   - Check message queue in localStorage

3. **High Latency**
   - Monitor connection quality indicator
   - Check network conditions
   - Consider reducing ping frequency

### Debug Mode

Enable debug logging:
```typescript
<WebSocketProvider debug={true}>
```

Check browser console for:
- Connection state changes
- Message send/receive logs
- Reconnection attempts
- Error details

## Demo

Visit `/realtime-demo` to see all real-time features in action:
- Live incident updates with visual feedback
- Agent status tracking
- Real-time chat with delivery status
- Activity feed with auto-scroll
- Connection status monitoring
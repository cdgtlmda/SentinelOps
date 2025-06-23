export enum ConnectionState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  RECONNECTING = 'RECONNECTING',
  ERROR = 'ERROR'
}

export enum MessagePriority {
  LOW = 0,
  NORMAL = 1,
  HIGH = 2,
  CRITICAL = 3
}

export enum ChannelType {
  INCIDENTS = 'incidents',
  AGENTS = 'agents',
  CHAT = 'chat',
  ALERTS = 'alerts',
  ACTIVITY = 'activity',
  SYSTEM = 'system'
}

export interface WebSocketMessage {
  id: string;
  type: string;
  channel: ChannelType;
  payload: any;
  timestamp: number;
  priority?: MessagePriority;
}

export interface OutgoingMessage {
  type: string;
  channel?: ChannelType;
  payload: any;
  priority?: MessagePriority;
}

export interface QueuedMessage extends OutgoingMessage {
  id: string;
  timestamp: number;
  retries: number;
  maxRetries: number;
}

export interface ConnectionOptions {
  url: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  maxReconnectAttempts?: number;
  timeout?: number;
  debug?: boolean;
}

export interface ConnectionMetrics {
  latency: number;
  messagesSent: number;
  messagesReceived: number;
  bytesReceived: number;
  bytesSent: number;
  errors: number;
  reconnects: number;
}

export type MessageHandler = (message: WebSocketMessage) => void;
export type ConnectionStateHandler = (state: ConnectionState) => void;
export type ErrorHandler = (error: Error) => void;

export interface Subscription {
  channel: ChannelType;
  handler: MessageHandler;
  id: string;
}

// Event types for specific channels
export interface IncidentUpdate {
  incidentId: string;
  type: 'created' | 'updated' | 'resolved' | 'escalated';
  data: any;
}

export interface AgentStatusUpdate {
  agentId: string;
  status: 'online' | 'offline' | 'busy' | 'away';
  lastSeen?: number;
}

export interface ChatMessage {
  id: string;
  conversationId: string;
  senderId: string;
  content: string;
  timestamp: number;
  read?: boolean;
}

export interface AlertNotification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: number;
  actionUrl?: string;
}

export interface ActivityEvent {
  id: string;
  type: string;
  actor: string;
  target: string;
  action: string;
  timestamp: number;
  metadata?: any;
}
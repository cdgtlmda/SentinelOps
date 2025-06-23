export type MessageType = 'request' | 'response' | 'broadcast' | 'error' | 'sync' | 'ack';
export type NetworkTopology = 'hub' | 'mesh' | 'hierarchical';
export type CoordinationState = 'waiting' | 'synchronized' | 'conflicted' | 'active';
export type MessageStatus = 'pending' | 'in-transit' | 'delivered' | 'failed' | 'timeout';

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'idle' | 'busy' | 'error';
  capabilities: string[];
  position?: { x: number; y: number };
  metrics: {
    messagesProcessed: number;
    averageResponseTime: number;
    errorRate: number;
    throughput: number;
  };
}

export interface Message {
  id: string;
  fromAgentId: string;
  toAgentId: string | string[]; // Support broadcast
  type: MessageType;
  status: MessageStatus;
  content: {
    action?: string;
    payload?: any;
    metadata?: Record<string, any>;
  };
  timestamp: number;
  responseTime?: number;
  size: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface CollaborationSession {
  id: string;
  agents: Agent[];
  messages: Message[];
  topology: NetworkTopology;
  startTime: number;
  endTime?: number;
  metrics: CollaborationMetrics;
}

export interface CollaborationMetrics {
  totalMessages: number;
  averageResponseTime: number;
  communicationOverhead: number;
  efficiency: number;
  throughput: number;
  errorRate: number;
  bottlenecks: Bottleneck[];
}

export interface Bottleneck {
  agentId: string;
  severity: 'low' | 'medium' | 'high';
  type: 'processing' | 'network' | 'resource';
  description: string;
  timestamp: number;
}

export interface SynchronizationPoint {
  id: string;
  agentIds: string[];
  state: CoordinationState;
  timestamp: number;
  duration?: number;
  result?: 'success' | 'failure' | 'timeout';
}

export interface ResourceLock {
  id: string;
  resourceId: string;
  ownerId: string;
  waitingIds: string[];
  acquiredAt: number;
  expiresAt?: number;
}

export interface ConsensusDecision {
  id: string;
  topic: string;
  participants: string[];
  votes: Record<string, boolean>;
  result: 'approved' | 'rejected' | 'pending';
  timestamp: number;
}

export interface CommunicationEdge {
  source: string;
  target: string;
  weight: number;
  latency: number;
  reliability: number;
}

export interface CollaborationState {
  session: CollaborationSession;
  synchronizationPoints: SynchronizationPoint[];
  resourceLocks: ResourceLock[];
  consensusDecisions: ConsensusDecision[];
  communicationGraph: CommunicationEdge[];
}
/**
 * Agent types and interfaces for SentinelOps
 */

export type AgentType = 'security' | 'monitoring' | 'remediation' | 'analysis' | 'network';

export type AgentStatus = 'idle' | 'processing' | 'waiting' | 'error' | 'completed';

export interface AgentTask {
  id: string;
  name: string;
  description: string;
  startTime: Date;
  endTime?: Date;
  progress: number; // 0-100
  status: 'pending' | 'running' | 'completed' | 'failed';
  error?: string;
}

export interface AgentMetrics {
  tasksCompleted: number;
  tasksFailed: number;
  averageResponseTime: number; // in ms
  uptime: number; // in seconds
  cpuUsage: number; // 0-100
  memoryUsage: number; // 0-100
}

export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  currentTask?: AgentTask;
  taskHistory: AgentTask[];
  lastActionTimestamp: Date;
  metrics: AgentMetrics;
  capabilities: string[];
  isActive: boolean;
  error?: {
    message: string;
    code?: string;
    timestamp: Date;
  };
}

export interface AgentAction {
  type: 'start' | 'stop' | 'restart' | 'assignTask' | 'clearError';
  agentId: string;
  payload?: any;
}

export interface AgentFilter {
  types?: AgentType[];
  statuses?: AgentStatus[];
  searchQuery?: string;
}

export type AgentSortOption = 'name' | 'status' | 'lastAction' | 'performance';
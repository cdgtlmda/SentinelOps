// Activity-related TypeScript interfaces

export type ActivityType = 
  | 'agent_status_change'
  | 'workflow_started' 
  | 'workflow_completed'
  | 'workflow_failed'
  | 'incident_created'
  | 'incident_updated'
  | 'alert_triggered'
  | 'resource_allocated'
  | 'api_call'
  | 'error'
  | 'info'

export type ActivitySeverity = 'info' | 'warning' | 'error' | 'critical'

export interface Activity {
  id: string
  type: ActivityType
  severity: ActivitySeverity
  timestamp: Date
  title: string
  description: string
  agentId?: string
  workflowId?: string
  incidentId?: string
  metadata?: Record<string, any>
  resourceUsage?: ResourceUsage
}

export interface ResourceUsage {
  cpu?: number // percentage
  memory?: number // MB
  apiCalls?: number
  estimatedCost?: number // in cents
  duration?: number // in ms
}

export interface ActivityFilter {
  types?: ActivityType[]
  severities?: ActivitySeverity[]
  agentIds?: string[]
  workflowIds?: string[]
  incidentIds?: string[]
  startTime?: Date
  endTime?: Date
  searchTerm?: string
}

export interface ActivityViewMode {
  view: 'timeline' | 'grouped' | 'compact'
  groupBy?: 'agent' | 'workflow' | 'incident' | 'type'
  sortBy: 'timestamp' | 'severity' | 'type'
  sortOrder: 'asc' | 'desc'
}

export interface AgentActivity {
  agentId: string
  status: 'idle' | 'processing' | 'waiting' | 'error' | 'completed'
  currentTask?: string
  lastActionTimestamp: Date
  tasksCompleted: number
  tasksInProgress: number
  errorCount: number
}

export interface WorkflowStep {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  startTime?: Date
  endTime?: Date
  agentId: string
  inputs?: Record<string, any>
  outputs?: Record<string, any>
  error?: string
  dependencies: string[] // IDs of steps this depends on
}

export interface WorkflowVisualization {
  workflowId: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number // 0-100
  steps: WorkflowStep[]
  startTime: Date
  endTime?: Date
  estimatedDuration?: number // in ms
}

export interface ResourceMetrics {
  timestamp: Date
  cloudResources: {
    compute: {
      instances: number
      vcpus: number
      memoryGB: number
    }
    storage: {
      usedGB: number
      totalGB: number
    }
    network: {
      ingressMbps: number
      egressMbps: number
    }
  }
  apiUsage: {
    provider: string
    callCount: number
    tokensUsed?: number
    rateLimit?: {
      limit: number
      remaining: number
      resetAt: Date
    }
  }[]
  estimatedCost: {
    compute: number
    storage: number
    network: number
    api: number
    total: number
  }
}
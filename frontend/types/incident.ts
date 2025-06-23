// Incident-related TypeScript interfaces

export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low'

export type IncidentStatus = 
  | 'new'
  | 'acknowledged'
  | 'investigating'
  | 'remediated'
  | 'resolved'
  | 'closed'

export type IncidentSource = 
  | 'monitoring'
  | 'alert'
  | 'manual'
  | 'automated_detection'
  | 'customer_report'

export interface Incident {
  id: string
  title: string
  description: string
  severity: IncidentSeverity
  status: IncidentStatus
  source: IncidentSource
  createdAt: Date
  updatedAt: Date
  acknowledgedAt?: Date
  resolvedAt?: Date
  closedAt?: Date
  assignedTo?: string
  tags: string[]
  affectedResources: AffectedResource[]
  alerts: Alert[]
  timeline: TimelineEvent[]
  remediationSteps: RemediationStep[]
  notes: IncidentNote[]
  metrics: IncidentMetrics
}

export interface AffectedResource {
  id: string
  type: 'server' | 'database' | 'service' | 'network' | 'application' | 'other'
  name: string
  status: 'healthy' | 'degraded' | 'down' | 'unknown'
  impact: string
  metadata?: Record<string, any>
}

export interface Alert {
  id: string
  name: string
  severity: IncidentSeverity
  timestamp: Date
  source: string
  message: string
  metadata?: Record<string, any>
}

export interface TimelineEvent {
  id: string
  timestamp: Date
  type: 'status_change' | 'action_taken' | 'comment' | 'alert' | 'automated_action'
  actor?: string // user or system that performed the action
  title: string
  description: string
  metadata?: Record<string, any>
}

export interface RemediationStep {
  id: string
  order: number
  title: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'skipped' | 'failed'
  automatable: boolean
  estimatedDuration?: number // in minutes
  actualDuration?: number // in minutes
  completedAt?: Date
  completedBy?: string
  result?: string
}

export interface IncidentNote {
  id: string
  timestamp: Date
  author: string
  content: string
  isInternal: boolean // internal notes vs customer-visible
}

export interface IncidentMetrics {
  timeToAcknowledge?: number // in seconds
  timeToResolve?: number // in seconds
  timeToClose?: number // in seconds
  impactedUsers?: number
  estimatedRevenueLoss?: number
  slaStatus: 'met' | 'at_risk' | 'breached' | 'n/a'
}

export interface IncidentFilter {
  severities?: IncidentSeverity[]
  statuses?: IncidentStatus[]
  sources?: IncidentSource[]
  assignedTo?: string[]
  tags?: string[]
  startDate?: Date
  endDate?: Date
  searchTerm?: string
}

export interface IncidentSort {
  field: 'createdAt' | 'updatedAt' | 'severity' | 'status' | 'title'
  order: 'asc' | 'desc'
}

export interface IncidentListView {
  mode: 'grid' | 'list'
  sortBy: IncidentSort
  filters: IncidentFilter
  page: number
  pageSize: number
}
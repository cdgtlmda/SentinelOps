// Action-related TypeScript interfaces

import { IncidentSeverity } from './incident'

export type ActionType = 
  | 'acknowledge'
  | 'remediate'
  | 'escalate'
  | 'resolve'
  | 'close'
  | 'assign'
  | 'comment'
  | 'custom'

export type ActionStatus = 
  | 'pending'
  | 'executing'
  | 'completed'
  | 'failed'
  | 'cancelled'

export type RemediationType = 
  | 'restart_service'
  | 'scale_resources'
  | 'rollback_deployment'
  | 'clear_cache'
  | 'rotate_credentials'
  | 'apply_patch'
  | 'failover'
  | 'custom_script'

export type EscalationLevel = 
  | 'team_lead'
  | 'manager'
  | 'director'
  | 'vp'
  | 'c_level'
  | 'on_call'
  | 'custom'

export interface Action {
  id: string
  type: ActionType
  label: string
  description?: string
  icon?: string
  enabled: boolean
  visible: boolean
  requiresConfirmation: boolean
  keyboardShortcut?: string
  metadata?: Record<string, any>
}

export interface QuickAction extends Action {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  tooltip?: string
}

export interface ActionExecutionContext {
  incidentIds: string[]
  userId: string
  timestamp: Date
  source: 'ui' | 'keyboard' | 'api' | 'automation'
  metadata?: Record<string, any>
}

export interface ActionResult {
  success: boolean
  actionId: string
  executionId: string
  timestamp: Date
  duration: number // in milliseconds
  affectedIncidents: string[]
  message?: string
  error?: string
  metadata?: Record<string, any>
}

export interface RemediationOption {
  id: string
  type: RemediationType
  name: string
  description: string
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  estimatedDuration: number // in seconds
  requiresApproval: boolean
  automatable: boolean
  prerequisites?: string[]
  impacts?: string[]
  rollbackable: boolean
  successRate?: number // percentage
  lastUsed?: Date
  tags?: string[]
}

export interface RemediationPlan {
  id: string
  incidentId: string
  name: string
  description: string
  steps: RemediationStep[]
  estimatedTotalDuration: number
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  approvalRequired: boolean
  approvedBy?: string
  approvedAt?: Date
  createdBy: string
  createdAt: Date
  status: ActionStatus
}

export interface RemediationStep {
  id: string
  order: number
  option: RemediationOption
  parameters?: Record<string, any>
  status: ActionStatus
  startedAt?: Date
  completedAt?: Date
  output?: string
  error?: string
}

export interface EscalationRecipient {
  id: string
  type: 'user' | 'team' | 'role' | 'external'
  name: string
  email?: string
  phone?: string
  level: EscalationLevel
  available: boolean
  responseTime?: number // average in minutes
  expertise?: string[]
  timezone?: string
  preferredContactMethod?: 'email' | 'phone' | 'slack' | 'pagerduty'
}

export interface EscalationRequest {
  id: string
  incidentId: string
  escalatedBy: string
  escalatedTo: EscalationRecipient[]
  priority: 'low' | 'medium' | 'high' | 'urgent'
  subject: string
  message: string
  attachments?: string[]
  template?: string
  dueBy?: Date
  escalatedAt: Date
  acknowledgedAt?: Date
  resolvedAt?: Date
  status: 'pending' | 'acknowledged' | 'in_progress' | 'resolved' | 'cancelled'
  response?: string
}

export interface ActionPermission {
  action: ActionType
  roles: string[]
  conditions?: {
    severities?: IncidentSeverity[]
    statuses?: string[]
    maxIncidents?: number
    timeRestrictions?: {
      allowedHours?: { start: number; end: number }
      allowedDays?: number[] // 0-6, Sunday-Saturday
    }
  }
}

export interface ActionHistory {
  id: string
  actionType: ActionType
  executedBy: string
  executedAt: Date
  context: ActionExecutionContext
  result: ActionResult
  incidentSnapshot?: any // Snapshot of incident state before action
  reversible: boolean
  reverseActionId?: string
}

export interface KeyboardShortcut {
  key: string
  modifiers?: ('ctrl' | 'alt' | 'shift' | 'meta')[]
  action: ActionType
  description: string
  enabled: boolean
  customizable: boolean
}

export interface ActionConfiguration {
  actions: Action[]
  permissions: ActionPermission[]
  shortcuts: KeyboardShortcut[]
  confirmationSettings: {
    requireForDestructive: boolean
    requireForBulk: boolean
    bulkThreshold: number
  }
  executionSettings: {
    maxConcurrent: number
    timeout: number // in seconds
    retryAttempts: number
    retryDelay: number // in seconds
  }
}
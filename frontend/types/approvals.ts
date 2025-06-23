// Approval workflow TypeScript interfaces

import { ActionType, RemediationType } from './actions'

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

export type ApprovalStatus = 
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'expired'
  | 'cancelled'
  | 'escalated'

export type ConfirmationMethod = 
  | 'checkbox'
  | 'text_input'
  | 'mfa'
  | 'biometric'
  | 'manager_approval'

export type UndoStatus = 
  | 'available'
  | 'executing'
  | 'completed'
  | 'expired'
  | 'failed'

export interface RiskFactor {
  id: string
  category: string
  description: string
  severity: RiskLevel
  probability: number // 0-1
  impact: string[]
  mitigations?: string[]
}

export interface RiskAssessment {
  overallRisk: RiskLevel
  riskScore: number // 0-100
  factors: RiskFactor[]
  potentialImpact: {
    users: number
    services: string[]
    revenue?: number
    downtime?: number // in minutes
  }
  historicalData?: {
    similarActionsCount: number
    successRate: number
    averageRecoveryTime: number
    lastIncident?: Date
  }
}

export interface ApprovalRequirement {
  id: string
  actionType: ActionType
  riskLevel: RiskLevel
  confirmationMethod: ConfirmationMethod
  approvers?: ApproverRole[]
  timeLimit?: number // in minutes
  escalationPolicy?: EscalationPolicy
  conditions?: ApprovalCondition[]
}

export interface ApproverRole {
  id: string
  name: string
  type: 'user' | 'role' | 'team'
  level: number // approval hierarchy level
  required: boolean
  alternates?: string[] // IDs of alternate approvers
}

export interface ApprovalCondition {
  type: 'time_window' | 'resource_threshold' | 'impact_scope' | 'custom'
  operator: 'equals' | 'greater_than' | 'less_than' | 'between' | 'in' | 'not_in'
  value: any
  description: string
}

export interface EscalationPolicy {
  timeoutMinutes: number
  escalateTo: ApproverRole[]
  notificationChannels: string[]
  autoApprove?: boolean
  autoReject?: boolean
}

export interface ApprovalRequest {
  id: string
  actionId: string
  actionType: ActionType
  requestedBy: string
  requestedAt: Date
  description: string
  riskAssessment: RiskAssessment
  requirement: ApprovalRequirement
  status: ApprovalStatus
  approvals: ApprovalRecord[]
  currentLevel: number
  expiresAt?: Date
  metadata?: Record<string, any>
}

export interface ApprovalRecord {
  id: string
  approverId: string
  approverName: string
  approverRole: string
  status: ApprovalStatus
  timestamp: Date
  comments?: string
  confirmationMethod: ConfirmationMethod
  confirmationData?: any
  level: number
}

export interface ConfirmationDialogConfig {
  title: string
  message: string
  riskLevel: RiskLevel
  confirmationMethod: ConfirmationMethod
  confirmationPrompt?: string
  confirmationPattern?: string | RegExp
  showRiskAssessment: boolean
  showImpactSummary: boolean
  requireExplicitConsent: boolean
  customFields?: CustomField[]
}

export interface CustomField {
  id: string
  type: 'text' | 'checkbox' | 'select' | 'textarea'
  label: string
  required: boolean
  validation?: (value: any) => boolean | string
  options?: { value: string; label: string }[]
}

export interface UndoableAction {
  id: string
  actionId: string
  actionType: ActionType
  description: string
  executedBy: string
  executedAt: Date
  undoDeadline: Date
  status: UndoStatus
  undoHandler: () => Promise<void>
  impactedResources: string[]
  originalState?: any
  currentState?: any
  canUndo: boolean
  undoReason?: string
}

export interface UndoQueueItem {
  action: UndoableAction
  priority: number
  dependencies?: string[] // IDs of actions that must be undone first
}

export interface AuditLogEntry {
  id: string
  timestamp: Date
  userId: string
  userName: string
  userRole: string
  actionType: ActionType
  actionId: string
  description: string
  ipAddress?: string
  userAgent?: string
  requestMethod?: string
  resourceId?: string
  resourceType?: string
  changes?: ChangeRecord[]
  result: 'success' | 'failure' | 'partial'
  errorMessage?: string
  duration?: number // in milliseconds
  metadata?: Record<string, any>
}

export interface ChangeRecord {
  field: string
  oldValue: any
  newValue: any
  changeType: 'create' | 'update' | 'delete'
}

export interface ApprovalChain {
  id: string
  name: string
  description: string
  levels: ApprovalLevel[]
  parallel: boolean // whether levels can be approved in parallel
  timeLimit?: number // total time limit in minutes
  createdBy: string
  createdAt: Date
  active: boolean
}

export interface ApprovalLevel {
  level: number
  name: string
  approvers: ApproverRole[]
  minApprovals: number
  timeLimit?: number // in minutes
  escalationPolicy?: EscalationPolicy
  conditions?: ApprovalCondition[]
  parallel: boolean // whether approvers in this level can approve in parallel
}

export interface ApprovalNotification {
  id: string
  type: 'new_request' | 'approved' | 'rejected' | 'escalated' | 'expiring' | 'expired'
  approvalRequestId: string
  recipientId: string
  sentAt: Date
  readAt?: Date
  channel: 'email' | 'slack' | 'in_app' | 'sms' | 'webhook'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  message: string
  actionRequired: boolean
  expiresAt?: Date
}

export interface ApprovalMetrics {
  totalRequests: number
  pendingRequests: number
  approvedRequests: number
  rejectedRequests: number
  averageApprovalTime: number // in minutes
  approvalRateByRisk: Record<RiskLevel, number>
  topApprovers: { userId: string; count: number }[]
  bottlenecks: { level: number; averageTime: number }[]
  expirationRate: number
  escalationRate: number
}

export interface ApprovalWorkflowConfig {
  enabled: boolean
  defaultTimeLimit: number // in minutes
  requireApprovalFor: {
    riskLevels: RiskLevel[]
    actionTypes: ActionType[]
    remediationTypes: RemediationType[]
  }
  autoApprovalRules: AutoApprovalRule[]
  notificationSettings: {
    channels: string[]
    reminderIntervals: number[] // in minutes
    escalationThreshold: number // in minutes
  }
  undoSettings: {
    enabled: boolean
    defaultTimeLimit: number // in seconds
    excludeActions: ActionType[]
  }
  auditSettings: {
    retentionDays: number
    includeSystemActions: boolean
    sensitiveFields: string[]
  }
}

export interface AutoApprovalRule {
  id: string
  name: string
  conditions: ApprovalCondition[]
  maxRiskLevel: RiskLevel
  enabled: boolean
  createdBy: string
  createdAt: Date
  usageCount: number
  lastUsed?: Date
}
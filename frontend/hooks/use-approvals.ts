// Approval workflow management hooks

import { useState, useCallback, useEffect, useRef } from 'react'
import { 
  ApprovalRequest, 
  ApprovalStatus, 
  RiskLevel, 
  RiskAssessment,
  UndoableAction,
  UndoStatus,
  AuditLogEntry,
  ApprovalChain,
  ConfirmationMethod,
  ApprovalRecord,
  RiskFactor
} from '@/types/approvals'
import { ActionType } from '@/types/actions'

// Mock API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export function useApprovalWorkflow() {
  const [approvalRequests, setApprovalRequests] = useState<ApprovalRequest[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createApprovalRequest = useCallback(async (
    actionType: ActionType,
    description: string,
    riskAssessment: RiskAssessment,
    metadata?: Record<string, any>
  ): Promise<ApprovalRequest> => {
    setLoading(true)
    setError(null)

    try {
      await delay(500)

      const request: ApprovalRequest = {
        id: `apr_${Date.now()}`,
        actionId: `act_${Date.now()}`,
        actionType,
        requestedBy: 'current_user',
        requestedAt: new Date(),
        description,
        riskAssessment,
        requirement: {
          id: 'req_1',
          actionType,
          riskLevel: riskAssessment.overallRisk,
          confirmationMethod: getConfirmationMethod(riskAssessment.overallRisk),
          timeLimit: getTimeLimit(riskAssessment.overallRisk),
        },
        status: 'pending',
        approvals: [],
        currentLevel: 0,
        expiresAt: new Date(Date.now() + getTimeLimit(riskAssessment.overallRisk) * 60000),
        metadata
      }

      setApprovalRequests(prev => [...prev, request])
      return request
    } catch (err) {
      setError('Failed to create approval request')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const approveRequest = useCallback(async (
    requestId: string,
    comments?: string,
    confirmationData?: any
  ) => {
    setLoading(true)
    try {
      await delay(300)
      
      setApprovalRequests(prev => prev.map(req => {
        if (req.id === requestId) {
          const approval: ApprovalRecord = {
            id: `rec_${Date.now()}`,
            approverId: 'current_user',
            approverName: 'Current User',
            approverRole: 'admin',
            status: 'approved',
            timestamp: new Date(),
            comments,
            confirmationMethod: req.requirement.confirmationMethod,
            confirmationData,
            level: req.currentLevel
          }

          return {
            ...req,
            status: 'approved',
            approvals: [...req.approvals, approval]
          }
        }
        return req
      }))
    } catch (err) {
      setError('Failed to approve request')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const rejectRequest = useCallback(async (
    requestId: string,
    reason: string
  ) => {
    setLoading(true)
    try {
      await delay(300)
      
      setApprovalRequests(prev => prev.map(req => {
        if (req.id === requestId) {
          const approval: ApprovalRecord = {
            id: `rec_${Date.now()}`,
            approverId: 'current_user',
            approverName: 'Current User',
            approverRole: 'admin',
            status: 'rejected',
            timestamp: new Date(),
            comments: reason,
            confirmationMethod: req.requirement.confirmationMethod,
            level: req.currentLevel
          }

          return {
            ...req,
            status: 'rejected',
            approvals: [...req.approvals, approval]
          }
        }
        return req
      }))
    } catch (err) {
      setError('Failed to reject request')
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    approvalRequests,
    loading,
    error,
    createApprovalRequest,
    approveRequest,
    rejectRequest
  }
}

export function useRiskCalculation() {
  const calculateRisk = useCallback((
    actionType: ActionType,
    impactScope: {
      users?: number
      services?: string[]
      critical?: boolean
    },
    historicalData?: {
      successRate?: number
      lastIncident?: Date
    }
  ): RiskAssessment => {
    const factors: RiskFactor[] = []
    let riskScore = 0

    // User impact factor
    if (impactScope.users) {
      const userImpact = impactScope.users
      if (userImpact > 10000) {
        factors.push({
          id: 'user_impact_high',
          category: 'User Impact',
          description: `Affects ${userImpact.toLocaleString()} users`,
          severity: 'high',
          probability: 0.8,
          impact: ['Service degradation', 'User experience impact'],
          mitigations: ['Gradual rollout', 'Feature flags']
        })
        riskScore += 30
      } else if (userImpact > 1000) {
        factors.push({
          id: 'user_impact_medium',
          category: 'User Impact',
          description: `Affects ${userImpact.toLocaleString()} users`,
          severity: 'medium',
          probability: 0.6,
          impact: ['Limited service impact'],
          mitigations: ['Monitoring alerts', 'Quick rollback']
        })
        riskScore += 15
      }
    }

    // Service criticality factor
    if (impactScope.critical) {
      factors.push({
        id: 'critical_service',
        category: 'Service Criticality',
        description: 'Affects critical infrastructure',
        severity: 'critical',
        probability: 0.9,
        impact: ['Potential system-wide outage', 'Revenue impact'],
        mitigations: ['Backup systems', 'Incident response team']
      })
      riskScore += 40
    }

    // Historical success rate
    if (historicalData?.successRate !== undefined) {
      const successRate = historicalData.successRate
      if (successRate < 50) {
        factors.push({
          id: 'low_success_rate',
          category: 'Historical Performance',
          description: `Low success rate: ${successRate}%`,
          severity: 'high',
          probability: 0.5,
          impact: ['High failure probability'],
          mitigations: ['Additional testing', 'Manual oversight']
        })
        riskScore += 25
      } else if (successRate < 80) {
        factors.push({
          id: 'moderate_success_rate',
          category: 'Historical Performance',
          description: `Moderate success rate: ${successRate}%`,
          severity: 'medium',
          probability: 0.3,
          impact: ['Possible failure'],
          mitigations: ['Enhanced monitoring']
        })
        riskScore += 10
      }
    }

    // Recent incident factor
    if (historicalData?.lastIncident) {
      const daysSinceIncident = Math.floor(
        (Date.now() - historicalData.lastIncident.getTime()) / (1000 * 60 * 60 * 24)
      )
      if (daysSinceIncident < 7) {
        factors.push({
          id: 'recent_incident',
          category: 'Incident History',
          description: `Recent incident ${daysSinceIncident} days ago`,
          severity: 'high',
          probability: 0.7,
          impact: ['Increased failure risk'],
          mitigations: ['Root cause analysis', 'Extra caution']
        })
        riskScore += 20
      }
    }

    // Determine overall risk level
    let overallRisk: RiskLevel = 'low'
    if (riskScore >= 70) overallRisk = 'critical'
    else if (riskScore >= 50) overallRisk = 'high'
    else if (riskScore >= 25) overallRisk = 'medium'

    return {
      overallRisk,
      riskScore,
      factors,
      potentialImpact: {
        users: impactScope.users || 0,
        services: impactScope.services || [],
        revenue: impactScope.critical ? 100000 : 0,
        downtime: impactScope.critical ? 60 : 0
      },
      historicalData: historicalData ? {
        similarActionsCount: 50,
        successRate: historicalData.successRate || 85,
        averageRecoveryTime: 15,
        lastIncident: historicalData.lastIncident
      } : undefined
    }
  }, [])

  return { calculateRisk }
}

export function useUndoManager() {
  const [undoQueue, setUndoQueue] = useState<UndoableAction[]>([])
  const timeoutsRef = useRef<Map<string, NodeJS.Timeout>>(new Map())

  const addUndoableAction = useCallback((action: Omit<UndoableAction, 'status' | 'canUndo'>) => {
    const undoableAction: UndoableAction = {
      ...action,
      status: 'available',
      canUndo: true
    }

    setUndoQueue(prev => [...prev, undoableAction])

    // Set expiration timeout
    const timeout = setTimeout(() => {
      setUndoQueue(prev => prev.map(a => 
        a.id === action.id 
          ? { ...a, status: 'expired', canUndo: false }
          : a
      ))
      timeoutsRef.current.delete(action.id)
    }, 30000) // 30 seconds

    timeoutsRef.current.set(action.id, timeout)
  }, [])

  const executeUndo = useCallback(async (actionId: string) => {
    const action = undoQueue.find(a => a.id === actionId)
    if (!action || !action.canUndo) {
      throw new Error('Action cannot be undone')
    }

    setUndoQueue(prev => prev.map(a => 
      a.id === actionId 
        ? { ...a, status: 'executing' }
        : a
    ))

    try {
      await action.undoHandler()
      
      setUndoQueue(prev => prev.map(a => 
        a.id === actionId 
          ? { ...a, status: 'completed', canUndo: false }
          : a
      ))

      // Clear timeout
      const timeout = timeoutsRef.current.get(actionId)
      if (timeout) {
        clearTimeout(timeout)
        timeoutsRef.current.delete(actionId)
      }
    } catch (error) {
      setUndoQueue(prev => prev.map(a => 
        a.id === actionId 
          ? { ...a, status: 'failed', canUndo: false }
          : a
      ))
      throw error
    }
  }, [undoQueue])

  const clearExpired = useCallback(() => {
    setUndoQueue(prev => prev.filter(a => a.status !== 'expired' && a.status !== 'completed'))
  }, [])

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      timeoutsRef.current.forEach(timeout => clearTimeout(timeout))
    }
  }, [])

  return {
    undoQueue,
    addUndoableAction,
    executeUndo,
    clearExpired
  }
}

export function useAuditLog() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([])
  const [filter, setFilter] = useState<{
    actionTypes?: ActionType[]
    userId?: string
    dateRange?: { start: Date; end: Date }
    result?: 'success' | 'failure' | 'partial'
  }>({})

  const logAction = useCallback((
    actionType: ActionType,
    actionId: string,
    description: string,
    result: 'success' | 'failure' | 'partial',
    changes?: any[],
    metadata?: Record<string, any>
  ) => {
    const entry: AuditLogEntry = {
      id: `audit_${Date.now()}`,
      timestamp: new Date(),
      userId: 'current_user',
      userName: 'Current User',
      userRole: 'admin',
      actionType,
      actionId,
      description,
      result,
      changes,
      metadata,
      duration: Math.floor(Math.random() * 1000) + 100
    }

    setEntries(prev => [entry, ...prev])
  }, [])

  const filteredEntries = entries.filter(entry => {
    if (filter.actionTypes && !filter.actionTypes.includes(entry.actionType)) {
      return false
    }
    if (filter.userId && entry.userId !== filter.userId) {
      return false
    }
    if (filter.dateRange) {
      const entryDate = entry.timestamp.getTime()
      if (entryDate < filter.dateRange.start.getTime() || 
          entryDate > filter.dateRange.end.getTime()) {
        return false
      }
    }
    if (filter.result && entry.result !== filter.result) {
      return false
    }
    return true
  })

  return {
    entries: filteredEntries,
    logAction,
    setFilter
  }
}

export function useApprovalChain() {
  const [chains, setChains] = useState<ApprovalChain[]>([])
  const [activeChainId, setActiveChainId] = useState<string | null>(null)

  const createChain = useCallback((
    name: string,
    description: string,
    levels: any[]
  ): ApprovalChain => {
    const chain: ApprovalChain = {
      id: `chain_${Date.now()}`,
      name,
      description,
      levels,
      parallel: false,
      createdBy: 'current_user',
      createdAt: new Date(),
      active: true
    }

    setChains(prev => [...prev, chain])
    return chain
  }, [])

  const getNextApprovers = useCallback((chainId: string, currentLevel: number) => {
    const chain = chains.find(c => c.id === chainId)
    if (!chain) return []

    const nextLevel = chain.levels.find(l => l.level === currentLevel + 1)
    return nextLevel?.approvers || []
  }, [chains])

  return {
    chains,
    activeChainId,
    setActiveChainId,
    createChain,
    getNextApprovers
  }
}

// Helper functions
function getConfirmationMethod(riskLevel: RiskLevel): ConfirmationMethod {
  switch (riskLevel) {
    case 'critical':
      return 'manager_approval'
    case 'high':
      return 'mfa'
    case 'medium':
      return 'text_input'
    default:
      return 'checkbox'
  }
}

function getTimeLimit(riskLevel: RiskLevel): number {
  switch (riskLevel) {
    case 'critical':
      return 30 // 30 minutes
    case 'high':
      return 60 // 1 hour
    case 'medium':
      return 120 // 2 hours
    default:
      return 240 // 4 hours
  }
}
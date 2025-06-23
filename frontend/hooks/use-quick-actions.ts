'use client'

import { useCallback, useState, useEffect } from 'react'
import { useIncidentStore } from '@/store'
import {
  ActionType,
  ActionExecutionContext,
  ActionResult,
  QuickAction,
  RemediationOption,
  EscalationRequest,
  KeyboardShortcut
} from '@/types/actions'

const defaultShortcuts: KeyboardShortcut[] = [
  {
    key: 'A',
    modifiers: [],
    action: 'acknowledge',
    description: 'Acknowledge selected incidents',
    enabled: true,
    customizable: true
  },
  {
    key: 'R',
    modifiers: [],
    action: 'remediate',
    description: 'Open remediation menu',
    enabled: true,
    customizable: true
  },
  {
    key: 'E',
    modifiers: [],
    action: 'escalate',
    description: 'Open escalation dialog',
    enabled: true,
    customizable: true
  },
  {
    key: 'X',
    modifiers: ['ctrl'],
    action: 'resolve',
    description: 'Resolve selected incidents',
    enabled: true,
    customizable: true
  }
]

export function useQuickActions() {
  const { incidents, updateIncident } = useIncidentStore()
  const [executingActions, setExecutingActions] = useState<Map<string, boolean>>(new Map())
  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>(defaultShortcuts)

  // Check if user has permission for an action
  const checkPermissions = useCallback((actionType: ActionType, incidentIds: string[]): boolean => {
    // Mock permission check - in real app would check user role/permissions
    switch (actionType) {
      case 'acknowledge':
      case 'comment':
        return true
      case 'remediate':
      case 'escalate':
        return incidentIds.length <= 10 // Limit bulk actions
      case 'resolve':
      case 'close':
        // Only allow resolve/close if all incidents are in appropriate state
        return incidentIds.every(id => {
          const incident = incidents.find(i => i.id === id)
          return incident && ['investigating', 'remediated'].includes(incident.status)
        })
      default:
        return false
    }
  }, [incidents])

  // Get available actions for selected incidents
  const getAvailableActions = useCallback((incidentIds: string[]): QuickAction[] => {
    if (incidentIds.length === 0) return []

    const selectedIncidents = incidents.filter(i => incidentIds.includes(i.id))
    const actions: QuickAction[] = []

    // Acknowledge - available if any incident is new
    if (selectedIncidents.some(i => i.status === 'new')) {
      actions.push({
        id: 'acknowledge',
        type: 'acknowledge',
        label: 'Acknowledge',
        icon: 'check-circle',
        enabled: checkPermissions('acknowledge', incidentIds),
        visible: true,
        requiresConfirmation: false,
        keyboardShortcut: 'A',
        variant: 'primary'
      })
    }

    // Remediate - available if any incident is acknowledged or investigating
    if (selectedIncidents.some(i => ['acknowledged', 'investigating'].includes(i.status))) {
      actions.push({
        id: 'remediate',
        type: 'remediate',
        label: 'Remediate',
        icon: 'wrench',
        enabled: checkPermissions('remediate', incidentIds),
        visible: true,
        requiresConfirmation: true,
        keyboardShortcut: 'R',
        variant: 'success'
      })
    }

    // Escalate - always available
    actions.push({
      id: 'escalate',
      type: 'escalate',
      label: 'Escalate',
      icon: 'trending-up',
      enabled: checkPermissions('escalate', incidentIds),
      visible: true,
      requiresConfirmation: false,
      keyboardShortcut: 'E',
      variant: 'warning'
    })

    // Resolve - available if remediated
    if (selectedIncidents.some(i => i.status === 'remediated')) {
      actions.push({
        id: 'resolve',
        type: 'resolve',
        label: 'Resolve',
        icon: 'check',
        enabled: checkPermissions('resolve', incidentIds),
        visible: true,
        requiresConfirmation: true,
        keyboardShortcut: 'Ctrl+X',
        variant: 'success'
      })
    }

    return actions
  }, [incidents, checkPermissions])

  // Execute an action
  const executeAction = useCallback(async (
    action: QuickAction,
    context: ActionExecutionContext
  ): Promise<ActionResult> => {
    const startTime = Date.now()
    const executionId = `exec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

    setExecutingActions(prev => new Map(prev).set(action.id, true))

    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000))

      // Process action based on type
      switch (action.type) {
        case 'acknowledge':
          context.incidentIds.forEach(id => {
            updateIncident(id, {
              status: 'acknowledged',
              acknowledgedAt: new Date(),
              acknowledgedBy: context.userId
            })
          })
          break

        case 'remediate':
          const remediationOption = action.metadata?.option as RemediationOption
          if (remediationOption) {
            context.incidentIds.forEach(id => {
              updateIncident(id, {
                status: 'investigating',
                remediationPlan: {
                  id: `plan-${Date.now()}`,
                  incidentId: id,
                  name: remediationOption.name,
                  description: remediationOption.description,
                  steps: [{
                    id: `step-1`,
                    order: 1,
                    option: remediationOption,
                    status: 'executing'
                  }],
                  estimatedTotalDuration: remediationOption.estimatedDuration,
                  riskLevel: remediationOption.riskLevel,
                  approvalRequired: remediationOption.requiresApproval,
                  createdBy: context.userId,
                  createdAt: new Date(),
                  status: 'executing'
                }
              })
            })
          }
          break

        case 'escalate':
          const escalationRequest = action.metadata?.request as Partial<EscalationRequest>
          if (escalationRequest) {
            // In real app, would send escalation notifications
            console.log('Escalating to:', escalationRequest.recipients)
          }
          break

        case 'resolve':
          context.incidentIds.forEach(id => {
            updateIncident(id, {
              status: 'resolved',
              resolvedAt: new Date(),
              resolvedBy: context.userId
            })
          })
          break

        default:
          throw new Error(`Unknown action type: ${action.type}`)
      }

      return {
        success: true,
        actionId: action.id,
        executionId,
        timestamp: new Date(),
        duration: Date.now() - startTime,
        affectedIncidents: context.incidentIds,
        message: `Successfully executed ${action.label} on ${context.incidentIds.length} incident(s)`
      }
    } catch (error) {
      return {
        success: false,
        actionId: action.id,
        executionId,
        timestamp: new Date(),
        duration: Date.now() - startTime,
        affectedIncidents: [],
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }
    } finally {
      setExecutingActions(prev => {
        const next = new Map(prev)
        next.delete(action.id)
        return next
      })
    }
  }, [updateIncident])

  // Register keyboard shortcuts
  const registerShortcut = useCallback((shortcut: KeyboardShortcut) => {
    setShortcuts(prev => [...prev.filter(s => s.key !== shortcut.key), shortcut])
  }, [])

  // Unregister keyboard shortcut
  const unregisterShortcut = useCallback((key: string) => {
    setShortcuts(prev => prev.filter(s => s.key !== key))
  }, [])

  return {
    executeAction,
    getAvailableActions,
    checkPermissions,
    executingActions,
    shortcuts,
    registerShortcut,
    unregisterShortcut
  }
}
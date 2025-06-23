'use client'

import { useState, useEffect } from 'react'
import {
  CheckCircle,
  Wrench,
  TrendingUp,
  MoreHorizontal,
  AlertTriangle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ActionButton } from './action-button'
import { RemediationMenu } from './remediation-menu'
import { EscalationDialog } from './escalation-dialog'
import { QuickAction, ActionExecutionContext } from '@/types/actions'
import { useQuickActions } from '@/hooks/use-quick-actions'
import { useAlertContext } from '@/components/alerts'
import { useRiskCalculation, useUndoManager, useAuditLog } from '@/hooks/use-approvals'
import { RiskLevel } from '@/types/approvals'

interface QuickActionBarProps {
  incidentIds: string[]
  className?: string
  variant?: 'fixed' | 'inline' | 'floating'
  onActionComplete?: (action: QuickAction, result: any) => void
}

export function QuickActionBar({
  incidentIds,
  className,
  variant = 'inline',
  onActionComplete
}: QuickActionBarProps) {
  const [showRemediation, setShowRemediation] = useState(false)
  const [showEscalation, setShowEscalation] = useState(false)
  const [loadingActions, setLoadingActions] = useState<Set<string>>(new Set())
  
  const { executeAction, getAvailableActions, checkPermissions } = useQuickActions()
  const { showAlert } = useAlertContext()
  const { calculateRisk } = useRiskCalculation()
  const { addUndoableAction } = useUndoManager()
  const { logAction } = useAuditLog()

  const actions = getAvailableActions(incidentIds)

  const handleAction = async (action: QuickAction, approvalData?: any) => {
    if (!checkPermissions(action.type, incidentIds)) {
      showAlert({
        type: 'error',
        title: 'Permission Denied',
        message: 'You do not have permission to perform this action.'
      })
      return
    }

    setLoadingActions(prev => new Set(prev).add(action.id))

    try {
      const startTime = Date.now()
      const context: ActionExecutionContext = {
        incidentIds,
        userId: 'current-user', // Would come from auth context
        timestamp: new Date(),
        source: 'ui',
        metadata: { ...action.metadata, approvalData }
      }

      // Log action start
      logAction(
        action.type,
        action.id,
        `Executing ${action.label} for ${incidentIds.length} incidents`,
        'success',
        undefined,
        context
      )

      const result = await executeAction(action, context)
      
      // Add to undo queue for reversible actions
      if (action.type !== 'comment' && action.type !== 'escalate') {
        addUndoableAction({
          id: `undo_${action.id}_${Date.now()}`,
          actionId: action.id,
          actionType: action.type,
          description: `Undo ${action.label} for ${incidentIds.length} incidents`,
          executedBy: context.userId,
          executedAt: new Date(),
          undoDeadline: new Date(Date.now() + 30000),
          undoHandler: async () => {
            console.log(`Undoing action: ${action.id} for incidents:`, incidentIds)
            // Implement actual undo logic here
          },
          impactedResources: incidentIds
        })
      }
      
      // Log successful completion
      const duration = Date.now() - startTime
      logAction(
        action.type,
        action.id,
        `Completed ${action.label} for ${incidentIds.length} incidents`,
        'success',
        undefined,
        { duration, result }
      )
      
      showAlert({
        type: 'success',
        title: 'Action Completed',
        message: `Successfully ${action.label.toLowerCase()}d ${incidentIds.length} incident(s)`
      })

      onActionComplete?.(action, result)
    } catch (error) {
      // Log failure
      logAction(
        action.type,
        action.id,
        `Failed to execute ${action.label}`,
        'failure',
        undefined,
        { error: error instanceof Error ? error.message : 'Unknown error' }
      )
      
      showAlert({
        type: 'error',
        title: 'Action Failed',
        message: error instanceof Error ? error.message : 'An error occurred'
      })
    } finally {
      setLoadingActions(prev => {
        const next = new Set(prev)
        next.delete(action.id)
        return next
      })
    }
  }

  const quickActions: QuickAction[] = [
    {
      id: 'acknowledge',
      type: 'acknowledge',
      label: 'Acknowledge',
      icon: 'check-circle',
      keyboardShortcut: 'A',
      enabled: actions.some(a => a.type === 'acknowledge'),
      visible: true,
      requiresConfirmation: false,
      variant: 'primary'
    },
    {
      id: 'remediate',
      type: 'remediate',
      label: 'Remediate',
      icon: 'wrench',
      keyboardShortcut: 'R',
      enabled: actions.some(a => a.type === 'remediate'),
      visible: true,
      requiresConfirmation: true,
      variant: 'success'
    },
    {
      id: 'escalate',
      type: 'escalate',
      label: 'Escalate',
      icon: 'trending-up',
      keyboardShortcut: 'E',
      enabled: actions.some(a => a.type === 'escalate'),
      visible: true,
      requiresConfirmation: false,
      variant: 'warning'
    }
  ]

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      
      const key = e.key.toUpperCase()
      const action = quickActions.find(a => a.keyboardShortcut === key)
      
      if (action && action.enabled) {
        e.preventDefault()
        if (action.type === 'remediate') {
          setShowRemediation(true)
        } else if (action.type === 'escalate') {
          setShowEscalation(true)
        } else {
          handleAction(action)
        }
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [quickActions, incidentIds])

  const variantClasses = {
    fixed: 'fixed bottom-4 left-1/2 -translate-x-1/2 bg-background border shadow-lg rounded-lg p-2',
    inline: 'inline-flex',
    floating: 'fixed bottom-4 right-4 bg-background border shadow-lg rounded-lg p-2'
  }

  return (
    <>
      <div className={cn('flex items-center gap-2', variantClasses[variant], className)}>
        {incidentIds.length === 0 ? (
          <p className="text-sm text-muted-foreground px-3 py-2">
            Select incidents to perform actions
          </p>
        ) : (
          <>
            <ActionButton
              action={quickActions[0]}
              icon={CheckCircle}
              loading={loadingActions.has('acknowledge')}
              riskLevel="low"
              impactScope={{ users: incidentIds.length * 100 }}
              onActionExecute={async (actionId) => {
                await handleAction(quickActions[0])
              }}
            />
            
            <ActionButton
              action={quickActions[1]}
              icon={Wrench}
              loading={loadingActions.has('remediate')}
              riskLevel="medium"
              impactScope={{ 
                users: incidentIds.length * 1000,
                services: ['affected-service'],
                critical: incidentIds.length > 5
              }}
              onActionExecute={async (actionId) => {
                setShowRemediation(true)
              }}
            />
            
            <ActionButton
              action={quickActions[2]}
              icon={TrendingUp}
              loading={loadingActions.has('escalate')}
              riskLevel="high"
              impactScope={{ 
                users: incidentIds.length * 5000,
                services: ['critical-service'],
                critical: true 
              }}
              onActionExecute={async (actionId) => {
                setShowEscalation(true)
              }}
            />

            {variant === 'inline' && (
              <ActionButton
                action={{
                  id: 'more',
                  type: 'custom',
                  label: 'More',
                  enabled: true,
                  visible: true,
                  requiresConfirmation: false
                }}
                icon={MoreHorizontal}
                showShortcut={false}
                size="sm"
              />
            )}

            {incidentIds.length > 1 && (
              <div className="ml-2 flex items-center gap-1 text-sm text-muted-foreground">
                <AlertTriangle className="h-3 w-3" />
                <span>{incidentIds.length} incidents selected</span>
              </div>
            )}
          </>
        )}
      </div>

      <RemediationMenu
        open={showRemediation}
        onClose={() => setShowRemediation(false)}
        incidentIds={incidentIds}
        onRemediate={async (option) => {
          await handleAction({
            ...quickActions[1],
            metadata: { option }
          })
          setShowRemediation(false)
        }}
      />

      <EscalationDialog
        open={showEscalation}
        onClose={() => setShowEscalation(false)}
        incidentIds={incidentIds}
        onEscalate={async (request) => {
          await handleAction({
            ...quickActions[2],
            metadata: { request }
          })
          setShowEscalation(false)
        }}
      />
    </>
  )
}
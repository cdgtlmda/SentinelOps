'use client'

import { ButtonHTMLAttributes, forwardRef, useState } from 'react'
import { Loader2, LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { QuickAction } from '@/types/actions'
import { ConfirmationDialog } from '@/components/approvals'
import { useRiskCalculation, useApprovalWorkflow, useUndoManager, useAuditLog } from '@/hooks/use-approvals'
import { RiskLevel, ConfirmationDialogConfig } from '@/types/approvals'

interface ActionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  action: QuickAction
  icon?: LucideIcon
  loading?: boolean
  showShortcut?: boolean
  size?: 'sm' | 'md' | 'lg'
  requireApproval?: boolean
  riskLevel?: RiskLevel
  impactScope?: {
    users?: number
    services?: string[]
    critical?: boolean
  }
  onActionExecute?: (actionId: string, approvalData?: any) => Promise<void>
  onActionComplete?: (actionId: string, result: any) => void
}

export const ActionButton = forwardRef<HTMLButtonElement, ActionButtonProps>(
  ({ 
    action, 
    icon: Icon, 
    loading: externalLoading, 
    showShortcut = true, 
    size = 'md', 
    className,
    requireApproval = false,
    riskLevel,
    impactScope,
    onActionExecute,
    onActionComplete,
    ...props 
  }, ref) => {
    const [showConfirmation, setShowConfirmation] = useState(false)
    const [isExecuting, setIsExecuting] = useState(false)
    
    const { calculateRisk } = useRiskCalculation()
    const { createApprovalRequest, approveRequest } = useApprovalWorkflow()
    const { addUndoableAction } = useUndoManager()
    const { logAction } = useAuditLog()
    
    const loading = externalLoading || isExecuting

    const sizeClasses = {
      sm: 'px-2 py-1 text-xs gap-1',
      md: 'px-3 py-2 text-sm gap-2',
      lg: 'px-4 py-3 text-base gap-2'
    }

    const variantClasses = {
      default: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
      primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
      success: 'bg-green-600 text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600',
      warning: 'bg-yellow-600 text-white hover:bg-yellow-700 dark:bg-yellow-500 dark:hover:bg-yellow-600',
      danger: 'bg-red-600 text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600'
    }

    const handleClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault()
      
      // Determine if approval is needed
      const needsApproval = requireApproval || action.requiresConfirmation || 
        (riskLevel && ['high', 'critical'].includes(riskLevel))
      
      if (needsApproval) {
        setShowConfirmation(true)
      } else {
        await executeAction()
      }
    }

    const executeAction = async (approvalData?: any) => {
      setIsExecuting(true)
      const startTime = Date.now()
      
      try {
        // Log action start
        logAction(
          action.type,
          action.id,
          `Executing ${action.label}`,
          'success',
          undefined,
          { approvalData }
        )
        
        // Execute the action
        if (onActionExecute) {
          await onActionExecute(action.id, approvalData)
        }
        
        // Add to undo queue if applicable
        if (action.type !== 'comment' && action.type !== 'escalate') {
          addUndoableAction({
            id: `undo_${action.id}_${Date.now()}`,
            actionId: action.id,
            actionType: action.type,
            description: `Undo ${action.label}`,
            executedBy: 'current_user',
            executedAt: new Date(),
            undoDeadline: new Date(Date.now() + 30000), // 30 seconds
            undoHandler: async () => {
              console.log(`Undoing action: ${action.id}`)
              // Implement undo logic here
            },
            impactedResources: impactScope?.services || []
          })
        }
        
        // Log successful completion
        const duration = Date.now() - startTime
        logAction(
          action.type,
          action.id,
          `Completed ${action.label}`,
          'success',
          undefined,
          { duration }
        )
        
        onActionComplete?.(action.id, { success: true })
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
        
        onActionComplete?.(action.id, { success: false, error })
      } finally {
        setIsExecuting(false)
        setShowConfirmation(false)
      }
    }

    const handleConfirm = async (confirmationData?: any) => {
      // If high risk, create approval request
      const calculatedRisk = calculateRisk(
        action.type,
        impactScope || {},
        { successRate: 85 }
      )
      
      if (calculatedRisk.overallRisk === 'critical' || calculatedRisk.overallRisk === 'high') {
        const approvalRequest = await createApprovalRequest(
          action.type,
          `Request to ${action.label}`,
          calculatedRisk,
          { actionId: action.id, confirmationData }
        )
        
        // For demo purposes, auto-approve after creation
        // In real app, this would go through proper approval chain
        await approveRequest(approvalRequest.id, 'Auto-approved for demo', confirmationData)
      }
      
      await executeAction(confirmationData)
    }

    const confirmationConfig: ConfirmationDialogConfig = {
      title: `Confirm ${action.label}`,
      message: action.description || `Are you sure you want to ${action.label.toLowerCase()}?`,
      riskLevel: riskLevel || (action.variant === 'danger' ? 'high' : 'medium'),
      confirmationMethod: riskLevel === 'critical' ? 'mfa' : 
                         riskLevel === 'high' ? 'text_input' : 'checkbox',
      showRiskAssessment: true,
      showImpactSummary: true,
      requireExplicitConsent: riskLevel === 'critical' || riskLevel === 'high'
    }

    const riskAssessment = impactScope ? calculateRisk(
      action.type,
      impactScope,
      { successRate: 85 }
    ) : undefined

    return (
      <>
        <button
          ref={ref}
          className={cn(
            'inline-flex items-center justify-center rounded-md font-medium transition-colors',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
            'disabled:pointer-events-none disabled:opacity-50',
            sizeClasses[size],
            variantClasses[action.variant || 'default'],
            className
          )}
          disabled={!action.enabled || loading}
          title={action.tooltip || action.description}
          onClick={handleClick}
          {...props}
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : Icon ? (
            <Icon className="h-4 w-4" />
          ) : null}
          <span>{action.label}</span>
          {showShortcut && action.keyboardShortcut && (
            <kbd className="ml-1 rounded bg-black/10 px-1 py-0.5 text-xs font-mono dark:bg-white/10">
              {action.keyboardShortcut}
            </kbd>
          )}
        </button>
        
        <ConfirmationDialog
          open={showConfirmation}
          onOpenChange={setShowConfirmation}
          config={confirmationConfig}
          riskAssessment={riskAssessment}
          onConfirm={handleConfirm}
          onCancel={() => setShowConfirmation(false)}
          loading={isExecuting}
        />
      </>
    )
  }
)

ActionButton.displayName = 'ActionButton'
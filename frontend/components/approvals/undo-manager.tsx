'use client'

import { useState, useEffect } from 'react'
import { Undo2, Clock, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { UndoableAction, UndoStatus } from '@/types/approvals'
import { formatDistanceToNow } from 'date-fns'

interface UndoManagerProps {
  actions: UndoableAction[]
  onUndo: (actionId: string) => Promise<void>
  onClearExpired?: () => void
  maxHeight?: number
  className?: string
}

const statusConfig = {
  available: {
    icon: Undo2,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    badgeVariant: 'default' as const,
    label: 'Can Undo'
  },
  executing: {
    icon: Loader2,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    badgeVariant: 'default' as const,
    label: 'Undoing...'
  },
  completed: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    badgeVariant: 'secondary' as const,
    label: 'Undone'
  },
  expired: {
    icon: Clock,
    color: 'text-gray-500',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    badgeVariant: 'outline' as const,
    label: 'Expired'
  },
  failed: {
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    badgeVariant: 'destructive' as const,
    label: 'Failed'
  }
}

function UndoableActionItem({
  action,
  onUndo
}: {
  action: UndoableAction
  onUndo: (actionId: string) => Promise<void>
}) {
  const [timeLeft, setTimeLeft] = useState<number>(0)
  const [isUndoing, setIsUndoing] = useState(false)
  
  const config = statusConfig[action.status]
  const Icon = config.icon

  useEffect(() => {
    if (action.status !== 'available') return

    const interval = setInterval(() => {
      const remaining = action.undoDeadline.getTime() - Date.now()
      setTimeLeft(Math.max(0, remaining))
      
      if (remaining <= 0) {
        clearInterval(interval)
      }
    }, 100)

    return () => clearInterval(interval)
  }, [action.undoDeadline, action.status])

  const handleUndo = async () => {
    setIsUndoing(true)
    try {
      await onUndo(action.id)
    } catch (error) {
      console.error('Undo failed:', error)
    } finally {
      setIsUndoing(false)
    }
  }

  const progress = action.status === 'available' 
    ? (timeLeft / 30000) * 100 
    : action.status === 'executing' ? 50 : 0

  return (
    <div className={cn(
      "p-4 rounded-lg border transition-all",
      config.borderColor,
      config.bgColor,
      action.status === 'expired' && "opacity-60"
    )}>
      <div className="flex items-start gap-3">
        <div className={cn(
          "p-2 rounded-lg shrink-0",
          "bg-white shadow-sm"
        )}>
          <Icon className={cn(
            "w-4 h-4",
            config.color,
            action.status === 'executing' && "animate-spin"
          )} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <div>
              <h4 className="text-sm font-medium">{action.description}</h4>
              <p className="text-xs text-muted-foreground">
                {action.actionType} • {formatDistanceToNow(action.executedAt, { addSuffix: true })}
              </p>
            </div>
            <Badge variant={config.badgeVariant} className="text-xs shrink-0">
              {config.label}
            </Badge>
          </div>

          {action.impactedResources.length > 0 && (
            <div className="mt-2 text-xs text-muted-foreground">
              Affected: {action.impactedResources.join(', ')}
            </div>
          )}

          {action.status === 'available' && (
            <>
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Time remaining</span>
                  <span className={cn(
                    "font-mono",
                    timeLeft < 5000 && "text-red-600 font-medium"
                  )}>
                    {Math.ceil(timeLeft / 1000)}s
                  </span>
                </div>
                <Progress 
                  value={progress} 
                  className={cn(
                    "h-1.5 transition-all",
                    timeLeft < 5000 && "[&>div]:bg-red-600"
                  )}
                />
              </div>
              
              <Button
                size="sm"
                variant="secondary"
                className="mt-3 w-full"
                onClick={handleUndo}
                disabled={isUndoing || !action.canUndo}
              >
                {isUndoing ? (
                  <>
                    <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                    Undoing...
                  </>
                ) : (
                  <>
                    <Undo2 className="w-3 h-3 mr-2" />
                    Undo Action
                  </>
                )}
              </Button>
            </>
          )}

          {action.status === 'failed' && action.undoReason && (
            <Alert className="mt-3 p-2 text-xs border-red-200 bg-red-50">
              <AlertCircle className="h-3 w-3 text-red-600" />
              <AlertDescription className="text-red-800">
                {action.undoReason}
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    </div>
  )
}

export function UndoManager({
  actions,
  onUndo,
  onClearExpired,
  maxHeight = 400,
  className
}: UndoManagerProps) {
  const availableActions = actions.filter(a => a.status === 'available')
  const completedActions = actions.filter(a => a.status === 'completed')
  const expiredActions = actions.filter(a => a.status === 'expired')

  const sortedActions = [...actions].sort((a, b) => {
    // Sort by status priority, then by execution time
    const statusPriority = {
      executing: 0,
      available: 1,
      failed: 2,
      completed: 3,
      expired: 4
    }
    
    const aPriority = statusPriority[a.status]
    const bPriority = statusPriority[b.status]
    
    if (aPriority !== bPriority) {
      return aPriority - bPriority
    }
    
    return b.executedAt.getTime() - a.executedAt.getTime()
  })

  if (actions.length === 0) {
    return (
      <Card className={cn("", className)}>
        <CardContent className="py-8">
          <div className="text-center text-muted-foreground">
            <Undo2 className="w-8 h-8 mx-auto mb-2 opacity-20" />
            <p className="text-sm">No undoable actions</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Undo Manager</CardTitle>
            <CardDescription>
              {availableActions.length} action{availableActions.length !== 1 ? 's' : ''} can be undone
            </CardDescription>
          </div>
          {onClearExpired && expiredActions.length > 0 && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onClearExpired}
              className="text-xs"
            >
              Clear expired ({expiredActions.length})
            </Button>
          )}
        </div>
        
        {availableActions.length > 0 && (
          <Alert className="mt-3 p-3 border-blue-200 bg-blue-50">
            <Undo2 className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800 text-sm">
              Actions can be undone within 30 seconds of execution
            </AlertDescription>
          </Alert>
        )}
      </CardHeader>
      
      <CardContent className="px-3 pb-3">
        <ScrollArea className="pr-3" style={{ maxHeight }}>
          <div className="space-y-2">
            {sortedActions.map((action) => (
              <UndoableActionItem
                key={action.id}
                action={action}
                onUndo={onUndo}
              />
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
'use client'

import { useState } from 'react'
import { 
  Users, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  ChevronRight,
  MessageSquare,
  Timer,
  User,
  Shield
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Progress } from '@/components/ui/progress'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import { 
  ApprovalChain, 
  ApprovalLevel, 
  ApprovalRequest,
  ApprovalStatus,
  ApproverRole 
} from '@/types/approvals'
import { formatDistanceToNow } from 'date-fns'

interface ApprovalChainProps {
  request: ApprovalRequest
  chain?: ApprovalChain
  onApprove?: (levelId: number, comments?: string) => void
  onReject?: (levelId: number, reason: string) => void
  currentUserId?: string
  className?: string
}

const statusColors = {
  pending: { color: 'text-yellow-600', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-200' },
  approved: { color: 'text-green-600', bgColor: 'bg-green-50', borderColor: 'border-green-200' },
  rejected: { color: 'text-red-600', bgColor: 'bg-red-50', borderColor: 'border-red-200' },
  expired: { color: 'text-gray-600', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' },
  cancelled: { color: 'text-gray-600', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' },
  escalated: { color: 'text-orange-600', bgColor: 'bg-orange-50', borderColor: 'border-orange-200' }
}

function ApprovalLevelItem({
  level,
  request,
  isCurrentLevel,
  onApprove,
  onReject,
  currentUserId
}: {
  level: ApprovalLevel
  request: ApprovalRequest
  isCurrentLevel: boolean
  onApprove?: (comments?: string) => void
  onReject?: (reason: string) => void
  currentUserId?: string
}) {
  const [showActions, setShowActions] = useState(false)
  const [comments, setComments] = useState('')
  const [rejectReason, setRejectReason] = useState('')
  const [showReject, setShowReject] = useState(false)

  // Find approvals for this level
  const levelApprovals = request.approvals.filter(a => a.level === level.level)
  const approved = levelApprovals.filter(a => a.status === 'approved').length
  const rejected = levelApprovals.some(a => a.status === 'rejected')
  
  const progress = (approved / level.minApprovals) * 100
  const isComplete = approved >= level.minApprovals
  const isPending = isCurrentLevel && !isComplete && !rejected

  const canUserApprove = currentUserId && level.approvers.some(
    approver => approver.id === currentUserId || 
    approver.alternates?.includes(currentUserId)
  )

  const hasUserApproved = currentUserId && levelApprovals.some(
    a => a.approverId === currentUserId
  )

  const getLevelStatus = () => {
    if (rejected) return 'rejected'
    if (isComplete) return 'approved'
    if (isPending) return 'pending'
    return 'waiting'
  }

  const status = getLevelStatus()
  const statusConfig = status === 'waiting' 
    ? { color: 'text-gray-400', bgColor: 'bg-gray-50', borderColor: 'border-gray-200' }
    : statusColors[status as keyof typeof statusColors]

  const StatusIcon = {
    approved: CheckCircle,
    rejected: XCircle,
    pending: Clock,
    waiting: Clock
  }[status]

  return (
    <div className={cn(
      "relative",
      !isCurrentLevel && status === 'waiting' && "opacity-50"
    )}>
      <div className={cn(
        "p-4 rounded-lg border transition-all",
        statusConfig.borderColor,
        isPending && "shadow-sm border-2"
      )}>
        <div className="flex items-start gap-3">
          <div className={cn(
            "p-2 rounded-lg shrink-0",
            statusConfig.bgColor
          )}>
            <StatusIcon className={cn("w-4 h-4", statusConfig.color)} />
          </div>
          
          <div className="flex-1 space-y-3">
            <div>
              <div className="flex items-center justify-between">
                <h4 className="font-medium">
                  Level {level.level}: {level.name}
                </h4>
                <Badge 
                  variant={status === 'approved' ? 'secondary' : 'outline'}
                  className={cn(
                    "text-xs",
                    statusConfig.color,
                    statusConfig.bgColor
                  )}
                >
                  {status.toUpperCase()}
                </Badge>
              </div>
              
              <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {approved}/{level.minApprovals} approvals
                </span>
                {level.timeLimit && (
                  <span className="flex items-center gap-1">
                    <Timer className="w-3 h-3" />
                    {level.timeLimit} min limit
                  </span>
                )}
              </div>
            </div>

            <Progress value={progress} className="h-1.5" />

            <Collapsible open={showActions} onOpenChange={setShowActions}>
              <div className="flex items-center justify-between">
                <CollapsibleTrigger className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
                  <span>{level.approvers.length} approvers</span>
                  <ChevronRight className={cn(
                    "w-3 h-3 transition-transform",
                    showActions && "rotate-90"
                  )} />
                </CollapsibleTrigger>
                
                {isPending && canUserApprove && !hasUserApproved && (
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setShowReject(!showReject)}
                    >
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => onApprove?.(comments)}
                    >
                      Approve
                    </Button>
                  </div>
                )}
              </div>
              
              <CollapsibleContent className="mt-3 space-y-2">
                {level.approvers.map((approver) => {
                  const approval = levelApprovals.find(a => a.approverId === approver.id)
                  
                  return (
                    <div 
                      key={approver.id}
                      className="flex items-center gap-3 p-2 rounded-lg bg-muted/50"
                    >
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={`/avatars/${approver.id}.jpg`} />
                        <AvatarFallback>
                          {approver.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{approver.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {approver.type === 'role' ? `@${approver.name}` : approver.type}
                        </p>
                      </div>
                      
                      {approval && (
                        <div className="text-right">
                          <Badge 
                            variant={approval.status === 'approved' ? 'secondary' : 'destructive'}
                            className="text-xs"
                          >
                            {approval.status}
                          </Badge>
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDistanceToNow(approval.timestamp, { addSuffix: true })}
                          </p>
                        </div>
                      )}
                      
                      {!approval && isPending && (
                        <Badge variant="outline" className="text-xs">
                          Pending
                        </Badge>
                      )}
                    </div>
                  )
                })}
                
                {isPending && canUserApprove && !hasUserApproved && (
                  <div className="mt-3 space-y-3 border-t pt-3">
                    <div>
                      <label className="text-sm font-medium">Comments (optional)</label>
                      <Textarea
                        placeholder="Add any comments about your decision..."
                        value={comments}
                        onChange={(e) => setComments(e.target.value)}
                        className="mt-1"
                        rows={3}
                      />
                    </div>
                    
                    {showReject && (
                      <Alert className="border-red-200 bg-red-50">
                        <AlertCircle className="h-4 w-4 text-red-600" />
                        <AlertDescription>
                          <div className="space-y-2">
                            <p className="text-sm text-red-800">
                              Please provide a reason for rejection:
                            </p>
                            <Textarea
                              placeholder="Reason for rejection..."
                              value={rejectReason}
                              onChange={(e) => setRejectReason(e.target.value)}
                              className="mt-1"
                              rows={2}
                            />
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => onReject?.(rejectReason)}
                              disabled={!rejectReason}
                            >
                              Confirm Rejection
                            </Button>
                          </div>
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}
              </CollapsibleContent>
            </Collapsible>

            {levelApprovals.length > 0 && (
              <div className="space-y-2 border-t pt-3">
                {levelApprovals.map((approval) => (
                  <div 
                    key={approval.id}
                    className="flex items-start gap-2 text-sm"
                  >
                    <div className={cn(
                      "mt-0.5 w-4 h-4 shrink-0",
                      approval.status === 'approved' ? 'text-green-600' : 'text-red-600'
                    )}>
                      {approval.status === 'approved' ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p>
                        <span className="font-medium">{approval.approverName}</span>
                        <span className="text-muted-foreground">
                          {' '}
                          {approval.status} • {formatDistanceToNow(approval.timestamp, { addSuffix: true })}
                        </span>
                      </p>
                      {approval.comments && (
                        <p className="text-muted-foreground mt-1">
                          <MessageSquare className="w-3 h-3 inline mr-1" />
                          {approval.comments}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      
    </div>
  )
}

export function ApprovalChainVisualization({
  request,
  chain,
  onApprove,
  onReject,
  currentUserId,
  className
}: ApprovalChainProps) {
  // Generate a default chain if not provided
  const defaultChain: ApprovalChain = chain || {
    id: 'default',
    name: 'Standard Approval',
    description: 'Default approval workflow',
    levels: [
      {
        level: 1,
        name: 'Initial Approval',
        approvers: [
          { id: 'user1', name: 'Team Lead', type: 'role', level: 1, required: true },
          { id: 'user2', name: 'Senior Engineer', type: 'role', level: 1, required: false }
        ],
        minApprovals: 1,
        timeLimit: 60,
        parallel: true
      },
      {
        level: 2,
        name: 'Management Approval',
        approvers: [
          { id: 'user3', name: 'Engineering Manager', type: 'role', level: 2, required: true }
        ],
        minApprovals: 1,
        timeLimit: 120,
        parallel: false
      }
    ],
    parallel: false,
    createdBy: 'system',
    createdAt: new Date(),
    active: true
  }

  const activeChain = chain || defaultChain
  const currentLevel = request.currentLevel

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">{activeChain.name}</CardTitle>
              <CardDescription>
                {activeChain.description}
              </CardDescription>
            </div>
          </div>
          <Badge variant={request.status === 'approved' ? 'secondary' : 'outline'}>
            {request.status.toUpperCase()}
          </Badge>
        </div>
        
        {request.expiresAt && request.status === 'pending' && (
          <Alert className="mt-4 p-3 border-yellow-200 bg-yellow-50">
            <Clock className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800 text-sm">
              Expires {formatDistanceToNow(request.expiresAt, { addSuffix: true })}
            </AlertDescription>
          </Alert>
        )}
      </CardHeader>
      
      <CardContent>
        <ScrollArea className="h-full">
          <div className="space-y-8 relative">
            {activeChain.levels.map((level, index) => (
              <div key={level.level} className="relative">
                <ApprovalLevelItem
                  level={level}
                  request={request}
                  isCurrentLevel={currentLevel === level.level}
                  onApprove={(comments) => onApprove?.(level.level, comments)}
                  onReject={(reason) => onReject?.(level.level, reason)}
                  currentUserId={currentUserId}
                />
                {/* Connector line to next level */}
                {index < activeChain.levels.length - 1 && (
                  <div className="absolute left-1/2 -translate-x-1/2 w-0.5 h-8 bg-gray-200 -bottom-8 z-0" />
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
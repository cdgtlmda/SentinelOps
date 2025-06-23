'use client'

import { useState } from 'react'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Undo2, 
  FileText,
  Zap,
  Server,
  Users
} from 'lucide-react'
import { 
  ConfirmationDialog,
  RiskWarning,
  UndoManager,
  AuditTrail,
  ApprovalChainVisualization
} from '@/components/approvals'
import { ActionButton } from '@/components/actions/action-button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { 
  useApprovalWorkflow, 
  useRiskCalculation, 
  useUndoManager, 
  useAuditLog,
  useApprovalChain
} from '@/hooks/use-approvals'
import { QuickAction } from '@/types/actions'
import { ConfirmationDialogConfig, RiskLevel } from '@/types/approvals'

export default function ApprovalsDemo() {
  const [showDialog, setShowDialog] = useState(false)
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<RiskLevel>('medium')
  
  const { calculateRisk } = useRiskCalculation()
  const { approvalRequests, createApprovalRequest, approveRequest, rejectRequest } = useApprovalWorkflow()
  const { undoQueue, addUndoableAction, executeUndo } = useUndoManager()
  const { entries, logAction } = useAuditLog()
  const { chains, createChain } = useApprovalChain()

  // Demo actions
  const demoActions: QuickAction[] = [
    {
      id: 'restart-service',
      type: 'remediate',
      label: 'Restart Service',
      description: 'Restart the authentication service',
      icon: 'rotate-cw',
      enabled: true,
      visible: true,
      requiresConfirmation: true,
      variant: 'warning'
    },
    {
      id: 'scale-up',
      type: 'remediate',
      label: 'Scale Up Resources',
      description: 'Increase compute resources by 50%',
      icon: 'trending-up',
      enabled: true,
      visible: true,
      requiresConfirmation: true,
      variant: 'primary'
    },
    {
      id: 'failover',
      type: 'remediate',
      label: 'Initiate Failover',
      description: 'Switch to backup datacenter',
      icon: 'shield',
      enabled: true,
      visible: true,
      requiresConfirmation: true,
      variant: 'danger'
    }
  ]

  const dialogConfig: ConfirmationDialogConfig = {
    title: 'Confirm Critical Action',
    message: 'This action will affect production systems and may cause temporary service disruption.',
    riskLevel: selectedRiskLevel,
    confirmationMethod: selectedRiskLevel === 'critical' ? 'mfa' : 
                       selectedRiskLevel === 'high' ? 'text_input' : 'checkbox',
    confirmationPrompt: selectedRiskLevel === 'high' ? 'Type "CONFIRM" to proceed' : undefined,
    confirmationPattern: selectedRiskLevel === 'high' ? /^CONFIRM$/i : undefined,
    showRiskAssessment: true,
    showImpactSummary: true,
    requireExplicitConsent: ['high', 'critical'].includes(selectedRiskLevel)
  }

  const riskAssessment = calculateRisk(
    'remediate',
    {
      users: selectedRiskLevel === 'critical' ? 50000 : 
             selectedRiskLevel === 'high' ? 10000 : 
             selectedRiskLevel === 'medium' ? 1000 : 100,
      services: ['auth-service', 'api-gateway', 'database'],
      critical: selectedRiskLevel === 'critical'
    },
    {
      successRate: selectedRiskLevel === 'critical' ? 60 : 85,
      lastIncident: selectedRiskLevel === 'high' ? 
        new Date(Date.now() - 3 * 24 * 60 * 60 * 1000) : undefined
    }
  )

  const handleActionExecute = async (actionId: string) => {
    // Simulate action execution
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Log the action
    logAction(
      'remediate',
      actionId,
      `Executed ${demoActions.find(a => a.id === actionId)?.label}`,
      'success',
      [{ field: 'status', oldValue: 'down', newValue: 'up', changeType: 'update' }],
      { executedFrom: 'demo' }
    )
    
    // Add to undo queue
    addUndoableAction({
      id: `undo_${actionId}_${Date.now()}`,
      actionId,
      actionType: 'remediate',
      description: `Undo ${demoActions.find(a => a.id === actionId)?.label}`,
      executedBy: 'demo_user',
      executedAt: new Date(),
      undoDeadline: new Date(Date.now() + 30000),
      undoHandler: async () => {
        console.log(`Undoing action: ${actionId}`)
        await new Promise(resolve => setTimeout(resolve, 1000))
      },
      impactedResources: ['service-1', 'service-2']
    })
  }

  // Create a sample approval request
  const sampleApprovalRequest = approvalRequests[0] || {
    id: 'demo_request',
    actionId: 'demo_action',
    actionType: 'remediate' as const,
    requestedBy: 'demo_user',
    requestedAt: new Date(),
    description: 'Scale up resources to handle increased load',
    riskAssessment,
    requirement: {
      id: 'req_demo',
      actionType: 'remediate' as const,
      riskLevel: 'high' as const,
      confirmationMethod: 'manager_approval' as const,
      timeLimit: 60
    },
    status: 'pending' as const,
    approvals: [],
    currentLevel: 1,
    expiresAt: new Date(Date.now() + 60 * 60 * 1000)
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Approval Workflows Demo</h1>
        <p className="text-muted-foreground">
          Comprehensive approval system with risk assessment, undo capabilities, and audit trails
        </p>
      </div>

      <Tabs defaultValue="confirmation" className="space-y-6">
        <TabsList className="grid grid-cols-5 w-full max-w-3xl mx-auto">
          <TabsTrigger value="confirmation">Confirmation</TabsTrigger>
          <TabsTrigger value="risk">Risk Warning</TabsTrigger>
          <TabsTrigger value="undo">Undo Manager</TabsTrigger>
          <TabsTrigger value="audit">Audit Trail</TabsTrigger>
          <TabsTrigger value="chain">Approval Chain</TabsTrigger>
        </TabsList>

        <TabsContent value="confirmation" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Confirmation Dialogs</CardTitle>
              <CardDescription>
                Risk-aware confirmation dialogs with multiple verification methods
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Risk Level Selection</h3>
                <div className="flex gap-2">
                  {(['low', 'medium', 'high', 'critical'] as RiskLevel[]).map((level) => (
                    <Button
                      key={level}
                      variant={selectedRiskLevel === level ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedRiskLevel(level)}
                    >
                      {level.toUpperCase()}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-medium">Demo Actions</h3>
                <div className="grid grid-cols-3 gap-4">
                  {demoActions.map((action) => (
                    <ActionButton
                      key={action.id}
                      action={action}
                      riskLevel={selectedRiskLevel}
                      impactScope={{
                        users: 10000,
                        services: ['auth', 'api', 'db'],
                        critical: selectedRiskLevel === 'critical'
                      }}
                      onActionExecute={handleActionExecute}
                    />
                  ))}
                </div>
              </div>

              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  Actions automatically show confirmation dialogs based on risk level.
                  Higher risk levels require stronger confirmation methods.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risk" className="space-y-6">
          <div className="grid gap-6">
            <RiskWarning 
              assessment={riskAssessment}
              showDetails={true}
              showMitigations={true}
            />

            <Card>
              <CardHeader>
                <CardTitle>Risk Assessment Features</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Risk Factors</h4>
                    <ul className="text-sm space-y-1 text-muted-foreground">
                      <li>• User impact analysis</li>
                      <li>• Service criticality assessment</li>
                      <li>• Historical performance data</li>
                      <li>• Recent incident tracking</li>
                    </ul>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Mitigation Strategies</h4>
                    <ul className="text-sm space-y-1 text-muted-foreground">
                      <li>• Gradual rollout options</li>
                      <li>• Monitoring alerts</li>
                      <li>• Quick rollback procedures</li>
                      <li>• Incident response teams</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="undo" className="space-y-6">
          <UndoManager 
            actions={undoQueue}
            onUndo={executeUndo}
            maxHeight={500}
          />

          <Card>
            <CardHeader>
              <CardTitle>Undo Capabilities</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                <Undo2 className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Actions can be undone within 30 seconds of execution
                </span>
              </div>
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Execute some actions from the Confirmation tab to see them appear in the undo queue.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="space-y-6">
          <AuditTrail 
            entries={entries}
            showExport={true}
            maxHeight={600}
          />

          <Card>
            <CardHeader>
              <CardTitle>Audit Trail Features</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="space-y-1">
                  <FileText className="h-4 w-4 text-muted-foreground mb-2" />
                  <p className="font-medium">Complete History</p>
                  <p className="text-muted-foreground">All actions logged</p>
                </div>
                <div className="space-y-1">
                  <Users className="h-4 w-4 text-muted-foreground mb-2" />
                  <p className="font-medium">User Attribution</p>
                  <p className="text-muted-foreground">Track who did what</p>
                </div>
                <div className="space-y-1">
                  <Zap className="h-4 w-4 text-muted-foreground mb-2" />
                  <p className="font-medium">Real-time Updates</p>
                  <p className="text-muted-foreground">Live audit logging</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="chain" className="space-y-6">
          <ApprovalChainVisualization
            request={sampleApprovalRequest}
            currentUserId="user1"
            onApprove={(level, comments) => {
              console.log(`Approved level ${level} with comments: ${comments}`)
            }}
            onReject={(level, reason) => {
              console.log(`Rejected level ${level} with reason: ${reason}`)
            }}
          />

          <Card>
            <CardHeader>
              <CardTitle>Approval Chain Features</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Multi-level Approvals</h4>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    <li>• Sequential approval levels</li>
                    <li>• Parallel approver support</li>
                    <li>• Time limits per level</li>
                    <li>• Escalation policies</li>
                  </ul>
                </div>
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Tracking & Visibility</h4>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    <li>• Real-time status updates</li>
                    <li>• Approver comments</li>
                    <li>• Decision history</li>
                    <li>• Progress visualization</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
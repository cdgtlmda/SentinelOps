# Approval Workflows Documentation

## Overview

The SentinelOps approval workflow system provides comprehensive controls for managing high-risk actions, ensuring proper authorization, maintaining audit trails, and enabling undo capabilities for reversible operations.

## Components

### 1. Confirmation Dialog (`confirmation-dialog.tsx`)

A risk-aware confirmation dialog that adapts its verification method based on the risk level of the action.

**Features:**
- Dynamic confirmation methods (checkbox, text input, MFA, manager approval)
- Risk level visualization (low, medium, high, critical)
- Impact summary display
- Customizable confirmation prompts
- Loading states and validation

**Usage:**
```tsx
<ConfirmationDialog
  open={showConfirmation}
  onOpenChange={setShowConfirmation}
  config={{
    title: 'Confirm Action',
    message: 'This will affect production systems',
    riskLevel: 'high',
    confirmationMethod: 'text_input',
    showRiskAssessment: true,
    showImpactSummary: true
  }}
  riskAssessment={calculatedRisk}
  onConfirm={handleConfirm}
  onCancel={handleCancel}
/>
```

### 2. Risk Warning (`risk-warning.tsx`)

Comprehensive risk assessment display with factors, mitigations, and historical data.

**Features:**
- Risk factor categorization
- Probability and impact visualization
- Mitigation strategy suggestions
- Historical performance metrics
- Visual risk score indicator

**Risk Categories:**
- User Impact
- Service Criticality
- Historical Performance
- Incident History
- Financial Impact
- Security Concerns
- Time Sensitivity

### 3. Undo Manager (`undo-manager.tsx`)

Time-limited undo capabilities for reversible actions.

**Features:**
- 30-second undo window
- Real-time countdown
- Action queuing
- Status tracking (available, executing, completed, expired, failed)
- Dependency management
- Batch undo support

**Supported Actions:**
- Service restarts
- Configuration changes
- Resource scaling
- Permission modifications
- Non-destructive remediation

### 4. Audit Trail (`audit-trail.tsx`)

Complete audit logging with search, filter, and export capabilities.

**Features:**
- Real-time action logging
- User attribution
- Change tracking
- Advanced filtering (action type, result, date range)
- CSV export
- Expandable details view
- Metadata storage

**Logged Information:**
- Timestamp
- User details
- Action type and ID
- Description
- Result (success/failure/partial)
- Duration
- Changes made
- Error messages

### 5. Approval Chain (`approval-chain.tsx`)

Multi-level approval workflow visualization and management.

**Features:**
- Sequential/parallel approval levels
- Role-based approvers
- Progress tracking
- Time limits and escalation
- Approver comments
- Visual workflow display
- Real-time status updates

**Approval Levels:**
- Initial team approval
- Management approval
- Security review
- Executive sign-off

## Hooks

### `useApprovalWorkflow()`
Manages approval requests and status updates.

```tsx
const { 
  approvalRequests,
  createApprovalRequest,
  approveRequest,
  rejectRequest,
  loading,
  error
} = useApprovalWorkflow()
```

### `useRiskCalculation()`
Calculates risk assessment based on action parameters.

```tsx
const { calculateRisk } = useRiskCalculation()

const assessment = calculateRisk(
  actionType,
  { users: 10000, services: ['api'], critical: true },
  { successRate: 85, lastIncident: new Date() }
)
```

### `useUndoManager()`
Manages the undo queue and execution.

```tsx
const { 
  undoQueue,
  addUndoableAction,
  executeUndo,
  clearExpired
} = useUndoManager()
```

### `useAuditLog()`
Handles audit logging and filtering.

```tsx
const { 
  entries,
  logAction,
  setFilter
} = useAuditLog()
```

### `useApprovalChain()`
Manages approval chain configuration and progression.

```tsx
const {
  chains,
  activeChainId,
  createChain,
  getNextApprovers
} = useApprovalChain()
```

## Integration

### Action Button Integration

The `ActionButton` component has been enhanced to support approval workflows:

```tsx
<ActionButton
  action={action}
  riskLevel="high"
  requireApproval={true}
  impactScope={{
    users: 10000,
    services: ['auth-service'],
    critical: true
  }}
  onActionExecute={handleExecute}
  onActionComplete={handleComplete}
/>
```

### Quick Action Bar Integration

The quick action bar automatically integrates approval workflows:
- Risk assessment for each action
- Automatic confirmation dialogs
- Undo queue management
- Audit logging
- Impact-based risk levels

## Risk Levels

### Low Risk
- < 1,000 users affected
- Non-critical services
- High success rate (> 90%)
- Simple checkbox confirmation

### Medium Risk
- 1,000 - 10,000 users affected
- Important services
- Good success rate (80-90%)
- Text input confirmation

### High Risk
- 10,000 - 50,000 users affected
- Critical services
- Moderate success rate (60-80%)
- MFA confirmation required

### Critical Risk
- > 50,000 users affected
- Core infrastructure
- Low success rate (< 60%)
- Manager approval required

## Compliance Features

### SOC 2 Compliance
- Complete audit trails
- User attribution
- Change tracking
- Access controls

### GDPR Compliance
- Data retention controls
- User consent tracking
- Right to be forgotten support
- Audit log privacy controls

### HIPAA Compliance
- PHI access logging
- Minimum necessary access
- Audit trail encryption
- User activity monitoring

## Best Practices

1. **Always assess risk** before executing high-impact actions
2. **Use appropriate confirmation methods** based on risk level
3. **Log all actions** for audit compliance
4. **Implement undo handlers** for reversible operations
5. **Set reasonable time limits** for approvals and undo windows
6. **Document approval chains** clearly
7. **Test rollback procedures** regularly
8. **Monitor approval metrics** for bottlenecks

## Configuration

### Approval Workflow Configuration

```typescript
const config: ApprovalWorkflowConfig = {
  enabled: true,
  defaultTimeLimit: 60, // minutes
  requireApprovalFor: {
    riskLevels: ['high', 'critical'],
    actionTypes: ['remediate', 'escalate'],
    remediationTypes: ['restart_service', 'failover']
  },
  autoApprovalRules: [...],
  notificationSettings: {
    channels: ['email', 'slack'],
    reminderIntervals: [15, 30, 45],
    escalationThreshold: 50
  },
  undoSettings: {
    enabled: true,
    defaultTimeLimit: 30,
    excludeActions: ['comment', 'escalate']
  },
  auditSettings: {
    retentionDays: 365,
    includeSystemActions: true,
    sensitiveFields: ['password', 'token']
  }
}
```

## Demo

Visit `/approvals-demo` to see all approval workflow components in action with interactive examples.
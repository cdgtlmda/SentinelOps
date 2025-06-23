# Database Schema Reference

**Last Updated**: June 11, 2025

## Overview

SentinelOps uses Google Firestore as its primary database for storing incidents, agent state, rules, and system configurations. This document provides a comprehensive reference for all Firestore collections and their schemas.

## Collections

### 1. incidents

Stores security incidents detected by the Detection Agent.

```typescript
interface Incident {
  id: string;                          // Auto-generated Firestore ID
  incident_id: string;                 // Unique incident identifier
  timestamp: Timestamp;                // Detection time
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  type: string;                        // Incident type (e.g., 'suspicious_login', 'ddos_attack')
  source: string;                      // Detection source
  affected_resources: string[];        // List of affected GCP resources
  metadata: {
    ip_addresses?: string[];
    user_accounts?: string[];
    gcp_projects?: string[];
    regions?: string[];
    [key: string]: any;              // Additional metadata
  };
  status: 'OPEN' | 'INVESTIGATING' | 'REMEDIATING' | 'RESOLVED' | 'FALSE_POSITIVE';
  created_at: Timestamp;
  updated_at: Timestamp;
  assigned_to?: string;                // Agent or human assignee
  resolution?: {
    resolved_at: Timestamp;
    resolved_by: string;
    resolution_notes: string;
    actions_taken: string[];
  };
}
```

**Indexes**:
- `status, created_at DESC`
- `severity, created_at DESC`
- `type, created_at DESC`
- `assigned_to, status, created_at DESC`

### 2. agent_state

Tracks the state and health of each agent in the system.

```typescript
interface AgentState {
  agent_id: string;                    // Primary key (e.g., 'detection-agent-01')
  agent_type: 'detection' | 'analysis' | 'remediation' | 'communication' | 'orchestrator';
  status: 'ACTIVE' | 'IDLE' | 'PROCESSING' | 'ERROR' | 'OFFLINE';
  last_heartbeat: Timestamp;
  current_task?: {
    task_id: string;
    incident_id?: string;
    started_at: Timestamp;
    progress: number;                  // 0-100
  };
  health_metrics: {
    cpu_usage: number;                 // Percentage
    memory_usage: number;              // Percentage
    error_rate: number;                // Errors per minute
    processing_time_avg: number;       // Milliseconds
  };
  configuration: {
    version: string;
    features_enabled: string[];
    rate_limits: Map<string, number>;
  };
  created_at: Timestamp;
  updated_at: Timestamp;
}
```

**Indexes**:
- `agent_type, status`
- `last_heartbeat DESC`

### 3. rules

Stores detection and response rules.

```typescript
interface Rule {
  rule_id: string;                     // Primary key
  name: string;
  description: string;
  type: 'detection' | 'correlation' | 'response';
  enabled: boolean;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  conditions: {
    query?: string;                    // BigQuery SQL
    patterns?: RegexPattern[];
    thresholds?: ThresholdCondition[];
    time_window?: number;              // Seconds
  };
  actions: {
    notify?: string[];                 // Notification channels
    remediate?: RemediationAction[];
    escalate?: boolean;
  };
  metadata: {
    created_by: string;
    tags: string[];
    category: string;
    false_positive_rate?: number;
  };
  created_at: Timestamp;
  updated_at: Timestamp;
  last_triggered?: Timestamp;
  trigger_count: number;
}

interface RegexPattern {
  field: string;
  pattern: string;
  flags?: string;
}

interface ThresholdCondition {
  metric: string;
  operator: '>' | '<' | '>=' | '<=' | '==' | '!=';
  value: number;
}

interface RemediationAction {
  type: string;
  parameters: Map<string, any>;
  requires_approval: boolean;
}
```

**Indexes**:
- `enabled, type`
- `severity, enabled`
- `last_triggered DESC`

### 4. workflows

Tracks multi-agent workflow execution.

```typescript
interface Workflow {
  workflow_id: string;                 // Primary key
  incident_id: string;
  status: 'INITIATED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  steps: WorkflowStep[];
  current_step: number;
  created_at: Timestamp;
  updated_at: Timestamp;
  completed_at?: Timestamp;
  error?: {
    step: number;
    agent: string;
    message: string;
    timestamp: Timestamp;
  };
}

interface WorkflowStep {
  step_id: string;
  agent: string;
  action: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  input: Map<string, any>;
  output?: Map<string, any>;
  started_at?: Timestamp;
  completed_at?: Timestamp;
  duration_ms?: number;
}
```

**Indexes**:
- `incident_id, created_at DESC`
- `status, created_at DESC`

### 5. analysis_results

Stores analysis results from the Analysis Agent.

```typescript
interface AnalysisResult {
  analysis_id: string;                 // Primary key
  incident_id: string;
  analyzed_by: string;                 // Agent ID
  analysis_type: 'root_cause' | 'impact' | 'threat_intel' | 'correlation';
  confidence_score: number;            // 0-1
  findings: {
    summary: string;
    details: string;
    indicators: Indicator[];
    recommendations: Recommendation[];
  };
  context: {
    related_incidents?: string[];
    historical_patterns?: Pattern[];
    external_references?: string[];
  };
  created_at: Timestamp;
  ttl: Timestamp;                      // Time to live for caching
}

interface Indicator {
  type: string;
  value: string;
  confidence: number;
}

interface Recommendation {
  action: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  reasoning: string;
  estimated_impact: string;
}

interface Pattern {
  pattern_type: string;
  occurrences: number;
  time_range: {
    start: Timestamp;
    end: Timestamp;
  };
}
```

**Indexes**:
- `incident_id, created_at DESC`
- `analysis_type, created_at DESC`
- `ttl` (for TTL policy)

### 6. remediation_history

Tracks all remediation actions taken.

```typescript
interface RemediationHistory {
  action_id: string;                   // Primary key
  incident_id: string;
  action_type: string;                 // e.g., 'block_ip', 'isolate_vm'
  target_resource: string;
  executed_by: string;                 // Agent ID
  status: 'PENDING' | 'EXECUTING' | 'COMPLETED' | 'FAILED' | 'ROLLED_BACK';
  dry_run: boolean;
  parameters: Map<string, any>;
  result?: {
    success: boolean;
    message: string;
    changes_made?: string[];
    rollback_info?: Map<string, any>;
  };
  approval?: {
    required: boolean;
    approved_by?: string;
    approved_at?: Timestamp;
  };
  executed_at: Timestamp;
  completed_at?: Timestamp;
  duration_ms?: number;
}
```

**Indexes**:
- `incident_id, executed_at DESC`
- `action_type, executed_at DESC`
- `status, executed_at DESC`

### 7. notifications

Tracks all notifications sent by the Communication Agent.

```typescript
interface Notification {
  notification_id: string;             // Primary key
  incident_id?: string;
  type: 'incident' | 'alert' | 'summary' | 'escalation';
  channel: 'slack' | 'email' | 'sms' | 'webhook';
  recipient: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'PENDING' | 'SENT' | 'DELIVERED' | 'FAILED';
  content: {
    subject?: string;
    body: string;
    attachments?: Attachment[];
    metadata?: Map<string, any>;
  };
  attempts: number;
  last_attempt?: Timestamp;
  error?: string;
  created_at: Timestamp;
  sent_at?: Timestamp;
  delivered_at?: Timestamp;
}

interface Attachment {
  name: string;
  type: string;
  size: number;
  url?: string;
}
```

**Indexes**:
- `incident_id, created_at DESC`
- `channel, status, created_at DESC`
- `recipient, created_at DESC`

### 8. system_config

Stores system-wide configuration.

```typescript
interface SystemConfig {
  config_id: string;                   // Primary key (e.g., 'global', 'agent-specific-id')
  scope: 'global' | 'agent' | 'feature';
  agent_id?: string;                   // If scope is 'agent'
  settings: {
    [key: string]: any;
  };
  version: number;
  updated_by: string;
  updated_at: Timestamp;
  change_history: ConfigChange[];
}

interface ConfigChange {
  version: number;
  changed_by: string;
  changed_at: Timestamp;
  changes: Map<string, {
    old_value: any;
    new_value: any;
  }>;
}
```

**Indexes**:
- `scope, agent_id`
- `updated_at DESC`

## Best Practices

### 1. Document Structure
- Keep documents under 1MB
- Use subcollections for large nested data
- Denormalize data for read performance

### 2. Query Optimization
- Create composite indexes for complex queries
- Use collection group queries sparingly
- Implement pagination for large result sets

### 3. Security Rules
```javascript
// Example security rule
match /incidents/{incident} {
  allow read: if request.auth != null;
  allow write: if request.auth != null && 
    request.auth.token.role in ['admin', 'agent'];
}
```

### 4. Data Retention
- Implement TTL for temporary data (analysis cache)
- Archive old incidents to Cloud Storage
- Use scheduled Cloud Functions for cleanup

### 5. Monitoring
- Track document read/write counts
- Monitor index usage
- Set up alerts for quota limits

## Migration and Versioning

### Schema Updates
1. Use versioned document structures
2. Implement backward compatibility
3. Run migrations in Cloud Functions
4. Test with production data snapshots

### Example Migration
```typescript
// Migrate incidents from v1 to v2
async function migrateIncidents() {
  const batch = firestore.batch();
  const incidents = await firestore
    .collection('incidents')
    .where('schema_version', '==', 1)
    .get();
    
  incidents.forEach(doc => {
    batch.update(doc.ref, {
      schema_version: 2,
      metadata: {
        ...doc.data().metadata,
        migrated_at: Timestamp.now()
      }
    });
  });
  
  await batch.commit();
}
```

## Performance Considerations

### Read Performance
- Use composite indexes for multi-field queries
- Implement client-side caching
- Use Firestore bundles for static data

### Write Performance
- Batch writes when possible (max 500 ops)
- Use distributed counters for high-frequency updates
- Implement exponential backoff for retries

### Cost Optimization
- Monitor document reads/writes
- Use field masks to reduce bandwidth
- Archive old data to reduce active storage
- Implement efficient query patterns

## Related Documentation
- [Firestore Indexes Reference](./firestore-indexes.md)
- [API Configuration Reference](../03-deployment/configuration/comprehensive-config-reference.md)
- [Database Schema Guide](../03-deployment/configuration/database-schema-guide.md)
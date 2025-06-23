# Data Flow Between Agents

## Overview

This document describes how data flows between the different agents in the SentinelOps system using the Google Agent Development Kit (ADK) framework. Each agent has specific inputs, processing logic, and outputs that contribute to the overall security incident response workflow.

## Agent Communication Protocol

All agents communicate using ADK's transfer system:

1. **Transfer Mechanism**: ADK TransferToAgentTool classes for agent-to-agent communication
2. **Context Passing**: Tool context carries incident data and metadata between agents
3. **Serialization**: Automatic handling by ADK framework
4. **Error Handling**: Built-in ADK error handling and recovery

## Core Data Structures

### SecurityEvent (passed via Tool Context)
```python
{
    "id": "evt-uuid-12345",
    "correlation_id": "corr-uuid-67890",
    "timestamp": "2024-01-01T12:00:00Z",
    "type": "security_incident",
    "source": "detection_agent",
    "severity": "high",
    "data": {
        "incident_type": "unauthorized_access",
        "resource": "projects/my-project/instances/web-server-1",
        "details": {...}
    },
    "metadata": {
        "agent_version": "1.0.0",
        "processing_time_ms": 150
    }
}
```

### ADK Tool Context
```python
{
    "session_id": "session-uuid-12345",
    "correlation_id": "corr-uuid-67890",
    "source_agent": "detection_agent",
    "target_agent": "analysis_agent",
    "timestamp": "2024-01-01T12:00:00Z",
    "transfer_type": "incident_detected",
    "payload": {...},
    "context": {
        "priority": "high",
        "ttl": 3600
    }
}
```

## Data Flow Sequences

### 1. Detection → Orchestrator → Analysis

**Flow Description:**
When the Detection Agent identifies a potential security incident, it creates an event and sends it to the Orchestrator for routing.

**Data Transformation:**
```
Detection Agent Output:
{
    "incident_id": "INC-20240101-001",
    "detection_time": "2024-01-01T12:00:00Z",
    "detection_rules": ["rule_1", "rule_2"],
    "confidence_score": 0.95,
    "raw_events": [
        {
            "log_entry": "...",
            "source": "cloud_logging",
            "timestamp": "..."
        }
    ],
    "affected_resources": [
        "projects/my-project/instances/web-server-1"
    ],
    "anomaly_indicators": {
        "unusual_ip": "192.168.1.100",
        "suspicious_commands": ["sudo rm -rf /"],
        "time_of_activity": "02:00 AM"
    }
}

↓ Orchestrator Processing ↓

Analysis Agent Input:
{
    "incident_id": "INC-20240101-001",
    "context": {
        "historical_incidents": [...],
        "resource_metadata": {...},
        "threat_intelligence": {...}
    },
    "detection_data": {...}, // Original detection data
    "analysis_request": {
        "requested_analyses": ["root_cause", "impact", "recommendations"],
        "urgency": "high"
    }
}
```

### 2. Analysis → Orchestrator → Remediation

**Flow Description:**
After analyzing an incident, the Analysis Agent sends recommendations to the Orchestrator, which determines if automated remediation should proceed.

**Data Transformation:**
```
Analysis Agent Output:
{
    "incident_id": "INC-20240101-001",
    "analysis_time": "2024-01-01T12:05:00Z",
    "severity_assessment": {
        "level": "critical",
        "score": 9.5,
        "factors": ["data_exposure", "privilege_escalation"]
    },
    "root_cause": {
        "type": "compromised_credentials",
        "confidence": 0.85,
        "evidence": [...]
    },
    "impact_analysis": {
        "affected_services": ["web", "database"],
        "data_at_risk": "customer_records",
        "business_impact": "high"
    },
    "recommendations": [
        {
            "action": "isolate_instance",
            "priority": 1,
            "automated": true,
            "risk_level": "low"
        },
        {
            "action": "revoke_credentials",
            "priority": 2,
            "automated": true,
            "risk_level": "low"
        },
        {
            "action": "forensic_snapshot",
            "priority": 3,
            "automated": false,
            "risk_level": "medium"
        }
    ]
}

↓ Orchestrator Decision Logic ↓

Remediation Agent Input:
{
    "incident_id": "INC-20240101-001",
    "approved_actions": [
        {
            "action": "isolate_instance",
            "target": "projects/my-project/instances/web-server-1",
            "parameters": {
                "method": "firewall_rule",
                "allow_management_access": true
            }
        },
        {
            "action": "revoke_credentials",
            "target": "serviceAccount:compromised-sa@project.iam",
            "parameters": {
                "revoke_keys": true,
                "disable_account": true
            }
        }
    ],
    "execution_constraints": {
        "dry_run": false,
        "max_execution_time": 300,
        "rollback_on_error": true
    }
}
```

### 3. Remediation → Orchestrator → Communication

**Flow Description:**
After executing remediation actions, the results are sent to the Communication Agent for stakeholder notification.

**Data Transformation:**
```
Remediation Agent Output:
{
    "incident_id": "INC-20240101-001",
    "execution_time": "2024-01-01T12:10:00Z",
    "actions_taken": [
        {
            "action": "isolate_instance",
            "status": "success",
            "execution_time_ms": 1500,
            "details": {
                "firewall_rule_created": "deny-all-ingress-web-server-1",
                "previous_state_snapshot": "snapshot-12345"
            }
        },
        {
            "action": "revoke_credentials",
            "status": "success",
            "execution_time_ms": 800,
            "details": {
                "keys_revoked": 3,
                "account_status": "disabled"
            }
        }
    ],
    "rollback_available": true,
    "audit_log": "gs://sentinelops-audit/INC-20240101-001.log"
}

↓ Orchestrator Formatting ↓

Communication Agent Input:
{
    "incident_id": "INC-20240101-001",
    "notification_request": {
        "channels": ["slack", "email"],
        "priority": "high",
        "recipients": {
            "slack": ["#security-incidents", "@oncall"],
            "email": ["security-team@company.com"]
        }
    },
    "incident_summary": {
        "title": "Critical Security Incident - Compromised Instance",
        "description": "Unauthorized access detected on web-server-1",
        "severity": "critical",
        "status": "contained",
        "timeline": [
            {"time": "12:00:00", "event": "Incident detected"},
            {"time": "12:05:00", "event": "Analysis completed"},
            {"time": "12:10:00", "event": "Remediation executed"}
        ],
        "actions_taken": [...],
        "next_steps": ["Review forensic data", "Update security policies"]
    }
}
```

## Inter-Agent Dependencies

### Data Dependencies Matrix

| Producer Agent | Data Produced | Consumer Agent | Data Required |
|----------------|---------------|----------------|---------------|
| Detection | Incident alerts, anomalies | Analysis | Raw events, detection rules |
| Analysis | Severity assessment, recommendations | Remediation | Approved actions, constraints |
| Remediation | Action results, rollback data | Communication | Status updates, summaries |
| All Agents | Metrics, logs | Orchestrator | Health status, performance |

### Timing Constraints

1. **Detection → Analysis**: Must complete within 30 seconds
2. **Analysis → Remediation**: Must complete within 60 seconds
3. **Remediation → Communication**: Must complete within 15 seconds
4. **End-to-end**: Target < 5 minutes for critical incidents

## Error Handling and Recovery

### Failed Message Delivery
```python
# Retry configuration for Pub/Sub
{
    "retry_policy": {
        "minimum_backoff": "10s",
        "maximum_backoff": "600s",
        "maximum_attempts": 5
    },
    "dead_letter_topic": "projects/my-project/topics/sentinelops-dlq"
}
```

### Data Validation
Each agent validates incoming data before processing:

1. **Schema validation** using Pydantic models
2. **Business rule validation** (e.g., severity levels)
3. **Resource existence checks** via GCP APIs
4. **Permission verification** before actions

### State Management
The Orchestrator maintains incident state in Cloud SQL:

```sql
CREATE TABLE incident_state (
    incident_id VARCHAR(50) PRIMARY KEY,
    current_stage VARCHAR(50),
    processing_agent VARCHAR(50),
    last_update TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB
);
```

## Performance Optimization

### Batching
Agents batch operations where possible:
- Detection: Process logs in 1000-record batches
- Analysis: Analyze up to 10 related incidents together
- Communication: Batch notifications per channel

### Caching
Frequently accessed data is cached:
- Resource metadata: 5-minute TTL
- Threat intelligence: 1-hour TTL
- Analysis results: 24-hour TTL

### Parallel Processing
Agents use async/await for concurrent operations:
- Detection: Parallel log source queries
- Analysis: Concurrent API calls to Gemini
- Remediation: Parallel action execution (when safe)

## Monitoring and Observability

### Key Metrics
Each agent exposes metrics via Prometheus:

```python
# Message processing metrics
messages_received_total{agent="detection", status="success"}
messages_processed_duration_seconds{agent="analysis", quantile="0.99"}
messages_failed_total{agent="remediation", reason="validation_error"}

# Data flow metrics
data_bytes_transferred{from="detection", to="analysis"}
processing_lag_seconds{stage="detection_to_analysis"}
queue_depth{agent="orchestrator", queue="high_priority"}
```

### Tracing
OpenTelemetry traces show complete data flow:

```
Trace: INC-20240101-001
├─ detection_agent.detect_incident (1.5s)
│  ├─ query_bigquery (0.8s)
│  └─ apply_detection_rules (0.7s)
├─ orchestrator.route_message (0.1s)
├─ analysis_agent.analyze_incident (3.2s)
│  ├─ gather_context (1.1s)
│  └─ gemini_analysis (2.1s)
├─ orchestrator.evaluate_recommendations (0.2s)
├─ remediation_agent.execute_actions (2.5s)
│  ├─ isolate_instance (1.5s)
│  └─ revoke_credentials (1.0s)
└─ communication_agent.send_notifications (0.8s)
   ├─ slack_notification (0.4s)
   └─ email_notification (0.4s)
```

## Security Considerations

### Data Encryption
- **In Transit**: TLS 1.3 for all agent communication
- **At Rest**: Google Cloud KMS for sensitive data
- **Message Signing**: HMAC-SHA256 for message integrity

### Access Control
- **Service Accounts**: Least privilege per agent
- **IAM Policies**: Resource-specific permissions
- **Audit Logging**: All data access logged

### Data Retention
- **Hot Storage**: 30 days in Pub/Sub and Cloud SQL
- **Cold Storage**: 1 year in BigQuery and GCS
- **Compliance**: GDPR-compliant data handling

# Incident Response Sequence Diagrams

## Overview

This document provides detailed sequence diagrams showing how SentinelOps handles various types of security incidents from detection through resolution using the Google Agent Development Kit (ADK) framework.

## 1. Unauthorized Access Incident

This sequence shows the complete flow for detecting and responding to unauthorized access attempts using ADK's transfer system.

```mermaid
sequenceDiagram
    participant CL as Cloud Logging
    participant DA as Detection Agent
    participant TT as ADK Transfer Tool
    participant OA as Orchestrator
    participant AA as Analysis Agent
    participant GA as Gemini AI
    participant RA as Remediation Agent
    participant CE as Compute Engine
    participant CA as Communication Agent
    participant SL as Slack

    Note over CL,SL: Unauthorized SSH attempt detected

    CL->>DA: Stream log entry (failed SSH)
    DA->>DA: Apply detection rules (RulesEngineTool)
    DA->>DA: Calculate anomaly score (AnomalyDetectionTool)

    alt Anomaly score > threshold
        DA->>TT: TransferToOrchestratorAgentTool
        TT->>OA: Transfer incident context
        OA->>OA: Create incident record (FirestoreTool)
        OA->>TT: TransferToAnalysisAgentTool
        TT->>AA: Transfer for analysis

        AA->>AA: Gather context (ContextTool)
        AA->>GA: Request AI analysis (GeminiAnalysisTool)
        GA->>AA: Return severity and recommendations
        AA->>TT: TransferToOrchestratorAgentTool
        TT->>OA: Transfer analysis results

        OA->>OA: Evaluate recommendations

        alt Auto-remediation approved
            OA->>TT: TransferToRemediationAgentTool
            TT->>RA: Transfer remediation tasks

            par Isolate Instance
                RA->>CE: Create isolation firewall rule (IsolateVMTool)
                CE->>RA: Rule created
            and Revoke Credentials
                RA->>CE: Disable service account
                CE->>RA: Account disabled
            and Create Snapshot
                RA->>CE: Create forensic snapshot
                CE->>RA: Snapshot created
            end

            RA->>PS: Publish completion status
            PS->>OA: Deliver status
        end

        OA->>PS: Route to Communication
        PS->>CA: Deliver notification request
        CA->>SL: Send incident alert
        SL->>CA: Delivery confirmed
        CA->>PS: Publish delivery status
        PS->>OA: Update incident status

        OA->>OA: Mark incident resolved
    else Normal activity
        DA->>DA: Log as normal
    end
```

## 2. Data Exfiltration Attempt

This sequence shows detection and response to potential data exfiltration.

```mermaid
sequenceDiagram
    participant BQ as BigQuery Audit Logs
    participant DA as Detection Agent
    participant PS as Pub/Sub
    participant OA as Orchestrator
    participant AA as Analysis Agent
    participant GA as Gemini AI
    participant RA as Remediation Agent
    participant IAM as Cloud IAM
    participant GCS as Cloud Storage
    participant CA as Communication Agent
    participant Email as Email Service

    Note over BQ,Email: Large data export detected

    BQ->>DA: Audit log (unusual export size)
    DA->>DA: Check export patterns
    DA->>DA: Compare to baseline

    alt Export size > 10x normal
        DA->>PS: Publish HIGH severity incident
        PS->>OA: Priority delivery
        OA->>OA: Fast-track routing

        OA->>PS: Route to Analysis (urgent)
        PS->>AA: Deliver with priority flag

        AA->>BQ: Query recent user activity
        BQ->>AA: Return activity history
        AA->>GA: Analyze exfiltration risk
        GA->>AA: High risk score (0.92)

        AA->>PS: Publish urgent recommendations
        PS->>OA: Deliver analysis

        OA->>OA: Trigger immediate response

        par Block User Access
            OA->>PS: Route to Remediation
            PS->>RA: Emergency response
            RA->>IAM: Revoke all user permissions
            IAM->>RA: Permissions revoked
        and Secure Exported Data
            RA->>GCS: Change bucket ACLs
            GCS->>RA: Access restricted
        and Kill Active Sessions
            RA->>BQ: Cancel running queries
            BQ->>RA: Queries terminated
        end

        RA->>PS: Publish actions taken
        PS->>OA: Update incident

        OA->>PS: Route to Communication
        PS->>CA: Urgent notification

        par Notify Security Team
            CA->>Email: Send critical alert
            Email->>CA: Delivered
        and Create Incident Report
            CA->>GCS: Store detailed report
            GCS->>CA: Report saved
        end

        CA->>PS: Notification complete
        PS->>OA: Close incident loop
    end
```

## 3. Privilege Escalation Detection

This sequence shows response to detected privilege escalation.

```mermaid
sequenceDiagram
    participant CL as Cloud Logging
    participant DA as Detection Agent
    participant PS as Pub/Sub
    participant OA as Orchestrator
    participant AA as Analysis Agent
    participant GA as Gemini AI
    participant RA as Remediation Agent
    participant IAM as Cloud IAM
    participant SM as Secret Manager
    participant CA as Communication Agent

    Note over CL,CA: IAM role change detected

    CL->>DA: IAM audit log entry
    DA->>DA: Check role change patterns

    alt Unexpected admin role grant
        DA->>PS: Publish security incident
        PS->>OA: Deliver incident

        OA->>PS: Route for analysis
        PS->>AA: Deliver incident data

        AA->>IAM: Get role change history
        IAM->>AA: Return recent changes
        AA->>CL: Query actor's recent activity
        CL->>AA: Return activity logs

        AA->>GA: Analyze privilege escalation
        GA->>AA: Confirm malicious (confidence: 0.89)

        AA->>PS: Publish critical finding
        PS->>OA: Deliver analysis

        OA->>OA: Initiate containment

        critical Containment Actions
            OA->>PS: Route to Remediation
            PS->>RA: Execute containment

            RA->>IAM: Revert role changes
            IAM->>RA: Roles reverted

            RA->>IAM: Suspend suspicious account
            IAM->>RA: Account suspended

            RA->>SM: Rotate affected secrets
            SM->>RA: Secrets rotated

            RA->>IAM: Enable additional MFA
            IAM->>RA: MFA enforced
        end

        RA->>PS: Report containment complete
        PS->>OA: Update status

        OA->>PS: Trigger notifications
        PS->>CA: Deliver alert request

        CA->>CA: Generate incident report
        CA->>CA: Send to security team
        CA->>PS: Confirm notifications
        PS->>OA: Mark handled
    end
```

## 4. Malware Detection and Response

This sequence shows the response to detected malware on a compute instance.

```mermaid
sequenceDiagram
    participant OSC as OS Config Agent
    participant DA as Detection Agent
    participant PS as Pub/Sub
    participant OA as Orchestrator
    participant AA as Analysis Agent
    participant GA as Gemini AI
    participant RA as Remediation Agent
    participant CE as Compute Engine
    participant GCS as Cloud Storage
    participant CA as Communication Agent

    Note over OSC,CA: Suspicious process detected

    OSC->>DA: Process anomaly alert
    DA->>DA: Check against malware signatures
    DA->>DA: Analyze process behavior

    alt Malware signature match
        DA->>PS: Publish CRITICAL incident
        PS->>OA: Express delivery

        OA->>OA: Lock instance for investigation
        OA->>PS: Route to Analysis
        PS->>AA: Deliver malware alert

        AA->>CE: Get instance metadata
        CE->>AA: Return instance details
        AA->>OSC: Query running processes
        OSC->>AA: Return process list

        AA->>GA: Analyze malware behavior
        GA->>AA: Identify ransomware variant

        AA->>PS: Publish findings
        PS->>OA: Deliver analysis

        critical Immediate Isolation
            OA->>PS: Emergency remediation
            PS->>RA: Execute isolation

            RA->>CE: Detach instance from network
            CE->>RA: Network detached

            RA->>CE: Create emergency snapshot
            CE->>RA: Snapshot created

            RA->>GCS: Backup critical data
            GCS->>RA: Backup complete

            RA->>CE: Stop infected instance
            CE->>RA: Instance stopped
        end

        RA->>PS: Report isolation complete
        PS->>OA: Update incident

        OA->>PS: Initiate recovery planning
        PS->>AA: Request recovery plan

        AA->>GA: Generate recovery steps
        GA->>AA: Return recovery plan

        AA->>PS: Publish recovery plan
        PS->>OA: Deliver plan

        OA->>PS: Notify stakeholders
        PS->>CA: Send notifications

        CA->>CA: Create incident timeline
        CA->>CA: Send executive summary
        CA->>PS: Confirm sent
        PS->>OA: Close notification loop
    end
```

## 5. DDoS Attack Mitigation

This sequence shows automated response to a detected DDoS attack.

```mermaid
sequenceDiagram
    participant LB as Load Balancer
    participant DA as Detection Agent
    participant PS as Pub/Sub
    participant OA as Orchestrator
    participant AA as Analysis Agent
    participant RA as Remediation Agent
    participant CF as Cloud Firewall
    participant CDN as Cloud CDN
    participant CA as Communication Agent

    Note over LB,CA: Traffic spike detected

    LB->>DA: High request rate alert
    DA->>DA: Analyze traffic patterns
    DA->>DA: Check source IPs

    alt DDoS pattern detected
        DA->>PS: Publish DDoS incident
        PS->>OA: Deliver alert

        OA->>PS: Route to Analysis
        PS->>AA: Deliver traffic data

        par Analyze Attack
            AA->>LB: Get traffic details
            LB->>AA: Return metrics
        and Check Geography
            AA->>AA: GeoIP analysis
        and Identify Patterns
            AA->>AA: Traffic pattern analysis
        end

        AA->>PS: Publish attack profile
        PS->>OA: Deliver analysis

        OA->>OA: Activate DDoS response

        OA->>PS: Route to Remediation
        PS->>RA: Execute mitigation

        par Block Malicious IPs
            RA->>CF: Create deny rules
            CF->>RA: Rules active
        and Enable Rate Limiting
            RA->>LB: Configure rate limits
            LB->>RA: Limits active
        and Activate CDN
            RA->>CDN: Enable caching
            CDN->>RA: Cache active
        and Scale Resources
            RA->>CE: Auto-scale instances
            CE->>RA: Scaling complete
        end

        RA->>PS: Report mitigation active
        PS->>OA: Update status

        loop Monitor Effectiveness
            OA->>LB: Check metrics
            LB->>OA: Return current load

            alt Attack continuing
                OA->>RA: Adjust mitigation
            else Attack subsiding
                OA->>OA: Plan rollback
            end
        end

        OA->>PS: Send status update
        PS->>CA: Deliver notification
        CA->>CA: Update status page
        CA->>PS: Confirm update
    end
```

## State Management

Each incident follows a defined state machine:

```mermaid
stateDiagram-v2
    [*] --> Detected: Detection Agent triggers
    Detected --> Analyzing: Orchestrator routes
    Analyzing --> Assessed: Analysis complete

    Assessed --> Remediating: Auto-remediation approved
    Assessed --> Escalated: Manual intervention required

    Remediating --> Contained: Actions successful
    Remediating --> Failed: Actions failed

    Failed --> Escalated: Fallback to manual
    Escalated --> Investigating: Human analyst assigned

    Investigating --> Remediating: Manual actions defined
    Contained --> Monitoring: Watch for recurrence

    Monitoring --> Resolved: No recurrence
    Monitoring --> Detected: Issue recurs

    Resolved --> [*]: Incident closed
```

## Error Handling Sequences

### Failed Remediation Recovery

```mermaid
sequenceDiagram
    participant RA as Remediation Agent
    participant CE as Compute Engine
    participant PS as Pub/Sub
    participant OA as Orchestrator
    participant CA as Communication Agent

    RA->>CE: Execute isolation
    CE-->>RA: Error: Permission denied

    RA->>RA: Log error
    RA->>PS: Publish failure event
    PS->>OA: Deliver error

    OA->>OA: Check retry policy

    alt Retries available
        OA->>OA: Wait with backoff
        OA->>PS: Retry remediation
        PS->>RA: Deliver retry request
        RA->>CE: Retry with elevated permissions
        CE->>RA: Success
    else Retries exhausted
        OA->>PS: Escalate to human
        PS->>CA: Send escalation
        CA->>CA: Page on-call engineer
        OA->>OA: Mark as escalated
    end
```

## Performance Considerations

### Parallel Processing
- Detection: Process multiple log streams concurrently
- Analysis: Batch related incidents for efficiency
- Remediation: Execute independent actions in parallel
- Communication: Batch notifications per channel

### Optimization Points
1. **Detection**: Use BigQuery materialized views for common queries
2. **Analysis**: Cache Gemini responses for similar incidents
3. **Remediation**: Pre-compute IAM policies for quick application
4. **Communication**: Use templates to reduce processing time

### SLA Targets
| Incident Type | Detection | Analysis | Remediation | Total |
|--------------|-----------|----------|-------------|--------|
| Critical | < 30s | < 60s | < 120s | < 4min |
| High | < 60s | < 120s | < 180s | < 6min |
| Medium | < 120s | < 180s | < 300s | < 10min |
| Low | < 300s | < 300s | < 600s | < 20min |

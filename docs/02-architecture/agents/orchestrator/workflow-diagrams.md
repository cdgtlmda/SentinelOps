# Orchestration Agent Workflow Diagrams

## Complete Incident Response Workflow

```mermaid
graph TB
    subgraph Detection Phase
        A[Incident Detected] --> B[Create Incident Record]
        B --> C[Add to Active Incidents]
        C --> D[Initialize Workflow]
    end
    
    subgraph Analysis Phase
        D --> E[Request Analysis]
        E --> F{Analysis Timeout?}
        F -->|No| G[Analysis Complete]
        F -->|Yes| H[Escalate to Human]
        G --> I{Confidence >= 0.7?}
        I -->|Yes| J[Request Remediation]
        I -->|No| K[Notify Low Confidence]
    end
    
    subgraph Remediation Phase
        J --> L[Propose Actions]
        L --> M[Validate Actions]
        M --> N{Auto-Approve?}
        N -->|Yes| O[Execute Actions]
        N -->|No| P[Request Approval]
        P --> Q{Approved?}
        Q -->|Yes| O
        Q -->|No| R[Log Denial]
        Q -->|Timeout| S[Handle Timeout]
    end
    
    subgraph Resolution Phase
        O --> T{Actions Successful?}
        T -->|Yes| U[Mark Resolved]
        T -->|No| V[Mark Failed]
        U --> W[Send Notifications]
        W --> X[Close Incident]
    end
    
    style A fill:#ff9999
    style G fill:#99ff99
    style O fill:#ffff99
    style U fill:#99ff99
    style V fill:#ff9999
```

## Message Flow Diagram

```mermaid
sequenceDiagram
    participant D as Detection Agent
    participant O as Orchestrator
    participant A as Analysis Agent
    participant R as Remediation Agent
    participant C as Communication Agent
    participant F as Firestore
    
    D->>O: new_incident
    O->>F: Store incident
    O->>A: analyze_incident
    A->>O: analysis_complete
    O->>F: Update incident
    O->>R: propose_remediation
    R->>O: remediation_proposed
    
    alt Auto-Approval
        O->>O: Check auto-approval rules
        O->>R: execute_remediation
    else Manual Approval
        O->>C: send_notification (approval_required)
        C->>O: notification_sent
        Note over O: Wait for approval
        O->>R: execute_remediation
    end
    
    R->>O: remediation_complete
    O->>F: Update status
    O->>C: send_notification (resolved)
```

## Error Recovery Flow

```mermaid
graph LR
    subgraph Error Detection
        A[Error Occurs] --> B{Error Type?}
    end
    
    subgraph Recovery Strategies
        B -->|Network| C[Retry with Backoff]
        B -->|Validation| D[Skip Operation]
        B -->|Timeout| E[Escalate]
        B -->|Critical| F[Fail Incident]
        
        C --> G{Success?}
        G -->|Yes| H[Continue Workflow]
        G -->|No| I[Circuit Breaker]
        
        I --> J{Circuit Open?}
        J -->|Yes| K[Block Operations]
        J -->|No| L[Allow Retry]
    end
    
    subgraph Resolution
        E --> M[Human Intervention]
        F --> N[Mark Failed]
        K --> O[Wait for Reset]
    end
```

## State Machine Detailed View

```mermaid
stateDiagram-v2
    state "Active States" as active {
        [*] --> INITIALIZED
        INITIALIZED --> DETECTION_RECEIVED: new_incident
        
        state "Analysis States" as analysis {
            DETECTION_RECEIVED --> ANALYSIS_REQUESTED: auto
            ANALYSIS_REQUESTED --> ANALYSIS_IN_PROGRESS: agent_ack
            ANALYSIS_IN_PROGRESS --> ANALYSIS_COMPLETE: results_received
        }
        
        state "Remediation States" as remediation {
            ANALYSIS_COMPLETE --> REMEDIATION_REQUESTED: high_confidence
            REMEDIATION_REQUESTED --> REMEDIATION_PROPOSED: actions_ready
            
            state approval <<choice>>
            REMEDIATION_PROPOSED --> approval
            approval --> APPROVAL_PENDING: manual_required
            approval --> REMEDIATION_APPROVED: auto_approved
            
            APPROVAL_PENDING --> REMEDIATION_APPROVED: human_approved
            REMEDIATION_APPROVED --> REMEDIATION_IN_PROGRESS: execute
            REMEDIATION_IN_PROGRESS --> REMEDIATION_COMPLETE: all_success
        }
        
        state "Resolution States" as resolution {
            REMEDIATION_COMPLETE --> INCIDENT_RESOLVED: update_status
            INCIDENT_RESOLVED --> INCIDENT_CLOSED: final_cleanup
        }
    }
    
    state "Terminal States" as terminal {
        WORKFLOW_FAILED: Permanent Failure
        WORKFLOW_TIMEOUT: Exceeded Time Limit
    }
    
    analysis --> WORKFLOW_TIMEOUT: timeout
    remediation --> WORKFLOW_FAILED: critical_error
    approval --> WORKFLOW_TIMEOUT: approval_timeout
```

## Auto-Approval Decision Tree

```mermaid
graph TD
    A[Remediation Proposed] --> B{Auto-Remediation Enabled?}
    B -->|No| C[Manual Approval Required]
    B -->|Yes| D{Check Each Action}
    
    D --> E{Action Matches Rule?}
    E -->|No| C
    E -->|Yes| F{Evaluate Conditions}
    
    F --> G{Severity Check}
    G -->|High/Critical| H{Confidence > 0.85?}
    G -->|Low/Medium| I{Confidence > 0.7?}
    
    H -->|No| C
    H -->|Yes| J{Risk Score}
    I -->|No| C
    I -->|Yes| J
    
    J --> K{Score < Max Allowed?}
    K -->|No| C
    K -->|Yes| L{All Actions Pass?}
    
    L -->|No| C
    L -->|Yes| M[Auto-Approve All]
    
    style M fill:#99ff99
    style C fill:#ffff99
```

## Performance Optimization Flow

```mermaid
graph LR
    subgraph Input Layer
        A[Incoming Request] --> B{Cache Hit?}
    end
    
    subgraph Cache Layer
        B -->|Yes| C[Return Cached]
        B -->|No| D[Check Query Cache]
        D -->|Hit| E[Use Cached Query]
        D -->|Miss| F[Execute Query]
    end
    
    subgraph Batch Layer
        G[Write Operation] --> H{Batch Queue}
        H --> I{Queue Full?}
        I -->|Yes| J[Flush Batch]
        I -->|No| K[Add to Queue]
        K --> L[Wait for Timeout]
        L --> J
    end
    
    subgraph Storage Layer
        F --> M[Firestore]
        J --> M
        E --> N[Process Results]
        M --> N
    end
    
    subgraph Output Layer
        C --> O[Return Response]
        N --> P[Update Cache]
        P --> O
    end
```

## Concurrent Incident Handling

```mermaid
graph TB
    subgraph Orchestrator
        A[Incident Queue] --> B{Concurrency Limit?}
        B -->|Under Limit| C[Process Incident]
        B -->|At Limit| D[Queue Incident]
        
        C --> E[Active Incidents Pool]
        E --> F[Track Progress]
        
        F --> G{Completed?}
        G -->|Yes| H[Remove from Pool]
        G -->|No| I[Continue Processing]
        
        H --> J[Check Queue]
        J --> K{Queue Empty?}
        K -->|No| L[Dequeue Next]
        K -->|Yes| M[Wait for New]
        
        L --> C
    end
    
    subgraph Monitoring
        E -.-> N[Metrics Collector]
        N --> O[Performance Stats]
    end
```

## Audit Trail Flow

```mermaid
graph TD
    subgraph Event Sources
        A[State Transition] --> E[Audit Logger]
        B[Agent Action] --> E
        C[Error Event] --> E
        D[Config Change] --> E
    end
    
    subgraph Audit Processing
        E --> F[Create Entry]
        F --> G[Add Metadata]
        G --> H[Calculate Hash]
        H --> I[Sign Entry]
    end
    
    subgraph Storage
        I --> J[Main Audit Log]
        I --> K[Incident Audit Log]
        
        J --> L[(Firestore)]
        K --> L
    end
    
    subgraph Verification
        L --> M[Integrity Check]
        M --> N{Valid Hash?}
        N -->|Yes| O[Trusted Entry]
        N -->|No| P[Flag Tampering]
    end
```

## Circuit Breaker State Machine

```mermaid
stateDiagram-v2
    [*] --> Closed
    
    Closed --> Open: Failure Threshold Reached
    Closed --> Closed: Success
    Closed --> Closed: Failure Below Threshold
    
    Open --> Half_Open: Timeout Expired
    Open --> Open: Request Blocked
    
    Half_Open --> Closed: Success
    Half_Open --> Open: Failure
    
    note right of Closed: Normal operation
    note right of Open: All requests blocked
    note right of Half_Open: Testing recovery
```

# Agent Interaction Diagrams

This document provides detailed diagrams showing how SentinelOps agents interact with each other and external systems using the Google Agent Development Kit (ADK).

## Agent Communication Overview (ADK-Based)

```mermaid
graph TB
    subgraph "ADK Framework"
        AT[ADK Transfer System]
        TC[Tool Context]
    end

    subgraph "SentinelOps ADK Agents"
        DA[Detection Agent<br/>extends LlmAgent]
        AA[Analysis Agent<br/>extends LlmAgent]
        RA[Remediation Agent<br/>extends LlmAgent]
        CA[Communication Agent<br/>extends LlmAgent]
        OA[Orchestrator Agent<br/>extends SentinelOpsBaseAgent]
    end

    subgraph "Google Cloud Services"
        CE[Compute Engine]
        CS[Cloud Storage]
        BQ[BigQuery]
        SM[Secret Manager]
        VA[Vertex AI/Gemini]
    end

    subgraph "External Services"
        SL[Slack]
        EM[Email]
        WH[Webhooks]
    end

    %% ADK Transfer connections
    DA -->|TransferToOrchestratorAgentTool| AT
    AT -->|routes to| OA
    OA -->|TransferToAnalysisAgentTool| AT
    AT -->|routes to| AA
    OA -->|TransferToRemediationAgentTool| AT
    AT -->|routes to| RA
    OA -->|TransferToCommunicationAgentTool| AT
    AT -->|routes to| CA

    %% Detection Agent connections
    DA -->|monitors| CE
    DA -->|monitors| CS
    DA -->|logs data| BQ

    %% Analysis Agent connections
    AA -->|queries| VA
    AA -->|stores results| BQ

    %% Remediation Agent connections
    RA -->|modifies| CE
    RA -->|modifies| CS
    RA -->|logs actions| BQ

    %% Communication Agent connections
    CA -->|receives alerts| OA
    CA -->|sends to| SL
    CA -->|sends to| EM
    CA -->|sends to| WH

    %% Orchestration Agent connections
    OA -->|coordinates| DA
    OA -->|coordinates| AA
    OA -->|coordinates| RA
    OA -->|coordinates| CA
    OA -->|manages state| BQ
    OA -->|retrieves secrets| SM
```

## Incident Response Flow (ADK-Based)

```mermaid
sequenceDiagram
    participant GC as Google Cloud Resource
    participant DA as Detection Agent
    participant TT as Transfer Tool
    participant AA as Analysis Agent
    participant OA as Orchestrator Agent
    participant RA as Remediation Agent
    participant CA as Communication Agent
    participant User as Security Team

    %% Detection Phase
    DA->>GC: Scan resources (via ADK Tools)
    GC-->>DA: Resource data
    DA->>DA: Evaluate rules (RulesEngineTool)
    Note over DA: Threat detected!
    DA->>TT: TransferToOrchestratorAgentTool
    TT->>OA: Transfer context & threat data

    %% Orchestration Phase
    OA->>OA: Evaluate severity
    OA->>TT: TransferToAnalysisAgentTool
    TT->>AA: Transfer incident context

    %% Analysis Phase
    AA->>GC: Gather context (ContextTool)
    GC-->>AA: Additional data
    AA->>AA: AI analysis (GeminiAnalysisTool)
    AA->>TT: TransferToOrchestratorAgentTool
    TT->>OA: Transfer analysis results

    %% Decision Phase
    OA->>OA: Evaluate response plan
    alt High/Critical Severity
        OA->>TT: TransferToCommunicationAgentTool
        TT->>CA: Transfer alert context
        CA->>User: Notification (SlackTool/EmailTool)
        OA->>TT: TransferToRemediationAgentTool
        TT->>RA: Transfer remediation plan
    else Medium/Low Severity
        OA->>TT: TransferToCommunicationAgentTool
        TT->>CA: Transfer for queued notification
        OA->>OA: Wait for batch window
    end

    %% Remediation Phase
    RA->>GC: Apply fix
    GC-->>RA: Confirmation
    RA->>OA: Action complete

    %% Communication Phase
    OA->>CA: Send summary
    CA->>User: Final notification
```

## Data Flow Diagram

```mermaid
graph LR
    subgraph "Data Sources"
        CL[Cloud Logs]
        CM[Cloud Metrics]
        CC[Cloud Configs]
        TI[Threat Intel]
    end

    subgraph "Processing Pipeline"
        subgraph "Ingestion"
            DA[Detection Agent]
            PS1[Pub/Sub Queue]
        end

        subgraph "Analysis"
            AA[Analysis Agent]
            ML[ML Models]
            AI[Gemini AI]
        end

        subgraph "Storage"
            BQ[(BigQuery)]
            GCS[(Cloud Storage)]
        end

        subgraph "Action"
            OA[Orchestration Agent]
            RA[Remediation Agent]
            CA[Communication Agent]
        end
    end

    subgraph "Outputs"
        API[REST API]
        NOT[Notifications]
        DASH[Dashboards]
    end

    %% Data flow connections
    CL --> DA
    CM --> DA
    CC --> DA
    TI --> AA

    DA --> PS1
    PS1 --> AA

    AA --> ML
    AA --> AI
    ML --> AA
    AI --> AA

    AA --> BQ
    AA --> GCS

    BQ --> OA
    OA --> RA
    OA --> CA

    OA --> API
    CA --> NOT
    BQ --> DASH
```

## Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> Initializing

    Initializing --> Healthy: Startup complete
    Initializing --> Failed: Startup error

    Healthy --> Processing: Work available
    Processing --> Healthy: Work complete
    Processing --> Error: Processing failed

    Error --> Recovering: Auto-recovery
    Error --> Failed: Max retries exceeded

    Recovering --> Healthy: Recovery successful
    Recovering --> Failed: Recovery failed

    Failed --> [*]: Shutdown
    Healthy --> [*]: Graceful shutdown

    state Processing {
        [*] --> Receiving
        Receiving --> Validating
        Validating --> Executing
        Executing --> Reporting
        Reporting --> [*]
    }
```

## Communication Patterns

### Synchronous Communication

```mermaid
graph LR
    subgraph "Request/Response"
        C[Client] -->|HTTP Request| API[API Gateway]
        API -->|Route| OA[Orchestration Agent]
        OA -->|Query| AA[Analysis Agent]
        AA -->|Response| OA
        OA -->|Response| API
        API -->|HTTP Response| C
    end
```

### Asynchronous Communication

```mermaid
graph TB
    subgraph "Event-Driven"
        DA[Detection Agent] -->|Publish| T1[threat-detected Topic]
        T1 -->|Subscribe| AA[Analysis Agent]
        T1 -->|Subscribe| OA[Orchestration Agent]

        AA -->|Publish| T2[analysis-complete Topic]
        T2 -->|Subscribe| OA
        T2 -->|Subscribe| CA[Communication Agent]

        OA -->|Publish| T3[action-required Topic]
        T3 -->|Subscribe| RA[Remediation Agent]
    end
```

## Security Flow

```mermaid
graph TB
    subgraph "Authentication & Authorization"
        U[User/Service] -->|1. Request + Credentials| AG[API Gateway]
        AG -->|2. Verify Token| AM[Auth Manager]
        AM -->|3. Check Permissions| IAM[Cloud IAM]
        IAM -->|4. Allow/Deny| AM
        AM -->|5. Auth Result| AG
        AG -->|6. Forward/Reject| S[Service]
    end

    subgraph "Secret Management"
        S -->|7. Request Secret| SM[Secret Manager]
        SM -->|8. Check Access| IAM
        IAM -->|9. Allow/Deny| SM
        SM -->|10. Return Secret| S
    end
```

## Scaling Architecture

```mermaid
graph TB
    subgraph "Load Distribution"
        LB[Load Balancer] --> DA1[Detection Agent 1]
        LB --> DA2[Detection Agent 2]
        LB --> DA3[Detection Agent 3]

        DA1 --> PS[Pub/Sub]
        DA2 --> PS
        DA3 --> PS

        PS --> AA1[Analysis Agent 1]
        PS --> AA2[Analysis Agent 2]

        AS[Auto Scaler] -.->|Monitor & Scale| DA1
        AS -.->|Monitor & Scale| DA2
        AS -.->|Monitor & Scale| DA3
    end
```

## Error Handling Flow

```mermaid
graph TD
    A[Agent Operation] -->|Success| B[Continue]
    A -->|Error| C{Retryable?}

    C -->|Yes| D[Exponential Backoff]
    D --> E{Retry Limit?}
    E -->|Not Exceeded| A
    E -->|Exceeded| F[Circuit Breaker Open]

    C -->|No| G[Log Error]
    G --> H[Alert Operations]

    F --> I[Fallback Logic]
    I --> J[Degraded Mode]

    J --> K[Health Check]
    K -->|Healthy| L[Circuit Breaker Close]
    L --> A
    K -->|Unhealthy| J
```

## Deployment Pipeline

```mermaid
graph LR
    subgraph "CI/CD Pipeline"
        GH[GitHub] -->|Push| CI[Cloud Build]
        CI -->|Test| TS[Test Suite]
        TS -->|Pass| CR[Container Registry]
        CR -->|Deploy| ST[Staging]
        ST -->|Validate| PT[Production]
    end

    subgraph "Rollback"
        PT -->|Issues| RB[Rollback]
        RB -->|Previous Version| CR
    end
```

## Monitoring Integration

```mermaid
graph TB
    subgraph "Metrics Collection"
        A1[Agent 1] -->|Metrics| PC[Prometheus Collector]
        A2[Agent 2] -->|Metrics| PC
        A3[Agent 3] -->|Metrics| PC

        A1 -->|Logs| CL[Cloud Logging]
        A2 -->|Logs| CL
        A3 -->|Logs| CL

        PC -->|Store| TS[(Time Series DB)]
        CL -->|Export| BQ[(BigQuery)]

        TS -->|Query| G[Grafana]
        BQ -->|Query| G

        G -->|Alert| PD[PagerDuty]
        G -->|Alert| CA[Communication Agent]
    end
```

These diagrams illustrate the complex interactions and data flows within the SentinelOps platform. Each agent has specific responsibilities and communication patterns that ensure efficient and reliable security monitoring and response.

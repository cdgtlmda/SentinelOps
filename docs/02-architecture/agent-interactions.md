# Agent Interactions - Comprehensive Guide

This document provides a complete overview of how SentinelOps agents interact with each other using Google's Agent Development Kit (ADK). It consolidates all agent interaction patterns, communication flows, and architectural decisions.

## Table of Contents
1. [ADK Agent Communication Overview](#adk-agent-communication-overview)
2. [Agent Transfer System](#agent-transfer-system)
3. [Agent Responsibilities](#agent-responsibilities)
4. [Communication Patterns](#communication-patterns)
5. [Incident Response Flow](#incident-response-flow)
6. [Production Patterns](#production-patterns)
7. [Scaling and Performance](#scaling-and-performance)

## ADK Agent Communication Overview

SentinelOps uses ADK's transfer system for all inter-agent communication, replacing traditional message queues with a type-safe, context-aware transfer mechanism.

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
        FS[Firestore]
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

    %% Service connections
    DA -->|monitors| CE
    DA -->|monitors| CS
    DA -->|queries| BQ
    AA -->|analyzes with| VA
    AA -->|stores results| FS
    RA -->|modifies| CE
    RA -->|logs actions| BQ
    CA -->|sends to| SL
    CA -->|sends to| EM
    OA -->|manages state| FS
    OA -->|retrieves secrets| SM
```

## Agent Transfer System

### Transfer Tools Architecture

```mermaid
graph TB
    subgraph TransferTools[Transfer Tools]
        T2A[TransferToAnalysisAgentTool]
        T2R[TransferToRemediationAgentTool]
        T2C[TransferToCommunicationAgentTool]
        T2O[TransferToOrchestratorAgentTool]
        T2D[TransferToDetectionAgentTool]
    end

    subgraph RoutingRules[ADK Routing Configuration]
        RR[Routing Rules:<br/>- Detection → Analysis<br/>- Detection → Orchestrator<br/>- Analysis → Remediation<br/>- Analysis → Communication<br/>- Remediation → Communication<br/>- All → Orchestrator]
    end

    TransferTools --> RR
```

### Transfer Flow Sequence

```mermaid
sequenceDiagram
    participant DA as Detection Agent
    participant TC as Tool Context
    participant TT as Transfer Tool
    participant ADK as ADK Transfer System
    participant AA as Analysis Agent

    Note over DA,AA: Example: Detection transfers incident to Analysis

    DA->>DA: Detect security incident
    DA->>TT: Execute transfer_to_analysis_agent tool
    TT->>TC: Set context.data["incident"] = incident_data
    TT->>TC: Set context.data["priority"] = "high"
    TT->>ADK: context.actions.transfer_to_agent("analysis_agent")

    ADK->>ADK: Validate routing rules
    ADK->>ADK: Save context state
    ADK->>AA: Invoke Analysis Agent with context

    AA->>TC: Read context.data["incident"]
    AA->>AA: Process incident with Gemini
    AA->>AA: Continue workflow
```

## Agent Responsibilities

### Orchestrator Agent (Central Hub)
- **Type**: SequentialAgent (ADK class for workflow orchestration)
- **Role**: Central coordinator and workflow manager
- **Transfer Capabilities**: Can transfer to all other agents
- **Key Responsibilities**:
  - Workflow orchestration using ADK patterns
  - State management in Firestore
  - Incident routing based on severity
  - Complex conditional logic implementation
  - Health monitoring of other agents

### Detection Agent
- **Type**: LlmAgent with Gemini Flash
- **Role**: Continuous monitoring and threat detection
- **Transfer Tools**:
  - TransferToAnalysisAgentTool
  - TransferToOrchestratorAgentTool
- **Domain Tools**:
  - LogMonitoringTool: BigQuery log analysis
  - AnomalyDetectionTool: ML-based detection
  - RulesEngineTool: Rule evaluation
  - EventCorrelatorTool: Event correlation
  - QueryBuilderTool: Query optimization
  - IncidentDeduplicatorTool: Deduplication

### Analysis Agent
- **Type**: LlmAgent with Gemini Pro
- **Role**: Deep incident analysis and risk assessment
- **Transfer Tools**:
  - TransferToRemediationAgentTool
  - TransferToCommunicationAgentTool
  - TransferToOrchestratorAgentTool
- **Domain Tools**:
  - IncidentAnalysisTool: Gemini-powered analysis
  - RecommendationTool: Remediation suggestions
  - ContextTool: Historical context retrieval
  - Performance Optimizer: Caching and batching

### Remediation Agent
- **Type**: LlmAgent with safety controls
- **Role**: Automated response execution
- **Transfer Tools**:
  - TransferToCommunicationAgentTool
  - TransferToOrchestratorAgentTool
- **Domain Tools**:
  - BlockIPTool: Firewall rule management
  - IsolateVMTool: Instance isolation
  - RevokeCredentialsTool: Credential revocation
  - All tools support dry-run mode and rollback

### Communication Agent
- **Type**: LlmAgent for multi-channel notifications
- **Role**: Stakeholder communication
- **Transfer Tools**:
  - TransferToOrchestratorAgentTool
- **Domain Tools**:
  - SlackNotificationTool: Slack integration
  - EmailNotificationTool: Email service
  - SMSNotificationTool: SMS alerts
  - WebhookTool: Custom integrations

## Communication Patterns

### Synchronous Pattern (API Requests)

```mermaid
graph LR
    C[Client] -->|HTTP Request| API[API Gateway]
    API -->|Route| OA[Orchestrator Agent]
    OA -->|Transfer| AA[Analysis Agent]
    AA -->|Response| OA
    OA -->|Response| API
    API -->|HTTP Response| C
```

### Asynchronous Pattern (Event-Driven)

```mermaid
graph TB
    subgraph "Event-Driven Flow"
        DA[Detection Agent] -->|Transfer| OA[Orchestrator Agent]
        OA -->|Transfer| AA[Analysis Agent]
        AA -->|Transfer| RA[Remediation Agent]
        RA -->|Transfer| CA[Communication Agent]
    end
```

## Incident Response Flow

### Complete Incident Lifecycle

```mermaid
sequenceDiagram
    participant GC as Google Cloud Resource
    participant DA as Detection Agent
    participant OA as Orchestrator Agent
    participant AA as Analysis Agent
    participant RA as Remediation Agent
    participant CA as Communication Agent
    participant User as Security Team

    %% Detection Phase
    DA->>GC: Monitor resources (via ADK Tools)
    GC-->>DA: Resource data
    DA->>DA: Evaluate rules (RulesEngineTool)
    Note over DA: Threat detected!
    DA->>OA: TransferToOrchestratorAgentTool

    %% Orchestration Phase
    OA->>OA: Evaluate severity
    OA->>AA: TransferToAnalysisAgentTool

    %% Analysis Phase
    AA->>GC: Gather context (ContextTool)
    GC-->>AA: Additional data
    AA->>AA: AI analysis (GeminiAnalysisTool)
    AA->>OA: Transfer analysis results

    %% Decision Phase
    OA->>OA: Evaluate response plan
    alt High/Critical Severity
        OA->>CA: TransferToCommunicationAgentTool
        CA->>User: Immediate notification
        OA->>RA: TransferToRemediationAgentTool
    else Medium/Low Severity
        OA->>CA: Queue for batch notification
        OA->>OA: Wait for batch window
    end

    %% Remediation Phase
    RA->>GC: Apply remediation
    GC-->>RA: Confirmation
    RA->>OA: Action complete

    %% Communication Phase
    OA->>CA: Send summary
    CA->>User: Final notification
```

## Production Patterns

### Circuit Breaker Pattern

```python
class TransferToAnalysisAgentTool(BaseTool):
    """Transfer tool with circuit breaker for resilience."""

    def __init__(self):
        super().__init__(
            name="transfer_to_analysis_agent",
            description="Transfer incident to Analysis Agent with fault tolerance"
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=TransferException
        )

    async def execute(self, context: ToolContext, **kwargs):
        if self.circuit_breaker.is_open():
            # Fallback: Send to orchestrator instead
            context.actions.transfer_to_agent("orchestrator_agent")
            return {"status": "circuit_open", "fallback": "orchestrator"}

        try:
            context.data.update(kwargs)
            context.actions.transfer_to_agent("analysis_agent")
            self.circuit_breaker.record_success()
            return {"status": "transferred", "target": "analysis_agent"}
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise
```

### Agent State Machine

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

### Error Handling Flow

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

## Scaling and Performance

### Load Distribution Architecture

```mermaid
graph TB
    subgraph "Load Distribution"
        LB[Load Balancer] --> DA1[Detection Agent 1]
        LB --> DA2[Detection Agent 2]
        LB --> DA3[Detection Agent 3]

        DA1 --> OA[Orchestrator Agent]
        DA2 --> OA
        DA3 --> OA

        OA --> AA1[Analysis Agent 1]
        OA --> AA2[Analysis Agent 2]

        AS[Auto Scaler] -.->|Monitor & Scale| DA1
        AS -.->|Monitor & Scale| DA2
        AS -.->|Monitor & Scale| DA3
    end
```

### Performance Optimizations

1. **Analysis Agent Caching**
   - 1-hour TTL for similar incidents
   - Reduces Gemini API calls by 30-50%
   - Sub-10ms response for cache hits

2. **Batch Processing**
   - Groups similar incidents for analysis
   - Reduces API costs significantly
   - Maintains response time SLAs

3. **Connection Pooling**
   - Reuses Firestore connections
   - Minimizes connection overhead
   - Improves throughput

## Key Differences from Traditional Architecture

| Aspect | Traditional | ADK-Based |
|--------|-------------|-----------|
| Communication | Pub/Sub messaging | ADK Transfer Tools |
| Context Passing | JSON messages | Rich Tool Context |
| Orchestration | Custom coordination | ADK SequentialAgent |
| Error Handling | Manual retry logic | Built-in resilience |
| Type Safety | Runtime validation | Compile-time safety |
| State Management | Distributed state | Centralized in Firestore |

## Best Practices

1. **Always use Transfer Tools** for agent communication
2. **Preserve context** throughout the transfer chain
3. **Implement circuit breakers** for production resilience
4. **Monitor transfer metrics** for performance optimization
5. **Use appropriate agent types** (LlmAgent vs SequentialAgent)
6. **Leverage ADK's built-in** error handling and retry logic

---

*This consolidated guide represents the complete agent interaction architecture for SentinelOps, leveraging ADK's powerful transfer system for reliable, scalable security operations.*

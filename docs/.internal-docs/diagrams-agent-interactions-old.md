# Agent Interaction Model with ADK

```mermaid
graph TB
    subgraph ADKFramework[ADK Framework Components]
        TransferSystem[Agent Transfer System]
        ToolContext[Tool Context]
        ADKRouter[ADK Routing Manager]
    end

    subgraph AgentCommunication[Agent Communication via ADK]
        OA[Orchestrator Agent<br/>SequentialAgent]
        DA[Detection Agent<br/>LlmAgent]
        AA[Analysis Agent<br/>LlmAgent]
        RA[Remediation Agent<br/>LlmAgent]
        CA[Communication Agent<br/>LlmAgent]
    end

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

    %% ADK Framework connections
    TransferSystem --> ToolContext
    TransferSystem --> ADKRouter
    ADKRouter --> RR

    %% Transfer tool connections
    TransferSystem --> T2A
    TransferSystem --> T2R
    TransferSystem --> T2C
    TransferSystem --> T2O
    TransferSystem --> T2D

    %% Agent transfer patterns
    DA -.->|uses| T2A
    DA -.->|uses| T2O
    AA -.->|uses| T2R
    AA -.->|uses| T2C
    AA -.->|uses| T2O
    RA -.->|uses| T2C
    RA -.->|uses| T2O
    CA -.->|uses| T2O
    OA -.->|uses| T2A
    OA -.->|uses| T2R
    OA -.->|uses| T2C
    OA -.->|uses| T2D

    style ADKFramework fill:#e3f2fd
    style TransferSystem fill:#bbdefb
    style ToolContext fill:#bbdefb
    style ADKRouter fill:#bbdefb
    
    style OA fill:#ffe0b2
    style DA fill:#fff3e0
    style AA fill:#fff3e0
    style RA fill:#fff3e0
    style CA fill:#fff3e0
    
    style T2A fill:#f3e5f5
    style T2R fill:#f3e5f5
    style T2C fill:#f3e5f5
    style T2O fill:#f3e5f5
    style T2D fill:#f3e5f5
    
    style RR fill:#e8f5e9
```

## ADK Agent Transfer Flow

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

## Agent Responsibilities with ADK

### Orchestrator Agent (Hub)
- **Type**: SequentialAgent (ADK class for workflow orchestration)
- **Transfer Tools**: Can transfer to all other agents
- **Responsibilities**:
  - Central coordinator using ADK's workflow patterns
  - Maintains incident state in Firestore
  - Routes incidents based on severity and type
  - Implements conditional logic for complex workflows

### Detection Agent
- **Type**: LlmAgent with Gemini Flash
- **Transfer Tools**: TransferToAnalysisAgentTool, TransferToOrchestratorAgentTool
- **Domain Tools**:
  - RulesEngineTool: Wraps detection rules engine
  - EventCorrelatorTool: Correlates related events
  - QueryBuilderTool: Optimizes BigQuery queries
  - IncidentCreationTool: Creates and deduplicates incidents

### Analysis Agent
- **Type**: LlmAgent with Gemini Pro
- **Transfer Tools**: TransferToRemediationAgentTool, TransferToCommunicationAgentTool, TransferToOrchestratorAgentTool
- **Domain Tools**:
  - GeminiAnalysisTool: Sophisticated prompt engineering for analysis
  - RecommendationTool: Generates remediation recommendations
  - RiskScoringTool: Calculates incident risk scores
  - ContextRetrievalTool: Enriches with historical data

### Remediation Agent
- **Type**: LlmAgent with safety controls
- **Transfer Tools**: TransferToCommunicationAgentTool, TransferToOrchestratorAgentTool
- **Domain Tools**:
  - BlockIPTool: Creates firewall rules
  - IsolateVMTool: Isolates compromised instances
  - RevokeCredentialsTool: Revokes service account keys
  - All tools include dry-run mode and rollback support

### Communication Agent
- **Type**: LlmAgent for multi-channel notifications
- **Transfer Tools**: TransferToOrchestratorAgentTool (for status updates)
- **Domain Tools**:
  - SlackNotificationTool: Slack integration
  - EmailNotificationTool: Email service
  - SMSNotificationTool: SMS alerts
  - WebhookTool: Custom integrations

## ADK Routing Configuration

The routing system enforces these rules:

1. **Orchestrator as Hub**: Can reach all agents, all agents can return to it
2. **Sequential Flow**: Detection → Analysis → Remediation → Communication
3. **Direct Shortcuts**: Analysis can directly notify via Communication for urgent alerts
4. **No Reverse Flow**: Prevents circular dependencies
5. **Bidirectional Validation**: Ensures routing integrity

## Key Differences from Original Architecture

1. **No Pub/Sub**: Replaced entirely with ADK's transfer system
2. **Rich Context**: Tool context carries full incident data and metadata
3. **Type Safety**: Strongly typed routing configuration
4. **Native Orchestration**: Uses ADK's built-in workflow patterns
5. **Tool-Based Communication**: All inter-agent communication through transfer tools

## Production Patterns

### Circuit Breaker Pattern in Transfer Tools
```python
class TransferToAnalysisAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="transfer_to_analysis_agent",
            description="Transfer incident to Analysis Agent"
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

This ensures system resilience even if an agent becomes unavailable.
# SentinelOps System Architecture with ADK

```mermaid
graph TB
    subgraph GoogleADK[Google Agent Development Kit Framework]
        ADKCore[ADK Core]
        LlmAgent[LlmAgent Base Class]
        SequentialAgent[SequentialAgent]
        BaseTool[BaseTool Class]
        ToolContext[Tool Context]
        TransferSystem[Agent Transfer System]
    end

    subgraph "Google Cloud Platform"
        subgraph "Data Sources"
            CL[Cloud Logging]
            BQ[BigQuery]
            CS[Cloud Storage]
            CM[Compute Engine]
            CH[Chronicle<br/>Optional]
        end

        subgraph "AI/ML Services"
            VA[Vertex AI<br/>Gemini Pro]
        end

        subgraph "Storage"
            SM[Secret Manager]
            FS[Firestore<br/>Incident State]
            BQS[BigQuery<br/>Analytics]
        end
    end

    subgraph "SentinelOps ADK Agents"
        subgraph "Detection System"
            DA[Detection Agent<br/>extends LlmAgent]
            DT[Detection Tools<br/>- RulesEngineTool<br/>- EventCorrelatorTool<br/>- QueryBuilderTool]
        end

        subgraph "Analysis System"
            AA[Analysis Agent<br/>extends LlmAgent]
            AT[Analysis Tools<br/>- GeminiAnalysisTool<br/>- RecommendationTool<br/>- RiskScoringTool]
        end

        subgraph "Remediation System"
            RA[Remediation Agent<br/>extends LlmAgent]
            RT[Remediation Tools<br/>- BlockIPTool<br/>- IsolateVMTool<br/>- RevokeCredentialsTool]
        end

        subgraph "Communication System"
            CA[Communication Agent<br/>extends LlmAgent]
            CT[Communication Tools<br/>- SlackNotificationTool<br/>- EmailNotificationTool<br/>- WebhookTool]
        end

        subgraph "Orchestration System"
            OA[Orchestrator Agent<br/>extends SequentialAgent]
            TT[Transfer Tools<br/>- TransferToAnalysisAgentTool<br/>- TransferToRemediationAgentTool<br/>- TransferToCommunicationAgentTool]
        end
    end

    subgraph "External Services"
        SL[Slack API]
        EM[Email Service]
        WH[Webhooks]
    end

    subgraph "Users"
        SO[Security Ops]
        AD[Administrators]
        DV[Developers]
    end

    %% ADK Framework connections
    ADKCore --> LlmAgent
    ADKCore --> SequentialAgent
    ADKCore --> BaseTool
    ADKCore --> TransferSystem
    BaseTool --> ToolContext

    %% Agent inheritance
    LlmAgent --> DA
    LlmAgent --> AA
    LlmAgent --> RA
    LlmAgent --> CA
    SequentialAgent --> OA

    %% Tool connections
    DA --> DT
    AA --> AT
    RA --> RT
    CA --> CT
    OA --> TT

    %% Data flow
    CL --> DA
    BQ --> DA
    CS --> DA
    CM --> DA
    CH -.-> DA

    %% ADK Transfer connections
    TransferSystem --> TT
    DA -.->|Transfer| AA
    AA -.->|Transfer| RA
    RA -.->|Transfer| CA
    OA -.->|Transfer| DA
    OA -.->|Transfer| AA
    OA -.->|Transfer| RA
    OA -.->|Transfer| CA

    %% External connections
    AA --> VA
    VA --> AA
    RA --> CM
    CA --> SL
    CA --> EM
    CA --> WH

    %% Storage connections
    DA --> FS
    AA --> FS
    RA --> FS
    OA --> FS
    SM --> DA
    SM --> AA
    SM --> RA

    %% User access
    SO --> OA
    AD --> OA
    DV --> OA

    style GoogleADK fill:#e3f2fd
    style ADKCore fill:#bbdefb
    style LlmAgent fill:#90caf9
    style BaseTool fill:#90caf9
    style TransferSystem fill:#90caf9
    
    style DA fill:#fff3e0
    style AA fill:#fff3e0
    style RA fill:#fff3e0
    style CA fill:#fff3e0
    style OA fill:#ffe0b2
    
    style DT fill:#f3e5f5
    style AT fill:#f3e5f5
    style RT fill:#f3e5f5
    style CT fill:#f3e5f5
    style TT fill:#f3e5f5
```

## Architecture Components with ADK

### Google Agent Development Kit (ADK)
- **ADK Core**: Foundation framework providing agent orchestration
- **LlmAgent**: Base class for all intelligent agents with Gemini integration
- **SequentialAgent**: Used for orchestrator to coordinate workflows
- **BaseTool**: Base class for all domain-specific tools
- **Tool Context**: Mechanism for passing data between tools and agents
- **Transfer System**: ADK's native agent-to-agent communication

### ADK Agents (Production Implementation)
- **Detection Agent**: Extends LlmAgent, monitors cloud resources for security incidents
  - Leverages Gemini Flash for intelligent pattern recognition
  - Executes specialized detection tools
- **Analysis Agent**: Extends LlmAgent, uses Gemini Pro for threat analysis
  - Sophisticated prompt engineering for security analysis
  - Multi-shot prompting for comprehensive analysis
- **Remediation Agent**: Extends LlmAgent, executes automated response actions
  - Production-grade tools with safety mechanisms
  - Direct GCP API integration
- **Communication Agent**: Extends LlmAgent, manages notifications
  - Multi-channel notification support
  - Template-based messaging
- **Orchestrator Agent**: Extends SequentialAgent, coordinates workflows
  - Conditional routing based on incident severity
  - Manages complex incident response workflows

### ADK Tools (Domain Expertise)
Each agent has 5-10 specialized tools that extend BaseTool:
- **Detection Tools**: Security event analysis and correlation
- **Analysis Tools**: AI-powered threat assessment and recommendations
- **Remediation Tools**: Automated response actions with safety controls
- **Communication Tools**: Multi-channel notification delivery
- **Transfer Tools**: Enable agent-to-agent communication via ADK

### Key Architecture Features
1. **ADK Native Design**: Built from the ground up using ADK patterns
2. **Tool-First Approach**: All functionality exposed through ADK tools
3. **Transfer System**: ADK's native agent communication
4. **Direct API Integration**: Agents interact directly with GCP services
5. **Production Patterns**: Circuit breakers, caching, telemetry in every tool
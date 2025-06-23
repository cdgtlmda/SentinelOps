# SentinelOps Architecture Diagrams

This document provides a comprehensive overview of the SentinelOps architecture through a series of detailed diagrams. These diagrams illustrate the system's components, interactions, data flows, and integration points.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Agent Interactions](#agent-interactions)
5. [GCP Integration](#gcp-integration)
6. [Incident Response Workflow](#incident-response-workflow)

## High-Level Architecture

This diagram illustrates the overall architecture of the SentinelOps system, showing the main components and their relationships.

```mermaid
graph TB
    subgraph "User Interaction"
        User([Security Engineer])
        UI[Web Dashboard]
        API[API Layer]
        CLI[Command-Line Interface]
    end

    subgraph "Core Engine"
        Orchestrator[Orchestrator Agent]
        Config[Configuration Management]
        CredentialMgr[Credential Manager]
        Recovery[Error Recovery System]
    end

    subgraph "Agent Ecosystem"
        Detection[Detection Agent]
        Analysis[Analysis Agent]
        Remediation[Remediation Agent]
        Communication[Communication Agent]
    end

    subgraph "Intelligence Services"
        Gemini[Gemini API]
        RulesEngine[Rules Engine]
        ContextRetrieval[Context Retrieval]
        IncidentDB[(Incident Database)]
    end

    subgraph "Cloud Integration"
        GCP[Google Cloud Platform]
        BigQuery[BigQuery]
        ADKTransfer[ADK Transfer System]
        SecretMgr[Secret Manager]
        CloudFunctions[Cloud Functions]
    end

    %% User Flow
    User <--> UI
    User <--> CLI
    UI <--> API
    CLI <--> API
    API <--> Orchestrator

    %% Core Engine Connections
    Orchestrator <--> Config
    Orchestrator <--> CredentialMgr
    Orchestrator <--> Recovery
    
    %% Agent Connections
    Orchestrator <--> Detection
    Orchestrator <--> Analysis
    Orchestrator <--> Remediation
    Orchestrator <--> Communication
    
    %% Agent Interactions
    Detection <--> Analysis
    Analysis <--> Remediation
    Remediation <--> Communication
    
    %% Intelligence Connections
    Detection <--> RulesEngine
    Analysis <--> Gemini
    Analysis <--> ContextRetrieval
    ContextRetrieval <--> IncidentDB
    
    %% GCP Connections
    Detection <--> BigQuery
    Detection <--> PubSub
    Analysis <--> BigQuery
    Remediation <--> CloudFunctions
    CredentialMgr <--> SecretMgr
    
    %% Style Classes
    classDef user fill:#f9f,stroke:#333,stroke-width:1px;
    classDef interface fill:#bbf,stroke:#333,stroke-width:1px;
    classDef core fill:#bfb,stroke:#333,stroke-width:1px;
    classDef agent fill:#fbf,stroke:#333,stroke-width:1px;
    classDef intelligence fill:#fdb,stroke:#333,stroke-width:1px;
    classDef cloud fill:#bff,stroke:#333,stroke-width:1px;
    classDef storage fill:#fbb,stroke:#333,stroke-width:1px;

    %% Apply Styles
    class User user;
    class UI,API,CLI interface;
    class Orchestrator,Config,CredentialMgr,Recovery core;
    class Detection,Analysis,Remediation,Communication agent;
    class Gemini,RulesEngine,ContextRetrieval intelligence;
    class GCP,BigQuery,PubSub,SecretMgr,CloudFunctions cloud;
    class IncidentDB storage;
```

## Core Components

This diagram details the internal components of each agent and the core services they depend on.

```mermaid
flowchart TB
    subgraph "Detection Agent"
        D_Agent[Agent Controller]
        D_Rules[Builtin Rules]
        D_QueryBuilder[Query Builder]
        D_QueryCache[Query Cache]
        D_Optimizer[Query Optimizer]
        D_EventCorrelator[Event Correlator]
        D_QuotaManager[Quota Manager]
        D_Pagination[Query Pagination]
        D_CatchupManager[Catchup Scan Manager]
        D_Monitoring[Performance Monitoring]
        
        D_Agent --> D_Rules
        D_Agent --> D_QueryBuilder
        D_QueryBuilder --> D_QueryCache
        D_QueryBuilder --> D_Optimizer
        D_Agent --> D_EventCorrelator
        D_Agent --> D_QuotaManager
        D_Agent --> D_Pagination
        D_Agent --> D_CatchupManager
        D_Agent --> D_Monitoring
    end
    
    subgraph "Analysis Agent"
        A_Agent[Agent Controller]
        A_EventExtraction[Event Extraction]
        A_EventCorrelation[Event Correlation]
        A_ContextRetrieval[Context Retrieval]
        A_IncidentRetrieval[Incident Retrieval]
        A_RecommendationEngine[Recommendation Engine]
        A_TokenOptimizer[Token Optimizer]
        A_Monitoring[Performance Monitoring]
        
        A_Agent --> A_EventExtraction
        A_Agent --> A_EventCorrelation
        A_Agent --> A_ContextRetrieval
        A_Agent --> A_IncidentRetrieval
        A_Agent --> A_RecommendationEngine
        A_Agent --> A_TokenOptimizer
        A_Agent --> A_Monitoring
    end
    
    subgraph "Remediation Agent"
        R_Agent[Agent Controller]
        R_ActionPlanner[Action Planner]
        R_RiskAssessor[Risk Assessor]
        R_ExecutionEngine[Execution Engine]
        R_VerificationSystem[Verification System]
        R_RollbackManager[Rollback Manager]
        
        R_Agent --> R_ActionPlanner
        R_Agent --> R_RiskAssessor
        R_Agent --> R_ExecutionEngine
        R_Agent --> R_VerificationSystem
        R_Agent --> R_RollbackManager
    end
    
    subgraph "Communication Agent"
        C_Agent[Agent Controller]
        C_NotificationSystem[Notification System]
        C_ReportGenerator[Report Generator]
        C_SeverityClassifier[Severity Classifier]
        C_StakeholderManager[Stakeholder Manager]
        
        C_Agent --> C_NotificationSystem
        C_Agent --> C_ReportGenerator
        C_Agent --> C_SeverityClassifier
        C_Agent --> C_StakeholderManager
    end
    
    subgraph "Orchestrator Agent"
        O_Agent[Agent Controller]
        O_WorkflowManager[Workflow Manager]
        O_StateManager[State Manager]
        O_ErrorHandler[Error Handler]
        O_AuditLogger[Audit Logger]
        O_CredentialManager[Credential Manager]
        
        O_Agent --> O_WorkflowManager
        O_Agent --> O_StateManager
        O_Agent --> O_ErrorHandler
        O_Agent --> O_AuditLogger
        O_Agent --> O_CredentialManager
    end
    
    subgraph "Core Services"
        Base[Base Agent Class]
        Exceptions[Exception Handling]
        Recovery[Recovery System]
        Secrets[Secrets Management]
    end
    
    %% Cross-Agent Interactions
    EventBus[Event Bus]
    
    D_Agent <--> EventBus
    A_Agent <--> EventBus
    R_Agent <--> EventBus
    C_Agent <--> EventBus
    O_Agent <--> EventBus
    
    %% Core Service Connections
    D_Agent --> Base
    A_Agent --> Base
    R_Agent --> Base
    C_Agent --> Base
    O_Agent --> Base
    
    O_ErrorHandler --> Exceptions
    O_ErrorHandler --> Recovery
    O_CredentialManager --> Secrets
    
    %% Agent Interactions
    D_EventCorrelator --> A_EventCorrelation
    A_RecommendationEngine --> R_ActionPlanner
    R_ExecutionEngine --> C_ReportGenerator
    O_WorkflowManager --> D_Agent
    O_WorkflowManager --> A_Agent
    O_WorkflowManager --> R_Agent
    O_WorkflowManager --> C_Agent
    
    %% Style definitions
    classDef detection fill:#f9d,stroke:#333,stroke-width:1px;
    classDef analysis fill:#bbf,stroke:#333,stroke-width:1px;
    classDef remediation fill:#bfb,stroke:#333,stroke-width:1px;
    classDef communication fill:#fdb,stroke:#333,stroke-width:1px;
    classDef orchestrator fill:#bff,stroke:#333,stroke-width:1px;
    classDef core fill:#ddd,stroke:#333,stroke-width:1px;
    classDef bus fill:#fbb,stroke:#333,stroke-width:1px;
    
    %% Apply styles
    class D_Agent,D_Rules,D_QueryBuilder,D_QueryCache,D_Optimizer,D_EventCorrelator,D_QuotaManager,D_Pagination,D_CatchupManager,D_Monitoring detection;
    class A_Agent,A_EventExtraction,A_EventCorrelation,A_ContextRetrieval,A_IncidentRetrieval,A_RecommendationEngine,A_TokenOptimizer,A_Monitoring analysis;
    class R_Agent,R_ActionPlanner,R_RiskAssessor,R_ExecutionEngine,R_VerificationSystem,R_RollbackManager remediation;
    class C_Agent,C_NotificationSystem,C_ReportGenerator,C_SeverityClassifier,C_StakeholderManager communication;
    class O_Agent,O_WorkflowManager,O_StateManager,O_ErrorHandler,O_AuditLogger,O_CredentialManager orchestrator;
    class Base,Exceptions,Recovery,Secrets core;
    class EventBus bus;
```

## Data Flow

This diagram shows how data flows through the SentinelOps system, from initial detection to incident resolution.

```mermaid
flowchart TD
    %% External Data Sources
    Logs[Cloud Logs] --> |Streaming| D_Ingestion[Log Ingestion]
    Alerts[Security Alerts] --> |Webhook| D_Ingestion
    Metrics[System Metrics] --> |Pull| D_Ingestion
    
    %% Detection Flow
    D_Ingestion --> D_Filtering[Log Filtering]
    D_Filtering --> D_Processing[Log Processing]
    D_Processing --> D_Matching[Rule Matching]
    D_RuleDB[(Rule Database)] --> D_Matching
    D_Matching --> |No Match| D_Storage[Log Storage]
    D_Matching --> |Match| D_SignalGen[Signal Generation]
    D_SignalGen --> D_Correlation[Signal Correlation]
    D_Correlation --> |Low Confidence| D_Storage
    D_Correlation --> |High Confidence| IncidentCreation[Incident Creation]
    
    %% Analysis Flow
    IncidentCreation --> A_Retrieval[Context Retrieval]
    D_Storage --> A_Retrieval
    HistoricalDB[(Historical Incidents)] --> A_Retrieval
    A_Retrieval --> A_Analysis[Incident Analysis]
    GeminiLLM[Gemini LLM] --> A_Analysis
    A_Analysis --> A_Classification[Incident Classification]
    A_Classification --> A_Enrichment[Context Enrichment]
    A_Enrichment --> A_RiskAssessment[Risk Assessment]
    A_RiskAssessment --> |Low Risk| Notification[Notification]
    A_RiskAssessment --> |Medium/High Risk| RemediationPlanning[Remediation Planning]
    
    %% Remediation Flow
    RemediationPlanning --> R_Actions[Action Generation]
    PlaybookDB[(Playbook Database)] --> R_Actions
    R_Actions --> R_Approval[Approval Process]
    R_Approval --> |Denied| Notification
    R_Approval --> |Auto-approved| R_Execution[Action Execution]
    R_Approval --> |Manually Approved| R_Execution
    R_Execution --> R_Verification[Result Verification]
    R_Verification --> |Failed| RemediationPlanning
    R_Verification --> |Success| IncidentClosure[Incident Closure]
    
    %% Communication Flow
    IncidentClosure --> C_ReportGen[Report Generation]
    Notification --> C_Notification[Stakeholder Notification]
    C_ReportGen --> C_Distribution[Report Distribution]
    C_Distribution --> C_Feedback[Feedback Collection]
    C_Feedback --> KnowledgeDB[(Knowledge Base)]
    
    %% Continuous Improvement
    KnowledgeDB --> D_RuleDB
    KnowledgeDB --> PlaybookDB
    IncidentClosure --> HistoricalDB
    
    %% Style Classes
    classDef source fill:#f9f,stroke:#333,stroke-width:1px;
    classDef detection fill:#bbf,stroke:#333,stroke-width:1px;
    classDef analysis fill:#bfb,stroke:#333,stroke-width:1px;
    classDef remediation fill:#fbf,stroke:#333,stroke-width:1px;
    classDef communication fill:#bff,stroke:#333,stroke-width:1px;
    classDef storage fill:#fdb,stroke:#333,stroke-width:1px;
    classDef external fill:#ddd,stroke:#333,stroke-width:1px;
    
    %% Apply Styles
    class Logs,Alerts,Metrics source;
    class D_Ingestion,D_Filtering,D_Processing,D_Matching,D_SignalGen,D_Correlation detection;
    class A_Retrieval,A_Analysis,A_Classification,A_Enrichment,A_RiskAssessment analysis;
    class RemediationPlanning,R_Actions,R_Approval,R_Execution,R_Verification remediation;
    class Notification,C_ReportGen,C_Distribution,C_Feedback,IncidentClosure communication;
    class D_Storage,HistoricalDB,D_RuleDB,PlaybookDB,KnowledgeDB storage;
    class GeminiLLM,IncidentCreation external;
```

## Agent Interactions

This sequence diagram illustrates how the different agents interact during an incident response scenario.

```mermaid
sequenceDiagram
    participant User as Security Engineer
    participant Orchestrator as Orchestrator Agent
    participant Detection as Detection Agent
    participant Analysis as Analysis Agent
    participant Remediation as Remediation Agent
    participant Communication as Communication Agent
    participant GCP as Google Cloud Platform
    
    %% Incident Detection Phase
    Detection->>GCP: Query security logs
    GCP-->>Detection: Log data
    Detection->>Detection: Apply detection rules
    Detection->>Orchestrator: Report potential incident
    Orchestrator->>Orchestrator: Create incident record
    Orchestrator->>Analysis: Request incident analysis
    
    %% Analysis Phase
    Analysis->>GCP: Retrieve additional context
    GCP-->>Analysis: Context data
    Analysis->>Analysis: Correlate events
    Analysis->>Analysis: Generate incident summary
    Analysis->>Orchestrator: Provide analysis results
    Orchestrator->>Orchestrator: Update incident record
    
    %% Decision Point
    alt High Severity Incident
        Orchestrator->>Remediation: Request automated response
        Orchestrator->>Communication: Notify stakeholders immediately
        Communication->>User: Send high-priority alert
    else Medium Severity Incident
        Orchestrator->>Communication: Request approval for remediation
        Communication->>User: Send approval request
        User-->>Communication: Approve remediation
        Communication->>Orchestrator: Forward approval
        Orchestrator->>Remediation: Request remediation with approval
    else Low Severity Incident
        Orchestrator->>Communication: Log incident for review
        Communication->>User: Add to security digest
    end
    
    %% Remediation Phase (for High/Medium)
    Remediation->>Remediation: Generate remediation plan
    Remediation->>Orchestrator: Submit remediation plan
    Orchestrator->>Orchestrator: Validate plan
    Orchestrator->>Remediation: Approve execution
    Remediation->>GCP: Execute remediation steps
    GCP-->>Remediation: Execution results
    Remediation->>Orchestrator: Report remediation results
    
    %% Verification and Closure
    Orchestrator->>Detection: Request verification scan
    Detection->>GCP: Run verification queries
    GCP-->>Detection: Verification data
    Detection->>Orchestrator: Confirm resolution
    
    %% Reporting
    Orchestrator->>Communication: Request incident report
    Communication->>Communication: Generate comprehensive report
    Communication->>User: Deliver incident report
    Communication->>Orchestrator: Report delivery confirmation
    Orchestrator->>Orchestrator: Close incident
    
    %% Learning Phase
    Orchestrator->>Detection: Update detection rules
    Orchestrator->>Analysis: Update analysis patterns
    Orchestrator->>Remediation: Update remediation playbooks
```

## GCP Integration

This diagram shows how SentinelOps integrates with various Google Cloud Platform services.

```mermaid
graph TB
    subgraph "SentinelOps System"
        API[API Gateway]
        Core[Core Engine]
        Agents[Agent System]
        Storage[Local Storage]
    end
    
    subgraph "Google Cloud Platform"
        subgraph "Data Sources"
            CloudLogs[(Cloud Logging)]
            SecurityCmd[(Security Command Center)]
            AuditLogs[(Audit Logs)]
            VPCFlow[(VPC Flow Logs)]
            FirewallRules[(Firewall Rules)]
        end
        
        subgraph "Data Processing"
            BigQuery[(BigQuery)]
            Dataflow[Dataflow]
            ADKContext[ADK Context Management]
        end
        
        subgraph "Execution Environment"
            CloudRun[Cloud Run]
            CloudFunctions[Cloud Functions]
            GCE[Compute Engine]
        end
        
        subgraph "Security & Management"
            IAM[Identity & Access Management]
            SecretManager[Secret Manager]
            KMS[Key Management Service]
        end
        
        subgraph "AI & ML"
            Gemini[Gemini API]
            VertexAI[Vertex AI]
        end
    end
    
    %% Data Source Connections
    CloudLogs --> BigQuery
    SecurityCmd --> BigQuery
    AuditLogs --> BigQuery
    VPCFlow --> BigQuery
    FirewallRules --> BigQuery
    
    %% Data Processing Flow
    CloudLogs --> PubSub
    PubSub --> Dataflow
    Dataflow --> BigQuery
    
    %% SentinelOps to GCP Connections
    API --> IAM
    Core --> CloudRun
    Agents --> CloudFunctions
    Storage --> BigQuery
    
    %% Security Connections
    Core --> SecretManager
    Core --> KMS
    Agents --> SecretManager
    
    %% AI Connections
    Agents --> Gemini
    Agents --> VertexAI
    
    %% Execution Environment
    CloudRun --> IAM
    CloudFunctions --> IAM
    GCE --> IAM
    
    %% Style Classes
    classDef sentinelops fill:#f9f,stroke:#333,stroke-width:1px;
    classDef datasource fill:#bbf,stroke:#333,stroke-width:1px;
    classDef processing fill:#bfb,stroke:#333,stroke-width:1px;
    classDef execution fill:#fbf,stroke:#333,stroke-width:1px;
    classDef security fill:#fdb,stroke:#333,stroke-width:1px;
    classDef ai fill:#bff,stroke:#333,stroke-width:1px;
    
    %% Apply Styles
    class API,Core,Agents,Storage sentinelops;
    class CloudLogs,SecurityCmd,AuditLogs,VPCFlow,FirewallRules datasource;
    class BigQuery,Dataflow,PubSub processing;
    class CloudRun,CloudFunctions,GCE execution;
    class IAM,SecretManager,KMS security;
    class Gemini,VertexAI ai;
```

## Incident Response Workflow

This state diagram illustrates the complete incident response workflow, from detection to resolution.

```mermaid
stateDiagram-v2
    [*] --> LogMonitoring
    
    state "Continuous Monitoring" as LogMonitoring {
        [*] --> Scanning
        Scanning --> RuleMatching: Log Entry
        RuleMatching --> Scanning: No Match
        RuleMatching --> SignalGeneration: Match Found
        SignalGeneration --> EventCorrelation
        EventCorrelation --> Scanning: Low Confidence
        EventCorrelation --> [*]: High Confidence
    }
    
    LogMonitoring --> IncidentCreation: Incident Detected
    
    state "Incident Analysis" as IncidentAnalysis {
        [*] --> ContextCollection
        ContextCollection --> EventCorrelation
        EventCorrelation --> RiskAssessment
        RiskAssessment --> SeverityClassification
        SeverityClassification --> [*]
    }
    
    IncidentCreation --> IncidentAnalysis
    
    IncidentAnalysis --> TriageProcess
    
    state "Triage & Prioritization" as TriageProcess {
        [*] --> ImpactAssessment
        ImpactAssessment --> UrgencyEvaluation
        UrgencyEvaluation --> ResponseSelection
        ResponseSelection --> [*]
    }
    
    state "Response Action" as ResponseAction {
        state AutomatedResponse {
            [*] --> ActionPlanning
            ActionPlanning --> Execution
            Execution --> Verification
            Verification --> [*]
        }
        
        state ManualResponse {
            [*] --> ApprovalRequest
            ApprovalRequest --> WaitingForApproval
            WaitingForApproval --> ActionPlanning: Approved
            WaitingForApproval --> Cancelled: Denied
            ActionPlanning --> GuidedExecution
            GuidedExecution --> ManualVerification
            ManualVerification --> [*]
            Cancelled --> [*]
        }
        
        [*] --> ResponseTypeSelection
        ResponseTypeSelection --> AutomatedResponse: Automated Path
        ResponseTypeSelection --> ManualResponse: Manual Path
        AutomatedResponse --> [*]
        ManualResponse --> [*]
    }
    
    TriageProcess --> ResponseAction
    
    ResponseAction --> VerificationProcess
    
    state "Verification & Closure" as VerificationProcess {
        [*] --> EffectivenessCheck
        EffectivenessCheck --> IncidentClosure: Successful
        EffectivenessCheck --> EscalationProcess: Failed
        EscalationProcess --> IncidentReassessment
        IncidentReassessment --> [*]
        IncidentClosure --> LessonsLearned
        LessonsLearned --> RuleUpdates
        RuleUpdates --> PlaybookUpdates
        PlaybookUpdates --> [*]
    }
    
    VerificationProcess --> [*]
    
    state "Communication Flow" as CommunicationFlow {
        [*] --> InitialAlert
        InitialAlert --> StatusUpdates
        StatusUpdates --> ResolutionNotice
        ResolutionNotice --> FinalReport
        FinalReport --> [*]
    }
    
    IncidentCreation --> CommunicationFlow
    ResponseAction --> CommunicationFlow: Status Update
    VerificationProcess --> CommunicationFlow: Resolution
```

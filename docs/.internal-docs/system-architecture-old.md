# SentinelOps Architecture Overview

## System Architecture

SentinelOps is a multi-agent, AI-powered platform that automates the detection, triage, and response to security incidents in Google Cloud environments. The system uses the Google Agent Development Kit (ADK) to orchestrate specialized agents that work together to provide comprehensive security monitoring and response.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Google Cloud Platform                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐ │
│  │   BigQuery      │     │  Cloud Storage  │     │  Compute Engine │ │
│  │  (Log Analysis) │     │   (Artifacts)   │     │  (Remediation)  │ │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘ │
│           │                       │                         │          │
│  ┌────────┴────────┐     ┌───────┴────────┐     ┌─────────┴────────┐ │
│  │   Firestore     │     │  Secret Manager│     │   Vertex AI      │ │
│  │  (State Store)  │     │   (Credentials)│     │  (Gemini LLM)    │ │
│  └────────┬────────┘     └───────┬────────┘     └─────────┬────────┘ │
│           │                       │                         │          │
└───────────┼───────────────────────┼─────────────────────────┼──────────┘
            │                       │                         │
┌───────────┼───────────────────────┼─────────────────────────┼──────────┐
│           │                       │                         │          │
│  ┌────────▼────────────────────────▼─────────────────────────▼────────┐│
│  │                    Orchestration Agent (ADK)                        ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            ││
│  │  │ ParallelAgent│  │   Transfer   │  │    State     │            ││
│  │  │   Pattern    │  │    Tools     │  │  Management  │            ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘            ││
│  └──────────────────────────┬──────────────────────────────────────────┘│
│                             │                                           │
│  ┌──────────────────────────┼──────────────────────────────────────┐  │
│  │                          │                                       │  │
│  │  ┌─────────────┐  ┌─────▼──────┐  ┌──────────────┐  ┌────────┐│  │
│  │  │ Detection   │  │  Analysis  │  │ Remediation  │  │ Comm.  ││  │
│  │  │   Agent     │◄─►    Agent    │◄─►    Agent     │◄─► Agent  ││  │
│  │  │             │  │            │  │              │  │        ││  │
│  │  │ • Monitor   │  │ • Analyze  │  │ • Execute    │  │ • Slack││  │
│  │  │ • Detect    │  │ • Triage   │  │ • Rollback   │  │ • Email││  │
│  │  │ • Alert     │  │ • Enrich   │  │ • Mitigate   │  │ • API  ││  │
│  │  └─────────────┘  └────────────┘  └──────────────┘  └────────┘│  │
│  │                                                                 │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                           SentinelOps Core                             │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                         Shared Services                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │ Logging  │  │ Metrics  │  │  Auth    │  │ Health Check │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                         FastAPI REST API                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │/incidents│  │ /agents  │  │ /health  │  │ /remediation │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Orchestration Agent (Central Coordinator)
The Orchestration Agent is built on Google ADK using both ParallelAgent and custom coordinator patterns.

**Responsibilities:**
- Manages agent lifecycle using ADK patterns
- Routes messages via ADK Transfer Tools
- Implements workflow orchestration with ParallelAgent
- Handles error recovery with ADK's built-in retry logic
- Maintains system state in Firestore

**Key Technologies:**
- Google Agent Development Kit (ADK)
- ADK Transfer Tools for agent communication
- ADK ParallelAgent for orchestration
- Firestore for state management

### 2. Detection Agent
Monitors Google Cloud resources and security logs to identify potential security incidents.

**Data Sources:**
- Cloud Logging
- BigQuery security logs
- Chronicle SIEM (if available)
- Cloud Asset Inventory
- VPC Flow Logs

**Detection Methods:**
- Rule-based detection
- Anomaly detection using ML
- Threat intelligence correlation
- Behavioral analysis

### 3. Analysis Agent
Performs deep analysis on detected incidents using Gemini AI and security context.

**Analysis Process:**
1. Incident enrichment with additional context
2. Severity assessment
3. Impact analysis
4. Root cause identification
5. Recommendation generation

**Integrations:**
- Vertex AI (Gemini) for intelligent analysis
- BigQuery for historical data
- Threat intelligence feeds

### 4. Remediation Agent
Executes automated remediation actions based on analysis results.

**Remediation Actions:**
- Isolate compromised instances
- Revoke compromised credentials
- Apply security patches
- Roll back unauthorized changes
- Update firewall rules

**Safety Features:**
- Dry-run mode for testing
- Approval workflows
- Rollback capabilities
- Audit logging

### 5. Communication Agent
Handles notifications and reporting for security incidents.

**Communication Channels:**
- Slack webhooks
- Email notifications
- SMS alerts (via Twilio)
- API webhooks
- Dashboard updates

**Features:**
- Template-based messaging
- Priority-based routing
- Escalation workflows
- Delivery tracking

## Data Flow

### Incident Detection Flow
```
1. Security Event Occurs
   └─► Cloud Logging captures event
       └─► Detection Agent polls/monitors logs via ADK tools
           └─► Pattern matching and anomaly detection (RulesEngineTool)
               └─► Incident created in system
                   └─► TransferToOrchestratorAgentTool invoked
```

### Incident Response Flow (ADK-Based)
```
1. Detection Agent identifies threat
   └─► TransferToOrchestratorAgentTool transfers context
       └─► Orchestrator Agent receives transfer
           └─► TransferToAnalysisAgentTool routes to Analysis
               └─► Gemini AI analyzes incident via GeminiAnalysisTool
                   └─► TransferToRemediationAgentTool for remediation
                       └─► TransferToCommunicationAgentTool for notifications
                           └─► Incident marked as resolved in Firestore
```

## ADK Architecture Patterns

### Tool-Based Architecture
All business logic is encapsulated in ADK tools that inherit from `BaseTool`:

```
BaseTool (ADK)
    ├── Detection Tools
    │   ├── LogMonitoringTool - BigQuery log analysis
    │   ├── AnomalyDetectionTool - ML-based detection
    │   ├── RulesEngineTool - Rule evaluation
    │   └── EventCorrelatorTool - Event correlation
    │
    ├── Analysis Tools
    │   ├── IncidentAnalysisTool - Gemini integration
    │   ├── RecommendationTool - Remediation suggestions
    │   └── ContextTool - Historical context retrieval
    │
    ├── Remediation Tools
    │   ├── BlockIPTool - Firewall rule updates
    │   ├── IsolateVMTool - VM quarantine
    │   └── RevokeCredentialsTool - IAM actions
    │
    └── Transfer Tools
        ├── TransferToDetectionAgentTool
        ├── TransferToAnalysisAgentTool
        ├── TransferToRemediationAgentTool
        └── TransferToCommunicationAgentTool
```

### Agent Communication Pattern
ADK's transfer system replaces traditional messaging:

1. **Traditional (Pre-ADK)**:
   - Direct Pub/Sub messaging
   - Manual message formatting
   - Custom retry logic
   - Complex error handling

2. **ADK Pattern**:
   - Transfer tools with typed interfaces
   - Automatic context preservation
   - Built-in retry and error handling
   - Seamless agent handoffs

### State Management
Firestore serves as the central state store:
- Incident state tracking
- Agent coordination state
- Workflow progress
- Audit trails

### Multi-Agent Orchestration
Two complementary patterns implemented:

1. **ParallelAgent Pattern**:
   - Concurrent agent execution
   - Automatic result aggregation
   - Built-in error handling

2. **Custom Coordinator Pattern**:
   - Complex workflow orchestration
   - Conditional routing
   - Business logic integration

## Security Considerations

### Authentication & Authorization
- Service accounts with least privilege
- API key and JWT token support
- Role-based access control (RBAC)
- OAuth 2.0 for user authentication

### Data Protection
- Encryption at rest using Google Cloud KMS
- Encryption in transit using TLS 1.3
- Secret Manager for sensitive credentials
- Data retention policies

### Network Security
- Private VPC for agent communication
- Cloud NAT for outbound connections
- Firewall rules for ingress control
- VPC Service Controls for API access

## Scalability & Performance

### Horizontal Scaling
- Agents run as Cloud Run services
- Auto-scaling based on load
- Regional deployment for HA
- Load balancing across instances

### Performance Optimization
- Caching with Redis/Memorystore
- Batch processing for logs
- Async processing throughout
- Connection pooling

## Monitoring & Observability

### Metrics
- Prometheus metrics endpoint
- Google Cloud Monitoring integration
- Custom dashboards in Grafana
- SLI/SLO tracking

### Logging
- Structured JSON logging
- Correlation IDs for tracing
- Log aggregation in Cloud Logging
- Log-based metrics and alerts

### Tracing
- OpenTelemetry integration
- Distributed tracing
- Performance profiling
- Error tracking

## Deployment Architecture

### Development Environment
- Local Docker containers
- Minikube for Kubernetes testing
- Local emulators for GCP services
- Mock data generators

### Production Environment
- Cloud Run for stateless agents
- Firestore for state management
- ADK Transfer Tools for agent communication
- Cloud Load Balancing

### CI/CD Pipeline
- GitHub Actions for CI
- Cloud Build for container builds
- Artifact Registry for images
- Automated deployment to Cloud Run

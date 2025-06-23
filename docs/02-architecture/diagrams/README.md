# SentinelOps Architecture Diagrams

This directory contains architecture diagrams for the SentinelOps platform, built with Google's Agent Development Kit (ADK).

## Available Diagrams

1. **[System Architecture with ADK](./system-architecture.md)**
   - Complete system architecture showing ADK framework integration
   - Agent inheritance from ADK base classes (LlmAgent, SequentialAgent)
   - ADK tools implementing security domain expertise
   - Integration points with Google Cloud services

2. **[Data Flow with ADK](./data-flow.md)**
   - End-to-end incident processing using ADK transfer system
   - Tool context propagation between agents
   - Sequence of operations from detection to remediation
   - ADK patterns for error handling and fallbacks

3. **[Agent Interactions with ADK](./agent-interactions.md)**
   - ADK transfer tools for agent communication
   - Routing configuration and rules
   - Tool-based communication patterns
   - Production patterns like circuit breakers

4. **[Deployment Architecture](./deployment-architecture.md)**
   - Cloud Run deployment for ADK agents
   - Containerization strategy for each agent
   - Integration with Vertex AI for Gemini models
   - Monitoring and observability setup

## Key ADK Integration Points

### Framework Components
- **LlmAgent**: Base class for Detection, Analysis, Remediation, and Communication agents
- **SequentialAgent**: Used by Orchestrator for workflow coordination
- **BaseTool**: Extended by all domain-specific tools (20+ production tools)
- **Transfer System**: Native ADK agent-to-agent communication

### Production Patterns
- **Tool Composition**: Each agent has 5-10 specialized tools
- **Context Propagation**: Rich context passed between agents
- **Error Resilience**: Circuit breakers and fallback mechanisms
- **Observability**: Full telemetry integration with Cloud Monitoring

## Architecture Highlights

1. **ADK-Native Design**: Built specifically for ADK patterns and best practices
2. **Direct API Integration**: Agents interact directly with GCP services
3. **Tool-First Architecture**: All functionality implemented as ADK tools
4. **Production Ready**: Includes caching, rate limiting, and safety controls

## Viewing Diagrams

These diagrams use Mermaid syntax and can be viewed in:
- GitHub (automatic rendering)
- VS Code with Mermaid extension
- Online at [mermaid.live](https://mermaid.live/)

## Understanding the Diagrams

### Color Coding
- 🔵 **Blue tones**: Google ADK framework components
- 🟡 **Yellow tones**: SentinelOps ADK agents
- 🟣 **Purple tones**: ADK tools
- 🔴 **Red/Orange tones**: Google Cloud services

### Reading the Flow
1. Start with System Architecture to understand the overall structure
2. Review Agent Interactions to see communication patterns
3. Follow Data Flow for detailed processing sequences
4. Check Deployment Architecture for infrastructure details

## ADK Implementation Philosophy

These diagrams reflect a production-grade implementation of ADK:
- **ADK provides the framework**, SentinelOps provides domain expertise
- **Tools are first-class citizens**, implementing security logic
- **Native ADK patterns** for all agent communication
- **Enterprise features** built into every component

This demonstrates how ADK should be used for production systems - as a comprehensive framework for building sophisticated multi-agent security applications.
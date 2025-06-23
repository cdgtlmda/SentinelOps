# SentinelOps Architecture Documentation

This directory contains architectural documentation for the SentinelOps project, including diagrams, data flows, and component interactions.

## Overview

SentinelOps is a multi-agent, AI-powered platform that automates the detection, triage, and response to security incidents in cloud environments. The architecture consists of five specialized agents working together to provide end-to-end incident response capabilities.

## Directory Contents

- [diagrams.md](./diagrams.md) - Comprehensive set of Mermaid diagrams documenting the system architecture
- [diagrams/](./diagrams/) - Generated SVG files for each architecture diagram
- [generate_diagrams.py](./generate_diagrams.py) - Script to generate SVG files from the Mermaid diagrams
- [system-architecture.md](./diagrams/system-architecture.md) - Detailed description of the system architecture
- [data-flow.md](./data-flow.md) - Documentation of data flows through the system
- [agent-interactions.md](./agent-interactions.md) - Description of how agents interact with each other
- [sequence-diagrams.md](./sequence-diagrams.md) - Sequence diagrams for key workflows
- [gcp-integration.md](./gcp-integration.md) - Details of integration with Google Cloud Platform
- [incident_response_workflow.md](./incident_response_workflow.md) - Documentation of the incident response workflow

## Key Architecture Components

1. **Detection Agent** - Continuously scans logs and security feeds for suspicious activity
2. **Analysis Agent** - Pulls relevant data, correlates events, and summarizes findings
3. **Remediation Agent** - Suggests and executes mitigation actions
4. **Communication Agent** - Notifies stakeholders and generates reports
5. **Orchestrator Agent** - Coordinates all agents and ensures auditability

## Generating Diagrams

To generate SVG files from the Mermaid diagrams:

1. Ensure you have Node.js installed
2. Install the Mermaid CLI: `npm install -g @mermaid-js/mermaid-cli`
3. Run the generation script: `python generate_diagrams.py`

The generated SVG files will be placed in the `diagrams/` directory.

## Architecture Philosophy

The SentinelOps architecture follows these key principles:

1. **Agent Autonomy** - Each agent operates independently but collaboratively
2. **Explainability** - All actions and decisions are documented and explained
3. **Modularity** - Components are designed to be replaceable and extensible
4. **Resilience** - The system can recover from failures in any component
5. **Security** - Zero-trust approach with least privilege access

For more detailed information, refer to the specific documentation files listed above.

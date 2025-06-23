# 🛡️ SentinelOps - Enterprise Security Operations Platform

> **🔒 SECURITY NOTICE**: This repository has been sanitized for public release. It contains **NO** real credentials, service account keys, or sensitive information. All configuration values are placeholders that you must replace with your own when setting up SentinelOps.

**SentinelOps** is a comprehensive, AI-powered security operations platform built on Google Cloud Platform (GCP) and the Google Agent Development Kit (ADK). It provides automated threat detection, intelligent analysis, and coordinated incident response through a multi-agent architecture.

## 🚨 **Setup Requirements**

Before using SentinelOps, you **MUST**:
1. **Create your own GCP project and service accounts**
2. **Replace all placeholder values** (`your-gcp-project-id`, `your-admin-password`, etc.)
3. **Generate your own service account keys** (none are included in this repository)
4. **Configure your own API keys** for external services (Slack, email, etc.)

See the [Quick Start Guide](docs/01-getting-started/quick-start.md) for detailed setup instructions.

# SentinelOps: Autonomous Multi-Agent Incident Response for Cloud Security

SentinelOps is a multi-agent, AI-powered platform that automates the detection, triage, and response to security incidents in cloud environments. It leverages the Agent Development Kit (ADK) and Google Cloud technologies to orchestrate specialized agents that collaboratively identify threats, analyze logs, recommend remediations, and execute mitigation steps.

> ⚠️ **Important**: Before making this repository public, see [CREDENTIAL_SAFETY.md](./CREDENTIAL_SAFETY.md) for handling sensitive credentials

## Key Features

- **Automated End-to-End Incident Response:** From detection to resolution, minimizing manual intervention
- **Explainable AI:** Uses Gemini to generate human-readable explanations for each step
- **Extensible Architecture:** Easily add new agent types (e.g., compliance, forensics) as plugins
- **Real-Time Collaboration:** Agents communicate and share context
- **Dual UI Options:** Choose between demonstration UI with threat simulator or full operational interface
- **Live Threat Simulation:** 25+ realistic security scenarios for testing and demonstrations

## Architecture

SentinelOps consists of five specialized agent types:

1. **Detection Agent:** Continuously scans logs and security feeds for suspicious activity
2. **Analysis Agent:** Pulls relevant data, correlates events, and summarizes findings
3. **Remediation Agent:** Suggests and executes mitigation actions
4. **Communication Agent:** Notifies stakeholders and generates reports
5. **Orchestrator Agent:** Coordinates all agents and ensures auditability

### Technology Stack

- **Backend**: Python 3.9+, Google Agent Development Kit (ADK), LangChain
- **AI/ML**: Google Gemini API, BigQuery ML
- **Cloud**: Google Cloud Platform (GCP)
- **Data Storage**: BigQuery, Cloud Storage, Firestore
- **Security**: Secret Manager, IAM, VPC Service Controls
- **Frontend**: Next.js (NEW UI), React (OLD UI), WebSocket real-time updates
- **API**: FastAPI with dual endpoints (Dashboard + Threat Simulation)

## ADK Architecture

SentinelOps is built on Google's Agent Development Kit (ADK), providing:

### Agent Hierarchy
```
SentinelOpsMultiAgent (ParallelAgent)
├── OrchestratorAgent (SequentialAgent) - Primary Coordinator
│   ├── DetectionAgent (LlmAgent) - Continuous Monitoring
│   ├── AnalysisAgent (LlmAgent) - Gemini-powered Analysis
│   ├── RemediationAgent (LlmAgent) - Response Actions
│   └── CommunicationAgent (LlmAgent) - Notifications
```

### ADK Components
- **Base Agent**: All agents inherit from `SentinelOpsBaseAgent` which extends ADK's `LlmAgent`
- **Tools**: Google Cloud services wrapped as ADK `BaseTool` implementations
- **Transfer System**: Inter-agent communication using ADK's transfer tools
- **Session Management**: Persistent sessions with Firestore backing
- **Telemetry**: Cloud Trace and Cloud Logging integration for monitoring

### Key ADK Features Used
- Multi-agent collaboration patterns (Parallel and Sequential agents)
- Built-in Gemini integration for AI-powered analysis
- Tool validation and schema enforcement
- Automatic retry and error handling
- Session persistence and context sharing

### High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Security Eng   │     │    Dashboard     │     │   Command-Line  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                │
                        ┌───────┴────────┐
                        │   API Layer    │
                        └───────┬────────┘
                                │
                       ┌────────┴────────┐
                       │ Orchestrator    │
                       └────────┬────────┘
                                │
       ┌──────────────┬─────────┼─────────┬──────────────┐
       │              │         │         │              │
┌──────▼─────┐ ┌──────▼─────┐   │   ┌─────▼──────┐ ┌─────▼──────┐
│ Detection  │ │  Analysis  │   │   │ Remediation│ │Communication│
└──────┬─────┘ └──────┬─────┘   │   └─────┬──────┘ └─────┬──────┘
       │              │         │         │              │
       └──────────────┴─────────┼─────────┴──────────────┘
                                │
                       ┌────────▼────────┐
                       │  Google Cloud   │
                       └─────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.12+
- Google Cloud SDK
- Agent Development Kit (ADK)
- Node.js 18+ (for frontend)
- Google Cloud Platform project with APIs enabled:
  - BigQuery
  - Pub/Sub
  - Cloud Functions
  - Secret Manager
  - Gemini API

### Quick Start (Recommended)

```bash
# Clone repository
git clone https://github.com/cdgtlmda/sentinelops.git
cd sentinelops

# One-command setup and launch
./build_and_run.sh
```

This script will:
- ✅ Check prerequisites and install dependencies
- ✅ Set up GCP authentication and enable APIs
- ✅ Start API server (port 8000) with threat simulator
- ✅ Launch NEW UI (port 3000) with live demonstrations

### 🎯 Component Status (June 2025)

#### **Frontend Interface**
- **Location**: `/frontend/sentinelops-ui` directory
- **Status**: ✅ Production-ready monorepo
- **Components**:
  - Main application (port 3000) - Security dashboard and management
  - Marketing site (port 3001) - Documentation and information
  - API integration layer - Backend connectivity
- **Technology**: Next.js 14.2, TypeScript, TailwindCSS, Turborepo
- **Features**: Real-time updates, threat simulation, modern UI components

### UI Options

SentinelOps provides two user interface options:

#### NEW UI (Recommended for Demonstrations)
- **Location**: `/ui` directory
- **Technology**: Next.js with real-time WebSocket updates
- **Features**: Live threat simulation, 25+ security scenarios, interactive dashboard
- **Startup**: `./build_and_run.sh` (fully automated)
- **URLs**:
  - Frontend: http://localhost:3000
  - API: http://localhost:8000
  - Threat Simulator: http://localhost:3000/threats

#### OLD UI (For Development/Advanced Features)
- **Location**: `/frontend` directory
- **Technology**: React with extensive component library
- **Features**: Full incident management, advanced workflows, mobile optimization
- **Startup**: Manual component startup (see docs/development/)

### Manual Installation

```bash
# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure GCP credentials
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Install frontend dependencies (for NEW UI)
cd ui && npm install && cd ..
```

## Usage

### Quick Demo (NEW UI)
```bash
# All-in-one startup (includes API + Frontend + Threat Simulator)
./build_and_run.sh

# Access the platform
open http://localhost:3000
```

### Manual Startup (Development)
```bash
# Start API server with threat simulator
python working_api.py

# Start NEW UI (separate terminal)
cd ui && npm run dev

# Access threat simulator
open http://localhost:3000/threats
```

### Threat Simulation
```bash
# CLI threat simulation
python src/tools/threat_simulator.py --stats
python src/tools/threat_simulator.py --batch 5

# API endpoints
curl http://localhost:8000/api/threat/stats
curl -X POST http://localhost:8000/api/threat/generate
```

## Documentation

- [System Architecture](docs/architecture/system-architecture.md)
- [Data Flows](docs/architecture/data-flow.md)
- [Agent Interactions](docs/architecture/agent-interactions.md)
- [API Reference](docs/api/README.md)
- [Deployment Guide](docs/deployment/README.md)

## Demo

See the [demo video](link-to-demo) for a walkthrough of a simulated incident response workflow.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for the Agent Development Kit Hackathon with Google Cloud
- Powered by Gemini models for natural language processing

# Local Development Guide with ADK

This comprehensive guide covers setting up and running SentinelOps locally with Google's Agent Development Kit (ADK) for development and testing.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [ADK Installation](#adk-installation)
4. [Local Services Setup](#local-services-setup)
5. [Running Agents Locally](#running-agents-locally)
6. [Development Workflow](#development-workflow)
7. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
8. [Best Practices](#best-practices)

## Prerequisites

### System Requirements
- Python 3.12+ (updated ADK requirement)
- Docker Desktop 20.10+
- Google Cloud SDK 400.0.0+
- Git 2.30+
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

### Account Requirements
- Google Cloud Project with billing enabled
- Service account with appropriate permissions
- Access to required GCP services

### Required Tools Installation
```bash
# Install Python (using pyenv)
pyenv install 3.12.0
pyenv local 3.12.0

# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Install Docker Desktop
# Download from https://www.docker.com/products/docker-desktop

# Verify installations
python --version  # Should be 3.12+
gcloud version
docker --version
```

## Environment Setup

### 1. Clone Repository
```bash
# Clone the repository
git clone https://github.com/cdgtlmda/SentinelOps.git
cd SentinelOps

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
# Install ADK first
pip install google-adk>=1.2.0

# Install project dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify ADK installation
python -c "from google.adk import Agent; print('ADK installed successfully')"
```

### 3. Configure Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
cat >> .env << EOF
# Core Configuration
GOOGLE_CLOUD_PROJECT=your-dev-project
ENVIRONMENT=development
DEBUG=true

# ADK Configuration
ADK_TELEMETRY_ENABLED=false  # Disable for local dev
ADK_LOG_LEVEL=DEBUG
ADK_TRACE_ENABLED=true

# Local Service Ports
FIRESTORE_EMULATOR_HOST=localhost:8080
BIGQUERY_EMULATOR_HOST=localhost:9050
PUBSUB_EMULATOR_HOST=localhost:8085

# Agent Configuration
DETECTION_AGENT_PORT=8001
ANALYSIS_AGENT_PORT=8002
REMEDIATION_AGENT_PORT=8003
COMMUNICATION_AGENT_PORT=8004
ORCHESTRATOR_AGENT_PORT=8005

# Development Settings
HOT_RELOAD=true
MOCK_EXTERNAL_SERVICES=true
DRY_RUN_DEFAULT=true
EOF
```

### 4. Set Up GCP Authentication
```bash
# Authenticate with GCP
gcloud auth application-default login

# Create development service account
gcloud iam service-accounts create sentinelops-dev \
  --display-name="SentinelOps Development"

# Download key
gcloud iam service-accounts keys create \
  ./service-account-dev.json \
  --iam-account=sentinelops-dev@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/service-account-dev.json"
```

## ADK Installation

### 1. Install ADK Package
```bash
# Install ADK from PyPI
pip install google-adk>=1.2.0

# Verify ADK installation
python -c "from google.adk.agents import LlmAgent; print('ADK installed successfully')"
```

### 2. Configure ADK for Development
```python
# config/adk_dev_config.py
ADK_DEV_CONFIG = {
    "development_mode": True,
    "mock_llm": False,  # Use real Gemini even in dev
    "telemetry": {
        "enabled": False,  # Disable for local dev
        "console_output": True
    },
    "tools": {
        "timeout": 60,  # Longer timeout for debugging
        "validation": "warn"  # Warn instead of error
    },
    "agents": {
        "hot_reload": True,
        "debug_mode": True
    }
}
```

### 3. Initialize ADK Components
```python
# Initialize ADK for local development
import os
import logging

# Set development environment variables
os.environ['GOOGLE_CLOUD_PROJECT'] = 'your-dev-project'
os.environ['ADK_DEBUG'] = 'true'

# Configure logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Local Services Setup

### 1. Start Local Emulators
```bash
# Start all emulators using Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Or start individually:

# Firestore Emulator
gcloud emulators firestore start \
  --host-port=localhost:8080 \
  --project=$GOOGLE_CLOUD_PROJECT

# BigQuery Emulator (using third-party)
docker run -d \
  --name bigquery-emulator \
  -p 9050:9050 \
  ghcr.io/goccy/bigquery-emulator:latest \
  --project=$GOOGLE_CLOUD_PROJECT

# Pub/Sub Emulator
gcloud emulators pubsub start \
  --host-port=localhost:8085 \
  --project=$GOOGLE_CLOUD_PROJECT
```

### 2. Initialize Local Data
```bash
# Create Firestore collections and indexes
python scripts/local_development/init_firestore.py

# Create BigQuery datasets and tables
python scripts/local_development/init_bigquery.py

# Load sample data
python scripts/local_development/load_sample_data.py
```

### 3. Configure Local Secrets
```bash
# Create local secrets file
cat > .secrets.local << EOF
SLACK_WEBHOOK_URL=http://localhost:8888/slack-webhook
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=test
SMTP_PASSWORD=test
EOF

# Start mock services
python scripts/local_development/mock_services.py
```

## Running Agents Locally

### 1. Start Individual Agents
```bash
# Terminal 1: Start Orchestrator Agent
python src/orchestrator_agent/main.py --dev

# Terminal 2: Start Detection Agent
python src/detection_agent/main.py --dev

# Terminal 3: Start Analysis Agent
python src/analysis_agent/main.py --dev

# Terminal 4: Start Remediation Agent
python src/remediation_agent/main.py --dev

# Terminal 5: Start Communication Agent
python src/communication_agent/main.py --dev
```

### 2. Start All Agents Together
```bash
# Currently, agents must be started individually in separate terminals
# A unified startup script is planned for future development

# Alternative: Use a process manager like tmux or screen
tmux new-session -d -s sentinelops
tmux send-keys -t sentinelops:0 'python src/orchestrator_agent/main.py --dev' C-m
tmux new-window -t sentinelops:1
tmux send-keys -t sentinelops:1 'python src/detection_agent/main.py --dev' C-m
# ... repeat for other agents
```

### 3. Verify Agent Health
```bash
# Check all agents are running
curl http://localhost:8005/health  # Orchestrator
curl http://localhost:8001/health  # Detection
curl http://localhost:8002/health  # Analysis
curl http://localhost:8003/health  # Remediation
curl http://localhost:8004/health  # Communication

# Check agent states in Firestore
python -c "from src.common.firestore_client import FirestoreClient; \
fc = FirestoreClient(); \
states = fc.query_collection('agent_state'); \
for s in states: print(f'{s.id}: {s.to_dict().get(\"status\")}')"
```

## Development Workflow

### 1. Hot Reload Setup
```python
# Hot reload can be implemented using watchdog
# Example: monitor file changes and restart agents
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AgentReloader(FileSystemEventHandler):
    def __init__(self, agent_path):
        self.agent_path = agent_path
        self.process = None

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"Reloading {self.agent_name}...")
            restart_agent(self.agent_name)

def enable_hot_reload():
    """Enable hot reload for all agents."""
    observer = Observer()
    for agent in ['detection', 'analysis', 'remediation', 'communication', 'orchestrator']:
        handler = AgentReloader(agent)
        observer.schedule(handler, f'src/{agent}_agent/', recursive=True)
    observer.start()
```

### 2. Local Testing Workflow
```bash
# 1. Make changes to agent code
vim src/detection_agent/adk_agent.py

# 2. Agent automatically reloads (if hot reload enabled)
# Or manually restart
./scripts/local_development/restart_agent.sh detection

# 3. Run tests
pytest tests/detection_agent/test_adk_agent.py -v

# 4. Test with sample incident
python scripts/local_development/create_test_incident.py \
  --type=brute_force \
  --severity=HIGH

# 5. Monitor agent logs
tail -f logs/detection_agent.log
```

### 3. ADK Tool Development
```python
# Example: Creating a new ADK tool locally
# src/tools/custom_tool.py

from google.adk import BaseTool, ToolContext
from typing import Dict, Any
import os

class CustomSecurityTool(BaseTool):
    """Custom tool for local development."""

    def __init__(self):
        super().__init__(
            name="custom_security_scan",
            description="Performs custom security analysis"
        )

    async def run_async(self, *, args: Dict[str, Any], tool_context: ToolContext) -> Dict[str, Any]:
        """Execute the tool."""
        # Get parameters from args
        resource_id = args.get("resource_id")
        scan_type = args.get("scan_type", "basic")

        # Development implementation
        if os.getenv("MOCK_EXTERNAL_SERVICES") == "true":
            return self._mock_execution(resource_id, scan_type)

        # Real implementation
        return await self._real_execution(resource_id, scan_type)

    def _mock_execution(self, resource_id: str, scan_type: str) -> Dict[str, Any]:
        """Mock execution for local development."""
        return {
            "success": True,
            "resource_id": resource_id,
            "scan_type": scan_type,
            "findings": ["test_finding_1", "test_finding_2"],
            "severity": "MEDIUM"
        }
```

### 4. Testing Agent Transfers Locally
```python
# scripts/local_development/test_transfers.py
async def test_agent_transfer():
    """Test ADK transfer between agents locally."""
    # Create test context
    context = {
        "incident_id": "test-001",
        "severity": "HIGH",
        "description": "Test incident for transfer"
    }

    # Start transfer from detection to analysis
    detection_url = "http://localhost:8001"
    response = requests.post(
        f"{detection_url}/transfer",
        json={
            "target": "analysis_agent",
            "context": context
        }
    )

    print(f"Transfer response: {response.json()}")

    # Verify analysis agent received transfer
    analysis_url = "http://localhost:8002"
    status = requests.get(f"{analysis_url}/incident/{context['incident_id']}")
    print(f"Analysis status: {status.json()}")
```

## Debugging and Troubleshooting

### 1. Enable Debug Logging
```python
# config/logging_dev.py
import logging
import sys

def setup_debug_logging():
    """Configure detailed logging for development."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/debug.log')
        ]
    )

    # Enable ADK debug logging
    logging.getLogger('google.adk').setLevel(logging.DEBUG)

    # Enable agent debug logging
    logging.getLogger('sentinelops').setLevel(logging.DEBUG)
```

### 2. Development Debugging Tools
```bash
# View agent logs with filtering
tail -f logs/*.log | grep -E "(ERROR|WARNING|Transfer)"

# Check agent state in Firestore
python -c "
from src.common.firestore_client import FirestoreClient
fc = FirestoreClient()
for doc in fc.query_collection('agent_state'):
    print(f'{doc.id}: {doc.to_dict()}')"

# Monitor Pub/Sub messages
gcloud pubsub subscriptions pull detection-subscription \
  --auto-ack --limit=10

# Profile agent performance
python -m cProfile -o profile.stats src/analysis_agent/main.py
python -m pstats profile.stats
```

### 3. Common Issues and Solutions

#### Agent Not Starting
```bash
# Check port availability
lsof -i :8001  # Check if port is in use

# Check dependencies
pip list | grep google-adk

# Check environment variables
env | grep -E "(GOOGLE|ADK|SENTINELOPS)"
```

#### Transfer Failures
```python
# Enable transfer debugging
export ADK_TRANSFER_DEBUG=true

# Check agent discovery
curl http://localhost:8005/agents

# Verify firestore emulator
curl http://localhost:8080
```

#### Performance Issues
```bash
# Profile agent performance
python -m cProfile -o profile.stats src/analysis_agent/main.py

# Analyze profile
python -m pstats profile.stats
```

### 4. Local Monitoring Dashboard
```bash
# Start local monitoring dashboard
python scripts/local_development/monitoring_dashboard.py

# Access at http://localhost:9090
# Features:
# - Agent health status
# - Request/response times
# - Error rates
# - Resource usage
```

## Best Practices

### 1. Development Environment Isolation
```bash
# Use separate GCP project for development
export GOOGLE_CLOUD_PROJECT=sentinelops-dev

# Use separate credentials
export GOOGLE_APPLICATION_CREDENTIALS=./service-account-dev.json

# Use development configuration
export SENTINELOPS_CONFIG=config/development.yaml
```

### 2. Testing Practices
```python
# Always test with dry-run mode first
os.environ["DRY_RUN_DEFAULT"] = "true"

# Use mock services for external dependencies
os.environ["MOCK_EXTERNAL_SERVICES"] = "true"

# Test with various severity levels
test_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
for severity in test_severities:
    create_test_incident(severity=severity)
```

### 3. Code Organization
```
src/
├── agent_name/
│   ├── __init__.py
│   ├── adk_agent.py      # ADK agent implementation
│   ├── tools.py          # Agent-specific tools
│   ├── config.py         # Configuration
│   └── main.py           # Entry point
├── tools/
│   ├── __init__.py
│   └── custom_tools.py   # Shared tools
└── common/
    ├── __init__.py
    └── adk_agent_base.py # Base agent class
```

### 4. Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-adk-tool

# Make changes and test locally
# ... development work ...

# Run pre-commit hooks
pre-commit run --all-files

# Commit with descriptive message
git commit -m "feat(tools): add custom security scan tool

- Implements CustomSecurityTool extending BaseTool
- Adds mock execution for local development
- Includes comprehensive unit tests"

# Push and create PR
git push origin feature/new-adk-tool
```

### 5. Performance Optimization Tips
- Use caching for expensive operations
- Batch similar operations
- Profile before optimizing
- Monitor memory usage
- Use async operations where possible

## Useful Scripts

### Start Development Environment
```bash
#!/bin/bash
# scripts/local_development/start_dev.sh

echo "Starting SentinelOps Development Environment..."

# Start emulators
docker-compose -f docker-compose.dev.yml up -d

# Wait for services
sleep 10

# Initialize data
python scripts/local_development/init_all.py

# Start agents
python scripts/local_development/run_dev_environment.py

echo "Development environment ready!"
echo "Dashboard: http://localhost:9090"
echo "API: http://localhost:8005"
```

### Reset Development Environment
```bash
#!/bin/bash
# scripts/local_development/reset_dev.sh

echo "Resetting development environment..."

# Stop all services
docker-compose -f docker-compose.dev.yml down -v

# Clear local data
rm -rf .local_data/

# Restart
./scripts/local_development/start_dev.sh
```

---

*This guide ensures a smooth local development experience with ADK, enabling rapid iteration and testing of SentinelOps agents and tools.*

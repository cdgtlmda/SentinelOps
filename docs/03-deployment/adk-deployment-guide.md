# ADK Deployment Guide for SentinelOps

## Overview

This guide covers deploying the SentinelOps multi-agent security system using Google Agent Development Kit (ADK) on Google Cloud Platform. SentinelOps implements a sophisticated dual-architecture approach combining containerized deployment with ADK-native implementations.

## Prerequisites

1. **Google Cloud Project** with the following APIs enabled:
   ```bash
   # Enable required APIs
   ./scripts/setup/enable-apis.sh
   ```
   - Cloud Run API
   - Cloud Build API
   - Firestore API
   - Pub/Sub API
   - Secret Manager API
   - BigQuery API
   - Cloud Logging API
   - Cloud Monitoring API
   - Vertex AI API

2. **Local Development Environment**:
   - Python 3.12+
   - Google Cloud SDK (`gcloud`)
   - Docker
   - Git

3. **ADK Installation**:
   ```bash
   pip install google-adk>=1.2.0
   ```

## Architecture Overview

### Dual-Architecture Implementation

SentinelOps implements a hybrid architecture with two complementary approaches:

#### 1. Cloud Run Deployment (`agents/` directory)
- Individual containerized agents for production deployment
- Microservice architecture with independent scaling
- Entry points: `agents/{agent_name}/main.py`

#### 2. ADK Multi-Agent System (`src/` directory)
- Native ADK implementation using `SentinelOpsMultiAgent`
- Coordinated multi-agent execution
- Entry point: `src/main.py`

- Parallel execution of agents for real-time response
- Built-in ADK session management 
- Orchestrator-based workflow coordination
- Production-grade monitoring and telemetry

```
┌─────────────────────────────────────────────────────────────┐
│                  SentinelOpsMultiAgent                       │
│                   (ADK ParallelAgent)                        │
└───────────┬─────────────┬────────────┬─────────────┬────────┘
            │             │            │             │
     ┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐ ┌─────▼─────┐
     │  Detection  │ │Analysis│ │Remediation│ │Communication│
     │   Agent     │ │ Agent  │ │   Agent   │ │   Agent    │
     │(ADK LlmAgent)│ │(Vertex AI)│ │(ADK Tools)│ │(Multi-Chan)│
     └─────────────┘ └────────┘ └──────────┘ └────────────┘
              │
     ┌────────▼────────┐
     │  Orchestrator   │
     │     Agent       │
     │ (Workflow Mgmt) │
     └─────────────────┘
```

### ADK Integration Features

- **Custom ADK Wrappers**: `src/common/adk_*` modules provide enhanced functionality
- **Agent Routing**: Advanced inter-agent communication via `adk_routing.py`
- **Session Management**: Production-grade session handling via `adk_session_manager.py`
- **Base Agent Class**: `SentinelOpsBaseAgent` extends ADK's `LlmAgent`

## Deployment Options

### Option 1: Cloud Run Deployment (Recommended for Production)

Deploy individual agents as containerized microservices:

```bash
# Deploy all agents
./scripts/deployment/deploy_all_agents.sh
```

### Option 2: ADK Multi-Agent System (Recommended for Development)

Run the unified multi-agent system:

```bash
# Start multi-agent system
python src/main.py
```

### Option 3: Hybrid Deployment

Combine both approaches for maximum flexibility.

## Deployment Steps

### 1. Configure Environment Variables

Create a `.env` file with required configuration:

```bash
# Google Cloud Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# ADK Configuration
ADK_TELEMETRY_ENABLED=true
ADK_LOG_LEVEL=INFO

# Agent Configuration
DETECTION_SCAN_INTERVAL=5
ANALYSIS_MODEL=gemini-1.5-pro-002
REMEDIATION_DRY_RUN=false
COMMUNICATION_CHANNELS=slack,email,sms

# API Keys (store in Secret Manager)
# Note: Vertex AI uses Application Default Credentials, no API key needed
SLACK_TOKEN=your-slack-token
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
```

### 2. Set Up Google Cloud Resources

```bash
# Set project
gcloud config set project $GCP_PROJECT_ID

# Enable APIs
./scripts/setup/enable-apis.sh

# Set up IAM permissions
./scripts/auth/setup_iam.sh

# Create Firestore database
gcloud firestore databases create --region=$GCP_REGION

# Create BigQuery dataset
bq mk --dataset --location=$GCP_REGION sentinelops_logs

# Set up Pub/Sub
./scripts/setup/setup_pubsub.py

# Set up Secret Manager
./scripts/setup/setup_secret_manager.py

# Set up monitoring
./scripts/setup/setup_monitoring.py
```

### 3. Build and Deploy Agents

#### Cloud Run Deployment:

```bash
# Deploy all agents to Cloud Run
./scripts/deployment/deploy_all_agents.sh

# Or deploy individually
./scripts/deployment/deploy_analysis_only.sh
./scripts/deployment/deploy_detection_only.sh
./scripts/deployment/deploy_remediation_only.sh
./scripts/deployment/deploy_communication_only.sh
./scripts/deployment/deploy_orchestrator_only.sh
```

#### ADK Multi-Agent Deployment:

```bash
# Install dependencies
pip install -r requirements.txt

# Run multi-agent system
python src/main.py
```

### 4. Configure ADK-Specific Settings

Each agent requires ADK-specific configuration in Cloud Run:

```bash
# Set ADK environment variables for each service
gcloud run services update detection-agent \
  --set-env-vars="ADK_TELEMETRY_ENABLED=true,ADK_LOG_LEVEL=INFO" \
  --region=$GCP_REGION

gcloud run services update analysis-agent \
  --set-env-vars="ADK_MODEL=gemini-pro,ADK_TEMPERATURE=0.7" \
  --region=$GCP_REGION

# Add service account permissions for ADK
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:detection-agent@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

### 5. Verify Deployment

```bash
# Check service status
gcloud run services list --region=$GCP_REGION

# Test detection agent
curl -X POST https://detection-agent-xxxxx.run.app/scan \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"action": "manual_scan"}'

# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

## Production Configuration

### 1. Auto-scaling Configuration

```yaml
# cloud-run-config.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: orchestrator-agent
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "100"
        autoscaling.knative.dev/target: "80"
    spec:
      containerConcurrency: 100
      timeoutSeconds: 300
```

### 2. ADK Performance Tuning

```python
# config/adk_performance.py
ADK_CONFIG = {
    "telemetry": {
        "enabled": True,
        "export_interval": 60,  # seconds
        "batch_size": 100
    },
    "memory": {
        "cache_size": 1000,  # items
        "ttl": 3600  # seconds
    },
    "execution": {
        "max_retries": 3,
        "timeout": 300,  # seconds
        "concurrent_tools": 5
    }
}
```

### 3. Security Hardening

```bash
# Enable VPC Service Controls
gcloud access-context-manager perimeters create sentinelops-perimeter \
  --resources=projects/$GCP_PROJECT_ID \
  --restricted-services=bigquery.googleapis.com,storage.googleapis.com

# Configure Cloud Armor
gcloud compute security-policies create sentinelops-policy \
  --description="Security policy for SentinelOps agents"

gcloud compute security-policies rules create 1000 \
  --security-policy=sentinelops-policy \
  --expression="origin.region_code == 'US'" \
  --action=allow
```

## Monitoring and Observability

### 1. ADK Telemetry Dashboard

Create a monitoring dashboard for ADK metrics:

```bash
# Deploy dashboard configuration
gcloud monitoring dashboards create --config-from-file=monitoring/adk-dashboard.json
```

Key metrics to monitor:
- Agent execution latency
- Tool execution success rate
- Memory usage per agent
- API quota consumption
- Error rates by agent

### 2. Alerting Policies

```yaml
# alerting/adk-alerts.yaml
- name: High Agent Error Rate
  condition: |
    metric.type="custom.googleapis.com/adk/agent/errors"
    AND resource.type="cloud_run_revision"
    AND metric.value > 10
  duration: 60s
  
- name: Workflow Timeout
  condition: |
    metric.type="custom.googleapis.com/adk/workflow/duration"
    AND metric.value > 1800
  duration: 0s
```

## Disaster Recovery

### 1. Backup Strategy

```bash
# Backup Firestore
gcloud firestore export gs://$GCP_PROJECT_ID-backups/firestore/$(date +%Y%m%d)

# Backup BigQuery
bq extract --destination_format=AVRO \
  sentinelops_logs.security_events \
  gs://$GCP_PROJECT_ID-backups/bigquery/events-$(date +%Y%m%d)/*.avro
```

### 2. Rollback Procedure

```bash
# Tag current deployment
gcloud container images add-tag \
  gcr.io/$GCP_PROJECT_ID/detection-agent:latest \
  gcr.io/$GCP_PROJECT_ID/detection-agent:stable

# Rollback to previous version
gcloud run services update detection-agent \
  --image=gcr.io/$GCP_PROJECT_ID/detection-agent:stable \
  --region=$GCP_REGION
```

## Cost Optimization

### 1. ADK Resource Optimization

```python
# Optimize Gemini API calls
GEMINI_CACHE_CONFIG = {
    "enabled": True,
    "ttl": 3600,
    "max_size": 1000
}

# Batch operations
BATCH_CONFIG = {
    "detection_batch_size": 100,
    "analysis_batch_delay": 5  # seconds
}
```

### 2. Cloud Run Optimization

```bash
# Use minimum instances during off-peak
gcloud run services update detection-agent \
  --min-instances=0 \
  --max-instances=50 \
  --region=$GCP_REGION
```

## Troubleshooting Common Issues

### 1. ADK Import Errors

```bash
# Verify ADK installation
python -c "from google.adk.agents import LlmAgent; print('ADK OK')"

# Check ADK version
pip show google-adk
```

### 2. Agent Communication Issues

```bash
# Check Pub/Sub subscriptions
gcloud pubsub subscriptions list

# Verify service-to-service authentication
gcloud run services describe detection-agent \
  --region=$GCP_REGION \
  --format="value(spec.template.spec.serviceAccountName)"
```

### 3. Performance Issues

```sql
-- Check BigQuery query performance
SELECT
  query,
  total_bytes_processed,
  total_slot_ms,
  creation_time
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY total_slot_ms DESC
LIMIT 10;
```

## Maintenance Tasks

### Weekly
- Review agent error logs
- Check ADK telemetry dashboards
- Verify backup completion
- Update threat intelligence data

### Monthly
- Rotate API keys and secrets
- Review and optimize BigQuery queries
- Update ADK and dependencies
- Performance testing

### Quarterly
- Security audit
- Disaster recovery drill
- Cost optimization review
- Architecture review

## Support Resources

- **ADK Documentation**: https://cloud.google.com/agent-development-kit/docs
- **SentinelOps GitHub**: https://github.com/cdgtlmda/SentinelOps
- **Support Email**: cdgtlmda@pm.me
- **Slack Channel**: #sentinelops-support

## Appendix: Useful Commands

```bash
# View real-time logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=detection-agent"

# Get agent URLs
for agent in detection analysis remediation communication orchestrator; do
  echo "$agent: $(gcloud run services describe $agent-agent --region=$GCP_REGION --format='value(status.url)')"
done

# Test end-to-end workflow
curl -X POST https://orchestrator-agent-xxxxx.run.app/workflow/new \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d @test/sample-incident.json
```

# Comprehensive GCP Deployment Guide for SentinelOps

This guide provides complete instructions for deploying SentinelOps with ADK on Google Cloud Platform, including Cloud Run deployment for all agents.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [ADK Deployment](#adk-deployment)
4. [Infrastructure Deployment](#infrastructure-deployment)
5. [Agent Deployment](#agent-deployment)
6. [Configuration](#configuration)
7. [Verification](#verification)
8. [Production Checklist](#production-checklist)

## Prerequisites

### Required Tools
```bash
# Verify tool versions
gcloud version                # 400.0.0+
python --version             # 3.9-3.11 (ADK requirement)
docker --version             # 20.10+
terraform --version          # 1.5.0+

# Install missing tools
curl https://sdk.cloud.google.com | bash  # Google Cloud SDK
pip install -e ./adk                      # ADK framework
```

### Required GCP Permissions
- **Roles needed**:
  - `roles/owner` or combination of:
  - `roles/iam.serviceAccountAdmin`
  - `roles/run.admin`
  - `roles/bigquery.admin`
  - `roles/datastore.owner`
  - `roles/secretmanager.admin`
  - `roles/monitoring.admin`

### Required APIs
```bash
# Enable all required APIs
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  bigquery.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudtrace.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

## Project Setup

### 1. Initialize GCP Project
```bash
# Set project
export PROJECT_ID="your-sentinelops-project"
export REGION="us-central1"
gcloud config set project $PROJECT_ID

# Create project (if needed)
gcloud projects create $PROJECT_ID --name="SentinelOps Production"
gcloud beta billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID
```

### 2. Create Service Accounts
```bash
# Create service accounts for each agent
for agent in detection analysis remediation communication orchestrator; do
  gcloud iam service-accounts create sentinelops-${agent} \
    --display-name="SentinelOps ${agent^} Agent" \
    --description="Service account for ${agent} agent"
done

# Create admin service account
gcloud iam service-accounts create sentinelops-admin \
  --display-name="SentinelOps Admin" \
  --description="Administrative service account"
```

### 3. Configure IAM Permissions
```bash
# Detection Agent permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sentinelops-detection@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sentinelops-detection@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.viewer"

# Analysis Agent permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sentinelops-analysis@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Remediation Agent permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sentinelops-remediation@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/compute.securityAdmin"

# All agents need Firestore access
for agent in detection analysis remediation communication orchestrator; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-${agent}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
done
```

## ADK Deployment

### 1. Prepare ADK Package
```bash
# Clone repository
git clone https://github.com/cdgtlmda/SentinelOps.git
cd SentinelOps

# Install ADK
pip install -e ./adk

# Verify ADK installation
python -c "from google.adk.agents import LlmAgent; print('ADK ready')"
```

### 2. Build Container Images
```bash
# Create Artifact Registry repository
gcloud artifacts repositories create sentinelops \
  --repository-format=docker \
  --location=$REGION \
  --description="SentinelOps container images"

# Configure Docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push images
for agent in detection analysis remediation communication orchestrator; do
  docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/${agent}-agent:latest \
    -f agents/${agent}_agent/Dockerfile .

  docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/${agent}-agent:latest
done
```

## Infrastructure Deployment

### 1. Create Firestore Database
```bash
# Create Firestore database
gcloud firestore databases create \
  --location=$REGION \
  --type=firestore-native

# Create indexes
python scripts/setup/create_firestore_indexes.py
```

### 2. Set Up BigQuery
```bash
# Create datasets
bq mk --dataset --location=$REGION ${PROJECT_ID}:sentinelops_logs
bq mk --dataset --location=$REGION ${PROJECT_ID}:sentinelops_incidents
bq mk --dataset --location=$REGION ${PROJECT_ID}:sentinelops_metrics

# Create log sink to BigQuery
gcloud logging sinks create sentinelops-sink \
  bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/sentinelops_logs \
  --log-filter='resource.type="cloud_run_revision"'
```

### 3. Configure Secret Manager
```bash
# Create secrets
echo -n "your-slack-webhook-url" | gcloud secrets create slack-webhook-url --data-file=-
echo -n "your-smtp-password" | gcloud secrets create smtp-password --data-file=-

# Grant access to agents
gcloud secrets add-iam-policy-binding slack-webhook-url \
  --member="serviceAccount:sentinelops-communication@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 4. Set Up Monitoring
```bash
# Create notification channels
gcloud alpha monitoring channels create \
  --display-name="SentinelOps Alerts" \
  --type=email \
  --channel-labels=email_address=cdgtlmda@pm.me

# Create uptime checks
gcloud monitoring uptime-checks create \
  sentinelops-health \
  --display-name="SentinelOps Health Check" \
  --resource-type="uptime-url" \
  --http-check-path="/health" \
  --monitored-resource="{'type':'uptime_url','labels':{'host':'orchestrator-agent-${PROJECT_ID}.run.app'}}"
```

## Agent Deployment

### 1. Deploy Orchestrator Agent
```bash
gcloud run deploy orchestrator-agent \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/orchestrator-agent:latest \
  --platform=managed \
  --region=$REGION \
  --service-account=sentinelops-orchestrator@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION}" \
  --set-env-vars="ADK_TELEMETRY_ENABLED=true" \
  --set-env-vars="GEMINI_MODEL=gemini-1.5-flash" \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=10 \
  --concurrency=100 \
  --timeout=3600
```

### 2. Deploy Detection Agent
```bash
gcloud run deploy detection-agent \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/detection-agent:latest \
  --platform=managed \
  --region=$REGION \
  --service-account=sentinelops-detection@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION}" \
  --set-env-vars="BIGQUERY_DATASET=sentinelops_logs" \
  --set-env-vars="DETECTION_POLL_INTERVAL=60" \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=20 \
  --concurrency=10
```

### 3. Deploy Analysis Agent
```bash
gcloud run deploy analysis-agent \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/analysis-agent:latest \
  --platform=managed \
  --region=$REGION \
  --service-account=sentinelops-analysis@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION}" \
  --set-env-vars="GEMINI_MODEL=gemini-1.5-pro" \
  --set-env-vars="ENABLE_CACHING=true" \
  --set-env-vars="CACHE_TTL=3600" \
  --memory=4Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=10 \
  --concurrency=50
```

### 4. Deploy Remediation Agent
```bash
gcloud run deploy remediation-agent \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/remediation-agent:latest \
  --platform=managed \
  --region=$REGION \
  --service-account=sentinelops-remediation@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION}" \
  --set-env-vars="DRY_RUN_DEFAULT=true" \
  --set-env-vars="APPROVAL_REQUIRED=true" \
  --memory=2Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --concurrency=10
```

### 5. Deploy Communication Agent
```bash
gcloud run deploy communication-agent \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/communication-agent:latest \
  --platform=managed \
  --region=$REGION \
  --service-account=sentinelops-communication@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION}" \
  --set-secrets="SLACK_WEBHOOK_URL=slack-webhook-url:latest" \
  --set-secrets="SMTP_PASSWORD=smtp-password:latest" \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=10 \
  --concurrency=100
```

## Configuration

### 1. Agent Discovery Configuration
```yaml
# config/agents.yaml
agents:
  orchestrator:
    url: https://orchestrator-agent-${PROJECT_ID}.run.app
    health_check: /health

  detection:
    url: https://detection-agent-${PROJECT_ID}.run.app
    poll_interval: 60

  analysis:
    url: https://analysis-agent-${PROJECT_ID}.run.app
    cache_enabled: true

  remediation:
    url: https://remediation-agent-${PROJECT_ID}.run.app
    dry_run: true

  communication:
    url: https://communication-agent-${PROJECT_ID}.run.app
    channels:
      - slack
      - email
```

### 2. Detection Rules
```bash
# Initialize detection rules
python scripts/setup/initialize_rules.py --project-id=$PROJECT_ID

# Verify rules
python scripts/manage_rules.py list
```

### 3. Notification Templates
```bash
# Deploy notification templates
gsutil cp -r templates/notifications gs://${PROJECT_ID}-sentinelops/templates/
```

## Verification

### 1. Health Checks
```bash
# Check all agents
for agent in orchestrator detection analysis remediation communication; do
  echo "Checking ${agent} agent..."
  curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
    https://${agent}-agent-${PROJECT_ID}.run.app/health
done
```

### 2. End-to-End Test
```bash
# Run integration test
python scripts/integration_test.py \
  --project-id=$PROJECT_ID \
  --test-type=full
```

### 3. ADK Telemetry
```bash
# View ADK metrics
gcloud monitoring dashboards create \
  --config-from-file=dashboards/adk-telemetry.json
```

## Production Checklist

### Pre-Deployment
- [ ] All service accounts created with appropriate permissions
- [ ] Firestore indexes created
- [ ] BigQuery datasets configured
- [ ] Secrets stored in Secret Manager
- [ ] Container images built and pushed
- [ ] Network security configured

### Deployment
- [ ] All agents deployed to Cloud Run
- [ ] Environment variables configured
- [ ] Service URLs documented
- [ ] Health checks passing
- [ ] Monitoring configured

### Post-Deployment
- [ ] Integration tests passing
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Runbooks prepared
- [ ] Team trained

### Security
- [ ] Service accounts follow least privilege
- [ ] Secrets not exposed in logs
- [ ] Network policies configured
- [ ] Audit logging enabled
- [ ] Vulnerability scanning enabled

## Troubleshooting

### Common Issues

**Agent Not Starting**
```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=detection-agent" --limit=50

# Check permissions
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:sentinelops-detection*"
```

**ADK Transfer Failures**
```bash
# Verify agent discovery
curl https://orchestrator-agent-${PROJECT_ID}.run.app/agents

# Check Firestore connectivity
gcloud firestore operations list
```

**Performance Issues**
```bash
# Scale up agents
gcloud run services update detection-agent --min-instances=3

# Check metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies"'
```

## Cost Optimization

### Recommended Settings
- Use Cloud Run minimum instances = 0 for non-critical agents
- Enable autoscaling based on CPU utilization
- Use Gemini Flash for high-volume operations
- Configure appropriate retention policies

### Monitoring Costs
```bash
# Set up budget alerts
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT_ID \
  --display-name="SentinelOps Monthly Budget" \
  --budget-amount=1000 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90
```

---

*This deployment guide ensures a production-ready SentinelOps installation with proper security, monitoring, and cost controls.*

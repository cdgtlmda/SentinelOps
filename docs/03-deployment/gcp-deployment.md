# SentinelOps Deployment Guide

This guide provides step-by-step instructions for deploying SentinelOps on Google Cloud Platform.

## 🔑 **Credentials and Security Notice**

**This repository contains NO service account keys or credentials.** All references to:
- `your-project-id` / `your-gcp-project-id`
- `/path/to/service-account-key.json`
- `your-admin-password`

Are **placeholders** that you must replace with your actual values. Follow the service account creation steps below before proceeding.

## Prerequisites

### Required Tools
- `gcloud` CLI version 400.0.0 or higher
- `terraform` version 1.5.0 or higher
- `docker` version 20.10 or higher
- `kubectl` version 1.25 or higher
- `python` version 3.12 or higher

### Required Permissions
- Project Owner or Editor role
- Billing Account Administrator
- Organization Policy Administrator (if applicable)

### Required APIs
Enable the following APIs in your GCP project:
```bash
gcloud services enable \
  compute.googleapis.com \
  container.googleapis.com \
  containerregistry.googleapis.com \
  run.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  bigquery.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudscheduler.googleapis.com \
  aiplatform.googleapis.com \
  billingbudgets.googleapis.com
```

## Environment Setup

### 1. Set Environment Variables
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export GCP_ZONE="us-central1-a"
export GCP_BILLING_ACCOUNT_ID="your-billing-account-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 2. Configure gcloud
```bash
gcloud auth login
gcloud config set project ${GCP_PROJECT_ID}
gcloud config set compute/region ${GCP_REGION}
gcloud config set compute/zone ${GCP_ZONE}
```

### 3. Create Service Account for Deployment
```bash
# Create deployment service account
gcloud iam service-accounts create deployment-sa \
  --display-name="SentinelOps Deployment Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:deployment-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/editor"

# Create and download key
gcloud iam service-accounts keys create deployment-key.json \
  --iam-account=deployment-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com
```

## Infrastructure Deployment

### 1. Terraform Setup
```bash
cd terraform/

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id = "${GCP_PROJECT_ID}"
region = "${GCP_REGION}"
zone = "${GCP_ZONE}"
billing_account_id = "${GCP_BILLING_ACCOUNT_ID}"
EOF

# Review the plan
terraform plan

# Apply infrastructure
terraform apply -auto-approve
```

### 2. Verify Infrastructure
```bash
# Check VPC creation
gcloud compute networks list

# Check firewall rules
gcloud compute firewall-rules list

# Check BigQuery datasets
bq ls

# Check Pub/Sub topics
gcloud pubsub topics list
```

## Application Deployment

### 1. Build and Push Container Images
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push each agent
for agent in detection analysis remediation communication orchestration; do
  cd src/agents/${agent}_agent/

  # Build image
  docker build -t gcr.io/${GCP_PROJECT_ID}/${agent}-agent:latest .

  # Push to GCR
  docker push gcr.io/${GCP_PROJECT_ID}/${agent}-agent:latest

  cd ../../../
done
```

### 2. Deploy Cloud Run Services
```bash
# Deploy Detection Agent
gcloud run deploy detection-agent \
  --image gcr.io/${GCP_PROJECT_ID}/detection-agent:latest \
  --platform managed \
  --region ${GCP_REGION} \
  --service-account detection-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 100 \
  --concurrency 1000

# Deploy Analysis Agent
gcloud run deploy analysis-agent \
  --image gcr.io/${GCP_PROJECT_ID}/analysis-agent:latest \
  --platform managed \
  --region ${GCP_REGION} \
  --service-account analysis-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 50 \
  --concurrency 100

# Deploy Communication Agent
gcloud run deploy communication-agent \
  --image gcr.io/${GCP_PROJECT_ID}/communication-agent:latest \
  --platform managed \
  --region ${GCP_REGION} \
  --service-account communication-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 256Mi \
  --cpu 0.5 \
  --min-instances 1 \
  --max-instances 20 \
  --concurrency 500

# Deploy Orchestration Agent
gcloud run deploy orchestration-agent \
  --image gcr.io/${GCP_PROJECT_ID}/orchestration-agent:latest \
  --platform managed \
  --region ${GCP_REGION} \
  --service-account orchestration-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 2 \
  --max-instances 50 \
  --concurrency 200
```

### 3. Deploy Cloud Functions
```bash
# Deploy remediation functions
cd src/agents/remediation_agent/

# Deploy revoke-credentials function
gcloud functions deploy revoke-credentials \
  --gen2 \
  --runtime python311 \
  --region ${GCP_REGION} \
  --source . \
  --entry-point revoke_credentials \
  --trigger-topic remediation-topic \
  --service-account remediation-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 256MB \
  --timeout 540s

# Deploy block-ip-address function
gcloud functions deploy block-ip-address \
  --gen2 \
  --runtime python311 \
  --region ${GCP_REGION} \
  --source . \
  --entry-point block_ip_address \
  --trigger-topic remediation-topic \
  --service-account remediation-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 256MB \
  --timeout 300s

# Deploy isolate-vm function
gcloud functions deploy isolate-vm \
  --gen2 \
  --runtime python311 \
  --region ${GCP_REGION} \
  --source . \
  --entry-point isolate_vm \
  --trigger-topic remediation-topic \
  --service-account remediation-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID} \
  --memory 512MB \
  --timeout 540s

cd ../../../
```

## Configuration

### 1. Set Up Secrets
```bash
# Store Gemini API key
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Grant access to Analysis Agent
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:analysis-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Store Slack webhook (if using)
echo -n "your-slack-webhook-url" | gcloud secrets create slack-webhook-url \
  --data-file=- \
  --replication-policy="automatic"

# Store Twilio credentials (if using)
echo -n "your-twilio-auth-token" | gcloud secrets create twilio-auth-token \
  --data-file=- \
  --replication-policy="automatic"
```

### 2. Configure Firestore
```bash
# Create initial configuration documents
python scripts/setup_firestore_config.py
```

### 3. Set Up Log Export
```bash
# Create log sink for VPC Flow Logs
gcloud logging sinks create vpc-flow-logs-sink \
  bigquery.googleapis.com/projects/${GCP_PROJECT_ID}/datasets/sentinelops_logs \
  --log-filter='resource.type="gce_subnetwork" AND log_name="projects/'${GCP_PROJECT_ID}'/logs/compute.googleapis.com%2Fvpc_flows"'

# Create log sink for Audit Logs
gcloud logging sinks create audit-logs-sink \
  bigquery.googleapis.com/projects/${GCP_PROJECT_ID}/datasets/sentinelops_logs \
  --log-filter='protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog"'
```

### 4. Configure Monitoring
```bash
# Set up budget alerts
python scripts/cost_optimization/setup_budget_alerts.py

# Create monitoring dashboards
python scripts/setup_monitoring.py

# Configure alert policies
gcloud alpha monitoring policies create --policy-from-file=monitoring/alert-policies.yaml
```

## Verification

### 1. Health Checks
```bash
# Check Cloud Run services
for service in detection-agent analysis-agent communication-agent orchestration-agent; do
  echo "Checking ${service}..."
  gcloud run services describe ${service} --region ${GCP_REGION} --format="value(status.url)"
  curl -s -o /dev/null -w "%{http_code}" $(gcloud run services describe ${service} --region ${GCP_REGION} --format="value(status.url)")/health
  echo ""
done

# Check Cloud Functions
for function in revoke-credentials block-ip-address isolate-vm; do
  echo "Checking ${function}..."
  gcloud functions describe ${function} --region ${GCP_REGION} --format="value(state)"
done
```

### 2. Test Message Flow
```bash
# Publish test message to detection topic
gcloud pubsub topics publish detection-topic \
  --message='{"event_type":"test","severity":"info","message":"Deployment test"}'

# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 10 --format json
```

### 3. Verify Permissions
```bash
# Test service account permissions
python scripts/verify_permissions.py
```

## Post-Deployment

### 1. Enable Scheduled Jobs
```bash
# Create Cloud Scheduler jobs for cost optimization
python scripts/cost_optimization/setup_scheduled_jobs.py

# Create backup jobs
gcloud scheduler jobs create http daily-firestore-backup \
  --location=${GCP_REGION} \
  --schedule="0 2 * * *" \
  --uri="https://firestore.googleapis.com/v1/projects/${GCP_PROJECT_ID}/databases/(default):exportDocuments" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"outputUriPrefix":"gs://'${GCP_PROJECT_ID}'-backups/firestore"}'
```

### 2. Configure Auto-scaling
```bash
# Update Cloud Run auto-scaling settings
gcloud run services update detection-agent \
  --region ${GCP_REGION} \
  --update-annotations autoscaling.knative.dev/minScale=1,autoscaling.knative.dev/maxScale=100
```

### 3. Set Up Continuous Deployment
```bash
# Create Cloud Build trigger
gcloud builds triggers create github \
  --repo-name=SentinelOps \
  --repo-owner=your-github-org \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

## Troubleshooting

### Common Issues

1. **Service Account Permission Errors**
   ```bash
   # Re-run IAM setup
   ./scripts/setup_iam.sh
   ```

2. **Cloud Run Service Not Starting**
   ```bash
   # Check logs
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" --limit 50
   ```

3. **Pub/Sub Messages Not Delivered**
   ```bash
   # Check subscription details
   gcloud pubsub subscriptions describe SUBSCRIPTION_NAME
   ```

4. **BigQuery Table Not Found**
   ```bash
   # Verify dataset and tables
   bq ls sentinelops_logs
   ```

### Rollback Procedure

1. **Revert Cloud Run Service**
   ```bash
   gcloud run services update-traffic SERVICE_NAME --to-revisions=PREVIOUS_REVISION=100
   ```

2. **Restore Firestore Backup**
   ```bash
   gcloud firestore import gs://PROJECT-backups/firestore/TIMESTAMP
   ```

3. **Terraform Rollback**
   ```bash
   terraform plan -destroy
   terraform destroy -auto-approve
   ```

## Maintenance

### Daily Tasks
- Review monitoring dashboards
- Check error logs
- Verify budget compliance

### Weekly Tasks
- Review security findings
- Update dependencies
- Analyze cost reports

### Monthly Tasks
- Rotate service account keys
- Review IAM permissions
- Update documentation

## Support

For deployment issues:
1. Check deployment logs in Cloud Logging
2. Review error messages in Cloud Error Reporting
3. Contact platform team at platform@sentinelops.com

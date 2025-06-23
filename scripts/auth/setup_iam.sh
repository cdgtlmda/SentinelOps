#!/bin/bash
# IAM Setup Script for SentinelOps
# Generated on 2025-05-29T20:20:11.268757

PROJECT_ID="your-gcp-project-id"

echo "🔐 Setting up IAM permissions for SentinelOps agents..."

# Create service accounts

echo "Creating service account for detection agent..."
gcloud iam service-accounts create sentinelops-detection \
    --display-name="SentinelOps Detection Agent" \
    --project=$PROJECT_ID || echo "Service account already exists"

echo "Creating service account for analysis agent..."
gcloud iam service-accounts create sentinelops-analysis \
    --display-name="SentinelOps Analysis Agent" \
    --project=$PROJECT_ID || echo "Service account already exists"

echo "Creating service account for remediation agent..."
gcloud iam service-accounts create sentinelops-remediation \
    --display-name="SentinelOps Remediation Agent" \
    --project=$PROJECT_ID || echo "Service account already exists"

echo "Creating service account for communication agent..."
gcloud iam service-accounts create sentinelops-communication \
    --display-name="SentinelOps Communication Agent" \
    --project=$PROJECT_ID || echo "Service account already exists"

echo "Creating service account for orchestrator agent..."
gcloud iam service-accounts create sentinelops-orchestrator \
    --display-name="SentinelOps Orchestrator Agent" \
    --project=$PROJECT_ID || echo "Service account already exists"

# Grant IAM roles to service accounts

echo "Granting roles/bigquery.dataViewer to detection agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-detection@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer" \
    --quiet

echo "Granting roles/bigquery.jobUser to detection agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-detection@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser" \
    --quiet

echo "Granting roles/pubsub.publisher to detection agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-detection@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher" \
    --quiet

echo "Granting roles/logging.logWriter to detection agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-detection@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" \
    --quiet

echo "Granting roles/monitoring.metricWriter to detection agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-detection@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter" \
    --quiet

echo "Granting roles/bigquery.dataViewer to analysis agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-analysis@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer" \
    --quiet

echo "Granting roles/pubsub.subscriber to analysis agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-analysis@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber" \
    --quiet

echo "Granting roles/pubsub.publisher to analysis agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-analysis@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher" \
    --quiet

echo "Granting roles/aiplatform.user to analysis agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-analysis@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user" \
    --quiet

echo "Granting roles/logging.logWriter to analysis agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-analysis@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" \
    --quiet

echo "Granting roles/pubsub.subscriber to remediation agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-remediation@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber" \
    --quiet

echo "Granting roles/pubsub.publisher to remediation agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-remediation@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher" \
    --quiet

echo "Granting roles/cloudfunctions.invoker to remediation agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-remediation@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/cloudfunctions.invoker" \
    --quiet

echo "Granting roles/compute.admin to remediation agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-remediation@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/compute.admin" \
    --quiet

echo "Granting roles/logging.logWriter to remediation agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-remediation@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" \
    --quiet

echo "Granting roles/pubsub.subscriber to communication agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-communication@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber" \
    --quiet

echo "Granting roles/secretmanager.secretAccessor to communication agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-communication@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo "Granting roles/logging.logWriter to communication agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-communication@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" \
    --quiet

echo "Granting roles/pubsub.subscriber to orchestrator agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber" \
    --quiet

echo "Granting roles/pubsub.publisher to orchestrator agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher" \
    --quiet

echo "Granting roles/datastore.user to orchestrator agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/datastore.user" \
    --quiet

echo "Granting roles/monitoring.viewer to orchestrator agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/monitoring.viewer" \
    --quiet

echo "Granting roles/logging.logWriter to orchestrator agent..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter" \
    --quiet

# Configure Workload Identity for Cloud Run services

echo "Configuring Workload Identity for sentinelops-detection..."
gcloud iam service-accounts add-iam-policy-binding \
    sentinelops-detection@your-gcp-project-id.iam.gserviceaccount.com \
    --member="serviceAccount:$PROJECT_ID.svc.id.goog[default/sentinelops-detection]" \
    --role="roles/iam.workloadIdentityUser" \
    --project=$PROJECT_ID || echo "Workload Identity already configured"

echo "Configuring Workload Identity for sentinelops-analysis..."
gcloud iam service-accounts add-iam-policy-binding \
    sentinelops-analysis@your-gcp-project-id.iam.gserviceaccount.com \
    --member="serviceAccount:$PROJECT_ID.svc.id.goog[default/sentinelops-analysis]" \
    --role="roles/iam.workloadIdentityUser" \
    --project=$PROJECT_ID || echo "Workload Identity already configured"

echo "Configuring Workload Identity for sentinelops-remediation..."
gcloud iam service-accounts add-iam-policy-binding \
    sentinelops-remediation@your-gcp-project-id.iam.gserviceaccount.com \
    --member="serviceAccount:$PROJECT_ID.svc.id.goog[default/sentinelops-remediation]" \
    --role="roles/iam.workloadIdentityUser" \
    --project=$PROJECT_ID || echo "Workload Identity already configured"

echo "Configuring Workload Identity for sentinelops-communication..."
gcloud iam service-accounts add-iam-policy-binding \
    sentinelops-communication@your-gcp-project-id.iam.gserviceaccount.com \
    --member="serviceAccount:$PROJECT_ID.svc.id.goog[default/sentinelops-communication]" \
    --role="roles/iam.workloadIdentityUser" \
    --project=$PROJECT_ID || echo "Workload Identity already configured"

echo "Configuring Workload Identity for sentinelops-orchestrator..."
gcloud iam service-accounts add-iam-policy-binding \
    sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com \
    --member="serviceAccount:$PROJECT_ID.svc.id.goog[default/sentinelops-orchestrator]" \
    --role="roles/iam.workloadIdentityUser" \
    --project=$PROJECT_ID || echo "Workload Identity already configured"

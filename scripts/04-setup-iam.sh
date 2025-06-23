#!/bin/bash
# SentinelOps GCP Project Setup - Step 4: IAM Configuration
# Creates service accounts and assigns roles for ADK agents

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No project ID provided or set"
    echo "Usage: $0 [PROJECT_ID]"
    exit 1
fi

echo "🔐 SentinelOps IAM Configuration"
echo "================================"
echo "Project: ${PROJECT_ID}"
echo ""

# Create service accounts for each agent
AGENTS=(
    "detection-agent:Monitors logs and detects security incidents"
    "analysis-agent:Analyzes incidents using Gemini AI"
    "remediation-agent:Executes remediation actions"
    "communication-agent:Sends notifications and alerts"
    "orchestrator-agent:Coordinates agent workflows"
    "api-service:Handles REST API and WebSocket connections"
)

echo "📋 Creating service accounts..."
for agent_desc in "${AGENTS[@]}"; do
    IFS=':' read -r agent description <<< "$agent_desc"
    echo "Creating $agent..."
    gcloud iam service-accounts create $agent \
        --description="$description" \
        --display-name="SentinelOps $agent" \
        --project=${PROJECT_ID} || echo "Service account $agent already exists"
done

echo ""
echo "🔑 Assigning IAM roles..."

# Detection Agent roles
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:detection-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:detection-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/logging.viewer"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:detection-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:detection-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

# Analysis Agent roles (needs Vertex AI access)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:analysis-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:analysis-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:analysis-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

# Remediation Agent roles (needs resource management)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:remediation-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/compute.securityAdmin"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:remediation-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:remediation-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:remediation-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

# Communication Agent roles
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:communication-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:communication-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.viewer"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:communication-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"

# Orchestrator Agent roles
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:orchestrator-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:orchestrator-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/pubsub.editor"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:orchestrator-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"

# API Service roles
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:api-service@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:api-service@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

echo ""
echo "✅ IAM configuration complete!"
echo ""
echo "Service accounts created:"
gcloud iam service-accounts list --project=${PROJECT_ID} | grep sentinelops
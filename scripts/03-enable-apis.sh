#!/bin/bash
# SentinelOps GCP Project Setup - Step 3: Enable Required APIs
# Enables all APIs needed for ADK-based SentinelOps deployment

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No project ID provided or set"
    echo "Usage: $0 [PROJECT_ID]"
    exit 1
fi

echo "🔌 SentinelOps API Enablement"
echo "============================="
echo "Project: ${PROJECT_ID}"
echo ""

# Required APIs for ADK-based SentinelOps
APIS=(
    "run.googleapis.com"                    # Cloud Run
    "firestore.googleapis.com"              # Firestore
    "pubsub.googleapis.com"                 # Pub/Sub
    "logging.googleapis.com"                # Cloud Logging
    "monitoring.googleapis.com"             # Cloud Monitoring
    "bigquery.googleapis.com"               # BigQuery
    "secretmanager.googleapis.com"          # Secret Manager
    "cloudbuild.googleapis.com"             # Cloud Build
    "artifactregistry.googleapis.com"       # Artifact Registry
    "aiplatform.googleapis.com"             # Vertex AI (for Gemini)
    "compute.googleapis.com"                # Compute Engine (for Cloud Armor)
    "iap.googleapis.com"                    # Identity-Aware Proxy
)

echo "📋 Enabling ${#APIS[@]} required APIs..."
echo ""

for api in "${APIS[@]}"; do
    echo "Enabling $api..."
    gcloud services enable $api --project=${PROJECT_ID}
done

echo ""
echo "✅ All APIs enabled successfully!"
echo ""
echo "Verifying enabled APIs:"
gcloud services list --enabled --project=${PROJECT_ID} | grep -E "(run|firestore|pubsub|logging|monitoring|bigquery|secretmanager|cloudbuild|artifactregistry|aiplatform)"
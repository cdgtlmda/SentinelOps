#!/bin/bash
# Script to enable required Google Cloud APIs for SentinelOps

set -e

echo "Enabling Google Cloud APIs for SentinelOps..."
echo "============================================"

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-gcp-project-id}"
echo "Project ID: $PROJECT_ID"

# List of APIs to enable
APIS=(
    "compute.googleapis.com"              # Compute Engine API
    "logging.googleapis.com"              # Cloud Logging API
    "storage.googleapis.com"              # Cloud Storage API
    "aiplatform.googleapis.com"           # Vertex AI API
    "bigquery.googleapis.com"             # BigQuery API
    "cloudfunctions.googleapis.com"       # Cloud Functions API
    "run.googleapis.com"                  # Cloud Run API
    "pubsub.googleapis.com"               # Pub/Sub API
    "secretmanager.googleapis.com"        # Secret Manager API
    "cloudresourcemanager.googleapis.com" # Resource Manager API
    "iam.googleapis.com"                  # IAM API
    "containerregistry.googleapis.com"    # Container Registry API
)

# Enable each API
for api in "${APIS[@]}"; do
    echo "Enabling $api..."
    gcloud services enable "$api" --project="$PROJECT_ID" || {
        echo "Failed to enable $api"
        exit 1
    }
done

echo ""
echo "✅ All APIs have been enabled successfully!"
echo ""
echo "You can verify enabled APIs with:"
echo "  gcloud services list --enabled --project=$PROJECT_ID"

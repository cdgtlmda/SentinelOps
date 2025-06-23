#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [REGION]"
    exit 1
fi

echo "Setting up Artifact Registry for project: $PROJECT_ID in region: $REGION"

# Enable Artifact Registry API
echo "Enabling Artifact Registry API..."
gcloud services enable artifactregistry.googleapis.com --project="$PROJECT_ID"

# Create repository if it doesn't exist
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create sentinelops \
    --repository-format=docker \
    --location="$REGION" \
    --description="Container images for SentinelOps" \
    --project="$PROJECT_ID" || echo "Repository already exists"

# Configure Docker authentication
echo "Configuring Docker authentication..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# Set up vulnerability scanning
echo "Configuring vulnerability scanning..."
gcloud artifacts repositories update sentinelops \
    --location="$REGION" \
    --project="$PROJECT_ID" \
    --enable-vulnerability-scanning

# Create service account for pulling images
echo "Creating service account for image pulling..."
gcloud iam service-accounts create sentinelops-registry-reader \
    --display-name="SentinelOps Registry Reader" \
    --project="$PROJECT_ID" || echo "Service account already exists"

# Grant permissions to service account
echo "Granting permissions to service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:sentinelops-registry-reader@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.reader"

echo "Container registry setup complete!"
echo "Registry URL: ${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops"
#!/bin/bash
# SentinelOps GCP Project Setup - Step 1: Project Creation
# For ADK-based deployment using Cloud Run

set -e

# Project configuration
PROJECT_ID="sentinelops-prod-${RANDOM}"
PROJECT_NAME="SentinelOps Production"
ORGANIZATION_ID="" # Set if you have an organization

echo "🚀 SentinelOps GCP Project Setup"
echo "================================"
echo "Project ID: ${PROJECT_ID}"
echo "Project Name: ${PROJECT_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Create the project
echo "📋 Creating GCP project..."
if [ -n "$ORGANIZATION_ID" ]; then
    gcloud projects create ${PROJECT_ID} \
        --name="${PROJECT_NAME}" \
        --organization=${ORGANIZATION_ID}
else
    gcloud projects create ${PROJECT_ID} \
        --name="${PROJECT_NAME}"
fi

# Set as active project
echo "🔧 Setting as active project..."
gcloud config set project ${PROJECT_ID}

echo "✅ Project created successfully!"
echo ""
echo "Project ID: ${PROJECT_ID}"
echo "Save this ID - you'll need it for all subsequent steps."
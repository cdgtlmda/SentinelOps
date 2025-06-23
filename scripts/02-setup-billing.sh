#!/bin/bash
# SentinelOps GCP Project Setup - Step 2: Billing Setup
# Links billing account to the project

set -e

# Get project ID from current config or argument
PROJECT_ID=${1:-$(gcloud config get-value project)}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No project ID provided or set"
    echo "Usage: $0 [PROJECT_ID]"
    exit 1
fi

echo "💳 SentinelOps Billing Setup"
echo "==========================="
echo "Project: ${PROJECT_ID}"
echo ""

# List available billing accounts
echo "📋 Available billing accounts:"
gcloud billing accounts list

# Get billing account ID
echo ""
echo "Enter the Billing Account ID to link (format: XXXXXX-XXXXXX-XXXXXX):"
read BILLING_ACCOUNT_ID

if [ -z "$BILLING_ACCOUNT_ID" ]; then
    echo "❌ Error: Billing account ID required"
    exit 1
fi

# Link billing account to project
echo "🔗 Linking billing account to project..."
gcloud billing projects link ${PROJECT_ID} \
    --billing-account=${BILLING_ACCOUNT_ID}

# Verify billing is enabled
echo "✅ Verifying billing status..."
gcloud billing projects describe ${PROJECT_ID}

echo ""
echo "✅ Billing setup complete!"
echo "Project ${PROJECT_ID} is now linked to billing account ${BILLING_ACCOUNT_ID}"
#!/bin/bash
# Enable billing for the SentinelOps project

BILLING_ACCOUNT_ID="01CE60-2FC06F-FC6062"
PROJECT_ID="your-gcp-project-id"

echo "Linking billing account to project..."
gcloud beta billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT_ID"

echo "Verifying billing is enabled..."
gcloud beta billing projects describe "$PROJECT_ID" --format="table(billingAccountName,billingEnabled)"

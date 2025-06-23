#!/bin/bash
# SentinelOps GCP Project Setup - Step 6: Firewall Rules
# Creates firewall rules for Cloud Run and agent communication

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No project ID provided or set"
    echo "Usage: $0 [PROJECT_ID]"
    exit 1
fi

echo "🔥 SentinelOps Firewall Rules Setup"
echo "===================================="
echo "Project: ${PROJECT_ID}"
echo ""

VPC_NAME="sentinelops-vpc"

# Allow internal communication between Cloud Run services
echo "📋 Creating internal communication rule..."
gcloud compute firewall-rules create sentinelops-allow-internal \
    --project=${PROJECT_ID} \
    --network=${VPC_NAME} \
    --allow=tcp,udp,icmp \
    --source-ranges=10.0.0.0/24 \
    --priority=1000 \
    --description="Allow internal communication between services" || echo "Rule already exists"

# Allow Cloud Run to access Google APIs
echo "📋 Creating Google API access rule..."
gcloud compute firewall-rules create sentinelops-allow-google-apis \
    --project=${PROJECT_ID} \
    --network=${VPC_NAME} \
    --allow=tcp:443 \
    --destination-ranges=199.36.153.8/30,199.36.153.4/30 \
    --priority=1000 \
    --description="Allow access to Google APIs" || echo "Rule already exists"

# Allow health checks from Google Load Balancers
echo "📋 Creating health check rule..."
gcloud compute firewall-rules create sentinelops-allow-health-checks \
    --project=${PROJECT_ID} \
    --network=${VPC_NAME} \
    --allow=tcp \
    --source-ranges=35.191.0.0/16,130.211.0.0/22 \
    --priority=1000 \
    --description="Allow Google Cloud health checks" || echo "Rule already exists"

# Allow IAP for secure access
echo "📋 Creating IAP access rule..."
gcloud compute firewall-rules create sentinelops-allow-iap \
    --project=${PROJECT_ID} \
    --network=${VPC_NAME} \
    --allow=tcp:22,tcp:3389,tcp:443 \
    --source-ranges=35.235.240.0/20 \
    --priority=1000 \
    --description="Allow Identity-Aware Proxy access" || echo "Rule already exists"

echo ""
echo "✅ Firewall rules created successfully!"
echo ""
echo "Active firewall rules:"
gcloud compute firewall-rules list --project=${PROJECT_ID} --filter="network:${VPC_NAME}"
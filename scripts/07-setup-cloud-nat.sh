#!/bin/bash
# SentinelOps GCP Project Setup - Step 7: Cloud NAT Setup
# Enables outbound internet access for Cloud Run services

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No project ID provided or set"
    echo "Usage: $0 [PROJECT_ID] [REGION]"
    exit 1
fi

echo "🌐 SentinelOps Cloud NAT Setup"
echo "=============================="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

VPC_NAME="sentinelops-vpc"
ROUTER_NAME="sentinelops-router"
NAT_NAME="sentinelops-nat"

# Create Cloud NAT gateway
echo "📋 Creating Cloud NAT gateway..."
gcloud compute nat create ${NAT_NAME} \
    --project=${PROJECT_ID} \
    --router=${ROUTER_NAME} \
    --region=${REGION} \
    --nat-all-subnet-ip-ranges \
    --auto-allocate-nat-external-ips \
    --enable-logging || echo "Cloud NAT ${NAT_NAME} already exists"

echo ""
echo "✅ Cloud NAT setup complete!"
echo ""
echo "NAT configuration:"
echo "- NAT Gateway: ${NAT_NAME}"
echo "- Router: ${ROUTER_NAME}"
echo "- Region: ${REGION}"
echo "- IP allocation: Automatic"
echo ""
echo "Verifying NAT status:"
gcloud compute nat describe ${NAT_NAME} \
    --router=${ROUTER_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID}
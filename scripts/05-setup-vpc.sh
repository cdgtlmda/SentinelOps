#!/bin/bash
# SentinelOps GCP Project Setup - Step 5: VPC Setup
# Creates VPC for Cloud Run with private Google Access

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-"us-central1"}

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No project ID provided or set"
    echo "Usage: $0 [PROJECT_ID] [REGION]"
    exit 1
fi

echo "🌐 SentinelOps VPC Setup"
echo "========================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# VPC configuration
VPC_NAME="sentinelops-vpc"
SUBNET_NAME="sentinelops-subnet"
SUBNET_RANGE="10.0.0.0/24"

# Create VPC network
echo "📋 Creating VPC network..."
gcloud compute networks create ${VPC_NAME} \
    --project=${PROJECT_ID} \
    --subnet-mode=custom \
    --bgp-routing-mode=regional \
    --mtu=1460 || echo "VPC ${VPC_NAME} already exists"

# Create subnet
echo "📋 Creating subnet..."
gcloud compute networks subnets create ${SUBNET_NAME} \
    --project=${PROJECT_ID} \
    --network=${VPC_NAME} \
    --region=${REGION} \
    --range=${SUBNET_RANGE} \
    --enable-private-ip-google-access \
    --enable-flow-logs || echo "Subnet ${SUBNET_NAME} already exists"

# Create Cloud Router (needed for Cloud NAT)
echo "📋 Creating Cloud Router..."
gcloud compute routers create sentinelops-router \
    --project=${PROJECT_ID} \
    --network=${VPC_NAME} \
    --region=${REGION} || echo "Router already exists"

echo ""
echo "✅ VPC setup complete!"
echo ""
echo "Network configuration:"
echo "- VPC: ${VPC_NAME}"
echo "- Subnet: ${SUBNET_NAME} (${SUBNET_RANGE})"
echo "- Region: ${REGION}"
echo "- Private Google Access: Enabled"
#!/bin/bash
# Deploy agents using Cloud Build for AMD64 compatibility

set -e

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"

echo "🚀 Deploying SentinelOps agents using Cloud Build..."
echo "   This will build AMD64 images in the cloud"

# Submit build to Cloud Build
echo -e "\n📦 Submitting build to Cloud Build..."
gcloud builds submit \
    --config=cloudbuild-agents.yaml \
    --project=${PROJECT_ID} \
    .

echo -e "\n✅ Images built successfully!"

# Deploy to Cloud Run
echo -e "\n☁️  Deploying services to Cloud Run..."

# Detection Agent
echo "Deploying Detection Agent..."
gcloud run deploy sentinelops-detection \
    --image us-central1-docker.pkg.dev/${PROJECT_ID}/sentinelops/detection-agent:latest \
    --platform managed \
    --region ${REGION} \
    --no-allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1 \
    --service-account sentinelops-detection@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},AGENT_TYPE=detection,LOG_LEVEL=INFO" \
    --project=${PROJECT_ID} || echo "Failed to deploy Detection Agent"

# Analysis Agent
echo "Deploying Analysis Agent..."
gcloud run deploy sentinelops-analysis \
    --image us-central1-docker.pkg.dev/${PROJECT_ID}/sentinelops/analysis-agent:latest \
    --platform managed \
    --region ${REGION} \
    --no-allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600 \
    --max-instances 5 \
    --min-instances 1 \
    --service-account sentinelops-analysis@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},AGENT_TYPE=analysis,LOG_LEVEL=INFO" \
    --project=${PROJECT_ID} || echo "Failed to deploy Analysis Agent"

# Remediation Agent
echo "Deploying Remediation Agent..."
gcloud run deploy sentinelops-remediation \
    --image us-central1-docker.pkg.dev/${PROJECT_ID}/sentinelops/remediation-agent:latest \
    --platform managed \
    --region ${REGION} \
    --no-allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 5 \
    --min-instances 0 \
    --service-account sentinelops-remediation@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},AGENT_TYPE=remediation,LOG_LEVEL=INFO" \
    --project=${PROJECT_ID} || echo "Failed to deploy Remediation Agent"

# Communication Agent
echo "Deploying Communication Agent..."
gcloud run deploy sentinelops-communication \
    --image us-central1-docker.pkg.dev/${PROJECT_ID}/sentinelops/communication-agent:latest \
    --platform managed \
    --region ${REGION} \
    --no-allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 10 \
    --min-instances 1 \
    --service-account sentinelops-communication@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},AGENT_TYPE=communication,LOG_LEVEL=INFO" \
    --project=${PROJECT_ID} || echo "Failed to deploy Communication Agent"

# Orchestrator Agent
echo "Deploying Orchestrator Agent..."
gcloud run deploy sentinelops-orchestrator \
    --image us-central1-docker.pkg.dev/${PROJECT_ID}/sentinelops/orchestrator-agent:latest \
    --platform managed \
    --region ${REGION} \
    --no-allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600 \
    --max-instances 3 \
    --min-instances 1 \
    --service-account sentinelops-orchestrator@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},AGENT_TYPE=orchestrator,LOG_LEVEL=INFO" \
    --project=${PROJECT_ID} || echo "Failed to deploy Orchestrator Agent"

echo -e "\n✅ Deployment process complete!"
echo -e "\n📋 Listing deployed services:"
gcloud run services list --platform managed --region ${REGION} --project=${PROJECT_ID}
#!/bin/bash
# Build AMD64 images for Cloud Run deployment

set -e

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
REGISTRY_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops"

echo "🏗️ Building AMD64 images for Cloud Run..."

# Define agents
AGENTS=("detection" "analysis" "remediation" "communication" "orchestrator")

for AGENT in "${AGENTS[@]}"; do
    echo -e "\n📦 Building ${AGENT} agent for AMD64..."
    
    IMAGE_TAG="${REGISTRY_URL}/${AGENT}-agent:latest"
    
    # Build for AMD64 platform
    docker buildx build \
        --platform linux/amd64 \
        -t ${IMAGE_TAG} \
        -f agents/${AGENT}/Dockerfile \
        --push \
        .
    
    echo "✅ Built and pushed ${AGENT} agent"
done

echo -e "\n✅ All AMD64 images built and pushed!"

# Now deploy to Cloud Run
echo -e "\n☁️ Deploying services to Cloud Run..."

# Detection Agent
echo "Deploying Detection Agent..."
gcloud run deploy sentinelops-detection \
    --image ${REGISTRY_URL}/detection-agent:latest \
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
    --project=${PROJECT_ID}

# Analysis Agent
echo "Deploying Analysis Agent..."
gcloud run deploy sentinelops-analysis \
    --image ${REGISTRY_URL}/analysis-agent:latest \
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
    --project=${PROJECT_ID}

# Remediation Agent
echo "Deploying Remediation Agent..."
gcloud run deploy sentinelops-remediation \
    --image ${REGISTRY_URL}/remediation-agent:latest \
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
    --project=${PROJECT_ID}

# Communication Agent
echo "Deploying Communication Agent..."
gcloud run deploy sentinelops-communication \
    --image ${REGISTRY_URL}/communication-agent:latest \
    --platform managed \
    --region ${REGION} \
    --no-allow-unauthenticated \
    --memory 512Mi \
    --cpu 0.5 \
    --timeout 60 \
    --max-instances 10 \
    --min-instances 1 \
    --service-account sentinelops-communication@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},AGENT_TYPE=communication,LOG_LEVEL=INFO" \
    --project=${PROJECT_ID}

# Orchestrator Agent
echo "Deploying Orchestrator Agent..."
gcloud run deploy sentinelops-orchestrator \
    --image ${REGISTRY_URL}/orchestrator-agent:latest \
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
    --project=${PROJECT_ID}

echo -e "\n✅ Deployment complete!"
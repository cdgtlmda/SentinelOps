#!/bin/bash
# Deploy SentinelOps agents to Cloud Run

set -e

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
ARTIFACT_REGISTRY="sentinelops"

echo "🚀 Deploying SentinelOps to Cloud Run"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"

# Check if Artifact Registry exists, create if not
echo "📦 Setting up Artifact Registry..."
if ! gcloud artifacts repositories describe $ARTIFACT_REGISTRY \
    --location=$REGION \
    --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create $ARTIFACT_REGISTRY \
        --repository-format=docker \
        --location=$REGION \
        --description="SentinelOps container images" \
        --project=$PROJECT_ID
fi

# Configure Docker authentication
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push images locally (alternative to Cloud Build)
echo "🏗️  Building Docker images..."

# Base image
echo "Building base image..."
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/sentinelops-base:latest .

# Agent images
AGENTS=("detection" "analysis" "remediation" "communication" "orchestrator")

for agent in "${AGENTS[@]}"; do
    echo "Building $agent agent..."
    docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/${agent}-agent:latest \
        -f agents/${agent}/Dockerfile .
done

# Push images
echo "📤 Pushing images to Artifact Registry..."
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/sentinelops-base:latest

for agent in "${AGENTS[@]}"; do
    docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/${agent}-agent:latest
done

# Deploy services to Cloud Run
echo "☁️  Deploying services to Cloud Run..."

# Detection Agent
echo "Deploying Detection Agent..."
gcloud run deploy sentinelops-detection \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/detection-agent:latest \
    --region $REGION \
    --platform managed \
    --no-allow-unauthenticated \
    --service-account sentinelops-detection@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
    --cpu 1 \
    --memory 1Gi \
    --max-instances 10 \
    --min-instances 1 \
    --project $PROJECT_ID || echo "Failed to deploy Detection Agent"

# Analysis Agent
echo "Deploying Analysis Agent..."
gcloud run deploy sentinelops-analysis \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/analysis-agent:latest \
    --region $REGION \
    --platform managed \
    --no-allow-unauthenticated \
    --service-account sentinelops-analysis@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
    --cpu 2 \
    --memory 2Gi \
    --max-instances 5 \
    --min-instances 1 \
    --project $PROJECT_ID || echo "Failed to deploy Analysis Agent"

# Remediation Agent
echo "Deploying Remediation Agent..."
gcloud run deploy sentinelops-remediation \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/remediation-agent:latest \
    --region $REGION \
    --platform managed \
    --no-allow-unauthenticated \
    --service-account sentinelops-remediation@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},DRY_RUN_DEFAULT=true \
    --cpu 1 \
    --memory 1Gi \
    --max-instances 5 \
    --min-instances 0 \
    --project $PROJECT_ID || echo "Failed to deploy Remediation Agent"

# Communication Agent  
echo "Deploying Communication Agent..."
gcloud run deploy sentinelops-communication \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/communication-agent:latest \
    --region $REGION \
    --platform managed \
    --no-allow-unauthenticated \
    --service-account sentinelops-communication@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
    --cpu 0.5 \
    --memory 512Mi \
    --max-instances 10 \
    --min-instances 1 \
    --project $PROJECT_ID || echo "Failed to deploy Communication Agent"

# Orchestrator Agent
echo "Deploying Orchestrator Agent..."
gcloud run deploy sentinelops-orchestrator \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/orchestrator-agent:latest \
    --region $REGION \
    --platform managed \
    --no-allow-unauthenticated \
    --service-account sentinelops-orchestrator@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
    --cpu 2 \
    --memory 2Gi \
    --max-instances 3 \
    --min-instances 1 \
    --port 8080 \
    --project $PROJECT_ID || echo "Failed to deploy Orchestrator Agent"

# List deployed services
echo -e "\n✅ Deployment complete!"
echo "Deployed services:"
gcloud run services list --platform managed --region $REGION --project $PROJECT_ID

echo -e "\n📋 Next steps:"
echo "1. Configure Pub/Sub push subscriptions to trigger the Cloud Run services"
echo "2. Set up Cloud Scheduler for periodic tasks"
echo "3. Configure monitoring and alerting"
echo "4. Test the deployment with sample security events"
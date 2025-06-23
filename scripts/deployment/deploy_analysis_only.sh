#!/bin/bash
# Deploy only the analysis agent to Cloud Run

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="sentinelops-analysis"
IMAGE_NAME="analysis-agent"

echo "🚀 Deploying Analysis Agent to Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Build the Docker image using Cloud Build
echo "📦 Building Docker image with Cloud Build..."
cat > /tmp/cloudbuild-analysis.yaml << EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/$IMAGE_NAME:latest',
      '-f', 'agents/analysis/Dockerfile',
      '.'
    ]
images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/$IMAGE_NAME:latest'
timeout: 1200s
options:
  machineType: 'E2_HIGHCPU_8'
EOF

# Submit the build
gcloud builds submit \
  --config=/tmp/cloudbuild-analysis.yaml \
  --project=$PROJECT_ID

if [ $? -ne 0 ]; then
  echo "❌ Build failed"
  exit 1
fi

echo "✅ Docker image built successfully"

# Deploy to Cloud Run
echo ""
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/$IMAGE_NAME:latest \
  --platform=managed \
  --region=$REGION \
  --project=$PROJECT_ID \
  --service-account=sentinelops-analysis@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=540 \
  --max-instances=10 \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,AGENT_TYPE=analysis,LOG_LEVEL=INFO,ENVIRONMENT=production"

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Analysis agent deployed successfully!"
  
  # Get the service URL
  SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)')
  
  echo ""
  echo "📍 Service URL: $SERVICE_URL"
  echo ""
  echo "Test with:"
  echo "  curl $SERVICE_URL/health"
  echo "  curl $SERVICE_URL/status"
else
  echo "❌ Deployment failed"
  exit 1
fi

# Clean up temp file
rm -f /tmp/cloudbuild-analysis.yaml
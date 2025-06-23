#!/bin/bash
# Deploy all SentinelOps agents to Cloud Run

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"

echo "🚀 Deploying All SentinelOps Agents to Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# First, update all Dockerfiles to use the simple wrapper
echo "📝 Updating Dockerfiles to use simple wrapper..."
for agent in analysis remediation communication orchestrator; do
    sed -i.bak 's/src\.cloud_run_[a-zA-Z_]*wrapper/src.cloud_run_simple_wrapper/g' agents/$agent/Dockerfile
    echo "✅ Updated $agent Dockerfile"
done

# Create Cloud Build configuration for all agents
cat > /tmp/cloudbuild-all-agents.yaml << EOF
steps:
  # Build Analysis Agent
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build-analysis'
    args: [
      'build',
      '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/analysis-agent:latest',
      '-f', 'agents/analysis/Dockerfile',
      '.'
    ]
    waitFor: ['-']
  
  # Build Remediation Agent
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build-remediation'
    args: [
      'build',
      '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/remediation-agent:latest',
      '-f', 'agents/remediation/Dockerfile',
      '.'
    ]
    waitFor: ['-']
  
  # Build Communication Agent
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build-communication'
    args: [
      'build',
      '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/communication-agent:latest',
      '-f', 'agents/communication/Dockerfile',
      '.'
    ]
    waitFor: ['-']
  
  # Build Orchestrator Agent
  - name: 'gcr.io/cloud-builders/docker'
    id: 'build-orchestrator'
    args: [
      'build',
      '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/orchestrator-agent:latest',
      '-f', 'agents/orchestrator/Dockerfile',
      '.'
    ]
    waitFor: ['-']

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/analysis-agent:latest'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/remediation-agent:latest'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/communication-agent:latest'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/orchestrator-agent:latest'
timeout: 2400s
options:
  machineType: 'E2_HIGHCPU_8'
EOF

# Submit the build
echo ""
echo "📦 Building Docker images with Cloud Build..."
gcloud builds submit \
  --config=/tmp/cloudbuild-all-agents.yaml \
  --project=$PROJECT_ID

if [ $? -ne 0 ]; then
  echo "❌ Build failed"
  exit 1
fi

echo "✅ All Docker images built successfully"

# Deploy each agent to Cloud Run
echo ""
echo "🌐 Deploying agents to Cloud Run..."

declare -A agents=(
  ["analysis"]="sentinelops-analysis"
  ["remediation"]="sentinelops-remediation"
  ["communication"]="sentinelops-communication"
  ["orchestrator"]="sentinelops-orchestrator"
)

for agent_type in "${!agents[@]}"; do
  service_name="${agents[$agent_type]}"
  echo ""
  echo "Deploying $service_name..."
  
  gcloud run deploy $service_name \
    --image=us-central1-docker.pkg.dev/$PROJECT_ID/sentinelops/${agent_type}-agent:latest \
    --platform=managed \
    --region=$REGION \
    --project=$PROJECT_ID \
    --service-account=sentinelops-${agent_type}@$PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --timeout=540 \
    --max-instances=10 \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,AGENT_TYPE=${agent_type},LOG_LEVEL=INFO,ENVIRONMENT=production"
  
  if [ $? -eq 0 ]; then
    echo "✅ $service_name deployed successfully"
  else
    echo "❌ Failed to deploy $service_name"
  fi
done

# Clean up
rm -f /tmp/cloudbuild-all-agents.yaml

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Test the services with:"
for agent_type in "${!agents[@]}"; do
  service_name="${agents[$agent_type]}"
  SERVICE_URL=$(gcloud run services describe $service_name \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)' 2>/dev/null)
  
  if [ ! -z "$SERVICE_URL" ]; then
    echo "  curl $SERVICE_URL/health"
  fi
done
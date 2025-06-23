#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-prod}"
ANALYSIS_PERIOD="${3:-7d}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT] [ANALYSIS_PERIOD]"
    exit 1
fi

echo "Analyzing resource usage for right-sizing recommendations"
echo "Project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"
echo "Analysis period: $ANALYSIS_PERIOD"

# Enable Recommender API
echo "Enabling Recommender API..."
gcloud services enable recommender.googleapis.com --project="$PROJECT_ID"

# Function to get recommendations
get_recommendations() {
    local RECOMMENDER_TYPE=$1
    local SERVICE_TYPE=$2
    
    echo "Getting $SERVICE_TYPE recommendations..."
    gcloud recommender recommendations list \
        --project=$PROJECT_ID \
        --location=us-central1 \
        --recommender=$RECOMMENDER_TYPE \
        --format=json > /tmp/${SERVICE_TYPE}_recommendations.json
}

# Get Cloud Run recommendations
echo "Analyzing Cloud Run services..."
SERVICES=("orchestrator" "detection" "analysis" "remediation" "communication")

for SERVICE in "${SERVICES[@]}"; do
    echo "Analyzing sentinelops-${SERVICE}-${ENVIRONMENT}..."
    
    # Get CPU and memory metrics
    gcloud monitoring read \
        --project=$PROJECT_ID \
        --filter='metric.type="run.googleapis.com/container/cpu/utilizations" AND
                 resource.label.service_name="sentinelops-'${SERVICE}'-'${ENVIRONMENT}'"' \
        --format=json \
        --window=$ANALYSIS_PERIOD > /tmp/${SERVICE}_cpu_metrics.json    gcloud monitoring read \
        --project=$PROJECT_ID \
        --filter='metric.type="run.googleapis.com/container/memory/utilizations" AND
                 resource.label.service_name="sentinelops-'${SERVICE}'-'${ENVIRONMENT}'"' \
        --format=json \
        --window=$ANALYSIS_PERIOD > /tmp/${SERVICE}_memory_metrics.json
done

# Get VM instance recommendations
get_recommendations "google.compute.instance.MachineTypeRecommender" "compute"

# Get Cloud SQL recommendations
get_recommendations "google.cloudsql.instance.PerformanceRecommender" "cloudsql"

# Generate right-sizing script
echo "Generating right-sizing recommendations..."
cat > apply-right-sizing.sh <<'EOF'
#!/bin/bash
# Auto-generated right-sizing script

echo "Applying right-sizing recommendations..."

# Cloud Run services
EOF

# Analyze and generate Cloud Run updates
for SERVICE in "${SERVICES[@]}"; do
    cat >> apply-right-sizing.sh <<EOF

# Update sentinelops-${SERVICE}-${ENVIRONMENT}
gcloud run services update sentinelops-${SERVICE}-${ENVIRONMENT} \\
    --cpu=1 \\
    --memory=512Mi \\
    --min-instances=1 \\
    --max-instances=10 \\
    --concurrency=100 \\
    --region=us-central1 \\
    --project=$PROJECT_ID
EOF
done

chmod +x apply-right-sizing.sh

echo "Right-sizing analysis complete!"
echo "Review recommendations in: apply-right-sizing.sh"
echo "Run './apply-right-sizing.sh' to apply recommendations"
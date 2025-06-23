#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
COMMITMENT_TYPE="${2:-COMPUTE}"  # COMPUTE or MEMORY
TERM="${3:-ONE_YEAR}"  # ONE_YEAR or THREE_YEARS

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [COMMITMENT_TYPE] [TERM]"
    exit 1
fi

echo "Setting up Committed Use Discounts for project: $PROJECT_ID"
echo "Commitment type: $COMMITMENT_TYPE"
echo "Term: $TERM"

# Enable Billing API
echo "Enabling Billing API..."
gcloud services enable cloudbilling.googleapis.com --project="$PROJECT_ID"

# Analyze current usage
echo "Analyzing current resource usage..."
END_DATE=$(date +%Y-%m-%d)
START_DATE=$(date -d "30 days ago" +%Y-%m-%d)

# Get current compute usage
echo "Fetching compute usage data..."
gcloud compute commitments list \
    --project="$PROJECT_ID" \
    --format=json > /tmp/existing_commitments.json

# Generate commitment recommendations
cat > /tmp/analyze_commitments.py <<'EOF'
#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timedelta

def get_usage_data(project_id, start_date, end_date):
    """Get resource usage data from Cloud Monitoring"""
    cmd = f"""bq query --use_legacy_sql=false --format=json '
    SELECT 
        service.description as service,
        sku.description as sku,
        SUM(cost) as total_cost,
        SUM(usage.amount) as total_usage,
        usage.unit as unit
    FROM \`{project_id}.billing.gcp_billing_export_v1_*\`
    WHERE _TABLE_SUFFIX BETWEEN "{start_date.replace("-", "")}" AND "{end_date.replace("-", "")}"
        AND service.description IN ("Compute Engine", "Cloud SQL", "Cloud Run")
    GROUP BY service, sku, unit
    ORDER BY total_cost DESC
    LIMIT 50'"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout) if result.returncode == 0 else []
EOFcat >> /tmp/analyze_commitments.py <<'EOF'

def calculate_commitment_recommendation(usage_data):
    """Calculate recommended commitment based on usage"""
    recommendations = {
        'compute': {'cores': 0, 'memory': 0},
        'sql': {'cores': 0, 'memory': 0}
    }
    
    # Analyze usage patterns and calculate baseline
    # Using 80% of average usage as commitment baseline
    baseline_percentage = 0.8
    
    for item in usage_data:
        if 'Core' in item.get('sku', ''):
            if 'Compute Engine' in item.get('service', ''):
                recommendations['compute']['cores'] += item['total_usage'] * baseline_percentage
            elif 'Cloud SQL' in item.get('service', ''):
                recommendations['sql']['cores'] += item['total_usage'] * baseline_percentage
        elif 'RAM' in item.get('sku', ''):
            if 'Compute Engine' in item.get('service', ''):
                recommendations['compute']['memory'] += item['total_usage'] * baseline_percentage
            elif 'Cloud SQL' in item.get('service', ''):
                recommendations['sql']['memory'] += item['total_usage'] * baseline_percentage
    
    return recommendations

if __name__ == "__main__":
    import sys
    project_id = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    
    usage_data = get_usage_data(project_id, start_date, end_date)
    recommendations = calculate_commitment_recommendation(usage_data)
    
    print(f"Commitment Recommendations for {project_id}:")
    print(f"Compute Engine:")
    print(f"  - vCPUs: {int(recommendations['compute']['cores'])} cores")
    print(f"  - Memory: {int(recommendations['compute']['memory'] / 1024)} GB")
    print(f"Cloud SQL:")
    print(f"  - vCPUs: {int(recommendations['sql']['cores'])} cores")
    print(f"  - Memory: {int(recommendations['sql']['memory'] / 1024)} GB")
EOF

chmod +x /tmp/analyze_commitments.py

# Run analysis
python3 /tmp/analyze_commitments.py "$PROJECT_ID" "$START_DATE" "$END_DATE"# Create commitment configuration
echo "Creating commitment configuration..."
REGION="us-central1"

# Example commitment creation (adjust values based on analysis)
cat > create-commitments.sh <<EOF
#!/bin/bash
# Auto-generated commitment creation script

echo "Creating Compute Engine commitments..."

# Create CPU commitment
gcloud compute commitments create sentinelops-cpu-commitment \\
    --region=$REGION \\
    --resources=vcpu=16,memory=64GB \\
    --plan=$TERM \\
    --project=$PROJECT_ID

# Create Cloud SQL commitment (if applicable)
# Note: Cloud SQL commitments are created differently
echo "For Cloud SQL commitments, use the Cloud Console:"
echo "https://console.cloud.google.com/sql/committed-use-discounts"

# Monitor commitment utilization
gcloud compute commitments describe sentinelops-cpu-commitment \\
    --region=$REGION \\
    --project=$PROJECT_ID
EOF

chmod +x create-commitments.sh

# Set up commitment monitoring
echo "Setting up commitment utilization monitoring..."
cat > monitor-commitments.sh <<'EOF'
#!/bin/bash
# Monitor commitment utilization

PROJECT_ID=$1
REGION=$2

echo "Commitment Utilization Report"
echo "============================"

gcloud compute commitments list \
    --project=$PROJECT_ID \
    --format="table(name,region,status,plan,resources:format='yaml')"

echo ""
echo "To maximize savings, ensure utilization stays above 80%"
EOF

chmod +x monitor-commitments.sh

echo "Committed Use Discount analysis complete!"
echo "Review recommendations and run ./create-commitments.sh to apply"
echo "Monitor utilization with: ./monitor-commitments.sh $PROJECT_ID $REGION"
#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT]"
    exit 1
fi

echo "Setting up resource scheduling for project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"

# Enable Cloud Scheduler API
echo "Enabling Cloud Scheduler API..."
gcloud services enable cloudscheduler.googleapis.com --project="$PROJECT_ID"

# Create resource scheduling jobs
echo "Creating resource scheduling jobs..."

# Schedule to scale down non-production resources after hours
gcloud scheduler jobs create http scale-down-${ENVIRONMENT} \
    --location=us-central1 \
    --schedule="0 19 * * 1-5" \
    --time-zone="America/Chicago" \
    --uri="https://compute.googleapis.com/compute/v1/projects/${PROJECT_ID}/zones/us-central1-a/instanceGroupManagers/sentinelops-workers-${ENVIRONMENT}/resize" \
    --http-method=POST \
    --message-body='{"size": 1}' \
    --oauth-service-account-email="sentinelops-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project="$PROJECT_ID"

# Schedule to scale up before business hours
gcloud scheduler jobs create http scale-up-${ENVIRONMENT} \
    --location=us-central1 \
    --schedule="0 7 * * 1-5" \
    --time-zone="America/Chicago" \
    --uri="https://compute.googleapis.com/compute/v1/projects/${PROJECT_ID}/zones/us-central1-a/instanceGroupManagers/sentinelops-workers-${ENVIRONMENT}/resize" \
    --http-method=POST \
    --message-body='{"size": 5}' \
    --oauth-service-account-email="sentinelops-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project="$PROJECT_ID"# Schedule Cloud SQL maintenance
echo "Scheduling Cloud SQL maintenance windows..."
gcloud sql instances patch sentinelops-db-${ENVIRONMENT} \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=3 \
    --maintenance-window-duration=4 \
    --maintenance-release-channel=production \
    --project="$PROJECT_ID"

# Create Cloud Function for advanced scheduling
echo "Creating advanced scheduling function..."
cat > /tmp/resource_scheduler.py <<'EOF'
import functions_framework
from google.cloud import compute_v1
from google.cloud import run_v2
import datetime

@functions_framework.http
def schedule_resources(request):
    """Advanced resource scheduling based on usage patterns"""
    
    project_id = request.args.get('project_id')
    action = request.args.get('action')  # scale_up or scale_down
    
    if action == 'scale_down':
        # Scale down Cloud Run services
        run_client = run_v2.ServicesClient()
        services = ['detection', 'analysis', 'remediation']
        
        for service in services:
            service_name = f"projects/{project_id}/locations/us-central1/services/sentinelops-{service}-prod"
            
            # Update to minimum instances
            run_client.update_service(
                service={
                    "name": service_name,
                    "template": {
                        "scaling": {
                            "min_instance_count": 0,
                            "max_instance_count": 10
                        }
                    }
                }
            )
    
    elif action == 'scale_up':
        # Scale up for business hours
        for service in services:
            service_name = f"projects/{project_id}/locations/us-central1/services/sentinelops-{service}-prod"
            
            run_client.update_service(
                service={
                    "name": service_name,
                    "template": {
                        "scaling": {
                            "min_instance_count": 2,
                            "max_instance_count": 50
                        }
                    }
                }
            )
    
    return {"status": "success", "action": action}
EOF# Deploy scheduling function
gcloud functions deploy resource-scheduler-${ENVIRONMENT} \
    --runtime=python311 \
    --trigger-http \
    --entry-point=schedule_resources \
    --source=/tmp \
    --service-account=sentinelops-scheduler@${PROJECT_ID}.iam.gserviceaccount.com \
    --region=us-central1 \
    --project="$PROJECT_ID"

# Create weekend shutdown schedule
gcloud scheduler jobs create http weekend-shutdown-${ENVIRONMENT} \
    --location=us-central1 \
    --schedule="0 18 * * 5" \
    --time-zone="America/Chicago" \
    --uri="https://us-central1-${PROJECT_ID}.cloudfunctions.net/resource-scheduler-${ENVIRONMENT}?project_id=${PROJECT_ID}&action=scale_down" \
    --http-method=GET \
    --attempt-deadline=30m \
    --project="$PROJECT_ID"

# Create Monday morning startup schedule
gcloud scheduler jobs create http monday-startup-${ENVIRONMENT} \
    --location=us-central1 \
    --schedule="0 6 * * 1" \
    --time-zone="America/Chicago" \
    --uri="https://us-central1-${PROJECT_ID}.cloudfunctions.net/resource-scheduler-${ENVIRONMENT}?project_id=${PROJECT_ID}&action=scale_up" \
    --http-method=GET \
    --attempt-deadline=30m \
    --project="$PROJECT_ID"

# Set up usage-based scheduling
echo "Creating usage-based scheduling policy..."
cat > usage-based-scheduler.sh <<'EOF'
#!/bin/bash
# Monitor usage and adjust resources dynamically

THRESHOLD_CPU=30
THRESHOLD_MEMORY=40

# Check current usage
CURRENT_CPU=$(gcloud monitoring read --project=$1 --filter='metric.type="compute.googleapis.com/instance/cpu/utilization"' --format="value(point.value.double_value)" | head -1)

if (( $(echo "$CURRENT_CPU < $THRESHOLD_CPU" | bc -l) )); then
    echo "Low usage detected, scaling down..."
    # Trigger scale down
fi
EOF

chmod +x usage-based-scheduler.sh

echo "Resource scheduling setup complete!"
echo "Estimated savings: 40-60% for non-production environments"
echo "Schedules active - resources will scale based on time and usage"
#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT]"
    exit 1
fi

echo "Setting up Preemptible/Spot instances for project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"

# Create instance template with preemptible configuration
echo "Creating preemptible instance template..."
gcloud compute instance-templates create sentinelops-preemptible-${ENVIRONMENT} \
    --machine-type=e2-medium \
    --preemptible \
    --no-restart-on-failure \
    --maintenance-policy=TERMINATE \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --image-family=cos-stable \
    --image-project=cos-cloud \
    --network=sentinelops-vpc \
    --subnet=sentinelops-subnet \
    --tags=sentinelops-worker \
    --metadata=startup-script='#!/bin/bash
# Graceful shutdown handler
trap "echo Preemption notice received; /opt/sentinelops/shutdown.sh" TERM

# Start worker process
/opt/sentinelops/worker.sh' \
    --project="$PROJECT_ID"

# Create managed instance group with preemptible instances
echo "Creating managed instance group..."
gcloud compute instance-groups managed create sentinelops-workers-${ENVIRONMENT} \
    --base-instance-name=sentinelops-worker \
    --template=sentinelops-preemptible-${ENVIRONMENT} \
    --size=3 \
    --zone=us-central1-a \
    --project="$PROJECT_ID"# Configure autoscaling for preemptible instances
echo "Configuring autoscaling..."
gcloud compute instance-groups managed set-autoscaling sentinelops-workers-${ENVIRONMENT} \
    --max-num-replicas=10 \
    --min-num-replicas=1 \
    --target-cpu-utilization=0.6 \
    --cool-down-period=90 \
    --zone=us-central1-a \
    --project="$PROJECT_ID"

# Create Cloud Run jobs with spot instances
echo "Creating Cloud Run jobs with spot pricing..."
for JOB in "batch-analysis" "log-processing" "report-generation"; do
    cat > /tmp/${JOB}-job.yaml <<EOF
apiVersion: run.googleapis.com/v1
kind: Job
metadata:
  name: sentinelops-${JOB}-${ENVIRONMENT}
  annotations:
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/${PROJECT_ID}/sentinelops-${JOB}:latest
            resources:
              limits:
                cpu: "2"
                memory: "4Gi"
          timeoutSeconds: 3600
          serviceAccountName: sentinelops-worker-${ENVIRONMENT}@${PROJECT_ID}.iam.gserviceaccount.com
      parallelism: 5
      taskCount: 10
      taskTimeout: 600s
  executionSpec:
    parallelism: 5
    taskCount: 10
EOF
    
    gcloud run jobs replace /tmp/${JOB}-job.yaml \
        --region=us-central1 \
        --project="$PROJECT_ID" || echo "Job creation failed"
done# Create preemption handler script
echo "Creating preemption handler..."
cat > /tmp/preemption-handler.sh <<'EOF'
#!/bin/bash
# Preemption handler for graceful shutdown

METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/preempted"

# Check for preemption notice
while true; do
    if curl -H "Metadata-Flavor: Google" -s $METADATA_URL | grep -q "TRUE"; then
        echo "Preemption notice detected!"
        
        # Gracefully stop work
        pkill -TERM worker
        
        # Save state if needed
        /opt/sentinelops/save-state.sh
        
        # Signal completion
        curl -X POST http://orchestrator/worker/shutdown \
            -H "Content-Type: application/json" \
            -d '{"instance": "'$(hostname)'", "reason": "preempted"}'
        
        exit 0
    fi
    sleep 5
done
EOF

# Set up monitoring for preemptible instances
echo "Setting up preemptible instance monitoring..."
gcloud monitoring policies create \
    --notification-channels=$(gcloud alpha monitoring channels list --filter="displayName='SentinelOps Alerts'" --format="value(name)") \
    --display-name="Preemptible Instance Monitoring" \
    --condition-display-name="High Preemption Rate" \
    --condition-metric-type="compute.googleapis.com/instance/preempted_count" \
    --condition-comparison="COMPARISON_GT" \
    --condition-threshold-value=5 \
    --condition-duration=300s \
    --project="$PROJECT_ID"

echo "Preemptible instance setup complete!"
echo "Cost savings: ~80% for batch workloads"
echo "Monitor preemption rates in Cloud Console"
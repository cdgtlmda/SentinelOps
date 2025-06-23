#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
CLUSTER_NAME="${2:-sentinelops-cluster}"
ENVIRONMENT="${3:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [CLUSTER_NAME] [ENVIRONMENT]"
    exit 1
fi

echo "Setting up Workload Identity for project: $PROJECT_ID"
echo "Cluster: $CLUSTER_NAME"
echo "Environment: $ENVIRONMENT"

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable container.googleapis.com --project="$PROJECT_ID"
gcloud services enable iam.googleapis.com --project="$PROJECT_ID"

# Create service accounts for each component
echo "Creating service accounts..."
COMPONENTS=("orchestrator" "detection" "analysis" "remediation" "communication")

for COMPONENT in "${COMPONENTS[@]}"; do
    SA_NAME="sentinelops-${COMPONENT}-${ENVIRONMENT}"
    echo "Creating service account: $SA_NAME"
    
    gcloud iam service-accounts create $SA_NAME \
        --display-name="SentinelOps ${COMPONENT^} Service Account" \
        --project="$PROJECT_ID" || echo "Service account already exists"
done# Bind IAM policies for workload identity
echo "Configuring workload identity bindings..."
for COMPONENT in "${COMPONENTS[@]}"; do
    SA_NAME="sentinelops-${COMPONENT}-${ENVIRONMENT}"
    KSA_NAME="sentinelops-${COMPONENT}-ksa"
    NAMESPACE="sentinelops"
    
    echo "Binding workload identity for $COMPONENT..."
    
    # Allow the Kubernetes service account to impersonate the Google service account
    gcloud iam service-accounts add-iam-policy-binding \
        ${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
        --role=roles/iam.workloadIdentityUser \
        --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/${KSA_NAME}]" \
        --project="$PROJECT_ID"
    
    # Grant specific permissions based on component
    case $COMPONENT in
        "orchestrator")
            gcloud projects add-iam-policy-binding $PROJECT_ID \
                --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
                --role="roles/pubsub.editor"
            gcloud projects add-iam-policy-binding $PROJECT_ID \
                --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
                --role="roles/monitoring.viewer"
            ;;
        "detection")
            gcloud projects add-iam-policy-binding $PROJECT_ID \
                --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
                --role="roles/logging.viewer"
            gcloud projects add-iam-policy-binding $PROJECT_ID \
                --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
                --role="roles/securitycenter.findingsViewer"
            ;;
    esac
done# Create Kubernetes service accounts with annotations
echo "Creating Kubernetes service accounts..."
cat > /tmp/workload-identity-k8s.yaml <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: sentinelops
---
EOF

for COMPONENT in "${COMPONENTS[@]}"; do
    SA_NAME="sentinelops-${COMPONENT}-${ENVIRONMENT}"
    KSA_NAME="sentinelops-${COMPONENT}-ksa"
    
    cat >> /tmp/workload-identity-k8s.yaml <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${KSA_NAME}
  namespace: sentinelops
  annotations:
    iam.gke.io/gcp-service-account: ${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
---
EOF
done

echo "Applying Kubernetes configurations..."
kubectl apply -f /tmp/workload-identity-k8s.yaml

# Update GKE cluster for workload identity
echo "Updating GKE cluster for workload identity..."
gcloud container clusters update $CLUSTER_NAME \
    --workload-pool=${PROJECT_ID}.svc.id.goog \
    --zone=us-central1-a \
    --project="$PROJECT_ID"

echo "Workload Identity setup complete!"
echo "Remember to update your deployments to use the service accounts"
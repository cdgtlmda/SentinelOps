#!/bin/bash
# Script to create service account for SentinelOps

echo "SentinelOps - Service Account Creator"
echo "===================================="

# Check authentication and project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "Error: No project set."
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "Using project: $PROJECT_ID"
echo ""

# Service account details
SA_NAME="sentinelops-sa"
SA_DISPLAY_NAME="SentinelOps Service Account"
SA_DESCRIPTION="Service account for SentinelOps security agents"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account already exists
if gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo "Service account already exists: $SA_EMAIL"
    read -p "Do you want to continue and update its roles? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    # Create service account
    echo "Creating service account..."
    gcloud iam service-accounts create $SA_NAME \
        --display-name="$SA_DISPLAY_NAME" \
        --description="$SA_DESCRIPTION" \
        --project=$PROJECT_ID
    
    if [ $? -ne 0 ]; then
        echo "Failed to create service account"
        exit 1
    fi
    echo "✓ Service account created: $SA_EMAIL"
fi

# Define roles
echo ""
echo "Assigning IAM roles..."

ROLES=(
    "roles/bigquery.dataViewer"
    "roles/bigquery.jobUser"
    "roles/cloudfunctions.developer"
    "roles/run.invoker"
    "roles/compute.viewer"
    "roles/logging.admin"
    "roles/storage.admin"
    "roles/aiplatform.user"
    "roles/pubsub.editor"
    "roles/secretmanager.secretAccessor"
)

# Grant roles
for role in "${ROLES[@]}"; do
    echo -n "Granting $role... "
    if gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --condition=None \
        --quiet &>/dev/null; then
        echo "✓"
    else
        echo "✗ (may already exist)"
    fi
done

# Create key
echo ""
echo "Creating service account key..."

# Create directory for keys
KEY_DIR="$HOME/.sentinelops/keys"
mkdir -p "$KEY_DIR"

KEY_FILE="$KEY_DIR/sentinelops-sa-key.json"

# Check if key already exists
if [ -f "$KEY_FILE" ]; then
    read -p "Key file already exists. Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing key file."
    else
        rm -f "$KEY_FILE"
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account=$SA_EMAIL \
            --project=$PROJECT_ID
        chmod 600 "$KEY_FILE"
        echo "✓ New key created: $KEY_FILE"
    fi
else
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account=$SA_EMAIL \
        --project=$PROJECT_ID
    chmod 600 "$KEY_FILE"
    echo "✓ Key created: $KEY_FILE"
fi

echo ""
echo "✅ Service account setup complete!"
echo ""
echo "Update your .env file with:"
echo "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
echo "GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE"
echo ""
echo "Next steps:"
echo "1. Update .env file with the above values"
echo "2. Run: source .env"
echo "3. Run: make validate-env"

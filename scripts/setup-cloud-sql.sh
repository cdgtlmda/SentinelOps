#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
INSTANCE_NAME="${2:-sentinelops-db}"
REGION="${3:-us-central1}"
ENVIRONMENT="${4:-dev}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [INSTANCE_NAME] [REGION] [ENVIRONMENT]"
    exit 1
fi

echo "Setting up Cloud SQL for project: $PROJECT_ID"

# Enable required APIs
echo "Enabling Cloud SQL APIs..."
gcloud services enable sqladmin.googleapis.com --project="$PROJECT_ID"
gcloud services enable cloudkms.googleapis.com --project="$PROJECT_ID"

# Create KMS key for encryption
echo "Creating KMS keyring and key..."
gcloud kms keyrings create sentinelops-sql \
    --location="$REGION" \
    --project="$PROJECT_ID" || echo "Keyring already exists"

gcloud kms keys create sql-encryption \
    --location="$REGION" \
    --keyring=sentinelops-sql \
    --purpose=encryption \
    --project="$PROJECT_ID" || echo "Key already exists"

# Set tier based on environment
if [ "$ENVIRONMENT" == "prod" ]; then
    TIER="db-custom-4-16384"
    HA_TYPE="REGIONAL"
else
    TIER="db-custom-2-8192"
    HA_TYPE="ZONAL"
fi

# Create Cloud SQL instance
echo "Creating Cloud SQL instance..."
gcloud sql instances create "$INSTANCE_NAME-$ENVIRONMENT" \
    --database-version=POSTGRES_15 \
    --tier="$TIER" \
    --region="$REGION" \
    --network=projects/"$PROJECT_ID"/global/networks/sentinelops-vpc-"$ENVIRONMENT" \
    --no-assign-ip \
    --availability-type="$HA_TYPE" \
    --enable-bin-log \
    --backup-start-time=03:00 \
    --retained-backups-count=30 \
    --retained-transaction-log-days=7 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4 \
    --maintenance-release-channel=production \
    --database-flags=cloudsql.iam_authentication=on \
    --disk-encryption-key=projects/"$PROJECT_ID"/locations/"$REGION"/keyRings/sentinelops-sql/cryptoKeys/sql-encryption \
    --project="$PROJECT_ID" || echo "Instance already exists"

# Create database
echo "Creating database..."
gcloud sql databases create sentinelops \
    --instance="$INSTANCE_NAME-$ENVIRONMENT" \
    --project="$PROJECT_ID" || echo "Database already exists"

# Create service account for Cloud SQL
echo "Creating Cloud SQL service account..."
gcloud iam service-accounts create sentinelops-sql-"$ENVIRONMENT" \
    --display-name="SentinelOps Cloud SQL Service Account $ENVIRONMENT" \
    --project="$PROJECT_ID" || echo "Service account already exists"

# Grant permissions
echo "Granting permissions..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:sentinelops-sql-${ENVIRONMENT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Create Cloud SQL Proxy connection
echo "Setting up Cloud SQL Proxy..."
CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME-$ENVIRONMENT" \
    --project="$PROJECT_ID" \
    --format="value(connectionName)")

echo "Cloud SQL setup complete!"
echo "Instance: $INSTANCE_NAME-$ENVIRONMENT"
echo "Connection name: $CONNECTION_NAME"
echo "Database: sentinelops"
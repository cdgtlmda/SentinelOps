#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
DATASET_ID="${2:-sentinelops_analytics}"
LOCATION="${3:-US}"
ENVIRONMENT="${4:-dev}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [DATASET_ID] [LOCATION] [ENVIRONMENT]"
    exit 1
fi

echo "Setting up BigQuery for project: $PROJECT_ID"

# Enable BigQuery API
echo "Enabling BigQuery API..."
gcloud services enable bigquery.googleapis.com --project="$PROJECT_ID"

# Create dataset
echo "Creating BigQuery dataset..."
bq mk -d \
    --location="$LOCATION" \
    --description="SentinelOps Analytics Dataset for $ENVIRONMENT" \
    --project_id="$PROJECT_ID" \
    "${DATASET_ID}_${ENVIRONMENT}" || echo "Dataset already exists"

# Set dataset expiration based on environment
if [ "$ENVIRONMENT" != "prod" ]; then
    echo "Setting dataset expiration for non-prod environment..."
    bq update \
        --default_table_expiration=7776000 \
        --project_id="$PROJECT_ID" \
        "${DATASET_ID}_${ENVIRONMENT}"
fi

# Create tables
echo "Creating tables..."

# Incidents table
bq mk -t \
    --project_id="$PROJECT_ID" \
    --description="Security incidents data" \
    --time_partitioning_field=created_at \
    --time_partitioning_type=DAY \
    "${DATASET_ID}_${ENVIRONMENT}.incidents" \
    incident_id:STRING,severity:STRING,status:STRING,created_at:TIMESTAMP,updated_at:TIMESTAMP,source:STRING,description:STRING,affected_resources:JSON,tags:STRING,remediation_actions:JSON

# Events table
bq mk -t \
    --project_id="$PROJECT_ID" \
    --description="Security events data" \
    --time_partitioning_field=timestamp \
    --time_partitioning_type=HOUR \
    --clustering_fields=event_type,severity \
    "${DATASET_ID}_${ENVIRONMENT}.events" \
    event_id:STRING,event_type:STRING,severity:STRING,timestamp:TIMESTAMP,source:STRING,resource_id:STRING,details:JSON

# Metrics table
bq mk -t \
    --project_id="$PROJECT_ID" \
    --description="System metrics data" \
    --time_partitioning_field=timestamp \
    --time_partitioning_type=HOUR \
    "${DATASET_ID}_${ENVIRONMENT}.metrics" \
    metric_name:STRING,value:FLOAT,timestamp:TIMESTAMP,labels:JSON,resource_type:STRING,resource_id:STRING

# Analysis results table
bq mk -t \
    --project_id="$PROJECT_ID" \
    --description="AI analysis results" \
    --time_partitioning_field=analysis_timestamp \
    --time_partitioning_type=DAY \
    "${DATASET_ID}_${ENVIRONMENT}.analysis_results" \
    analysis_id:STRING,incident_id:STRING,analysis_type:STRING,analysis_timestamp:TIMESTAMP,results:JSON,confidence_score:FLOAT,recommendations:JSON

# Create views
echo "Creating views..."

# Active incidents view
bq mk --use_legacy_sql=false \
    --project_id="$PROJECT_ID" \
    --view "SELECT * FROM \`${PROJECT_ID}.${DATASET_ID}_${ENVIRONMENT}.incidents\` WHERE status != 'resolved' ORDER BY severity DESC, created_at DESC" \
    "${DATASET_ID}_${ENVIRONMENT}.active_incidents"

# High severity events view
bq mk --use_legacy_sql=false \
    --project_id="$PROJECT_ID" \
    --view "SELECT * FROM \`${PROJECT_ID}.${DATASET_ID}_${ENVIRONMENT}.events\` WHERE severity IN ('critical', 'high') AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)" \
    "${DATASET_ID}_${ENVIRONMENT}.high_severity_events"

# Grant permissions
echo "Setting up permissions..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:sentinelops-${ENVIRONMENT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor" || echo "Binding already exists"

echo "BigQuery setup complete!"
echo "Dataset: ${DATASET_ID}_${ENVIRONMENT}"
echo "Location: $LOCATION"
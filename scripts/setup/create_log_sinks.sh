#!/bin/bash
# Log Export Setup Script
# Run this with appropriate permissions to create log sinks

PROJECT_ID="your-gcp-project-id"
DATASET_ID="sentinelops_dev"

echo "Creating log sinks for SentinelOps..."


# Create vpc-flow-logs-to-bigquery
gcloud logging sinks create vpc-flow-logs-to-bigquery \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/$DATASET_ID \
    --log-filter='resource.type="gce_subnetwork" AND log_name:"vpc_flows"' \
    --description="Export VPC flow logs to BigQuery" \
    --project=$PROJECT_ID


# Create audit-logs-to-bigquery
gcloud logging sinks create audit-logs-to-bigquery \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/$DATASET_ID \
    --log-filter='log_name:"cloudaudit.googleapis.com" AND severity >= WARNING' \
    --description="Export audit logs to BigQuery" \
    --project=$PROJECT_ID


# Create firewall-logs-to-bigquery
gcloud logging sinks create firewall-logs-to-bigquery \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/$DATASET_ID \
    --log-filter='resource.type="gce_firewall_rule"' \
    --description="Export firewall logs to BigQuery" \
    --project=$PROJECT_ID


echo "Log sinks created. Don't forget to grant BigQuery Data Editor role to the service accounts created by the sinks."

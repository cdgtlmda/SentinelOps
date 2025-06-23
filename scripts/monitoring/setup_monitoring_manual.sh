#!/bin/bash
# Manual setup script for SentinelOps monitoring

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"

echo "🚀 Setting up Monitoring for SentinelOps"
echo "   Project: $PROJECT_ID"
echo ""

# Create log-based metrics
echo "📏 Creating log-based metrics..."

# Incident count metric
gcloud logging metrics create incident_count \
    --description="Count of security incidents" \
    --log-filter='jsonPayload.event_type="security_incident"' \
    --value-extractor='EXTRACT(jsonPayload.severity)' \
    --project=$PROJECT_ID || echo "Metric may already exist"

# Remediation success rate
gcloud logging metrics create remediation_success_rate \
    --description="Rate of successful remediation actions" \
    --log-filter='jsonPayload.action="remediation_complete"' \
    --value-extractor='EXTRACT(IF(jsonPayload.success="true", 1, 0))' \
    --project=$PROJECT_ID || echo "Metric may already exist"

# Detection latency
gcloud logging metrics create detection_latency \
    --description="Time to detect threats in milliseconds" \
    --log-filter='jsonPayload.event_type="threat_detected"' \
    --value-extractor='EXTRACT(jsonPayload.detection_latency_ms)' \
    --project=$PROJECT_ID || echo "Metric may already exist"

# API errors
gcloud logging metrics create api_errors \
    --description="API errors by type" \
    --log-filter='severity>=ERROR AND jsonPayload.component="api"' \
    --project=$PROJECT_ID || echo "Metric may already exist"

echo "✅ Log-based metrics created"

# Create log sinks
echo -e "\n📤 Creating log sinks..."

# Create BigQuery dataset for security logs
echo "Creating BigQuery dataset for security logs..."
bq mk --dataset \
    --location=US \
    --description="Security logs from SentinelOps" \
    $PROJECT_ID:sentinelops_security_logs || echo "Dataset may already exist"

# Create log sink to BigQuery
gcloud logging sinks create security-logs-to-bigquery \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/sentinelops_security_logs \
    --log-filter='jsonPayload.event_type="security_incident" OR jsonPayload.event_type="threat_detected" OR severity >= ERROR' \
    --project=$PROJECT_ID || echo "Sink may already exist"

# Get the service account for the sink and grant permissions
SINK_SA=$(gcloud logging sinks describe security-logs-to-bigquery --project=$PROJECT_ID --format='value(writerIdentity)')
echo "Granting BigQuery Data Editor role to: $SINK_SA"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member=$SINK_SA \
    --role=roles/bigquery.dataEditor

# Create storage bucket for audit logs
echo -e "\nCreating storage bucket for audit logs..."
gsutil mb -p $PROJECT_ID -l $REGION gs://$PROJECT_ID-audit-logs || echo "Bucket may already exist"

# Create log sink to Cloud Storage
gcloud logging sinks create audit-logs-to-storage \
    storage.googleapis.com/$PROJECT_ID-audit-logs \
    --log-filter='protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog"' \
    --project=$PROJECT_ID || echo "Sink may already exist"

# Grant permissions
AUDIT_SINK_SA=$(gcloud logging sinks describe audit-logs-to-storage --project=$PROJECT_ID --format='value(writerIdentity)')
echo "Granting Storage Object Creator role to: $AUDIT_SINK_SA"
gsutil iam ch $AUDIT_SINK_SA:objectCreator gs://$PROJECT_ID-audit-logs

echo "✅ Log sinks created"

# Create alert policies
echo -e "\n🚨 Creating alert policies..."

# Note: Alert policies need to be created via Console or API with full JSON
# Here we provide the commands to check if monitoring API is enabled

gcloud services enable monitoring.googleapis.com --project=$PROJECT_ID

echo "✅ Monitoring API enabled"

# Create uptime checks
echo -e "\n🏥 Creating uptime checks..."

# Note: Uptime checks require the Cloud Run service URLs
# This is a template that needs to be updated with actual URLs

cat > uptime_checks.json << EOF
{
  "displayName": "Orchestrator Health Check",
  "monitoredResource": {
    "type": "uptime_url",
    "labels": {
      "project_id": "$PROJECT_ID",
      "host": "sentinelops-orchestrator-[HASH].a.run.app"
    }
  },
  "httpCheck": {
    "path": "/health",
    "port": 443,
    "requestMethod": "GET",
    "useSsl": true,
    "validateSsl": true
  },
  "period": "60s",
  "timeout": "10s",
  "selectedRegions": ["USA"]
}
EOF

echo "📝 Uptime check configuration saved to uptime_checks.json"
echo "   Update the host field with your actual Cloud Run URL"

# Create notification channels
echo -e "\n📧 Setting up notification channels..."

# Email notification channel
gcloud alpha monitoring channels create \
    --display-name="Security Team Email" \
    --type=email \
    --channel-labels=email_address=security-team@example.com \
    --project=$PROJECT_ID || echo "Channel may already exist"

echo "✅ Notification channels configured"

# Display useful links
echo -e "\n🔗 Useful Links:"
echo "Monitoring Console: https://console.cloud.google.com/monitoring?project=$PROJECT_ID"
echo "Logging Console: https://console.cloud.google.com/logs?project=$PROJECT_ID"
echo "Error Reporting: https://console.cloud.google.com/errors?project=$PROJECT_ID"
echo "Dashboards: https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
echo "Alerts: https://console.cloud.google.com/monitoring/alerting?project=$PROJECT_ID"

echo -e "\n📋 Next Steps:"
echo "1. Update uptime_checks.json with actual Cloud Run URLs"
echo "2. Create custom dashboards in the Monitoring Console"
echo "3. Configure alert policies with appropriate thresholds"
echo "4. Set up notification channels (Slack, PagerDuty)"
echo "5. Create SLOs for critical user journeys"

echo -e "\n✅ Monitoring setup complete!"
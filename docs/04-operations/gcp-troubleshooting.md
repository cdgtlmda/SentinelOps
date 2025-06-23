# SentinelOps Troubleshooting Guide

This guide provides solutions for common issues encountered with the SentinelOps platform on Google Cloud Platform.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Service-Specific Issues](#service-specific-issues)
3. [Common Error Messages](#common-error-messages)
4. [Performance Issues](#performance-issues)
5. [Integration Problems](#integration-problems)
6. [Data Issues](#data-issues)
7. [Networking Issues](#networking-issues)
8. [Authentication and Authorization](#authentication-and-authorization)
9. [Cost and Billing Issues](#cost-and-billing-issues)
10. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostics

### System Health Check Script

```bash
#!/bin/bash
# quick_diagnostics.sh

echo "=== SentinelOps Quick Diagnostics ==="
echo "Timestamp: $(date)"
echo "Project: ${GCP_PROJECT_ID}"

# Check service status
echo -e "\n[SERVICE STATUS]"
for service in detection-agent analysis-agent communication-agent orchestration-agent; do
  STATUS=$(gcloud run services describe $service --region=us-central1 --format="value(status.conditions[0].message)" 2>&1)
  echo "$service: $STATUS"
done

# Check recent errors
echo -e "\n[RECENT ERRORS (Last Hour)]"
ERROR_COUNT=$(gcloud logging read 'severity>=ERROR' --freshness=1h --format="value(jsonPayload.message)" | wc -l)
echo "Total errors: $ERROR_COUNT"

# Check Pub/Sub health
echo -e "\n[PUB/SUB HEALTH]"
for topic in detection-topic analysis-topic remediation-topic communication-topic; do
  MSG_COUNT=$(gcloud pubsub topics list-snapshots $topic --format="value(name)" 2>&1 | wc -l)
  echo "$topic: Active"
done

# Check resource utilization
echo -e "\n[RESOURCE UTILIZATION]"
gcloud monitoring read --project=${GCP_PROJECT_ID} \
  --filter='metric.type="run.googleapis.com/container/cpu/utilizations"' \
  --format="table(resource.labels.service_name,point.value.distribution_value.mean)" \
  --window=1h | head -10

# Check budget status
echo -e "\n[BUDGET STATUS]"
CURRENT_SPEND=$(gcloud beta billing budgets list --billing-account=${BILLING_ACCOUNT_ID} \
  --format="value(amount.specifiedAmount.units,amountSpentSoFar.units)" | head -1)
echo "Monthly budget/spent: $CURRENT_SPEND"
```

### Common Diagnostic Commands

```bash
# View service logs
gcloud logging read "resource.labels.service_name='SERVICE_NAME'" \
  --limit=50 --format=json | jq '.[] | {timestamp: .timestamp, severity: .severity, message: .jsonPayload.message}'

# Check Pub/Sub subscription backlog
gcloud pubsub subscriptions list --format="table(name,ackDeadlineSeconds,numBacklogMessages)"

# View recent deployments
gcloud run revisions list --service=SERVICE_NAME --region=us-central1 --limit=5

# Check firewall rules
gcloud compute firewall-rules list --filter="name:sentinelops"

# Monitor real-time logs
gcloud logging tail "resource.type=cloud_run_revision" --format="value(timestamp,jsonPayload.message)"
```

## Service-Specific Issues

### Detection Agent Issues

#### Problem: Detection Agent not processing logs

**Symptoms:**
- No new incidents in Firestore
- BigQuery shows logs but no detections
- Detection topic has no messages

**Solution:**
```bash
# 1. Check BigQuery permissions
gcloud projects get-iam-policy ${GCP_PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:detection-agent-sa@" \
  --format="table(bindings.role)"

# 2. Verify BigQuery dataset access
bq show --format=prettyjson sentinelops_logs | jq '.access[]'

# 3. Check service logs for errors
gcloud logging read "resource.labels.service_name='detection-agent' AND severity>=ERROR" \
  --limit=20 --format=json

# 4. Restart the service
gcloud run services update detection-agent --region=us-central1 --clear-env-vars=DUMMY
gcloud run services update detection-agent --region=us-central1 --update-env-vars=DUMMY=1

# 5. Test with manual query
bq query --use_legacy_sql=false '
SELECT COUNT(*) as log_count 
FROM `sentinelops_logs.vpc_flow_logs` 
WHERE DATE(timestamp) = CURRENT_DATE()'
```

#### Problem: Detection rules not triggering

**Solution:**
```python
#!/usr/bin/env python3
# test_detection_rules.py

from google.cloud import firestore
import json

def test_detection_rule(rule_id):
    """Test a specific detection rule."""
    db = firestore.Client()
    
    # Get rule configuration
    rule = db.collection('detection_rules').document(rule_id).get()
    
    if not rule.exists:
        print(f"Rule {rule_id} not found")
        return
    
    rule_data = rule.to_dict()
    print(f"Testing rule: {rule_data['name']}")
    print(f"Condition: {rule_data['condition']}")
    
    # Test the rule logic
    test_event = {
        'severity': 'HIGH',
        'event_type': 'suspicious_login',
        'source_ip': '192.168.1.100',
        'user': 'test@example.com'
    }
    
    # Evaluate condition (simplified)
    try:
        result = eval(rule_data['condition'], {'event': test_event})
        print(f"Rule triggered: {result}")
    except Exception as e:
        print(f"Rule error: {e}")

# Test specific rule
test_detection_rule('suspicious_login_rule')
```

### Analysis Agent Issues

#### Problem: Vertex AI errors

**Symptoms:**
- Analysis timing out
- Authentication errors
- Rate limit exceeded

**Solution:**
```bash
# 1. Verify Vertex AI API is enabled
gcloud services list --enabled | grep aiplatform

# 2. Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"

# 3. Test Vertex AI directly
python -c "from vertexai.generative_models import GenerativeModel
from google.cloud import aiplatform
aiplatform.init(project='$PROJECT_ID', location='us-central1')
model = GenerativeModel('gemini-1.5-pro-002')
print(model.generate_content('Hello').text)"

# 4. Check rate limits
gcloud logging read "resource.labels.service_name='analysis-agent' AND jsonPayload.error_code='RATE_LIMIT_EXCEEDED'" \
  --limit=10

# 5. Implement exponential backoff
cat > /tmp/update_analysis_agent.py <<EOF
import time
import random

def exponential_backoff(attempt):
    """Calculate backoff time."""
    base_delay = 1.0
    max_delay = 60.0
    
    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
    time.sleep(delay)
    return delay
EOF
```

### Communication Agent Issues

#### Problem: Notifications not being sent

**Solution:**
```bash
# 1. Check Pub/Sub subscription
gcloud pubsub subscriptions describe communication-subscription \
  --format="json" | jq '.pushConfig'

# 2. Verify notification credentials
gcloud secrets list --filter="name:slack-webhook OR name:twilio"

# 3. Test notification channels manually
# Slack test
curl -X POST $(gcloud secrets versions access latest --secret=slack-webhook-url) \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test notification from SentinelOps"}'

# 4. Check communication agent logs
gcloud logging read "resource.labels.service_name='communication-agent' AND jsonPayload.notification_sent=true" \
  --limit=10

# 5. Verify Firestore incident records
cat > /tmp/check_incidents.py <<EOF
from google.cloud import firestore

db = firestore.Client()
incidents = db.collection('incidents').where('notified', '==', False).limit(10).stream()

for inc in incidents:
    data = inc.to_dict()
    print(f"Unnotified incident: {inc.id} - {data.get('created_at')}")
EOF

python /tmp/check_incidents.py
```

## Common Error Messages

### Error: "Permission denied"

**Context:** Any service trying to access GCP resources

**Solutions:**
```bash
# 1. Identify the missing permission
ERROR_MSG="permission \"bigquery.tables.getData\" denied"
PERMISSION=$(echo $ERROR_MSG | grep -oP '"\K[^"]+(?=")')

# 2. Find appropriate role
gcloud iam roles list --filter="permissions:$PERMISSION" --limit=5

# 3. Grant the role
SERVICE_ACCOUNT="detection-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/bigquery.dataViewer"

# 4. Wait for propagation (up to 60 seconds)
sleep 60

# 5. Test access
gcloud auth application-default login --impersonate-service-account=${SERVICE_ACCOUNT}
bq query --use_legacy_sql=false "SELECT 1"
```

### Error: "502 Bad Gateway"

**Context:** Cloud Run services

**Solutions:**
```bash
# 1. Check service status
gcloud run services describe SERVICE_NAME --region=us-central1

# 2. View recent logs
gcloud logging read "resource.labels.service_name='SERVICE_NAME' AND severity>=WARNING" \
  --limit=50 --format=json

# 3. Check container health
gcloud run revisions describe SERVICE_NAME-REVISION --region=us-central1 \
  --format="value(status.conditions[].message)"

# 4. Increase memory/CPU
gcloud run services update SERVICE_NAME \
  --memory=2Gi \
  --cpu=2 \
  --region=us-central1

# 5. Check startup probe
gcloud run services update SERVICE_NAME \
  --health-check-path=/health \
  --health-check-interval=30s \
  --health-check-timeout=10s \
  --region=us-central1
```

### Error: "Deadline exceeded"

**Context:** Long-running operations

**Solutions:**
```python
#!/usr/bin/env python3
# fix_timeout_issues.py

import os
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError

# Increase timeout for Pub/Sub
publisher = pubsub_v1.PublisherClient()
publisher.api.publish.retry._deadline = 600.0  # 10 minutes

# For Cloud Run services
os.environ['GRPC_CHANNEL_ARGS'] = json.dumps({
    "grpc.http2.max_pings_without_data": 0,
    "grpc.keepalive_time_ms": 30000,
    "grpc.keepalive_timeout_ms": 10000
})

# Update service timeout
os.system("""
gcloud run services update SERVICE_NAME \
  --timeout=3600 \
  --region=us-central1
""")
```

## Performance Issues

### Slow Query Performance

**Diagnosis:**
```sql
-- Find slow BigQuery queries
SELECT
  user_email,
  query,
  total_slot_ms,
  total_bytes_processed,
  TIMESTAMP_DIFF(end_time, start_time, SECOND) as duration_seconds
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE 
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
  AND total_slot_ms > 100000
ORDER BY total_slot_ms DESC
LIMIT 10;
```

**Solutions:**
```sql
-- 1. Add partition filter
SELECT * FROM sentinelops_logs.audit_logs
WHERE DATE(timestamp) = CURRENT_DATE()  -- Add partition filter
  AND severity = 'ERROR';

-- 2. Use clustering
CREATE OR REPLACE TABLE sentinelops_logs.audit_logs_optimized
PARTITION BY DATE(timestamp)
CLUSTER BY severity, resource_type
AS SELECT * FROM sentinelops_logs.audit_logs;

-- 3. Materialized views for repeated queries
CREATE MATERIALIZED VIEW sentinelops_logs.daily_summary AS
SELECT
  DATE(timestamp) as log_date,
  severity,
  COUNT(*) as count
FROM sentinelops_logs.audit_logs
GROUP BY log_date, severity;
```

### High Latency

**Diagnosis:**
```bash
# Check service latencies
for service in detection-agent analysis-agent communication-agent orchestration-agent; do
  echo "=== $service latency ==="
  gcloud monitoring read \
    --filter="metric.type=\"run.googleapis.com/request_latencies\" AND resource.labels.service_name=\"$service\"" \
    --format="table(point.value.distribution_value.mean)" \
    --window=1h | head -5
done
```

**Solutions:**
```bash
# 1. Enable Cloud CDN for static content
gcloud compute backend-services update sentinelops-backend \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC

# 2. Increase min instances to reduce cold starts
gcloud run services update SERVICE_NAME \
  --min-instances=2 \
  --region=us-central1

# 3. Optimize container startup
cat > Dockerfile.optimized <<EOF
FROM python:3.11-slim
# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Then copy code
COPY . .
# Use exec form to reduce startup overhead
ENTRYPOINT ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

# 4. Enable HTTP/2
gcloud run services update SERVICE_NAME \
  --use-http2 \
  --region=us-central1
```

## Integration Problems

### Pub/Sub Message Delivery Issues

**Diagnosis:**
```bash
# Check subscription metrics
SUBSCRIPTION="detection-subscription"
gcloud monitoring read \
  --filter="metric.type=\"pubsub.googleapis.com/subscription/oldest_unacked_message_age\" AND resource.labels.subscription_id=\"$SUBSCRIPTION\"" \
  --window=1h

# View dead letter queue
gcloud pubsub subscriptions describe $SUBSCRIPTION --format=json | jq '.deadLetterPolicy'
```

**Solutions:**
```bash
# 1. Increase ack deadline
gcloud pubsub subscriptions update $SUBSCRIPTION \
  --ack-deadline=600

# 2. Configure retry policy
gcloud pubsub subscriptions update $SUBSCRIPTION \
  --min-retry-delay=10s \
  --max-retry-delay=600s

# 3. Set up dead letter topic
gcloud pubsub topics create dead-letter-topic
gcloud pubsub subscriptions update $SUBSCRIPTION \
  --dead-letter-topic=dead-letter-topic \
  --max-delivery-attempts=5

# 4. Process dead letter messages
cat > process_dead_letters.py <<EOF
from google.cloud import pubsub_v1

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, 'dead-letter-subscription')

def callback(message):
    print(f"Dead letter message: {message.data}")
    # Investigate why message failed
    # Potentially replay to main topic
    message.ack()

flow_control = pubsub_v1.types.FlowControl(max_messages=100)
streaming_pull_future = subscriber.subscribe(
    subscription_path, callback=callback, flow_control=flow_control
)

with subscriber:
    streaming_pull_future.result()
EOF
```

### Firestore Connection Issues

**Diagnosis:**
```python
from google.cloud import firestore
import time

def test_firestore_connection():
    """Test Firestore connectivity and latency."""
    db = firestore.Client()
    
    # Write test
    start = time.time()
    doc_ref = db.collection('test').document('connectivity')
    doc_ref.set({'timestamp': firestore.SERVER_TIMESTAMP})
    write_time = time.time() - start
    
    # Read test
    start = time.time()
    doc = doc_ref.get()
    read_time = time.time() - start
    
    print(f"Write latency: {write_time*1000:.2f}ms")
    print(f"Read latency: {read_time*1000:.2f}ms")
    
    # Clean up
    doc_ref.delete()

test_firestore_connection()
```

**Solutions:**
```bash
# 1. Check Firestore mode
gcloud firestore databases describe --database="(default)"

# 2. Optimize queries with indexes
cat > firestore.indexes.json <<EOF
{
  "indexes": [
    {
      "collectionGroup": "incidents",
      "fields": [
        {"fieldPath": "severity", "order": "DESCENDING"},
        {"fieldPath": "created_at", "order": "DESCENDING"}
      ]
    }
  ]
}
EOF
gcloud firestore indexes create --file=firestore.indexes.json

# 3. Enable offline persistence (client-side)
cat > firestore_config.py <<EOF
import firebase_admin
from firebase_admin import firestore

# Enable offline persistence
db = firestore.client()
db._firestore_client._database._settings.cache_size_bytes = 100 * 1024 * 1024  # 100MB
EOF
```

## Data Issues

### Missing or Corrupted Data

**Diagnosis:**
```sql
-- Check for data gaps in BigQuery
WITH date_series AS (
  SELECT DATE_SUB(CURRENT_DATE(), INTERVAL day DAY) as check_date
  FROM UNNEST(GENERATE_ARRAY(0, 30)) AS day
)
SELECT 
  ds.check_date,
  COUNT(logs.timestamp) as log_count
FROM date_series ds
LEFT JOIN sentinelops_logs.audit_logs logs
  ON DATE(logs.timestamp) = ds.check_date
GROUP BY ds.check_date
HAVING log_count = 0
ORDER BY ds.check_date DESC;
```

**Recovery:**
```bash
# 1. Restore from backup
BACKUP_DATE="20240101"
gcloud firestore import gs://sentinelops-backups/firestore/${BACKUP_DATE}

# 2. Replay missing logs
bq query --use_legacy_sql=false "
INSERT INTO sentinelops_logs.audit_logs
SELECT * FROM sentinelops_logs.audit_logs_backup
WHERE DATE(timestamp) = '2024-01-01'"

# 3. Reconcile data
python scripts/reconcile_data.py --date=2024-01-01
```

### Data Inconsistency

**Detection:**
```python
#!/usr/bin/env python3
# detect_inconsistencies.py

from google.cloud import bigquery, firestore
import pandas as pd

def check_data_consistency():
    """Compare data between BigQuery and Firestore."""
    
    # Get incident count from Firestore
    db = firestore.Client()
    fs_incidents = db.collection('incidents').stream()
    fs_count = sum(1 for _ in fs_incidents)
    
    # Get incident count from BigQuery
    bq_client = bigquery.Client()
    query = """
    SELECT COUNT(*) as count
    FROM sentinelops_logs.incidents
    WHERE DATE(timestamp) >= CURRENT_DATE() - 7
    """
    bq_count = list(bq_client.query(query))[0].count
    
    print(f"Firestore incidents: {fs_count}")
    print(f"BigQuery incidents: {bq_count}")
    
    if abs(fs_count - bq_count) > 10:
        print("WARNING: Significant data inconsistency detected!")
        return False
    return True

check_data_consistency()
```

## Networking Issues

### Connection Timeouts

**Diagnosis:**
```bash
# Test connectivity to GCP services
for endpoint in bigquery.googleapis.com firestore.googleapis.com pubsub.googleapis.com; do
  echo "Testing $endpoint..."
  curl -w "@curl-format.txt" -o /dev/null -s https://$endpoint/
done

# Check VPC configuration
gcloud compute networks describe sentinelops-vpc
gcloud compute routers describe sentinelops-router --region=us-central1
```

**Solutions:**
```bash
# 1. Enable Private Google Access
gcloud compute networks subnets update sentinelops-subnet \
  --region=us-central1 \
  --enable-private-ip-google-access

# 2. Configure Cloud NAT for outbound
gcloud compute routers nats create sentinelops-nat \
  --router=sentinelops-router \
  --region=us-central1 \
  --nat-all-subnet-ip-ranges \
  --auto-allocate-nat-external-ips

# 3. Update firewall rules
gcloud compute firewall-rules create allow-google-apis \
  --network=sentinelops-vpc \
  --allow=tcp:443 \
  --destination-ranges=199.36.153.8/30,199.36.153.4/30 \
  --priority=1000
```

### DNS Resolution Issues

**Diagnosis:**
```bash
# Test DNS resolution
nslookup bigquery.googleapis.com
nslookup firestore.googleapis.com

# Check Cloud DNS configuration
gcloud dns managed-zones list
gcloud dns record-sets list --zone=sentinelops-zone
```

**Solutions:**
```bash
# 1. Configure Cloud DNS forwarding
gcloud dns managed-zones create google-apis \
  --description="Google APIs" \
  --dns-name="googleapis.com." \
  --networks=sentinelops-vpc \
  --forwarding-targets=8.8.8.8,8.8.4.4

# 2. Update resolv.conf in containers
cat >> Dockerfile <<EOF
RUN echo "nameserver 169.254.169.254" > /etc/resolv.conf
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf
EOF
```

## Authentication and Authorization

### Service Account Key Issues

**Diagnosis:**
```bash
# List all service account keys
for sa in $(gcloud iam service-accounts list --format="value(email)"); do
  echo "Keys for $sa:"
  gcloud iam service-accounts keys list --iam-account=$sa
done

# Check key age
gcloud iam service-accounts keys list \
  --iam-account=detection-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --filter="validAfterTime<-P90D" \
  --format="table(name,validAfterTime)"
```

**Solutions:**
```bash
# 1. Rotate service account key
SA_EMAIL="detection-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
OLD_KEY=$(gcloud iam service-accounts keys list --iam-account=$SA_EMAIL \
  --filter="keyType=USER_MANAGED" --format="value(name)" | head -1)

# Create new key
gcloud iam service-accounts keys create new-key.json --iam-account=$SA_EMAIL

# Update secret
gcloud secrets versions add sa-key --data-file=new-key.json

# Delete old key (after verification)
gcloud iam service-accounts keys delete $OLD_KEY --iam-account=$SA_EMAIL

# 2. Use Workload Identity instead
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${GCP_PROJECT_ID}.svc.id.goog[default/detection-agent]"
```

### Token Expiration

**Solutions:**
```python
#!/usr/bin/env python3
# handle_token_expiration.py

from google.auth import exceptions
from google.auth.transport import requests
import google.auth

def get_authenticated_client():
    """Get client with automatic token refresh."""
    credentials, project = google.auth.default()
    
    # Create a session that will automatically refresh tokens
    authed_session = requests.AuthorizedSession(credentials)
    
    # Token will be refreshed automatically
    return authed_session

def safe_api_call(func, *args, **kwargs):
    """Wrapper to handle token expiration."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except exceptions.RefreshError:
            if attempt < max_retries - 1:
                # Get new credentials
                credentials, _ = google.auth.default()
                credentials.refresh(requests.Request())
                continue
            raise
```

## Cost and Billing Issues

### Unexpected High Costs

**Diagnosis:**
```bash
# Identify cost spikes
bq query --use_legacy_sql=false "
SELECT
  service.description as service,
  sku.description as sku,
  DATE(usage_start_time) as usage_date,
  SUM(cost) as daily_cost
FROM \`${GCP_PROJECT_ID}.sentinelops_billing.gcp_billing_export_v1_*\`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY service, sku, usage_date
HAVING daily_cost > 100
ORDER BY daily_cost DESC"

# Check for unused resources
gcloud compute instances list --filter="status=TERMINATED"
gcloud compute disks list --filter="users:empty"
```

**Solutions:**
```bash
# 1. Set up budget alerts
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT_ID \
  --display-name="SentinelOps Daily Alert" \
  --budget-amount=500 \
  --threshold-rule=percent=0.8,basis=current-spend \
  --notification-channel-from-email=alerts@company.com

# 2. Implement cost controls
cat > cost_controls.sh <<EOF
#!/bin/bash
# Daily cost control script

# Stop idle instances
for instance in \$(gcloud compute instances list --filter="status=RUNNING" --format="value(name,zone)"); do
  NAME=\$(echo \$instance | cut -d' ' -f1)
  ZONE=\$(echo \$instance | cut -d' ' -f2)
  
  # Check CPU usage
  CPU_USAGE=\$(gcloud monitoring read \
    --filter="metric.type=\"compute.googleapis.com/instance/cpu/utilization\" AND resource.labels.instance_id=\"\$NAME\"" \
    --format="value(point.value.double_value)" \
    --window=1h | awk '{sum+=\$1} END {print sum/NR}')
  
  if (( \$(echo "\$CPU_USAGE < 0.05" | bc -l) )); then
    echo "Stopping idle instance: \$NAME"
    gcloud compute instances stop \$NAME --zone=\$ZONE
  fi
done
EOF

# 3. Optimize BigQuery usage
# Convert to clustered tables
bq update --clustering_fields=severity,event_type \
  sentinelops_logs.audit_logs
```

## Emergency Procedures

### Complete System Outage

```bash
#!/bin/bash
# emergency_recovery.sh

echo "EMERGENCY: Starting system recovery"

# 1. Check basic connectivity
if ! gcloud auth list &>/dev/null; then
  echo "ERROR: No GCP authentication"
  exit 1
fi

# 2. Verify project exists
if ! gcloud projects describe ${GCP_PROJECT_ID} &>/dev/null; then
  echo "ERROR: Project not accessible"
  exit 1
fi

# 3. Start core services
SERVICES="orchestration-agent detection-agent analysis-agent communication-agent"
for service in $SERVICES; do
  echo "Starting $service..."
  gcloud run services update $service \
    --region=us-central1 \
    --min-instances=1 \
    --max-instances=10 || echo "Failed to start $service"
done

# 4. Verify Pub/Sub
for topic in detection-topic analysis-topic remediation-topic communication-topic; do
  gcloud pubsub topics publish $topic --message="system_recovery_test" || \
    gcloud pubsub topics create $topic
done

# 5. Check data stores
bq query --use_legacy_sql=false "SELECT 1" || echo "BigQuery unavailable"
python -c "from google.cloud import firestore; firestore.Client().collection('test').add({})" || \
  echo "Firestore unavailable"

echo "Recovery attempt complete. Check service status."
```

### Data Corruption Recovery

```python
#!/usr/bin/env python3
# recover_corrupted_data.py

from google.cloud import firestore, bigquery
from datetime import datetime, timedelta
import json

def identify_corruption(collection_name, field_validations):
    """Identify corrupted documents."""
    db = firestore.Client()
    corrupted = []
    
    for doc in db.collection(collection_name).stream():
        data = doc.to_dict()
        
        for field, validator in field_validations.items():
            if field in data:
                try:
                    if not validator(data[field]):
                        corrupted.append({
                            'id': doc.id,
                            'field': field,
                            'value': data[field]
                        })
                except:
                    corrupted.append({
                        'id': doc.id,
                        'field': field,
                        'error': 'validation_failed'
                    })
    
    return corrupted

def restore_from_backup(collection_name, backup_date):
    """Restore specific documents from backup."""
    backup_path = f"gs://sentinelops-backups/firestore/{backup_date}/{collection_name}"
    
    # Import backup to temporary collection
    os.system(f"""
    gcloud firestore import {backup_path} \
      --collection-ids={collection_name}_restore
    """)
    
    print(f"Backup restored to {collection_name}_restore")
    print("Manual verification required before replacing production data")

# Example usage
validations = {
    'incidents': {
        'severity': lambda x: x in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        'timestamp': lambda x: isinstance(x, datetime),
        'status': lambda x: x in ['new', 'investigating', 'resolved']
    }
}

corrupted_docs = identify_corruption('incidents', validations['incidents'])
if corrupted_docs:
    print(f"Found {len(corrupted_docs)} corrupted documents")
    restore_from_backup('incidents', '20240101')
```

## Monitoring and Alerting

### Set Up Enhanced Monitoring

```yaml
# monitoring/troubleshooting-alerts.yaml
displayName: "High Error Rate Alert"
conditions:
  - displayName: "Error rate > 5%"
    conditionThreshold:
      filter: |
        resource.type="cloud_run_revision"
        metric.type="logging.googleapis.com/log_entry_count"
        metric.labels.severity="ERROR"
      comparison: COMPARISON_GT
      thresholdValue: 0.05
      duration: 300s
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_RATE
notificationChannels:
  - projects/[PROJECT_ID]/notificationChannels/[CHANNEL_ID]
---
displayName: "Service Unavailable Alert"
conditions:
  - displayName: "Service returning 5xx errors"
    conditionThreshold:
      filter: |
        resource.type="cloud_run_revision"
        metric.type="run.googleapis.com/request_count"
        metric.labels.response_code_class="5xx"
      comparison: COMPARISON_GT
      thresholdValue: 10
      duration: 60s
```

### Custom Debug Dashboard

```python
#!/usr/bin/env python3
# create_debug_dashboard.py

from google.cloud import monitoring_dashboard_v1

def create_troubleshooting_dashboard():
    """Create a dashboard for troubleshooting."""
    
    client = monitoring_dashboard_v1.DashboardsServiceClient()
    project_name = f"projects/{PROJECT_ID}"
    
    dashboard = monitoring_dashboard_v1.Dashboard()
    dashboard.display_name = "SentinelOps Troubleshooting"
    dashboard.grid_layout = monitoring_dashboard_v1.GridLayout()
    
    # Error rate widget
    error_widget = monitoring_dashboard_v1.Widget()
    error_widget.title = "Error Rate by Service"
    error_widget.xy_chart = monitoring_dashboard_v1.XyChart()
    
    # Add more widgets...
    
    dashboard.grid_layout.widgets.append(error_widget)
    
    response = client.create_dashboard(
        parent=project_name,
        dashboard=dashboard
    )
    
    print(f"Created dashboard: {response.name}")

create_troubleshooting_dashboard()
```

## Common Solutions Reference

### Quick Fixes Checklist

- [ ] Restart service: `gcloud run services update SERVICE --min-instances=0 && sleep 5 && gcloud run services update SERVICE --min-instances=1`
- [ ] Clear Pub/Sub backlog: `gcloud pubsub subscriptions seek SUBSCRIPTION --time=$(date -u +%Y-%m-%dT%H:%M:%S)`
- [ ] Increase timeout: `gcloud run services update SERVICE --timeout=3600`
- [ ] Add memory: `gcloud run services update SERVICE --memory=2Gi`
- [ ] Check quotas: `gcloud compute project-info describe --project=$PROJECT_ID`
- [ ] View audit logs: `gcloud logging read "protoPayload.@type=type.googleapis.com/google.cloud.audit.AuditLog"`
- [ ] Test connectivity: `gcloud compute ssh test-instance --command="curl -I https://www.google.com"`
- [ ] Validate IAM: `gcloud projects get-iam-policy $PROJECT_ID`

### Support Escalation

1. **Level 1**: Check this troubleshooting guide
2. **Level 2**: Platform team (#platform-support)
3. **Level 3**: Google Cloud Support (Enterprise)
4. **Emergency**: On-call engineer (PagerDuty)
# SentinelOps Maintenance Guide

This guide provides procedures for routine maintenance, updates, and operational tasks for the SentinelOps platform.

## Table of Contents

1. [Maintenance Schedule](#maintenance-schedule)
2. [Daily Maintenance Tasks](#daily-maintenance-tasks)
3. [Weekly Maintenance Tasks](#weekly-maintenance-tasks)
4. [Monthly Maintenance Tasks](#monthly-maintenance-tasks)
5. [Service Updates](#service-updates)
6. [Database Maintenance](#database-maintenance)
7. [Security Maintenance](#security-maintenance)
8. [Performance Optimization](#performance-optimization)
9. [Backup and Recovery](#backup-and-recovery)
10. [Emergency Procedures](#emergency-procedures)

## Maintenance Schedule

### Maintenance Windows

| Type | Schedule | Duration | Impact |
|------|----------|----------|--------|
| Daily Health Checks | 06:00 UTC | 30 min | None |
| Weekly Updates | Sunday 02:00-04:00 UTC | 2 hours | Minimal |
| Monthly Patches | First Sunday 00:00-06:00 UTC | 6 hours | Moderate |
| Quarterly Upgrades | Announced 30 days prior | 8 hours | Significant |

### Notification Policy

- Daily: No notification required
- Weekly: 24-hour notice via status page
- Monthly: 1-week notice via email
- Quarterly: 30-day notice via all channels

## Daily Maintenance Tasks

### 1. System Health Checks (06:00 UTC)

```bash
#!/bin/bash
# daily-health-check.sh

echo "=== SentinelOps Daily Health Check ==="
echo "Date: $(date)"

# Check Cloud Run services
echo -e "\n[Cloud Run Services]"
for service in detection-agent analysis-agent communication-agent orchestration-agent; do
  STATUS=$(gcloud run services describe $service --region=us-central1 --format="value(status.conditions[0].status)")
  echo "$service: $STATUS"
done

# Check Cloud Functions
echo -e "\n[Cloud Functions]"
for function in revoke-credentials block-ip-address isolate-vm; do
  STATE=$(gcloud functions describe $function --region=us-central1 --format="value(state)")
  echo "$function: $STATE"
done

# Check Pub/Sub subscriptions
echo -e "\n[Pub/Sub Subscriptions]"
gcloud pubsub subscriptions list --format="table(name,ackDeadlineSeconds,messageRetentionDuration)"

# Check BigQuery datasets
echo -e "\n[BigQuery Datasets]"
bq ls --format=prettyjson | jq -r '.[] | "\(.datasetReference.datasetId): \(.location)"'

# Check error rates
echo -e "\n[Error Rates - Last 24h]"
gcloud logging read 'severity="ERROR"' \
  --format="value(timestamp)" \
  --freshness=1d | wc -l

# Check budget status
echo -e "\n[Budget Status]"
python scripts/cost_optimization/check_daily_spend.py
```

### 2. Log Review

```bash
# Review security-relevant logs
gcloud logging read 'protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog" AND severity="WARNING"' \
  --freshness=1d \
  --limit=20

# Check for failed authentication attempts
gcloud logging read 'protoPayload.authenticationInfo.principalEmail!="" AND protoPayload.status.code!=0' \
  --freshness=1d \
  --limit=10
```

### 3. Metric Collection

```bash
# Collect daily metrics
python scripts/collect_daily_metrics.py

# Generate daily report
python scripts/generate_daily_report.py --date=$(date +%Y-%m-%d)
```

## Weekly Maintenance Tasks

### 1. Security Updates (Sunday 02:00 UTC)

```bash
#!/bin/bash
# weekly-security-update.sh

# Update container base images
for agent in detection analysis remediation communication orchestration; do
  echo "Updating $agent-agent..."

  # Pull latest base image
  docker pull python:3.11-slim

  # Rebuild with security patches
  cd src/agents/${agent}_agent/
  docker build --no-cache -t gcr.io/${GCP_PROJECT_ID}/${agent}-agent:latest .

  # Push updated image
  docker push gcr.io/${GCP_PROJECT_ID}/${agent}-agent:latest

  # Deploy rolling update
  gcloud run deploy ${agent}-agent \
    --image gcr.io/${GCP_PROJECT_ID}/${agent}-agent:latest \
    --region us-central1 \
    --max-instances 100 \
    --no-traffic

  # Gradual traffic migration
  for percent in 25 50 75 100; do
    gcloud run services update-traffic ${agent}-agent \
      --to-latest=$percent \
      --region us-central1

    # Wait and monitor
    sleep 300

    # Check error rate
    ERROR_COUNT=$(gcloud logging read "resource.labels.service_name=\"${agent}-agent\" AND severity=\"ERROR\"" \
      --freshness=5m --format="value(timestamp)" | wc -l)

    if [ $ERROR_COUNT -gt 10 ]; then
      echo "High error rate detected, rolling back..."
      gcloud run services update-traffic ${agent}-agent \
        --to-revisions=PREVIOUS=100 \
        --region us-central1
      exit 1
    fi
  done

  cd ../../../
done
```

### 2. Dependency Updates

```bash
# Update Python dependencies
cd /path/to/sentinelops

# Check for outdated packages
pip list --outdated

# Update requirements
pip-compile --upgrade requirements.in

# Test updated dependencies
python -m pytest tests/

# Commit updates
git add requirements.txt
git commit -m "chore: update dependencies $(date +%Y-%m-%d)"
git push
```

### 3. Performance Analysis

```bash
# Analyze Cloud Run performance
for service in detection-agent analysis-agent communication-agent orchestration-agent; do
  echo "=== $service Performance ==="

  # Get request latencies
  gcloud monitoring read \
    --project=${GCP_PROJECT_ID} \
    --filter='metric.type="run.googleapis.com/request_latencies" AND
             resource.labels.service_name="'$service'"' \
    --window=7d \
    --format="table(point.value.distribution_value.mean)"

  # Get CPU utilization
  gcloud monitoring read \
    --project=${GCP_PROJECT_ID} \
    --filter='metric.type="run.googleapis.com/container/cpu/utilizations" AND
             resource.labels.service_name="'$service'"' \
    --window=7d \
    --format="table(point.value.double_value)"
done

# Generate performance report
python scripts/analyze_performance.py --period=weekly
```

## Monthly Maintenance Tasks

### 1. Infrastructure Updates (First Sunday)

```bash
#!/bin/bash
# monthly-infrastructure-update.sh

# Update Terraform modules
cd terraform/
terraform get -update
terraform plan -out=monthly-update.tfplan

# Review plan
terraform show monthly-update.tfplan

# Apply updates during maintenance window
terraform apply monthly-update.tfplan

# Verify infrastructure
terraform validate
terraform output
```

### 2. Certificate Renewal

```bash
# Check certificate expiration
gcloud compute ssl-certificates list --format="table(name,expireTime)"

# Renew certificates expiring within 30 days
for cert in $(gcloud compute ssl-certificates list \
  --filter="expireTime < $(date -d '+30 days' --iso-8601)" \
  --format="value(name)"); do

  echo "Renewing certificate: $cert"

  # Generate new certificate
  gcloud compute ssl-certificates create ${cert}-renewed \
    --certificate=certs/${cert}.crt \
    --private-key=certs/${cert}.key

  # Update load balancer
  gcloud compute target-https-proxies update sentinelops-https-proxy \
    --ssl-certificates=${cert}-renewed

  # Delete old certificate after verification
  gcloud compute ssl-certificates delete $cert --quiet
done
```

### 3. Capacity Planning

```python
#!/usr/bin/env python3
# monthly_capacity_planning.py

import pandas as pd
from google.cloud import monitoring_v3
from datetime import datetime, timedelta

def analyze_growth_trends():
    """Analyze resource usage growth trends."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    # Define metrics to analyze
    metrics = [
        "run.googleapis.com/request_count",
        "compute.googleapis.com/instance/cpu/utilization",
        "storage.googleapis.com/storage/total_bytes"
    ]

    growth_analysis = {}

    for metric in metrics:
        # Get 3 months of data
        interval = monitoring_v3.TimeInterval({
            "end_time": {"seconds": int(datetime.now().timestamp())},
            "start_time": {"seconds": int((datetime.now() - timedelta(days=90)).timestamp())}
        })

        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": f'metric.type="{metric}"',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
            }
        )

        # Analyze growth rate
        data_points = []
        for result in results:
            for point in result.points:
                data_points.append({
                    'timestamp': point.interval.end_time,
                    'value': point.value.double_value or point.value.int64_value
                })

        if data_points:
            df = pd.DataFrame(data_points)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Calculate monthly growth rate
            monthly_growth = df.resample('M', on='timestamp')['value'].mean().pct_change().mean()

            growth_analysis[metric] = {
                'monthly_growth_rate': monthly_growth,
                'projected_3_month': df['value'].iloc[-1] * (1 + monthly_growth) ** 3,
                'current_value': df['value'].iloc[-1]
            }

    return growth_analysis

# Generate capacity planning report
growth_trends = analyze_growth_trends()
print("=== Capacity Planning Report ===")
for metric, analysis in growth_trends.items():
    print(f"\n{metric}:")
    print(f"  Current: {analysis['current_value']:.2f}")
    print(f"  Monthly Growth: {analysis['monthly_growth_rate']:.2%}")
    print(f"  3-Month Projection: {analysis['projected_3_month']:.2f}")
```

### 4. Database Optimization

```bash
# BigQuery optimization
echo "=== BigQuery Table Optimization ==="

# Analyze table sizes
bq query --use_legacy_sql=false '
SELECT
  table_schema as dataset,
  table_name,
  ROUND(size_bytes/1024/1024/1024, 2) as size_gb,
  row_count,
  TIMESTAMP_MILLIS(creation_time) as created,
  TIMESTAMP_MILLIS(LAST_MODIFIED_TIME) as last_modified
FROM `sentinelops-project.sentinelops_logs.__TABLES__`
ORDER BY size_bytes DESC'

# Optimize partitioning for large tables
for table in vpc_flow_logs audit_logs firewall_logs; do
  echo "Optimizing $table..."

  # Create optimized table
  bq query --use_legacy_sql=false "
  CREATE OR REPLACE TABLE sentinelops_logs.${table}_optimized
  PARTITION BY DATE(timestamp)
  CLUSTER BY severity, resource_type
  AS SELECT * FROM sentinelops_logs.${table}"

  # Verify optimization
  bq show --format=prettyjson sentinelops_logs.${table}_optimized
done

# Firestore optimization
echo -e "\n=== Firestore Index Optimization ==="
gcloud firestore indexes list
gcloud firestore indexes composite list

# Clean up old documents
python scripts/cleanup_old_incidents.py --days=90
```

## Service Updates

### Rolling Update Procedure

1. **Preparation**
   ```bash
   # Create update checklist
   cat > update_checklist.md <<EOF
   - [ ] Code review completed
   - [ ] Tests passing
   - [ ] Security scan clean
   - [ ] Documentation updated
   - [ ] Rollback plan ready
   - [ ] Stakeholders notified
   EOF
   ```

2. **Build and Test**
   ```bash
   # Build new version
   docker build -t gcr.io/${PROJECT_ID}/service:v${VERSION} .

   # Run integration tests
   docker-compose -f docker-compose.test.yml up --abort-on-container-exit

   # Security scan
   gcloud container images scan gcr.io/${PROJECT_ID}/service:v${VERSION}
   ```

3. **Deploy Canary**
   ```bash
   # Deploy new version without traffic
   gcloud run deploy service \
     --image gcr.io/${PROJECT_ID}/service:v${VERSION} \
     --tag canary \
     --no-traffic

   # Route 5% traffic to canary
   gcloud run services update-traffic service \
     --to-tags canary=5

   # Monitor canary
   watch -n 10 'gcloud logging read "resource.labels.service_name=\"service\" AND labels.\"run.googleapis.com/execution_id\"" --limit 10'
   ```

4. **Progressive Rollout**
   ```bash
   # Increase traffic gradually
   for percent in 10 25 50 100; do
     gcloud run services update-traffic service \
       --to-tags canary=$percent

     # Wait and monitor
     sleep 600

     # Check metrics
     python scripts/check_deployment_health.py --service=service --version=v${VERSION}
   done
   ```

### Rollback Procedure

```bash
#!/bin/bash
# rollback.sh

SERVICE=$1
PREVIOUS_VERSION=$2

echo "Rolling back $SERVICE to $PREVIOUS_VERSION"

# Immediate traffic shift
gcloud run services update-traffic $SERVICE \
  --to-revisions=${SERVICE}-${PREVIOUS_VERSION}=100 \
  --region=us-central1

# Verify rollback
STATUS=$(gcloud run services describe $SERVICE \
  --region=us-central1 \
  --format="value(status.traffic[0].revisionName)")

echo "Current revision: $STATUS"

# Create incident report
cat > rollback_report_$(date +%Y%m%d_%H%M%S).md <<EOF
# Rollback Report

**Service:** $SERVICE
**Date:** $(date)
**Previous Version:** $PREVIOUS_VERSION
**Reason:** [Fill in reason]
**Impact:** [Fill in impact]
**Actions Taken:** Immediate rollback to stable version
**Follow-up Required:** [Fill in follow-up]
EOF
```

## Database Maintenance

### BigQuery Maintenance

```bash
# Monthly table maintenance
#!/bin/bash

# Export old data for archival
EXPORT_DATE=$(date -d '90 days ago' +%Y%m%d)
bq extract \
  --destination_format=AVRO \
  --compression=SNAPPY \
  sentinelops_logs.audit_logs \
  gs://sentinelops-archive/bigquery/audit_logs_${EXPORT_DATE}/*.avro

# Delete old partitions
bq query --use_legacy_sql=false "
DELETE FROM sentinelops_logs.audit_logs
WHERE DATE(timestamp) < DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)"

# Update table statistics
bq update \
  --description="Audit logs - Last updated $(date)" \
  sentinelops_logs.audit_logs
```

### Firestore Maintenance

```python
#!/usr/bin/env python3
# firestore_maintenance.py

from google.cloud import firestore
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_documents():
    """Remove documents older than retention period."""
    db = firestore.Client()

    collections = ['incidents', 'audit_logs', 'metrics']
    retention_days = {'incidents': 90, 'audit_logs': 365, 'metrics': 30}

    for collection in collections:
        cutoff_date = datetime.now() - timedelta(days=retention_days[collection])

        # Query old documents
        old_docs = db.collection(collection).where(
            'timestamp', '<', cutoff_date
        ).limit(500).stream()

        batch = db.batch()
        count = 0

        for doc in old_docs:
            batch.delete(doc.reference)
            count += 1

            if count >= 500:
                batch.commit()
                batch = db.batch()
                count = 0

        if count > 0:
            batch.commit()

        logger.info(f"Cleaned up {count} documents from {collection}")

def optimize_indexes():
    """Review and optimize Firestore indexes."""
    # This would typically be done through the console or gcloud
    logger.info("Review indexes at: https://console.cloud.google.com/firestore/indexes")

if __name__ == "__main__":
    cleanup_old_documents()
    optimize_indexes()
```

## Security Maintenance

### 1. Access Review

```bash
#!/bin/bash
# monthly_access_review.sh

echo "=== Monthly IAM Access Review ==="
echo "Date: $(date)"

# List all IAM bindings
echo -e "\n[Service Account Permissions]"
for sa in $(gcloud iam service-accounts list --format="value(email)"); do
  echo -e "\nService Account: $sa"
  gcloud projects get-iam-policy $GCP_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$sa" \
    --format="table(bindings.role)"
done

# Check for overly permissive roles
echo -e "\n[Checking for Owner/Editor Roles]"
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role:(roles/owner OR roles/editor)" \
  --format="table(bindings.members,bindings.role)"

# Unused service accounts
echo -e "\n[Checking for Unused Service Accounts]"
for sa in $(gcloud iam service-accounts list --format="value(email)"); do
  LAST_AUTH=$(gcloud logging read "protoPayload.authenticationInfo.principalEmail=\"$sa\"" \
    --limit=1 --format="value(timestamp)" 2>/dev/null)

  if [ -z "$LAST_AUTH" ]; then
    echo "Never used: $sa"
  else
    DAYS_AGO=$(( ($(date +%s) - $(date -d "$LAST_AUTH" +%s)) / 86400 ))
    if [ $DAYS_AGO -gt 30 ]; then
      echo "Inactive $DAYS_AGO days: $sa"
    fi
  fi
done
```

### 2. Security Patches

```bash
# Check for security bulletins
curl -s https://cloud.google.com/security-bulletins | \
  grep -A 5 "$(date +%Y-%m)"

# Update security policies
gcloud compute security-policies list

# Apply recommended rules
gcloud compute security-policies rules create 9999 \
  --security-policy=sentinelops-security-policy \
  --expression="origin.region_code == 'CN' || origin.region_code == 'RU'" \
  --action=deny-403 \
  --description="Block high-risk regions"
```

### 3. Key Rotation

```bash
#!/bin/bash
# rotate_service_account_keys.sh

for sa in $(gcloud iam service-accounts list --format="value(email)"); do
  echo "Rotating keys for: $sa"

  # List existing keys
  OLD_KEYS=$(gcloud iam service-accounts keys list \
    --iam-account=$sa \
    --filter="keyType:USER_MANAGED AND validAfterTime<-P30D" \
    --format="value(name)")

  if [ ! -z "$OLD_KEYS" ]; then
    # Create new key
    gcloud iam service-accounts keys create \
      keys/${sa}-$(date +%Y%m%d).json \
      --iam-account=$sa

    # Update secret manager
    gcloud secrets versions add ${sa}-key \
      --data-file=keys/${sa}-$(date +%Y%m%d).json

    # Schedule old key deletion (7 days grace period)
    for key in $OLD_KEYS; do
      echo "Scheduling deletion of key: $key"
      # Add to deletion queue
      echo "$key" >> keys_to_delete_$(date -d '+7 days' +%Y%m%d).txt
    done
  fi
done
```

## Performance Optimization

### 1. Query Optimization

```python
#!/usr/bin/env python3
# optimize_queries.py

from google.cloud import bigquery
import pandas as pd

def analyze_query_performance():
    """Analyze and optimize slow queries."""
    client = bigquery.Client()

    # Find slow queries
    query = """
    SELECT
        user_email,
        query,
        total_slot_ms,
        total_bytes_processed,
        total_bytes_billed,
        TIMESTAMP_DIFF(end_time, start_time, SECOND) as duration_seconds
    FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE
        creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        AND job_type = 'QUERY'
        AND state = 'DONE'
        AND total_slot_ms > 10000
    ORDER BY total_slot_ms DESC
    LIMIT 20
    """

    results = client.query(query).to_dataframe()

    # Generate optimization recommendations
    for _, row in results.iterrows():
        print(f"\nQuery by {row['user_email']}:")
        print(f"Duration: {row['duration_seconds']}s")
        print(f"Bytes processed: {row['total_bytes_processed'] / 1e9:.2f} GB")

        # Check for common issues
        if "SELECT *" in row['query']:
            print("⚠️  Recommendation: Avoid SELECT *, specify needed columns")

        if "JOIN" in row['query'] and row['total_bytes_processed'] > 1e10:
            print("⚠️  Recommendation: Consider filtering before JOIN")

        if row['total_bytes_processed'] > row['total_bytes_billed'] * 2:
            print("⚠️  Recommendation: Add partition filter to reduce scan")

if __name__ == "__main__":
    analyze_query_performance()
```

### 2. Resource Right-Sizing

```bash
# Analyze Cloud Run utilization
for service in detection-agent analysis-agent communication-agent orchestration-agent; do
  echo "=== $service Utilization ==="

  # Get current configuration
  CURRENT_CPU=$(gcloud run services describe $service --region=us-central1 \
    --format="value(spec.template.spec.containers[0].resources.limits.cpu)")
  CURRENT_MEM=$(gcloud run services describe $service --region=us-central1 \
    --format="value(spec.template.spec.containers[0].resources.limits.memory)")

  echo "Current: CPU=$CURRENT_CPU, Memory=$CURRENT_MEM"

  # Analyze actual usage
  python scripts/analyze_service_utilization.py --service=$service --recommend
done
```

## Backup and Recovery

### Daily Backup Tasks

```bash
#!/bin/bash
# daily_backup.sh

BACKUP_DATE=$(date +%Y%m%d)
BACKUP_BUCKET="gs://sentinelops-backups"

echo "Starting daily backup for $BACKUP_DATE"

# Backup Firestore
gcloud firestore export ${BACKUP_BUCKET}/firestore/${BACKUP_DATE} \
  --collection-ids=incidents,configurations,audit_logs

# Backup configurations
gsutil -m rsync -r /sentinelops/config ${BACKUP_BUCKET}/configs/${BACKUP_DATE}/

# Backup scripts
tar -czf scripts_${BACKUP_DATE}.tar.gz scripts/
gsutil cp scripts_${BACKUP_DATE}.tar.gz ${BACKUP_BUCKET}/scripts/

# Verify backups
gsutil ls -l ${BACKUP_BUCKET}/*/${BACKUP_DATE}

# Clean up old backups (keep 30 days)
gsutil -m rm -r ${BACKUP_BUCKET}/*/$(date -d '30 days ago' +%Y%m%d)/
```

### Recovery Procedures

```bash
#!/bin/bash
# restore_from_backup.sh

RESTORE_DATE=$1
BACKUP_BUCKET="gs://sentinelops-backups"

if [ -z "$RESTORE_DATE" ]; then
  echo "Usage: $0 YYYYMMDD"
  exit 1
fi

echo "Restoring from backup date: $RESTORE_DATE"

# Restore Firestore
gcloud firestore import ${BACKUP_BUCKET}/firestore/${RESTORE_DATE}

# Restore configurations
gsutil -m rsync -r ${BACKUP_BUCKET}/configs/${RESTORE_DATE}/ /sentinelops/config/

# Restore scripts
gsutil cp ${BACKUP_BUCKET}/scripts/scripts_${RESTORE_DATE}.tar.gz .
tar -xzf scripts_${RESTORE_DATE}.tar.gz

echo "Restore completed. Please verify system functionality."
```

## Emergency Procedures

### System Outage Response

```bash
#!/bin/bash
# emergency_response.sh

case "$1" in
  "total_outage")
    echo "EMERGENCY: Total system outage detected"

    # 1. Switch to disaster recovery region
    gcloud config set compute/region us-east1

    # 2. Deploy emergency instances
    for service in detection analysis communication orchestration; do
      gcloud run deploy ${service}-agent-dr \
        --image gcr.io/${GCP_PROJECT_ID}/${service}-agent:stable \
        --region us-east1 \
        --service-account ${service}-agent-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
        --max-instances 10
    done

    # 3. Update DNS
    gcloud dns record-sets update sentinelops.com \
      --type=A \
      --rrdatas=DISASTER_RECOVERY_IP \
      --zone=sentinelops-zone
    ;;

  "data_corruption")
    echo "EMERGENCY: Data corruption detected"

    # 1. Stop all writes
    gcloud run services update-traffic detection-agent --to-percent=0 --region=us-central1

    # 2. Create snapshot
    SNAPSHOT_NAME="emergency-snapshot-$(date +%Y%m%d-%H%M%S)"
    gcloud firestore export gs://sentinelops-emergency/${SNAPSHOT_NAME}

    # 3. Restore from last known good backup
    ./restore_from_backup.sh $(date -d yesterday +%Y%m%d)
    ;;

  "security_breach")
    echo "EMERGENCY: Security breach detected"

    # 1. Revoke all service account keys
    for sa in $(gcloud iam service-accounts list --format="value(email)"); do
      for key in $(gcloud iam service-accounts keys list --iam-account=$sa --format="value(name)"); do
        gcloud iam service-accounts keys delete $key --iam-account=$sa --quiet
      done
    done

    # 2. Reset all passwords
    gcloud secrets versions add admin-password --data-file=<(openssl rand -base64 32)

    # 3. Enable emergency firewall rules
    gcloud compute firewall-rules create emergency-lockdown \
      --direction=INGRESS \
      --priority=1 \
      --action=DENY \
      --rules=all \
      --source-ranges=0.0.0.0/0
    ;;
esac
```

### Disaster Recovery Test

```bash
# Quarterly DR test procedure
#!/bin/bash
# dr_test.sh

echo "=== Disaster Recovery Test ==="
echo "Date: $(date)"
echo "Tester: $USER"

# 1. Verify backups
echo -e "\n[Verifying Backups]"
gsutil ls -l gs://sentinelops-backups/*/ | tail -10

# 2. Test restore to DR environment
echo -e "\n[Testing Restore]"
gcloud firestore import gs://sentinelops-backups/firestore/$(date +%Y%m%d) \
  --database=sentinelops-dr

# 3. Verify data integrity
echo -e "\n[Verifying Data]"
python scripts/verify_dr_data.py

# 4. Test failover
echo -e "\n[Testing Failover]"
./simulate_failover.sh

# 5. Generate report
cat > dr_test_report_$(date +%Y%m%d).md <<EOF
# Disaster Recovery Test Report

**Date:** $(date)
**Tester:** $USER

## Test Results
- [ ] Backups verified
- [ ] Restore successful
- [ ] Data integrity confirmed
- [ ] Failover tested
- [ ] Rollback successful

## Issues Found
[List any issues]

## Recommendations
[List any improvements]
EOF
```

## Monitoring and Alerting

### Alert Configuration

```yaml
# monitoring/maintenance-alerts.yaml
---
displayName: "Maintenance Window Alert"
conditions:
  - displayName: "Maintenance mode active"
    conditionThreshold:
      filter: 'resource.type="global"
              AND metric.type="custom.googleapis.com/maintenance/active"'
      comparison: COMPARISON_GT
      thresholdValue: 0
      duration: 0s
notificationChannels:
  - projects/[PROJECT_ID]/notificationChannels/[CHANNEL_ID]
documentation:
  content: |
    Maintenance mode is currently active.
    Expected end time: Check maintenance schedule.
    Contact: platform-team@company.com
---
displayName: "Backup Failure Alert"
conditions:
  - displayName: "Backup job failed"
    conditionThreshold:
      filter: 'resource.type="global"
              AND metric.type="custom.googleapis.com/backup/status"
              AND metric.labels.status="failed"'
      comparison: COMPARISON_GT
      thresholdValue: 0
      duration: 0s
notificationChannels:
  - projects/[PROJECT_ID]/notificationChannels/[CHANNEL_ID]
documentation:
  content: |
    Backup job has failed. Immediate action required.
    Check: /var/log/backup.log
    Runbook: https://wiki/backup-failure-runbook
```

### Maintenance Metrics

```python
#!/usr/bin/env python3
# report_maintenance_metrics.py

from google.cloud import monitoring_v3
import time

def report_metric(metric_type, value, labels=None):
    """Report custom metric to Cloud Monitoring."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    series = monitoring_v3.TimeSeries()
    series.metric.type = f"custom.googleapis.com/{metric_type}"
    series.resource.type = "global"

    if labels:
        for key, val in labels.items():
            series.metric.labels[key] = val

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)

    point = monitoring_v3.Point()
    point.interval.end_time.seconds = seconds
    point.interval.end_time.nanos = nanos
    point.value.double_value = value

    series.points = [point]

    client.create_time_series(name=project_name, time_series=[series])

# Report maintenance window status
report_metric("maintenance/active", 1.0, {"type": "scheduled"})

# Report backup status
report_metric("backup/status", 1.0, {"status": "success", "type": "firestore"})
```

## Documentation

### Maintenance Log Template

```markdown
# Maintenance Log Entry

**Date:** YYYY-MM-DD
**Time:** HH:MM UTC - HH:MM UTC
**Type:** [Daily|Weekly|Monthly|Emergency]
**Performed By:** [Name]

## Tasks Completed
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Issues Encountered
- None | Description of issues

## Changes Made
- Configuration changes
- Code deployments
- Infrastructure updates

## Follow-up Required
- None | List of follow-up items

## Metrics
- Downtime: X minutes
- Services affected: List
- Users impacted: Number

## Notes
Additional observations or recommendations
```

### Runbook Template

```markdown
# Runbook: [Procedure Name]

## Overview
Brief description of when and why to use this runbook.

## Prerequisites
- Required access levels
- Tools needed
- Initial checks

## Procedure
1. Step 1
   ```bash
   command example
   ```
2. Step 2
   - Sub-step A
   - Sub-step B

## Verification
- How to verify success
- Expected outcomes

## Rollback
- How to undo changes
- Recovery procedures

## Escalation
- When to escalate
- Who to contact

## Related Documents
- Link to other runbooks
- Reference documentation
```

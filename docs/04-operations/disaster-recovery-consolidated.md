# Consolidated Disaster Recovery and Backup Guide

This guide provides comprehensive disaster recovery (DR) and backup procedures for SentinelOps, including ADK-specific considerations and automated recovery processes.

## Table of Contents
1. [Overview](#overview)
2. [Backup Strategy](#backup-strategy)
3. [Disaster Recovery Plan](#disaster-recovery-plan)
4. [Automated Failover](#automated-failover)
5. [Recovery Procedures](#recovery-procedures)
6. [Testing and Validation](#testing-and-validation)
7. [Quick Reference](#quick-reference)

## Overview

### Recovery Objectives
- **RTO (Recovery Time Objective)**: 30 minutes
- **RPO (Recovery Point Objective)**: 1 hour
- **Availability Target**: 99.9% (8.76 hours downtime/year)

### DR Architecture
```mermaid
graph TD
    subgraph Primary Region (us-central1)
        PA[Primary Agents]
        PF[Primary Firestore]
        PB[Primary BigQuery]
    end

    subgraph DR Region (us-east1)
        DA[DR Agents - Standby]
        DF[Firestore Replica]
        DB[BigQuery Replica]
    end

    subgraph Backup Storage
        GCS[Cloud Storage Backups]
        SNAP[Snapshots]
    end

    PA -->|Continuous Sync| DA
    PF -->|Real-time Replication| DF
    PB -->|Scheduled Export| DB

    PF --> GCS
    PA --> SNAP
```

## Backup Strategy

### 1. Firestore Backups

#### Automated Daily Backups
```bash
# Create backup schedule
gcloud firestore backups schedules create daily-backup \
  --database='(default)' \
  --recurrence=daily \
  --retention=7d \
  --day-of-week=all

# Manual backup command
gcloud firestore export gs://${PROJECT_ID}-backups/firestore/$(date +%Y%m%d-%H%M%S) \
  --collection-ids='incidents,agent_states,rules,configurations'
```

#### Backup Configuration
```yaml
# config/backup.yaml
firestore_backup:
  schedule: "0 2 * * *"  # 2 AM daily
  retention_days: 7
  collections:
    - incidents
    - agent_states
    - rules
    - configurations
    - adk_sessions
  destination: gs://${PROJECT_ID}-backups/firestore/
  notification_channel: backup-alerts
```

### 2. BigQuery Backups

#### Dataset Snapshots
```sql
-- Create dataset snapshot
CREATE SNAPSHOT TABLE `sentinelops_logs_backup.snapshot_20250611`
CLONE `sentinelops_logs.security_events`
OPTIONS(
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
);
```

#### Export to Cloud Storage
```bash
# Export BigQuery tables
bq extract \
  --destination_format=AVRO \
  --compression=SNAPPY \
  sentinelops_logs.security_events \
  gs://${PROJECT_ID}-backups/bigquery/security_events_*.avro
```

### 3. Configuration Backups

#### ADK Configuration Backup
```python
# scripts/backup_adk_config.py
import json
from google.cloud import secretmanager, storage

def backup_adk_configuration():
    """Backup all ADK configurations and secrets."""
    backup_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "adk_config": load_adk_config(),
        "agent_configs": load_agent_configs(),
        "secret_refs": list_secret_references()
    }

    # Save to Cloud Storage
    bucket = storage.Client().bucket(f"{PROJECT_ID}-backups")
    blob = bucket.blob(f"configs/adk-config-{timestamp}.json")
    blob.upload_from_string(json.dumps(backup_data))
```

### 4. Container Image Backups

```bash
# Tag production images
for agent in detection analysis remediation communication orchestrator; do
  gcloud container images add-tag \
    ${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/${agent}-agent:latest \
    ${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinelops/${agent}-agent:backup-$(date +%Y%m%d)
done
```

## Disaster Recovery Plan

### 1. Detection and Declaration

#### Automated Detection
```yaml
# Disaster detection rules
disaster_triggers:
  - condition: primary_region_down
    threshold: all_agents_unhealthy
    duration: 5_minutes

  - condition: firestore_unavailable
    threshold: connection_errors > 100
    duration: 2_minutes

  - condition: data_corruption
    threshold: checksum_failures > 10
    duration: immediate
```

#### Manual Declaration Process
1. Incident Commander assesses situation
2. Confirms with 2+ team members
3. Initiates DR procedure
4. Notifies stakeholders

### 2. Failover Procedures

#### Automatic Failover
```python
# src/dr/auto_failover.py
class DisasterRecoveryManager:
    def __init__(self):
        self.primary_region = "us-central1"
        self.dr_region = "us-east1"

    async def initiate_failover(self):
        """Orchestrate automatic failover to DR region."""
        # 1. Update DNS/Load Balancer
        await self.update_traffic_routing(self.dr_region)

        # 2. Activate DR agents
        await self.activate_standby_agents()

        # 3. Verify data sync
        await self.verify_data_consistency()

        # 4. Update configuration
        await self.update_active_region_config()

        # 5. Notify stakeholders
        await self.send_failover_notifications()
```

#### Manual Failover Steps
```bash
# 1. Switch traffic to DR region
gcloud compute url-maps set-default-service sentinelops-lb \
  --default-service=sentinelops-dr-backend

# 2. Scale up DR agents
for agent in detection analysis remediation communication orchestrator; do
  gcloud run services update ${agent}-agent \
    --region=us-east1 \
    --min-instances=1 \
    --max-instances=20
done

# 3. Update Firestore connection
export FIRESTORE_REGION=us-east1
gcloud run services update orchestrator-agent \
  --update-env-vars="FIRESTORE_REGION=${FIRESTORE_REGION}"

# 4. Verify agent health
./scripts/dr/verify_dr_health.sh
```

### 3. Data Recovery Procedures

#### Firestore Recovery
```bash
# Restore from backup
gcloud firestore import gs://${PROJECT_ID}-backups/firestore/20250611-020000 \
  --database='(default)'

# Verify data integrity
python scripts/dr/verify_firestore_integrity.py \
  --collections=incidents,agent_states,rules
```

#### BigQuery Recovery
```sql
-- Restore from snapshot
CREATE OR REPLACE TABLE `sentinelops_logs.security_events`
CLONE `sentinelops_logs_backup.snapshot_20250611`;

-- Verify row counts
SELECT
  COUNT(*) as restored_rows,
  MAX(timestamp) as latest_event
FROM `sentinelops_logs.security_events`;
```

## Automated Failover

### 1. Health Check Configuration
```yaml
# config/health_checks.yaml
health_checks:
  orchestrator:
    endpoint: /health
    interval: 30s
    timeout: 10s
    failure_threshold: 3

  detection:
    endpoint: /health
    custom_check: verify_bigquery_access
    interval: 60s

  cross_region:
    enabled: true
    regions: [us-central1, us-east1]
    comparison_threshold: 0.8
```

### 2. Failover Automation Script
```python
# scripts/dr/automated_failover.py
class AutomatedFailover:
    def __init__(self):
        self.health_checker = HealthChecker()
        self.failover_manager = FailoverManager()

    async def monitor_and_failover(self):
        """Continuous monitoring with automatic failover."""
        while True:
            health_status = await self.health_checker.check_all_regions()

            if health_status.primary_unhealthy:
                if health_status.dr_healthy:
                    await self.execute_failover()
                else:
                    await self.alert_total_failure()

            await asyncio.sleep(30)

    async def execute_failover(self):
        """Execute automated failover process."""
        try:
            # Pre-failover snapshot
            await self.create_failover_snapshot()

            # Execute failover
            await self.failover_manager.failover_to_dr()

            # Verify success
            if await self.verify_failover_success():
                await self.notify_failover_complete()
            else:
                await self.initiate_rollback()

        except Exception as e:
            await self.escalate_to_oncall(e)
```

## Recovery Procedures

### 1. Full System Recovery

#### Step-by-Step Recovery
```bash
#!/bin/bash
# scripts/dr/full_recovery.sh

echo "Starting SentinelOps Full Recovery..."

# 1. Restore Firestore
echo "Restoring Firestore data..."
gcloud firestore import $FIRESTORE_BACKUP_PATH

# 2. Restore BigQuery
echo "Restoring BigQuery datasets..."
bq load --source_format=AVRO \
  sentinelops_logs.security_events \
  $BIGQUERY_BACKUP_PATH

# 3. Deploy agents
echo "Deploying all agents..."
for agent in detection analysis remediation communication orchestrator; do
  gcloud run deploy ${agent}-agent \
    --image=${DR_REGISTRY}/${agent}-agent:${RECOVERY_TAG} \
    --region=${RECOVERY_REGION}
done

# 4. Restore configurations
echo "Restoring configurations..."
gsutil cp -r gs://${BACKUP_BUCKET}/configs/* /config/

# 5. Verify system health
echo "Verifying system health..."
python scripts/dr/verify_recovery.py
```

### 2. Partial Recovery

#### Single Agent Recovery
```python
# scripts/dr/agent_recovery.py
async def recover_agent(agent_name: str, backup_timestamp: str):
    """Recover a single agent from backup."""
    # 1. Stop current agent
    await stop_agent(agent_name)

    # 2. Restore agent-specific data
    await restore_agent_state(agent_name, backup_timestamp)

    # 3. Deploy agent from backup image
    backup_image = f"{agent_name}-agent:backup-{backup_timestamp}"
    await deploy_agent(agent_name, backup_image)

    # 4. Verify agent functionality
    await verify_agent_health(agent_name)
```

### 3. Data-Only Recovery

```python
# scripts/dr/data_recovery.py
class DataRecovery:
    def recover_incident_data(self, start_time: datetime, end_time: datetime):
        """Recover lost incident data from backups."""
        # 1. Identify missing data
        missing_incidents = self.identify_gaps(start_time, end_time)

        # 2. Restore from Firestore backup
        restored_from_firestore = self.restore_firestore_range(
            missing_incidents
        )

        # 3. Reconstruct from BigQuery logs
        reconstructed = self.reconstruct_from_logs(
            missing_incidents - restored_from_firestore
        )

        # 4. Validate recovered data
        self.validate_recovered_data(
            restored_from_firestore | reconstructed
        )
```

## Testing and Validation

### 1. DR Test Schedule

```yaml
# config/dr_testing.yaml
dr_tests:
  monthly:
    - test: backup_restoration
      scope: single_collection
      duration: 30_minutes

  quarterly:
    - test: regional_failover
      scope: full_system
      duration: 2_hours
      notification_required: true

  annually:
    - test: complete_disaster_recovery
      scope: everything
      duration: 4_hours
      stakeholder_participation: required
```

### 2. Test Procedures

#### Backup Test
```bash
# scripts/dr/test_backup.sh
#!/bin/bash

# 1. Create test incident
TEST_ID=$(python scripts/create_test_incident.py)

# 2. Trigger backup
gcloud firestore export gs://${TEST_BUCKET}/test-backup

# 3. Delete test incident
python scripts/delete_incident.py --id=$TEST_ID

# 4. Restore from backup
gcloud firestore import gs://${TEST_BUCKET}/test-backup

# 5. Verify restoration
python scripts/verify_incident.py --id=$TEST_ID
```

#### Failover Test
```python
# scripts/dr/test_failover.py
async def test_regional_failover():
    """Test failover without affecting production."""
    # 1. Create DR test environment
    test_env = await create_test_environment("dr-test")

    # 2. Simulate primary failure
    await test_env.disable_primary_region()

    # 3. Execute failover
    await test_env.execute_failover()

    # 4. Validate functionality
    results = await test_env.run_validation_suite()

    # 5. Clean up
    await test_env.cleanup()

    return results
```

### 3. Validation Checklist

- [ ] All agents responding in DR region
- [ ] Data consistency verified
- [ ] Alert notifications working
- [ ] Performance within SLA
- [ ] No data loss detected
- [ ] Rollback procedures tested

## Quick Reference

### Emergency Contacts
- **Incident Commander**: On-call rotation
- **Cloud Support**: [Google Cloud Priority Support]
- **Escalation**: cdgtlmda@pm.me

### Critical Commands
```bash
# Immediate failover
./scripts/dr/emergency_failover.sh

# Check DR readiness
./scripts/dr/check_dr_ready.sh

# Restore latest backup
./scripts/dr/restore_latest.sh

# Verify system health
./scripts/dr/health_check_all.sh
```

### Recovery Priorities
1. **Restore agent functionality** (Detection → Orchestrator)
2. **Verify data integrity** (Incidents, State)
3. **Resume processing** (Clear backlogs)
4. **Validate remediation** (Safety checks)
5. **Notify stakeholders** (Status updates)

### Key Metrics During Recovery
- Agent health status
- Data sync lag
- Processing backlog
- Error rates
- Recovery time elapsed

---

*This consolidated DR guide ensures rapid recovery from any disaster scenario while maintaining data integrity and service availability.*

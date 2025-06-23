# SentinelOps Redundancy Guide

## Overview
This guide describes the redundancy mechanisms implemented in SentinelOps to ensure high availability and data durability.

## Redundancy Components

### 1. Database Redundancy (Firestore)
- **Primary**: us-central1
- **Replicas**: us-east1, us-west1
- **Backup Schedule**: Daily with 30-day retention
- **Sync Frequency**: Every 6 hours

**Backup Locations**:
- Primary: `gs://your-gcp-project-id-firestore-backups/`
- Secondary: `gs://your-gcp-project-id-firestore-backups-us-east1/`
- Tertiary: `gs://your-gcp-project-id-firestore-backups-us-west1/`

### 2. Message Queue Redundancy (Pub/Sub)
Each topic has 3 regional subscriptions with priority-based consumption:
- Priority 1: us-central1
- Priority 2: us-east1
- Priority 3: us-west1

**Dead Letter Queues**: Configured for all topics with 30-day retention

### 3. Container Image Redundancy
All agent images are replicated across regional Artifact Registries:
- `us-central1-docker.pkg.dev/your-gcp-project-id/sentinelops/`
- `us-east1-docker.pkg.dev/your-gcp-project-id/sentinelops/`
- `us-west1-docker.pkg.dev/your-gcp-project-id/sentinelops/`

### 4. Secret Redundancy
Secrets are replicated across regions (where supported):
- Multi-region replication for new secrets
- Manual sync for existing secrets

### 5. Network Redundancy
- VPC peering between all regions
- Global load balancer with regional backends
- Automatic traffic rerouting on failure

## Sync Operations

### Manual Sync Commands

**Firestore Backups**:
```bash
./scripts/sync_firestore_backups.sh
```

**Container Images**:
```bash
./scripts/sync_container_images.sh
```

**Pub/Sub Setup**:
```bash
./scripts/setup_pubsub_redundancy.sh
```

### Automated Sync
Configure cron jobs for automated synchronization:
```bash
# Add to crontab
0 */6 * * * /path/to/scripts/sync_firestore_backups.sh
0 */12 * * * /path/to/scripts/sync_container_images.sh
```

## Monitoring Redundancy

### Health Check
```bash
python scripts/monitor_redundancy_health.py
```

### Key Metrics to Monitor
1. **Backup Age**: No backup older than 24 hours
2. **Image Sync Status**: All images present in all regions
3. **Subscription Health**: All subscriptions active and processing
4. **Network Connectivity**: VPC peering active
5. **Secret Access**: Secrets accessible from all regions

## Failure Scenarios

### Single Region Failure
- **Impact**: Minimal, traffic automatically rerouted
- **Recovery**: Automatic within 30 seconds
- **Data Loss**: None (real-time replication)

### Primary Region Failure
- **Impact**: Performance degradation, no service interruption
- **Recovery**: Secondary region becomes primary
- **Action Required**: Monitor and prepare failback

### Multi-Region Failure
- **Impact**: Service degradation or interruption
- **Recovery**: Manual intervention required
- **Action**: Execute disaster recovery procedures

## Best Practices

### 1. Regular Testing
- Monthly redundancy verification
- Quarterly failover drills
- Annual full DR exercise

### 2. Monitoring
- Set up alerts for sync failures
- Monitor replication lag
- Track redundancy costs

### 3. Documentation
- Keep runbooks updated
- Document all manual procedures
- Maintain contact lists

## Cost Management

### Redundancy Costs
- **Storage**: 3x for all data and images
- **Network**: Cross-region traffic charges
- **Compute**: Minimal (only during active use)

### Optimization Tips
1. Use lifecycle policies for old backups
2. Implement intelligent routing
3. Monitor and optimize sync frequency
4. Use committed use discounts

## Maintenance Procedures

### Weekly Tasks
- Verify backup sync status
- Check image replication
- Review monitoring alerts

### Monthly Tasks
- Test failover procedures
- Update documentation
- Review costs

### Quarterly Tasks
- Full redundancy audit
- Performance testing
- Cost optimization review

## Emergency Procedures

### Loss of Redundancy
1. Identify affected component
2. Check recent changes
3. Execute recovery procedure
4. Monitor restoration
5. Document incident

### Contact Information
- **On-Call**: [Your on-call system]
- **Escalation**: [Escalation path]
- **GCP Support**: [Support details]

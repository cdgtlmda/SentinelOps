# SentinelOps Multi-Region High Availability Guide

## Overview
SentinelOps is deployed across multiple regions for high availability and disaster recovery.

**Deployment Regions:**
- Primary: us-central1 (70% traffic)
- Secondary: us-east1 (20% traffic)
- Tertiary: us-west1 (10% traffic)

## Architecture

### Regional Deployment
Each region contains:
- All 5 agent services (Detection, Analysis, Remediation, Communication, Orchestrator)
- Regional Artifact Registry for container images
- Regional Cloud Run services
- Regional monitoring and logging

### Global Components
- Global Load Balancer with SSL termination
- Health checks across all regions
- Automatic failover between regions
- Unified monitoring dashboard

## Deployment Process

### 1. Deploy to All Regions
```bash
./scripts/deploy_multi_region.sh
```

### 2. Configure Global Load Balancer
```bash
./scripts/setup_global_load_balancer.sh
```

### 3. Monitor Health
```bash
python scripts/monitor_multi_region_health.py
```

## Failover Scenarios

### Automatic Failover
The system automatically handles:
1. **Primary Region Failure**: Traffic routes to Secondary region
2. **Secondary Region Failure**: Traffic routes to Tertiary region
3. **Partial Failures**: Weighted routing adjusts based on health

### Manual Failover
To manually failover to a specific region:
```bash
gcloud compute url-maps set-default-service sentinelops-url-map \
    --default-service=sentinelops-backend-REGION \
    --project=your-gcp-project-id
```

## Health Monitoring

### Health Check Configuration
- Interval: 10 seconds
- Timeout: 5 seconds
- Unhealthy threshold: 3 failed checks
- Healthy threshold: 2 successful checks

### Monitoring Commands
```bash
# Check all regions
for region in us-central1 us-east1 us-west1; do
    echo "Checking $region..."
    gcloud run services list --region=$region --project=your-gcp-project-id
done

# Check global load balancer
gcloud compute backend-services list --global --project=your-gcp-project-id
```

## Traffic Distribution

### Normal Operation
- us-central1: 70% of traffic
- us-east1: 20% of traffic
- us-west1: 10% of traffic

### During Failover
- Healthy regions receive proportional traffic increase
- No manual intervention required
- < 30 second failover time

## Cost Considerations

### Multi-Region Costs
- 3x Cloud Run instances
- 3x Artifact Registry storage
- Global Load Balancer charges
- Cross-region network traffic

### Cost Optimization
1. Use committed use discounts
2. Implement auto-scaling policies
3. Schedule non-critical services
4. Monitor and optimize traffic patterns

## Testing Procedures

### Monthly HA Test
1. Simulate primary region failure
2. Verify automatic failover
3. Test application functionality
4. Restore normal operation
5. Document results

### Quarterly DR Drill
1. Full multi-region deployment
2. Data replication verification
3. Complete failover test
4. Performance benchmarking
5. Update procedures

## Troubleshooting

### Region Not Healthy
1. Check Cloud Run service status
2. Verify health endpoint responses
3. Review service logs
4. Check IAM permissions
5. Verify network connectivity

### Load Balancer Issues
1. Check backend service configuration
2. Verify SSL certificate
3. Review URL map rules
4. Check forwarding rules
5. Monitor traffic distribution

## Emergency Contacts

| Issue Type | Contact Method |
|------------|----------------|
| Regional Outage | PagerDuty On-Call |
| Load Balancer | GCP Support Ticket |
| Application Issues | Development Team |

## Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single Region Failure | < 30 seconds | 0 (real-time) |
| Multi-Region Failure | < 5 minutes | < 1 minute |
| Complete Rebuild | < 30 minutes | < 24 hours |

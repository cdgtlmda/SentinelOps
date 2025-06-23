# SentinelOps Resilience Testing Guide

## Overview
This guide describes the resilience testing framework for SentinelOps, which validates the system's ability to maintain operations during various failure scenarios.

## Test Categories

### 1. Single Service Failure
Tests the system's ability to continue operating when individual services fail.
- **Target**: One service at a time
- **Expected Result**: Other services remain operational
- **Recovery Time**: < 30 seconds

### 2. Load Spike Resilience
Validates performance under sudden traffic increases.
- **Load**: 100 concurrent requests
- **Success Criteria**: >90% success rate, <5x baseline latency
- **Auto-scaling**: Verified

### 3. Data Consistency
Ensures data remains synchronized across all regions.
- **Scope**: Firestore backups, configuration files
- **Validation**: Backup counts and timestamps
- **Sync Frequency**: Every 6 hours

### 4. Failover Performance
Measures the time required for automatic failover.
- **Detection**: 30 seconds (3 failed health checks)
- **Decision**: 10 seconds (pre-failover validation)
- **Execution**: 60 seconds (traffic rerouting)
- **Total Target**: < 2 minutes

### 5. Network Partition Resilience
Tests service operation during network segmentation.
- **Scenario**: Region isolation
- **Expected**: Services continue independently
- **Connectivity**: VPC peering validation

### 6. Cascading Failure Prevention
Validates mechanisms to prevent failure propagation.
- **Circuit Breakers**: Timeout and retry limits
- **Resource Isolation**: CPU and memory limits
- **Backoff Policies**: Exponential retry delays

### 7. Recovery Procedures
Tests automated recovery capabilities.
- **Scripts**: Master restore, failover automation
- **Monitoring**: Health checks and alerts
- **Documentation**: Runbooks and procedures

## Running Tests

### Manual Execution
```bash
# Run full test suite
python scripts/test_resilience.py

# Run specific test scenarios
./scripts/test_failover_scenarios.sh test-primary-failure
./scripts/test_failover_scenarios.sh test-cascade-failure
```

### Continuous Testing
Tests run automatically:
- **Daily**: 3:00 AM UTC
- **Post-deployment**: After any service update
- **On-demand**: Via manual trigger

### Test Reports
- **Location**: `RESILIENCE_TEST_REPORT.md`
- **Format**: Markdown with pass/fail status
- **Metrics**: Success rate, timing, details

## Interpreting Results

### Success Criteria
- **All Pass**: System is resilient and ready
- **Any Fail**: Investigate and remediate
- **Trends**: Monitor for degradation

### Common Issues
1. **Service Timeout**: Increase health check intervals
2. **Data Sync Lag**: Check network bandwidth
3. **Failover Delay**: Optimize detection thresholds
4. **Load Failures**: Review auto-scaling policies

## Best Practices

### Testing Schedule
- **Weekly**: Full resilience test suite
- **Monthly**: Disaster recovery drill
- **Quarterly**: Multi-region failure simulation
- **Annually**: Complete system stress test

### Pre-Production Testing
1. Deploy to staging environment
2. Run resilience tests
3. Fix any failures
4. Promote to production

### Monitoring Integration
- Export test results to monitoring dashboard
- Set up alerts for test failures
- Track trends over time
- Correlate with incidents

## Test Scenarios

### Scenario 1: Regional Outage
```bash
# Simulate primary region failure
./scripts/test_failover_scenarios.sh test-primary-failure
```

### Scenario 2: Service Degradation
```bash
# Generate load on specific service
python scripts/test_resilience.py --test load-spike
```

### Scenario 3: Data Center Migration
```bash
# Test controlled failover
python scripts/failover_automation.py us-central1 us-east1
```

## Maintenance

### Updating Tests
1. Identify new failure modes
2. Add test cases
3. Update success criteria
4. Document changes

### Test Data Management
- Clean up test artifacts
- Archive old reports
- Maintain test databases
- Update test configurations

## Troubleshooting

### Test Failures
1. Check service logs
2. Verify network connectivity
3. Review recent changes
4. Consult runbooks

### False Positives
- Adjust timeout values
- Update health check URLs
- Verify test assumptions
- Review success criteria

## Contact Information
- **Test Framework**: Platform Team
- **Service Owners**: Development Teams
- **Escalation**: On-call Engineer
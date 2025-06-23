# Runbook: [Procedure Name]

## Overview

- **Purpose**: Brief description of what this runbook covers
- **Severity**: Low | Medium | High | Critical
- **Expected Duration**: X minutes
- **Required Permissions**: List of required roles/permissions

## When to Use This Runbook

This runbook should be used when:
- Condition 1
- Condition 2
- Condition 3

## Prerequisites

- [ ] Access to Google Cloud Console
- [ ] Required IAM permissions
- [ ] Access to monitoring dashboards
- [ ] Other prerequisites

## Steps

### 1. Initial Assessment

**Time Estimate**: 2-5 minutes

1. Check the monitoring dashboard at [URL]
2. Verify the alert details:
   ```bash
   gcloud logging read "resource.type=xyz" --limit=10
   ```
3. Document initial findings

**Expected Output**: Description of what you should see

### 2. Diagnose the Issue

**Time Estimate**: 5-10 minutes

1. Run diagnostic command:
   ```bash
   # Command to diagnose issue
   kubectl get pods -n sentinelops
   ```

2. Check service health:
   ```bash
   curl https://api.sentinelops.com/health
   ```

3. Review recent changes:
   ```bash
   gcloud deployment-manager deployments list
   ```

**Decision Point**: Based on findings, proceed to appropriate resolution step.

### 3. Resolution Steps

#### Option A: Quick Fix

**When to use**: When issue is minor

1. Apply quick fix:
   ```bash
   # Quick fix command
   ```

2. Verify fix:
   ```bash
   # Verification command
   ```

#### Option B: Full Recovery

**When to use**: When quick fix doesn't work

1. Stop affected services:
   ```bash
   kubectl scale deployment detection-agent --replicas=0
   ```

2. Apply recovery procedure:
   ```bash
   # Recovery commands
   ```

3. Restart services:
   ```bash
   kubectl scale deployment detection-agent --replicas=3
   ```

### 4. Verification

**Time Estimate**: 5 minutes

1. Verify service is healthy:
   ```bash
   # Health check commands
   ```

2. Check metrics are normal:
   - Metric 1 should be < X
   - Metric 2 should be > Y

3. Monitor for 5 minutes to ensure stability

### 5. Post-Incident Actions

1. Update incident ticket with resolution
2. Document any deviations from this runbook
3. Schedule post-mortem if severity was High/Critical

## Rollback Procedure

If the resolution steps make things worse:

1. Stop current fix attempt
2. Restore from backup:
   ```bash
   # Rollback commands
   ```
3. Escalate to senior engineer

## Escalation

Escalate if:
- Issue persists after attempting resolution
- You encounter unexpected behavior
- Severity increases during resolution

### Escalation Contacts

1. **Primary**: On-call SRE - PagerDuty
2. **Secondary**: Team Lead - [Contact Info]
3. **Emergency**: CTO - [Contact Info]

## Common Issues

### Issue 1: [Description]
**Symptoms**: What you'll see
**Quick Fix**: Command or action
**Root Cause**: Why it happens

### Issue 2: [Description]
**Symptoms**: What you'll see
**Quick Fix**: Command or action
**Root Cause**: Why it happens

## Monitoring Commands

```bash
# View agent logs
kubectl logs -n sentinelops deployment/detection-agent --tail=100

# Check resource usage
kubectl top pods -n sentinelops

# View recent errors
gcloud logging read "severity>=ERROR" --limit=20

# Check API latency
curl -w "@curl-format.txt" https://api.sentinelops.com/health
```

## Related Documentation

- [Architecture Documentation](../architecture/README.md)
- [Agent Documentation](../agents/README.md)
- [Incident Response Plan](./incident-response.md)

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-15 | [Name] | Initial version |

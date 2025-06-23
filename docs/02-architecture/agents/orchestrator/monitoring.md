# Orchestration Agent Monitoring Guide

## Overview

This guide provides comprehensive monitoring strategies for the Orchestration Agent, including key metrics, dashboards, alerts, and troubleshooting procedures.

## Key Performance Indicators (KPIs)

### 1. Incident Processing Metrics

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `incident_processing_rate` | Incidents processed per minute | > 10/min | < 5/min |
| `incident_resolution_time` | Average time from detection to resolution | < 10 min | > 30 min |
| `incident_backlog` | Number of pending incidents | < 20 | > 50 |
| `incident_success_rate` | Percentage of successfully resolved incidents | > 95% | < 90% |

### 2. Workflow Performance Metrics

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `workflow_completion_rate` | Workflows completed successfully | > 98% | < 95% |
| `state_transition_time` | Average time per state transition | < 30s | > 60s |
| `workflow_timeout_rate` | Percentage of workflows timing out | < 2% | > 5% |
| `stuck_incident_rate` | Incidents stuck in a state | < 1% | > 3% |

### 3. System Health Metrics

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| `agent_uptime` | Orchestrator availability | > 99.9% | < 99% |
| `error_rate` | Errors per 1000 operations | < 5 | > 10 |
| `circuit_breaker_trips` | Circuit breaker activations per hour | < 2 | > 5 |
| `resource_utilization` | CPU/Memory usage | < 70% | > 85% |

## Monitoring Setup

### 1. Google Cloud Monitoring

```python
# Configure metric descriptors
metric_descriptors = [
    {
        "type": "custom.googleapis.com/orchestrator/incidents_processed",
        "metric_kind": "GAUGE",
        "value_type": "INT64",
        "description": "Number of incidents processed"
    },
    {
        "type": "custom.googleapis.com/orchestrator/workflow_duration",
        "metric_kind": "GAUGE",
        "value_type": "DOUBLE",
        "description": "Workflow completion time in seconds"
    }
]
```

### 2. Prometheus Metrics

```yaml
# Prometheus scrape configuration
scrape_configs:
  - job_name: 'orchestrator'
    static_configs:
      - targets: ['orchestrator:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### 3. Custom Metrics Collection

```python
# In your orchestrator code
await metrics_collector.record_metric(
    MetricType.WORKFLOW_DURATION,
    duration_seconds,
    labels={
        "severity": incident.severity,
        "outcome": "success"
    }
)
```

## Dashboard Configuration

### 1. Incident Overview Dashboard

```json
{
  "dashboard": {
    "title": "Orchestrator - Incident Overview",
    "panels": [
      {
        "title": "Active Incidents",
        "type": "gauge",
        "query": "sum(orchestrator_active_incidents)"
      },
      {
        "title": "Incident Processing Rate",
        "type": "line",
        "query": "rate(orchestrator_incidents_processed[5m])"
      },
      {
        "title": "Incidents by Severity",
        "type": "pie",
        "query": "sum by (severity) (orchestrator_incidents_by_severity)"
      },
      {
        "title": "Average Resolution Time",
        "type": "stat",
        "query": "avg(orchestrator_resolution_time_seconds)"
      }
    ]
  }
}
```

### 2. Workflow Performance Dashboard

```json
{
  "dashboard": {
    "title": "Orchestrator - Workflow Performance",
    "panels": [
      {
        "title": "State Transition Times",
        "type": "heatmap",
        "query": "orchestrator_state_transition_duration_seconds"
      },
      {
        "title": "Workflow Success Rate",
        "type": "gauge",
        "query": "rate(orchestrator_workflows_completed{status='success'}[5m])"
      },
      {
        "title": "Timeout Distribution",
        "type": "bar",
        "query": "sum by (state) (orchestrator_timeouts_total)"
      }
    ]
  }
}
```

### 3. System Health Dashboard

```json
{
  "dashboard": {
    "title": "Orchestrator - System Health",
    "panels": [
      {
        "title": "Error Rate",
        "type": "line",
        "query": "rate(orchestrator_errors_total[5m])"
      },
      {
        "title": "Circuit Breaker Status",
        "type": "table",
        "query": "orchestrator_circuit_breaker_state"
      },
      {
        "title": "Cache Performance",
        "type": "gauge",
        "query": "orchestrator_cache_hit_rate"
      },
      {
        "title": "Resource Usage",
        "type": "line",
        "query": "orchestrator_resource_usage_percent"
      }
    ]
  }
}
```

## Alert Configuration

### 1. Critical Alerts

```yaml
alerts:
  - name: "OrchestatorDown"
    expr: "up{job='orchestrator'} == 0"
    for: "1m"
    severity: "critical"
    annotations:
      summary: "Orchestrator is down"
      description: "The orchestrator agent has been down for more than 1 minute"
      
  - name: "HighErrorRate"
    expr: "rate(orchestrator_errors_total[5m]) > 0.1"
    for: "5m"
    severity: "critical"
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"
```

### 2. Warning Alerts

```yaml
alerts:
  - name: "IncidentBacklog"
    expr: "orchestrator_pending_incidents > 50"
    for: "10m"
    severity: "warning"
    annotations:
      summary: "Large incident backlog"
      description: "{{ $value }} incidents are pending processing"
      
  - name: "SlowWorkflows"
    expr: "histogram_quantile(0.95, orchestrator_workflow_duration_seconds) > 1800"
    for: "15m"
    severity: "warning"
    annotations:
      summary: "Workflows are running slowly"
      description: "95th percentile workflow duration is {{ $value }} seconds"
```

### 3. Info Alerts

```yaml
alerts:
  - name: "AutoApprovalDisabled"
    expr: "orchestrator_auto_approval_enabled == 0"
    for: "5m"
    severity: "info"
    annotations:
      summary: "Auto-approval is disabled"
      description: "Manual approval required for all remediation actions"
```

## Logging Strategy

### 1. Structured Logging

```python
# Log format configuration
logging_config = {
    "version": 1,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(timestamp)s %(level)s %(name)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        }
    }
}
```

### 2. Log Levels and Categories

| Category | Level | Description |
|----------|-------|-------------|
| `orchestrator.workflow` | INFO | Workflow state transitions |
| `orchestrator.messaging` | DEBUG | Inter-agent communications |
| `orchestrator.errors` | ERROR | Error conditions and failures |
| `orchestrator.performance` | INFO | Performance metrics and optimizations |
| `orchestrator.audit` | INFO | Audit trail entries |

### 3. Log Aggregation Queries

```sql
-- Find stuck incidents
SELECT incident_id, current_state, timestamp
FROM logs
WHERE message LIKE '%stuck in state%'
  AND timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- Analyze error patterns
SELECT 
  REGEXP_EXTRACT(message, r'error_type: (\w+)') as error_type,
  COUNT(*) as count
FROM logs
WHERE severity = 'ERROR'
  AND timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY error_type
ORDER BY count DESC;
```

## Health Checks

### 1. Liveness Probe

```python
@app.route('/health/live')
async def liveness():
    """Basic liveness check"""
    return {"status": "alive"}, 200
```

### 2. Readiness Probe

```python
@app.route('/health/ready')
async def readiness():
    """Comprehensive readiness check"""
    checks = {
        "firestore": await check_firestore_connection(),
        "pubsub": await check_pubsub_connection(),
        "workflow_engine": workflow_engine.is_healthy(),
        "circuit_breakers": all(
            breaker["state"] != "open" 
            for breaker in circuit_breaker_state.values()
        )
    }
    
    if all(checks.values()):
        return {"status": "ready", "checks": checks}, 200
    else:
        return {"status": "not ready", "checks": checks}, 503
```

### 3. Deep Health Check

```python
@app.route('/health/deep')
async def deep_health():
    """Detailed system health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "active_incidents": len(active_incidents),
            "error_rate": calculate_error_rate(),
            "cache_hit_rate": performance_optimizer.get_cache_hit_rate(),
            "workflow_success_rate": calculate_workflow_success_rate()
        },
        "components": {
            "workflow_engine": workflow_engine.get_health(),
            "audit_logger": audit_logger.is_healthy(),
            "metrics_collector": metrics_collector.is_healthy()
        }
    }
```

## Troubleshooting Guide

### 1. High Incident Backlog

**Symptoms:**
- Increasing pending incidents
- Slow processing rate
- Memory usage growing

**Investigation Steps:**
1. Check concurrent incident limit
2. Review workflow timeouts
3. Analyze bottleneck states
4. Verify agent health

**Resolution:**
```python
# Increase concurrent processing
orchestrator.update_config("max_concurrent_incidents", 20)

# Clear stuck incidents
stuck = await orchestrator.get_stuck_incidents()
for incident_id in stuck:
    await orchestrator.error_recovery.repair_incident(incident_id)
```

### 2. Workflow Timeouts

**Symptoms:**
- Frequent timeout alerts
- Incidents stuck in states
- Escalation notifications

**Investigation Steps:**
1. Identify timeout patterns
2. Check agent response times
3. Review network connectivity
4. Analyze incident complexity

**Resolution:**
```python
# Adjust timeouts based on analysis
orchestrator.update_config("timeouts.analysis", 600)
orchestrator.update_config("timeouts.remediation", 900)
```

### 3. Circuit Breaker Trips

**Symptoms:**
- Repeated failures
- Service unavailable errors
- Blocked operations

**Investigation Steps:**
1. Check error logs
2. Verify external services
3. Review failure patterns
4. Analyze recovery attempts

**Resolution:**
```python
# Manual circuit breaker reset
orchestrator.error_recovery.reset_circuit_breaker("firestore_error")

# Adjust thresholds
orchestrator.update_config("error_recovery.circuit_breaker.failure_threshold", 10)
```

## Performance Tuning

### 1. Cache Optimization

Monitor cache effectiveness:
```sql
SELECT 
  cache_hit_rate,
  cache_size,
  eviction_count
FROM metrics
WHERE metric_type = 'cache_performance'
ORDER BY timestamp DESC
LIMIT 100;
```

Adjust cache settings:
```python
# Increase cache size for better hit rate
orchestrator.update_config("performance.cache.max_size", 2000)

# Adjust TTL based on data freshness needs
orchestrator.update_config("performance.cache.ttl_minutes", 10)
```

### 2. Batch Processing Optimization

Monitor batch performance:
```python
batch_metrics = await orchestrator.performance_optimizer.get_batch_metrics()
print(f"Average batch size: {batch_metrics['avg_batch_size']}")
print(f"Batch commit time: {batch_metrics['avg_commit_time_ms']}ms")
```

Tune batch settings:
```python
# Increase batch size for better throughput
orchestrator.update_config("performance.batching.firestore.max_batch_size", 100)

# Reduce flush interval for lower latency
orchestrator.update_config("performance.batching.firestore.flush_interval_ms", 500)
```

## Capacity Planning

### 1. Resource Requirements

| Metric | Formula | Example |
|--------|---------|---------|
| Memory | `base_memory + (cache_size * avg_incident_size) + (concurrent_incidents * workflow_memory)` | 2GB + (1000 * 10KB) + (20 * 50MB) = 3GB |
| CPU | `base_cpu + (incident_rate * processing_cost)` | 1 core + (10/min * 0.05) = 1.5 cores |
| Storage | `audit_retention_days * daily_incident_count * avg_audit_size` | 30 * 1000 * 1MB = 30GB |

### 2. Scaling Recommendations

```yaml
scaling:
  horizontal:
    min_replicas: 2
    max_replicas: 10
    target_cpu_utilization: 70
    target_memory_utilization: 80
    
  vertical:
    requests:
      cpu: "1"
      memory: "2Gi"
    limits:
      cpu: "4"
      memory: "8Gi"
```

For additional monitoring information, see the [SentinelOps Monitoring Guide](../../monitoring/README.md).

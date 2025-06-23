# SentinelOps Comprehensive Monitoring and Metrics Guide

## Overview

This guide provides a complete reference for monitoring the SentinelOps multi-agent security system, including ADK telemetry, Cloud Monitoring integration, custom dashboards, alerts, performance monitoring, and cost tracking.

## Table of Contents

1. [ADK Telemetry and Metrics](#adk-telemetry-and-metrics)
2. [Cloud Monitoring Integration](#cloud-monitoring-integration)
3. [Custom Dashboards](#custom-dashboards)
4. [Alert Configuration](#alert-configuration)
5. [Performance Monitoring](#performance-monitoring)
6. [Cost Tracking](#cost-tracking)
7. [Troubleshooting with Metrics](#troubleshooting-with-metrics)
8. [Disaster Recovery Monitoring](#disaster-recovery-monitoring)

## ADK Telemetry and Metrics

### ADK-Specific Metrics

The Google Agent Development Kit (ADK) provides built-in telemetry for all agents:

```python
# Enable ADK telemetry in agent configuration
ADK_CONFIG = {
    "telemetry": {
        "enabled": True,
        "export_interval": 60,  # seconds
        "batch_size": 100,
        "custom_metrics_prefix": "sentinelops.adk"
    },
    "monitoring": {
        "trace_enabled": True,
        "span_processors": ["batch"],
        "metric_exporters": ["cloud_monitoring"]
    }
}
```

### Key ADK Metrics

| Metric Name | Type | Description | Unit |
|------------|------|-------------|------|
| `adk.agent.execution_time` | Histogram | Time taken for agent execution | ms |
| `adk.agent.memory_usage` | Gauge | Current memory usage by agent | MB |
| `adk.agent.active_sessions` | Gauge | Number of active ADK sessions | count |
| `adk.tool.execution_count` | Counter | Number of tool executions | count |
| `adk.tool.failure_rate` | Gauge | Tool execution failure rate | percentage |
| `adk.llm.token_usage` | Counter | LLM token consumption | tokens |
| `adk.llm.response_time` | Histogram | LLM response latency | ms |
| `adk.workflow.transitions` | Counter | Workflow state transitions | count |

### Accessing ADK Metrics

```bash
# View ADK metrics in Cloud Monitoring
gcloud monitoring dashboards list --filter="displayName:ADK"

# Query specific ADK metrics
gcloud monitoring time-series list \
  --filter='metric.type="custom.googleapis.com/adk/agent/execution_time"' \
  --interval-start-time='2025-01-01T00:00:00Z'
```

## Cloud Monitoring Integration

### Setting Up Cloud Monitoring

1. **Enable Required APIs**:
```bash
gcloud services enable monitoring.googleapis.com
gcloud services enable cloudtrace.googleapis.com
gcloud services enable logging.googleapis.com
```

2. **Configure Metric Descriptors**:
```python
from google.cloud import monitoring_v3

client = monitoring_v3.MetricServiceClient()
project_name = f"projects/{project_id}"

# Create custom metric for incident processing
descriptor = monitoring_v3.MetricDescriptor(
    type="custom.googleapis.com/sentinelops/incidents_processed",
    metric_kind=monitoring_v3.MetricDescriptor.MetricKind.CUMULATIVE,
    value_type=monitoring_v3.MetricDescriptor.ValueType.INT64,
    description="Number of security incidents processed",
    display_name="Incidents Processed",
    labels=[
        monitoring_v3.LabelDescriptor(
            key="severity",
            value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
        ),
        monitoring_v3.LabelDescriptor(
            key="agent",
            value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
        ),
    ],
)

client.create_metric_descriptor(name=project_name, metric_descriptor=descriptor)
```

3. **Export Metrics from Agents**:
```python
# In your agent code
async def export_metrics(self):
    """Export metrics to Cloud Monitoring"""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{self.project_id}"

    # Create time series data
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/sentinelops/incidents_processed"
    series.metric.labels["severity"] = incident.severity
    series.metric.labels["agent"] = self.agent_name

    # Add data point
    now = time.time()
    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": int(now), "nanos": int((now - int(now)) * 10**9)}}
    )
    point = monitoring_v3.Point(
        {"interval": interval, "value": {"int64_value": self.incidents_processed}}
    )
    series.points = [point]

    # Write time series
    client.create_time_series(name=project_name, time_series=[series])
```

### Integration with Prometheus

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 30s
  external_labels:
    monitor: 'sentinelops'
    environment: 'production'

scrape_configs:
  - job_name: 'detection-agent'
    static_configs:
      - targets: ['detection-agent:8080']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'detection-agent'

  - job_name: 'orchestrator-agent'
    static_configs:
      - targets: ['orchestrator-agent:8080']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'orchestrator-agent'

# Export to Cloud Monitoring
remote_write:
  - url: "https://monitoring.googleapis.com/v1/projects/PROJECT_ID/location/global/prometheus/api/v1/write"
    authorization:
      credentials_file: "/etc/prometheus/key.json"
```

## Custom Dashboards

### 1. System Overview Dashboard

```json
{
  "displayName": "SentinelOps System Overview",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 4,
        "height": 4,
        "widget": {
          "title": "Active Incidents",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"custom.googleapis.com/sentinelops/active_incidents\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            },
            "gaugeView": {
              "lowerBound": 0,
              "upperBound": 100
            }
          }
        }
      },
      {
        "xPos": 4,
        "width": 4,
        "height": 4,
        "widget": {
          "title": "Agent Health Status",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"custom.googleapis.com/sentinelops/agent_health\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_MEAN",
                  "groupByFields": ["metric.label.agent_name"]
                }
              }
            }
          }
        }
      },
      {
        "xPos": 8,
        "width": 4,
        "height": 4,
        "widget": {
          "title": "System Error Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/sentinelops/error_rate\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              },
              "plotType": "LINE"
            }]
          }
        }
      }
    ]
  }
}
```

### 2. ADK Performance Dashboard

```json
{
  "displayName": "ADK Performance Metrics",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "ADK Agent Execution Time",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/adk/agent/execution_time\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_DELTA",
                    "groupByFields": ["resource.label.service_name"]
                  }
                }
              },
              "plotType": "STACKED_AREA"
            }]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "LLM Token Usage by Agent",
          "pieChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/adk/llm/token_usage\"",
                  "aggregation": {
                    "alignmentPeriod": "3600s",
                    "perSeriesAligner": "ALIGN_SUM",
                    "groupByFields": ["metric.label.agent_name"]
                  }
                }
              }
            }]
          }
        }
      },
      {
        "yPos": 4,
        "width": 12,
        "height": 4,
        "widget": {
          "title": "ADK Memory Usage Trend",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/adk/agent/memory_usage\"",
                  "aggregation": {
                    "alignmentPeriod": "300s",
                    "perSeriesAligner": "ALIGN_MEAN",
                    "groupByFields": ["resource.label.service_name"]
                  }
                }
              },
              "plotType": "LINE"
            }],
            "thresholds": [{
              "value": 2048,
              "label": "Memory Limit"
            }]
          }
        }
      }
    ]
  }
}
```

### 3. Incident Response Dashboard

```json
{
  "displayName": "Incident Response Metrics",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Incident Resolution Time Distribution",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/sentinelops/incident_resolution_time\"",
                  "aggregation": {
                    "alignmentPeriod": "300s",
                    "perSeriesAligner": "ALIGN_DELTA",
                    "groupByFields": ["metric.label.severity"]
                  }
                }
              },
              "plotType": "HEATMAP"
            }]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Workflow State Transitions",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/adk/workflow/transitions\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE",
                    "groupByFields": ["metric.label.from_state", "metric.label.to_state"]
                  }
                }
              },
              "plotType": "STACKED_BAR"
            }]
          }
        }
      }
    ]
  }
}
```

## Alert Configuration

### Critical Alerts

```yaml
# critical-alerts.yaml
alertPolicy:
  - displayName: "SentinelOps - Agent Down"
    conditions:
      - displayName: "Agent Unavailable"
        conditionThreshold:
          filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"'
          aggregations:
            - alignmentPeriod: "60s"
              perSeriesAligner: "ALIGN_RATE"
          comparison: "COMPARISON_LT"
          thresholdValue: 0.1
          duration: "180s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/PAGERDUTY_CHANNEL"
    alertStrategy:
      autoClose: "1800s"

  - displayName: "SentinelOps - High Error Rate"
    conditions:
      - displayName: "Error Rate > 5%"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/sentinelops/error_rate"'
          aggregations:
            - alignmentPeriod: "300s"
              perSeriesAligner: "ALIGN_MEAN"
          comparison: "COMPARISON_GT"
          thresholdValue: 0.05
          duration: "300s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/SLACK_CRITICAL"
      - "projects/PROJECT_ID/notificationChannels/EMAIL_ONCALL"

  - displayName: "ADK - Circuit Breaker Open"
    conditions:
      - displayName: "Circuit Breaker Triggered"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/adk/circuit_breaker/state" AND metric.label.state="open"'
          aggregations:
            - alignmentPeriod: "60s"
              perSeriesAligner: "ALIGN_MAX"
          comparison: "COMPARISON_GT"
          thresholdValue: 0
          duration: "60s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/SLACK_CRITICAL"
```

### Warning Alerts

```yaml
# warning-alerts.yaml
alertPolicy:
  - displayName: "SentinelOps - Incident Backlog"
    conditions:
      - displayName: "Pending Incidents > 50"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/sentinelops/pending_incidents"'
          aggregations:
            - alignmentPeriod: "300s"
              perSeriesAligner: "ALIGN_MEAN"
          comparison: "COMPARISON_GT"
          thresholdValue: 50
          duration: "600s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/SLACK_WARNINGS"

  - displayName: "ADK - High Memory Usage"
    conditions:
      - displayName: "Memory > 80%"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/adk/agent/memory_usage"'
          aggregations:
            - alignmentPeriod: "300s"
              perSeriesAligner: "ALIGN_MEAN"
          comparison: "COMPARISON_GT"
          thresholdValue: 1638  # 80% of 2048MB
          duration: "900s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/SLACK_WARNINGS"

  - displayName: "SentinelOps - Slow Workflow Execution"
    conditions:
      - displayName: "P95 Latency > 30 minutes"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/sentinelops/workflow_duration"'
          aggregations:
            - alignmentPeriod: "900s"
              perSeriesAligner: "ALIGN_PERCENTILE_95"
          comparison: "COMPARISON_GT"
          thresholdValue: 1800
          duration: "900s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/EMAIL_TEAM"
```

### Info Alerts

```yaml
# info-alerts.yaml
alertPolicy:
  - displayName: "ADK - Token Usage Spike"
    conditions:
      - displayName: "Token usage increased by 200%"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/adk/llm/token_usage"'
          aggregations:
            - alignmentPeriod: "3600s"
              perSeriesAligner: "ALIGN_RATE"
          comparison: "COMPARISON_GT"
          thresholdValue: 10000  # tokens per hour
          duration: "3600s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/SLACK_INFO"

  - displayName: "SentinelOps - Configuration Change"
    conditions:
      - displayName: "Config update detected"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/sentinelops/config_changes"'
          aggregations:
            - alignmentPeriod: "60s"
              perSeriesAligner: "ALIGN_SUM"
          comparison: "COMPARISON_GT"
          thresholdValue: 0
          duration: "60s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/AUDIT_CHANNEL"
```

## Performance Monitoring

### Key Performance Indicators (KPIs)

| Category | Metric | Target | Warning | Critical |
|----------|--------|--------|---------|----------|
| **System Health** | Uptime | >99.9% | <99.5% | <99% |
| | Error Rate | <1% | >2% | >5% |
| | Response Time (P95) | <1s | >2s | >5s |
| **Incident Processing** | Processing Rate | >10/min | <5/min | <2/min |
| | Resolution Time | <10min | >20min | >30min |
| | Success Rate | >95% | <90% | <80% |
| **ADK Performance** | Agent Execution Time | <500ms | >1s | >2s |
| | Memory Usage | <70% | >80% | >90% |
| | Token Usage | <100k/day | >150k/day | >200k/day |
| **Workflow Efficiency** | Completion Rate | >98% | <95% | <90% |
| | State Transition Time | <30s | >60s | >120s |
| | Timeout Rate | <2% | >5% | >10% |

### Performance Optimization Metrics

```python
# Track cache performance
cache_metrics = {
    "hit_rate": cache_hits / (cache_hits + cache_misses),
    "eviction_rate": evictions / total_operations,
    "avg_latency": sum(latencies) / len(latencies),
    "memory_usage": cache.memory_bytes / cache.max_memory_bytes
}

# Monitor batch processing efficiency
batch_metrics = {
    "avg_batch_size": sum(batch_sizes) / len(batch_sizes),
    "processing_time": batch_end_time - batch_start_time,
    "throughput": items_processed / processing_time,
    "error_rate": failed_items / total_items
}

# Track resource utilization
resource_metrics = {
    "cpu_usage": psutil.cpu_percent(interval=1),
    "memory_usage": psutil.virtual_memory().percent,
    "disk_io": psutil.disk_io_counters(),
    "network_io": psutil.net_io_counters()
}
```

### Performance Tuning Based on Metrics

```python
# Auto-tune based on metrics
async def auto_tune_performance(self):
    """Automatically adjust performance parameters based on metrics"""

    # Cache tuning
    if self.cache_metrics["hit_rate"] < 0.8:
        self.config["cache"]["ttl"] *= 1.5  # Increase TTL
        self.config["cache"]["max_size"] = min(
            self.config["cache"]["max_size"] * 1.2,
            self.MAX_CACHE_SIZE
        )

    # Batch size tuning
    if self.batch_metrics["error_rate"] > 0.05:
        self.config["batch"]["size"] = max(
            self.config["batch"]["size"] * 0.8,
            self.MIN_BATCH_SIZE
        )
    elif self.batch_metrics["processing_time"] > 1000:  # 1 second
        self.config["batch"]["size"] = max(
            self.config["batch"]["size"] * 0.9,
            self.MIN_BATCH_SIZE
        )

    # Concurrency tuning
    if self.resource_metrics["cpu_usage"] < 50:
        self.config["concurrency"]["max_workers"] = min(
            self.config["concurrency"]["max_workers"] + 1,
            self.MAX_WORKERS
        )
```

## Cost Tracking

### Cost Monitoring Metrics

```python
# Define cost tracking metrics
cost_metrics = {
    "cloud_run": {
        "cpu_seconds": "run.googleapis.com/billable_cpu_allocation_time",
        "memory_gb_seconds": "run.googleapis.com/billable_memory_allocation_time",
        "requests": "run.googleapis.com/request_count"
    },
    "firestore": {
        "reads": "firestore.googleapis.com/document/read_count",
        "writes": "firestore.googleapis.com/document/write_count",
        "deletes": "firestore.googleapis.com/document/delete_count"
    },
    "bigquery": {
        "bytes_scanned": "bigquery.googleapis.com/storage/table/uploaded_bytes",
        "slots_used": "bigquery.googleapis.com/slots/total_allocated"
    },
    "gemini_api": {
        "tokens_used": "custom.googleapis.com/adk/llm/token_usage"
    }
}
```

### Cost Dashboard Configuration

```json
{
  "displayName": "SentinelOps Cost Tracking",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 4,
        "height": 4,
        "widget": {
          "title": "Daily Estimated Cost",
          "scorecard": {
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"custom.googleapis.com/sentinelops/daily_cost_estimate\"",
                "aggregation": {
                  "alignmentPeriod": "86400s",
                  "perSeriesAligner": "ALIGN_SUM"
                }
              }
            }
          }
        }
      },
      {
        "xPos": 4,
        "width": 8,
        "height": 4,
        "widget": {
          "title": "Cost by Service",
          "pieChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/sentinelops/service_cost\"",
                  "aggregation": {
                    "alignmentPeriod": "86400s",
                    "perSeriesAligner": "ALIGN_SUM",
                    "groupByFields": ["metric.label.service_name"]
                  }
                }
              }
            }]
          }
        }
      },
      {
        "yPos": 4,
        "width": 12,
        "height": 4,
        "widget": {
          "title": "Cost Trend (30 days)",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"custom.googleapis.com/sentinelops/daily_cost_estimate\"",
                  "aggregation": {
                    "alignmentPeriod": "86400s",
                    "perSeriesAligner": "ALIGN_SUM"
                  }
                }
              },
              "plotType": "LINE"
            }]
          }
        }
      }
    ]
  }
}
```

### Cost Optimization Alerts

```yaml
alertPolicy:
  - displayName: "Cost - Daily Budget Exceeded"
    conditions:
      - displayName: "Daily cost > $100"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/sentinelops/daily_cost_estimate"'
          aggregations:
            - alignmentPeriod: "86400s"
              perSeriesAligner: "ALIGN_SUM"
          comparison: "COMPARISON_GT"
          thresholdValue: 100
          duration: "300s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/FINANCE_TEAM"

  - displayName: "Cost - Unusual Token Usage"
    conditions:
      - displayName: "Token usage spike"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/adk/llm/token_usage"'
          aggregations:
            - alignmentPeriod: "3600s"
              perSeriesAligner: "ALIGN_RATE"
          comparison: "COMPARISON_GT"
          thresholdValue: 50000  # tokens per hour
          duration: "3600s"
```

## Troubleshooting with Metrics

### Common Issues and Metric Patterns

| Issue | Metric Pattern | Investigation Steps |
|-------|----------------|-------------------|
| **Slow Processing** | High `execution_time`, normal `error_rate` | 1. Check `memory_usage`<br>2. Review `batch_size`<br>3. Analyze `cache_hit_rate` |
| **High Error Rate** | Spike in `error_rate`, increased `circuit_breaker` trips | 1. Check logs for error patterns<br>2. Verify external service health<br>3. Review recent deployments |
| **Memory Leaks** | Gradually increasing `memory_usage` | 1. Check `active_sessions`<br>2. Review object lifecycle<br>3. Analyze heap dumps |
| **API Throttling** | Increased `response_time`, 429 errors | 1. Check `token_usage`<br>2. Review rate limits<br>3. Implement backoff |
| **Stuck Workflows** | High `state_transition_time`, increased `timeout_rate` | 1. Check specific state metrics<br>2. Review agent health<br>3. Analyze deadlocks |

### Metric-Based Diagnostics

```python
async def diagnose_performance_issue(self):
    """Diagnose performance issues using metrics"""
    diagnostics = {}

    # Check CPU bottleneck
    cpu_usage = await self.get_metric("cpu_usage", period="5m")
    if cpu_usage.mean() > 80:
        diagnostics["cpu_bottleneck"] = {
            "severity": "high",
            "recommendation": "Scale up CPU or optimize compute-intensive operations"
        }

    # Check memory pressure
    memory_usage = await self.get_metric("memory_usage", period="5m")
    if memory_usage.mean() > 85:
        diagnostics["memory_pressure"] = {
            "severity": "high",
            "recommendation": "Increase memory limit or optimize memory usage"
        }

    # Check cache effectiveness
    cache_hit_rate = await self.get_metric("cache_hit_rate", period="1h")
    if cache_hit_rate.mean() < 70:
        diagnostics["cache_ineffective"] = {
            "severity": "medium",
            "recommendation": "Increase cache size or TTL"
        }

    # Check external dependencies
    api_latency = await self.get_metric("external_api_latency", period="5m")
    if api_latency.p95() > 2000:  # 2 seconds
        diagnostics["slow_dependencies"] = {
            "severity": "high",
            "recommendation": "Review API performance or implement caching"
        }

    return diagnostics
```

## Disaster Recovery Monitoring

### Backup Monitoring

```yaml
# Monitor backup completion
alertPolicy:
  - displayName: "DR - Backup Failed"
    conditions:
      - displayName: "Backup not completed"
        conditionThreshold:
          filter: 'metric.type="custom.googleapis.com/sentinelops/backup_success" AND metric.label.backup_type="firestore"'
          aggregations:
            - alignmentPeriod: "86400s"
              perSeriesAligner: "ALIGN_MIN"
          comparison: "COMPARISON_LT"
          thresholdValue: 1
          duration: "300s"
    notificationChannels:
      - "projects/PROJECT_ID/notificationChannels/DR_TEAM"
```

### Recovery Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| `backup_success_rate` | Percentage of successful backups | >99% |
| `backup_duration` | Time to complete backup | <30min |
| `recovery_time_objective` | Time to restore from backup | <1hr |
| `recovery_point_objective` | Maximum data loss window | <15min |
| `dr_test_success_rate` | DR drill success rate | 100% |

### Health Check Monitoring

```python
# Comprehensive health check with metrics
async def deep_health_check(self):
    """Perform deep health check and export metrics"""
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }

    # Check Firestore
    try:
        await self.firestore_client.collection("_health").document("check").set(
            {"timestamp": firestore.SERVER_TIMESTAMP}
        )
        health_status["components"]["firestore"] = "healthy"
        await self.export_metric("component_health", 1, {"component": "firestore"})
    except Exception as e:
        health_status["components"]["firestore"] = f"unhealthy: {str(e)}"
        await self.export_metric("component_health", 0, {"component": "firestore"})

    # Check BigQuery
    try:
        query = "SELECT 1"
        self.bigquery_client.query(query).result()
        health_status["components"]["bigquery"] = "healthy"
        await self.export_metric("component_health", 1, {"component": "bigquery"})
    except Exception as e:
        health_status["components"]["bigquery"] = f"unhealthy: {str(e)}"
        await self.export_metric("component_health", 0, {"component": "bigquery"})

    # Check ADK components
    health_status["components"]["adk"] = {
        "active_sessions": len(self.adk_sessions),
        "circuit_breakers": self.get_circuit_breaker_status(),
        "memory_usage": self.get_memory_usage(),
        "cache_stats": self.get_cache_stats()
    }

    return health_status
```

## Monitoring Best Practices

### 1. Metric Naming Convention

```python
# Use consistent naming for custom metrics
METRIC_PREFIX = "custom.googleapis.com/sentinelops"

METRIC_NAMES = {
    # System metrics
    f"{METRIC_PREFIX}/system/uptime",
    f"{METRIC_PREFIX}/system/error_rate",
    f"{METRIC_PREFIX}/system/request_count",

    # Agent metrics
    f"{METRIC_PREFIX}/agent/execution_time",
    f"{METRIC_PREFIX}/agent/success_rate",
    f"{METRIC_PREFIX}/agent/active_instances",

    # Workflow metrics
    f"{METRIC_PREFIX}/workflow/completion_time",
    f"{METRIC_PREFIX}/workflow/state_transitions",
    f"{METRIC_PREFIX}/workflow/timeout_count",

    # Cost metrics
    f"{METRIC_PREFIX}/cost/daily_estimate",
    f"{METRIC_PREFIX}/cost/by_service",
    f"{METRIC_PREFIX}/cost/token_usage"
}
```

### 2. Metric Collection Guidelines

- **Sampling Rate**: Use appropriate sampling for high-frequency metrics
- **Aggregation**: Pre-aggregate where possible to reduce storage
- **Labels**: Use consistent label names across metrics
- **Cardinality**: Limit label values to prevent metric explosion

### 3. Dashboard Organization

- **Overview Dashboard**: System health at a glance
- **Service Dashboards**: One per agent/service
- **Performance Dashboard**: Latency, throughput, errors
- **Cost Dashboard**: Budget tracking and optimization
- **Incident Dashboard**: Active incidents and resolution metrics

### 4. Alert Fatigue Prevention

- **Deduplication**: Group related alerts
- **Severity Levels**: Use appropriate severity (Critical/Warning/Info)
- **Auto-resolution**: Configure auto-close for transient issues
- **Maintenance Windows**: Suppress alerts during planned maintenance

## Monitoring Scripts and Tools

### Quick Status Check

```bash
#!/bin/bash
# check_sentinelops_health.sh

echo "SentinelOps Health Check - $(date)"
echo "================================"

# Check agent health endpoints
AGENTS=("detection" "analysis" "remediation" "communication" "orchestrator")
for agent in "${AGENTS[@]}"; do
    URL="https://${agent}-agent-xxxxx.run.app/health"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" $URL)
    if [ $STATUS -eq 200 ]; then
        echo "✓ ${agent^} Agent: Healthy"
    else
        echo "✗ ${agent^} Agent: Unhealthy (HTTP $STATUS)"
    fi
done

# Check key metrics
echo -e "\nKey Metrics:"
gcloud monitoring time-series list \
    --filter='metric.type=~"custom.googleapis.com/sentinelops/.*"' \
    --format="table(metric.type, points[0].value.int64Value)" \
    --limit=10

# Check active alerts
echo -e "\nActive Alerts:"
gcloud alpha monitoring policies list \
    --filter="enabled=true" \
    --format="table(displayName, conditions[0].displayName)"
```

### Metric Export Script

```python
#!/usr/bin/env python3
# export_metrics.py

import pandas as pd
from google.cloud import monitoring_v3
from datetime import datetime, timedelta

def export_metrics_to_csv(project_id, metric_type, hours=24):
    """Export metrics to CSV for analysis"""
    client = monitoring_v3.MetricServiceClient()

    # Query time range
    interval = monitoring_v3.TimeInterval(
        {
            "end_time": datetime.utcnow(),
            "start_time": datetime.utcnow() - timedelta(hours=hours),
        }
    )

    # List time series
    results = client.list_time_series(
        request={
            "name": f"projects/{project_id}",
            "filter": f'metric.type="{metric_type}"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    # Convert to DataFrame
    data = []
    for result in results:
        for point in result.points:
            data.append({
                "timestamp": point.interval.end_time,
                "value": point.value.int64_value or point.value.double_value,
                **result.metric.labels
            })

    df = pd.DataFrame(data)
    df.to_csv(f"{metric_type.replace('/', '_')}.csv", index=False)
    print(f"Exported {len(df)} data points to CSV")

if __name__ == "__main__":
    export_metrics_to_csv(
        "your-project-id",
        "custom.googleapis.com/sentinelops/incidents_processed",
        hours=168  # Last week
    )
```

## Next Steps

1. **Set up monitoring infrastructure**:
   - Deploy Prometheus and Grafana for advanced visualization
   - Configure metric retention policies
   - Set up metric archival for long-term analysis

2. **Implement custom metrics**:
   - Add application-specific metrics
   - Create business KPI dashboards
   - Set up SLI/SLO tracking

3. **Optimize based on metrics**:
   - Regular performance reviews
   - Cost optimization workshops
   - Capacity planning sessions

4. **Training and documentation**:
   - Team training on dashboard usage
   - Runbook updates based on metric patterns
   - Regular metric review meetings

For additional information, refer to:
- [ADK Troubleshooting Guide](./adk-troubleshooting.md)
- [Disaster Recovery Runbook](./disaster-recovery-runbook.md)
- [Performance Optimization Guide](../02-architecture/agents/detection-agent-performance.md)

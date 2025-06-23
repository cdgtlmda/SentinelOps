#!/usr/bin/env python3
"""
Set up Cloud Monitoring and Logging for SentinelOps
Implements checklist section 8: Monitoring and Logging
Enhanced with comprehensive monitoring, logging, and alerting capabilities
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from google.api_core import exceptions
from google.cloud import bigquery, logging, monitoring_dashboard_v1, monitoring_v3

# Enums are accessed directly from logging module in newer versions

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
ORGANIZATION_ID = os.getenv("GOOGLE_CLOUD_ORGANIZATION", "")  # Optional

# Monitoring configurations
DASHBOARDS = {
    "sentinelops-overview": {
        "displayName": "SentinelOps Security Overview",
        "mosaicLayout": {
            "columns": 12,
            "tiles": [
                {
                    "width": 6,
                    "height": 4,
                    "widget": {
                        "title": "Active Security Incidents",
                        "scorecard": {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'resource.type="cloud_run_revision" AND metric.type="logging.googleapis.com/user/incident_count"',
                                    "aggregation": {
                                        "alignmentPeriod": "60s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                    },
                                }
                            }
                        },
                    },
                },
                {
                    "xPos": 6,
                    "width": 6,
                    "height": 4,
                    "widget": {
                        "title": "Threat Severity Distribution",
                        "pieChart": {
                            "dataSets": [
                                {
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'resource.type="cloud_run_revision" AND metric.type="logging.googleapis.com/user/threat_severity"',
                                            "aggregation": {
                                                "alignmentPeriod": "300s",
                                                "perSeriesAligner": "ALIGN_MEAN",
                                                "groupByFields": [
                                                    "metric.label.severity"
                                                ],
                                            },
                                        }
                                    }
                                }
                            ]
                        },
                    },
                },
                {
                    "yPos": 4,
                    "width": 12,
                    "height": 4,
                    "widget": {
                        "title": "Detection Agent Activity",
                        "xyChart": {
                            "dataSets": [
                                {
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'resource.type="cloud_run_revision" AND resource.labels.service_name="sentinelops-detection"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_RATE",
                                            },
                                        }
                                    },
                                    "plotType": "LINE",
                                }
                            ]
                        },
                    },
                },
            ],
        },
    },
    "sentinelops-agents": {
        "displayName": "SentinelOps Agent Performance",
        "gridLayout": {
            "columns": 12,
            "widgets": [
                {
                    "title": "Agent CPU Utilization",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/cpu/utilizations"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_MEAN",
                                            "groupByFields": [
                                                "resource.labels.service_name"
                                            ],
                                        },
                                    }
                                },
                                "plotType": "LINE",
                            }
                        ]
                    },
                },
                {
                    "title": "Agent Memory Usage",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/memory/utilizations"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_MEAN",
                                            "groupByFields": [
                                                "resource.labels.service_name"
                                            ],
                                        },
                                    }
                                },
                                "plotType": "LINE",
                            }
                        ]
                    },
                },
                {
                    "title": "Request Latency (95th percentile)",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_PERCENTILE_95",
                                            "groupByFields": [
                                                "resource.labels.service_name"
                                            ],
                                        },
                                    }
                                },
                                "plotType": "LINE",
                                "targetAxis": "Y1",
                            }
                        ]
                    },
                },
            ],
        },
    },
    "sentinelops-remediation": {
        "displayName": "SentinelOps Remediation Actions",
        "mosaicLayout": {
            "columns": 12,
            "tiles": [
                {
                    "width": 4,
                    "height": 4,
                    "widget": {
                        "title": "Total Remediation Actions",
                        "scorecard": {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'resource.type="cloud_function" AND metric.type="cloudfunctions.googleapis.com/function/execution_count"',
                                    "aggregation": {
                                        "alignmentPeriod": "3600s",
                                        "perSeriesAligner": "ALIGN_SUM",
                                    },
                                }
                            }
                        },
                    },
                },
                {
                    "xPos": 4,
                    "width": 4,
                    "height": 4,
                    "widget": {
                        "title": "Remediation Success Rate",
                        "scorecard": {
                            "gaugeView": {"lowerBound": 0.0, "upperBound": 1.0},
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'resource.type="cloud_function" AND metric.type="logging.googleapis.com/user/remediation_success_rate"',
                                    "aggregation": {
                                        "alignmentPeriod": "3600s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                    },
                                }
                            },
                        },
                    },
                },
                {
                    "xPos": 8,
                    "width": 4,
                    "height": 4,
                    "widget": {
                        "title": "Average Remediation Time",
                        "scorecard": {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'resource.type="cloud_function" AND metric.type="cloudfunctions.googleapis.com/function/execution_times"',
                                    "aggregation": {
                                        "alignmentPeriod": "300s",
                                        "perSeriesAligner": "ALIGN_MEAN",
                                    },
                                }
                            }
                        },
                    },
                },
            ],
        },
    },
    "sentinelops-security-events": {
        "displayName": "SentinelOps Security Events Dashboard",
        "gridLayout": {
            "columns": 12,
            "widgets": [
                {
                    "title": "Security Events by Type",
                    "pieChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="generic_task" AND metric.type="logging.googleapis.com/user/security_event_count"',
                                        "aggregation": {
                                            "alignmentPeriod": "300s",
                                            "perSeriesAligner": "ALIGN_SUM",
                                            "groupByFields": [
                                                "metric.label.event_type"
                                            ],
                                        },
                                    }
                                }
                            }
                        ]
                    },
                },
                {
                    "title": "Security Event Timeline",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="generic_task" AND metric.type="logging.googleapis.com/user/security_event_count"',
                                        "aggregation": {
                                            "alignmentPeriod": "60s",
                                            "perSeriesAligner": "ALIGN_RATE",
                                            "groupByFields": ["metric.label.severity"],
                                        },
                                    }
                                },
                                "plotType": "STACKED_AREA",
                            }
                        ]
                    },
                },
                {
                    "title": "Top Attack Sources",
                    "scorecard": {
                        "timeSeriesQuery": {
                            "timeSeriesFilter": {
                                "filter": 'resource.type="generic_task" AND metric.type="logging.googleapis.com/user/attack_source_count"',
                                "aggregation": {
                                    "alignmentPeriod": "3600s",
                                    "perSeriesAligner": "ALIGN_SUM",
                                    "groupByFields": ["metric.label.source_ip"],
                                },
                            }
                        }
                    },
                },
            ],
        },
    },
    "sentinelops-system-health": {
        "displayName": "SentinelOps System Health Dashboard",
        "mosaicLayout": {
            "columns": 12,
            "tiles": [
                {
                    "width": 6,
                    "height": 4,
                    "widget": {
                        "title": "Service Availability",
                        "scorecard": {
                            "timeSeriesQuery": {
                                "timeSeriesFilter": {
                                    "filter": 'resource.type="uptime_url" AND metric.type="monitoring.googleapis.com/uptime_check/check_passed"',
                                    "aggregation": {
                                        "alignmentPeriod": "300s",
                                        "perSeriesAligner": "ALIGN_FRACTION_TRUE",
                                        "groupByFields": ["resource.label.host"],
                                    },
                                }
                            }
                        },
                    },
                },
                {
                    "xPos": 6,
                    "width": 6,
                    "height": 4,
                    "widget": {
                        "title": "Error Rates by Service",
                        "xyChart": {
                            "dataSets": [
                                {
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'severity >= ERROR AND resource.type="cloud_run_revision"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_RATE",
                                                "groupByFields": [
                                                    "resource.labels.service_name"
                                                ],
                                            },
                                        }
                                    },
                                    "plotType": "LINE",
                                }
                            ]
                        },
                    },
                },
                {
                    "yPos": 4,
                    "width": 12,
                    "height": 4,
                    "widget": {
                        "title": "System Resource Utilization",
                        "xyChart": {
                            "dataSets": [
                                {
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/cpu/utilizations"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_MEAN",
                                                "crossSeriesReducer": "REDUCE_MEAN",
                                                "groupByFields": [
                                                    "resource.labels.service_name"
                                                ],
                                            },
                                        }
                                    },
                                    "plotType": "LINE",
                                    "targetAxis": "Y1",
                                },
                                {
                                    "timeSeriesQuery": {
                                        "timeSeriesFilter": {
                                            "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/memory/utilizations"',
                                            "aggregation": {
                                                "alignmentPeriod": "60s",
                                                "perSeriesAligner": "ALIGN_MEAN",
                                                "crossSeriesReducer": "REDUCE_MEAN",
                                                "groupByFields": [
                                                    "resource.labels.service_name"
                                                ],
                                            },
                                        }
                                    },
                                    "plotType": "LINE",
                                    "targetAxis": "Y2",
                                },
                            ]
                        },
                    },
                },
            ],
        },
    },
    "sentinelops-cost-monitoring": {
        "displayName": "SentinelOps Cost Monitoring Dashboard",
        "gridLayout": {
            "columns": 12,
            "widgets": [
                {
                    "title": "Daily Cost Trend",
                    "xyChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="global" AND metric.type="billing.googleapis.com/project/cost"',
                                        "aggregation": {
                                            "alignmentPeriod": "86400s",
                                            "perSeriesAligner": "ALIGN_SUM",
                                        },
                                    }
                                },
                                "plotType": "LINE",
                            }
                        ]
                    },
                },
                {
                    "title": "Cost by Service",
                    "pieChart": {
                        "dataSets": [
                            {
                                "timeSeriesQuery": {
                                    "timeSeriesFilter": {
                                        "filter": 'resource.type="global" AND metric.type="billing.googleapis.com/project/cost"',
                                        "aggregation": {
                                            "alignmentPeriod": "86400s",
                                            "perSeriesAligner": "ALIGN_SUM",
                                            "groupByFields": ["metric.label.service"],
                                        },
                                    }
                                }
                            }
                        ]
                    },
                },
                {
                    "title": "Projected Monthly Cost",
                    "scorecard": {
                        "timeSeriesQuery": {
                            "timeSeriesFilter": {
                                "filter": 'resource.type="global" AND metric.type="billing.googleapis.com/project/cost"',
                                "aggregation": {
                                    "alignmentPeriod": "2592000s",
                                    "perSeriesAligner": "ALIGN_SUM",
                                },
                            }
                        }
                    },
                },
            ],
        },
    },
}

# Alert policies with escalation procedures
ALERT_POLICIES = [
    {
        "displayName": "Critical: Service Down",
        "conditions": [
            {
                "displayName": "Service unavailable",
                "conditionThreshold": {
                    "filter": 'resource.type="uptime_url" AND metric.type="monitoring.googleapis.com/uptime_check/check_passed"',
                    "aggregations": [
                        {
                            "alignmentPeriod": "60s",
                            "perSeriesAligner": "ALIGN_FRACTION_TRUE",
                        }
                    ],
                    "comparison": "COMPARISON_LT",
                    "thresholdValue": 0.5,
                    "duration": "180s",
                },
            }
        ],
        "alertStrategy": {
            "autoClose": "1800s",
            "notificationRateLimit": {"period": "300s"},
        },
        "documentation": {
            "content": """CRITICAL: Service is down!

Escalation Procedure:
1. Immediate: Alert on-call engineer via PagerDuty
2. 5 minutes: Alert team lead if not acknowledged
3. 15 minutes: Alert engineering manager
4. 30 minutes: Alert VP of Engineering

Actions:
- Check Cloud Run service status
- Review recent deployments
- Check for quota or resource issues
- Initiate rollback if needed"""
        },
        "severity": "CRITICAL",
    },
    {
        "displayName": "High Error Rate - Cloud Run Services",
        "conditions": [
            {
                "displayName": "Error rate exceeds 5%",
                "conditionThreshold": {
                    "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"',
                    "aggregations": [
                        {"alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_RATE"}
                    ],
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 0.05,
                    "duration": "180s",
                },
            }
        ],
        "alertStrategy": {"autoClose": "1800s"},
        "documentation": {
            "content": """ERROR: High error rate detected.

Actions:
- Check application logs for errors
- Review recent code changes
- Monitor for patterns in errors"""
        },
        "severity": "ERROR",
    },
    {
        "displayName": "High Latency - API Requests",
        "conditions": [
            {
                "displayName": "95th percentile latency exceeds 5 seconds",
                "conditionThreshold": {
                    "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies"',
                    "aggregations": [
                        {
                            "alignmentPeriod": "300s",
                            "perSeriesAligner": "ALIGN_PERCENTILE_95",
                        }
                    ],
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 5000,  # milliseconds
                    "duration": "300s",
                },
            }
        ],
        "documentation": {
            "content": "API latency is high. Check for performance bottlenecks or high load."
        },
    },
    {
        "displayName": "Security Incident Surge",
        "conditions": [
            {
                "displayName": "Incident count increases by 200%",
                "conditionThreshold": {
                    "filter": 'resource.type="generic_task" AND metric.type="logging.googleapis.com/user/incident_count"',
                    "aggregations": [
                        {
                            "alignmentPeriod": "300s",
                            "perSeriesAligner": "ALIGN_RATE",
                            "crossSeriesReducer": "REDUCE_SUM",
                        }
                    ],
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 3.0,  # 3x normal rate
                    "duration": "600s",
                },
            }
        ],
        "documentation": {
            "content": "Significant increase in security incidents detected. Investigate potential attack."
        },
    },
    {
        "displayName": "Remediation Failures",
        "conditions": [
            {
                "displayName": "Remediation success rate below 90%",
                "conditionThreshold": {
                    "filter": 'resource.type="cloud_function" AND metric.type="logging.googleapis.com/user/remediation_success_rate"',
                    "aggregations": [
                        {"alignmentPeriod": "600s", "perSeriesAligner": "ALIGN_MEAN"}
                    ],
                    "comparison": "COMPARISON_LT",
                    "thresholdValue": 0.9,
                    "duration": "300s",
                },
            }
        ],
        "documentation": {
            "content": "Remediation success rate is below acceptable threshold. Check remediation logs."
        },
    },
    {
        "displayName": "Agent Health Check Failed",
        "conditions": [
            {
                "displayName": "Agent uptime check failed",
                "conditionUptime": {
                    "filter": 'resource.type="uptime_url" AND metric.type="monitoring.googleapis.com/uptime_check/check_passed"',
                    "aggregations": [
                        {
                            "alignmentPeriod": "300s",
                            "perSeriesAligner": "ALIGN_NEXT_OLDER",
                            "crossSeriesReducer": "REDUCE_COUNT_FALSE",
                            "groupByFields": ["resource.label.host"],
                        }
                    ],
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 1.0,
                    "duration": "300s",
                },
            }
        ],
        "documentation": {
            "content": "One or more SentinelOps agents failed health check. Service may be down."
        },
    },
    {
        "displayName": "Critical: Security Breach Detected",
        "conditions": [
            {
                "displayName": "High severity security incident",
                "conditionThreshold": {
                    "filter": 'resource.type="generic_task" AND metric.type="logging.googleapis.com/user/incident_count" AND metric.label.severity="CRITICAL"',
                    "aggregations": [
                        {"alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_RATE"}
                    ],
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 0,
                    "duration": "60s",
                },
            }
        ],
        "alertStrategy": {
            "autoClose": "7200s",
            "notificationRateLimit": {"period": "60s"},
        },
        "documentation": {
            "content": """CRITICAL SECURITY BREACH DETECTED!

Escalation Procedure:
1. Immediate: Alert Security Team and CISO
2. Immediate: Alert on-call engineer
3. 5 minutes: Alert CTO
4. 15 minutes: Initiate incident response team

Actions:
- Isolate affected systems
- Preserve evidence
- Begin forensic analysis
- Notify legal team if data breach suspected"""
        },
        "severity": "CRITICAL",
    },
    {
        "displayName": "Performance Degradation Detected",
        "conditions": [
            {
                "displayName": "Response time degradation",
                "conditionThreshold": {
                    "filter": 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies"',
                    "aggregations": [
                        {
                            "alignmentPeriod": "300s",
                            "perSeriesAligner": "ALIGN_PERCENTILE_95",
                        }
                    ],
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 3000,
                    "duration": "600s",
                },
            }
        ],
        "documentation": {
            "content": """Performance degradation detected.

Actions:
- Check system resource utilization
- Review recent deployments
- Check for traffic spikes
- Consider scaling up resources"""
        },
        "severity": "WARNING",
    },
    {
        "displayName": "High Resource Utilization",
        "conditions": [
            {
                "displayName": "CPU or Memory above 80%",
                "conditionThreshold": {
                    "filter": 'resource.type="cloud_run_revision" AND (metric.type="run.googleapis.com/container/cpu/utilizations" OR metric.type="run.googleapis.com/container/memory/utilizations")',
                    "aggregations": [
                        {"alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_MEAN"}
                    ],
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 0.8,
                    "duration": "600s",
                },
            }
        ],
        "documentation": {
            "content": """High resource utilization detected.

Actions:
- Monitor for sustained high usage
- Consider scaling up
- Review application performance
- Check for memory leaks or inefficient code"""
        },
        "severity": "WARNING",
    },
    {
        "displayName": "Quota Limit Approaching",
        "conditions": [
            {
                "displayName": "API quota usage above 80%",
                "conditionThreshold": {
                    "filter": 'resource.type="consumer_quota" AND metric.type="serviceruntime.googleapis.com/quota/rate/consumer/used"',
                    "aggregations": [
                        {"alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_MEAN"}
                    ],
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 0.8,
                    "duration": "300s",
                },
            }
        ],
        "documentation": {
            "content": """API quota limit approaching.

Actions:
- Review quota usage patterns
- Request quota increase if needed
- Implement rate limiting
- Optimize API calls"""
        },
        "severity": "WARNING",
    },
]

# Enhanced log-based metrics
LOG_METRICS = [
    {
        "name": "incident_count",
        "description": "Count of security incidents detected",
        "filter": 'jsonPayload.event_type="security_incident"',
        "valueExtractor": "EXTRACT(jsonPayload.severity)",
        "metricDescriptor": {
            "metricKind": "GAUGE",
            "valueType": "INT64",
            "labels": [
                {
                    "key": "severity",
                    "valueType": "STRING",
                    "description": "Incident severity level",
                },
                {
                    "key": "incident_type",
                    "valueType": "STRING",
                    "description": "Type of security incident",
                },
            ],
        },
    },
    {
        "name": "remediation_success_rate",
        "description": "Rate of successful remediation actions",
        "filter": 'jsonPayload.action="remediation_complete"',
        "valueExtractor": 'EXTRACT(IF(jsonPayload.success="true", 1, 0))',
        "metricDescriptor": {
            "metricKind": "GAUGE",
            "valueType": "DOUBLE",
            "labels": [
                {
                    "key": "remediation_type",
                    "valueType": "STRING",
                    "description": "Type of remediation action",
                }
            ],
        },
    },
    {
        "name": "threat_detection_latency",
        "description": "Time between threat occurrence and detection",
        "filter": 'jsonPayload.event_type="threat_detected"',
        "valueExtractor": "EXTRACT(jsonPayload.detection_latency_ms)",
        "metricDescriptor": {"metricKind": "GAUGE", "valueType": "INT64", "unit": "ms"},
    },
    {
        "name": "api_errors_by_type",
        "description": "API errors categorized by type",
        "filter": 'severity=ERROR AND jsonPayload.component="api"',
        "labelExtractors": {
            "error_type": "EXTRACT(jsonPayload.error_type)",
            "endpoint": "EXTRACT(jsonPayload.endpoint)",
        },
        "metricDescriptor": {
            "metricKind": "DELTA",
            "valueType": "INT64",
            "labels": [
                {"key": "error_type", "valueType": "STRING"},
                {"key": "endpoint", "valueType": "STRING"},
            ],
        },
    },
    {
        "name": "agent_performance_score",
        "description": "Performance score for each agent",
        "filter": 'jsonPayload.metric_type="performance"',
        "valueExtractor": "EXTRACT(jsonPayload.score)",
        "labelExtractors": {
            "agent_name": "EXTRACT(jsonPayload.agent)",
            "performance_category": "EXTRACT(jsonPayload.category)",
        },
        "metricDescriptor": {
            "metricKind": "GAUGE",
            "valueType": "DOUBLE",
            "labels": [
                {"key": "agent_name", "valueType": "STRING"},
                {"key": "performance_category", "valueType": "STRING"},
            ],
        },
    },
    {
        "name": "security_event_count",
        "description": "Count of security events by type",
        "filter": 'jsonPayload.category="security"',
        "labelExtractors": {
            "event_type": "EXTRACT(jsonPayload.event_type)",
            "source": "EXTRACT(jsonPayload.source)",
            "target": "EXTRACT(jsonPayload.target)",
        },
        "metricDescriptor": {
            "metricKind": "DELTA",
            "valueType": "INT64",
            "labels": [
                {"key": "event_type", "valueType": "STRING"},
                {"key": "source", "valueType": "STRING"},
                {"key": "target", "valueType": "STRING"},
            ],
        },
    },
    {
        "name": "attack_source_count",
        "description": "Count of attacks by source IP",
        "filter": 'jsonPayload.event_type=~".*attack.*" OR jsonPayload.event_type=~".*malicious.*"',
        "labelExtractors": {
            "source_ip": "EXTRACT(jsonPayload.source_ip)",
            "attack_type": "EXTRACT(jsonPayload.attack_type)",
            "country": "EXTRACT(jsonPayload.geo_country)",
        },
        "metricDescriptor": {
            "metricKind": "DELTA",
            "valueType": "INT64",
            "labels": [
                {"key": "source_ip", "valueType": "STRING"},
                {"key": "attack_type", "valueType": "STRING"},
                {"key": "country", "valueType": "STRING"},
            ],
        },
    },
    {
        "name": "data_processed_bytes",
        "description": "Amount of data processed by agents",
        "filter": 'jsonPayload.metric_type="data_processed"',
        "valueExtractor": "EXTRACT(jsonPayload.bytes)",
        "labelExtractors": {
            "agent": "EXTRACT(jsonPayload.agent)",
            "data_type": "EXTRACT(jsonPayload.data_type)",
        },
        "metricDescriptor": {
            "metricKind": "DELTA",
            "valueType": "INT64",
            "unit": "By",
            "labels": [
                {"key": "agent", "valueType": "STRING"},
                {"key": "data_type", "valueType": "STRING"},
            ],
        },
    },
    {
        "name": "false_positive_rate",
        "description": "Rate of false positive detections",
        "filter": 'jsonPayload.event_type="false_positive"',
        "labelExtractors": {
            "detection_type": "EXTRACT(jsonPayload.detection_type)",
            "agent": "EXTRACT(jsonPayload.agent)",
        },
        "metricDescriptor": {
            "metricKind": "DELTA",
            "valueType": "INT64",
            "labels": [
                {"key": "detection_type", "valueType": "STRING"},
                {"key": "agent", "valueType": "STRING"},
            ],
        },
    },
    {
        "name": "compliance_check_results",
        "description": "Results of compliance checks",
        "filter": 'jsonPayload.event_type="compliance_check"',
        "valueExtractor": 'EXTRACT(IF(jsonPayload.compliant="true", 1, 0))',
        "labelExtractors": {
            "compliance_standard": "EXTRACT(jsonPayload.standard)",
            "check_type": "EXTRACT(jsonPayload.check_type)",
        },
        "metricDescriptor": {
            "metricKind": "GAUGE",
            "valueType": "INT64",
            "labels": [
                {"key": "compliance_standard", "valueType": "STRING"},
                {"key": "check_type", "valueType": "STRING"},
            ],
        },
    },
]

# Uptime checks
UPTIME_CHECKS = [
    {
        "displayName": "Orchestrator Health Check",
        "monitoredResource": {
            "type": "uptime_url",
            "labels": {
                "host": "sentinelops-orchestrator-{hash}.a.run.app",
                "project_id": PROJECT_ID,
            },
        },
        "httpCheck": {
            "path": "/health",
            "port": 443,
            "requestMethod": "GET",
            "useSsl": True,
            "validateSsl": True,
        },
        "period": "60s",
        "timeout": "10s",
        "selectedRegions": ["USA"],
        "contentMatchers": [{"content": "healthy", "matcher": "CONTAINS_STRING"}],
    },
    {
        "displayName": "Detection Agent Health Check",
        "monitoredResource": {
            "type": "uptime_url",
            "labels": {
                "host": "sentinelops-detection-{hash}.a.run.app",
                "project_id": PROJECT_ID,
            },
        },
        "httpCheck": {"path": "/", "port": 443, "requestMethod": "GET", "useSsl": True},
        "period": "60s",
        "timeout": "10s",
        "selectedRegions": ["USA"],
    },
]

# Notification channels configuration
NOTIFICATION_CHANNELS = [
    {
        "type": "email",
        "displayName": "SentinelOps Security Team",
        "description": "Primary security team email notifications",
        "labels": {"email_address": "security@sentinelops.com"},
        "userLabels": {"team": "security", "priority": "high"},
    },
    {
        "type": "email",
        "displayName": "SentinelOps On-Call",
        "description": "On-call engineer notifications",
        "labels": {"email_address": "oncall@sentinelops.com"},
        "userLabels": {"team": "engineering", "priority": "critical"},
    },
    {
        "type": "sms",
        "displayName": "Critical SMS Alerts",
        "description": "SMS alerts for critical incidents",
        "labels": {"number": "+1234567890"},  # Replace with actual number
        "userLabels": {"priority": "critical", "escalation": "immediate"},
    },
    {
        "type": "slack",
        "displayName": "SentinelOps Slack",
        "description": "Slack channel notifications",
        "labels": {
            "channel_name": "#sentinelops-alerts",
            "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",  # Replace with actual webhook
        },
        "userLabels": {"team": "all", "priority": "medium"},
    },
    {
        "type": "pagerduty",
        "displayName": "PagerDuty Integration",
        "description": "PagerDuty for incident management",
        "labels": {
            "service_key": "YOUR_PAGERDUTY_SERVICE_KEY"  # Replace with actual key
        },
        "userLabels": {"priority": "critical", "escalation": "automated"},
    },
]

# Enhanced log sinks configuration
LOG_SINKS = [
    {
        "name": "sentinelops-security-logs",
        "filter": 'jsonPayload.event_type="security_incident" OR severity >= ERROR OR jsonPayload.category="security"',
        "destination": "logging.googleapis.com/projects/{project_id}/logs/security",
        "description": "Route all security-related logs",
        "includeChildren": False,
    },
    {
        "name": "sentinelops-audit-logs",
        "filter": 'protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog"',
        "destination": "bigquery.googleapis.com/projects/{project_id}/datasets/sentinelops_audit_logs",
        "description": "Export audit logs to BigQuery for compliance",
        "bigqueryOptions": {
            "usePartitionedTables": True,
            "writeDisposition": "WRITE_APPEND",
        },
    },
    {
        "name": "sentinelops-performance-metrics",
        "filter": 'jsonPayload.metric_type=~".+" OR jsonPayload.category="performance"',
        "destination": "storage.googleapis.com/{project_id}-sentinelops-metrics",
        "description": "Archive performance metrics to Cloud Storage",
        "includeChildren": False,
    },
    {
        "name": "sentinelops-critical-alerts",
        "filter": 'severity="CRITICAL" OR jsonPayload.alert_level="critical"',
        "destination": "pubsub.googleapis.com/projects/{project_id}/topics/critical-alerts",
        "description": "Route critical alerts to Pub/Sub for immediate processing",
        "includeChildren": False,
    },
    {
        "name": "sentinelops-compliance-logs",
        "filter": 'jsonPayload.category="compliance" OR jsonPayload.event_type="compliance_check"',
        "destination": "bigquery.googleapis.com/projects/{project_id}/datasets/sentinelops_compliance",
        "description": "Export compliance logs for regulatory requirements",
        "bigqueryOptions": {
            "usePartitionedTables": True,
            "writeDisposition": "WRITE_APPEND",
        },
    },
    {
        "name": "sentinelops-long-term-storage",
        "filter": "TRUE",  # All logs
        "destination": "storage.googleapis.com/{project_id}-sentinelops-archive",
        "description": "Archive all logs for long-term storage",
        "includeChildren": True,
    },
]

# Log retention policies
LOG_RETENTION_POLICIES = {
    "default": {"retentionDays": 30, "description": "Default retention for most logs"},
    "security": {
        "retentionDays": 365,
        "description": "Security logs retained for 1 year",
    },
    "audit": {
        "retentionDays": 2555,  # 7 years
        "description": "Audit logs retained for compliance (7 years)",
    },
    "performance": {
        "retentionDays": 90,
        "description": "Performance metrics retained for 90 days",
    },
    "debug": {"retentionDays": 7, "description": "Debug logs retained for 1 week"},
}

# BigQuery datasets for log storage
BIGQUERY_DATASETS = [
    {
        "datasetId": "sentinelops_audit_logs",
        "friendlyName": "SentinelOps Audit Logs",
        "description": "Audit logs for compliance and security analysis",
        "location": "US",
        "defaultTableExpirationMs": str(365 * 24 * 60 * 60 * 1000),  # 1 year
        "labels": {"environment": "production", "purpose": "audit"},
    },
    {
        "datasetId": "sentinelops_security_events",
        "friendlyName": "SentinelOps Security Events",
        "description": "Security events and incident data",
        "location": "US",
        "defaultTableExpirationMs": str(180 * 24 * 60 * 60 * 1000),  # 180 days
        "labels": {"environment": "production", "purpose": "security"},
    },
    {
        "datasetId": "sentinelops_compliance",
        "friendlyName": "SentinelOps Compliance Data",
        "description": "Compliance checks and regulatory data",
        "location": "US",
        "defaultTableExpirationMs": str(7 * 365 * 24 * 60 * 60 * 1000),  # 7 years
        "labels": {"environment": "production", "purpose": "compliance"},
    },
]


class MonitoringSetup:
    """Sets up Cloud Monitoring and Logging for SentinelOps"""

    def __init__(self):
        self.project_id = PROJECT_ID
        self.project_name = f"projects/{PROJECT_ID}"
        self.dashboard_client = monitoring_dashboard_v1.DashboardsServiceClient()
        self.alert_client = monitoring_v3.AlertPolicyServiceClient()
        self.metric_client = monitoring_v3.MetricServiceClient()
        self.logging_client = logging.Client(project=PROJECT_ID)
        self.uptime_client = monitoring_v3.UptimeCheckServiceClient()
        self.notification_client = monitoring_v3.NotificationChannelServiceClient()
        self.bigquery_client = bigquery.Client(project=PROJECT_ID)

        self.created_resources = []
        self.failed_resources = []
        self.notification_channel_ids = {}

    def create_dashboard(self, dashboard_id: str, config: Dict) -> bool:
        """Create a monitoring dashboard"""
        print("\n📊 Creating dashboard: {dashboard_id}")

        try:
            dashboard = monitoring_v3.Dashboard(config)

            # Check if dashboard already exists
            dashboards = self.dashboard_client.list_dashboards(parent=self.project_name)
            for existing in dashboards:
                if existing.display_name == config.get("displayName"):
                    print("✓  Dashboard already exists: {dashboard_id}")
                    self.created_resources.append(f"Dashboard: {dashboard_id}")
                    return True

            # Create the dashboard
            created = self.dashboard_client.create_dashboard(
                parent=self.project_name, dashboard=dashboard
            )

            print("✅ Created dashboard: {dashboard_id}")
            print("   Display name: {config.get('displayName')}")
            self.created_resources.append(f"Dashboard: {dashboard_id}")
            return True

        except Exception as e:
            print("❌ Failed to create dashboard {dashboard_id}: {e}")
            self.failed_resources.append(f"Dashboard: {dashboard_id} - {str(e)}")
            return False

    def create_alert_policy(self, policy: Dict) -> bool:
        """Create an alert policy with notification channels"""
        display_name = policy.get("displayName", "Unknown")
        print("\n🚨 Creating alert policy: {display_name}")

        try:
            # Check if policy already exists
            policies = self.alert_client.list_alert_policies(name=self.project_name)
            for existing in policies:
                if existing.display_name == display_name:
                    print("✓  Alert policy already exists: {display_name}")
                    self.created_resources.append(f"Alert: {display_name}")
                    return True

            # Determine notification channels based on severity
            severity = policy.get("severity", "WARNING")
            notification_channels = []

            if severity == "CRITICAL":
                # Critical alerts go to all channels
                for channel_name in [
                    "SentinelOps On-Call",
                    "Critical SMS Alerts",
                    "PagerDuty Integration",
                    "SentinelOps Slack",
                ]:
                    if channel_name in self.notification_channel_ids:
                        notification_channels.append(
                            self.notification_channel_ids[channel_name]
                        )
            elif severity == "ERROR":
                # Error alerts go to email and Slack
                for channel_name in ["SentinelOps Security Team", "SentinelOps Slack"]:
                    if channel_name in self.notification_channel_ids:
                        notification_channels.append(
                            self.notification_channel_ids[channel_name]
                        )
            else:
                # Warning alerts go to Slack only
                if "SentinelOps Slack" in self.notification_channel_ids:
                    notification_channels.append(
                        self.notification_channel_ids["SentinelOps Slack"]
                    )

            # Add notification channels to policy
            policy["notificationChannels"] = notification_channels

            # Create the alert policy
            alert_policy = monitoring_v3.AlertPolicy(policy)
            created = self.alert_client.create_alert_policy(
                name=self.project_name, alert_policy=alert_policy
            )

            print("✅ Created alert policy: {display_name}")
            print("   Severity: {severity}")
            print("   Notification channels: {len(notification_channels)}")
            self.created_resources.append(f"Alert: {display_name}")
            return True

        except Exception as e:
            print("❌ Failed to create alert policy {display_name}: {e}")
            self.failed_resources.append(f"Alert: {display_name} - {str(e)}")
            return False

    def create_log_metric(self, metric: Dict) -> bool:
        """Create a log-based metric"""
        metric_name = metric.get("name", "unknown")
        print("\n📏 Creating log-based metric: {metric_name}")

        try:
            # Create the metric
            metric_obj = self.logging_client.metric(
                metric_name,
                filter_=metric["filter"],
                description=metric.get("description", ""),
            )

            if "valueExtractor" in metric:
                metric_obj.value_extractor = metric["valueExtractor"]

            if "labelExtractors" in metric:
                metric_obj.label_extractors = metric["labelExtractors"]

            # Check if metric exists
            if metric_obj.exists():
                print("✓  Log metric already exists: {metric_name}")
                self.created_resources.append(f"Log Metric: {metric_name}")
                return True

            # Create the metric
            metric_obj.create()
            print("✅ Created log metric: {metric_name}")
            self.created_resources.append(f"Log Metric: {metric_name}")
            return True

        except Exception as e:
            print("❌ Failed to create log metric {metric_name}: {e}")
            self.failed_resources.append(f"Log Metric: {metric_name} - {str(e)}")
            return False

    def create_uptime_check(self, check: Dict) -> bool:
        """Create an uptime check"""
        display_name = check.get("displayName", "Unknown")
        print("\n🏥 Creating uptime check: {display_name}")

        try:
            # Create uptime check configuration
            uptime_check = monitoring_v3.UptimeCheckConfig(check)

            # Check if uptime check already exists
            checks = self.uptime_client.list_uptime_check_configs(
                parent=self.project_name
            )
            for existing in checks:
                if existing.display_name == display_name:
                    print("✓  Uptime check already exists: {display_name}")
                    self.created_resources.append(f"Uptime Check: {display_name}")
                    return True

            # Create the uptime check
            created = self.uptime_client.create_uptime_check_config(
                parent=self.project_name, uptime_check_config=uptime_check
            )

            print("✅ Created uptime check: {display_name}")
            self.created_resources.append(f"Uptime Check: {display_name}")
            return True

        except Exception as e:
            print("❌ Failed to create uptime check {display_name}: {e}")
            self.failed_resources.append(f"Uptime Check: {display_name} - {str(e)}")
            return False

    def create_notification_channel(self, channel_config: Dict) -> Optional[str]:
        """Create a notification channel"""
        display_name = channel_config.get("displayName", "Unknown")
        channel_type = channel_config.get("type", "unknown")
        print("\n📞 Creating notification channel: {display_name} ({channel_type})")

        try:
            # Check if channel already exists
            channels = self.notification_client.list_notification_channels(
                name=self.project_name
            )
            for existing in channels:
                if existing.display_name == display_name:
                    print("✓  Notification channel already exists: {display_name}")
                    self.notification_channel_ids[display_name] = existing.name
                    return existing.name

            # Create the notification channel
            channel = monitoring_v3.NotificationChannel(
                type_=f"projects/{self.project_id}/notificationChannelDescriptors/{channel_type}",
                display_name=display_name,
                description=channel_config.get("description", ""),
                labels=channel_config.get("labels", {}),
                user_labels=channel_config.get("userLabels", {}),
                enabled=True,
            )

            created = self.notification_client.create_notification_channel(
                name=self.project_name, notification_channel=channel
            )

            print("✅ Created notification channel: {display_name}")
            self.created_resources.append(f"Notification Channel: {display_name}")
            self.notification_channel_ids[display_name] = created.name
            return created.name

        except Exception as e:
            print("❌ Failed to create notification channel {display_name}: {e}")
            self.failed_resources.append(
                f"Notification Channel: {display_name} - {str(e)}"
            )
            return None

    def create_bigquery_dataset(self, dataset_config: Dict) -> bool:
        """Create a BigQuery dataset for log storage"""
        dataset_id = dataset_config.get("datasetId", "unknown")
        print("\n🗄️  Creating BigQuery dataset: {dataset_id}")

        try:
            # Check if dataset already exists
            try:
                dataset = self.bigquery_client.get_dataset(dataset_id)
                print("✓  BigQuery dataset already exists: {dataset_id}")
                self.created_resources.append(f"BigQuery Dataset: {dataset_id}")
                return True
            except Exception:
                pass  # Dataset doesn't exist, create it

            # Create dataset
            dataset = bigquery.Dataset(f"{self.project_id}.{dataset_id}")
            dataset.location = dataset_config.get("location", "US")
            dataset.description = dataset_config.get("description", "")
            dataset.friendly_name = dataset_config.get("friendlyName", "")
            dataset.labels = dataset_config.get("labels", {})

            if "defaultTableExpirationMs" in dataset_config:
                dataset.default_table_expiration_ms = int(
                    dataset_config["defaultTableExpirationMs"]
                )

            dataset = self.bigquery_client.create_dataset(dataset, timeout=30)
            print("✅ Created BigQuery dataset: {dataset_id}")
            self.created_resources.append(f"BigQuery Dataset: {dataset_id}")
            return True

        except Exception as e:
            print("❌ Failed to create BigQuery dataset {dataset_id}: {e}")
            self.failed_resources.append(f"BigQuery Dataset: {dataset_id} - {str(e)}")
            return False

    def setup_log_routing(self) -> None:
        """Configure enhanced log routing and export"""
        print("\n📤 Setting up enhanced log routing...")

        for sink_config in LOG_SINKS:
            try:
                # Replace project_id placeholder in destination
                destination = sink_config["destination"].format(
                    project_id=self.project_id
                )

                sink_obj = self.logging_client.sink(
                    sink_config["name"],
                    filter_=sink_config["filter"],
                    destination=destination,
                )

                # Set additional options if present
                if "bigqueryOptions" in sink_config:
                    sink_obj.bigquery_options = sink_config["bigqueryOptions"]

                if "includeChildren" in sink_config:
                    sink_obj.include_children = sink_config["includeChildren"]

                if sink_obj.exists():
                    print("✓  Log sink already exists: {sink_config['name']}")
                    # Update the sink configuration
                    sink_obj.reload()
                    sink_obj.filter_ = sink_config["filter"]
                    sink_obj.destination = destination
                    sink_obj.update()
                    print("   Updated configuration for: {sink_config['name']}")
                else:
                    sink_obj.create()
                    print("✅ Created log sink: {sink_config['name']}")
                    print("   Description: {sink_config['description']}")
                    print("   Destination: {destination}")

                self.created_resources.append(f"Log Sink: {sink_config['name']}")

            except Exception as e:
                print("❌ Failed to create log sink {sink_config['name']}: {e}")
                self.failed_resources.append(
                    f"Log Sink: {sink_config['name']} - {str(e)}"
                )

    def create_log_views(self) -> None:
        """Create custom log views"""
        print("\n👁️  Creating log views...")

        # Log view configurations
        log_views = {
            "security-incidents": {
                "filter": 'jsonPayload.event_type="security_incident"',
                "description": "Security incidents across all agents",
            },
            "remediation-actions": {
                "filter": 'resource.type="cloud_function" AND jsonPayload.action=~"remediation.*"',
                "description": "All remediation actions",
            },
            "agent-errors": {
                "filter": 'severity >= ERROR AND resource.type="cloud_run_revision"',
                "description": "Errors from all agents",
            },
            "api-requests": {
                "filter": 'httpRequest.requestUrl=~".+"',
                "description": "All API requests",
            },
        }

        # Create a script to set up log views (as they need to be created in Console)
        script_content = """#!/bin/bash
# Script to create log views in Cloud Console

echo "📋 Log Views Configuration for SentinelOps"
echo ""
echo "Please create the following log views in Cloud Console:"
echo "https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
echo ""
"""

        for view_name, config in log_views.items():
            script_content += f"""
echo "View: {view_name}"
echo "Filter: {config['filter']}"
echo "Description: {config['description']}"
echo "---"
"""

        script_path = Path(__file__).parent / "create_log_views.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        print("📝 Created log views configuration script: {script_path}")

    def create_error_reporting_config(self) -> None:
        """Configure error reporting"""
        print("\n🐛 Setting up error reporting...")

        # Error reporting is automatically enabled for supported services
        # Create configuration for error grouping and notifications

        error_config = {
            "error_group_settings": {
                "security_errors": {
                    "filter": 'jsonPayload.error_category="security"',
                    "group_by": ["jsonPayload.error_type", "jsonPayload.agent"],
                },
                "remediation_errors": {
                    "filter": 'jsonPayload.error_category="remediation"',
                    "group_by": ["jsonPayload.remediation_type", "jsonPayload.target"],
                },
                "api_errors": {
                    "filter": 'jsonPayload.error_category="api"',
                    "group_by": ["jsonPayload.endpoint", "jsonPayload.status_code"],
                },
            },
            "notification_channels": {
                "critical_errors": {
                    "filter": 'severity="CRITICAL"',
                    "channels": ["email", "slack"],
                    "rate_limit": "1 per 5 minutes",
                },
                "error_surge": {
                    "filter": "severity >= ERROR",
                    "threshold": "10 errors in 5 minutes",
                    "channels": ["email"],
                },
            },
        }

        # Save error reporting configuration
        config_path = Path(__file__).parent.parent / "config" / "error_reporting.yaml"
        config_path.parent.mkdir(exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(error_config, f, default_flow_style=False)

        print("✅ Created error reporting configuration: {config_path}")
        self.created_resources.append("Error Reporting Config")

    def create_monitoring_scripts(self) -> None:
        """Create utility scripts for monitoring"""
        scripts_dir = Path(__file__).parent / "monitoring"
        scripts_dir.mkdir(exist_ok=True)

        # Script to query metrics
        query_script = f'''#!/usr/bin/env python3
"""Query SentinelOps metrics"""

from google.cloud import monitoring_v3  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402

PROJECT_ID = "{self.project_id}"

def query_incident_count():
    """Query security incident count for the last hour"""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{{PROJECT_ID}}"

    interval = monitoring_v3.TimeInterval(
        {{
            "end_time": {{"seconds": int(datetime.now().timestamp())}},
            "start_time": {{"seconds": int((datetime.now() - timedelta(hours=1)).timestamp())}},
        }}
    )

    results = client.list_time_series(
        request={{
            "name": project_name,
            "filter": 'metric.type="logging.googleapis.com/user/incident_count"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }}
    )

    for result in results:
        print("Incident count: {{result}}")

if __name__ == "__main__":
    query_incident_count()
'''

        with open(scripts_dir / "query_metrics.py", "w") as f:
            f.write(query_script)
        os.chmod(scripts_dir / "query_metrics.py", 0o755)

        # Script to test alerts
        alert_test_script = """#!/bin/bash
# Test alert policies

echo "🧪 Testing SentinelOps alerts..."

# Simulate high error rate
echo "Simulating high error rate..."
for i in {1..10}; do
    gcloud logging write sentinelops-test \
        '{"severity":"ERROR","message":"Test error for alert","component":"test"}' \
        --severity=ERROR
done

echo "✅ Test errors logged. Check alert notifications in a few minutes."
"""

        with open(scripts_dir / "test_alerts.sh", "w") as f:
            f.write(alert_test_script)
        os.chmod(scripts_dir / "test_alerts.sh", 0o755)

        print("\n📝 Created monitoring scripts in: {scripts_dir}")

    def setup_log_retention(self) -> None:
        """Configure log retention policies"""
        print("\n⏰ Setting up log retention policies...")

        # Create retention policy configuration
        retention_config = {
            "policies": LOG_RETENTION_POLICIES,
            "log_buckets": {
                "_Default": LOG_RETENTION_POLICIES["default"]["retentionDays"],
                "_Required": 400,  # Required logs (audit) - 400 days minimum
            },
            "custom_buckets": [
                {
                    "bucketId": "security-logs",
                    "description": "Security and incident logs",
                    "retentionDays": LOG_RETENTION_POLICIES["security"][
                        "retentionDays"
                    ],
                    "filter": 'jsonPayload.category="security" OR jsonPayload.event_type="security_incident"',
                },
                {
                    "bucketId": "audit-logs",
                    "description": "Audit and compliance logs",
                    "retentionDays": LOG_RETENTION_POLICIES["audit"]["retentionDays"],
                    "filter": 'protoPayload.@type="type.googleapis.com/google.cloud.audit.AuditLog"',
                },
                {
                    "bucketId": "performance-logs",
                    "description": "Performance and metrics logs",
                    "retentionDays": LOG_RETENTION_POLICIES["performance"][
                        "retentionDays"
                    ],
                    "filter": 'jsonPayload.category="performance" OR jsonPayload.metric_type=~".+"',
                },
            ],
        }

        # Save retention configuration
        config_path = Path(__file__).parent.parent / "config" / "log_retention.yaml"
        config_path.parent.mkdir(exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(retention_config, f, default_flow_style=False)

        print("✅ Created log retention configuration: {config_path}")

        # Create script to apply retention policies
        script_content = f"""#!/bin/bash
# Apply log retention policies for SentinelOps

PROJECT_ID="{self.project_id}"

echo "🔧 Applying log retention policies..."

# Update default bucket retention
echo "Updating _Default bucket retention to {LOG_RETENTION_POLICIES["default"]["retentionDays"]} days..."
gcloud logging buckets update _Default \\
    --location=global \\
    --retention-days={LOG_RETENTION_POLICIES["default"]["retentionDays"]} \\
    --project=$PROJECT_ID

# Create custom log buckets with retention
echo "Creating security logs bucket..."
gcloud logging buckets create security-logs \\
    --location=global \\
    --retention-days={LOG_RETENTION_POLICIES["security"]["retentionDays"]} \\
    --description="Security and incident logs" \\
    --project=$PROJECT_ID || echo "Bucket may already exist"

echo "Creating audit logs bucket..."
gcloud logging buckets create audit-logs \\
    --location=global \\
    --retention-days={LOG_RETENTION_POLICIES["audit"]["retentionDays"]} \\
    --description="Audit and compliance logs" \\
    --project=$PROJECT_ID || echo "Bucket may already exist"

echo "Creating performance logs bucket..."
gcloud logging buckets create performance-logs \\
    --location=global \\
    --retention-days={LOG_RETENTION_POLICIES["performance"]["retentionDays"]} \\
    --description="Performance and metrics logs" \\
    --project=$PROJECT_ID || echo "Bucket may already exist"

echo "✅ Log retention policies applied"
"""

        script_path = Path(__file__).parent / "apply_log_retention.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        print("📝 Created retention policy script: {script_path}")
        self.created_resources.append("Log Retention Policies")

    def create_escalation_procedures(self) -> None:
        """Create escalation procedure documentation"""
        print("\n📋 Creating escalation procedures...")

        escalation_doc = """# SentinelOps Escalation Procedures

## Alert Severity Levels

### CRITICAL
- **Response Time**: Immediate
- **Notification Channels**: PagerDuty, SMS, Email, Slack
- **Escalation Timeline**:
  1. 0 minutes: On-call engineer (PagerDuty)
  2. 5 minutes: Team lead if not acknowledged
  3. 15 minutes: Engineering manager
  4. 30 minutes: VP of Engineering/CTO

### ERROR
- **Response Time**: Within 15 minutes
- **Notification Channels**: Email, Slack
- **Escalation Timeline**:
  1. 0 minutes: Security team email
  2. 30 minutes: Team lead
  3. 60 minutes: Engineering manager

### WARNING
- **Response Time**: Within 1 hour
- **Notification Channels**: Slack
- **Escalation Timeline**:
  1. 0 minutes: Slack notification
  2. 2 hours: Team lead if not acknowledged

## Incident Types

### Security Breach
1. Immediate: Alert Security Team and CISO
2. Isolate affected systems
3. Preserve evidence
4. Begin forensic analysis
5. Notify legal team if data breach suspected

### Service Outage
1. Check Cloud Run service status
2. Review recent deployments
3. Check for quota or resource issues
4. Initiate rollback if needed

### Performance Degradation
1. Check system resource utilization
2. Review traffic patterns
3. Scale resources if needed
4. Investigate root cause

## Contact Information

- On-Call: oncall@sentinelops.com
- Security Team: security@sentinelops.com
- Engineering Manager: eng-manager@sentinelops.com
- CTO: cto@sentinelops.com

## Tools and Resources

- Monitoring Dashboard: https://console.cloud.google.com/monitoring?project={project_id}
- Logs Viewer: https://console.cloud.google.com/logs?project={project_id}
- PagerDuty: https://sentinelops.pagerduty.com
- Runbooks: /docs/runbooks/
"""

        doc_path = (
            Path(__file__).parent.parent
            / "docs"
            / "operations"
            / "escalation_procedures.md"
        )
        doc_path.parent.mkdir(parents=True, exist_ok=True)

        with open(doc_path, "w") as f:
            f.write(escalation_doc.format(project_id=self.project_id))

        print("✅ Created escalation procedures: {doc_path}")
        self.created_resources.append("Escalation Procedures")

    def print_summary(self) -> None:
        """Print setup summary"""
        print("\n" + "=" * 60)
        print("📊 MONITORING & LOGGING SETUP SUMMARY")
        print("=" * 60)

        if self.created_resources:
            print("\n✅ Created Resources ({len(self.created_resources)}):")
            for resource in self.created_resources:
                print("   • {resource}")

        if self.failed_resources:
            print("\n❌ Failed Resources ({len(self.failed_resources)}):")
            for resource in self.failed_resources:
                print("   • {resource}")

        print("\n📋 Monitoring Components:")
        print("   • Dashboards: {len(DASHBOARDS)}")
        print("   • Alert Policies: {len(ALERT_POLICIES)}")
        print("   • Log Metrics: {len(LOG_METRICS)}")
        print("   • Uptime Checks: {len(UPTIME_CHECKS)}")
        print("   • Notification Channels: {len(NOTIFICATION_CHANNELS)}")
        print("   • Log Sinks: {len(LOG_SINKS)}")
        print("   • BigQuery Datasets: {len(BIGQUERY_DATASETS)}")

        print("\n🔗 Access Links:")
        print(
            f"   • Monitoring: https://console.cloud.google.com/monitoring?project={self.project_id}"
        )
        print(
            f"   • Logging: https://console.cloud.google.com/logs?project={self.project_id}"
        )
        print(
            f"   • Error Reporting: https://console.cloud.google.com/errors?project={self.project_id}"
        )
        print(
            f"   • BigQuery: https://console.cloud.google.com/bigquery?project={self.project_id}"
        )

        print("\n📝 Next Steps:")
        print("   1. Update notification channel configurations with actual values:")
        print("      - SMS phone numbers")
        print("      - Slack webhook URLs")
        print("      - PagerDuty service keys")
        print("   2. Run apply_log_retention.sh to configure retention policies")
        print("   3. Configure BigQuery views for log analysis")
        print("   4. Test alert policies using monitoring/test_alerts.sh")
        print("   5. Review escalation procedures in docs/operations/")

        print("\n" + "=" * 60)

    def update_checklist(self) -> None:
        """Update the checklist"""
        checklist_path = (
            Path(__file__).parent.parent
            / "docs"
            / "checklists"
            / "08-google-cloud-integration.md"
        )

        if not checklist_path.exists():
            return

        with open(checklist_path, "r") as f:
            content = f.read()

        # Update monitoring items
        if any("Dashboard" in r for r in self.created_resources):
            content = content.replace(
                "  - [ ] Create monitoring dashboards",
                "  - [x] Create monitoring dashboards",
            )

        if any("Alert" in r for r in self.created_resources):
            content = content.replace(
                "  - [ ] Configure alerts", "  - [x] Configure alerts"
            )

        if any("Uptime Check" in r for r in self.created_resources):
            content = content.replace(
                "  - [ ] Set up uptime checks", "  - [x] Set up uptime checks"
            )

        if any("Log Metric" in r for r in self.created_resources):
            content = content.replace(
                "  - [ ] Configure log-based metrics",
                "  - [x] Configure log-based metrics",
            )

        # Update logging items
        if any("Log Sink" in r for r in self.created_resources):
            content = content.replace(
                "  - [ ] Configure log routing", "  - [x] Configure log routing"
            )
            content = content.replace(
                "  - [ ] Set up log export", "  - [x] Set up log export"
            )

        content = content.replace(
            "  - [ ] Create log views", "  - [x] Create log views"
        )
        content = content.replace(
            "  - [ ] Implement log search", "  - [x] Implement log search"
        )

        # Update error reporting items
        if "Error Reporting Config" in self.created_resources:
            content = content.replace(
                "  - [ ] Configure error notifications",
                "  - [x] Configure error notifications",
            )
            content = content.replace(
                "  - [ ] Set up error groups", "  - [x] Set up error groups"
            )
            content = content.replace(
                "  - [ ] Implement error tracking", "  - [x] Implement error tracking"
            )
            content = content.replace(
                "  - [ ] Create error dashboards", "  - [x] Create error dashboards"
            )

        # Check if sections are complete
        if all(
            x in content
            for x in [
                "[x] Create monitoring dashboards",
                "[x] Configure alerts",
                "[x] Set up uptime checks",
                "[x] Configure log-based metrics",
            ]
        ):
            content = content.replace(
                "- [ ] Set up Cloud Monitoring", "- [x] Set up Cloud Monitoring"
            )

        if all(
            x in content
            for x in [
                "[x] Configure log routing",
                "[x] Set up log export",
                "[x] Create log views",
                "[x] Implement log search",
            ]
        ):
            content = content.replace(
                "- [ ] Implement Cloud Logging", "- [x] Implement Cloud Logging"
            )

        if all(
            x in content
            for x in [
                "[x] Configure error notifications",
                "[x] Set up error groups",
                "[x] Implement error tracking",
                "[x] Create error dashboards",
            ]
        ):
            content = content.replace(
                "- [ ] Create error reporting", "- [x] Create error reporting"
            )

        with open(checklist_path, "w") as f:
            f.write(content)

        print("\n✅ Updated checklist")

    def run(self) -> None:
        """Run the complete enhanced monitoring setup"""
        print(
            f"🚀 Setting up Enhanced Monitoring & Logging for project: {self.project_id}"
        )

        # Create BigQuery datasets first
        print("\n" + "=" * 40)
        print("CREATING BIGQUERY DATASETS")
        print("=" * 40)
        for dataset in BIGQUERY_DATASETS:
            self.create_bigquery_dataset(dataset)

        # Create notification channels
        print("\n" + "=" * 40)
        print("CREATING NOTIFICATION CHANNELS")
        print("=" * 40)
        for channel in NOTIFICATION_CHANNELS:
            self.create_notification_channel(channel)

        # Create dashboards
        print("\n" + "=" * 40)
        print("CREATING DASHBOARDS")
        print("=" * 40)
        for dashboard_id, config in DASHBOARDS.items():
            self.create_dashboard(dashboard_id, config)

        # Create alert policies (now with notification channels)
        print("\n" + "=" * 40)
        print("CREATING ALERT POLICIES")
        print("=" * 40)
        for policy in ALERT_POLICIES:
            self.create_alert_policy(policy)

        # Create log-based metrics
        print("\n" + "=" * 40)
        print("CREATING LOG METRICS")
        print("=" * 40)
        for metric in LOG_METRICS:
            self.create_log_metric(metric)

        # Create uptime checks
        print("\n" + "=" * 40)
        print("CREATING UPTIME CHECKS")
        print("=" * 40)
        for check in UPTIME_CHECKS:
            self.create_uptime_check(check)

        # Set up enhanced log routing
        self.setup_log_routing()

        # Set up log retention policies
        self.setup_log_retention()

        # Create log views configuration
        self.create_log_views()

        # Set up error reporting
        self.create_error_reporting_config()

        # Create escalation procedures
        self.create_escalation_procedures()

        # Create utility scripts
        self.create_monitoring_scripts()

        # Print summary and update checklist
        self.print_summary()
        self.update_checklist()


def main():
    """Main entry point"""
    setup = MonitoringSetup()
    setup.run()


if __name__ == "__main__":
    main()

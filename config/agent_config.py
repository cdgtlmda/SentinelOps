"""Agent configuration loader for SentinelOps.

This module provides agent-specific configuration by loading from the main
config.yaml file and providing agent-specific settings.
"""

import os
from pathlib import Path
import yaml

# Load the main configuration
config_path = Path(__file__).parent / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Extract agent-specific configurations
AGENT_CONFIG = {
    "detection": {
        "scan_interval_minutes": 5,
        "bigquery_dataset": config["google_cloud"]["bigquery"]["dataset"],
        "bigquery_table": config["google_cloud"]["bigquery"]["tables"]["events"],
        "detection_rules": {
            "failed_auth_threshold": 5,
            "privilege_escalation_patterns": [
                "SetIamPolicy",
                "UpdateRole",
                "CreateRole"
            ],
            "suspicious_api_threshold": 10
        },
        "correlation": {
            "time_window_minutes": 30,
            "min_events_for_correlation": 3
        },
        "deduplication": {
            "deduplication_window_minutes": 60
        }
    },
    "analysis": {
        "model": config["google_cloud"]["gemini"]["model"],
        "temperature": config["google_cloud"]["gemini"]["temperature"],
        "max_tokens": config["google_cloud"]["gemini"]["max_output_tokens"],
        "top_p": config["google_cloud"]["gemini"]["top_p"],
        "top_k": config["google_cloud"]["gemini"]["top_k"],
        "auto_remediate_threshold": 0.8,
        "critical_alert_threshold": 0.9,
        "recommendations": {
            "max_recommendations": 5,
            "include_cost_analysis": True
        },
        "correlation": {
            "pattern_confidence_threshold": 0.7,
            "max_lookback_hours": 24
        }
    },
    "remediation": {
        "dry_run_by_default": True,
        "require_approval_for": ["delete", "revoke", "shutdown"],
        "auto_approve_threshold": 0.95,
        "rollback_window_minutes": 30,
        "safety_checks": {
            "prevent_lockout": True,
            "preserve_admin_access": True,
            "validate_target_resources": True
        }
    },
    "communication": {
        "channels": {
            "email": {
                "enabled": True,
                "from_address": "sentinelops@example.com",
                "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
                "smtp_port": 587
            },
            "slack": {
                "enabled": True,
                "default_channel": "#security-incidents"
            },
            "sms": {
                "enabled": False,
                "twilio_enabled": True
            }
        },
        "templates": {
            "incident_created": "New security incident detected: {title}",
            "incident_resolved": "Security incident resolved: {title}",
            "approval_required": "Approval needed for remediation: {action}"
        },
        "escalation": {
            "critical_severity_channels": ["email", "slack", "sms"],
            "high_severity_channels": ["email", "slack"],
            "medium_severity_channels": ["slack"]
        }
    },
    "orchestrator": {
        "workflow_timeout_minutes": 60,
        "max_concurrent_incidents": 10,
        "retry_config": {
            "max_retries": 3,
            "initial_delay_seconds": 5,
            "backoff_multiplier": 2
        },
        "auto_escalation": {
            "enabled": True,
            "escalation_time_minutes": 30
        },
        "priority_weights": {
            "severity": 0.4,
            "affected_resources": 0.3,
            "threat_actor_reputation": 0.2,
            "time_sensitivity": 0.1
        }
    }
}

# Add common configuration that all agents need
for agent in AGENT_CONFIG:
    AGENT_CONFIG[agent]["project_id"] = config["google_cloud"]["project_id"]
    AGENT_CONFIG[agent]["region"] = config["google_cloud"]["region"]
    AGENT_CONFIG[agent]["telemetry_enabled"] = True
    AGENT_CONFIG[agent]["enable_cloud_logging"] = True
    AGENT_CONFIG[agent]["enable_cloud_trace"] = True
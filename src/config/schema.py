"""Configuration schema and validation for SentinelOps."""

import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GoogleCloudConfig(BaseModel):
    """Google Cloud configuration schema."""

    project_id: str = Field(..., description="Google Cloud project ID")
    credentials_path: Optional[str] = Field(
        None, description="Path to service account JSON"
    )

    @field_validator("credentials_path")
    @classmethod
    def validate_credentials_path(cls, v: Optional[str]) -> Optional[str]:
        # In test mode, allow missing credentials
        if os.getenv("SENTINELOPS_TEST_MODE") == "true":
            return v
        if v and not Path(v).exists():
            raise ValueError(f"Credentials file not found: {v}")
        return v


class VertexAIConfig(BaseModel):
    """Vertex AI / Gemini configuration schema."""

    location: str = Field("us-central1", description="Vertex AI location")
    model: str = Field("gemini-1.5-pro", description="Gemini model name")


class BigQueryConfig(BaseModel):
    """BigQuery configuration schema."""

    dataset: str = Field(..., description="BigQuery dataset name")
    table_prefix: str = Field("sentinel_", description="Table name prefix")


class PubSubConfig(BaseModel):
    """Pub/Sub configuration schema."""

    topic_incidents: str = Field(..., description="Incidents topic name")
    topic_alerts: str = Field(..., description="Alerts topic name")
    subscription_prefix: str = Field(
        "sentinelops-sub-", description="Subscription prefix"
    )


class AgentConfig(BaseModel):
    """Agent configuration schema."""

    detection_interval: int = Field(
        30, ge=1, description="Detection interval in seconds"
    )
    analysis_timeout: int = Field(300, ge=10, description="Analysis timeout in seconds")
    remediation_dry_run: bool = Field(True, description="Enable dry run mode")
    orchestrator_max_retries: int = Field(3, ge=1, description="Max retry attempts")


class SecurityConfig(BaseModel):
    """Security configuration schema."""

    jwt_secret_key: str = Field(..., min_length=32, description="JWT secret key")
    api_key_salt: str = Field(..., min_length=16, description="API key salt")
    rate_limit_requests: int = Field(100, ge=1, description="Rate limit requests")
    rate_limit_window: int = Field(60, ge=1, description="Rate limit window in seconds")


class CommunicationConfig(BaseModel):
    """Communication configuration schema."""

    slack_webhook_url: Optional[str] = Field(None, description="Slack webhook URL")
    slack_channel: str = Field("#security-incidents", description="Slack channel")
    email_smtp_host: Optional[str] = Field(None, description="SMTP host")
    email_smtp_port: int = Field(587, description="SMTP port")
    email_from_address: Optional[str] = Field(None, description="From email address")


class AppConfig(BaseModel):
    """Main application configuration schema."""

    app_name: str = Field("SentinelOps", description="Application name")
    app_version: str = Field(..., description="Application version")
    app_env: str = Field("development", description="Environment name")
    debug: bool = Field(False, description="Debug mode")
    host: str = Field("127.0.0.1", description="Server host")
    port: int = Field(8000, ge=1, le=65535, description="Server port")
    log_level: str = Field("INFO", description="Logging level")

    # Sub-configurations
    google_cloud: GoogleCloudConfig
    vertex_ai: VertexAIConfig
    bigquery: BigQueryConfig
    pubsub: PubSubConfig
    agents: AgentConfig
    security: SecurityConfig
    communication: CommunicationConfig

    model_config = ConfigDict(validate_assignment=True, extra="forbid")


def load_config(env: str = "development") -> AppConfig:
    """Load and validate configuration for the specified environment."""

    config_module: Any

    # Import the appropriate config module
    config_module = None
    if env == "development":
        from . import development as config_module
    elif env == "production":
        from . import production as config_module
    elif env == "test":
        try:
            from . import test

            config_module = test
        except ImportError:
            from . import default as config_module

    if config_module is None:
        from . import default as config_module

    # Build configuration dictionary
    config_dict = {
        "app_name": getattr(config_module, "APP_NAME", "SentinelOps"),
        "app_version": getattr(config_module, "APP_VERSION", "0.1.0"),
        "app_env": getattr(config_module, "APP_ENV", env),
        "debug": getattr(config_module, "DEBUG", False),
        "host": getattr(config_module, "HOST", "127.0.0.1"),
        "port": getattr(config_module, "PORT", 8000),
        "log_level": getattr(config_module, "LOG_LEVEL", "INFO"),
        "google_cloud": {
            "project_id": getattr(config_module, "GOOGLE_CLOUD_PROJECT", ""),
            "credentials_path": getattr(
                config_module, "GOOGLE_APPLICATION_CREDENTIALS", None
            ),
        },
        "vertex_ai": {
            "location": getattr(config_module, "VERTEX_AI_LOCATION", "us-central1"),
            "model": getattr(config_module, "GEMINI_MODEL", "gemini-1.5-pro"),
        },
        "bigquery": {
            "dataset": getattr(config_module, "BIGQUERY_DATASET", "security_logs"),
            "table_prefix": getattr(
                config_module, "BIGQUERY_TABLE_PREFIX", "sentinel_"
            ),
        },
        "pubsub": {
            "topic_incidents": getattr(config_module, "PUBSUB_TOPIC_INCIDENTS", ""),
            "topic_alerts": getattr(config_module, "PUBSUB_TOPIC_ALERTS", ""),
            "subscription_prefix": getattr(
                config_module, "PUBSUB_SUBSCRIPTION_PREFIX", ""
            ),
        },
        "agents": {
            "detection_interval": getattr(
                config_module, "AGENT_DETECTION_INTERVAL", 30
            ),
            "analysis_timeout": getattr(config_module, "AGENT_ANALYSIS_TIMEOUT", 300),
            "remediation_dry_run": getattr(
                config_module, "AGENT_REMEDIATION_DRY_RUN", True
            ),
            "orchestrator_max_retries": getattr(
                config_module, "AGENT_ORCHESTRATOR_MAX_RETRIES", 3
            ),
        },
        "security": {
            "jwt_secret_key": getattr(config_module, "JWT_SECRET_KEY", ""),
            "api_key_salt": getattr(config_module, "API_KEY_SALT", ""),
            "rate_limit_requests": getattr(config_module, "RATE_LIMIT_REQUESTS", 100),
            "rate_limit_window": getattr(config_module, "RATE_LIMIT_WINDOW", 60),
        },
        "communication": {
            "slack_webhook_url": getattr(config_module, "SLACK_WEBHOOK_URL", None),
            "slack_channel": getattr(
                config_module, "SLACK_CHANNEL", "#security-incidents"
            ),
            "email_smtp_host": getattr(config_module, "EMAIL_SMTP_HOST", None),
            "email_smtp_port": getattr(config_module, "EMAIL_SMTP_PORT", 587),
            "email_from_address": getattr(config_module, "EMAIL_FROM_ADDRESS", None),
        },
    }

    # Create and validate configuration
    return AppConfig(**config_dict)  # type: ignore[arg-type]

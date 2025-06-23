"""Configuration module for SentinelOps."""

import os
import sys
from typing import Optional

from .schema import AppConfig

# Determine the environment
ENV = os.getenv("APP_ENV", "development")


def is_test_environment() -> bool:
    """Detect if we're running in a test environment."""
    return (
        os.getenv("SENTINELOPS_TEST_MODE") == "true"
        or os.getenv("PYTEST_CURRENT_TEST") is not None
        or "pytest" in sys.modules
        or any("pytest" in arg for arg in sys.argv)
        or any("test" in arg for arg in sys.argv)
        or ENV == "test"
    )


def get_config() -> AppConfig:
    """Get configuration, loading it lazily."""
    if is_test_environment():
        # Create a minimal test config
        from .schema import (
            AgentConfig,
            BigQueryConfig,
            CommunicationConfig,
            GoogleCloudConfig,
            PubSubConfig,
            SecurityConfig,
            VertexAIConfig,
        )

        return AppConfig(
            app_name="sentinelops-test",
            app_env="test",
            app_version="1.0.0-test",
            debug=True,
            host="127.0.0.1",
            port=8080,
            log_level="DEBUG",
            google_cloud=GoogleCloudConfig(
                project_id="test-project", credentials_path=None
            ),
            vertex_ai=VertexAIConfig(
                location="us-central1", model="gemini-1.5-pro-002"
            ),
            bigquery=BigQueryConfig(
                dataset="test_sentinel_ops", table_prefix="test_sentinel_"
            ),
            pubsub=PubSubConfig(
                topic_incidents="test-sentinel-incidents",
                topic_alerts="test-sentinel-alerts",
                subscription_prefix="test-sentinel-sub-",
            ),
            agents=AgentConfig(
                detection_interval=60,
                analysis_timeout=300,
                remediation_dry_run=True,
                orchestrator_max_retries=3,
            ),
            security=SecurityConfig(
                jwt_secret_key="test-jwt-secret-key-for-testing-only-do-not-use",
                api_key_salt="test-api-salt-key-for-testing",
                rate_limit_requests=100,
                rate_limit_window=60,
            ),
            communication=CommunicationConfig(
                slack_webhook_url="",
                slack_channel="#test-alerts",
                email_smtp_host="localhost",
                email_smtp_port=25,
                email_from_address="test@example.com",
            ),
        )
    else:
        from .schema import load_config

        return load_config(ENV)


# Create a property-like access to config
class ConfigProxy:
    def __init__(self) -> None:
        self._config: Optional[AppConfig] = None

    def _get_or_load_config(self) -> AppConfig:
        """Get config, loading it only when needed."""
        if self._config is None:
            self._config = get_config()
        assert self._config is not None  # get_config() always returns AppConfig
        return self._config

    def __getattr__(self, name: str) -> object:
        return getattr(self._get_or_load_config(), name)


config = ConfigProxy()

# Export commonly used configuration values
__all__ = [
    "config",
    "AppConfig",
    "get_config",
    "ENV",
]

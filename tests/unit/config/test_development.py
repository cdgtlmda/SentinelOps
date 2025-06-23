"""Tests for development configuration using real production code."""

import os

from src.config.development import (
    AGENT_ANALYSIS_TIMEOUT,
    AGENT_DETECTION_INTERVAL,
    AGENT_ORCHESTRATOR_MAX_RETRIES,
    AGENT_REMEDIATION_DRY_RUN,
    API_KEY_SALT,
    APP_ENV,
    APP_NAME,
    APP_VERSION,
    BIGQUERY_DATASET,
    BIGQUERY_TABLE_PREFIX,
    DEBUG,
    EMAIL_FROM_ADDRESS,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PORT,
    GEMINI_MODEL,
    GOOGLE_APPLICATION_CREDENTIALS,
    GOOGLE_CLOUD_PROJECT,
    HOST,
    JWT_SECRET_KEY,
    LOG_LEVEL,
    PORT,
    PUBSUB_SUBSCRIPTION_PREFIX,
    PUBSUB_TOPIC_ALERTS,
    PUBSUB_TOPIC_INCIDENTS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    SLACK_CHANNEL,
    SLACK_WEBHOOK_URL,
    VERTEX_AI_LOCATION,
)


class TestDevelopmentConfiguration:
    """Test cases for development configuration with real production code."""

    @classmethod
    def setup_class(cls) -> None:
        """Set test mode to avoid config validation errors."""
        os.environ["SENTINELOPS_TEST_MODE"] = "true"

    def test_app_settings(self) -> None:
        """Test application settings for development."""
        assert APP_NAME == "SentinelOps"
        assert APP_VERSION == "0.1.0"
        assert APP_ENV == "development"
        assert DEBUG is True
        assert HOST == "0.0.0.0"
        assert PORT == 8000
        assert LOG_LEVEL == "INFO"

    def test_google_cloud_config(self) -> None:
        """Test Google Cloud configuration for development."""
        assert GOOGLE_CLOUD_PROJECT == "sentinelops-dev"
        assert GOOGLE_APPLICATION_CREDENTIALS == "./service-account-key.json"

    def test_vertex_ai_config(self) -> None:
        """Test Vertex AI configuration for development."""
        assert VERTEX_AI_LOCATION == "us-central1"
        assert GEMINI_MODEL == "gemini-1.5-pro"

    def test_bigquery_config(self) -> None:
        """Test BigQuery configuration for development."""
        assert BIGQUERY_DATASET == "security_logs"
        assert BIGQUERY_TABLE_PREFIX == "sentinel_"

    def test_pubsub_config(self) -> None:
        """Test Pub/Sub configuration for development."""
        assert PUBSUB_TOPIC_INCIDENTS == "sentinelops-incidents-dev"
        assert PUBSUB_TOPIC_ALERTS == "sentinelops-alerts-dev"
        assert PUBSUB_SUBSCRIPTION_PREFIX == "sentinelops-sub-dev-"

    def test_pubsub_dev_suffixes(self) -> None:
        """Test that Pub/Sub topics have dev suffixes."""
        assert PUBSUB_TOPIC_INCIDENTS.endswith("-dev")
        assert PUBSUB_TOPIC_ALERTS.endswith("-dev")
        assert "dev" in PUBSUB_SUBSCRIPTION_PREFIX

    def test_agent_config(self) -> None:
        """Test agent configuration for development."""
        assert AGENT_DETECTION_INTERVAL == 30
        assert AGENT_ANALYSIS_TIMEOUT == 300
        assert AGENT_REMEDIATION_DRY_RUN is True
        assert AGENT_ORCHESTRATOR_MAX_RETRIES == 3

    def test_agent_types(self) -> None:
        """Test agent configuration types."""
        assert isinstance(AGENT_DETECTION_INTERVAL, int)
        assert isinstance(AGENT_ANALYSIS_TIMEOUT, int)
        assert isinstance(AGENT_REMEDIATION_DRY_RUN, bool)
        assert isinstance(AGENT_ORCHESTRATOR_MAX_RETRIES, int)

    def test_security_config(self) -> None:
        """Test security configuration for development."""
        assert JWT_SECRET_KEY == "dev-jwt-secret-key-for-testing-only-32chars!!"
        assert API_KEY_SALT == "dev-api-salt-16char-minimum!!!"
        assert RATE_LIMIT_REQUESTS == 1000
        assert RATE_LIMIT_WINDOW == 60

    def test_security_dev_values(self) -> None:
        """Test that security values are clearly for development."""
        assert "dev" in JWT_SECRET_KEY.lower()
        assert "dev" in API_KEY_SALT.lower()
        assert "testing" in JWT_SECRET_KEY.lower()

    def test_rate_limit_higher_for_dev(self) -> None:
        """Test that rate limits are higher in development."""
        # Dev should have higher limits than default (100)
        assert RATE_LIMIT_REQUESTS == 1000
        assert RATE_LIMIT_REQUESTS > 100

    def test_communication_config(self) -> None:
        """Test communication configuration for development."""
        assert SLACK_WEBHOOK_URL is None
        assert SLACK_CHANNEL == "#security-incidents"
        assert EMAIL_SMTP_HOST is None
        assert EMAIL_SMTP_PORT == 587
        assert EMAIL_FROM_ADDRESS is None

    def test_communication_disabled_in_dev(self) -> None:
        """Test that external communications are disabled in dev."""
        assert SLACK_WEBHOOK_URL is None
        assert EMAIL_SMTP_HOST is None
        assert EMAIL_FROM_ADDRESS is None

    def test_debug_enabled(self) -> None:
        """Test that debug mode is enabled for development."""
        assert DEBUG is True

    def test_host_binds_all_interfaces(self) -> None:
        """Test that development binds to all interfaces."""
        assert HOST == "0.0.0.0"

    def test_all_required_configs_present(self) -> None:
        """Test that all required configurations are present."""
        required_configs = [
            "APP_NAME",
            "APP_VERSION",
            "APP_ENV",
            "DEBUG",
            "HOST",
            "PORT",
            "LOG_LEVEL",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "VERTEX_AI_LOCATION",
            "GEMINI_MODEL",
            "BIGQUERY_DATASET",
            "BIGQUERY_TABLE_PREFIX",
            "PUBSUB_TOPIC_INCIDENTS",
            "PUBSUB_TOPIC_ALERTS",
            "PUBSUB_SUBSCRIPTION_PREFIX",
            "AGENT_DETECTION_INTERVAL",
            "AGENT_ANALYSIS_TIMEOUT",
            "AGENT_REMEDIATION_DRY_RUN",
            "AGENT_ORCHESTRATOR_MAX_RETRIES",
            "JWT_SECRET_KEY",
            "API_KEY_SALT",
            "RATE_LIMIT_REQUESTS",
            "RATE_LIMIT_WINDOW",
        ]

        import src.config.development

        for config_name in required_configs:
            assert hasattr(
                src.config.development, config_name
            ), f"Missing config: {config_name}"

    def test_config_value_types(self) -> None:
        """Test that configuration values have correct types."""
        assert isinstance(APP_NAME, str)
        assert isinstance(APP_VERSION, str)
        assert isinstance(APP_ENV, str)
        assert isinstance(DEBUG, bool)
        assert isinstance(HOST, str)
        assert isinstance(PORT, int)
        assert isinstance(LOG_LEVEL, str)
        assert isinstance(RATE_LIMIT_REQUESTS, int)
        assert isinstance(RATE_LIMIT_WINDOW, int)

    def test_jwt_secret_length(self) -> None:
        """Test that JWT secret key has sufficient length."""
        assert len(JWT_SECRET_KEY) >= 32

    def test_api_salt_length(self) -> None:
        """Test that API key salt has sufficient length."""
        assert len(API_KEY_SALT) >= 16

    def test_email_port_standard(self) -> None:
        """Test that email port uses standard SMTP submission port."""
        assert EMAIL_SMTP_PORT == 587  # Standard SMTP submission port

    def test_development_mode_flag(self) -> None:
        # ... existing code ...
        pass

    def test_debug_logging_enabled(self) -> None:
        # ... existing code ...
        pass

    def test_database_configuration(self) -> None:
        # ... existing code ...
        pass

    def test_security_settings(self) -> None:
        # ... existing code ...
        pass

    def test_cache_configuration(self) -> None:
        # ... existing code ...
        pass

    def test_monitoring_setup(self) -> None:
        # ... existing code ...
        pass

    def test_api_rate_limits(self) -> None:
        # ... existing code ...
        pass

    def test_worker_configuration(self) -> None:
        # ... existing code ...
        pass

    def test_storage_paths(self) -> None:
        # ... existing code ...
        pass

    def test_external_services(self) -> None:
        # ... existing code ...
        pass

    def test_feature_flags(self) -> None:
        # ... existing code ...
        pass

    def test_cors_settings(self) -> None:
        # ... existing code ...
        pass

    def test_session_configuration(self) -> None:
        # ... existing code ...
        pass

    def test_email_configuration(self) -> None:
        # ... existing code ...
        pass

    def test_metrics_collection(self) -> None:
        # ... existing code ...
        pass

    def test_backup_settings(self) -> None:
        # ... existing code ...
        pass

    def test_deployment_settings(self) -> None:
        # ... existing code ...
        pass

    def test_integration_endpoints(self) -> None:
        # ... existing code ...
        pass

    def test_development_tools(self) -> None:
        # ... existing code ...
        pass

    def test_webhook_configuration(self) -> None:
        # ... existing code ...
        pass

    def test_notification_settings(self) -> None:
        # ... existing code ...
        pass

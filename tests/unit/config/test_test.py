"""Tests for test configuration using real production code."""

import os

from src.config.test import (
    ANALYSIS_AGENT_TIMEOUT,
    API_KEY_SALT,
    APP_ENV,
    APP_NAME,
    APP_VERSION,
    BIGQUERY_DATASET,
    BIGQUERY_LOCATION,
    BIGQUERY_TABLE_PREFIX,
    DEBUG,
    DETECTION_AGENT_INTERVAL,
    EMAIL_FROM_ADDRESS,
    EMAIL_FROM_NAME,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PASSWORD,
    EMAIL_SMTP_PORT,
    EMAIL_SMTP_USER,
    FIRESTORE_COLLECTION_PREFIX,
    FIRESTORE_DATABASE,
    FIXTURE_PATH,
    GOOGLE_APPLICATION_CREDENTIALS,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_REGION,
    GOOGLE_CLOUD_ZONE,
    HOST,
    JWT_ALGORITHM,
    JWT_EXPIRATION_DELTA,
    JWT_SECRET_KEY,
    LOG_BACKUP_COUNT,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_MAX_BYTES,
    MOCK_EXTERNAL_SERVICES,
    ORCHESTRATOR_AGENT_MAX_RETRIES,
    PORT,
    PUBSUB_SUBSCRIPTION_PREFIX,
    PUBSUB_TOPIC_ALERTS,
    PUBSUB_TOPIC_INCIDENTS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    REMEDIATION_AGENT_DRY_RUN,
    SLACK_CHANNEL,
    SLACK_ICON_EMOJI,
    SLACK_USERNAME,
    SLACK_WEBHOOK_URL,
    TEST_MODE,
    USE_FIXTURES,
    VERTEX_AI_LOCATION,
    VERTEX_AI_MAX_OUTPUT_TOKENS,
    VERTEX_AI_MODEL,
    VERTEX_AI_TEMPERATURE,
)


class TestTestConfiguration:
    """Test cases for test environment configuration with real production code."""

    @classmethod
    def setup_class(cls) -> None:
        """Set test mode to avoid config validation errors."""
        os.environ["SENTINELOPS_TEST_MODE"] = "true"

    def test_app_config(self) -> None:
        """Test application configuration for test environment."""
        assert APP_NAME == "SentinelOps"
        assert APP_VERSION == "1.0.0-test"
        assert APP_ENV == "test"
        assert DEBUG is True
        assert HOST == "0.0.0.0"
        assert PORT == 8080

    def test_test_version_suffix(self) -> None:
        """Test that version has test suffix."""
        assert APP_VERSION.endswith("-test")

    def test_logging_config(self) -> None:
        """Test logging configuration for test environment."""
        assert LOG_LEVEL == "DEBUG"
        assert LOG_FORMAT == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert LOG_FILE == "logs/test/sentinelops.log"
        assert LOG_MAX_BYTES == 10485760  # 10MB
        assert LOG_BACKUP_COUNT == 5

    def test_log_file_in_test_directory(self) -> None:
        """Test that log file is in test subdirectory."""
        assert "test" in LOG_FILE

    def test_google_cloud_config(self) -> None:
        """Test Google Cloud configuration for test environment."""
        assert GOOGLE_CLOUD_PROJECT == "test-project"
        assert GOOGLE_CLOUD_REGION == "us-central1"
        assert GOOGLE_CLOUD_ZONE == "us-central1-a"
        assert GOOGLE_APPLICATION_CREDENTIALS is None  # Mock credentials

    def test_vertex_ai_config(self) -> None:
        """Test Vertex AI configuration for test environment."""
        assert VERTEX_AI_LOCATION == "us-central1"
        assert VERTEX_AI_MODEL == "gemini-1.5-pro"
        assert VERTEX_AI_TEMPERATURE == 0.7
        assert VERTEX_AI_MAX_OUTPUT_TOKENS == 2048

    def test_bigquery_config(self) -> None:
        """Test BigQuery configuration for test environment."""
        assert BIGQUERY_DATASET == "test_sentinel_ops"
        assert BIGQUERY_TABLE_PREFIX == "test_sentinel_"
        assert BIGQUERY_LOCATION == "US"

    def test_test_prefixes(self) -> None:
        """Test that resources have test prefixes."""
        assert BIGQUERY_DATASET.startswith("test_")
        assert BIGQUERY_TABLE_PREFIX.startswith("test_")
        assert FIRESTORE_COLLECTION_PREFIX.startswith("test_")
        assert PUBSUB_TOPIC_INCIDENTS.startswith("test-")
        assert PUBSUB_TOPIC_ALERTS.startswith("test-")
        assert PUBSUB_SUBSCRIPTION_PREFIX.startswith("test-")

    def test_pubsub_config(self) -> None:
        """Test Pub/Sub configuration for test environment."""
        assert PUBSUB_TOPIC_INCIDENTS == "test-sentinel-incidents"
        assert PUBSUB_TOPIC_ALERTS == "test-sentinel-alerts"
        assert PUBSUB_SUBSCRIPTION_PREFIX == "test-sentinel-sub-"

    def test_firestore_config(self) -> None:
        """Test Firestore configuration for test environment."""
        assert FIRESTORE_DATABASE == "(default)"
        assert FIRESTORE_COLLECTION_PREFIX == "test_"

    def test_agent_config(self) -> None:
        """Test agent configuration for test environment."""
        assert DETECTION_AGENT_INTERVAL == 60
        assert ANALYSIS_AGENT_TIMEOUT == 300
        assert REMEDIATION_AGENT_DRY_RUN is True
        assert ORCHESTRATOR_AGENT_MAX_RETRIES == 3

    def test_agent_config_types(self) -> None:
        """Test agent configuration types."""
        assert isinstance(DETECTION_AGENT_INTERVAL, int)
        assert isinstance(ANALYSIS_AGENT_TIMEOUT, int)
        assert isinstance(REMEDIATION_AGENT_DRY_RUN, bool)
        assert isinstance(ORCHESTRATOR_AGENT_MAX_RETRIES, int)

    def test_security_config(self) -> None:
        """Test security configuration for test environment."""
        assert JWT_SECRET_KEY == "test-jwt-secret-key-for-testing-only-do-not-use"
        assert JWT_ALGORITHM == "HS256"
        assert JWT_EXPIRATION_DELTA == 3600  # 1 hour
        assert API_KEY_SALT == "test-api-salt-key-for-testing"
        assert RATE_LIMIT_REQUESTS == 100
        assert RATE_LIMIT_WINDOW == 60

    def test_security_test_warnings(self) -> None:
        """Test that security keys have test warnings."""
        assert "test" in JWT_SECRET_KEY.lower()
        assert "testing" in JWT_SECRET_KEY.lower()
        assert "do-not-use" in JWT_SECRET_KEY.lower()
        assert "test" in API_KEY_SALT.lower()

    def test_communication_config(self) -> None:
        """Test communication configuration for test environment."""
        assert SLACK_WEBHOOK_URL == ""
        assert SLACK_CHANNEL == "#test-alerts"
        assert SLACK_USERNAME == "SentinelOps Test"
        assert SLACK_ICON_EMOJI == ":robot_face:"

        assert EMAIL_SMTP_HOST == "localhost"
        assert EMAIL_SMTP_PORT == 25
        assert EMAIL_SMTP_USER == ""
        assert EMAIL_SMTP_PASSWORD == ""
        assert EMAIL_FROM_ADDRESS == "test@example.com"
        assert EMAIL_FROM_NAME == "SentinelOps Test"

    def test_communication_disabled(self) -> None:
        """Test that external communications are disabled."""
        assert SLACK_WEBHOOK_URL == ""
        assert EMAIL_SMTP_USER == ""
        assert EMAIL_SMTP_PASSWORD == ""

    def test_test_specific_config(self) -> None:
        """Test configuration specific to test environment."""
        assert TEST_MODE is True
        assert MOCK_EXTERNAL_SERVICES is True
        assert USE_FIXTURES is True
        assert FIXTURE_PATH == "tests/fixtures"

    def test_test_flags_enabled(self) -> None:
        """Test that all test flags are enabled."""
        assert TEST_MODE is True
        assert MOCK_EXTERNAL_SERVICES is True
        assert USE_FIXTURES is True
        assert DEBUG is True

    def test_dry_run_enabled(self) -> None:
        """Test that dry run is enabled for safety."""
        assert REMEDIATION_AGENT_DRY_RUN is True

    def test_localhost_email(self) -> None:
        """Test that email uses localhost for testing."""
        assert EMAIL_SMTP_HOST == "localhost"
        assert EMAIL_SMTP_PORT == 25

    def test_example_email(self) -> None:
        """Test that email uses example.com domain."""
        assert EMAIL_FROM_ADDRESS.endswith("@example.com")

    def test_test_channel_prefix(self) -> None:
        """Test that Slack channel has test prefix."""
        assert SLACK_CHANNEL.startswith("#test")

    def test_log_rotation_config(self) -> None:
        """Test log rotation configuration."""
        assert LOG_MAX_BYTES == 10485760  # 10MB
        assert LOG_BACKUP_COUNT == 5
        assert isinstance(LOG_MAX_BYTES, int)
        assert isinstance(LOG_BACKUP_COUNT, int)

    def test_vertex_ai_params(self) -> None:
        """Test Vertex AI parameter ranges."""
        assert 0 <= VERTEX_AI_TEMPERATURE <= 1.0
        assert VERTEX_AI_MAX_OUTPUT_TOKENS > 0
        assert isinstance(VERTEX_AI_TEMPERATURE, float)
        assert isinstance(VERTEX_AI_MAX_OUTPUT_TOKENS, int)

    def test_jwt_expiration(self) -> None:
        """Test JWT expiration is reasonable for testing."""
        assert JWT_EXPIRATION_DELTA == 3600  # 1 hour
        assert JWT_EXPIRATION_DELTA > 0

    def test_rate_limiting_reasonable(self) -> None:
        """Test rate limiting is reasonable for testing."""
        assert RATE_LIMIT_REQUESTS == 100
        assert RATE_LIMIT_WINDOW == 60
        assert RATE_LIMIT_REQUESTS > 0
        assert RATE_LIMIT_WINDOW > 0

    def test_all_test_configs_defined(self) -> None:
        """Test that all test configurations are defined."""
        test_configs = [
            "APP_NAME",
            "APP_VERSION",
            "APP_ENV",
            "DEBUG",
            "HOST",
            "PORT",
            "LOG_LEVEL",
            "LOG_FORMAT",
            "LOG_FILE",
            "LOG_MAX_BYTES",
            "LOG_BACKUP_COUNT",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_REGION",
            "GOOGLE_CLOUD_ZONE",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "VERTEX_AI_LOCATION",
            "VERTEX_AI_MODEL",
            "VERTEX_AI_TEMPERATURE",
            "VERTEX_AI_MAX_OUTPUT_TOKENS",
            "BIGQUERY_DATASET",
            "BIGQUERY_TABLE_PREFIX",
            "BIGQUERY_LOCATION",
            "PUBSUB_TOPIC_INCIDENTS",
            "PUBSUB_TOPIC_ALERTS",
            "PUBSUB_SUBSCRIPTION_PREFIX",
            "FIRESTORE_DATABASE",
            "FIRESTORE_COLLECTION_PREFIX",
            "DETECTION_AGENT_INTERVAL",
            "ANALYSIS_AGENT_TIMEOUT",
            "REMEDIATION_AGENT_DRY_RUN",
            "ORCHESTRATOR_AGENT_MAX_RETRIES",
            "JWT_SECRET_KEY",
            "JWT_ALGORITHM",
            "JWT_EXPIRATION_DELTA",
            "API_KEY_SALT",
            "RATE_LIMIT_REQUESTS",
            "RATE_LIMIT_WINDOW",
            "SLACK_WEBHOOK_URL",
            "SLACK_CHANNEL",
            "SLACK_USERNAME",
            "SLACK_ICON_EMOJI",
            "EMAIL_SMTP_HOST",
            "EMAIL_SMTP_PORT",
            "EMAIL_SMTP_USER",
            "EMAIL_SMTP_PASSWORD",
            "EMAIL_FROM_ADDRESS",
            "EMAIL_FROM_NAME",
            "TEST_MODE",
            "MOCK_EXTERNAL_SERVICES",
            "USE_FIXTURES",
            "FIXTURE_PATH",
        ]

        import src.config.test

        for config_name in test_configs:
            assert hasattr(
                src.config.test, config_name
            ), f"Missing config: {config_name}"

    def test_debug_enabled_for_testing(self) -> None:
        """Test that debug mode is enabled for test environment."""
        assert DEBUG is True
        assert LOG_LEVEL == "DEBUG"

    def test_port_different_from_default(self) -> None:
        """Test that test port is different from default."""
        assert PORT == 8080  # Different from default 8000

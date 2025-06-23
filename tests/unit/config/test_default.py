"""Tests for default configuration using real production code."""

import os
import sys
from pathlib import Path

from src.config.default import (
    AGENT_ANALYSIS_TIMEOUT,
    AGENT_DETECTION_INTERVAL,
    AGENT_ORCHESTRATOR_MAX_RETRIES,
    AGENT_REMEDIATION_DRY_RUN,
    API_KEY_SALT,
    APP_ENV,
    APP_NAME,
    APP_VERSION,
    BASE_DIR,
    BIGQUERY_DATASET,
    BIGQUERY_TABLE_PREFIX,
    DEBUG,
    GCS_BUCKET_NAME,
    GCS_LOGS_PREFIX,
    GEMINI_MODEL,
    GOOGLE_APPLICATION_CREDENTIALS,
    GOOGLE_CLOUD_PROJECT,
    HOST,
    JWT_SECRET_KEY,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    PORT,
    PUBSUB_SUBSCRIPTION_PREFIX,
    PUBSUB_TOPIC_ALERTS,
    PUBSUB_TOPIC_INCIDENTS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    VERTEX_AI_LOCATION,
)


class TestDefaultConfiguration:
    """Test cases for default configuration with real production code."""

    @classmethod
    def setup_class(cls) -> None:
        """Set test mode to avoid config validation errors."""
        os.environ["SENTINELOPS_TEST_MODE"] = "true"
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    def test_base_constants(self) -> None:
        """Test base application constants."""
        assert APP_NAME == "SentinelOps"
        assert APP_VERSION == "0.1.0"
        assert isinstance(BASE_DIR, Path)
        assert BASE_DIR.name == "SentinelOps"  # Project root directory

    def test_log_format(self) -> None:
        """Test log format string."""
        assert LOG_FORMAT == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT
        assert "%(message)s" in LOG_FORMAT

    def test_log_file_path(self) -> None:
        """Test log file path construction."""
        assert isinstance(LOG_FILE, Path)
        assert LOG_FILE.parent.name == "logs"
        assert LOG_FILE.name == "sentinelops.log"

    def test_app_env_current_value(self) -> None:
        """Test APP_ENV current value in real environment."""
        # Test the actual current value
        assert isinstance(APP_ENV, str)
        assert APP_ENV in ["development", "test", "production"]

    def test_debug_mode_current_value(self) -> None:
        """Test DEBUG mode current value."""
        # Test the actual current value
        assert isinstance(DEBUG, bool)

    def test_server_config_current_values(self) -> None:
        """Test server configuration current values."""
        # Test actual current values
        assert isinstance(HOST, str)
        assert isinstance(PORT, int)
        assert PORT > 0 and PORT < 65536

    def test_port_type_conversion(self) -> None:
        """Test that PORT is properly converted to integer."""
        assert isinstance(PORT, int)

    def test_log_level_current_value(self) -> None:
        """Test log level current value."""
        # Test actual current value
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_google_cloud_config_current_values(self) -> None:
        """Test Google Cloud configuration current values."""
        # Test actual current values - may be None or set
        if GOOGLE_CLOUD_PROJECT is not None:
            assert isinstance(GOOGLE_CLOUD_PROJECT, str)
        if GOOGLE_APPLICATION_CREDENTIALS is not None:
            assert isinstance(GOOGLE_APPLICATION_CREDENTIALS, str)

    def test_vertex_ai_defaults(self) -> None:
        """Test Vertex AI default values."""
        # These should use defaults when env vars not set
        assert VERTEX_AI_LOCATION == "us-central1"
        assert GEMINI_MODEL == "gemini-1.5-pro"

    def test_vertex_ai_current_values(self) -> None:
        """Test Vertex AI configuration current values."""
        # Test actual current values
        assert isinstance(VERTEX_AI_LOCATION, str)
        assert isinstance(GEMINI_MODEL, str)
        assert GEMINI_MODEL.startswith("gemini-")

    def test_bigquery_defaults(self) -> None:
        """Test BigQuery default values."""
        assert BIGQUERY_DATASET == "security_logs"
        assert BIGQUERY_TABLE_PREFIX == "sentinel_"

    def test_gcs_defaults(self) -> None:
        """Test Cloud Storage default values."""
        assert GCS_BUCKET_NAME == "sentinelops-data"
        assert GCS_LOGS_PREFIX == "logs/"

    def test_pubsub_defaults(self) -> None:
        """Test Pub/Sub default values."""
        assert PUBSUB_TOPIC_INCIDENTS == "sentinelops-incidents"
        assert PUBSUB_TOPIC_ALERTS == "sentinelops-alerts"
        assert PUBSUB_SUBSCRIPTION_PREFIX == "sentinelops-sub-"

    def test_agent_config_defaults(self) -> None:
        """Test agent configuration default values."""
        assert AGENT_DETECTION_INTERVAL == 30
        assert AGENT_ANALYSIS_TIMEOUT == 300
        assert AGENT_REMEDIATION_DRY_RUN is True
        assert AGENT_ORCHESTRATOR_MAX_RETRIES == 3

    def test_agent_config_types(self) -> None:
        """Test agent configuration type conversions."""
        assert isinstance(AGENT_DETECTION_INTERVAL, int)
        assert isinstance(AGENT_ANALYSIS_TIMEOUT, int)
        assert isinstance(AGENT_REMEDIATION_DRY_RUN, bool)
        assert isinstance(AGENT_ORCHESTRATOR_MAX_RETRIES, int)

    def test_agent_dry_run_current_value(self) -> None:
        """Test agent dry run mode current value."""
        # Test actual current value
        assert isinstance(AGENT_REMEDIATION_DRY_RUN, bool)

    def test_security_defaults(self) -> None:
        """Test security configuration defaults."""
        assert JWT_SECRET_KEY == "change-this-in-production"
        assert API_KEY_SALT == "change-this-in-production"

    def test_security_current_values(self) -> None:
        """Test security configuration current values."""
        # Test actual current values
        assert isinstance(JWT_SECRET_KEY, str)
        assert isinstance(API_KEY_SALT, str)
        assert len(JWT_SECRET_KEY) > 0
        assert len(API_KEY_SALT) > 0

    def test_rate_limit_defaults(self) -> None:
        """Test rate limiting default values."""
        assert RATE_LIMIT_REQUESTS == 100
        assert RATE_LIMIT_WINDOW == 60

    def test_rate_limit_types(self) -> None:
        """Test rate limiting type conversions."""
        assert isinstance(RATE_LIMIT_REQUESTS, int)
        assert isinstance(RATE_LIMIT_WINDOW, int)

    def test_rate_limit_current_values(self) -> None:
        """Test rate limiting current values."""
        # Test actual current values
        assert RATE_LIMIT_REQUESTS > 0
        assert RATE_LIMIT_WINDOW > 0

    def test_google_cloud_values_type(self) -> None:
        """Test that Google Cloud values have correct types."""
        # These can be None or string
        assert GOOGLE_CLOUD_PROJECT is None or isinstance(GOOGLE_CLOUD_PROJECT, str)
        assert GOOGLE_APPLICATION_CREDENTIALS is None or isinstance(
            GOOGLE_APPLICATION_CREDENTIALS, str
        )

    def test_path_construction(self) -> None:
        """Test that paths are properly constructed."""
        # BASE_DIR should be 3 levels up from the config file
        config_file = Path(__file__).resolve()
        expected_base = config_file.parent.parent.parent.parent
        assert BASE_DIR == expected_base

        # LOG_FILE should be under BASE_DIR/logs
        assert LOG_FILE.parent == BASE_DIR / "logs"

    def test_config_value_types(self) -> None:
        """Test that all config values have correct types."""
        # Test numeric values are properly typed
        assert isinstance(AGENT_DETECTION_INTERVAL, int)
        assert isinstance(AGENT_ANALYSIS_TIMEOUT, int)
        assert isinstance(AGENT_ORCHESTRATOR_MAX_RETRIES, int)
        assert isinstance(RATE_LIMIT_REQUESTS, int)
        assert isinstance(RATE_LIMIT_WINDOW, int)
        assert isinstance(PORT, int)

    def test_all_config_values_defined(self) -> None:
        """Test that all expected configuration values are defined."""
        expected_configs = [
            "APP_NAME",
            "APP_VERSION",
            "APP_ENV",
            "DEBUG",
            "HOST",
            "PORT",
            "LOG_LEVEL",
            "LOG_FORMAT",
            "LOG_FILE",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "VERTEX_AI_LOCATION",
            "GEMINI_MODEL",
            "BIGQUERY_DATASET",
            "BIGQUERY_TABLE_PREFIX",
            "GCS_BUCKET_NAME",
            "GCS_LOGS_PREFIX",
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

        import src.config.default

        for config_name in expected_configs:
            assert hasattr(
                src.config.default, config_name
            ), f"Missing config: {config_name}"

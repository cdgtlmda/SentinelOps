"""
Configuration loading and validation utilities for SentinelOps.

This module provides functionality to load, validate, and manage configuration
from YAML files with environment variable overrides.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    field: str
    message: str

    def __str__(self) -> str:
        return f"Configuration error for '{self.field}': {self.message}"


class ConfigLoader:
    """
    Loads and manages configuration for SentinelOps.

    Supports:
    - Loading from YAML files
    - Environment variable overrides
    - Configuration validation
    - Default values
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to the configuration file. If not provided,
                        looks for CONFIG_PATH env var or uses default.
        """
        self.logger = logging.getLogger(__name__)

        # Determine config file path
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Check environment variable
            env_config_path = os.environ.get("SENTINELOPS_CONFIG_PATH")
            if env_config_path:
                self.config_path = Path(env_config_path)
            else:
                # Use default path
                self.config_path = (
                    Path(__file__).parent.parent.parent / "config" / "config.yaml"
                )

        self._config: Dict[str, Any] = {}
        self._env_overrides: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file and apply environment overrides.

        Returns:
            The loaded and validated configuration dictionary

        Raises:
            ConfigValidationError: If configuration is invalid
            FileNotFoundError: If configuration file not found
        """
        # Load from YAML file
        self._load_from_file()

        # Apply defaults before env overrides
        self._apply_defaults()

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Validate configuration
        self._validate()

        return self._config

    def _load_from_file(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            self.logger.info("Loaded configuration from %s", self.config_path)
        except yaml.YAMLError as e:
            raise ConfigValidationError(
                "yaml_parse", f"Failed to parse YAML: {e}"
            ) from e
        except Exception as e:
            raise ConfigValidationError(
                "file_read", f"Failed to read config file: {e}"
            ) from e

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Define environment variable mappings
        env_mappings = {
            "SENTINELOPS_PROJECT_ID": "google_cloud.project_id",
            "SENTINELOPS_REGION": "google_cloud.region",
            "SENTINELOPS_DEBUG": "development.debug",
            "SENTINELOPS_TEST_MODE": "development.test_mode",
            "SENTINELOPS_DRY_RUN": "development.dry_run",
            "SMTP_HOST": "agents.communication.channels.email.smtp_host",
            "SMTP_PORT": "agents.communication.channels.email.smtp_port",
            "SMTP_USERNAME": "agents.communication.channels.email.username",
            "SMTP_PASSWORD": "agents.communication.channels.email.password",
            "SLACK_WEBHOOK_URL": "agents.communication.channels.slack.webhook_url",
        }

        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                self._set_nested_value(config_path, value)
                self._env_overrides[config_path] = value
                self.logger.debug(
                    "Applied env override: %s -> %s", env_var, config_path
                )

    def _set_nested_value(self, path: str, value: Any) -> None:
        """
        Set a nested value in the configuration dictionary.

        Args:
            path: Dot-separated path to the value (e.g., 'google_cloud.project_id')
            value: Value to set
        """
        keys = path.split(".")
        current = self._config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value, converting types as needed
        final_key = keys[-1]
        if isinstance(value, str):
            # Try to convert string values to appropriate types
            if value.lower() in ("true", "false"):
                current[final_key] = value.lower() == "true"
            elif value.isdigit():
                current[final_key] = int(value)
            elif "." in value and all(part.isdigit() for part in value.split(".", 1)):
                current[final_key] = float(value)
            else:
                current[final_key] = value
        else:
            current[final_key] = value

    def _validate(self) -> None:
        """Validate the loaded configuration."""
        # Check required fields
        required_fields = [
            ("google_cloud.project_id", "Google Cloud project ID"),
            ("google_cloud.region", "Google Cloud region"),
            ("google_cloud.bigquery.dataset", "BigQuery dataset"),
            ("google_cloud.pubsub.topics.detection_events", "Detection events topic"),
        ]

        for field_path, description in required_fields:
            value = self.get(field_path)
            if not value:
                raise ConfigValidationError(field_path, f"{description} is required")

            # Type validation for required fields
            if field_path == "google_cloud.project_id" and not isinstance(value, str):
                raise ConfigValidationError(
                    field_path, f"{description} must be a string type"
                )

            if field_path == "google_cloud.pubsub.topics.detection_events":
                # Check parent is dict
                topics = self.get("google_cloud.pubsub.topics")
                if not isinstance(topics, dict):
                    raise ConfigValidationError(
                        "google_cloud.pubsub.topics", "Topics must be a dictionary type"
                    )

        # Validate specific value ranges
        if self.get("development.debug") not in (True, False, None):
            raise ConfigValidationError("development.debug", "Must be a boolean value")

        # Validate Gemini configuration if present
        self._validate_gemini_config()

        # Validate security settings if present
        self._validate_security_config()

        # Validate performance settings if present
        self._validate_performance_config()

        # Validate agent configurations
        for agent_type in [
            "detection",
            "analysis",
            "remediation",
            "communication",
            "orchestrator",
        ]:
            agent_config = self.get(f"agents.{agent_type}")
            if not agent_config:
                self.logger.warning("No configuration found for %s agent", agent_type)
            else:
                self._validate_agent_config(agent_type, agent_config)

    def _validate_gemini_config(self) -> None:
        """Validate Gemini API configuration."""
        gemini_config = self.get("google_cloud.gemini")
        if not gemini_config:
            return

        # Validate numeric fields
        numeric_fields = [
            ("requests_per_minute", 1, 10000),
            ("temperature", 0.0, 1.0),
            ("connection_pool_size", 1, 100),
            ("max_workers", 1, 100),
        ]

        for field, min_val, max_val in numeric_fields:
            value = gemini_config.get(field)
            if value is not None:
                if not isinstance(value, (int, float)):
                    raise ConfigValidationError(
                        f"google_cloud.gemini.{field}", "Must be a numeric value"
                    )
                if value < min_val or value > max_val:
                    raise ConfigValidationError(
                        f"google_cloud.gemini.{field}",
                        f"Must be between {min_val} and {max_val}",
                    )

    def _validate_security_config(self) -> None:
        """Validate security configuration."""
        security_config = self.get("security")
        if not security_config:
            return

        # Validate boolean fields
        if "require_authentication" in security_config:
            if not isinstance(security_config["require_authentication"], bool):
                raise ConfigValidationError(
                    "security.require_authentication", "Must be a boolean value"
                )

        # Validate audit logging
        audit_config = security_config.get("audit_logging", {})
        if "retention_days" in audit_config:
            retention = audit_config["retention_days"]
            if not isinstance(retention, int) or retention <= 0:
                raise ConfigValidationError(
                    "security.audit_logging.retention_days",
                    "Must be a positive integer",
                )

    def _validate_performance_config(self) -> None:
        """Validate performance configuration."""
        perf_config = self.get("performance")
        if not perf_config:
            return

        # Validate memory limit
        if "max_memory_mb" in perf_config:
            memory = perf_config["max_memory_mb"]
            if not isinstance(memory, (int, float)) or memory <= 0:
                raise ConfigValidationError(
                    "performance.max_memory_mb", "Must be a positive numeric value"
                )

        # Validate CPU percentage
        if "max_cpu_percentage" in perf_config:
            cpu = perf_config["max_cpu_percentage"]
            if not isinstance(cpu, (int, float)) or cpu <= 0 or cpu > 100:
                raise ConfigValidationError(
                    "performance.max_cpu_percentage", "Must be between 0 and 100"
                )

        # Validate connection timeout
        if "connection_timeout" in perf_config:
            timeout = perf_config["connection_timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ConfigValidationError(
                    "performance.connection_timeout", "Must be a positive numeric value"
                )

    def _validate_agent_config(self, agent_type: str, config: Dict[str, Any]) -> None:
        """Validate agent-specific configuration."""
        validators = {
            "detection": self._validate_detection_agent,
            "analysis": self._validate_analysis_agent,
            "remediation": self._validate_remediation_agent,
        }

        validator = validators.get(agent_type)
        if validator:
            validator(config)

    def _validate_detection_agent(self, config: Dict[str, Any]) -> None:
        """Validate detection agent configuration."""
        self._validate_positive_numeric(
            config, "polling_interval", "agents.detection.polling_interval"
        )
        self._validate_positive_integer(
            config, "batch_size", "agents.detection.batch_size"
        )
        self._validate_dict_field(
            config, "severity_thresholds", "agents.detection.severity_thresholds"
        )

    def _validate_analysis_agent(self, config: Dict[str, Any]) -> None:
        """Validate analysis agent configuration."""
        self._validate_positive_numeric(config, "timeout", "agents.analysis.timeout")
        self._validate_confidence_thresholds(config)

    def _validate_remediation_agent(self, config: Dict[str, Any]) -> None:
        """Validate remediation agent configuration."""
        self._validate_non_negative_integer(
            config, "max_retries", "agents.remediation.max_retries"
        )
        self._validate_positive_numeric(
            config, "action_timeout", "agents.remediation.action_timeout"
        )
        self._validate_auto_remediation(config)

    def _validate_positive_numeric(
        self, config: Dict[str, Any], field: str, path: str
    ) -> None:
        """Validate that a field is a positive numeric value."""
        if field in config:
            value = config[field]
            if not isinstance(value, (int, float)) or value <= 0:
                raise ConfigValidationError(path, "Must be a positive numeric value")

    def _validate_positive_integer(
        self, config: Dict[str, Any], field: str, path: str
    ) -> None:
        """Validate that a field is a positive integer."""
        if field in config:
            value = config[field]
            if not isinstance(value, int) or value <= 0:
                raise ConfigValidationError(path, "Must be a positive integer")

    def _validate_non_negative_integer(
        self, config: Dict[str, Any], field: str, path: str
    ) -> None:
        """Validate that a field is a non-negative integer."""
        if field in config:
            value = config[field]
            if not isinstance(value, int) or value < 0:
                raise ConfigValidationError(path, "Must be a non-negative integer")

    def _validate_dict_field(
        self, config: Dict[str, Any], field: str, path: str
    ) -> None:
        """Validate that a field is a dictionary."""
        if field in config:
            value = config[field]
            if not isinstance(value, dict):
                raise ConfigValidationError(path, "Must be a dictionary")

    def _validate_confidence_thresholds(self, config: Dict[str, Any]) -> None:
        """Validate confidence thresholds."""
        if "confidence_thresholds" in config:
            thresholds = config["confidence_thresholds"]
            if isinstance(thresholds, dict):
                for key, value in thresholds.items():
                    if not isinstance(value, (int, float)) or value < 0 or value > 1:
                        raise ConfigValidationError(
                            f"agents.analysis.confidence_thresholds.{key}",
                            "Must be between 0 and 1",
                        )

    def _validate_auto_remediation(self, config: Dict[str, Any]) -> None:
        """Validate auto remediation configuration."""
        if "auto_remediation" in config:
            auto_config = config["auto_remediation"]
            if isinstance(auto_config, dict):
                if "enabled" in auto_config and not isinstance(
                    auto_config["enabled"], bool
                ):
                    raise ConfigValidationError(
                        "agents.remediation.auto_remediation.enabled",
                        "Must be a boolean value",
                    )
                if "allowed_actions" in auto_config and not isinstance(
                    auto_config["allowed_actions"], list
                ):
                    raise ConfigValidationError(
                        "agents.remediation.auto_remediation.allowed_actions",
                        "Must be a list",
                    )

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by path.

        Args:
            path: Dot-separated path to the value (e.g., 'google_cloud.project_id')
            default: Default value if path not found

        Returns:
            The configuration value or default
        """
        keys = path.split(".")
        current = self._config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.

        Args:
            agent_type: Type of agent (e.g., 'detection', 'analysis')

        Returns:
            Agent configuration dictionary
        """
        agent_config: Dict[str, Any] = self.get(f"agents.{agent_type}", {})

        # Add common configuration
        agent_config["project_id"] = self.get("google_cloud.project_id")
        agent_config["region"] = self.get("google_cloud.region")
        agent_config["debug"] = self.get("development.debug", False)
        agent_config["use_cloud_logging"] = not self.get("development.test_mode", False)

        return agent_config

    def reload(self) -> Dict[str, Any]:
        """Reload configuration from file."""
        self._config = {}
        self._env_overrides = {}
        return self.load()

    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._config.copy()

    def save_to_file(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to a file.

        Args:
            path: Path to save to. If not provided, uses original path.
        """
        save_path = Path(path) if path else self.config_path

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)

        self.logger.info("Saved configuration to %s", save_path)

    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field name indicates sensitive data."""
        sensitive_patterns = [
            "api_key",
            "apikey",
            "api-key",
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "auth",
            "private_key",
            "privatekey",
            "private-key",
            "webhook_url",
            "webhook-url",
            "credential",
            "cred",
        ]
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in sensitive_patterns)

    def _log_configuration_summary(self) -> None:
        """Log configuration summary with sensitive data masked."""

        def mask_sensitive(config: Dict[str, Any], path: str = "") -> Dict[str, Any]:
            """Recursively mask sensitive values in configuration."""
            masked: Dict[str, Any] = {}
            for key, value in config.items():
                current_path = f"{path}.{key}" if path else key

                if self._is_sensitive_field(key):
                    masked[key] = "***MASKED***"
                elif isinstance(value, dict):
                    masked[key] = mask_sensitive(value, current_path)
                else:
                    masked[key] = value
            return masked

        masked_config = mask_sensitive(self._config)
        self.logger.info("Configuration loaded: %s", masked_config)

    def _apply_defaults(self) -> None:
        """Apply default values to configuration."""
        # This method would apply default values for optional fields
        # For now, it's a placeholder that extended tests expect


# Global configuration instance
_config_loader: Optional[ConfigLoader] = None


def get_config() -> Dict[str, Any]:
    """Get the global configuration instance."""
    global _config_loader  # pylint: disable=global-statement
    if _config_loader is None:
        _config_loader = ConfigLoader()
        _config_loader.load()
    return _config_loader.to_dict()


def get_config_value(path: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    global _config_loader  # pylint: disable=global-statement
    if _config_loader is None:
        _config_loader = ConfigLoader()
        _config_loader.load()
    return _config_loader.get(path, default)


def reload_config() -> Dict[str, Any]:
    """Reload the global configuration."""
    global _config_loader  # pylint: disable=global-statement
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader.reload()

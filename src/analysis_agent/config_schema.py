"""
Configuration schema for the Analysis Agent.

This module defines the configuration options and validation for the Analysis Agent.
"""

from typing import Any, ClassVar


class AnalysisAgentConfig:
    """Configuration schema for the Analysis Agent."""

    DEFAULT_CONFIG: ClassVar[dict[str, Any]] = {
        "gemini": {
            "model": "gemini-pro",
            "temperature": 0.7,
            "max_output_tokens": 2048,
            "top_k": 40,
            "top_p": 0.95,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "timeout": 30,
        },
        "analysis": {
            "confidence_thresholds": {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8,
                "critical": 0.9,
            },
            "correlation_window": 3600,  # 1 hour in seconds
            "max_related_events": 50,
            "max_analysis_time": 300,  # 5 minutes
            "enable_context_retrieval": True,
            "enable_recommendation_engine": True,
        },
        "performance": {
            "cache_enabled": True,
            "cache_ttl": 3600,  # 1 hour
            "batch_size": 10,
            "max_concurrent_analyses": 5,
            "rate_limit": {"enabled": True, "max_per_minute": 30, "max_per_hour": 500},
        },
        "pubsub": {
            "topics": {
                "analysis_requests": "analysis-requests",
                "orchestration_commands": "orchestration-commands",
            },
            "subscriptions": {"orchestrator_to_analysis": "analysis-requests-sub"},
            "ack_deadline": 600,  # 10 minutes
            "max_messages": 10,
        },
    }

    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and merge configuration with defaults.

        Args:
            config: User-provided configuration

        Returns:
            Validated and merged configuration

        Raises:
            ValueError: If configuration is invalid
        """
        # Deep merge with defaults
        merged_config = cls._deep_merge(cls.DEFAULT_CONFIG.copy(), config)

        # Validate Gemini configuration
        gemini_config = merged_config.get("gemini", {})
        cls._validate_gemini_config(gemini_config)

        # Validate analysis configuration
        analysis_config = merged_config.get("analysis", {})
        cls._validate_analysis_config(analysis_config)

        # Validate performance configuration
        performance_config = merged_config.get("performance", {})
        cls._validate_performance_config(performance_config)

        return merged_config

    @staticmethod
    def _deep_merge(
        default: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = default.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = AnalysisAgentConfig._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def _validate_gemini_config(config: dict[str, Any]) -> None:
        """Validate Gemini configuration."""
        # Model validation
        valid_models = ["gemini-pro", "gemini-pro-vision", "gemini-ultra"]
        if config.get("model") not in valid_models:
            msg = f"Invalid Gemini model. Must be one of: {valid_models}"
            raise ValueError(msg)

        # Temperature validation
        temperature = config.get("temperature", 0.7)
        if not 0.0 <= temperature <= 1.0:
            msg = "Temperature must be between 0.0 and 1.0"
            raise ValueError(msg)

        # Token limit validation
        max_tokens = config.get("max_output_tokens", 2048)
        max_token_limit = 8192
        if not 1 <= max_tokens <= max_token_limit:
            msg = "max_output_tokens must be between 1 and 8192"
            raise ValueError(msg)

        # Retry validation
        retry_attempts = config.get("retry_attempts", 3)
        max_retry_attempts = 10
        if not 1 <= retry_attempts <= max_retry_attempts:
            msg = "retry_attempts must be between 1 and 10"
            raise ValueError(msg)

    @staticmethod
    def _validate_analysis_config(config: dict[str, Any]) -> None:
        """Validate analysis configuration."""
        # Confidence thresholds validation
        thresholds = config.get("confidence_thresholds", {})
        for level, value in thresholds.items():
            if not 0.0 <= value <= 1.0:
                msg = f"Confidence threshold for {level} must be between 0.0 and 1.0"
                raise ValueError(msg)

        # Ensure thresholds are in ascending order
        if thresholds:
            values = [
                thresholds.get("low", 0),
                thresholds.get("medium", 0),
                thresholds.get("high", 0),
                thresholds.get("critical", 0),
            ]
            if values != sorted(values):
                msg = "Confidence thresholds must be in ascending order"
                raise ValueError(msg)

        # Correlation window validation
        correlation_window = config.get("correlation_window", 3600)
        seconds_in_day = 86400  # 24 hours
        if not 60 <= correlation_window <= seconds_in_day:
            msg = "correlation_window must be between 60 and 86400 seconds"
            raise ValueError(msg)

        # Max events validation
        max_events = config.get("max_related_events", 50)
        max_events_limit = 1000
        if not 1 <= max_events <= max_events_limit:
            msg = "max_related_events must be between 1 and 1000"
            raise ValueError(msg)

    @staticmethod
    def _validate_performance_config(config: dict[str, Any]) -> None:
        """Validate performance configuration."""
        # Cache TTL validation
        if config.get("cache_enabled", True):
            cache_ttl = config.get("cache_ttl", 3600)
            seconds_in_day = 86400
            if not 60 <= cache_ttl <= seconds_in_day:
                msg = "cache_ttl must be between 60 and 86400 seconds"
                raise ValueError(msg)

        # Batch size validation
        batch_size = config.get("batch_size", 10)
        max_batch_size = 100
        if not 1 <= batch_size <= max_batch_size:
            msg = "batch_size must be between 1 and 100"
            raise ValueError(msg)

        # Concurrent analyses validation
        max_concurrent = config.get("max_concurrent_analyses", 5)
        max_concurrent_limit = 20
        if not 1 <= max_concurrent <= max_concurrent_limit:
            msg = "max_concurrent_analyses must be between 1 and 20"
            raise ValueError(msg)

        # Rate limit validation
        rate_limit = config.get("rate_limit", {})
        if rate_limit.get("enabled", True):
            max_per_minute = rate_limit.get("max_per_minute", 30)
            max_rate_per_minute = 100
            if not 1 <= max_per_minute <= max_rate_per_minute:
                msg = "max_per_minute must be between 1 and 100"
                raise ValueError(msg)

            max_per_hour = rate_limit.get("max_per_hour", 500)
            max_rate_per_hour = 2000
            if not max_per_minute <= max_per_hour <= max_rate_per_hour:
                msg = "max_per_hour must be between max_per_minute and 2000"
                raise ValueError(msg)

    @classmethod
    def get_config_documentation(cls) -> str:
        """Get human-readable documentation for configuration options."""
        return """
Analysis Agent Configuration Options:

GEMINI CONFIGURATION:
- model: Gemini model to use (gemini-pro, gemini-pro-vision, gemini-ultra)
- temperature: Controls randomness (0.0-1.0, default: 0.7)
- max_output_tokens: Maximum tokens in response (1-8192, default: 2048)
- top_k: Top-k sampling parameter (default: 40)
- top_p: Top-p sampling parameter (default: 0.95)
- retry_attempts: Number of retry attempts for API calls (1-10, default: 3)
- retry_delay: Initial delay between retries in seconds (default: 1.0)
- timeout: API call timeout in seconds (default: 30)

ANALYSIS CONFIGURATION:
- confidence_thresholds: Thresholds for confidence levels
  - low: Low confidence threshold (0.0-1.0, default: 0.3)
  - medium: Medium confidence threshold (0.0-1.0, default: 0.6)
  - high: High confidence threshold (0.0-1.0, default: 0.8)
  - critical: Critical confidence threshold (0.0-1.0, default: 0.9)
- correlation_window: Time window for event correlation in seconds (60-86400, default: 3600)
- max_related_events: Maximum related events to analyze (1-1000, default: 50)
- max_analysis_time: Maximum time for analysis in seconds (default: 300)
- enable_context_retrieval: Enable additional context retrieval (default: true)
- enable_recommendation_engine: Enable recommendation engine (default: true)

PERFORMANCE CONFIGURATION:
- cache_enabled: Enable caching of analysis results (default: true)
- cache_ttl: Cache time-to-live in seconds (60-86400, default: 3600)
- batch_size: Batch size for processing (1-100, default: 10)
- max_concurrent_analyses: Maximum concurrent analyses (1-20, default: 5)
- rate_limit: Rate limiting configuration
  - enabled: Enable rate limiting (default: true)
  - max_per_minute: Maximum requests per minute (1-100, default: 30)
  - max_per_hour: Maximum requests per hour (max_per_minute-2000, default: 500)

PUBSUB CONFIGURATION:
- topics: Pub/Sub topic names
  - analysis_requests: Topic for analysis requests
  - orchestration_commands: Topic for orchestration commands
- subscriptions: Pub/Sub subscription names
  - orchestrator_to_analysis: Subscription for orchestrator messages
- ack_deadline: Message acknowledgment deadline in seconds (default: 600)
- max_messages: Maximum messages to pull at once (default: 10)
"""

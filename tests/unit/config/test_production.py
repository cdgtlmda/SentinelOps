"""Tests for production configuration using real production code."""

import os

from src.config.production import (
    AGENT_REMEDIATION_DRY_RUN,
    APP_ENV,
    CACHE_ENABLED,
    CACHE_TTL,
    CORS_ORIGINS,
    DB_CONNECT_TIMEOUT,
    DB_ECHO_POOL,
    DB_MAX_OVERFLOW,
    DB_MONITOR_ENABLED,
    DB_POOL_PRE_PING,
    DB_POOL_RECYCLE,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
    DB_POOL_USE_LIFO,
    DB_QUERY_CACHE_SIZE,
    DB_USE_INSERTMANYVALUES,
    DEBUG,
    DEMO_MODE,
    ENABLE_METRICS,
    KEEPALIVE,
    LOG_LEVEL,
    METRICS_PORT,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    SSL_REDIRECT,
    USE_SSL,
    WORKER_CONNECTIONS,
    WORKERS,
)


class TestProductionConfiguration:
    """Test cases for production configuration with real production code."""

    @classmethod
    def setup_class(cls) -> None:
        """Set test mode to avoid config validation errors."""
        os.environ["SENTINELOPS_TEST_MODE"] = "true"

    def test_app_settings(self) -> None:
        """Test application settings for production."""
        assert APP_ENV == "production"
        assert DEBUG is False
        assert LOG_LEVEL == "WARNING"

    def test_debug_disabled_in_production(self) -> None:
        """Test that debug mode is disabled in production."""
        assert DEBUG is False

    def test_ssl_enabled_in_production(self) -> None:
        """Test that SSL is enabled in production."""
        assert USE_SSL is True
        assert SSL_REDIRECT is True

    def test_production_logging_level(self) -> None:
        """Test that production uses appropriate logging level."""
        assert LOG_LEVEL in ["WARNING", "ERROR"]

    def test_cors_origins_security(self) -> None:
        """Test that CORS origins are properly configured for security."""
        # In production, CORS should be more restrictive
        assert not CORS_ORIGINS or isinstance(CORS_ORIGINS, list)

    def test_cache_configuration(self) -> None:
        """Test caching configuration for production."""
        assert CACHE_ENABLED is True
        assert isinstance(CACHE_TTL, int)
        assert CACHE_TTL > 0

    def test_database_connection_pooling(self) -> None:
        """Test database connection pooling configuration."""
        assert isinstance(DB_POOL_SIZE, int)
        assert DB_POOL_SIZE > 0
        assert isinstance(DB_MAX_OVERFLOW, int)
        assert DB_MAX_OVERFLOW >= 0
        assert isinstance(DB_POOL_TIMEOUT, int)
        assert DB_POOL_TIMEOUT > 0

    def test_cors_origins_empty_list_check(self) -> None:
        """Test CORS origins empty list check."""
        # Fix the pylint issue by using implicit boolean check
        assert not CORS_ORIGINS  # Empty list is falsy

    def test_database_optimizations(self) -> None:
        """Test database optimization settings."""
        assert DB_POOL_PRE_PING is True  # For production reliability
        assert isinstance(DB_POOL_RECYCLE, int)
        assert DB_POOL_RECYCLE > 0

    def test_rate_limiting_production(self) -> None:
        """Test that rate limiting is appropriate for production."""
        assert isinstance(RATE_LIMIT_REQUESTS, int)
        assert isinstance(RATE_LIMIT_WINDOW, int)
        assert RATE_LIMIT_REQUESTS > 0
        assert RATE_LIMIT_WINDOW > 0

    def test_worker_configuration(self) -> None:
        """Test worker configuration for production."""
        assert isinstance(WORKERS, int)
        assert WORKERS > 0
        assert isinstance(WORKER_CONNECTIONS, int)
        assert WORKER_CONNECTIONS > 0

    def test_metrics_enabled(self) -> None:
        """Test that metrics are enabled in production."""
        assert ENABLE_METRICS is True
        assert isinstance(METRICS_PORT, int)
        assert METRICS_PORT > 0

    def test_agent_configuration(self) -> None:
        """Test agent configuration for production."""
        assert AGENT_REMEDIATION_DRY_RUN is False  # Real actions in prod

    def test_demo_mode_disabled(self) -> None:
        """Test that demo mode is disabled in production."""
        assert DEMO_MODE is False

    def test_database_monitoring(self) -> None:
        """Test database monitoring is enabled."""
        assert DB_MONITOR_ENABLED is True

    def test_keepalive_configuration(self) -> None:
        """Test keepalive configuration."""
        assert isinstance(KEEPALIVE, int)
        assert KEEPALIVE > 0

    def test_database_query_optimizations(self) -> None:
        """Test database query optimization settings."""
        assert isinstance(DB_QUERY_CACHE_SIZE, int)
        assert DB_QUERY_CACHE_SIZE > 0
        assert DB_USE_INSERTMANYVALUES is True
        assert DB_POOL_USE_LIFO is True

    def test_database_echo_disabled(self) -> None:
        """Test that database echo is disabled in production for performance."""
        assert DB_ECHO_POOL is False

    def test_connection_timeout(self) -> None:
        """Test connection timeout is reasonable for production."""
        assert isinstance(DB_CONNECT_TIMEOUT, int)
        assert DB_CONNECT_TIMEOUT > 0

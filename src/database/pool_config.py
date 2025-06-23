"""
Database connection pool configuration for SentinelOps.

This module provides production-ready connection pool settings for PostgreSQL
using SQLAlchemy's async engine with asyncpg driver.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ConnectionPoolConfig:
    """Configuration for database connection pooling."""

    # Core pool settings
    pool_size: int = 20  # Number of connections to maintain in pool
    max_overflow: int = 10  # Maximum overflow connections beyond pool_size
    pool_timeout: float = 30.0  # Seconds to wait before timing out
    pool_recycle: int = 3600  # Recycle connections after 1 hour
    pool_pre_ping: bool = True  # Test connections before using

    # Connection settings
    connect_timeout: int = 10  # Connection timeout in seconds
    command_timeout: Optional[int] = None  # Command timeout in seconds
    server_settings: Optional[Dict[str, Any]] = None  # PostgreSQL server settings

    # Retry settings
    pool_use_lifo: bool = True  # Use LIFO to prefer recently used connections
    echo_pool: bool = False  # Echo pool checkouts/checkins

    # Performance settings
    query_cache_size: int = 1200  # Number of queries to cache
    use_insertmanyvalues: bool = True  # Use efficient bulk inserts

    @classmethod
    def from_env(cls) -> "ConnectionPoolConfig":
        """Create configuration from environment variables."""
        return cls(
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=float(os.getenv("DB_POOL_TIMEOUT", "30.0")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
            connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
            command_timeout=(
                int(os.getenv("DB_COMMAND_TIMEOUT", ""))
                if os.getenv("DB_COMMAND_TIMEOUT")
                else None
            ),
            pool_use_lifo=os.getenv("DB_POOL_USE_LIFO", "true").lower() == "true",
            echo_pool=os.getenv("DB_ECHO_POOL", "false").lower() == "true",
            query_cache_size=int(os.getenv("DB_QUERY_CACHE_SIZE", "1200")),
            use_insertmanyvalues=os.getenv("DB_USE_INSERTMANYVALUES", "true").lower()
            == "true",
        )

    def get_engine_kwargs(self) -> Dict[str, Any]:
        """Get keyword arguments for create_async_engine."""
        kwargs: Dict[str, Any] = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "pool_use_lifo": self.pool_use_lifo,
            "echo_pool": self.echo_pool,
            "query_cache_size": self.query_cache_size,
            "use_insertmanyvalues": self.use_insertmanyvalues,
        }

        # Add connect args
        connect_args: Dict[str, Any] = {
            "timeout": self.connect_timeout,
            "server_settings": self.server_settings or {},
        }

        if self.command_timeout is not None:
            connect_args["command_timeout"] = self.command_timeout

        kwargs["connect_args"] = connect_args

        return kwargs


def get_development_config() -> ConnectionPoolConfig:
    """Get development environment connection pool configuration."""
    return ConnectionPoolConfig(
        pool_size=5,  # Smaller pool for development
        max_overflow=5,
        pool_timeout=30.0,
        pool_recycle=3600,
        pool_pre_ping=True,
        connect_timeout=10,
        echo_pool=True,  # Enable pool logging in development
        query_cache_size=500,
    )


def get_production_config() -> ConnectionPoolConfig:
    """Get production environment connection pool configuration."""
    config = ConnectionPoolConfig.from_env()

    # Ensure production defaults
    config.pool_pre_ping = True  # Always test connections in production
    config.echo_pool = False  # Disable verbose logging in production

    # Set server settings for production
    config.server_settings = {
        "application_name": "sentinelops",
        "jit": "on",
        "log_min_duration_statement": "1000",  # Log slow queries (>1s)
    }

    return config

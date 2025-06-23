"""
Logging configuration for SentinelOps
"""

import logging
import logging.config
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    # Try new import path first (for newer versions)
    from pythonjsonlogger import json as jsonlogger
except ImportError:
    # Fall back to old import path for compatibility
    from pythonjsonlogger import jsonlogger  # type: ignore[no-redef]


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""

    def __init__(self) -> None:
        super().__init__()
        self._correlation_id: Optional[str] = None

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID for the current context."""
        self._correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the log record."""
        record.correlation_id = self._correlation_id or "no-correlation-id"
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["service"] = "sentinelops"
        log_record["environment"] = self.environment

        # Add custom fields if they exist
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id
        if hasattr(record, "agent_id"):
            log_record["agent_id"] = record.agent_id
        if hasattr(record, "incident_id"):
            log_record["incident_id"] = record.incident_id

    def __init__(
        self, *args: Any, environment: str = "development", **kwargs: Any
    ) -> None:
        self.environment = environment
        super().__init__(*args, **kwargs)


def get_logging_config(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    environment: str = "development",
    enable_json: bool = True,
) -> Dict[str, Any]:
    """
    Generate logging configuration dictionary.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        environment: Environment name (development, production, test)
        enable_json: Whether to use JSON formatting

    Returns:
        Logging configuration dictionary
    """

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "json" if enable_json else "standard",
            "stream": "ext://sys.stdout",
            "filters": ["correlation_id"],
        }
    }

    if log_file:
        # Use variables of type Any to avoid strict type checking on integer fields
        max_bytes: Any = 10_485_760  # 10 MB
        backup_count: Any = 5

        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json" if enable_json else "standard",
            "filename": str(log_file),
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "filters": ["correlation_id"],
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"correlation_id": {"()": CorrelationIdFilter}},
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(correlation_id)s - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": CustomJsonFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s",
                "environment": environment,
            },
        },
        "handlers": handlers,
        "loggers": {
            "src": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "fastapi": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
        },
        "root": {"level": log_level, "handlers": list(handlers.keys())},
    }


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    environment: str = "development",
    enable_json: bool = True,
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level
        log_file: Optional path to log file
        environment: Environment name
        enable_json: Whether to use JSON formatting
    """
    config = get_logging_config(log_level, log_file, environment, enable_json)
    logging.config.dictConfig(config)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "environment": environment,
            "json_enabled": enable_json,
            "log_file": str(log_file) if log_file else None,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def setup_structured_logging(
    level: str = "INFO", _environment: str = "development"
) -> None:
    """
    Set up structured JSON logging for GCP Cloud Logging integration.

    Args:
        level: Logging level (default: INFO)
        environment: Environment name (default: development)
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    try:
        from google.cloud.logging import Client

        client = Client()  # type: ignore[no-untyped-call]
        client.setup_logging()  # type: ignore[no-untyped-call]
    except ImportError:
        # Fall back to standard logging if google-cloud-logging is not available
        logging.basicConfig(level=level, format=log_format)
    except (ValueError, AttributeError) as e:
        # Fall back to standard logging on any error
        print(f"Failed to setup GCP logging: {e}")
        logging.basicConfig(level=level, format=log_format)


def get_agent_logger(
    agent_id: str, agent_type: str
) -> logging.LoggerAdapter[logging.Logger]:
    """
    Get a logger instance for a specific agent.

    Args:
        agent_id: Unique agent identifier
        agent_type: Type of agent

    Returns:
        Logger instance with agent context
    """
    logger = logging.getLogger(f"src.agents.{agent_type}.{agent_id}")

    # Add a custom adapter to include agent context
    class AgentLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
        def process(self, msg: Any, kwargs: Any) -> Tuple[Any, Any]:
            extra = kwargs.get("extra", {})
            extra["agent_id"] = agent_id
            extra["agent_type"] = agent_type
            kwargs["extra"] = extra
            return msg, kwargs

    return AgentLoggerAdapter(logger, {})

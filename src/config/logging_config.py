"""
Logging configuration for SentinelOps.
"""

import logging
import logging.config
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    # Try new import path first (for newer versions)
    from pythonjsonlogger import json as jsonlogger
except ImportError:
    # Fall back to old import path for compatibility
    from pythonjsonlogger import jsonlogger  # type: ignore[no-redef]


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Add correlation ID from context if available
        record.correlation_id = getattr(record, "correlation_id", "no-correlation-id")
        return True


class SentinelOpsJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add level name
        log_record["level"] = record.levelname

        # Add module and function info
        log_record["module"] = record.module
        log_record["function"] = record.funcName

        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id

        # Add agent name if present
        if hasattr(record, "agent_name"):
            log_record["agent_name"] = record.agent_name


def get_logging_config(
    log_level: str = "INFO",
    log_dir: Path = Path("logs"),
    enable_file_logging: bool = True,
    enable_json_logging: bool = True,
) -> Dict[str, Any]:
    """
    Get logging configuration dictionary.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        enable_file_logging: Whether to enable file logging
        enable_json_logging: Whether to use JSON format for logs

    Returns:
        Logging configuration dictionary
    """
    # Ensure log directory exists
    if enable_file_logging:
        log_dir.mkdir(parents=True, exist_ok=True)

    # Base configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"correlation_id": {"()": CorrelationIdFilter}},
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "detailed": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(funcName)s:%(lineno)d - %(message)s"
                )
            },
            "json": {
                "()": SentinelOpsJsonFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json" if enable_json_logging else "detailed",
                "stream": sys.stdout,
                "filters": ["correlation_id"],
            }
        },
        "loggers": {
            "src": {"level": log_level, "handlers": ["console"], "propagate": False},
            "sentinelops": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "fastapi": {"level": "INFO", "handlers": ["console"], "propagate": False},
        },
        "root": {"level": log_level, "handlers": ["console"]},
    }

    # Add file handlers if enabled
    if enable_file_logging:
        # General application log
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json" if enable_json_logging else "detailed",
            "filename": str(log_dir / "sentinelops.log"),
            "maxBytes": "10485760",  # 10MB
            "backupCount": "5",
            "filters": ["correlation_id"],
        }

        # Error log
        config["handlers"]["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json" if enable_json_logging else "detailed",
            "filename": str(log_dir / "sentinelops_errors.log"),
            "maxBytes": "10485760",  # 10MB
            "backupCount": "5",
            "filters": ["correlation_id"],
        }

        # Add file handlers to loggers
        for logger_name in ["src", "sentinelops", "root"]:
            if logger_name == "root":
                config["root"]["handlers"].extend(["file", "error_file"])
            else:
                config["loggers"][logger_name]["handlers"].extend(
                    ["file", "error_file"]
                )

    return config


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path = Path("logs"),
    enable_file_logging: bool = True,
    enable_json_logging: bool = True,
) -> None:
    """
    Set up logging for the application.

    Args:
        log_level: Logging level
        log_dir: Directory for log files
        enable_file_logging: Whether to enable file logging
        enable_json_logging: Whether to use JSON format
    """
    config = get_logging_config(
        log_level=log_level,
        log_dir=log_dir,
        enable_file_logging=enable_file_logging,
        enable_json_logging=enable_json_logging,
    )

    logging.config.dictConfig(config)

    # Log initialization
    logger = logging.getLogger("sentinelops")
    logger.info(
        "Logging initialized",
        extra={
            "log_level": log_level,
            "log_dir": str(log_dir),
            "file_logging": enable_file_logging,
            "json_logging": enable_json_logging,
        },
    )


def get_logger(
    name: str, agent_name: Optional[str] = None
) -> Union[logging.Logger, logging.LoggerAdapter[logging.Logger]]:
    """
    Get a logger instance with optional agent name.

    Args:
        name: Logger name (usually __name__)
        agent_name: Optional agent name to include in logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if agent_name:
        # Create a custom adapter that adds agent_name to all records
        class AgentLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
            def process(self, msg: Any, kwargs: Any) -> tuple[Any, Any]:
                kwargs["extra"] = kwargs.get("extra", {})
                kwargs["extra"]["agent_name"] = agent_name
                return msg, kwargs

        return AgentLoggerAdapter(logger, {})

    return logger


# Example usage in other modules:
# from src.config.logging_config import get_logger
# logger = get_logger(__name__, agent_name="detection_agent")

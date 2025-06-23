"""
Logging and monitoring configuration for SentinelOps.

This module provides structured logging setup with Google Cloud Logging integration
and performance monitoring utilities.
"""

import json
import logging
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.cloud import logging as cloud_logging
from google.cloud.logging.handlers import CloudLoggingHandler

from .config_loader import get_config_value


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "agent_id"):
            log_obj["agent_id"] = record.agent_id
        if hasattr(record, "agent_type"):
            log_obj["agent_type"] = record.agent_type
        if hasattr(record, "incident_id"):
            log_obj["incident_id"] = record.incident_id
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id

        # Add any additional extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                if key not in log_obj:
                    log_obj[key] = value

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(
    agent_type: str,
    agent_id: str,
    use_cloud_logging: bool = True,
    log_level: str = "INFO",
) -> logging.Logger:
    """
    Set up logging for an agent with optional Cloud Logging integration.

    Args:
        agent_type: Type of agent (e.g., 'detection', 'analysis')
        agent_id: Unique identifier for the agent
        use_cloud_logging: Whether to use Google Cloud Logging
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger_name = f"sentinelops.{agent_type}"
    logger = logging.getLogger(logger_name)

    # Clear existing handlers
    logger.handlers.clear()

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    if use_cloud_logging:
        try:
            # Set up Cloud Logging
            client = cloud_logging.Client()  # type: ignore[no-untyped-call]
            handler = CloudLoggingHandler(client, name=logger_name)

            # Add structured logging support
            handler.setFormatter(StructuredFormatter())

            logger.addHandler(handler)
            logger.info("Cloud Logging enabled for %s", agent_type)

        except (ImportError, ValueError, AttributeError) as e:
            # Fall back to console logging
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(StructuredFormatter())
            logger.addHandler(console_handler)
            logger.warning("Failed to set up Cloud Logging: %s", e)
    else:
        # Use console logging for development
        console_handler = logging.StreamHandler()

        if get_config_value("development.debug", False):
            # Use human-readable format for development
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
        else:
            console_handler.setFormatter(StructuredFormatter())

        logger.addHandler(console_handler)

    # Add agent context to all logs
    class AgentContextFilter(logging.Filter):
        def filter(self, record: Any) -> bool:
            record.agent_type = agent_type
            record.agent_id = agent_id
            return True

    logger.addFilter(AgentContextFilter())

    return logger


class PerformanceMonitor:
    """
    Monitors performance metrics for agents and operations.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the performance monitor.

        Args:
            logger: Logger instance to use for reporting
        """
        self.logger = logger or logging.getLogger(__name__)
        self.metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "errors": 0,
            }
        )
        self._lock = threading.Lock()

    @contextmanager
    def measure(self, operation_name: str, **tags: Any) -> Any:
        """
        Context manager to measure operation performance.

        Args:
            operation_name: Name of the operation being measured
            **tags: Additional tags to include in metrics
        """
        start_time = time.time()
        error_occurred = False

        try:
            yield
        except Exception:
            error_occurred = True
            raise
        finally:
            duration = time.time() - start_time
            self._record_metric(operation_name, duration, error_occurred, tags)

    def _record_metric(
        self, operation_name: str, duration: float, error: bool, tags: Dict[str, Any]
    ) -> None:
        """Record a performance metric."""
        with self._lock:
            metric = self.metrics[operation_name]
            metric["count"] += 1
            metric["total_time"] += duration
            metric["min_time"] = min(metric["min_time"], duration)
            metric["max_time"] = max(metric["max_time"], duration)
            if error:
                metric["errors"] += 1

        # Log the metric
        self.logger.debug(
            f"Performance metric: {operation_name}",
            extra={
                "metric_type": "performance",
                "operation": operation_name,
                "duration_ms": duration * 1000,
                "error": error,
                **tags,
            },
        )

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all collected metrics."""
        with self._lock:
            # Calculate averages
            result = {}
            for name, metric in self.metrics.items():
                result[name] = {
                    **metric,
                    "avg_time": (
                        metric["total_time"] / metric["count"]
                        if metric["count"] > 0
                        else 0
                    ),
                    "error_rate": (
                        metric["errors"] / metric["count"] if metric["count"] > 0 else 0
                    ),
                }
            return result

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self.metrics.clear()


class CorrelationContext:
    """
    Thread-local storage for correlation IDs.
    """

    _context = threading.local()

    @classmethod
    def set_correlation_id(cls, correlation_id: str) -> None:
        """Set the correlation ID for the current context."""
        cls._context.correlation_id = correlation_id

    @classmethod
    def get_correlation_id(cls) -> Optional[str]:
        """Get the correlation ID for the current context."""
        return getattr(cls._context, "correlation_id", None)

    @classmethod
    def clear(cls) -> None:
        """Clear the correlation ID."""
        if hasattr(cls._context, "correlation_id"):
            delattr(cls._context, "correlation_id")


@contextmanager
def log_context(**kwargs: Any) -> Any:
    """
    Context manager to add extra fields to all logs within the context.

    Args:
        **kwargs: Fields to add to log records
    """
    # Get the current logger
    logger = logging.getLogger()

    # Create a filter that adds the context fields
    class ContextFilter(logging.Filter):
        def filter(self, record: Any) -> bool:
            for key, value in kwargs.items():
                setattr(record, key, value)

            # Also add correlation ID if present
            correlation_id = CorrelationContext.get_correlation_id()
            if correlation_id:
                record.correlation_id = correlation_id

            return True

    # Add the filter
    context_filter = ContextFilter()
    logger.addFilter(context_filter)

    try:
        yield
    finally:
        # Remove the filter
        logger.removeFilter(context_filter)


def log_agent_status(
    logger: logging.Logger,
    agent_type: str,
    agent_id: str,
    status: str,
    **extra_fields: Any,
) -> None:
    """
    Log agent status with standardized format.

    Args:
        logger: Logger instance
        agent_type: Type of agent
        agent_id: Agent identifier
        status: Current status
        **extra_fields: Additional fields to include
    """
    logger.info(
        f"Agent status: {status}",
        extra={
            "log_type": "agent_status",
            "agent_type": agent_type,
            "agent_id": agent_id,
            "status": status,
            **extra_fields,
        },
    )


def create_incident_logger(
    base_logger: logging.Logger, incident_id: str
) -> logging.Logger:
    """
    Create a logger that automatically includes incident context.

    Args:
        base_logger: Base logger to derive from
        incident_id: Incident ID to include in all logs

    Returns:
        Logger with incident context
    """
    # Create a child logger
    incident_logger = base_logger.getChild(f"incident.{incident_id}")

    # Add incident context filter
    class IncidentFilter(logging.Filter):
        def filter(self, record: Any) -> bool:
            record.incident_id = incident_id
            return True

    incident_logger.addFilter(IncidentFilter())

    return incident_logger


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor  # pylint: disable=global-statement
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

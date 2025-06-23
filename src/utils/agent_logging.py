"""
Agent-specific logging utilities.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from ..config.logging_config import get_logger


class AgentLogger:
    """Logger wrapper for agents with additional context."""

    def __init__(self, agent_name: str, agent_type: str):
        """
        Initialize agent logger.

        Args:
            agent_name: Name of the agent
            agent_type: Type of agent (detection, analysis, etc.)
        """
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.logger = get_logger(f"sentinelops.agents.{agent_name}", agent_name)

    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add agent context to log extras."""
        context = {"agent_name": self.agent_name, "agent_type": self.agent_type}
        if extra:
            context.update(extra)
        return context

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with agent context."""
        kwargs["extra"] = self._add_context(kwargs.get("extra"))
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with agent context."""
        kwargs["extra"] = self._add_context(kwargs.get("extra"))
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with agent context."""
        kwargs["extra"] = self._add_context(kwargs.get("extra"))
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with agent context."""
        kwargs["extra"] = self._add_context(kwargs.get("extra"))
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with agent context."""
        kwargs["extra"] = self._add_context(kwargs.get("extra"))
        self.logger.critical(message, **kwargs)

    def log_event(self, event_type: str, event_data: Dict[str, Any], **kwargs: Any) -> None:
        """Log a structured event."""
        extra = {"event_type": event_type, "event_data": event_data}
        kwargs["extra"] = self._add_context(extra)
        self.logger.info(f"Agent event: {event_type}", **kwargs)

    def log_metric(
        self, metric_name: str, value: Any, unit: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Log a metric value."""
        extra = {"metric_name": metric_name, "metric_value": value, "metric_unit": unit}
        kwargs["extra"] = self._add_context(extra)
        self.logger.info(f"Agent metric: {metric_name}={value}", **kwargs)


F = TypeVar('F', bound=Callable[..., Any])


def log_agent_method(func: F) -> F:
    """
    Decorator to log agent method calls.

    Usage:
        @log_agent_method
        async def process_event(self, event):
            ...
    """

    @wraps(func)
    async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        logger = getattr(self, "logger", logging.getLogger(__name__))
        method_name = func.__name__

        logger.debug(
            f"Calling {method_name}",
            extra={
                "method": method_name,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            },
        )

        try:
            result = await func(self, *args, **kwargs)
            logger.debug(
                f"Completed {method_name}",
                extra={"method": method_name, "success": True},
            )
            return result

        except Exception as e:
            logger.error(
                f"Error in {method_name}: {e}",
                extra={
                    "method": method_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

    @wraps(func)
    def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        logger = getattr(self, "logger", logging.getLogger(__name__))
        method_name = func.__name__

        logger.debug(
            f"Calling {method_name}",
            extra={
                "method": method_name,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            },
        )

        try:
            result = func(self, *args, **kwargs)
            logger.debug(
                f"Completed {method_name}",
                extra={"method": method_name, "success": True},
            )
            return result

        except Exception as e:
            logger.error(
                f"Error in {method_name}: {e}",
                extra={
                    "method": method_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    else:
        return cast(F, sync_wrapper)

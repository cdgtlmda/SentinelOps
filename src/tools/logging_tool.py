"""Google Cloud Logging tool for ADK agents.

This module provides a Cloud Logging tool implementation using ADK's BaseTool
for writing and querying logs in Google Cloud Logging.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from google.adk.tools import BaseTool
from google.cloud import logging as cloud_logging
from google.cloud.logging_v2.entries import StructEntry, TextEntry
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class LoggingConfig(BaseModel):
    """Configuration for Cloud Logging operations."""

    project_id: str = Field(description="Google Cloud Project ID")
    timeout: float = Field(default=30.0, description="Operation timeout in seconds")
    max_entries: int = Field(default=100, description="Maximum log entries to retrieve")

    @field_validator("timeout")
    def validate_timeout(cls, v: float) -> float:  # pylint: disable=no-self-argument
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @field_validator("max_entries")
    def validate_max_entries(cls, v: int) -> int:  # pylint: disable=no-self-argument
        if v <= 0 or v > 1000:
            raise ValueError("max_entries must be between 1 and 1000")
        return v


class WriteLogInput(BaseModel):
    """Input schema for writing a log entry."""

    log_name: str = Field(description="Name of the log to write to")
    severity: str = Field(
        default="INFO",
        description="Log severity: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    message: str = Field(description="Log message text")
    labels: Optional[Dict[str, str]] = Field(
        default=None, description="Additional labels for the log entry"
    )
    structured_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Structured data to include with the log"
    )

    @field_validator("severity")
    def validate_severity(cls, v: str) -> str:  # pylint: disable=no-self-argument
        valid_severities = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_severities:
            raise ValueError(f"Severity must be one of: {valid_severities}")
        return v.upper()


class QueryLogsInput(BaseModel):
    """Input schema for querying logs."""

    filter_expression: str = Field(description="Cloud Logging filter expression")
    hours_back: Optional[int] = Field(
        default=24, description="Number of hours to look back"
    )
    max_entries: Optional[int] = Field(
        default=None, description="Maximum number of entries to return"
    )
    order_by: Optional[str] = Field(
        default="timestamp desc", description="Order results by field"
    )


class LoggingTool(BaseTool):
    """ADK tool for interacting with Google Cloud Logging.

    This tool provides methods for:
    - Writing structured and text logs
    - Querying logs with filters
    - Retrieving log metrics
    - Managing log retention
    """

    def __init__(self, config: LoggingConfig):
        """Initialize the Cloud Logging tool.

        Args:
            config: Configuration for Cloud Logging operations
        """
        super().__init__(
            name="cloud_logging",
            description="Tool for reading and writing Google Cloud logs",
        )
        self.config = config
        self.client = cloud_logging.Client(project=config.project_id)  # type: ignore[no-untyped-call]
        self._logger_cache: Dict[str, Any] = {}

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Define the input schema for the tool.

        Returns:
            JSON schema for tool inputs
        """
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["write_log", "query_logs", "delete_logs"],
                    "description": "Operation to perform",
                },
                "params": {
                    "type": "object",
                    "description": "Operation-specific parameters",
                },
            },
            "required": ["operation", "params"],
        }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute a Cloud Logging operation.

        Args:
            **kwargs: Operation and parameters

        Returns:
            Operation result
        """
        operation = kwargs.get("operation")
        params = kwargs.get("params", {})

        if operation == "write_log":
            return await self._write_log(**params)
        elif operation == "query_logs":
            return await self._query_logs(**params)
        elif operation == "delete_logs":
            return await self._delete_logs(**params)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _write_log(self, **kwargs: Any) -> Dict[str, Any]:
        """Write a log entry to Cloud Logging.

        Args:
            **kwargs: Parameters from WriteLogInput

        Returns:
            Result with log entry ID
        """
        try:
            # Validate input
            log_input = WriteLogInput(**kwargs)

            # Get or create logger
            if log_input.log_name not in self._logger_cache:
                self._logger_cache[log_input.log_name] = self.client.logger(  # type: ignore[no-untyped-call]
                    log_input.log_name
                )
            logger_instance = self._logger_cache[log_input.log_name]

            # Prepare log entry
            if log_input.structured_data:
                # Write structured log
                logger_instance.log_struct(
                    log_input.structured_data,
                    severity=log_input.severity,
                    labels=log_input.labels,
                )
            else:
                # Write text log
                logger_instance.log_text(
                    log_input.message,
                    severity=log_input.severity,
                    labels=log_input.labels,
                )

            return {
                "success": True,
                "log_name": log_input.log_name,
                "severity": log_input.severity,
                "message": "Log entry written successfully",
            }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to write log: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _query_logs(self, **kwargs: Any) -> Dict[str, Any]:
        """Query logs from Cloud Logging.

        Args:
            **kwargs: Parameters from QueryLogsInput

        Returns:
            Result with log entries
        """
        try:
            # Validate input
            query_input = QueryLogsInput(**kwargs)

            # Build time filter
            if query_input.hours_back:
                start_time = datetime.utcnow() - timedelta(hours=query_input.hours_back)
                time_filter = f'timestamp >= "{start_time.isoformat()}Z"'
                if query_input.filter_expression:
                    filter_expression = (
                        f"{query_input.filter_expression} AND {time_filter}"
                    )
                else:
                    filter_expression = time_filter
            else:
                filter_expression = query_input.filter_expression

            # Query logs
            entries = []
            max_entries = query_input.max_entries or self.config.max_entries

            for entry in self.client.list_entries(  # type: ignore[no-untyped-call]
                filter_=filter_expression,
                order_by=query_input.order_by,
                max_results=max_entries,
            ):
                entry_dict = {
                    "timestamp": (
                        entry.timestamp.isoformat() if entry.timestamp else None
                    ),
                    "severity": entry.severity,
                    "log_name": entry.log_name,
                    "labels": dict(entry.labels) if entry.labels else {},
                }

                if isinstance(entry, TextEntry):
                    entry_dict["text_payload"] = entry.payload  # type: ignore[attr-defined]
                elif isinstance(entry, StructEntry):
                    entry_dict["json_payload"] = entry.payload  # type: ignore[attr-defined]
                else:
                    entry_dict["proto_payload"] = str(entry.payload)

                entries.append(entry_dict)

            return {
                "success": True,
                "entries": entries,
                "count": len(entries),
                "filter": filter_expression,
            }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to query logs: %s", str(e))
            return {"success": False, "error": str(e)}

    async def _delete_logs(self, **kwargs: Any) -> Dict[str, Any]:
        """Delete logs matching a filter (requires appropriate permissions).

        Args:
            **kwargs: Log name and filter parameters

        Returns:
            Result of deletion operation
        """
        try:
            log_name = kwargs.get("log_name")
            if not log_name:
                return {"success": False, "error": "log_name is required for deletion"}

            # Delete log (this deletes all entries in the log)
            logger_instance = self.client.logger(log_name)  # type: ignore[no-untyped-call]
            logger_instance.delete()

            # Remove from cache
            if log_name in self._logger_cache:
                del self._logger_cache[log_name]

            return {
                "success": True,
                "message": f"Log '{log_name}' deleted successfully",
            }

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to delete logs: %s", str(e))
            return {"success": False, "error": str(e)}

    def get_severity_filter(self, min_severity: str) -> str:
        """Get a filter expression for minimum severity.

        Args:
            min_severity: Minimum severity level

        Returns:
            Filter expression string
        """
        severity_levels = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4,
        }

        if min_severity.upper() not in severity_levels:
            raise ValueError(f"Invalid severity: {min_severity}")

        min_level = severity_levels[min_severity.upper()]
        severities = [s for s, l in severity_levels.items() if l >= min_level]

        return f'severity=({" OR ".join(severities)})'


# Helper functions for creating common filters
def create_resource_filter(
    resource_type: str, resource_id: Optional[str] = None
) -> str:
    """Create a filter for specific resource types.

    Args:
        resource_type: Type of resource (e.g., "gce_instance", "cloud_function")
        resource_id: Optional specific resource ID

    Returns:
        Filter expression
    """
    filter_expr = f'resource.type="{resource_type}"'
    if resource_id:
        filter_expr += f' AND resource.labels.instance_id="{resource_id}"'
    return filter_expr


def create_time_range_filter(start_time: datetime, end_time: datetime) -> str:
    """Create a filter for a specific time range.

    Args:
        start_time: Start of time range
        end_time: End of time range

    Returns:
        Filter expression
    """
    return f'timestamp >= "{start_time.isoformat()}Z" AND timestamp <= "{end_time.isoformat()}Z"'

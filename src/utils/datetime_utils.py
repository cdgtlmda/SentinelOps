"""
Datetime utility functions for SentinelOps.

Provides timezone-aware datetime operations to ensure consistency
across the entire system.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union


def utcnow() -> datetime:
    """
    Get current UTC time with timezone awareness.

    Returns:
        datetime: Current UTC time with timezone info.

    Note:
        This replaces datetime.now(timezone.utc) which returns timezone-naive
        datetimes and is deprecated in Python 3.12+.
    """
    return datetime.now(timezone.utc)


def parse_iso_datetime(date_string: str) -> datetime:
    """
    Parse ISO format datetime string to timezone-aware datetime.

    Args:
        date_string: ISO format datetime string

    Returns:
        datetime: Timezone-aware datetime object

    Raises:
        ValueError: If the string cannot be parsed
    """
    # Try parsing with timezone
    try:
        dt = datetime.fromisoformat(date_string)
        if dt.tzinfo is None:
            # If no timezone, assume UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        # Try alternative formats
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]:
            try:
                dt = datetime.strptime(date_string, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse datetime string: {date_string}") from None


def format_iso_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime to ISO string with timezone.

    Args:
        dt: Datetime object (can be None)

    Returns:
        str: ISO formatted datetime string or None
    """
    if dt is None:
        return None

    # Ensure timezone aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.isoformat()


def seconds_since(start_time: datetime) -> float:
    """
    Calculate seconds elapsed since start_time.

    Args:
        start_time: Start datetime

    Returns:
        float: Number of seconds elapsed
    """
    return (utcnow() - start_time).total_seconds()


def add_seconds(dt: datetime, seconds: Union[int, float]) -> datetime:
    """
    Add seconds to a datetime.

    Args:
        dt: Base datetime
        seconds: Number of seconds to add

    Returns:
        datetime: New datetime with seconds added
    """
    return dt + timedelta(seconds=seconds)


def ensure_timezone_aware(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware.

    If the datetime is naive, it assumes UTC.

    Args:
        dt: Datetime object

    Returns:
        datetime: Timezone-aware datetime
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def datetime_to_timestamp(dt: datetime) -> float:
    """
    Convert datetime to Unix timestamp.

    Args:
        dt: Datetime object

    Returns:
        float: Unix timestamp
    """
    return ensure_timezone_aware(dt).timestamp()


def timestamp_to_datetime(timestamp: float) -> datetime:
    """
    Convert Unix timestamp to timezone-aware datetime.

    Args:
        timestamp: Unix timestamp

    Returns:
        datetime: Timezone-aware datetime in UTC
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

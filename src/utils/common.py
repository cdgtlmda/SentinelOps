"""
General utility functions for SentinelOps.

This module provides pure utility functions for string manipulation,
data transformation, and validation.
"""

import base64
import hashlib
import json
import re
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union


# String manipulation utilities
def sanitize_string(text: str, allowed_chars: Optional[str] = None) -> str:
    """
    Sanitize a string by removing unwanted characters.

    Args:
        text: String to sanitize
        allowed_chars: Optional string of allowed characters

    Returns:
        Sanitized string
    """
    if allowed_chars is None:
        # Default: alphanumeric, spaces, and common punctuation
        allowed_chars = r"[^a-zA-Z0-9\s\-_.,!?]"
        return re.sub(allowed_chars, "", text)
    else:
        pattern = f"[^{re.escape(allowed_chars)}]"
        return re.sub(pattern, "", text)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in a string (replace multiple spaces with single space).

    Args:
        text: String to normalize

    Returns:
        Normalized string
    """
    return " ".join(text.split())


def to_snake_case(text: str) -> str:
    """
    Convert string to snake_case.

    Args:
        text: String to convert

    Returns:
        snake_case string
    """
    # Replace hyphens with underscores
    text = text.replace("-", "_")
    # Insert underscore before uppercase letters
    text = re.sub("([a-z0-9])([A-Z])", r"\1_\2", text)
    return text.lower()


def to_camel_case(text: str) -> str:
    """
    Convert string to camelCase.

    Args:
        text: String to convert

    Returns:
        camelCase string
    """
    components = text.replace("-", "_").split("_")
    return components[0].lower() + "".join(x.title() for x in components[1:])


# Data transformation utilities
def flatten_dict(
    nested_dict: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        nested_dict: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items: List[Tuple[str, Any]] = []
    for k, v in nested_dict.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def merge_dicts_deep(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (values override dict1)

    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts_deep(result[key], value)
        else:
            result[key] = value
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_json_parse(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with fallback.

    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def encode_base64(data: Union[str, bytes]) -> str:
    """
    Encode data to base64 string.

    Args:
        data: Data to encode

    Returns:
        Base64 encoded string
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("utf-8")


def decode_base64(encoded: str) -> bytes:
    """
    Decode base64 string to bytes.

    Args:
        encoded: Base64 encoded string

    Returns:
        Decoded bytes
    """
    return base64.b64decode(encoded.encode("utf-8"))


# Validation helpers
def is_valid_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_uuid(uuid_str: str) -> bool:
    """
    Validate UUID string format.

    Args:
        uuid_str: UUID string to validate

    Returns:
        True if valid UUID format
    """
    try:
        uuid.UUID(uuid_str)
        return True
    except ValueError:
        return False


def is_valid_ip_address(ip: str) -> bool:
    """
    Validate IP address format (IPv4).

    Args:
        ip: IP address to validate

    Returns:
        True if valid IPv4 address
    """
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, ip):
        return False

    parts = ip.split(".")
    return all(0 <= int(part) <= 255 for part in parts)


def is_valid_timestamp(timestamp: Union[str, int, float]) -> bool:
    """
    Validate if value is a valid timestamp.

    Args:
        timestamp: Timestamp to validate

    Returns:
        True if valid timestamp
    """
    try:
        if isinstance(timestamp, str):
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return True
        else:  # timestamp is int or float
            datetime.fromtimestamp(timestamp)
            return True
    except (ValueError, TypeError):
        return False


def calculate_hash(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """
    Calculate hash of data.

    Args:
        data: Data to hash
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of hash
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def group_by_key(
    items: List[Dict[str, Any]], key: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group list of dictionaries by a specific key.

    Args:
        items: List of dictionaries
        key: Key to group by

    Returns:
        Dictionary with grouped items
    """
    grouped = defaultdict(list)
    for item in items:
        if key in item:
            grouped[item[key]].append(item)
    return dict(grouped)


def extract_field_from_list(items: List[Dict[str, Any]], field: str) -> List[Any]:
    """
    Extract a specific field from a list of dictionaries.

    Args:
        items: List of dictionaries
        field: Field to extract

    Returns:
        List of field values
    """
    return [item.get(field) for item in items if field in item]

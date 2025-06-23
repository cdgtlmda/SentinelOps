"""
Request validation utilities for SentinelOps API.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator

from ..config.logging_config import get_logger

logger = get_logger(__name__)


class RequestValidator:
    """Validates incoming requests for security and data integrity."""

    # Regex patterns for validation
    PATTERNS = {
        "alphanumeric": re.compile(r"^[a-zA-Z0-9]+$"),
        "identifier": re.compile(r"^[a-zA-Z0-9_-]+$"),
        "resource_name": re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$"),
        "gcp_project": re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$"),
        "ip_address": re.compile(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        ),
        "url": re.compile(
            r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}"
            r"\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)$"
        ),
        "semantic_version": re.compile(
            r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
            r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
            r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
            r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
        ),
    }

    # Maximum allowed sizes
    MAX_STRING_LENGTH = 1024
    MAX_ARRAY_LENGTH = 100
    MAX_OBJECT_DEPTH = 5

    @classmethod
    def validate_identifier(cls, value: str, field_name: str = "identifier") -> str:
        """
        Validate an identifier string.

        Args:
            value: The identifier to validate
            field_name: Name of the field for error messages

        Returns:
            Validated identifier

        Raises:
            HTTPException if invalid
        """
        if not value or not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name}: must be a non-empty string",
            )

        if len(value) > cls.MAX_STRING_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name}: exceeds maximum length",
            )

        if not cls.PATTERNS["identifier"].match(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid {field_name}: must contain only alphanumeric "
                    "characters, hyphens, and underscores"
                ),
            )

        return value

    @classmethod
    def validate_resource_name(cls, value: str) -> str:
        """Validate a resource name."""
        if not value or not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resource name must be a non-empty string",
            )

        if not cls.PATTERNS["resource_name"].match(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid resource name format",
            )

        return value

    @classmethod
    def validate_gcp_project_id(cls, value: str) -> str:
        """Validate a Google Cloud project ID."""
        if not cls.PATTERNS["gcp_project"].match(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google Cloud project ID format",
            )
        return value

    @classmethod
    def validate_ip_address(cls, value: str) -> str:
        """Validate an IP address."""
        if not cls.PATTERNS["ip_address"].match(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid IP address format",
            )
        return value

    @classmethod
    def validate_url(cls, value: str) -> str:
        """Validate a URL."""
        if not cls.PATTERNS["url"].match(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL format"
            )
        return value

    @classmethod
    def sanitize_string(cls, value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize a string for safe storage/display.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        # Remove control characters
        value = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")

        # Trim whitespace
        value = value.strip()

        # Enforce max length
        if max_length:
            value = value[:max_length]

        return value

    @classmethod
    def validate_pagination(
        cls, page: int = 1, page_size: int = 20, max_page_size: int = 100
    ) -> Dict[str, int]:
        """
        Validate pagination parameters.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            max_page_size: Maximum allowed page size

        Returns:
            Validated pagination parameters
        """
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1",
            )

        if page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be >= 1"
            )

        if page_size > max_page_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page size exceeds maximum of {max_page_size}",
            )

        return {
            "page": page,
            "page_size": page_size,
            "offset": (page - 1) * page_size,
            "limit": page_size,
        }


# Pydantic models for common request/response structures
class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, le=10000, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class FilterParams(BaseModel):
    """Common filter parameters."""

    search: Optional[str] = Field(default=None, max_length=256, description="Search query")
    status: Optional[str] = Field(default=None, description="Status filter")
    start_date: Optional[datetime] = Field(default=None, description="Start date filter")
    end_date: Optional[datetime] = Field(default=None, description="End date filter")
    tags: Optional[List[str]] = Field(default=None, max_length=10, description="Tag filters")

    @validator("search")
    @classmethod
    def sanitize_search(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize search query."""
        if v:
            return RequestValidator.sanitize_string(v, max_length=256)
        return v

    @validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tag list."""
        if v:
            return [RequestValidator.sanitize_string(tag, max_length=50) for tag in v]
        return v


class SortParams(BaseModel):
    """Sorting parameters."""

    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")

    @validator("sort_by")
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        """Validate sort field."""
        allowed_fields = [
            "created_at",
            "updated_at",
            "name",
            "status",
            "severity",
            "priority",
            "score",
        ]
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort field. Allowed: {allowed_fields}")
        return v


class BaseResponse(BaseModel):
    """Base response model."""

    success: bool = Field(True, description="Request success status")
    message: Optional[str] = Field(None, description="Response message")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp"
    )


class PaginatedResponse(BaseResponse):
    """Paginated response model."""

    data: List[Any] = Field(..., description="Response data")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")

    @classmethod
    def create(
        cls, data: List[Any], page: int, page_size: int, total_count: int, **kwargs: Any
    ) -> "PaginatedResponse":
        """Create a paginated response."""
        total_pages = (total_count + page_size - 1) // page_size

        return cls(
            data=data,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            **kwargs,
        )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: Dict[str, Any] = Field(..., description="Error details")

    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> "ErrorResponse":
        """Create an error response."""
        return cls(
            error={
                "code": code,
                "message": message,
                "details": details or {},
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc),
            }
        )


# Input validation models for specific endpoints
class CreateIncidentRequest(BaseModel):
    """Request model for creating an incident."""

    title: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=4096)
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    source: str = Field(min_length=1, max_length=128)
    affected_resources: List[str] = Field(default_factory=list, max_length=50)
    tags: List[str] = Field(default_factory=list, max_length=20)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("title", "description", "source")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Sanitize text fields."""
        return RequestValidator.sanitize_string(v)

    @validator("affected_resources")
    @classmethod
    def validate_resources(cls, v: List[str]) -> List[str]:
        """Validate resource identifiers."""
        return [RequestValidator.validate_identifier(r, "resource") for r in v]


class UpdateAgentConfigRequest(BaseModel):
    """Request model for updating agent configuration."""

    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("config", "metadata")
    @classmethod
    def validate_object_depth(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Ensure objects don't exceed maximum depth."""

        def check_depth(obj: Any, depth: int = 0) -> None:
            if depth > RequestValidator.MAX_OBJECT_DEPTH:
                raise ValueError("Object exceeds maximum nesting depth")
            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1)

        if v:
            check_depth(v)
        return v

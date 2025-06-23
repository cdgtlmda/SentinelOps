"""Tests for request validation utilities using real production code."""

import re
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.api.validation import (
    BaseResponse,
    CreateIncidentRequest,
    ErrorResponse,
    FilterParams,
    PaginatedResponse,
    PaginationParams,
    RequestValidator,
    SortParams,
    UpdateAgentConfigRequest,
)


class TestRequestValidator:
    """Test cases for RequestValidator with real production code."""

    def test_validate_identifier_valid(self) -> None:
        """Test validation of valid identifiers."""
        valid_ids = [
            "test123",
            "test_123",
            "test-123",
            "TEST_456",
            "a1b2c3",
            "_test",
            "-test",
            "test_-_123",
        ]

        for valid_id in valid_ids:
            result = RequestValidator.validate_identifier(valid_id)
            assert result == valid_id

    def test_validate_identifier_invalid(self) -> None:
        """Test validation of invalid identifiers."""
        invalid_cases = [
            ("", "must be a non-empty string"),
            (None, "must be a non-empty string"),
            (123, "must be a non-empty string"),
            ("test@123", "must contain only alphanumeric"),
            ("test.123", "must contain only alphanumeric"),
            ("test 123", "must contain only alphanumeric"),
            ("x" * 1025, "exceeds maximum length"),
        ]

        for invalid_id, expected_msg in invalid_cases:
            with pytest.raises(HTTPException) as exc_info:
                RequestValidator.validate_identifier(
                    str(invalid_id) if invalid_id is not None else ""
                )

            assert exc_info.value.status_code == 400
            assert expected_msg in exc_info.value.detail

    def test_validate_identifier_custom_field_name(self) -> None:
        """Test identifier validation with custom field name."""
        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_identifier("test@123", "custom_field")

        assert "Invalid custom_field:" in exc_info.value.detail

    def test_validate_resource_name_valid(self) -> None:
        """Test validation of valid resource names."""
        valid_names = ["resource1", "my_resource", "test-resource-123", "a1b2c3"]

        for name in valid_names:
            result = RequestValidator.validate_resource_name(name)
            assert result == name

    def test_validate_resource_name_invalid(self) -> None:
        """Test validation of invalid resource names."""
        invalid_cases = [
            ("", "must be a non-empty string"),
            (None, "must be a non-empty string"),
            ("_invalid", "Invalid resource name format"),  # Can't start with underscore
            ("-invalid", "Invalid resource name format"),  # Can't start with hyphen
            ("test@resource", "Invalid resource name format"),
            ("test.resource", "Invalid resource name format"),
        ]

        for invalid_name, expected_msg in invalid_cases:
            with pytest.raises(HTTPException) as exc_info:
                RequestValidator.validate_resource_name(
                    str(invalid_name) if invalid_name is not None else ""
                )

            assert exc_info.value.status_code == 400
            assert expected_msg in exc_info.value.detail

    def test_validate_gcp_project_id_valid(self) -> None:
        """Test validation of valid GCP project IDs."""
        valid_projects = [
            "my-project-123",
            "test-project",
            "project-name-456",
            "a123456",
        ]

        for project in valid_projects:
            result = RequestValidator.validate_gcp_project_id(project)
            assert result == project

    def test_validate_gcp_project_id_invalid(self) -> None:
        """Test validation of invalid GCP project IDs."""
        invalid_projects = [
            "My-Project",  # Uppercase not allowed
            "project_name",  # Underscore not allowed
            "p",  # Too short
            "1-project",  # Can't start with number
            "-project",  # Can't start with hyphen
            "project-",  # Can't end with hyphen
            "a" * 31,  # Too long
        ]

        for project in invalid_projects:
            with pytest.raises(HTTPException) as exc_info:
                RequestValidator.validate_gcp_project_id(project)

            assert exc_info.value.status_code == 400
            assert "Invalid Google Cloud project ID format" in exc_info.value.detail

    def test_validate_ip_address_valid(self) -> None:
        """Test validation of valid IP addresses."""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "255.255.255.255",
            "0.0.0.0",
        ]

        for ip in valid_ips:
            result = RequestValidator.validate_ip_address(ip)
            assert result == ip

    def test_validate_ip_address_invalid(self) -> None:
        """Test validation of invalid IP addresses."""
        invalid_ips = [
            "256.1.1.1",  # Out of range
            "192.168.1",  # Missing octet
            "192.168.1.1.1",  # Too many octets
            "192.168.-1.1",  # Negative number
            "192.168.a.1",  # Non-numeric
            "192.168.1.1:80",  # With port
            "::1",  # IPv6 (not supported by this validator)
        ]

        for ip in invalid_ips:
            with pytest.raises(HTTPException) as exc_info:
                RequestValidator.validate_ip_address(ip)

            assert exc_info.value.status_code == 400
            assert "Invalid IP address format" in exc_info.value.detail

    def test_validate_url_valid(self) -> None:
        """Test validation of valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://test.example.com",
            "https://example.com/path",
            "https://example.com/path?query=value",
            "https://sub.example.com:8080/path",
            "https://example.com/path#anchor",
        ]

        for url in valid_urls:
            result = RequestValidator.validate_url(url)
            assert result == url

    def test_validate_url_invalid(self) -> None:
        """Test validation of invalid URLs."""
        invalid_urls = [
            "ftp://example.com",  # Wrong protocol
            "example.com",  # Missing protocol
            "https://",  # Missing domain
            "https://.com",  # Invalid domain
            "https://example",  # Missing TLD
            "javascript:alert(1)",  # XSS attempt
        ]

        for url in invalid_urls:
            with pytest.raises(HTTPException) as exc_info:
                RequestValidator.validate_url(url)

            assert exc_info.value.status_code == 400
            assert "Invalid URL format" in exc_info.value.detail

    def test_sanitize_string_basic(self) -> None:
        """Test basic string sanitization."""
        # Test trimming
        assert RequestValidator.sanitize_string("  test  ") == "test"

        # Test control character removal
        assert RequestValidator.sanitize_string("test\x00\x01\x02") == "test"
        assert RequestValidator.sanitize_string("test\nline\ttab") == "test\nline\ttab"

        # Test max length
        assert (
            RequestValidator.sanitize_string("test" * 10, max_length=10) == "testtestte"
        )

    def test_sanitize_string_with_unicode(self) -> None:
        """Test string sanitization with unicode characters."""
        # Unicode should be preserved
        assert RequestValidator.sanitize_string("test 测试 🔥") == "test 测试 🔥"

        # Control characters in unicode range should be removed
        assert RequestValidator.sanitize_string("test\u0000\u0001") == "test"

    def test_validate_pagination_valid(self) -> None:
        """Test validation of valid pagination parameters."""
        result = RequestValidator.validate_pagination(page=2, page_size=50)

        assert result["page"] == 2
        assert result["page_size"] == 50
        assert result["offset"] == 50
        assert result["limit"] == 50

    def test_validate_pagination_defaults(self) -> None:
        """Test pagination with default values."""
        result = RequestValidator.validate_pagination()

        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["offset"] == 0
        assert result["limit"] == 20

    def test_validate_pagination_invalid(self) -> None:
        """Test validation of invalid pagination parameters."""
        # Invalid page
        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_pagination(page=0)
        assert "Page number must be >= 1" in exc_info.value.detail

        # Invalid page size
        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_pagination(page_size=0)
        assert "Page size must be >= 1" in exc_info.value.detail

        # Exceeds max page size
        with pytest.raises(HTTPException) as exc_info:
            RequestValidator.validate_pagination(page_size=101, max_page_size=100)
        assert "Page size exceeds maximum of 100" in exc_info.value.detail

    def test_regex_patterns(self) -> None:
        """Test that all regex patterns are valid and compile."""
        for name, pattern in RequestValidator.PATTERNS.items():
            assert isinstance(pattern, re.Pattern)
            assert pattern.pattern  # Pattern string exists


class TestPaginationParams:
    """Test cases for PaginationParams model."""

    def test_default_values(self) -> None:
        """Test default pagination values."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.offset == 0
        assert params.limit == 20

    def test_custom_values(self) -> None:
        """Test custom pagination values."""
        params = PaginationParams(page=5, page_size=50)
        assert params.page == 5
        assert params.page_size == 50
        assert params.offset == 200  # (5-1) * 50
        assert params.limit == 50

    def test_validation_constraints(self) -> None:
        """Test pagination validation constraints."""
        # Page too low
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

        # Page too high
        with pytest.raises(ValidationError):
            PaginationParams(page=10001)

        # Page size too low
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

        # Page size too high
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)


class TestFilterParams:
    """Test cases for FilterParams model."""

    def test_default_values(self) -> None:
        """Test default filter values."""
        params = FilterParams()
        assert params.search is None
        assert params.status is None
        assert params.start_date is None
        assert params.end_date is None
        assert params.tags is None

    def test_search_sanitization(self) -> None:
        """Test search query sanitization."""
        params = FilterParams(search="  test query  ")
        assert params.search == "test query"

        # Test with control characters
        params = FilterParams(search="test\x00query")
        assert params.search == "testquery"

    def test_search_max_length(self) -> None:
        """Test search query max length enforcement."""
        # Pydantic enforces max_length, so this should raise ValidationError
        long_search = "x" * 300
        with pytest.raises(ValidationError) as exc_info:
            FilterParams(search=long_search)

        assert "String should have at most 256 characters" in str(exc_info.value)

    def test_tags_validation(self) -> None:
        """Test tags validation and sanitization."""
        params = FilterParams(tags=["  tag1  ", "tag2\x00", "tag3"])
        assert params.tags == ["tag1", "tag2", "tag3"]

        # Test tag length limit
        params = FilterParams(tags=["x" * 100])
        assert params.tags is not None and len(params.tags[0]) == 50

    def test_tags_max_count(self) -> None:
        """Test maximum number of tags."""
        with pytest.raises(ValidationError):
            FilterParams(tags=["tag" + str(i) for i in range(11)])

    def test_date_filters(self) -> None:
        """Test date filter parameters."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 12, 31, tzinfo=timezone.utc)

        params = FilterParams(start_date=start, end_date=end)
        assert params.start_date == start
        assert params.end_date == end


class TestSortParams:
    """Test cases for SortParams model."""

    def test_default_values(self) -> None:
        """Test default sort values."""
        params = SortParams(sort_by="created_at")
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"

    def test_valid_sort_fields(self) -> None:
        """Test valid sort field values."""
        valid_fields = [
            "created_at",
            "updated_at",
            "name",
            "status",
            "severity",
            "priority",
            "score",
        ]

        for field in valid_fields:
            params = SortParams(sort_by=field)
            assert params.sort_by == field

    def test_invalid_sort_field(self) -> None:
        """Test invalid sort field."""
        with pytest.raises(ValidationError) as exc_info:
            SortParams(sort_by="invalid_field")

        assert "Invalid sort field" in str(exc_info.value)

    def test_sort_order_validation(self) -> None:
        """Test sort order validation."""
        params = SortParams(sort_by="created_at", sort_order="asc")
        assert params.sort_order == "asc"

        params = SortParams(sort_by="created_at", sort_order="desc")
        assert params.sort_order == "desc"

        with pytest.raises(ValidationError):
            SortParams(sort_by="created_at", sort_order="invalid")


class TestResponseModels:
    """Test cases for response models."""

    def test_base_response(self) -> None:
        """Test BaseResponse model."""
        response = BaseResponse(
            success=True, message="Success", correlation_id="test-123"
        )
        assert response.success is True
        assert response.message == "Success"
        assert response.correlation_id == "test-123"
        assert isinstance(response.timestamp, datetime)

    def test_base_response_with_values(self) -> None:
        """Test BaseResponse with custom values."""
        response = BaseResponse(
            success=False, message="Error occurred", correlation_id="123-456"
        )
        assert response.success is False
        assert response.message == "Error occurred"
        assert response.correlation_id == "123-456"

    def test_paginated_response_create(self) -> None:
        """Test PaginatedResponse creation."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse.create(
            data=data, page=2, page_size=10, total_count=25, correlation_id="test-123"
        )

        assert response.data == data
        assert response.pagination["page"] == 2
        assert response.pagination["page_size"] == 10
        assert response.pagination["total_count"] == 25
        assert response.pagination["total_pages"] == 3
        assert response.pagination["has_next"] is True
        assert response.pagination["has_previous"] is True
        assert response.correlation_id == "test-123"

    def test_paginated_response_edge_cases(self) -> None:
        """Test PaginatedResponse edge cases."""
        # First page
        response = PaginatedResponse.create([], 1, 10, 50)
        assert response.pagination["has_previous"] is False
        assert response.pagination["has_next"] is True

        # Last page
        response = PaginatedResponse.create([], 5, 10, 50)
        assert response.pagination["has_previous"] is True
        assert response.pagination["has_next"] is False

        # Single page
        response = PaginatedResponse.create([], 1, 10, 5)
        assert response.pagination["has_previous"] is False
        assert response.pagination["has_next"] is False

    def test_error_response_create(self) -> None:
        """Test ErrorResponse creation."""
        response = ErrorResponse.create(
            code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "email", "reason": "invalid format"},
            correlation_id="error-123",
        )

        assert response.error["code"] == "VALIDATION_ERROR"
        assert response.error["message"] == "Invalid input"
        assert response.error["details"]["field"] == "email"
        assert response.error["correlation_id"] == "error-123"
        assert isinstance(response.error["timestamp"], datetime)


class TestCreateIncidentRequest:
    """Test cases for CreateIncidentRequest model."""

    def test_valid_request(self) -> None:
        """Test valid incident creation request."""
        request = CreateIncidentRequest(
            title="Test Incident",
            description="Test description",
            severity="high",
            source="monitoring",
            affected_resources=["resource-1", "resource-2"],
            tags=["test", "incident"],
            metadata={"custom": "data"},
        )

        assert request.title == "Test Incident"
        assert request.severity == "high"
        assert len(request.affected_resources) == 2
        assert len(request.tags) == 2

    def test_text_sanitization(self) -> None:
        """Test text field sanitization."""
        request = CreateIncidentRequest(
            title="  Test Title  ",
            description="Description\x00with\x01control",
            severity="low",
            source="  api  ",
        )

        assert request.title == "Test Title"
        assert request.description == "Descriptionwithcontrol"
        assert request.source == "api"

    def test_field_length_validation(self) -> None:
        """Test field length constraints."""
        # Title too long
        with pytest.raises(ValidationError):
            CreateIncidentRequest(
                title="x" * 257, description="test", severity="low", source="api"
            )

        # Description too long
        with pytest.raises(ValidationError):
            CreateIncidentRequest(
                title="test", description="x" * 4097, severity="low", source="api"
            )

    def test_severity_validation(self) -> None:
        """Test severity validation."""
        valid_severities = ["low", "medium", "high", "critical"]

        for severity in valid_severities:
            request = CreateIncidentRequest(
                title="test", description="test", severity=severity, source="api"
            )
            assert request.severity == severity

        with pytest.raises(ValidationError):
            CreateIncidentRequest(
                title="test", description="test", severity="invalid", source="api"
            )

    def test_resource_validation(self) -> None:
        """Test affected resources validation."""
        # Invalid resource format should raise exception
        with pytest.raises(HTTPException):
            CreateIncidentRequest(
                title="test",
                description="test",
                severity="low",
                source="api",
                affected_resources=["valid-resource", "invalid@resource"],
            )

    def test_max_collections(self) -> None:
        """Test maximum collection sizes."""
        # Too many resources
        with pytest.raises(ValidationError):
            CreateIncidentRequest(
                title="test",
                description="test",
                severity="low",
                source="api",
                affected_resources=[f"resource-{i}" for i in range(51)],
            )

        # Too many tags
        with pytest.raises(ValidationError):
            CreateIncidentRequest(
                title="test",
                description="test",
                severity="low",
                source="api",
                tags=[f"tag-{i}" for i in range(21)],
            )


class TestUpdateAgentConfigRequest:
    """Test cases for UpdateAgentConfigRequest model."""

    def test_optional_fields(self) -> None:
        """Test all fields are optional."""
        request = UpdateAgentConfigRequest()
        assert request.enabled is None
        assert request.config is None
        assert request.metadata is None

    def test_valid_update(self) -> None:
        """Test valid update request."""
        request = UpdateAgentConfigRequest(
            enabled=True,
            config={"threshold": 0.8, "timeout": 30},
            metadata={"updated_by": "admin"},
        )

        assert request.enabled is True
        assert request.config is not None and request.config["threshold"] == 0.8
        assert request.metadata is not None and request.metadata["updated_by"] == "admin"

    def test_max_depth_validation(self) -> None:
        """Test maximum object nesting depth validation."""
        # Create deeply nested object
        deep_config = {
            "level1": {
                "level2": {"level3": {"level4": {"level5": {"level6": "too deep"}}}}
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            UpdateAgentConfigRequest(config=deep_config)

        assert "exceeds maximum nesting depth" in str(exc_info.value)

    def test_valid_nesting_depth(self) -> None:
        """Test valid nesting depth."""
        # Exactly at max depth (5 levels)
        config = {"l1": {"l2": {"l3": {"l4": {"l5": "valid"}}}}}

        request = UpdateAgentConfigRequest(config=config)
        assert (request.config is not None and 
                request.config["l1"]["l2"]["l3"]["l4"]["l5"] == "valid")

    def test_nested_arrays(self) -> None:
        """Test nested arrays in depth validation."""
        # Arrays also count towards depth
        config = {
            "items": [{"subitems": [{"data": [{"nested": [{"too": ["deep"]}]}]}]}]
        }

        with pytest.raises(ValidationError):
            UpdateAgentConfigRequest(config=config)

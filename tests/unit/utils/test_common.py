"""
Unit tests for common utility functions.

Tests cover:
- String manipulation utilities
- Data transformation functions
- Validation functions
- JSON/Base64 operations
- Hash functions
"""

import uuid as uuid_module
from typing import Any, Dict, List

from src.utils.common import (
    calculate_hash,
    chunk_list,
    decode_base64,
    encode_base64,
    extract_field_from_list,
    flatten_dict,
    group_by_key,
    is_valid_email,
    is_valid_ip_address,
    is_valid_timestamp,
    is_valid_uuid,
    merge_dicts_deep,
    normalize_whitespace,
    safe_json_parse,
    sanitize_string,
    to_camel_case,
    to_snake_case,
    truncate_string,
)


class TestStringManipulation:
    """Tests for string manipulation utilities."""

    def test_sanitize_string_default(self) -> None:
        """Test sanitize_string with default allowed characters."""
        assert sanitize_string("Hello, World!") == "Hello, World!"
        assert sanitize_string("Test@123#$%") == "Test123"
        assert sanitize_string("foo<script>bar</script>") == "fooscriptbarscript"
        # Whitespace (\s) includes newlines and tabs - they are kept by default
        assert "\n" in sanitize_string("line1\nline2\tline3")
        assert "\t" in sanitize_string("line1\nline2\tline3")

    def test_sanitize_string_custom_allowed(self) -> None:
        """Test sanitize_string with custom allowed characters."""
        # When using custom allowed chars, pass literal characters (not regex)
        assert (
            sanitize_string("test@example.com", "testxampleco@.") == "test@example.com"
        )
        assert sanitize_string("Hello-World_123", "HeloWrd123-_") == "Hello-World_123"
        assert sanitize_string("a+b=c", "abc+=") == "a+b=c"

    def test_truncate_string(self) -> None:
        """Test string truncation."""
        assert truncate_string("Hello World", 20) == "Hello World"
        assert truncate_string("Hello World", 8) == "Hello..."
        assert truncate_string("Hello World", 8, "…") == "Hello W…"
        assert truncate_string("Short", 10) == "Short"
        assert truncate_string("", 5) == ""

    def test_normalize_whitespace(self) -> None:
        """Test whitespace normalization."""
        assert normalize_whitespace("  Hello   World  ") == "Hello World"
        assert normalize_whitespace("Tab\there\nNewline") == "Tab here Newline"
        assert normalize_whitespace("   ") == ""
        assert normalize_whitespace("NoSpaces") == "NoSpaces"

    def test_to_snake_case(self) -> None:
        """Test conversion to snake_case."""
        assert to_snake_case("helloWorld") == "hello_world"
        assert to_snake_case("HelloWorld") == "hello_world"
        assert to_snake_case("hello-world") == "hello_world"
        assert to_snake_case("HTTPRequest") == "httprequest"
        assert to_snake_case("getHTTPResponseCode") == "get_httpresponse_code"
        assert to_snake_case("already_snake_case") == "already_snake_case"

    def test_to_camel_case(self) -> None:
        """Test conversion to camelCase."""
        assert to_camel_case("hello_world") == "helloWorld"
        assert to_camel_case("test_case_string") == "testCaseString"
        assert to_camel_case("hello-world") == "helloWorld"
        assert to_camel_case("single") == "single"
        assert to_camel_case("") == ""


class TestDataTransformation:
    """Tests for data transformation utilities."""

    def test_flatten_dict(self) -> None:
        """Test dictionary flattening."""
        nested = {"a": 1, "b": {"c": 2, "d": {"e": 3}}, "f": [1, 2, 3]}
        expected = {"a": 1, "b.c": 2, "b.d.e": 3, "f": [1, 2, 3]}
        assert flatten_dict(nested) == expected
        # Test empty dict
        assert not flatten_dict({})

        # Test already flat dict
        flat = {"a": 1, "b": 2}
        assert flatten_dict(flat) == flat

    def test_flatten_dict_empty_dict(self) -> None:
        """Test flatten_dict with empty dict."""
        assert not flatten_dict({})

    def test_merge_dicts_deep(self) -> None:
        """Test deep dictionary merging."""
        dict1 = {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2]}
        dict2 = {"b": {"c": 20, "f": 4}, "e": [3, 4], "g": 5}
        expected = {"a": 1, "b": {"c": 20, "d": 3, "f": 4}, "e": [3, 4], "g": 5}
        assert merge_dicts_deep(dict1, dict2) == expected

        # Test empty dicts
        assert merge_dicts_deep({}, {"a": 1}) == {"a": 1}
        assert merge_dicts_deep({"a": 1}, {}) == {"a": 1}
        assert not merge_dicts_deep({}, {})

    def test_merge_dicts_deep_empty_base(self) -> None:
        """Test merge_dicts_deep with empty base dict."""
        result = merge_dicts_deep({}, {"a": 1})
        assert result == {"a": 1}

        # Test empty result
        assert not merge_dicts_deep({}, {})

    def test_chunk_list(self) -> None:
        """Test list chunking."""
        # Normal case
        lst = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert chunk_list(lst, 3) == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        # Uneven chunks
        assert chunk_list(lst, 4) == [[1, 2, 3, 4], [5, 6, 7, 8], [9]]

        # Empty list
        assert chunk_list([], 3) == []

        # Chunk size larger than list
        assert chunk_list([1, 2], 5) == [[1, 2]]

    def test_safe_json_parse(self) -> None:
        """Test safe JSON parsing."""
        # Valid JSON
        assert safe_json_parse('{"key": "value"}') == {"key": "value"}
        assert safe_json_parse("[1, 2, 3]") == [1, 2, 3]
        assert safe_json_parse('"string"') == "string"

        # Invalid JSON with default
        assert safe_json_parse("invalid json", default={}) == {}
        assert safe_json_parse('{"unclosed": ', default=None) is None
        assert safe_json_parse(None, default="default") == "default"  # type: ignore[arg-type]

    def test_group_by_key(self) -> None:
        """Test grouping dictionaries by key."""
        items = [
            {"type": "A", "value": 1},
            {"type": "B", "value": 2},
            {"type": "A", "value": 3},
            {"type": "B", "value": 4},
        ]
        result = group_by_key(items, "type")
        assert result == {
            "A": [{"type": "A", "value": 1}, {"type": "A", "value": 3}],
            "B": [{"type": "B", "value": 2}, {"type": "B", "value": 4}],
        }
        # Empty list
        assert not group_by_key([], "type")

        # Missing key in some items
        items_partial: List[Dict[str, Any]] = [
            {"type": "A", "value": 1},
            {"value": 2},  # No type key
            {"type": "A", "value": 3},
        ]
        result = group_by_key(items_partial, "type")
        assert result == {"A": [{"type": "A", "value": 1}, {"type": "A", "value": 3}]}

    def test_group_by_key_empty_list(self) -> None:
        """Test group_by_key with empty list."""
        assert not group_by_key([], "key")

    def test_extract_field_from_list(self) -> None:
        """Test extracting field from list of dicts."""
        items = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]
        assert extract_field_from_list(items, "name") == ["Alice", "Bob", "Charlie"]
        assert extract_field_from_list(items, "id") == [1, 2, 3]

        # Missing field
        assert extract_field_from_list(items, "missing") == []

        # Empty list
        assert extract_field_from_list([], "name") == []


class TestEncodingAndHashing:
    """Tests for encoding and hashing functions."""

    def test_encode_decode_base64(self) -> None:
        """Test base64 encoding and decoding."""  # String encoding
        text = "Hello, World!"
        encoded = encode_base64(text)
        decoded = decode_base64(encoded).decode("utf-8")
        assert decoded == text

        # Binary data
        data = b"Binary\x00Data\xff"
        encoded_bytes = encode_base64(data)
        decoded_bytes = decode_base64(encoded_bytes)
        assert decoded_bytes == data

        # Empty string
        assert decode_base64(encode_base64("")).decode("utf-8") == ""

    def test_calculate_hash(self) -> None:
        """Test hash calculation."""
        # Consistent hashing
        text = "test string"
        hash1 = calculate_hash(text)
        hash2 = calculate_hash(text)
        assert hash1 == hash2

        # Different strings produce different hashes
        assert calculate_hash("string1") != calculate_hash("string2")

        # Different algorithms
        sha256_hash = calculate_hash(text, algorithm="sha256")
        sha512_hash = calculate_hash(text, algorithm="sha512")
        assert sha256_hash != sha512_hash
        assert len(sha512_hash) > len(sha256_hash)

        # Binary data
        assert calculate_hash(b"binary data") != ""


class TestValidation:
    """Tests for validation functions."""

    def test_is_valid_email(self) -> None:
        """Test email validation."""
        # Valid emails
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name@company.co.uk") is True
        assert is_valid_email("user+tag@example.org") is True
        assert is_valid_email("123@example.com") is True

        # Invalid emails
        assert is_valid_email("invalid.email") is False
        assert is_valid_email("@example.com") is False
        assert is_valid_email("user@") is False
        assert is_valid_email("user space@example.com") is False
        assert is_valid_email("") is False

    def test_is_valid_uuid(self) -> None:
        """Test UUID validation."""
        # Valid UUIDs
        valid_uuid = str(uuid_module.uuid4())
        assert is_valid_uuid(valid_uuid) is True
        assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True

        # Invalid UUIDs
        assert is_valid_uuid("invalid-uuid") is False
        assert is_valid_uuid("550e8400-e29b-41d4-a716") is False
        assert is_valid_uuid("") is False
        assert is_valid_uuid("not-a-uuid-at-all") is False

    def test_is_valid_ip_address(self) -> None:
        """Test IP address validation."""
        # Valid IPs
        assert is_valid_ip_address("192.168.1.1") is True
        assert is_valid_ip_address("10.0.0.0") is True
        assert is_valid_ip_address("255.255.255.255") is True
        assert is_valid_ip_address("0.0.0.0") is True

        # Invalid IPs
        assert is_valid_ip_address("256.1.1.1") is False
        assert is_valid_ip_address("192.168.1") is False
        assert is_valid_ip_address("192.168.1.1.1") is False
        assert is_valid_ip_address("not.an.ip.address") is False
        assert is_valid_ip_address("") is False

    def test_is_valid_timestamp(self) -> None:
        """Test timestamp validation."""
        # Valid timestamps
        assert is_valid_timestamp("2024-01-01T00:00:00") is True
        assert is_valid_timestamp("2024-01-01T00:00:00Z") is True
        assert is_valid_timestamp("2024-01-01T00:00:00+00:00") is True
        assert is_valid_timestamp(1704067200) is True  # Unix timestamp
        assert is_valid_timestamp(1704067200.5) is True  # Float timestamp

        # Invalid timestamps
        assert is_valid_timestamp("invalid-date") is False
        assert is_valid_timestamp("2024-13-01") is False  # Invalid month
        assert is_valid_timestamp([]) is False  # type: ignore[arg-type]
        assert is_valid_timestamp({}) is False  # type: ignore[arg-type]

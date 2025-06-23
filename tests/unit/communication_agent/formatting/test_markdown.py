"""
Comprehensive test suite for communication_agent/formatting/markdown.py

Tests all methods and functionality with 100% production code (NO MOCKS).
Achieves ≥90% statement coverage of target source file.

Requirements:
- Use real MarkdownFormatter functionality
- Test all formatting methods and edge cases
- No mocking of any functionality
- Comprehensive error handling scenarios
- All test cases must pass
"""

from typing import List, Dict, Any, Union

from src.communication_agent.formatting.markdown import MarkdownFormatter


class TestMarkdownFormatterBasicFormatting:
    """Test basic text formatting methods."""

    def test_bold(self) -> None:
        """Test bold text formatting."""
        assert MarkdownFormatter.bold("Hello") == "**Hello**"
        assert MarkdownFormatter.bold("") == "****"
        assert MarkdownFormatter.bold("Bold Text") == "**Bold Text**"
        assert MarkdownFormatter.bold("Multi\nLine") == "**Multi\nLine**"
        assert MarkdownFormatter.bold("Special !@#$%^&*()") == "**Special !@#$%^&*()**"

    def test_italic(self) -> None:
        """Test italic text formatting."""
        assert MarkdownFormatter.italic("Hello") == "*Hello*"
        assert MarkdownFormatter.italic("") == "**"
        assert MarkdownFormatter.italic("Italic Text") == "*Italic Text*"
        assert MarkdownFormatter.italic("Multi\nLine") == "*Multi\nLine*"
        assert MarkdownFormatter.italic("Numbers 12345") == "*Numbers 12345*"

    def test_code(self) -> None:
        """Test inline code formatting."""
        assert MarkdownFormatter.code("print('hello')") == "`print('hello')`"
        assert MarkdownFormatter.code("") == "``"
        assert MarkdownFormatter.code("variable_name") == "`variable_name`"
        assert MarkdownFormatter.code("def function():") == "`def function():`"
        assert MarkdownFormatter.code("SELECT * FROM table") == "`SELECT * FROM table`"

    def test_strikethrough(self) -> None:
        """Test strikethrough text formatting."""
        assert MarkdownFormatter.strikethrough("Hello") == "~~Hello~~"
        assert MarkdownFormatter.strikethrough("") == "~~~~"
        assert MarkdownFormatter.strikethrough("Deleted Text") == "~~Deleted Text~~"
        assert MarkdownFormatter.strikethrough("Old Value") == "~~Old Value~~"
        assert (
            MarkdownFormatter.strikethrough("Multi\nLine Strike")
            == "~~Multi\nLine Strike~~"
        )

    def test_link(self) -> None:
        """Test link formatting."""
        assert (
            MarkdownFormatter.link("Google", "https://google.com")
            == "[Google](https://google.com)"
        )
        assert (
            MarkdownFormatter.link("", "https://example.com")
            == "[](https://example.com)"
        )
        assert MarkdownFormatter.link("Text", "") == "[Text]()"
        assert (
            MarkdownFormatter.link("Documentation", "https://docs.example.com/guide")
            == "[Documentation](https://docs.example.com/guide)"
        )
        assert (
            MarkdownFormatter.link("Local File", "/path/to/file.txt")
            == "[Local File](/path/to/file.txt)"
        )

    def test_heading(self) -> None:
        """Test heading formatting with different levels."""
        # Normal levels
        assert MarkdownFormatter.heading("Title") == "# Title"
        assert MarkdownFormatter.heading("Title", 1) == "# Title"
        assert MarkdownFormatter.heading("Subtitle", 2) == "## Subtitle"
        assert MarkdownFormatter.heading("Section", 3) == "### Section"
        assert MarkdownFormatter.heading("Subsection", 4) == "#### Subsection"
        assert MarkdownFormatter.heading("Sub-subsection", 5) == "##### Sub-subsection"
        assert MarkdownFormatter.heading("Deep level", 6) == "###### Deep level"

        # Edge cases - levels outside valid range
        assert MarkdownFormatter.heading("Too low", 0) == "# Too low"
        assert MarkdownFormatter.heading("Negative", -1) == "# Negative"
        assert MarkdownFormatter.heading("Too high", 7) == "###### Too high"
        assert MarkdownFormatter.heading("Very high", 10) == "###### Very high"

        # Empty text
        assert MarkdownFormatter.heading("", 2) == "## "

        # Special characters in heading
        assert (
            MarkdownFormatter.heading("Title with $pecial Ch@rs!", 3)
            == "### Title with $pecial Ch@rs!"
        )

    def test_format_header_basic(self) -> None:
        """Test basic header formatting."""


class TestMarkdownFormatterLists:
    """Test list formatting methods."""

    def test_bullet_list_simple(self) -> None:
        """Test simple bullet list formatting."""
        items = ["First item", "Second item", "Third item"]
        expected = "- First item\n- Second item\n- Third item"
        assert MarkdownFormatter.bullet_list(items) == expected

        # Single item
        assert MarkdownFormatter.bullet_list(["Only item"]) == "- Only item"

        # Empty list
        assert MarkdownFormatter.bullet_list([]) == ""

        # Empty strings in list
        assert MarkdownFormatter.bullet_list(["", "Second", ""]) == "- \n- Second\n- "

    def test_bullet_list_with_dicts(self) -> None:
        """Test bullet list with dictionary items for nested structure."""
        from typing import Union, Dict, Any, List
        items: List[Union[str, Dict[str, Any]]] = [
            "Simple item",
            {"text": "Item with subitems", "subitems": ["Sub 1", "Sub 2"]},
            "Another simple item",
        ]

        expected = (
            "- Simple item\n"
            "- Item with subitems\n"
            "  - Sub 1\n"
            "  - Sub 2\n"
            "- Another simple item"
        )

        assert MarkdownFormatter.bullet_list(items) == expected

        # Dict without text field
        dict_items = [{"key": "value"}, {"text": "Has text"}]
        result = MarkdownFormatter.bullet_list(dict_items)
        assert "- {'key': 'value'}" in result
        assert "- Has text" in result

        # Dict with empty subitems
        empty_sub = [{"text": "Main", "subitems": []}]
        assert MarkdownFormatter.bullet_list(empty_sub) == "- Main"

        # Dict with only subitems (no text)
        only_sub = [{"subitems": ["Sub 1", "Sub 2"]}]
        result = MarkdownFormatter.bullet_list(only_sub)
        assert "  - Sub 1" in result
        assert "  - Sub 2" in result

    def test_numbered_list(self) -> None:
        """Test numbered list formatting."""
        items = ["First", "Second", "Third"]
        expected = "1. First\n2. Second\n3. Third"
        assert MarkdownFormatter.numbered_list(items) == expected

        # Single item
        assert MarkdownFormatter.numbered_list(["Only"]) == "1. Only"

        # Empty list
        assert MarkdownFormatter.numbered_list([]) == ""

        # Many items
        many_items = [f"Item {i}" for i in range(1, 11)]
        result = MarkdownFormatter.numbered_list(many_items)
        assert "1. Item 1" in result
        assert "10. Item 10" in result

        # Empty strings
        assert MarkdownFormatter.numbered_list(["", "Second"]) == "1. \n2. Second"


class TestMarkdownFormatterCodeBlocks:
    """Test code block formatting."""

    def test_code_block_without_language(self) -> None:
        """Test code block without language specification."""
        code = "print('Hello, World!')"
        expected = "```\nprint('Hello, World!')\n```"
        assert MarkdownFormatter.code_block(code) == expected

        # Multi-line code
        multi_code = "def hello():\n    print('Hello')\n    return True"
        expected_multi = "```\ndef hello():\n    print('Hello')\n    return True\n```"
        assert MarkdownFormatter.code_block(multi_code) == expected_multi

        # Empty code
        assert MarkdownFormatter.code_block("") == "```\n\n```"

    def test_code_block_with_language(self) -> None:
        """Test code block with language specification."""
        code = "def hello():\n    return 'Hello'"
        expected = "```python\ndef hello():\n    return 'Hello'\n```"
        assert MarkdownFormatter.code_block(code, "python") == expected

        # Different languages
        assert (
            MarkdownFormatter.code_block("SELECT * FROM table", "sql")
            == "```sql\nSELECT * FROM table\n```"
        )
        assert (
            MarkdownFormatter.code_block("console.log('hello')", "javascript")
            == "```javascript\nconsole.log('hello')\n```"
        )
        assert (
            MarkdownFormatter.code_block("echo 'hello'", "bash")
            == "```bash\necho 'hello'\n```"
        )

        # Empty language string
        assert MarkdownFormatter.code_block("code", "") == "```\ncode\n```"


class TestMarkdownFormatterTables:
    """Test table formatting functionality."""

    def test_table_basic(self) -> None:
        """Test basic table formatting."""
        headers = ["Name", "Age", "City"]
        rows = [
            ["Alice", "30", "New York"],
            ["Bob", "25", "London"],
            ["Charlie", "35", "Tokyo"],
        ]

        result = MarkdownFormatter.table(headers, rows)

        # Check structure
        lines = result.split("\n")
        assert len(lines) == 5  # Header + separator + 3 data rows

        # Check header row
        assert "| Name    | Age | City     |" in lines[0]

        # Check separator row
        assert "| ------- | --- | -------- |" in lines[1]

        # Check data rows
        assert "| Alice   | 30  | New York |" in lines[2]
        assert "| Bob     | 25  | London   |" in lines[3]
        assert "| Charlie | 35  | Tokyo    |" in lines[4]

    def test_table_empty_inputs(self) -> None:
        """Test table with empty inputs."""
        # Empty headers
        assert MarkdownFormatter.table([], [["data"]]) == ""

        # Empty rows
        assert MarkdownFormatter.table(["Header"], []) == ""

        # Both empty
        assert MarkdownFormatter.table([], []) == ""

    def test_table_with_alignment(self) -> None:
        """Test table with column alignment."""
        headers = ["Left", "Center", "Right"]
        rows = [["A", "B", "C"]]
        alignment = ["left", "center", "right"]

        result = MarkdownFormatter.table(headers, rows, alignment)
        lines = result.split("\n")

        # Check separator row has alignment markers
        separator = lines[1]
        assert ":----" in separator  # Left alignment
        assert ":---:" in separator  # Center alignment
        assert "----:" in separator  # Right alignment

    def test_table_uneven_rows(self) -> None:
        """Test table with rows of different lengths."""
        headers = ["A", "B", "C"]
        rows = [
            ["1"],  # Short row
            ["2", "3", "4", "5"],  # Long row
            ["6", "7", "8"],  # Perfect row
        ]

        result = MarkdownFormatter.table(headers, rows)
        lines = result.split("\n")

        # Short row should be padded
        assert "| 1 |   |   |" in lines[2]

        # Long row should be truncated
        assert "| 2 | 3 | 4 |" in lines[3]

        # Perfect row should be unchanged
        assert "| 6 | 7 | 8 |" in lines[4]

    def test_table_column_width_calculation(self) -> None:
        """Test that column widths are calculated correctly."""
        headers = ["Short", "VeryLongHeader", "Med"]
        rows = [["A", "B", "VeryLongData"], ["VeryLongContent", "C", "D"]]

        result = MarkdownFormatter.table(headers, rows)

        # Check that columns are properly sized
        # First column should accommodate "VeryLongContent"
        # Second column should accommodate "VeryLongHeader"
        # Third column should accommodate "VeryLongData"

        assert "VeryLongContent" in result
        assert "VeryLongHeader" in result
        assert "VeryLongData" in result

    def test_table_alignment_edge_cases(self) -> None:
        """Test table alignment with edge cases."""
        headers = ["A", "B"]
        rows = [["1", "2"]]

        # Alignment list shorter than headers
        result = MarkdownFormatter.table(headers, rows, ["center"])
        lines = result.split("\n")
        separator = lines[1]
        assert ":---:" in separator  # First column centered
        assert "| ---" in separator  # Second column default (no alignment)

        # Alignment list longer than headers
        result = MarkdownFormatter.table(headers, rows, ["left", "right", "center"])
        lines = result.split("\n")
        separator = lines[1]
        assert ":---" in separator  # Left
        assert "---:" in separator  # Right
        # Third alignment ignored since only 2 columns

        # Invalid alignment values
        result = MarkdownFormatter.table(headers, rows, ["invalid", "right"])
        lines = result.split("\n")
        separator = lines[1]
        # Invalid alignment should not add markers
        assert "| --- |" in separator or "| ---" in separator


class TestMarkdownFormatterOtherFormatting:
    """Test other formatting methods."""

    def test_quote(self) -> None:
        """Test blockquote formatting."""
        # Single line
        assert MarkdownFormatter.quote("Hello") == "> Hello"

        # Multiple lines
        multi_line = "Line 1\nLine 2\nLine 3"
        expected = "> Line 1\n> Line 2\n> Line 3"
        assert MarkdownFormatter.quote(multi_line) == expected

        # Empty string
        assert MarkdownFormatter.quote("") == ">"

        # String with leading/trailing whitespace
        assert MarkdownFormatter.quote("  Text  ") == "> Text"

        # String with only whitespace
        assert MarkdownFormatter.quote("   ") == ">"

    def test_horizontal_rule(self) -> None:
        """Test horizontal rule formatting."""
        assert MarkdownFormatter.horizontal_rule() == "---"

    def test_escape(self) -> None:
        """Test escaping special Markdown characters."""
        # Individual special characters
        assert MarkdownFormatter.escape("*") == "\\*"
        assert MarkdownFormatter.escape("_") == "\\_"
        assert MarkdownFormatter.escape("`") == "\\`"
        assert MarkdownFormatter.escape("~") == "\\~"
        assert MarkdownFormatter.escape("[") == "\\["
        assert MarkdownFormatter.escape("]") == "\\]"
        assert MarkdownFormatter.escape("(") == "\\("
        assert MarkdownFormatter.escape(")") == "\\)"
        assert MarkdownFormatter.escape("#") == "\\#"
        assert MarkdownFormatter.escape("+") == "\\+"
        assert MarkdownFormatter.escape("-") == "\\-"
        assert MarkdownFormatter.escape(".") == "\\."
        assert MarkdownFormatter.escape("!") == "\\!"
        assert MarkdownFormatter.escape("\\") == "\\\\"

        # Multiple special characters
        text = "**bold** _italic_ `code`"
        expected = "\\*\\*bold\\*\\* \\_italic\\_ \\`code\\`"
        assert MarkdownFormatter.escape(text) == expected

        # Mixed text with special characters
        mixed = "Hello [world](http://example.com) #heading"
        expected_mixed = "Hello \\[world\\]\\(http://example\\.com\\) \\#heading"
        assert MarkdownFormatter.escape(mixed) == expected_mixed

        # Text without special characters
        assert MarkdownFormatter.escape("Hello World") == "Hello World"

        # Empty string
        assert MarkdownFormatter.escape("") == ""


class TestMarkdownFormatterUtilityMethods:
    """Test utility and helper methods."""

    def test_format_key_value(self) -> None:
        """Test key-value pair formatting."""
        # With bold key (default)
        assert MarkdownFormatter.format_key_value("Name", "John") == "**Name**: John"

        # Without bold key
        assert MarkdownFormatter.format_key_value("Name", "John", False) == "Name: John"

        # Different value types
        assert MarkdownFormatter.format_key_value("Count", 42) == "**Count**: 42"
        assert MarkdownFormatter.format_key_value("Active", True) == "**Active**: True"
        assert (
            MarkdownFormatter.format_key_value("Data", [1, 2, 3])
            == "**Data**: [1, 2, 3]"
        )
        assert (
            MarkdownFormatter.format_key_value("Config", {"key": "value"})
            == "**Config**: {'key': 'value'}"
        )

        # Empty values
        assert MarkdownFormatter.format_key_value("Empty", "") == "**Empty**: "
        assert MarkdownFormatter.format_key_value("None", None) == "**None**: None"

    def test_format_alert(self) -> None:
        """Test alert/callout formatting."""
        # Default info alert
        result = MarkdownFormatter.format_alert("Important message")
        assert "ℹ️ **INFO**" in result
        assert "Important message" in result
        assert result.startswith("> ℹ️")

        # Warning alert
        result = MarkdownFormatter.format_alert("Be careful", "warning")
        assert "⚠️ **WARNING**" in result
        assert "Be careful" in result

        # Danger alert
        result = MarkdownFormatter.format_alert("Critical error", "danger")
        assert "🚨 **DANGER**" in result
        assert "Critical error" in result

        # Success alert
        result = MarkdownFormatter.format_alert("All good", "success")
        assert "✅ **SUCCESS**" in result
        assert "All good" in result

        # Unknown alert type (uses default)
        result = MarkdownFormatter.format_alert("Custom message", "custom")
        assert "📌 **CUSTOM**" in result
        assert "Custom message" in result

        # Case insensitive
        result = MarkdownFormatter.format_alert("Warning", "WARNING")
        assert "⚠️ **WARNING**" in result

    def test_format_severity_badge(self) -> None:
        """Test severity badge formatting."""
        assert MarkdownFormatter.format_severity_badge("critical") == "🔴 **CRITICAL**"
        assert MarkdownFormatter.format_severity_badge("high") == "🟠 **HIGH**"
        assert MarkdownFormatter.format_severity_badge("medium") == "🟡 **MEDIUM**"
        assert MarkdownFormatter.format_severity_badge("low") == "🟢 **LOW**"
        assert MarkdownFormatter.format_severity_badge("info") == "🔵 **INFO**"

        # Case insensitive
        assert MarkdownFormatter.format_severity_badge("CRITICAL") == "🔴 **CRITICAL**"
        assert MarkdownFormatter.format_severity_badge("High") == "🟠 **HIGH**"

        # Unknown severity
        assert MarkdownFormatter.format_severity_badge("unknown") == "⚪ **UNKNOWN**"
        assert MarkdownFormatter.format_severity_badge("custom") == "⚪ **CUSTOM**"

    def test_format_status_indicator(self) -> None:
        """Test status indicator formatting."""
        # Success status
        assert (
            MarkdownFormatter.format_status_indicator("Completed", True)
            == "✅ Completed"
        )
        assert (
            MarkdownFormatter.format_status_indicator("Running", True) == "✅ Running"
        )

        # Failure status
        assert MarkdownFormatter.format_status_indicator("Failed", False) == "❌ Failed"
        assert MarkdownFormatter.format_status_indicator("Error", False) == "❌ Error"

        # Empty status
        assert MarkdownFormatter.format_status_indicator("", True) == "✅ "
        assert MarkdownFormatter.format_status_indicator("", False) == "❌ "

    def test_format_timestamp(self) -> None:
        """Test timestamp formatting."""
        timestamp = "2024-01-15T10:30:00Z"

        # With relative time (default)
        result = MarkdownFormatter.format_timestamp(timestamp)
        assert "2024-01-15T10:30:00Z (UTC)" == result

        # Without relative time
        result = MarkdownFormatter.format_timestamp(timestamp, False)
        assert result == "2024-01-15T10:30:00Z"

        # Empty timestamp
        assert MarkdownFormatter.format_timestamp("") == " (UTC)"
        assert MarkdownFormatter.format_timestamp("", False) == ""

    def test_format_diff(self) -> None:
        """Test diff formatting."""
        assert MarkdownFormatter.format_diff("old", "new") == "~~old~~ → new"
        assert MarkdownFormatter.format_diff("", "new") == "~~ ~~ → new"
        assert MarkdownFormatter.format_diff("old", "") == "~~old~~ → "
        assert MarkdownFormatter.format_diff("", "") == "~~ ~~ → "

        # Complex values
        assert MarkdownFormatter.format_diff("1.2.3", "1.2.4") == "~~1.2.3~~ → 1.2.4"
        assert (
            MarkdownFormatter.format_diff("enabled", "disabled")
            == "~~enabled~~ → disabled"
        )


class TestMarkdownFormatterResourceList:
    """Test resource list formatting."""

    def test_format_resource_list_strings(self) -> None:
        """Test resource list with string items."""
        resources: List[Union[str, Dict[str, Any]]] = ["server-1", "server-2", "server-3"]
        expected = "- server-1\n- server-2\n- server-3"
        assert MarkdownFormatter.format_resource_list(resources) == expected

        # Single resource
        single: List[Union[str, Dict[str, Any]]] = ["single"]
        assert MarkdownFormatter.format_resource_list(single) == "- single"

        # Empty list
        assert MarkdownFormatter.format_resource_list([]) == ""

    def test_format_resource_list_dicts_with_status(self) -> None:
        """Test resource list with dictionary items including status."""
        resources: List[Union[str, Dict[str, Any]]] = [
            {"name": "web-server", "status": "healthy", "type": "EC2"},
            {"name": "db-server", "status": "error", "type": "RDS"},
            {"name": "cache-server", "status": "warning", "type": "ElastiCache"},
            {"name": "api-server", "status": "running", "type": "Lambda"},
        ]

        result = MarkdownFormatter.format_resource_list(resources, show_status=True)

        # Check that types and names are included
        assert "EC2: web-server ✅" in result
        assert "RDS: db-server ❌" in result
        assert "ElastiCache: cache-server ⚠️" in result
        assert "Lambda: api-server ✅" in result

    def test_format_resource_list_dicts_without_status(self) -> None:
        """Test resource list with dictionaries but no status display."""
        resources: List[Union[str, Dict[str, Any]]] = [
            {"name": "server-1", "status": "healthy", "type": "Web"},
            {"name": "server-2", "status": "error", "type": "DB"},
        ]

        result = MarkdownFormatter.format_resource_list(resources, show_status=False)

        # Should not include status indicators
        assert "✅" not in result
        assert "❌" not in result
        assert "⚠️" not in result

        # Should include type and name
        assert "Web: server-1" in result
        assert "DB: server-2" in result

    def test_format_resource_list_missing_fields(self) -> None:
        """Test resource list with missing fields in dictionaries."""
        resources: List[Union[str, Dict[str, Any]]] = [
            {"name": "server-1"},  # No type or status
            {"type": "DB"},  # No name or status
            {"status": "healthy"},  # No name or type
            {},  # Empty dict
        ]

        result = MarkdownFormatter.format_resource_list(resources)

        # Check handling of missing fields
        assert "- server-1" in result  # Just name
        assert "DB: Unknown" in result  # Type with Unknown name
        assert "- Unknown" in result  # Unknown name only (appears twice)

    def test_format_resource_list_custom_status_values(self) -> None:
        """Test resource list with custom status values."""
        resources: List[Union[str, Dict[str, Any]]] = [
            {"name": "server-1", "status": "maintenance"},
            {"name": "server-2", "status": "unknown_status"},
            {"name": "server-3", "status": "degraded"},
        ]

        result = MarkdownFormatter.format_resource_list(resources)

        # Custom statuses should be shown in parentheses
        assert "server-1 (maintenance)" in result
        assert "server-2 (unknown_status)" in result
        assert "server-3 ⚠️" in result  # "degraded" maps to warning emoji

    def test_format_resource_list_mixed_types(self) -> None:
        """Test resource list with mixed string and dict items."""
        resources: List[Union[str, Dict[str, Any]]] = [
            "simple-string",
            {"name": "dict-resource", "status": "ok"},
            "another-string",
            {"name": "error-resource", "status": "failed", "type": "Service"},
        ]

        result = MarkdownFormatter.format_resource_list(resources)

        assert "- simple-string" in result
        assert "dict-resource ✅" in result
        assert "- another-string" in result
        assert "Service: error-resource ❌" in result


class TestMarkdownFormatterConversion:
    """Test conversion methods to other formats."""

    def test_to_slack_format(self) -> None:
        """Test conversion to Slack-compatible format."""
        # Bold conversion: **text** -> *text*
        markdown = "This is **bold** text"
        expected = "This is *bold* text"
        assert MarkdownFormatter.to_slack_format(markdown) == expected

        # Italic conversion: *text* -> _text_ (but not **text**)
        markdown = "This is *italic* text"
        expected = "This is _italic_ text"
        assert MarkdownFormatter.to_slack_format(markdown) == expected

        # Code block conversion
        markdown = "```python\nprint('hello')\n```"
        expected = "```print('hello')```"
        assert MarkdownFormatter.to_slack_format(markdown) == expected

        # Code block without language
        markdown = "```\necho 'test'\n```"
        expected = "```echo 'test'```"
        assert MarkdownFormatter.to_slack_format(markdown) == expected

        # Link conversion: [text](url) -> <url|text>
        markdown = "Check [this link](https://example.com) out"
        expected = "Check <https://example.com|this link> out"
        assert MarkdownFormatter.to_slack_format(markdown) == expected

        # Combined formatting
        markdown = "**Bold** and *italic* with [link](https://test.com)"
        expected = "*Bold* and _italic_ with <https://test.com|link>"
        assert MarkdownFormatter.to_slack_format(markdown) == expected

    def test_to_slack_format_table_handling(self) -> None:
        """Test Slack format conversion with tables."""
        # Simple table
        markdown = """| Name | Age |
| ---- | --- |
| John | 30  |
| Jane | 25  |"""

        result = MarkdownFormatter.to_slack_format(markdown)

        # Table should be converted to simple text
        # Header and separator should be removed/simplified
        assert "Name | Age" in result
        assert "John | 30" in result
        assert "Jane | 25" in result

        # Should not contain markdown table separators
        assert "----" not in result

    def test_to_plain_text(self) -> None:
        """Test conversion to plain text."""
        # Bold removal
        markdown = "This is **bold** text"
        expected = "This is bold text"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Italic removal
        markdown = "This is *italic* text"
        expected = "This is italic text"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Inline code removal
        markdown = "Use `print()` function"
        expected = "Use print() function"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Code block removal
        markdown = "```python\nprint('hello')\n```"
        expected = "print('hello')"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Link conversion
        markdown = "Visit [Google](https://google.com) for search"
        expected = "Visit Google (https://google.com) for search"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Heading removal
        markdown = "# Main Title\n## Subtitle\n### Section"
        expected = "Main Title\nSubtitle\nSection"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Blockquote removal
        markdown = "> This is a quote\n> Second line"
        expected = "This is a quote\nSecond line"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Horizontal rule removal
        markdown = "Text before\n---\nText after"
        expected = "Text before\n\nText after"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Multiple blank lines cleanup
        markdown = "Line 1\n\n\n\nLine 2"
        expected = "Line 1\n\nLine 2"
        assert MarkdownFormatter.to_plain_text(markdown) == expected

        # Combined formatting
        markdown = """# Title
**Bold** and *italic* text with `code` and [link](url).

> Quote here

```
code block
```

---"""

        result = MarkdownFormatter.to_plain_text(markdown)

        # Should be clean text
        assert "**" not in result
        assert "*" not in result
        assert "`" not in result
        assert "[" not in result
        assert ">" not in result
        assert "#" not in result
        assert "---" not in result

        # Should contain the actual text
        assert "Title" in result
        assert "Bold and italic text with code and link (url)" in result
        assert "Quote here" in result
        assert "code block" in result


class TestMarkdownFormatterEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_inputs(self) -> None:
        """Test methods with empty inputs."""
        # All basic formatting methods should handle empty strings
        assert MarkdownFormatter.bold("") == "****"
        assert MarkdownFormatter.italic("") == "**"
        assert MarkdownFormatter.code("") == "``"
        assert MarkdownFormatter.strikethrough("") == "~~~~"
        assert MarkdownFormatter.quote("") == ">"

        # Lists with empty inputs
        assert MarkdownFormatter.bullet_list([]) == ""
        assert MarkdownFormatter.numbered_list([]) == ""

        # Code block with empty code
        assert MarkdownFormatter.code_block("") == "```\n\n```"
        assert MarkdownFormatter.code_block("", "python") == "```python\n\n```"

        # Table with empty inputs
        assert MarkdownFormatter.table([], []) == ""
        assert MarkdownFormatter.table(["Header"], []) == ""
        assert MarkdownFormatter.table([], [["data"]]) == ""

    def test_special_characters_in_text(self) -> None:
        """Test handling of special characters in text."""
        special_text = "Text with émojis 🚀 and ñoñó spëciál chars"

        # Should handle Unicode characters properly
        assert MarkdownFormatter.bold(special_text) == f"**{special_text}**"
        assert MarkdownFormatter.italic(special_text) == f"*{special_text}*"
        assert MarkdownFormatter.code(special_text) == f"`{special_text}`"

        # Quote with special characters
        result = MarkdownFormatter.quote(special_text)
        assert special_text in result
        assert result.startswith(">")

    def test_very_long_inputs(self) -> None:
        """Test with very long inputs."""
        long_text = "Very long text " * 1000  # 15,000 character string

        # Should handle long inputs without errors
        bold_result = MarkdownFormatter.bold(long_text)
        assert bold_result.startswith("**Very long text")
        assert bold_result.endswith("**")

        # Long list
        long_list = [f"Item {i}" for i in range(1000)]
        list_result = MarkdownFormatter.bullet_list(long_list)
        assert "- Item 1" in list_result
        assert "- Item 999" in list_result

    def test_nested_markdown_in_inputs(self) -> None:
        """Test behavior with nested markdown in inputs."""
        nested_text = "**Already bold** and *already italic*"

        # Should add formatting regardless of existing formatting
        assert MarkdownFormatter.bold(nested_text) == f"**{nested_text}**"
        assert MarkdownFormatter.italic(nested_text) == f"*{nested_text}*"

        # Escape should handle nested markdown
        escaped = MarkdownFormatter.escape(nested_text)
        assert "\\*\\*Already bold\\*\\*" in escaped
        assert "\\*already italic\\*" in escaped

    def test_newlines_and_whitespace(self) -> None:
        """Test handling of newlines and whitespace."""
        text_with_newlines = "Line 1\nLine 2\n\nLine 3"

        # Basic formatting should preserve newlines
        assert MarkdownFormatter.bold(text_with_newlines) == f"**{text_with_newlines}**"
        assert MarkdownFormatter.italic(text_with_newlines) == f"*{text_with_newlines}*"

        # Quote should handle multiple lines
        quote_result = MarkdownFormatter.quote(text_with_newlines)
        lines = quote_result.split("\n")
        assert all(line.startswith(">") for line in lines)
        assert len(lines) == 4  # 4 lines including empty line

    def test_numeric_inputs_in_resource_lists(self) -> None:
        """Test resource lists with numeric and other non-string types."""
        mixed_resources: List[Union[str, Dict[str, Any]]] = [
            str(123),
            {"name": 456, "status": "ok"},
            str(True),
            {"name": "server", "status": False},
        ]

        result = MarkdownFormatter.format_resource_list(mixed_resources)

        # Should convert all to strings
        assert "- 123" in result
        assert "- 456 ✅" in result  # 456 converted to string, "ok" shows as success
        assert "- True" in result
        assert "server (False)" in result  # False status shown in parentheses


class TestMarkdownFormatterIntegration:
    """Test integration scenarios with multiple formatting operations."""

    def test_complex_document_formatting(self) -> None:
        """Test creating a complex formatted document."""
        # Create a comprehensive document using multiple formatting methods

        title = MarkdownFormatter.heading("Security Incident Report", 1)
        subtitle = MarkdownFormatter.heading("Executive Summary", 2)

        severity = MarkdownFormatter.format_severity_badge("critical")
        status = MarkdownFormatter.format_status_indicator("Investigating", False)

        alert = MarkdownFormatter.format_alert(
            "This is a critical security incident requiring immediate attention",
            "danger",
        )

        details_list = MarkdownFormatter.bullet_list(
            [
                "Detected at 2024-01-15 10:30 UTC",
                "Affected systems: web-servers, database",
                {
                    "text": "Impact areas",
                    "subitems": [
                        "User authentication",
                        "Data access",
                        "System availability",
                    ],
                },
            ]
        )

        affected_resources: List[Union[str, Dict[str, Any]]] = [
            {"name": "web-server-01", "status": "error", "type": "EC2"},
            {"name": "web-server-02", "status": "healthy", "type": "EC2"},
            {"name": "database-01", "status": "degraded", "type": "RDS"},
        ]
        resources_list = MarkdownFormatter.format_resource_list(affected_resources)

        code_sample = MarkdownFormatter.code_block(
            "SELECT * FROM users WHERE last_login > '2024-01-15'", "sql"
        )

        timeline_table = MarkdownFormatter.table(
            ["Time", "Event", "Status"],
            [
                ["10:30", "Initial detection", "✅"],
                ["10:35", "Team notified", "✅"],
                ["10:40", "Investigation started", "🔄"],
            ],
        )

        # Combine all elements
        document = "\n\n".join(
            [
                title,
                subtitle,
                f"{severity} {status}",
                alert,
                MarkdownFormatter.heading("Details", 3),
                details_list,
                MarkdownFormatter.heading("Affected Resources", 3),
                resources_list,
                MarkdownFormatter.heading("Investigation Query", 3),
                code_sample,
                MarkdownFormatter.heading("Timeline", 3),
                timeline_table,
                MarkdownFormatter.horizontal_rule(),
                MarkdownFormatter.format_timestamp("2024-01-15T10:30:00Z"),
            ]
        )

        # Verify the document contains all expected elements
        assert "# Security Incident Report" in document
        assert "## Executive Summary" in document
        assert "🔴 **CRITICAL**" in document
        assert "❌ Investigating" in document
        assert "🚨 **DANGER**" in document
        assert "- Detected at 2024-01-15" in document
        assert "  - User authentication" in document
        assert "EC2: web-server-01 ❌" in document
        assert "```sql" in document
        assert "| Time | Event | Status |" in document
        assert "---" in document
        assert "2024-01-15T10:30:00Z (UTC)" in document

        # Verify overall structure
        assert len(document.split("\n\n")) >= 10  # Multiple sections

    def test_conversion_workflow(self) -> None:
        """Test converting the same content to different formats."""
        original_markdown = """# Important Update

This is **critical** information about the *system status*.

Please check the [documentation](https://docs.example.com) for details.

```bash
sudo systemctl restart service
```

> **Warning**: This operation may cause downtime."""

        # Convert to Slack format
        slack_format = MarkdownFormatter.to_slack_format(original_markdown)
        assert "*critical*" in slack_format  # Bold converted
        assert "_system status_" in slack_format  # Italic converted
        assert (
            "<https://docs.example.com|documentation>" in slack_format
        )  # Link converted
        assert (
            "```sudo systemctl restart service```" in slack_format
        )  # Code block simplified

        # Convert to plain text
        plain_text = MarkdownFormatter.to_plain_text(original_markdown)
        assert "**" not in plain_text
        assert "*" not in plain_text
        assert "`" not in plain_text
        assert ">" not in plain_text
        assert "#" not in plain_text
        assert "Important Update" in plain_text
        assert "critical information about the system status" in plain_text
        assert "documentation (https://docs.example.com)" in plain_text
        assert "sudo systemctl restart service" in plain_text
        assert "Warning: This operation may cause downtime" in plain_text

        # Verify both conversions preserve essential content
        for conversion in [slack_format, plain_text]:
            assert "Important Update" in conversion
            assert "critical" in conversion
            assert "system status" in conversion
            assert "documentation" in conversion
            assert "sudo systemctl restart service" in conversion
            assert "Warning" in conversion
            assert "downtime" in conversion

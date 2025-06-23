"""
Markdown formatter for rich text message formatting.

Provides utilities for formatting messages with Markdown syntax,
including tables, code blocks, and styling.
"""

import re
from typing import Any, Dict, List, Optional, Sequence, Union

from src.utils.logging import get_logger

logger = get_logger(__name__)


class MarkdownFormatter:
    """Formatter for Markdown-based rich text."""

    @staticmethod
    def bold(text: str) -> str:
        """Format text as bold."""
        return f"**{text}**"

    @staticmethod
    def italic(text: str) -> str:
        """Format text as italic."""
        return f"*{text}*"

    @staticmethod
    def code(text: str) -> str:
        """Format text as inline code."""
        return f"`{text}`"

    @staticmethod
    def strikethrough(text: str) -> str:
        """Format text with strikethrough."""
        return f"~~{text}~~"

    @staticmethod
    def link(text: str, url: str) -> str:
        """Create a markdown link."""
        return f"[{text}]({url})"

    @staticmethod
    def heading(text: str, level: int = 1) -> str:
        """Create a heading."""
        if level < 1:
            level = 1
        elif level > 6:
            level = 6
        return f"{'#' * level} {text}"

    @staticmethod
    def bullet_list(items: Sequence[Union[str, Dict[str, Any]]]) -> str:
        """Create a bulleted list."""
        lines = []
        for item in items:
            if isinstance(item, dict):
                # Handle nested structure
                main = item.get("text", str(item))
                lines.append(f"- {main}")
                if "subitems" in item:
                    for subitem in item["subitems"]:
                        lines.append(f"  - {subitem}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)

    @staticmethod
    def numbered_list(items: List[str]) -> str:
        """Create a numbered list."""
        return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))

    @staticmethod
    def code_block(code: str, language: Optional[str] = None) -> str:
        """
        Create a code block.

        Args:
            code: The code content
            language: Optional language for syntax highlighting

        Returns:
            Formatted code block
        """
        if language:
            return f"```{language}\n{code}\n```"
        else:
            return f"```\n{code}\n```"

    @staticmethod
    def table(  # noqa: C901
        headers: List[str],
        rows: List[List[str]],
        alignment: Optional[List[str]] = None,
    ) -> str:
        """
        Create a Markdown table.

        Args:
            headers: Table headers
            rows: Table rows
            alignment: Column alignment ('left', 'center', 'right')

        Returns:
            Formatted Markdown table
        """
        if not headers or not rows:
            return ""

        # Ensure all rows have same number of columns
        num_cols = len(headers)
        normalized_rows = []
        for row in rows:
            if len(row) < num_cols:
                row = row + [""] * (num_cols - len(row))
            elif len(row) > num_cols:
                row = row[:num_cols]
            normalized_rows.append(row)

        # Calculate column widths
        col_widths = []
        for i in range(num_cols):
            width = len(headers[i])
            for row in normalized_rows:
                width = max(width, len(str(row[i])))
            col_widths.append(width)

        # Build header row
        header_parts = []
        for i, header in enumerate(headers):
            header_parts.append(header.ljust(col_widths[i]))
        table_lines = ["| " + " | ".join(header_parts) + " |"]

        # Build separator row with alignment
        separator_parts = []
        for i in range(num_cols):
            separator = "-" * col_widths[i]
            if alignment and i < len(alignment):
                if alignment[i] == "center":
                    separator = ":" + separator[1:-1] + ":"
                elif alignment[i] == "right":
                    separator = separator[:-1] + ":"
                elif alignment[i] == "left":
                    separator = ":" + separator[1:]
            separator_parts.append(separator)
        table_lines.append("| " + " | ".join(separator_parts) + " |")

        # Build data rows
        for row in normalized_rows:
            row_parts = []
            for i, cell in enumerate(row):
                row_parts.append(str(cell).ljust(col_widths[i]))
            table_lines.append("| " + " | ".join(row_parts) + " |")

        return "\n".join(table_lines)

    @staticmethod
    def quote(text: str) -> str:
        """Create a blockquote."""
        lines = text.strip().split("\n")
        return "\n".join(f"> {line}" for line in lines)

    @staticmethod
    def horizontal_rule() -> str:
        """Create a horizontal rule."""
        return "---"

    @staticmethod
    def escape(text: str) -> str:
        """Escape special Markdown characters."""
        # Characters that need escaping in Markdown
        special_chars = r"*_`~[]()#+-.!\\"
        pattern = f"([{re.escape(special_chars)}])"
        return re.sub(pattern, r"\\\1", text)

    @staticmethod
    def format_key_value(key: str, value: Any, bold_key: bool = True) -> str:
        """Format a key-value pair."""
        formatted_key = MarkdownFormatter.bold(key) if bold_key else key
        return f"{formatted_key}: {value}"

    @staticmethod
    def format_alert(message: str, alert_type: str = "info") -> str:
        """
        Format an alert/callout box.

        Args:
            message: Alert message
            alert_type: Type of alert (info, warning, danger, success)

        Returns:
            Formatted alert
        """
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "danger": "🚨",
            "success": "✅",
        }

        emoji = emoji_map.get(alert_type.lower(), "📌")
        title = alert_type.upper()

        return f"""
> {emoji} **{title}**
>
> {message}
""".strip()

    @staticmethod
    def format_severity_badge(severity: str) -> str:
        """Format a severity level as a badge."""
        severity_lower = severity.lower()

        # Emoji indicators
        emoji_map = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵",
        }

        emoji = emoji_map.get(severity_lower, "⚪")
        return f"{emoji} **{severity.upper()}**"

    @staticmethod
    def format_status_indicator(status: str, success: bool) -> str:
        """Format a status with visual indicator."""
        indicator = "✅" if success else "❌"
        return f"{indicator} {status}"

    @staticmethod
    def format_timestamp(timestamp: str, include_relative: bool = True) -> str:
        """Format a timestamp with optional relative time."""
        # For now, just format the timestamp
        # In production, would calculate relative time
        if include_relative:
            return f"{timestamp} (UTC)"
        return timestamp

    @staticmethod
    def format_diff(old_value: str, new_value: str) -> str:
        """Format a diff between old and new values."""
        return f"~~{old_value}~~ → {new_value}"

    @staticmethod
    def format_resource_list(
        resources: List[Union[str, Dict[str, Any]]],
        show_status: bool = True,
    ) -> str:
        """Format a list of resources with optional status."""
        items = []

        for resource in resources:
            if isinstance(resource, dict):
                name = resource.get("name", "Unknown")
                status = resource.get("status", "")
                resource_type = resource.get("type", "")

                item = name
                if resource_type:
                    item = f"{resource_type}: {name}"
                if show_status and status:
                    if status.lower() in ["healthy", "ok", "running", "active"]:
                        item += " ✅"
                    elif status.lower() in ["error", "failed", "down"]:
                        item += " ❌"
                    elif status.lower() in ["warning", "degraded"]:
                        item += " ⚠️"
                    else:
                        item += f" ({status})"
                items.append(item)
            else:
                items.append(str(resource))

        return MarkdownFormatter.bullet_list(items)

    @staticmethod
    def to_slack_format(markdown_text: str) -> str:
        """Convert Markdown to Slack-compatible format."""
        # Convert **bold** to *bold*
        text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", markdown_text)

        # Convert *italic* to _italic_
        text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"_\1_", text)

        # Convert ```code blocks``` to Slack format
        text = re.sub(r"```(\w+)?\n(.*?)\n```", r"```\2```", text, flags=re.DOTALL)

        # Convert [links](url) to <url|text>
        text = re.sub(r"\[(.+?)\]\((.+?)\)", r"<\2|\1>", text)

        # Remove unsupported elements like tables
        # Slack doesn't support Markdown tables, so convert to simple text
        lines = text.split("\n")
        in_table = False
        new_lines = []

        for line in lines:
            if line.startswith("|") and line.endswith("|"):
                if not in_table and "---" in line:
                    in_table = True
                    continue
                elif in_table:
                    # Extract table content
                    cells = [cell.strip() for cell in line.split("|")[1:-1]]
                    new_lines.append(" | ".join(cells))
                else:
                    new_lines.append(line)
            else:
                in_table = False
                new_lines.append(line)

        return "\n".join(new_lines)

    @staticmethod
    def to_plain_text(markdown_text: str) -> str:
        """Convert Markdown to plain text."""
        # Remove bold
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", markdown_text)

        # Remove italic
        text = re.sub(r"\*(.+?)\*", r"\1", text)

        # Remove code formatting
        text = re.sub(r"`(.+?)`", r"\1", text)

        # Remove code blocks
        text = re.sub(r"```\w*\n(.*?)\n```", r"\1", text, flags=re.DOTALL)

        # Convert links to text (URL)
        text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)

        # Remove heading markers
        text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

        # Remove blockquote markers
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

        # Remove horizontal rules
        text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)

        # Clean up multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

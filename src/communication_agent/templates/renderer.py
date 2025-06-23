"""
Template renderer for the Communication Agent.

Renders message templates with context data and formatting.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from src.communication_agent.templates.loader import TemplateLoader
from src.communication_agent.types import MessageType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TemplateRenderer:
    """Renders message templates with context data."""

    def __init__(self, template_loader: Optional[TemplateLoader] = None):
        """
        Initialize template renderer.

        Args:
            template_loader: Template loader instance
        """
        self.loader = template_loader or TemplateLoader()

    def render(
        self,
        message_type: MessageType,
        context: Dict[str, Any],
        format_type: str = "full",
    ) -> Dict[str, str]:
        """
        Render a message template with context.

        Args:
            message_type: Type of message to render
            context: Context data for template
            format_type: "full", "short", or "both"

        Returns:
            Dictionary with rendered content
        """
        template = self.loader.get_template(message_type)

        if not template:
            logger.warning("No template found for message type: %s", message_type)
            return {}

        # Prepare context with default values
        prepared_context = self._prepare_context(context)

        result = {}

        # Render subject
        if "subject" in template:
            result["subject"] = self._render_string(
                template["subject"],
                prepared_context,
            )

        # Render body or short format
        if format_type in ["full", "both"] and "body" in template:
            result["body"] = self._render_string(
                template["body"],
                prepared_context,
            )

        if format_type in ["short", "both"] and "short" in template:
            result["short"] = self._render_string(
                template["short"],
                prepared_context,
            )

        return result

    def _prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context with default values and formatting."""
        prepared = context.copy()

        # Add timestamp if not present
        if "timestamp" not in prepared:
            prepared["timestamp"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )

        # Format lists
        for key, value in context.items():
            if isinstance(value, list) and key.endswith("_list"):
                # Convert list to formatted string
                if value:
                    prepared[key] = self._format_list(value)
                else:
                    prepared[key] = "None"
            elif isinstance(value, list):
                # Add count variable
                prepared[f"{key}_count"] = len(value)

        # Add default values for common fields
        defaults = {
            "dashboard_link": "[Dashboard URL not configured]",
            "analysis_link": "[Analysis URL not configured]",
            "report_link": "[Report URL not configured]",
            "remediation_link": "[Remediation URL not configured]",
            "emergency_link": "[Emergency URL not configured]",
            "war_room_link": "[War Room URL not configured]",
            "health_dashboard_link": "[Health Dashboard URL not configured]",
        }

        for key, default_value in defaults.items():
            if key not in prepared:
                prepared[key] = default_value

        return prepared

    def _render_string(self, template: str, context: Dict[str, Any]) -> str:
        """Render a template string with context."""
        try:
            # Use format-style templating with error handling
            # First, find all placeholder names in the template
            placeholders = re.findall(r"\{(\w+)\}", template)

            # Create a context with default values for missing keys
            safe_context = {}
            for placeholder in placeholders:
                if placeholder in context:
                    safe_context[placeholder] = context[placeholder]
                else:
                    safe_context[placeholder] = f"[{placeholder}]"
                    logger.warning(
                        "Missing template variable: %s",
                        placeholder,
                        extra={"template_snippet": template[:100]},
                    )

            return template.format(**safe_context)

        except (ValueError, KeyError, AttributeError) as e:
            logger.error(
                "Error rendering template: %s",
                e,
                extra={"template_snippet": template[:100]},
                exc_info=True,
            )
            return template

    def _format_list(
        self,
        items: List[Union[str, Dict[str, Any]]],
        indent: str = "- ",
    ) -> str:
        """Format a list for display in templates."""
        if not items:
            return "None"

        formatted_items = []
        for item in items:
            if isinstance(item, dict):
                # Format dictionary items
                if "name" in item and "status" in item:
                    formatted_items.append(
                        f"{indent}**{item['name']}**: {item['status']}"
                    )
                elif "id" in item and "type" in item:
                    formatted_items.append(f"{indent}{item['type']} ({item['id']})")
                else:
                    # Generic dictionary formatting
                    parts = []
                    for k, v in item.items():
                        parts.append(f"{k}: {v}")
                    formatted_items.append(f"{indent}{', '.join(parts)}")
            else:
                # Simple string items
                formatted_items.append(f"{indent}{item}")

        return "\n".join(formatted_items)

    def render_for_channel(
        self,
        message_type: MessageType,
        context: Dict[str, Any],
        channel: str,
    ) -> Dict[str, str]:
        """
        Render template optimized for specific channel.

        Args:
            message_type: Type of message
            context: Template context
            channel: Communication channel (email, sms, slack, webhook)

        Returns:
            Rendered content optimized for channel
        """
        # SMS needs short format
        if channel == "sms":
            return self.render(message_type, context, format_type="short")

        # Slack can use markdown but needs some adjustments
        elif channel == "slack":
            rendered = self.render(message_type, context, format_type="full")
            if "body" in rendered:
                # Convert markdown bold to Slack format
                rendered["body"] = rendered["body"].replace("**", "*")
                # Remove unnecessary line breaks for Slack
                rendered["body"] = re.sub(r"\n{3,}", "\n\n", rendered["body"])
            return rendered

        # Email and webhook use full format
        else:
            return self.render(message_type, context, format_type="full")

    def get_required_variables(self, message_type: MessageType) -> List[str]:
        """
        Get list of required template variables for a message type.

        Args:
            message_type: Type of message

        Returns:
            List of variable names used in the template
        """
        template = self.loader.get_template(message_type)
        variables = set()

        if not template:
            return []

        # Extract variables from all template parts
        for key in ["subject", "body", "short"]:
            if key in template:
                placeholders = re.findall(r"\{(\w+)\}", template[key])
                variables.update(placeholders)

        return sorted(list(variables))

    def validate_context(
        self,
        message_type: MessageType,
        context: Dict[str, Any],
    ) -> List[str]:
        """
        Validate that context has required variables.

        Args:
            message_type: Type of message
            context: Context to validate

        Returns:
            List of missing required variables
        """
        required = self.get_required_variables(message_type)
        missing = []

        for var in required:
            if var not in context and not self._has_default(var):
                missing.append(var)

        return missing

    def _has_default(self, variable: str) -> bool:
        """Check if a variable has a default value."""
        # These variables have defaults in _prepare_context
        defaults_with_values = [
            "timestamp",
            "dashboard_link",
            "analysis_link",
            "report_link",
            "remediation_link",
            "emergency_link",
            "war_room_link",
            "health_dashboard_link",
        ]

        # Variables ending with _count are auto-generated
        if variable.endswith("_count"):
            return True

        return variable in defaults_with_values

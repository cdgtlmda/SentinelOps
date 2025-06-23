"""
Template loader for the Communication Agent.

Loads and manages message templates from files or embedded strings.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.communication_agent.types import MessageType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TemplateLoader:
    """Loads and manages message templates."""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template loader.

        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = template_dir or Path(__file__).parent
        self.templates: Dict[MessageType, Dict[str, Any]] = {}
        self._load_embedded_templates()
        self._load_file_templates()

    def _load_embedded_templates(self) -> None:
        """Load embedded default templates."""
        # Templates are now loaded from JSON files

    def _load_file_templates(self) -> None:
        """Load templates from JSON files."""
        messages_dir = self.template_dir / "messages"
        if not messages_dir.exists():
            logger.warning("Messages directory not found: %s", messages_dir)
            return

        # Map file names to MessageType enum values
        file_to_message_type = {
            "incident_detected": MessageType.INCIDENT_DETECTED,
            "analysis_complete": MessageType.ANALYSIS_COMPLETE,
            "remediation_started": MessageType.REMEDIATION_STARTED,
            "remediation_complete": MessageType.REMEDIATION_COMPLETE,
            "incident_escalation": MessageType.INCIDENT_ESCALATION,
            "status_update": MessageType.STATUS_UPDATE,
            "daily_summary": MessageType.DAILY_SUMMARY,
            "weekly_report": MessageType.WEEKLY_REPORT,
            "critical_alert": MessageType.CRITICAL_ALERT,
            "system_health": MessageType.SYSTEM_HEALTH,
        }

        # Load JSON template files
        template_files = messages_dir.glob("*.json")
        loaded_count = 0

        for template_file in template_files:
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    template_data = json.load(f)

                # Load templates for each message type in the file
                for template_key, template_content in template_data.items():
                    if template_key in file_to_message_type:
                        message_type = file_to_message_type[template_key]
                        self.templates[message_type] = template_content
                        loaded_count += 1
                        logger.debug(
                            "Loaded template: %s from %s",
                            message_type.value,
                            template_file.name,
                        )

            except (IOError, json.JSONDecodeError, ValueError) as e:
                logger.error(
                    "Failed to load template file: %s",
                    template_file,
                    extra={"error": str(e)},
                    exc_info=True,
                )

        logger.info(
            "Loaded %d templates from %d files",
            loaded_count,
            len(list(template_files)),
            extra={"template_dir": str(messages_dir)},
        )

    def get_template(self, message_type: MessageType) -> Optional[Dict[str, Any]]:
        """
        Get a template by message type.

        Args:
            message_type: The message type

        Returns:
            Template dictionary or None if not found
        """
        return self.templates.get(message_type)

    def list_templates(self) -> List[str]:
        """Get list of available template names."""
        return [mt.value for mt in self.templates]

    def reload_templates(self) -> None:
        """Reload all templates from disk."""
        self.templates.clear()
        self._load_embedded_templates()
        self._load_file_templates()
        logger.info("Templates reloaded")

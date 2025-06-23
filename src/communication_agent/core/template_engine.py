"""
Template engine for communication agent
"""

from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader


class TemplateEngine:
    """Handles message template rendering"""

    def __init__(self, template_dir: Optional[str] = None):
        """Initialize template engine"""
        self.template_dir = template_dir
        if template_dir:
            self.env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=True
            )
        else:
            self.env = Environment(autoescape=True)

        # Add custom filters
        self.env.filters['format_severity'] = self._format_severity
        self.env.filters['format_time'] = self._format_time

    def render(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render a template string with context"""
        template = self.env.from_string(template_str)
        return template.render(**context)

    def render_file(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template file with context"""
        template = self.env.get_template(template_name)
        return template.render(**context)

    @staticmethod
    def _format_severity(severity: str) -> str:
        """Format severity for display"""
        severity_map = {
            'critical': '🔴 CRITICAL',
            'high': '🟠 HIGH',
            'medium': '🟡 MEDIUM',
            'low': '🟢 LOW',
            'info': 'ℹ️ INFO'
        }
        return severity_map.get(severity.lower(), severity.upper())

    @staticmethod
    def _format_time(timestamp: str) -> str:
        """Format timestamp for display"""
        # Simple formatting, can be enhanced
        return timestamp.replace('T', ' ').split('.')[0]

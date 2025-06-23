"""
Structured output handling for Gemini responses
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class StructuredOutput:
    """Base class for structured output formats"""

    raw_response: str
    parsed_data: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Parse the response after initialization"""
        if self.raw_response and not self.parsed_data:
            self.parse()

    def parse(self) -> None:
        """Parse the raw response into structured data"""
        self.validation_errors = []

        # Try to extract JSON from the response
        try:
            # Look for JSON blocks in markdown
            json_pattern = r"```json\s*(.*?)\s*```"
            matches = re.findall(json_pattern, self.raw_response, re.DOTALL)

            if matches:
                # Use the first JSON block found
                json_str = matches[0]
                self.parsed_data = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                self.parsed_data = json.loads(self.raw_response)

        except json.JSONDecodeError as e:
            self.validation_errors.append(f"JSON parsing error: {e}")
            # Try to extract any structured data we can
            self._fallback_parse()

    def _fallback_parse(self) -> None:
        """Fallback parsing for non-JSON responses"""
        # This is a basic implementation - subclasses can override
        self.parsed_data = {"raw_text": self.raw_response, "parsing_failed": True}

    def is_valid(self) -> bool:
        """Check if the output was successfully parsed"""
        return self.parsed_data is not None and not self.validation_errors

    def get(self, path: str, default: Any = None) -> Any:
        """Get a value from parsed data using dot notation"""
        if not self.parsed_data:
            return default

        keys = path.split(".")
        value = self.parsed_data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value


class SecurityAnalysisOutput(StructuredOutput):
    """Structured output for security analysis"""

    def get_severity(self) -> str:
        """Get the highest severity level from the analysis"""
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        # Check threats
        threats = self.get("threats_detected", [])
        for threat in threats:
            severity = threat.get("severity")
            if severity in severities:
                return str(severity)

        # Check overall assessment
        overall = self.get("threat_assessment.threat_level")
        if overall in severities:
            return str(overall)

        return "LOW"

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get prioritized recommendations"""
        recs = self.get("recommendations", [])
        # Sort by priority
        priority_order = {"IMMEDIATE": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        return sorted(
            recs, key=lambda r: priority_order.get(r.get("priority", "LOW"), 3)
        )

    def get_iocs(self) -> List[Dict[str, str]]:
        """Extract all Indicators of Compromise"""
        iocs = self.get("iocs", [])
        if isinstance(iocs, list):
            return iocs
        return []

"""
Gemini project configuration management
"""

import os
from typing import Any, Dict, Optional


class GeminiProjectConfig:
    """Manages Gemini project configuration"""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        default_model: str = "gemini-pro",
        safety_settings: Optional[Dict[str, Any]] = None,
    ):
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.default_model = default_model
        self.safety_settings = safety_settings or {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
        }

    def get_generation_config(self, **kwargs: Any) -> Dict[str, Any]:
        """Get generation configuration with defaults"""
        defaults = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        defaults.update(kwargs)
        return defaults

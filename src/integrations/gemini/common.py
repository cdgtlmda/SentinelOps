"""
Common imports and utilities for Gemini AI Integration
"""

import logging

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Configure logging
logger = logging.getLogger(__name__)

# Export the commonly used items
__all__ = ["logger", "genai", "google_exceptions"]

"""
Gemini Threat Analyst Integration
Advanced threat analysis using Google's Gemini AI for security intelligence
"""

import logging

import google.generativeai as genai


class GeminiThreatAnalyst:
    """AI-powered threat analysis using Gemini models"""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    # ... existing code ...

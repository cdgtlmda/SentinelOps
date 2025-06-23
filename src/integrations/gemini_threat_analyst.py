"""
Gemini Threat Analyst Integration
Advanced threat analysis using Google's Gemini AI for security intelligence
"""

import json
import logging
import asyncio
from typing import Any, Dict, List

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions


class GeminiThreatAnalyst:
    """AI-powered threat analysis using Gemini models"""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def analyze_incident_context(
        self, incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze incident with AI-powered context understanding
        """

        analysis_prompt = f"""
        You are a cybersecurity expert analyzing a security incident.
        Provide detailed threat analysis of the following incident data:

        {json.dumps(incident_data, indent=2)}

        Please provide analysis in JSON format with these sections:
        1. threat_assessment: Overall threat level and confidence
        2. attack_patterns: Identified attack techniques/patterns
        3. indicators: Key indicators of compromise
        4. recommendations: Specific remediation steps
        5. attribution: Potential threat actor or campaign if identifiable
        6. timeline: Reconstructed attack timeline if possible
        """

        try:
            response = await self._generate_content_async(analysis_prompt)

            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                analysis_json = json.loads(response[json_start:json_end])
                return {
                    "success": True,
                    "analysis": analysis_json,
                    "raw_response": response,
                    "model_used": self.model_name,
                    "timestamp": None,
                }
            else:
                return {
                    "success": False,
                    "error": "No valid JSON found in response",
                    "raw_response": response,
                }

        except (json.JSONDecodeError, ValueError, AttributeError, TypeError) as e:
            self.logger.error("Error in incident analysis: %s", e)
            return {"success": False, "error": str(e)}

    async def enrich_with_threat_intelligence(
        self, indicators: List[str]
    ) -> Dict[str, Any]:
        """
        Use AI to enrich indicators with threat intelligence context
        """

        enrichment_prompt = f"""
        As a threat intelligence analyst, provide enrichment for these indicators:

        Indicators: {indicators}

        For each indicator, provide:
        1. threat_type: What type of threat this represents
        2. severity: Risk level (LOW/MEDIUM/HIGH/CRITICAL)
        3. confidence: How confident you are (0.0-1.0)
        4. context: Background information and known associations
        5. ttps: Related tactics, techniques, and procedures
        6. mitigation: Recommended defensive actions

        Return as JSON array with one object per indicator.
        """

        try:
            response = await self._generate_content_async(enrichment_prompt)

            json_start = response.find("[")
            json_end = response.rfind("]") + 1

            if json_start >= 0 and json_end > json_start:
                enrichment_data = json.loads(response[json_start:json_end])
                return {
                    "success": True,
                    "enrichment": enrichment_data,
                    "indicators_processed": len(indicators),
                    "model_used": self.model_name,
                }
            else:
                return {
                    "success": False,
                    "error": "No valid JSON array found in response",
                    "raw_response": response,
                }

        except (json.JSONDecodeError, ValueError, AttributeError, TypeError) as e:
            self.logger.error("Error in threat enrichment: %s", e)
            return {"success": False, "error": str(e)}

    async def analyze_attack_patterns(
        self, events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use AI to identify attack patterns across multiple security events
        """

        pattern_prompt = f"""
        Analyze these security events to identify potential attack patterns:

        Events:
        {json.dumps(events, indent=2, default=str)}

        Look for:
        1. Kill chain progression
        2. Lateral movement patterns
        3. Data exfiltration indicators
        4. Persistence mechanisms
        5. Privilege escalation attempts

        Provide analysis as JSON with:
        - attack_chain: Reconstructed attack sequence
        - confidence: Overall confidence in the analysis (0.0 - 1.0)
        - pattern_type: Primary attack pattern identified
        - threat_level: Overall threat assessment
        - next_likely_steps: Predicted adversary next moves
        """

        try:
            response = await self._generate_content_async(pattern_prompt)

            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                pattern_analysis = json.loads(response[json_start:json_end])
                return {
                    "success": True,
                    "pattern_analysis": pattern_analysis,
                    "events_analyzed": len(events),
                    "model_used": self.model_name,
                }
            else:
                return {
                    "success": False,
                    "error": "No valid JSON found in response",
                    "raw_response": response,
                }

        except (json.JSONDecodeError, ValueError, AttributeError, TypeError) as e:
            self.logger.error("Error in pattern analysis: %s", e)
            return {"success": False, "error": str(e)}

    async def _generate_content_async(self, prompt: str) -> str:
        """
        Generate content asynchronously with error handling
        """
        try:
            response = self.model.generate_content(prompt)
            return str(response.text)
        except google_exceptions.ResourceExhausted:
            self.logger.warning("Gemini API quota exceeded, retrying...")
            # Simple retry with delay
            await asyncio.sleep(60)
            response = self.model.generate_content(prompt)
            return str(response.text)
        except (google_exceptions.GoogleAPIError, ValueError, TypeError, AttributeError) as e:
            self.logger.error("Error generating content: %s", e)
            raise


def create_threat_analyst(api_key: str, model_name: str = "gemini-1.5-pro") -> GeminiThreatAnalyst:
    """Factory function to create a GeminiThreatAnalyst instance"""
    return GeminiThreatAnalyst(api_key=api_key, model_name=model_name)

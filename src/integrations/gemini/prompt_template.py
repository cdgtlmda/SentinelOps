"""
Prompt template management for Gemini AI
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PromptTemplate:
    """Template for structured prompts"""

    name: str
    template: str
    variables: List[str]
    output_format: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None

    def format(self, **kwargs: Any) -> str:
        """Format the template with provided variables"""
        # Check all required variables are provided
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        prompt = self.template.format(**kwargs)

        # Add output format instructions if specified
        if self.output_format:
            prompt += f"\n\nProvide your response in the following format:\n{self.output_format}"

        # Add examples if provided
        if self.examples:
            prompt += "\n\nExamples:"
            for i, example in enumerate(self.examples, 1):
                prompt += f"\n\nExample {i}:"
                for key, value in example.items():
                    prompt += f"\n{key}: {value}"

        return prompt


# Security Analysis Prompt Templates - Part 1
SECURITY_PROMPTS_PART1 = {
    "log_analysis": PromptTemplate(
        name="log_analysis",
        template="""Analyze the following log entries for security threats and anomalies:

Log Entries:
{log_entries}

Time Range: {time_range}
Source System: {source_system}

Perform a comprehensive security analysis including:
1. Identify any suspicious patterns or anomalies
2. Detect potential security threats or attacks
3. Assess the severity of any findings
4. Identify affected resources or systems
5. Recommend immediate actions if needed

Focus on accuracy and provide evidence for each finding.""",
        variables=["log_entries", "time_range", "source_system"],
        output_format="""```json
{
  "summary": "Brief overview of findings",
  "threats_detected": [
    {
      "threat_type": "Type of threat",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "confidence": 0.0-1.0,
      "evidence": ["List of supporting evidence"],
      "affected_resources": ["List of affected resources"],
      "first_seen": "timestamp",
      "last_seen": "timestamp"
    }
  ],
  "anomalies": [
    {
      "type": "Type of anomaly",
      "description": "Detailed description",
      "severity": "HIGH|MEDIUM|LOW",
      "evidence": ["Supporting log entries"]
    }
  ],
  "recommendations": [
    {
      "action": "Recommended action",
      "priority": "IMMEDIATE|HIGH|MEDIUM|LOW",
      "rationale": "Why this action is needed"
    }
  ]
}
```""",
    ),
    "threat_detection": PromptTemplate(
        name="threat_detection",
        template="""Analyze the following indicators for potential security threats:

Indicators:
{indicators}

Context:
- Environment: {environment}
- Baseline Activity: {baseline}
- Recent Incidents: {recent_incidents}

Identify:
1. Known attack patterns or signatures
2. Indicators of Compromise (IoCs)
3. Tactics, Techniques, and Procedures (TTPs)
4. Potential threat actors
5. Attack stage and progression""",
        variables=["indicators", "environment", "baseline", "recent_incidents"],
        output_format="""```json
{
  "threat_assessment": {
    "threat_level": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
    "confidence": 0.0-1.0,
    "threat_category": "Category of threat"
  },
  "detected_patterns": [
    {
      "pattern_name": "Name of attack pattern",
      "mitre_attack_id": "MITRE ATT&CK ID if applicable",
      "confidence": 0.0-1.0,
      "indicators": ["List of matching indicators"]
    }
  ],
  "iocs": [
    {
      "type": "IP|DOMAIN|HASH|URL|EMAIL|OTHER",
      "value": "The IoC value",
      "context": "Where/how it was observed"
    }
  ],
  "ttps": [
    {
      "tactic": "MITRE ATT&CK tactic",
      "technique": "Specific technique",
      "evidence": ["Supporting evidence"]
    }
  ],
  "attribution": {
    "threat_actor": "Suspected threat actor or group",
    "confidence": 0.0-1.0,
    "supporting_evidence": ["Evidence for attribution"]
  }
}
```""",
    ),
}

# Security Analysis Prompt Templates - Part 2
SECURITY_PROMPTS_PART2 = {
    "risk_assessment": PromptTemplate(
        name="risk_assessment",
        template="""Perform a risk assessment based on the following security findings:

Findings:
{findings}

Asset Information:
- Critical Assets: {critical_assets}
- Business Context: {business_context}
- Current Controls: {current_controls}

Assess:
1. Likelihood of exploitation
2. Potential business impact
3. Risk score calculation
4. Existing control effectiveness
5. Residual risk level""",
        variables=[
            "findings",
            "critical_assets",
            "business_context",
            "current_controls",
        ],
        output_format="""```json
{
  "risk_summary": {
    "overall_risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
    "risk_score": 0-100,
    "trend": "INCREASING|STABLE|DECREASING"
  },
  "risk_factors": [
    {
      "factor": "Description of risk factor",
      "likelihood": "VERY_HIGH|HIGH|MEDIUM|LOW|VERY_LOW",
      "impact": "CATASTROPHIC|MAJOR|MODERATE|MINOR|NEGLIGIBLE",
      "risk_score": 0-100,
      "affected_assets": ["List of affected assets"]
    }
  ],
  "control_assessment": [
    {
      "control": "Control name",
      "effectiveness": "EFFECTIVE|PARTIALLY_EFFECTIVE|INEFFECTIVE",
      "gaps": ["Identified gaps"],
      "recommendations": ["Improvement recommendations"]
    }
  ],  "residual_risks": [
    {
      "risk": "Description of residual risk",
      "level": "HIGH|MEDIUM|LOW",
      "mitigation_options": ["Possible mitigations"]
    }
  ]
}
```""",
    ),
    "pattern_recognition": PromptTemplate(
        name="pattern_recognition",
        template="""Analyze the following data for security-relevant patterns:

Data:
{data}

Historical Context:
{historical_context}

Pattern Types to Identify:
1. Temporal patterns (time-based attacks)
2. Behavioral patterns (user/system behavior)
3. Network patterns (traffic anomalies)
4. Access patterns (authentication/authorization)
5. Data patterns (exfiltration indicators)

Look for both known attack patterns and novel/emerging patterns.""",
        variables=["data", "historical_context"],
        output_format="""```json
{
  "identified_patterns": [
    {
      "pattern_type": "TEMPORAL|BEHAVIORAL|NETWORK|ACCESS|DATA|OTHER",
      "description": "Detailed pattern description",
      "confidence": 0.0-1.0,
      "frequency": "Number of occurrences",
      "time_window": "Time period of pattern",
      "entities_involved": ["List of users/systems/IPs"],
      "anomaly_score": 0.0-1.0
    }
  ],
  "correlations": [
    {
      "pattern_1": "First pattern ID/name",
      "pattern_2": "Second pattern ID/name",
      "correlation_strength": 0.0-1.0,
      "relationship": "Description of relationship"
    }
  ],  "predictions": [
    {
      "prediction": "What might happen next",
      "confidence": 0.0-1.0,
      "time_frame": "Expected time frame",
      "indicators_to_watch": ["What to monitor"]
    }
  ]
}
```""",
    ),
}

# Merge all security prompts
SECURITY_PROMPTS = {**SECURITY_PROMPTS_PART1, **SECURITY_PROMPTS_PART2}


class PromptLibrary:
    """Manages prompt templates and their usage"""

    def __init__(self) -> None:
        self.templates = SECURITY_PROMPTS.copy()
        self.custom_templates: Dict[str, PromptTemplate] = {}

    def add_template(self, template: PromptTemplate) -> None:
        """Add a custom prompt template"""
        self.custom_templates[template.name] = template

    def get_template(self, name: str) -> PromptTemplate:
        """Get a prompt template by name"""
        if name in self.custom_templates:
            return self.custom_templates[name]
        if name in self.templates:
            return self.templates[name]
        raise ValueError(f"Unknown template: {name}")

    def format_prompt(self, template_name: str, **kwargs: Any) -> str:
        """Format a prompt template with variables"""
        template = self.get_template(template_name)
        return template.format(**kwargs)

    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys()) + list(self.custom_templates.keys())

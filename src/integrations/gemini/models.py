"""
Gemini model definitions and characteristics
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class GeminiModel(Enum):
    """Available Gemini models with their characteristics"""

    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_PRO_LATEST = "gemini-1.5-pro-latest"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_LATEST = "gemini-1.5-flash-latest"
    GEMINI_2_FLASH = "gemini-2.0-flash"


@dataclass
class ModelCharacteristics:
    """Characteristics of a Gemini model"""

    name: str
    context_window: int
    max_output_tokens: int
    supports_vision: bool
    supports_function_calling: bool
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    recommended_use_cases: List[str]


# Model characteristics database
MODEL_CHARACTERISTICS = {
    GeminiModel.GEMINI_PRO: ModelCharacteristics(
        name="gemini-pro",
        context_window=32768,
        max_output_tokens=8192,
        supports_vision=False,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
        recommended_use_cases=["text analysis", "general reasoning", "code generation"],
    ),
    GeminiModel.GEMINI_PRO_VISION: ModelCharacteristics(
        name="gemini-pro-vision",
        context_window=16384,
        max_output_tokens=4096,
        supports_vision=True,
        supports_function_calling=False,
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
        recommended_use_cases=["image analysis", "visual understanding"],
    ),
    GeminiModel.GEMINI_1_5_PRO: ModelCharacteristics(
        name="gemini-1.5-pro",
        context_window=1048576,  # 1M tokens
        max_output_tokens=8192,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.00125,
        cost_per_1k_output_tokens=0.00375,
        recommended_use_cases=[
            "long context analysis",
            "complex reasoning",
            "multimodal tasks",
        ],
    ),
    GeminiModel.GEMINI_1_5_FLASH: ModelCharacteristics(
        name="gemini-1.5-flash",
        context_window=1048576,  # 1M tokens
        max_output_tokens=8192,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.00025,
        cost_per_1k_output_tokens=0.00075,
        recommended_use_cases=[
            "fast inference",
            "high volume processing",
            "cost optimization",
        ],
    ),
    GeminiModel.GEMINI_1_5_PRO_LATEST: ModelCharacteristics(
        name="gemini-1.5-pro-latest",
        context_window=2097152,  # 2M tokens
        max_output_tokens=8192,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.00125,
        cost_per_1k_output_tokens=0.00375,
        recommended_use_cases=[
            "cutting-edge features",
            "latest improvements",
            "experimental capabilities",
        ],
    ),
    GeminiModel.GEMINI_1_5_FLASH_LATEST: ModelCharacteristics(
        name="gemini-1.5-flash-latest",
        context_window=1048576,  # 1M tokens
        max_output_tokens=8192,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.00025,
        cost_per_1k_output_tokens=0.00075,
        recommended_use_cases=[
            "latest flash optimizations",
            "improved speed",
            "experimental fast features",
        ],
    ),
    GeminiModel.GEMINI_2_FLASH: ModelCharacteristics(
        name="gemini-2.0-flash",
        context_window=1048576,  # 1M tokens
        max_output_tokens=8192,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.00015,
        cost_per_1k_output_tokens=0.0006,
        recommended_use_cases=[
            "next-gen performance",
            "enhanced capabilities",
            "best cost-performance ratio",
        ],
    ),
}


@dataclass
class ModelProfile:
    """Configuration profile for specific use cases"""

    name: str
    model: GeminiModel
    temperature: float
    top_p: float
    top_k: int
    max_output_tokens: int
    stop_sequences: Optional[List[str]] = None
    system_instruction: Optional[str] = None

    def to_generation_config(self) -> Dict[str, Any]:
        """Convert profile to generation config"""
        config: Dict[str, Any] = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens,
        }
        if self.stop_sequences:
            config["stop_sequences"] = self.stop_sequences
        return config


# Predefined model profiles for different use cases
MODEL_PROFILES = {
    "security_analysis": ModelProfile(
        name="security_analysis",
        model=GeminiModel.GEMINI_1_5_PRO,
        temperature=0.3,
        top_p=0.95,
        top_k=40,
        max_output_tokens=4096,
        system_instruction=(
            "You are a security analyst AI assistant specializing in log analysis, "
            "threat detection, and incident response. Provide detailed, accurate "
            "analysis with evidence-based reasoning. Always cite specific log entries "
            "or indicators when making assessments."
        ),
    ),
    "incident_summarization": ModelProfile(
        name="incident_summarization",
        model=GeminiModel.GEMINI_1_5_FLASH,
        temperature=0.5,
        top_p=0.90,
        top_k=30,
        max_output_tokens=2048,
        system_instruction="""You are an expert at summarizing security incidents concisely.
        Focus on: 1) What happened, 2) When it happened, 3) Impact assessment, 4) Key indicators,
        5) Recommended actions. Be clear and actionable.""",
    ),
    "recommendation_generation": ModelProfile(
        name="recommendation_generation",
        model=GeminiModel.GEMINI_1_5_PRO,
        temperature=0.4,
        top_p=0.95,
        top_k=40,
        max_output_tokens=3072,
        system_instruction="""You are a security remediation expert. Generate specific, actionable
        recommendations for addressing security issues. Include: 1) Immediate actions, 2) Long-term
        fixes, 3) Prevention measures, 4) Risk mitigation strategies. Prioritize by severity.""",
    ),
    "natural_language_query": ModelProfile(
        name="natural_language_query",
        model=GeminiModel.GEMINI_PRO,
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=2048,
        system_instruction="""You are a helpful security assistant that answers questions about
        security incidents, logs, and system status. Provide clear, accurate responses based on
        the available data. If uncertain, clearly state limitations.""",
    ),
}

"""
Gemini AI Integration Module

This module provides a centralized interface for interacting with Google's Gemini AI API,
including API key management, rate limiting, quota monitoring, and error handling.
"""

from .models import GeminiModel, ModelCharacteristics, ModelProfile, MODEL_PROFILES
from .model_selector import ModelSelector
from .prompt_template import PromptTemplate, PromptLibrary, SECURITY_PROMPTS
from .structured_output import StructuredOutput, SecurityAnalysisOutput
from .rate_limiter import RateLimitConfig, QuotaUsage, RateLimiter
from .api_key_manager import GeminiAPIKeyManager
from .quota_monitor import QuotaMonitor
from .project_config import GeminiProjectConfig
from .connection_pool import ConnectionPool
from .response_cache import ResponseCache
from .token_optimizer import TokenOptimizer
from .cost_tracker import CostTracker
from .integration import GeminiIntegration

# Backward compatibility aliases
VertexAIGeminiClient = GeminiIntegration
VertexAIModel = GeminiModel

__all__ = [
    "GeminiModel",
    "ModelCharacteristics",
    "ModelProfile",
    "MODEL_PROFILES",
    "ModelSelector",
    "PromptTemplate",
    "PromptLibrary",
    "SECURITY_PROMPTS",
    "StructuredOutput",
    "SecurityAnalysisOutput",
    "RateLimitConfig",
    "QuotaUsage",
    "RateLimiter",
    "GeminiAPIKeyManager",
    "QuotaMonitor",
    "GeminiProjectConfig",
    "ConnectionPool",
    "ResponseCache",
    "TokenOptimizer",
    "CostTracker",
    "GeminiIntegration",
    # Backward compatibility aliases
    "VertexAIGeminiClient",
    "VertexAIModel",
]

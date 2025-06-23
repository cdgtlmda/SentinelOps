"""
Model selector for choosing appropriate Gemini models
"""

from typing import List, Optional

from .common import logger
from .models import GeminiModel, MODEL_CHARACTERISTICS


class ModelSelector:
    """Intelligent model selection based on task requirements"""

    def __init__(self, available_models: Optional[List[GeminiModel]] = None):
        self.available_models = available_models or list(MODEL_CHARACTERISTICS.keys())

    def select_model(
        self,
        context_size: int,
        needs_vision: bool = False,
        needs_function_calling: bool = False,
        optimize_for: str = "quality",
    ) -> GeminiModel:
        """
        Select the most appropriate model based on requirements

        Args:
            context_size: Required context window size
            needs_vision: Whether vision capabilities are needed
            needs_function_calling: Whether function calling is needed
            optimize_for: "quality", "speed", or "cost"

        Returns:
            Selected Gemini model
        """
        suitable_models = []

        for model in self.available_models:
            characteristics = MODEL_CHARACTERISTICS.get(model)
            if not characteristics:
                continue

            # Check requirements
            if context_size > characteristics.context_window:
                continue
            if needs_vision and not characteristics.supports_vision:
                continue
            if needs_function_calling and not characteristics.supports_function_calling:
                continue

            suitable_models.append(model)

        if not suitable_models:
            raise ValueError("No suitable model found for the given requirements")

        # Sort based on optimization preference
        if optimize_for == "cost":
            suitable_models.sort(
                key=lambda m: MODEL_CHARACTERISTICS[m].cost_per_1k_input_tokens
            )
        elif optimize_for == "speed":
            # Flash models are optimized for speed
            suitable_models.sort(key=lambda m: 0 if "flash" in m.value.lower() else 1)
        else:  # quality
            # Pro models generally offer better quality
            suitable_models.sort(
                key=lambda m: (
                    0
                    if "pro" in m.value.lower() and "flash" not in m.value.lower()
                    else 1
                )
            )

        selected = suitable_models[0]
        logger.info(
            "Selected model %s for context_size=%s, "
            "vision=%s, function_calling=%s, "
            "optimize_for=%s",
            selected.value, context_size, needs_vision, needs_function_calling,
            optimize_for
        )

        return selected

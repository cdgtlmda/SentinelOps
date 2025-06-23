"""
Tests for Gemini model selector - real implementation, no mocks.
"""

import pytest

from src.integrations.gemini.model_selector import ModelSelector
from src.integrations.gemini.models import GeminiModel, MODEL_CHARACTERISTICS


class TestModelSelector:
    """Test the ModelSelector class with real model data."""

    def test_initialization_default(self) -> None:
        """Test ModelSelector initialization with default models."""
        selector = ModelSelector()
        assert selector.available_models == list(MODEL_CHARACTERISTICS.keys())
        assert len(selector.available_models) > 0

    def test_initialization_custom_models(self) -> None:
        """Test ModelSelector initialization with custom model list."""
        custom_models = [GeminiModel.GEMINI_PRO, GeminiModel.GEMINI_1_5_FLASH]
        selector = ModelSelector(available_models=custom_models)
        assert selector.available_models == custom_models
        assert len(selector.available_models) == 2

    def test_select_model_basic_text(self) -> None:
        """Test selecting a model for basic text processing."""
        selector = ModelSelector()
        model = selector.select_model(
            context_size=10000,
            needs_vision=False,
            needs_function_calling=False,
            optimize_for="quality"
        )
        assert isinstance(model, GeminiModel)
        characteristics = MODEL_CHARACTERISTICS[model]
        assert characteristics.context_window >= 10000
        assert characteristics.supports_function_calling or not False
        assert characteristics.supports_vision or not False

    def test_select_model_with_vision(self) -> None:
        """Test selecting a model that supports vision."""
        selector = ModelSelector()
        model = selector.select_model(
            context_size=5000,
            needs_vision=True,
            needs_function_calling=False,
            optimize_for="quality"
        )

        assert isinstance(model, GeminiModel)
        characteristics = MODEL_CHARACTERISTICS[model]
        assert characteristics.supports_vision is True
        assert characteristics.context_window >= 5000

    def test_select_model_with_function_calling(self) -> None:
        """Test selecting a model that supports function calling."""
        selector = ModelSelector()
        model = selector.select_model(
            context_size=20000,
            needs_vision=False,
            needs_function_calling=True,
            optimize_for="quality"
        )

        assert isinstance(model, GeminiModel)
        characteristics = MODEL_CHARACTERISTICS[model]
        assert characteristics.supports_function_calling is True
        assert characteristics.context_window >= 20000

    def test_select_model_optimize_for_cost(self) -> None:
        """Test selecting the most cost-effective model."""
        selector = ModelSelector()
        model = selector.select_model(
            context_size=5000,
            needs_vision=False,
            needs_function_calling=False,
            optimize_for="cost"
        )

        # Verify it selected a model and check if it's among the cheaper ones
        assert isinstance(model, GeminiModel)

        # Find all suitable models for comparison
        suitable_models = []
        for m in selector.available_models:
            char = MODEL_CHARACTERISTICS[m]
            if char.context_window >= 5000:
                suitable_models.append((m, char.cost_per_1k_input_tokens))

        # Verify our selected model is the cheapest suitable one
        suitable_models.sort(key=lambda x: x[1])
        assert model == suitable_models[0][0]

    def test_select_model_optimize_for_speed(self) -> None:
        """Test selecting the fastest model."""
        selector = ModelSelector()
        model = selector.select_model(
            context_size=10000,
            needs_vision=False,
            needs_function_calling=False,
            optimize_for="speed"
        )
        assert isinstance(model, GeminiModel)
        # Flash models are optimized for speed
        assert ("flash" in model.value.lower() or
                len([m for m in selector.available_models if "flash" in m.value.lower()]) == 0)

    def test_select_model_large_context(self) -> None:
        """Test selecting a model for large context requirements."""
        selector = ModelSelector()
        large_context = 100000

        model = selector.select_model(
            context_size=large_context,
            needs_vision=False,
            needs_function_calling=False,
            optimize_for="quality"
        )

        assert isinstance(model, GeminiModel)
        characteristics = MODEL_CHARACTERISTICS[model]
        assert characteristics.context_window >= large_context

    def test_select_model_no_suitable_model(self) -> None:
        """Test error when no suitable model exists."""
        selector = ModelSelector()

        # Request impossible requirements
        with pytest.raises(ValueError) as exc_info:
            selector.select_model(
                context_size=10000000,  # 10M tokens - no model supports this
                needs_vision=False,
                needs_function_calling=False,
                optimize_for="quality"
            )

        assert "No suitable model found" in str(exc_info.value)

    def test_select_model_with_limited_models(self) -> None:
        """Test model selection with limited available models."""
        limited_models = [GeminiModel.GEMINI_PRO, GeminiModel.GEMINI_1_5_FLASH]
        selector = ModelSelector(available_models=limited_models)

        model = selector.select_model(
            context_size=10000,
            needs_vision=False,
            needs_function_calling=True,
            optimize_for="quality"
        )

        assert model in limited_models
        characteristics = MODEL_CHARACTERISTICS[model]
        assert characteristics.supports_function_calling is True

    def test_select_model_all_requirements(self) -> None:
        """Test model selection with vision and function calling requirements."""
        selector = ModelSelector()

        model = selector.select_model(
            context_size=15000,
            needs_vision=True,
            needs_function_calling=True,
            optimize_for="quality"
        )

        assert isinstance(model, GeminiModel)
        characteristics = MODEL_CHARACTERISTICS[model]
        assert characteristics.supports_vision is True
        assert characteristics.supports_function_calling is True
        assert characteristics.context_window >= 15000

    def test_all_models_have_characteristics(self) -> None:
        """Test that all models in the enum have characteristics defined."""
        missing_models = []
        for model in GeminiModel:
            if model not in MODEL_CHARACTERISTICS:
                missing_models.append(model.value)

        assert len(missing_models) == 0, f"Missing characteristics for models: {missing_models}"

        # Also verify each characteristic is properly defined
        for model, char in MODEL_CHARACTERISTICS.items():
            assert isinstance(model, GeminiModel)
            assert char.name == model.value
            assert char.context_window > 0
            assert char.max_output_tokens > 0
            assert isinstance(char.supports_vision, bool)
            assert isinstance(char.supports_function_calling, bool)
            assert char.cost_per_1k_input_tokens >= 0
            assert char.cost_per_1k_output_tokens >= 0
            assert len(char.recommended_use_cases) > 0

    def test_select_model_with_new_models(self) -> None:
        """Test model selection includes new models like Gemini 2.0 Flash."""
        selector = ModelSelector()

        # Test that Gemini 2.0 Flash can be selected for cost optimization
        model = selector.select_model(
            context_size=50000,
            needs_vision=True,
            needs_function_calling=True,
            optimize_for="cost"
        )

        # Should select one of the cheaper models with all capabilities
        assert isinstance(model, GeminiModel)
        characteristics = MODEL_CHARACTERISTICS[model]
        assert characteristics.supports_vision is True
        assert characteristics.supports_function_calling is True
        assert characteristics.context_window >= 50000

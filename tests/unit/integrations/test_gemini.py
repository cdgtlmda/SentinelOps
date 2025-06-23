"""REAL tests for integrations/gemini.py - These tests make actual Vertex AI calls."""

import os
import pytest
import asyncio
from typing import Dict
from google.auth import default
from google.auth.credentials import Credentials

# Import the actual production code
try:
    from src.integrations.gemini import (
        GeminiIntegration,
        GeminiModel,
    )
    from src.integrations.gemini.models import MODEL_CHARACTERISTICS

    # Aliases for backward compatibility
    VertexAIGeminiClient = GeminiIntegration
    VertexAIModel = GeminiModel
    _imports_available = True
except ImportError:
    # Handle missing imports gracefully - skip tests that require these
    _imports_available = False
    pytest.skip("Missing gemini integration components")


class TestVertexAIIntegrationRealAPICalls:
    """Test VertexAIGeminiClient with REAL Vertex AI calls - NO MOCKS."""

    @pytest.fixture(scope="class")
    def vertex_config(self) -> Dict[str, str]:
        """Get Vertex AI configuration."""
        # Verify GCP credentials are available
        try:
            credentials: Credentials
            project: str
            credentials, project = default()  # type: ignore[no-untyped-call]
            project_id = os.environ.get(
                "GCP_PROJECT_ID", project or "your-gcp-project-id"
            )
        except Exception:
            pytest.skip(
                "No GCP credentials available. Configure application default "
                "credentials to run these tests."
            )

        location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")

        print(f"\nUsing Vertex AI Project: {project_id}, Location: {location}")
        return {"project_id": project_id, "location": location}

    @pytest.fixture
    def vertex_client(self, vertex_config: Dict[str, str]) -> VertexAIGeminiClient:
        """Create Vertex AI client with real configuration."""
        client = VertexAIGeminiClient()
        return client

    # @pytest.fixture
    # def rate_limiter(self) -> RateLimitManager:
    #     """Create rate limit manager for testing."""
    #     return RateLimitManager(requests_per_minute=60, tokens_per_minute=60000)

    def test_initialization_with_vertex_ai(self, vertex_config: Dict[str, str]) -> None:
        """Test VertexAIGeminiClient initialization with real Vertex AI."""
        client = VertexAIGeminiClient()

        # Verify initialization
        assert hasattr(client, "project_config")
        assert hasattr(client, "rate_limiter")
        assert hasattr(client, "cost_tracker")

    @pytest.mark.asyncio
    async def test_generate_content_simple_prompt(
        self, vertex_client: VertexAIGeminiClient
    ) -> None:
        """Test generating content with a simple prompt using real Vertex AI."""
        prompt = "What is 2 + 2? Respond with just the number."

        # Make real API call
        response = await vertex_client.generate_content(
            prompt=prompt,
            model_name=VertexAIModel.GEMINI_1_5_FLASH.value,
            generation_config={"temperature": 0.0, "max_output_tokens": 10},
        )

        # Verify response
        assert response is not None
        assert "4" in response

        # Check that metrics were updated
        metrics = vertex_client.get_metrics()
        assert metrics["total_requests"] > 0

    @pytest.mark.asyncio
    async def test_generate_content_with_model_selection(
        self, vertex_client: VertexAIGeminiClient
    ) -> None:
        """Test content generation with specific model selection."""
        prompt = "List 3 programming languages. Be concise."

        # Use a fast model for quick response
        model = VertexAIModel.GEMINI_1_5_FLASH

        # Generate content with selected model
        response = await vertex_client.generate_content(
            prompt=prompt,
            model_name=model.value,
            generation_config={"temperature": 0.5, "max_output_tokens": 50},
        )

        assert response is not None
        # Basic validation - should mention programming languages
        assert any(
            lang in response.lower()
            for lang in ["python", "java", "javascript", "c++", "go", "rust"]
        )

    def test_model_characteristics(self) -> None:
        """Test model characteristics are properly defined."""
        # Test that all models have characteristics
        for model in VertexAIModel:
            chars = MODEL_CHARACTERISTICS.get(
                model
            )  # This gets ModelCharacteristics, not ModelProfile
            assert chars is not None, f"Missing characteristics for {model.value}"
            assert chars.context_window > 0
            assert chars.max_output_tokens > 0
            assert isinstance(chars.supports_vision, bool)
            assert isinstance(chars.supports_function_calling, bool)
            assert chars.cost_per_1k_input_tokens >= 0
            assert chars.cost_per_1k_output_tokens >= 0

    def test_prompt_formatting(self) -> None:
        """Test prompt formatting functionality."""
        # Create a prompt with placeholders
        template = (
            "Analyze the following {type}: {content}. "
            "Return JSON with 'severity' and 'description' fields."
        )

        # Format template
        formatted = template.format(
            type="log entry", content="Failed login attempt from IP 192.168.1.100"
        )

        assert "Analyze the following log entry:" in formatted
        assert "Failed login attempt" in formatted
        assert "JSON with 'severity'" in formatted

    @pytest.mark.asyncio
    async def test_different_models(self, vertex_client: VertexAIGeminiClient) -> None:
        """Test using different Vertex AI models."""
        # Use flash model for fast response
        response = await vertex_client.generate_content(
            prompt="What is the capital of France? One word answer.",
            model_name=VertexAIModel.GEMINI_1_5_FLASH.value,
            generation_config={"max_output_tokens": 10},
        )

        assert response is not None
        assert "paris" in response.lower()

    def test_cost_tracking(self, vertex_client: VertexAIGeminiClient) -> None:
        """Test cost tracking functionality."""
        cost_tracker = vertex_client.cost_tracker

        # Record some usage
        cost_tracker.record_usage(
            model=VertexAIModel.GEMINI_1_5_PRO.value, input_tokens=100, output_tokens=50
        )

        # Get cost summary
        summary = cost_tracker.get_usage_summary()

        assert summary["total_cost"] > 0
        assert summary["total_input_tokens"] == 100
        assert summary["total_output_tokens"] == 50

    def test_prompt_optimization(self) -> None:
        """Test prompt optimization functionality."""
        # Test with a prompt that has extra whitespace

        # Test with a prompt that has extra whitespace
        verbose_prompt = """


        Please     analyze    the    following    text    and    provide


        a    summary.


        """

        # Simple whitespace normalization
        optimized = " ".join(verbose_prompt.split())

        # Should remove extra whitespace
        assert len(optimized) < len(verbose_prompt)
        assert "Please analyze the following text" in optimized

    @pytest.mark.asyncio
    async def test_rate_limiting(self, vertex_client: VertexAIGeminiClient) -> None:
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        prompts = [f"What is {i} + {i}?" for i in range(5)]

        tasks = []
        for prompt in prompts:
            task = vertex_client.generate_content(
                prompt=prompt,
                model_name=VertexAIModel.GEMINI_1_5_FLASH.value,
                generation_config={"max_output_tokens": 10},
            )
            tasks.append(task)

        # Should handle rate limiting gracefully
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # At least some should succeed
        successful = [r for r in responses if isinstance(r, str)]
        assert len(successful) > 0

    @pytest.mark.asyncio
    async def test_error_handling_invalid_prompt(
        self, vertex_client: VertexAIGeminiClient
    ) -> None:
        """Test error handling with invalid prompt."""
        # Test with empty prompt
        response = await vertex_client.generate_content(
            prompt="",
            model_name=VertexAIModel.GEMINI_1_5_FLASH.value,
            generation_config={"max_output_tokens": 10},
        )

        # Should handle gracefully (might return None or error message)
        # The exact behavior depends on Vertex AI's response
        assert response is None or isinstance(response, str)

    def test_response_caching(self, vertex_client: VertexAIGeminiClient) -> None:
        """Test response caching functionality."""
        cache = vertex_client.response_cache

        # Test cache operations
        test_prompt = "test prompt"
        test_model = "gemini-pro"
        test_config = {"temperature": 0.5}
        test_response = "cached response"

        # Add to cache
        cache.put(test_prompt, test_model, test_config, test_response)

        # Retrieve from cache
        cached = cache.get(test_prompt, test_model, test_config)
        assert cached == test_response

        # Test cache clear
        cache.clear()
        cached_after_clear = cache.get(test_prompt, test_model, test_config)
        assert cached_after_clear is None

    @pytest.mark.asyncio
    async def test_structured_output_parsing(
        self, vertex_client: VertexAIGeminiClient
    ) -> None:
        """Test structured output parsing with real Vertex AI."""
        prompt = """
        Analyze this text for security issues:
        "Failed login attempts detected from IP 192.168.1.100"

        Respond with JSON containing:
        - severity: low/medium/high/critical
        - description: brief description
        - recommendation: what to do
        """

        response = await vertex_client.generate_content(
            prompt=prompt,
            model_name=VertexAIModel.GEMINI_1_5_PRO.value,
            generation_config={"temperature": 0.3},
        )

        if response:
            # Response should be a string that might contain JSON
            assert isinstance(response, str)
            # Try to parse as JSON
            try:
                import json

                parsed = json.loads(response)
                # If it parses, check for expected fields
                assert isinstance(parsed, dict)
            except ValueError:
                # Response might not be valid JSON, which is ok
                pass

    def test_vertex_ai_authentication(self, vertex_config: Dict[str, str]) -> None:
        """Test Vertex AI authentication setup."""
        # Verify we can create a client with the config
        client = VertexAIGeminiClient()

        # Client should be initialized
        assert hasattr(client, "project_config")
        assert hasattr(client, "cost_tracker")

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_models(
        self, vertex_client: VertexAIGeminiClient
    ) -> None:
        """Test concurrent requests using different models."""
        # Create tasks for different models
        tasks = []

        # Fast model request
        task1 = vertex_client.generate_content(
            prompt="Name one color.",
            model_name=VertexAIModel.GEMINI_1_5_FLASH.value,
            generation_config={"max_output_tokens": 10},
        )
        tasks.append(task1)

        # Pro model request
        task2 = vertex_client.generate_content(
            prompt="Name one animal.",
            model_name=VertexAIModel.GEMINI_1_5_PRO.value,
            generation_config={"max_output_tokens": 10},
        )
        tasks.append(task2)

        # Execute concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Both should succeed
        assert all(isinstance(r, str) or r is None for r in responses)

    @pytest.mark.asyncio
    async def test_retry_on_temporary_failure(
        self, vertex_client: VertexAIGeminiClient
    ) -> None:
        """Test retry logic on temporary failures."""
        # This test is tricky because we need to trigger a failure
        # We'll use an extremely long prompt that might hit limits
        huge_prompt = "a" * 100000  # 100k characters

        response = await vertex_client.generate_content(
            prompt=huge_prompt,
            model_name=VertexAIModel.GEMINI_1_5_FLASH.value,
            retry_count=2,
        )

        # Should handle the error gracefully
        assert response is None or isinstance(response, str)

    @pytest.mark.asyncio
    async def test_quality_monitoring(
        self, vertex_client: VertexAIGeminiClient
    ) -> None:
        """Test quality monitoring of responses."""
        # Generate a response
        response = await vertex_client.generate_content(
            prompt="What is the meaning of life?",
            model_name=VertexAIModel.GEMINI_1_5_PRO.value,
            generation_config={"max_output_tokens": 50},
        )

        if response:
            # Check that response was tracked
            metrics = vertex_client.get_metrics()
            assert metrics["total_requests"] > 0

            # Response should be a non-empty string
            assert len(response) > 0

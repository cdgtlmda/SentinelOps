"""
Gemini AI Integration for SentinelOps
Provides analysis and reasoning capabilities through Google's Gemini models
"""

# Standard library imports
import asyncio
import hashlib
import logging
import os
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple, AsyncGenerator

# Third-party imports
import vertexai
from google.api_core import exceptions as google_exceptions
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part, Tool

logger = logging.getLogger(__name__)

# Initialize Vertex AI
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")

# Initialize once at module level
vertexai.init(project=PROJECT_ID, location=LOCATION)


class VertexAIModel(Enum):
    """Available Vertex AI Gemini models with their characteristics"""

    GEMINI_1_5_PRO = "gemini-1.5-pro-002"
    GEMINI_1_5_FLASH = "gemini-1.5-flash-002"
    GEMINI_1_0_PRO = "gemini-1.0-pro-002"


@dataclass
class ModelCharacteristics:
    """Characteristics of a Vertex AI model"""

    name: str
    context_window: int
    max_output_tokens: int
    supports_vision: bool
    supports_function_calling: bool
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float


# Model characteristics database
MODEL_CHARACTERISTICS = {
    VertexAIModel.GEMINI_1_5_PRO: ModelCharacteristics(
        name="gemini-1.5-pro-002",
        context_window=2_097_152,  # 2M tokens
        max_output_tokens=8192,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.00125,
        cost_per_1k_output_tokens=0.00375,
    ),
    VertexAIModel.GEMINI_1_5_FLASH: ModelCharacteristics(
        name="gemini-1.5-flash-002",
        context_window=1_048_576,  # 1M tokens
        max_output_tokens=8192,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.00015,
        cost_per_1k_output_tokens=0.0006,
    ),
    VertexAIModel.GEMINI_1_0_PRO: ModelCharacteristics(
        name="gemini-1.0-pro-002",
        context_window=32768,
        max_output_tokens=8192,
        supports_vision=False,
        supports_function_calling=True,
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
    ),
}


class VertexAIGeminiClient:
    """
    Production-ready Vertex AI Gemini client with enterprise features.

    No API keys required - uses Application Default Credentials (ADC).
    """

    def __init__(
        self,
        model: Union[str, VertexAIModel] = VertexAIModel.GEMINI_1_5_PRO,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_output_tokens: int = 2048,
        rate_limit_per_minute: int = 60,
        enable_caching: bool = True,
        cache_ttl: int = 3600,
        enable_monitoring: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        connection_pool_size: int = 10,
    ):
        """
        Initialize the Vertex AI Gemini client.

        Args:
            model: Model to use (enum or string)
            temperature: Controls randomness (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            max_output_tokens: Maximum tokens in response
            rate_limit_per_minute: Rate limit for requests
            enable_caching: Enable response caching
            cache_ttl: Cache time-to-live in seconds
            enable_monitoring: Enable metrics collection
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            connection_pool_size: Size of connection pool
        """
        # Model configuration
        if isinstance(model, str):
            self.model_enum = VertexAIModel(model)
        else:
            self.model_enum = model

        self.model_name = self.model_enum.value
        self.characteristics = MODEL_CHARACTERISTICS[self.model_enum]

        # Generation configuration
        self.generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
        )

        # Initialize the model
        self.model = GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
        )

        # Rate limiting
        self.rate_limit_per_minute = rate_limit_per_minute
        self._request_times = deque()
        self._rate_limit_lock = threading.Lock()

        # Caching
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_lock = threading.Lock()

        # Monitoring
        self.enable_monitoring = enable_monitoring
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "errors_by_type": {},
        }
        self._metrics_lock = threading.Lock()

        # Error handling
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Connection pooling
        self.executor = ThreadPoolExecutor(max_workers=connection_pool_size)

        logger.info(
            "Initialized Vertex AI Gemini client with model %s, project: %s, location: %s",
            self.model_name,
            PROJECT_ID,
            LOCATION,
        )

    def generate_content(
        self,
        prompt: Union[str, List[Union[str, Part]]],
        stream: bool = False,
        retry_on_error: bool = True,
        custom_generation_config: Optional[GenerationConfig] = None,
        safety_settings: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Tool]] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate content using Vertex AI Gemini.

        Args:
            prompt: Text prompt or list of content parts
            stream: Whether to stream the response
            retry_on_error: Whether to retry on errors
            custom_generation_config: Override default generation config
            safety_settings: Safety settings for content generation
            tools: Function calling tools

        Returns:
            Generated text or async generator for streaming
        """
        # Check rate limit
        self._check_rate_limit()

        # Check cache
        if self.enable_caching and not stream:
            cache_key = self._generate_cache_key(prompt)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                self._record_metric("cache_hits", 1)
                return cached_response
            else:
                self._record_metric("cache_misses", 1)

        # Use custom generation config if provided
        generation_config = custom_generation_config or self.generation_config

        # Record request
        self._record_metric("total_requests", 1)

        try:
            # Generate content
            response = self.model.generate_content(
                contents=prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                tools=tools,
                stream=stream,
            )

            if stream:
                return self._handle_streaming_response(response)
            else:
                text = response.text
                self._record_metric("successful_requests", 1)

                # Cache the response
                if self.enable_caching:
                    self._cache_response(cache_key, text)

                # Record token usage (if available)
                if hasattr(response, "usage_metadata"):
                    self._record_token_usage(response.usage_metadata)

                return text

        except (ValueError, AttributeError, TypeError, RuntimeError) as e:
            self._record_metric("failed_requests", 1)
            self._record_error(type(e).__name__)

            if retry_on_error and self._should_retry(e):
                return self._retry_request(
                    prompt, stream, custom_generation_config, safety_settings, tools
                )
            else:
                logger.error("Vertex AI Gemini error: %s", e)
                raise

    async def generate_content_async(
        self,
        prompt: Union[str, List[Union[str, Part]]],
        stream: bool = False,
        retry_on_error: bool = True,
        custom_generation_config: Optional[GenerationConfig] = None,
        safety_settings: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Tool]] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Async version of generate_content.
        """
        # Check rate limit
        await asyncio.get_event_loop().run_in_executor(None, self._check_rate_limit)

        # Run generation in executor
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.generate_content,
            prompt,
            stream,
            retry_on_error,
            custom_generation_config,
            safety_settings,
            tools,
        )

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        with self._rate_limit_lock:
            now = time.time()
            # Remove requests older than 1 minute
            while self._request_times and self._request_times[0] < now - 60:
                self._request_times.popleft()

            # Check if we're at the limit
            if len(self._request_times) >= self.rate_limit_per_minute:
                sleep_time = 60 - (now - self._request_times[0])
                if sleep_time > 0:
                    logger.warning("Rate limit reached, sleeping for %.2fs", sleep_time)
                    time.sleep(sleep_time)

            # Record this request
            self._request_times.append(now)

    def _generate_cache_key(self, prompt: Union[str, List[Union[str, Part]]]) -> str:
        """Generate a cache key for the prompt."""
        if isinstance(prompt, str):
            prompt_str = prompt
        else:
            prompt_str = str(prompt)

        return hashlib.sha256(
            f"{self.model_name}:{prompt_str}:{self.generation_config}".encode()
        ).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get a cached response if available and not expired."""
        with self._cache_lock:
            if cache_key in self._cache:
                response, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    return response
                else:
                    del self._cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: str) -> None:
        """Cache a response."""
        with self._cache_lock:
            self._cache[cache_key] = (response, time.time())

            # Limit cache size
            if len(self._cache) > 1000:
                # Remove oldest entries
                sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])
                for key, _ in sorted_items[:100]:
                    del self._cache[key]

    def _handle_streaming_response(self, response) -> AsyncGenerator[str, None]:
        """Handle streaming response."""

        async def stream_generator():
            try:
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                self._record_metric("successful_requests", 1)
            except Exception as e:
                self._record_metric("failed_requests", 1)
                self._record_error(type(e).__name__)
                raise

        return stream_generator()

    def _should_retry(self, error: Exception) -> bool:
        """Determine if an error should be retried."""
        # Retry on specific Google API errors
        if isinstance(error, google_exceptions.GoogleAPIError):
            # Retry on rate limit and server errors
            if hasattr(error, "code"):
                return error.code in [429, 500, 502, 503, 504]
        return False

    def _retry_request(
        self,
        prompt: Union[str, List[Union[str, Part]]],
        stream: bool,
        custom_generation_config: Optional[GenerationConfig],
        safety_settings: Optional[Dict[str, Any]],
        tools: Optional[List[Tool]],
        attempt: int = 1,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Retry a failed request with exponential backoff."""
        if attempt > self.max_retries:
            raise RuntimeError(f"Max retries ({self.max_retries}) exceeded")

        delay = self.retry_delay * (2 ** (attempt - 1))
        logger.info(
            "Retrying request (attempt %d/%d) after %.1fs",
            attempt,
            self.max_retries,
            delay,
        )
        time.sleep(delay)

        try:
            return self.generate_content(
                prompt=prompt,
                stream=stream,
                retry_on_error=False,  # Prevent infinite recursion
                custom_generation_config=custom_generation_config,
                safety_settings=safety_settings,
                tools=tools,
            )
        except (ValueError, AttributeError, TypeError, RuntimeError) as e:
            if self._should_retry(e) and attempt < self.max_retries:
                return self._retry_request(
                    prompt,
                    stream,
                    custom_generation_config,
                    safety_settings,
                    tools,
                    attempt + 1,
                )
            else:
                raise

    def _record_metric(self, metric: str, value: Union[int, float]) -> None:
        """Record a metric."""
        if not self.enable_monitoring:
            return

        with self._metrics_lock:
            if metric in self._metrics:
                self._metrics[metric] += value

    def _record_error(self, error_type: str) -> None:
        """Record an error occurrence."""
        if not self.enable_monitoring:
            return

        with self._metrics_lock:
            if error_type not in self._metrics["errors_by_type"]:
                self._metrics["errors_by_type"][error_type] = 0
            self._metrics["errors_by_type"][error_type] += 1

    def _record_token_usage(self, usage_metadata: Any) -> None:
        """Record token usage from response metadata."""
        if not self.enable_monitoring:
            return

        with self._metrics_lock:
            if hasattr(usage_metadata, "prompt_token_count"):
                input_tokens = usage_metadata.prompt_token_count
                self._metrics["total_input_tokens"] += input_tokens

            if hasattr(usage_metadata, "candidates_token_count"):
                output_tokens = usage_metadata.candidates_token_count
                self._metrics["total_output_tokens"] += output_tokens

                # Calculate cost
                input_cost = (
                    input_tokens / 1000
                ) * self.characteristics.cost_per_1k_input_tokens
                output_cost = (
                    output_tokens / 1000
                ) * self.characteristics.cost_per_1k_output_tokens
                self._metrics["total_cost"] += input_cost + output_cost

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        with self._metrics_lock:
            return self._metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self._metrics_lock:
            self._metrics = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "errors_by_type": {},
            }

    def close(self) -> None:
        """Clean up resources."""
        self.executor.shutdown(wait=True)
        logger.info("Vertex AI Gemini client closed")


# Convenience function for simple use cases
def create_gemini_client(
    model: str = "gemini-1.5-pro-002", **kwargs
) -> VertexAIGeminiClient:
    """
    Create a Vertex AI Gemini client with default settings.

    Args:
        model: Model name
        **kwargs: Additional arguments for VertexAIGeminiClient

    Returns:
        Configured VertexAIGeminiClient instance
    """
    return VertexAIGeminiClient(model=model, **kwargs)

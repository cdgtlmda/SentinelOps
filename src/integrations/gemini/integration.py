"""
Main Gemini AI integration class
"""

import asyncio
import json
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, AsyncGenerator, Tuple

from .common import logger, genai, google_exceptions
from .models import GeminiModel, ModelProfile, MODEL_PROFILES, MODEL_CHARACTERISTICS
from .model_selector import ModelSelector
from .prompt_template import PromptLibrary
from .structured_output import SecurityAnalysisOutput
from .rate_limiter import RateLimitConfig, RateLimiter
from .api_key_manager import GeminiAPIKeyManager
from .quota_monitor import QuotaMonitor
from .project_config import GeminiProjectConfig
from .connection_pool import ConnectionPool
from .response_cache import ResponseCache
from .token_optimizer import TokenOptimizer
from .cost_tracker import CostTracker


class LogAnalysisResult:
    """Result object for log analysis"""

    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def is_valid(self) -> bool:
        """Check if analysis is valid"""
        return self.data.get("analysis") is not None

    def get_severity(self) -> str:
        """Get severity level"""
        return str(self.data.get("severity", "UNKNOWN"))

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations"""
        recommendations = self.data.get("recommendations", [])
        return recommendations if isinstance(recommendations, list) else []


class GeminiIntegration:
    """Main Gemini AI integration class"""

    def __init__(
        self,
        api_key_manager: Optional[GeminiAPIKeyManager] = None,
        project_config: Optional[GeminiProjectConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        connection_pool_size: int = 5,
        max_workers: int = 10,
        model_profiles: Optional[Dict[str, ModelProfile]] = None,
    ):

        self.key_manager = api_key_manager or GeminiAPIKeyManager()
        self.project_config = project_config or GeminiProjectConfig()
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.quota_monitor = QuotaMonitor()

        # Model configuration
        self.model_selector = ModelSelector()
        self.model_profiles = model_profiles or MODEL_PROFILES
        self.current_profile: Optional[ModelProfile] = None
        self.default_profile = "security_analysis"
        self.default_model = GeminiModel.GEMINI_2_FLASH

        # Prompt engineering
        self.prompt_library = PromptLibrary()

        # Connection pooling
        self.connection_pool_size = connection_pool_size
        self.connection_pools: Dict[str, ConnectionPool] = {}  # Pool per model

        # Thread pool for concurrent requests
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Caching configuration
        self.cache_enabled = True
        self.response_cache = ResponseCache(ttl=timedelta(minutes=15))

        # Token optimization
        self.token_optimizer = TokenOptimizer()

        # Cost tracking
        self.cost_tracker = CostTracker()

        # Initialize prompt library
        self.prompt_library = PromptLibrary()

        # Safety and validation configuration
        self.confidence_threshold = 0.7  # Default confidence threshold
        self.human_review_triggers: Dict[str, Any] = {
            "low_confidence": 0.5,  # Trigger review if confidence below this
            "high_risk_actions": ["delete", "shutdown", "disable", "remove", "destroy"],
            "critical_severity": True,  # Always review critical issues
            "multiple_inconsistencies": 3,  # Review if more than N inconsistencies
            "unverified_claims_ratio": 0.3,  # Review if >30% claims unverified
        }
        self.human_review_callbacks: List[Callable[..., Any]] = []  # Callbacks for human review
        self.content_filters: List[Callable[[str], str]] = []  # Additional content filters
        self.custom_safety_guardrails: Dict[str, Callable[..., Any]] = {}  # Custom safety checks

        # Metrics tracking
        self._response_times: deque[float] = deque(maxlen=1000)  # Track last 1000 response times
        self._error_count = 0
        self._total_requests = 0
        self._rate_limit_hits = 0
        self._metrics_lock = threading.Lock()
        self._quality_history: List[Dict[str, Any]] = []  # Track response quality
        # Quality monitoring callback
        self._monitoring_callback: Optional[Callable[..., Any]] = None

        # Conversation state for natural language interface
        # user_id -> conversation state
        self._conversation_states: Dict[str, Dict[str, Any]] = {}
        self._conversation_lock = threading.Lock()

        # Embedding cache for future use
        self._embedding_cache: Dict[str, List[float]] = {}
        self._embedding_cache_lock = threading.Lock()

        # Initialize Gemini
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Gemini client with current API key"""
        genai.configure(api_key=self.key_manager.get_current_key())

        # Create connection pools for each unique model in profiles
        unique_models = set()
        for profile in self.model_profiles.values():
            unique_models.add(profile.model.value)

        # Add default model
        unique_models.add(self.project_config.default_model)

        # Create pools
        for model_name in unique_models:
            self.connection_pools[model_name] = ConnectionPool(
                model_name,
                self.connection_pool_size,
                self.project_config.safety_settings,
            )

        logger.info(
            "Initialized Gemini integration with %s model pools", len(unique_models)
        )

    def set_profile(self, profile_name: str) -> None:
        """Set the active model profile"""
        if profile_name not in self.model_profiles:
            raise ValueError(f"Unknown profile: {profile_name}")

        self.current_profile = self.model_profiles[profile_name]
        logger.info("Set active profile to: %s", profile_name)

    def analyze_security_logs(
        self,
        log_entries: str,
        time_range: str,
        source_system: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SecurityAnalysisOutput:
        """
        Analyze security logs for threats and anomalies

        Args:
            log_entries: The log entries to analyze
            time_range: Time range of the logs
            source_system: Source system generating the logs
            context: Additional context information

        Returns:
            Structured analysis output
        """
        # Use the default profile for security analysis
        self.set_profile("security_analysis")

        # Format the prompt
        prompt = self.prompt_library.format_prompt(
            "log_analysis",
            log_entries=log_entries,
            time_range=time_range,
            source_system=source_system,
        )

        # Add context if provided
        if context:
            prompt += f"\n\nAdditional Context:\n{context}"

        # Generate analysis
        response = asyncio.run(
            self.generate_content(
                prompt=prompt,
                profile_name="security_analysis",
            )
        )

        if not response:
            raise ValueError("Failed to generate security analysis")

        # Parse and return structured output
        return SecurityAnalysisOutput(raw_response=response)

    def _determine_model_and_profile(
        self,
        profile_name: Optional[str],
        model_name: Optional[str]
    ) -> Tuple[Optional[ModelProfile], str]:
        """Determine the profile and model to use"""
        profile = None
        if profile_name and profile_name in self.model_profiles:
            profile = self.model_profiles[profile_name]
        elif self.current_profile:
            profile = self.current_profile

        if model_name:
            selected_model = model_name
        elif profile:
            selected_model = profile.model.value
        else:
            selected_model = self.project_config.default_model

        return profile, selected_model

    def _prepare_generation_config(
        self,
        profile: Optional[ModelProfile],
        generation_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare generation configuration"""
        if profile and not generation_config:
            return profile.to_generation_config()
        return self.project_config.get_generation_config(
            **(generation_config or {})
        )

    def _prepare_prompt(
        self,
        prompt: str,
        profile: Optional[ModelProfile]
    ) -> Tuple[str, int]:
        """Prepare and optimize prompt, return optimized prompt and estimated tokens"""
        if profile and profile.system_instruction:
            prompt = f"{profile.system_instruction}\n\n{prompt}"

        optimized_prompt = self.token_optimizer.optimize_prompt(prompt)
        estimated_tokens = self.token_optimizer.estimate_tokens(optimized_prompt)

        return optimized_prompt, estimated_tokens

    async def _execute_generation(
        self,
        selected_model: str,
        optimized_prompt: str,
        config: Dict[str, Any],
        estimated_tokens: int,
        prompt: str
    ) -> Optional[str]:
        """Execute the actual generation request"""
        pool = self.connection_pools.get(selected_model)
        if not pool:
            pool = ConnectionPool(
                selected_model,
                self.connection_pool_size,
                self.project_config.safety_settings,
            )
            self.connection_pools[selected_model] = pool

        model = pool.acquire()
        try:
            start_time = time.time()
            self._total_requests += 1

            response = model.generate_content(optimized_prompt, **config)

            response_time = time.time() - start_time
            self._response_times.append(response_time)

            result_text = response.text if hasattr(response, 'text') else str(response)

            self.rate_limiter.record_request(estimated_tokens)
            self.quota_monitor.record_usage(estimated_tokens)

            if self.cache_enabled:
                self.response_cache.put(prompt, selected_model, config, result_text)

            self.cost_tracker.record_usage(
                selected_model,
                estimated_tokens,
                len(result_text) // 4,
            )

            return result_text
        finally:
            pool.release(model)

    async def generate_content(
        self,
        prompt: str,
        generation_config: Optional[Dict[str, Any]] = None,
        profile_name: Optional[str] = None,
        model_name: Optional[str] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ) -> Optional[str]:
        """
        Generate content using Gemini API with rate limiting and error handling

        Args:
            prompt: The prompt to send to Gemini
            generation_config: Optional generation configuration
            profile_name: Name of the profile to use
            model_name: Specific model to use
            retry_count: Number of retries on failure
            retry_delay: Delay between retries in seconds

        Returns:
            Generated content or None on failure
        """
        profile, selected_model = self._determine_model_and_profile(profile_name, model_name)
        config = self._prepare_generation_config(profile, generation_config)
        optimized_prompt, estimated_tokens = self._prepare_prompt(prompt, profile)

        if self.cache_enabled:
            cached = self.response_cache.get(prompt, selected_model, config)
            if cached:
                return cached

        for attempt in range(retry_count):
            try:
                can_proceed, wait_time = self.rate_limiter.can_make_request(estimated_tokens)
                if not can_proceed and wait_time:
                    await asyncio.sleep(wait_time)
                    continue

                return await self._execute_generation(
                    selected_model, optimized_prompt, config, estimated_tokens, prompt
                )

            except (ValueError, AttributeError, TypeError, RuntimeError, google_exceptions.GoogleAPIError) as e:
                self._error_count += 1
                logger.error("Error in attempt %s/%s: %s", attempt + 1, retry_count, str(e))

                if self._handle_api_error(e) and attempt < retry_count - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue

                if attempt == retry_count - 1:
                    logger.error("All retry attempts failed for prompt generation")

        return None

    def _handle_api_error(self, error: Exception) -> bool:
        """Handle API errors and determine if retry is possible"""
        error_type = type(error).__name__

        if "ResourceExhausted" in error_type:
            # Try rotating API key
            if self.key_manager.rotate_key():
                self._initialize_client()
                return True
            return False

        elif "InvalidArgument" in error_type:
            logger.error("Invalid request: %s", error)
            return False

        elif any(x in error_type for x in ["ServiceUnavailable", "DeadlineExceeded"]):
            logger.warning("Temporary API error: %s", error)
            return True

        logger.error("Unexpected API error: %s", error)
        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics and statistics"""
        with self._metrics_lock:
            avg_response_time = (
                sum(self._response_times) / len(self._response_times)
                if self._response_times
                else 0
            )
            return {
                "total_requests": self._total_requests,
                "error_count": self._error_count,
                "error_rate": self._error_count / max(self._total_requests, 1),
                "average_response_time": avg_response_time,
                "rate_limit_hits": self._rate_limit_hits,
                "cache_stats": self.response_cache.get_stats(),
                "quota_usage": self.quota_monitor.get_usage_summary(),
                "cost_summary": self.cost_tracker.get_usage_summary(),
                "rate_limiter_stats": self.rate_limiter.get_usage_stats(),
            }

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        logger.info("Gemini integration cleaned up")

    # Convenience methods for common security operations
    async def detect_threats(
        self, indicators: str, environment: str, baseline: str, recent_incidents: str
    ) -> SecurityAnalysisOutput:
        """Detect threats from indicators"""
        prompt = self.prompt_library.format_prompt(
            "threat_detection",
            indicators=indicators,
            environment=environment,
            baseline=baseline,
            recent_incidents=recent_incidents,
        )
        response = await self.generate_content(prompt, profile_name="security_analysis")
        return SecurityAnalysisOutput(raw_response=response or "")

    async def assess_risk(
        self,
        findings: str,
        critical_assets: str,
        business_context: str,
        current_controls: str,
    ) -> SecurityAnalysisOutput:
        """Perform risk assessment"""
        prompt = self.prompt_library.format_prompt(
            "risk_assessment",
            findings=findings,
            critical_assets=critical_assets,
            business_context=business_context,
            current_controls=current_controls,
        )
        response = await self.generate_content(prompt, profile_name="security_analysis")
        return SecurityAnalysisOutput(raw_response=response or "")

    def use_profile(self, profile_name: str) -> None:
        """Set the default profile for model selection"""
        if profile_name not in MODEL_PROFILES:
            raise ValueError(f"Unknown profile: {profile_name}")
        self.default_profile = profile_name

    async def warm_up_models(self, models: Optional[List[str]] = None) -> None:
        """Warm up model connections"""
        test_prompt = "Hello, this is a warm-up request."

        if models:
            # Warm up specific models
            for model_name in models:
                if model_name in self.connection_pools:
                    pool = self.connection_pools[model_name]
                    model = pool.acquire()
                    try:
                        model.generate_content(test_prompt)
                    finally:
                        pool.release(model)
        else:
            # Default warm up behavior
            tasks = []
            for _ in range(min(3, self.connection_pool_size)):
                tasks.append(self.generate_content(test_prompt))
            await asyncio.gather(*tasks, return_exceptions=True)

    async def get_quota_usage(self) -> Dict[str, Any]:
        """Get current quota usage statistics"""
        return self.quota_monitor.get_usage_stats()

    async def analyze_logs(
        self,
        logs: Optional[List[Dict[str, Any]]] = None,
        log_entries: Optional[str] = None,
        time_range: Optional[str] = None,
        source_system: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> LogAnalysisResult:
        """Analyze security logs using Gemini"""
        # Handle both old and new API
        if log_entries is not None:
            # New API with string log entries
            log_text = log_entries
            analysis_context = {
                "time_range": time_range,
                "source_system": source_system,
                **(context or {})
            }
        else:
            # Old API with list of log dicts
            logs = logs or []
            log_text = "\n".join([
                f"{log.get('timestamp', 'N/A')}: {log.get('message', '')}"
                for log in logs[:100]
            ])
            analysis_context = context or {}

        prompt = f"""Analyze the following security logs and identify any potential threats
        or anomalies:

Logs:
{log_text}

Context:
{json.dumps(analysis_context, indent=2) if analysis_context else 'No additional context provided'}

Provide:
1. Summary of findings
2. Identified threats or anomalies
3. Severity assessment
4. Recommended actions
"""

        response = await self.generate_content(prompt, profile_name="security_analysis")

        # Parse response to extract structured data
        severity = (
            "HIGH" if response and any(
                word in response.upper()
                for word in ["CRITICAL", "HIGH", "SEVERE", "FAILED LOGIN"]
            ) else "MEDIUM"
        )

        return LogAnalysisResult({
            "analysis": response,
            "log_count": len(logs) if logs else 1,
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "recommendations": (
                [{"action": "Review logs", "priority": "IMMEDIATE"}]
                if severity == "HIGH" else []
            )
        })

    def estimate_cost(self, text: str, model_name: Optional[str] = None) -> Dict[str, float]:
        """Estimate the cost of processing text"""
        default_model_str = (
            self.default_model.value
            if isinstance(self.default_model, GeminiModel)
            else str(self.default_model)
        )
        actual_model = model_name or default_model_str

        # Estimate tokens (rough: 1 token per 4 characters)
        input_tokens = len(text) // 4
        # Estimate output tokens (assume similar length response)
        output_tokens = input_tokens

        # Get model pricing
        model_enum = None
        for m in GeminiModel:
            if m.value == actual_model:
                model_enum = m
                break

        if model_enum and model_enum in MODEL_CHARACTERISTICS:
            char = MODEL_CHARACTERISTICS[model_enum]
            input_cost = (input_tokens / 1000) * char.cost_per_1k_input_tokens
            output_cost = (output_tokens / 1000) * char.cost_per_1k_output_tokens
        else:
            # Default pricing
            input_cost = (input_tokens / 1000) * 0.0001
            output_cost = (output_tokens / 1000) * 0.0002

        total_cost = input_cost + output_cost

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }

    async def batch_generate(self, prompts: List[str], **kwargs: Any) -> List[Optional[str]]:
        """Generate content for multiple prompts in batch"""
        tasks = [self.generate_content(prompt, **kwargs) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Convert exceptions to None for proper return type
        return [result if not isinstance(result, BaseException) else None for result in results]

    # Safety and validation methods
    async def _verify_facts(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify facts in response against context"""
        verified_claims = []
        unverified_claims = []

        # Simple implementation - can be enhanced with more sophisticated fact checking

        # Check for numbers in response
        import re
        numbers_in_response = re.findall(r'\b\d+\b', response)
        context_values = [str(v) for v in context.values() if isinstance(v, (int, float))]

        for num in numbers_in_response:
            if num in context_values:
                verified_claims.append(f"Number {num} verified")
            else:
                unverified_claims.append(f"Number {num} unverified")

        # Check for IPs
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips_in_response = re.findall(ip_pattern, response)
        context_ips = [
            str(v) for v in context.values()
            if isinstance(v, str) and re.match(ip_pattern, v)
        ]

        for ip in ips_in_response:
            if ip in context_ips:
                verified_claims.append(f"IP {ip} verified")
            else:
                unverified_claims.append(f"IP {ip} unverified")

        total_claims = len(verified_claims) + len(unverified_claims)
        verification_rate = len(verified_claims) / total_claims if total_claims > 0 else 1.0

        return {
            "all_verified": len(unverified_claims) == 0,
            "verification_rate": verification_rate,
            "verified_claims": verified_claims,
            "unverified_claims": unverified_claims
        }

    async def _check_consistency(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check response consistency"""
        inconsistencies = []

        # Simple consistency checks
        response_lower = response.lower()

        # Check for contradictions in severity
        if "critical" in response_lower and context.get("severity") == "low":
            inconsistencies.append("Response claims critical but context shows low severity")

        if "minimal impact" in response_lower and context.get("severity") == "critical":
            inconsistencies.append(
                "Response claims minimal impact but context shows critical severity"
            )

        return {
            "is_consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies,
            "confidence": 1.0 - (len(inconsistencies) * 0.2)  # Reduce confidence per inconsistency
        }

    async def _check_human_review_needed(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if human review is needed"""
        triggers = []

        # Check confidence threshold
        confidence = context.get("confidence", 1.0)
        if confidence < self.human_review_triggers["low_confidence"]:
            triggers.append(f"Low confidence: {confidence}")

        # Check for high-risk actions
        response_lower = response.lower()
        for action in self.human_review_triggers["high_risk_actions"]:
            if action in response_lower:
                triggers.append(f"High-risk action: {action}")

        # Check critical severity
        if (
            self.human_review_triggers["critical_severity"]
            and context.get("severity") == "critical"
        ):
            triggers.append("Critical severity issue")

        return {
            "review_needed": len(triggers) > 0,
            "triggers": triggers,
            "priority": "high" if len(triggers) > 1 else "medium"
        }

    def add_human_review_callback(self, callback: Callable[..., Any]) -> None:
        """Add a callback for human review"""
        self.human_review_callbacks.append(callback)

    async def _trigger_human_review(self, issue: str, context: Dict[str, Any]) -> None:
        """Trigger human review callbacks"""
        for callback in self.human_review_callbacks:
            await callback(issue, context)

    def add_content_filter(self, filter_func: Callable[[str], str]) -> None:
        """Add a content filter"""
        self.content_filters.append(filter_func)

    def _apply_content_filters(self, content: str) -> str:
        """Apply all content filters to the content"""
        filtered_content = content
        for filter_func in self.content_filters:
            filtered_content = filter_func(filtered_content)
        return filtered_content

    def add_safety_guardrail(self, name: str, guardrail: Callable[..., Any]) -> None:
        """Add a custom safety guardrail"""
        self.custom_safety_guardrails[name] = guardrail

    async def _check_prompt_safety(self, prompt: str) -> Dict[str, Any]:
        """Check prompt safety using custom guardrails"""
        violations = []

        for name, guardrail in self.custom_safety_guardrails.items():
            result = await guardrail(prompt)
            if not result.get("safe", True):
                violations.append({
                    "guardrail": name,
                    "reason": result.get("reason", "Unknown")
                })

        return {
            "safe": len(violations) == 0,
            "violations": violations
        }

    async def generate_with_validation(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate content with validation and safety checks"""
        context = context or {}

        # Check prompt safety
        safety_result = await self._check_prompt_safety(prompt)
        if not safety_result["safe"]:
            return {
                "success": False,
                "error": "Prompt failed safety checks",
                "violations": safety_result["violations"]
            }

        # Generate content
        response = await self.generate_content(prompt, **kwargs)

        if not response:
            return {
                "success": False,
                "error": "Failed to generate response"
            }

        # Apply content filters
        filtered_response = self._apply_content_filters(response)

        # Verify facts
        fact_result = await self._verify_facts(filtered_response, context)

        # Check consistency
        consistency_result = await self._check_consistency(filtered_response, context)

        # Update context with confidence
        context["confidence"] = consistency_result["confidence"]

        # Check if human review needed
        review_result = await self._check_human_review_needed(filtered_response, context)

        # Trigger review if needed
        if review_result["review_needed"]:
            await self._trigger_human_review(
                f"Review needed for response: {filtered_response[:100]}...",
                {
                    "triggers": review_result["triggers"],
                    "context": context,
                    "response": filtered_response
                }
            )

        return {
            "success": True,
            "response": filtered_response,
            "validation": {
                "facts": fact_result,
                "consistency": consistency_result,
                "human_review": review_result
            },
            "confidence": consistency_result["confidence"]
        }

    def _calculate_average_response_time(self) -> float:
        """Calculate average response time from recent requests"""
        with self._metrics_lock:
            if not self._response_times:
                return 0.0
            return sum(self._response_times) / len(self._response_times)

    def _calculate_error_rate(self) -> float:
        """Calculate error rate from requests"""
        with self._metrics_lock:
            if self._total_requests == 0:
                return 0.0
            return self._error_count / self._total_requests

    def _get_rate_limit_hits(self) -> int:
        """Get number of rate limit hits"""
        with self._metrics_lock:
            return self._rate_limit_hits

    def get_conversation_state(self, user_id: str) -> Dict[str, Any]:
        """Get or create conversation state for a user"""
        with self._conversation_lock:
            if user_id not in self._conversation_states:
                self._conversation_states[user_id] = {
                    "history": [],
                    "context": {},
                    "created_at": datetime.now().isoformat()
                }
            return self._conversation_states[user_id].copy()

    def update_conversation_state(
        self,
        user_id: str,
        query: str,
        response: str,
        intent: Optional[str] = None
    ) -> None:
        """Update conversation state with new interaction"""
        with self._conversation_lock:
            state = self.get_conversation_state(user_id)
            state["history"].append({
                "query": query,
                "response": response,
                "intent": intent,
                "timestamp": datetime.now().isoformat()
            })
            # Keep only last 10 interactions
            if len(state["history"]) > 10:
                state["history"] = state["history"][-10:]
            self._conversation_states[user_id] = state

    async def process_natural_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a natural language query with conversation context"""
        # Get conversation state if user_id provided
        conversation_context = ""
        if user_id:
            state = self.get_conversation_state(user_id)
            if state["history"]:
                conversation_context = "\n\nPrevious conversation:\n"
                for item in state["history"][-3:]:  # Last 3 interactions
                    conversation_context += (
                        f"User: {item['query']}\n"
                        f"Assistant: {item['response']}\n"
                    )

        # Build prompt with context
        full_prompt = f"{conversation_context}\n\nCurrent query: {query}"
        if context:
            full_prompt += f"\n\nContext: {json.dumps(context)}"

        # Generate response
        response = await self.generate_content(full_prompt)

        # Update conversation state
        if user_id and response:
            self.update_conversation_state(user_id, query, response)

        return {
            "query": query,
            "response": response,
            "context_used": bool(conversation_context),
            "success": response is not None
        }

    async def get_embedding(self, text: str, model_name: Optional[str] = None) -> List[float]:
        """Get embedding for text with caching"""
        # Check cache first
        cache_key = f"{model_name or 'default'}:{text}"
        with self._embedding_cache_lock:
            if cache_key in self._embedding_cache:
                return self._embedding_cache[cache_key]

        # Generate embedding
        model_name = model_name or "models/text-embedding-004"
        model = genai.GenerativeModel(model_name)

        # pylint: disable=no-member
        result = await model.embed_content_async(text)
        embedding_raw = result.get("embedding", [])

        # Ensure embedding is a list of floats
        embedding: List[float]
        if not isinstance(embedding_raw, list):
            embedding = []
        else:
            embedding = [float(x) for x in embedding_raw]

        # Cache the result
        with self._embedding_cache_lock:
            self._embedding_cache[cache_key] = embedding

        return embedding

    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get cost analysis for current usage"""
        usage_history = self.cost_tracker.usage_history

        total_input_tokens = sum(entry["input_tokens"] for entry in usage_history)
        total_output_tokens = sum(entry["output_tokens"] for entry in usage_history)
        total_cost = sum(entry["cost"] for entry in usage_history)

        return {
            "current_usage": {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_cost": total_cost,
                "entries": len(usage_history)
            },
            "by_model": {},  # Could aggregate by model if needed
            "timestamp": datetime.now().isoformat()
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            "cache": self.response_cache.get_stats(),
            "costs": self.get_cost_analysis(),
            "quota": self.quota_monitor.get_usage_stats(),
            "optimization": {
                "tokens_optimized": getattr(self.token_optimizer, "_total_optimized", 0),
                "optimization_rate": getattr(self.token_optimizer, "_optimization_rate", 0.0)
            },
            "response_times": {
                "average": self._calculate_average_response_time(),
                "count": len(self._response_times)
            },
            "errors": {
                "count": self._error_count,
                "rate": self._calculate_error_rate()
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the integration"""
        checks = {
            "api_connectivity": False,
            "rate_limits": True,
            "cache": True,
            "quota": True
        }

        # Test API connectivity
        try:
            test_response = await self.generate_content(
                "Hello", generation_config={"max_output_tokens": 10}
            )
            checks["api_connectivity"] = test_response is not None
        except Exception:  # pylint: disable=broad-exception-caught
            checks["api_connectivity"] = False

        # Check rate limits
        can_proceed, _ = self.rate_limiter.can_make_request()
        if not can_proceed:
            checks["rate_limits"] = False

        # Check cache
        cache_stats = self.response_cache.get_stats()
        if cache_stats.get("size", 0) > 10000:  # Arbitrary threshold
            checks["cache"] = False

        # Check quota
        quota_stats = self.quota_monitor.get_usage_stats()
        if quota_stats.get("tokens_used", 0) > quota_stats.get("daily_limit", float('inf')) * 0.9:
            checks["quota"] = False

        overall_status = "healthy" if all(checks.values()) else "unhealthy"

        return {
            "status": overall_status,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }

    def get_embedding_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding cache"""
        with self._embedding_cache_lock:
            num_entries = len(self._embedding_cache)
            # Estimate memory usage (rough calculation)
            # Assuming each float is 4 bytes and typical embedding size is 1536
            memory_estimate_mb = (num_entries * 1536 * 4) / (1024 * 1024)

            return {
                "entries": num_entries,
                "memory_estimate_mb": memory_estimate_mb
            }

    def _get_generation_config(
        self,
        profile: ModelProfile,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """Get generation config from profile with overrides"""
        config = genai.types.GenerationConfig(
            temperature=temperature or profile.temperature,
            max_output_tokens=max_tokens or profile.max_output_tokens,
            top_p=profile.top_p,
            top_k=profile.top_k,
            **kwargs
        )
        return config

    def _get_safety_settings(self, profile_name: str) -> List[Any]:
        """Get safety settings for a profile"""
        # Default safety settings
        safety_settings = [
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": (
                    genai.types.HarmBlockThreshold.BLOCK_NONE
                    if profile_name == "security_analysis"
                    else genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                )
            }
        ]

        # Convert to safety setting objects
        return [
            genai.types.SafetySetting(**setting) for setting in safety_settings  # pylint: disable=no-member
        ]

    async def analyze_security_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a security incident using Gemini"""
        prompt = f"""Analyze the following security incident and provide recommendations:

Incident Data:
{json.dumps(incident_data, indent=2)}

Provide:
1. Incident classification
2. Severity assessment
3. Potential impact
4. Recommended response actions
5. Prevention measures
"""

        response = await self.generate_content(prompt, profile_name="security_analysis")

        # Try to get structured response
        if response:
            parsed = self._parse_structured_response(response)
            if parsed:
                return parsed

        return {
            "result": "success" if response else "failed",
            "analysis": response,
            "incident_data": incident_data
        }

    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """Parse structured JSON from response text"""
        if not response:
            return {}

        # Try direct JSON parse
        try:
            result = json.loads(response)
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from code blocks
        import re
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        if matches:
            try:
                result = json.loads(matches[0])
                return result if isinstance(result, dict) else {}
            except json.JSONDecodeError:
                pass

        # Try to find embedded JSON
        json_like_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_like_pattern, response)
        for match in matches:
            try:
                result = json.loads(match)
                return result if isinstance(result, dict) else {}
            except json.JSONDecodeError:
                continue

        # Return structured format with raw response
        return {"raw_response": response}

    def _truncate_to_context_window(self, text: str, max_tokens: int = 8000) -> str:
        """Truncate text to fit within token limit"""
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4

        if len(text) <= max_chars:
            return text

        # Truncate with ellipsis
        return text[:max_chars - 3] + "..."

    def _sanitize_input(self, text: str) -> str:
        """Sanitize input to prevent injection attacks"""
        if not text:
            return ""

        # Remove potential system prompts and injection attempts
        sanitized = text

        # Remove common injection patterns
        injection_patterns = [
            r'\[\[.*?\]\]',  # Double bracket patterns
            r'{{.*?}}',      # Template patterns
            r'\\n\\n\[SYSTEM\].*',  # System instruction attempts
            r"';\s*DROP\s+TABLE.*",  # SQL injection
            r'<script.*?>.*?</script>',  # Script tags
            r'system\..*',   # System access attempts
            r'api_key',      # API key references
        ]

        import re
        for pattern in injection_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        # Remove multiple consecutive newlines
        sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)

        # Escape special characters if needed
        sanitized = sanitized.replace('\\', '\\\\')

        return sanitized.strip()

    async def stream_analysis(self, _prompt: str) -> AsyncGenerator[str, None]:
        """Stream analysis results"""
        # Get or create model
        model = genai.GenerativeModel(self.default_model.value)

        # Generate streaming response
        response = await model.generate_content_async(_prompt, stream=True)

        async for chunk in response:
            if hasattr(chunk, 'text'):
                yield chunk.text

    async def analyze_with_fallback(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with fallback to alternative models on failure"""
        models_to_try = [
            GeminiModel.GEMINI_1_5_PRO_LATEST,
            GeminiModel.GEMINI_2_FLASH,
            GeminiModel.GEMINI_PRO,
        ]

        last_error = None
        for model in models_to_try:
            try:
                prompt = f"Analyze this incident: {json.dumps(incident_data)}"
                response = await self.generate_content(
                    prompt,
                    model_name=model.value
                )

                if response:
                    parsed = self._parse_structured_response(response)
                    return parsed if parsed else {"result": "from_fallback", "response": response}

            except Exception as e:  # pylint: disable=broad-exception-caught
                last_error = e
                logger.warning("Model %s failed: %s", model.value, e)
                continue

        # All models failed
        raise RuntimeError(f"All models failed. Last error: {last_error}")

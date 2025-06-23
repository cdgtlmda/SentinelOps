"""
Cost tracking for Gemini API usage
"""

import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import GeminiModel, MODEL_CHARACTERISTICS


class CostTracker:
    """Track API usage costs"""

    def __init__(self) -> None:
        self.usage_history: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def record_usage(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Record token usage for cost tracking"""
        with self.lock:
            self.usage_history.append(
                {
                    "timestamp": datetime.now(),
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": self._calculate_cost(model, input_tokens, output_tokens),
                }
            )

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost based on current pricing"""
        # Get pricing from model characteristics
        model_enum = None
        for m in GeminiModel:
            if m.value == model:
                model_enum = m
                break

        if model_enum and model_enum in MODEL_CHARACTERISTICS:
            char = MODEL_CHARACTERISTICS[model_enum]
            input_cost = (input_tokens / 1000) * char.cost_per_1k_input_tokens
            output_cost = (output_tokens / 1000) * char.cost_per_1k_output_tokens
            return round(input_cost + output_cost, 6)

        return 0.0

    def get_usage_summary(
        self, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get usage summary for specified time window"""
        with self.lock:
            if time_window:
                cutoff = datetime.now() - time_window
                relevant_usage = [
                    u for u in self.usage_history if u["timestamp"] > cutoff
                ]
            else:
                relevant_usage = self.usage_history

            if not relevant_usage:
                return {
                    "total_cost": 0.0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "request_count": 0,
                    "by_model": {},
                }

            # Aggregate by model
            by_model = {}
            for usage in relevant_usage:
                model = usage["model"]
                if model not in by_model:
                    by_model[model] = {
                        "cost": 0.0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "requests": 0,
                    }

                by_model[model]["cost"] += usage["cost"]
                by_model[model]["input_tokens"] += usage["input_tokens"]
                by_model[model]["output_tokens"] += usage["output_tokens"]
                by_model[model]["requests"] += 1

            return {
                "total_cost": sum(usage["cost"] for usage in relevant_usage),
                "total_input_tokens": sum(
                    usage["input_tokens"] for usage in relevant_usage
                ),
                "total_output_tokens": sum(
                    usage["output_tokens"] for usage in relevant_usage
                ),
                "request_count": len(relevant_usage),
                "by_model": by_model,
                "time_window": str(time_window) if time_window else "all_time",
            }

    def get_cost_projection(self, projection_days: int = 30) -> Dict[str, float]:
        """Project costs based on recent usage"""
        # Use last 7 days for projection
        recent_usage = self.get_usage_summary(timedelta(days=7))

        if recent_usage["request_count"] == 0:
            return {
                "projected_cost": 0.0,
                "projected_requests": 0,
                "projected_tokens": 0,
                "projection_days": projection_days,
            }

        # Calculate daily averages
        daily_cost = recent_usage["total_cost"] / 7
        daily_requests = recent_usage["request_count"] / 7
        daily_tokens = (
            recent_usage["total_input_tokens"] + recent_usage["total_output_tokens"]
        ) / 7

        return {
            "projected_cost": round(daily_cost * projection_days, 2),
            "projected_requests": int(daily_requests * projection_days),
            "projected_tokens": int(daily_tokens * projection_days),
            "projection_days": projection_days,
            "based_on_days": 7,
        }

    def clear_history(self, older_than: Optional[timedelta] = None) -> int:
        """Clear usage history older than specified time"""
        with self.lock:
            if older_than:
                cutoff = datetime.now() - older_than
                initial_count = len(self.usage_history)
                self.usage_history = [
                    u for u in self.usage_history if u["timestamp"] > cutoff
                ]
                return initial_count - len(self.usage_history)
            else:
                count = len(self.usage_history)
                self.usage_history.clear()
                return count

    def estimate_cost(self, text: str, model_name: str) -> float:
        """Estimate the cost of processing text with a given model"""
        # Rough estimation: ~1 token per 4 characters
        estimated_tokens = len(text) // 4

        # Get model pricing from model characteristics
        model_enum = None
        for m in GeminiModel:
            if m.value == model_name:
                model_enum = m
                break

        if model_enum and model_enum in MODEL_CHARACTERISTICS:
            char = MODEL_CHARACTERISTICS[model_enum]
            input_price = char.cost_per_1k_input_tokens
        else:
            # Use a default pricing if model not found
            input_price = 0.0001  # Default price per 1K tokens

        # Calculate estimated cost
        estimated_cost = (estimated_tokens / 1000) * input_price

        return estimated_cost

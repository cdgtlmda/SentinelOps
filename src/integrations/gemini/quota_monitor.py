"""
Quota monitoring for Gemini API usage
"""

import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

from .rate_limiter import QuotaUsage


class QuotaMonitor:
    """Monitors API quota usage and provides insights"""

    def __init__(self) -> None:
        self.usage = QuotaUsage()
        self.hourly_history: List[QuotaUsage] = []
        self.lock = threading.Lock()
        self.daily_requests = 0
        self.request_history: List[datetime] = []

    def record_usage(self, tokens: int) -> None:
        """Record token usage"""
        with self.lock:
            now = datetime.now()

            # Reset hourly counters if needed
            if self.usage.last_reset is None or now - self.usage.last_reset > timedelta(hours=1):
                self.hourly_history.append(self.usage)
                self.usage = QuotaUsage(last_reset=now)

                # Keep only last 24 hours
                if len(self.hourly_history) > 24:
                    self.hourly_history.pop(0)

            self.usage.requests_count += 1
            self.usage.tokens_used += tokens
            self.daily_requests += 1
            self.request_history.append(now)

            # Clean old request history (keep only last 24 hours)
            cutoff = now - timedelta(hours=24)
            self.request_history = [t for t in self.request_history if t > cutoff]

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive usage summary"""
        with self.lock:
            total_requests_24h = sum(h.requests_count for h in self.hourly_history)
            total_tokens_24h = sum(h.tokens_used for h in self.hourly_history)

            # Add current hour
            total_requests_24h += self.usage.requests_count
            total_tokens_24h += self.usage.tokens_used

            return {
                "current_hour": {
                    "requests": self.usage.requests_count,
                    "tokens": self.usage.tokens_used,
                },
                "last_24_hours": {
                    "requests": total_requests_24h,
                    "tokens": total_tokens_24h,
                },
                "hourly_average": {
                    "requests": total_requests_24h / max(len(self.hourly_history), 1),
                    "tokens": total_tokens_24h / max(len(self.hourly_history), 1),
                },
            }

    def predict_remaining_quota(
        self, daily_quota: int, hourly_quota: int
    ) -> Tuple[float, float]:
        """Predict remaining quota based on current usage patterns"""
        summary = self.get_usage_summary()

        # Calculate burn rate
        current_hour_usage = summary["current_hour"]["tokens"]
        avg_hourly_usage = summary["hourly_average"]["tokens"]

        # Predict hours until daily quota exhausted
        remaining_daily = daily_quota - summary["last_24_hours"]["tokens"]
        hours_until_daily_limit = (
            remaining_daily / avg_hourly_usage
            if avg_hourly_usage > 0
            else float("inf")
        )

        # Predict hours until hourly quota exhausted
        remaining_hourly = hourly_quota - current_hour_usage
        minutes_until_hourly_limit = (
            (remaining_hourly / current_hour_usage) * 60
            if current_hour_usage > 0
            else float("inf")
        )

        return hours_until_daily_limit, minutes_until_hourly_limit

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        usage_pct = self.get_usage_percentage()
        hours_to_daily, mins_to_hourly = self.predict_quota_exhaustion()

        return {
            "daily_usage_percentage": usage_pct["daily"],
            "hourly_usage_percentage": usage_pct["hourly"],
            "daily_quota_used": self.daily_requests,
            "hourly_quota_used": len([
                t for t in self.request_history
                if (datetime.now() - t).seconds < 3600
            ]),
            "hours_until_daily_limit": hours_to_daily,
            "minutes_until_hourly_limit": mins_to_hourly,
            "timestamp": datetime.now().isoformat()
        }

    def get_usage_percentage(self) -> Dict[str, float]:
        """Get usage percentage for daily and hourly quotas"""
        # These values should be configurable - using defaults for now
        daily_quota = 1000000  # Default daily quota
        hourly_quota = 50000   # Default hourly quota

        summary = self.get_usage_summary()

        daily_usage = summary["last_24_hours"]["requests"]
        hourly_usage = summary["current_hour"]["requests"]

        return {
            "daily": (daily_usage / daily_quota) * 100 if daily_quota > 0 else 0,
            "hourly": (hourly_usage / hourly_quota) * 100 if hourly_quota > 0 else 0
        }

    def predict_quota_exhaustion(self) -> Tuple[float, float]:
        """Predict when quotas will be exhausted"""
        # Using default quotas - should be configurable
        daily_quota = 1000000
        hourly_quota = 50000

        return self.predict_remaining_quota(daily_quota, hourly_quota)

"""
Rate limiting functionality for Gemini API calls
"""

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    tokens_per_minute: int = 60000
    tokens_per_hour: int = 1000000


@dataclass
class QuotaUsage:
    """Track quota usage"""

    requests_count: int = 0
    tokens_used: int = 0
    last_reset: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.last_reset is None:
            self.last_reset = datetime.now()


class RateLimiter:
    """Implements rate limiting for API calls"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_times: deque[datetime] = deque()
        self.token_usage: deque[Tuple[datetime, int]] = deque()
        self.lock = threading.Lock()

    def can_make_request(
        self, estimated_tokens: int = 0
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if a request can be made within rate limits

        Returns:
            Tuple of (can_proceed, wait_time_seconds)
        """
        with self.lock:
            now = datetime.now()

            # Clean old entries
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)

            self.request_times = deque(t for t in self.request_times if t > hour_ago)
            self.token_usage = deque(
                (t, tokens) for t, tokens in self.token_usage if t > hour_ago
            )

            # Check request limits
            requests_last_minute = sum(1 for t in self.request_times if t > minute_ago)
            requests_last_hour = len(self.request_times)

            if requests_last_minute >= self.config.requests_per_minute:
                wait_time = (self.request_times[0] - minute_ago).total_seconds()
                return False, wait_time

            if requests_last_hour >= self.config.requests_per_hour:
                wait_time = (self.request_times[0] - hour_ago).total_seconds()
                return False, wait_time

            # Check token limits
            tokens_last_minute = sum(
                tokens for t, tokens in self.token_usage if t > minute_ago
            )
            tokens_last_hour = sum(tokens for _, tokens in self.token_usage)

            if (
                tokens_last_minute + estimated_tokens
                > self.config.tokens_per_minute
            ):
                # Find when we can proceed
                for t, tokens in self.token_usage:
                    if t > minute_ago:
                        wait_time = (t - minute_ago).total_seconds()
                        return False, wait_time

            if tokens_last_hour + estimated_tokens > self.config.tokens_per_hour:
                # Find when we can proceed
                for t, tokens in self.token_usage:
                    if t > hour_ago:
                        wait_time = (t - hour_ago).total_seconds()
                        return False, wait_time

            return True, None

    def record_request(self, tokens_used: int) -> None:
        """Record a completed request"""
        with self.lock:
            now = datetime.now()
            self.request_times.append(now)
            self.token_usage.append((now, tokens_used))

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        with self.lock:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)

            requests_last_minute = sum(
                1 for t in self.request_times if t > minute_ago
            )
            requests_last_hour = len(
                [t for t in self.request_times if t > hour_ago]
            )

            tokens_last_minute = sum(
                tokens for t, tokens in self.token_usage if t > minute_ago
            )
            tokens_last_hour = sum(
                tokens for t, tokens in self.token_usage if t > hour_ago
            )

            return {
                "requests_last_minute": requests_last_minute,
                "requests_last_hour": requests_last_hour,
                "tokens_last_minute": tokens_last_minute,
                "tokens_last_hour": tokens_last_hour,
                "requests_per_minute_limit": self.config.requests_per_minute,
                "requests_per_hour_limit": self.config.requests_per_hour,
                "tokens_per_minute_limit": self.config.tokens_per_minute,
                "tokens_per_hour_limit": self.config.tokens_per_hour,
            }

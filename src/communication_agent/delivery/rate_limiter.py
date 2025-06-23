"""
Rate limiting for message delivery.

Implements token bucket algorithm for rate limiting
with per-channel and per-recipient controls.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Messages per second
    rate: float
    # Maximum burst size
    burst: int
    # Whether to allow bursting
    allow_burst: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.rate <= 0:
            raise ValueError("Rate must be positive")
        if self.burst < 1:
            raise ValueError("Burst must be at least 1")


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Tokens are added at a constant rate up to a maximum capacity.
    Each request consumes one token.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (success, wait_time_if_failed)
        """
        async with self._lock:
            now = time.monotonic()

            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.rate))
            self.last_update = now

            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0

            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate

            return False, wait_time

    async def wait_and_consume(self, tokens: int = 1) -> None:
        """Wait until tokens are available and consume them."""
        while True:
            success, wait_time = await self.consume(tokens)
            if success:
                return

            # Wait for tokens to be available
            await asyncio.sleep(wait_time)


class RateLimiter:
    """
    Rate limiter for message delivery.

    Supports:
    - Global rate limiting
    - Per-channel rate limiting
    - Per-recipient rate limiting
    - Burst control
    """

    def __init__(
        self,
        global_config: Optional[RateLimitConfig] = None,
        channel_configs: Optional[Dict[str, RateLimitConfig]] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            global_config: Global rate limit configuration
            channel_configs: Per-channel rate limit configurations
        """
        # Default global config
        self.global_config = global_config or RateLimitConfig(
            rate=100.0,  # 100 messages per second
            burst=200,
        )

        # Default channel configs
        self.channel_configs = channel_configs or {
            "email": RateLimitConfig(rate=10.0, burst=20),
            "sms": RateLimitConfig(rate=1.0, burst=5),
            "slack": RateLimitConfig(rate=50.0, burst=100),
            "webhook": RateLimitConfig(rate=20.0, burst=40),
        }

        # Create token buckets
        self.global_bucket = TokenBucket(
            self.global_config.rate,
            self.global_config.burst,
        )

        self.channel_buckets: Dict[str, TokenBucket] = {}
        for channel, config in self.channel_configs.items():
            self.channel_buckets[channel] = TokenBucket(
                config.rate,
                config.burst,
            )

        # Per-recipient buckets (created on demand)
        self.recipient_buckets: Dict[str, TokenBucket] = {}
        self.recipient_bucket_lock = asyncio.Lock()

        # Statistics
        self.stats = {
            "total_allowed": 0,
            "total_limited": 0,
            "total_wait_time": 0.0,
        }

    async def check_rate_limit(
        self,
        channel: str,
        recipient: Optional[str] = None,
        message_count: int = 1,
    ) -> Tuple[bool, float]:
        """
        Check if message delivery is allowed under rate limits.

        Args:
            channel: Delivery channel
            recipient: Optional recipient for per-recipient limiting
            message_count: Number of messages

        Returns:
            Tuple of (allowed, wait_time_if_not_allowed)
        """
        # Check global rate limit
        global_allowed, global_wait = await self.global_bucket.consume(message_count)
        if not global_allowed:
            self.stats["total_limited"] += 1
            return False, global_wait

        # Check channel rate limit
        if channel in self.channel_buckets:
            channel_allowed, channel_wait = await self.channel_buckets[channel].consume(
                message_count
            )
            if not channel_allowed:
                # Return tokens to global bucket
                await self.global_bucket.consume(-message_count)
                self.stats["total_limited"] += 1
                return False, channel_wait

        # Check recipient rate limit if configured
        if recipient:
            recipient_bucket = await self._get_recipient_bucket(recipient)
            if recipient_bucket:
                recipient_allowed, recipient_wait = await recipient_bucket.consume(
                    message_count
                )
                if not recipient_allowed:
                    # Return tokens to other buckets
                    await self.global_bucket.consume(-message_count)
                    if channel in self.channel_buckets:
                        await self.channel_buckets[channel].consume(-message_count)
                    self.stats["total_limited"] += 1
                    return False, recipient_wait

        self.stats["total_allowed"] += 1
        return True, 0.0

    async def wait_if_limited(
        self,
        channel: str,
        recipient: Optional[str] = None,
        message_count: int = 1,
    ) -> None:
        """
        Wait if rate limited before allowing delivery.

        Args:
            channel: Delivery channel
            recipient: Optional recipient
            message_count: Number of messages
        """
        start_time = time.monotonic()

        while True:
            allowed, wait_time = await self.check_rate_limit(
                channel,
                recipient,
                message_count,
            )

            if allowed:
                total_wait = time.monotonic() - start_time
                if total_wait > 0:
                    self.stats["total_wait_time"] += total_wait
                    logger.debug(
                        "Rate limit wait completed",
                        extra={
                            "channel": channel,
                            "wait_time": total_wait,
                        },
                    )
                return

            # Wait before retrying
            logger.debug(
                "Rate limited, waiting %.2fs", wait_time,
                extra={
                    "channel": channel,
                    "recipient": recipient,
                },
            )
            await asyncio.sleep(wait_time)

    async def _get_recipient_bucket(
        self,
        recipient: str,  # pylint: disable=unused-argument
    ) -> Optional[TokenBucket]:
        """Get or create a recipient-specific token bucket."""
        # For now, return None (no per-recipient limiting)
        # This could be implemented based on configuration
        return None

    def update_channel_config(
        self,
        channel: str,
        config: RateLimitConfig,
    ) -> None:
        """Update rate limit configuration for a channel."""
        self.channel_configs[channel] = config

        # Create new bucket with updated config
        self.channel_buckets[channel] = TokenBucket(
            config.rate,
            config.burst,
        )

        logger.info(
            "Updated rate limit for channel %s", channel,
            extra={
                "rate": config.rate,
                "burst": config.burst,
            },
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        channel_stats = {}
        for channel, bucket in self.channel_buckets.items():
            channel_stats[channel] = {
                "tokens_available": int(bucket.tokens),
                "capacity": bucket.capacity,
                "rate": bucket.rate,
            }

        return {
            **self.stats,
            "global_tokens": int(self.global_bucket.tokens),
            "channels": channel_stats,
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            "total_allowed": 0,
            "total_limited": 0,
            "total_wait_time": 0.0,
        }

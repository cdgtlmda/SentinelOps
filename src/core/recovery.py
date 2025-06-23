"""
Error recovery strategies for SentinelOps agents.
"""

import asyncio
import functools
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from ..api.exceptions import AgentException
from ..config.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RecoveryStrategy(Enum):
    """Available recovery strategies."""

    RETRY = "retry"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK = "fallback"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    BULKHEAD = "bulkhead"


@dataclass
class RetryConfig:
    """Configuration for retry strategy."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[Type[Exception]] = field(
        default_factory=lambda: [Exception]
    )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker strategy."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting strategy."""

    max_calls: int = 10
    time_window: float = 60.0  # seconds


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead isolation."""

    max_concurrent_calls: int = 10
    max_queue_size: int = 50


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED

    def call_succeeded(self) -> None:
        """Record successful call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def call_failed(self) -> None:
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                "Circuit breaker opened after %s failures", self.failure_count
            )

    def can_execute(self) -> bool:
        """Check if call can be executed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time:
                time_since_failure = (
                    datetime.now(timezone.utc) - self.last_failure_time
                ).total_seconds()

                if time_since_failure >= self.config.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker moved to half-open state")
                    return True

            return False

        # HALF_OPEN state
        return True


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = float(config.max_calls)
        self.last_update = datetime.now(timezone.utc)
        self.lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Try to acquire a token."""
        async with self.lock:
            now = datetime.now(timezone.utc)
            time_passed = (now - self.last_update).total_seconds()

            # Replenish tokens
            tokens_to_add = time_passed * (
                self.config.max_calls / self.config.time_window
            )
            self.tokens = min(self.config.max_calls, self.tokens + tokens_to_add)
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True

            return False


class Bulkhead:
    """Bulkhead isolation implementation."""

    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent_calls)
        self.queue_size = 0
        self.lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Try to acquire bulkhead slot."""
        async with self.lock:
            if self.queue_size >= self.config.max_queue_size:
                return False
            self.queue_size += 1

        try:
            await self.semaphore.acquire()
            return True
        finally:
            async with self.lock:
                self.queue_size -= 1

    def release(self) -> None:
        """Release bulkhead slot."""
        self.semaphore.release()


def with_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retry logic.

    Args:
        config: Retry configuration
        on_retry: Callback function called on each retry
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        retry_handler = _RetryHandler(config, on_retry)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_handler.execute_with_retry_async(func, args, kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            return retry_handler.execute_with_retry_sync(func, args, kwargs)

        if asyncio.iscoroutinefunction(func):
            return cast(Callable[..., T], async_wrapper)
        else:
            return cast(Callable[..., T], sync_wrapper)

    return decorator


class _RetryHandler:
    """Helper class to handle retry logic."""

    def __init__(
        self,
        config: RetryConfig,
        on_retry: Optional[Callable[[Exception, int], None]] = None,
    ):
        self.config = config
        self.on_retry = on_retry

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Check if we should retry based on exception and attempt."""
        if not any(
            isinstance(exception, exc_type)
            for exc_type in self.config.retryable_exceptions
        ):
            return False
        return attempt < self.config.max_attempts - 1

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = min(
            self.config.initial_delay * (self.config.exponential_base**attempt),
            self.config.max_delay,
        )

        if self.config.jitter:
            import random

            delay *= 0.5 + random.random()

        return delay

    def _log_retry(self, exception: Exception, attempt: int, delay: float) -> None:
        """Log retry attempt."""
        logger.warning(
            "Retry attempt %s/%s after %.2fs delay. Error: %s",
            attempt + 1,
            self.config.max_attempts,
            delay,
            exception,
        )

        if self.on_retry:
            self.on_retry(exception, attempt + 1)

    async def execute_with_retry_async(
        self, func: Callable[..., T], args: Any, kwargs: Any
    ) -> T:
        """Execute function with async retry logic."""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return cast(T, await result)
                else:
                    return result
            except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                last_exception = e

                if not self._should_retry(e, attempt):
                    raise

                delay = self._calculate_delay(attempt)
                self._log_retry(e, attempt, delay)
                await asyncio.sleep(delay)

        if last_exception is not None:
            raise last_exception
        else:
            raise RuntimeError("Max retry attempts reached without capturing exception")

    def execute_with_retry_sync(
        self, func: Callable[..., T], args: Any, kwargs: Any
    ) -> T:
        """Execute function with sync retry logic."""
        import time

        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)
            except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                last_exception = e

                if not self._should_retry(e, attempt):
                    raise

                delay = self._calculate_delay(attempt)
                self._log_retry(e, attempt, delay)
                time.sleep(delay)

        if last_exception is not None:
            raise last_exception
        else:
            raise RuntimeError("Max retry attempts reached without capturing exception")


def with_circuit_breaker(
    breaker: CircuitBreaker,
    fallback: Optional[Union[Callable[..., T], Callable[..., Awaitable[T]]]] = None,
) -> Callable[
    [Union[Callable[..., T], Callable[..., Awaitable[T]]]],
    Union[Callable[..., T], Callable[..., Awaitable[T]]],
]:
    """
    Decorator for circuit breaker pattern.

    Args:
        breaker: Circuit breaker instance
        fallback: Optional fallback function when circuit is open
    """

    def decorator(
        func: Union[Callable[..., T], Callable[..., Awaitable[T]]],
    ) -> Union[Callable[..., T], Callable[..., Awaitable[T]]]:

        handler: _CircuitBreakerHandler = _CircuitBreakerHandler(breaker, fallback)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            return await handler.execute_async(func, args, kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            return cast(T, handler.execute_sync(func, args, kwargs))

        if asyncio.iscoroutinefunction(func):
            return cast(
                Union[Callable[..., T], Callable[..., Awaitable[T]]], async_wrapper
            )
        else:
            return cast(
                Union[Callable[..., T], Callable[..., Awaitable[T]]], sync_wrapper
            )

    return decorator


class _CircuitBreakerHandler:
    """Helper class to handle circuit breaker logic."""

    def __init__(
        self,
        breaker: CircuitBreaker,
        fallback: Optional[
            Union[Callable[..., Any], Callable[..., Awaitable[Any]]]
        ] = None,
    ):
        self.breaker = breaker
        self.fallback = fallback

    def _handle_circuit_open(self, func_name: str) -> None:
        """Handle when circuit is open, raise or return fallback."""
        logger.warning("Circuit breaker is open for %s", func_name)
        if not self.fallback:
            raise AgentException(
                agent_name="circuit_breaker",
                message="Service unavailable - circuit breaker is open",
            )

    async def execute_async(
        self,
        func: Union[Callable[..., T], Callable[..., Awaitable[T]]],
        args: Any,
        kwargs: Any,
    ) -> T:
        """Execute async function with circuit breaker protection."""
        if not self.breaker.can_execute():
            self._handle_circuit_open(func.__name__)
            if self.fallback:
                result = self.fallback(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return cast(T, await result)
                return cast(T, result)

        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            self.breaker.call_succeeded()
            return cast(T, result)
        except self.breaker.config.expected_exception:
            self.breaker.call_failed()
            raise

    def execute_sync(self, func: Callable[..., T], args: Any, kwargs: Any) -> T:
        """Execute sync function with circuit breaker protection."""
        if not self.breaker.can_execute():
            self._handle_circuit_open(func.__name__)
            if self.fallback:
                return cast(T, self.fallback(*args, **kwargs))
            raise AgentException(
                agent_name="circuit_breaker",
                message="Service unavailable - circuit breaker is open",
            )

        try:
            result = func(*args, **kwargs)
            self.breaker.call_succeeded()
            return result
        except self.breaker.config.expected_exception:
            self.breaker.call_failed()
            raise


def with_timeout(
    timeout_seconds: float,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for timeout handling.

    Args:
        timeout_seconds: Timeout in seconds
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs), timeout=timeout_seconds
                )
            except asyncio.TimeoutError as exc:
                logger.error("Timeout after %ss for %s", timeout_seconds, func.__name__)
                raise AgentException(
                    agent_name="timeout",
                    message=f"Operation timed out after {timeout_seconds} seconds",
                ) from exc

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            raise ValueError("Timeout decorator only supports async functions")

    return decorator


def with_rate_limit(
    limiter: "RateLimiter",
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for rate limiting.

    Args:
        limiter: Rate limiter instance
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            if not await limiter.acquire():
                logger.warning("Rate limit exceeded for %s", func.__name__)
                raise AgentException(
                    agent_name="rate_limiter", message="Rate limit exceeded"
                )

            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            raise ValueError("Rate limit decorator only supports async functions")

    return decorator


def with_bulkhead(
    bulkhead: "Bulkhead",
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for bulkhead isolation.

    Args:
        bulkhead: Bulkhead instance
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            if not await bulkhead.acquire():
                logger.warning("Bulkhead full for %s", func.__name__)
                raise AgentException(
                    agent_name="bulkhead", message="Service at capacity"
                )

            try:
                return await func(*args, **kwargs)
            finally:
                bulkhead.release()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            raise ValueError("Bulkhead decorator only supports async functions")

    return decorator


class RecoveryManager:
    """
    Manages recovery strategies for agents.
    """

    def __init__(self) -> None:
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.bulkheads: Dict[str, Bulkhead] = {}

    def get_circuit_breaker(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                config or CircuitBreakerConfig()
            )
        return self.circuit_breakers[name]

    def get_rate_limiter(
        self, name: str, config: Optional[RateLimitConfig] = None
    ) -> RateLimiter:
        """Get or create a rate limiter."""
        if name not in self.rate_limiters:
            self.rate_limiters[name] = RateLimiter(config or RateLimitConfig())
        return self.rate_limiters[name]

    def get_bulkhead(
        self, name: str, config: Optional[BulkheadConfig] = None
    ) -> Bulkhead:
        """Get or create a bulkhead."""
        if name not in self.bulkheads:
            self.bulkheads[name] = Bulkhead(config or BulkheadConfig())
        return self.bulkheads[name]

    def apply_recovery_strategies(
        self, func: Callable[..., T], strategies: List[RecoveryStrategy], **configs: Any
    ) -> Callable[..., T]:
        """
        Apply multiple recovery strategies to a function.

        Args:
            func: Function to wrap
            strategies: List of strategies to apply
            **configs: Strategy configurations

        Returns:
            Wrapped function
        """
        wrapped: Callable[..., Any] = func

        for strategy in strategies:
            if strategy == RecoveryStrategy.RETRY:
                config = configs.get("retry_config", RetryConfig())
                wrapped = with_retry(config)(wrapped)

            elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                cb_config: CircuitBreakerConfig = configs.get(
                    "circuit_breaker_config", CircuitBreakerConfig()
                )
                breaker = self.get_circuit_breaker(func.__name__, cb_config)
                fallback = configs.get("fallback")
                decorator: Callable[
                    [Union[Callable[..., Any], Callable[..., Awaitable[Any]]]],
                    Union[Callable[..., Any], Callable[..., Awaitable[Any]]],
                ] = with_circuit_breaker(breaker, fallback)
                wrapped = cast(Callable[..., Any], decorator(wrapped))

            elif strategy == RecoveryStrategy.RATE_LIMIT:
                # Rate limit only supports async functions
                if not asyncio.iscoroutinefunction(wrapped):
                    logger.warning(
                        "Skipping rate limit strategy for non-async function %s",
                        func.__name__,
                    )
                    continue
                config = configs.get("rate_limit_config", RateLimitConfig())
                limiter = self.get_rate_limiter(func.__name__, config)
                wrapped = cast(Callable[..., T], with_rate_limit(limiter)(wrapped))

            elif strategy == RecoveryStrategy.TIMEOUT:
                # Timeout only supports async functions
                if not asyncio.iscoroutinefunction(wrapped):
                    logger.warning(
                        "Skipping timeout strategy for non-async function %s",
                        func.__name__,
                    )
                    continue
                timeout = configs.get("timeout", 30.0)
                wrapped = cast(Callable[..., T], with_timeout(timeout)(wrapped))

            elif strategy == RecoveryStrategy.BULKHEAD:
                # Bulkhead only supports async functions
                if not asyncio.iscoroutinefunction(wrapped):
                    logger.warning(
                        "Skipping bulkhead strategy for non-async function %s",
                        func.__name__,
                    )
                    continue
                config = configs.get("bulkhead_config", BulkheadConfig())
                bulkhead = self.get_bulkhead(func.__name__, config)
                wrapped = cast(Callable[..., T], with_bulkhead(bulkhead)(wrapped))

        return cast(Callable[..., T], wrapped)


# Global recovery manager instance
_recovery_manager: RecoveryManager = RecoveryManager()


def get_recovery_manager() -> RecoveryManager:
    """Get the global recovery manager."""
    return _recovery_manager


# Example usage for agents
def recoverable_agent_method(
    strategies: Optional[List[RecoveryStrategy]] = None, **configs: Any
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to make agent methods recoverable.

    Usage:
        @recoverable_agent_method(
            strategies=[RecoveryStrategy.RETRY, RecoveryStrategy.CIRCUIT_BREAKER],
            retry_config=RetryConfig(max_attempts=5),
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=3)
        )
        async def process_event(self, event):
            ...
    """
    if strategies is None:
        strategies = [RecoveryStrategy.RETRY]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        manager = get_recovery_manager()
        return manager.apply_recovery_strategies(func, strategies, **configs)

    return decorator

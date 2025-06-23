"""
Tests for error recovery strategies.
"""

import asyncio
import time
from typing import Any, cast
from unittest import TestCase

import pytest

from src.api.exceptions import AgentException
from src.core.recovery import (
    Bulkhead,
    BulkheadConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    RateLimiter,
    RateLimitConfig,
    RecoveryManager,
    RecoveryStrategy,
    RetryConfig,
    get_recovery_manager,
    recoverable_agent_method,
    with_bulkhead,
    with_circuit_breaker,
    with_rate_limit,
    with_retry,
    with_timeout,
)


class TestRetryConfig(TestCase):
    """Test retry configuration."""

    def test_default_config(self) -> None:
        """Test default retry configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.retryable_exceptions == [Exception]

    def test_custom_config(self) -> None:
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False,
            retryable_exceptions=[ValueError, TypeError],
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.retryable_exceptions == [ValueError, TypeError]


class TestCircuitBreaker(TestCase):
    """Test circuit breaker implementation."""

    def test_initial_state(self) -> None:
        """Test circuit breaker initial state."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.last_failure_time is None
        assert breaker.can_execute() is True

    def test_failure_counting(self) -> None:
        """Test failure counting and state transitions."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        # First failure
        breaker.call_failed()
        assert breaker.failure_count == 1
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.can_execute() is True

        # Second failure
        breaker.call_failed()
        assert breaker.failure_count == 2
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.can_execute() is True
        # Third failure - should open circuit
        breaker.call_failed()
        assert breaker.failure_count == 3
        # Check state after it should have transitioned
        # Use cast to work around mypy's literal type inference
        current_state = cast(CircuitBreakerState, breaker.state)
        assert current_state == CircuitBreakerState.OPEN
        assert breaker.can_execute() is False

    def test_successful_call_resets(self) -> None:
        """Test that successful calls reset the failure count."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        # Add some failures
        breaker.call_failed()
        breaker.call_failed()
        assert breaker.failure_count == 2

        # Success should reset
        breaker.call_succeeded()
        assert breaker.failure_count == 0
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_recovery_timeout(self) -> None:
        """Test circuit breaker recovery after timeout."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        breaker = CircuitBreaker(config)

        # Open the circuit
        breaker.call_failed()
        breaker.call_failed()
        # Read state freshly to avoid literal type narrowing
        current_state = breaker.state
        assert current_state == CircuitBreakerState.OPEN
        assert breaker.can_execute() is False
        # Wait for recovery timeout
        time.sleep(0.15)

        # Should move to half-open state
        assert breaker.can_execute() is True
        # Read state again to avoid type narrowing
        new_state = breaker.state
        assert new_state == CircuitBreakerState.HALF_OPEN


class TestRateLimiter(TestCase):
    """Test rate limiter implementation."""

    @pytest.mark.asyncio
    async def test_token_consumption(self) -> None:
        """Test token consumption and replenishment."""
        config = RateLimitConfig(max_calls=3, time_window=1.0)
        limiter = RateLimiter(config)

        # Should allow initial calls
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True

        # Fourth call should fail
        assert await limiter.acquire() is False

    @pytest.mark.asyncio
    async def test_token_replenishment(self) -> None:
        """Test that tokens replenish over time."""
        config = RateLimitConfig(max_calls=2, time_window=0.2)
        limiter = RateLimiter(config)
        # Use all tokens
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        assert await limiter.acquire() is False

        # Wait for replenishment
        await asyncio.sleep(0.15)

        # Should have at least one token replenished
        assert await limiter.acquire() is True


class TestBulkhead(TestCase):
    """Test bulkhead isolation implementation."""

    @pytest.mark.asyncio
    async def test_concurrent_limit(self) -> None:
        """Test bulkhead concurrent call limits."""
        config = BulkheadConfig(max_concurrent_calls=2, max_queue_size=1)
        bulkhead = Bulkhead(config)

        # Acquire slots
        assert await bulkhead.acquire() is True
        assert await bulkhead.acquire() is True

        # Try to acquire when full
        result = await bulkhead.acquire()
        # Should fail as queue is limited
        assert result is False or bulkhead.queue_size > 0

    @pytest.mark.asyncio
    async def test_release_slot(self) -> None:
        """Test releasing bulkhead slots."""
        config = BulkheadConfig(max_concurrent_calls=1)
        bulkhead = Bulkhead(config)

        # Acquire the only slot
        assert await bulkhead.acquire() is True

        # Release it
        bulkhead.release()

        # Should be able to acquire again
        assert await bulkhead.acquire() is True


class TestRetryDecorator(TestCase):
    """Test retry decorator functionality."""

    def test_sync_retry_success(self) -> None:
        """Test sync function retry that eventually succeeds."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        def flaky_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_sync_retry_failure(self) -> None:
        """Test sync function that exceeds max attempts."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=2, initial_delay=0.01))
        def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            always_fails()

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_retry_success(self) -> None:
        """Test async function retry that eventually succeeds."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        async def async_flaky_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "async success"

        result = await async_flaky_function()
        assert result == "async success"
        assert call_count == 2

    def test_retryable_exceptions(self) -> None:
        """Test that only specified exceptions trigger retry."""
        call_count = 0

        @with_retry(
            RetryConfig(
                max_attempts=3, initial_delay=0.01, retryable_exceptions=[ValueError]
            )
        )
        def selective_retry() -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable")
            raise TypeError("Not retryable")

        # TypeError should not be retried
        with pytest.raises(TypeError, match="Not retryable"):
            selective_retry()

        # Should have tried twice (once for ValueError, once for TypeError)
        assert call_count == 2

    def test_retry_callback(self) -> None:
        """Test retry callback functionality."""
        retry_attempts = []

        def on_retry(_exception: Exception, attempt: int) -> None:
            # Use the exception parameter to avoid unused argument warning
            retry_attempts.append(attempt)

        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.01), on_retry=on_retry)
        def failing_function() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        assert len(retry_attempts) == 2  # Two retry attempts before final failure
        assert retry_attempts[0] == 1
        assert retry_attempts[1] == 2


class TestCircuitBreakerDecorator(TestCase):
    """Test circuit breaker decorator functionality."""

    def test_sync_circuit_breaker(self) -> None:
        """Test sync function with circuit breaker."""
        breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=2))
        call_count = 0

        @with_circuit_breaker(breaker)
        def protected_function() -> Any:
            nonlocal call_count
            call_count += 1
            raise ValueError("Service error")

        # First two calls should execute and fail
        for _ in range(2):
            with pytest.raises(ValueError):
                protected_function()

        assert call_count == 2
        assert breaker.state == CircuitBreakerState.OPEN
        # Next call should be rejected by circuit breaker
        with pytest.raises(AgentException, match="circuit breaker is open"):
            protected_function()

        # Call count shouldn't increase
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_with_fallback(self) -> None:
        """Test async function with circuit breaker and fallback."""
        breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1))
        main_calls = 0
        fallback_calls = 0

        async def fallback_function() -> Any:
            nonlocal fallback_calls
            fallback_calls += 1
            return "fallback result"

        @with_circuit_breaker(breaker, fallback=fallback_function)
        async def protected_async_function() -> Any:
            nonlocal main_calls
            main_calls += 1
            raise ValueError("Service error")

        # First call fails and opens circuit
        with pytest.raises(ValueError):
            await protected_async_function()

        assert main_calls == 1
        assert fallback_calls == 0
        # Circuit is now open, should use fallback
        result = await protected_async_function()
        assert result == "fallback result"
        assert main_calls == 1  # Main function not called
        assert fallback_calls == 1


class TestTimeoutDecorator(TestCase):
    """Test timeout decorator functionality."""

    @pytest.mark.asyncio
    async def test_timeout_success(self) -> None:
        """Test function that completes within timeout."""

        @with_timeout(0.1)
        async def fast_function() -> str:
            await asyncio.sleep(0.01)
            return "completed"

        result = await fast_function()
        assert result == "completed"

    @pytest.mark.asyncio
    async def test_timeout_failure(self) -> None:
        """Test function that exceeds timeout."""

        @with_timeout(0.05)
        async def slow_function() -> str:
            await asyncio.sleep(0.1)
            return "too late"

        with pytest.raises(AgentException, match="Operation timed out"):
            await slow_function()

    def test_timeout_sync_not_supported(self) -> None:
        """Test that timeout decorator rejects sync functions."""
        def sync_function() -> str:
            return "sync"
        with pytest.raises(ValueError, match="only supports async functions"):
            # Try to apply timeout decorator to sync function
            # Use Any cast to test error case
            decorator = with_timeout(1.0)
            cast(Any, decorator)(sync_function)


class TestRateLimitDecorator(TestCase):
    """Test rate limit decorator functionality."""

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self) -> None:
        """Test that rate limits are enforced."""
        limiter = RateLimiter(RateLimitConfig(max_calls=2, time_window=0.2))
        call_count = 0

        @with_rate_limit(limiter)
        async def rate_limited_function() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        # First two calls should succeed
        assert await rate_limited_function() == 1
        assert await rate_limited_function() == 2

        # Third call should fail
        with pytest.raises(AgentException, match="Rate limit exceeded"):
            await rate_limited_function()

        assert call_count == 2


class TestBulkheadDecorator(TestCase):
    """Test bulkhead decorator functionality."""

    @pytest.mark.asyncio
    async def test_bulkhead_isolation(self) -> None:
        """Test bulkhead isolation limits concurrent calls."""
        bulkhead = Bulkhead(BulkheadConfig(max_concurrent_calls=1))

        @with_bulkhead(bulkhead)
        async def isolated_function() -> str:
            await asyncio.sleep(0.05)
            return "done"

        # Start first call
        coro = isolated_function()
        task1: asyncio.Task[Any] = asyncio.create_task(cast(Any, coro))

        # Give it time to acquire the bulkhead
        await asyncio.sleep(0.01)

        # Second call should fail immediately
        with pytest.raises(AgentException, match="Service at capacity"):
            await isolated_function()

        # First call should complete
        result = await task1
        assert result == "done"


class TestRecoveryManager(TestCase):
    """Test recovery manager functionality."""

    def test_get_circuit_breaker(self) -> None:
        """Test getting circuit breakers from manager."""
        manager = RecoveryManager()

        # Get new circuit breaker
        breaker1 = manager.get_circuit_breaker("service1")
        assert isinstance(breaker1, CircuitBreaker)

        # Get same circuit breaker
        breaker2 = manager.get_circuit_breaker("service1")
        assert breaker1 is breaker2

        # Get different circuit breaker
        breaker3 = manager.get_circuit_breaker("service2")
        assert breaker3 is not breaker1

    def test_get_rate_limiter(self) -> None:
        """Test getting rate limiters from manager."""
        manager = RecoveryManager()

        # Get new rate limiter
        limiter1 = manager.get_rate_limiter("api1")
        assert isinstance(limiter1, RateLimiter)

        # Get same rate limiter
        limiter2 = manager.get_rate_limiter("api1")
        assert limiter1 is limiter2

    def test_get_bulkhead(self) -> None:
        """Test getting bulkheads from manager."""
        manager = RecoveryManager()
        # Get new bulkhead
        bulkhead1 = manager.get_bulkhead("worker1")
        assert isinstance(bulkhead1, Bulkhead)

        # Get same bulkhead
        bulkhead2 = manager.get_bulkhead("worker1")
        assert bulkhead1 is bulkhead2

    def test_apply_multiple_strategies_sync(self) -> None:
        """Test applying multiple recovery strategies to sync function."""
        manager = RecoveryManager()
        call_count = 0

        def test_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"

        # Apply retry and circuit breaker
        wrapped = manager.apply_recovery_strategies(
            test_function,
            [RecoveryStrategy.RETRY, RecoveryStrategy.CIRCUIT_BREAKER],
            retry_config=RetryConfig(max_attempts=3, initial_delay=0.01),
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5),
        )

        result = wrapped()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_apply_multiple_strategies_async(self) -> None:
        """Test applying multiple recovery strategies to async function."""
        manager = RecoveryManager()
        call_count = 0

        async def async_test_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(0.2)  # Will timeout
            return "success"

        # Apply timeout and retry
        wrapped = manager.apply_recovery_strategies(
            async_test_function,
            [RecoveryStrategy.TIMEOUT, RecoveryStrategy.RETRY],
            timeout=0.1,
            retry_config=RetryConfig(max_attempts=2, initial_delay=0.01),
        )

        result = await wrapped()
        assert result == "success"
        assert call_count == 2  # First attempt timed out, second succeeded


class TestGlobalRecoveryManager(TestCase):
    """Test global recovery manager functionality."""

    def test_get_recovery_manager(self) -> None:
        """Test getting global recovery manager."""
        manager1 = get_recovery_manager()
        manager2 = get_recovery_manager()
        assert isinstance(manager1, RecoveryManager)
        assert manager1 is manager2  # Should be singleton


class TestRecoverableAgentMethod(TestCase):
    """Test recoverable agent method decorator."""

    @pytest.mark.asyncio
    async def test_recoverable_agent_method_decorator(self) -> None:
        """Test recoverable agent method with multiple strategies."""
        call_count = 0

        @recoverable_agent_method(
            strategies=[RecoveryStrategy.RETRY, RecoveryStrategy.CIRCUIT_BREAKER],
            retry_config=RetryConfig(max_attempts=3, initial_delay=0.01),
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=10),
        )
        async def agent_method(agent_self: object, value: str) -> str:
            nonlocal call_count
            call_count += 1
            # Use the agent_self parameter to avoid unused argument warning
            assert agent_self is not None
            if call_count < 2:
                raise ValueError("Temporary agent error")
            return f"processed: {value}"

        # Create a dummy self object
        class DummyAgent:
            pass

        agent = DummyAgent()
        result = await agent_method(agent, "test_value")
        assert result == "processed: test_value"
        assert call_count == 2

    def test_recoverable_agent_method_default_strategy(self) -> None:
        """Test recoverable agent method with default retry strategy."""
        call_count = 0

        @recoverable_agent_method()
        def simple_agent_method(agent_self: object) -> str:
            nonlocal call_count
            call_count += 1
            # Use the agent_self parameter to avoid unused argument warning
            assert agent_self is not None
            if call_count == 1:
                raise ValueError("First attempt fails")
            return "success"

        class DummyAgent:
            pass

        agent = DummyAgent()
        result = simple_agent_method(agent)
        assert result == "success"
        assert call_count == 2  # Default retry strategy applied


class TestEdgeCases(TestCase):
    """Test edge cases and error conditions."""

    def test_retry_with_no_jitter(self) -> None:
        """Test retry delay calculation without jitter."""
        config = RetryConfig(initial_delay=1.0, max_delay=10.0, jitter=False)

        @with_retry(config)
        def test_func() -> None:
            raise ValueError("Always fails")

        start_time = time.time()
        with pytest.raises(ValueError):
            test_func()
        # With 3 attempts and delays of 1s and 2s, total time should be ~3s
        elapsed = time.time() - start_time
        assert 2.8 < elapsed < 3.5  # Allow some margin

    def test_max_delay_cap(self) -> None:
        """Test that retry delay is capped at max_delay."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=1.0,
            max_delay=2.0,
            exponential_base=10.0,  # Would grow very fast
            jitter=False,
        )

        delays = []

        def on_retry(exception: Exception, attempt: int) -> None:
            _ = exception  # Mark exception as used to avoid unused argument warning
            if attempt > 1:
                delays.append(time.time())

        @with_retry(config, on_retry=on_retry)
        def test_func() -> None:
            delays.append(time.time())
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            test_func()

        # Check that delays don't exceed max_delay
        for i in range(1, len(delays) - 1):
            delay = delays[i + 1] - delays[i]
            assert delay <= 2.5  # Max delay + small margin

    def test_async_only_decorators_with_sync_functions(self) -> None:
        """Test that async-only decorators reject sync functions properly."""
        manager = RecoveryManager()

        def sync_function() -> str:
            return "sync result"

        # Rate limit should skip for sync functions
        wrapped = manager.apply_recovery_strategies(
            sync_function,
            [RecoveryStrategy.RATE_LIMIT],
            rate_limit_config=RateLimitConfig(),
        )
        # Should work but without rate limiting
        assert wrapped() == "sync result"

        # Timeout should skip for sync functions
        wrapped = manager.apply_recovery_strategies(
            sync_function, [RecoveryStrategy.TIMEOUT], timeout=5.0
        )
        # Should work but without timeout
        assert wrapped() == "sync result"

        # Bulkhead should skip for sync functions
        wrapped = manager.apply_recovery_strategies(
            sync_function, [RecoveryStrategy.BULKHEAD], bulkhead_config=BulkheadConfig()
        )
        # Should work but without bulkhead
        assert wrapped() == "sync result"

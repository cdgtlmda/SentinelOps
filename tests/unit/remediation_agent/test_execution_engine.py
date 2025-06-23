"""
Tests for the Action Execution Engine.

Tests all components with actual project behavior - no mocks.
"""

import asyncio
import time
from datetime import datetime, timezone
from unittest import TestCase

import pytest

from src.common.models import RemediationAction
from src.remediation_agent.action_registry import ActionRiskLevel
from src.remediation_agent.execution_engine import (
    ActionQueue,
    ConcurrencyController,
    ExecutionMonitor,
    ExecutionPriority,
    ExecutionResult,
    PrioritizedAction,
    RateLimiter,
    RetryPolicy,
    determine_action_priority,
)


class TestExecutionPriority(TestCase):
    """Test ExecutionPriority enum."""

    def test_priority_values(self) -> None:
        """Test that priority values are correctly ordered."""
        self.assertEqual(ExecutionPriority.CRITICAL.value, 1)
        self.assertEqual(ExecutionPriority.HIGH.value, 2)
        self.assertEqual(ExecutionPriority.MEDIUM.value, 3)
        self.assertEqual(ExecutionPriority.LOW.value, 4)
        self.assertEqual(ExecutionPriority.BACKGROUND.value, 5)

    def test_priority_comparison(self) -> None:
        """Test that higher priority (lower value) comes first."""
        self.assertLess(ExecutionPriority.CRITICAL.value, ExecutionPriority.HIGH.value)
        self.assertLess(ExecutionPriority.HIGH.value, ExecutionPriority.MEDIUM.value)


class TestExecutionResult(TestCase):
    """Test ExecutionResult enum."""

    def test_result_values(self) -> None:
        """Test all execution result values."""
        self.assertEqual(ExecutionResult.SUCCESS.value, "success")
        self.assertEqual(ExecutionResult.FAILED.value, "failed")
        self.assertEqual(ExecutionResult.TIMEOUT.value, "timeout")
        self.assertEqual(ExecutionResult.VALIDATION_FAILED.value, "validation_failed")
        self.assertEqual(ExecutionResult.RESOURCE_NOT_FOUND.value, "resource_not_found")
        self.assertEqual(ExecutionResult.PERMISSION_DENIED.value, "permission_denied")
        self.assertEqual(ExecutionResult.RATE_LIMITED.value, "rate_limited")


class TestRetryPolicy(TestCase):
    """Test RetryPolicy class."""

    def test_default_initialization(self) -> None:
        """Test default retry policy initialization."""
        policy = RetryPolicy()
        self.assertEqual(policy.max_retries, 3)
        self.assertEqual(policy.initial_delay, 1.0)
        self.assertEqual(policy.max_delay, 60.0)
        self.assertEqual(policy.exponential_base, 2.0)

    def test_custom_initialization(self) -> None:
        """Test custom retry policy initialization."""
        policy = RetryPolicy(
            max_retries=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0
        )
        self.assertEqual(policy.max_retries, 5)
        self.assertEqual(policy.initial_delay, 2.0)
        self.assertEqual(policy.max_delay, 120.0)
        self.assertEqual(policy.exponential_base, 3.0)

    def test_get_retry_delay(self) -> None:
        """Test retry delay calculation with exponential backoff."""
        policy = RetryPolicy(initial_delay=1.0, exponential_base=2.0, max_delay=10.0)

        # First retry
        delay1 = policy.get_retry_delay(0)
        self.assertGreaterEqual(delay1, 1.0)  # Base delay
        self.assertLessEqual(delay1, 1.1)  # Base + max jitter

        # Second retry
        delay2 = policy.get_retry_delay(1)
        self.assertGreaterEqual(delay2, 2.0)  # 1 * 2^1
        self.assertLessEqual(delay2, 2.2)  # With jitter

        # Test max delay cap
        delay_max = policy.get_retry_delay(10)
        self.assertLessEqual(delay_max, 11.0)  # Max delay + jitter

    def test_is_retryable(self) -> None:
        """Test retryable error detection."""
        policy = RetryPolicy()

        # Retryable errors
        self.assertTrue(policy.is_retryable(TimeoutError("timeout")))
        self.assertTrue(policy.is_retryable(ConnectionError("connection failed")))

        # Retryable by message
        self.assertTrue(policy.is_retryable(Exception("Request timeout")))
        self.assertTrue(policy.is_retryable(Exception("Rate limit exceeded")))
        self.assertTrue(policy.is_retryable(Exception("Temporarily unavailable")))

        # Non-retryable
        self.assertFalse(policy.is_retryable(ValueError("invalid value")))
        self.assertFalse(policy.is_retryable(KeyError("missing key")))

    def test_should_retry(self) -> None:
        """Test retry decision logic."""
        policy = RetryPolicy(max_retries=3)
        timeout_error = TimeoutError("timeout")
        value_error = ValueError("invalid")

        # Should retry for retryable errors within limit
        self.assertTrue(policy.should_retry(0, timeout_error))
        self.assertTrue(policy.should_retry(2, timeout_error))

        # Should not retry after max attempts
        self.assertFalse(policy.should_retry(3, timeout_error))

        # Should not retry non-retryable errors
        self.assertFalse(policy.should_retry(0, value_error))


class TestPrioritizedAction(TestCase):
    """Test PrioritizedAction dataclass."""

    def test_prioritized_action_creation(self) -> None:
        """Test creating a prioritized action."""
        action = RemediationAction(
            action_id="test-123",
            action_type="block_ip_address",
            incident_id="inc-456",
            params={"ip": "192.168.1.1"}
        )

        now = datetime.now(timezone.utc)
        prioritized = PrioritizedAction(
            priority=ExecutionPriority.HIGH.value,
            timestamp=now,
            action=action
        )

        self.assertEqual(prioritized.priority, 2)
        self.assertEqual(prioritized.timestamp, now)
        self.assertEqual(prioritized.action.action_id, "test-123")

    def test_prioritized_action_ordering(self) -> None:
        """Test that prioritized actions are ordered by priority value."""
        action1 = RemediationAction(action_id="1", action_type="test", incident_id="inc-1", params={})
        action2 = RemediationAction(action_id="2", action_type="test", incident_id="inc-2", params={})

        now = datetime.now(timezone.utc)
        high_priority = PrioritizedAction(ExecutionPriority.HIGH.value, now, action1)
        critical_priority = PrioritizedAction(ExecutionPriority.CRITICAL.value, now, action2)

        # Critical (1) should come before High (2)
        self.assertLess(critical_priority, high_priority)


@pytest.mark.asyncio
class TestActionQueue:
    """Test ActionQueue class."""

    async def test_queue_initialization(self) -> None:
        """Test queue initialization."""
        queue = ActionQueue()
        assert queue._queue is not None
        assert len(queue._queue) == 0
        assert len(queue._pending_actions) == 0
        assert len(queue._completed_actions) == 0

    async def test_enqueue_dequeue(self) -> None:
        """Test basic enqueue and dequeue operations."""
        queue = ActionQueue()

        action = RemediationAction(
            action_id="test-123",
            action_type="block_ip_address",
            incident_id="inc-456",
            params={"ip": "192.168.1.1"}
        )

        # Enqueue action
        await queue.enqueue(action, ExecutionPriority.HIGH)
        stats = await queue.get_queue_stats()
        assert stats["total_pending"] == 1

        # Dequeue action
        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.action_id == "test-123"

        # Check completed
        stats = await queue.get_queue_stats()
        assert stats["total_pending"] == 0
        assert stats["total_completed"] == 1

    async def test_priority_ordering(self) -> None:
        """Test that actions are dequeued in priority order."""
        queue = ActionQueue()

        # Create actions with different priorities
        actions = [
            RemediationAction(action_id="low", action_type="test", incident_id="inc-1", params={}),
            RemediationAction(action_id="critical", action_type="test", incident_id="inc-2", params={}),
            RemediationAction(action_id="medium", action_type="test", incident_id="inc-3", params={}),
        ]

        # Enqueue in random order
        await queue.enqueue(actions[0], ExecutionPriority.LOW)
        await queue.enqueue(actions[1], ExecutionPriority.CRITICAL)
        await queue.enqueue(actions[2], ExecutionPriority.MEDIUM)

        # Dequeue should be in priority order
        first = await queue.dequeue()
        assert first is not None
        assert first.action_id == "critical"

        second = await queue.dequeue()
        assert second is not None
        assert second.action_id == "medium"

        third = await queue.dequeue()
        assert third is not None
        assert third.action_id == "low"

    async def test_duplicate_enqueue(self) -> None:
        """Test that duplicate actions are not enqueued."""
        queue = ActionQueue()

        action = RemediationAction(
            action_id="test-123",
            action_type="test",
            incident_id="inc-1",
            params={}
        )

        # First enqueue should succeed
        await queue.enqueue(action)
        stats = await queue.get_queue_stats()
        assert stats["total_pending"] == 1

        # Second enqueue should be ignored
        await queue.enqueue(action)
        stats = await queue.get_queue_stats()
        assert stats["total_pending"] == 1

    async def test_remove_action(self) -> None:
        """Test removing a specific action from queue."""
        queue = ActionQueue()

        action1 = RemediationAction(action_id="1", action_type="test", incident_id="inc-1", params={})
        action2 = RemediationAction(action_id="2", action_type="test", incident_id="inc-2", params={})

        await queue.enqueue(action1)
        await queue.enqueue(action2)

        # Remove action1
        removed = await queue.remove("1")
        assert removed is True

        # Only action2 should remain
        stats = await queue.get_queue_stats()
        assert stats["total_pending"] == 1

        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.action_id == "2"

    async def test_peek(self) -> None:
        """Test peeking at next action without removing."""
        queue = ActionQueue()

        action = RemediationAction(action_id="test", action_type="test", incident_id="inc-1", params={})
        await queue.enqueue(action)

        # Peek should return action without removing
        peeked = await queue.peek()
        assert peeked is not None
        assert peeked.action_id == "test"

        # Queue should still have the action
        stats = await queue.get_queue_stats()
        assert stats["total_pending"] == 1


@pytest.mark.asyncio
class TestRateLimiter:
    """Test RateLimiter class."""

    async def test_rate_limiter_initialization(self) -> None:
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_calls_per_window=10, window_seconds=60)
        assert limiter.max_calls == 10
        assert limiter.window_seconds == 60
        assert len(limiter._call_times) == 0

    async def test_acquire_within_limit(self) -> None:
        """Test acquiring within rate limit."""
        limiter = RateLimiter(max_calls_per_window=5, window_seconds=1)

        # Should be able to make 5 calls quickly
        start = time.time()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.time() - start

        # Should complete quickly (no waiting)
        assert elapsed < 0.1

    async def test_acquire_exceeds_limit(self) -> None:
        """Test that exceeding limit causes wait."""
        limiter = RateLimiter(max_calls_per_window=2, window_seconds=1)

        # Make 2 calls
        await limiter.acquire()
        await limiter.acquire()

        # Third call should wait
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start


        # Should have waited approximately 1 second
        assert elapsed >= 0.9

    async def test_get_current_rate(self) -> None:
        """Test getting current call rate."""
        limiter = RateLimiter(max_calls_per_window=10, window_seconds=2)

        # Initially zero
        rate = await limiter.get_current_rate()
        assert rate == 0.0

        # Make some calls
        await limiter.acquire()
        await limiter.acquire()
        await asyncio.sleep(0.1)

        # Check rate
        rate = await limiter.get_current_rate()
        assert rate > 0


@pytest.mark.asyncio
class TestConcurrencyController:
    """Test ConcurrencyController class."""

    async def test_controller_initialization(self) -> None:
        """Test concurrency controller initialization."""
        controller = ConcurrencyController(
            max_concurrent_actions=5,
            max_per_resource_type={"compute": 2, "network": 3}
        )

        assert controller.max_concurrent == 5
        assert controller.max_per_type["compute"] == 2
        assert controller.max_per_type["network"] == 3

    async def test_acquire_release(self) -> None:
        """Test acquiring and releasing execution slots."""
        controller = ConcurrencyController(max_concurrent_actions=2)

        action1 = RemediationAction(
            action_id="1",
            action_type="stop_instance",
            incident_id="inc-1",
            params={}
        )
        action2 = RemediationAction(
            action_id="2",
            action_type="block_ip_address",
            incident_id="inc-2",
            params={}
        )

        # Acquire slots
        acquired1 = await controller.acquire(action1)
        assert acquired1 is True
        assert controller.current_count == 1

        acquired2 = await controller.acquire(action2)
        assert acquired2 is True
        assert controller.current_count == 2

        # Release one slot
        await controller.release(action1)
        assert controller.current_count == 1


    async def test_resource_type_limits(self) -> None:
        """Test per-resource-type concurrency limits."""
        controller = ConcurrencyController(
            max_concurrent_actions=10,
            max_per_resource_type={"compute": 2}
        )

        # Create 3 compute actions
        actions = [
            RemediationAction(
                action_id=str(i),
                action_type="stop_instance",  # compute type
                incident_id=f"inc-{i}",
                params={}
            )
            for i in range(3)
        ]

        # First two should succeed
        assert await controller.acquire(actions[0]) is True
        assert await controller.acquire(actions[1]) is True

        # Third should fail (compute limit reached)
        assert await controller.acquire(actions[2]) is False

        # Release one and try again
        await controller.release(actions[0])
        assert await controller.acquire(actions[2]) is True

    async def test_get_status(self) -> None:
        """Test getting controller status."""
        controller = ConcurrencyController(max_concurrent_actions=5)

        action = RemediationAction(
            action_id="test",
            action_type="block_ip_address",
            incident_id="inc-1",
            params={}
        )

        # Check initial status
        status = await controller.get_status()
        assert status["active_actions"] == 0
        assert status["max_concurrent"] == 5
        assert status["available_slots"] == 5

        # Acquire and check again
        await controller.acquire(action)
        status = await controller.get_status()
        assert status["active_actions"] == 1
        assert status["available_slots"] == 4


class TestExecutionMonitor(TestCase):
    """Test ExecutionMonitor class (sync tests for simplicity)."""

    def test_monitor_initialization(self) -> None:
        """Test execution monitor initialization."""
        monitor = ExecutionMonitor(timeout_seconds=300, check_interval=10)
        self.assertEqual(monitor.timeout_seconds, 300)
        self.assertEqual(monitor.check_interval, 10)
        self.assertEqual(len(monitor._executions), 0)

    def test_start_stop_monitoring(self) -> None:
        """Test starting and stopping monitoring."""
        monitor = ExecutionMonitor(timeout_seconds=5)

        # Start monitoring
        monitor.start_monitoring_sync("exec-1")
        self.assertEqual(len(monitor.active_executions), 1)
        self.assertIn("exec-1", monitor.active_executions)

        # Stop monitoring
        monitor.complete_execution("exec-1")
        self.assertEqual(len(monitor.active_executions), 0)

    def test_timeout_detection(self) -> None:
        """Test timeout detection."""
        monitor = ExecutionMonitor(timeout_seconds=1)  # 1 second timeout

        # Start monitoring
        monitor.start_monitoring_sync("exec-1")

        # Initially not timed out
        self.assertFalse(monitor.check_timeout("exec-1"))

        # Wait for timeout
        time.sleep(0.2)

        # Should now be timed out
        self.assertTrue(monitor.check_timeout("exec-1"))
        self.assertEqual(monitor.active_executions["exec-1"]["status"], "timed_out")


@pytest.mark.asyncio
class TestExecutionMonitorAsync:
    """Test ExecutionMonitor async methods."""

    async def test_async_monitoring(self) -> None:
        """Test async monitoring methods."""
        monitor = ExecutionMonitor()

        action = RemediationAction(
            action_id="test-123",
            action_type="block_ip_address",
            incident_id="inc-456",
            params={}
        )

        # Start monitoring
        await monitor.start_monitoring(action)

        # Check stats
        stats = await monitor.get_execution_stats()
        assert stats["active_executions"] == 1
        assert stats["by_status"]["executing"] == 1

        # Stop monitoring
        await monitor.stop_monitoring("test-123")
        stats = await monitor.get_execution_stats()
        assert stats["active_executions"] == 0

    async def test_check_timeouts_async(self) -> None:
        """Test async timeout checking."""
        monitor = ExecutionMonitor(timeout_seconds=1)


        action = RemediationAction(
            action_id="test-timeout",
            action_type="test",
            incident_id="inc-1",
            params={}
        )

        await monitor.start_monitoring(action)

        # Wait for timeout
        await asyncio.sleep(0.2)

        # Check for timeouts
        timed_out = await monitor.check_timeouts()
        assert len(timed_out) == 1
        assert "test-timeout" in timed_out


class TestDetermineActionPriority(TestCase):
    """Test determine_action_priority function."""

    def test_critical_actions(self) -> None:
        """Test that critical actions get CRITICAL priority."""
        critical_types = [
            "block_ip_address",
            "disable_user_account",
            "quarantine_instance",
            "revoke_api_key"
        ]

        for action_type in critical_types:
            action = RemediationAction(
                action_id="test",
                action_type=action_type,
                incident_id="inc-1",
                params={}
            )
            priority = determine_action_priority(action)
            self.assertEqual(priority, ExecutionPriority.CRITICAL)

    def test_high_priority_actions(self) -> None:
        """Test that high priority actions get HIGH priority."""
        high_types = [
            "rotate_credentials",
            "revoke_iam_permission",
            "remove_service_account_key"
        ]

        for action_type in high_types:
            action = RemediationAction(
                action_id="test",
                action_type=action_type,
                incident_id="inc-1",
                params={}
            )
            priority = determine_action_priority(action)
            self.assertEqual(priority, ExecutionPriority.HIGH)

    def test_low_priority_actions(self) -> None:
        """Test that low priority actions get LOW priority."""
        low_types = [
            "enable_additional_logging",
            "snapshot_instance",
            "enable_bucket_versioning"
        ]


        for action_type in low_types:
            action = RemediationAction(
                action_id="test",
                action_type=action_type,
                incident_id="inc-1",
                params={}
            )
            priority = determine_action_priority(action)
            self.assertEqual(priority, ExecutionPriority.LOW)

    def test_risk_level_priority(self) -> None:
        """Test priority based on risk level."""
        action = RemediationAction(
            action_id="test",
            action_type="unknown_action",
            incident_id="inc-1",
            params={}
        )

        # Critical risk level
        priority = determine_action_priority(action, ActionRiskLevel.CRITICAL)
        self.assertEqual(priority, ExecutionPriority.HIGH)

        # Low risk level
        priority = determine_action_priority(action, ActionRiskLevel.LOW)
        self.assertEqual(priority, ExecutionPriority.LOW)

        # Medium risk level (default)
        priority = determine_action_priority(action, ActionRiskLevel.MEDIUM)
        self.assertEqual(priority, ExecutionPriority.MEDIUM)

    def test_default_priority(self) -> None:
        """Test default priority for unknown actions."""
        action = RemediationAction(
            action_id="test",
            action_type="some_unknown_action",
            incident_id="inc-1",
            params={}
        )

        priority = determine_action_priority(action)
        self.assertEqual(priority, ExecutionPriority.MEDIUM)

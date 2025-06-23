"""
Action Execution Engine for the Remediation Agent.

This module provides the execution framework including queuing, priority-based
execution, concurrent action handling, and rate limiting.
"""

import asyncio
import heapq
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from google.api_core import exceptions as google_exceptions

from src.common.exceptions import GoogleCloudError
from src.common.models import RemediationAction
from src.remediation_agent.action_registry import ActionRiskLevel


class ExecutionPriority(Enum):
    """Priority levels for action execution."""

    CRITICAL = 1  # Highest priority
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5  # Lowest priority


class ExecutionResult(Enum):
    """Result status for action execution."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    VALIDATION_FAILED = "validation_failed"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMITED = "rate_limited"


class RetryPolicy:
    """Policy for retrying failed actions."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """
        Initialize retry policy.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt.

        Args:
            attempt: Retry attempt number (0-based)

        Returns:
            Delay in seconds
        """
        import random

        # Calculate exponential backoff with jitter
        delay = min(
            self.initial_delay * (self.exponential_base**attempt), self.max_delay
        )
        # Add jitter to prevent thundering herd
        jitter = delay * 0.1 * random.random()
        return delay + jitter

    def is_retryable(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.

        Args:
            error: The exception to check

        Returns:
            True if the error is retryable, False otherwise
        """
        # Transient errors that should be retried
        retryable_types = (
            TimeoutError,
            ConnectionError,
            google_exceptions.ResourceExhausted,
            GoogleCloudError,
        )

        # Check if it's a known retryable error type
        if isinstance(error, retryable_types):
            return True

        # Check for specific error messages
        error_msg = str(error).lower()
        retryable_patterns = [
            "timeout",
            "connection",
            "temporarily unavailable",
            "rate limit",
            "quota exceeded",
        ]

        return any(pattern in error_msg for pattern in retryable_patterns)

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """
        Determine if an action should be retried.

        Args:
            attempt: Current attempt number (0-based)
            error: The exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        # Check if we've exceeded max retries
        if attempt >= self.max_retries:
            return False

        # Check if the error is retryable
        return self.is_retryable(error)


@dataclass(order=True)
class PrioritizedAction:
    """Wrapper for actions with priority ordering."""

    priority: int
    timestamp: datetime = field(compare=False)
    action: RemediationAction = field(compare=False)

    def __post_init__(self) -> None:
        """Ensure proper ordering (lower priority value = higher priority)."""


class ActionQueue:
    """Priority queue for remediation actions."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the action queue.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._queue: List[PrioritizedAction] = []
        self._lock = asyncio.Lock()
        self._pending_actions: Dict[str, PrioritizedAction] = {}
        self._completed_actions: Set[str] = set()

    async def enqueue(
        self,
        action: RemediationAction,
        priority: ExecutionPriority = ExecutionPriority.MEDIUM,
    ) -> None:
        """
        Add an action to the queue.

        Args:
            action: The remediation action to enqueue
            priority: Execution priority
        """
        async with self._lock:
            # Check if action is already queued or completed
            if action.action_id in self._pending_actions:
                self.logger.warning("Action %s already in queue", action.action_id)
                return

            if action.action_id in self._completed_actions:
                self.logger.warning("Action %s already completed", action.action_id)
                return

            # Create prioritized action
            prioritized_action = PrioritizedAction(
                priority=priority.value,
                timestamp=datetime.now(timezone.utc),
                action=action,
            )

            # Add to queue
            heapq.heappush(self._queue, prioritized_action)
            self._pending_actions[action.action_id] = prioritized_action

            self.logger.info(
                "Enqueued action %s (%s) with priority %s",
                action.action_id,
                action.action_type,
                priority.name,
            )

    async def dequeue(self) -> Optional[RemediationAction]:
        """
        Get the next action from the queue.

        Returns:
            Next action to execute or None if queue is empty
        """
        async with self._lock:
            if not self._queue:
                return None

            prioritized_action = heapq.heappop(self._queue)
            action = prioritized_action.action

            # Remove from pending
            if action.action_id in self._pending_actions:
                del self._pending_actions[action.action_id]

            # Add to completed
            self._completed_actions.add(action.action_id)

            self.logger.debug(f"Dequeued action {action.action_id}")

            return action

    async def peek(self) -> Optional[RemediationAction]:
        """
        Peek at the next action without removing it.

        Returns:
            Next action or None if queue is empty
        """
        async with self._lock:
            if not self._queue:
                return None
            return self._queue[0].action

    async def remove(self, action_id: str) -> bool:
        """
        Remove a specific action from the queue.

        Args:
            action_id: ID of the action to remove

        Returns:
            True if action was removed, False otherwise
        """
        async with self._lock:
            if action_id not in self._pending_actions:
                return False

            # Remove from pending
            del self._pending_actions[action_id]

            # Rebuild queue without the action
            self._queue = [pa for pa in self._queue if pa.action.action_id != action_id]
            heapq.heapify(self._queue)

            self.logger.info(f"Removed action {action_id} from queue")

            return True

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        async with self._lock:
            priority_counts: Dict[str, int] = {}
            for pa in self._queue:
                priority_name = ExecutionPriority(pa.priority).name
                priority_counts[priority_name] = (
                    priority_counts.get(priority_name, 0) + 1
                )

            return {
                "total_pending": len(self._queue),
                "total_completed": len(self._completed_actions),
                "priority_breakdown": priority_counts,
                "oldest_action_age": (
                    (
                        datetime.now(timezone.utc)
                        - min(pa.timestamp for pa in self._queue)
                    ).total_seconds()
                    if self._queue
                    else 0
                ),
            }


class RateLimiter:
    """Rate limiter for API calls and action execution."""

    def __init__(
        self,
        max_calls_per_window: int = 60,
        window_seconds: int = 60,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the rate limiter.

        Args:
            max_calls_per_window: Maximum calls allowed per window
            window_seconds: Window duration in seconds
            logger: Logger instance
        """
        self.max_calls = max_calls_per_window
        self.window_seconds = window_seconds
        self.logger = logger or logging.getLogger(__name__)

        self._call_times: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to make a call.

        Blocks if rate limit would be exceeded.
        """
        async with self._lock:
            now = time.time()

            # Remove old calls outside the window
            cutoff_time = now - self.window_seconds
            self._call_times = [t for t in self._call_times if t > cutoff_time]

            # Check if we need to wait
            if len(self._call_times) >= self.max_calls:
                # Calculate wait time
                oldest_call = self._call_times[0]
                wait_time = oldest_call + self.window_seconds - now

                if wait_time > 0:
                    self.logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)

                    # Clean up again after waiting
                    now = time.time()
                    cutoff_time = now - self.window_seconds
                    self._call_times = [t for t in self._call_times if t > cutoff_time]

            # Record this call
            self._call_times.append(now)

    async def get_current_rate(self) -> float:
        """
        Get the current call rate.

        Returns:
            Calls per second in the current window
        """
        async with self._lock:
            now = time.time()
            cutoff_time = now - self.window_seconds
            recent_calls = [t for t in self._call_times if t > cutoff_time]

            if not recent_calls:
                return 0.0

            time_span = now - min(recent_calls)
            if time_span == 0:
                return 0.0

            return len(recent_calls) / time_span


class ConcurrencyController:
    """Controls concurrent execution of actions."""

    def __init__(
        self,
        max_concurrent_actions: int = 5,
        max_per_resource_type: Optional[Dict[str, int]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the concurrency controller.

        Args:
            max_concurrent_actions: Maximum total concurrent actions
            max_per_resource_type: Maximum concurrent actions per resource type
            logger: Logger instance
        """
        self.max_concurrent = max_concurrent_actions
        self.max_per_type = max_per_resource_type or {}
        self.logger = logger or logging.getLogger(__name__)

        self._active_actions: Dict[str, RemediationAction] = {}
        self._actions_by_type: Dict[str, Set[str]] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent_actions)
        self._type_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._lock = asyncio.Lock()

        # Create semaphores for each resource type limit
        for resource_type, limit in self.max_per_type.items():
            self._type_semaphores[resource_type] = asyncio.Semaphore(limit)

    async def acquire(self, action: RemediationAction) -> bool:
        """
        Acquire permission to execute an action.

        Args:
            action: The action to execute

        Returns:
            True if acquired, False if would exceed limits
        """
        # Determine resource type
        resource_type = self._get_resource_type(action)

        # Check if we can acquire global semaphore
        if not self._semaphore.locked() or self._semaphore._value > 0:
            # Check type-specific semaphore if applicable
            if resource_type in self._type_semaphores:
                type_sem = self._type_semaphores[resource_type]
                if type_sem.locked() and type_sem._value == 0:
                    self.logger.warning(
                        f"Cannot execute action: {resource_type} concurrency limit reached"
                    )
                    return False

            # Acquire semaphores
            await self._semaphore.acquire()

            if resource_type in self._type_semaphores:
                await self._type_semaphores[resource_type].acquire()

            # Track active action
            async with self._lock:
                self._active_actions[action.action_id] = action

                if resource_type not in self._actions_by_type:
                    self._actions_by_type[resource_type] = set()
                self._actions_by_type[resource_type].add(action.action_id)

            self.logger.debug(
                "Acquired execution slot for action %s (type: %s)",
                action.action_id,
                resource_type,
            )

            return True
        else:
            self.logger.warning(
                "Cannot execute action: global concurrency limit reached"
            )
            return False

    async def release(self, action: RemediationAction) -> None:
        """
        Release execution slot for an action.

        Args:
            action: The completed action
        """
        resource_type = self._get_resource_type(action)

        # Remove from tracking
        async with self._lock:
            if action.action_id in self._active_actions:
                del self._active_actions[action.action_id]

            if resource_type in self._actions_by_type:
                self._actions_by_type[resource_type].discard(action.action_id)

        # Release semaphores
        self._semaphore.release()

        if resource_type in self._type_semaphores:
            self._type_semaphores[resource_type].release()

        self.logger.debug(f"Released execution slot for action {action.action_id}")

    def _get_resource_type(self, action: RemediationAction) -> str:
        """Get the resource type from an action."""
        # Map action types to resource types
        action_to_resource = {
            "stop_instance": "compute",
            "snapshot_instance": "compute",
            "quarantine_instance": "compute",
            "block_ip_address": "network",
            "update_firewall_rule": "network",
            "disable_user_account": "iam",
            "revoke_iam_permission": "iam",
            "update_bucket_permissions": "storage",
            "enable_bucket_versioning": "storage",
        }

        return action_to_resource.get(action.action_type, "other")

    async def get_status(self) -> Dict[str, Any]:
        """Get concurrency controller status."""
        async with self._lock:
            return {
                "active_actions": len(self._active_actions),
                "max_concurrent": self.max_concurrent,
                "available_slots": self._semaphore._value,
                "actions_by_type": {
                    rtype: len(actions)
                    for rtype, actions in self._actions_by_type.items()
                },
                "type_limits": self.max_per_type,
            }

    @property
    def current_count(self) -> int:
        """Get the current count of active actions."""
        return len(self._active_actions)


class ExecutionMonitor:
    """Monitors action execution for timeouts and issues."""

    def __init__(
        self,
        timeout_seconds: int = 300,
        check_interval: int = 10,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the execution monitor.

        Args:
            timeout_seconds: Default timeout for actions
            check_interval: How often to check for timeouts
            logger: Logger instance
        """
        self.timeout_seconds = timeout_seconds
        self.check_interval = check_interval
        self.logger = logger or logging.getLogger(__name__)

        self._executions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._monitoring_task: Optional[asyncio.Task[Any]] = None

    async def start_monitoring(self, action: RemediationAction) -> None:
        """
        Start monitoring an action execution.

        Args:
            action: The action being executed
        """
        async with self._lock:
            self._executions[action.action_id] = {
                "action": action,
                "start_time": datetime.now(timezone.utc),
                "timeout": self.timeout_seconds,
                "status": "executing",
            }

        self.logger.debug(f"Started monitoring action {action.action_id}")

    async def stop_monitoring(self, action_id: str) -> None:
        """
        Stop monitoring an action.

        Args:
            action_id: ID of the action
        """
        async with self._lock:
            if action_id in self._executions:
                del self._executions[action_id]

        self.logger.debug(f"Stopped monitoring action {action_id}")

    async def check_timeouts(self) -> List[str]:
        """
        Check for timed out actions.

        Returns:
            List of timed out action IDs
        """
        now = datetime.now(timezone.utc)
        timed_out = []

        async with self._lock:
            for action_id, info in self._executions.items():
                elapsed = (now - info["start_time"]).total_seconds()

                if elapsed > info["timeout"]:
                    timed_out.append(action_id)
                    info["status"] = "timed_out"

                    self.logger.error(
                        f"Action {action_id} timed out after {elapsed:.1f}s"
                    )

        return timed_out

    async def run_monitor_loop(self) -> None:
        """Run the monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.check_interval)

                timed_out = await self.check_timeouts()

                if timed_out:
                    # Could trigger timeout handling here
                    pass

            except asyncio.CancelledError:
                break
            except (RuntimeError, OSError, ValueError) as e:
                self.logger.error(f"Error in monitor loop: {e}")

    def start(self) -> None:
        """Start the monitoring task."""
        if not self._monitoring_task or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self.run_monitor_loop())

    def stop(self) -> None:
        """Stop the monitoring task."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()

    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        async with self._lock:
            now = datetime.now(timezone.utc)

            stats: Dict[str, Any] = {
                "active_executions": len(self._executions),
                "by_status": {},
                "average_runtime": 0.0,
            }

            total_runtime = 0.0

            for info in self._executions.values():
                status = info["status"]
                by_status = stats["by_status"]
                if isinstance(by_status, dict):
                    by_status[status] = by_status.get(status, 0) + 1

                runtime = (now - info["start_time"]).total_seconds()
                total_runtime += runtime

            if self._executions:
                stats["average_runtime"] = total_runtime / len(self._executions)

            return stats

    def start_monitoring_sync(self, execution_id: str) -> None:
        """Start monitoring an execution (synchronous version for tests)."""
        self._executions[execution_id] = {
            "start_time": datetime.now(timezone.utc),
            "timeout": self.timeout_seconds,
            "status": "executing",
        }
        self.logger.debug(f"Started monitoring execution {execution_id}")

    def check_timeout(self, execution_id: str) -> bool:
        """Check if a specific execution has timed out."""
        if execution_id not in self._executions:
            return False

        info = self._executions[execution_id]
        elapsed = (datetime.now(timezone.utc) - info["start_time"]).total_seconds()

        if elapsed > info["timeout"]:
            info["status"] = "timed_out"
            return True

        return False

    def complete_execution(self, execution_id: str) -> None:
        """Mark an execution as complete and stop monitoring it."""
        if execution_id in self._executions:
            del self._executions[execution_id]
            self.logger.debug(f"Completed execution {execution_id}")

    @property
    def active_executions(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active executions."""
        return self._executions


def determine_action_priority(
    action: RemediationAction, risk_level: Optional[ActionRiskLevel] = None
) -> ExecutionPriority:
    """
    Determine the execution priority for an action.

    Args:
        action: The remediation action
        risk_level: Risk level of the action

    Returns:
        Execution priority
    """
    # Critical actions that stop active threats
    critical_actions = [
        "block_ip_address",
        "disable_user_account",
        "quarantine_instance",
        "revoke_api_key",
    ]

    if action.action_type in critical_actions:
        return ExecutionPriority.CRITICAL

    # High priority for credential and access control
    high_priority_actions = [
        "rotate_credentials",
        "revoke_iam_permission",
        "remove_service_account_key",
    ]

    if action.action_type in high_priority_actions:
        return ExecutionPriority.HIGH

    # Low priority for non-urgent actions
    low_priority_actions = [
        "enable_additional_logging",
        "snapshot_instance",
        "enable_bucket_versioning",
    ]

    if action.action_type in low_priority_actions:
        return ExecutionPriority.LOW

    # Use risk level if provided
    if risk_level:
        if risk_level == ActionRiskLevel.CRITICAL:
            return ExecutionPriority.HIGH
        elif risk_level == ActionRiskLevel.LOW:
            return ExecutionPriority.LOW

    # Default to medium
    return ExecutionPriority.MEDIUM

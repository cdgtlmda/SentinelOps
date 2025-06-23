"""
PRODUCTION ADK CATCHUP SCAN MANAGER TESTS - 100% NO MOCKING

Comprehensive tests for CatchUpScanManager and CatchUpTask with REAL scan management.
ZERO MOCKING - All tests use production scan management and real task execution.

Target: ≥90% statement coverage of src/detection_agent/catchup_scan_manager.py
VERIFICATION:
python -m coverage run -m pytest tests/unit/detection_agent/test_catchup_scan_manager.py && python -m coverage report --include="*catchup_scan_manager.py" --show-missing

CRITICAL: Uses 100% production code - NO MOCKING ALLOWED
Project: your-gcp-project-id
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

# REAL IMPORTS - NO MOCKING
from src.detection_agent.catchup_scan_manager import CatchUpTask, CatchUpScanManager


class TestCatchUpTask:
    """Test CatchUpTask dataclass functionality."""

    def test_catchup_task_creation(self) -> None:
        """Test basic CatchUpTask creation."""
        start_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="audit",
            start_time=start_time,
            end_time=end_time,
            priority=5,
            chunk_size_minutes=30,
        )

        assert task.log_type == "audit"
        assert task.start_time == start_time
        assert task.end_time == end_time
        assert task.priority == 5
        assert task.chunk_size_minutes == 30

    def test_catchup_task_defaults(self) -> None:
        """Test CatchUpTask with default values."""
        start_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="system_event", start_time=start_time, end_time=end_time
        )

        assert task.priority == 0
        assert task.chunk_size_minutes == 60

    def test_get_chunks_single_chunk(self) -> None:
        """Test get_chunks when time range fits in one chunk."""
        start_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="audit",
            start_time=start_time,
            end_time=end_time,
            chunk_size_minutes=60,
        )

        chunks = task.get_chunks()
        assert len(chunks) == 1
        assert chunks[0] == (start_time, end_time)

    def test_get_chunks_multiple_chunks(self) -> None:
        """Test get_chunks when time range requires multiple chunks."""
        start_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="data_access",
            start_time=start_time,
            end_time=end_time,
            chunk_size_minutes=60,
        )

        chunks = task.get_chunks()
        assert len(chunks) == 3

        # First chunk: 10:00 - 11:00
        assert chunks[0] == (start_time, start_time + timedelta(minutes=60))

        # Second chunk: 11:00 - 12:00
        assert chunks[1] == (
            start_time + timedelta(minutes=60),
            start_time + timedelta(minutes=120),
        )

        # Third chunk: 12:00 - 12:30
        assert chunks[2] == (start_time + timedelta(minutes=120), end_time)

    def test_get_chunks_exact_boundary(self) -> None:
        """Test get_chunks when time range is exact multiple of chunk size."""
        start_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(
            2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
        )  # Exactly 2 hours

        task = CatchUpTask(
            log_type="vpc_flow",
            start_time=start_time,
            end_time=end_time,
            chunk_size_minutes=60,
        )

        chunks = task.get_chunks()
        assert len(chunks) == 2
        assert chunks[0] == (start_time, start_time + timedelta(minutes=60))
        assert chunks[1] == (start_time + timedelta(minutes=60), end_time)

    def test_get_chunks_small_chunk_size(self) -> None:
        """Test get_chunks with small chunk size."""
        start_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 10, 45, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="firewall",
            start_time=start_time,
            end_time=end_time,
            chunk_size_minutes=15,
        )

        chunks = task.get_chunks()
        assert len(chunks) == 3
        assert chunks[0] == (start_time, start_time + timedelta(minutes=15))
        assert chunks[1] == (
            start_time + timedelta(minutes=15),
            start_time + timedelta(minutes=30),
        )
        assert chunks[2] == (start_time + timedelta(minutes=30), end_time)


class TestCatchUpScanManager:
    """Test CatchUpScanManager functionality."""

    def test_init_default_config(self) -> None:
        """Test CatchUpScanManager initialization with default config."""
        manager = CatchUpScanManager({})

        assert manager.max_catchup_hours == 24
        assert manager.default_chunk_minutes == 60
        assert manager.max_concurrent_catchup == 2
        assert manager.log_type_priorities == {
            "audit": 10,
            "data_access": 8,
            "system_event": 6,
            "vpc_flow": 4,
            "firewall": 5,
        }
        assert not manager.active_tasks
        assert not manager.completed_tasks
        assert not manager.pending_tasks
        assert manager.catchup_start_time is None
        assert manager.total_catchup_duration == 0.0

    def test_init_custom_config(self) -> None:
        """Test CatchUpScanManager initialization with custom config."""
        config = {
            "agents": {
                "detection": {
                    "catch_up_scan": {
                        "max_catchup_hours": 48,
                        "default_chunk_minutes": 30,
                        "max_concurrent_catchup": 4,
                        "audit_priority": 15,
                        "data_access_priority": 12,
                        "system_event_priority": 8,
                        "vpc_flow_priority": 6,
                        "firewall_priority": 10,
                    }
                }
            }
        }

        manager = CatchUpScanManager(config)

        assert manager.max_catchup_hours == 48
        assert manager.default_chunk_minutes == 30
        assert manager.max_concurrent_catchup == 4
        assert manager.log_type_priorities == {
            "audit": 15,
            "data_access": 12,
            "system_event": 8,
            "vpc_flow": 6,
            "firewall": 10,
        }

    def test_identify_catchup_needs_no_gaps(self) -> None:
        """Test identify_catchup_needs when no catch-up is needed."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Recent scan times (within 5 minutes)
        last_scan_times = {
            "audit": current_time - timedelta(minutes=2),
            "data_access": current_time - timedelta(minutes=1),
            "system_event": current_time - timedelta(minutes=3),
        }

        tasks = manager.identify_catchup_needs(last_scan_times, current_time)
        assert len(tasks) == 0

    def test_identify_catchup_needs_small_gaps(self) -> None:
        """Test identify_catchup_needs with gaps requiring catch-up."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Scan times requiring catch-up
        last_scan_times = {
            "audit": current_time - timedelta(hours=2),
            "data_access": current_time - timedelta(hours=1),
            "system_event": current_time - timedelta(minutes=30),
        }

        tasks = manager.identify_catchup_needs(last_scan_times, current_time)

        # Should have 3 tasks (all have gaps > 5 minutes)
        assert len(tasks) == 3

        # Tasks should be sorted by priority (audit=10, data_access=8, system_event=6)
        assert tasks[0].log_type == "audit"
        assert tasks[0].priority == 10
        assert tasks[1].log_type == "data_access"
        assert tasks[1].priority == 8
        assert tasks[2].log_type == "system_event"
        assert tasks[2].priority == 6

        # Check time ranges
        assert tasks[0].start_time == current_time - timedelta(hours=2)
        assert tasks[0].end_time == current_time

    def test_identify_catchup_needs_max_lookback(self) -> None:
        """Test identify_catchup_needs respects max_catchup_hours limit."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Very old scan time (beyond max_catchup_hours)
        last_scan_times = {
            "audit": current_time - timedelta(hours=48),  # 48 hours ago
            "data_access": current_time - timedelta(hours=6),  # 6 hours ago
        }

        tasks = manager.identify_catchup_needs(last_scan_times, current_time)

        assert len(tasks) == 2

        # Audit task should be limited to max_catchup_hours (24 hours)
        audit_task = next(t for t in tasks if t.log_type == "audit")
        expected_start = current_time - timedelta(hours=24)
        assert audit_task.start_time == expected_start
        assert audit_task.end_time == current_time

        # Data access task should use actual last scan time
        data_task = next(t for t in tasks if t.log_type == "data_access")
        assert data_task.start_time == current_time - timedelta(hours=6)

    def test_identify_catchup_needs_unknown_log_type(self) -> None:
        """Test identify_catchup_needs with unknown log type gets default priority."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        last_scan_times = {"unknown_type": current_time - timedelta(hours=1)}

        tasks = manager.identify_catchup_needs(last_scan_times, current_time)

        assert len(tasks) == 1
        assert tasks[0].log_type == "unknown_type"
        assert tasks[0].priority == 5  # Default priority

    def test_schedule_catchup_tasks_empty(self) -> None:
        """Test scheduling empty task list."""
        manager = CatchUpScanManager({})
        manager.schedule_catchup_tasks([])

        assert len(manager.pending_tasks) == 0

    def test_schedule_catchup_tasks_single(self) -> None:
        """Test scheduling single task."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="audit",
            start_time=current_time - timedelta(hours=1),
            end_time=current_time,
            priority=10,
        )

        manager.schedule_catchup_tasks([task])

        assert len(manager.pending_tasks) == 1
        assert manager.pending_tasks[0] == task

    def test_schedule_catchup_tasks_multiple_sorted(self) -> None:
        """Test scheduling multiple tasks are sorted by priority."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task1 = CatchUpTask(
            log_type="system_event",
            start_time=current_time,
            end_time=current_time,
            priority=6,
        )
        task2 = CatchUpTask(
            log_type="audit",
            start_time=current_time,
            end_time=current_time,
            priority=10,
        )
        task3 = CatchUpTask(
            log_type="data_access",
            start_time=current_time,
            end_time=current_time,
            priority=8,
        )

        manager.schedule_catchup_tasks([task1, task2, task3])

        assert len(manager.pending_tasks) == 3
        # Should be sorted by priority (highest first)
        assert manager.pending_tasks[0].priority == 10  # audit
        assert manager.pending_tasks[1].priority == 8  # data_access
        assert manager.pending_tasks[2].priority == 6  # system_event

    def test_schedule_catchup_tasks_duplicates(self) -> None:
        """Test scheduling removes duplicates, keeping highest priority."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task1 = CatchUpTask(
            log_type="audit", start_time=current_time, end_time=current_time, priority=8
        )
        task2 = CatchUpTask(
            log_type="audit",
            start_time=current_time,
            end_time=current_time,
            priority=10,
        )
        task3 = CatchUpTask(
            log_type="data_access",
            start_time=current_time,
            end_time=current_time,
            priority=8,
        )

        manager.schedule_catchup_tasks([task1, task2, task3])

        assert len(manager.pending_tasks) == 2
        # Should keep the higher priority audit task
        audit_task = next(t for t in manager.pending_tasks if t.log_type == "audit")
        assert audit_task.priority == 10

    @pytest.mark.asyncio
    async def test_execute_catchup_scans_no_tasks(self) -> None:
        """Test execute_catchup_scans with no pending tasks."""
        manager = CatchUpScanManager({})

        async def dummy_scan_callback(_task: CatchUpTask) -> bool:
            return True

        result = await manager.execute_catchup_scans(dummy_scan_callback)

        assert result["status"] == "no_tasks"
        assert result["message"] == "No catch-up tasks to execute"

    @pytest.mark.asyncio
    async def test_execute_catchup_scans_successful(self) -> None:
        """Test successful execution of catch-up scans."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create task with 2 chunks
        task = CatchUpTask(
            log_type="audit",
            start_time=current_time - timedelta(hours=2),
            end_time=current_time,
            priority=10,
            chunk_size_minutes=60,
        )
        manager.pending_tasks = [task]

        # Track callback calls
        callback_calls = []

        async def scan_callback(chunk_task: CatchUpTask) -> bool:
            callback_calls.append(chunk_task)
            return True  # Success

        progress_updates = []

        def progress_callback(progress: dict[str, Any]) -> None:
            progress_updates.append(progress)

        result = await manager.execute_catchup_scans(scan_callback, progress_callback)

        assert result["status"] == "completed"
        assert result["total_tasks"] == 1
        assert result["total_chunks"] == 2
        assert result["completed_chunks"] == 2
        assert result["failed_chunks"] == 0
        assert len(result["failures"]) == 0
        assert result["duration_seconds"] > 0

        # Verify callback was called for each chunk
        assert len(callback_calls) == 2

        # Verify progress updates
        assert len(progress_updates) == 2
        assert progress_updates[-1]["completed_chunks"] == 2
        assert progress_updates[-1]["total_chunks"] == 2

        # Verify task was moved to completed
        assert len(manager.completed_tasks) == 1
        assert len(manager.pending_tasks) == 0
        assert len(manager.active_tasks) == 0

    @pytest.mark.asyncio
    async def test_execute_catchup_scans_with_failures(self) -> None:
        """Test execution with some failed chunks."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="data_access",
            start_time=current_time - timedelta(hours=2),
            end_time=current_time,
            priority=8,
            chunk_size_minutes=60,
        )
        manager.pending_tasks = [task]

        # Fail first chunk, succeed second
        call_count = 0

        async def scan_callback(_chunk_task: CatchUpTask) -> bool:
            nonlocal call_count
            call_count += 1
            return call_count > 1  # Fail first, succeed rest

        result = await manager.execute_catchup_scans(scan_callback)

        assert result["status"] == "completed"
        assert result["total_chunks"] == 2
        assert result["completed_chunks"] == 1
        assert result["failed_chunks"] == 1
        assert len(result["failures"]) == 1

        # Check failure details
        failure = result["failures"][0]
        assert failure["log_type"] == "data_access"
        assert "start_time" in failure
        assert "end_time" in failure

    @pytest.mark.asyncio
    async def test_execute_catchup_scans_with_exceptions(self) -> None:
        """Test execution when scan callback raises exceptions."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="vpc_flow",
            start_time=current_time - timedelta(minutes=30),
            end_time=current_time,
            priority=4,
            chunk_size_minutes=60,  # Single chunk
        )
        manager.pending_tasks = [task]

        async def failing_scan_callback(chunk_task: CatchUpTask) -> bool:
            raise ValueError("Simulated scan failure")

        result = await manager.execute_catchup_scans(failing_scan_callback)

        assert result["status"] == "completed"
        assert result["failed_chunks"] == 1
        assert len(result["failures"]) == 1

        failure = result["failures"][0]
        assert failure["error"] == "Simulated scan failure"

    @pytest.mark.asyncio
    async def test_execute_catchup_scans_concurrent_tasks(self) -> None:
        """Test concurrent execution of multiple tasks."""
        manager = CatchUpScanManager(
            {"agents": {"detection": {"catch_up_scan": {"max_concurrent_catchup": 3}}}}
        )
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create 3 tasks with single chunks each
        tasks = [
            CatchUpTask(
                log_type="audit",
                start_time=current_time - timedelta(minutes=30),
                end_time=current_time,
                priority=10,
                chunk_size_minutes=60,
            ),
            CatchUpTask(
                log_type="data_access",
                start_time=current_time - timedelta(minutes=30),
                end_time=current_time,
                priority=8,
                chunk_size_minutes=60,
            ),
            CatchUpTask(
                log_type="system_event",
                start_time=current_time - timedelta(minutes=30),
                end_time=current_time,
                priority=6,
                chunk_size_minutes=60,
            ),
        ]
        manager.pending_tasks = tasks

        processed_log_types = []

        async def scan_callback(chunk_task: CatchUpTask) -> bool:
            processed_log_types.append(chunk_task.log_type)
            await asyncio.sleep(0.01)  # Small delay to test concurrency
            return True

        result = await manager.execute_catchup_scans(scan_callback)

        assert result["status"] == "completed"
        assert result["total_tasks"] == 3
        assert result["completed_chunks"] == 3
        assert len(processed_log_types) == 3

    def test_get_catchup_status_idle(self) -> None:
        """Test get_catchup_status when idle."""
        manager = CatchUpScanManager({})

        status = manager.get_catchup_status()

        assert status["active_tasks"] == 0
        assert status["pending_tasks"] == 0
        assert status["completed_tasks"] == 0
        assert status["is_running"] is False
        assert not status["active_log_types"]

    def test_get_catchup_status_with_tasks(self) -> None:
        """Test get_catchup_status with various task states."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Add some tasks to different states
        active_task = CatchUpTask(
            log_type="audit", start_time=current_time, end_time=current_time
        )
        pending_task = CatchUpTask(
            log_type="data_access", start_time=current_time, end_time=current_time
        )
        completed_task = CatchUpTask(
            log_type="system_event", start_time=current_time, end_time=current_time
        )

        manager.active_tasks["audit"] = active_task
        manager.pending_tasks.append(pending_task)
        manager.completed_tasks.append(completed_task)
        manager.catchup_start_time = datetime.now(timezone.utc)

        status = manager.get_catchup_status()

        assert status["active_tasks"] == 1
        assert status["pending_tasks"] == 1
        assert status["completed_tasks"] == 1
        assert status["is_running"] is True
        assert status["active_log_types"] == ["audit"]
        assert "elapsed_seconds" in status

    def test_get_catchup_status_with_completion_time(self) -> None:
        """Test get_catchup_status includes last completion time."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task1 = CatchUpTask(
            log_type="audit",
            start_time=current_time,
            end_time=current_time + timedelta(hours=1),
        )
        task2 = CatchUpTask(
            log_type="data_access",
            start_time=current_time,
            end_time=current_time + timedelta(hours=2),
        )

        manager.completed_tasks = [task1, task2]

        status = manager.get_catchup_status()

        assert "last_completion" in status
        # Should be the latest end_time
        expected_time = (current_time + timedelta(hours=2)).isoformat()
        assert status["last_completion"] == expected_time

    def test_estimate_catchup_duration_empty(self) -> None:
        """Test estimate_catchup_duration with no tasks."""
        manager = CatchUpScanManager({})

        duration = manager.estimate_catchup_duration([])
        assert duration == 0.0

    def test_estimate_catchup_duration_single_task(self) -> None:
        """Test estimate_catchup_duration with single task."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="audit",
            start_time=current_time - timedelta(hours=2),
            end_time=current_time,
        )

        duration = manager.estimate_catchup_duration([task])
        # 2 hours * 1 minute per hour = 2 minutes = 120 seconds
        assert duration == 120.0

    def test_estimate_catchup_duration_multiple_tasks(self) -> None:
        """Test estimate_catchup_duration with multiple tasks."""
        manager = CatchUpScanManager(
            {"agents": {"detection": {"catch_up_scan": {"max_concurrent_catchup": 2}}}}
        )
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        tasks = [
            CatchUpTask(
                log_type="audit",
                start_time=current_time - timedelta(hours=3),
                end_time=current_time,
            ),
            CatchUpTask(
                log_type="data_access",
                start_time=current_time - timedelta(hours=1),
                end_time=current_time,
            ),
        ]

        duration = manager.estimate_catchup_duration(tasks)
        # (3 + 1) hours * 1 minute per hour = 4 minutes = 240 seconds
        # Divided by concurrency (2 tasks, 2 concurrent) = 240 / 2 = 120 seconds
        assert duration == 120.0

    def test_should_pause_regular_scans_no_active(self) -> None:
        """Test should_pause_regular_scans with no active tasks."""
        manager = CatchUpScanManager({})

        assert manager.should_pause_regular_scans() is False

    def test_should_pause_regular_scans_low_priority(self) -> None:
        """Test should_pause_regular_scans with low priority active tasks."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="vpc_flow",
            start_time=current_time,
            end_time=current_time,
            priority=4,
        )
        manager.active_tasks["vpc_flow"] = task

        assert manager.should_pause_regular_scans() is False

    def test_should_pause_regular_scans_high_priority(self) -> None:
        """Test should_pause_regular_scans with high priority active tasks."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task = CatchUpTask(
            log_type="audit",
            start_time=current_time,
            end_time=current_time,
            priority=10,
        )
        manager.active_tasks["audit"] = task

        assert manager.should_pause_regular_scans() is True

    def test_should_pause_regular_scans_mixed_priorities(self) -> None:
        """Test should_pause_regular_scans with mixed priority active tasks."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        task1 = CatchUpTask(
            log_type="vpc_flow",
            start_time=current_time,
            end_time=current_time,
            priority=4,
        )
        task2 = CatchUpTask(
            log_type="data_access",
            start_time=current_time,
            end_time=current_time,
            priority=8,
        )

        manager.active_tasks["vpc_flow"] = task1
        manager.active_tasks["data_access"] = task2

        # Should pause because max priority (8) >= 8
        assert manager.should_pause_regular_scans() is True

    def test_clear_history(self) -> None:
        """Test clear_history clears all tracking data."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Add some history data
        task = CatchUpTask(
            log_type="audit", start_time=current_time, end_time=current_time
        )
        manager.completed_tasks.append(task)
        manager.total_catchup_duration = 300.0
        manager.catchup_start_time = current_time

        manager.clear_history()

        assert len(manager.completed_tasks) == 0
        assert manager.total_catchup_duration == 0.0
        assert manager.catchup_start_time is None

    def test_edge_case_empty_time_range(self) -> None:
        """Test edge case with identical start and end times."""
        task = CatchUpTask(
            log_type="test",
            start_time=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        chunks = task.get_chunks()
        assert len(chunks) == 0

    def test_edge_case_very_small_time_range(self) -> None:
        """Test edge case with very small time range."""
        start_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end_time = start_time + timedelta(seconds=1)

        task = CatchUpTask(
            log_type="test",
            start_time=start_time,
            end_time=end_time,
            chunk_size_minutes=60,
        )

        chunks = task.get_chunks()
        assert len(chunks) == 1
        assert chunks[0] == (start_time, end_time)

    def test_integration_full_workflow(self) -> None:
        """Test complete workflow from identification to execution."""
        manager = CatchUpScanManager({})
        current_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Step 1: Identify catch-up needs
        last_scan_times = {
            "audit": current_time - timedelta(hours=3),
            "data_access": current_time - timedelta(hours=1),
        }

        tasks = manager.identify_catchup_needs(last_scan_times, current_time)
        assert len(tasks) == 2

        # Step 2: Schedule tasks
        manager.schedule_catchup_tasks(tasks)
        assert len(manager.pending_tasks) == 2

        # Step 3: Check status before execution
        status = manager.get_catchup_status()
        assert status["pending_tasks"] == 2
        assert status["is_running"] is False

        # Step 4: Estimate duration
        duration = manager.estimate_catchup_duration(manager.pending_tasks)
        assert duration > 0

        # Step 5: Check if should pause regular scans
        should_pause = manager.should_pause_regular_scans()
        assert should_pause is False  # No active tasks yet

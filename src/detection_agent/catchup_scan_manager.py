"""
Catch-up scan management for the Detection Agent.

This module handles scanning of historical logs when the agent has been offline.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable
import logging


@dataclass
class CatchUpTask:
    """Represents a catch-up scan task."""
    log_type: str
    start_time: datetime
    end_time: datetime
    priority: int = 0  # Higher priority = more important
    chunk_size_minutes: int = 60  # Size of each scan chunk

    def get_chunks(self) -> List[Tuple[datetime, datetime]]:
        """Split the catch-up period into manageable chunks."""
        chunks = []
        current_start = self.start_time

        while current_start < self.end_time:
            chunk_end = min(
                current_start + timedelta(minutes=self.chunk_size_minutes),
                self.end_time
            )
            chunks.append((current_start, chunk_end))
            current_start = chunk_end

        return chunks


class CatchUpScanManager:
    """Manages catch-up scanning when the agent has been offline."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the catch-up scan manager.

        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)

        # Configure catch-up settings
        catchup_config = config.get("agents", {}).get("detection", {}).get("catch_up_scan", {})

        # Maximum time to look back for catch-up
        self.max_catchup_hours = catchup_config.get("max_catchup_hours", 24)

        # Chunk size for catch-up scans
        self.default_chunk_minutes = catchup_config.get("default_chunk_minutes", 60)

        # Priority levels for different log types
        self.log_type_priorities = {
            "audit": catchup_config.get("audit_priority", 10),
            "data_access": catchup_config.get("data_access_priority", 8),
            "system_event": catchup_config.get("system_event_priority", 6),
            "vpc_flow": catchup_config.get("vpc_flow_priority", 4),
            "firewall": catchup_config.get("firewall_priority", 5)
        }

        # Concurrent catch-up tasks limit
        self.max_concurrent_catchup = catchup_config.get("max_concurrent_catchup", 2)

        # Track active catch-up tasks
        self.active_tasks: Dict[str, CatchUpTask] = {}
        self.completed_tasks: List[CatchUpTask] = []
        self.pending_tasks: List[CatchUpTask] = []

        # Performance tracking
        self.catchup_start_time: Optional[datetime] = None
        self.total_catchup_duration: float = 0.0

    def identify_catchup_needs(
        self,
        last_scan_times: Dict[str, datetime],
        current_time: datetime
    ) -> List[CatchUpTask]:
        """
        Identify which log types need catch-up scanning.

        Args:
            last_scan_times: Last successful scan time for each log type
            current_time: Current time

        Returns:
            List of catch-up tasks needed
        """
        tasks = []
        max_lookback = current_time - timedelta(hours=self.max_catchup_hours)

        for log_type, last_scan in last_scan_times.items():
            # Skip if last scan is recent enough
            if current_time - last_scan <= timedelta(minutes=5):
                continue

            # Limit lookback to max_catchup_hours
            effective_start = max(last_scan, max_lookback)

            if effective_start < current_time:
                task = CatchUpTask(
                    log_type=log_type,
                    start_time=effective_start,
                    end_time=current_time,
                    priority=self.log_type_priorities.get(log_type, 5),
                    chunk_size_minutes=self.default_chunk_minutes
                )

                gap_hours = (current_time - effective_start).total_seconds() / 3600
                self.logger.info(
                    "Catch-up needed for %s: %.1f hours from %s to %s",
                    log_type, gap_hours, effective_start, current_time
                )

                tasks.append(task)

        # Sort by priority (highest first)
        tasks.sort(key=lambda t: t.priority, reverse=True)

        return tasks

    def schedule_catchup_tasks(self, tasks: List[CatchUpTask]) -> None:
        """
        Schedule catch-up tasks for execution.

        Args:
            tasks: List of catch-up tasks to schedule
        """
        self.pending_tasks.extend(tasks)

        # Remove duplicates (keep highest priority)
        unique_tasks: Dict[str, CatchUpTask] = {}
        for task in self.pending_tasks:
            key = task.log_type
            if key not in unique_tasks or task.priority > unique_tasks[key].priority:
                unique_tasks[key] = task

        self.pending_tasks = list(unique_tasks.values())
        self.pending_tasks.sort(key=lambda t: t.priority, reverse=True)

        self.logger.info("Scheduled %s catch-up tasks", len(self.pending_tasks))

    async def execute_catchup_scans(
        self,
        scan_callback: Callable[[CatchUpTask], Any],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute scheduled catch-up scans.

        Args:
            scan_callback: Async function to call for each scan chunk
                          (log_type, start_time, end_time) -> bool
            progress_callback: Optional callback for progress updates
                              (completed_chunks, total_chunks, current_log_type)

        Returns:
            Summary of catch-up execution
        """
        if not self.pending_tasks:
            return {"status": "no_tasks", "message": "No catch-up tasks to execute"}

        self.catchup_start_time = datetime.now(timezone.utc)
        total_chunks = sum(len(task.get_chunks()) for task in self.pending_tasks)
        completed_chunks = 0
        failed_chunks = []
        self.logger.info(
            "Starting catch-up scan execution: %s tasks, %s total chunks",
            len(self.pending_tasks), total_chunks
        )

        # Process tasks with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent_catchup)

        async def process_task(task: CatchUpTask) -> None:
            """Process a single catch-up task."""
            async with semaphore:
                self.active_tasks[task.log_type] = task
                chunks = task.get_chunks()

                for _, (start_time, end_time) in enumerate(chunks):
                    try:
                        # Execute scan for this chunk
                        chunk_task = CatchUpTask(
                            log_type=task.log_type,
                            start_time=start_time,
                            end_time=end_time,
                            priority=task.priority,
                            chunk_size_minutes=task.chunk_size_minutes
                        )
                        success = await scan_callback(chunk_task)

                        if not success:
                            failed_chunks.append({
                                "log_type": task.log_type,
                                "start_time": start_time,
                                "end_time": end_time
                            })
                        else:
                            nonlocal completed_chunks
                            completed_chunks += 1

                        # Report progress
                        if progress_callback:
                            progress_callback({
                                "completed_chunks": completed_chunks,
                                "total_chunks": total_chunks,
                                "current_log_type": task.log_type
                            })

                    except (RuntimeError, ValueError, KeyError, asyncio.TimeoutError, OSError) as e:
                        self.logger.error(
                            "Error in catch-up scan for %s chunk %s to %s: %s",
                            task.log_type, start_time, end_time, e
                        )
                        failed_chunks.append({
                            "log_type": task.log_type,
                            "start_time": start_time,
                            "end_time": end_time,
                            "error": str(e)
                        })
                # Mark task as completed
                del self.active_tasks[task.log_type]
                self.completed_tasks.append(task)

        # Execute all tasks concurrently
        await asyncio.gather(*[process_task(task) for task in self.pending_tasks])

        # Calculate duration
        self.total_catchup_duration = (
            datetime.now(timezone.utc) - self.catchup_start_time
        ).total_seconds()

        # Clear pending tasks
        self.pending_tasks = []

        return {
            "status": "completed",
            "total_tasks": len(self.completed_tasks),
            "total_chunks": total_chunks,
            "completed_chunks": completed_chunks,
            "failed_chunks": len(failed_chunks),
            "duration_seconds": self.total_catchup_duration,
            "failures": failed_chunks
        }

    def get_catchup_status(self) -> Dict[str, Any]:
        """Get the current status of catch-up scanning."""
        status = {
            "active_tasks": len(self.active_tasks),
            "pending_tasks": len(self.pending_tasks),
            "completed_tasks": len(self.completed_tasks),
            "is_running": len(self.active_tasks) > 0,
            "active_log_types": list(self.active_tasks.keys())
        }

        if self.catchup_start_time and self.active_tasks:
            elapsed = (datetime.now(timezone.utc) - self.catchup_start_time).total_seconds()
            status["elapsed_seconds"] = elapsed

        if self.completed_tasks:
            status["last_completion"] = max(
                task.end_time for task in self.completed_tasks
            ).isoformat()

        return status

    def estimate_catchup_duration(self, tasks: List[CatchUpTask]) -> float:
        """
        Estimate how long catch-up scanning will take.

        Args:
            tasks: List of catch-up tasks

        Returns:
            Estimated duration in seconds
        """
        if not tasks:
            return 0.0

        # Calculate total time range to scan
        total_hours = 0.0
        for task in tasks:
            hours = (task.end_time - task.start_time).total_seconds() / 3600
            total_hours += hours

        # Estimate based on historical performance or defaults
        # Assume 1 minute per hour of logs per log type (configurable)
        minutes_per_hour = 1.0
        estimated_minutes = total_hours * minutes_per_hour

        # Adjust for concurrency
        if self.max_concurrent_catchup > 1:
            estimated_minutes /= min(self.max_concurrent_catchup, len(tasks))

        return estimated_minutes * 60  # Return seconds

    def should_pause_regular_scans(self) -> bool:
        """
        Determine if regular scans should be paused during catch-up.

        Returns:
            True if regular scans should be paused
        """
        # Pause if we have high-priority catch-up tasks running
        if self.active_tasks:
            max_priority = max(
                task.priority for task in self.active_tasks.values()
            )
            return max_priority >= 8  # High priority threshold

        return False

    def clear_history(self) -> None:
        """Clear completed task history."""
        self.completed_tasks = []
        self.total_catchup_duration = 0.0
        self.catchup_start_time = None
        self.logger.info("Cleared catch-up scan history")

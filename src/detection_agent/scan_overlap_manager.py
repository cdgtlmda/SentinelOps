"""
Scan overlap management for the Detection Agent.

This module ensures reliable log scanning by managing overlapping time windows.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import logging


@dataclass
class ScanWindow:
    """Represents a scan time window."""

    start_time: datetime
    end_time: datetime
    overlap_seconds: int = 60  # Default 1 minute overlap

    def get_overlapped_window(self) -> Tuple[datetime, datetime]:
        """
        Get the scan window with overlap applied.

        Returns:
            Tuple of (adjusted_start_time, end_time)
        """
        adjusted_start = self.start_time - timedelta(seconds=self.overlap_seconds)
        return adjusted_start, self.end_time


class ScanOverlapManager:
    """Manages scan overlap to ensure no log entries are missed."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the scan overlap manager.

        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)

        # Configure overlap settings
        overlap_config = (
            config.get("agents", {}).get("detection", {}).get("scan_overlap", {})
        )

        # Default overlap in seconds for different log types
        self.default_overlap_seconds = overlap_config.get("default_overlap_seconds", 60)

        # Log-type specific overlaps
        self.log_type_overlaps = {
            "audit": overlap_config.get("audit_overlap_seconds", 60),
            "data_access": overlap_config.get("data_access_overlap_seconds", 60),
            "system_event": overlap_config.get("system_event_overlap_seconds", 60),
            "vpc_flow": overlap_config.get(
                "vpc_flow_overlap_seconds", 300
            ),  # 5 min for flow logs
            "firewall": overlap_config.get("firewall_overlap_seconds", 120),
        }

        # Maximum allowed overlap to prevent excessive rescanning
        self.max_overlap_seconds = overlap_config.get(
            "max_overlap_seconds", 600
        )  # 10 minutes

        # Track scan windows for monitoring
        self.scan_history: Dict[str, List[ScanWindow]] = {}
        self.max_history_entries = 100

    def calculate_scan_window(
        self,
        log_type: str,
        last_scan_time: datetime,
        current_time: datetime,
        force_overlap: Optional[int] = None,
    ) -> ScanWindow:
        """
        Calculate the scan window with appropriate overlap.

        Args:
            log_type: Type of log being scanned
            last_scan_time: Time of the last successful scan
            current_time: Current time (end of scan window)
            force_overlap: Override overlap seconds if specified

        Returns:
            ScanWindow with appropriate overlap
        """
        # Determine overlap seconds
        if force_overlap is not None:
            overlap_seconds = min(force_overlap, self.max_overlap_seconds)
        else:
            overlap_seconds = self.log_type_overlaps.get(
                log_type, self.default_overlap_seconds
            )

        # Ensure overlap doesn't exceed maximum
        overlap_seconds = min(overlap_seconds, self.max_overlap_seconds)

        # Create scan window
        window = ScanWindow(
            start_time=last_scan_time,
            end_time=current_time,
            overlap_seconds=overlap_seconds,
        )

        # Log the window
        self.logger.debug(
            "Calculated scan window for %s: %s to %s with %ss overlap",
            log_type,
            last_scan_time,
            current_time,
            overlap_seconds,
        )
        # Track in history
        self._add_to_history(log_type, window)

        return window

    def detect_gaps(
        self, log_type: str, new_window: ScanWindow
    ) -> Optional[ScanWindow]:
        """
        Detect if there's a gap between the last scan and the new window.

        Args:
            log_type: Type of log being scanned
            new_window: The proposed scan window

        Returns:
            ScanWindow covering the gap if one exists, None otherwise
        """
        if log_type not in self.scan_history or not self.scan_history[log_type]:
            return None

        # Get the last scan window
        last_windows = self.scan_history[log_type]
        if not last_windows:
            return None

        last_window = last_windows[-1]

        # Check for gap (considering overlap)
        last_effective_end = last_window.end_time
        new_effective_start, _ = new_window.get_overlapped_window()

        if new_effective_start > last_effective_end:
            # There's a gap
            gap_duration = (new_effective_start - last_effective_end).total_seconds()

            self.logger.warning(
                "Detected gap in %s scanning: %ss between %s and %s",
                log_type,
                gap_duration,
                last_effective_end,
                new_effective_start,
            )

            # Create a window to cover the gap
            gap_window = ScanWindow(
                start_time=last_effective_end,
                end_time=new_effective_start,
                overlap_seconds=0,  # No overlap needed for gap filling
            )

            return gap_window

        return None

    def _add_to_history(self, log_type: str, window: ScanWindow) -> None:
        """Add a scan window to the history."""
        if log_type not in self.scan_history:
            self.scan_history[log_type] = []

        self.scan_history[log_type].append(window)

        # Trim history if needed
        if len(self.scan_history[log_type]) > self.max_history_entries:
            self.scan_history[log_type] = self.scan_history[log_type][
                -self.max_history_entries :
            ]

    def get_adaptive_overlap(
        self, log_type: str, processing_delay: float, error_rate: float
    ) -> int:
        """
        Calculate adaptive overlap based on system performance.

        Args:
            log_type: Type of log being scanned
            processing_delay: Average processing delay in seconds
            error_rate: Recent error rate (0.0 to 1.0)

        Returns:
            Recommended overlap in seconds
        """
        # Start with base overlap for log type
        base_overlap = self.log_type_overlaps.get(
            log_type, self.default_overlap_seconds
        )

        # Adjust based on processing delay
        delay_factor = 1.0
        if processing_delay > 30:  # More than 30s delay
            delay_factor = min(2.0, 1.0 + (processing_delay / 60))

        # Adjust based on error rate
        error_factor = 1.0
        if error_rate > 0.05:  # More than 5% errors
            error_factor = min(2.0, 1.0 + (error_rate * 2))

        # Calculate adjusted overlap
        adjusted_overlap = base_overlap * delay_factor * error_factor

        # Ensure within bounds
        adjusted_overlap = max(self.default_overlap_seconds, adjusted_overlap)
        adjusted_overlap = min(self.max_overlap_seconds, adjusted_overlap)

        self.logger.info(
            "Adaptive overlap for %s: %ss (delay_factor=%.2f, error_factor=%.2f)",
            log_type,
            adjusted_overlap,
            delay_factor,
            error_factor,
        )

        return int(adjusted_overlap)

    def validate_scan_continuity(self, log_type: str) -> Tuple[bool, str]:
        """
        Validate that scans for a log type have been continuous.

        Args:
            log_type: Type of log to validate

        Returns:
            Tuple of (is_continuous, message)
        """
        if log_type not in self.scan_history or len(self.scan_history[log_type]) < 2:
            return True, "Insufficient history to validate"

        windows = self.scan_history[log_type]
        gaps_found = []

        for i in range(1, len(windows)):
            prev_window = windows[i - 1]
            curr_window = windows[i]

            # Check for gap
            curr_start_with_overlap, _ = curr_window.get_overlapped_window()

            if curr_start_with_overlap > prev_window.end_time:
                gap_seconds = (
                    curr_start_with_overlap - prev_window.end_time
                ).total_seconds()
                gaps_found.append(
                    {
                        "start": prev_window.end_time,
                        "end": curr_start_with_overlap,
                        "duration_seconds": gap_seconds,
                    }
                )

        if gaps_found:
            total_gap_time = sum(
                float(str(g["duration_seconds"]))
                for g in gaps_found
                if g["duration_seconds"] is not None
            )
            return False, f"Found {len(gaps_found)} gaps totaling {total_gap_time}s"

        return True, "Scan continuity verified"

    def get_scan_statistics(self) -> Dict[str, Any]:
        """Get statistics about scan windows and overlaps."""
        stats: Dict[str, Any] = {
            "log_types": {},
            "total_windows": 0,
            "gaps_detected": 0,
        }

        for log_type, windows in self.scan_history.items():
            if not windows:
                continue

            # Calculate average overlap
            avg_overlap = sum(w.overlap_seconds for w in windows) / len(windows)

            # Check continuity
            is_continuous, message = self.validate_scan_continuity(log_type)

            stats["log_types"][log_type] = {
                "window_count": len(windows),
                "average_overlap_seconds": avg_overlap,
                "is_continuous": is_continuous,
                "continuity_message": message,
            }

            stats["total_windows"] += len(windows)
            if not is_continuous:
                stats["gaps_detected"] += 1

        return stats

"""
Test suite for scan_overlap_manager.py

COVERAGE TARGET: ≥90% statement coverage of
src/detection_agent/scan_overlap_manager.py
VERIFICATION: python -m coverage run -m pytest
tests/unit/detection_agent/test_scan_overlap_manager.py
REPORT: python -m coverage report
--include="*detection_agent/scan_overlap_manager.py" --show-missing

Tests the ScanOverlapManager class and ScanWindow dataclass.
Uses 100% production code - NO MOCKING per project requirements.
"""

import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

# Load the production module using importlib
spec = importlib.util.spec_from_file_location(
    "scan_overlap_manager",
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "detection_agent"
    / "scan_overlap_manager.py",
)
assert spec is not None, "Module spec could not be created"
assert spec.loader is not None, "Module spec has no loader"
scan_overlap_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_overlap_manager)

ScanWindow = scan_overlap_manager.ScanWindow
ScanOverlapManager = scan_overlap_manager.ScanOverlapManager


class TestScanWindow:
    """Test the ScanWindow dataclass."""

    def test_scan_window_creation(self) -> None:
        """Test basic ScanWindow creation."""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)

        window = ScanWindow(start_time=start, end_time=end)

        assert window.start_time == start
        assert window.end_time == end
        assert window.overlap_seconds == 60  # Default value

    def test_scan_window_custom_overlap(self) -> None:
        """Test ScanWindow with custom overlap."""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)

        window = ScanWindow(start_time=start, end_time=end, overlap_seconds=120)

        assert window.overlap_seconds == 120

    def test_get_overlapped_window_default(self) -> None:
        """Test get_overlapped_window with default overlap."""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)

        window = ScanWindow(start_time=start, end_time=end)
        adjusted_start, actual_end = window.get_overlapped_window()

        expected_start = start - timedelta(seconds=60)
        assert adjusted_start == expected_start
        assert actual_end == end

    def test_get_overlapped_window_custom(self) -> None:
        """Test get_overlapped_window with custom overlap."""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)

        window = ScanWindow(start_time=start, end_time=end, overlap_seconds=300)
        adjusted_start, actual_end = window.get_overlapped_window()

        expected_start = start - timedelta(seconds=300)
        assert adjusted_start == expected_start
        assert actual_end == end

    def test_get_overlapped_window_zero_overlap(self) -> None:
        """Test get_overlapped_window with zero overlap."""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)

        window = ScanWindow(start_time=start, end_time=end, overlap_seconds=0)
        adjusted_start, actual_end = window.get_overlapped_window()

        assert adjusted_start == start  # No adjustment
        assert actual_end == end


class TestScanOverlapManager:
    """Test the ScanOverlapManager class."""

    def test_init_default_config(self) -> None:
        """Test initialization with empty config."""
        config: Dict[str, Any] = {}
        manager = ScanOverlapManager(config)

        assert manager.default_overlap_seconds == 60
        assert manager.log_type_overlaps["audit"] == 60
        assert manager.log_type_overlaps["vpc_flow"] == 300
        assert manager.max_overlap_seconds == 600
        assert manager.scan_history == {}
        assert manager.max_history_entries == 100

    def test_init_custom_config(self) -> None:
        """Test initialization with custom config."""
        config = {
            "agents": {
                "detection": {
                    "scan_overlap": {
                        "default_overlap_seconds": 120,
                        "audit_overlap_seconds": 180,
                        "vpc_flow_overlap_seconds": 600,
                        "max_overlap_seconds": 1200,
                    }
                }
            }
        }

        manager = ScanOverlapManager(config)

        assert manager.default_overlap_seconds == 120
        assert manager.log_type_overlaps["audit"] == 180
        assert manager.log_type_overlaps["vpc_flow"] == 600
        assert manager.max_overlap_seconds == 1200

    def test_init_partial_config(self) -> None:
        """Test initialization with partial config."""
        config = {
            "agents": {"detection": {"scan_overlap": {"audit_overlap_seconds": 90}}}
        }

        manager = ScanOverlapManager(config)

        assert manager.default_overlap_seconds == 60  # Default
        assert manager.log_type_overlaps["audit"] == 90  # Custom
        assert manager.log_type_overlaps["vpc_flow"] == 300  # Default

    def test_calculate_scan_window_default_overlap(self) -> None:
        """Test calculate_scan_window with default overlap."""
        manager = ScanOverlapManager({})

        last_scan = datetime(2024, 1, 1, 10, 0, 0)
        current_time = datetime(2024, 1, 1, 11, 0, 0)

        window = manager.calculate_scan_window("audit", last_scan, current_time)

        assert window.start_time == last_scan
        assert window.end_time == current_time
        assert window.overlap_seconds == 60  # Default for audit

    def test_calculate_scan_window_log_type_specific(self) -> None:
        """Test calculate_scan_window with log-type specific overlap."""
        manager = ScanOverlapManager({})

        last_scan = datetime(2024, 1, 1, 10, 0, 0)
        current_time = datetime(2024, 1, 1, 11, 0, 0)

        window = manager.calculate_scan_window("vpc_flow", last_scan, current_time)

        assert window.start_time == last_scan
        assert window.end_time == current_time
        assert window.overlap_seconds == 300  # VPC flow specific

    def test_calculate_scan_window_force_overlap(self) -> None:
        """Test calculate_scan_window with forced overlap."""
        manager = ScanOverlapManager({})

        last_scan = datetime(2024, 1, 1, 10, 0, 0)
        current_time = datetime(2024, 1, 1, 11, 0, 0)

        window = manager.calculate_scan_window(
            "audit", last_scan, current_time, force_overlap=180
        )

        assert window.overlap_seconds == 180

    def test_calculate_scan_window_force_overlap_exceeds_max(self) -> None:
        """Test calculate_scan_window with forced overlap exceeding max."""
        manager = ScanOverlapManager({})

        last_scan = datetime(2024, 1, 1, 10, 0, 0)
        current_time = datetime(2024, 1, 1, 11, 0, 0)

        window = manager.calculate_scan_window(
            "audit", last_scan, current_time, force_overlap=1000
        )

        assert window.overlap_seconds == 600  # Capped at max

    def test_calculate_scan_window_unknown_log_type(self) -> None:
        """Test calculate_scan_window with unknown log type."""
        manager = ScanOverlapManager({})

        last_scan = datetime(2024, 1, 1, 10, 0, 0)
        current_time = datetime(2024, 1, 1, 11, 0, 0)

        window = manager.calculate_scan_window("unknown_type", last_scan, current_time)

        assert window.overlap_seconds == 60  # Falls back to default

    def test_calculate_scan_window_adds_to_history(self) -> None:
        """Test that calculate_scan_window adds to history."""
        manager = ScanOverlapManager({})

        last_scan = datetime(2024, 1, 1, 10, 0, 0)
        current_time = datetime(2024, 1, 1, 11, 0, 0)

        window = manager.calculate_scan_window("audit", last_scan, current_time)

        assert "audit" in manager.scan_history
        assert len(manager.scan_history["audit"]) == 1
        assert manager.scan_history["audit"][0] == window

    def test_detect_gaps_no_history(self) -> None:
        """Test detect_gaps with no scan history."""
        manager = ScanOverlapManager({})

        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)

        gaps = manager.detect_gaps("audit", start, end)

        # Should return one gap covering the entire period
        assert len(gaps) == 1
        assert gaps[0][0] == start
        assert gaps[0][1] == end

    def test_detect_gaps_empty_history(self) -> None:
        """Test detect_gaps with empty scan history for log type."""
        manager = ScanOverlapManager({})
        manager.scan_history["audit"] = []  # Explicitly empty

        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)

        gaps = manager.detect_gaps("audit", start, end)

        assert len(gaps) == 1
        assert gaps[0][0] == start
        assert gaps[0][1] == end

    def test_detect_gaps_empty_history_after_add_and_clear(self) -> None:
        """Test detect_gaps with history that was cleared."""
        manager = ScanOverlapManager({})

        # Add some history first
        window = ScanWindow(
            start_time=datetime(2024, 1, 1, 9, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 0, 0),
        )
        manager._add_to_history("audit", window)

        # Clear the history
        manager.scan_history["audit"] = []

        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 11, 0, 0)

        gaps = manager.detect_gaps("audit", start, end)

        assert len(gaps) == 1
        assert gaps[0][0] == start
        assert gaps[0][1] == end

    def test_detect_gaps_no_gap(self) -> None:
        """Test detect_gaps with continuous coverage."""
        manager = ScanOverlapManager({})

        # Add windows that cover the entire period
        window1 = ScanWindow(
            start_time=datetime(2024, 1, 1, 9, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 0, 0),
        )
        window2 = ScanWindow(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0),
        )

        manager._add_to_history("audit", window1)
        manager._add_to_history("audit", window2)

        gaps = manager.detect_gaps(
            "audit", datetime(2024, 1, 1, 9, 30, 0), datetime(2024, 1, 1, 10, 30, 0)
        )

        assert len(gaps) == 0

    def test_detect_gaps_with_gap(self) -> None:
        """Test detect_gaps with a gap in coverage."""
        manager = ScanOverlapManager({})

        # Add windows with a gap between them
        window1 = ScanWindow(
            start_time=datetime(2024, 1, 1, 9, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 0, 0),
        )
        window2 = ScanWindow(
            start_time=datetime(2024, 1, 1, 11, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 0, 0),
        )

        manager._add_to_history("audit", window1)
        manager._add_to_history("audit", window2)

        gaps = manager.detect_gaps(
            "audit", datetime(2024, 1, 1, 9, 30, 0), datetime(2024, 1, 1, 11, 30, 0)
        )

        # Should detect gap between 10:00 and 11:00
        assert len(gaps) == 1
        assert gaps[0][0] == datetime(2024, 1, 1, 10, 0, 0)
        assert gaps[0][1] == datetime(2024, 1, 1, 11, 0, 0)

    def test_add_to_history_new_log_type(self) -> None:
        """Test adding scan window for new log type."""
        manager = ScanOverlapManager({})

        window = ScanWindow(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0),
        )

        manager._add_to_history("new_type", window)

        assert "new_type" in manager.scan_history
        assert len(manager.scan_history["new_type"]) == 1
        assert manager.scan_history["new_type"][0] == window

    def test_add_to_history_existing_log_type(self) -> None:
        """Test adding scan window to existing log type."""
        manager = ScanOverlapManager({})

        window1 = ScanWindow(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0),
        )
        window2 = ScanWindow(
            start_time=datetime(2024, 1, 1, 11, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 0, 0),
        )

        manager._add_to_history("audit", window1)
        manager._add_to_history("audit", window2)

        assert len(manager.scan_history["audit"]) == 2
        assert manager.scan_history["audit"][0] == window1
        assert manager.scan_history["audit"][1] == window2

    def test_add_to_history_trim_when_exceeds_max(self) -> None:
        """Test history trimming when max entries exceeded."""
        config = {"agents": {"detection": {"scan_overlap": {"max_history_entries": 2}}}}
        manager = ScanOverlapManager(config)

        # Add three windows (exceeds max of 2)
        for i in range(3):
            window = ScanWindow(
                start_time=datetime(2024, 1, 1, 10 + i, 0, 0),
                end_time=datetime(2024, 1, 1, 11 + i, 0, 0),
            )
            manager._add_to_history("audit", window)

        # Should only keep the latest 2
        assert len(manager.scan_history["audit"]) == 2
        assert manager.scan_history["audit"][0].start_time == datetime(
            2024, 1, 1, 11, 0, 0
        )
        assert manager.scan_history["audit"][1].start_time == datetime(
            2024, 1, 1, 12, 0, 0
        )

    def test_get_adaptive_overlap_base_case(self) -> None:
        """Test adaptive overlap with base case."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=0, error_rate=0.0
        )

        assert overlap == 60  # Base overlap for audit

    def test_get_adaptive_overlap_high_delay(self) -> None:
        """Test adaptive overlap with high processing delay."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=300, error_rate=0.0
        )

        assert overlap > 60  # Should increase due to delay

    def test_get_adaptive_overlap_high_error_rate(self) -> None:
        """Test adaptive overlap with high error rate."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=0, error_rate=0.1
        )

        assert overlap > 60  # Should increase due to error rate

    def test_get_adaptive_overlap_combined_factors(self) -> None:
        """Test adaptive overlap with combined factors."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=300, error_rate=0.1
        )

        assert overlap > 60  # Should increase due to both factors

    def test_get_adaptive_overlap_capped_by_max(self) -> None:
        """Test adaptive overlap is capped by max_overlap_seconds."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=1000, error_rate=0.5
        )

        assert overlap <= manager.max_overlap_seconds

    def test_get_adaptive_overlap_actually_capped(self) -> None:
        """Test adaptive overlap hits the cap."""
        config = {
            "agents": {"detection": {"scan_overlap": {"max_overlap_seconds": 100}}}
        }
        manager = ScanOverlapManager(config)

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=1000, error_rate=0.8
        )

        assert overlap == 100  # Should be capped at max

    def test_get_adaptive_overlap_minimum_enforced(self) -> None:
        """Test adaptive overlap enforces minimum."""
        config = {
            "agents": {"detection": {"scan_overlap": {"audit_overlap_seconds": 300}}}
        }
        manager = ScanOverlapManager(config)

        # Even with zero delay and error rate, should not go below base
        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=0, error_rate=0.0
        )

        assert overlap >= 300

    def test_get_adaptive_overlap_unknown_log_type(self) -> None:
        """Test adaptive overlap with unknown log type."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "unknown", processing_delay=100, error_rate=0.05
        )

        # Should use default overlap as base
        assert overlap >= 60

    def test_validate_scan_continuity_insufficient_history(self) -> None:
        """Test continuity validation with insufficient history."""
        manager = ScanOverlapManager({})

        is_continuous, gaps = manager.validate_scan_continuity("audit", window_count=3)

        assert not is_continuous
        assert len(gaps) == 0  # No gaps reported for insufficient history

    def test_validate_scan_continuity_one_window(self) -> None:
        """Test continuity validation with single window."""
        manager = ScanOverlapManager({})

        window = ScanWindow(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0),
        )
        manager._add_to_history("audit", window)

        is_continuous, gaps = manager.validate_scan_continuity("audit", window_count=1)

        assert is_continuous
        assert len(gaps) == 0

    def test_validate_scan_continuity_continuous(self) -> None:
        """Test continuity validation with continuous windows."""
        manager = ScanOverlapManager({})

        # Add continuous windows
        window1 = ScanWindow(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0),
        )
        window2 = ScanWindow(
            start_time=datetime(2024, 1, 1, 11, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 0, 0),
        )

        manager._add_to_history("audit", window1)
        manager._add_to_history("audit", window2)

        is_continuous, gaps = manager.validate_scan_continuity("audit", window_count=2)

        assert is_continuous
        assert len(gaps) == 0

    def test_validate_scan_continuity_with_gaps(self) -> None:
        """Test continuity validation with gaps."""
        manager = ScanOverlapManager({})

        # Add windows with a gap
        window1 = ScanWindow(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0),
        )
        window2 = ScanWindow(
            start_time=datetime(2024, 1, 1, 12, 0, 0),  # Gap from 11:00 to 12:00
            end_time=datetime(2024, 1, 1, 13, 0, 0),
        )

        manager._add_to_history("audit", window1)
        manager._add_to_history("audit", window2)

        is_continuous, gaps = manager.validate_scan_continuity("audit", window_count=2)

        assert not is_continuous
        assert len(gaps) == 1
        assert gaps[0] == (
            datetime(2024, 1, 1, 11, 0, 0),
            datetime(2024, 1, 1, 12, 0, 0),
        )

    def test_validate_scan_continuity_multiple_gaps(self) -> None:
        """Test continuity validation with multiple gaps."""
        manager = ScanOverlapManager({})

        # Add windows with multiple gaps
        window1 = ScanWindow(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0),
        )
        window2 = ScanWindow(
            start_time=datetime(2024, 1, 1, 12, 0, 0),  # Gap 1: 11:00-12:00
            end_time=datetime(2024, 1, 1, 13, 0, 0),
        )
        window3 = ScanWindow(
            start_time=datetime(2024, 1, 1, 14, 0, 0),  # Gap 2: 13:00-14:00
            end_time=datetime(2024, 1, 1, 15, 0, 0),
        )

        manager._add_to_history("audit", window1)
        manager._add_to_history("audit", window2)
        manager._add_to_history("audit", window3)

        is_continuous, gaps = manager.validate_scan_continuity("audit", window_count=3)

        assert not is_continuous
        assert len(gaps) == 2

    def test_get_scan_statistics_empty(self) -> None:
        """Test statistics with no scan history."""
        manager = ScanOverlapManager({})

        stats = manager.get_scan_statistics()

        assert stats["total_log_types"] == 0
        assert stats["total_windows"] == 0

    def test_get_scan_statistics_single_log_type(self) -> None:
        """Test statistics with single log type."""
        manager = ScanOverlapManager({})

        # Add windows for one log type
        for i in range(3):
            window = ScanWindow(
                start_time=datetime(2024, 1, 1, 10 + i, 0, 0),
                end_time=datetime(2024, 1, 1, 11 + i, 0, 0),
            )
            manager._add_to_history("audit", window)

        stats = manager.get_scan_statistics()

        assert stats["total_log_types"] == 1
        assert stats["total_windows"] == 3
        assert stats["log_types"]["audit"]["window_count"] == 3
        assert "earliest_scan" in stats["log_types"]["audit"]
        assert "latest_scan" in stats["log_types"]["audit"]

    def test_get_scan_statistics_multiple_log_types(self) -> None:
        """Test statistics with multiple log types."""
        manager = ScanOverlapManager({})

        # Add windows for multiple log types
        audit_window = ScanWindow(
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 0, 0),
        )
        vpc_window = ScanWindow(
            start_time=datetime(2024, 1, 1, 11, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 0, 0),
        )

        manager._add_to_history("audit", audit_window)
        manager._add_to_history("vpc_flow", vpc_window)

        stats = manager.get_scan_statistics()

        assert stats["total_log_types"] == 2
        assert stats["total_windows"] == 2
        assert "audit" in stats["log_types"]
        assert "vpc_flow" in stats["log_types"]

    def test_get_scan_statistics_empty_windows_list(self) -> None:
        """Test statistics with empty windows list."""
        manager = ScanOverlapManager({})
        manager.scan_history["audit"] = []  # Explicitly empty

        stats = manager.get_scan_statistics()

        assert stats["total_log_types"] == 1  # Log type exists but no windows
        assert stats["total_windows"] == 0

    def test_edge_case_extremely_large_overlap(self) -> None:
        """Test with extremely large overlap values."""
        config = {
            "agents": {"detection": {"scan_overlap": {"max_overlap_seconds": 10000}}}
        }
        manager = ScanOverlapManager(config)

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=5000, error_rate=0.9
        )

        assert overlap <= 10000
        assert overlap > 60

    def test_edge_case_zero_processing_delay(self) -> None:
        """Test with zero processing delay."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=0, error_rate=0.0
        )

        assert overlap == 60  # Should be base overlap

    def test_edge_case_negative_processing_delay(self) -> None:
        """Test with negative processing delay."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=-100, error_rate=0.0
        )

        assert overlap >= 60  # Should not go below base

    def test_edge_case_error_rate_above_one(self) -> None:
        """Test with error rate above 1.0."""
        manager = ScanOverlapManager({})

        overlap = manager.get_adaptive_overlap(
            "audit", processing_delay=0, error_rate=1.5
        )

        assert overlap <= manager.max_overlap_seconds

    def test_edge_case_very_short_time_windows(self) -> None:
        """Test with very short time windows."""
        manager = ScanOverlapManager({})

        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 10, 0, 1)  # 1 second window

        window = manager.calculate_scan_window("audit", start, end)

        assert window.start_time == start
        assert window.end_time == end
        assert window.overlap_seconds > 0

    def test_edge_case_same_start_end_time(self) -> None:
        """Test with same start and end time."""
        manager = ScanOverlapManager({})

        timestamp = datetime(2024, 1, 1, 10, 0, 0)

        window = manager.calculate_scan_window("audit", timestamp, timestamp)

        assert window.start_time == timestamp
        assert window.end_time == timestamp

    def test_logging_integration(self) -> None:
        """Test that methods don't fail when logging is called."""
        manager = ScanOverlapManager({})

        # These should not raise exceptions even if logging is called
        last_scan = datetime(2024, 1, 1, 10, 0, 0)
        current_time = datetime(2024, 1, 1, 11, 0, 0)

        window = manager.calculate_scan_window("audit", last_scan, current_time)
        gaps = manager.detect_gaps("audit", last_scan, current_time)
        stats = manager.get_scan_statistics()

        assert window is not None
        assert isinstance(gaps, list)
        assert isinstance(stats, dict)

    def test_comprehensive_workflow(self) -> None:
        """Test comprehensive workflow combining multiple features."""
        config = {
            "agents": {
                "detection": {
                    "scan_overlap": {
                        "default_overlap_seconds": 90,
                        "audit_overlap_seconds": 120,
                        "vpc_flow_overlap_seconds": 360,
                        "max_overlap_seconds": 900,
                        "max_history_entries": 50,
                    }
                }
            }
        }
        manager = ScanOverlapManager(config)

        # Simulate a series of scans
        current_time = datetime(2024, 1, 1, 10, 0, 0)

        for i in range(5):
            last_scan = current_time
            current_time = current_time + timedelta(hours=1)

            # Calculate scan window with adaptive overlap
            adaptive_overlap = manager.get_adaptive_overlap(
                "audit", processing_delay=i * 30, error_rate=i * 0.02
            )

            window = manager.calculate_scan_window(
                "audit", last_scan, current_time, force_overlap=adaptive_overlap
            )

            # Verify window properties
            assert window.start_time == last_scan
            assert window.end_time == current_time
            assert window.overlap_seconds >= 120  # At least base overlap

        # Validate scan continuity
        is_continuous, gaps = manager.validate_scan_continuity("audit", window_count=5)

        # Get statistics
        stats = manager.get_scan_statistics()

        # Verify results
        assert len(manager.scan_history["audit"]) == 5
        assert is_continuous
        assert len(gaps) == 0
        assert stats["total_log_types"] == 1
        assert stats["total_windows"] == 5

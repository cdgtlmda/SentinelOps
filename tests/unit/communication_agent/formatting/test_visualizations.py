#!/usr/bin/env python3
"""
Comprehensive tests for visualization generators.

Tests ALL functionality in ChartGenerator and TimelineGenerator classes
using 100% production code with NO MOCKING.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict

from src.communication_agent.formatting.visualizations import (
    ChartGenerator,
    TimelineGenerator,
)


# Test fixtures
@pytest.fixture
def sample_data() -> Dict[str, float]:
    """Sample data for testing chart generation."""
    return {"CPU": 75.0, "Memory": 60.0, "Disk": 45.0}


class TestChartGenerator:
    """Test ChartGenerator functionality with real data scenarios."""

    def test_bar_chart_basic(self) -> None:
        """Test basic bar chart generation."""
        data = {"CPU": 75.0, "Memory": 60.0, "Disk": 45.0}
        result = ChartGenerator.bar_chart(data)

        assert "CPU" in result
        assert "Memory" in result
        assert "Disk" in result
        assert "│" in result
        assert "█" in result
        assert "75.0" in result
        assert "60.0" in result
        assert "45.0" in result

    def test_bar_chart_empty_data(self) -> None:
        """Test bar chart with empty data."""
        result = ChartGenerator.bar_chart({})
        assert result == "No data available"

    def test_bar_chart_zero_values(self) -> None:
        """Test bar chart with zero values."""
        data = {"Item1": 0.0, "Item2": 0.0, "Item3": 0.0}
        result = ChartGenerator.bar_chart(data)

        assert "Item1" in result
        assert "Item2" in result
        assert "Item3" in result
        assert "│" in result

    def test_bar_chart_custom_width(self) -> None:
        """Test bar chart with custom width."""
        data = {"Test": 50.0}
        result_default = ChartGenerator.bar_chart(data)
        result_custom = ChartGenerator.bar_chart(data, width=20)

        # Custom width should have fewer bars for same value
        assert len(result_custom.split("█")) <= len(result_default.split("█"))

    def test_bar_chart_without_values(self) -> None:
        """Test bar chart without showing values."""
        data = {"CPU": 75.0, "Memory": 60.0}
        result = ChartGenerator.bar_chart(data, show_values=False)

        assert "CPU" in result
        assert "Memory" in result
        assert "75.0" not in result
        assert "60.0" not in result

    def test_bar_chart_custom_character(self) -> None:
        """Test bar chart with custom character."""
        data = {"Test": 50.0}
        result = ChartGenerator.bar_chart(data, char="▓")

        assert "▓" in result
        assert "█" not in result

    def test_sparkline_basic(self) -> None:
        """Test basic sparkline generation."""
        values = [10.0, 20.0, 15.0, 30.0, 25.0]
        result = ChartGenerator.sparkline(values)

        # Should contain Unicode block characters
        assert len(result) == len(values)
        assert all(c in "▁▂▃▄▅▆▇█" for c in result)

    def test_sparkline_empty(self) -> None:
        """Test sparkline with empty values."""
        result = ChartGenerator.sparkline([])
        assert result == ""

    def test_sparkline_same_values(self) -> None:
        """Test sparkline with identical values."""
        values = [50.0, 50.0, 50.0, 50.0]
        result = ChartGenerator.sparkline(values)

        # All should be same character (middle range)
        assert len(set(result)) == 1
        assert result[0] in "▁▂▃▄▅▆▇█"

    def test_sparkline_with_width_limit(self) -> None:
        """Test sparkline with width limitation."""
        values = [float(i) for i in range(100)]  # 100 values as floats
        result = ChartGenerator.sparkline(values, width=20)

        assert len(result) == 20

    def test_pie_chart_basic(self) -> None:
        """Test basic pie chart generation."""
        data = {"Critical": 5.0, "High": 15.0, "Medium": 25.0, "Low": 55.0}
        result = ChartGenerator.pie_chart(data)

        assert "Critical" in result
        assert "High" in result
        assert "Medium" in result
        assert "Low" in result
        assert "%" in result
        assert "◼" in result
        assert "◻" in result

    def test_pie_chart_empty_data(self) -> None:
        """Test pie chart with empty data."""
        result = ChartGenerator.pie_chart({})
        assert result == "No data available"

    def test_pie_chart_zero_total(self) -> None:
        """Test pie chart with zero total."""
        data = {"Item1": 0.0, "Item2": 0.0}
        result = ChartGenerator.pie_chart(data)
        assert result == "No data available"

    def test_pie_chart_custom_size(self) -> None:
        """Test pie chart with custom size."""
        data = {"A": 50.0, "B": 50.0}
        result = ChartGenerator.pie_chart(data, size=5)

        # Should contain blocks and percentages
        assert "50.0%" in result
        assert "◼" in result or "◻" in result

    def test_trend_indicator_increase(self) -> None:
        """Test trend indicator for increasing values."""
        result = ChartGenerator.trend_indicator(120.0, 100.0)

        assert "120.0" in result
        assert "↑" in result
        assert "+20.0%" in result

    def test_trend_indicator_decrease(self) -> None:
        """Test trend indicator for decreasing values."""
        result = ChartGenerator.trend_indicator(80.0, 100.0)

        assert "80.0" in result
        assert "↓" in result
        assert "-20.0%" in result

    def test_trend_indicator_no_change(self) -> None:
        """Test trend indicator for no change."""
        result = ChartGenerator.trend_indicator(100.0, 100.0)

        assert "100.0" in result
        assert "→" in result
        assert "0.0%" in result

    def test_trend_indicator_zero_previous(self) -> None:
        """Test trend indicator with zero previous value."""
        result = ChartGenerator.trend_indicator(50.0, 0.0)

        assert "50.0" in result
        assert "(—)" in result

    def test_trend_indicator_without_percentage(self) -> None:
        """Test trend indicator without percentage."""
        result = ChartGenerator.trend_indicator(120.0, 100.0, show_percentage=False)

        assert "120.0" in result
        assert "↑" in result
        assert "+20" in result
        assert "%" not in result

    def test_heatmap_basic(self) -> None:
        """Test basic heatmap generation."""
        data = [[10.0, 20.0, 30.0], [40.0, 50.0, 60.0], [70.0, 80.0, 90.0]]
        row_labels = ["Row1", "Row2", "Row3"]
        col_labels = ["Col1", "Col2", "Col3"]

        result = ChartGenerator.heatmap(data, row_labels, col_labels)

        assert "Row1" in result
        assert "Col1" in result
        assert all(
            c in " ·░▒▓█"
            for line in result.split("\n")
            for c in line
            if c not in "Row123 Col|-"
        )

    def test_heatmap_empty_data(self) -> None:
        """Test heatmap with empty data."""
        result = ChartGenerator.heatmap([])
        assert result == "No data available"

    def test_heatmap_no_labels(self) -> None:
        """Test heatmap without labels."""
        data = [[10.0, 20.0], [30.0, 40.0]]
        result = ChartGenerator.heatmap(data)

        # Should contain heat characters
        assert any(c in " ·░▒▓█" for c in result)

    def test_heatmap_same_values(self) -> None:
        """Test heatmap with identical values."""
        data = [[50.0, 50.0], [50.0, 50.0]]
        result = ChartGenerator.heatmap(data)

        # All should use middle heat character
        heat_lines = [
            line for line in result.split("\n") if any(c in " ·░▒▓█" for c in line)
        ]
        assert len(heat_lines) > 0


class TestTimelineGenerator:
    """Test TimelineGenerator functionality with real timeline scenarios."""

    def test_event_timeline_basic(self) -> None:
        """Test basic event timeline generation."""
        now = datetime.now(timezone.utc)
        events = [
            {"time": now, "label": "Event 1"},
            {"time": now + timedelta(minutes=30), "label": "Event 2"},
            {"time": now + timedelta(hours=1), "label": "Event 3"},
        ]

        result = TimelineGenerator.event_timeline(events)

        assert "Event 1" in result
        assert "Event 2" in result
        assert "Event 3" in result
        assert "┼" in result  # Timeline markers
        assert "└─" in result  # Event connectors

    def test_event_timeline_empty(self) -> None:
        """Test event timeline with no events."""
        result = TimelineGenerator.event_timeline([])
        assert result == "No events"

    def test_event_timeline_same_time(self) -> None:
        """Test event timeline with events at same time."""
        now = datetime.now(timezone.utc)
        events = [
            {"time": now, "label": "Event 1"},
            {"time": now, "label": "Event 2"},
            {"time": now, "label": "Event 3"},
        ]

        result = TimelineGenerator.event_timeline(events)

        assert "Event 1" in result
        assert "Event 2" in result
        assert "Event 3" in result
        assert "├─" in result

    def test_event_timeline_with_severity(self) -> None:
        """Test event timeline with severity indicators."""
        now = datetime.now(timezone.utc)
        events = [
            {"time": now, "label": "Critical Alert", "severity": "critical"},
            {
                "time": now + timedelta(minutes=10),
                "label": "High Alert",
                "severity": "high",
            },
            {
                "time": now + timedelta(minutes=20),
                "label": "Medium Alert",
                "severity": "medium",
            },
            {
                "time": now + timedelta(minutes=30),
                "label": "Low Alert",
                "severity": "low",
            },
        ]

        result = TimelineGenerator.event_timeline(events)

        assert "Critical Alert" in result
        assert "High Alert" in result
        assert "Medium Alert" in result
        assert "Low Alert" in result

    def test_event_timeline_custom_width(self) -> None:
        """Test event timeline with custom width."""
        now = datetime.now(timezone.utc)
        events = [
            {"time": now, "label": "Start"},
            {"time": now + timedelta(hours=1), "label": "End"},
        ]

        result = TimelineGenerator.event_timeline(events, width=30)

        # Should contain timeline elements
        assert "Start" in result
        assert "End" in result

    def test_gantt_chart_basic(self) -> None:
        """Test basic Gantt chart generation."""
        now = datetime.now(timezone.utc)
        tasks = [
            {
                "name": "Task 1",
                "start": now,
                "end": now + timedelta(hours=2),
                "status": "completed",
            },
            {
                "name": "Task 2",
                "start": now + timedelta(hours=1),
                "end": now + timedelta(hours=4),
                "status": "in_progress",
            },
            {
                "name": "Task 3",
                "start": now + timedelta(hours=3),
                "end": now + timedelta(hours=5),
                "status": "pending",
            },
        ]

        result = TimelineGenerator.gantt_chart(tasks)

        assert "Task 1" in result
        assert "Task 2" in result
        assert "Task 3" in result
        assert "█" in result  # Completed task
        assert "▓" in result  # In progress task
        assert "░" in result  # Pending task
        assert "Gantt Chart" in result

    def test_gantt_chart_empty(self) -> None:
        """Test Gantt chart with no tasks."""
        result = TimelineGenerator.gantt_chart([])
        assert result == "No tasks"

    def test_gantt_chart_no_duration(self) -> None:
        """Test Gantt chart with zero duration."""
        now = datetime.now(timezone.utc)
        tasks = [
            {"name": "Task 1", "start": now, "end": now},
            {"name": "Task 2", "start": now, "end": now},
        ]

        result = TimelineGenerator.gantt_chart(tasks)
        assert result == "No duration"

    def test_gantt_chart_custom_width(self) -> None:
        """Test Gantt chart with custom width."""
        now = datetime.now(timezone.utc)
        tasks = [
            {
                "name": "Test Task",
                "start": now,
                "end": now + timedelta(hours=1),
                "status": "completed",
            }
        ]

        result = TimelineGenerator.gantt_chart(tasks, width=20)

        assert "Test Task" in result
        assert "█" in result

    def test_progress_bar_basic(self) -> None:
        """Test basic progress bar generation."""
        result = TimelineGenerator.progress_bar(75, 100)

        assert "[" in result
        assert "]" in result
        assert "█" in result
        assert "░" in result
        assert "75.0%" in result
        assert "(75/100)" in result

    def test_progress_bar_zero_total(self) -> None:
        """Test progress bar with zero total."""
        result = TimelineGenerator.progress_bar(10, 0)

        assert "0.0%" in result
        assert "(10/0)" in result

    def test_progress_bar_complete(self) -> None:
        """Test progress bar at 100%."""
        result = TimelineGenerator.progress_bar(100, 100)

        assert "100.0%" in result
        assert "█" in result

    def test_progress_bar_without_percentage(self) -> None:
        """Test progress bar without percentage display."""
        result = TimelineGenerator.progress_bar(50, 100, show_percentage=False)

        assert "%" not in result
        assert "50/100" in result

    def test_progress_bar_custom_width(self) -> None:
        """Test progress bar with custom width."""
        result = TimelineGenerator.progress_bar(50, 100, width=10)

        # Should contain 5 filled and 5 empty characters
        bar_part = result.split("]")[0].split("[")[1]
        assert len(bar_part) == 10

    def test_status_timeline_basic(self) -> None:
        """Test basic status timeline generation."""
        now = datetime.now(timezone.utc)
        statuses = [
            (now, "System Started", True),
            (now + timedelta(minutes=10), "Error Detected", False),
            (now + timedelta(minutes=20), "Error Resolved", True),
            (now + timedelta(minutes=30), "System Healthy", True),
        ]

        result = TimelineGenerator.status_timeline(statuses)

        assert "System Started" in result
        assert "Error Detected" in result
        assert "Error Resolved" in result
        assert "System Healthy" in result
        assert "✅" in result  # Success indicator
        assert "❌" in result  # Failure indicator
        assert "┌─" in result  # First item
        assert "└─" in result  # Last item
        assert "├─" in result  # Middle items

    def test_status_timeline_empty(self) -> None:
        """Test status timeline with no statuses."""
        result = TimelineGenerator.status_timeline([])
        assert result == "No status history"

    def test_status_timeline_single_status(self) -> None:
        """Test status timeline with single status."""
        now = datetime.now(timezone.utc)
        statuses = [(now, "Single Event", True)]

        result = TimelineGenerator.status_timeline(statuses)

        assert "Single Event" in result
        assert "✅" in result
        assert "┌─" in result

    def test_status_timeline_sorting(self) -> None:
        """Test status timeline with unsorted input."""
        now = datetime.now(timezone.utc)
        statuses = [
            (now + timedelta(minutes=20), "Third Event", True),
            (now, "First Event", True),
            (now + timedelta(minutes=10), "Second Event", False),
        ]

        result = TimelineGenerator.status_timeline(statuses)
        lines = result.split("\n")

        # Should be sorted by time
        assert "First Event" in lines[0]
        assert "Second Event" in lines[1]
        assert "Third Event" in lines[2]


class TestVisualizationEdgeCases:
    """Test edge cases and error conditions for both generators."""

    def test_large_numbers(self) -> None:
        """Test visualizations with very large numbers."""
        data = {"Item1": 1000000.0, "Item2": 999999.0, "Item3": 1000001.0}
        result = ChartGenerator.bar_chart(data)

        assert "1000000.0" in result
        assert "999999.0" in result
        assert "1000001.0" in result

    def test_negative_numbers(self) -> None:
        """Test visualizations with negative numbers."""
        data = {"Profit": 100.0, "Loss": -50.0}
        result = ChartGenerator.bar_chart(data)

        assert "Profit" in result
        assert "Loss" in result

    def test_float_precision(self) -> None:
        """Test handling of float precision."""
        data = {"Value1": 33.333333, "Value2": 66.666666}
        result = ChartGenerator.bar_chart(data)

        assert "Value1" in result
        assert "Value2" in result

    def test_unicode_labels(self) -> None:
        """Test visualizations with Unicode labels."""
        data = {"CPU使用率": 75.0, "メモリ": 60.0, "🔥Critical": 90.0}
        result = ChartGenerator.bar_chart(data)

        assert "CPU使用率" in result
        assert "メモリ" in result
        assert "🔥Critical" in result

    def test_very_long_labels(self) -> None:
        """Test visualizations with very long labels."""
        data = {"Very_Long_Label_That_Should_Still_Work_Properly": 50.0}
        result = ChartGenerator.bar_chart(data)

        assert "Very_Long_Label_That_Should_Still_Work_Properly" in result

    def test_extreme_sparkline_values(self) -> None:
        """Test sparkline with extreme value ranges."""
        values = [0.001, 1000000.0, 0.002, 999999.0]
        result = ChartGenerator.sparkline(values)

        assert len(result) == 4
        assert all(c in "▁▂▃▄▅▆▇█" for c in result)

    def test_timeline_distant_future(self) -> None:
        """Test timeline with dates far in the future."""
        base = datetime(2030, 1, 1, tzinfo=timezone.utc)
        events = [
            {"time": base, "label": "Future Event 1"},
            {"time": base + timedelta(days=365), "label": "Future Event 2"},
        ]

        result = TimelineGenerator.event_timeline(events)

        assert "Future Event 1" in result
        assert "Future Event 2" in result


if __name__ == "__main__":
    pytest.main([__file__])

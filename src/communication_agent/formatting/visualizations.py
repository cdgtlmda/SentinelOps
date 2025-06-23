"""
Visualization generators for message formatting.

Provides ASCII-based charts and timeline visualizations for
cross-platform compatibility.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ChartGenerator:
    """Generator for ASCII-based charts and graphs."""

    @staticmethod
    def bar_chart(
        data: Dict[str, float],
        width: int = 40,
        show_values: bool = True,
        char: str = "█",
    ) -> str:
        """
        Generate a horizontal bar chart.

        Args:
            data: Dictionary of labels to values
            width: Maximum bar width
            show_values: Whether to show values
            char: Character to use for bars

        Returns:
            ASCII bar chart
        """
        if not data:
            return "No data available"

        # Find max value and label length
        max_value = max(data.values()) if data.values() else 1
        max_label_len = max(len(str(label)) for label in data.keys())

        lines = []
        for label, value in data.items():
            # Calculate bar length
            bar_length = int((value / max_value) * width) if max_value > 0 else 0
            bar_str = char * bar_length

            # Format line
            label_str = str(label).ljust(max_label_len)
            if show_values:
                line = f"{label_str} │ {bar_str} {value}"
            else:
                line = f"{label_str} │ {bar_str}"

            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def sparkline(
        values: List[float],
        width: Optional[int] = None,
    ) -> str:
        """
        Generate a sparkline chart.

        Args:
            values: List of values
            width: Optional width limit

        Returns:
            Unicode sparkline
        """
        if not values:
            return ""

        # Sparkline characters
        sparks = "▁▂▃▄▅▆▇█"

        # Limit values if width specified
        if width and len(values) > width:
            # Sample values to fit width
            step = len(values) / width
            sampled = []
            for i in range(width):
                idx = int(i * step)
                sampled.append(values[idx])
            values = sampled

        # Normalize values
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val

        if range_val == 0:
            # All values are the same
            return sparks[4] * len(values)

        # Convert to sparkline
        sparkline = ""
        for value in values:
            normalized = (value - min_val) / range_val
            index = int(normalized * (len(sparks) - 1))
            sparkline += sparks[index]

        return sparkline

    @staticmethod
    def pie_chart(
        data: Dict[str, float],
        size: int = 10,
    ) -> str:
        """
        Generate a simple ASCII pie chart representation.

        Args:
            data: Dictionary of labels to values
            size: Size of the chart

        Returns:
            ASCII pie chart representation
        """
        if not data:
            return "No data available"

        total = sum(data.values())
        if total == 0:
            return "No data available"

        # Calculate percentages
        percentages = []
        for label, value in data.items():
            percentage = (value / total) * 100
            percentages.append((label, value, percentage))

        # Sort by percentage descending
        percentages.sort(key=lambda x: x[2], reverse=True)

        # Build chart
        lines = []
        for label, value, percentage in percentages:
            # Create a simple bar representation
            bar_length = int((percentage / 100) * size)
            bar_str = "◼" * bar_length + "◻" * (size - bar_length)
            lines.append(f"{label:.<20} {bar_str} {percentage:5.1f}% ({value})")

        return "\n".join(lines)

    @staticmethod
    def trend_indicator(
        current: float,
        previous: float,
        show_percentage: bool = True,
    ) -> str:
        """
        Generate a trend indicator.

        Args:
            current: Current value
            previous: Previous value
            show_percentage: Whether to show percentage change

        Returns:
            Trend indicator string
        """
        if previous == 0:
            return f"{current} (—)"

        change = current - previous
        percentage = (change / previous) * 100

        if change > 0:
            arrow = "↑"
            sign = "+"
        elif change < 0:
            arrow = "↓"
            sign = ""
        else:
            arrow = "→"
            sign = ""

        if show_percentage:
            return f"{current} ({arrow} {sign}{percentage:.1f}%)"
        else:
            return f"{current} ({arrow} {sign}{change})"

    @staticmethod
    def heatmap(
        data: List[List[float]],
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a simple heatmap.

        Args:
            data: 2D array of values
            row_labels: Labels for rows
            col_labels: Labels for columns

        Returns:
            ASCII heatmap
        """
        if not data or not data[0]:
            return "No data available"

        # Heat characters (light to dark)
        heat_chars = " ·░▒▓█"

        # Find min/max values
        flat_data = [val for row in data for val in row]
        min_val = min(flat_data)
        max_val = max(flat_data)
        range_val = max_val - min_val

        lines = []

        # Add column headers if provided
        if col_labels:
            header = "      " if row_labels else ""
            header += " ".join(f"{label:^3}" for label in col_labels[: len(data[0])])
            lines.append(header)
            lines.append(
                "      " + "-" * (4 * len(data[0]))
                if row_labels
                else "-" * (4 * len(data[0]))
            )

        # Build heatmap
        for i, row in enumerate(data):
            line = ""
            if row_labels and i < len(row_labels):
                line = f"{row_labels[i]:>5} "

            for val in row:
                if range_val == 0:
                    index = len(heat_chars) // 2
                else:
                    normalized = (val - min_val) / range_val
                    index = int(normalized * (len(heat_chars) - 1))
                line += f" {heat_chars[index]}  "

            lines.append(line)

        return "\n".join(lines)


class TimelineGenerator:
    """Generator for timeline visualizations."""

    @staticmethod
    def event_timeline(
        events: List[Dict[str, Any]],
        width: int = 60,
    ) -> str:
        """
        Generate an event timeline.

        Args:
            events: List of events with 'time' and 'label' keys
            width: Width of the timeline

        Returns:
            ASCII timeline
        """
        if not events:
            return "No events"

        sorted_events = TimelineGenerator._sort_events_by_time(events)
        times = TimelineGenerator._extract_event_times(sorted_events)
        start_time = min(times)
        end_time = max(times)
        time_range = (end_time - start_time).total_seconds()

        if time_range == 0:
            return TimelineGenerator._create_same_time_timeline(sorted_events)

        positions = TimelineGenerator._calculate_event_positions(
            sorted_events, start_time, time_range, width
        )

        timeline_line = TimelineGenerator._create_timeline_with_markers(positions, width)
        event_lines = TimelineGenerator._create_event_labels(positions)
        time_labels = TimelineGenerator._create_time_labels(start_time, end_time, width)

        return "\n".join([timeline_line] + event_lines + ["", time_labels])

    @staticmethod
    def _sort_events_by_time(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort events by their time attribute."""
        return sorted(events, key=lambda x: x.get("time", datetime.now(timezone.utc)))

    @staticmethod
    def _extract_event_times(events: List[Dict[str, Any]]) -> List[datetime]:
        """Extract times from events."""
        return [e.get("time", datetime.now(timezone.utc)) for e in events]

    @staticmethod
    def _create_same_time_timeline(events: List[Dict[str, Any]]) -> str:
        """Create timeline for events at the same time."""
        lines = ["│"]
        for event in events:
            lines.append(f"├─ {event.get('label', 'Event')}")
        lines.append("│")
        return "\n".join(lines)

    @staticmethod
    def _calculate_event_positions(
        events: List[Dict[str, Any]],
        start_time: datetime,
        time_range: float,
        width: int
    ) -> List[Tuple[int, Dict[str, Any]]]:
        """Calculate positions of events on the timeline."""
        positions = []
        for event in events:
            event_time = event.get("time", datetime.now(timezone.utc))
            offset = (event_time - start_time).total_seconds()
            position = int((offset / time_range) * (width - 1))
            positions.append((position, event))
        return positions

    @staticmethod
    def _create_timeline_with_markers(
        positions: List[Tuple[int, Dict[str, Any]]],
        width: int
    ) -> str:
        """Create timeline line with event markers."""
        timeline_chars = list("─" * width)
        for pos, _ in positions:
            if 0 <= pos < width:
                timeline_chars[pos] = "┼"
        return "".join(timeline_chars)

    @staticmethod
    def _get_severity_indicator(severity: str) -> str:
        """Get indicator symbol for severity level."""
        severity_indicators = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        return severity_indicators.get(severity.lower(), "•")

    @staticmethod
    def _create_event_labels(
        positions: List[Tuple[int, Dict[str, Any]]]
    ) -> List[str]:
        """Create event label lines."""
        lines = []
        for pos, event in positions:
            label = event.get("label", "Event")
            severity = event.get("severity", "")
            indicator = TimelineGenerator._get_severity_indicator(severity)

            padding = " " * pos
            lines.append(f"{padding}│")
            lines.append(f"{padding}└─ {indicator} {label}")
        return lines

    @staticmethod
    def _create_time_labels(start_time: datetime, end_time: datetime, width: int) -> str:
        """Create time labels for timeline."""
        return f"{start_time.strftime('%H:%M')}{' ' * (width - 10)}{end_time.strftime('%H:%M')}"

    @staticmethod
    def gantt_chart(
        tasks: List[Dict[str, Any]],
        width: int = 50,
    ) -> str:
        """
        Generate a Gantt chart for tasks.

        Args:
            tasks: List of tasks with 'name', 'start', 'end' keys
            width: Width of the chart

        Returns:
            ASCII Gantt chart
        """
        if not tasks:
            return "No tasks"

        # Get overall time range
        all_starts = [t.get("start", datetime.now(timezone.utc)) for t in tasks]
        all_ends = [t.get("end", datetime.now(timezone.utc)) for t in tasks]

        start_time = min(all_starts)
        end_time = max(all_ends)
        total_duration = (end_time - start_time).total_seconds()

        if total_duration == 0:
            return "No duration"

        # Find max task name length
        max_name_len = max(len(t.get("name", "Task")) for t in tasks)

        lines = []

        # Header
        lines.append(f"{'Task'.ljust(max_name_len)} │ {'Gantt Chart'.center(width)}")
        lines.append(f"{'-' * max_name_len} │ {'-' * width}")

        # Tasks
        for task in tasks:
            name = task.get("name", "Task").ljust(max_name_len)
            task_start = task.get("start", start_time)
            task_end = task.get("end", end_time)
            status = task.get("status", "pending")

            # Calculate position and length
            start_offset = (task_start - start_time).total_seconds()
            duration = (task_end - task_start).total_seconds()

            start_pos = int((start_offset / total_duration) * width)
            bar_length = max(1, int((duration / total_duration) * width))

            # Choose bar character based on status
            if status == "completed":
                bar_char = "█"
            elif status == "in_progress":
                bar_char = "▓"
            else:
                bar_char = "░"

            # Build bar
            timeline_bar = " " * start_pos + bar_char * bar_length
            if len(timeline_bar) > width:
                timeline_bar = timeline_bar[:width]
            else:
                timeline_bar = timeline_bar.ljust(width)

            lines.append(f"{name} │ {timeline_bar}")

        # Time labels
        lines.append(f"{' ' * max_name_len} │ {' ' * width}")
        lines.append(
            f"{' ' * max_name_len} │ "
            f"{start_time.strftime('%m/%d')}"
            f"{' ' * (width - 12)}"
            f"{end_time.strftime('%m/%d')}"
        )

        return "\n".join(lines)

    @staticmethod
    def progress_bar(
        current: int,
        total: int,
        width: int = 30,
        show_percentage: bool = True,
    ) -> str:
        """
        Generate a progress bar.

        Args:
            current: Current value
            total: Total value
            width: Bar width
            show_percentage: Whether to show percentage

        Returns:
            ASCII progress bar
        """
        if total == 0:
            percentage = 0.0
        else:
            percentage = (current / total) * 100

        filled_length = int((percentage / 100) * width)
        progress_bar = "█" * filled_length + "░" * (width - filled_length)

        if show_percentage:
            return f"[{progress_bar}] {percentage:.1f}% ({current}/{total})"
        else:
            return f"[{progress_bar}] {current}/{total}"

    @staticmethod
    def status_timeline(
        statuses: List[Tuple[datetime, str, bool]],
    ) -> str:
        """
        Generate a status timeline showing changes over time.

        Args:
            statuses: List of (timestamp, status, is_success) tuples

        Returns:
            ASCII status timeline
        """
        if not statuses:
            return "No status history"

        # Sort by timestamp
        sorted_statuses = sorted(statuses, key=lambda x: x[0])

        lines = []
        for i, (timestamp, status, is_success) in enumerate(sorted_statuses):
            # Choose indicator
            if is_success:
                indicator = "✅"
            else:
                indicator = "❌"

            # Format timestamp
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # Build line
            if i == 0:
                connector = "┌─"
            elif i == len(sorted_statuses) - 1:
                connector = "└─"
            else:
                connector = "├─"

            lines.append(f"{connector} {time_str} {indicator} {status}")

        return "\n".join(lines)

#!/usr/bin/env python3
"""Generate comprehensive coverage reports with analysis and visualization."""

import argparse
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from google.cloud import bigquery, storage
from jinja2 import Template

# Set style for better-looking plots
plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")


class CoverageReporter:
    """Generates comprehensive coverage reports with visualizations."""

    def __init__(self, project_id: str):
        """Initialize coverage reporter.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.bigquery_client = bigquery.Client()
        self.storage_client = storage.Client()

    def analyze_coverage_xml(self, coverage_xml_path: str) -> Dict:
        """Analyze coverage XML file and extract detailed metrics.

        Args:
            coverage_xml_path: Path to coverage.xml file

        Returns:
            Dictionary containing coverage analysis
        """
        tree = ET.parse(coverage_xml_path)
        root = tree.getroot()

        # Overall metrics
        overall_metrics = {
            "line_rate": float(root.get("line-rate", 0)),
            "branch_rate": float(root.get("branch-rate", 0)),
            "lines_covered": 0,
            "lines_total": 0,
            "branches_covered": 0,
            "branches_total": 0,
            "complexity": 0,
        }

        # Package-level metrics
        packages = {}

        # File-level metrics
        files = []

        # Process packages
        for package in root.findall(".//package"):
            package_name = package.get("name", "unknown")
            package_metrics = {
                "line_rate": float(package.get("line-rate", 0)),
                "branch_rate": float(package.get("branch-rate", 0)),
                "complexity": int(package.get("complexity", 0)),
                "files": [],
                "classes": [],
            }

            # Process classes
            for class_elem in package.findall(".//class"):
                class_info = {
                    "name": class_elem.get("name", ""),
                    "filename": class_elem.get("filename", ""),
                    "line_rate": float(class_elem.get("line-rate", 0)),
                    "branch_rate": float(class_elem.get("branch-rate", 0)),
                    "complexity": int(class_elem.get("complexity", 0)),
                    "lines": [],
                    "methods": [],
                }

                # Count lines
                lines_covered = 0
                lines_total = 0
                branches_covered = 0
                branches_total = 0

                for line in class_elem.findall(".//line"):
                    lines_total += 1
                    hits = int(line.get("hits", 0))
                    if hits > 0:
                        lines_covered += 1

                    # Track uncovered lines
                    if hits == 0:
                        class_info["lines"].append(
                            {
                                "number": int(line.get("number", 0)),
                                "hits": 0,
                                "branch": line.get("branch") == "true",
                            }
                        )

                    # Count branches
                    if line.get("branch") == "true":
                        branches_total += 1
                        condition_coverage = line.get("condition-coverage", "")
                        if "100%" in condition_coverage:
                            branches_covered += 1

                # Update totals
                overall_metrics["lines_covered"] += lines_covered
                overall_metrics["lines_total"] += lines_total
                overall_metrics["branches_covered"] += branches_covered
                overall_metrics["branches_total"] += branches_total
                overall_metrics["complexity"] += class_info["complexity"]

                # Process methods
                for method in class_elem.findall(".//method"):
                    method_info = {
                        "name": method.get("name", ""),
                        "signature": method.get("signature", ""),
                        "line_rate": float(method.get("line-rate", 0)),
                        "branch_rate": float(method.get("branch-rate", 0)),
                    }
                    class_info["methods"].append(method_info)

                package_metrics["classes"].append(class_info)

                # Add to files list
                files.append(
                    {
                        "path": class_info["filename"],
                        "package": package_name,
                        "line_coverage": (
                            (lines_covered / lines_total * 100)
                            if lines_total > 0
                            else 0
                        ),
                        "branch_coverage": (
                            (branches_covered / branches_total * 100)
                            if branches_total > 0
                            else 0
                        ),
                        "lines_covered": lines_covered,
                        "lines_total": lines_total,
                        "uncovered_lines": lines_total - lines_covered,
                        "complexity": class_info["complexity"],
                    }
                )

            packages[package_name] = package_metrics

        # Sort files by coverage
        files.sort(key=lambda x: x["line_coverage"])

        # Identify coverage gaps
        coverage_gaps = self._identify_coverage_gaps(packages, files)

        # Generate recommendations
        recommendations = self._generate_coverage_recommendations(
            overall_metrics, files, coverage_gaps
        )

        return {
            "overall": overall_metrics,
            "packages": packages,
            "files": files,
            "coverage_gaps": coverage_gaps,
            "recommendations": recommendations,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def generate_coverage_visualizations(self, analysis: Dict, output_dir: str):
        """Generate coverage visualization charts.

        Args:
            analysis: Coverage analysis data
            output_dir: Directory to save visualizations
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Overall coverage pie chart
        self._create_coverage_pie_chart(
            analysis["overall"], output_path / "overall_coverage.png"
        )

        # 2. Package coverage bar chart
        self._create_package_coverage_chart(
            analysis["packages"], output_path / "package_coverage.png"
        )

        # 3. File coverage heatmap
        self._create_file_coverage_heatmap(
            analysis["files"], output_path / "file_coverage_heatmap.png"
        )

        # 4. Coverage distribution histogram
        self._create_coverage_distribution(
            analysis["files"], output_path / "coverage_distribution.png"
        )

        # 5. Complexity vs coverage scatter plot
        self._create_complexity_coverage_plot(
            analysis["files"], output_path / "complexity_vs_coverage.png"
        )

        # 6. Coverage trends (if historical data available)
        self._create_coverage_trends(output_path / "coverage_trends.png")

    def generate_html_report(self, analysis: Dict, output_path: str):
        """Generate comprehensive HTML coverage report.

        Args:
            analysis: Coverage analysis data
            output_path: Path to save HTML report
        """
        template = Template(
            """
<!DOCTYPE html>
<html>
<head>
    <title>SentinelOps Coverage Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 14px;
        }
        .coverage-good { color: #27ae60; }
        .coverage-warning { color: #f39c12; }
        .coverage-critical { color: #e74c3c; }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #34495e;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .recommendation {
            background-color: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin-bottom: 10px;
        }
        .gap {
            background-color: #f8d7da;
            padding: 15px;
            border-left: 4px solid #dc3545;
            margin-bottom: 10px;
        }
        .chart-container {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
        img {
            max-width: 100%;
            height: auto;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>SentinelOps Coverage Report</h1>
        <p>Generated: {{ timestamp }}</p>
    </div>

    <div class="grid">
        <div class="metric-card">
            <div class="metric-value {{ coverage_class(overall.line_rate * 100) }}">
                {{ "%.1f" | format(overall.line_rate * 100) }}%
            </div>
            <div class="metric-label">Line Coverage</div>
            <small>{{ overall.lines_covered }} / {{ overall.lines_total }} lines</small>
        </div>

        <div class="metric-card">
            <div class="metric-value {{ coverage_class(overall.branch_rate * 100) }}">
                {{ "%.1f" | format(overall.branch_rate * 100) }}%
            </div>
            <div class="metric-label">Branch Coverage</div>
            <small>{{ overall.branches_covered }} / {{ overall.branches_total }} branches</small>
        </div>

        <div class="metric-card">
            <div class="metric-value">{{ overall.complexity }}</div>
            <div class="metric-label">Total Complexity</div>
        </div>

        <div class="metric-card">
            <div class="metric-value">{{ packages | length }}</div>
            <div class="metric-label">Packages</div>
        </div>
    </div>

    <div class="metric-card">
        <h2>Coverage Status</h2>
        {% if overall.line_rate >= 0.9 %}
        <p class="coverage-good">✅ Coverage meets target (90%+)</p>
        {% elif overall.line_rate >= 0.8 %}
        <p class="coverage-warning">⚠️ Coverage below target (80-90%)</p>
        {% else %}
        <p class="coverage-critical">❌ Coverage critically low (< 80%)</p>
        {% endif %}
    </div>

    <div class="metric-card">
        <h2>Recommendations</h2>
        {% for rec in recommendations %}
        <div class="recommendation">{{ rec }}</div>
        {% endfor %}
    </div>

    <div class="metric-card">
        <h2>Coverage Gaps</h2>
        {% for gap in coverage_gaps %}
        <div class="gap">
            <strong>{{ gap.type }}</strong>: {{ gap.description }}
            <br><small>Files: {{ gap.files | join(', ') }}</small>
        </div>
        {% endfor %}
    </div>

    <div class="chart-container">
        <h2>Overall Coverage Distribution</h2>
        <img src="overall_coverage.png" alt="Overall Coverage">
    </div>

    <div class="chart-container">
        <h2>Package Coverage</h2>
        <img src="package_coverage.png" alt="Package Coverage">
    </div>

    <div class="chart-container">
        <h2>File Coverage Heatmap</h2>
        <img src="file_coverage_heatmap.png" alt="File Coverage Heatmap">
    </div>

    <div class="metric-card">
        <h2>Files with Lowest Coverage</h2>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Line Coverage</th>
                    <th>Uncovered Lines</th>
                    <th>Complexity</th>
                </tr>
            </thead>
            <tbody>
                {% for file in files[:10] %}
                <tr>
                    <td>{{ file.path.split('/')[-1] }}</td>
                    <td class="{{ coverage_class(file.line_coverage) }}">
                        {{ "%.1f" | format(file.line_coverage) }}%
                    </td>
                    <td>{{ file.uncovered_lines }}</td>
                    <td>{{ file.complexity }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="chart-container">
        <h2>Coverage Distribution</h2>
        <img src="coverage_distribution.png" alt="Coverage Distribution">
    </div>

    <div class="chart-container">
        <h2>Complexity vs Coverage</h2>
        <img src="complexity_vs_coverage.png" alt="Complexity vs Coverage">
    </div>

    <div class="chart-container">
        <h2>Coverage Trends</h2>
        <img src="coverage_trends.png" alt="Coverage Trends">
    </div>
</body>
</html>
        """
        )

        # Define Jinja2 filter for coverage class
        def coverage_class(value):
            if value >= 90:
                return "coverage-good"
            elif value >= 80:
                return "coverage-warning"
            else:
                return "coverage-critical"

        # Render template
        html_content = template.render(
            **analysis,
            coverage_class=coverage_class,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

        # Save HTML
        with open(output_path, "w") as f:
            f.write(html_content)

    def _identify_coverage_gaps(self, packages: Dict, files: List[Dict]) -> List[Dict]:
        """Identify specific coverage gaps and patterns."""
        gaps = []

        # 1. Critical files with low coverage
        critical_patterns = ["auth", "security", "api", "handler", "service"]
        critical_files = [
            f
            for f in files
            if any(pattern in f["path"].lower() for pattern in critical_patterns)
            and f["line_coverage"] < 80
        ]

        if critical_files:
            gaps.append(
                {
                    "type": "Critical Files",
                    "description": f"{len(critical_files)} critical files have coverage below 80%",
                    "files": [f["path"] for f in critical_files[:5]],
                    "severity": "high",
                }
            )

        # 2. Error handling gaps
        error_files = [
            f
            for f in files
            if ("error" in f["path"].lower() or "exception" in f["path"].lower())
            and f["line_coverage"] < 70
        ]

        if error_files:
            gaps.append(
                {
                    "type": "Error Handling",
                    "description": f"{len(error_files)} error handling modules have insufficient coverage",
                    "files": [f["path"] for f in error_files[:5]],
                    "severity": "medium",
                }
            )

        # 3. Complex files with low coverage
        complex_files = [
            f for f in files if f["complexity"] > 10 and f["line_coverage"] < 85
        ]

        if complex_files:
            gaps.append(
                {
                    "type": "Complex Code",
                    "description": f"{len(complex_files)} complex files need better coverage",
                    "files": [f["path"] for f in complex_files[:5]],
                    "severity": "medium",
                }
            )

        # 4. Integration points
        integration_files = [
            f
            for f in files
            if ("client" in f["path"].lower() or "integration" in f["path"].lower())
            and f["line_coverage"] < 75
        ]

        if integration_files:
            gaps.append(
                {
                    "type": "Integration Points",
                    "description": f"{len(integration_files)} integration modules lack coverage",
                    "files": [f["path"] for f in integration_files[:5]],
                    "severity": "medium",
                }
            )

        # 5. New/modified files
        # This would check git history in a real implementation

        return gaps

    def _generate_coverage_recommendations(
        self, overall: Dict, files: List[Dict], gaps: List[Dict]
    ) -> List[str]:
        """Generate actionable coverage recommendations."""
        recommendations = []

        # Overall coverage recommendations
        line_coverage = overall["line_rate"] * 100
        if line_coverage < 80:
            recommendations.append(
                f"Critical: Overall line coverage is {line_coverage:.1f}%. "
                "Focus on writing tests for the most critical paths first."
            )
        elif line_coverage < 90:
            recommendations.append(
                f"Line coverage is {line_coverage:.1f}%. "
                "Target 90% coverage by adding tests for edge cases and error handling."
            )

        # Branch coverage recommendations
        branch_coverage = overall["branch_rate"] * 100
        if branch_coverage < line_coverage - 10:
            recommendations.append(
                "Branch coverage is significantly lower than line coverage. "
                "Add tests for different conditional paths and edge cases."
            )

        # File-specific recommendations
        uncovered_critical = len([f for f in files if f["line_coverage"] < 50])
        if uncovered_critical > 0:
            recommendations.append(
                f"{uncovered_critical} files have less than 50% coverage. "
                "Prioritize testing these files to avoid blind spots."
            )

        # Gap-based recommendations
        high_severity_gaps = [g for g in gaps if g.get("severity") == "high"]
        if high_severity_gaps:
            recommendations.append(
                "Address critical coverage gaps in security and authentication modules immediately."
            )

        # Complexity recommendations
        complex_low_coverage = len(
            [f for f in files if f["complexity"] > 15 and f["line_coverage"] < 80]
        )
        if complex_low_coverage > 0:
            recommendations.append(
                f"{complex_low_coverage} highly complex files have low coverage. "
                "Consider refactoring or increasing test coverage for these files."
            )

        return recommendations[:5]  # Top 5 recommendations

    def _create_coverage_pie_chart(self, overall: Dict, output_path: Path):
        """Create pie chart showing covered vs uncovered code."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Line coverage pie
        line_covered = overall["lines_covered"]
        line_uncovered = overall["lines_total"] - overall["lines_covered"]

        ax1.pie(
            [line_covered, line_uncovered],
            labels=["Covered", "Uncovered"],
            autopct="%1.1f%%",
            colors=["#27ae60", "#e74c3c"],
            startangle=90,
        )
        ax1.set_title("Line Coverage")

        # Branch coverage pie
        branch_covered = overall["branches_covered"]
        branch_uncovered = overall["branches_total"] - overall["branches_covered"]

        if overall["branches_total"] > 0:
            ax2.pie(
                [branch_covered, branch_uncovered],
                labels=["Covered", "Uncovered"],
                autopct="%1.1f%%",
                colors=["#27ae60", "#e74c3c"],
                startangle=90,
            )
        ax2.set_title("Branch Coverage")

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

    def _create_package_coverage_chart(self, packages: Dict, output_path: Path):
        """Create bar chart of package coverage."""
        if not packages:
            return

        # Prepare data
        package_names = []
        line_rates = []
        branch_rates = []

        for name, metrics in packages.items():
            package_names.append(name.split(".")[-1])  # Short name
            line_rates.append(metrics["line_rate"] * 100)
            branch_rates.append(metrics["branch_rate"] * 100)

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))

        x = range(len(package_names))
        width = 0.35

        bars1 = ax.bar(
            [i - width / 2 for i in x],
            line_rates,
            width,
            label="Line Coverage",
            color="#3498db",
        )
        bars2 = ax.bar(
            [i + width / 2 for i in x],
            branch_rates,
            width,
            label="Branch Coverage",
            color="#2ecc71",
        )

        # Add target line
        ax.axhline(y=90, color="red", linestyle="--", label="Target (90%)")

        ax.set_xlabel("Package")
        ax.set_ylabel("Coverage %")
        ax.set_title("Coverage by Package")
        ax.set_xticks(x)
        ax.set_xticklabels(package_names, rotation=45, ha="right")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 1,
                    f"{height:.0f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

    def _create_file_coverage_heatmap(self, files: List[Dict], output_path: Path):
        """Create heatmap of file coverage."""
        if not files:
            return

        # Group files by directory
        dir_coverage = {}
        for file in files:
            parts = file["path"].split("/")
            if len(parts) >= 2:
                dir_name = "/".join(parts[:-1])
                if dir_name not in dir_coverage:
                    dir_coverage[dir_name] = []
                dir_coverage[dir_name].append(file["line_coverage"])

        # Calculate average coverage per directory
        dir_avg = {k: sum(v) / len(v) for k, v in dir_coverage.items()}

        # Create matrix for heatmap
        sorted_dirs = sorted(dir_avg.items(), key=lambda x: x[1])[:20]  # Top 20

        fig, ax = plt.subplots(figsize=(10, 8))

        # Create heatmap data
        data = [[cov] for _, cov in sorted_dirs]

        im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=100)

        # Set labels
        ax.set_yticks(range(len(sorted_dirs)))
        ax.set_yticklabels([d[0].split("/")[-1] for d in sorted_dirs])
        ax.set_xticks([0])
        ax.set_xticklabels(["Coverage %"])

        # Add text annotations
        for i, (_, cov) in enumerate(sorted_dirs):
            ax.text(
                0,
                i,
                f"{cov:.0f}%",
                ha="center",
                va="center",
                color="white" if cov < 50 else "black",
            )

        ax.set_title("Directory Coverage Heatmap (Lowest 20)")

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Coverage %")

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

    def _create_coverage_distribution(self, files: List[Dict], output_path: Path):
        """Create histogram of coverage distribution."""
        if not files:
            return

        coverages = [f["line_coverage"] for f in files]

        fig, ax = plt.subplots(figsize=(10, 6))

        # Create histogram
        n, bins, patches = ax.hist(coverages, bins=20, edgecolor="black", alpha=0.7)

        # Color bars based on coverage level
        for i, patch in enumerate(patches):
            if bins[i] < 50:
                patch.set_facecolor("#e74c3c")
            elif bins[i] < 80:
                patch.set_facecolor("#f39c12")
            elif bins[i] < 90:
                patch.set_facecolor("#3498db")
            else:
                patch.set_facecolor("#27ae60")

        ax.axvline(x=90, color="red", linestyle="--", label="Target (90%)")
        ax.axvline(
            x=sum(coverages) / len(coverages),
            color="blue",
            linestyle="--",
            label="Average",
        )

        ax.set_xlabel("Coverage %")
        ax.set_ylabel("Number of Files")
        ax.set_title("Coverage Distribution Across Files")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add statistics
        stats_text = f"Files: {len(files)}\nAvg: {sum(coverages) /len(coverages):.1f}%\nMin: {min(coverages):.1f}%\nMax: {max(coverages):.1f}%"
        ax.text(
            0.02,
            0.98,
            stats_text,
            transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

    def _create_complexity_coverage_plot(self, files: List[Dict], output_path: Path):
        """Create scatter plot of complexity vs coverage."""
        if not files:
            return

        # Filter files with complexity > 0
        complex_files = [f for f in files if f["complexity"] > 0]

        if not complex_files:
            return

        complexities = [f["complexity"] for f in complex_files]
        coverages = [f["line_coverage"] for f in complex_files]

        fig, ax = plt.subplots(figsize=(10, 8))

        # Create scatter plot
        scatter = ax.scatter(complexities, coverages, alpha=0.6, s=50)

        # Add quadrant lines
        ax.axhline(
            y=90, color="red", linestyle="--", alpha=0.5, label="Target Coverage"
        )
        ax.axvline(
            x=10, color="orange", linestyle="--", alpha=0.5, label="High Complexity"
        )

        # Highlight problematic files (high complexity, low coverage)
        problem_files = [
            f for f in complex_files if f["complexity"] > 10 and f["line_coverage"] < 80
        ]
        if problem_files:
            problem_x = [f["complexity"] for f in problem_files]
            problem_y = [f["line_coverage"] for f in problem_files]
            ax.scatter(
                problem_x,
                problem_y,
                color="red",
                s=100,
                alpha=0.8,
                label="Problem Files",
            )

        ax.set_xlabel("Cyclomatic Complexity")
        ax.set_ylabel("Line Coverage %")
        ax.set_title("Code Complexity vs Coverage")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add annotations for outliers
        for f in complex_files:
            if f["complexity"] > 20 or f["line_coverage"] < 30:
                ax.annotate(
                    f["path"].split("/")[-1],
                    (f["complexity"], f["line_coverage"]),
                    fontsize=8,
                    alpha=0.7,
                )

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

    def _create_coverage_trends(self, output_path: Path):
        """Create coverage trend chart from historical data."""
        # Query historical coverage data
        query = f"""
        SELECT
            DATE(timestamp) as date,
            AVG(coverage_overall) as avg_coverage,
            AVG(coverage_branch) as avg_branch_coverage,
            MIN(coverage_overall) as min_coverage,
            MAX(coverage_overall) as max_coverage
        FROM `{self.project_id}.sentinelops_metrics.test_execution_metrics`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY date
        ORDER BY date
        """

        try:
            df = self.bigquery_client.query(query).to_dataframe()

            if df.empty:
                # Create placeholder chart
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(
                    0.5,
                    0.5,
                    "No historical data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                ax.set_title("Coverage Trends (Last 30 Days)")
                plt.savefig(output_path, dpi=150, bbox_inches="tight")
                plt.close()
                return

            fig, ax = plt.subplots(figsize=(12, 6))

            # Plot coverage trends
            ax.plot(
                df["date"], df["avg_coverage"], "b-", linewidth=2, label="Line Coverage"
            )
            ax.plot(
                df["date"],
                df["avg_branch_coverage"],
                "g-",
                linewidth=2,
                label="Branch Coverage",
            )

            # Add min/max range
            ax.fill_between(
                df["date"],
                df["min_coverage"],
                df["max_coverage"],
                alpha=0.2,
                color="blue",
                label="Min/Max Range",
            )

            # Add target line
            ax.axhline(y=90, color="red", linestyle="--", label="Target (90%)")

            ax.set_xlabel("Date")
            ax.set_ylabel("Coverage %")
            ax.set_title("Coverage Trends (Last 30 Days)")
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Rotate x-axis labels
            plt.xticks(rotation=45, ha="right")

            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()

        except Exception as e:
            print("Failed to create coverage trends: {e}")

    def publish_to_gcs(self, local_dir: str, bucket_name: str, prefix: str):
        """Publish coverage report to Google Cloud Storage.

        Args:
            local_dir: Local directory containing report files
            bucket_name: GCS bucket name
            prefix: Prefix for uploaded files
        """
        bucket = self.storage_client.bucket(bucket_name)

        for file_path in Path(local_dir).glob("*"):
            if file_path.is_file():
                blob_name = f"{prefix}/{file_path.name}"
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(str(file_path))

                # Make publicly readable
                blob.make_public()

                print("Uploaded {file_path.name} to gs://{bucket_name}/{blob_name}")

    def generate_markdown_summary(self, analysis: Dict) -> str:
        """Generate markdown summary for PR comments.

        Args:
            analysis: Coverage analysis data

        Returns:
            Markdown formatted summary
        """
        overall = analysis["overall"]
        line_coverage = overall["line_rate"] * 100
        branch_coverage = overall["branch_rate"] * 100

        # Determine status emoji
        if line_coverage >= 90:
            status = "✅"
        elif line_coverage >= 80:
            status = "⚠️"
        else:
            status = "❌"

        summary = f"""
## Coverage Report {status}

**Line Coverage:** {line_coverage:.1f}% ({overall['lines_covered']}/{overall['lines_total']} lines)
**Branch Coverage:** {branch_coverage:.1f}% ({overall['branches_covered']}/{overall['branches_total']} branches)

### Files with Lowest Coverage
| File | Coverage | Uncovered Lines |
|------|----------|-----------------|
"""

        # Add lowest coverage files
        for file in analysis["files"][:5]:
            summary += f"| {file['path'].split('/')[-1]} | {file['line_coverage']:.1f}% | {file['uncovered_lines']} |\n"

        # Add recommendations
        if analysis["recommendations"]:
            summary += "\n### Recommendations\n"
            for i, rec in enumerate(analysis["recommendations"][:3], 1):
                summary += f"{i}. {rec}\n"

        return summary

    def create_pr_comment(self, analysis: Dict, pr_number: int, repo: str):
        """Create PR comment with coverage summary.

        Args:
            analysis: Coverage analysis data
            pr_number: Pull request number
            repo: Repository name (owner/repo)
        """
        summary = self.generate_markdown_summary(analysis)

        # This would use GitHub API to post comment
        # For now, just save to file
        with open(f"pr-comment-{pr_number}.md", "w") as f:
            f.write(summary)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate coverage reports")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--coverage-xml", required=True, help="Path to coverage.xml")
    parser.add_argument(
        "--output-dir", default="coverage-report", help="Output directory"
    )
    parser.add_argument("--upload-gcs", help="Upload to GCS bucket")
    parser.add_argument("--pr-number", type=int, help="PR number for comment")
    parser.add_argument("--repo", help="Repository (owner/repo)")
    args = parser.parse_args()

    reporter = CoverageReporter(args.project_id)

    # Analyze coverage
    print("Analyzing coverage...")
    analysis = reporter.analyze_coverage_xml(args.coverage_xml)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save analysis JSON
    with open(output_dir / "coverage-analysis.json", "w") as f:
        json.dump(analysis, f, indent=2, default=str)

    # Generate visualizations
    print("Generating visualizations...")
    reporter.generate_coverage_visualizations(analysis, args.output_dir)

    # Generate HTML report
    print("Generating HTML report...")
    reporter.generate_html_report(analysis, output_dir / "index.html")

    # Upload to GCS if requested
    if args.upload_gcs:
        print("Uploading to GCS bucket {args.upload_gcs}...")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        reporter.publish_to_gcs(
            args.output_dir, args.upload_gcs, f"coverage-reports/{timestamp}"
        )

    # Create PR comment if requested
    if args.pr_number and args.repo:
        print("Creating PR comment for #{args.pr_number}...")
        reporter.create_pr_comment(analysis, args.pr_number, args.repo)

    # Print summary
    print("\nCoverage Summary:")
    print("Line Coverage: {analysis['overall']['line_rate'] * 100:.1f}%")
    print("Branch Coverage: {analysis['overall']['branch_rate'] * 100:.1f}%")
    print("Total Complexity: {analysis['overall']['complexity']}")


if __name__ == "__main__":
    main()

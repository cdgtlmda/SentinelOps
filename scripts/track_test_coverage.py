#!/usr/bin/env python3
"""
Automated test coverage tracking script.
Generates accurate metrics for test coverage progress.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

def find_source_files(src_dir: str = "src") -> List[Path]:
    """Find all Python source files excluding __init__.py."""
    source_files = []
    for root, dirs, files in os.walk(src_dir):
        if '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                source_files.append(Path(root) / file)
    return source_files

def find_test_files(test_dir: str = "tests") -> List[Path]:
    """Find all test files."""
    test_files = []
    for root, dirs, files in os.walk(test_dir):
        if '__pycache__' in root:
            continue
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(Path(root) / file)
    return test_files

def check_test_coverage(source_files: List[Path], test_files: List[str]) -> Dict:
    """Check which source files have corresponding tests."""
    test_names = [f.name for f in test_files]
    
    covered = []
    uncovered = []
    
    for src_file in source_files:
        expected_test_name = f"test_{src_file.name}"
        if expected_test_name in test_names:
            covered.append(src_file)
        else:
            uncovered.append(src_file)
    
    return {
        "covered": covered,
        "uncovered": uncovered,
        "coverage_ratio": len(covered) / len(source_files) if source_files else 0
    }

def get_file_metrics(file_path: Path) -> Dict:
    """Get metrics for a file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Count test functions
        test_count = sum(1 for line in lines if line.strip().startswith('def test_'))
        
        return {
            "lines": len(lines),
            "test_count": test_count,
            "size": file_path.stat().st_size
        }
    except Exception as e:
        return {"lines": 0, "test_count": 0, "size": 0, "error": str(e)}

def run_coverage_report() -> Dict:
    """Run pytest with coverage and parse results."""
    try:
        # Run pytest with coverage
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=term-missing", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse coverage from output
        lines = result.stdout.split('\n')
        for line in lines:
            if line.strip().startswith('TOTAL'):
                parts = line.split()
                if len(parts) >= 4:
                    return {
                        "statements": int(parts[1]),
                        "missed": int(parts[2]),
                        "coverage_percent": float(parts[3].rstrip('%'))
                    }
    except Exception as e:
        print(f"Error running coverage: {e}")
    
    return {"statements": 0, "missed": 0, "coverage_percent": 0}

def generate_report(output_file: str = None):
    """Generate comprehensive test coverage report."""
    print("SentinelOps Test Coverage Report")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Find files
    source_files = find_source_files()
    test_files = find_test_files()
    
    print(f"Total source files (excluding __init__.py): {len(source_files)}")
    print(f"Total test files: {len(test_files)}")
    
    # Check coverage
    coverage_info = check_test_coverage(source_files, test_files)
    
    print(f"Source files with tests: {len(coverage_info['covered'])}")
    print(f"Source files without tests: {len(coverage_info['uncovered'])}")
    print(f"File coverage ratio: {coverage_info['coverage_ratio']:.1%}")
    print()

    # Get sizes of uncovered files
    uncovered_with_size = []
    for src_file in coverage_info['uncovered']:
        metrics = get_file_metrics(src_file)
        uncovered_with_size.append((src_file, metrics['lines']))
    
    # Sort by size
    uncovered_with_size.sort(key=lambda x: x[1], reverse=True)
    
    # Show top priority files
    print("Top 10 Priority Files (Largest Without Tests):")
    print("-" * 80)
    for i, (file_path, lines) in enumerate(uncovered_with_size[:10], 1):
        print(f"{i:2d}. {str(file_path):<60} {lines:>5} lines")
    print()
    
    # Run actual coverage
    print("Running pytest coverage analysis...")
    coverage_results = run_coverage_report()
    print(f"Statement Coverage: {coverage_results['coverage_percent']}%")
    print(f"Total Statements: {coverage_results['statements']:,}")
    print(f"Missed Statements: {coverage_results['missed']:,}")
    print()
    
    # Summary
    print("Summary:")
    print("-" * 80)
    print(f"✓ Test files created: {len(test_files)}")
    print(f"✓ Source files with tests: {len(coverage_info['covered'])} / {len(source_files)}")
    print(f"✗ Source files needing tests: {len(coverage_info['uncovered'])}")
    print(f"✗ Gap to 1:1 ratio: {len(coverage_info['uncovered'])} files")
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            # Redirect stdout to file
            original_stdout = sys.stdout
            sys.stdout = f
            generate_report()  # Recursive call to write to file
            sys.stdout = original_stdout
        print(f"\nReport saved to: {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Track SentinelOps test coverage")
    parser.add_argument("-o", "--output", help="Save report to file")
    args = parser.parse_args()
    
    os.chdir(Path(__file__).parent.parent)  # Change to project root
    generate_report(args.output)

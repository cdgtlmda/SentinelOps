#!/bin/bash
# Run all code quality checks for SentinelOps

set -e

echo "Running code quality checks..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check formatting with Black
echo "Checking code formatting with Black..."
black --check src tests

# Check import sorting with isort
echo "Checking import sorting with isort..."
isort --check-only --profile black src tests

# Run Ruff linter
echo "Running Ruff linter..."
ruff check src tests

# Run type checking with mypy
echo "Running type checking with mypy..."
mypy src

# Run unit tests with pytest
echo "Running unit tests with pytest..."
pytest tests/unit -v

# Check for security issues with bandit
echo "Checking for security issues with bandit..."
bandit -r src

# Check dependencies for security vulnerabilities
echo "Checking dependencies for vulnerabilities..."
pip-audit

echo "All code quality checks passed!"
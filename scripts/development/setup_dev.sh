#!/bin/bash
# Setup development environment for SentinelOps

set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[dev]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pip install pre-commit
pre-commit install

# Set up Git hooks
echo "Setting up Git hooks..."
git config core.hooksPath .git/hooks

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/fixtures

echo "Development environment setup complete!"
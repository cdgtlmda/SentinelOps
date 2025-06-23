#!/bin/bash
# Script to activate SentinelOps virtual environment

VENV_PATH="/path/to/sentinelops/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

echo "✅ To activate the virtual environment, run:"
echo "source $VENV_PATH/bin/activate"
echo ""
echo "Or if you're using fish shell:"
echo "source $VENV_PATH/bin/activate.fish"
echo ""
echo "To deactivate, simply run: deactivate"

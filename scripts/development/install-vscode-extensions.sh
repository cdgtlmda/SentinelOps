#!/bin/bash
# Script to install required VS Code extensions for SentinelOps development

echo "Installing VS Code Extensions for SentinelOps..."
echo "=============================================="

# Check if 'code' command is available
if ! command -v code &> /dev/null; then
    echo "❌ 'code' command not found in PATH"
    echo "To install it:"
    echo "1. Open VS Code"
    echo "2. Press Cmd+Shift+P (macOS) or Ctrl+Shift+P (Windows/Linux)"
    echo "3. Type 'Shell Command: Install code command in PATH'"
    echo "4. Press Enter and restart your terminal"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Python extension
echo "Installing Python extension..."
code --install-extension ms-python.python

# Pylint extension (included with Python extension)
echo "Pylint is included with the Python extension"

# Black formatter extension
echo "Installing Black formatter extension..."
code --install-extension ms-python.black-formatter

# mypy extension for type checking
echo "Installing mypy extension..."
code --install-extension ms-python.mypy-type-checker

# Additional helpful extensions
echo "Installing additional helpful extensions..."
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.isort
code --install-extension donjayamanne.githistory
code --install-extension eamodio.gitlens

echo ""
echo "✅ VS Code extensions installation complete!"
echo "Please restart VS Code to ensure all extensions are loaded."

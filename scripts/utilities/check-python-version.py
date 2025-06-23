#!/usr/bin/env python3
"""Check Python version before installation."""
import sys

MIN_PYTHON = (3, 11)

if sys.version_info < MIN_PYTHON:
    print("Error: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or higher is required.")
    print("You are using Python {sys.version_info.major}.{sys.version_info.minor}.")
    sys.exit(1)
else:
    print("✓ Python {sys.version_info.major}.{sys.version_info.minor} - OK")

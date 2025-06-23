"""
Environment-specific logging configuration.
"""

import os
from pathlib import Path
from typing import Any

from .logging_config import setup_logging


def configure_logging_for_environment() -> dict[str, Any]:
    """Configure logging based on the current environment."""

    # Get environment from env variable
    env = os.getenv("APP_ENV", "development").lower()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Environment-specific settings
    env_configs = {
        "development": {
            "log_level": log_level or "DEBUG",
            "enable_file_logging": True,
            "enable_json_logging": False,  # Human-readable in dev
            "log_dir": Path("logs/dev"),
        },
        "test": {
            "log_level": "WARNING",
            "enable_file_logging": False,  # No file logging in tests
            "enable_json_logging": False,
            "log_dir": Path("logs/test"),
        },
        "production": {
            "log_level": log_level or "INFO",
            "enable_file_logging": True,
            "enable_json_logging": True,  # Structured logs for production
            "log_dir": Path("logs/prod"),
        },
    }

    # Get config for current environment
    config: dict[str, Any] = env_configs.get(env, env_configs["development"])

    # Apply logging setup
    setup_logging(
        log_level=config["log_level"],
        log_dir=config["log_dir"],
        enable_file_logging=config["enable_file_logging"],
        enable_json_logging=config["enable_json_logging"],
    )

    return config


# Initialize logging when module is imported
if __name__ != "__main__":
    configure_logging_for_environment()

"""Base module for SentinelOps."""

from typing import Dict, Any


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, name: str):
        """Initialize agent with name."""
        self.name = name

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data (to be implemented by subclasses)."""
        raise NotImplementedError

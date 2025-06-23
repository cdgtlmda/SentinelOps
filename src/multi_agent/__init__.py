"""
SentinelOps Multi-Agent System Module

This module provides the main multi-agent coordination using Google ADK.
"""

from .sentinelops_multi_agent import (
    SentinelOpsMultiAgent,
    create_sentinelops_multi_agent
)

__all__ = [
    "SentinelOpsMultiAgent",
    "create_sentinelops_multi_agent"
]

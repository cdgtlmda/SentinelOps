"""
Detection Agent module for SentinelOps.

This module contains the detection agent implementation that continuously
scans logs and security feeds for suspicious activity.
"""

from .adk_agent import DetectionAgent
from .rules_engine import DetectionRule, RulesEngine, RuleStatus
from .query_builder import QueryBuilder
from .event_correlator import EventCorrelator

__all__ = [
    "DetectionAgent",
    "DetectionRule",
    "RulesEngine",
    "RuleStatus",
    "QueryBuilder",
    "EventCorrelator",
]

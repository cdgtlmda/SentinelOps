"""
Database models for SentinelOps.
"""

from src.database.models.incidents import IncidentModel
from src.database.models.rules import RuleModel

__all__ = ["RuleModel", "IncidentModel"]

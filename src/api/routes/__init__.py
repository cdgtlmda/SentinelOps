"""
API routes for SentinelOps.
"""

from .incidents import router as incidents_router
from .rules import router as rules_router

__all__ = [
    "incidents_router",
    "rules_router",
]

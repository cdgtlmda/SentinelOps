"""
Query builder for detection rules.

This module provides utilities for building BigQuery queries for detection rules.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class QueryBuilder:
    """Builder for constructing detection queries."""

    @staticmethod
    def build_query(
        query_template: str,
        project_id: str,
        dataset_id: str,
        last_scan_time: datetime,
        current_time: datetime,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a query by substituting parameters."""
        params = {
            "project_id": project_id,
            "dataset_id": dataset_id,
            "last_scan_time": last_scan_time.isoformat(),
            "current_time": current_time.isoformat(),
        }

        if additional_params:
            params.update(additional_params)

        return query_template.format(**params)

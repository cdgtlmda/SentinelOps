"""
Query optimization module for the Detection Agent.

This module provides query optimization techniques to improve BigQuery performance.
"""

from typing import Any, Dict, List, Optional
import re
from datetime import datetime, timedelta


class QueryOptimizer:
    """Optimizes detection queries for better performance."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the query optimizer.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Optimization settings
        opt_config = config.get("agents", {}).get("detection", {}).get("query_optimization", {})

        # Time-based optimization
        self.enable_time_partitioning = opt_config.get("enable_time_partitioning", True)
        self.max_scan_days = opt_config.get("max_scan_days", 7)

        # Result limiting
        self.default_limit = opt_config.get("default_limit", 10000)
        self.enable_sampling = opt_config.get("enable_sampling", True)
        self.sample_percentage = opt_config.get("sample_percentage", 10)  # 10% sampling

        # Column optimization
        self.enable_column_pruning = opt_config.get("enable_column_pruning", True)
        self.required_columns = set(opt_config.get("required_columns", [
            "timestamp", "actor", "source_ip", "resource_name",
            "method_name", "status_code"
        ]))

    def optimize_query(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        rule_type: Optional[str] = None
    ) -> str:
        """
        Optimize a query for better performance.

        Args:
            query: Original SQL query
            start_time: Query start time
            end_time: Query end time
            rule_type: Type of detection rule

        Returns:
            Optimized query
        """
        optimized_query = query

        # Apply time range optimization
        if self.enable_time_partitioning:
            optimized_query = self._optimize_time_range(optimized_query, start_time, end_time)

        # Apply column pruning
        if self.enable_column_pruning:
            optimized_query = self._prune_unnecessary_columns(optimized_query)

        # Apply result limiting
        optimized_query = self._apply_result_limits(optimized_query)

        # Apply sampling for large time ranges
        if self.enable_sampling and self._should_sample(start_time, end_time):
            optimized_query = self._apply_sampling(optimized_query)

        # Optimize joins and filters
        optimized_query = self._optimize_joins_and_filters(optimized_query)

        # Apply clustering optimization
        optimized_query = self._apply_clustering_optimization(optimized_query)

        # Optimize specific rule types
        if rule_type:
            optimized_query = self._optimize_for_rule_type(optimized_query, rule_type)

        return optimized_query

    def _optimize_time_range(self, query: str, start_time: datetime, end_time: datetime) -> str:
        """
        Optimize query time range to limit data scanned.

        Args:
            query: SQL query
            start_time: Start time
            end_time: End time

        Returns:
            Query with optimized time range
        """
        # Limit scan to max_scan_days if range is too large
        max_range = timedelta(days=self.max_scan_days)
        if end_time - start_time > max_range:
            # Adjust start time to limit range
            new_start = end_time - max_range

            # Replace timestamp placeholders with new range
            query = query.replace(
                f"TIMESTAMP('{start_time.isoformat()}')",
                f"TIMESTAMP('{new_start.isoformat()}')"
            )
            query = query.replace(
                f"'{start_time.isoformat()}'",
                f"'{new_start.isoformat()}'"
            )

        # Add partition pruning hint if not present
        if "_PARTITIONTIME" not in query and "timestamp" in query.lower():
            # Add partition filter after WHERE clause
            where_match = re.search(r'WHERE\s+', query, re.IGNORECASE)
            if where_match:
                insert_pos = where_match.end()
                partition_filter = (
                    f"_PARTITIONTIME >= TIMESTAMP('{start_time.date().isoformat()}') "
                    f"AND _PARTITIONTIME <= TIMESTAMP('{end_time.date().isoformat()}') AND "
                )
                query = query[:insert_pos] + partition_filter + query[insert_pos:]

        return query

    def _prune_unnecessary_columns(self, query: str) -> str:
        """
        Remove unnecessary columns from SELECT to reduce data transfer.

        Args:
            query: SQL query

        Returns:
            Query with pruned columns
        """
        # Check if query uses SELECT *
        if re.search(r'SELECT\s+\*', query, re.IGNORECASE):
            # Replace with specific columns
            columns_str = ", ".join(sorted(self.required_columns))
            query = re.sub(
                r'SELECT\s+\*',
                f'SELECT {columns_str}',
                query,
                flags=re.IGNORECASE
            )

        return query

    def _apply_result_limits(self, query: str) -> str:
        """
        Apply result limits if not already present.

        Args:
            query: SQL query

        Returns:
            Query with result limits
        """
        # Check if query already has LIMIT
        if not re.search(r'LIMIT\s+\d+', query, re.IGNORECASE):
            # Add default limit
            query = query.rstrip().rstrip(';') + f' LIMIT {self.default_limit}'
        else:
            # Check if existing limit is too high
            limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
            if limit_match:
                current_limit = int(limit_match.group(1))
                if current_limit > self.default_limit:
                    query = re.sub(
                        r'LIMIT\s+\d+',
                        f'LIMIT {self.default_limit}',
                        query,
                        flags=re.IGNORECASE
                    )

        return query

    def _should_sample(self, start_time: datetime, end_time: datetime) -> bool:
        """
        Determine if sampling should be applied based on time range.

        Args:
            start_time: Query start time
            end_time: Query end time

        Returns:
            Whether to apply sampling
        """
        # Sample if range is more than 24 hours
        time_range = end_time - start_time
        return time_range > timedelta(hours=24)

    def _apply_sampling(self, query: str) -> str:
        """
        Apply sampling to reduce data scanned.

        Args:
            query: SQL query

        Returns:
            Query with sampling applied
        """
        # Check if query already has TABLESAMPLE
        if "TABLESAMPLE" in query.upper():
            return query

        # Find the FROM clause
        from_match = re.search(r'FROM\s+([^\s]+)', query, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1)
            # Add TABLESAMPLE after table name
            sampled_table = f"{table_name} TABLESAMPLE SYSTEM ({self.sample_percentage} PERCENT)"
            query = query.replace(table_name, sampled_table, 1)

        return query

    def _optimize_joins_and_filters(self, query: str) -> str:
        """
        Optimize JOIN operations and filter placement for better performance.

        Args:
            query: SQL query

        Returns:
            Query with optimized joins and filters
        """
        optimized_query = query

        # Move filters to earliest possible position (filter pushdown)
        optimized_query = self._apply_filter_pushdown(optimized_query)

        # Optimize JOIN order for smaller intermediate results
        optimized_query = self._optimize_join_order(optimized_query)

        # Add join hints for large tables
        optimized_query = self._add_join_hints(optimized_query)

        return optimized_query

    def _apply_filter_pushdown(self, query: str) -> str:
        """
        Push filters closer to data sources to reduce data scanned.

        Args:
            query: SQL query

        Returns:
            Query with pushed down filters
        """
        # For timestamp filters, ensure they're applied as early as possible
        if "JOIN" in query.upper() and "timestamp" in query.lower():
            # Find timestamp filters that can be pushed down
            timestamp_filters = re.findall(
                r'(timestamp\s*[><=]+\s*[^)]+)',
                query,
                re.IGNORECASE
            )

            # For each join, add timestamp filters to both sides if possible
            for filter_expr in timestamp_filters:
                # This is a simplified approach - in production you'd need
                # more sophisticated parsing
                if "main." not in filter_expr.lower() and "sub." not in filter_expr.lower():
                    # Add table aliases to timestamp filters
                    optimized_filter = filter_expr.replace("timestamp", "main.timestamp")
                    query = query.replace(filter_expr, optimized_filter)

        return query

    def _optimize_join_order(self, query: str) -> str:
        """
        Optimize JOIN order to minimize intermediate result sizes.

        Args:
            query: SQL query

        Returns:
            Query with optimized join order
        """
        # Look for patterns where we can suggest better join order
        # This is a simplified heuristic - in production you'd use query statistics

        # If joining audit logs with VPC logs, prefer filtering audit logs first
        if "audit_logs" in query.lower() and "vpc_flow_logs" in query.lower():
            # Ensure more selective filters are applied to larger tables first
            if "WHERE" in query.upper():
                # Add comment hint for query planner
                comment_hint = "/* Prefer audit_logs filtering first for better selectivity */"
                query = comment_hint + "\n" + query

        return query

    def _add_join_hints(self, query: str) -> str:
        """
        Add BigQuery-specific join hints for large tables.

        Args:
            query: SQL query

        Returns:
            Query with join hints
        """
        # Add hash join hints for large table joins
        if "JOIN" in query.upper():
            # Check for patterns indicating large table joins
            large_table_patterns = [
                "vpc_flow_logs", "audit_logs", "firewall_logs",
                "flow_logs", "activity_logs"
            ]

            for pattern in large_table_patterns:
                if pattern in query.lower():
                    # Add join method hint
                    join_hint = "/* Use HASH JOIN for large tables */"
                    if join_hint not in query:
                        query = join_hint + "\n" + query
                    break

        return query

    def _apply_clustering_optimization(self, query: str) -> str:
        """
        Apply clustering-aware optimizations to leverage BigQuery clustering.

        Args:
            query: SQL query

        Returns:
            Query optimized for clustering
        """
        # Ensure filters on clustered columns are applied effectively
        clustered_columns = ["timestamp", "actor", "resource_name", "source_ip"]

        for column in clustered_columns:
            if column in query.lower():
                # Add clustering hint comment
                clustering_hint = f"/* Filter on clustered column: {column} */"
                if clustering_hint not in query:
                    query = clustering_hint + "\n" + query

                # Ensure clustered column filters use efficient operators
                query = self._optimize_clustered_column_filters(query, column)

        return query

    def _optimize_clustered_column_filters(self, query: str, column: str) -> str:
        """
        Optimize filters on clustered columns for better performance.

        Args:
            query: SQL query
            column: Clustered column name

        Returns:
            Query with optimized clustered column filters
        """
        # For string columns, prefer prefix matching over LIKE with wildcards
        if column in ["actor", "resource_name"]:
            # Replace inefficient LIKE patterns
            like_pattern = rf"({column})\s+LIKE\s+'%([^%]+)%'"
            matches = re.finditer(like_pattern, query, re.IGNORECASE)

            for match in matches:
                col_name = match.group(1)
                search_term = match.group(2)

                # If the search term is at the beginning, use prefix matching
                if not search_term.startswith('%'):
                    # Replace with more efficient prefix filter
                    original = match.group(0)
                    optimized = f"{col_name} >= '{search_term}' AND {col_name} < '{search_term}~'"
                    query = query.replace(original, optimized)

        # For timestamp columns, ensure range filters are used
        elif column == "timestamp":
            # Ensure timestamp filters use range operators
            if f"{column} =" in query.lower():
                # Replace exact timestamp matches with small ranges
                exact_pattern = rf"({column})\s*=\s*'([^']+)'"
                matches = re.finditer(exact_pattern, query, re.IGNORECASE)

                for match in matches:
                    col_name = match.group(1)
                    timestamp_val = match.group(2)

                    # Replace with range for better clustering
                    original = match.group(0)
                    optimized = (f"{col_name} >= '{timestamp_val}' "
                                 f"AND {col_name} < TIMESTAMP_ADD(TIMESTAMP('{timestamp_val}'), "
                                 f"INTERVAL 1 SECOND)")
                    query = query.replace(original, optimized)

        return query

    def _optimize_for_rule_type(self, query: str, rule_type: str) -> str:
        """
        Apply rule-specific optimizations.

        Args:
            query: SQL query
            rule_type: Type of detection rule

        Returns:
            Optimized query for the specific rule type
        """
        # Optimize based on rule type
        if rule_type == "suspicious_login":
            # For login rules, prioritize recent events and specific methods
            query = self._add_method_filter(query, ["LoginAttempt", "LoginSuccess", "LoginFailure"])

        elif rule_type == "privilege_escalation":
            # For privilege escalation, focus on IAM operations
            query = self._add_method_filter(query, [
                "SetIamPolicy", "UpdateRole", "CreateRole",
                "CreateServiceAccountKey", "GrantRole"
            ])

        elif rule_type == "data_exfiltration":
            # For data exfiltration, focus on data access operations
            query = self._add_method_filter(query, [
                "GetObject", "ListObjects", "ExportTable",
                "DownloadObject", "ReadData"
            ])

        elif rule_type == "resource_modification":
            # For resource changes, focus on write operations
            query = self._add_method_filter(query, [
                "Update", "Delete", "Create", "Modify", "Patch"
            ])

        elif rule_type == "firewall_change":
            # For firewall changes, focus on specific resources
            query = self._add_resource_filter(query, ["firewall", "security", "network"])

        return query

    def _add_method_filter(self, query: str, methods: List[str]) -> str:
        """
        Add method name filtering to reduce data scanned.

        Args:
            query: SQL query
            methods: List of method names to filter

        Returns:
            Query with method filter
        """
        # Build method filter condition
        method_conditions = " OR ".join([f"method_name LIKE '%{method}%'" for method in methods])
        method_filter = f"({method_conditions})"

        # Add filter to WHERE clause
        where_match = re.search(r'WHERE\s+', query, re.IGNORECASE)
        if where_match:
            # Find the end of WHERE clause conditions
            insert_pos = where_match.end()
            query = query[:insert_pos] + f"{method_filter} AND " + query[insert_pos:]
        else:
            # Add WHERE clause if not present
            from_match = re.search(r'FROM\s+[^\s]+', query, re.IGNORECASE)
            if from_match:
                insert_pos = from_match.end()
                query = query[:insert_pos] + f" WHERE {method_filter}" + query[insert_pos:]

        return query

    def _add_resource_filter(self, query: str, resource_keywords: List[str]) -> str:
        """
        Add resource name filtering.

        Args:
            query: SQL query
            resource_keywords: Keywords to filter resources

        Returns:
            Query with resource filter
        """
        # Build resource filter condition
        resource_conditions = " OR ".join([
            f"LOWER(resource_name) LIKE '%{keyword}%'"
            for keyword in resource_keywords
        ])
        resource_filter = f"({resource_conditions})"

        # Add filter similar to method filter
        where_match = re.search(r'WHERE\s+', query, re.IGNORECASE)
        if where_match:
            insert_pos = where_match.end()
            query = query[:insert_pos] + f"{resource_filter} AND " + query[insert_pos:]
        else:
            from_match = re.search(r'FROM\s+[^\s]+', query, re.IGNORECASE)
            if from_match:
                insert_pos = from_match.end()
                query = query[:insert_pos] + f" WHERE {resource_filter}" + query[insert_pos:]

        return query

    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get statistics about query optimizations.

        Returns:
            Dictionary of optimization statistics
        """
        return {
            "time_partitioning_enabled": self.enable_time_partitioning,
            "max_scan_days": self.max_scan_days,
            "column_pruning_enabled": self.enable_column_pruning,
            "sampling_enabled": self.enable_sampling,
            "sample_percentage": self.sample_percentage,
            "default_limit": self.default_limit,
            "join_optimization_enabled": True,
            "clustering_optimization_enabled": True,
            "filter_pushdown_enabled": True
        }

    def estimate_bytes_processed(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[int]:
        """
        Estimate bytes that will be processed by query.

        Args:
            query: SQL query
            start_time: Query start time
            end_time: Query end time

        Returns:
            Estimated bytes to be processed (None if unable to estimate)
        """
        # Simple estimation based on time range and sampling
        time_range_days = (end_time - start_time).days

        # Base estimate: 1GB per day of logs
        base_bytes = time_range_days * 1_000_000_000

        # Apply sampling reduction
        if self.enable_sampling and self._should_sample(start_time, end_time):
            base_bytes = int(base_bytes * (self.sample_percentage / 100))

        # Apply column pruning reduction (estimate 30% reduction)
        if self.enable_column_pruning and "SELECT *" not in query.upper():
            base_bytes = int(base_bytes * 0.7)

        return base_bytes

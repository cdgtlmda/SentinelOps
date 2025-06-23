"""
BigQuery pagination support for the Detection Agent.

This module provides utilities for handling paginated query results from BigQuery.
"""

from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, cast

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

if TYPE_CHECKING:
    GoogleCloudErrorType = GoogleCloudError
else:
    GoogleCloudErrorType = GoogleCloudError


class PaginatedQueryExecutor:
    """Handles paginated execution of BigQuery queries."""

    def __init__(
        self,
        client: bigquery.Client,
        page_size: int = 1000,
        max_results: Optional[int] = None,
        timeout_ms: int = 30000,
    ):
        """
        Initialize the paginated query executor.

        Args:
            client: BigQuery client instance
            page_size: Number of results per page
            max_results: Maximum total results to return (None for no limit)
            timeout_ms: Query timeout in milliseconds
        """
        self.client = client
        self.page_size = page_size
        self.max_results = max_results
        self.timeout_ms = timeout_ms

    async def execute_query(
        self, query: str, job_config: Optional[bigquery.QueryJobConfig] = None
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Execute a query and yield results page by page.

        Args:
            query: SQL query to execute
            job_config: Optional query job configuration

        Yields:
            Pages of query results as lists of dictionaries
        """
        if job_config is None:
            job_config = bigquery.QueryJobConfig()

        # Set query configuration
        job_config.use_query_cache = False
        job_config.timeout_ms = self.timeout_ms

        try:
            # Execute the query
            query_job = self.client.query(query, job_config=job_config)

            # Get paginated results
            results_processed = 0

            while True:
                # Get a page of results
                rows = list(
                    query_job.result(
                        page_size=self.page_size, start_index=results_processed
                    )
                )

                if not rows:
                    break

                # Convert rows to dictionaries
                page_results = []
                for row in rows:
                    page_results.append(dict(row.items()))
                    results_processed += 1

                    # Check if we've reached max results
                    if self.max_results and results_processed >= self.max_results:
                        yield page_results
                        return

                yield page_results

                # Check if there are more pages
                if len(rows) < self.page_size:
                    break

        except (ValueError, RuntimeError, AttributeError) as e:
            raise RuntimeError(f"Unexpected error during query pagination: {e}") from e

    def execute_query_sync(
        self, query: str, job_config: Optional[bigquery.QueryJobConfig] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query synchronously and return all results.

        Args:
            query: SQL query to execute
            job_config: Optional query job configuration

        Returns:
            All query results as a list of dictionaries
        """
        if job_config is None:
            job_config = bigquery.QueryJobConfig()

        job_config.use_query_cache = False
        job_config.timeout_ms = self.timeout_ms

        try:
            # Execute the query
            query_job = self.client.query(query, job_config=job_config)

            # Collect all results with pagination
            all_results = []
            results_processed = 0

            # Use the BigQuery result iterator with page size
            result_iterator = query_job.result(page_size=self.page_size)

            for row in result_iterator:
                all_results.append(dict(row.items()))
                results_processed += 1

                # Check if we've reached max results
                if self.max_results and results_processed >= self.max_results:
                    break

            return all_results

        except (ValueError, RuntimeError, AttributeError) as e:
            raise RuntimeError(f"Unexpected error during query execution: {e}") from e

    @staticmethod
    def add_pagination_to_query(
        query: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> str:
        """
        Add LIMIT and OFFSET clauses to a query if not already present.

        Args:
            query: SQL query
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Modified query with pagination clauses
        """
        query = query.strip().rstrip(";")

        # Check if query already has LIMIT
        if "LIMIT" not in query.upper():
            if limit:
                query += f" LIMIT {limit}"

        # Add OFFSET if specified
        if offset and "OFFSET" not in query.upper():
            query += f" OFFSET {offset}"

        return query

    def estimate_query_size(self, query: str) -> Optional[int]:
        """
        Estimate the number of rows a query will return.

        Args:
            query: SQL query to estimate

        Returns:
            Estimated row count or None if unable to estimate
        """
        try:
            # Validate query to prevent SQL injection
            if not query or not isinstance(query, str):
                return None

            # Basic validation - ensure query doesn't contain dangerous patterns
            dangerous_patterns = [
                "--",
                "/*",
                "*/",
                ";",
                "DROP",
                "DELETE",
                "INSERT",
                "UPDATE",
                "CREATE",
                "ALTER",
            ]
            query_upper = query.upper()
            if any(pattern in query_upper for pattern in dangerous_patterns):
                return None

            # Create a count query - wrapping the validated query
            # Query is validated above for dangerous patterns
            count_query = (
                f"SELECT COUNT(*) as row_count FROM ({query}) as subquery"  # nosec B608
            )

            job_config = bigquery.QueryJobConfig(
                use_query_cache=True, timeout_ms=10000  # 10 second timeout for count
            )

            query_job = self.client.query(count_query, job_config=job_config)
            results = list(query_job.result())

            if results:
                return cast(int, results[0].row_count)

            return None

        except (ValueError, AttributeError):
            # If count query fails, return None
            return None

    async def cleanup(self) -> None:
        """Clean up resources used by the paginated query executor."""
        # Cancel any running jobs if we had references to them
        if hasattr(self, "_active_jobs"):
            for job in self._active_jobs:
                try:
                    job.cancel()
                except (ValueError, AttributeError):
                    pass  # Ignore cancellation errors
            self._active_jobs.clear()

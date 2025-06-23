"""Integration tests for BigQuery connectivity."""

import os
import time
from datetime import datetime

import pytest
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


class TestBigQueryConnectivity:
    """Test BigQuery connectivity and operations."""

    @pytest.fixture(scope="class")
    def bigquery_client(self) -> bigquery.Client:
        """Create BigQuery client."""
        return bigquery.Client()

    @pytest.fixture(scope="class")
    def project_id(self) -> str:
        """Get project ID from environment or default."""
        return os.environ.get("GCP_PROJECT_ID", "sentinelops-testing")

    @pytest.fixture(scope="class")
    def dataset_id(self) -> str:
        """Get dataset ID."""
        return "security_logs"

    def test_bigquery_client_creation(self, bigquery_client: bigquery.Client) -> None:
        """Test that BigQuery client can be created successfully."""
        assert bigquery_client is not None
        assert isinstance(bigquery_client, bigquery.Client)

    def test_dataset_exists(
        self, bigquery_client: bigquery.Client, project_id: str, dataset_id: str
    ) -> None:
        """Test that the security_logs dataset exists."""
        dataset_ref = f"{project_id}.{dataset_id}"

        try:
            dataset = bigquery_client.get_dataset(dataset_ref)
            assert dataset is not None
            assert dataset.dataset_id == dataset_id
        except NotFound:
            pytest.skip(f"Dataset {dataset_ref} not found - requires infrastructure setup")

    def test_required_tables_exist(
        self, bigquery_client: bigquery.Client, project_id: str, dataset_id: str
    ) -> None:
        """Test that all required tables exist in the dataset."""
        required_tables = ["vpc_flow_logs", "audit_logs", "firewall_logs", "iam_logs"]

        dataset_ref = f"{project_id}.{dataset_id}"

        for table_name in required_tables:
            table_ref = f"{dataset_ref}.{table_name}"
            try:
                table = bigquery_client.get_table(table_ref)
                assert table is not None
                assert table.table_id == table_name
            except NotFound:
                pytest.skip(f"Required table {table_ref} not found - requires infrastructure setup")

    def test_query_execution(
        self, bigquery_client: bigquery.Client, project_id: str, dataset_id: str
    ) -> None:
        """Test that we can execute queries against BigQuery."""
        # Simple query to test connectivity
        query = f"""
        SELECT
            COUNT(*) as record_count,
            MIN(_PARTITIONTIME) as earliest_record,
            MAX(_PARTITIONTIME) as latest_record
        FROM `{project_id}.{dataset_id}.vpc_flow_logs`
        WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        """  # noqa: E501

        try:
            query_job = bigquery_client.query(query)
            results = list(query_job.result())
            assert len(results) == 1
            row = results[0]
            assert row.record_count >= 0
        except NotFound as e:
            pytest.skip(f"Required BigQuery infrastructure not found: {str(e)}")
        except (ValueError, RuntimeError, TypeError) as e:
            pytest.fail(f"Failed to execute query: {str(e)}")

    def test_write_permissions(
        self, bigquery_client: bigquery.Client, project_id: str, dataset_id: str
    ) -> None:
        """Test that we can write to BigQuery (using a temp table)."""
        temp_table_id = f"test_write_{int(time.time())}"
        table_ref = f"{project_id}.{dataset_id}.{temp_table_id}"

        # Create a simple schema
        schema = [
            bigquery.SchemaField("test_id", "STRING"),
            bigquery.SchemaField("test_value", "INTEGER"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
        ]
        table = bigquery.Table(table_ref, schema=schema)

        try:
            # Create the table
            table = bigquery_client.create_table(table)
            assert table.table_id == temp_table_id

            # Insert some test data
            rows_to_insert = [
                {"test_id": "1", "test_value": 100, "created_at": datetime.utcnow()},
                {"test_id": "2", "test_value": 200, "created_at": datetime.utcnow()},
            ]
            errors = bigquery_client.insert_rows_json(table, rows_to_insert)
            assert errors == []

            # Clean up - delete the test table
            bigquery_client.delete_table(table_ref)
        except NotFound as e:
            pytest.skip(f"Required BigQuery infrastructure not found: {str(e)}")
        except (ValueError, RuntimeError, TypeError) as e:
            # Try to clean up if test fails
            try:
                bigquery_client.delete_table(table_ref)
            except (NotFound, ValueError, RuntimeError):
                pass
            pytest.fail(f"Failed to test write permissions: {str(e)}")

    def test_log_sink_permissions(
        self, bigquery_client: bigquery.Client, project_id: str, dataset_id: str
    ) -> None:
        """Test that log sinks have proper permissions to write."""
        # Query the dataset metadata to check permissions
        dataset_ref = f"{project_id}.{dataset_id}"

        try:
            dataset = bigquery_client.get_dataset(dataset_ref)
            access_entries = dataset.access_entries

            # Check for log sink service account permissions
            log_sink_found = False
            for entry in access_entries:
                if hasattr(entry, "entity_id") and "gserviceaccount.com" in str(
                    entry.entity_id
                ):
                    if "logging" in str(entry.entity_id) or "logs" in str(
                        entry.entity_id
                    ):
                        log_sink_found = True
                        break
            assert (
                log_sink_found
            ), "No log sink service account found in dataset permissions"
        except NotFound as e:
            pytest.skip(f"Required BigQuery infrastructure not found: {str(e)}")
        except (ValueError, RuntimeError, TypeError) as e:
            pytest.fail(f"Failed to check log sink permissions: {str(e)}")

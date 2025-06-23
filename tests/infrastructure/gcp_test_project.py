"""
Real GCP Test Project Infrastructure for SentinelOps.

This module provides infrastructure for testing with REAL Google Cloud Platform services.
NO MOCKING - All functionality uses actual GCP APIs with the your-gcp-project-id project.
"""

import logging
import os
from typing import Dict, Any, Optional, List

from google.cloud import bigquery, secretmanager, logging as cloud_logging
from google.cloud import firestore
from google.cloud.exceptions import NotFound

logger = logging.getLogger(__name__)

# Real GCP Project Configuration
REAL_GCP_PROJECT_ID = "your-gcp-project-id"
TEST_DATASET_ID = "test_sentinelops_dataset"


class GCPTestProject:
    """
    Real GCP test project for comprehensive testing.

    This class provides access to real GCP services for testing SentinelOps components.
    All operations use actual Google Cloud Platform APIs.
    """

    def __init__(self, project_id: str = REAL_GCP_PROJECT_ID):
        """Initialize with real GCP project."""
        self.project_id = project_id
        self._bigquery_client: Optional[bigquery.Client] = None
        self._firestore_client: Optional[firestore.Client] = None
        self._secret_manager_client: Optional[
            secretmanager.SecretManagerServiceClient
        ] = None
        self._logging_client: Optional[cloud_logging.Client] = None

        # Set environment variables for real GCP access
        os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id
        os.environ["GCP_PROJECT_ID"] = self.project_id
        os.environ["SENTINELOPS_PROJECT_ID"] = self.project_id

    @property
    def bigquery_client(self) -> bigquery.Client:
        """Get real BigQuery client."""
        if self._bigquery_client is None:
            self._bigquery_client = bigquery.Client(project=self.project_id)
        return self._bigquery_client

    @property
    def firestore_client(self) -> firestore.Client:
        """Get real Firestore client."""
        if self._firestore_client is None:
            self._firestore_client = firestore.Client(project=self.project_id)
        return self._firestore_client

    @property
    def secret_manager_client(self) -> secretmanager.SecretManagerServiceClient:
        """Get real Secret Manager client."""
        if self._secret_manager_client is None:
            self._secret_manager_client = secretmanager.SecretManagerServiceClient()
        return self._secret_manager_client

    @property
    def logging_client(self) -> cloud_logging.Client:
        """Get real Cloud Logging client."""
        if self._logging_client is None:
            self._logging_client = cloud_logging.Client(
                project=self.project_id
            )  # type: ignore[no-untyped-call]
        return self._logging_client

    def get_service_clients(self) -> Dict[str, Any]:
        """Get all real GCP service clients as a dictionary."""
        return {
            "bigquery": self.bigquery_client,
            "firestore": self.firestore_client,
            "secret_manager": self.secret_manager_client,
            "logging": self.logging_client,
        }

    def ensure_test_dataset(
        self, dataset_id: str = TEST_DATASET_ID
    ) -> bigquery.Dataset:
        """Ensure test dataset exists in real BigQuery."""
        full_dataset_id = f"{self.project_id}.{dataset_id}"
        try:
            dataset = self.bigquery_client.get_dataset(full_dataset_id)
            logger.info("Test dataset %s already exists", full_dataset_id)
            return dataset
        except NotFound:
            logger.info("Creating test dataset %s", full_dataset_id)
            dataset = bigquery.Dataset(full_dataset_id)
            dataset.location = "US"
            dataset.description = "Test dataset for SentinelOps automated testing"
            return self.bigquery_client.create_dataset(dataset, exists_ok=True)

    def ensure_test_table(
        self, table_id: str, schema: list[Any], dataset_id: str = TEST_DATASET_ID
    ) -> bigquery.Table:
        """Ensure test table exists in real BigQuery with specified schema."""
        dataset = self.ensure_test_dataset(dataset_id)
        table_ref = dataset.table(table_id)

        try:
            table = self.bigquery_client.get_table(table_ref)
            logger.info("Test table %s already exists", table_id)
            return table
        except NotFound:
            logger.info("Creating test table %s", table_id)
            table = bigquery.Table(table_ref, schema=schema)
            return self.bigquery_client.create_table(table)

    def cleanup_test_data(
        self,
        collection_names: Optional[List[str]] = None,
        table_names: Optional[List[str]] = None,
    ) -> None:
        """
        Clean up test data from real GCP services.

        Args:
            collection_names: Firestore collections to clean
            table_names: BigQuery tables to clean
        """
        # Clean Firestore collections
        if collection_names:
            for collection_name in collection_names:
                try:
                    collection_ref = self.firestore_client.collection(collection_name)
                    docs = collection_ref.where("test_data", "==", True).stream()
                    for doc in docs:
                        doc.reference.delete()
                    logger.info(
                        "Cleaned test data from Firestore collection %s",
                        collection_name,
                    )
                except (ValueError, RuntimeError, TypeError) as e:
                    logger.warning(
                        "Failed to clean collection %s: %s", collection_name, e
                    )

        # Clean BigQuery tables
        if table_names:
            for table_name in table_names:
                try:
                    # table_ref would be used if we delete via API instead of SQL
                    # table_ref = self.bigquery_client.dataset(TEST_DATASET_ID).table(table_name)
                    query = (
                        f"DELETE FROM `{self.project_id}.{TEST_DATASET_ID}.{table_name}` "
                        "WHERE test_data = true"
                    )
                    job = self.bigquery_client.query(query)
                    job.result()  # Wait for completion
                    logger.info("Cleaned test data from BigQuery table %s", table_name)
                except (ValueError, RuntimeError, TypeError) as e:
                    logger.warning("Failed to clean table %s: %s", table_name, e)

    def reset(self) -> None:
        """Reset test project to clean state (minimal cleanup for real services)."""
        logger.info("Resetting real GCP test project state")
        # For real services, we only clean test data, not entire resources
        self.cleanup_test_data(
            collection_names=["test_incidents", "test_analysis", "test_remediation"],
            table_names=["test_logs", "test_events", "test_metrics"],
        )


def setup_gcp_test_project(project_id: str = REAL_GCP_PROJECT_ID) -> GCPTestProject:
    """
    Set up a real GCP test project for testing.

    Args:
        project_id: Real GCP project ID to use for testing

    Returns:
        GCPTestProject instance configured for real testing
    """
    logger.info("Setting up real GCP test project: %s", project_id)

    project = GCPTestProject(project_id)

    # Ensure basic test infrastructure exists
    try:
        project.ensure_test_dataset()
        logger.info("Real GCP test project setup complete")
    except Exception as e:
        logger.error("Failed to set up GCP test project: %s", e)
        raise

    return project

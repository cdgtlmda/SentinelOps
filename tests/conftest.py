"""
Test configuration for SentinelOps - Real GCP Service Testing.

This conftest.py provides fixtures for testing with REAL GCP services.
NO MOCKING - All tests use actual Google Cloud Platform APIs.
"""

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import (
    Generator,
    Dict,
    Any,
    Optional,
    Callable,
    Union,
    Awaitable,
    AsyncGenerator,
)
from datetime import datetime

import pytest
import pytest_asyncio
from google.cloud import bigquery, secretmanager, logging as cloud_logging

try:
    from google.cloud import firestore_v1 as firestore

    FIRESTORE_AVAILABLE = True
except ImportError:
    # If firestore is not available, skip firestore tests
    firestore = None  # type: ignore[assignment]
    FIRESTORE_AVAILABLE = False
from google.cloud.exceptions import NotFound

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Configure pytest plugins
pytest_plugins = [
    "pytest_asyncio",
]

# Real GCP Project Configuration
REAL_GCP_PROJECT_ID = "your-gcp-project-id"
TEST_DATASET_ID = "test_sentinelops_dataset"
TEST_COLLECTION_PREFIX = "test_"

# Configure environment for real GCP services
os.environ["GOOGLE_CLOUD_PROJECT"] = REAL_GCP_PROJECT_ID
os.environ["GCP_PROJECT_ID"] = REAL_GCP_PROJECT_ID
os.environ["SENTINELOPS_PROJECT_ID"] = REAL_GCP_PROJECT_ID


@pytest.fixture(autouse=True)
def configure_test_logging() -> Generator[None, None, None]:
    """Configure logging for test runs."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )

    # Reduce noise from GCP libraries
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("grpc").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    yield


@pytest.fixture(scope="session")
def gcp_project_id() -> str:
    """Provide the real GCP project ID for testing."""
    return REAL_GCP_PROJECT_ID


@pytest.fixture(scope="session")
def real_bigquery_client(
    gcp_project_id: str,
) -> Generator[bigquery.Client, None, None]:
    """Provide a real BigQuery client for testing."""
    client = bigquery.Client(project=gcp_project_id)

    # Ensure test dataset exists
    dataset_id = f"{gcp_project_id}.{TEST_DATASET_ID}"
    try:
        client.get_dataset(dataset_id)
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset, exists_ok=True)

    yield client


@pytest.fixture(scope="session")
def real_firestore_client(
    project_id: str = REAL_GCP_PROJECT_ID,
) -> Generator[Any, None, None]:
    """Provide a real Firestore client for testing."""
    if not FIRESTORE_AVAILABLE or firestore is None:
        pytest.skip("Firestore not available")
    client = firestore.Client(project=project_id)
    yield client


@pytest.fixture(scope="session")
def real_secret_manager_client() -> (
    Generator[secretmanager.SecretManagerServiceClient, None, None]
):
    """Provide a real Secret Manager client for testing."""
    client = secretmanager.SecretManagerServiceClient()
    yield client


@pytest.fixture(scope="session")
def real_logging_client(
    project_id: str = REAL_GCP_PROJECT_ID,
) -> Generator[cloud_logging.Client, None, None]:
    """Provide a real Cloud Logging client for testing."""
    client = cloud_logging.Client(project=project_id)  # type: ignore[no-untyped-call]
    yield client


@pytest.fixture
def cleanup_firestore_test_data(
    firestore_client: Any,
) -> Generator[Callable[[str, str], None], None, None]:
    """Clean up test data from Firestore after tests."""
    created_docs = []

    def track_document(collection_name: str, doc_id: str) -> None:
        """Track a document for cleanup."""
        created_docs.append((collection_name, doc_id))

    yield track_document

    # Cleanup after test
    for collection_name, doc_id in created_docs:
        try:
            doc_ref = firestore_client.collection(collection_name).document(doc_id)
            doc_ref.delete()
        except (AttributeError, ValueError, RuntimeError):
            pass  # Best effort cleanup


@pytest.fixture
def cleanup_bigquery_test_data(
    bigquery_client: bigquery.Client,
) -> Generator[Callable[[str, str], None], None, None]:
    """Clean up test data from BigQuery after tests."""
    created_tables = []

    def track_table(dataset_id: str, table_id: str) -> None:
        """Track a table for cleanup."""
        created_tables.append((dataset_id, table_id))

    yield track_table

    # Cleanup after test
    for dataset_id, table_id in created_tables:
        try:
            table_ref = bigquery_client.dataset(dataset_id).table(table_id)
            bigquery_client.delete_table(table_ref, not_found_ok=True)
        except (AttributeError, ValueError, RuntimeError):
            pass  # Best effort cleanup


class RealGCPTestProject:
    """Real GCP test project fixture for comprehensive testing."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._bigquery_client: Optional[bigquery.Client] = None
        self._firestore_client: Optional[Any] = None
        self._secret_manager_client: Optional[
            secretmanager.SecretManagerServiceClient
        ] = None
        self._logging_client: Optional[cloud_logging.Client] = None

    @property
    def bigquery_client(self) -> bigquery.Client:
        """Get BigQuery client."""
        if self._bigquery_client is None:
            self._bigquery_client = bigquery.Client(project=self.project_id)
        return self._bigquery_client

    @property
    def firestore_client(self) -> Any:
        """Get Firestore client."""
        if self._firestore_client is None:
            self._firestore_client = firestore.Client(project=self.project_id)
        return self._firestore_client

    @property
    def secret_manager_client(self) -> secretmanager.SecretManagerServiceClient:
        """Get Secret Manager client."""
        if self._secret_manager_client is None:
            self._secret_manager_client = secretmanager.SecretManagerServiceClient()
        return self._secret_manager_client

    @property
    def logging_client(self) -> cloud_logging.Client:
        """Get Cloud Logging client."""
        if self._logging_client is None:
            self._logging_client = cloud_logging.Client(
                project=self.project_id
            )  # type: ignore[no-untyped-call]
        return self._logging_client

    def get_service_clients(self) -> Dict[str, Any]:
        """Get all service clients as a dictionary."""
        return {
            "bigquery": self.bigquery_client,
            "firestore": self.firestore_client,
            "secret_manager": self.secret_manager_client,
            "logging": self.logging_client,
        }

    def ensure_test_dataset(
        self, dataset_id: str = TEST_DATASET_ID
    ) -> bigquery.Dataset:
        """Ensure test dataset exists in BigQuery."""
        full_dataset_id = f"{self.project_id}.{dataset_id}"
        try:
            return self.bigquery_client.get_dataset(full_dataset_id)
        except NotFound:
            dataset = bigquery.Dataset(full_dataset_id)
            dataset.location = "US"
            return self.bigquery_client.create_dataset(dataset, exists_ok=True)


@pytest.fixture(scope="session")
def real_gcp_test_project(
    project_id: str = REAL_GCP_PROJECT_ID,
) -> Generator[RealGCPTestProject, None, None]:
    """Provide a complete real GCP test project."""
    project = RealGCPTestProject(project_id)

    # Ensure test infrastructure exists
    project.ensure_test_dataset()

    yield project


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_temp_dir() -> AsyncGenerator[Path, None]:
    """Async version of temp_dir fixture."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestUtils:
    """Common test utilities for real GCP testing."""

    @staticmethod
    def create_test_id(prefix: str = "test") -> str:
        """Create a unique test ID."""
        import uuid

        return f"{prefix}_{str(uuid.uuid4()).replace('-', '_')[:8]}"

    @staticmethod
    async def wait_for_condition(
        condition_func: Callable[[], Union[bool, Awaitable[bool]]],
        timeout: float = 30.0,
        interval: float = 1.0,
    ) -> bool:
        """Wait for a condition to become true (longer timeout for real GCP)."""
        import time

        start = time.time()
        while time.time() - start < timeout:
            if (
                await condition_func()
                if asyncio.iscoroutinefunction(condition_func)
                else condition_func()
            ):
                return True
            await asyncio.sleep(interval)
        return False

    @staticmethod
    def assert_datetime_close(
        dt1: Optional[datetime], dt2: Optional[datetime], max_diff_seconds: int = 60
    ) -> None:
        """Assert two datetimes are close (longer tolerance for real services)."""
        if dt1 is None or dt2 is None:
            assert dt1 == dt2
            return
        # datetime already imported at module level

        if isinstance(dt1, datetime) and isinstance(dt2, datetime):
            diff = abs((dt1 - dt2).total_seconds())
            assert (
                diff <= max_diff_seconds
            ), f"Datetime difference {diff}s exceeds max {max_diff_seconds}s"


@pytest.fixture
def test_utils() -> TestUtils:
    """Provide test utilities to tests."""
    return TestUtils()


# Markers for test organization
def pytest_configure(config: Any) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line(
        "markers", "integration: Integration tests with real GCP services"
    )
    config.addinivalue_line("markers", "e2e: End-to-end tests with full GCP stack")
    config.addinivalue_line("markers", "slow: Slow tests (>30s)")
    config.addinivalue_line("markers", "smoke: Smoke tests for quick validation")
    config.addinivalue_line("markers", "security: Security tests")

    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "real_gcp: Tests that require real GCP services")

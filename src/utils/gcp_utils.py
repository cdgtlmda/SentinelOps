"""
Google Cloud Platform utility functions.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import google.api_core.exceptions
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)

# Initialize availability flags
COMPUTE_AVAILABLE = False
STORAGE_AVAILABLE = False

if TYPE_CHECKING:
    from google.cloud import compute_v1, storage
else:
    # Import with fallback handling
    try:
        from google.cloud import compute_v1, storage

        COMPUTE_AVAILABLE = True
        STORAGE_AVAILABLE = True
    except ImportError:
        # Graceful degradation if packages not available
        compute_v1 = None  # type: ignore
        storage = None  # type: ignore
        COMPUTE_AVAILABLE = False
        STORAGE_AVAILABLE = False


async def check_gcp_connectivity() -> bool:
    """
    Check if we can connect to Google Cloud services.

    Returns:
        True if connected, False otherwise
    """
    try:
        # Try to get default credentials
        credentials, project = default()  # type: ignore[no-untyped-call]

        if not project:
            project = os.getenv("GOOGLE_CLOUD_PROJECT")

        if not project:
            logger.error("No Google Cloud project configured")
            return False

        # Try a simple API call to verify connectivity
        client = storage.Client(project=project, credentials=credentials)

        # List buckets with a limit of 1 to minimize API calls
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: list(client.list_buckets(max_results=1))
            )
            logger.info("Successfully connected to Google Cloud project: %s", project)
            return True

        except google.api_core.exceptions.Forbidden:
            # This is actually OK - it means we're authenticated but don't have
            # permission to list buckets. Authentication is working.
            logger.info(
                "Connected to Google Cloud project: %s (limited permissions)", project
            )
            return True

    except DefaultCredentialsError:
        logger.error(
            "No Google Cloud credentials found. "
            "Set GOOGLE_APPLICATION_CREDENTIALS or run 'gcloud auth application-default login'"
        )
        return False

    except (ValueError, ImportError, AttributeError) as e:
        logger.error("Failed to connect to Google Cloud: %s", e)
        return False


async def list_compute_instances(
    project_id: Optional[str] = None,
    zone: str = "us-central1-a",
    filter_str: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List compute instances in a project.

    Args:
        project_id: GCP project ID (uses default if None)
        zone: Compute zone
        filter_str: Optional filter string

    Returns:
        List of instance dictionaries
    """
    try:
        project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("No project ID provided")

        # Create compute client
        compute_client = compute_v1.InstancesClient()

        # Build request
        request = compute_v1.ListInstancesRequest(project=project_id, zone=zone)

        if filter_str:
            request.filter = filter_str

        # Get instances
        loop = asyncio.get_event_loop()
        instances = await loop.run_in_executor(
            None, lambda: list(compute_client.list(request=request))
        )

        # Convert to dictionaries
        instance_list = []
        for instance in instances:
            instance_list.append(
                {
                    "name": instance.name,
                    "id": instance.id,
                    "status": instance.status,
                    "machine_type": instance.machine_type.split("/")[-1],
                    "zone": zone,
                    "creation_timestamp": instance.creation_timestamp,
                    "network_interfaces": [
                        {
                            "network": ni.network.split("/")[-1],
                            "internal_ip": ni.network_i_p,
                            "external_ip": (
                                ni.access_configs[0].nat_i_p
                                if ni.access_configs
                                else None
                            ),
                        }
                        for ni in instance.network_interfaces
                    ],
                    "labels": dict(instance.labels) if instance.labels else {},
                    "metadata": {
                        item.key: item.value for item in (instance.metadata.items or [])
                    },
                }
            )

        logger.info("Found %d instances in %s", len(instance_list), zone)
        return instance_list

    except Exception as e:
        logger.error("Failed to list compute instances: %s", e)
        raise


async def get_instance_details(
    instance_name: str, project_id: Optional[str] = None, zone: str = "us-central1-a"
) -> Optional[Dict[str, Any]]:
    """
    Get details of a specific compute instance.

    Args:
        instance_name: Name of the instance
        project_id: GCP project ID
        zone: Compute zone

    Returns:
        Instance details or None if not found
    """
    try:
        instances = await list_compute_instances(
            project_id=project_id, zone=zone, filter_str=f"name={instance_name}"
        )

        return instances[0] if instances else None

    except (ValueError, KeyError, AttributeError, TypeError) as e:
        logger.error("Failed to get instance details: %s", e)
        return None


async def stop_compute_instance(
    instance_name: str, project_id: Optional[str] = None, zone: str = "us-central1-a"
) -> bool:
    """
    Stop a compute instance.

    Args:
        instance_name: Name of the instance
        project_id: GCP project ID
        zone: Compute zone

    Returns:
        True if successful, False otherwise
    """
    try:
        project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("No project ID provided")

        compute_client = compute_v1.InstancesClient()

        # Stop the instance
        compute_client.stop(project=project_id, zone=zone, instance=instance_name)

        logger.info("Stopping instance %s in %s", instance_name, zone)

        # Wait for operation to complete
        # In production, you might want to handle this asynchronously
        return True

    except (ValueError, KeyError, AttributeError, TypeError) as e:
        logger.error("Failed to stop instance %s: %s", instance_name, e)
        return False


async def start_compute_instance(
    instance_name: str, project_id: Optional[str] = None, zone: str = "us-central1-a"
) -> bool:
    """
    Start a compute instance.

    Args:
        instance_name: Name of the instance
        project_id: GCP project ID
        zone: Compute zone

    Returns:
        True if successful, False otherwise
    """
    try:
        project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("No project ID provided")

        compute_client = compute_v1.InstancesClient()

        # Start the instance
        compute_client.start(project=project_id, zone=zone, instance=instance_name)

        logger.info("Starting instance %s in %s", instance_name, zone)
        return True

    except (ValueError, KeyError, AttributeError, TypeError) as e:
        logger.error("Failed to start instance %s: %s", instance_name, e)
        return False


async def create_storage_bucket(
    bucket_name: str,
    project_id: Optional[str] = None,
    location: str = "us-central1",
    storage_class: str = "STANDARD",
) -> bool:
    """
    Create a Cloud Storage bucket.

    Args:
        bucket_name: Name of the bucket
        project_id: GCP project ID
        location: Bucket location
        storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)

    Returns:
        True if successful, False otherwise
    """
    try:
        project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("No project ID provided")

        storage_client = storage.Client(project=project_id)

        bucket = storage_client.bucket(bucket_name)
        bucket.location = location
        bucket.storage_class = storage_class

        # Create bucket
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: storage_client.create_bucket(bucket))

        logger.info("Created bucket %s in %s", bucket_name, location)
        return True

    except google.api_core.exceptions.Conflict:
        logger.warning("Bucket %s already exists", bucket_name)
        return True

    except (ValueError, KeyError, AttributeError, TypeError) as e:
        logger.error("Failed to create bucket %s: %s", bucket_name, e)
        return False


# Singleton for caching GCP clients
class GCPClientManager:
    """Manages GCP client instances."""

    def __init__(self) -> None:
        self._storage_client: Optional[Any] = None
        self._compute_client: Optional[Any] = None
        self._project_id: Optional[str] = None

    @property
    def project_id(self) -> str:
        """Get the current project ID."""
        if not self._project_id:
            self._project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not self._project_id:
                try:
                    _, self._project_id = default()  # type: ignore[no-untyped-call]
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

        return self._project_id or ""

    @property
    def storage_client(self) -> Any:
        """Get or create storage client."""
        if not self._storage_client:
            if not STORAGE_AVAILABLE or not storage:
                raise ImportError("Google Cloud Storage client not available")
            self._storage_client = storage.Client(project=self.project_id)
        return self._storage_client

    @property
    def compute_client(self) -> Any:
        """Get or create compute client."""
        if not self._compute_client:
            if not COMPUTE_AVAILABLE or not compute_v1:
                raise ImportError("Google Cloud Compute client not available")
            self._compute_client = compute_v1.InstancesClient()
        return self._compute_client


# Global client manager
_gcp_client_manager = GCPClientManager()


def get_gcp_client_manager() -> GCPClientManager:
    """Get the global GCP client manager."""
    return _gcp_client_manager


def get_project_id() -> Optional[str]:
    """
    Get the GCP project ID from environment or metadata service.

    Returns:
        Project ID or None if not found
    """
    # Check environment variable first
    project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")

    if project_id:
        return project_id

    # Try to get from default credentials
    try:
        import google.auth as gauth

        _, project = gauth.default()  # type: ignore[no-untyped-call]
        return str(project) if project else None
    except (ImportError, ValueError, AttributeError):
        return None


def get_service_account_email() -> Optional[str]:
    """
    Get the service account email.

    Returns:
        Service account email or None
    """
    try:
        import google.auth as gauth

        credentials, _ = gauth.default()  # type: ignore[no-untyped-call]
        if hasattr(credentials, "service_account_email"):
            return str(credentials.service_account_email)
        return None
    except (ImportError, ValueError, AttributeError):
        return None


def generate_resource_name(base_name: str, resource_type: str) -> str:
    """
    Generate a GCP-compliant resource name.

    Args:
        base_name: Base name for the resource
        resource_type: Type of resource

    Returns:
        Generated resource name
    """
    # Clean the base name
    clean_base = base_name.lower().replace("_", "-").replace(" ", "-")
    clean_type = resource_type.lower().replace("_", "-").replace(" ", "-")

    # Generate a short UUID suffix
    suffix = str(uuid.uuid4())[:8]

    # Construct the name
    name = f"{clean_base}-{clean_type}-{suffix}"

    # Ensure it meets GCP requirements (max 63 chars, lowercase, hyphens)
    name = name[:63]

    return name


def parse_gcp_timestamp(timestamp_str: str) -> datetime:
    """
    Parse a GCP timestamp string.

    Args:
        timestamp_str: Timestamp string from GCP

    Returns:
        Parsed datetime object
    """
    # Handle various GCP timestamp formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    # If none of the formats work, try ISO format
    try:
        # Try ISO format with potential timezone
        if "T" in timestamp_str:
            # Replace Z with +00:00 for fromisoformat compatibility
            iso_str = timestamp_str.replace("Z", "+00:00")
            return datetime.fromisoformat(iso_str)
        else:
            # If no T, assume it's a date only
            return datetime.fromisoformat(timestamp_str)
    except ValueError:
        # As a last resort, try to parse basic formats
        # This handles cases like "2024-01-01 12:00:00"
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            # Give up and raise
            raise ValueError(f"Unable to parse timestamp: {timestamp_str}") from exc


def format_gcp_timestamp(dt: datetime) -> str:
    """
    Format a datetime for GCP APIs.

    Args:
        dt: Datetime object

    Returns:
        Formatted timestamp string
    """
    # GCP typically uses RFC3339 format
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

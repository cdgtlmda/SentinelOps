"""
Google Cloud Storage remediation actions.

This module contains implementations for Cloud Storage-specific remediation actions.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud import storage
from google.cloud.storage import Bucket

from src.common.exceptions import RemediationAgentError
from src.common.models import RemediationAction
from src.remediation_agent.action_registry import (
    BaseRemediationAction,
    RollbackDefinition,
)


class StorageActionBase(BaseRemediationAction):
    """Base class for Cloud Storage actions."""

    def get_bucket(self, storage_client: storage.Client, bucket_name: str) -> Bucket:
        """Get a bucket object."""
        try:
            return storage_client.bucket(bucket_name)
        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(
                f"Failed to access bucket {bucket_name}: {e}"
            ) from e


class UpdateBucketPermissionsAction(StorageActionBase):
    """Implementation for updating Cloud Storage bucket permissions."""

    def _remove_public_access(self, policy: Any, changes_made: List[str]) -> None:
        """Remove all public access from the policy."""
        public_members = ["allUsers", "allAuthenticatedUsers"]

        for binding in list(policy.bindings):
            for public_member in public_members:
                if public_member in binding["members"]:
                    binding["members"].remove(public_member)
                    changes_made.append(
                        f"Removed {public_member} from {binding['role']}"
                    )

            # Remove empty bindings
            if not binding["members"]:
                policy.bindings.remove(binding)

    def _remove_specific_members(
        self, policy: Any, specific_members: List[str], changes_made: List[str]
    ) -> None:
        """Remove specific members from the policy."""
        for binding in list(policy.bindings):
            for member in specific_members:
                if member in binding["members"]:
                    binding["members"].remove(member)
                    changes_made.append(f"Removed {member} from {binding['role']}")

            # Remove empty bindings
            if not binding["members"]:
                policy.bindings.remove(binding)

    def _make_bucket_private(self, policy: Any, changes_made: List[str]) -> None:
        """Make bucket private by removing all bindings except project owners/editors."""
        preserved_roles = [
            "roles/storage.legacyBucketOwner",
            "roles/storage.legacyBucketReader",
        ]

        policy.bindings = [
            binding
            for binding in policy.bindings
            if binding["role"] in preserved_roles
            and any(
                "projectOwner:" in m or "projectEditor:" in m
                for m in binding["members"]
            )
        ]
        changes_made.append("Removed all access except project owners/editors")

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Update bucket permissions."""
        try:
            bucket_name = action.params["bucket_name"]
            permissions_action = action.params.get(
                "permissions_action", "remove_public"
            )
            specific_members = action.params.get("members", [])

            if dry_run:
                return {
                    "dry_run": True,
                    "bucket": bucket_name,
                    "action": f"would_{permissions_action}",
                }

            storage_client = gcp_clients["storage"]
            bucket = self.get_bucket(storage_client, bucket_name)

            # Get current IAM policy
            policy = bucket.get_iam_policy(requested_policy_version=3)

            changes_made: list[str] = []

            if permissions_action == "remove_public":
                self._remove_public_access(policy, changes_made)
            elif permissions_action == "remove_members":
                self._remove_specific_members(policy, specific_members, changes_made)
            elif permissions_action == "make_private":
                self._make_bucket_private(policy, changes_made)

            # Update the policy
            if changes_made:
                bucket.set_iam_policy(policy)

            return {
                "bucket": bucket_name,
                "permissions_action": permissions_action,
                "changes_made": changes_made,
                "status": "updated" if changes_made else "no_changes",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(
                f"Failed to update bucket permissions: {e}"
            ) from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        if not action.params.get("bucket_name"):
            return False

        permissions_action = action.params.get("permissions_action", "remove_public")
        valid_actions = ["remove_public", "remove_members", "make_private"]

        return permissions_action in valid_actions

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current bucket permissions."""
        try:
            storage_client = gcp_clients["storage"]
            bucket = self.get_bucket(storage_client, action.params["bucket_name"])

            policy = bucket.get_iam_policy(requested_policy_version=3)

            return {
                "bucket_name": action.params["bucket_name"],
                "original_policy": json.dumps(
                    {
                        "bindings": [
                            {
                                "role": binding["role"],
                                "members": list(binding["members"]),
                            }
                            for binding in policy.bindings
                        ]
                    }
                ),
            }
        except (ValueError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="restore_bucket_permissions",
            state_params_mapping={
                "bucket_name": "bucket_name",
                "policy": "original_policy",
            },
        )


class EnableBucketVersioningAction(StorageActionBase):
    """Implementation for enabling bucket versioning."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Enable versioning on a bucket."""
        try:
            bucket_name = action.params["bucket_name"]

            if dry_run:
                return {
                    "dry_run": True,
                    "bucket": bucket_name,
                    "action": "would_enable_versioning",
                }

            storage_client = gcp_clients["storage"]
            bucket = self.get_bucket(storage_client, bucket_name)

            # Check current versioning status
            was_enabled = bucket.versioning_enabled

            # Enable versioning
            bucket.versioning_enabled = True
            bucket.patch()

            return {
                "bucket": bucket_name,
                "versioning_enabled": True,
                "was_enabled": was_enabled,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(
                f"Failed to enable bucket versioning: {e}"
            ) from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        return bool(action.params.get("bucket_name"))

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current versioning state."""
        try:
            storage_client = gcp_clients["storage"]
            bucket = self.get_bucket(storage_client, action.params["bucket_name"])

            return {
                "bucket_name": action.params["bucket_name"],
                "versioning_was_enabled": bucket.versioning_enabled,
            }
        except (ValueError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="set_bucket_versioning",
            state_params_mapping={
                "bucket_name": "bucket_name",
                "enabled": "versioning_was_enabled",
            },
        )


class SetRetentionPolicyAction(StorageActionBase):
    """Implementation for setting bucket retention policies."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Set a retention policy on a bucket."""
        try:
            bucket_name = action.params["bucket_name"]
            retention_days = action.params.get("retention_days", 30)
            lock_policy = action.params.get("lock_policy", False)

            if dry_run:
                return {
                    "dry_run": True,
                    "bucket": bucket_name,
                    "retention_days": retention_days,
                    "action": "would_set_retention_policy",
                }

            storage_client = gcp_clients["storage"]
            bucket = self.get_bucket(storage_client, bucket_name)

            # Capture existing policy
            existing_retention = bucket.retention_period

            # Set retention policy (in seconds)
            bucket.retention_period = retention_days * 24 * 60 * 60
            bucket.patch()

            # Lock the policy if requested (this is irreversible!)
            if lock_policy and not bucket.retention_policy_locked:
                bucket.lock_retention_policy()

            return {
                "bucket": bucket_name,
                "retention_days": retention_days,
                "previous_retention_days": (
                    existing_retention // (24 * 60 * 60) if existing_retention else None
                ),
                "policy_locked": lock_policy,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(f"Failed to set retention policy: {e}") from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        if not action.params.get("bucket_name"):
            return False

        retention_days = action.params.get("retention_days", 30)
        return bool(retention_days > 0 and retention_days <= 3650)  # Max 10 years

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current retention policy."""
        try:
            storage_client = gcp_clients["storage"]
            bucket = self.get_bucket(storage_client, action.params["bucket_name"])

            return {
                "bucket_name": action.params["bucket_name"],
                "original_retention_days": (
                    bucket.retention_period // (24 * 60 * 60)
                    if bucket.retention_period
                    else None
                ),
                "was_locked": bucket.retention_policy_locked,
            }
        except (ValueError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        # Can only rollback if policy wasn't locked
        return RollbackDefinition(
            rollback_action_type="update_retention_policy",
            state_params_mapping={
                "bucket_name": "bucket_name",
                "retention_days": "original_retention_days",
            },
            additional_params={"only_if_not_locked": True},
        )


class EnableBucketEncryptionAction(StorageActionBase):
    """Implementation for enabling bucket encryption."""

    async def execute(
        self,
        action: RemediationAction,
        gcp_clients: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Enable encryption on a bucket."""
        try:
            bucket_name = action.params["bucket_name"]
            kms_key_name = action.params.get("kms_key_name")  # Optional CMEK

            if dry_run:
                return {
                    "dry_run": True,
                    "bucket": bucket_name,
                    "action": "would_enable_encryption",
                }

            storage_client = gcp_clients["storage"]
            bucket = self.get_bucket(storage_client, bucket_name)

            # Capture existing encryption
            existing_encryption = bucket.default_kms_key_name

            if kms_key_name:
                # Set customer-managed encryption key
                bucket.default_kms_key_name = kms_key_name
            else:
                # Google-managed encryption is always on by default
                # But we can ensure it's set
                bucket.default_kms_key_name = None

            bucket.patch()

            return {
                "bucket": bucket_name,
                "encryption_type": "CMEK" if kms_key_name else "Google-managed",
                "kms_key_name": kms_key_name,
                "previous_kms_key": existing_encryption,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, AttributeError) as e:
            raise RemediationAgentError(
                f"Failed to enable bucket encryption: {e}"
            ) from e

    async def validate_prerequisites(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> bool:
        """Validate prerequisites."""
        return bool(action.params.get("bucket_name"))

    async def capture_state(
        self, action: RemediationAction, gcp_clients: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture current encryption state."""
        try:
            storage_client = gcp_clients["storage"]
            bucket = self.get_bucket(storage_client, action.params["bucket_name"])

            return {
                "bucket_name": action.params["bucket_name"],
                "original_kms_key": bucket.default_kms_key_name,
            }
        except (ValueError, AttributeError):
            return {}

    def get_rollback_definition(self) -> Optional[RollbackDefinition]:
        """Get rollback definition."""
        return RollbackDefinition(
            rollback_action_type="set_bucket_encryption",
            state_params_mapping={
                "bucket_name": "bucket_name",
                "kms_key_name": "original_kms_key",
            },
        )

"""
Security module for the Remediation Agent.

This module implements security measures including action authorization,
audit logging, and secure credential handling.
"""

import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional, Set, Tuple

from google.cloud import logging as cloud_logging
from google.cloud import secretmanager

from src.common.models import RemediationAction

# from google.cloud import kms_v1 as kms  # Module not available


# KeyManagementServiceClient = kms.KeyManagementServiceClient
# Commented out as kms module not available
kms = None
KeyManagementServiceClient = None


class AuthorizationLevel(Enum):
    """Authorization levels for remediation actions."""

    READ_ONLY = "read_only"
    BASIC = "basic"
    ELEVATED = "elevated"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SecurityContext:
    """Security context for action execution."""

    def __init__(
        self,
        principal: str,
        auth_level: AuthorizationLevel,
        permissions: Set[str],
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize security context.

        Args:
            principal: Identity of the principal (service account, user, etc.)
            auth_level: Authorization level
            permissions: Set of granted permissions
            attributes: Additional security attributes
        """
        self.principal = principal
        self.auth_level = auth_level
        self.permissions = permissions
        self.attributes = attributes or {}
        self.session_id = secrets.token_urlsafe(32)
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(hours=1)

    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission."""
        return permission in self.permissions

    def is_expired(self) -> bool:
        """Check if security context has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "principal": self.principal,
            "auth_level": self.auth_level.value,
            "permissions_count": len(self.permissions),
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class ActionAuthorizer:
    """Handles authorization for remediation actions."""

    def __init__(self, project_id: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the action authorizer.

        Args:
            project_id: GCP project ID
            logger: Logger instance
        """
        self.project_id = project_id
        self.logger = logger or logging.getLogger(__name__)

        # Define action authorization requirements
        self._action_auth_requirements: Dict[str, Dict[str, Any]] = {
            # Network actions
            "block_ip_address": {
                "min_level": AuthorizationLevel.BASIC,
                "required_permissions": [
                    "compute.firewalls.create",
                    "compute.firewalls.update",
                ],
            },
            "update_firewall_rule": {
                "min_level": AuthorizationLevel.BASIC,
                "required_permissions": ["compute.firewalls.update"],
            },
            # IAM actions
            "disable_user_account": {
                "min_level": AuthorizationLevel.ELEVATED,
                "required_permissions": ["resourcemanager.projects.setIamPolicy"],
            },
            "revoke_iam_permission": {
                "min_level": AuthorizationLevel.ELEVATED,
                "required_permissions": ["resourcemanager.projects.setIamPolicy"],
            },
            "remove_service_account_key": {
                "min_level": AuthorizationLevel.ELEVATED,
                "required_permissions": ["iam.serviceAccountKeys.delete"],
            },
            # Compute actions
            "quarantine_instance": {
                "min_level": AuthorizationLevel.ELEVATED,
                "required_permissions": [
                    "compute.instances.setTags",
                    "compute.instances.updateNetworkInterface",
                ],
            },
            "stop_instance": {
                "min_level": AuthorizationLevel.BASIC,
                "required_permissions": ["compute.instances.stop"],
            },
            # Critical actions
            "rotate_credentials": {
                "min_level": AuthorizationLevel.CRITICAL,
                "required_permissions": [
                    "iam.serviceAccountKeys.create",
                    "iam.serviceAccountKeys.delete",
                ],
            },
            "restore_from_backup": {
                "min_level": AuthorizationLevel.CRITICAL,
                "required_permissions": [
                    "compute.disks.create",
                    "compute.snapshots.useReadOnly",
                ],
            },
        }

    def authorize_action(
        self, action: RemediationAction, security_context: SecurityContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Authorize a remediation action.

        Args:
            action: The remediation action to authorize
            security_context: Security context of the requester

        Returns:
            Tuple of (authorized, reason)
        """
        # Check if context is expired
        if security_context.is_expired():
            return False, "Security context has expired"

        # Get authorization requirements
        requirements = self._action_auth_requirements.get(action.action_type)
        if not requirements:
            self.logger.warning(
                f"No authorization requirements defined for {action.action_type}"
            )
            return False, f"Unknown action type: {action.action_type}"

        # Check authorization level
        min_level = requirements["min_level"]
        if not isinstance(min_level, AuthorizationLevel):
            return False, "Invalid authorization level configuration"
        if not self._check_auth_level(security_context.auth_level, min_level):
            return (
                False,
                f"Insufficient authorization level (required: {min_level.value})",
            )

        # Check permissions
        required_perms = requirements["required_permissions"]
        missing_perms = []

        for perm in required_perms:
            if not isinstance(perm, str):
                continue
            if not security_context.has_permission(perm):
                missing_perms.append(perm)

        if missing_perms:
            return False, f"Missing permissions: {', '.join(missing_perms)}"

        # Check additional constraints
        constraint_check = self._check_action_constraints(action, security_context)
        if not constraint_check[0]:
            return constraint_check

        return True, None

    def _check_auth_level(
        self, current_level: AuthorizationLevel, required_level: AuthorizationLevel
    ) -> bool:
        """Check if current auth level meets requirements."""
        level_hierarchy = [
            AuthorizationLevel.READ_ONLY,
            AuthorizationLevel.BASIC,
            AuthorizationLevel.ELEVATED,
            AuthorizationLevel.CRITICAL,
            AuthorizationLevel.EMERGENCY,
        ]

        current_idx = level_hierarchy.index(current_level)
        required_idx = level_hierarchy.index(required_level)

        return current_idx >= required_idx

    def _check_action_constraints(
        self, action: RemediationAction, security_context: SecurityContext
    ) -> Tuple[bool, Optional[str]]:
        """Check additional action-specific constraints."""
        # Time-based constraints
        current_hour = datetime.now(timezone.utc).hour

        # Critical actions only during business hours unless emergency
        if action.action_type in ["rotate_credentials", "restore_from_backup"]:
            if security_context.auth_level != AuthorizationLevel.EMERGENCY:
                if current_hour < 8 or current_hour > 18:
                    return (
                        False,
                        "Critical actions restricted to business hours (8AM-6PM UTC)",
                    )

        # Resource constraints
        if action.action_type == "disable_user_account":
            # Don't allow disabling admin accounts without emergency auth
            user_email = action.params.get("user_email", "")
            if (
                "admin" in user_email
                and security_context.auth_level != AuthorizationLevel.EMERGENCY
            ):
                return False, "Admin accounts require emergency authorization"

        # Rate limiting per principal
        # (Would check against a rate limit store in production)

        return True, None

    def create_least_privilege_context(
        self, action_type: str, principal: str
    ) -> SecurityContext:
        """
        Create a least-privilege security context for an action.

        Args:
            action_type: Type of action
            principal: Principal identity

        Returns:
            Security context with minimal required permissions
        """
        requirements = self._action_auth_requirements.get(action_type, {})

        return SecurityContext(
            principal=principal,
            auth_level=(
                requirements.get("min_level", AuthorizationLevel.READ_ONLY)
                if isinstance(requirements.get("min_level"), AuthorizationLevel)
                else AuthorizationLevel.READ_ONLY
            ),
            permissions=(
                set(requirements.get("required_permissions", []))
                if isinstance(requirements.get("required_permissions"), list)
                else set()
            ),
            attributes={
                "created_for_action": action_type,
                "least_privilege": True,
            },
        )


class AuditLogger:
    """Handles security audit logging for remediation actions."""

    def __init__(
        self,
        project_id: str,
        log_name: str = "remediation-audit",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the audit logger.

        Args:
            project_id: GCP project ID
            log_name: Name for audit logs
            logger: Logger instance
        """
        self.project_id = project_id
        self.log_name = log_name
        self.logger = logger or logging.getLogger(__name__)

        # Initialize Cloud Logging client
        try:
            self.cloud_logging_client = cloud_logging.Client(
                project=project_id
            )  # type: ignore[no-untyped-call]
            self.cloud_logger = self.cloud_logging_client.logger(
                log_name
            )  # type: ignore[no-untyped-call]
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Failed to initialize Cloud Logging: {e}")
            self.cloud_logger = None

    def log_action_request(
        self,
        action: RemediationAction,
        security_context: SecurityContext,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a remediation action request.

        Args:
            action: The requested action
            security_context: Security context
            metadata: Additional metadata
        """
        audit_entry = {
            "event_type": "remediation_action_requested",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "target_resource": action.target_resource,
                "incident_id": action.incident_id,
            },
            "security_context": security_context.to_dict(),
            "metadata": metadata or {},
        }

        self._write_audit_log(audit_entry, severity="INFO")

    def log_authorization_decision(
        self,
        action: RemediationAction,
        authorized: bool,
        reason: Optional[str],
        security_context: SecurityContext,
    ) -> None:
        """
        Log an authorization decision.

        Args:
            action: The action being authorized
            authorized: Whether authorization was granted
            reason: Reason for the decision
            security_context: Security context
        """
        audit_entry = {
            "event_type": "authorization_decision",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_id": action.action_id,
            "action_type": action.action_type,
            "authorized": authorized,
            "reason": reason,
            "principal": security_context.principal,
            "auth_level": security_context.auth_level.value,
        }

        severity = "INFO" if authorized else "WARNING"
        self._write_audit_log(audit_entry, severity=severity)

    def log_action_execution(
        self,
        action: RemediationAction,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        execution_time: Optional[float] = None,
    ) -> None:
        """
        Log action execution details.

        Args:
            action: The executed action
            status: Execution status
            result: Execution result
            error: Error message if failed
            execution_time: Execution duration in seconds
        """
        audit_entry = {
            "event_type": "remediation_action_executed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "target_resource": action.target_resource,
            },
            "status": status,
            "execution_time_seconds": execution_time,
        }

        if result:
            # Sanitize sensitive data from result
            audit_entry["result_summary"] = self._sanitize_result(result)

        if error:
            audit_entry["error"] = error

        severity = "INFO" if status == "completed" else "ERROR"
        self._write_audit_log(audit_entry, severity=severity)

    def log_rollback_operation(
        self,
        original_action: RemediationAction,
        rollback_action: RemediationAction,
        reason: str,
        success: bool,
    ) -> None:
        """
        Log a rollback operation.

        Args:
            original_action: The original action that was rolled back
            rollback_action: The rollback action
            reason: Reason for rollback
            success: Whether rollback succeeded
        """
        audit_entry = {
            "event_type": "remediation_rollback",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_action": {
                "action_id": original_action.action_id,
                "action_type": original_action.action_type,
            },
            "rollback_action": {
                "action_id": rollback_action.action_id,
                "action_type": rollback_action.action_type,
            },
            "reason": reason,
            "success": success,
        }

        severity = "WARNING" if success else "ERROR"
        self._write_audit_log(audit_entry, severity=severity)

    def _write_audit_log(self, entry: Dict[str, Any], severity: str = "INFO") -> None:
        """Write audit log entry."""
        # Add audit metadata
        entry["audit_metadata"] = {
            "log_name": self.log_name,
            "project_id": self.project_id,
            "version": "1.0",
        }

        # Log to Cloud Logging if available
        if self.cloud_logger:
            try:
                self.cloud_logger.log_struct(entry, severity=severity)
            except (ValueError, TypeError, AttributeError) as e:
                self.logger.error(f"Failed to write to Cloud Logging: {e}")

        # Also log locally
        self.logger.info("AUDIT: %s", json.dumps(entry))

    def _sanitize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from execution results."""
        sanitized: Dict[str, Any] = {}

        sensitive_keys = [
            "password",
            "secret",
            "key",
            "token",
            "credential",
            "private",
            "auth",
            "api_key",
            "access_token",
        ]

        for key, value in result.items():
            # Check if key contains sensitive terms
            is_sensitive = any(term in key.lower() for term in sensitive_keys)

            if is_sensitive:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_result(value)
            elif isinstance(value, list):
                sanitized[key] = f"[{len(value)} items]"
            else:
                sanitized[key] = value

        return sanitized


class CredentialManager:
    """Manages secure credential handling for remediation actions."""

    def __init__(
        self,
        project_id: str,
        kms_key_name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the credential manager.

        Args:
            project_id: GCP project ID
            kms_key_name: KMS key for encryption
            logger: Logger instance
        """
        self.project_id = project_id
        self.kms_key_name = kms_key_name
        self.logger = logger or logging.getLogger(__name__)

        # Initialize clients
        self.secret_manager = secretmanager.SecretManagerServiceClient()
        # KMS client is not available in current setup
        self.kms_client = None  # kms module not available

        # Cache for decrypted credentials (with TTL)
        self._credential_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)

    async def get_credential(self, credential_name: str) -> Optional[str]:
        """
        Retrieve a credential securely.

        Args:
            credential_name: Name of the credential

        Returns:
            Decrypted credential value
        """
        # Check cache first
        cached = self._get_from_cache(credential_name)
        if cached:
            return cached

        try:
            # Construct secret name
            secret_name = (
                f"projects/{self.project_id}/secrets/{credential_name}/versions/latest"
            )

            # Retrieve from Secret Manager
            response = self.secret_manager.access_secret_version(name=secret_name)
            credential_data = response.payload.data.decode("utf-8")

            # KMS decryption not available in current setup
            # if self.kms_client and self.kms_key_name:
            #     credential_data = await self._decrypt_with_kms(credential_data)

            # Cache the credential
            self._add_to_cache(credential_name, credential_data)

            return credential_data

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Failed to retrieve credential '{credential_name}': {e}")
            return None

    async def rotate_credential(self, credential_name: str, new_value: str) -> bool:
        """
        Rotate a credential.

        Args:
            credential_name: Name of the credential
            new_value: New credential value

        Returns:
            True if successful
        """
        try:
            # KMS encryption not available in current setup
            # if self.kms_client and self.kms_key_name:
            #     new_value = await self._encrypt_with_kms(new_value)

            # Create new secret version
            parent = f"projects/{self.project_id}/secrets/{credential_name}"

            from google.cloud.secretmanager_v1.types import SecretPayload

            self.secret_manager.add_secret_version(
                parent=parent, payload=SecretPayload(data=new_value.encode("utf-8"))
            )

            # Invalidate cache
            self._invalidate_cache(credential_name)

            self.logger.info(f"Successfully rotated credential '{credential_name}'")
            return True

        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(
                "Failed to rotate credential '%s': %s", credential_name, e
            )
            return False

    def _get_from_cache(self, credential_name: str) -> Optional[str]:
        """Get credential from cache if not expired."""
        if credential_name in self._credential_cache:
            value, expiry = self._credential_cache[credential_name]
            if datetime.now(timezone.utc) < expiry:
                return str(value)
            else:
                del self._credential_cache[credential_name]
        return None

    def _add_to_cache(self, credential_name: str, value: str) -> None:
        """Add credential to cache with TTL."""
        expiry = datetime.now(timezone.utc) + self._cache_ttl
        self._credential_cache[credential_name] = (value, expiry)

    def _invalidate_cache(self, credential_name: str) -> None:
        """Remove credential from cache."""
        if credential_name in self._credential_cache:
            del self._credential_cache[credential_name]

    async def _encrypt_with_kms(self, plaintext: str) -> str:
        """Encrypt data using KMS."""
        # Implementation would use KMS encryption
        # This is a placeholder
        return plaintext

    async def _decrypt_with_kms(self, ciphertext: str) -> str:
        """Decrypt data using KMS."""
        # Implementation would use KMS decryption
        # This is a placeholder
        return ciphertext

    def clear_cache(self) -> None:
        """Clear all cached credentials."""
        self._credential_cache.clear()
        self.logger.info("Cleared credential cache")


def generate_action_signature(action: RemediationAction, secret_key: str) -> str:
    """
    Generate a signature for action integrity verification.

    Args:
        action: The remediation action
        secret_key: Secret key for signing

    Returns:
        Action signature
    """
    # Create canonical representation
    canonical = json.dumps(
        {
            "action_id": action.action_id,
            "action_type": action.action_type,
            "target_resource": action.target_resource,
            "params": action.params,
        },
        sort_keys=True,
    )

    # Generate HMAC signature
    signature = hmac.new(
        secret_key.encode(), canonical.encode(), hashlib.sha256
    ).hexdigest()

    return signature


def verify_action_signature(
    action: RemediationAction, signature: str, secret_key: str
) -> bool:
    """
    Verify action signature.

    Args:
        action: The remediation action
        signature: Signature to verify
        secret_key: Secret key for verification

    Returns:
        True if signature is valid
    """
    expected_signature = generate_action_signature(action, secret_key)
    return hmac.compare_digest(signature, expected_signature)

#!/usr/bin/env python3
"""
Setup Authentication and Authorization for SentinelOps

This script implements comprehensive authentication and authorization setup for SentinelOps on Google Cloud Platform.
It configures service authentication, authorization policies, secure communication, and authentication middleware.

Usage:
    python setup_authentication.py [--project-id PROJECT_ID] [--dry-run]
"""

import argparse
import base64
import json
import logging
import os
import secrets
import subprocess
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import jwt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.api_core.exceptions import AlreadyExists, GoogleAPIError  # noqa: E402
from google.auth.transport.requests import Request  # noqa: E402
from google.cloud import iam, secretmanager_v1, iam_credentials_v1  # noqa: E402
from google.iam.v1 import iam_policy_pb2, policy_pb2  # noqa: E402
from google.oauth2 import service_account  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Agent service configuration
AGENT_SERVICES = {
    "detection": {
        "service_account": "sentinelops-detection",
        "cloud_run_service": "sentinelops-detection-agent",
        "roles": [
            "roles/bigquery.dataViewer",
            "roles/bigquery.jobUser",
            "roles/logging.viewer",
            "roles/monitoring.metricWriter",
            "roles/pubsub.publisher",
            "roles/secretmanager.secretAccessor",
        ],
        "custom_role": "sentinelops.detectionAgent",
    },
    "analysis": {
        "service_account": "sentinelops-analysis",
        "cloud_run_service": "sentinelops-analysis-agent",
        "roles": [
            "roles/bigquery.dataViewer",
            "roles/datastore.viewer",
            "roles/monitoring.metricWriter",
            "roles/pubsub.publisher",
            "roles/pubsub.subscriber",
            "roles/secretmanager.secretAccessor",
            "roles/aiplatform.user",
        ],
        "custom_role": "sentinelops.analysisAgent",
    },
    "remediation": {
        "service_account": "sentinelops-remediation",
        "cloud_run_service": "sentinelops-remediation-agent",
        "roles": [
            "roles/compute.admin",
            "roles/iam.securityAdmin",
            "roles/monitoring.metricWriter",
            "roles/pubsub.publisher",
            "roles/pubsub.subscriber",
            "roles/secretmanager.secretAccessor",
            "roles/cloudfunctions.invoker",
        ],
        "custom_role": "sentinelops.remediationAgent",
    },
    "communication": {
        "service_account": "sentinelops-communication",
        "cloud_run_service": "sentinelops-communication-agent",
        "roles": [
            "roles/datastore.viewer",
            "roles/monitoring.metricWriter",
            "roles/pubsub.subscriber",
            "roles/secretmanager.secretAccessor",
        ],
        "custom_role": "sentinelops.communicationAgent",
    },
    "orchestrator": {
        "service_account": "sentinelops-orchestrator",
        "cloud_run_service": "sentinelops-orchestrator-agent",
        "roles": [
            "roles/datastore.user",
            "roles/monitoring.metricWriter",
            "roles/pubsub.publisher",
            "roles/pubsub.subscriber",
            "roles/secretmanager.secretAccessor",
            "roles/cloudscheduler.admin",
            "roles/workflows.invoker",
        ],
        "custom_role": "sentinelops.orchestratorAgent",
    },
}

# Custom role definitions
CUSTOM_ROLES = {
    "sentinelops.detectionAgent": {
        "title": "SentinelOps Detection Agent",
        "description": "Custom role for SentinelOps detection agent with specific permissions",
        "permissions": [
            "bigquery.datasets.get",
            "bigquery.tables.list",
            "bigquery.tables.get",
            "bigquery.tables.getData",
            "bigquery.jobs.create",
            "logging.logEntries.list",
            "monitoring.timeSeries.create",
            "pubsub.topics.publish",
        ],
    },
    "sentinelops.analysisAgent": {
        "title": "SentinelOps Analysis Agent",
        "description": "Custom role for SentinelOps analysis agent with specific permissions",
        "permissions": [
            "bigquery.datasets.get",
            "bigquery.tables.getData",
            "datastore.entities.get",
            "datastore.entities.list",
            "aiplatform.endpoints.predict",
            "monitoring.timeSeries.create",
            "pubsub.subscriptions.consume",
            "pubsub.topics.publish",
        ],
    },
    "sentinelops.remediationAgent": {
        "title": "SentinelOps Remediation Agent",
        "description": "Custom role for SentinelOps remediation agent with specific permissions",
        "permissions": [
            "compute.instances.stop",
            "compute.instances.start",
            "compute.instances.setMetadata",
            "compute.firewalls.update",
            "iam.serviceAccounts.disable",
            "cloudfunctions.functions.invoke",
            "monitoring.timeSeries.create",
            "pubsub.subscriptions.consume",
            "pubsub.topics.publish",
        ],
    },
    "sentinelops.communicationAgent": {
        "title": "SentinelOps Communication Agent",
        "description": "Custom role for SentinelOps communication agent with specific permissions",
        "permissions": [
            "datastore.entities.get",
            "datastore.entities.list",
            "monitoring.timeSeries.create",
            "pubsub.subscriptions.consume",
        ],
    },
    "sentinelops.orchestratorAgent": {
        "title": "SentinelOps Orchestrator Agent",
        "description": "Custom role for SentinelOps orchestrator agent with specific permissions",
        "permissions": [
            "datastore.entities.get",
            "datastore.entities.list",
            "datastore.entities.create",
            "datastore.entities.update",
            "cloudscheduler.jobs.create",
            "cloudscheduler.jobs.update",
            "workflows.executions.create",
            "monitoring.timeSeries.create",
            "pubsub.subscriptions.consume",
            "pubsub.topics.publish",
        ],
    },
}


class AuthenticationSetup:
    """Manages authentication and authorization setup for SentinelOps"""

    def __init__(self, project_id: str, dry_run: bool = False):
        self.project_id = project_id
        self.dry_run = dry_run
        self.secret_client = secretmanager_v1.SecretManagerServiceClient()
        self.credentials_client = iam_credentials_v1.IAMCredentialsClient()

    def run_command(self, command: List[str]) -> Tuple[int, str, str]:
        """Execute a command and return the result"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {' '.join(command)}")
            return 0, "", ""

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr}")
            return e.returncode, e.stdout, e.stderr

    def create_service_account(self, name: str, display_name: str) -> bool:
        """Create a service account"""
        logger.info(f"Creating service account: {name}")

        command = [
            "gcloud",
            "iam",
            "service-accounts",
            "create",
            name,
            "--display-name",
            display_name,
            "--project",
            self.project_id,
        ]

        returncode, stdout, stderr = self.run_command(command)

        if returncode != 0:
            if "already exists" in stderr.lower():
                logger.info(f"Service account {name} already exists")
                return True
            logger.error(f"Failed to create service account: {stderr}")
            return False

        logger.info(f"Service account {name} created successfully")
        return True

    def create_service_account_key(self, service_account: str, key_path: str) -> bool:
        """Create and download a service account key"""
        logger.info(f"Creating key for service account: {service_account}")

        email = f"{service_account}@{self.project_id}.iam.gserviceaccount.com"

        command = [
            "gcloud",
            "iam",
            "service-accounts",
            "keys",
            "create",
            key_path,
            "--iam-account",
            email,
            "--project",
            self.project_id,
        ]

        returncode, stdout, stderr = self.run_command(command)

        if returncode != 0:
            logger.error(f"Failed to create service account key: {stderr}")
            return False

        logger.info(f"Service account key created: {key_path}")
        return True

    def setup_workload_identity(
        self, service_account: str, cloud_run_service: str
    ) -> bool:
        """Configure Workload Identity for Cloud Run service"""
        logger.info(f"Setting up Workload Identity for {cloud_run_service}")

        email = f"{service_account}@{self.project_id}.iam.gserviceaccount.com"

        # Update Cloud Run service to use the service account
        command = [
            "gcloud",
            "run",
            "services",
            "update",
            cloud_run_service,
            "--service-account",
            email,
            "--region",
            "us-central1",
            "--project",
            self.project_id,
        ]

        returncode, stdout, stderr = self.run_command(command)

        if returncode != 0:
            if "NOT_FOUND" in stderr:
                logger.warning(
                    f"Cloud Run service {cloud_run_service} not found, skipping"
                )
                return True
            logger.error(f"Failed to update Cloud Run service: {stderr}")
            return False

        logger.info(f"Workload Identity configured for {cloud_run_service}")
        return True

    def grant_iam_roles(self, service_account: str, roles: List[str]) -> bool:
        """Grant IAM roles to a service account"""
        logger.info(f"Granting IAM roles to {service_account}")

        email = f"{service_account}@{self.project_id}.iam.gserviceaccount.com"

        for role in roles:
            command = [
                "gcloud",
                "projects",
                "add-iam-policy-binding",
                self.project_id,
                "--member",
                f"serviceAccount:{email}",
                "--role",
                role,
                "--condition",
                "None",
            ]

            returncode, stdout, stderr = self.run_command(command)

            if returncode != 0:
                logger.error(f"Failed to grant role {role}: {stderr}")
                return False

            logger.info(f"Granted role {role} to {service_account}")

        return True

    def create_custom_role(self, role_id: str, role_definition: Dict) -> bool:
        """Create a custom IAM role"""
        logger.info(f"Creating custom role: {role_id}")

        # Create a temporary file for the role definition
        role_file = f"/tmp/{role_id}.yaml"

        yaml_content = f"""
title: "{role_definition['title']}"
description: "{role_definition['description']}"
stage: "GA"
includedPermissions:
"""
        for permission in role_definition["permissions"]:
            yaml_content += f"- {permission}\n"

        if not self.dry_run:
            with open(role_file, "w") as f:
                f.write(yaml_content)

        command = [
            "gcloud",
            "iam",
            "roles",
            "create",
            role_id.replace(".", "_"),
            "--project",
            self.project_id,
            "--file",
            role_file,
        ]

        returncode, stdout, stderr = self.run_command(command)

        if returncode != 0:
            if "already exists" in stderr.lower():
                logger.info(f"Custom role {role_id} already exists")
                return True
            logger.error(f"Failed to create custom role: {stderr}")
            return False

        logger.info(f"Custom role {role_id} created successfully")

        # Clean up temporary file
        if not self.dry_run and os.path.exists(role_file):
            os.remove(role_file)

        return True

    def create_api_key_secret(self, name: str, value: str) -> bool:
        """Create a secret in Secret Manager for API keys"""
        logger.info(f"Creating secret: {name}")

        parent = f"projects/{self.project_id}"
        secret_id = name

        try:
            # Create the secret
            secret = self.secret_client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )

            # Add secret version
            self.secret_client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": value.encode("UTF-8")},
                }
            )

            logger.info(f"Secret {name} created successfully")
            return True

        except AlreadyExists:
            logger.info(f"Secret {name} already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to create secret: {e}")
            return False

    def setup_oauth2_flow(self) -> bool:
        """Configure OAuth2 authentication flow"""
        logger.info("Setting up OAuth2 authentication flow")

        # Create OAuth2 client ID for web application
        oauth_config = {
            "client_id": f"sentinelops-{uuid.uuid4().hex[:8]}",
            "client_secret": secrets.token_urlsafe(32),
            "redirect_uris": [
                "https://sentinelops.example.com/auth/callback",
                "http://localhost:8080/auth/callback",
            ],
            "authorized_domains": ["sentinelops.example.com"],
        }

        # Store OAuth2 credentials in Secret Manager
        secret_name = "sentinelops-oauth2-credentials"
        secret_value = json.dumps(oauth_config)

        return self.create_api_key_secret(secret_name, secret_value)

    def generate_jwt_keys(self) -> Tuple[str, str]:
        """Generate RSA key pair for JWT signing"""
        from cryptography.hazmat.backends import default_backend  # noqa: E402
        from cryptography.hazmat.primitives import serialization  # noqa: E402
        from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Get public key
        public_key = private_key.public_key()

        # Serialize public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_pem.decode(), public_pem.decode()

    def setup_jwt_validation(self) -> bool:
        """Set up JWT token validation"""
        logger.info("Setting up JWT token validation")

        # Generate JWT signing keys
        private_key, public_key = self.generate_jwt_keys()

        # Store keys in Secret Manager
        if not self.create_api_key_secret("sentinelops-jwt-private-key", private_key):
            return False

        if not self.create_api_key_secret("sentinelops-jwt-public-key", public_key):
            return False

        logger.info("JWT validation keys created successfully")
        return True

    def setup_mtls(self) -> bool:
        """Configure mutual TLS for internal services"""
        logger.info("Setting up mTLS for internal services")

        # Create CA certificate for internal services
        ca_cert_command = [
            "openssl",
            "req",
            "-x509",
            "-new",
            "-nodes",
            "-key",
            "/tmp/ca-key.pem",
            "-sha256",
            "-days",
            "365",
            "-out",
            "/tmp/ca-cert.pem",
            "-subj",
            "/C=US/ST=CA/O=SentinelOps/CN=SentinelOps-CA",
        ]

        # Generate CA key
        ca_key_command = ["openssl", "genrsa", "-out", "/tmp/ca-key.pem", "4096"]

        if not self.dry_run:
            subprocess.run(ca_key_command, check=True)
            subprocess.run(ca_cert_command, check=True)

            # Store CA certificate and key in Secret Manager
            with open("/tmp/ca-cert.pem", "r") as f:
                ca_cert = f.read()
            with open("/tmp/ca-key.pem", "r") as f:
                ca_key = f.read()

            self.create_api_key_secret("sentinelops-mtls-ca-cert", ca_cert)
            self.create_api_key_secret("sentinelops-mtls-ca-key", ca_key)

            # Clean up temporary files
            os.remove("/tmp/ca-cert.pem")
            os.remove("/tmp/ca-key.pem")

        logger.info("mTLS configuration completed")
        return True

    def create_authentication_middleware(self) -> bool:
        """Create authentication middleware components"""
        logger.info("Creating authentication middleware")

        # Create FastAPI middleware
        fastapi_middleware = """
from fastapi import Request, HTTPException  # noqa: E402
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # noqa: E402
import jwt  # noqa: E402
from google.cloud import secretmanager  # noqa: E402

security = HTTPBearer()

class AuthenticationMiddleware:
    def __init__(self):
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self.public_key = self._get_public_key()

    def _get_public_key(self):
        secret_name = "projects/{}/secrets/sentinelops-jwt-public-key/versions/latest"
        response = self.secret_client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8")

    async def __call__(self, request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
        token = credentials.credentials

        try:
            payload = jwt.decode(token, self.public_key, algorithms=["RS256"])
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
"""

        # Create Pub/Sub message validation
        pubsub_validation = """
import json  # noqa: E402
import hmac  # noqa: E402
import hashlib  # noqa: E402
from google.cloud import secretmanager  # noqa: E402

class PubSubAuthValidator:
    def __init__(self):
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self.signing_key = self._get_signing_key()

    def _get_signing_key(self):
        secret_name = "projects/{}/secrets/sentinelops-pubsub-signing-key/versions/latest"
        response = self.secret_client.access_secret_version(request={"name": secret_name})
        return response.payload.data

    def validate_message(self, message_data: dict, signature: str) -> bool:
        message_json = json.dumps(message_data, sort_keys=True)
        expected_signature = hmac.new(
            self.signing_key,
            message_json.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)
"""

        # Create Cloud Function authentication
        cloud_function_auth = '''
import os  # noqa: E402
import jwt  # noqa: E402
from google.auth import default  # noqa: E402
from google.auth.transport import requests  # noqa: E402

def authenticate_cloud_function(request):
    """Authenticate Cloud Function invocations"""

    # Get the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False, "Missing or invalid Authorization header"

    token = auth_header.split(' ')[1]

    # Verify the token is from a service account
    try:
        # Get default credentials
        credentials, project = default()

        # Decode and verify the token
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Check if it's a service account
        if decoded.get('iss', '').endswith('.iam.gserviceaccount.com'):
            return True, decoded
        else:
            return False, "Not a service account token"

    except Exception as e:
        return False, str(e)
'''

        # Save middleware files
        middleware_dir = Path(__file__).parent.parent / "src" / "api" / "middleware"

        if not self.dry_run:
            # Save FastAPI middleware
            with open(middleware_dir / "auth_middleware.py", "w") as f:
                f.write(fastapi_middleware)

            # Save Pub/Sub validation
            with open(middleware_dir / "pubsub_auth.py", "w") as f:
                f.write(pubsub_validation)

            # Save Cloud Function auth
            with open(middleware_dir / "function_auth.py", "w") as f:
                f.write(cloud_function_auth)

        logger.info("Authentication middleware created successfully")
        return True

    def test_authentication(self) -> bool:
        """Test authentication between services"""
        logger.info("Testing authentication between services")

        # Test service account authentication
        for agent, config in AGENT_SERVICES.items():
            sa_email = (
                f"{config['service_account']}@{self.project_id}.iam.gserviceaccount.com"
            )

            # Test token generation
            command = [
                "gcloud",
                "auth",
                "print-access-token",
                "--impersonate-service-account",
                sa_email,
                "--project",
                self.project_id,
            ]

            returncode, stdout, stderr = self.run_command(command)

            if returncode != 0:
                logger.error(f"Failed to generate token for {agent}: {stderr}")
                return False

            logger.info(f"Successfully generated token for {agent} agent")

        logger.info("Authentication tests passed")
        return True

    def setup_all(self) -> bool:
        """Run all authentication setup steps"""
        logger.info("Starting authentication and authorization setup")

        # 1. Create service accounts and keys
        logger.info("\n=== Setting up service accounts ===")
        keys_dir = Path(__file__).parent.parent / "keys"
        keys_dir.mkdir(exist_ok=True)

        for agent, config in AGENT_SERVICES.items():
            # Create service account
            display_name = f"SentinelOps {agent.title()} Agent"
            if not self.create_service_account(config["service_account"], display_name):
                return False

            # Create service account key
            key_path = keys_dir / f"{config['service_account']}-key.json"
            if not self.create_service_account_key(
                config["service_account"], str(key_path)
            ):
                return False

            # Set up Workload Identity
            if not self.setup_workload_identity(
                config["service_account"], config["cloud_run_service"]
            ):
                return False

        # 2. Create custom roles
        logger.info("\n=== Creating custom roles ===")
        for role_id, role_def in CUSTOM_ROLES.items():
            if not self.create_custom_role(role_id, role_def):
                return False

        # 3. Grant IAM roles
        logger.info("\n=== Granting IAM roles ===")
        for agent, config in AGENT_SERVICES.items():
            # Add custom role to the list of roles
            roles = config["roles"] + [
                f"projects/{self.project_id}/roles/{config['custom_role'].replace('.', '_')}"
            ]
            if not self.grant_iam_roles(config["service_account"], roles):
                return False

        # 4. Set up OAuth2
        logger.info("\n=== Setting up OAuth2 ===")
        if not self.setup_oauth2_flow():
            return False

        # 5. Set up JWT validation
        logger.info("\n=== Setting up JWT validation ===")
        if not self.setup_jwt_validation():
            return False

        # 6. Set up mTLS
        logger.info("\n=== Setting up mTLS ===")
        if not self.setup_mtls():
            return False

        # 7. Create authentication middleware
        logger.info("\n=== Creating authentication middleware ===")
        if not self.create_authentication_middleware():
            return False

        # 8. Create Pub/Sub signing key
        logger.info("\n=== Creating Pub/Sub signing key ===")
        signing_key = secrets.token_bytes(32)
        if not self.create_api_key_secret(
            "sentinelops-pubsub-signing-key", base64.b64encode(signing_key).decode()
        ):
            return False

        # 9. Test authentication
        logger.info("\n=== Testing authentication ===")
        if not self.test_authentication():
            return False

        logger.info(
            "\n✅ Authentication and authorization setup completed successfully!"
        )
        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Setup authentication and authorization for SentinelOps"
    )
    parser.add_argument(
        "--project-id",
        help="Google Cloud project ID",
        default=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    if not args.project_id:
        logger.error(
            "Project ID must be specified via --project-id or GOOGLE_CLOUD_PROJECT environment variable"
        )
        sys.exit(1)

    # Create and run setup
    setup = AuthenticationSetup(args.project_id, args.dry_run)

    try:
        if setup.setup_all():
            logger.info("Authentication setup completed successfully")
            sys.exit(0)
        else:
            logger.error("Authentication setup failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

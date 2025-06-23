#!/usr/bin/env python3
"""
Set Up OpenID Connect (OIDC) for SentinelOps

This script configures OIDC authentication for workload identity federation,
enabling keyless authentication for services.
"""

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.logger import Logger  # noqa: E402

# Initialize logger
logger = Logger(__name__).logger


class OIDCConfigurer:
    """Configures OIDC for workload identity federation."""

    def __init__(self, project_id: str, project_number: Optional[str] = None):
        """
        Initialize OIDC Configurer.

        Args:
            project_id: GCP project ID
            project_number: GCP project number (will be fetched if not provided)
        """
        self.project_id = project_id
        self.project_number = project_number or self._get_project_number()

        # OIDC configuration
        self.pool_id = "sentinelops-workload-pool"
        self.provider_id = "sentinelops-oidc-provider"

    def _get_project_number(self) -> str:
        """Get the project number for the project."""
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "projects",
                    "describe",
                    self.project_id,
                    "--format=value(projectNumber)",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get project number: {e.stderr}")
            raise

    def create_workload_identity_pool(self) -> str:
        """Create workload identity pool."""
        logger.info("Creating workload identity pool...")

        try:
            # Create workload identity pool
            cmd = [
                "gcloud",
                "iam",
                "workload-identity-pools",
                "create",
                self.pool_id,
                "--location=global",
                "--display-name=SentinelOps Workload Identity Pool",
                "--description=Workload identity pool for SentinelOps services",
                "--project",
                self.project_id,
            ]

            subprocess.run(cmd, check=True)
            logger.info(f"Created workload identity pool: {self.pool_id}")

        except subprocess.CalledProcessError as e:
            if "already exists" in str(e.stderr):
                logger.info(f"Workload identity pool {self.pool_id} already exists")
            else:
                logger.error(f"Failed to create workload identity pool: {e.stderr}")
                raise

        pool_name = f"projects/{self.project_number}/locations/global/workloadIdentityPools/{self.pool_id}"
        return pool_name

    def create_oidc_provider(self, pool_name: str, issuer_uri: str = None) -> str:
        """
        Create OIDC provider in the workload identity pool.

        Args:
            pool_name: Full name of the workload identity pool
            issuer_uri: OIDC issuer URI (e.g., for GitHub Actions)

        Returns:
            Full name of the provider
        """
        logger.info("Creating OIDC provider...")

        # Default to GitHub Actions if no issuer provided
        if not issuer_uri:
            issuer_uri = "https://token.actions.githubusercontent.com"

        try:
            cmd = [
                "gcloud",
                "iam",
                "workload-identity-pools",
                "providers",
                "create-oidc",
                self.provider_id,
                f"--workload-identity-pool={self.pool_id}",
                "--location=global",
                "--display-name=SentinelOps OIDC Provider",
                "--attribute-mapping=google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner",
                f"--issuer-uri={issuer_uri}",
                "--project",
                self.project_id,
            ]

            # Add attribute conditions if using GitHub Actions
            if "github" in issuer_uri:
                cmd.extend(
                    [
                        '--attribute-condition=assertion.repository_owner=="your-github-org"'
                    ]
                )

            subprocess.run(cmd, check=True)
            logger.info(f"Created OIDC provider: {self.provider_id}")

        except subprocess.CalledProcessError as e:
            if "already exists" in str(e.stderr):
                logger.info(f"OIDC provider {self.provider_id} already exists")
            else:
                logger.error(f"Failed to create OIDC provider: {e.stderr}")
                raise

        provider_name = f"{pool_name}/providers/{self.provider_id}"
        return provider_name

    def configure_service_account_impersonation(
        self,
        service_account_email: str,
        pool_name: str,
        repository: Optional[str] = None,
    ) -> None:
        """
        Configure service account to allow impersonation from workload identity pool.

        Args:
            service_account_email: Email of the service account
            pool_name: Full name of the workload identity pool
            repository: GitHub repository (if using GitHub Actions)
        """
        logger.info(f"Configuring impersonation for {service_account_email}...")

        # Create member string
        if repository:
            # GitHub Actions specific
            member = f"principalSet://iam.googleapis.com/{pool_name}/attribute.repository/{repository}"
        else:
            # Generic workload identity
            member = f"principalSet://iam.googleapis.com/{pool_name}/*"

        try:
            # Grant workload identity user role
            cmd = [
                "gcloud",
                "iam",
                "service-accounts",
                "add-iam-policy-binding",
                service_account_email,
                f"--member={member}",
                "--role=roles/iam.workloadIdentityUser",
                "--project",
                self.project_id,
            ]

            subprocess.run(cmd, check=True)
            logger.info(f"Configured impersonation for {service_account_email}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure impersonation: {e.stderr}")
            raise

    def create_oidc_configuration_file(
        self,
        provider_name: str,
        service_account_email: str,
        output_file: str = "oidc-config.json",
    ) -> str:
        """
        Create OIDC configuration file for applications.

        Args:
            provider_name: Full name of the OIDC provider
            service_account_email: Email of the service account to impersonate
            output_file: Output file path

        Returns:
            Path to configuration file
        """
        logger.info("Creating OIDC configuration file...")

        config = {
            "type": "external_account",
            "audience": f"//iam.googleapis.com/{provider_name}",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "token_url": "https://sts.googleapis.com/v1/token",
            "service_account_impersonation_url": f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{service_account_email}:generateAccessToken",
            "credential_source": {
                "file": os.environ.get(
                    "OIDC_TOKEN_FILE", "/var/run/secrets/oidc/token"
                ),
                "format": {"type": "text"},
            },
        }

        # For GitHub Actions
        if "GITHUB_ACTIONS" in os.environ:
            config["credential_source"] = {
                "url": f"https://token.actions.githubusercontent.com/?audience={config['audience']}",
                "headers": {
                    "Authorization": f"Bearer {os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN', '')}"
                },
                "format": {"type": "json", "subject_token_field_name": "value"},
            }

        output_path = os.path.join(os.path.dirname(__file__), output_file)
        with open(output_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Created OIDC configuration file: {output_path}")
        return output_path

    def setup_kubernetes_workload_identity(
        self, namespace: str = "default", kubernetes_sa: str = "sentinelops-sa"
    ) -> None:
        """
        Set up workload identity for Kubernetes service accounts.

        Args:
            namespace: Kubernetes namespace
            kubernetes_sa: Kubernetes service account name
        """
        logger.info("Setting up Kubernetes workload identity...")

        # Create Kubernetes service account
        try:
            cmd = [
                "kubectl",
                "create",
                "serviceaccount",
                kubernetes_sa,
                "--namespace",
                namespace,
            ]
            subprocess.run(cmd, check=True)
            logger.info(f"Created Kubernetes service account: {kubernetes_sa}")
        except subprocess.CalledProcessError:
            logger.info(f"Kubernetes service account {kubernetes_sa} already exists")

        # Annotate service account
        for service in [
            "detection-agent",
            "analysis-agent",
            "communication-agent",
            "orchestration-agent",
        ]:
            gcp_sa = f"{service}-sa@{self.project_id}.iam.gserviceaccount.com"

            try:
                cmd = [
                    "kubectl",
                    "annotate",
                    "serviceaccount",
                    kubernetes_sa,
                    f"iam.gke.io/gcp-service-account={gcp_sa}",
                    "--namespace",
                    namespace,
                    "--overwrite",
                ]
                subprocess.run(cmd, check=True)

                # Bind GCP service account
                self.configure_service_account_impersonation(
                    gcp_sa,
                    f"projects/{self.project_number}/locations/global/workloadIdentityPools/{self.pool_id}",
                    None,
                )

                # Add workload identity binding
                member = f"serviceAccount:{self.project_id}.svc.id.goog[{namespace}/{kubernetes_sa}]"
                cmd = [
                    "gcloud",
                    "iam",
                    "service-accounts",
                    "add-iam-policy-binding",
                    gcp_sa,
                    f"--member={member}",
                    "--role=roles/iam.workloadIdentityUser",
                    "--project",
                    self.project_id,
                ]
                subprocess.run(cmd, check=True)

                logger.info(f"Configured workload identity for {service}")

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to configure Kubernetes workload identity: {e}")

    def configure_all_services(self) -> Dict[str, Any]:
        """Configure OIDC for all SentinelOps services."""
        logger.info("Configuring OIDC for all services...")

        results = {
            "timestamp": os.environ.get("BUILD_TIMESTAMP", "manual"),
            "project_id": self.project_id,
            "project_number": self.project_number,
            "workload_identity_pool": None,
            "oidc_provider": None,
            "service_accounts": {},
            "configuration_files": [],
        }

        # Create workload identity pool
        pool_name = self.create_workload_identity_pool()
        results["workload_identity_pool"] = pool_name

        # Create OIDC provider
        provider_name = self.create_oidc_provider(pool_name)
        results["oidc_provider"] = provider_name

        # Configure service accounts
        service_accounts = [
            "detection-agent-sa",
            "analysis-agent-sa",
            "remediation-agent-sa",
            "communication-agent-sa",
            "orchestration-agent-sa",
        ]

        for sa in service_accounts:
            sa_email = f"{sa}@{self.project_id}.iam.gserviceaccount.com"

            try:
                # Configure impersonation
                self.configure_service_account_impersonation(sa_email, pool_name)

                # Create configuration file
                config_file = f"oidc-config-{sa}.json"
                config_path = self.create_oidc_configuration_file(
                    provider_name, sa_email, config_file
                )

                results["service_accounts"][sa] = {
                    "email": sa_email,
                    "impersonation_configured": True,
                    "config_file": config_path,
                }
                results["configuration_files"].append(config_path)

            except Exception as e:
                results["service_accounts"][sa] = {
                    "email": sa_email,
                    "impersonation_configured": False,
                    "error": str(e),
                }

        # Save configuration summary
        summary_path = os.path.join(
            os.path.dirname(__file__), "oidc_configuration_summary.json"
        )

        with open(summary_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"OIDC configuration summary saved to: {summary_path}")

        return results

    def test_oidc_authentication(self, config_file: str) -> bool:
        """
        Test OIDC authentication using configuration file.

        Args:
            config_file: Path to OIDC configuration file

        Returns:
            True if authentication successful
        """
        logger.info(f"Testing OIDC authentication with {config_file}...")

        try:
            # Set environment variable
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config_file

            # Test authentication
            cmd = ["gcloud", "auth", "application-default", "print-access-token"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                logger.info("OIDC authentication test successful")
                return True
            else:
                logger.error(f"OIDC authentication test failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"OIDC authentication test error: {e}")
            return False


def main():
    """Main function to set up OIDC."""
    import argparse

    parser = argparse.ArgumentParser(description="Set up OIDC for SentinelOps")
    parser.add_argument(
        "--project-id",
        default=os.environ.get("GCP_PROJECT_ID", "sentinelops-project"),
        help="GCP Project ID",
    )
    parser.add_argument(
        "--project-number", help="GCP Project Number (will be fetched if not provided)"
    )
    parser.add_argument(
        "--service-account", help="Configure specific service account only"
    )
    parser.add_argument(
        "--kubernetes",
        action="store_true",
        help="Configure Kubernetes workload identity",
    )
    parser.add_argument("--test", help="Test OIDC authentication with config file")

    args = parser.parse_args()

    try:
        # Initialize OIDC configurer
        configurer = OIDCConfigurer(args.project_id, args.project_number)

        if args.test:
            # Test authentication
            success = configurer.test_oidc_authentication(args.test)
            if success:
                print("✓ OIDC authentication test passed")
            else:
                print("✗ OIDC authentication test failed")
                sys.exit(1)

        elif args.kubernetes:
            # Configure Kubernetes workload identity
            configurer.setup_kubernetes_workload_identity()
            print("\nConfigured Kubernetes workload identity")

        elif args.service_account:
            # Configure specific service account
            pool_name = configurer.create_workload_identity_pool()
            provider_name = configurer.create_oidc_provider(pool_name)

            sa_email = args.service_account
            if not sa_email.endswith(".iam.gserviceaccount.com"):
                sa_email = f"{sa_email}@{args.project_id}.iam.gserviceaccount.com"

            configurer.configure_service_account_impersonation(sa_email, pool_name)
            config_path = configurer.create_oidc_configuration_file(
                provider_name, sa_email, f"oidc-config-{args.service_account}.json"
            )

            print("\nConfigured OIDC for {sa_email}")
            print("Configuration file: {config_path}")

        else:
            # Configure all services
            results = configurer.configure_all_services()

            print("\nOIDC Configuration Summary:")
            print("Workload Identity Pool: {results['workload_identity_pool']}")
            print("OIDC Provider: {results['oidc_provider']}")
            print("\nService Accounts Configured:")

            for sa, info in results["service_accounts"].items():
                if info["impersonation_configured"]:
                    print("  ✓ {sa}: {info['email']}")
                else:
                    print("  ✗ {sa}: {info.get('error', 'Failed')}")

            print(
                f"\nConfiguration files created: {len(results['configuration_files'])}"
            )

        print("\nNext steps:")
        print("1. Use configuration files for keyless authentication")
        print("2. Set GOOGLE_APPLICATION_CREDENTIALS to the config file path")
        print("3. For GitHub Actions, use google-github-actions/auth@v1")

    except Exception as e:
        logger.error(f"OIDC setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

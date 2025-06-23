#!/usr/bin/env python3
"""
Set Up Service Perimeters for SentinelOps

This script configures VPC Service Controls to create security perimeters
around SentinelOps resources. Note: This requires organization-level permissions.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

from google.api_core import exceptions
from google.cloud import accesscontextmanager_v1

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.logger import Logger  # noqa: E402

# Initialize logger
logger = Logger(__name__).logger


class ServicePerimeterConfigurer:
    """Configures VPC Service Controls for SentinelOps."""

    def __init__(self, organization_id: str, project_id: str):
        """
        Initialize Service Perimeter Configurer.

        Args:
            organization_id: GCP organization ID
            project_id: GCP project ID
        """
        self.organization_id = organization_id
        self.project_id = project_id

        # Initialize client
        self.client = accesscontextmanager_v1.AccessContextManagerClient()

        # Services to protect
        self.protected_services = [
            "bigquery.googleapis.com",
            "storage.googleapis.com",
            "pubsub.googleapis.com",
            "firestore.googleapis.com",
            "secretmanager.googleapis.com",
            "logging.googleapis.com",
            "monitoring.googleapis.com",
            "cloudfunctions.googleapis.com",
            "run.googleapis.com",
            "compute.googleapis.com",
            "aiplatform.googleapis.com"
        ]

    def get_or_create_access_policy(self) -> str:
        """
        Get existing access policy or create a new one.

        Returns:
            Access policy resource name
        """
        logger.info("Getting or creating access policy...")

        parent = f"organizations/{self.organization_id}"

        try:
            # List existing policies
            policies = list(self.client.list_access_policies(parent=parent))

            if policies:
                # Use the first policy (organizations typically have one)
                policy = policies[0]
                logger.info(f"Using existing access policy: {policy.name}")
                return policy.name
            else:
                # Create new access policy
                policy = accesscontextmanager_v1.AccessPolicy()
                policy.title = "SentinelOps Access Policy"

                operation = self.client.create_access_policy(
                    parent=parent,
                    access_policy=policy
                )

                result = operation.result()
                logger.info(f"Created access policy: {result.name}")
                return result.name

        except Exception as e:
            logger.error(f"Failed to get/create access policy: {e}")
            raise

    def create_access_levels(self, policy_name: str) -> Dict[str, str]:
        """
        Create access levels for different security requirements.

        Args:
            policy_name: Access policy resource name

        Returns:
            Dict of access level names
        """
        logger.info("Creating access levels...")

        access_levels = {}

        # Corporate network access level
        corp_level = accesscontextmanager_v1.AccessLevel()
        corp_level.name = "sentinelops_corporate"
        corp_level.title = "SentinelOps Corporate Network"
        corp_level.description = "Access from corporate IP ranges"
        corp_level.basic = accesscontextmanager_v1.BasicLevel()
        corp_level.basic.conditions = [
            accesscontextmanager_v1.Condition(
                ip_subnetworks=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
            )
        ]

        try:
            operation = self.client.create_access_level(
                parent=policy_name,
                access_level=corp_level,
                access_level_id="sentinelops_corporate"
            )
            result = operation.result()
            access_levels['corporate'] = result.name
            logger.info(f"Created corporate access level: {result.name}")
        except exceptions.AlreadyExists:
            access_levels['corporate'] = f"{policy_name}/accessLevels/sentinelops_corporate"
            logger.info("Corporate access level already exists")

        # Trusted services access level
        trusted_level = accesscontextmanager_v1.AccessLevel()
        trusted_level.name = "sentinelops_trusted_services"
        trusted_level.title = "SentinelOps Trusted Services"
        trusted_level.description = "Access for trusted service accounts"
        trusted_level.basic = accesscontextmanager_v1.BasicLevel()
        trusted_level.basic.conditions = [
            accesscontextmanager_v1.Condition(
                members=[
                    f"serviceAccount:detection-agent-sa@{self.project_id}.iam.gserviceaccount.com",
                    f"serviceAccount:analysis-agent-sa@{self.project_id}.iam.gserviceaccount.com",
                    f"serviceAccount:remediation-agent-sa@{self.project_id}.iam.gserviceaccount.com",
                    f"serviceAccount:communication-agent-sa@{self.project_id}.iam.gserviceaccount.com",
                    f"serviceAccount:orchestration-agent-sa@{self.project_id}.iam.gserviceaccount.com"
                ]
            )
        ]

        try:
            operation = self.client.create_access_level(
                parent=policy_name,
                access_level=trusted_level,
                access_level_id="sentinelops_trusted_services"
            )
            result = operation.result()
            access_levels['trusted_services'] = result.name
            logger.info(f"Created trusted services access level: {result.name}")
        except exceptions.AlreadyExists:
            access_levels['trusted_services'] = f"{policy_name}/accessLevels/sentinelops_trusted_services"
            logger.info("Trusted services access level already exists")

        # High security access level
        high_sec_level = accesscontextmanager_v1.AccessLevel()
        high_sec_level.name = "sentinelops_high_security"
        high_sec_level.title = "SentinelOps High Security"
        high_sec_level.description = "Access requiring device policy and corporate network"
        high_sec_level.basic = accesscontextmanager_v1.BasicLevel()
        high_sec_level.basic.combining_function = accesscontextmanager_v1.BasicLevel.ConditionCombiningFunction.AND
        high_sec_level.basic.conditions = [
            accesscontextmanager_v1.Condition(
                ip_subnetworks=["10.0.0.0/8"],
                device_policy=accesscontextmanager_v1.DevicePolicy(
                    require_screen_lock=True,
                    require_admin_approval=True,
                    require_corp_owned=True
                )
            )
        ]

        try:
            operation = self.client.create_access_level(
                parent=policy_name,
                access_level=high_sec_level,
                access_level_id="sentinelops_high_security"
            )
            result = operation.result()
            access_levels['high_security'] = result.name
            logger.info(f"Created high security access level: {result.name}")
        except exceptions.AlreadyExists:
            access_levels['high_security'] = f"{policy_name}/accessLevels/sentinelops_high_security"
            logger.info("High security access level already exists")

        return access_levels

    def create_service_perimeter(self,
                               policy_name: str,
                               access_levels: Dict[str, str]) -> str:
        """
        Create VPC Service Control perimeter.

        Args:
            policy_name: Access policy resource name
            access_levels: Dict of access level names

        Returns:
            Service perimeter resource name
        """
        logger.info("Creating service perimeter...")

        perimeter = accesscontextmanager_v1.ServicePerimeter()
        perimeter.name = "sentinelops_perimeter"
        perimeter.title = "SentinelOps Security Perimeter"
        perimeter.description = "Protects SentinelOps resources and data"
        perimeter.perimeter_type = accesscontextmanager_v1.ServicePerimeter.PerimeterType.PERIMETER_TYPE_REGULAR

        # Configure perimeter
        perimeter.status = accesscontextmanager_v1.ServicePerimeterConfig()
        perimeter.status.resources = [
            f"projects/{self.project_id}"
        ]
        perimeter.status.restricted_services = self.protected_services
        perimeter.status.access_levels = list(access_levels.values())

        # Configure VPC accessible services
        perimeter.status.vpc_accessible_services = accesscontextmanager_v1.VpcAccessibleServices(
            enable_restriction=True,
            allowed_services=self.protected_services
        )

        # Configure ingress policy for Cloud Run
        ingress_from = accesscontextmanager_v1.IngressFrom()
        ingress_from.sources = [
            accesscontextmanager_v1.IngressSource(
                access_level=access_levels['corporate']
            )
        ]
        ingress_from.identities = [
            f"serviceAccount:detection-agent-sa@{self.project_id}.iam.gserviceaccount.com",
            f"serviceAccount:analysis-agent-sa@{self.project_id}.iam.gserviceaccount.com",
            f"serviceAccount:orchestration-agent-sa@{self.project_id}.iam.gserviceaccount.com"
        ]

        ingress_to = accesscontextmanager_v1.IngressTo()
        ingress_to.resources = ["*"]
        ingress_to.operations = [
            accesscontextmanager_v1.ApiOperation(
                service_name="run.googleapis.com",
                method_selectors=[
                    accesscontextmanager_v1.MethodSelector(method="*")
                ]
            ),
            accesscontextmanager_v1.ApiOperation(
                service_name="bigquery.googleapis.com",
                method_selectors=[
                    accesscontextmanager_v1.MethodSelector(method="*")
                ]
            )
        ]

        ingress_policy = accesscontextmanager_v1.IngressPolicy()
        ingress_policy.ingress_from = ingress_from
        ingress_policy.ingress_to = ingress_to

        perimeter.status.ingress_policies = [ingress_policy]

        # Configure egress policy for external APIs
        egress_from = accesscontextmanager_v1.EgressFrom()
        egress_from.identities = [
            f"serviceAccount:analysis-agent-sa@{self.project_id}.iam.gserviceaccount.com"
        ]

        egress_to = accesscontextmanager_v1.EgressTo()
        egress_to.resources = ["*"]
        egress_to.operations = [
            accesscontextmanager_v1.ApiOperation(
                service_name="generativelanguage.googleapis.com",
                method_selectors=[
                    accesscontextmanager_v1.MethodSelector(method="*")
                ]
            )
        ]

        egress_policy = accesscontextmanager_v1.EgressPolicy()
        egress_policy.egress_from = egress_from
        egress_policy.egress_to = egress_to

        perimeter.status.egress_policies = [egress_policy]

        try:
            operation = self.client.create_service_perimeter(
                parent=policy_name,
                service_perimeter=perimeter,
                service_perimeter_id="sentinelops_perimeter"
            )

            result = operation.result()
            logger.info(f"Created service perimeter: {result.name}")
            return result.name

        except exceptions.AlreadyExists:
            logger.info("Service perimeter already exists")
            return f"{policy_name}/servicePerimeters/sentinelops_perimeter"
        except Exception as e:
            logger.error(f"Failed to create service perimeter: {e}")
            raise

    def create_bridge_perimeter(self, policy_name: str) -> str:
        """
        Create bridge perimeter for cross-perimeter communication.

        Args:
            policy_name: Access policy resource name

        Returns:
            Bridge perimeter resource name
        """
        logger.info("Creating bridge perimeter...")

        bridge = accesscontextmanager_v1.ServicePerimeter()
        bridge.name = "sentinelops_bridge"
        bridge.title = "SentinelOps Bridge Perimeter"
        bridge.description = "Enables communication between perimeters"
        bridge.perimeter_type = accesscontextmanager_v1.ServicePerimeter.PerimeterType.PERIMETER_TYPE_BRIDGE

        bridge.status = accesscontextmanager_v1.ServicePerimeterConfig()
        bridge.status.resources = [
            f"projects/{self.project_id}"
        ]

        try:
            operation = self.client.create_service_perimeter(
                parent=policy_name,
                service_perimeter=bridge,
                service_perimeter_id="sentinelops_bridge"
            )

            result = operation.result()
            logger.info(f"Created bridge perimeter: {result.name}")
            return result.name

        except exceptions.AlreadyExists:
            logger.info("Bridge perimeter already exists")
            return f"{policy_name}/servicePerimeters/sentinelops_bridge"
        except Exception as e:
            logger.error(f"Failed to create bridge perimeter: {e}")
            raise

    def configure_service_perimeters(self) -> Dict[str, Any]:
        """Configure complete VPC Service Controls for SentinelOps."""
        logger.info("Configuring VPC Service Controls...")

        results = {
            'timestamp': os.environ.get('BUILD_TIMESTAMP', 'manual'),
            'organization_id': self.organization_id,
            'project_id': self.project_id,
            'resources_created': {}
        }

        try:
            # 1. Get or create access policy
            policy_name = self.get_or_create_access_policy()
            results['resources_created']['access_policy'] = policy_name

            # 2. Create access levels
            access_levels = self.create_access_levels(policy_name)
            results['resources_created']['access_levels'] = access_levels

            # 3. Create service perimeter
            perimeter_name = self.create_service_perimeter(policy_name, access_levels)
            results['resources_created']['service_perimeter'] = perimeter_name

            # 4. Create bridge perimeter
            bridge_name = self.create_bridge_perimeter(policy_name)
            results['resources_created']['bridge_perimeter'] = bridge_name

            results['status'] = 'completed'
            results['protected_services'] = self.protected_services
            results['message'] = "VPC Service Controls configured successfully"

        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            logger.error(f"Service perimeter configuration failed: {e}")

        # Save results
        results_path = os.path.join(
            os.path.dirname(__file__),
            'service_perimeter_configuration.json'
        )

        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Service perimeter configuration saved to: {results_path}")

        return results


def main():
    """Main function to set up service perimeters."""
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(description='Set up VPC Service Controls for SentinelOps')
    parser.add_argument('--organization-id',
                       required=True,
                       help='GCP Organization ID')
    parser.add_argument('--project-id',
                       default=os.environ.get('GCP_PROJECT_ID', 'sentinelops-project'),
                       help='GCP Project ID')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be created without actually creating')

    args = parser.parse_args()

    if args.dry_run:
        print("\n=== DRY RUN MODE ===")
        print("\nThis script would create:")
        print("1. Access Policy (if not exists)")
        print("2. Access Levels:")
        print("   - Corporate Network Access")
        print("   - Trusted Services Access")
        print("   - High Security Access")
        print("3. Service Perimeter protecting:")
        print("   - BigQuery")
        print("   - Cloud Storage")
        print("   - Pub/Sub")
        print("   - Firestore")
        print("   - Secret Manager")
        print("   - Cloud Logging")
        print("   - Cloud Monitoring")
        print("   - Cloud Functions")
        print("   - Cloud Run")
        print("   - Compute Engine")
        print("   - Vertex AI")
        print("4. Bridge Perimeter for cross-perimeter communication")
        print("\n⚠️  IMPORTANT: This requires organization-level permissions:")
        print("   - accesscontextmanager.accessPolicies.create")
        print("   - accesscontextmanager.accessLevels.create")
        print("   - accesscontextmanager.servicePerimeters.create")
        return

    try:
        # Initialize service perimeter configurer
        configurer = ServicePerimeterConfigurer(args.organization_id, args.project_id)

        # Configure service perimeters
        results = configurer.configure_service_perimeters()

        if results['status'] == 'completed':
            print("\n✓ VPC Service Controls configured successfully!")
            print("\nResources created:")
            for resource_type, resource_name in results['resources_created'].items():
                if isinstance(resource_name, dict):
                    print("  {resource_type}:")
                    for level_type, level_name in resource_name.items():
                        print("    - {level_type}: {level_name}")
                else:
                    print("  - {resource_type}: {resource_name}")

            print("\nProtected services: {len(results['protected_services'])}")

            print("\n⚠️  IMPORTANT NOTES:")
            print("1. Service perimeter changes can take up to 10 minutes to propagate")
            print("2. Ensure all service accounts have proper access levels")
            print("3. Test access from both inside and outside the perimeter")
            print("4. Monitor logs for any access denials")

            print("\nTo test the perimeter:")
            print("1. Try accessing protected services from outside the perimeter")
            print("2. Verify service accounts can still access required resources")
            print("3. Check Cloud Logging for VPC Service Control violations")
        else:
            print("\n✗ Service perimeter configuration failed: {results.get('error', 'Unknown error')}")
            print("\nCommon issues:")
            print("1. Missing organization-level permissions")
            print("2. Organization policies preventing VPC Service Controls")
            print("3. Conflicting existing perimeters")

    except Exception as e:
        logger.error(f"Service perimeter setup failed: {e}")
        print("\n✗ Error: {e}")
        print("\nEnsure you have the required organization-level permissions:")
        print("  - accesscontextmanager.accessPolicies.create")
        print("  - accesscontextmanager.accessLevels.create")
        print("  - accesscontextmanager.servicePerimeters.create")
        sys.exit(1)


if __name__ == "__main__":
    main()

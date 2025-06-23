#!/usr/bin/env python3
"""
Configure Load Balancing for SentinelOps

This script sets up load balancing for SentinelOps services using Google Cloud
Load Balancing with Cloud Run services as backends.
"""

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from google.api_core import exceptions
from google.cloud import compute_v1

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.logger import Logger  # noqa: E402

# Initialize logger
logger = Logger(__name__).logger


class LoadBalancerConfigurer:
    """Configures load balancing for SentinelOps services."""

    def __init__(self, project_id: str, region: str = "us-central1"):
        """
        Initialize Load Balancer Configurer.

        Args:
            project_id: GCP project ID
            region: Default region for regional resources
        """
        self.project_id = project_id
        self.region = region

        # Initialize clients
        self.backend_services_client = compute_v1.BackendServicesClient()
        self.url_maps_client = compute_v1.UrlMapsClient()
        self.target_proxies_client = compute_v1.TargetHttpsProxiesClient()
        self.forwarding_rules_client = compute_v1.GlobalForwardingRulesClient()
        self.ssl_certificates_client = compute_v1.SslCertificatesClient()
        self.health_checks_client = compute_v1.HealthChecksClient()
        self.network_endpoint_groups_client = compute_v1.NetworkEndpointGroupsClient()

    def create_health_check(self, name: str, port: int = 443) -> str:
        """
        Create a health check for backend services.

        Args:
            name: Name of the health check
            port: Port to check (default: 443)

        Returns:
            Health check resource name
        """
        logger.info(f"Creating health check: {name}...")

        health_check = compute_v1.HealthCheck()
        health_check.name = name
        health_check.type_ = "HTTPS"
        health_check.https_health_check = compute_v1.HTTPSHealthCheck()
        health_check.https_health_check.port = port
        health_check.https_health_check.request_path = "/health"
        health_check.check_interval_sec = 10
        health_check.timeout_sec = 5
        health_check.healthy_threshold = 2
        health_check.unhealthy_threshold = 3

        try:
            operation = self.health_checks_client.insert(
                project=self.project_id,
                health_check_resource=health_check
            )

            # Wait for operation to complete
            self._wait_for_operation(operation)

            logger.info(f"Created health check: {name}")
            return f"projects/{self.project_id}/global/healthChecks/{name}"

        except exceptions.Conflict:
            logger.info(f"Health check {name} already exists")
            return f"projects/{self.project_id}/global/healthChecks/{name}"
        except Exception as e:
            logger.error(f"Failed to create health check: {e}")
            raise

    def create_backend_service(self,
                             name: str,
                             health_check: str,
                             service_name: str) -> str:
        """
        Create a backend service for a Cloud Run service.

        Args:
            name: Name of the backend service
            health_check: Health check resource name
            service_name: Cloud Run service name

        Returns:
            Backend service resource name
        """
        logger.info(f"Creating backend service: {name}...")

        backend_service = compute_v1.BackendService()
        backend_service.name = name
        backend_service.protocol = "HTTPS"
        backend_service.port_name = "https"
        backend_service.health_checks = [health_check]
        backend_service.load_balancing_scheme = "EXTERNAL_MANAGED"
        backend_service.timeout_sec = 30

        # Configure Cloud Run backend
        backend_service.custom_request_headers = [
            f"X-Cloud-Run-Service:{service_name}"
        ]

        # Enable Cloud CDN for better performance
        backend_service.enable_cdn = True
        backend_service.cdn_policy = compute_v1.BackendServiceCdnPolicy()
        backend_service.cdn_policy.cache_mode = "USE_ORIGIN_HEADERS"
        backend_service.cdn_policy.default_ttl = 3600
        backend_service.cdn_policy.max_ttl = 86400

        # Configure logging
        backend_service.log_config = compute_v1.BackendServiceLogConfig()
        backend_service.log_config.enable = True
        backend_service.log_config.sample_rate = 1.0

        try:
            operation = self.backend_services_client.insert(
                project=self.project_id,
                backend_service_resource=backend_service
            )

            # Wait for operation to complete
            self._wait_for_operation(operation)

            logger.info(f"Created backend service: {name}")
            return f"projects/{self.project_id}/global/backendServices/{name}"

        except exceptions.Conflict:
            logger.info(f"Backend service {name} already exists")
            return f"projects/{self.project_id}/global/backendServices/{name}"
        except Exception as e:
            logger.error(f"Failed to create backend service: {e}")
            raise

    def create_url_map(self, name: str, backend_services: Dict[str, str]) -> str:
        """
        Create URL map for routing traffic to backend services.

        Args:
            name: Name of the URL map
            backend_services: Map of path to backend service

        Returns:
            URL map resource name
        """
        logger.info(f"Creating URL map: {name}...")

        url_map = compute_v1.UrlMap()
        url_map.name = name

        # Set default service
        default_service = list(backend_services.values())[0]
        url_map.default_service = default_service

        # Create host rules
        host_rule = compute_v1.HostRule()
        host_rule.hosts = [f"sentinelops.{self.project_id}.com", f"*.sentinelops.{self.project_id}.com"]
        host_rule.path_matcher = "sentinelops-paths"
        url_map.host_rules = [host_rule]

        # Create path matcher
        path_matcher = compute_v1.PathMatcher()
        path_matcher.name = "sentinelops-paths"
        path_matcher.default_service = default_service

        # Add path rules
        path_rules = []
        for path, backend in backend_services.items():
            if path != "/":
                path_rule = compute_v1.PathRule()
                path_rule.paths = [f"{path}/*"]
                path_rule.service = backend
                path_rules.append(path_rule)

        path_matcher.path_rules = path_rules
        url_map.path_matchers = [path_matcher]

        try:
            operation = self.url_maps_client.insert(
                project=self.project_id,
                url_map_resource=url_map
            )

            # Wait for operation to complete
            self._wait_for_operation(operation)

            logger.info(f"Created URL map: {name}")
            return f"projects/{self.project_id}/global/urlMaps/{name}"

        except exceptions.Conflict:
            logger.info(f"URL map {name} already exists")
            return f"projects/{self.project_id}/global/urlMaps/{name}"
        except Exception as e:
            logger.error(f"Failed to create URL map: {e}")
            raise

    def create_ssl_certificate(self, name: str, domains: List[str]) -> str:
        """
        Create managed SSL certificate.

        Args:
            name: Name of the SSL certificate
            domains: List of domains to secure

        Returns:
            SSL certificate resource name
        """
        logger.info(f"Creating SSL certificate: {name}...")

        ssl_cert = compute_v1.SslCertificate()
        ssl_cert.name = name
        ssl_cert.type_ = "MANAGED"
        ssl_cert.managed = compute_v1.SslCertificateManagedSslCertificate()
        ssl_cert.managed.domains = domains

        try:
            operation = self.ssl_certificates_client.insert(
                project=self.project_id,
                ssl_certificate_resource=ssl_cert
            )

            # Wait for operation to complete
            self._wait_for_operation(operation)

            logger.info(f"Created SSL certificate: {name}")
            return f"projects/{self.project_id}/global/sslCertificates/{name}"

        except exceptions.Conflict:
            logger.info(f"SSL certificate {name} already exists")
            return f"projects/{self.project_id}/global/sslCertificates/{name}"
        except Exception as e:
            logger.error(f"Failed to create SSL certificate: {e}")
            raise

    def create_target_proxy(self,
                           name: str,
                           url_map: str,
                           ssl_certificate: str) -> str:
        """
        Create target HTTPS proxy.

        Args:
            name: Name of the target proxy
            url_map: URL map resource name
            ssl_certificate: SSL certificate resource name

        Returns:
            Target proxy resource name
        """
        logger.info(f"Creating target HTTPS proxy: {name}...")

        target_proxy = compute_v1.TargetHttpsProxy()
        target_proxy.name = name
        target_proxy.url_map = url_map
        target_proxy.ssl_certificates = [ssl_certificate]

        try:
            operation = self.target_proxies_client.insert(
                project=self.project_id,
                target_https_proxy_resource=target_proxy
            )

            # Wait for operation to complete
            self._wait_for_operation(operation)

            logger.info(f"Created target HTTPS proxy: {name}")
            return f"projects/{self.project_id}/global/targetHttpsProxies/{name}"

        except exceptions.Conflict:
            logger.info(f"Target HTTPS proxy {name} already exists")
            return f"projects/{self.project_id}/global/targetHttpsProxies/{name}"
        except Exception as e:
            logger.error(f"Failed to create target HTTPS proxy: {e}")
            raise

    def create_forwarding_rule(self,
                              name: str,
                              target_proxy: str,
                              ip_address: Optional[str] = None) -> str:
        """
        Create global forwarding rule.

        Args:
            name: Name of the forwarding rule
            target_proxy: Target proxy resource name
            ip_address: Static IP address (optional)

        Returns:
            Forwarding rule resource name
        """
        logger.info(f"Creating forwarding rule: {name}...")

        forwarding_rule = compute_v1.ForwardingRule()
        forwarding_rule.name = name
        forwarding_rule.target = target_proxy
        forwarding_rule.port_range = "443"
        forwarding_rule.ip_protocol = "TCP"
        forwarding_rule.load_balancing_scheme = "EXTERNAL_MANAGED"
        forwarding_rule.network_tier = "PREMIUM"

        if ip_address:
            forwarding_rule.ip_address = ip_address

        try:
            operation = self.forwarding_rules_client.insert(
                project=self.project_id,
                forwarding_rule_resource=forwarding_rule
            )

            # Wait for operation to complete
            self._wait_for_operation(operation)

            logger.info(f"Created forwarding rule: {name}")
            return f"projects/{self.project_id}/global/forwardingRules/{name}"

        except exceptions.Conflict:
            logger.info(f"Forwarding rule {name} already exists")
            return f"projects/{self.project_id}/global/forwardingRules/{name}"
        except Exception as e:
            logger.error(f"Failed to create forwarding rule: {e}")
            raise

    def create_cloud_run_neg(self,
                            name: str,
                            service_name: str,
                            region: str) -> str:
        """
        Create Network Endpoint Group for Cloud Run service.

        Args:
            name: Name of the NEG
            service_name: Cloud Run service name
            region: Region where service is deployed

        Returns:
            NEG resource name
        """
        logger.info(f"Creating Cloud Run NEG: {name}...")

        neg = compute_v1.NetworkEndpointGroup()
        neg.name = name
        neg.network_endpoint_type = "SERVERLESS"
        neg.cloud_run = compute_v1.NetworkEndpointGroupCloudRun()
        neg.cloud_run.service = service_name

        try:
            operation = self.network_endpoint_groups_client.insert(
                project=self.project_id,
                zone=f"{region}-a",  # Cloud Run NEGs use zone format
                network_endpoint_group_resource=neg
            )

            # Wait for operation to complete
            self._wait_for_operation(operation)

            logger.info(f"Created Cloud Run NEG: {name}")
            return f"projects/{self.project_id}/zones/{region}-a/networkEndpointGroups/{name}"

        except exceptions.Conflict:
            logger.info(f"Cloud Run NEG {name} already exists")
            return f"projects/{self.project_id}/zones/{region}-a/networkEndpointGroups/{name}"
        except Exception as e:
            logger.error(f"Failed to create Cloud Run NEG: {e}")
            raise

    def _wait_for_operation(self, operation: Any, timeout: int = 300) -> None:
        """Wait for a compute operation to complete."""
        start_time = time.time()

        while not operation.done():
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Operation timed out after {timeout} seconds")

            time.sleep(5)
            # Note: In production, you would refresh the operation status

        if operation.error:
            raise Exception(f"Operation failed: {operation.error}")

    def configure_load_balancing(self) -> Dict[str, Any]:
        """Configure complete load balancing setup for SentinelOps."""
        logger.info("Configuring load balancing for SentinelOps...")

        results = {
            'timestamp': os.environ.get('BUILD_TIMESTAMP', 'manual'),
            'project_id': self.project_id,
            'resources_created': {}
        }

        # Define services
        services = {
            'detection-agent': '/api/detection',
            'analysis-agent': '/api/analysis',
            'communication-agent': '/api/communication',
            'orchestration-agent': '/api/orchestration'
        }

        try:
            # 1. Create health check
            health_check = self.create_health_check("sentinelops-health-check")
            results['resources_created']['health_check'] = health_check

            # 2. Create backend services for each Cloud Run service
            backend_services = {}
            for service_name, path in services.items():
                backend_name = f"sentinelops-backend-{service_name}"
                backend_service = self.create_backend_service(
                    backend_name,
                    health_check,
                    service_name
                )
                backend_services[path] = backend_service
                results['resources_created'][f'backend_{service_name}'] = backend_service

            # 3. Create URL map
            url_map = self.create_url_map("sentinelops-url-map", backend_services)
            results['resources_created']['url_map'] = url_map

            # 4. Create SSL certificate
            domains = [
                f"sentinelops.{self.project_id}.com",
                f"*.sentinelops.{self.project_id}.com"
            ]
            ssl_cert = self.create_ssl_certificate("sentinelops-ssl-cert", domains)
            results['resources_created']['ssl_certificate'] = ssl_cert

            # 5. Create target HTTPS proxy
            target_proxy = self.create_target_proxy(
                "sentinelops-https-proxy",
                url_map,
                ssl_cert
            )
            results['resources_created']['target_proxy'] = target_proxy

            # 6. Create forwarding rule
            forwarding_rule = self.create_forwarding_rule(
                "sentinelops-https-rule",
                target_proxy
            )
            results['resources_created']['forwarding_rule'] = forwarding_rule

            # Get the assigned IP address
            rule = self.forwarding_rules_client.get(
                project=self.project_id,
                forwarding_rule="sentinelops-https-rule"
            )
            results['load_balancer_ip'] = rule.ip_address

            # Success
            results['status'] = 'completed'
            results['message'] = f"Load balancer configured successfully at IP: {rule.ip_address}"

        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            logger.error(f"Load balancing configuration failed: {e}")

        # Save results
        results_path = os.path.join(
            os.path.dirname(__file__),
            'load_balancing_configuration.json'
        )

        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Load balancing configuration saved to: {results_path}")

        return results


def main():
    """Main function to configure load balancing."""
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(description='Configure load balancing for SentinelOps')
    parser.add_argument('--project-id',
                       default=os.environ.get('GCP_PROJECT_ID', 'sentinelops-project'),
                       help='GCP Project ID')
    parser.add_argument('--region',
                       default='us-central1',
                       help='Region for regional resources')
    parser.add_argument('--health-check-only',
                       action='store_true',
                       help='Create only health check')
    parser.add_argument('--backend-service',
                       help='Create backend service for specific Cloud Run service')

    args = parser.parse_args()

    try:
        # Initialize load balancer configurer
        configurer = LoadBalancerConfigurer(args.project_id, args.region)

        if args.health_check_only:
            # Create only health check
            health_check = configurer.create_health_check("sentinelops-health-check")
            print("Created health check: {health_check}")

        elif args.backend_service:
            # Create backend service for specific service
            health_check = configurer.create_health_check("sentinelops-health-check")
            backend_service = configurer.create_backend_service(
                f"sentinelops-backend-{args.backend_service}",
                health_check,
                args.backend_service
            )
            print("Created backend service: {backend_service}")

        else:
            # Configure complete load balancing
            results = configurer.configure_load_balancing()

            if results['status'] == 'completed':
                print("\n✓ Load balancing configured successfully!")
                print("\nLoad Balancer IP: {results.get('load_balancer_ip', 'Pending')}")
                print("\nResources created:")
                for resource_type, resource_name in results['resources_created'].items():
                    print("  - {resource_type}: {resource_name}")

                print("\nNext steps:")
                print("1. Update DNS records to point to IP: {results.get('load_balancer_ip', 'Pending')}")
                print("2. Wait for SSL certificate provisioning (may take up to 60 minutes)")
                print("3. Test endpoints:")
                for service in ['detection', 'analysis', 'communication', 'orchestration']:
                    print("   https://sentinelops.{args.project_id}.com/api/{service}/health")
            else:
                print("\n✗ Load balancing configuration failed: {results.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Load balancing configuration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

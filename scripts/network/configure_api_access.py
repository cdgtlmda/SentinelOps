#!/usr/bin/env python3
"""
Configure API Access for SentinelOps

This script configures API access controls including API Gateway setup,
API keys, quotas, and rate limiting for SentinelOps services.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

import yaml
from google.api_core import exceptions
from google.cloud import api_keys_v1, apigateway_v1, serviceusage_v1

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.logger import Logger  # noqa: E402

# Initialize logger
logger = Logger(__name__).logger


class APIAccessConfigurer:
    """Configures API access controls for SentinelOps."""

    def __init__(self, project_id: str):
        """
        Initialize API Access Configurer.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id

        # Initialize clients
        self.api_gateway_client = apigateway_v1.ApiGatewayServiceClient()
        self.api_config_client = apigateway_v1.ApiConfigServiceClient()
        self.gateway_client = apigateway_v1.GatewayServiceClient()
        self.service_usage_client = serviceusage_v1.ServiceUsageClient()
        self.api_keys_client = api_keys_v1.ApiKeysClient()

    def enable_required_apis(self) -> List[str]:
        """Enable required APIs for API Gateway."""
        logger.info("Enabling required APIs...")

        required_apis = [
            "apigateway.googleapis.com",
            "servicemanagement.googleapis.com",
            "servicecontrol.googleapis.com",
            "apikeys.googleapis.com"
        ]

        enabled_apis = []

        for api in required_apis:
            try:
                service_name = f"projects/{self.project_id}/services/{api}"
                operation = self.service_usage_client.enable_service(name=service_name)

                logger.info(f"Enabled API: {api}")
                enabled_apis.append(api)

            except exceptions.FailedPrecondition:
                logger.info(f"API already enabled: {api}")
                enabled_apis.append(api)
            except Exception as e:
                logger.error(f"Failed to enable API {api}: {e}")

        return enabled_apis

    def create_api_spec(self) -> str:
        """
        Create OpenAPI specification for SentinelOps API.

        Returns:
            Path to the created spec file
        """
        logger.info("Creating API specification...")

        api_spec = {
            "swagger": "2.0",
            "info": {
                "title": "SentinelOps API",
                "description": "Security monitoring and response system API",
                "version": "1.0.0"
            },
            "host": f"sentinelops-api.{self.project_id}.apigateway.cloud.goog",
            "schemes": ["https"],
            "produces": ["application/json"],
            "x-google-backend": {
                "address": f"https://sentinelops.{self.project_id}.com"
            },
            "x-google-management": {
                "metrics": [
                    {
                        "name": "request-count",
                        "displayName": "Request Count",
                        "valueType": "INT64",
                        "metricKind": "DELTA"
                    }
                ],
                "quota": {
                    "limits": [
                        {
                            "name": "request-limit",
                            "metric": "request-count",
                            "unit": "1/min/{project}",
                            "values": {
                                "STANDARD": 100,
                                "HIGH": 1000,
                                "UNLIMITED": 10000
                            }
                        }
                    ]
                }
            },
            "security": [
                {
                    "api_key": []
                }
            ],
            "securityDefinitions": {
                "api_key": {
                    "type": "apiKey",
                    "name": "x-api-key",
                    "in": "header"
                }
            },
            "paths": {
                "/api/detection/analyze": {
                    "post": {
                        "summary": "Analyze security logs",
                        "operationId": "analyzeSecurityLogs",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "log_type": {"type": "string"},
                                        "time_range": {
                                            "type": "object",
                                            "properties": {
                                                "start": {"type": "string"},
                                                "end": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Analysis results",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "incidents": {"type": "array"},
                                        "summary": {"type": "object"}
                                    }
                                }
                            }
                        },
                        "x-google-backend": {
                            "address": f"https://detection-agent-{self.project_id}.run.app",
                            "path_translation": "APPEND_PATH_TO_ADDRESS"
                        }
                    }
                },
                "/api/incidents": {
                    "get": {
                        "summary": "List security incidents",
                        "operationId": "listIncidents",
                        "parameters": [
                            {
                                "name": "status",
                                "in": "query",
                                "type": "string",
                                "enum": ["open", "investigating", "resolved"]
                            },
                            {
                                "name": "severity",
                                "in": "query",
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"]
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of incidents",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "incidents": {"type": "array"},
                                        "total": {"type": "integer"}
                                    }
                                }
                            }
                        },
                        "x-google-backend": {
                            "address": f"https://orchestration-agent-{self.project_id}.run.app",
                            "path_translation": "APPEND_PATH_TO_ADDRESS"
                        }
                    }
                },
                "/api/remediation/execute": {
                    "post": {
                        "summary": "Execute remediation action",
                        "operationId": "executeRemediation",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "incident_id": {"type": "string"},
                                        "action": {"type": "string"},
                                        "parameters": {"type": "object"}
                                    },
                                    "required": ["incident_id", "action"]
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Remediation result",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "result": {"type": "object"}
                                    }
                                }
                            }
                        },
                        "x-google-backend": {
                            "address": f"https://orchestration-agent-{self.project_id}.run.app",
                            "path_translation": "APPEND_PATH_TO_ADDRESS"
                        },
                        "x-google-quota": {
                            "metricCosts": {
                                "request-count": 10
                            }
                        }
                    }
                },
                "/api/health": {
                    "get": {
                        "summary": "Health check endpoint",
                        "operationId": "healthCheck",
                        "security": [],
                        "responses": {
                            "200": {
                                "description": "Service health status",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "services": {"type": "object"}
                                    }
                                }
                            }
                        },
                        "x-google-backend": {
                            "address": f"https://orchestration-agent-{self.project_id}.run.app",
                            "path_translation": "APPEND_PATH_TO_ADDRESS"
                        }
                    }
                }
            }
        }

        # Save spec to file
        spec_path = os.path.join(
            os.path.dirname(__file__),
            'sentinelops-api-spec.yaml'
        )

        with open(spec_path, 'w') as f:
            yaml.dump(api_spec, f, default_flow_style=False)

        logger.info(f"API specification saved to: {spec_path}")
        return spec_path

    def create_api(self, api_id: str = "sentinelops-api") -> str:
        """
        Create API in API Gateway.

        Args:
            api_id: ID for the API

        Returns:
            API resource name
        """
        logger.info(f"Creating API: {api_id}...")

        api = apigateway_v1.Api()
        api.display_name = "SentinelOps API"
        api.managed_service = f"{api_id}.apigateway.{self.project_id}.cloud.goog"

        parent = f"projects/{self.project_id}/locations/global"

        try:
            operation = self.api_gateway_client.create_api(
                parent=parent,
                api_id=api_id,
                api=api
            )

            # Wait for operation to complete
            response = operation.result()

            logger.info(f"Created API: {response.name}")
            return response.name

        except exceptions.AlreadyExists:
            logger.info(f"API {api_id} already exists")
            return f"{parent}/apis/{api_id}"
        except Exception as e:
            logger.error(f"Failed to create API: {e}")
            raise

    def create_api_config(self,
                         api_name: str,
                         spec_path: str,
                         config_id: str = "v1") -> str:
        """
        Create API configuration.

        Args:
            api_name: Name of the API resource
            spec_path: Path to OpenAPI spec file
            config_id: ID for the configuration

        Returns:
            API config resource name
        """
        logger.info(f"Creating API configuration: {config_id}...")

        # Read spec file
        with open(spec_path, 'r') as f:
            spec_content = f.read()

        config = apigateway_v1.ApiConfig()
        config.display_name = f"SentinelOps API Config {config_id}"
        config.openapi_documents = [
            apigateway_v1.ApiConfig.OpenApiDocument(
                document=apigateway_v1.ApiConfig.File(
                    path="openapi.yaml",
                    contents=spec_content.encode()
                )
            )
        ]

        try:
            operation = self.api_config_client.create_api_config(
                parent=api_name,
                api_config_id=config_id,
                api_config=config
            )

            # Wait for operation to complete
            response = operation.result()

            logger.info(f"Created API configuration: {response.name}")
            return response.name

        except exceptions.AlreadyExists:
            logger.info(f"API configuration {config_id} already exists")
            return f"{api_name}/configs/{config_id}"
        except Exception as e:
            logger.error(f"Failed to create API configuration: {e}")
            raise

    def create_gateway(self,
                      api_config: str,
                      gateway_id: str = "sentinelops-gateway") -> str:
        """
        Create API Gateway.

        Args:
            api_config: API configuration resource name
            gateway_id: ID for the gateway

        Returns:
            Gateway resource name
        """
        logger.info(f"Creating gateway: {gateway_id}...")

        gateway = apigateway_v1.Gateway()
        gateway.api_config = api_config
        gateway.display_name = "SentinelOps API Gateway"

        parent = f"projects/{self.project_id}/locations/us-central1"

        try:
            operation = self.gateway_client.create_gateway(
                parent=parent,
                gateway_id=gateway_id,
                gateway=gateway
            )

            # Wait for operation to complete
            response = operation.result()

            logger.info(f"Created gateway: {response.name}")
            return response.name

        except exceptions.AlreadyExists:
            logger.info(f"Gateway {gateway_id} already exists")
            return f"{parent}/gateways/{gateway_id}"
        except Exception as e:
            logger.error(f"Failed to create gateway: {e}")
            raise

    def create_api_key(self,
                      name: str,
                      restrictions: Optional[Dict[str, Any]] = None) -> str:
        """
        Create API key with restrictions.

        Args:
            name: Name for the API key
            restrictions: API key restrictions

        Returns:
            API key string
        """
        logger.info(f"Creating API key: {name}...")

        key = api_keys_v1.Key()
        key.display_name = name

        # Set restrictions
        if restrictions:
            key.restrictions = api_keys_v1.Restrictions()

            # API restrictions
            if 'apis' in restrictions:
                key.restrictions.api_targets = [
                    api_keys_v1.ApiTarget(service=api)
                    for api in restrictions['apis']
                ]

            # IP restrictions
            if 'allowed_ips' in restrictions:
                key.restrictions.server_key_restrictions = api_keys_v1.ServerKeyRestrictions(
                    allowed_ips=restrictions['allowed_ips']
                )

        parent = f"projects/{self.project_id}/locations/global"

        try:
            operation = self.api_keys_client.create_key(
                parent=parent,
                key=key,
                key_id=name.lower().replace(' ', '-')
            )

            # Wait for operation to complete
            response = operation.result()

            # Get the key string
            key_string = response.key_string

            logger.info(f"Created API key: {response.name}")
            return key_string

        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise

    def configure_api_access(self) -> Dict[str, Any]:
        """Configure complete API access for SentinelOps."""
        logger.info("Configuring API access for SentinelOps...")

        results = {
            'timestamp': os.environ.get('BUILD_TIMESTAMP', 'manual'),
            'project_id': self.project_id,
            'resources_created': {},
            'api_keys': {}
        }

        try:
            # 1. Enable required APIs
            enabled_apis = self.enable_required_apis()
            results['enabled_apis'] = enabled_apis

            # 2. Create API specification
            spec_path = self.create_api_spec()
            results['api_spec'] = spec_path

            # 3. Create API
            api_name = self.create_api()
            results['resources_created']['api'] = api_name

            # 4. Create API configuration
            config_name = self.create_api_config(api_name, spec_path)
            results['resources_created']['api_config'] = config_name

            # 5. Create Gateway
            gateway_name = self.create_gateway(config_name)
            results['resources_created']['gateway'] = gateway_name

            # Get gateway URL
            gateway = self.gateway_client.get_gateway(name=gateway_name)
            results['gateway_url'] = f"https://{gateway.default_hostname}"

            # 6. Create API keys with different access levels

            # Read-only key
            read_key = self.create_api_key(
                "SentinelOps Read Key",
                {
                    'apis': [f"sentinelops-api.apigateway.{self.project_id}.cloud.goog"]
                }
            )
            results['api_keys']['read_only'] = {
                'key': read_key[:8] + "..." + read_key[-4:],  # Masked for security
                'full_key_saved_to': 'api_keys.json'
            }

            # Admin key
            admin_key = self.create_api_key(
                "SentinelOps Admin Key",
                {
                    'apis': [f"sentinelops-api.apigateway.{self.project_id}.cloud.goog"],
                    'allowed_ips': ['0.0.0.0/0']  # Allow all IPs for now
                }
            )
            results['api_keys']['admin'] = {
                'key': admin_key[:8] + "..." + admin_key[-4:],  # Masked for security
                'full_key_saved_to': 'api_keys.json'
            }

            # Save full API keys securely
            api_keys_path = os.path.join(
                os.path.dirname(__file__),
                'api_keys.json'
            )

            with open(api_keys_path, 'w') as f:
                json.dump({
                    'read_only': read_key,
                    'admin': admin_key,
                    'gateway_url': results['gateway_url'],
                    'warning': 'Keep these keys secure! Do not commit to version control.'
                }, f, indent=2)

            os.chmod(api_keys_path, 0o600)  # Restrict file permissions

            results['status'] = 'completed'
            results['message'] = f"API Gateway configured at: {results['gateway_url']}"

        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            logger.error(f"API access configuration failed: {e}")

        # Save results (without sensitive data)
        results_path = os.path.join(
            os.path.dirname(__file__),
            'api_access_configuration.json'
        )

        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"API access configuration saved to: {results_path}")

        return results


def main():
    """Main function to configure API access."""
    import argparse  # noqa: E402

    parser = argparse.ArgumentParser(description='Configure API access for SentinelOps')
    parser.add_argument('--project-id',
                       default=os.environ.get('GCP_PROJECT_ID', 'sentinelops-project'),
                       help='GCP Project ID')
    parser.add_argument('--create-spec-only',
                       action='store_true',
                       help='Create only API specification')
    parser.add_argument('--create-key',
                       help='Create API key with specified name')

    args = parser.parse_args()

    try:
        # Initialize API access configurer
        configurer = APIAccessConfigurer(args.project_id)

        if args.create_spec_only:
            # Create only API specification
            spec_path = configurer.create_api_spec()
            print("Created API specification: {spec_path}")

        elif args.create_key:
            # Create API key
            api_key = configurer.create_api_key(args.create_key)
            print("\nCreated API key: {args.create_key}")
            print("Key: {api_key[:8]}...{api_key[-4:]}")
            print("\nFull key saved to api_keys.json")
            print("⚠️  Keep this key secure!")

        else:
            # Configure complete API access
            results = configurer.configure_api_access()

            if results['status'] == 'completed':
                print("\n✓ API access configured successfully!")
                print("\nGateway URL: {results['gateway_url']}")
                print("\nResources created:")
                for resource_type, resource_name in results['resources_created'].items():
                    print("  - {resource_type}: {resource_name}")

                print("\nAPI Keys created:")
                for key_type, key_info in results['api_keys'].items():
                    print("  - {key_type}: {key_info['key']}")

                print("\n⚠️  Full API keys saved to: api_keys.json")
                print("Keep this file secure and do not commit to version control!")

                print("\nExample API calls:")
                print("curl -H 'x-api-key: YOUR_API_KEY' {results['gateway_url']}/api/health")
                print("curl -H 'x-api-key: YOUR_API_KEY' {results['gateway_url']}/api/incidents")
            else:
                print("\n✗ API access configuration failed: {results.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"API access configuration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

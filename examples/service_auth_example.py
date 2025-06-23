#!/usr/bin/env python3
"""
Example: Service-to-Service Authentication using OIDC
"""

import asyncio
import os
from typing import Optional

import aiohttp
import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials
from google.oauth2 import service_account


class ServiceAuthClient:
    """Client for service-to-service authentication"""

    def __init__(
        self, target_audience: str, service_account_email: Optional[str] = None
    ):
        self.target_audience = target_audience
        self.service_account_email = service_account_email
        self._token = None
        self._token_expiry = 0

    async def get_id_token(self) -> str:
        """Get an ID token for the target audience"""
        import time

        # Check if we have a valid cached token
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        # Get default credentials
        credentials, project = google.auth.default()

        # If service account email is specified, impersonate it
        if self.service_account_email:
            credentials = impersonated_credentials.Credentials(
                source_credentials=credentials,
                target_principal=self.service_account_email,
                target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )

        # Create an auth request
        auth_req = google.auth.transport.requests.Request()

        # Get ID token
        credentials.refresh(auth_req)

        # For service accounts, we need to get an ID token
        if hasattr(credentials, "id_token"):
            self._token = credentials.id_token
        else:
            # Use the access token as a bearer token
            self._token = credentials.token

        # Cache for 1 hour (tokens typically last 1 hour)
        self._token_expiry = time.time() + 3600

        return self._token

    async def call_service(
        self, url: str, method: str = "GET", json_data: Optional[dict] = None
    ):
        """Call a service with OIDC authentication"""
        token = await self.get_id_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, headers=headers, json=json_data
            ) as response:
                response.raise_for_status()
                return await response.json()


# Example usage
async def main():
    # Create client for calling the detection service
    detection_url = "https://sentinelops-detection-xxxxx-uc.a.run.app"

    client = ServiceAuthClient(
        target_audience=detection_url,
        service_account_email="sentinelops-orchestrator@your-gcp-project-id.iam.gserviceaccount.com",
    )

    # Call the service
    try:
        result = await client.call_service(f"{detection_url}/health")
        print("Service response: {result}")
    except Exception as e:
        print("Error calling service: {e}")


if __name__ == "__main__":
    asyncio.run(main())

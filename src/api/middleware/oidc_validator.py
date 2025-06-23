"""
OIDC Token Validator for SentinelOps
"""

import os
import time
from functools import lru_cache
from typing import Any, Dict

import requests
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

security = HTTPBearer()


class OIDCValidator:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.issuer = "https://accounts.google.com"
        self._jwks_cache: Dict[str, Any] = {}
        self._jwks_cache_time: float = 0

    @lru_cache(maxsize=128)
    def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set from Google"""
        current_time = time.time()

        # Cache for 1 hour
        if current_time - self._jwks_cache_time > 3600:
            response = requests.get(
                "https://www.googleapis.com/oauth2/v3/certs", timeout=30
            )
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_cache_time = current_time

        return self._jwks_cache

    async def validate_token(
        self, credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> Dict[str, Any]:
        """Validate OIDC token"""
        token = credentials.credentials

        try:
            # For Google-issued ID tokens
            request: google_requests.Request = (
                google_requests.Request()  # type: ignore[no-untyped-call]
            )

            # Verify the token
            claims = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                token, request, audience=self.project_id
            )

            # Check issuer
            if claims.get("iss") not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                raise ValueError(f"Invalid issuer: {claims.get('iss')}")

            # Check expiration
            if claims.get("exp", 0) < time.time():
                raise ValueError("Token has expired")

            return {
                "sub": claims.get("sub"),
                "email": claims.get("email"),
                "email_verified": claims.get("email_verified"),
                "name": claims.get("name"),
                "picture": claims.get("picture"),
                "iat": claims.get("iat"),
                "exp": claims.get("exp"),
            }

        except Exception as e:
            raise HTTPException(
                status_code=401, detail=f"Invalid token: {str(e)}"
            ) from e


# Global validator instance
oidc_validator = OIDCValidator(os.getenv("PROJECT_ID", "your-gcp-project-id"))


# Dependency for protected routes
async def validate_oidc_token(
    claims: Dict[str, Any] = Security(oidc_validator.validate_token),
) -> Dict[str, Any]:
    """Validate OIDC token for protected routes"""
    return claims

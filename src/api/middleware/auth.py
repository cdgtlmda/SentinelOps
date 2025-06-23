"""
Authentication middleware for SentinelOps API
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests
from google.oauth2 import id_token

security = HTTPBearer()


class AuthMiddleware:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.jwt_config = self._load_jwt_config()

    def _load_jwt_config(self) -> dict[str, Any]:
        """Load JWT configuration"""
        config_path = "config/auth/jwt_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return dict(data)
            except (json.JSONDecodeError, IOError):
                # Fall back to default config if file is invalid
                pass
        return {
            "algorithm": "RS256",
            "issuer": f"sentinelops@{self.project_id}",
            "audience": f"https://sentinelops-{self.project_id}.cloudfunctions.net",
            "expiry_minutes": 60,
        }

    async def verify_token(
        self, credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> dict[str, Any]:
        """Verify JWT token"""
        token = credentials.credentials

        try:
            # For Google-issued tokens (from service accounts)
            if token.startswith("ya29."):
                return await self._verify_google_token(token)

            # For custom JWT tokens
            return self._verify_jwt_token(token)

        except Exception as e:
            raise HTTPException(
                status_code=401, detail=f"Invalid authentication credentials: {str(e)}"
            ) from e

    async def _verify_google_token(self, token: str) -> dict[str, Any]:
        """Verify Google OAuth2 token"""
        try:
            request = requests.Request()  # type: ignore[no-untyped-call]
            claims = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                token, request, self.jwt_config["audience"]
            )
            return {
                "email": claims.get("email"),
                "sub": claims.get("sub"),
                "type": "google_oauth2",
            }
        except Exception as e:
            raise ValueError(f"Invalid Google token: {e}") from e

    def _verify_jwt_token(self, token: str) -> dict[str, Any]:
        """Verify custom JWT token"""
        # In production, load public key from Secret Manager
        # For now, we'll skip verification
        try:
            # Decode without verification for development
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=[self.jwt_config["algorithm"]],
            )

            # Verify expiry
            if "exp" in payload:
                exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
                if exp_time < datetime.now(timezone.utc):
                    raise ValueError("Token has expired")

            if not isinstance(payload, dict):
                raise ValueError("Invalid token payload")
            return dict(payload)

        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid JWT token: {e}") from e


# Global middleware instance
auth_middleware = AuthMiddleware(
    os.getenv("PROJECT_ID", "your-gcp-project-id")
)


# Dependency for protected routes
async def verify_auth(
    claims: dict[str, Any] = Depends(auth_middleware.verify_token)
) -> dict[str, Any]:
    """Verify authentication for protected routes"""
    return claims

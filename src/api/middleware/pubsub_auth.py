"""
Pub/Sub message authentication for SentinelOps
"""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class PubSubAuth:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or "temporary-development-key"

    def sign_message(self, message: Dict[str, Any]) -> str:
        """Sign a Pub/Sub message"""
        message_json = json.dumps(message, sort_keys=True)
        signature = hmac.new(
            self.secret_key.encode(), message_json.encode(), hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()

    def verify_message(self, message: Dict[str, Any], signature: str) -> bool:
        """Verify a Pub/Sub message signature"""
        expected_signature = self.sign_message(message)
        return hmac.compare_digest(expected_signature, signature)

    def add_auth_attributes(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add authentication attributes to a message"""
        signature = self.sign_message(message)

        if "attributes" not in message:
            message["attributes"] = {}

        message["attributes"]["signature"] = signature
        message["attributes"]["signed_at"] = datetime.now(timezone.utc).isoformat()

        return message

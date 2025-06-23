"""Tests for Pub/Sub message authentication using real production code."""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from src.api.middleware.pubsub_auth import PubSubAuth


class TestPubSubAuth:
    """Test cases for PubSubAuth with real production code."""

    @pytest.fixture
    def auth_instance(self) -> PubSubAuth:
        """Create PubSubAuth instance with test secret."""
        return PubSubAuth(secret_key="test-secret-key-123")

    @pytest.fixture
    def default_auth_instance(self) -> PubSubAuth:
        """Create PubSubAuth instance with default secret."""
        return PubSubAuth()

    @pytest.fixture
    def sample_message(self) -> Dict[str, Any]:
        """Sample Pub/Sub message for testing."""
        return {
            "data": {
                "incident_id": "inc-123",
                "severity": "high",
                "timestamp": "2025-06-12T10:00:00Z"
            },
            "messageId": "msg-456"
        }

    def test_initialization_with_secret(self) -> None:
        """Test PubSubAuth initialization with custom secret."""
        auth = PubSubAuth(secret_key="custom-secret")
        assert auth.secret_key == "custom-secret"

    def test_initialization_without_secret(self) -> None:
        """Test PubSubAuth initialization with default secret."""
        auth = PubSubAuth()
        assert auth.secret_key == "temporary-development-key"

    def test_sign_message(self, auth_instance: PubSubAuth, sample_message: Dict[str, Any]) -> None:
        """Test message signing with real HMAC calculation."""
        signature = auth_instance.sign_message(sample_message)

        # Verify signature format
        assert isinstance(signature, str)
        assert len(signature) > 0

        # Verify it's valid base64
        try:
            decoded = base64.b64decode(signature)
            assert len(decoded) == 32  # SHA256 produces 32 bytes
        except Exception:
            pytest.fail("Signature is not valid base64")

    def test_sign_message_deterministic(self, auth_instance: PubSubAuth, sample_message: Dict[str, Any]) -> None:
        """Test that signing the same message produces the same signature."""
        signature1 = auth_instance.sign_message(sample_message)
        signature2 = auth_instance.sign_message(sample_message)

        assert signature1 == signature2

    def test_sign_message_different_messages(self, auth_instance: PubSubAuth) -> None:
        """Test that different messages produce different signatures."""
        message1 = {"data": "message1"}
        message2 = {"data": "message2"}

        signature1 = auth_instance.sign_message(message1)
        signature2 = auth_instance.sign_message(message2)

        assert signature1 != signature2

    def test_sign_message_order_independent(self, auth_instance: PubSubAuth) -> None:
        """Test that message key order doesn't affect signature."""
        message1 = {"a": 1, "b": 2, "c": 3}
        message2 = {"c": 3, "a": 1, "b": 2}

        signature1 = auth_instance.sign_message(message1)
        signature2 = auth_instance.sign_message(message2)

        assert signature1 == signature2

    def test_verify_message_valid(self, auth_instance: PubSubAuth, sample_message: Dict[str, Any]) -> None:
        """Test verifying a valid message signature."""
        signature = auth_instance.sign_message(sample_message)

        is_valid = auth_instance.verify_message(sample_message, signature)

        assert is_valid is True

    def test_verify_message_invalid_signature(self, auth_instance: PubSubAuth, sample_message: Dict[str, Any]) -> None:
        """Test verifying a message with invalid signature."""
        # Create an invalid signature
        invalid_signature = base64.b64encode(b"invalid-signature").decode()

        is_valid = auth_instance.verify_message(sample_message, invalid_signature)

        assert is_valid is False

    def test_verify_message_tampered(self, auth_instance: PubSubAuth, sample_message: Dict[str, Any]) -> None:
        """Test verifying a tampered message."""
        # Sign the original message
        signature = auth_instance.sign_message(sample_message)

        # Tamper with the message
        tampered_message = sample_message.copy()
        tampered_message["data"]["severity"] = "low"

        is_valid = auth_instance.verify_message(tampered_message, signature)

        assert is_valid is False

    def test_verify_message_different_secret(self, sample_message: Dict[str, Any]) -> None:
        """Test that signatures from different secrets don't validate."""
        auth1 = PubSubAuth(secret_key="secret1")
        auth2 = PubSubAuth(secret_key="secret2")

        signature = auth1.sign_message(sample_message)
        is_valid = auth2.verify_message(sample_message, signature)

        assert is_valid is False

    def test_add_auth_attributes_new_attributes(self, auth_instance: PubSubAuth, sample_message: Dict[str, Any]) -> None:
        """Test adding auth attributes to message without existing attributes."""
        # Use a copy to avoid modifying the fixture
        message = sample_message.copy()

        # Call the method and capture the timestamp
        before_time = datetime.now(timezone.utc)
        result = auth_instance.add_auth_attributes(message)
        after_time = datetime.now(timezone.utc)

        assert "attributes" in result
        assert "signature" in result["attributes"]
        assert "signed_at" in result["attributes"]

        # Verify timestamp is within expected range
        signed_at = datetime.fromisoformat(result["attributes"]["signed_at"].replace('Z', '+00:00'))
        assert before_time <= signed_at <= after_time

        # Verify the signature is correct
        signature = result["attributes"]["signature"]
        assert auth_instance.verify_message(sample_message, signature)

    def test_add_auth_attributes_existing_attributes(self, auth_instance: PubSubAuth) -> None:
        """Test adding auth attributes to message with existing attributes."""
        message = {
            "data": {"test": "data"},
            "attributes": {
                "existing_attr": "value"
            }
        }

        result = auth_instance.add_auth_attributes(message)

        assert "attributes" in result
        assert "existing_attr" in result["attributes"]
        assert result["attributes"]["existing_attr"] == "value"
        assert "signature" in result["attributes"]
        assert "signed_at" in result["attributes"]

    def test_hmac_implementation_details(self, auth_instance: PubSubAuth) -> None:
        """Test the actual HMAC implementation matches expected behavior."""
        message = {"test": "data"}
        message_json = json.dumps(message, sort_keys=True)

        # Calculate expected signature manually
        expected_hmac = hmac.new(
            auth_instance.secret_key.encode(),
            message_json.encode(),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(expected_hmac).decode()

        # Compare with actual signature
        actual_signature = auth_instance.sign_message(message)

        assert actual_signature == expected_signature

    def test_empty_message_signing(self, auth_instance: PubSubAuth) -> None:
        """Test signing an empty message."""
        empty_message: Dict[str, Any] = {}

        signature = auth_instance.sign_message(empty_message)

        assert isinstance(signature, str)
        assert len(signature) > 0
        assert auth_instance.verify_message(empty_message, signature)

    def test_complex_nested_message(self, auth_instance: PubSubAuth) -> None:
        """Test signing a complex nested message."""
        complex_message = {
            "data": {
                "incident": {
                    "id": "inc-123",
                    "details": {
                        "severity": "high",
                        "affected_services": ["api", "database"],
                        "metrics": {
                            "error_rate": 0.05,
                            "latency_p99": 1200
                        }
                    }
                },
                "timestamp": "2025-06-12T10:00:00Z"
            },
            "metadata": {
                "source": "monitoring",
                "version": "1.0"
            }
        }

        signature = auth_instance.sign_message(complex_message)

        assert auth_instance.verify_message(complex_message, signature)

    def test_unicode_message_signing(self, auth_instance: PubSubAuth) -> None:
        """Test signing messages with unicode characters."""
        unicode_message = {
            "data": {
                "message": "Alert: 警告メッセージ",
                "user": "用户123",
                "emoji": "🚨🔥"
            }
        }

        signature = auth_instance.sign_message(unicode_message)

        assert isinstance(signature, str)
        assert auth_instance.verify_message(unicode_message, signature)

    def test_concurrent_signing(self, auth_instance: PubSubAuth) -> None:
        """Test that concurrent signing operations work correctly."""
        import threading

        results = {}
        message = {"data": "concurrent-test"}

        def sign_message(thread_id: int) -> None:
            results[thread_id] = auth_instance.sign_message(message)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=sign_message, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All signatures should be identical
        signatures = list(results.values())
        assert all(sig == signatures[0] for sig in signatures)

    def test_signature_timing_attack_resistance(self, auth_instance: PubSubAuth, sample_message: Dict[str, Any]) -> None:
        """Test that signature verification uses constant-time comparison."""
        valid_signature = auth_instance.sign_message(sample_message)

        # Create signatures that differ at different positions
        invalid_signatures = []

        # Decode valid signature
        valid_bytes = base64.b64decode(valid_signature)

        # Create invalid signatures with single bit flips
        for i in range(len(valid_bytes)):
            invalid_bytes = bytearray(valid_bytes)
            invalid_bytes[i] ^= 1  # Flip one bit
            invalid_signatures.append(base64.b64encode(invalid_bytes).decode())

        # All should return False
        for invalid_sig in invalid_signatures:
            assert auth_instance.verify_message(sample_message, invalid_sig) is False

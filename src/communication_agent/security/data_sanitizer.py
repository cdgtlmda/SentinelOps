"""
Data sanitization implementation for the Communication Agent.

Provides functionality for removing PII, masking secrets, and redacting
sensitive information from notifications and logs.
"""

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Set, Union

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SanitizationConfig:
    """Configuration for data sanitization."""

    # PII removal settings
    remove_emails: bool = True
    remove_phone_numbers: bool = True
    remove_ssn: bool = True
    remove_credit_cards: bool = True
    remove_ip_addresses: bool = False  # May be needed for debugging
    remove_custom_patterns: List[Pattern[str]] = field(default_factory=list)

    # Secret masking settings
    mask_api_keys: bool = True
    mask_tokens: bool = True
    mask_passwords: bool = True
    mask_credentials: bool = True
    secret_patterns: List[Pattern[str]] = field(default_factory=list)

    # Log redaction settings
    redact_logs: bool = True
    log_redaction_placeholder: str = "[REDACTED]"
    preserve_length: bool = False  # If True, shows [REDACTED-X] where X is length

    # Custom sensitive fields to redact
    sensitive_fields: Set[str] = field(
        default_factory=lambda: {
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "api_key",
            "apikey",
            "access_token",
            "refresh_token",
            "private_key",
            "privatekey",
            "credential",
            "auth",
            "authorization",
            "ssn",
            "social_security",
            "credit_card",
            "card_number",
            "cvv",
            "pin",
            "account_number",
            "routing_number",
            "license_number",
            "passport",
            "bank_account",
        }
    )

    # Whitelisted patterns that should not be sanitized
    whitelist_patterns: List[Pattern[str]] = field(default_factory=list)


class DataSanitizer:
    """
    Sanitizes data to remove PII and mask sensitive information.

    Provides comprehensive sanitization for notifications and logs to ensure
    compliance with privacy regulations and security best practices.
    """

    def __init__(self, config: Optional[SanitizationConfig] = None):
        """Initialize the data sanitizer."""
        self.config = config or SanitizationConfig()
        self._compile_patterns()
        logger.info("Data sanitizer initialized")

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        # Email pattern
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )

        # Phone number patterns (various formats)
        self.phone_patterns = [
            re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),  # US format
            re.compile(r"\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b"),  # US with parens
            re.compile(
                r"\b\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b"
            ),  # International
        ]

        # SSN pattern
        self.ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b")

        # Credit card patterns
        self.credit_card_patterns = [
            re.compile(r"\b4[0-9]{12}(?:[0-9]{3})?\b"),  # Visa
            re.compile(r"\b5[1-5][0-9]{14}\b"),  # Mastercard
            re.compile(r"\b3[47][0-9]{13}\b"),  # Amex
            re.compile(r"\b3(?:0[0-5]|[68][0-9])[0-9]{11}\b"),  # Diners
            re.compile(r"\b6(?:011|5[0-9]{2})[0-9]{12}\b"),  # Discover
            re.compile(r"\b(?:2131|1800|35\d{3})\d{11}\b"),  # JCB
        ]

        # IP address patterns
        self.ip_patterns = [
            re.compile(  # IPv4
                r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
            ),
            re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"),  # IPv6
        ]

        # API key and token patterns
        self.secret_patterns = [
            re.compile(
                r'[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]\s*[:=]\s*["\']?([^"\'\s]+)["\']?'
            ),
            re.compile(r'[Tt][Oo][Kk][Ee][Nn]\s*[:=]\s*["\']?([^"\'\s]+)["\']?'),
            re.compile(r'[Ss][Ee][Cc][Rr][Ee][Tt]\s*[:=]\s*["\']?([^"\'\s]+)["\']?'),
            re.compile(
                r'[Pp][Aa][Ss][Ss][Ww]?[Oo]?[Rr]?[Dd]?\s*[:=]\s*["\']?([^"\'\s]+)["\']?'
            ),
            re.compile(
                r"[Bb][Ee][Aa][Rr][Ee][Rr]\s+([A-Za-z0-9+/=._-]{20,})"
            ),  # Bearer tokens
            re.compile(r"[Bb][Aa][Ss][Ii][Cc]\s+([A-Za-z0-9+/=]{20,})"),  # Basic auth
        ] + self.config.secret_patterns

    def sanitize(self, data: Any) -> Any:
        """
        Sanitize data based on its type.

        Args:
            data: Data to sanitize (string, dict, or list)

        Returns:
            Sanitized data of the same type
        """
        if isinstance(data, str):
            return self.sanitize_string(data)
        elif isinstance(data, dict):
            return self.sanitize_dict(data)
        elif isinstance(data, list):
            return self.sanitize_list(data)
        else:
            # For other types, convert to string, sanitize, and convert back if possible
            # Don't modify numeric/boolean values
            if isinstance(data, (int, float, bool)):
                return data
            try:
                sanitized_str = self.sanitize_string(str(data))
                return sanitized_str
            except (ValueError, AttributeError):
                return data

    def sanitize_string(self, text: str) -> str:
        """
        Sanitize a string by removing PII and masking secrets.

        Args:
            text: String to sanitize

        Returns:
            Sanitized string
        """
        if not text:
            return text

        # Check whitelist patterns first
        if self._is_whitelisted(text):
            return text

        # Remove PII and mask secrets
        text = self._remove_pii(text)
        text = self._apply_custom_patterns(text)
        text = self._mask_secrets_if_configured(text)

        return text

    def _is_whitelisted(self, text: str) -> bool:
        """Check if text matches any whitelist pattern."""
        for pattern in self.config.whitelist_patterns:
            if pattern.search(text):
                return True
        return False

    def _remove_pii(self, text: str) -> str:
        """Remove various types of PII from text."""
        if self.config.remove_emails:
            text = self._sanitize_emails(text)

        if self.config.remove_phone_numbers:
            text = self._sanitize_phone_numbers(text)

        if self.config.remove_ssn:
            text = self._sanitize_ssn(text)

        if self.config.remove_credit_cards:
            text = self._sanitize_credit_cards(text)

        if self.config.remove_ip_addresses:
            text = self._sanitize_ip_addresses(text)

        return text

    def _apply_custom_patterns(self, text: str) -> str:
        """Apply custom PII removal patterns."""
        for pattern in self.config.remove_custom_patterns:
            text = pattern.sub(self._get_replacement_text, text)
        return text

    def _mask_secrets_if_configured(self, text: str) -> str:
        """Mask secrets if configured to do so."""
        if (
            self.config.mask_api_keys
            or self.config.mask_tokens
            or self.config.mask_passwords
        ):
            text = self._mask_secrets(text)
        return text

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a dictionary by sanitizing values and redacting sensitive fields.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized: Dict[str, Any] = {}

        for key, value in data.items():
            # Check if the key indicates sensitive data
            if self._is_sensitive_field(key):
                sanitized[key] = self._get_replacement_text(str(value))
            else:
                # Recursively sanitize the value
                sanitized[key] = self.sanitize(value)

        return sanitized

    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """
        Sanitize a list by sanitizing each element.

        Args:
            data: List to sanitize

        Returns:
            Sanitized list
        """
        return [self.sanitize(item) for item in data]

    def _sanitize_emails(self, text: str) -> str:
        """Remove email addresses from text."""
        return self.email_pattern.sub(self._get_replacement_text, text)

    def _sanitize_phone_numbers(self, text: str) -> str:
        """Remove phone numbers from text."""
        for pattern in self.phone_patterns:
            text = pattern.sub(self._get_replacement_text, text)
        return text

    def _sanitize_ssn(self, text: str) -> str:
        """Remove SSN from text."""
        return self.ssn_pattern.sub(self._get_replacement_text, text)

    def _sanitize_credit_cards(self, text: str) -> str:
        """Remove credit card numbers from text."""
        for pattern in self.credit_card_patterns:
            text = pattern.sub(self._get_replacement_text, text)
        return text

    def _sanitize_ip_addresses(self, text: str) -> str:
        """Remove IP addresses from text."""
        for pattern in self.ip_patterns:
            text = pattern.sub(self._get_replacement_text, text)
        return text

    def _mask_secrets(self, text: str) -> str:
        """Mask secrets like API keys and tokens."""
        for pattern in self.secret_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                # Get the secret value (usually in group 1)
                secret = match.group(1) if match.groups() else match.group(0)
                if len(secret) > 4:  # Only mask if secret is long enough
                    # Show first 2 and last 2 characters
                    masked = f"{secret[:2]}{'*' * (len(secret) - 4)}{secret[-2:]}"
                    text = text.replace(secret, masked)

        return text

    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field name indicates sensitive data."""
        field_lower = field_name.lower()

        # Check against known sensitive fields
        for sensitive in self.config.sensitive_fields:
            if sensitive in field_lower:
                return True

        return False

    def _get_replacement_text(self, match_or_text: Union[str, re.Match[str]]) -> str:
        """Get replacement text for redacted content."""
        if isinstance(match_or_text, str):
            text = match_or_text
        else:
            text = match_or_text.group(0)

        if self.config.preserve_length:
            return f"[REDACTED-{len(text)}]"
        else:
            return self.config.log_redaction_placeholder

    def sanitize_for_logs(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Special sanitization for log entries.

        Args:
            log_data: Log data to sanitize

        Returns:
            Sanitized log data
        """
        if not self.config.redact_logs:
            return log_data

        # Create a deep copy to avoid modifying the original
        sanitized_data = copy.deepcopy(log_data)

        # Sanitize the entire log data
        return self.sanitize_dict(sanitized_data)

    def create_safe_summary(self, data: Dict[str, Any]) -> str:
        """
        Create a safe summary of data for logging or display.

        Args:
            data: Data to summarize

        Returns:
            Safe summary string
        """
        sanitized = self.sanitize_dict(data)

        summary_parts = []
        for key, value in sanitized.items():
            if isinstance(value, (dict, list)):
                summary_parts.append(f"{key}: <{type(value).__name__}>")
            else:
                summary_parts.append(f"{key}: {value}")

        return ", ".join(summary_parts)

    def validate_sanitization(self, sanitized: str) -> List[str]:
        """
        Validate that sanitization was effective.

        Args:
            sanitized: Sanitized text

        Returns:
            List of potential issues found
        """
        issues = []

        # Check for remaining emails
        if self.config.remove_emails and self.email_pattern.search(sanitized):
            issues.append("Email addresses may still be present")

        # Check for remaining phone numbers
        if self.config.remove_phone_numbers:
            for pattern in self.phone_patterns:
                if pattern.search(sanitized):
                    issues.append("Phone numbers may still be present")
                    break

        # Check for remaining SSN
        if self.config.remove_ssn and self.ssn_pattern.search(sanitized):
            issues.append("SSN may still be present")

        # Check for remaining credit cards
        if self.config.remove_credit_cards:
            for pattern in self.credit_card_patterns:
                if pattern.search(sanitized):
                    issues.append("Credit card numbers may still be present")
                    break

        return issues

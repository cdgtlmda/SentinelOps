"""
Webhook configuration for the Communication Agent.

Provides configuration loading for webhook notifications.
"""

import json
import os
from typing import Dict, Optional

from src.communication_agent.services.webhook_service import (
    WebhookAuthType,
    WebhookConfig,
    WebhookMethod,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def get_webhook_config() -> Optional[WebhookConfig]:  # noqa: C901
    """
    Get default webhook configuration from environment variables.

    Expected environment variables:
    - WEBHOOK_URL: Default webhook URL
    - WEBHOOK_METHOD: HTTP method (default: POST)
    - WEBHOOK_AUTH_TYPE: Authentication type (none, basic, bearer, api_key, hmac)
    - WEBHOOK_AUTH_CREDENTIALS: JSON string with auth credentials
    - WEBHOOK_HEADERS: JSON string with custom headers
    - WEBHOOK_TIMEOUT: Request timeout in seconds (default: 30)
    - WEBHOOK_MAX_RETRIES: Maximum retry attempts (default: 3)
    - WEBHOOK_VERIFY_SSL: Verify SSL certificates (default: true)

    Returns:
        WebhookConfig if URL is set, None otherwise
    """
    webhook_url = os.getenv("WEBHOOK_URL")

    if not webhook_url:
        logger.debug("No default webhook URL configured")
        return None

    # Parse method
    method_str = os.getenv("WEBHOOK_METHOD", "POST").upper()
    try:
        method = WebhookMethod(method_str)
    except ValueError:
        logger.warning(f"Invalid webhook method: {method_str}, using POST")
        method = WebhookMethod.POST

    # Parse auth type
    auth_type_str = os.getenv("WEBHOOK_AUTH_TYPE", "none").lower()
    try:
        auth_type = WebhookAuthType(auth_type_str)
    except ValueError:
        logger.warning(f"Invalid auth type: {auth_type_str}, using none")
        auth_type = WebhookAuthType.NONE

    # Parse auth credentials
    auth_credentials = None
    auth_creds_str = os.getenv("WEBHOOK_AUTH_CREDENTIALS")
    if auth_creds_str:
        try:
            auth_credentials = json.loads(auth_creds_str)
        except json.JSONDecodeError:
            logger.error("Failed to parse WEBHOOK_AUTH_CREDENTIALS as JSON")

    # Parse custom headers
    headers = None
    headers_str = os.getenv("WEBHOOK_HEADERS")
    if headers_str:
        try:
            headers = json.loads(headers_str)
        except json.JSONDecodeError:
            logger.error("Failed to parse WEBHOOK_HEADERS as JSON")

    config = WebhookConfig(
        url=webhook_url,
        method=method,
        auth_type=auth_type,
        auth_credentials=auth_credentials,
        headers=headers,
        timeout=int(os.getenv("WEBHOOK_TIMEOUT", "30")),
        max_retries=int(os.getenv("WEBHOOK_MAX_RETRIES", "3")),
        retry_delay=int(os.getenv("WEBHOOK_RETRY_DELAY", "5")),
        verify_ssl=os.getenv("WEBHOOK_VERIFY_SSL", "true").lower() == "true",
    )

    logger.info(
        "Default webhook configuration loaded",
        extra={
            "url": webhook_url,
            "method": method.value,
            "auth_type": auth_type.value,
            "has_headers": bool(headers),
        },
    )

    return config


def get_webhook_configs() -> Dict[str, WebhookConfig]:
    """
    Load named webhook configurations from environment.

    Looks for environment variables in the format:
    WEBHOOK_CONFIG_<NAME>='{"url": "...", "method": "POST", ...}'

    Returns:
        Dictionary of webhook configurations by name
    """
    configs = {}
    prefix = "WEBHOOK_CONFIG_"

    for key, value in os.environ.items():
        if key.startswith(prefix):
            name = key[len(prefix) :].lower()
            try:
                config_dict = json.loads(value)

                # Parse method
                method = WebhookMethod(config_dict.get("method", "POST").upper())

                # Parse auth type
                auth_type = WebhookAuthType(
                    config_dict.get("auth_type", "none").lower()
                )

                configs[name] = WebhookConfig(
                    url=config_dict["url"],
                    method=method,
                    auth_type=auth_type,
                    auth_credentials=config_dict.get("auth_credentials"),
                    headers=config_dict.get("headers"),
                    timeout=config_dict.get("timeout", 30),
                    max_retries=config_dict.get("max_retries", 3),
                    retry_delay=config_dict.get("retry_delay", 5),
                    verify_ssl=config_dict.get("verify_ssl", True),
                )

                logger.info(
                    f"Loaded webhook configuration: {name}",
                    extra={"url": config_dict["url"]},
                )

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(
                    f"Failed to parse webhook config {key}: {e}",
                    extra={"key": key, "value": value},
                )

    return configs

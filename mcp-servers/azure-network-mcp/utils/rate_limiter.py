"""Error handling, retry configuration, and Azure exception translation."""

from __future__ import annotations

import json
import logging
from typing import Optional

from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ResourceNotFoundError as AzureResourceNotFoundError,
    ServiceRequestError,
)

from utils.constants import AZURE_ERROR_CODES, MAX_RETRIES, RETRY_BACKOFF_FACTOR, RETRY_BACKOFF_MAX

logger = logging.getLogger("azure-network-mcp")


def get_retry_policy() -> dict:
    """Return retry configuration for Azure SDK clients."""
    return {
        "retry_total": MAX_RETRIES,
        "retry_backoff_factor": RETRY_BACKOFF_FACTOR,
        "retry_backoff_max": RETRY_BACKOFF_MAX,
        "retry_on_status_codes": [429, 500, 502, 503, 504],
    }


def translate_azure_error(error: Exception) -> dict:
    """
    Translate Azure SDK exceptions into user-friendly error dicts.

    Returns:
        Dict with 'error' key containing code, message, and details.
    """
    error_response = {
        "error": {
            "code": "UnknownError",
            "message": "An unexpected error occurred.",
            "details": str(error),
        }
    }

    if isinstance(error, ClientAuthenticationError):
        error_response["error"]["code"] = "AuthenticationError"
        error_response["error"]["message"] = AZURE_ERROR_CODES.get(
            "AuthenticationFailed", {}
        ).get("message", "Authentication failed.")

    elif isinstance(error, AzureResourceNotFoundError):
        error_response["error"]["code"] = "ResourceNotFoundError"
        error_response["error"]["message"] = AZURE_ERROR_CODES.get(
            "ResourceNotFound", {}
        ).get("message", "Resource not found.")

    elif isinstance(error, HttpResponseError):
        status = getattr(error, "status_code", None)
        error_code = getattr(error, "error", None)
        code_str = getattr(error_code, "code", "") if error_code else ""

        if status == 403 or code_str == "AuthorizationFailed":
            error_response["error"]["code"] = "AuthorizationError"
            error_response["error"]["message"] = AZURE_ERROR_CODES.get(
                "AuthorizationFailed", {}
            ).get("message", "Authorization failed.")
        elif status == 404:
            # Check for subscription not found vs resource not found
            if "SubscriptionNotFound" in str(error):
                error_response["error"]["code"] = "SubscriptionNotFoundError"
                error_response["error"]["message"] = AZURE_ERROR_CODES.get(
                    "SubscriptionNotFound", {}
                ).get("message", "Subscription not found.")
            else:
                error_response["error"]["code"] = "ResourceNotFoundError"
                error_response["error"]["message"] = AZURE_ERROR_CODES.get(
                    "ResourceNotFound", {}
                ).get("message", "Resource not found.")
        elif status == 429 or code_str == "TooManyRequests":
            error_response["error"]["code"] = "ThrottlingError"
            error_response["error"]["message"] = AZURE_ERROR_CODES.get(
                "TooManyRequests", {}
            ).get("message", "Rate limit exceeded.")
        elif status == 400:
            error_response["error"]["code"] = "ValidationError"
            error_response["error"]["message"] = AZURE_ERROR_CODES.get(
                "InvalidParameter", {}
            ).get("message", "Invalid parameter.")
        else:
            error_response["error"]["code"] = f"AzureError_{status}"
            error_response["error"]["message"] = str(error)

    elif isinstance(error, ServiceRequestError):
        error_response["error"]["code"] = "ServiceRequestError"
        error_response["error"]["message"] = (
            "Failed to connect to Azure services. Check network connectivity."
        )

    elif isinstance(error, ValueError):
        error_response["error"]["code"] = "ValidationError"
        error_response["error"]["message"] = str(error)

    error_response["error"]["details"] = str(error)
    return error_response


def format_error_response(error: Exception) -> str:
    """Format an Azure error as a JSON string for MCP tool responses."""
    return json.dumps(translate_azure_error(error), indent=2)

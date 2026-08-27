"""Pinned Azure ARM API versions and error code mappings."""

# Azure ARM API versions - pinned for stability
NETWORK_API_VERSION = "2024-05-01"
RESOURCE_API_VERSION = "2024-03-01"
DNS_API_VERSION = "2023-07-01-preview"
FRONTDOOR_API_VERSION = "2024-02-01"

# Azure error code to user-friendly message mappings
AZURE_ERROR_CODES = {
    "AuthenticationFailed": {
        "code": "AuthenticationError",
        "message": "Failed to authenticate. Verify AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET environment variables are set correctly.",
    },
    "AuthorizationFailed": {
        "code": "AuthorizationError",
        "message": "Service principal lacks required permissions. Ensure Reader role is assigned on the target subscription.",
    },
    "SubscriptionNotFound": {
        "code": "SubscriptionNotFoundError",
        "message": "Subscription ID not found or not accessible. Verify AZURE_SUBSCRIPTION_ID is correct.",
    },
    "ResourceNotFound": {
        "code": "ResourceNotFoundError",
        "message": "The specified resource does not exist.",
    },
    "ResourceGroupNotFound": {
        "code": "ResourceNotFoundError",
        "message": "The specified resource group does not exist.",
    },
    "TooManyRequests": {
        "code": "ThrottlingError",
        "message": "Azure ARM API rate limit exceeded. The server will automatically retry with backoff.",
    },
    "InvalidParameter": {
        "code": "ValidationError",
        "message": "Invalid parameter provided.",
    },
    "NetworkWatcherNotFound": {
        "code": "NetworkWatcherUnavailable",
        "message": "Network Watcher is not enabled in the target region.",
    },
}

# Concurrency limits
MAX_CONCURRENT_SUBSCRIPTIONS = 5

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5
RETRY_BACKOFF_MAX = 30

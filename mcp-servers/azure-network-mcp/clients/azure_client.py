"""Azure SDK client factory with DefaultAzureCredential and per-subscription client caching."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.dns import DnsManagementClient
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError

from utils.constants import MAX_CONCURRENT_SUBSCRIPTIONS

logger = logging.getLogger("azure-network-mcp")


class AzureClientFactory:
    """Factory for Azure SDK clients with credential caching and concurrency limiting."""

    def __init__(self):
        self._credential: Optional[DefaultAzureCredential | ClientSecretCredential] = None
        self._network_clients: dict[str, NetworkManagementClient] = {}
        self._dns_clients: dict[str, DnsManagementClient] = {}
        self._subscription_client: Optional[SubscriptionClient] = None
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_SUBSCRIPTIONS)
        self._default_subscription_id: Optional[str] = None

    def initialize(self) -> None:
        """Initialize credentials from environment variables."""
        tenant_id = os.environ.get("AZURE_TENANT_ID")
        client_id = os.environ.get("AZURE_CLIENT_ID")
        client_secret = os.environ.get("AZURE_CLIENT_SECRET")
        self._default_subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

        if tenant_id and client_id and client_secret:
            self._credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
            logger.info("Initialized with ClientSecretCredential (service principal)")
        else:
            self._credential = DefaultAzureCredential()
            logger.info("Initialized with DefaultAzureCredential (fallback chain)")

    def validate_credentials(self) -> bool:
        """Validate that credentials can authenticate."""
        if self._credential is None:
            self.initialize()
        try:
            self._credential.get_token("https://management.azure.com/.default")
            logger.info("Credential validation successful")
            return True
        except ClientAuthenticationError as e:
            logger.error(f"Credential validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during credential validation: {e}")
            return False

    @property
    def default_subscription_id(self) -> Optional[str]:
        return self._default_subscription_id

    def resolve_subscription_id(self, subscription_id: Optional[str] = None) -> str:
        """Resolve subscription ID from parameter or environment default."""
        sub_id = subscription_id or self._default_subscription_id
        if not sub_id:
            raise ValueError(
                "No subscription_id provided and AZURE_SUBSCRIPTION_ID is not set. "
                "Pass subscription_id parameter or set the AZURE_SUBSCRIPTION_ID environment variable."
            )
        return sub_id

    def get_network_client(self, subscription_id: Optional[str] = None) -> NetworkManagementClient:
        """Get or create a NetworkManagementClient for the given subscription."""
        if self._credential is None:
            self.initialize()
        sub_id = self.resolve_subscription_id(subscription_id)
        if sub_id not in self._network_clients:
            self._network_clients[sub_id] = NetworkManagementClient(
                credential=self._credential,
                subscription_id=sub_id,
            )
        return self._network_clients[sub_id]

    def get_dns_client(self, subscription_id: Optional[str] = None) -> DnsManagementClient:
        """Get or create a DnsManagementClient for the given subscription."""
        if self._credential is None:
            self.initialize()
        sub_id = self.resolve_subscription_id(subscription_id)
        if sub_id not in self._dns_clients:
            self._dns_clients[sub_id] = DnsManagementClient(
                credential=self._credential,
                subscription_id=sub_id,
            )
        return self._dns_clients[sub_id]

    def get_subscription_client(self) -> SubscriptionClient:
        """Get or create a SubscriptionClient."""
        if self._credential is None:
            self.initialize()
        if self._subscription_client is None:
            self._subscription_client = SubscriptionClient(credential=self._credential)
        return self._subscription_client

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """Concurrency semaphore for multi-subscription queries."""
        return self._semaphore


# Singleton instance
azure_client_factory = AzureClientFactory()

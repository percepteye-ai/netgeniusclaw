"""
SuzieQ REST API Client for NetClaw MCP Server

Async HTTP client that wraps the SuzieQ REST API. Handles connection setup,
authentication (access_token), SSL configuration, query parameter building,
and structured error handling.

Environment Variables:
    SUZIEQ_API_URL: Base URL of the SuzieQ REST API (required)
    SUZIEQ_API_KEY: API access token for authentication (required)
    SUZIEQ_VERIFY_SSL: Whether to verify SSL certificates (default: true)
    SUZIEQ_TIMEOUT: Query timeout in seconds (default: 30)
"""

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger("suzieq-mcp")

# ---------------------------------------------------------------------------
# Known tables and assert-capable tables
# ---------------------------------------------------------------------------
KNOWN_TABLES = [
    "address", "arpnd", "bgp", "device", "devconfig",
    "evpnVni", "fs", "ifCounters", "interface", "inventory",
    "lldp", "mac", "mlag", "namespace", "network",
    "ospf", "route", "sqPoller", "topology", "vlan",
]

ASSERT_TABLES = ["bgp", "ospf", "interface", "evpnVni"]


class SuzieQClient:
    """Async HTTP client for the SuzieQ REST API."""

    def __init__(self) -> None:
        self.api_url = os.environ.get("SUZIEQ_API_URL", "").rstrip("/")
        self.api_key = os.environ.get("SUZIEQ_API_KEY", "")
        self.verify_ssl = os.environ.get("SUZIEQ_VERIFY_SSL", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        self.timeout = int(os.environ.get("SUZIEQ_TIMEOUT", "30"))
        self._client: Optional[httpx.AsyncClient] = None

    def validate_config(self) -> None:
        """Validate that required environment variables are set.

        Raises:
            ValueError: If SUZIEQ_API_URL or SUZIEQ_API_KEY is missing.
        """
        missing = []
        if not self.api_url:
            missing.append("SUZIEQ_API_URL")
        if not self.api_key:
            missing.append("SUZIEQ_API_KEY")
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the shared async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @staticmethod
    def build_query_params(
        namespace: Optional[str] = None,
        hostname: Optional[str] = None,
        columns: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        view: Optional[str] = None,
        filters: Optional[str] = None,
    ) -> dict[str, str]:
        """Convert tool parameters into SuzieQ REST API query parameters.

        Args:
            namespace: SuzieQ namespace filter.
            hostname: Device hostname filter.
            columns: Comma-separated column names.
            start_time: ISO 8601 or relative time string (e.g., "1h", "2d").
            end_time: ISO 8601 or relative time string.
            view: Data view: "latest", "all", or "changes".
            filters: Additional key=value pairs separated by ampersand.

        Returns:
            Dict of query parameter names to values.
        """
        params: dict[str, str] = {}

        if namespace:
            params["namespace"] = namespace
        if hostname:
            params["hostname"] = hostname
        if columns:
            params["columns"] = columns
        if start_time:
            params["start-time"] = start_time
        if end_time:
            params["end-time"] = end_time
        if view:
            params["view"] = view

        # Parse additional filters string (key=value&key=value)
        if filters:
            for pair in filters.split("&"):
                pair = pair.strip()
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        params[key] = value

        return params

    async def query(
        self,
        table: str,
        verb: str,
        params: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Execute a query against the SuzieQ REST API.

        Args:
            table: SuzieQ table name (e.g., "bgp", "route").
            verb: Operation verb (e.g., "show", "summarize", "assert", "unique").
            params: Optional query parameters dict.

        Returns:
            Dict with keys: success, data, error.
        """
        url = f"{self.api_url}/api/v2/{table}/{verb}"
        query_params = {"access_token": self.api_key}
        if params:
            query_params.update(params)

        try:
            client = await self._get_client()
            response = await client.get(url, params=query_params)

            if response.status_code in (401, 403):
                return {
                    "success": False,
                    "data": [],
                    "error": "SuzieQ authentication failed. Verify SUZIEQ_API_KEY is correct.",
                }

            response.raise_for_status()
            data = response.json()

            # SuzieQ returns a list of records for most verbs
            if isinstance(data, list):
                return {"success": True, "data": data, "error": None}
            elif isinstance(data, dict):
                return {"success": True, "data": [data], "error": None}
            else:
                return {"success": True, "data": data, "error": None}

        except httpx.ConnectError:
            return {
                "success": False,
                "data": [],
                "error": f"SuzieQ API unreachable at {self.api_url}: connection refused or DNS failure",
            }
        except httpx.TimeoutException:
            return {
                "success": False,
                "data": [],
                "error": f"SuzieQ query timed out after {self.timeout}s. Try narrowing filters.",
            }
        except httpx.HTTPStatusError as exc:
            return {
                "success": False,
                "data": [],
                "error": f"SuzieQ API returned HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            }
        except Exception as exc:
            return {
                "success": False,
                "data": [],
                "error": f"Unexpected error querying SuzieQ: {type(exc).__name__}: {exc}",
            }

    async def query_path(
        self,
        namespace: str,
        source: str,
        destination: str,
        vrf: str = "default",
    ) -> dict[str, Any]:
        """Execute a path trace query against the SuzieQ REST API.

        Args:
            namespace: SuzieQ namespace (required).
            source: Source IP address.
            destination: Destination IP address.
            vrf: VRF name (default: "default").

        Returns:
            Dict with keys: success, data, error.
        """
        url = f"{self.api_url}/api/v2/path/show"
        query_params = {
            "access_token": self.api_key,
            "namespace": namespace,
            "src": source,
            "dest": destination,
            "vrf": vrf,
        }

        try:
            client = await self._get_client()
            response = await client.get(url, params=query_params)

            if response.status_code in (401, 403):
                return {
                    "success": False,
                    "data": [],
                    "error": "SuzieQ authentication failed. Verify SUZIEQ_API_KEY is correct.",
                }

            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return {"success": True, "data": data, "error": None}
            elif isinstance(data, dict):
                return {"success": True, "data": [data], "error": None}
            else:
                return {"success": True, "data": data, "error": None}

        except httpx.ConnectError:
            return {
                "success": False,
                "data": [],
                "error": f"SuzieQ API unreachable at {self.api_url}: connection refused or DNS failure",
            }
        except httpx.TimeoutException:
            return {
                "success": False,
                "data": [],
                "error": f"SuzieQ path query timed out after {self.timeout}s. Try narrowing the scope.",
            }
        except httpx.HTTPStatusError as exc:
            return {
                "success": False,
                "data": [],
                "error": f"SuzieQ API returned HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            }
        except Exception as exc:
            return {
                "success": False,
                "data": [],
                "error": f"Unexpected error querying SuzieQ path: {type(exc).__name__}: {exc}",
            }

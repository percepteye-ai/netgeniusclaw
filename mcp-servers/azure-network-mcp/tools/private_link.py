"""Private Endpoint tools: list private endpoints, DNS zone associations."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import PrivateEndpoint, to_json
from utils.pagination import collect_all_pages
from utils.rate_limiter import format_error_response

logger = logging.getLogger("azure-network-mcp")


def _extract_resource_group(resource_id: str) -> Optional[str]:
    if resource_id:
        parts = resource_id.split("/")
        for i, part in enumerate(parts):
            if part.lower() == "resourcegroups" and i + 1 < len(parts):
                return parts[i + 1]
    return None


def _map_private_endpoint(pe) -> PrivateEndpoint:
    subnet_id = pe.subnet.id if pe.subnet else None

    # Get the first private IP from custom DNS configs or NIC
    private_ip = None
    if pe.custom_dns_configs:
        for dns_cfg in pe.custom_dns_configs:
            if dns_cfg.ip_addresses:
                private_ip = dns_cfg.ip_addresses[0]
                break

    # Service connection details
    service_connection = None
    if pe.private_link_service_connections:
        for conn in pe.private_link_service_connections:
            service_connection = {
                "name": conn.name,
                "private_link_service_id": conn.private_link_service_id,
                "group_ids": list(conn.group_ids or []),
                "status": (
                    conn.private_link_service_connection_state.status
                    if conn.private_link_service_connection_state else None
                ),
                "description": (
                    conn.private_link_service_connection_state.description
                    if conn.private_link_service_connection_state else None
                ),
            }
            break
    elif pe.manual_private_link_service_connections:
        for conn in pe.manual_private_link_service_connections:
            service_connection = {
                "name": conn.name,
                "private_link_service_id": conn.private_link_service_id,
                "group_ids": list(conn.group_ids or []),
                "status": (
                    conn.private_link_service_connection_state.status
                    if conn.private_link_service_connection_state else None
                ),
                "approval_required": True,
            }
            break

    # Private DNS zone associations
    dns_zones = []
    if pe.private_dns_zone_configs:
        for zone_cfg in pe.private_dns_zone_configs:
            if zone_cfg.private_dns_zone_id:
                dns_zones.append(zone_cfg.private_dns_zone_id)

    return PrivateEndpoint(
        name=pe.name or "",
        id=pe.id or "",
        resource_group=_extract_resource_group(pe.id) or "",
        location=pe.location or "",
        subnet_id=subnet_id,
        private_ip=private_ip,
        service_connection=service_connection,
        private_dns_zones=dns_zones,
        provisioning_state=pe.provisioning_state,
    )


async def azure_get_private_endpoints(
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Get Private Endpoint and Private Link configurations.

    Args:
        resource_group: Resource group filter.
        subscription_id: Target subscription ID.

    Returns:
        JSON array of PrivateEndpoint objects with DNS zone associations.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        if resource_group:
            endpoints = collect_all_pages(
                client.private_endpoints.list(resource_group),
                transform=_map_private_endpoint,
            )
        else:
            endpoints = collect_all_pages(
                client.private_endpoints.list_by_subscription(),
                transform=_map_private_endpoint,
            )

        if not endpoints:
            return json.dumps({
                "private_endpoints": [],
                "message": "No Private Endpoints found.",
            }, indent=2)
        return to_json(endpoints)
    except Exception as e:
        return format_error_response(e)

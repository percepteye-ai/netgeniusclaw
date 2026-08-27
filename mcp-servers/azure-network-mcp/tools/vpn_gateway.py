"""VPN Gateway tools: gateway status, connections, BGP settings."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import VPNGateway, VPNConnection, to_json
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


def _map_connection(conn) -> VPNConnection:
    return VPNConnection(
        name=conn.name or "",
        id=conn.id or "",
        connection_type=str(conn.connection_type) if conn.connection_type else "",
        connection_status=str(conn.connection_status) if conn.connection_status else "Unknown",
        routing_weight=conn.routing_weight or 0,
        shared_key_set=bool(conn.shared_key),
        egress_bytes_transferred=conn.egress_bytes_transferred or 0,
        ingress_bytes_transferred=conn.ingress_bytes_transferred or 0,
    )


def _map_gateway(gw, connections: list[VPNConnection] = None) -> VPNGateway:
    bgp_settings = None
    if gw.bgp_settings:
        bgp_settings = {
            "asn": gw.bgp_settings.asn,
            "bgp_peering_address": gw.bgp_settings.bgp_peering_address,
            "peer_weight": gw.bgp_settings.peer_weight,
        }
        if gw.bgp_settings.bgp_peering_addresses:
            bgp_settings["peering_addresses"] = [
                {
                    "ipconfiguration_id": addr.ipconfiguration_id,
                    "default_bgp_ip_addresses": list(addr.default_bgp_ip_addresses or []),
                    "custom_bgp_ip_addresses": list(addr.custom_bgp_ip_addresses or []),
                    "tunnel_ip_addresses": list(addr.tunnel_ip_addresses or []),
                }
                for addr in gw.bgp_settings.bgp_peering_addresses
            ]

    return VPNGateway(
        name=gw.name or "",
        id=gw.id or "",
        resource_group=_extract_resource_group(gw.id) or "",
        location=gw.location or "",
        sku=gw.sku.name if gw.sku else None,
        gateway_type=str(gw.gateway_type) if gw.gateway_type else None,
        vpn_type=str(gw.vpn_type) if gw.vpn_type else None,
        active_active=bool(gw.active_active),
        bgp_settings=bgp_settings,
        connections=connections or [],
        provisioning_state=gw.provisioning_state,
    )


async def azure_get_vpn_gateway_status(
    gateway_name: Optional[str] = None,
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Get VPN Gateway configuration and connection status.

    Args:
        gateway_name: Specific gateway (omit for all gateways).
        resource_group: Resource group filter.
        subscription_id: Target subscription ID.

    Returns:
        JSON array of VPNGateway objects with connection status and BGP settings.
        Shared keys are never exposed.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        if gateway_name and resource_group:
            gw = client.virtual_network_gateways.get(resource_group, gateway_name)
            gateways = [gw]
            rg_list = [resource_group]
        else:
            # List all gateways - need to iterate resource groups
            all_gateways = []
            rg_list = []

            # List all resource groups to find gateways
            from azure.mgmt.resource import ResourceManagementClient
            res_client = azure_client_factory.get_subscription_client()
            sub_id = azure_client_factory.resolve_subscription_id(subscription_id)

            # Use network client to list via known pattern
            # Virtual network gateways don't have a list_all(), must iterate by resource group
            # Use a broader approach: list all via REST-like iteration
            try:
                from azure.mgmt.resource import ResourceManagementClient
                from azure.identity import DefaultAzureCredential
                cred = azure_client_factory._credential
                rm_client = ResourceManagementClient(cred, sub_id)
                for rg in rm_client.resource_groups.list():
                    try:
                        for gw in client.virtual_network_gateways.list(rg.name):
                            all_gateways.append(gw)
                            rg_list.append(rg.name)
                    except Exception:
                        continue
            except Exception:
                # Fallback: return empty if we can't enumerate
                return json.dumps({
                    "gateways": [],
                    "message": "Could not enumerate VPN gateways. Provide gateway_name and resource_group for specific lookup.",
                }, indent=2)

            gateways = all_gateways

        results = []
        for i, gw in enumerate(gateways):
            rg = _extract_resource_group(gw.id) or (rg_list[i] if i < len(rg_list) else "")
            # Get connections for this gateway's resource group
            connections = []
            try:
                for conn in client.virtual_network_gateway_connections.list(rg):
                    connections.append(_map_connection(conn))
            except Exception:
                pass

            results.append(_map_gateway(gw, connections))

        if not results:
            return json.dumps({
                "gateways": [],
                "message": "No VPN Gateways found in this subscription.",
            }, indent=2)
        return to_json(results)
    except Exception as e:
        return format_error_response(e)

"""VNet topology tools: list, details, peerings."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import VNet, Subnet, VNetPeering, to_json
from utils.pagination import collect_all_pages
from utils.rate_limiter import format_error_response

logger = logging.getLogger("azure-network-mcp")


def _extract_name_from_id(resource_id: str) -> Optional[str]:
    """Extract resource name from an Azure resource ID."""
    if resource_id:
        parts = resource_id.split("/")
        if parts:
            return parts[-1]
    return None


def _extract_resource_group(resource_id: str) -> Optional[str]:
    """Extract resource group name from an Azure resource ID."""
    if resource_id:
        parts = resource_id.split("/")
        for i, part in enumerate(parts):
            if part.lower() == "resourcegroups" and i + 1 < len(parts):
                return parts[i + 1]
    return None


def _map_subnet(subnet) -> Subnet:
    """Map Azure SDK subnet object to Subnet response model."""
    nsg_id = subnet.network_security_group.id if subnet.network_security_group else None
    rt_id = subnet.route_table.id if subnet.route_table else None

    delegations = []
    if subnet.delegations:
        delegations = [d.service_name for d in subnet.delegations if d.service_name]

    service_endpoints = []
    if subnet.service_endpoints:
        service_endpoints = [se.service for se in subnet.service_endpoints if se.service]

    private_endpoints = []
    if subnet.private_endpoints:
        private_endpoints = [pe.id for pe in subnet.private_endpoints if pe.id]

    return Subnet(
        name=subnet.name,
        id=subnet.id or "",
        address_prefix=subnet.address_prefix or (
            subnet.address_prefixes[0] if subnet.address_prefixes else ""
        ),
        nsg_id=nsg_id,
        nsg_name=_extract_name_from_id(nsg_id) if nsg_id else None,
        route_table_id=rt_id,
        route_table_name=_extract_name_from_id(rt_id) if rt_id else None,
        delegations=delegations,
        service_endpoints=service_endpoints,
        private_endpoints=private_endpoints,
        provisioning_state=subnet.provisioning_state,
    )


def _map_peering(peering) -> VNetPeering:
    """Map Azure SDK peering object to VNetPeering response model."""
    remote_vnet_id = ""
    if peering.remote_virtual_network:
        remote_vnet_id = peering.remote_virtual_network.id or ""

    return VNetPeering(
        name=peering.name,
        id=peering.id or "",
        remote_vnet_id=remote_vnet_id,
        peering_state=str(peering.peering_state) if peering.peering_state else "Unknown",
        allow_vnet_access=bool(peering.allow_virtual_network_access),
        allow_forwarded_traffic=bool(peering.allow_forwarded_traffic),
        allow_gateway_transit=bool(peering.allow_gateway_transit),
        use_remote_gateways=bool(peering.use_remote_gateways),
    )


def _map_vnet_summary(vnet) -> VNet:
    """Map Azure SDK VNet object to VNet summary response model."""
    address_space = []
    if vnet.address_space and vnet.address_space.address_prefixes:
        address_space = list(vnet.address_space.address_prefixes)

    subnet_count = len(vnet.subnets) if vnet.subnets else 0
    peering_count = len(vnet.virtual_network_peerings) if vnet.virtual_network_peerings else 0

    return VNet(
        name=vnet.name,
        id=vnet.id or "",
        resource_group=_extract_resource_group(vnet.id) or "",
        location=vnet.location or "",
        address_space=address_space,
        provisioning_state=vnet.provisioning_state,
        tags=dict(vnet.tags) if vnet.tags else {},
        subnet_count=subnet_count,
        peering_count=peering_count,
    )


async def azure_list_vnets(subscription_id: Optional[str] = None) -> str:
    """List all Virtual Networks in a subscription.

    Args:
        subscription_id: Target subscription ID (defaults to AZURE_SUBSCRIPTION_ID).

    Returns:
        JSON array of VNet objects with name, location, address_space, subnet_count,
        peering_count, provisioning_state, and tags.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)
        vnets = collect_all_pages(
            client.virtual_networks.list_all(),
            transform=_map_vnet_summary,
        )
        if not vnets:
            return json.dumps({
                "vnets": [],
                "message": "No Virtual Networks found in this subscription.",
            }, indent=2)
        return to_json(vnets)
    except Exception as e:
        return format_error_response(e)


async def azure_get_vnet_details(
    vnet_name: Optional[str] = None,
    resource_group: Optional[str] = None,
    resource_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Get detailed VNet configuration including subnets, peerings, and DNS settings.

    Provide either (vnet_name + resource_group) or resource_id.

    Args:
        vnet_name: VNet name (required if resource_id not provided).
        resource_group: Resource group (required if resource_id not provided).
        resource_id: Full Azure resource ID (alternative to name+RG).
        subscription_id: Target subscription ID.

    Returns:
        Full VNet object with subnets (NSG/route table associations), peerings, and DNS settings.
    """
    try:
        if resource_id:
            vnet_name = _extract_name_from_id(resource_id)
            resource_group = _extract_resource_group(resource_id)
            # Extract subscription from resource ID if not provided
            if not subscription_id:
                parts = resource_id.split("/")
                for i, part in enumerate(parts):
                    if part.lower() == "subscriptions" and i + 1 < len(parts):
                        subscription_id = parts[i + 1]
                        break

        if not vnet_name or not resource_group:
            return json.dumps({
                "error": {
                    "code": "ValidationError",
                    "message": "Provide either (vnet_name + resource_group) or resource_id.",
                }
            }, indent=2)

        client = azure_client_factory.get_network_client(subscription_id)
        vnet = client.virtual_networks.get(resource_group, vnet_name)

        address_space = []
        if vnet.address_space and vnet.address_space.address_prefixes:
            address_space = list(vnet.address_space.address_prefixes)

        subnets = [_map_subnet(s) for s in (vnet.subnets or [])]
        peerings = [_map_peering(p) for p in (vnet.virtual_network_peerings or [])]

        dns_servers = []
        if vnet.dhcp_options and vnet.dhcp_options.dns_servers:
            dns_servers = list(vnet.dhcp_options.dns_servers)

        result = VNet(
            name=vnet.name,
            id=vnet.id or "",
            resource_group=_extract_resource_group(vnet.id) or resource_group,
            location=vnet.location or "",
            address_space=address_space,
            subnets=subnets,
            peerings=peerings,
            dns_servers=dns_servers,
            provisioning_state=vnet.provisioning_state,
            tags=dict(vnet.tags) if vnet.tags else {},
            subnet_count=len(subnets),
            peering_count=len(peerings),
        )
        return to_json(result)
    except Exception as e:
        return format_error_response(e)


async def azure_get_vnet_peerings(
    vnet_name: str,
    resource_group: str,
    subscription_id: Optional[str] = None,
) -> str:
    """Get VNet peering status for a specific VNet.

    Args:
        vnet_name: VNet name.
        resource_group: Resource group name.
        subscription_id: Target subscription ID.

    Returns:
        JSON array of VNetPeering objects with peering state and traffic forwarding settings.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)
        peerings = collect_all_pages(
            client.virtual_network_peerings.list(resource_group, vnet_name),
            transform=_map_peering,
        )
        if not peerings:
            return json.dumps({
                "peerings": [],
                "message": f"No peerings found for VNet '{vnet_name}' in resource group '{resource_group}'.",
            }, indent=2)
        return to_json(peerings)
    except Exception as e:
        return format_error_response(e)

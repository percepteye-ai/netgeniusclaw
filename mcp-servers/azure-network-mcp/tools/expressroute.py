"""ExpressRoute tools: circuit status and route tables."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import ExpressRouteCircuit, ExpressRoutePeering, to_json
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


def _map_peering(peering) -> ExpressRoutePeering:
    return ExpressRoutePeering(
        name=peering.name or "",
        peering_type=str(peering.peering_type) if peering.peering_type else "",
        state=str(peering.state) if peering.state else "Unknown",
        primary_peer_address_prefix=peering.primary_peer_address_prefix,
        secondary_peer_address_prefix=peering.secondary_peer_address_prefix,
        vlan_id=peering.vlan_id,
        azure_asn=peering.azure_asn,
        peer_asn=peering.peer_asn,
    )


def _map_circuit(circuit) -> ExpressRouteCircuit:
    sku_name = None
    sku_tier = None
    sku_family = None
    if circuit.sku:
        sku_name = circuit.sku.name
        sku_tier = str(circuit.sku.tier) if circuit.sku.tier else None
        sku_family = str(circuit.sku.family) if circuit.sku.family else None

    peerings = []
    if circuit.peerings:
        peerings = [_map_peering(p) for p in circuit.peerings]

    return ExpressRouteCircuit(
        name=circuit.name or "",
        id=circuit.id or "",
        resource_group=_extract_resource_group(circuit.id) or "",
        location=circuit.location or "",
        sku_name=sku_name,
        sku_tier=sku_tier,
        sku_family=sku_family,
        bandwidth_in_mbps=circuit.bandwidth_in_mbps,
        peering_location=circuit.peering_location,
        service_provider_name=(
            circuit.service_provider_properties.service_provider_name
            if circuit.service_provider_properties else None
        ),
        provisioning_state=circuit.provisioning_state,
        circuit_provisioning_state=circuit.circuit_provisioning_state,
        peerings=peerings,
    )


async def azure_get_expressroute_status(
    circuit_name: Optional[str] = None,
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Get ExpressRoute circuit status and peering details.

    Args:
        circuit_name: Specific circuit (omit for all circuits).
        resource_group: Resource group filter.
        subscription_id: Target subscription ID.

    Returns:
        JSON array of ExpressRouteCircuit objects with peering configuration.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        if circuit_name and resource_group:
            circuit = client.express_route_circuits.get(resource_group, circuit_name)
            circuits = [_map_circuit(circuit)]
        else:
            circuits = collect_all_pages(
                client.express_route_circuits.list_all(),
                transform=_map_circuit,
            )

        if not circuits:
            return json.dumps({
                "circuits": [],
                "message": "No ExpressRoute circuits found in this subscription.",
            }, indent=2)
        return to_json(circuits)
    except Exception as e:
        return format_error_response(e)


async def azure_get_expressroute_routes(
    circuit_name: str,
    resource_group: str,
    peering_name: str,
    subscription_id: Optional[str] = None,
) -> str:
    """Get route table for an ExpressRoute peering.

    Args:
        circuit_name: Circuit name.
        resource_group: Resource group name.
        peering_name: Peering type (AzurePrivatePeering/MicrosoftPeering).
        subscription_id: Target subscription ID.

    Returns:
        JSON array of learned routes (prefix, next_hop, as_path, origin).
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        # List routes table for primary device (devicePath = primary)
        poller = client.express_route_circuits.begin_list_routes_table(
            resource_group, circuit_name, peering_name, "primary"
        )
        result = poller.result()

        routes = []
        if result and result.value:
            for route in result.value:
                routes.append({
                    "network": route.network,
                    "next_hop": route.next_hop,
                    "local_pref": route.local_pref,
                    "weight": route.weight,
                    "path": route.path,
                })

        return json.dumps({
            "circuit_name": circuit_name,
            "peering_name": peering_name,
            "device_path": "primary",
            "routes": routes,
            "total_routes": len(routes),
        }, indent=2, default=str)
    except Exception as e:
        return format_error_response(e)

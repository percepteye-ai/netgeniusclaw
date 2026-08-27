"""Route Table tools: list route tables, get routes, effective routes."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import RouteTable, Route, to_json
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


def _map_route_table(rt) -> RouteTable:
    routes = []
    if rt.routes:
        for r in rt.routes:
            routes.append(Route(
                name=r.name or "",
                address_prefix=r.address_prefix or "",
                next_hop_type=str(r.next_hop_type) if r.next_hop_type else "",
                next_hop_ip=r.next_hop_ip_address,
            ))

    associated_subnets = []
    if rt.subnets:
        associated_subnets = [s.id for s in rt.subnets if s.id]

    return RouteTable(
        name=rt.name or "",
        id=rt.id or "",
        resource_group=_extract_resource_group(rt.id) or "",
        location=rt.location or "",
        routes=routes,
        associated_subnets=associated_subnets,
        disable_bgp_route_propagation=bool(rt.disable_bgp_route_propagation),
    )


async def azure_get_route_tables(
    route_table_name: Optional[str] = None,
    resource_group: Optional[str] = None,
    nic_name: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Get route tables and effective routes.

    Args:
        route_table_name: Specific route table (omit for all).
        resource_group: Resource group filter.
        nic_name: NIC name for effective routes.
        subscription_id: Target subscription ID.

    Returns:
        Route table configuration with UDRs and subnet associations.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        # If NIC name is provided, get effective routes
        if nic_name and resource_group:
            poller = client.network_interfaces.begin_get_effective_route_table(
                resource_group, nic_name
            )
            result = poller.result()

            effective_routes = []
            if result and result.value:
                for route in result.value:
                    effective_routes.append({
                        "source": str(route.source) if route.source else "",
                        "state": str(route.state) if route.state else "",
                        "address_prefix": list(route.address_prefix or []),
                        "next_hop_type": str(route.next_hop_type) if route.next_hop_type else "",
                        "next_hop_ip": list(route.next_hop_ip_address or []),
                    })

            return json.dumps({
                "nic_name": nic_name,
                "resource_group": resource_group,
                "effective_routes": effective_routes,
                "total_routes": len(effective_routes),
            }, indent=2, default=str)

        # Get static route tables
        if route_table_name and resource_group:
            rt = client.route_tables.get(resource_group, route_table_name)
            return to_json(_map_route_table(rt))
        else:
            route_tables = collect_all_pages(
                client.route_tables.list_all(),
                transform=_map_route_table,
            )
            if not route_tables:
                return json.dumps({
                    "route_tables": [],
                    "message": "No Route Tables found in this subscription.",
                }, indent=2)
            return to_json(route_tables)
    except Exception as e:
        return format_error_response(e)

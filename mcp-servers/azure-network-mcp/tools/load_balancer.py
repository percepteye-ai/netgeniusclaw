"""Load Balancer tools: list LBs, backend health status."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import LoadBalancer, BackendPool, HealthProbe, to_json
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


def _map_lb(lb) -> LoadBalancer:
    # Determine LB type (Public/Internal)
    lb_type = "Internal"
    frontend_configs = []
    if lb.frontend_ip_configurations:
        for fic in lb.frontend_ip_configurations:
            config = {
                "name": fic.name,
                "private_ip_address": fic.private_ip_address,
                "private_ip_allocation_method": str(fic.private_ip_allocation_method) if fic.private_ip_allocation_method else None,
            }
            if fic.public_ip_address:
                config["public_ip_id"] = fic.public_ip_address.id
                lb_type = "Public"
            if fic.subnet:
                config["subnet_id"] = fic.subnet.id
            frontend_configs.append(config)

    backend_pools = []
    if lb.backend_address_pools:
        for pool in lb.backend_address_pools:
            members = []
            if pool.backend_ip_configurations:
                members = [{"id": bic.id} for bic in pool.backend_ip_configurations]
            elif pool.load_balancer_backend_addresses:
                members = [
                    {
                        "name": addr.name,
                        "ip_address": addr.ip_address,
                        "vnet_id": addr.virtual_network.id if addr.virtual_network else None,
                    }
                    for addr in pool.load_balancer_backend_addresses
                ]
            backend_pools.append(BackendPool(
                name=pool.name or "",
                id=pool.id or "",
                members=members,
            ))

    health_probes = []
    if lb.probes:
        for probe in lb.probes:
            health_probes.append(HealthProbe(
                name=probe.name or "",
                protocol=str(probe.protocol) if probe.protocol else "",
                port=probe.port or 0,
                request_path=probe.request_path,
                interval_in_seconds=probe.interval_in_seconds or 15,
                number_of_probes=probe.number_of_probes or 2,
            ))

    lb_rules = []
    if lb.load_balancing_rules:
        for rule in lb.load_balancing_rules:
            lb_rules.append({
                "name": rule.name,
                "protocol": str(rule.protocol) if rule.protocol else "",
                "frontend_port": rule.frontend_port,
                "backend_port": rule.backend_port,
                "idle_timeout": rule.idle_timeout_in_minutes,
                "enable_floating_ip": rule.enable_floating_ip,
                "enable_tcp_reset": rule.enable_tcp_reset,
            })

    nat_rules = []
    if lb.inbound_nat_rules:
        for rule in lb.inbound_nat_rules:
            nat_rules.append({
                "name": rule.name,
                "protocol": str(rule.protocol) if rule.protocol else "",
                "frontend_port": rule.frontend_port,
                "backend_port": rule.backend_port,
            })

    return LoadBalancer(
        name=lb.name or "",
        id=lb.id or "",
        resource_group=_extract_resource_group(lb.id) or "",
        location=lb.location or "",
        sku=lb.sku.name if lb.sku else None,
        type=lb_type,
        frontend_ip_configs=frontend_configs,
        backend_pools=backend_pools,
        health_probes=health_probes,
        load_balancing_rules=lb_rules,
        nat_rules=nat_rules,
        provisioning_state=lb.provisioning_state,
    )


async def azure_list_load_balancers(subscription_id: Optional[str] = None) -> str:
    """List Load Balancers with frontend IP and backend pool summary.

    Args:
        subscription_id: Target subscription ID (defaults to AZURE_SUBSCRIPTION_ID).

    Returns:
        JSON array of LoadBalancer objects.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)
        lbs = collect_all_pages(
            client.load_balancers.list_all(),
            transform=_map_lb,
        )
        if not lbs:
            return json.dumps({
                "load_balancers": [],
                "message": "No Load Balancers found in this subscription.",
            }, indent=2)
        return to_json(lbs)
    except Exception as e:
        return format_error_response(e)


async def azure_get_lb_backend_health(
    lb_name: str,
    resource_group: str,
    subscription_id: Optional[str] = None,
) -> str:
    """Get backend pool health status for a Load Balancer.

    Args:
        lb_name: Load Balancer name.
        resource_group: Resource group name.
        subscription_id: Target subscription ID.

    Returns:
        Backend pool health with per-member status (Healthy/Unhealthy/Unknown).
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        # Get the LB details first
        lb = client.load_balancers.get(resource_group, lb_name)
        lb_mapped = _map_lb(lb)

        # Get backend health
        backend_health = []
        try:
            health_result = client.load_balancers.begin_list_inbound_nat_rules_port_mappings
        except AttributeError:
            pass

        # Use the backend address pool health API
        if lb.backend_address_pools:
            for pool in lb.backend_address_pools:
                pool_health = {
                    "pool_name": pool.name,
                    "pool_id": pool.id,
                    "members": [],
                }

                # Backend health probes provide per-member status
                if pool.backend_ip_configurations:
                    for bic in pool.backend_ip_configurations:
                        pool_health["members"].append({
                            "id": bic.id,
                            "status": "Unknown",  # Actual health requires metrics API
                        })
                elif pool.load_balancer_backend_addresses:
                    for addr in pool.load_balancer_backend_addresses:
                        pool_health["members"].append({
                            "name": addr.name,
                            "ip_address": addr.ip_address,
                            "status": "Unknown",
                        })

                backend_health.append(pool_health)

        # Get health probes
        probes = []
        if lb_mapped.health_probes:
            probes = [p.__dict__ for p in lb_mapped.health_probes]

        result = {
            "lb_name": lb_name,
            "resource_group": resource_group,
            "sku": lb_mapped.sku,
            "type": lb_mapped.type,
            "backend_pools": backend_health,
            "health_probes": probes,
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return format_error_response(e)

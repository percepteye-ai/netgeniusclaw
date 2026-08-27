"""Application Gateway and Front Door tools: config, WAF, backend health."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
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


def _map_app_gateway(gw) -> dict:
    """Map Application Gateway to a response dict."""
    # Listeners
    listeners = []
    if gw.http_listeners:
        for listener in gw.http_listeners:
            listeners.append({
                "name": listener.name,
                "protocol": str(listener.protocol) if listener.protocol else "",
                "frontend_port": listener.frontend_port.id.split("/")[-1] if listener.frontend_port else None,
                "host_name": listener.host_name,
                "host_names": list(listener.host_names or []) if hasattr(listener, "host_names") else [],
                "require_server_name_indication": getattr(listener, "require_server_name_indication", False),
            })

    # Routing rules
    routing_rules = []
    if gw.request_routing_rules:
        for rule in gw.request_routing_rules:
            routing_rules.append({
                "name": rule.name,
                "rule_type": str(rule.rule_type) if rule.rule_type else "",
                "priority": rule.priority,
                "http_listener": rule.http_listener.id.split("/")[-1] if rule.http_listener else None,
                "backend_address_pool": (
                    rule.backend_address_pool.id.split("/")[-1]
                    if rule.backend_address_pool else None
                ),
                "backend_http_settings": (
                    rule.backend_http_settings.id.split("/")[-1]
                    if rule.backend_http_settings else None
                ),
            })

    # WAF configuration
    waf_config = None
    if gw.web_application_firewall_configuration:
        waf = gw.web_application_firewall_configuration
        disabled_rules = []
        if waf.disabled_rule_groups:
            for drg in waf.disabled_rule_groups:
                disabled_rules.append({
                    "rule_group_name": drg.rule_group_name,
                    "rules": list(drg.rules or []),
                })
        waf_config = {
            "enabled": waf.enabled,
            "firewall_mode": str(waf.firewall_mode) if waf.firewall_mode else "",
            "rule_set_type": waf.rule_set_type,
            "rule_set_version": waf.rule_set_version,
            "max_request_body_size_in_kb": waf.max_request_body_size_in_kb,
            "file_upload_limit_in_mb": waf.file_upload_limit_in_mb,
            "disabled_rule_groups": disabled_rules,
        }

    # Backend address pools
    backend_pools = []
    if gw.backend_address_pools:
        for pool in gw.backend_address_pools:
            addresses = []
            if pool.backend_addresses:
                for addr in pool.backend_addresses:
                    addresses.append({
                        "fqdn": addr.fqdn,
                        "ip_address": addr.ip_address,
                    })
            backend_pools.append({
                "name": pool.name,
                "addresses": addresses,
            })

    return {
        "name": gw.name,
        "id": gw.id,
        "resource_group": _extract_resource_group(gw.id),
        "location": gw.location,
        "sku": {
            "name": gw.sku.name if gw.sku else None,
            "tier": str(gw.sku.tier) if gw.sku and gw.sku.tier else None,
            "capacity": gw.sku.capacity if gw.sku else None,
        },
        "provisioning_state": gw.provisioning_state,
        "operational_state": str(gw.operational_state) if gw.operational_state else None,
        "listeners": listeners,
        "routing_rules": routing_rules,
        "backend_pools": backend_pools,
        "waf_configuration": waf_config,
    }


async def azure_get_app_gateway_health(
    gateway_name: Optional[str] = None,
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Get Application Gateway configuration and backend health.

    Args:
        gateway_name: Specific gateway (omit for all).
        resource_group: Resource group filter.
        subscription_id: Target subscription ID.

    Returns:
        Application Gateway/Front Door config with WAF status and backend health.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        results = {"application_gateways": [], "front_doors": []}

        # Application Gateways
        if gateway_name and resource_group:
            gw = client.application_gateways.get(resource_group, gateway_name)
            gw_data = _map_app_gateway(gw)

            # Try to get backend health
            try:
                poller = client.application_gateways.begin_backend_health(
                    resource_group, gateway_name
                )
                health = poller.result()
                backend_health = []
                if health.backend_address_pools:
                    for pool_health in health.backend_address_pools:
                        pool_data = {
                            "pool": pool_health.backend_address_pool.id.split("/")[-1] if pool_health.backend_address_pool else "unknown",
                            "servers": [],
                        }
                        if pool_health.backend_http_settings_collection:
                            for settings_health in pool_health.backend_http_settings_collection:
                                if settings_health.servers:
                                    for server in settings_health.servers:
                                        pool_data["servers"].append({
                                            "address": server.address,
                                            "health": str(server.health) if server.health else "Unknown",
                                            "health_probe_log": server.health_probe_log,
                                        })
                        backend_health.append(pool_data)
                gw_data["backend_health"] = backend_health
            except Exception as health_err:
                gw_data["backend_health_error"] = str(health_err)

            results["application_gateways"].append(gw_data)
        else:
            gateways = collect_all_pages(client.application_gateways.list_all())
            for gw in gateways:
                results["application_gateways"].append(_map_app_gateway(gw))

        # Front Door (via azure-mgmt-frontdoor)
        try:
            from azure.mgmt.frontdoor import FrontDoorManagementClient
            sub_id = azure_client_factory.resolve_subscription_id(subscription_id)
            fd_client = FrontDoorManagementClient(
                credential=azure_client_factory._credential,
                subscription_id=sub_id,
            )
            for fd in fd_client.front_doors.list():
                fd_data = {
                    "name": fd.name,
                    "id": fd.id,
                    "resource_group": _extract_resource_group(fd.id),
                    "frontend_endpoints": [],
                    "routing_rules": [],
                    "backend_pools": [],
                    "health_probe_settings": [],
                }

                if fd.frontend_endpoints:
                    for ep in fd.frontend_endpoints:
                        fd_data["frontend_endpoints"].append({
                            "name": ep.name,
                            "host_name": ep.host_name,
                            "session_affinity_enabled_state": str(ep.session_affinity_enabled_state) if ep.session_affinity_enabled_state else None,
                            "web_application_firewall_policy_link": (
                                ep.web_application_firewall_policy_link.id
                                if ep.web_application_firewall_policy_link else None
                            ),
                        })

                if fd.routing_rules:
                    for rr in fd.routing_rules:
                        fd_data["routing_rules"].append({
                            "name": rr.name,
                            "accepted_protocols": [str(p) for p in (rr.accepted_protocols or [])],
                            "patterns_to_match": list(rr.patterns_to_match or []),
                            "enabled_state": str(rr.enabled_state) if rr.enabled_state else None,
                        })

                if fd.backend_pools:
                    for pool in fd.backend_pools:
                        origins = []
                        if pool.backends:
                            for backend in pool.backends:
                                origins.append({
                                    "address": backend.address,
                                    "http_port": backend.http_port,
                                    "https_port": backend.https_port,
                                    "enabled_state": str(backend.enabled_state) if backend.enabled_state else None,
                                    "priority": backend.priority,
                                    "weight": backend.weight,
                                })
                        fd_data["backend_pools"].append({
                            "name": pool.name,
                            "origins": origins,
                        })

                results["front_doors"].append(fd_data)
        except ImportError:
            results["front_door_note"] = "azure-mgmt-frontdoor not installed. Install to enable Front Door queries."
        except Exception as fd_err:
            results["front_door_error"] = str(fd_err)

        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        return format_error_response(e)

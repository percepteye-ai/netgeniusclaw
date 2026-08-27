"""Azure Firewall tools: list firewalls, get firewall policy details."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import (
    AzureFirewall, FirewallPolicy, RuleCollectionGroup, RuleCollection, to_json,
)
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


def _extract_name_from_id(resource_id: str) -> Optional[str]:
    if resource_id:
        parts = resource_id.split("/")
        if parts:
            return parts[-1]
    return None


def _map_firewall(fw) -> AzureFirewall:
    ip_configs = []
    if fw.ip_configurations:
        for ip_cfg in fw.ip_configurations:
            config = {
                "name": ip_cfg.name,
                "private_ip_address": ip_cfg.private_ip_address,
            }
            if ip_cfg.public_ip_address:
                config["public_ip_id"] = ip_cfg.public_ip_address.id
            if ip_cfg.subnet:
                config["subnet_id"] = ip_cfg.subnet.id
            ip_configs.append(config)

    policy_id = None
    if fw.firewall_policy:
        policy_id = fw.firewall_policy.id

    return AzureFirewall(
        name=fw.name or "",
        id=fw.id or "",
        resource_group=_extract_resource_group(fw.id) or "",
        location=fw.location or "",
        sku_tier=fw.sku.tier if fw.sku else None,
        provisioning_state=fw.provisioning_state,
        firewall_policy_id=policy_id,
        threat_intel_mode=str(fw.threat_intel_mode) if fw.threat_intel_mode else None,
        ip_configurations=ip_configs,
    )


async def azure_list_firewalls(subscription_id: Optional[str] = None) -> str:
    """List Azure Firewalls and associated policies.

    Args:
        subscription_id: Target subscription ID (defaults to AZURE_SUBSCRIPTION_ID).

    Returns:
        JSON array of AzureFirewall objects with SKU and policy association.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)
        firewalls = collect_all_pages(
            client.azure_firewalls.list_all(),
            transform=_map_firewall,
        )
        if not firewalls:
            return json.dumps({
                "firewalls": [],
                "message": "No Azure Firewalls found in this subscription.",
            }, indent=2)

        # Add informational note for firewalls with classic rules (no policy)
        result = []
        for fw in firewalls:
            fw_dict = fw.__dict__.copy()
            if not fw.firewall_policy_id:
                fw_dict["note"] = (
                    "This firewall uses classic rules (no Firewall Policy). "
                    "Use azure_get_firewall_policy for policy-based firewalls."
                )
            result.append(fw_dict)

        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return format_error_response(e)


def _map_rule_collection(rc) -> RuleCollection:
    """Map a firewall policy rule collection."""
    rules = []
    rule_type = "Unknown"

    # Determine rule type from the collection type
    rc_type = type(rc).__name__
    if "Network" in rc_type:
        rule_type = "Network"
        if hasattr(rc, "rules") and rc.rules:
            for r in rc.rules:
                rules.append({
                    "name": r.name,
                    "rule_type": "Network",
                    "ip_protocols": [str(p) for p in (r.ip_protocols or [])],
                    "source_addresses": list(r.source_addresses or []),
                    "destination_addresses": list(r.destination_addresses or []),
                    "destination_ports": list(r.destination_ports or []),
                    "source_ip_groups": list(r.source_ip_groups or []) if hasattr(r, "source_ip_groups") else [],
                    "destination_ip_groups": list(r.destination_ip_groups or []) if hasattr(r, "destination_ip_groups") else [],
                    "destination_fqdns": list(r.destination_fqdns or []) if hasattr(r, "destination_fqdns") else [],
                })
    elif "Application" in rc_type:
        rule_type = "Application"
        if hasattr(rc, "rules") and rc.rules:
            for r in rc.rules:
                protocols = []
                if hasattr(r, "protocols") and r.protocols:
                    protocols = [{"type": str(p.protocol_type), "port": p.port} for p in r.protocols]
                rules.append({
                    "name": r.name,
                    "rule_type": "Application",
                    "source_addresses": list(r.source_addresses or []),
                    "target_fqdns": list(r.target_fqdns or []) if hasattr(r, "target_fqdns") else [],
                    "protocols": protocols,
                    "fqdn_tags": list(r.fqdn_tags or []) if hasattr(r, "fqdn_tags") else [],
                    "web_categories": list(r.web_categories or []) if hasattr(r, "web_categories") else [],
                })
    elif "Nat" in rc_type or "DNAT" in rc_type:
        rule_type = "NAT"
        if hasattr(rc, "rules") and rc.rules:
            for r in rc.rules:
                rules.append({
                    "name": r.name,
                    "rule_type": "NAT",
                    "source_addresses": list(r.source_addresses or []),
                    "destination_addresses": list(r.destination_addresses or []),
                    "destination_ports": list(r.destination_ports or []),
                    "translated_address": getattr(r, "translated_address", None),
                    "translated_port": getattr(r, "translated_port", None),
                    "ip_protocols": [str(p) for p in (r.ip_protocols or [])] if hasattr(r, "ip_protocols") else [],
                })

    action_type = ""
    if hasattr(rc, "action") and rc.action:
        action_type = str(rc.action.type) if rc.action.type else ""

    return RuleCollection(
        name=rc.name or "",
        priority=rc.priority or 0,
        action_type=action_type,
        rule_type=rule_type,
        rules=rules,
    )


async def azure_get_firewall_policy(
    policy_name: str,
    resource_group: str,
    subscription_id: Optional[str] = None,
) -> str:
    """Get firewall policy details including rule collections and threat intelligence.

    Args:
        policy_name: Firewall policy name.
        resource_group: Resource group name.
        subscription_id: Target subscription ID.

    Returns:
        FirewallPolicy object with rule collection groups and threat intel config.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)
        policy = client.firewall_policies.get(resource_group, policy_name)

        # Get rule collection groups
        rcgs = collect_all_pages(
            client.firewall_policy_rule_collection_groups.list(resource_group, policy_name)
        )

        rule_collection_groups = []
        for rcg in rcgs:
            collections = []
            if rcg.rule_collections:
                for rc in rcg.rule_collections:
                    collections.append(_map_rule_collection(rc))

            rule_collection_groups.append(RuleCollectionGroup(
                name=rcg.name or "",
                priority=rcg.priority or 0,
                rule_collections=collections,
            ))

        # Sort by priority
        rule_collection_groups.sort(key=lambda g: g.priority)

        intrusion_detection_mode = None
        if policy.intrusion_detection and policy.intrusion_detection.mode:
            intrusion_detection_mode = str(policy.intrusion_detection.mode)

        result = FirewallPolicy(
            name=policy.name or "",
            id=policy.id or "",
            threat_intelligence_mode=(
                str(policy.threat_intel_mode) if policy.threat_intel_mode else None
            ),
            dns_proxy_enabled=bool(
                policy.dns_settings and policy.dns_settings.enable_proxy
            ),
            intrusion_detection_mode=intrusion_detection_mode,
            rule_collection_groups=rule_collection_groups,
        )
        return to_json(result)
    except Exception as e:
        return format_error_response(e)

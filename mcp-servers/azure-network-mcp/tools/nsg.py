"""NSG tools: list, rules, effective security rules, compliance audit."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import NetworkSecurityGroup, SecurityRule, to_json
from compliance.cis_azure import run_all_checks
from utils.pagination import collect_all_pages
from utils.rate_limiter import format_error_response

logger = logging.getLogger("azure-network-mcp")


def _extract_resource_group(resource_id: str) -> Optional[str]:
    """Extract resource group name from an Azure resource ID."""
    if resource_id:
        parts = resource_id.split("/")
        for i, part in enumerate(parts):
            if part.lower() == "resourcegroups" and i + 1 < len(parts):
                return parts[i + 1]
    return None


def _map_security_rule(rule) -> SecurityRule:
    """Map Azure SDK security rule to SecurityRule model."""
    return SecurityRule(
        name=rule.name or "",
        priority=rule.priority or 0,
        direction=str(rule.direction) if rule.direction else "",
        access=str(rule.access) if rule.access else "",
        protocol=str(rule.protocol) if rule.protocol else "",
        source_address_prefix=rule.source_address_prefix,
        source_address_prefixes=list(rule.source_address_prefixes or []),
        source_port_range=rule.source_port_range,
        destination_address_prefix=rule.destination_address_prefix,
        destination_address_prefixes=list(rule.destination_address_prefixes or []),
        destination_port_range=rule.destination_port_range,
        description=rule.description,
    )


def _map_nsg(nsg) -> NetworkSecurityGroup:
    """Map Azure SDK NSG object to NetworkSecurityGroup model."""
    security_rules = sorted(
        [_map_security_rule(r) for r in (nsg.security_rules or [])],
        key=lambda r: r.priority,
    )
    default_rules = sorted(
        [_map_security_rule(r) for r in (nsg.default_security_rules or [])],
        key=lambda r: r.priority,
    )

    associated_subnets = []
    if nsg.subnets:
        associated_subnets = [s.id for s in nsg.subnets if s.id]

    associated_nics = []
    if nsg.network_interfaces:
        associated_nics = [n.id for n in nsg.network_interfaces if n.id]

    is_orphaned = len(associated_subnets) == 0 and len(associated_nics) == 0

    return NetworkSecurityGroup(
        name=nsg.name or "",
        id=nsg.id or "",
        resource_group=_extract_resource_group(nsg.id) or "",
        location=nsg.location or "",
        security_rules=security_rules,
        default_rules=default_rules,
        associated_subnets=associated_subnets,
        associated_nics=associated_nics,
        is_orphaned=is_orphaned,
        tags=dict(nsg.tags) if nsg.tags else {},
    )


async def azure_list_nsgs(subscription_id: Optional[str] = None) -> str:
    """List all Network Security Groups in a subscription.

    Args:
        subscription_id: Target subscription ID (defaults to AZURE_SUBSCRIPTION_ID).

    Returns:
        JSON array of NSG objects with association info and orphaned status.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)
        nsgs = collect_all_pages(
            client.network_security_groups.list_all(),
            transform=_map_nsg,
        )
        if not nsgs:
            return json.dumps({
                "nsgs": [],
                "message": "No Network Security Groups found in this subscription.",
            }, indent=2)
        return to_json(nsgs)
    except Exception as e:
        return format_error_response(e)


async def azure_get_nsg_rules(
    nsg_name: str,
    resource_group: str,
    subscription_id: Optional[str] = None,
) -> str:
    """Get all rules for a specific NSG, sorted by priority.

    Args:
        nsg_name: NSG name.
        resource_group: Resource group name.
        subscription_id: Target subscription ID.

    Returns:
        JSON object with sorted inbound and outbound rules (custom + default).
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)
        nsg = client.network_security_groups.get(resource_group, nsg_name)

        all_rules = [_map_security_rule(r) for r in (nsg.security_rules or [])]
        all_rules.extend([_map_security_rule(r) for r in (nsg.default_security_rules or [])])

        inbound = sorted(
            [r for r in all_rules if r.direction == "Inbound"],
            key=lambda r: r.priority,
        )
        outbound = sorted(
            [r for r in all_rules if r.direction == "Outbound"],
            key=lambda r: r.priority,
        )

        result = {
            "nsg_name": nsg_name,
            "resource_group": resource_group,
            "inbound_rules": [r.__dict__ for r in inbound],
            "outbound_rules": [r.__dict__ for r in outbound],
            "total_rules": len(all_rules),
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return format_error_response(e)


async def azure_get_effective_security_rules(
    nic_name: str,
    resource_group: str,
    subscription_id: Optional[str] = None,
) -> str:
    """Get effective (aggregated) security rules for a network interface.

    Args:
        nic_name: Network interface name.
        resource_group: Resource group name.
        subscription_id: Target subscription ID.

    Returns:
        Aggregated effective security rules from all applicable NSGs.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)
        poller = client.network_interfaces.begin_list_effective_network_security_groups(
            resource_group, nic_name
        )
        result = poller.result()

        effective_rules = []
        if result and result.value:
            for nsg_group in result.value:
                nsg_id = getattr(nsg_group, "network_security_group", None)
                nsg_ref = nsg_id.id if nsg_id and hasattr(nsg_id, "id") else str(nsg_id) if nsg_id else "unknown"

                if nsg_group.effective_security_rules:
                    for rule in nsg_group.effective_security_rules:
                        effective_rules.append({
                            "nsg": nsg_ref,
                            "name": rule.name,
                            "priority": rule.priority,
                            "direction": str(rule.direction) if rule.direction else "",
                            "access": str(rule.access) if rule.access else "",
                            "protocol": str(rule.protocol) if rule.protocol else "",
                            "source_address_prefix": rule.source_address_prefix,
                            "source_port_range": (
                                list(rule.source_port_ranges) if rule.source_port_ranges else []
                            ),
                            "destination_address_prefix": rule.destination_address_prefix,
                            "destination_port_range": (
                                list(rule.destination_port_ranges) if rule.destination_port_ranges else []
                            ),
                        })

        return json.dumps({
            "nic_name": nic_name,
            "resource_group": resource_group,
            "effective_rules": sorted(effective_rules, key=lambda r: r.get("priority", 0)),
            "total_rules": len(effective_rules),
        }, indent=2, default=str)
    except Exception as e:
        return format_error_response(e)


async def azure_audit_nsg_compliance(
    nsg_name: Optional[str] = None,
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Audit NSG rules against CIS Azure Foundations Benchmark.

    Args:
        nsg_name: Specific NSG to audit (omit for all NSGs).
        resource_group: Resource group filter.
        subscription_id: Target subscription ID.

    Returns:
        JSON array of ComplianceFinding objects with severity, description, and remediation.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        if nsg_name and resource_group:
            nsg = client.network_security_groups.get(resource_group, nsg_name)
            nsgs_to_audit = [nsg]
        else:
            nsgs_to_audit = collect_all_pages(client.network_security_groups.list_all())

        all_findings = []
        for nsg in nsgs_to_audit:
            rules = [_map_security_rule(r) for r in (nsg.security_rules or [])]
            findings = run_all_checks(
                rules=rules,
                nsg_id=nsg.id or "",
                nsg_name=nsg.name or "",
                flow_logs_enabled=False,  # Flow log status requires Network Watcher query
                retention_days=0,
            )
            all_findings.extend(findings)

        result = {
            "nsgs_audited": len(nsgs_to_audit),
            "total_findings": len(all_findings),
            "critical_findings": len([f for f in all_findings if f.severity == "Critical"]),
            "high_findings": len([f for f in all_findings if f.severity == "High"]),
            "medium_findings": len([f for f in all_findings if f.severity == "Medium"]),
            "findings": [f.__dict__ for f in all_findings],
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return format_error_response(e)

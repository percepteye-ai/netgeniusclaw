"""Network Watcher tools: availability, connection monitors, flow logs, topology."""

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


async def azure_get_network_watcher_status(
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Check Network Watcher availability, connection monitors, and flow log configuration.

    Args:
        resource_group: Resource group to check topology (optional).
        subscription_id: Target subscription ID.

    Returns:
        Network Watcher status per region, connection monitors, and flow log config.
    """
    try:
        client = azure_client_factory.get_network_client(subscription_id)

        # List all Network Watchers
        watchers = collect_all_pages(client.network_watchers.list_all())

        watcher_list = []
        for nw in watchers:
            nw_rg = _extract_resource_group(nw.id) or ""
            watcher_data = {
                "name": nw.name,
                "id": nw.id,
                "resource_group": nw_rg,
                "location": nw.location,
                "provisioning_state": nw.provisioning_state,
                "connection_monitors": [],
                "flow_logs": [],
            }

            # Get connection monitors for this watcher
            try:
                monitors = collect_all_pages(
                    client.connection_monitors.list(nw_rg, nw.name)
                )
                for mon in monitors:
                    watcher_data["connection_monitors"].append({
                        "name": mon.name,
                        "provisioning_state": mon.provisioning_state,
                        "monitoring_status": mon.monitoring_status,
                        "start_time": str(mon.start_time) if mon.start_time else None,
                    })
            except Exception as mon_err:
                watcher_data["connection_monitors_error"] = str(mon_err)

            # Get flow logs for this watcher
            try:
                flow_logs = collect_all_pages(
                    client.flow_logs.list(nw_rg, nw.name)
                )
                for fl in flow_logs:
                    retention_days = 0
                    if fl.retention_policy and fl.retention_policy.enabled:
                        retention_days = fl.retention_policy.days or 0

                    watcher_data["flow_logs"].append({
                        "name": fl.name,
                        "target_resource_id": fl.target_resource_id,
                        "storage_id": fl.storage_id,
                        "enabled": fl.enabled,
                        "retention_days": retention_days,
                        "format_type": str(fl.format.type) if fl.format and fl.format.type else None,
                        "format_version": fl.format.version if fl.format else None,
                    })
            except Exception as fl_err:
                watcher_data["flow_logs_error"] = str(fl_err)

            # Get topology if resource_group provided
            if resource_group:
                try:
                    from azure.mgmt.network.models import TopologyParameters
                    topology = client.network_watchers.get_topology(
                        nw_rg,
                        nw.name,
                        TopologyParameters(target_resource_group_name=resource_group),
                    )
                    topo_resources = []
                    if topology.resources:
                        for res in topology.resources:
                            topo_resources.append({
                                "name": res.name,
                                "id": res.id,
                                "associations": [
                                    {"name": a.name, "resource_id": a.resource_id, "association_type": str(a.association_type)}
                                    for a in (res.associations or [])
                                ],
                            })
                    watcher_data["topology"] = {
                        "resource_group": resource_group,
                        "resources": topo_resources,
                    }
                except Exception as topo_err:
                    watcher_data["topology_error"] = str(topo_err)

            watcher_list.append(watcher_data)

        if not watcher_list:
            return json.dumps({
                "network_watchers": [],
                "message": (
                    "No Network Watchers found. Network Watcher must be enabled per region "
                    "to use connection monitoring, flow logs, and topology features."
                ),
            }, indent=2)

        return json.dumps({
            "network_watchers": watcher_list,
            "total_watchers": len(watcher_list),
            "regions_covered": list(set(w["location"] for w in watcher_list)),
        }, indent=2, default=str)
    except Exception as e:
        return format_error_response(e)

"""Azure DNS tools: zones and record sets."""

from __future__ import annotations

import json
import logging
from typing import Optional

from clients.azure_client import azure_client_factory
from models.responses import DnsZone, DnsRecordSet, to_json
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


def _extract_records(record_set) -> list[str]:
    """Extract record values from a DNS record set."""
    records = []
    if record_set.a_records:
        records.extend([r.ipv4_address for r in record_set.a_records])
    if record_set.aaaa_records:
        records.extend([r.ipv6_address for r in record_set.aaaa_records])
    if record_set.cname_record:
        records.append(record_set.cname_record.cname)
    if record_set.mx_records:
        records.extend([f"{r.preference} {r.exchange}" for r in record_set.mx_records])
    if record_set.ns_records:
        records.extend([r.nsdname for r in record_set.ns_records])
    if record_set.ptr_records:
        records.extend([r.ptrdname for r in record_set.ptr_records])
    if record_set.soa_record:
        soa = record_set.soa_record
        records.append(
            f"{soa.host} {soa.email} {soa.serial_number} "
            f"{soa.refresh_time} {soa.retry_time} {soa.expire_time} {soa.minimum_ttl}"
        )
    if record_set.srv_records:
        records.extend([
            f"{r.priority} {r.weight} {r.port} {r.target}"
            for r in record_set.srv_records
        ])
    if record_set.txt_records:
        for r in record_set.txt_records:
            records.extend(r.value or [])
    return records


def _map_zone(zone) -> DnsZone:
    zone_type = "Public"
    if hasattr(zone, "zone_type") and zone.zone_type:
        zone_type = str(zone.zone_type)

    name_servers = []
    if zone.name_servers:
        name_servers = list(zone.name_servers)

    return DnsZone(
        name=zone.name or "",
        id=zone.id or "",
        resource_group=_extract_resource_group(zone.id) or "",
        zone_type=zone_type,
        record_count=zone.number_of_record_sets or 0,
        name_servers=name_servers,
        linked_vnets=[],  # Private zone links need separate query
    )


async def azure_get_dns_zones(
    zone_name: Optional[str] = None,
    zone_type: Optional[str] = None,
    subscription_id: Optional[str] = None,
) -> str:
    """Get Azure DNS zone configuration and record sets.

    Args:
        zone_name: Specific zone (omit for all zones).
        zone_type: Filter by Public/Private.
        subscription_id: Target subscription ID.

    Returns:
        JSON array of DnsZone objects with record sets.
    """
    try:
        dns_client = azure_client_factory.get_dns_client(subscription_id)

        if zone_name:
            # Need to find which resource group the zone is in
            all_zones = collect_all_pages(dns_client.zones.list())
            target_zone = None
            for z in all_zones:
                if z.name == zone_name:
                    target_zone = z
                    break

            if not target_zone:
                return json.dumps({
                    "error": {
                        "code": "ResourceNotFoundError",
                        "message": f"DNS zone '{zone_name}' not found.",
                    }
                }, indent=2)

            zone_rg = _extract_resource_group(target_zone.id) or ""
            zone_data = _map_zone(target_zone)

            # Get record sets for this zone
            record_sets = collect_all_pages(
                dns_client.record_sets.list_by_dns_zone(zone_rg, zone_name)
            )

            records = []
            for rs in record_sets:
                record_type = rs.type.split("/")[-1] if rs.type else ""
                records.append(DnsRecordSet(
                    name=rs.name or "",
                    type=record_type,
                    ttl=rs.ttl or 0,
                    records=_extract_records(rs),
                ))

            result = {
                "zone": zone_data.__dict__,
                "record_sets": [r.__dict__ for r in records],
                "total_records": len(records),
            }
            return json.dumps(result, indent=2, default=str)
        else:
            zones = collect_all_pages(dns_client.zones.list(), transform=_map_zone)

            # Filter by zone type if specified
            if zone_type:
                zones = [z for z in zones if z.zone_type.lower() == zone_type.lower()]

            if not zones:
                return json.dumps({
                    "zones": [],
                    "message": "No DNS zones found.",
                }, indent=2)
            return to_json(zones)
    except Exception as e:
        return format_error_response(e)

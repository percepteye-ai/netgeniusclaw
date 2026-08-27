# MCP Tool Contracts: Prisma SD-WAN

**Feature**: 013-prisma-sdwan-mcp-server
**Date**: 2026-04-03

## Overview

This document defines the MCP tool contracts for the Prisma SD-WAN integration. All tools are read-only and return JSON responses optimized for LLM consumption.

## Common Response Format

All tools return responses in this structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

On error:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Invalid credentials",
    "remediation": "Check PAN_CLIENT_ID and PAN_CLIENT_SECRET"
  }
}
```

---

## Topology Tools (prisma-sdwan-topology skill)

### get_sites

Retrieve all SD-WAN sites or a specific site by ID.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | No | Specific site UUID to retrieve |

**Response**:

```json
{
  "success": true,
  "data": {
    "sites": [
      {
        "id": "abc123",
        "name": "Headquarters",
        "description": "Main office",
        "element_count": 2,
        "admin_state": "active",
        "address": {
          "city": "San Francisco",
          "state": "CA",
          "country": "US"
        }
      }
    ],
    "total_count": 1
  }
}
```

---

### get_elements

Retrieve ION devices, optionally filtered by site.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| element_id | string | No | Specific element UUID to retrieve |
| site_id | string | No | Filter by site UUID |

**Response**:

```json
{
  "success": true,
  "data": {
    "elements": [
      {
        "id": "def456",
        "name": "hq-router-1",
        "site_id": "abc123",
        "site_name": "Headquarters",
        "serial_number": "PA-1234567",
        "model_name": "ION 3000",
        "software_version": "6.2.1",
        "state": "online",
        "connected": true,
        "role": "hub"
      }
    ],
    "total_count": 1
  }
}
```

---

### get_machines

Retrieve hardware inventory details.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| machine_id | string | No | Specific machine UUID to retrieve |

**Response**:

```json
{
  "success": true,
  "data": {
    "machines": [
      {
        "id": "ghi789",
        "element_id": "def456",
        "serial_number": "PA-1234567",
        "model_name": "ION 3000",
        "hardware_version": "rev2",
        "software_version": "6.2.1"
      }
    ],
    "total_count": 1
  }
}
```

---

### get_topology

Retrieve the full network topology graph.

**Parameters**: None

**Response**:

```json
{
  "success": true,
  "data": {
    "topology": {
      "sites": [...],
      "links": [
        {
          "source_site_id": "abc123",
          "target_site_id": "xyz789",
          "type": "vpn",
          "state": "up"
        }
      ]
    }
  }
}
```

---

## Status Tools (prisma-sdwan-status skill)

### get_element_status

Retrieve operational health status for elements.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| element_id | string | No | Specific element UUID |

**Response**:

```json
{
  "success": true,
  "data": {
    "element_status": [
      {
        "element_id": "def456",
        "element_name": "hq-router-1",
        "state": "online",
        "cpu_usage": 15.2,
        "memory_usage": 42.8,
        "uptime_seconds": 864000,
        "last_seen": "2026-04-03T12:00:00Z"
      }
    ]
  }
}
```

---

### get_software_status

Retrieve software version and upgrade state.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| element_id | string | No | Specific element UUID |

**Response**:

```json
{
  "success": true,
  "data": {
    "software_status": [
      {
        "element_id": "def456",
        "element_name": "hq-router-1",
        "current_version": "6.2.1",
        "available_version": "6.2.3",
        "upgrade_available": true,
        "upgrade_scheduled": false
      }
    ]
  }
}
```

---

### get_events

Retrieve recent operational events.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| limit | integer | No | Maximum events to return (default: 20) |

**Response**:

```json
{
  "success": true,
  "data": {
    "events": [
      {
        "id": "evt123",
        "type": "element_state_change",
        "severity": "info",
        "message": "Element hq-router-1 came online",
        "timestamp": "2026-04-03T11:55:00Z",
        "entity_type": "element",
        "entity_id": "def456"
      }
    ],
    "total_count": 1
  }
}
```

---

### get_alarms

Retrieve active critical and major alarms.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| limit | integer | No | Maximum alarms to return (default: 20) |

**Response**:

```json
{
  "success": true,
  "data": {
    "alarms": [
      {
        "id": "alm456",
        "severity": "critical",
        "type": "interface_down",
        "message": "WAN interface 1 is down on hq-router-1",
        "timestamp": "2026-04-03T10:30:00Z",
        "entity_type": "interface",
        "entity_id": "int789",
        "acknowledged": false
      }
    ],
    "total_count": 1
  }
}
```

---

## Configuration Tools (prisma-sdwan-config skill)

### get_interfaces

Retrieve LAN/WAN interface configurations.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes | Site UUID |
| element_id | string | Yes | Element UUID |

**Response**:

```json
{
  "success": true,
  "data": {
    "interfaces": [
      {
        "id": "int001",
        "name": "1",
        "type": "lan",
        "admin_state": "up",
        "operational_state": "up",
        "mac_address": "00:11:22:33:44:55",
        "ipv4_config": {
          "address": "192.168.1.1",
          "prefix": 24,
          "gateway": null
        },
        "mtu": 1500,
        "speed": 1000
      }
    ],
    "total_count": 1
  }
}
```

---

### get_wan_interfaces

Retrieve WAN-specific interface configurations.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes | Site UUID |

**Response**:

```json
{
  "success": true,
  "data": {
    "wan_interfaces": [
      {
        "id": "wan001",
        "name": "WAN-ISP1",
        "type": "internet",
        "label": "Comcast Business",
        "bandwidth_up": 100000,
        "bandwidth_down": 500000,
        "bfd_mode": "enabled"
      }
    ],
    "total_count": 1
  }
}
```

---

### get_bgp_peers

Retrieve BGP peer configurations.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes | Site UUID |
| element_id | string | Yes | Element UUID |

**Response**:

```json
{
  "success": true,
  "data": {
    "bgp_peers": [
      {
        "id": "bgp001",
        "name": "ISP-Peer",
        "peer_ip": "203.0.113.1",
        "peer_asn": 65001,
        "local_asn": 65000,
        "state": "established"
      }
    ],
    "total_count": 1
  }
}
```

---

### get_static_routes

Retrieve static route configurations.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes | Site UUID |
| element_id | string | Yes | Element UUID |

**Response**:

```json
{
  "success": true,
  "data": {
    "static_routes": [
      {
        "id": "rt001",
        "destination": "10.0.0.0/8",
        "next_hop": "192.168.1.254",
        "metric": 10,
        "description": "Route to datacenter"
      }
    ],
    "total_count": 1
  }
}
```

---

### get_policy_sets

Retrieve policy set definitions.

**Parameters**: None

**Response**:

```json
{
  "success": true,
  "data": {
    "policy_sets": [
      {
        "id": "pol001",
        "name": "Default-Policy",
        "description": "Default traffic policy",
        "default_policy": true
      }
    ],
    "total_count": 1
  }
}
```

---

### get_security_zones

Retrieve security zone definitions.

**Parameters**: None

**Response**:

```json
{
  "success": true,
  "data": {
    "security_zones": [
      {
        "id": "zone001",
        "name": "trusted",
        "description": "Internal trusted network",
        "zone_type": "default"
      }
    ],
    "total_count": 1
  }
}
```

---

### generate_site_config

Generate validated YAML configuration for a site.

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes | Site UUID to generate config for |
| elements | array[string] | No | Element UUIDs to include (all if omitted) |
| filename | string | No | Output filename (default: site-config.yaml) |
| overwrite | boolean | No | Overwrite existing file (default: false) |

**Response**:

```json
{
  "success": true,
  "data": {
    "filename": "headquarters-config.yaml",
    "path": "/tmp/headquarters-config.yaml",
    "validation": {
      "valid": true,
      "errors": []
    }
  }
}
```

---

## Application Tools (prisma-sdwan-apps skill)

### get_app_defs

Retrieve application definitions.

**Parameters**: None

**Response**:

```json
{
  "success": true,
  "data": {
    "applications": [
      {
        "id": "app001",
        "name": "office365",
        "display_name": "Microsoft Office 365",
        "category": "business",
        "subcategory": "productivity",
        "risk": "low",
        "app_type": "saas"
      }
    ],
    "total_count": 1
  }
}
```

---

## Error Codes

| Code | Description | Remediation |
|------|-------------|-------------|
| AUTH_FAILED | OAuth2 authentication failed | Check PAN_CLIENT_ID, PAN_CLIENT_SECRET, PAN_TSG_ID |
| TOKEN_EXPIRED | Access token expired | Automatic refresh should handle; restart if persistent |
| NETWORK_ERROR | Cannot reach Prisma SASE API | Check network connectivity to api.sase.paloaltonetworks.com |
| NOT_FOUND | Requested resource not found | Verify site_id, element_id exists via get_sites, get_elements |
| RATE_LIMITED | API rate limit exceeded | Wait and retry; reduce request frequency |
| INVALID_PARAM | Invalid parameter value | Check parameter format (UUIDs, integers) |
| REGION_MISMATCH | Wrong regional endpoint | Set PAN_REGION=europe for EU deployments |

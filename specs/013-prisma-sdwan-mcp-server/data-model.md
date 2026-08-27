# Data Model: Prisma SD-WAN MCP Server Integration

**Feature**: 013-prisma-sdwan-mcp-server
**Date**: 2026-04-03

## Overview

This document defines the key entities exposed by the Prisma SD-WAN MCP server. All entities are read-only views of data managed by the Prisma SASE controller — NetGeniusClaw does not persist or modify these entities.

## Entity Definitions

### Site

A physical or logical location in the SD-WAN fabric.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique site identifier |
| name | string | Human-readable site name |
| description | string | Optional site description |
| address | object | Physical address (street, city, state, country, postal_code) |
| location | object | Geographic coordinates (latitude, longitude) |
| element_count | integer | Number of ION devices at this site |
| admin_state | string | Administrative state (active, disabled) |
| tags | array[string] | User-defined tags for categorization |

**Relationships**:
- Has many Elements (1:N)
- Has many Interfaces via Elements (1:N:N)

### Element

An ION device (router/edge device) deployed at a site.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique element identifier |
| name | string | Device hostname |
| site_id | string (UUID) | Parent site reference |
| serial_number | string | Hardware serial number |
| model_name | string | Device model (e.g., ION 3000, ION 9000) |
| software_version | string | Current software version |
| state | string | Operational state (online, offline, degraded) |
| connected | boolean | Controller connectivity status |
| role | string | Device role (spoke, hub, controller) |

**Relationships**:
- Belongs to Site (N:1)
- Has one Machine (1:1)
- Has many Interfaces (1:N)
- Has many BGP Peers (1:N)
- Has many Static Routes (1:N)

### Machine

Hardware inventory information for an element.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique machine identifier |
| element_id | string (UUID) | Associated element reference |
| serial_number | string | Hardware serial number |
| model_name | string | Hardware model |
| manufacture_date | string (date) | Manufacturing date |
| software_version | string | Installed software version |
| hardware_version | string | Hardware revision |

**Relationships**:
- Belongs to Element (1:1)

### Interface

Network interface on an element (LAN or WAN).

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique interface identifier |
| element_id | string (UUID) | Parent element reference |
| name | string | Interface name (e.g., 1, 2, port1) |
| type | string | Interface type (lan, wan, loopback) |
| admin_state | string | Administrative state (up, down) |
| operational_state | string | Operational state (up, down) |
| mac_address | string | MAC address |
| ipv4_config | object | IPv4 configuration (address, prefix, gateway) |
| ipv6_config | object | IPv6 configuration (address, prefix, gateway) |
| mtu | integer | Maximum transmission unit |
| speed | integer | Link speed in Mbps |

**Relationships**:
- Belongs to Element (N:1)

### WAN Interface

WAN-specific interface configuration.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique WAN interface identifier |
| site_id | string (UUID) | Parent site reference |
| name | string | Circuit/WAN interface name |
| type | string | WAN type (internet, mpls, lte, satellite) |
| label | string | Circuit label (e.g., ISP name) |
| bandwidth_up | integer | Upload bandwidth in Kbps |
| bandwidth_down | integer | Download bandwidth in Kbps |
| network_id | string (UUID) | Associated network reference |
| bfd_mode | string | BFD configuration |

**Relationships**:
- Belongs to Site (N:1)

### BGP Peer

BGP peering configuration on an element.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique BGP peer identifier |
| element_id | string (UUID) | Parent element reference |
| site_id | string (UUID) | Parent site reference |
| name | string | Peer name/description |
| peer_ip | string | Peer IP address |
| peer_asn | integer | Peer autonomous system number |
| local_asn | integer | Local autonomous system number |
| state | string | BGP session state (established, idle, active) |
| route_map_in | string | Inbound route map |
| route_map_out | string | Outbound route map |

**Relationships**:
- Belongs to Element (N:1)
- Belongs to Site (N:1)

### Static Route

Static route entry on an element.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique route identifier |
| element_id | string (UUID) | Parent element reference |
| site_id | string (UUID) | Parent site reference |
| destination | string | Destination prefix (CIDR) |
| next_hop | string | Next hop IP address |
| interface | string | Egress interface |
| metric | integer | Route metric/preference |
| description | string | Route description |

**Relationships**:
- Belongs to Element (N:1)
- Belongs to Site (N:1)

### Policy Set

Traffic handling rules for the SD-WAN fabric.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique policy set identifier |
| name | string | Policy set name |
| description | string | Policy set description |
| default_policy | boolean | Whether this is the default policy |
| clone_from | string (UUID) | Source policy if cloned |
| rules | array[object] | List of policy rules |

**Relationships**:
- Contains many Policy Rules (1:N)

### Security Zone

Network segmentation for security policy enforcement.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique security zone identifier |
| name | string | Zone name |
| description | string | Zone description |
| zone_type | string | Zone type (default, custom) |

**Relationships**:
- Referenced by Interfaces (M:N)
- Referenced by Policy Rules (M:N)

### Application Definition

Classification rules for identifying application traffic.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique application identifier |
| name | string | Application name |
| display_name | string | Human-readable display name |
| category | string | Application category |
| subcategory | string | Application subcategory |
| risk | string | Risk level (low, medium, high) |
| transfer_type | string | Data transfer type |
| app_type | string | Application type (saas, custom, predefined) |

**Relationships**:
- Referenced by Policy Rules (M:N)

### Alarm

Active alert indicating an issue requiring attention.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique alarm identifier |
| severity | string | Severity level (critical, major, minor, warning) |
| type | string | Alarm type/category |
| entity_type | string | Affected entity type (site, element, interface) |
| entity_id | string (UUID) | Affected entity identifier |
| entity_name | string | Affected entity name |
| message | string | Alarm description |
| timestamp | string (datetime) | Alarm occurrence time |
| acknowledged | boolean | Whether alarm is acknowledged |

**Relationships**:
- References Site, Element, or Interface (polymorphic)

### Event

Operational occurrence recorded for audit and troubleshooting.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique event identifier |
| type | string | Event type/category |
| severity | string | Event severity |
| entity_type | string | Related entity type |
| entity_id | string (UUID) | Related entity identifier |
| message | string | Event description |
| timestamp | string (datetime) | Event occurrence time |
| operator | string | User/system that triggered event |

**Relationships**:
- References various entities (polymorphic)

## Entity Relationship Diagram

```
┌─────────┐       ┌───────────┐       ┌──────────┐
│  Site   │──────<│  Element  │──────<│ Interface│
└─────────┘  1:N  └───────────┘  1:N  └──────────┘
     │                  │
     │ 1:N              │ 1:1
     ▼                  ▼
┌─────────────┐   ┌──────────┐
│WAN Interface│   │ Machine  │
└─────────────┘   └──────────┘

┌───────────┐            ┌─────────────┐
│  Element  │───────────<│  BGP Peer   │
└───────────┘      1:N   └─────────────┘
     │
     │ 1:N
     ▼
┌──────────────┐
│ Static Route │
└──────────────┘

┌────────────┐   ┌───────────────┐   ┌─────────────────────┐
│ Policy Set │   │ Security Zone │   │ Application Def     │
└────────────┘   └───────────────┘   └─────────────────────┘
     (standalone entities referenced by policies)

┌─────────┐   ┌─────────┐
│  Alarm  │   │  Event  │
└─────────┘   └─────────┘
 (operational monitoring entities)
```

## State Transitions

### Element State

```
                    ┌──────────┐
                    │  online  │
                    └────┬─────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │ degraded │  │ offline  │  │ rebooting│
     └──────────┘  └──────────┘  └──────────┘
```

### BGP Peer State

```
┌──────┐ ───► ┌────────┐ ───► ┌─────────────┐
│ idle │      │ active │      │ established │
└──────┘ ◄─── └────────┘ ◄─── └─────────────┘
```

## Notes

- All IDs are UUIDs assigned by the Prisma SASE controller
- Timestamps are ISO 8601 format in UTC
- This is a read-only data model — no create/update/delete operations
- Pagination is handled automatically by the MCP server for large result sets

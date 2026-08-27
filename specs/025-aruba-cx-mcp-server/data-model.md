# Data Model: Aruba CX MCP Server Integration

**Feature**: 025-aruba-cx-mcp-server
**Date**: 2026-04-08

## Overview

This document defines the data entities and relationships for the Aruba CX MCP server integration. The server acts as a stateless proxy to Aruba CX switch REST APIs.

## Core Entities

### SwitchTarget

Represents a configured Aruba CX switch connection target.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| name | string | Unique identifier for the switch | Yes |
| host | string | IP address or hostname | Yes |
| username | string | REST API username | Yes |
| password | string | REST API password (from env) | Yes |
| port | integer | REST API port (default: 443) | No |
| api_version | string | API version (default: "v10.13") | No |
| verify_ssl | boolean | Verify SSL certificates (default: true) | No |

**Validation Rules**:
- `name` must be unique across all targets
- `host` must be valid IP address or resolvable hostname
- `port` must be 1-65535
- `api_version` must match pattern "v10.XX"

### SystemInfo

Switch system information response.

| Field | Type | Description |
|-------|------|-------------|
| hostname | string | Configured hostname |
| model | string | Switch model (e.g., "6300M") |
| serial_number | string | Chassis serial number |
| software_version | string | AOS-CX version |
| uptime | integer | Seconds since boot |
| boot_time | datetime | Last boot timestamp |

### Interface

Physical or logical switch interface.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Interface name (e.g., "1/1/1") |
| admin_state | enum | up, down |
| oper_state | enum | up, down, testing |
| speed | string | Negotiated speed (e.g., "10G") |
| description | string | User-configured description |
| mtu | integer | Maximum transmission unit |
| type | string | Interface type (ethernet, lag, vlan) |

### VLAN

Layer 2 VLAN configuration.

| Field | Type | Description |
|-------|------|-------------|
| id | integer | VLAN ID (1-4094) |
| name | string | VLAN name |
| admin_state | enum | up, down |
| tagged_ports | list[string] | Tagged interface names |
| untagged_ports | list[string] | Untagged interface names |
| voice | boolean | Voice VLAN flag |

**Validation Rules**:
- `id` must be 1-4094
- `name` must be 1-32 characters, alphanumeric with underscores

### LLDPNeighbor

LLDP discovered neighbor.

| Field | Type | Description |
|-------|------|-------------|
| local_port | string | Local interface name |
| remote_chassis_id | string | Neighbor chassis ID |
| remote_port_id | string | Neighbor port ID |
| remote_system_name | string | Neighbor hostname |
| remote_system_description | string | Neighbor system description |
| remote_capabilities | list[string] | Advertised capabilities |

### MACEntry

MAC address table entry.

| Field | Type | Description |
|-------|------|-------------|
| mac_address | string | MAC address (aa:bb:cc:dd:ee:ff) |
| vlan_id | integer | Associated VLAN |
| port | string | Learned interface |
| type | enum | dynamic, static |
| age | integer | Entry age in seconds |

### DOMDiagnostics

Digital Optical Monitoring data.

| Field | Type | Description |
|-------|------|-------------|
| interface | string | Interface name |
| temperature | float | Module temperature (Celsius) |
| temperature_status | enum | normal, warning, alarm |
| tx_power | float | Transmit power (dBm) |
| tx_power_status | enum | normal, warning, alarm |
| rx_power | float | Receive power (dBm) |
| rx_power_status | enum | normal, warning, alarm |
| voltage | float | Supply voltage (V) |
| vendor | string | Transceiver vendor |
| part_number | string | Transceiver part number |

**Threshold Detection**:
- `*_status` fields indicate whether values exceed warning/alarm thresholds
- Thresholds are read from transceiver EEPROM

### VSFMember

Virtual Switching Framework member.

| Field | Type | Description |
|-------|------|-------------|
| member_id | integer | VSF member number |
| role | enum | commander, standby, member |
| serial_number | string | Member serial number |
| model | string | Member switch model |
| status | enum | ready, syncing, failed |
| priority | integer | Election priority |

### FirmwareInfo

Software/firmware details.

| Field | Type | Description |
|-------|------|-------------|
| primary_version | string | Primary image version |
| secondary_version | string | Secondary image version |
| boot_image | enum | primary, secondary |
| issu_capable | boolean | ISSU support flag |
| last_upgrade | datetime | Last upgrade timestamp |

### ISSUStatus

In-Service Software Upgrade status.

| Field | Type | Description |
|-------|------|-------------|
| state | enum | idle, downloading, staging, upgrading, complete, failed |
| progress | integer | Percentage complete (0-100) |
| target_version | string | Version being installed |
| start_time | datetime | Upgrade start time |
| error_message | string | Error details if failed |

### Configuration

Switch configuration snapshot.

| Field | Type | Description |
|-------|------|-------------|
| type | enum | running, startup |
| content | string | Full configuration text |
| checksum | string | Configuration checksum |
| last_modified | datetime | Last change timestamp |
| modified_by | string | User who made last change |

## Relationships

```
SwitchTarget
    ├── 1:1 SystemInfo
    ├── 1:1 FirmwareInfo
    ├── 1:1 ISSUStatus
    ├── 1:N Interface
    │       └── 1:1 DOMDiagnostics (if optical)
    ├── 1:N VLAN
    ├── 1:N LLDPNeighbor
    ├── 1:N MACEntry
    ├── 1:N VSFMember (if VSF enabled)
    └── 1:2 Configuration (running, startup)
```

## State Transitions

### Interface Admin State
```
down → up (via configure_interface)
up → down (via configure_interface)
```

### VLAN Lifecycle
```
(none) → created (via create_vlan)
created → modified (via configure_vlan)
created/modified → deleted (via delete_vlan)
```

### ISSU State Machine
```
idle → downloading (firmware download started)
downloading → staging (image validated)
staging → upgrading (ISSU in progress)
upgrading → complete (success)
upgrading → failed (error occurred)
failed → idle (error cleared)
complete → idle (upgrade finished)
```

## Notes

- All entities are ephemeral (queried on demand, not persisted)
- Write operations require ITSM approval when ITSM_ENABLED=true
- VSFMember entities only exist for VSF-enabled switches
- DOMDiagnostics only available for optical transceiver ports

# MCP Tools Contract: Aruba CX MCP Server

**Feature**: 025-aruba-cx-mcp-server
**Date**: 2026-04-08
**Server**: aruba-cx-mcp

## Overview

This document defines the MCP tool contracts for the Aruba CX MCP server integration. All tools follow the MCP JSON-RPC protocol.

## Read-Only Tools (11)

### get_system_info

Get system information from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name from configuration |

**Response**:
```json
{
  "hostname": "core-sw-1",
  "model": "Aruba 6300M",
  "serial_number": "SG1234567890",
  "software_version": "10.13.1000",
  "uptime": 8640000,
  "boot_time": "2026-01-01T00:00:00Z"
}
```

---

### get_interfaces

Get interface status from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| interface | string | No | Specific interface (e.g., "1/1/1"). Omit for all. |

**Response** (array):
```json
[
  {
    "name": "1/1/1",
    "admin_state": "up",
    "oper_state": "up",
    "speed": "10G",
    "description": "Uplink to spine",
    "mtu": 9198,
    "type": "ethernet"
  }
]
```

---

### get_vlans

Get VLAN configuration from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| vlan_id | integer | No | Specific VLAN ID. Omit for all. |

**Response** (array):
```json
[
  {
    "id": 100,
    "name": "Management",
    "admin_state": "up",
    "tagged_ports": ["1/1/49", "1/1/50"],
    "untagged_ports": ["1/1/1", "1/1/2"],
    "voice": false
  }
]
```

---

### get_running_config

Get running configuration from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| section | string | No | Config section (e.g., "interface", "vlan"). Omit for full config. |

**Response**:
```json
{
  "type": "running",
  "content": "hostname core-sw-1\n...",
  "checksum": "abc123",
  "last_modified": "2026-04-08T10:00:00Z"
}
```

---

### get_startup_config

Get startup configuration from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |

**Response**: Same format as get_running_config with `"type": "startup"`.

---

### get_routing_table

Get IP routing table from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| vrf | string | No | VRF name (default: "default") |

**Response** (array):
```json
[
  {
    "destination": "10.0.0.0/8",
    "next_hop": "10.1.1.1",
    "interface": "vlan100",
    "protocol": "static",
    "metric": 1,
    "admin_distance": 1
  }
]
```

---

### get_lldp_neighbors

Get LLDP neighbor information from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| interface | string | No | Specific interface. Omit for all. |

**Response** (array):
```json
[
  {
    "local_port": "1/1/49",
    "remote_chassis_id": "aa:bb:cc:dd:ee:ff",
    "remote_port_id": "Ethernet1",
    "remote_system_name": "spine-1",
    "remote_system_description": "Aruba 8325",
    "remote_capabilities": ["bridge", "router"]
  }
]
```

---

### get_mac_table

Get MAC address table from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| vlan_id | integer | No | Filter by VLAN ID |
| mac_address | string | No | Search for specific MAC |

**Response** (array):
```json
[
  {
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "vlan_id": 100,
    "port": "1/1/1",
    "type": "dynamic",
    "age": 300
  }
]
```

---

### get_dom_diagnostics

Get Digital Optical Monitoring data from an Aruba CX switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| interface | string | No | Specific interface. Omit for all optical ports. |

**Response** (array):
```json
[
  {
    "interface": "1/1/49",
    "temperature": 35.5,
    "temperature_status": "normal",
    "tx_power": -2.5,
    "tx_power_status": "normal",
    "rx_power": -3.1,
    "rx_power_status": "normal",
    "voltage": 3.3,
    "vendor": "Aruba",
    "part_number": "JL484A"
  }
]
```

---

### get_issu_status

Get ISSU (In-Service Software Upgrade) status.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |

**Response**:
```json
{
  "state": "idle",
  "progress": 0,
  "target_version": null,
  "start_time": null,
  "error_message": null
}
```

---

### get_firmware_info

Get firmware/software version details.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |

**Response**:
```json
{
  "primary_version": "10.13.1000",
  "secondary_version": "10.12.0030",
  "boot_image": "primary",
  "issu_capable": true,
  "last_upgrade": "2026-03-01T00:00:00Z"
}
```

---

### get_vsf_topology

Get VSF (Virtual Switching Framework) topology.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name (any VSF member) |

**Response**:
```json
{
  "enabled": true,
  "domain_id": 1,
  "members": [
    {
      "member_id": 1,
      "role": "commander",
      "serial_number": "SG1234567890",
      "model": "6300M",
      "status": "ready",
      "priority": 255
    },
    {
      "member_id": 2,
      "role": "standby",
      "serial_number": "SG0987654321",
      "model": "6300M",
      "status": "ready",
      "priority": 128
    }
  ]
}
```

**Note**: Returns `{"enabled": false}` if VSF is not configured.

---

## Write Tools (5)

> **ITSM Gating**: All write tools require ServiceNow CR approval when ITSM_ENABLED=true.

### configure_interface

Configure interface parameters.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| interface | string | Yes | Interface name (e.g., "1/1/1") |
| admin_state | string | No | "up" or "down" |
| description | string | No | Interface description |
| cr_number | string | Conditional | ServiceNow CR (required if ITSM_ENABLED) |

**Response**:
```json
{
  "success": true,
  "message": "Interface 1/1/1 configured",
  "changes": {
    "admin_state": {"old": "down", "new": "up"},
    "description": {"old": "", "new": "Server port"}
  }
}
```

---

### create_vlan

Create a new VLAN.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| vlan_id | integer | Yes | VLAN ID (1-4094) |
| name | string | No | VLAN name |
| cr_number | string | Conditional | ServiceNow CR (required if ITSM_ENABLED) |

**Response**:
```json
{
  "success": true,
  "message": "VLAN 200 created",
  "vlan": {
    "id": 200,
    "name": "Guest_Network"
  }
}
```

---

### configure_vlan

Modify an existing VLAN.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| vlan_id | integer | Yes | VLAN ID |
| name | string | No | New VLAN name |
| tagged_ports | array | No | Tagged port list |
| untagged_ports | array | No | Untagged port list |
| cr_number | string | Conditional | ServiceNow CR (required if ITSM_ENABLED) |

**Response**: Similar to create_vlan with changes shown.

---

### delete_vlan

Delete a VLAN.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| vlan_id | integer | Yes | VLAN ID to delete |
| cr_number | string | Conditional | ServiceNow CR (required if ITSM_ENABLED) |

**Response**:
```json
{
  "success": true,
  "message": "VLAN 200 deleted"
}
```

---

### save_config

Save running configuration to startup.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| cr_number | string | Conditional | ServiceNow CR (required if ITSM_ENABLED) |

**Response**:
```json
{
  "success": true,
  "message": "Configuration saved",
  "checksum": "def456"
}
```

---

### issu_upgrade

Initiate an In-Service Software Upgrade.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| image | string | Yes | Firmware image path or URL |
| cr_number | string | Conditional | ServiceNow CR (required if ITSM_ENABLED) |

**Response**:
```json
{
  "success": true,
  "message": "ISSU initiated",
  "job_id": "issu-2026-04-08-001"
}
```

**Note**: Use `get_issu_status` to monitor progress.

---

### upload_firmware / download_firmware

Upload firmware to switch or download from switch.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| target | string | Yes | Switch target name |
| source | string | Yes | Source path/URL |
| destination | string | Yes | Destination path |
| cr_number | string | Conditional | ServiceNow CR (required if ITSM_ENABLED) |

**Response**:
```json
{
  "success": true,
  "message": "Firmware transfer complete",
  "size_bytes": 524288000
}
```

---

## Error Responses

All tools return errors in MCP standard format:

```json
{
  "error": {
    "code": -32000,
    "message": "Authentication failed",
    "data": {
      "target": "core-sw-1",
      "details": "Invalid credentials"
    }
  }
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| -32000 | Authentication failure |
| -32001 | Connection timeout |
| -32002 | Target not found in configuration |
| -32003 | ITSM CR required but not provided |
| -32004 | ITSM CR validation failed |
| -32005 | Operation not supported on this device |
| -32006 | Invalid parameter value |
| -32007 | Write operation failed |

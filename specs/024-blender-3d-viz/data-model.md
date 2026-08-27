# Data Model: Blender 3D Network Visualization

**Feature**: 024-blender-3d-viz
**Date**: 2026-04-05

## Overview

This document defines the data structures used for transforming network topology data into 3D visualization commands.

## Entities

### NetworkDevice

Represents a network device to be rendered in 3D.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `hostname` | string | Device hostname | CDP/LLDP neighbor data |
| `device_type` | enum | Type of device | Inferred from hostname/model |
| `ip_address` | string? | Management IP (optional) | CDP/LLDP or inventory |
| `model` | string? | Device model (optional) | CDP/LLDP |
| `neighbors` | string[] | List of neighbor hostnames | CDP/LLDP adjacencies |

**Device Types**:
```
enum DeviceType {
  ROUTER = "router"
  SWITCH = "switch"
  FIREWALL = "firewall"
  ACCESS_POINT = "access_point"
  UNKNOWN = "unknown"
}
```

**Type Inference Rules**:
- Contains "rtr" or "router" → ROUTER
- Contains "sw" or "switch" → SWITCH
- Contains "fw" or "firewall" or "asa" → FIREWALL
- Contains "ap" or "wap" or "wireless" → ACCESS_POINT
- Otherwise → UNKNOWN

### TopologyGraph

Represents the complete network topology as a graph structure.

| Field | Type | Description |
|-------|------|-------------|
| `devices` | NetworkDevice[] | All devices in topology |
| `links` | TopologyLink[] | All connections between devices |
| `total_device_count` | int | Original count before truncation |
| `is_truncated` | bool | True if exceeds 25-device limit |

### TopologyLink

Represents a connection between two devices.

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Source device hostname |
| `target` | string | Target device hostname |
| `local_interface` | string? | Interface on source device |
| `remote_interface` | string? | Interface on target device |

### BlenderObject

Represents a 3D object in Blender (internal representation).

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Blender object name |
| `object_type` | string | Primitive type (cube, cylinder) |
| `position` | Vector3 | X, Y, Z coordinates |
| `scale` | Vector3 | X, Y, Z scale factors |
| `rotation` | Vector3 | Euler rotation (radians) |
| `color` | RGB | Material color |

### Vector3

3D coordinate or scale vector.

| Field | Type | Description |
|-------|------|-------------|
| `x` | float | X component |
| `y` | float | Y component |
| `z` | float | Z component |

### RGB

Color representation.

| Field | Type | Description |
|-------|------|-------------|
| `r` | float | Red (0.0-1.0) |
| `g` | float | Green (0.0-1.0) |
| `b` | float | Blue (0.0-1.0) |

## Color Mappings

| DeviceType | RGB | Hex |
|------------|-----|-----|
| ROUTER | (0.2, 0.4, 0.8) | #3366CC |
| SWITCH | (0.2, 0.7, 0.3) | #33B34D |
| FIREWALL | (0.8, 0.2, 0.2) | #CC3333 |
| ACCESS_POINT | (0.9, 0.8, 0.2) | #E6CC33 |
| UNKNOWN | (0.5, 0.5, 0.5) | #808080 |

## Data Flow

```
CDP/LLDP Query → NetworkDevice[] → TopologyGraph → Layout Algorithm → BlenderObject[] → MCP Commands
```

### Step 1: Extract Topology
```
Input: Raw CDP/LLDP neighbor tables from pyATS
Output: TopologyGraph with devices and links
```

### Step 2: Apply Layout
```
Input: TopologyGraph
Output: TopologyGraph with positions assigned to each device
```

### Step 3: Generate Objects
```
Input: Positioned TopologyGraph
Output: BlenderObject[] (devices as cubes, links as cylinders)
```

### Step 4: Render via MCP
```
Input: BlenderObject[]
Output: MCP tool calls (create_object, set_material)
```

## Validation Rules

### NetworkDevice
- `hostname`: Required, non-empty string
- `device_type`: Must be valid DeviceType enum value
- `neighbors`: May be empty list (isolated device)

### TopologyGraph
- `devices`: Max 25 elements (enforced by truncation)
- `links`: Must reference valid device hostnames
- No duplicate device hostnames (deduplicated by hostname)

### BlenderObject
- `name`: Unique within scene (hostname-based)
- `position`: All components must be finite numbers
- `scale`: All components must be positive
- `color`: All components must be in [0.0, 1.0]

## State Transitions

This feature is stateless within NetGeniusClaw. Each visualization request:
1. Queries current CDP/LLDP state
2. Generates new topology
3. Clears previous Blender scene (or creates new)
4. Renders current topology

No persistent state is maintained between requests.

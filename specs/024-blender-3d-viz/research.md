# Research: Blender 3D Network Visualization

**Feature**: 024-blender-3d-viz
**Date**: 2026-04-05

## Overview

This document captures research findings for integrating the Blender MCP server with NetGeniusClaw for 3D network topology visualization.

## Blender MCP Server Analysis

### Source
- **Repository**: https://github.com/ahujasid/blender-mcp
- **Package**: `blender-mcp` (available via uvx)
- **License**: Open source (community project)

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NetGeniusClaw/WSL   │────▶│   blender-mcp   │────▶│ Blender/Windows │
│   (MCP Client)  │     │   (MCP Server)  │     │   (Addon)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │                       │
    Natural language      JSON-RPC/MCP           Socket:9876
    topology request      tool calls              bpy commands
```

**Components**:
1. **Blender Addon** (`addon.py`): Python script running inside Blender, creates socket server on port 9876
2. **MCP Server** (`blender-mcp`): Python package invoked via uvx, implements MCP protocol, forwards commands to addon

### Available MCP Tools

| Tool | Description | Use Case for Topology |
|------|-------------|----------------------|
| `get_scene_info` | Returns current scene objects | Verify scene state |
| `create_object` | Creates primitives (cube, sphere, cylinder) | Create device nodes |
| `modify_object` | Transform position/rotation/scale | Position devices in layout |
| `set_material` | Apply colors and materials | Color by device type |
| `execute_blender_code` | Run arbitrary Python in Blender | Complex operations, labels |
| `get_polyhaven_categories` | List Poly Haven assets | Future: HDRIs, textures |
| `search_polyhaven_assets` | Search external assets | Future: 3D models |
| `download_polyhaven_asset` | Download and apply assets | Future: environments |

### Decision: Tool Selection for Topology Rendering

**Decision**: Use `create_object`, `modify_object`, `set_material`, and `execute_blender_code` for core topology rendering.

**Rationale**:
- `create_object` provides primitives sufficient for device representation
- `execute_blender_code` enables text labels and complex operations
- Poly Haven tools are optional enhancements, not required for MVP

**Alternatives Considered**:
- Custom Blender addon for network-specific primitives: Rejected (over-engineering for v1)
- Pre-built 3D models for devices: Deferred (out of scope per spec assumptions)

## WSL-to-Windows Connectivity

### Challenge
Blender runs on Windows (GUI application), NetGeniusClaw runs in WSL2. The MCP server must reach Blender's socket on Windows.

### Decision: Use Windows Host IP

**Decision**: Configure `BLENDER_HOST` to the Windows host IP discovered from `/etc/resolv.conf`.

**Rationale**:
- WSL2 has separate network namespace; `localhost` does not reach Windows
- Windows host IP is consistently available via nameserver in resolv.conf
- No additional configuration required on Windows side

**Implementation**:
```bash
# Discovery command for .env setup
WIN_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
export BLENDER_HOST=$WIN_IP
export BLENDER_PORT=9876
```

**Alternatives Considered**:
- Port forwarding via netsh: Rejected (requires admin, adds complexity)
- Running Blender in WSL with WSLg: Possible but less reliable for graphics-heavy apps

## Device Type Visual Differentiation

### Decision: Color-Based Differentiation

**Decision**: Use distinct colors for device types with cube primitives for all devices.

| Device Type | Color | Rationale |
|-------------|-------|-----------|
| Router | Blue | Convention (Visio, draw.io) |
| Switch | Green | Convention |
| Firewall | Red | Security = red (alert color) |
| Access Point | Yellow | Wireless = distinct |
| Unknown/Other | Gray | Neutral default |

**Rationale**:
- Color is universally understood and quick to implement
- Cubes are simple, performant, and clearly visible
- Matches common network diagramming conventions

**Alternatives Considered**:
- Different shapes per device type: Adds complexity, harder to label
- Custom 3D models: Out of scope for v1

## Topology Layout Algorithm

### Decision: Force-Directed Spring Layout

**Decision**: Implement a simple force-directed layout in Python, position devices before sending to Blender.

**Rationale**:
- Produces readable layouts for network topologies
- Can be computed in NetGeniusClaw before rendering
- Works well for 5-25 devices

**Algorithm**:
1. Place center device (highest degree) at origin
2. Place neighbors in ring around center
3. Apply repulsion between non-adjacent devices
4. Iterate until stable (or max iterations)

**Alternatives Considered**:
- Hierarchical layout: Better for tree structures but CDP graphs may have cycles
- Grid layout: Simple but doesn't show logical relationships
- User-specified positions: Requires additional input, not natural language friendly

## Connection Rendering

### Decision: Cylinder Primitives for Links

**Decision**: Use thin cylinders stretched between device centers.

**Rationale**:
- Simple to create with `create_object`
- Visually clear as "cables"
- Can be colored to indicate link types (future)

**Implementation**:
```python
# Pseudocode for link creation
for link in topology.links:
    midpoint = (device_a.position + device_b.position) / 2
    length = distance(device_a.position, device_b.position)
    create_cylinder(position=midpoint, height=length, rotation=toward_devices)
```

## Device Limit Enforcement

### Decision: Hard Limit of 25 Devices (Per Clarification)

**Decision**: Render up to 25 devices. If topology exceeds limit, warn user and render first 25 by highest connectivity.

**Rationale**:
- Blender performance degrades with many objects
- 25 devices provides meaningful visualization for most campus/branch networks
- Larger networks should use dedicated diagramming tools

**Implementation**:
- Sort devices by neighbor count (descending)
- Take first 25
- Display warning: "Topology truncated: showing 25 of N devices"

## Error Handling

### Decision: Graceful Degradation with Clear Messages

| Error Condition | User Message | Behavior |
|-----------------|--------------|----------|
| Blender not running | "Blender connection unavailable. Please start Blender and enable the MCP addon." | Abort |
| No CDP data | "No CDP/LLDP neighbor data available. Query devices first." | Abort |
| Partial topology | "Warning: Could not render N devices due to missing data." | Render available |
| Export failure | "Export failed: [reason]. Check Blender is visible and not minimized." | Abort export |

## Best Practices Applied

1. **MCP Standard Compliance**: Uses official MCP protocol, no custom extensions
2. **Existing Patterns**: Follows NetGeniusClaw's uvx-based MCP server registration pattern
3. **Environment Variables**: BLENDER_HOST and BLENDER_PORT follow .env.example conventions
4. **Skill Modularity**: Single-purpose skill with clear boundaries
5. **Error Transparency**: No silent failures; all errors reported to user

## Summary of Decisions

| Topic | Decision |
|-------|----------|
| MCP Package | `blender-mcp` via uvx |
| Tool Selection | create_object, modify_object, set_material, execute_blender_code |
| WSL Connectivity | Windows host IP from resolv.conf |
| Device Representation | Colored cubes (router=blue, switch=green, firewall=red) |
| Layout Algorithm | Force-directed spring layout |
| Connection Rendering | Thin cylinders between devices |
| Device Limit | 25 devices maximum |
| Error Handling | Clear messages, graceful degradation |

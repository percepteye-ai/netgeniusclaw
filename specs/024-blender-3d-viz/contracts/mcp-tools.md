# MCP Tool Contracts: Blender 3D Visualization

**Feature**: 024-blender-3d-viz
**Date**: 2026-04-05

## Overview

This document defines the MCP tool interfaces used by the blender-3d-viz skill. These are contracts with the upstream `blender-mcp` package.

## Tools Used

### get_scene_info

**Purpose**: Retrieve current Blender scene state for verification.

**Parameters**: None

**Response**:
```json
{
  "objects": [
    {
      "name": "string",
      "type": "string",
      "location": [float, float, float],
      "rotation": [float, float, float],
      "scale": [float, float, float]
    }
  ],
  "active_object": "string | null"
}
```

**Usage**: Called before rendering to check existing objects, after rendering to verify creation.

---

### create_object

**Purpose**: Create a 3D primitive object in Blender.

**Parameters**:
```json
{
  "type": "cube | sphere | cylinder | cone | plane",
  "name": "string (optional)",
  "location": [float, float, float] (optional, default [0,0,0]),
  "scale": [float, float, float] (optional, default [1,1,1]),
  "rotation": [float, float, float] (optional, default [0,0,0])
}
```

**Response**:
```json
{
  "success": true,
  "object_name": "string"
}
```

**Usage**:
- Create cubes for network devices
- Create cylinders for connection links

**Example - Device**:
```json
{
  "type": "cube",
  "name": "router-1",
  "location": [0, 0, 0],
  "scale": [0.5, 0.5, 0.5]
}
```

**Example - Link**:
```json
{
  "type": "cylinder",
  "name": "link-router-1-switch-1",
  "location": [2.5, 0, 0],
  "scale": [0.05, 0.05, 2.5],
  "rotation": [0, 1.5708, 0]
}
```

---

### modify_object

**Purpose**: Transform an existing object's position, rotation, or scale.

**Parameters**:
```json
{
  "name": "string (required)",
  "location": [float, float, float] (optional),
  "rotation": [float, float, float] (optional),
  "scale": [float, float, float] (optional)
}
```

**Response**:
```json
{
  "success": true
}
```

**Usage**: Adjust device positions after initial layout calculation.

---

### set_material

**Purpose**: Apply color/material to an object.

**Parameters**:
```json
{
  "object_name": "string (required)",
  "color": [float, float, float] (RGB, 0.0-1.0),
  "metallic": float (optional, 0.0-1.0),
  "roughness": float (optional, 0.0-1.0)
}
```

**Response**:
```json
{
  "success": true
}
```

**Usage**: Color devices by type (router=blue, switch=green, etc.)

**Example**:
```json
{
  "object_name": "router-1",
  "color": [0.2, 0.4, 0.8],
  "metallic": 0.3,
  "roughness": 0.7
}
```

---

### execute_blender_code

**Purpose**: Run arbitrary Python code in Blender for complex operations.

**Parameters**:
```json
{
  "code": "string (Python code)"
}
```

**Response**:
```json
{
  "success": true,
  "output": "string (stdout if any)"
}
```

**Usage**:
- Add text labels to devices
- Clear scene before new topology
- Complex transformations not possible with primitives

**Example - Add Label**:
```python
import bpy
bpy.ops.object.text_add(location=(0, 0, 1))
obj = bpy.context.active_object
obj.data.body = "router-1"
obj.scale = (0.3, 0.3, 0.3)
```

**Example - Clear Scene**:
```python
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

---

## Error Handling Contract

All tools may return errors in this format:
```json
{
  "error": true,
  "message": "string"
}
```

**Common Error Conditions**:
- Blender not connected: `"Blender connection unavailable"`
- Object not found: `"Object '{name}' not found in scene"`
- Invalid parameters: `"Invalid parameter: {details}"`

## Skill-Level Wrappers

The blender-3d-viz skill SHOULD provide high-level natural language interfaces that map to these tools:

| Natural Language | MCP Tool Sequence |
|------------------|-------------------|
| "Draw the topology" | execute_blender_code (clear) → create_object × N → set_material × N |
| "Color router-1 red" | set_material(router-1, [0.8, 0.2, 0.2]) |
| "Add labels" | execute_blender_code (add text for each device) |
| "Export as PNG" | execute_blender_code (render to file) |
| "What's in the scene?" | get_scene_info |

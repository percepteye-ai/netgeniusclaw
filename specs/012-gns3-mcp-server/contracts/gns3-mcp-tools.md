# GNS3 MCP Server Tool Contracts

**Feature**: 012-gns3-mcp-server
**Date**: 2026-04-02
**Total Tools**: 23

## Tool Naming Convention

All tools follow the pattern: `gns3_<action>_<entity>`

Examples:
- `gns3_list_projects`
- `gns3_create_node`
- `gns3_start_capture`

---

## Skill: gns3-project-lifecycle (9 tools)

### gns3_list_projects

List all GNS3 projects on the server.

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "data": [
    {
      "project_id": "uuid",
      "name": "string",
      "status": "opened|closed",
      "path": "string",
      "auto_open": "boolean",
      "created_at": "datetime"
    }
  ],
  "count": "integer"
}
```

---

### gns3_create_project

Create a new GNS3 project.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Project name (unique) |
| auto_open | boolean | No | Open project on server start (default: false) |
| auto_close | boolean | No | Close when unused (default: false) |
| auto_start | boolean | No | Start nodes when opened (default: false) |

**Returns**:
```json
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "name": "string",
    "status": "opened",
    "path": "string"
  },
  "message": "Project 'name' created successfully"
}
```

---

### gns3_get_project

Get details of a specific project.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "name": "string",
    "status": "opened|closed",
    "path": "string",
    "scene_width": "integer",
    "scene_height": "integer",
    "zoom": "integer",
    "auto_open": "boolean",
    "auto_close": "boolean",
    "auto_start": "boolean"
  }
}
```

---

### gns3_open_project

Open a closed project.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "name": "string",
    "status": "opened"
  },
  "message": "Project 'name' opened"
}
```

---

### gns3_close_project

Close an opened project and release resources.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "name": "string",
    "status": "closed"
  },
  "message": "Project 'name' closed"
}
```

---

### gns3_delete_project

Delete a project and all its resources.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |

**Returns**:
```json
{
  "success": true,
  "message": "Project 'name' deleted"
}
```

---

### gns3_clone_project

Create a copy of an existing project.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Source project UUID or name |
| new_name | string | Yes | Name for the cloned project |
| reset_mac_addresses | boolean | No | Generate new MAC addresses (default: true) |

**Returns**:
```json
{
  "success": true,
  "data": {
    "project_id": "uuid (new)",
    "name": "string",
    "status": "closed"
  },
  "message": "Project cloned as 'new_name'"
}
```

---

### gns3_export_project

Export a project as a portable archive.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| include_snapshots | boolean | No | Include snapshots (default: true) |
| include_images | boolean | No | Include disk images (default: false) |
| compression | string | No | Compression type: none, zip, gzip (default: zip) |

**Returns**:
```json
{
  "success": true,
  "data": {
    "export_path": "string",
    "file_size": "integer"
  },
  "message": "Project exported to 'path'"
}
```

---

### gns3_import_project

Import a project from an archive.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file_path | string | Yes | Path to project archive |
| name | string | No | Override project name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "name": "string",
    "status": "closed"
  },
  "message": "Project 'name' imported"
}
```

---

## Skill: gns3-node-operations (7 tools)

### gns3_list_nodes

List all nodes in a project.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": [
    {
      "node_id": "uuid",
      "name": "string",
      "node_type": "string",
      "status": "started|stopped|suspended",
      "console": "integer",
      "console_type": "telnet|vnc|http|https|none",
      "console_host": "string"
    }
  ],
  "count": "integer"
}
```

---

### gns3_create_node

Create a node from a template.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| template | string | Yes | Template name or ID (fuzzy match supported) |
| name | string | No | Node name (auto-generated if not provided) |
| x | integer | No | Canvas X position (default: 0) |
| y | integer | No | Canvas Y position (default: 0) |
| compute_id | string | No | Target compute (default: "local") |

**Returns**:
```json
{
  "success": true,
  "data": {
    "node_id": "uuid",
    "name": "string",
    "node_type": "string",
    "status": "stopped",
    "console": "integer",
    "console_type": "string",
    "ports": [...]
  },
  "message": "Node 'name' created from template 'template'"
}
```

---

### gns3_start_node

Start a node (power on).

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| node_id | string | Yes | Node UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "node_id": "uuid",
    "name": "string",
    "status": "started"
  },
  "message": "Node 'name' started"
}
```

---

### gns3_stop_node

Stop a node (power off).

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| node_id | string | Yes | Node UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "node_id": "uuid",
    "name": "string",
    "status": "stopped"
  },
  "message": "Node 'name' stopped"
}
```

---

### gns3_suspend_node

Suspend a node (save state).

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| node_id | string | Yes | Node UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "node_id": "uuid",
    "name": "string",
    "status": "suspended"
  },
  "message": "Node 'name' suspended"
}
```

---

### gns3_reload_node

Reload a node (restart).

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| node_id | string | Yes | Node UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "node_id": "uuid",
    "name": "string",
    "status": "started"
  },
  "message": "Node 'name' reloaded"
}
```

---

### gns3_bulk_node_action

Perform an action on all nodes in a project.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| action | string | Yes | Action: start, stop, suspend, reload |

**Returns**:
```json
{
  "success": true,
  "data": {
    "affected_nodes": "integer",
    "action": "string"
  },
  "message": "Action 'action' applied to N nodes"
}
```

---

## Skill: gns3-link-management (4 tools)

### gns3_list_links

List all links in a project.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": [
    {
      "link_id": "uuid",
      "nodes": [
        {"node_id": "uuid", "node_name": "string", "adapter_number": 0, "port_number": 0},
        {"node_id": "uuid", "node_name": "string", "adapter_number": 0, "port_number": 0}
      ],
      "suspend": "boolean",
      "capturing": "boolean"
    }
  ],
  "count": "integer"
}
```

---

### gns3_create_link

Create a link between two node interfaces.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| node1 | string | Yes | First node UUID or name |
| port1 | string | Yes | First node interface (e.g., "eth0", "Gi0/0") |
| node2 | string | Yes | Second node UUID or name |
| port2 | string | Yes | Second node interface |

**Returns**:
```json
{
  "success": true,
  "data": {
    "link_id": "uuid",
    "nodes": [...]
  },
  "message": "Link created between node1:port1 and node2:port2"
}
```

---

### gns3_delete_link

Delete a link between nodes.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| link_id | string | Yes | Link UUID |

**Returns**:
```json
{
  "success": true,
  "message": "Link deleted"
}
```

---

### gns3_isolate_node

Disable all links to a node (isolate without deleting).

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| node_id | string | Yes | Node UUID or name |
| isolate | boolean | Yes | true = isolate, false = unisolate |

**Returns**:
```json
{
  "success": true,
  "data": {
    "node_id": "uuid",
    "node_name": "string",
    "isolated": "boolean",
    "affected_links": "integer"
  },
  "message": "Node 'name' isolated/unisolated"
}
```

---

## Skill: gns3-packet-capture (3 tools)

### gns3_start_capture

Start packet capture on a link.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| link_id | string | Yes | Link UUID |
| capture_file_name | string | No | Custom PCAP filename |

**Returns**:
```json
{
  "success": true,
  "data": {
    "link_id": "uuid",
    "capturing": true,
    "capture_file_name": "string",
    "capture_file_path": "string"
  },
  "message": "Capture started on link"
}
```

---

### gns3_stop_capture

Stop packet capture on a link.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| link_id | string | Yes | Link UUID |

**Returns**:
```json
{
  "success": true,
  "data": {
    "link_id": "uuid",
    "capturing": false,
    "capture_file_path": "string"
  },
  "message": "Capture stopped. PCAP available at: path"
}
```

---

### gns3_get_capture

Get capture file path or stream info for a link.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| link_id | string | Yes | Link UUID |

**Returns**:
```json
{
  "success": true,
  "data": {
    "link_id": "uuid",
    "capturing": "boolean",
    "capture_file_path": "string",
    "stream_url": "string (if capturing)"
  },
  "message": "Capture info retrieved"
}
```

---

## Skill: gns3-snapshot-ops (4 tools)

### gns3_list_snapshots

List all snapshots for a project.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": [
    {
      "snapshot_id": "uuid",
      "name": "string",
      "created_at": "datetime"
    }
  ],
  "count": "integer"
}
```

---

### gns3_create_snapshot

Create a snapshot of the current project state.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| name | string | Yes | Snapshot name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "snapshot_id": "uuid",
    "name": "string",
    "created_at": "datetime"
  },
  "message": "Snapshot 'name' created"
}
```

---

### gns3_restore_snapshot

Restore a project to a previous snapshot state.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| snapshot_id | string | Yes | Snapshot UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "snapshot_id": "uuid",
    "snapshot_name": "string",
    "project_id": "uuid"
  },
  "message": "Project restored to snapshot 'name'"
}
```

---

### gns3_delete_snapshot

Delete a snapshot.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| snapshot_id | string | Yes | Snapshot UUID or name |

**Returns**:
```json
{
  "success": true,
  "message": "Snapshot 'name' deleted"
}
```

---

## Utility Tools (not skill-specific)

### gns3_list_templates

List available node templates.

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "data": [
    {
      "template_id": "uuid",
      "name": "string",
      "template_type": "string",
      "category": "router|switch|guest|firewall|multilayer_switch",
      "builtin": "boolean"
    }
  ],
  "count": "integer"
}
```

---

### gns3_list_computes

List available compute servers.

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "data": [
    {
      "compute_id": "string",
      "name": "string",
      "host": "string",
      "port": "integer",
      "protocol": "http|https",
      "connected": "boolean",
      "cpu_usage_percent": "float",
      "memory_usage_percent": "float"
    }
  ],
  "count": "integer"
}
```

---

### gns3_get_node_console

Get console connection information for a node.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_id | string | Yes | Project UUID or name |
| node_id | string | Yes | Node UUID or name |

**Returns**:
```json
{
  "success": true,
  "data": {
    "node_id": "uuid",
    "node_name": "string",
    "console": "integer",
    "console_type": "telnet|vnc|http|https|none",
    "console_host": "string",
    "connection_string": "telnet host port"
  },
  "message": "Console: telnet host port"
}
```

---

## Error Responses

All tools return consistent error format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "GNS3_ERROR_CODE",
  "status_code": 404
}
```

**Common Error Codes**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| GNS3_NOT_FOUND | 404 | Resource (project/node/link/snapshot) not found |
| GNS3_CONFLICT | 409 | Resource conflict (locked, already exists, etc.) |
| GNS3_VALIDATION | 422 | Invalid parameters |
| GNS3_FORBIDDEN | 403 | Insufficient privileges |
| GNS3_AUTH_FAILED | 401 | Authentication failed |
| GNS3_SERVER_ERROR | 500 | GNS3 server internal error |
| GNS3_UNREACHABLE | 503 | GNS3 server unreachable |

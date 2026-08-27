# Data Model: GNS3 MCP Server

**Feature**: 012-gns3-mcp-server
**Date**: 2026-04-02
**Source**: GNS3 REST API v3 OpenAPI specification

## Entities

### Project

A GNS3 lab environment containing nodes, links, and topology configuration.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| project_id | UUID | Unique identifier | Read-only, auto-generated |
| name | string | Project display name | Required, max 255 chars |
| status | enum | Current state | `opened`, `closed` |
| path | string | File system path | Read-only |
| filename | string | Project file name | Read-only |
| auto_open | boolean | Open on server start | Default: false |
| auto_close | boolean | Close when unused | Default: false |
| auto_start | boolean | Start nodes on open | Default: false |
| scene_width | integer | Canvas width | Default: 2000 |
| scene_height | integer | Canvas height | Default: 1000 |
| zoom | integer | Canvas zoom level | Default: 100 |
| created_at | datetime | Creation timestamp | Read-only |
| updated_at | datetime | Last modified | Read-only |

**State Transitions**:
- `closed` → `opened` (via open)
- `opened` → `closed` (via close)

### Node

A network device instance within a project (router, switch, firewall, etc.).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| node_id | UUID | Unique identifier | Read-only, auto-generated |
| project_id | UUID | Parent project | Required, foreign key |
| compute_id | string | Compute server | Required (e.g., "local") |
| name | string | Node display name | Required, unique in project |
| node_type | string | Emulator type | Required (qemu, docker, vpcs, etc.) |
| template_id | UUID | Source template | Optional, reference |
| status | enum | Power state | `stopped`, `started`, `suspended` |
| console | integer | Console port | Read-only, auto-assigned |
| console_type | enum | Console protocol | `telnet`, `vnc`, `http`, `https`, `none` |
| console_host | string | Console server | Read-only |
| x | integer | Canvas X position | Default: 0 |
| y | integer | Canvas Y position | Default: 0 |
| z | integer | Canvas Z order | Default: 1 |
| width | integer | Symbol width | Read-only |
| height | integer | Symbol height | Read-only |
| symbol | string | Icon path | Optional |
| label | object | Label configuration | Optional |
| ports | array | Interface list | Read-only |
| properties | object | Node-specific config | Varies by node_type |
| locked | boolean | Position locked | Default: false |
| first_port_name | string | First interface name | Optional |
| port_name_format | string | Interface naming | Optional |
| port_segment_size | integer | Port group size | Optional |

**State Transitions**:
- `stopped` → `started` (via start)
- `started` → `stopped` (via stop)
- `started` → `suspended` (via suspend)
- `suspended` → `started` (via start)
- `*` → `stopped` (via reload, then restart)

### Link

A connection between two node interfaces.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| link_id | UUID | Unique identifier | Read-only, auto-generated |
| project_id | UUID | Parent project | Required, foreign key |
| nodes | array | Connected endpoints | Required, exactly 2 |
| nodes[].node_id | UUID | Node reference | Required |
| nodes[].adapter_number | integer | Interface adapter | Required |
| nodes[].port_number | integer | Interface port | Required |
| nodes[].label | object | Label config | Optional |
| suspend | boolean | Link disabled | Default: false |
| filters | object | Traffic filters | Optional |
| capturing | boolean | Capture active | Read-only |
| capture_file_name | string | PCAP filename | Read-only (when capturing) |
| capture_file_path | string | PCAP file path | Read-only (when capturing) |
| capture_compute_id | string | Capture server | Read-only |
| link_style | object | Visual styling | Optional |
| link_type | string | Connection type | Read-only |

**State Transitions**:
- `suspend: false` → `suspend: true` (via isolate)
- `suspend: true` → `suspend: false` (via unisolate)
- `capturing: false` → `capturing: true` (via capture start)
- `capturing: true` → `capturing: false` (via capture stop)

### Template

A device definition that can be instantiated as nodes.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| template_id | UUID | Unique identifier | Read-only, auto-generated |
| name | string | Template name | Required |
| template_type | string | Device type | Required (qemu, docker, etc.) |
| category | enum | Device category | `router`, `switch`, `guest`, `firewall`, `multilayer_switch` |
| compute_id | string | Target compute | Default: "local" |
| symbol | string | Icon path | Optional |
| builtin | boolean | System template | Read-only |
| default_name_format | string | Node naming pattern | Optional |
| version | string | Template version | Read-only |
| (type-specific fields) | various | Per-template config | Varies by template_type |

### Snapshot

A saved state of a project that can be restored.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| snapshot_id | UUID | Unique identifier | Read-only, auto-generated |
| project_id | UUID | Parent project | Required, foreign key |
| name | string | Snapshot name | Required |
| created_at | datetime | Creation timestamp | Read-only |

**State Transitions**:
- Created via snapshot create
- Deleted via snapshot delete
- Applied via snapshot restore (project state changes)

### Compute

A server that runs node emulations (QEMU, Docker, VirtualBox, VMware, Dynamips).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| compute_id | string | Unique identifier | Required (e.g., "local", UUID) |
| name | string | Display name | Required |
| protocol | enum | Connection protocol | `http`, `https` |
| host | string | Server hostname/IP | Required |
| port | integer | Server port | Default: 3080 |
| user | string | Username | Optional |
| connected | boolean | Connection status | Read-only |
| cpu_usage_percent | float | CPU utilization | Read-only |
| memory_usage_percent | float | Memory utilization | Read-only |
| disk_usage_percent | float | Disk utilization | Read-only |
| last_error | string | Last error message | Read-only |
| capabilities | object | Supported features | Read-only |

## Entity Relationships

```
Project (1) ────────── (*) Node
    │                      │
    │                      │ (via link.nodes[])
    │                      ▼
    ├──────────────── (*) Link
    │
    └──────────────── (*) Snapshot

Template (1) ──────── (*) Node (created from)

Compute (1) ────────── (*) Node (runs on)
```

## Validation Rules

### Project
- Name must be non-empty and ≤255 characters
- Name must be unique across all projects on the server
- Cannot delete an opened project (must close first)

### Node
- Name must be unique within the project
- compute_id must reference an existing, connected compute
- Template must exist if template_id is provided
- Cannot start a node without sufficient compute resources
- Cannot delete a node with active links (links auto-deleted)

### Link
- Exactly 2 node endpoints required
- Both nodes must exist in the same project
- Interface must not already be connected to another link
- Cannot create link to a non-existent node interface

### Snapshot
- Name must be non-empty
- Name must be unique within the project
- Cannot restore snapshot on a project with running nodes (stops them first)

### Compute
- Host must be reachable for connection
- Only one "local" compute allowed
- Cannot delete compute with running nodes

## Response Formats

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "GNS3_ERROR_CODE",
  "status_code": 404
}
```

### List Response
```json
{
  "success": true,
  "data": [ ... ],
  "count": 5,
  "message": "Retrieved 5 items"
}
```

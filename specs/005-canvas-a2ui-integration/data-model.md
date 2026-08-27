# Data Model: Canvas / A2UI Integration

**Feature**: 005-canvas-a2ui-integration
**Date**: 2026-03-26

## Entities

### CanvasVisualization

The root entity for any inline visualization rendered via A2UI.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique visualization instance ID |
| `type` | enum | Yes | One of: `topology`, `dashboard`, `alert`, `timeline`, `diff`, `path-trace`, `scorecard` |
| `title` | string | Yes | Human-readable title displayed above the visualization |
| `timestamp` | ISO 8601 | Yes | When the visualization was generated |
| `dataSources` | DataSourceRef[] | Yes | Which MCP servers provided data |
| `scope` | Scope | Yes | What subset of the network is visualized |
| `content` | object | Yes | Type-specific visualization payload (see sub-entities) |
| `warnings` | Warning[] | No | Degradation/staleness warnings |

### DataSourceRef

Tracks which MCP servers contributed data to a visualization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server` | string | Yes | MCP server name (e.g., `pyats`, `grafana`, `prometheus`, `servicenow`) |
| `tool` | string | Yes | Specific MCP tool invoked (e.g., `pyats_show_cdp_neighbors`) |
| `status` | enum | Yes | `ok`, `partial`, `unavailable` |
| `fetchedAt` | ISO 8601 | Yes | When the data was retrieved |
| `latencyMs` | number | No | Round-trip time for the data fetch |

### Scope

Defines the filtering/scoping applied to the visualization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `devices` | string[] | No | Specific device hostnames included |
| `sites` | string[] | No | Site names included |
| `roles` | string[] | No | Device roles included (e.g., `spine`, `leaf`, `router`) |
| `severities` | string[] | No | Severity levels included (for alerts) |
| `timeRange` | TimeRange | No | Start/end time filter |

### TimeRange

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | ISO 8601 | Yes | Start of time window |
| `end` | ISO 8601 | Yes | End of time window |

### Warning

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `level` | enum | Yes | `info`, `warning`, `error` |
| `message` | string | Yes | Human-readable warning text |
| `source` | string | No | Which data source or component generated the warning |

---

## Visualization-Specific Content Models

### TopologyContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `nodes` | TopologyNode[] | Yes | Devices in the topology |
| `edges` | TopologyEdge[] | Yes | Neighbor relationships |
| `clusters` | TopologyCluster[] | No | Site-based groupings (for large topologies) |
| `legend` | LegendEntry[] | Yes | Color legend mapping |

### TopologyNode

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Device hostname |
| `label` | string | Yes | Display label |
| `role` | string | No | Device role (spine, leaf, router, switch, firewall) |
| `site` | string | No | Site name |
| `health` | enum | Yes | `healthy`, `warning`, `critical`, `unknown` |
| `metrics` | NodeMetrics | No | Key metric values for tooltip/drill-down |
| `x` | number | No | Layout X position (computed by graph-layout.js) |
| `y` | number | No | Layout Y position (computed by graph-layout.js) |

### NodeMetrics

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cpuPercent` | number | No | CPU utilization percentage |
| `memoryPercent` | number | No | Memory utilization percentage |
| `interfaceErrors` | number | No | Total interface error count |
| `bgpPeersUp` | number | No | Count of established BGP peers |
| `bgpPeersTotal` | number | No | Total configured BGP peers |
| `ospfAdjacenciesUp` | number | No | Count of full OSPF adjacencies |

### TopologyEdge

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Source device hostname |
| `target` | string | Yes | Target device hostname |
| `sourceInterface` | string | Yes | Source interface name |
| `targetInterface` | string | Yes | Target interface name |
| `protocol` | string | Yes | Discovery protocol (CDP, LLDP) |
| `status` | enum | Yes | `up`, `down`, `unknown` |

### TopologyCluster

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Cluster identifier (site name) |
| `label` | string | Yes | Display label |
| `nodeIds` | string[] | Yes | Device hostnames in this cluster |
| `expanded` | boolean | Yes | Whether cluster is initially expanded |

### LegendEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `color` | string | Yes | CSS color value |
| `label` | string | Yes | Legend text (e.g., "Healthy", "Warning", "Critical") |

---

### DashboardContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `panels` | DashboardPanel[] | Yes | Metric panels to display |
| `deviceSummary` | string | No | Summary text for the dashboard target |

### DashboardPanel

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Panel identifier |
| `title` | string | Yes | Panel heading (e.g., "CPU Utilization", "BGP Peers") |
| `type` | enum | Yes | `gauge`, `counter`, `status-list`, `bar`, `sparkline` |
| `value` | number or string | Yes | Current metric value |
| `unit` | string | No | Unit label (e.g., "%", "errors", "peers") |
| `threshold` | ThresholdConfig | No | Warning/critical thresholds for coloring |
| `items` | StatusItem[] | No | For status-list type: list of items with individual status |

### ThresholdConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `warning` | number | Yes | Value at which amber warning begins |
| `critical` | number | Yes | Value at which red critical begins |

### StatusItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Item name (e.g., peer IP, interface name) |
| `status` | enum | Yes | `up`, `down`, `warning`, `unknown` |
| `detail` | string | No | Additional detail text |

---

### AlertContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `summary` | AlertSummary | Yes | Severity counts and total |
| `alerts` | AlertCard[] | Yes | Individual alert cards, sorted by severity |
| `filter` | string | No | Active filter description (if filtered) |
| `unfilteredCount` | number | No | Total alerts before filtering |

### AlertSummary

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `critical` | number | Yes | Count of critical alerts |
| `warning` | number | Yes | Count of warning alerts |
| `info` | number | Yes | Count of informational alerts |
| `total` | number | Yes | Total alert count |

### AlertCard

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Alert identifier |
| `name` | string | Yes | Alert name/rule name |
| `severity` | enum | Yes | `critical`, `warning`, `info` |
| `source` | string | Yes | Source system (Grafana, Prometheus, syslog) |
| `device` | string | No | Affected device hostname |
| `interface` | string | No | Affected interface (if applicable) |
| `description` | string | Yes | Alert description |
| `triggeredAt` | ISO 8601 | Yes | When the alert fired |

---

### TimelineContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `changeRequests` | ChangeRequestTimeline[] | Yes | CR timeline entries |

### ChangeRequestTimeline

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `crNumber` | string | Yes | ServiceNow CR number (e.g., CR-12345) |
| `description` | string | Yes | CR description |
| `assignee` | string | No | Assigned engineer |
| `scheduledWindow` | TimeRange | No | Planned implementation window |
| `stages` | TimelineStage[] | Yes | Lifecycle stages |
| `currentStage` | string | Yes | Current active stage name |
| `status` | enum | Yes | `in-progress`, `completed`, `rejected`, `rolled-back` |
| `rejectionReason` | string | No | Reason if rejected/rolled-back |
| `linkedIncident` | string | No | Related incident number |

### TimelineStage

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Stage name (assess, authorize, implement, review) |
| `status` | enum | Yes | `completed`, `active`, `pending`, `skipped`, `failed` |
| `completedAt` | ISO 8601 | No | When stage completed |

---

### DiffContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `diffType` | enum | Yes | `config`, `routing`, `acl` |
| `device` | string | Yes | Device hostname |
| `before` | string | No | Label for the "before" state |
| `after` | string | No | Label for the "after" state |
| `hunks` | DiffHunk[] | Yes | Diff sections |

### DiffHunk

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `header` | string | No | Section header (e.g., "interface GigabitEthernet0/1") |
| `lines` | DiffLine[] | Yes | Individual diff lines |

### DiffLine

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | enum | Yes | `added`, `removed`, `context` |
| `content` | string | Yes | Line text |
| `lineNumber` | number | No | Line number in original/new file |

---

### PathTraceContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Source IP address |
| `destination` | string | Yes | Destination IP address |
| `paths` | TracePath[] | Yes | One or more forwarding paths (ECMP) |
| `blackHole` | BlackHoleInfo | No | Present if path trace encountered a black hole |

### TracePath

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Path identifier (for ECMP: "path-1", "path-2") |
| `hops` | TraceHop[] | Yes | Ordered list of hops |
| `isEcmp` | boolean | No | Whether this is one of multiple equal-cost paths |

### TraceHop

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order` | number | Yes | Hop number (1-based) |
| `device` | string | Yes | Device hostname |
| `ingressInterface` | string | Yes | Ingress interface |
| `egressInterface` | string | Yes | Egress interface |
| `nextHop` | string | Yes | Next-hop IP address |
| `action` | string | No | Routing decision (e.g., "longest-match", "default-route") |

### BlackHoleInfo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lastHop` | string | Yes | Last device hostname before failure |
| `lastInterface` | string | Yes | Last interface before failure |
| `reason` | string | Yes | Reason for black hole (e.g., "no route to destination") |

---

### ScorecardContent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `level` | enum | Yes | `site`, `device` |
| `entries` | ScorecardEntry[] | Yes | Health score entries |

### ScorecardEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Device or site name |
| `overallHealth` | enum | Yes | `healthy`, `warning`, `critical`, `unknown` |
| `score` | number | Yes | Composite health score (0-100) |
| `indicators` | HealthIndicator[] | Yes | Individual health metrics |
| `drillDown` | boolean | Yes | Whether this entry supports expansion to detail view |

### HealthIndicator

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Indicator name (e.g., "CPU", "Memory", "BGP", "Interfaces") |
| `status` | enum | Yes | `healthy`, `warning`, `critical`, `unknown` |
| `value` | string | Yes | Current value as display string |

---

## State Transitions

### Visualization Lifecycle

```
request_received → fetching_data → rendering → displayed
                      │                           │
                      ▼                           ▼
                 partial_data              gait_logged
                      │
                      ▼
              degraded_display → gait_logged
```

### Alert Card Severity Mapping

| Source | Source Level | Mapped Severity |
|--------|------------|-----------------|
| Prometheus | `critical` | `critical` |
| Prometheus | `warning` | `warning` |
| Grafana | `alerting` | `critical` |
| Grafana | `pending` | `warning` |
| Syslog | 0-2 (Emergency/Alert/Critical) | `critical` |
| Syslog | 3-4 (Error/Warning) | `warning` |
| Syslog | 5-7 (Notice/Info/Debug) | `info` |

### Health Score Calculation

```
score = weighted_average(
  cpu_score     * 0.20,   # 100 - cpu_percent
  memory_score  * 0.20,   # 100 - memory_percent
  interface_score * 0.25, # (up_interfaces / total_interfaces) * 100
  bgp_score     * 0.20,   # (established_peers / total_peers) * 100
  ospf_score    * 0.15    # (full_adjacencies / total_adjacencies) * 100
)
```

Missing indicators are excluded and weights redistributed proportionally.

## Validation Rules

- `CanvasVisualization.type` must be one of the 7 defined enum values.
- `CanvasVisualization.dataSources` must contain at least one entry.
- `TopologyNode.health` computed from `NodeMetrics` thresholds (warning: 70%, critical: 90%).
- `AlertCard.severity` must be derived from source-specific mapping, never assumed.
- `ScorecardEntry.score` must be 0-100 integer, computed from available indicators only.
- `DiffLine.type` must be one of `added`, `removed`, `context` — no mixed types.
- `TraceHop.order` must be sequential starting at 1 with no gaps.
- All timestamps must be valid ISO 8601 with timezone (UTC preferred).

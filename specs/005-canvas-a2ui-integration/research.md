# Research: Canvas / A2UI Integration

**Feature**: 005-canvas-a2ui-integration
**Date**: 2026-03-26
**Status**: Complete

## Research Tasks

### 1. OpenClaw Canvas/A2UI Rendering Primitives

**Decision**: Use A2UI JSON output format to declare visualization artifacts that the OpenClaw Canvas runtime renders inline in the chat interface. The skill produces structured JSON describing the visualization (type, data, layout, styling), and the Canvas framework handles the actual DOM rendering.

**Rationale**: A2UI is the agent-to-UI communication protocol in OpenClaw. By outputting A2UI JSON, the skill delegates rendering to the framework and remains decoupled from specific rendering implementation details. This is the standard pattern for OpenClaw skills that produce visual output.

**Alternatives Considered**:
- Direct HTML injection into chat: Rejected — bypasses the Canvas framework and may break with framework updates.
- Server-side image generation (SVG/PNG): Rejected — loses interactivity and increases latency. A2UI supports interactive components natively.
- Embedding an iframe to a separate visualization server: Rejected — violates FR-008 (must render inline, not in separate tab/window) and adds infrastructure complexity.

### 2. Graph Layout for Topology Maps

**Decision**: Implement a simple force-directed layout algorithm in JavaScript within `graph-layout.js`. For large topologies (200+ nodes), use hierarchical layout with spine/leaf detection heuristics based on device role metadata.

**Rationale**: Network topologies have well-understood structural patterns (spine-leaf, hub-spoke, ring). A force-directed layout handles arbitrary topologies well, while hierarchical layout leverages device roles (from pyATS/NetBox) for cleaner presentation of structured fabrics. Keeping the layout engine local avoids external dependencies.

**Alternatives Considered**:
- D3.js force simulation: Rejected — adds a large dependency for a single use case. The layout algorithm is straightforward to implement for the expected scale (up to 500 nodes).
- Server-side layout (Graphviz/dot): Rejected — requires additional server infrastructure and increases latency.
- Cytoscape.js: Rejected — heavyweight library for the rendering needs. A2UI Canvas primitives are sufficient.

### 3. Data Fetching Strategy from MCP Servers

**Decision**: Use a `data-fetcher.js` abstraction that invokes existing MCP server tools via the OpenClaw agent's tool-calling mechanism. The skill requests data by calling MCP tools (e.g., `pyats_show_cdp_neighbors`, `grafana_query_prometheus`, `servicenow_get_change_request`) and transforms the responses into visualization-ready data structures.

**Rationale**: The skill runs within the OpenClaw agent context and has access to all registered MCP tools. Direct tool invocation is the standard pattern for skills that compose data from multiple sources. No new connections or APIs needed.

**Alternatives Considered**:
- Direct HTTP calls to MCP servers: Rejected — bypasses the agent's MCP tool abstraction and authentication.
- Caching layer between MCP servers and visualization: Rejected — adds complexity; MCP servers already manage their own caching (e.g., Meraki ENABLE_CACHING). Data staleness addressed by timestamp display.

### 4. Health-to-Color Mapping Standard

**Decision**: Use a three-tier color scale (green/amber/red) with an additional gray for unknown/unreachable state. Thresholds: green (healthy, all metrics normal), amber (warning, any metric exceeds 70% utilization or has non-critical alerts), red (critical, any metric exceeds 90% utilization, interface down, protocol adjacency lost). Color values follow WCAG 2.1 AA contrast requirements.

**Rationale**: Three-tier severity is the network operations standard (matches Grafana, Prometheus alertmanager, and syslog severity mapping). Gray for unknown prevents false positive/negative visual signals. WCAG compliance ensures readability for operators with color vision deficiencies.

**Alternatives Considered**:
- Five-tier scale (critical/high/medium/low/info): Rejected — too granular for at-a-glance topology view. Three tiers are sufficient for the primary use case. Alert cards use the finer granularity.
- Custom color palette per operator: Rejected — unnecessary complexity for initial release. Can be added later via configuration.

### 5. GAIT Audit Logging for Visualization Events

**Decision**: Emit a GAIT log entry for each visualization generation event. The log entry includes: visualization type, data sources consulted, scope (device list, site, role filter), timestamp, and rendering duration. Use the existing `gait-session-tracking` skill's logging mechanism.

**Rationale**: FR-011 and SC-006 mandate 100% GAIT audit coverage. Visualization events are operational decisions (which data was shown, to whom, when) and must be traceable. Using the existing GAIT infrastructure avoids building a separate audit mechanism.

**Alternatives Considered**:
- Logging only on errors: Rejected — violates Constitution Principle IV (no silent operations) and FR-011 (all events logged).
- Separate audit log file: Rejected — GAIT is the single audit trail; creating a parallel log would fragment audit history.

### 6. Graceful Degradation Strategy

**Decision**: When a data source is unavailable, render the visualization with available data and include a "Data Source Unavailable" indicator panel listing which sources failed and when they were last reachable. The visualization is never fully blank — at minimum, the layout/structure renders with placeholder markers.

**Rationale**: FR-012 requires graceful degradation. Network operators expect partial information over no information. Explicit "unavailable" indicators prevent operators from mistakenly assuming the absence of data means the absence of problems.

**Alternatives Considered**:
- Blocking render until all sources respond: Rejected — any single MCP server timeout would block all visualization.
- Rendering without any unavailability indication: Rejected — operators could misinterpret missing data as "all clear."

### 7. Large Topology Handling (500+ Nodes)

**Decision**: For topologies exceeding 200 nodes, automatically apply site-based clustering. Nodes are grouped by site (from NetBox/pyATS metadata) and rendered as expandable cluster nodes. The operator can expand a cluster to see individual devices. If no site metadata is available, the system warns that the topology is large and suggests applying a filter.

**Rationale**: Rendering 500+ individual nodes in an inline chat visualization exceeds visual comprehension limits. Site-based clustering mirrors how operators think about large networks (by site/region). This directly addresses the edge case in the spec about 500+ node topologies.

**Alternatives Considered**:
- Hard limit with error message: Rejected — unhelpful; operators need to see something even for large networks.
- Automatic zoom/pan with all nodes visible: Rejected — inline chat visualization has limited viewport; pan/zoom interaction is limited in A2UI.

### 8. Coexistence with Three.js HUD

**Decision**: The Canvas/A2UI skill operates entirely within the OpenClaw chat interface. It shares NO code, state, or rendering context with the Three.js HUD at `ui/netclaw-visual/`. The Three.js HUD continues to serve as the immersive 3D visualization accessed via its own URL. A new HUD node will be added to represent the Canvas visualization capability in the HUD's system topology view.

**Rationale**: FR-009 and SC-005 require coexistence without interference. Complete separation ensures neither system can break the other. The HUD node addition satisfies Constitution Principle XI (artifact coherence).

**Alternatives Considered**:
- Shared data layer between HUD and Canvas: Rejected — coupling creates risk of breaking the HUD when modifying Canvas components.
- Replacing HUD with Canvas: Rejected — explicitly prohibited by FR-009 and spec assumptions.

# Feature Specification: OpenClaw Canvas / A2UI Integration

**Feature Branch**: `005-canvas-a2ui-integration`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "OpenClaw Canvas A2UI Integration - Leverage OpenClaw Canvas and A2UI to render real-time network dashboards, topology maps, and alert panels natively in the OpenClaw interface."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Render Network Topology Maps Inline (Priority: P1)

As a network engineer, I want to see an auto-generated network topology
map rendered directly in the OpenClaw chat interface from CDP/LLDP
discovery data, color-coded by device health status, so I can
understand the physical and logical layout of my network without
switching to a separate browser tab or external tool.

**Why this priority**: Topology visualization is the foundational
visual capability. It transforms raw discovery data into an
immediately comprehensible picture of the network. Every other
visualization (path traces, diffs, alerts) benefits from having a
topology context. This is also the highest-impact demonstration of
Canvas/A2UI value over plain text output.

**Independent Test**: Can be fully tested by asking "show me the
network topology" after CDP/LLDP discovery data has been collected,
and verifying that an inline visual map appears with devices as
nodes, links as edges, and health-based color coding.

**Acceptance Scenarios**:

1. **Given** CDP/LLDP discovery data is available from the pyATS
   MCP server for a network with 5+ devices,
   **When** the operator requests "show me the network topology",
   **Then** the system renders an inline Canvas visualization
   showing each device as a labeled node, each discovered neighbor
   relationship as a connecting edge, and a color legend mapping
   device health states to colors.

2. **Given** CDP/LLDP discovery data is available and some devices
   report critical health (high CPU, interface errors, or down BGP
   peers),
   **When** the topology map is rendered,
   **Then** unhealthy devices are visually distinguished from healthy
   devices through color coding (e.g., red for critical, amber for
   warning, green for healthy) and the operator can identify
   problem areas at a glance.

3. **Given** CDP/LLDP discovery data is available,
   **When** the operator requests a topology map filtered by site
   or device role (e.g., "show topology for Site-A" or "show spine
   topology"),
   **Then** the system renders only the matching subset of devices
   and their interconnections, omitting unrelated devices.

4. **Given** no CDP/LLDP discovery data has been collected yet,
   **When** the operator requests a topology map,
   **Then** the system returns a clear message explaining that
   discovery data is required and suggests running a discovery
   operation first, rather than rendering an empty or broken
   visualization.

5. **Given** a topology map has been rendered,
   **When** the operator asks a follow-up question about a specific
   device visible in the map,
   **Then** the agent can reference the topology context and provide
   device-specific details without requiring the operator to
   re-specify the device hostname.

---

### User Story 2 - Display Real-Time Dashboard Panels (Priority: P2)

As a network engineer, I want to see real-time dashboard panels
showing interface counters, BGP peer status, OSPF adjacency state,
and CPU/memory metrics rendered inline in the OpenClaw chat, so I
can monitor device health without switching to Grafana or logging
into individual devices.

**Why this priority**: Dashboard panels are the second most
requested visualization after topology. They provide the operational
heartbeat of the network and are used continuously during
monitoring, maintenance windows, and incident response. They rely
on data already collected by Grafana, Prometheus, and pyATS MCP
servers.

**Independent Test**: Can be tested by requesting "show me a health
dashboard for router R1" and verifying that inline panels appear
with current metric values for key indicators.

**Acceptance Scenarios**:

1. **Given** Grafana/Prometheus metrics and pyATS data are available
   for a device,
   **When** the operator requests "show health dashboard for R1",
   **Then** the system renders inline Canvas panels displaying
   CPU utilization, memory usage, interface error counters, BGP
   peer states, and OSPF adjacency states with current values.

2. **Given** metric data is available for multiple devices at a site,
   **When** the operator requests "show site dashboard for Site-A",
   **Then** the system renders a multi-device summary panel showing
   per-device health indicators and aggregate statistics.

3. **Given** a dashboard panel is rendered with metrics,
   **When** one or more metrics exceed warning or critical
   thresholds,
   **Then** those metrics are visually highlighted with severity
   colors and positioned prominently in the panel.

4. **Given** Grafana/Prometheus is unreachable but pyATS data is
   available,
   **When** the operator requests a health dashboard,
   **Then** the system renders a partial dashboard with available
   pyATS data and clearly indicates which panels could not be
   populated due to the data source being unavailable.

---

### User Story 3 - Visualize Alerts and Incidents (Priority: P3)

As a network engineer responding to incidents, I want to see alert
cards rendered inline in OpenClaw with severity indicators, source
information, and timestamps, so I can triage and prioritize issues
directly from the chat interface without switching between Grafana
alert panels, Prometheus alertmanager, and syslog viewers.

**Why this priority**: Alert visualization is critical for incident
response workflows. Consolidating alerts from multiple sources
(Grafana, Prometheus, syslog) into a unified visual format reduces
context-switching and speeds triage. It depends on US2's data
pipeline foundations but delivers distinct incident response value.

**Independent Test**: Can be tested by requesting "show current
alerts" when active alerts exist in Grafana or Prometheus, and
verifying that severity-colored alert cards appear inline.

**Acceptance Scenarios**:

1. **Given** active alerts exist in Grafana and/or Prometheus,
   **When** the operator requests "show current alerts",
   **Then** the system renders inline alert cards sorted by severity
   (critical first), each displaying alert name, severity level,
   affected device/interface, trigger time, and source system.

2. **Given** alerts exist across multiple severity levels (critical,
   warning, info),
   **When** alert cards are rendered,
   **Then** each card uses a distinct severity color (e.g., red for
   critical, amber for warning, blue for informational) and
   severity counts are summarized at the top.

3. **Given** device syslog messages have been collected,
   **When** the operator requests "show syslog alerts for R1",
   **Then** the system renders syslog entries as alert cards with
   severity mapping (syslog level to alert severity) and
   timestamp-ordered display.

4. **Given** no active alerts exist in any data source,
   **When** the operator requests current alerts,
   **Then** the system renders a clear "all clear" status card
   indicating no active alerts, rather than an empty visualization.

5. **Given** alerts exist but the operator applies a filter (e.g.,
   "show critical alerts only" or "show alerts for device R2"),
   **When** the filtered request is processed,
   **Then** only matching alerts are displayed, with a note
   indicating the active filter and the total unfiltered count.

---

### User Story 4 - Show Change Management Workflow Status (Priority: P4)

As a network engineer managing change requests, I want to see the
lifecycle of a change request from ServiceNow rendered as a visual
timeline in OpenClaw (assess, authorize, implement, review), so I
can track CR progress and identify workflow bottlenecks without
navigating the ServiceNow UI.

**Why this priority**: Change management visualization supports
ITIL workflow compliance and provides operational oversight. It is
lower priority than real-time monitoring (US1-US3) because it
operates on a slower cadence, but it is essential for auditable
change processes and ties into the GAIT audit trail.

**Independent Test**: Can be tested by requesting "show change
request CR-12345 status" when ServiceNow data is available, and
verifying that a visual timeline is rendered showing the CR
lifecycle stages.

**Acceptance Scenarios**:

1. **Given** ServiceNow MCP server has data for an active change
   request,
   **When** the operator requests "show status of CR-12345",
   **Then** the system renders an inline visual timeline showing
   all lifecycle stages (assess, authorize, implement, review),
   with the current stage highlighted, completed stages marked,
   and pending stages shown as upcoming.

2. **Given** multiple change requests are in progress,
   **When** the operator requests "show all active change requests",
   **Then** the system renders a summary view with each CR as a
   compact timeline row, showing CR number, description, current
   stage, assignee, and scheduled window.

3. **Given** a change request has been rejected or rolled back,
   **When** the CR timeline is rendered,
   **Then** the timeline clearly indicates the rejection/rollback
   point with the associated reason and any linked incident numbers.

4. **Given** ServiceNow MCP server is unreachable,
   **When** the operator requests change management visualization,
   **Then** the system returns a clear message indicating the
   ServiceNow data source is unavailable and suggests retrying.

---

### User Story 5 - Render Path Trace and Diff Visualizations (Priority: P5)

As a network engineer troubleshooting connectivity or reviewing
changes, I want to see hop-by-hop forwarding paths rendered as
interactive network diagrams and before/after configuration diffs
displayed as visual comparisons, so I can quickly identify where
traffic is being misrouted or what configuration changed.

**Why this priority**: Path trace and diff visualizations are
advanced troubleshooting tools. They provide high value during
incident response and change review but are used less frequently
than topology maps and dashboards. They depend on data from
US1 (topology context) and the existing pyATS/SuzieQ data
collection.

**Independent Test**: Can be tested by requesting "trace path from
10.0.1.1 to 10.0.2.1" or "show config diff for R1" and verifying
that visual diagrams appear inline.

**Acceptance Scenarios**:

1. **Given** routing and forwarding data is available from
   pyATS/SuzieQ,
   **When** the operator requests "trace path from 10.0.1.1 to
   10.0.2.1",
   **Then** the system renders an inline diagram showing the
   hop-by-hop forwarding path with each node, ingress/egress
   interfaces, and next-hop decisions clearly labeled.

2. **Given** a path trace traverses a device with multiple ECMP
   next-hops,
   **When** the path diagram is rendered,
   **Then** all equal-cost paths are shown as parallel branches
   in the diagram, with load-sharing indicators.

3. **Given** a configuration change has been made to a device,
   **When** the operator requests "show config diff for R1",
   **Then** the system renders a visual side-by-side or unified
   diff view with additions highlighted in green, deletions in
   red, and unchanged context lines in neutral color.

4. **Given** routing table changes have occurred (e.g., new prefixes
   learned, prefixes withdrawn),
   **When** the operator requests "show routing changes for R1",
   **Then** the system renders a visual diff showing added routes,
   removed routes, and changed attributes (next-hop, metric,
   preference) with clear color coding.

5. **Given** ACL modifications have been made,
   **When** the operator requests "show ACL diff for R1",
   **Then** the system renders a visual comparison of ACL entries
   with added, removed, and reordered rules clearly indicated.

6. **Given** a path trace encounters a black hole (no route to
   destination at a hop),
   **When** the diagram is rendered,
   **Then** the visualization clearly marks the point of failure
   with an error indicator and the last known hop before the
   black hole.

---

### Edge Cases

- What happens when the Canvas/A2UI rendering engine encounters a
  topology with 500+ nodes that exceeds visual display capacity?
- How does the system handle a request for visualization when the
  underlying data source (pyATS, Grafana, ServiceNow) returns
  partial data due to timeout?
- What happens when the operator requests a visualization type that
  is not supported (e.g., "show me a 3D hologram of the network")?
- How does the system behave when two concurrent visualization
  requests are made for different data (e.g., topology and
  dashboard simultaneously)?
- What happens when the Canvas/A2UI framework itself is unavailable
  or the OpenClaw client does not support Canvas rendering?
- How does the system handle visualization of stale data when the
  data source has not been polled recently?
- What happens when a topology map is requested for a network with
  a single device and no neighbor relationships?
- How does the system handle extremely long diff outputs (e.g.,
  a full running configuration replacement)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render network topology maps as inline
  Canvas/A2UI visualizations within the OpenClaw chat interface,
  using CDP/LLDP discovery data from existing MCP servers as the
  data source.
- **FR-002**: System MUST apply health-based color coding to
  topology map nodes, reflecting device health status derived
  from available metric data (CPU, memory, interface errors,
  protocol adjacency states).
- **FR-003**: System MUST render real-time dashboard panels inline,
  displaying interface counters, BGP peer status, OSPF adjacency
  state, and CPU/memory metrics sourced from Grafana, Prometheus,
  and pyATS MCP servers.
- **FR-004**: System MUST render alert cards inline with severity-
  based color coding, sourced from Grafana alerts, Prometheus
  alertmanager, and device syslog data.
- **FR-005**: System MUST render change management lifecycle
  timelines from ServiceNow change request data, showing all
  stages (assess, authorize, implement, review) with current
  state indication.
- **FR-006**: System MUST render hop-by-hop path trace diagrams
  as inline visual network diagrams from routing/forwarding data.
- **FR-007**: System MUST render configuration diff visualizations
  (before/after comparisons) with color-coded additions, deletions,
  and context lines for running configs, routing tables, and ACLs.
- **FR-008**: System MUST operate within OpenClaw's Canvas/A2UI
  framework and render all visualizations inline in the chat
  interface — not in a separate browser tab or window.
- **FR-009**: System MUST complement the existing Three.js HUD
  (ui/netclaw-visual/) without replacing or interfering with it.
  Both visualization systems MUST coexist and operate independently.
- **FR-010**: System MUST source all visualization data from
  existing MCP servers (pyATS, Grafana, Prometheus, ServiceNow,
  SuzieQ, Batfish) without establishing new direct connections
  to network devices.
- **FR-011**: System MUST log all visualization generation events
  to the GAIT audit trail, including the visualization type,
  data sources consulted, scope (devices/sites), and timestamp.
- **FR-012**: System MUST gracefully degrade when one or more
  data sources are unavailable, rendering partial visualizations
  with clear indicators of which data is missing and why.
- **FR-013**: System MUST support filtering and scoping of
  visualizations by device name, site, device role, severity level,
  and time range as appropriate to each visualization type.
- **FR-014**: System MUST render health scorecards with per-device
  and per-site health scores, supporting drill-down from site-level
  summaries to individual device details.
- **FR-015**: System MUST render OSI-layer troubleshooting diagnosis
  results as visual flow diagrams during interactive troubleshooting
  sessions.

### Key Entities

- **Canvas Visualization**: A visual artifact rendered inline within
  the OpenClaw chat interface via the Canvas/A2UI framework. Each
  visualization has a type (topology, dashboard, alert, timeline,
  diff, path trace, scorecard), data source references, scope, and
  rendering timestamp.
- **Topology Map**: A graph visualization where nodes represent
  network devices and edges represent discovered neighbor
  relationships (CDP/LLDP). Nodes carry health status and device
  metadata.
- **Dashboard Panel**: A collection of metric displays (gauges,
  counters, status indicators) for one or more devices, sourced
  from time-series and state data.
- **Alert Card**: A visual representation of an active alert or
  incident, carrying severity level, source system, affected
  entity, description, and timestamp.
- **Change Timeline**: A visual lifecycle representation of a
  ServiceNow change request, showing sequential stages with
  status indicators and metadata.
- **Diff View**: A visual comparison of two states (configurations,
  routing tables, ACLs) highlighting additions, deletions, and
  modifications.
- **Path Trace Diagram**: A directed graph showing the forwarding
  path between two endpoints, with per-hop interface and routing
  decision details.
- **Health Scorecard**: An aggregated health summary for a device
  or site, combining multiple health indicators into a composite
  score with drill-down capability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can request and receive an inline topology
  map visualization within 10 seconds for networks up to 200
  devices.
- **SC-002**: Dashboard panels display metric values that match the
  source data (Grafana/Prometheus/pyATS) with no more than 60
  seconds of data staleness.
- **SC-003**: Alert visualizations correctly reflect 100% of active
  alerts from configured data sources, with accurate severity
  classification.
- **SC-004**: All visualization types (topology, dashboard, alert,
  timeline, diff, path trace, scorecard) render inline within the
  OpenClaw chat interface without requiring a separate browser tab.
- **SC-005**: The existing Three.js HUD (ui/netclaw-visual/)
  remains fully functional and unmodified after Canvas/A2UI
  integration is deployed.
- **SC-006**: 100% of visualization generation events are recorded
  in the GAIT audit trail with complete metadata.
- **SC-007**: All artifact coherence checklist items are complete
  (README, install.sh, SOUL.md, SKILL.md, .env.example, TOOLS.md,
  config/openclaw.json).
- **SC-008**: Graceful degradation is verified: when any single
  data source is unavailable, the system renders partial
  visualizations for all visualization types that can still be
  served by remaining sources.
- **SC-009**: Existing NetGeniusClaw skills and MCP servers remain fully
  functional after the addition (backwards compatibility verified).

## Assumptions

- OpenClaw's Canvas/A2UI framework is available and supports the
  rendering primitives needed for graph visualizations (nodes,
  edges, labels), metric panels, timeline views, and diff displays.
  If Canvas/A2UI capabilities are more limited than assumed, the
  scope of visualization types may need to be adjusted.
- All data required for visualizations is already accessible via
  existing MCP servers (pyATS, Grafana, Prometheus, ServiceNow,
  SuzieQ, Batfish). No new data collection mechanisms or device
  connections are introduced by this feature.
- The existing Three.js HUD (ui/netclaw-visual/) will continue to
  serve as the immersive 3D visualization tool. Canvas/A2UI
  provides complementary inline visualizations within the chat
  experience, not a replacement.
- Network topology data from CDP/LLDP discovery provides sufficient
  neighbor relationship information to construct meaningful topology
  maps. Networks that do not run CDP or LLDP may have limited or
  no topology visualization capability.
- The GAIT audit logging infrastructure is already operational and
  accepts new event types for visualization generation without
  requiring modifications to the audit framework itself.
- Operators interact with visualizations through natural language
  requests in the OpenClaw chat. The agent determines the
  appropriate visualization type and data sources based on the
  operator's intent.
- Canvas/A2UI rendering performance is sufficient for the data
  volumes typical of enterprise networks (up to 500 devices,
  thousands of interfaces, hundreds of alerts). Larger environments
  may require scoping/filtering to maintain rendering performance.

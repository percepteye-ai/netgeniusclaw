# Feature Specification: SuzieQ MCP Server

**Feature Branch**: `001-suzieq-mcp-server`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "Build a new MCP server wrapping the SuzieQ network observability platform. SuzieQ provides multi-vendor network observability with time-travel queries."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Current Network State (Priority: P1)

As a network engineer, I want to query the current state of any
network table (routes, interfaces, MAC, ARP, BGP, OSPF, LLDP, VLANs,
etc.) across all devices in my environment from a single natural
language request, so I can understand what is happening on the network
right now without logging into individual devices.

**Why this priority**: This is the foundational capability. Every
other feature (time-travel, assertions, path analysis) depends on
the ability to query current network state. Without this, the MCP
server has no value.

**Independent Test**: Can be fully tested by issuing a query like
"show me all BGP peers" and verifying that results return from
SuzieQ with correct device, namespace, and table data.

**Acceptance Scenarios**:

1. **Given** SuzieQ is running and has collected network data,
   **When** the operator requests "show all OSPF neighbors",
   **Then** the system returns a structured table of OSPF neighbor
   relationships across all devices with state, area, and interface
   details.

2. **Given** SuzieQ is running with data from multiple vendors,
   **When** the operator requests "show interfaces on router R1",
   **Then** the system returns interface status, IP addresses, MTU,
   speed, and error counters for that specific device.

3. **Given** SuzieQ has no data for a requested table or device,
   **When** the operator queries that table or device,
   **Then** the system returns a clear message indicating no data
   is available rather than an error.

---

### User Story 2 - Time-Travel Queries (Priority: P2)

As a network engineer investigating a past incident, I want to query
what the network looked like at a specific point in time, so I can
understand what changed and correlate network state with reported
issues.

**Why this priority**: Time-travel is SuzieQ's signature
differentiator. Without it, the MCP server is just another device
query tool. This enables root-cause analysis and change correlation
that no other NetGeniusClaw MCP server provides.

**Independent Test**: Can be tested by querying "show BGP peers at
2026-03-25 14:00" and verifying the results reflect the historical
snapshot, not current state.

**Acceptance Scenarios**:

1. **Given** SuzieQ has historical data spanning multiple days,
   **When** the operator requests "show routes at 2026-03-20 09:00",
   **Then** the system returns the routing table as it existed at
   that specific timestamp.

2. **Given** SuzieQ has historical data,
   **When** the operator requests "show interfaces between
   2026-03-20 and 2026-03-21",
   **Then** the system returns interface state changes that occurred
   within that time window.

3. **Given** the operator requests a timestamp before SuzieQ began
   collecting data,
   **When** the query is executed,
   **Then** the system returns a clear message indicating no
   historical data is available for that period.

---

### User Story 3 - Network Assertions (Priority: P3)

As a network engineer, I want to run validation assertions against
the network (e.g., "all BGP peers should be established", "no
interface should have errors above threshold") so I can proactively
detect drift and compliance violations.

**Why this priority**: Assertions transform SuzieQ from a passive
query tool into an active validation engine. This supports the
constitution's "verify after every change" principle (VIII).

**Independent Test**: Can be tested by running "assert all BGP
sessions are established" and verifying it returns pass/fail results
per device with details on any failures.

**Acceptance Scenarios**:

1. **Given** SuzieQ has current network data,
   **When** the operator requests "assert all BGP peers are
   established",
   **Then** the system returns a pass/fail result for each device
   with details on any peers not in Established state.

2. **Given** SuzieQ has current network data with some interface
   errors,
   **When** the operator requests "assert no interfaces have errors",
   **Then** the system returns failures listing each interface with
   non-zero error counters and the specific counts.

3. **Given** the operator runs an assertion against a table with no
   data,
   **When** the assertion executes,
   **Then** the system reports the assertion cannot be evaluated
   due to missing data rather than returning a false pass.

---

### User Story 4 - Summarized Network Views (Priority: P4)

As a network engineer, I want to get aggregated summary views of
network tables (e.g., total routes per device, interface utilization
distribution, BGP peer count by state) so I can quickly assess
overall network health without reading through hundreds of rows.

**Why this priority**: Summaries provide the high-level operational
dashboard view. Important for daily operations but not blocking
for core functionality.

**Independent Test**: Can be tested by requesting "summarize routes"
and verifying aggregated counts, distributions, and per-device
breakdowns are returned.

**Acceptance Scenarios**:

1. **Given** SuzieQ has route data from multiple devices,
   **When** the operator requests "summarize routes",
   **Then** the system returns per-device route counts, protocol
   distribution, and total unique prefixes.

2. **Given** SuzieQ has interface data,
   **When** the operator requests "summarize interfaces",
   **Then** the system returns counts by state (up/down/admin-down),
   speed distribution, and error rate statistics.

---

### User Story 5 - Network Path Analysis (Priority: P5)

As a network engineer troubleshooting connectivity, I want to trace
the forwarding path between two endpoints through the network so I
can identify where traffic is being dropped, misrouted, or suboptimally
forwarded.

**Why this priority**: Path analysis is a high-value troubleshooting
tool but depends on comprehensive data collection from US1. It is
an advanced feature built on top of the core query capabilities.

**Independent Test**: Can be tested by requesting "trace path from
10.0.1.1 to 10.0.2.1" and verifying the hop-by-hop forwarding path
is returned with interface and next-hop details at each step.

**Acceptance Scenarios**:

1. **Given** SuzieQ has routing and interface data for the network,
   **When** the operator requests "trace path from 10.0.1.1 to
   10.0.2.1",
   **Then** the system returns the hop-by-hop forwarding path with
   ingress/egress interfaces, next-hops, and the forwarding decision
   at each node.

2. **Given** the path between two endpoints traverses a device not
   monitored by SuzieQ,
   **When** the path trace is executed,
   **Then** the system indicates a gap in the path where the
   unmonitored device exists.

---

### Edge Cases

- What happens when SuzieQ's REST API is unreachable or returns
  a connection timeout?
- How does the system handle queries for network tables that SuzieQ
  does not support?
- What happens when a namespace filter matches no devices?
- How does the system behave when SuzieQ is mid-collection and data
  is partially stale?
- What happens when time-travel queries specify a timestamp in the
  future?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose SuzieQ "show" operations for all
  supported network tables (routes, interfaces, MAC, ARP, BGP, OSPF,
  LLDP, EVPN, VLANs, MLAG, device inventory, and others).
- **FR-002**: System MUST support filtering queries by device name,
  namespace, hostname, and any column-level filter that SuzieQ
  supports.
- **FR-003**: System MUST support time-travel queries by accepting
  a timestamp or time range parameter on any show operation.
- **FR-004**: System MUST expose SuzieQ "summarize" operations for
  aggregated views of any supported network table.
- **FR-005**: System MUST expose SuzieQ "assert" operations for
  validation checks against network state.
- **FR-006**: System MUST expose SuzieQ "path" analysis for tracing
  forwarding paths between endpoints.
- **FR-007**: System MUST be strictly read-only — no write, delete,
  or configuration operations on SuzieQ or any network device.
- **FR-008**: System MUST return structured, parseable results with
  clear column headers and data types.
- **FR-009**: System MUST handle SuzieQ API errors gracefully,
  returning descriptive error messages without exposing internal
  details or credentials.
- **FR-010**: System MUST log all queries to the GAIT audit trail.
- **FR-011**: System MUST support namespace-scoped queries for
  multi-tenant or segmented network environments.
- **FR-012**: All connection credentials (SuzieQ REST API URL, API
  key/token) MUST be read from environment variables at runtime.

### Key Entities

- **Network Table**: A category of network data collected by SuzieQ
  (e.g., routes, interfaces, BGP, OSPF). Each table has a defined
  schema of columns and supports show, summarize, and assert.
- **Namespace**: A logical grouping of devices in SuzieQ, used to
  segment queries by network domain, site, or tenant.
- **Snapshot**: A point-in-time capture of network state, enabling
  time-travel queries by referencing a specific timestamp.
- **Assertion Result**: A pass/fail validation result for a network
  table, including device-level detail on any failures.
- **Path Trace**: A hop-by-hop forwarding path between two endpoints,
  including ingress/egress interfaces and forwarding decisions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can query any SuzieQ-supported network table
  and receive results within 5 seconds for networks up to 500 devices.
- **SC-002**: Time-travel queries return historical state accurately
  when compared against known snapshots from the same timestamp.
- **SC-003**: Assertions correctly identify 100% of known network
  state violations when tested against a controlled environment with
  intentionally degraded peers/interfaces.
- **SC-004**: Path analysis returns the correct forwarding path when
  validated against traceroute output in the same network.
- **SC-005**: All artifact coherence checklist items are complete
  (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md,
  config/openclaw.json).
- **SC-006**: Existing NetGeniusClaw skills and MCP servers remain fully
  functional after the addition (backwards compatibility verified).
- **SC-007**: 100% of queries are recorded in the GAIT audit trail.

## Assumptions

- SuzieQ is already deployed and collecting data from the target
  network via its poller component. This MCP server does not manage
  SuzieQ deployment or polling configuration.
- SuzieQ's REST API is accessible from the machine running the MCP
  server (network connectivity and authentication are pre-configured).
- The MCP server communicates with SuzieQ via its REST API, not by
  importing SuzieQ as a library or accessing its database directly.
- The MCP server is read-only by design — it queries SuzieQ but
  never modifies network device configuration.
- The existing community SuzieQ MCP project
  (github.com/PovedaAqui/suzieq-mcp) is used as reference but the
  implementation follows NetGeniusClaw's MCP server standards (FastMCP,
  GAIT integration, constitution compliance).
- SuzieQ supports the REST API endpoints needed for show, summarize,
  assert, and path operations. If any endpoint is unavailable, the
  corresponding tool will return a "not supported" message.
